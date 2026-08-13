"""FastDocs data layer — SQLite folders, documents, blocks, templates, versions.

A document is an ordered list of typed **blocks** (heading/paragraph/list/quote/
code/divider). Templates seed a document's blocks; versions snapshot them as JSON;
publishing mints a read-only public token. Mirrors the FastSlides/FastSheets shape.
"""
from __future__ import annotations

import json
import os
import secrets
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = os.getenv("FASTDOCS_DB") or str(Path(__file__).parent / "fastdocs.sqlite")

# Block types and their human labels (order = the "add block" menu order).
BLOCK_TYPES = ["heading1", "heading2", "heading3", "paragraph", "bullet", "numbered", "quote", "code", "divider"]
BLOCK_LABELS = {
    "heading1": "Heading 1", "heading2": "Heading 2", "heading3": "Heading 3",
    "paragraph": "Paragraph", "bullet": "Bulleted list", "numbered": "Numbered list",
    "quote": "Quote", "code": "Code", "divider": "Divider",
}


def connect():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


@contextmanager
def cursor():
    conn = connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def db_exists() -> bool:
    p = Path(DB_PATH)
    return p.exists() and p.stat().st_size > 0


def rows(sql, params=()):
    with cursor() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


def one(sql, params=()):
    with cursor() as conn:
        r = conn.execute(sql, params).fetchone()
        return dict(r) if r else None


def scalar(sql, params=()):
    with cursor() as conn:
        r = conn.execute(sql, params).fetchone()
        return r[0] if r else None


SCHEMA = """
CREATE TABLE IF NOT EXISTS folders (
    id            INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    position      INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS documents (
    id            INTEGER PRIMARY KEY,
    folder_id     INTEGER REFERENCES folders(id) ON DELETE SET NULL,
    title         TEXT NOT NULL,
    created       TEXT,
    updated       TEXT,
    public_token  TEXT                       -- non-null ⇒ published read-only
);
CREATE TABLE IF NOT EXISTS blocks (
    id            INTEGER PRIMARY KEY,
    document_id   INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    position      INTEGER NOT NULL DEFAULT 0,
    type          TEXT NOT NULL DEFAULT 'paragraph',
    content       TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS templates (
    id            INTEGER PRIMARY KEY,
    title         TEXT NOT NULL,
    description   TEXT
);
CREATE TABLE IF NOT EXISTS template_blocks (
    id            INTEGER PRIMARY KEY,
    template_id   INTEGER REFERENCES templates(id) ON DELETE CASCADE,
    position      INTEGER NOT NULL DEFAULT 0,
    type          TEXT NOT NULL DEFAULT 'paragraph',
    content       TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS doc_versions (
    id            INTEGER PRIMARY KEY,
    document_id   INTEGER REFERENCES documents(id) ON DELETE CASCADE,
    title         TEXT,
    snapshot      TEXT NOT NULL,             -- JSON: [{type, content}, ...]
    manual        INTEGER NOT NULL DEFAULT 0,
    created       TEXT
);
CREATE TABLE IF NOT EXISTS chat_messages (
    id            INTEGER PRIMARY KEY,
    thread_id     TEXT NOT NULL,
    role          TEXT NOT NULL,
    content       TEXT NOT NULL,
    created       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_block_doc ON blocks(document_id, position);
CREATE INDEX IF NOT EXISTS idx_doc_folder ON documents(folder_id);
CREATE INDEX IF NOT EXISTS idx_ver_doc ON doc_versions(document_id, id);
"""


def init_schema():
    """Idempotent; safe on every boot so new tables/columns reach existing DBs."""
    with cursor() as conn:
        conn.executescript(SCHEMA)
        # migrate older DBs that predate the public_token column
        have = {r[1] for r in conn.execute("PRAGMA table_info(documents)").fetchall()}
        if "public_token" not in have:
            conn.execute("ALTER TABLE documents ADD COLUMN public_token TEXT")


# --- reads ------------------------------------------------------------------

def folders():
    return rows("SELECT * FROM folders ORDER BY position, id")


def folder(fid):
    return one("SELECT * FROM folders WHERE id=?", (fid,))


def documents(folder_id=None):
    if folder_id is None:
        return rows("SELECT * FROM documents ORDER BY updated DESC, id DESC")
    return rows("SELECT * FROM documents WHERE folder_id=? ORDER BY updated DESC, id DESC", (folder_id,))


def document(doc_id):
    return one("SELECT * FROM documents WHERE id=?", (doc_id,))


