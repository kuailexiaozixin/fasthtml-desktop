"""FastSlides data layer — SQLite presentations + slides."""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = os.getenv("FASTSLIDES_DB") or str(Path(__file__).parent / "fastslides.sqlite")

THEMES = ["midnight", "coral", "forest", "mono"]
THEME_BG = {"midnight": "#0f172a", "coral": "#db2777", "forest": "#065f46", "mono": "#1f2937"}


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
CREATE TABLE IF NOT EXISTS presentations (
    id            INTEGER PRIMARY KEY,
    title         TEXT NOT NULL,
    subtitle      TEXT,
    theme         TEXT NOT NULL DEFAULT 'midnight',
    created       TEXT
);
CREATE TABLE IF NOT EXISTS slides (
    id            INTEGER PRIMARY KEY,
    presentation_id INTEGER REFERENCES presentations(id) ON DELETE CASCADE,
    position      INTEGER NOT NULL DEFAULT 0,
    title         TEXT,
    body          TEXT,            -- markdown / bullet lines
    layout        TEXT NOT NULL DEFAULT 'content'   -- title | content | section
);
CREATE TABLE IF NOT EXISTS chat_messages (
    id            INTEGER PRIMARY KEY,
    thread_id     TEXT NOT NULL,
    role          TEXT NOT NULL,
    content       TEXT NOT NULL,
    created       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_slide_pres ON slides(presentation_id, position);
"""


def init_schema():
    with cursor() as conn:
        conn.executescript(SCHEMA)


def presentations():
    return rows("""SELECT p.*, (SELECT COUNT(*) FROM slides s WHERE s.presentation_id=p.id) n
                   FROM presentations p ORDER BY p.id DESC""")


def presentation(pid):
    return one("SELECT * FROM presentations WHERE id=?", (pid,))


def slides(pid):
    return rows("SELECT * FROM slides WHERE presentation_id=? ORDER BY position, id", (pid,))


def slide(sid):
    return one("SELECT * FROM slides WHERE id=?", (sid,))


def create_presentation(title, subtitle, theme, slide_list):
    """slide_list: [{title, body, layout}]. Returns new presentation id."""
    with cursor() as conn:
        conn.execute("INSERT INTO presentations(title,subtitle,theme,created) VALUES (?,?,?,datetime('now'))",
                     (title, subtitle, theme if theme in THEMES else "midnight"))
        pid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        for i, s in enumerate(slide_list):
            conn.execute("INSERT INTO slides(presentation_id,position,title,body,layout) VALUES (?,?,?,?,?)",
                         (pid, i, s.get("title", ""), s.get("body", ""), s.get("layout", "content")))
    return pid


# --- slide CRUD -------------------------------------------------------------

def add_slide(pid: int, after_sid=None) -> int:
    """Insert a blank slide after `after_sid` (or at the end). Returns new id."""
    with cursor() as conn:
        if after_sid:
            pos = conn.execute("SELECT position FROM slides WHERE id=?", (after_sid,)).fetchone()
            at = (pos[0] + 1) if pos else 999
        else:
            at = (conn.execute("SELECT COALESCE(MAX(position),-1)+1 FROM slides WHERE presentation_id=?", (pid,)).fetchone()[0])
        conn.execute("UPDATE slides SET position = position + 1 WHERE presentation_id=? AND position >= ?", (pid, at))
        conn.execute("INSERT INTO slides(presentation_id,position,title,body,layout) VALUES (?,?,?,?,'content')",
                     (pid, at, "New slide", "- Point one\n- Point two"))
        return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def delete_slide(sid: int) -> int | None:
    """Delete a slide, returning the presentation id (and re-packing positions)."""
    s = slide(sid)
    if not s:
        return None
    pid = s["presentation_id"]
    with cursor() as conn:
        conn.execute("DELETE FROM slides WHERE id=?", (sid,))
        # re-pack positions
        for i, r in enumerate(conn.execute("SELECT id FROM slides WHERE presentation_id=? ORDER BY position, id", (pid,)).fetchall()):
            conn.execute("UPDATE slides SET position=? WHERE id=?", (i, r[0]))
    return pid


def move_slide(sid: int, direction: int):
    """direction: -1 up, +1 down. Swaps positions with the neighbour."""
    s = slide(sid)
    if not s:
        return None
    pid = s["presentation_id"]
    ordered = rows("SELECT id, position FROM slides WHERE presentation_id=? ORDER BY position, id", (pid,))
    idx = next((i for i, r in enumerate(ordered) if r["id"] == sid), None)
    j = idx + direction
    if idx is None or j < 0 or j >= len(ordered):
        return pid
    a, b = ordered[idx], ordered[j]
    with cursor() as conn:
        conn.execute("UPDATE slides SET position=? WHERE id=?", (b["position"], a["id"]))
        conn.execute("UPDATE slides SET position=? WHERE id=?", (a["position"], b["id"]))
    return pid


def create_blank_deck(title: str, theme: str = "midnight") -> int:
    title = (title or "Untitled deck").strip() or "Untitled deck"
    return create_presentation(title, "Synthetic demo deck", theme, [
        {"title": title, "body": "A new presentation", "layout": "title"},
        {"title": "First slide", "body": "- Start here\n- Add your points", "layout": "content"},
    ])
