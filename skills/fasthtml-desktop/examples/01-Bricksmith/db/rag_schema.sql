-- Bricksmith RAG schema (SQLite + sqlite-vec). Idempotent.
--
-- Retrieval over CRE documents (leases, zoning memos, environmental Phase I,
-- property condition, title commitments, market reports).
--
-- Upstream used PostgreSQL + pgvector. Here the vector index is the
-- `sqlite-vec` extension, which exposes KNN search through `vec0` virtual
-- tables. Table names lose the `bricksmith_rag.` qualifier (SQLite has no
-- schemas); the shim in db/__init__.py strips it from incoming SQL.
--
-- Layout note: the plain tables come first and the `vec0` table last, behind
-- the `-- >>> VECTOR TABLE` marker. db/migrate.py truncates the script at that
-- marker when the sqlite-vec extension cannot be loaded, so the app still
-- installs and falls back to keyword search instead of failing to start.

CREATE TABLE IF NOT EXISTS documents (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id  INTEGER,             -- soft reference to properties(id)
    doc_type     TEXT NOT NULL,       -- lease | zoning | environmental | pcr | title | market | misc
    title        TEXT NOT NULL,
    source_path  TEXT,
    metadata     TEXT NOT NULL DEFAULT '{}',   -- JSON
    created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS documents_property_idx ON documents(property_id);
CREATE INDEX IF NOT EXISTS documents_type_idx     ON documents(doc_type);

CREATE TABLE IF NOT EXISTS chunks (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id  INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    ord          INTEGER NOT NULL,
    text         TEXT NOT NULL,
    token_count  INTEGER,
    metadata     TEXT NOT NULL DEFAULT '{}',   -- JSON
    UNIQUE (document_id, ord)
);
CREATE INDEX IF NOT EXISTS chunks_document_idx ON chunks(document_id);

CREATE TABLE IF NOT EXISTS rag_queries (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER,
    session_id  INTEGER,
    query       TEXT NOT NULL,
    top_k       INTEGER,
    filters     TEXT,            -- JSON
    latency_ms  INTEGER,
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- >>> VECTOR TABLE (requires the sqlite-vec extension) ----------------------
--
-- `{{EMBEDDING_DIM}}` is substituted by db/migrate.py from the EMBEDDING_DIM
-- setting. Changing the dimension requires `python -m db.migrate --drop`
-- (destroys the RAG tables) followed by a re-index.
--
-- Deliberately minimal: only the primary key and the vector live in `vec0`.
-- Three hard-won constraints drove that decision:
--   1. vec0 metadata columns reject NULL ("Expected integer for INTEGER
--      metadata column ..., received NULL"), and `documents.property_id` is
--      legitimately nullable.
--   2. vec0 has no UPSERT — re-inserting an existing primary key raises
--      "UNIQUE constraint failed". rag/indexer.py therefore deletes first.
--   3. Virtual tables cannot carry foreign keys, so deleting a document does
--      NOT cascade here. Orphaned vectors still consume the top-k budget, so
--      rag/indexer.py removes them explicitly (see purge_orphan_vectors).
--
-- Filtering by doc_type / property_id happens by pushing a
-- `chunk_id IN (SELECT ... FROM chunks JOIN documents ...)` subquery into the
-- KNN query, which vec0 supports and which also filters out any orphans.
CREATE VIRTUAL TABLE IF NOT EXISTS embeddings USING vec0(
    chunk_id  INTEGER PRIMARY KEY,
    embedding float[{{EMBEDDING_DIM}}] distance_metric=cosine
);