def document_by_token(token):
    if not token:
        return None
    return one("SELECT * FROM documents WHERE public_token=?", (token,))


def blocks(doc_id):
    return rows("SELECT * FROM blocks WHERE document_id=? ORDER BY position, id", (doc_id,))


def block(bid):
    return one("SELECT * FROM blocks WHERE id=?", (bid,))


def doc_count(folder_id):
    return scalar("SELECT COUNT(*) FROM documents WHERE folder_id=?", (folder_id,)) or 0


def word_count(doc_id):
    txt = " ".join(b["content"] for b in blocks(doc_id))
    return len(txt.split())


# --- document / folder writes ----------------------------------------------

def _norm_type(t):
    return t if t in BLOCK_TYPES else "paragraph"


def create_folder(name) -> int:
    name = (name or "Untitled folder").strip() or "Untitled folder"
    with cursor() as conn:
        at = conn.execute("SELECT COALESCE(MAX(position),-1)+1 FROM folders").fetchone()[0]
        conn.execute("INSERT INTO folders(name, position) VALUES (?,?)", (name, at))
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def create_document(folder_id, title, block_list) -> int:
    """block_list: [{type, content}]. Returns new document id."""
    title = (title or "Untitled document").strip() or "Untitled document"
    with cursor() as conn:
        conn.execute(
            "INSERT INTO documents(folder_id,title,created,updated) VALUES (?,?,datetime('now'),datetime('now'))",
            (folder_id, title))
        doc_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        for i, b in enumerate(block_list):
            conn.execute("INSERT INTO blocks(document_id,position,type,content) VALUES (?,?,?,?)",
                         (doc_id, i, _norm_type(b.get("type", "paragraph")), b.get("content", "")))
    return doc_id


def create_blank_doc(folder_id=None, title="Untitled document") -> int:
    return create_document(folder_id, title, [
        {"type": "heading1", "content": title},
        {"type": "paragraph", "content": "Start writing here…"},
    ])


def rename_document(doc_id, title):
    title = (title or "").strip() or "Untitled document"
    with cursor() as conn:
        conn.execute("UPDATE documents SET title=?, updated=datetime('now') WHERE id=?", (title, doc_id))


def move_document(doc_id, folder_id):
    """folder_id may be None (loose) or an int."""
    with cursor() as conn:
        conn.execute("UPDATE documents SET folder_id=?, updated=datetime('now') WHERE id=?", (folder_id, doc_id))


def delete_document(doc_id):
    with cursor() as conn:
        conn.execute("DELETE FROM documents WHERE id=?", (doc_id,))


def touch(doc_id):
    with cursor() as conn:
        conn.execute("UPDATE documents SET updated=datetime('now') WHERE id=?", (doc_id,))


# --- block writes -----------------------------------------------------------

def add_block(doc_id, after_bid=None, btype="paragraph", content="") -> int:
    """Insert a block after `after_bid` (or at the end). Returns the new id."""
    with cursor() as conn:
        if after_bid:
            pos = conn.execute("SELECT position FROM blocks WHERE id=?", (after_bid,)).fetchone()
            at = (pos[0] + 1) if pos else 999
        else:
            at = conn.execute("SELECT COALESCE(MAX(position),-1)+1 FROM blocks WHERE document_id=?", (doc_id,)).fetchone()[0]
        conn.execute("UPDATE blocks SET position = position + 1 WHERE document_id=? AND position >= ?", (doc_id, at))
        conn.execute("INSERT INTO blocks(document_id,position,type,content) VALUES (?,?,?,?)",
                     (doc_id, at, _norm_type(btype), content))
        nbid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("UPDATE documents SET updated=datetime('now') WHERE id=?", (doc_id,))
        return nbid


def update_block(bid, content, btype=None):
    b = block(bid)
    if not b:
        return None
    with cursor() as conn:
        if btype is not None:
            conn.execute("UPDATE blocks SET content=?, type=? WHERE id=?", (content, _norm_type(btype), bid))
        else:
            conn.execute("UPDATE blocks SET content=? WHERE id=?", (content, bid))
        conn.execute("UPDATE documents SET updated=datetime('now') WHERE id=?", (b["document_id"],))
    return b["document_id"]


def delete_block(bid) -> int | None:
    b = block(bid)
    if not b:
        return None
    doc_id = b["document_id"]
    with cursor() as conn:
        conn.execute("DELETE FROM blocks WHERE id=?", (bid,))
        for i, r in enumerate(conn.execute("SELECT id FROM blocks WHERE document_id=? ORDER BY position, id", (doc_id,)).fetchall()):
            conn.execute("UPDATE blocks SET position=? WHERE id=?", (i, r[0]))
        conn.execute("UPDATE documents SET updated=datetime('now') WHERE id=?", (doc_id,))
    return doc_id


