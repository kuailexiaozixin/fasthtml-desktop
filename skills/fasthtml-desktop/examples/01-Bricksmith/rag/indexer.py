"""Chunk + embed + upsert into the RAG tables (SQLite + sqlite-vec).

The chunking logic is unchanged from upstream; only the storage layer moved
from pgvector to a `vec0` virtual table. Two consequences drive the code below:

* **`vec0` cannot upsert.** Re-inserting an existing `chunk_id` raises
  `UNIQUE constraint failed`, so every write deletes the old vector first.
* **`vec0` ignores foreign keys.** `DELETE FROM documents` cascades to `chunks`
  but *not* to `embeddings`, so vectors have to be removed explicitly or they
  linger as orphans and eat into future top-k results.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

from db import connect, vector_search_available
from rag.embeddings import embed_texts
from rag.retriever import pack_vector

log = logging.getLogger(__name__)

# Simple target chunk size. Splits on paragraph boundaries first; falls back
# to sentence splits if a paragraph is too long.
TARGET_CHARS = 1800
OVERLAP_CHARS = 150


@dataclass
class DocIn:
    title: str
    doc_type: str
    text: str
    property_id: int | None = None
    source_path: str | None = None
    metadata: dict | None = None


def chunk_text(text: str, target: int = TARGET_CHARS, overlap: int = OVERLAP_CHARS) -> list[str]:
    """Greedy paragraph-first chunker with character overlap."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    buf = ""
    for p in paras:
        if len(p) > target:
            for s in re.split(r"(?<=[.!?])\s+", p):
                if len(buf) + len(s) + 1 > target:
                    if buf:
                        chunks.append(buf.strip())
                    buf = (buf[-overlap:] if overlap and buf else "") + " " + s
                else:
                    buf = (buf + " " + s).strip()
            continue
        if len(buf) + len(p) + 2 > target:
            if buf:
                chunks.append(buf.strip())
            buf = (buf[-overlap:] if overlap and buf else "") + "\n\n" + p
        else:
            buf = (buf + "\n\n" + p).strip() if buf else p
    if buf.strip():
        chunks.append(buf.strip())
    return chunks


def upsert_document(doc: DocIn, *, replace: bool = False) -> int:
    """Insert document + chunks + embeddings. Returns document_id.

    If replace=True and a document with the same (title, source_path) already
    exists, delete it first so re-runs are idempotent.
    """
    meta_json = json.dumps(doc.metadata or {})
    store_vectors = vector_search_available()

    with connect() as conn, conn.cursor() as cur:
        if replace:
            # Order matters: vectors first, because the cascade that removes
            # the chunks would otherwise hide the ids we need to look up.
            if store_vectors:
                cur.execute(
                    """
                    DELETE FROM embeddings WHERE chunk_id IN (
                        SELECT c.id FROM chunks c
                        JOIN documents d ON d.id = c.document_id
                        WHERE d.title = %s AND d.source_path IS NOT DISTINCT FROM %s
                    )
                    """,
                    (doc.title, doc.source_path),
                )
            cur.execute(
                "DELETE FROM documents WHERE title = %s AND source_path IS NOT DISTINCT FROM %s",
                (doc.title, doc.source_path),
            )

        cur.execute(
            """
            INSERT INTO documents (property_id, doc_type, title, source_path, metadata)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
            """,
            (doc.property_id, doc.doc_type, doc.title, doc.source_path, meta_json),
        )
        doc_id = cur.fetchone()[0]

        chunks = chunk_text(doc.text)
        if not chunks:
            conn.commit()
            return doc_id

        vectors = embed_texts(chunks) if store_vectors else []
        if store_vectors and len(vectors) != len(chunks):
            raise RuntimeError(
                f"embedder returned {len(vectors)} vectors for {len(chunks)} chunks"
            )

        for i, text in enumerate(chunks):
            cur.execute(
                """
                INSERT INTO chunks (document_id, ord, text, token_count)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (doc_id, i, text, len(text) // 4),
            )
            chunk_id = cur.fetchone()[0]
            if not store_vectors:
                continue
            # AUTOINCREMENT ids can be reused after a table reset, so clear any
            # stale vector sitting on this id before inserting (vec0 has no
            # ON CONFLICT support).
            cur.execute("DELETE FROM embeddings WHERE chunk_id = %s", (chunk_id,))
            cur.execute(
                "INSERT INTO embeddings (chunk_id, embedding) VALUES (%s, %s)",
                (chunk_id, pack_vector(vectors[i])),
            )

        conn.commit()
    return doc_id


def upsert_documents(docs: list[DocIn], *, replace: bool = False) -> list[int]:
    ids: list[int] = []
    for d in docs:
        ids.append(upsert_document(d, replace=replace))
    return ids


def purge_orphan_vectors() -> int:
    """Drop vectors whose chunk no longer exists. Returns how many were removed.

    `vec0` is a virtual table and therefore outside SQLite's foreign-key
    machinery, so orphans accumulate whenever a document is deleted through any
    path that does not go via :func:`upsert_document`.
    """
    if not vector_search_available():
        return 0
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT count(*) AS n FROM embeddings
            WHERE chunk_id NOT IN (SELECT id FROM chunks)
            """
        )
        n = int(cur.fetchone()["n"] or 0)
        if n:
            cur.execute(
                "DELETE FROM embeddings WHERE chunk_id NOT IN (SELECT id FROM chunks)"
            )
            conn.commit()
            log.info("purged %d orphaned vectors", n)
    return n


def build_ann_index(lists: int = 100) -> None:
    """Finalise the vector index after a bulk load.

    Upstream this built a pgvector ivfflat index. `vec0` maintains its own
    index on write, so there is nothing to build — the useful work left is
    sweeping orphans and reporting the corpus size. The name and signature are
    kept so existing callers (e.g. the synthetic data generator) still work.
    """
    if not vector_search_available():
        log.info("sqlite-vec unavailable — skipping vector index maintenance")
        return
    purge_orphan_vectors()
    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT count(*) AS n FROM embeddings")
        n = int(cur.fetchone()["n"] or 0)
    log.info("vector index ready: %d embeddings (vec0 indexes on write)", n)
