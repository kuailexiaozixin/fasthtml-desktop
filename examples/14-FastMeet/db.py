"""FastMeet data layer — SQLite meetings + participants.

Frappe Meet is a WebRTC video app; server-rendered HTML can't carry live video,
so FastMeet demonstrates the **scheduling & rooms** half: meetings, participants,
agendas, recordings (metadata), and a lobby. All synthetic.
"""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = os.getenv("FASTMEET_DB") or str(Path(__file__).parent / "fastmeet.sqlite")
NOW = datetime(2026, 6, 12, 12, 0, 0)
HOST = "you@fastmeet.example"

STATUSES = ["Scheduled", "Live", "Ended", "Cancelled"]
RSVPS = ["Accepted", "Tentative", "Declined", "No response"]


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
CREATE TABLE IF NOT EXISTS meetings (
    id            INTEGER PRIMARY KEY,
    title         TEXT NOT NULL,
    host          TEXT,
    start_time    TEXT NOT NULL,
    duration_min  INTEGER NOT NULL DEFAULT 30,
    status        TEXT NOT NULL DEFAULT 'Scheduled',
    room_code     TEXT,
    agenda        TEXT,
    has_recording INTEGER NOT NULL DEFAULT 0,
    summary       TEXT
);
CREATE TABLE IF NOT EXISTS participants (
    id            INTEGER PRIMARY KEY,
    meeting_id    INTEGER REFERENCES meetings(id) ON DELETE CASCADE,
    name          TEXT,
    email         TEXT,
    role          TEXT DEFAULT 'Attendee',
    rsvp          TEXT DEFAULT 'No response'
);
CREATE TABLE IF NOT EXISTS chat_messages (
    id            INTEGER PRIMARY KEY,
    thread_id     TEXT NOT NULL,
    role          TEXT NOT NULL,
    content       TEXT NOT NULL,
    created       TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_part_meeting ON participants(meeting_id);
CREATE INDEX IF NOT EXISTS idx_meet_start ON meetings(start_time);
"""


def init_schema():
    with cursor() as conn:
        conn.executescript(SCHEMA)


def meetings(scope="all"):
    now = NOW.strftime("%Y-%m-%d %H:%M:%S")
    if scope == "upcoming":
        return rows("SELECT * FROM meetings WHERE start_time>=? AND status!='Cancelled' ORDER BY start_time", (now,))
    if scope == "past":
        return rows("SELECT * FROM meetings WHERE start_time<? OR status='Ended' ORDER BY start_time DESC", (now,))
    return rows("SELECT * FROM meetings ORDER BY start_time DESC")


def meeting(mid):
    return one("SELECT * FROM meetings WHERE id=?", (mid,))


def participants(mid):
    return rows("SELECT * FROM participants WHERE meeting_id=? ORDER BY (role!='Host'), name", (mid,))


def stats():
    now = NOW.strftime("%Y-%m-%d %H:%M:%S")
    today = NOW.strftime("%Y-%m-%d")
    return {
        "upcoming": scalar("SELECT COUNT(*) FROM meetings WHERE start_time>=? AND status!='Cancelled'", (now,)) or 0,
        "today": scalar("SELECT COUNT(*) FROM meetings WHERE start_time LIKE ? AND status!='Cancelled'", (today + "%",)) or 0,
        "live": scalar("SELECT COUNT(*) FROM meetings WHERE status='Live'") or 0,
        "recordings": scalar("SELECT COUNT(*) FROM meetings WHERE has_recording=1") or 0,
        "total": scalar("SELECT COUNT(*) FROM meetings") or 0,
    }


def set_rsvp(participant_id: int, rsvp: str):
    if rsvp not in RSVPS:
        return None
    with cursor() as conn:
        conn.execute("UPDATE participants SET rsvp=? WHERE id=?", (rsvp, participant_id))
        r = conn.execute("SELECT meeting_id FROM participants WHERE id=?", (participant_id,)).fetchone()
        return r[0] if r else None


def rsvp_tally(mid: int) -> dict:
    out = {s: 0 for s in RSVPS}
    for r in rows("SELECT rsvp, COUNT(*) n FROM participants WHERE meeting_id=? AND role!='Host' GROUP BY rsvp", (mid,)):
        out[r["rsvp"]] = r["n"]
    return out
