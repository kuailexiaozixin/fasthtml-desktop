-- open-docflow: SQLite schema
-- Dokumentu darbo eigos valdymo sistema
--
-- Ported from the upstream PostgreSQL schema so the example runs fully offline:
--   SERIAL PRIMARY KEY -> INTEGER PRIMARY KEY AUTOINCREMENT
--   JSONB              -> TEXT (JSON string)
--   TIMESTAMPTZ/NOW()  -> TEXT (ISO-8601) / CURRENT_TIMESTAMP
--   CREATE SCHEMA      -> dropped (SQLite has no schemas; everything is "main")
--
-- Applying this file is optional: src/models.py::init_db() creates the same
-- tables via SQLAlchemy and seeds the document types. Use it when you want to
-- bootstrap the database with the sqlite3 CLI instead:
--     sqlite3 data/open-docflow.sqlite < sql/schema.sql

PRAGMA foreign_keys = ON;

-- Dokumentu tipai
CREATE TABLE IF NOT EXISTS document_types (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    required_fields TEXT DEFAULT '[]',
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Dokumentai
CREATE TABLE IF NOT EXISTS documents (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       VARCHAR(500) NOT NULL,
    doc_type_id INTEGER REFERENCES document_types(id),
    status      VARCHAR(50) NOT NULL DEFAULT 'gautas'
                CHECK (status IN ('gautas', 'perziurimas', 'patvirtintas', 'atmestas')),
    uploaded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    file_path   VARCHAR(1000),
    file_size   INTEGER,
    metadata    TEXT DEFAULT '{}',
    submitted_by VARCHAR(200),
    assigned_to  VARCHAR(200)
);

CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_documents_doc_type ON documents(doc_type_id);
CREATE INDEX IF NOT EXISTS idx_documents_uploaded_at ON documents(uploaded_at);

-- Darbo eigos zingsniai (audito sekimas)
CREATE TABLE IF NOT EXISTS workflow_steps (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id  INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    from_status  VARCHAR(50),
    to_status    VARCHAR(50) NOT NULL,
    actor        VARCHAR(200) NOT NULL,
    comment      TEXT,
    created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_workflow_steps_document ON workflow_steps(document_id);
CREATE INDEX IF NOT EXISTS idx_workflow_steps_created ON workflow_steps(created_at);

-- Pradiniai dokumentu tipai
INSERT INTO document_types (name, description, required_fields) VALUES
    ('Prasymas',      'Oficialus prasymas institucijoms',               '["tema", "prasytojas", "data"]'),
    ('Leidimas',      'Leidimas vykdyti veikla ar atlikti veiksmus',   '["numeris", "galiojimo_data"]'),
    ('Pazymejimas',   'Kvalifikacijos arba fakto patvirtinimo dokumentas', '["numeris", "istaiga"]'),
    ('Sutartis',      'Dviesale ar daugiasale sutartis',                '["salys", "suma", "galiojimo_laikotarpis"]'),
    ('Ataskaita',     'Periodine arba vienkartine ataskaita',           '["laikotarpis", "rengejo_pareigos"]'),
    ('Isakymas',      'Vadovo ar institucijos isakymas',                '["numeris", "data", "pasirases"]'),
    ('Protokolas',    'Posedzio ar susirinkimo protokolas',             '["data", "dalyviai", "pirmininkas"]'),
    ('Aktas',         'Patikrinimo arba perdavimo aktas',              '["data", "komisija"]')
ON CONFLICT (name) DO NOTHING;