def move_block(bid, direction) -> int | None:
    """direction: -1 up, +1 down. Swaps with the neighbour."""
    b = block(bid)
    if not b:
        return None
    doc_id = b["document_id"]
    ordered = rows("SELECT id, position FROM blocks WHERE document_id=? ORDER BY position, id", (doc_id,))
    idx = next((i for i, r in enumerate(ordered) if r["id"] == bid), None)
    if idx is None:
        return doc_id
    j = idx + direction
    if j < 0 or j >= len(ordered):
        return doc_id
    a, c = ordered[idx], ordered[j]
    with cursor() as conn:
        conn.execute("UPDATE blocks SET position=? WHERE id=?", (c["position"], a["id"]))
        conn.execute("UPDATE blocks SET position=? WHERE id=?", (a["position"], c["id"]))
        conn.execute("UPDATE documents SET updated=datetime('now') WHERE id=?", (doc_id,))
    return doc_id


# --- templates --------------------------------------------------------------

def templates():
    return rows("""SELECT t.*, (SELECT COUNT(*) FROM template_blocks tb WHERE tb.template_id=t.id) n
                   FROM templates t ORDER BY t.id""")


def template(tid):
    return one("SELECT * FROM templates WHERE id=?", (tid,))


def template_blocks(tid):
    return rows("SELECT * FROM template_blocks WHERE template_id=? ORDER BY position, id", (tid,))


def create_template(title, description, block_list) -> int:
    with cursor() as conn:
        conn.execute("INSERT INTO templates(title,description) VALUES (?,?)", (title, description))
        tid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        for i, b in enumerate(block_list):
            conn.execute("INSERT INTO template_blocks(template_id,position,type,content) VALUES (?,?,?,?)",
                         (tid, i, _norm_type(b.get("type", "paragraph")), b.get("content", "")))
    return tid


def create_doc_from_template(tid, folder_id=None) -> int | None:
    t = template(tid)
    if not t:
        return None
    blks = [{"type": b["type"], "content": b["content"]} for b in template_blocks(tid)]
    if not blks:
        blks = [{"type": "heading1", "content": t["title"]}]
    return create_document(folder_id, t["title"], blks)


# --- versions ---------------------------------------------------------------

def snapshot_version(doc_id, manual=True) -> int | None:
    d = document(doc_id)
    if not d:
        return None
    snap = json.dumps([{"type": b["type"], "content": b["content"]} for b in blocks(doc_id)])
    with cursor() as conn:
        conn.execute("INSERT INTO doc_versions(document_id,title,snapshot,manual,created) VALUES (?,?,?,?,datetime('now'))",
                     (doc_id, d["title"], snap, 1 if manual else 0))
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def versions(doc_id):
    return rows("SELECT id, title, manual, created FROM doc_versions WHERE document_id=? ORDER BY id DESC", (doc_id,))


def version(vid):
    return one("SELECT * FROM doc_versions WHERE id=?", (vid,))


def restore_version(vid) -> int | None:
    v = version(vid)
    if not v:
        return None
    doc_id = v["document_id"]
    # snapshot current state first so a restore is itself undoable
    snapshot_version(doc_id, manual=False)
    blks = json.loads(v["snapshot"])
    with cursor() as conn:
        conn.execute("DELETE FROM blocks WHERE document_id=?", (doc_id,))
        for i, b in enumerate(blks):
            conn.execute("INSERT INTO blocks(document_id,position,type,content) VALUES (?,?,?,?)",
                         (doc_id, i, _norm_type(b.get("type", "paragraph")), b.get("content", "")))
        if v["title"]:
            conn.execute("UPDATE documents SET title=? WHERE id=?", (v["title"], doc_id))
        conn.execute("UPDATE documents SET updated=datetime('now') WHERE id=?", (doc_id,))
    return doc_id


# --- publishing -------------------------------------------------------------

def publish(doc_id) -> str | None:
    d = document(doc_id)
    if not d:
        return None
    token = d.get("public_token") or secrets.token_urlsafe(9)
    with cursor() as conn:
        conn.execute("UPDATE documents SET public_token=? WHERE id=?", (token, doc_id))
    return token


def unpublish(doc_id):
    with cursor() as conn:
        conn.execute("UPDATE documents SET public_token=NULL WHERE id=?", (doc_id,))
