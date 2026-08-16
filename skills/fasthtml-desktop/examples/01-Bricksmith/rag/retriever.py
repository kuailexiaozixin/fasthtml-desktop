"""Cosine similarity retrieval over the RAG tables, backed by sqlite-vec.

Upstream used pgvector (`embedding <=> query` inside a plain SQL join). Here the
vectors live in a `vec0` virtual table, which exposes k-nearest-neighbour search
through two magic columns:

    WHERE embedding MATCH :blob AND k = :n     -- returns a `distance` column

Two implementation notes that are easy to get wrong:

1. **Metadata filters are pushed *into* the KNN**, not applied afterwards.
   `vec0` accepts `chunk_id IN (<subquery>)` alongside `MATCH`, so the engine
   only ever considers the chunks that survive the filter. Filtering after the
   fact would silently return fewer than `k` rows.
2. **`vec0` has no foreign keys.** Deleting a document cascades to `chunks` but
   leaves its vectors behind, and those orphans still consume the top-k budget.
   The `chunk_id IN (...)` subquery doubles as an orphan guard, so a stale
   vector can never displace a real result.
"""

from __future__ import annotations

import json
import logging
import re
import struct
import time
from dataclasses import dataclass

from db import connect, vector_search_available
from rag.embeddings import embed_one

log = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    chunk_id: int
    document_id: int
    doc_type: str
    title: str
    property_id: int | None
    ord: int
    text: str
    score: float  # cosine similarity in [0, 1]
    metadata: dict


def pack_vector(values) -> bytes:
    """Serialise an embedding into the little-endian float32 blob vec0 wants."""
    floats = [float(x) for x in values]
    return struct.pack(f"<{len(floats)}f", *floats)


_BASE_SQL = """
    SELECT c.id AS chunk_id, c.document_id, c.ord, c.text, c.metadata,
           d.doc_type, d.title, d.property_id, v.distance AS distance
    FROM embeddings v
    JOIN chunks c ON c.id = v.chunk_id
    JOIN documents d ON d.id = c.document_id
    WHERE v.embedding MATCH %s AND v.k = %s
"""


def _filter_clause(
    doc_types: list[str] | None, property_id: int | None
) -> tuple[str, list]:
    """Build the `chunk_id IN (...)` pushdown plus its bound parameters."""
    conds = ["1=1"]
    params: list = []
    if doc_types:
        conds.append("fd.doc_type IN (%s)" % ",".join(["%s"] * len(doc_types)))
        params.extend(doc_types)
    if property_id is not None:
        conds.append("fd.property_id = %s")
        params.append(property_id)
    clause = (
        " AND v.chunk_id IN ("
        " SELECT fc.id FROM chunks fc"
        " JOIN documents fd ON fd.id = fc.document_id"
        f" WHERE {' AND '.join(conds)})"
    )
    return clause, params


def _row_to_chunk(row, score: float) -> RetrievedChunk:
    metadata = row["metadata"]
    if isinstance(metadata, str):  # shim already decodes JSON columns
        try:
            metadata = json.loads(metadata)
        except ValueError:
            metadata = {}
    return RetrievedChunk(
        chunk_id=row["chunk_id"],
        document_id=row["document_id"],
        ord=row["ord"],
        text=row["text"],
        metadata=metadata or {},
        doc_type=row["doc_type"],
        title=row["title"],
        property_id=row["property_id"],
        score=score,
    )


def _keyword_fallback(
    cur,
    query: str,
    k: int,
    doc_types: list[str] | None,
    property_id: int | None,
) -> list[RetrievedChunk]:
    """Degrade to LIKE matching when the sqlite-vec extension is missing.

    Far worse than real embeddings, but it keeps the app usable instead of
    crashing on a machine where the extension cannot be loaded.
    """
    terms = [t for t in re.findall(r"[A-Za-z0-9']{3,}", query.lower())][:8]
    if not terms:
        return []

    score_expr = " + ".join(["(CASE WHEN lower(c.text) LIKE %s THEN 1 ELSE 0 END)"] * len(terms))
    sql = [
        f"""
        SELECT c.id AS chunk_id, c.document_id, c.ord, c.text, c.metadata,
               d.doc_type, d.title, d.property_id,
               ({score_expr}) AS hits
        FROM chunks c
        JOIN documents d ON d.id = c.document_id
        WHERE 1=1
        """
    ]
    params: list = [f"%{t}%" for t in terms]
    if doc_types:
        sql.append("AND d.doc_type IN (%s)" % ",".join(["%s"] * len(doc_types)))
        params.extend(doc_types)
    if property_id is not None:
        sql.append("AND d.property_id = %s")
        params.append(property_id)
    sql.append("ORDER BY hits DESC, c.id ASC LIMIT %s")
    params.append(k)

    cur.execute(" ".join(sql), params)
    out = []
    for row in cur.fetchall():
        hits = row["hits"] or 0
        if hits == 0:
            continue
        out.append(_row_to_chunk(row, round(hits / len(terms), 4)))
    return out


def retrieve(
    query: str,
    *,
    k: int = 6,
    doc_types: list[str] | None = None,
    property_id: int | None = None,
    log_query: bool = True,
    user_id: int | None = None,
    session_id: int | None = None,
) -> list[RetrievedChunk]:
    started = time.time()
    use_vectors = vector_search_available()

    with connect() as conn, conn.cursor() as cur:
        if use_vectors:
            clause, filter_params = _filter_clause(doc_types, property_id)
            cur.execute(
                _BASE_SQL + clause + " ORDER BY v.distance",
                [pack_vector(embed_one(query)), k, *filter_params],
            )
            out = [
                # vec0 reports cosine *distance* in [0, 2]; flip it back into a
                # similarity and clamp so callers never see a negative score.
                _row_to_chunk(row, max(0.0, min(1.0, 1.0 - float(row["distance"]))))
                for row in cur.fetchall()
            ]
        else:
            out = _keyword_fallback(cur, query, k, doc_types, property_id)

        if log_query:
            cur.execute(
                """
                INSERT INTO rag_queries (user_id, session_id, query, top_k, filters, latency_ms)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    session_id,
                    query,
                    k,
                    json.dumps(
                        {
                            "doc_types": doc_types,
                            "property_id": property_id,
                            "mode": "vector" if use_vectors else "keyword",
                        }
                    ),
                    int((time.time() - started) * 1000),
                ),
            )
            conn.commit()

    return out
