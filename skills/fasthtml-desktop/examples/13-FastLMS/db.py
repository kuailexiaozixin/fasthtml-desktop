"""FastLMS database layer — SQLite via SQLAlchemy (offline-first).

Desktop-example note
--------------------
Upstream FastLMS targets PostgreSQL and keeps its tables in a dedicated
``fastlms`` schema.  For the offline desktop bundle we run on SQLite instead so
the example is double-click runnable with no database server.

The port is deliberately minimal: ``SCHEMA`` is re-pointed at SQLite's built-in
``main`` database alias, so every ``{S}.table`` reference across ``db.py``,
``school.py``, ``seed*.py``, ``main.py`` and ``components/api.py`` keeps working
verbatim.  Only the DDL (SERIAL/TIMESTAMPTZ/JSONB/schema-qualified REFERENCES)
and a handful of ``now()`` calls had to be translated.

Set ``DB_URL`` to a PostgreSQL URL to run against the upstream backend again;
in that case also set ``FASTLMS_SCHEMA=fastlms``.
"""

from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from functools import lru_cache
from pathlib import Path

import sqlalchemy as sa
from dotenv import load_dotenv
from sqlalchemy.engine import Engine

load_dotenv()

# SQLite exposes the primary database as "main"; Postgres deployments override
# this with FASTLMS_SCHEMA=fastlms.
SCHEMA = os.environ.get("FASTLMS_SCHEMA") or "main"

DATA_DIR = Path(os.environ.get("FASTLMS_DATA_DIR") or (Path(__file__).resolve().parent / "data"))


def default_sqlite_path() -> Path:
    """Resolve the on-disk SQLite file (FASTLMS_DB wins, else data/fastlms.sqlite)."""
    override = os.environ.get("FASTLMS_DB")
    path = Path(override) if override else (DATA_DIR / "fastlms.sqlite")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


_TYPES_REGISTERED = False


def _register_sqlite_types() -> None:
    """Teach sqlite3 about date/datetime so DATE/TIMESTAMP columns round-trip.

    Python 3.12 deprecated the implicit adapters, so register explicit ones and
    pair them with ``detect_types=PARSE_DECLTYPES`` on the connection.
    """
    global _TYPES_REGISTERED
    if _TYPES_REGISTERED:
        return
    sqlite3.register_adapter(date, lambda d: d.isoformat())
    sqlite3.register_adapter(datetime, lambda d: d.isoformat(sep=" "))

    def _to_date(raw: bytes):
        try:
            return date.fromisoformat(raw.decode()[:10])
        except ValueError:
            return raw.decode()

    def _to_datetime(raw: bytes):
        try:
            return datetime.fromisoformat(raw.decode())
        except ValueError:
            return raw.decode()

    sqlite3.register_converter("DATE", _to_date)
    sqlite3.register_converter("TIMESTAMP", _to_datetime)
    _TYPES_REGISTERED = True


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    url = os.environ.get("DB_URL")
    if not url:
        url = f"sqlite:///{default_sqlite_path()}"
    if url.startswith("sqlite"):
        _register_sqlite_types()
        return sa.create_engine(
            url,
            connect_args={"check_same_thread": False, "detect_types": sqlite3.PARSE_DECLTYPES},
        )
    return sa.create_engine(url, pool_pre_ping=True, pool_recycle=300)


@contextmanager
def connect():
    with get_engine().connect() as conn:
        yield conn


@contextmanager
def begin():
    with get_engine().begin() as conn:
        yield conn


# ---------------------------------------------------------------------------
# Schema bootstrap
# ---------------------------------------------------------------------------

SCHEMA_SQL = f"""
-- Users
CREATE TABLE IF NOT EXISTS {SCHEMA}.users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    email           TEXT UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    display_name    TEXT NOT NULL,
    role            TEXT NOT NULL DEFAULT 'student',  -- student | instructor | admin
    avatar_url      TEXT,
    xp              INTEGER NOT NULL DEFAULT 0,
    level           TEXT NOT NULL DEFAULT 'Novice',
    streak_days     INTEGER NOT NULL DEFAULT 0,
    streak_last     DATE,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Courses
CREATE TABLE IF NOT EXISTS {SCHEMA}.courses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    title           TEXT NOT NULL,
    slug            TEXT UNIQUE NOT NULL,
    description     TEXT,
    category        TEXT,
    difficulty      TEXT NOT NULL DEFAULT 'beginner',  -- beginner | intermediate | advanced
    thumbnail_url   TEXT,
    instructor_id   INTEGER REFERENCES users(id),
    is_published    BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Modules (sections within a course)
CREATE TABLE IF NOT EXISTS {SCHEMA}.modules (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id       INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title           TEXT NOT NULL,
    description     TEXT,
    order_idx       INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Lessons
CREATE TABLE IF NOT EXISTS {SCHEMA}.lessons (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    module_id       INTEGER NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
    title           TEXT NOT NULL,
    content_md      TEXT,
    content_type    TEXT NOT NULL DEFAULT 'text',  -- text | video | interactive
    video_url       TEXT,
    duration_min    INTEGER,
    xp_reward       INTEGER NOT NULL DEFAULT 25,
    order_idx       INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Quizzes (one per lesson, optional)
CREATE TABLE IF NOT EXISTS {SCHEMA}.quizzes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id       INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    title           TEXT NOT NULL,
    pass_threshold  INTEGER NOT NULL DEFAULT 70,  -- percent
    xp_reward       INTEGER NOT NULL DEFAULT 50,
    time_limit_min  INTEGER,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Quiz questions (options is a JSON array, stored as TEXT on SQLite)
CREATE TABLE IF NOT EXISTS {SCHEMA}.quiz_questions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id         INTEGER NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
    question_text   TEXT NOT NULL,
    question_type   TEXT NOT NULL DEFAULT 'multiple_choice',
    options         TEXT NOT NULL DEFAULT '[]',
    correct_answer  TEXT NOT NULL,
    explanation     TEXT,
    order_idx       INTEGER NOT NULL DEFAULT 0
);

-- Lesson progress
CREATE TABLE IF NOT EXISTS {SCHEMA}.lesson_progress (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lesson_id       INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    status          TEXT NOT NULL DEFAULT 'not_started',  -- not_started | in_progress | completed
    completed_at    TIMESTAMP,
    UNIQUE(user_id, lesson_id)
);

-- Quiz attempts
CREATE TABLE IF NOT EXISTS {SCHEMA}.quiz_attempts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    quiz_id         INTEGER NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
    score           INTEGER NOT NULL,
    passed          BOOLEAN NOT NULL,
    answers         TEXT NOT NULL DEFAULT '{{}}',
    started_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at    TIMESTAMP
);

-- Badges
CREATE TABLE IF NOT EXISTS {SCHEMA}.badges (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    slug            TEXT UNIQUE NOT NULL,
    name            TEXT NOT NULL,
    description     TEXT,
    icon            TEXT NOT NULL DEFAULT '🏅',
    criteria_type   TEXT NOT NULL,  -- lessons_completed | streak | quiz_score | xp_total | course_completed
    criteria_value  INTEGER NOT NULL DEFAULT 1
);

-- User badges
CREATE TABLE IF NOT EXISTS {SCHEMA}.user_badges (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    badge_id        INTEGER NOT NULL REFERENCES badges(id) ON DELETE CASCADE,
    earned_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, badge_id)
);

-- Course enrolments
CREATE TABLE IF NOT EXISTS {SCHEMA}.enrolments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    course_id       INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    enrolled_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, course_id)
);

-- Discussions (per-lesson threaded comments)
CREATE TABLE IF NOT EXISTS {SCHEMA}.discussions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    lesson_id       INTEGER NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    content         TEXT NOT NULL,
    parent_id       INTEGER REFERENCES discussions(id) ON DELETE CASCADE,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Chat messages (AI tutor per-lesson conversations)
CREATE TABLE IF NOT EXISTS {SCHEMA}.chat_messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    lesson_id       INTEGER REFERENCES lessons(id) ON DELETE SET NULL,
    role            TEXT NOT NULL,  -- user | assistant | system
    content         TEXT NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_lessons_module ON lessons(module_id, order_idx);
CREATE INDEX IF NOT EXISTS idx_modules_course ON modules(course_id, order_idx);
CREATE INDEX IF NOT EXISTS idx_progress_user ON lesson_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_user_lesson ON chat_messages(user_id, lesson_id);
CREATE INDEX IF NOT EXISTS idx_enrolments_user ON enrolments(user_id);
CREATE INDEX IF NOT EXISTS idx_discussions_lesson ON discussions(lesson_id);
"""


def bootstrap_schema():
    with begin() as conn:
        for stmt in SCHEMA_SQL.split(";"):
            stmt = stmt.strip()
            if stmt:
                conn.execute(sa.text(stmt))
        # school-administration layer (students/programs/gradebook/attendance/fees)
        import school
        school.bootstrap(conn)


def drop_all():
    """Drop every FastLMS table (SQLite replacement for ``DROP SCHEMA CASCADE``)."""
    with begin() as conn:
        rows = conn.execute(
            sa.text("SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'")
        ).scalars().all()
        for name in rows:
            conn.execute(sa.text(f'DROP TABLE IF EXISTS "{name}"'))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

S = SCHEMA  # shorthand for queries


def get_user(conn, user_id: int) -> dict | None:
    row = conn.execute(sa.text(f"SELECT * FROM {S}.users WHERE id = :id"), {"id": user_id}).mappings().first()
    return dict(row) if row else None


def get_user_by_email(conn, email: str) -> dict | None:
    row = conn.execute(sa.text(f"SELECT * FROM {S}.users WHERE email = :e"), {"e": email}).mappings().first()
    return dict(row) if row else None


def get_courses(conn, published_only=True) -> list[dict]:
    where = f"WHERE is_published = true" if published_only else ""
    rows = conn.execute(sa.text(f"SELECT * FROM {S}.courses {where} ORDER BY created_at DESC")).mappings().all()
    return [dict(r) for r in rows]


def get_course(conn, slug: str) -> dict | None:
    row = conn.execute(sa.text(f"SELECT * FROM {S}.courses WHERE slug = :s"), {"s": slug}).mappings().first()
    return dict(row) if row else None


def get_modules(conn, course_id: int) -> list[dict]:
    rows = conn.execute(
        sa.text(f"SELECT * FROM {S}.modules WHERE course_id = :c ORDER BY order_idx"),
        {"c": course_id},
    ).mappings().all()
    return [dict(r) for r in rows]


def get_lessons(conn, module_id: int) -> list[dict]:
    rows = conn.execute(
        sa.text(f"SELECT * FROM {S}.lessons WHERE module_id = :m ORDER BY order_idx"),
        {"m": module_id},
    ).mappings().all()
    return [dict(r) for r in rows]


def get_lesson(conn, lesson_id: int) -> dict | None:
    row = conn.execute(sa.text(f"SELECT * FROM {S}.lessons WHERE id = :id"), {"id": lesson_id}).mappings().first()
    return dict(row) if row else None


def get_quiz_for_lesson(conn, lesson_id: int) -> dict | None:
    row = conn.execute(
        sa.text(f"SELECT * FROM {S}.quizzes WHERE lesson_id = :l"), {"l": lesson_id}
    ).mappings().first()
    return dict(row) if row else None


def get_quiz_questions(conn, quiz_id: int) -> list[dict]:
    rows = conn.execute(
        sa.text(f"SELECT * FROM {S}.quiz_questions WHERE quiz_id = :q ORDER BY order_idx"),
        {"q": quiz_id},
    ).mappings().all()
    return [dict(r) for r in rows]


def get_lesson_progress(conn, user_id: int, lesson_id: int) -> dict | None:
    row = conn.execute(
        sa.text(f"SELECT * FROM {S}.lesson_progress WHERE user_id = :u AND lesson_id = :l"),
        {"u": user_id, "l": lesson_id},
    ).mappings().first()
    return dict(row) if row else None


def get_user_course_progress(conn, user_id: int, course_id: int) -> dict:
    """Return {total, completed, percent} for a user's progress in a course."""
    row = conn.execute(
        sa.text(f"""
            SELECT count(l.id) AS total,
                   count(lp.id) FILTER (WHERE lp.status = 'completed') AS completed
            FROM {S}.lessons l
            JOIN {S}.modules m ON m.id = l.module_id
            LEFT JOIN {S}.lesson_progress lp ON lp.lesson_id = l.id AND lp.user_id = :u
            WHERE m.course_id = :c
        """),
        {"u": user_id, "c": course_id},
    ).mappings().first()
    total = row["total"] or 0
    completed = row["completed"] or 0
    return {"total": total, "completed": completed, "percent": round(completed / total * 100) if total else 0}


def mark_lesson_complete(conn, user_id: int, lesson_id: int) -> int:
    """Mark lesson complete, award XP, update streak. Returns XP earned."""
    lesson = get_lesson(conn, lesson_id)
    xp = lesson["xp_reward"] if lesson else 25

    conn.execute(
        sa.text(f"""
            INSERT INTO {S}.lesson_progress (user_id, lesson_id, status, completed_at)
            VALUES (:u, :l, 'completed', CURRENT_TIMESTAMP)
            ON CONFLICT (user_id, lesson_id) DO UPDATE SET status = 'completed', completed_at = CURRENT_TIMESTAMP
        """),
        {"u": user_id, "l": lesson_id},
    )

    conn.execute(sa.text(f"UPDATE {S}.users SET xp = xp + :xp WHERE id = :u"), {"xp": xp, "u": user_id})
    _update_streak(conn, user_id)
    _update_level(conn, user_id)
    return xp


def _update_streak(conn, user_id: int):
    today = date.today()
    user = get_user(conn, user_id)
    if not user:
        return
    last = user["streak_last"]
    if last == today:
        return
    if last and (today - last).days == 1:
        conn.execute(
            sa.text(f"UPDATE {S}.users SET streak_days = streak_days + 1, streak_last = :d WHERE id = :u"),
            {"d": today, "u": user_id},
        )
    else:
        conn.execute(
            sa.text(f"UPDATE {S}.users SET streak_days = 1, streak_last = :d WHERE id = :u"),
            {"d": today, "u": user_id},
        )


LEVELS = [
    (0, "Novice"),
    (500, "Apprentice"),
    (2000, "Scholar"),
    (5000, "Expert"),
    (10000, "Master"),
    (25000, "Grandmaster"),
]


def _update_level(conn, user_id: int):
    user = get_user(conn, user_id)
    if not user:
        return
    xp = user["xp"]
    level = "Novice"
    for threshold, name in LEVELS:
        if xp >= threshold:
            level = name
    if level != user["level"]:
        conn.execute(sa.text(f"UPDATE {S}.users SET level = :l WHERE id = :u"), {"l": level, "u": user_id})


def get_leaderboard(conn, limit: int = 20) -> list[dict]:
    rows = conn.execute(
        sa.text(f"SELECT id, display_name, xp, level, streak_days FROM {S}.users ORDER BY xp DESC LIMIT :l"),
        {"l": limit},
    ).mappings().all()
    return [dict(r) for r in rows]


def get_user_badges(conn, user_id: int) -> list[dict]:
    rows = conn.execute(
        sa.text(f"""
            SELECT b.*, ub.earned_at FROM {S}.user_badges ub
            JOIN {S}.badges b ON b.id = ub.badge_id
            WHERE ub.user_id = :u ORDER BY ub.earned_at DESC
        """),
        {"u": user_id},
    ).mappings().all()
    return [dict(r) for r in rows]


def check_and_award_badges(conn, user_id: int) -> list[dict]:
    """Check badge criteria and award any newly earned badges. Returns newly awarded list."""
    user = get_user(conn, user_id)
    if not user:
        return []

    existing = {r["badge_id"] for r in conn.execute(
        sa.text(f"SELECT badge_id FROM {S}.user_badges WHERE user_id = :u"), {"u": user_id}
    ).mappings().all()}

    all_badges = conn.execute(sa.text(f"SELECT * FROM {S}.badges")).mappings().all()
    awarded = []

    for badge in all_badges:
        if badge["id"] in existing:
            continue

        earned = False
        ct, cv = badge["criteria_type"], badge["criteria_value"]

        if ct == "xp_total":
            earned = user["xp"] >= cv
        elif ct == "streak":
            earned = user["streak_days"] >= cv
        elif ct == "lessons_completed":
            cnt = conn.execute(
                sa.text(f"SELECT count(*) FROM {S}.lesson_progress WHERE user_id = :u AND status = 'completed'"),
                {"u": user_id},
            ).scalar()
            earned = cnt >= cv
        elif ct == "quiz_score":
            cnt = conn.execute(
                sa.text(f"SELECT count(*) FROM {S}.quiz_attempts WHERE user_id = :u AND score >= :v"),
                {"u": user_id, "v": cv},
            ).scalar()
            earned = cnt > 0
        elif ct == "course_completed":
            # check if any course is 100% complete
            enrolments = conn.execute(
                sa.text(f"SELECT course_id FROM {S}.enrolments WHERE user_id = :u"), {"u": user_id}
            ).mappings().all()
            for e in enrolments:
                prog = get_user_course_progress(conn, user_id, e["course_id"])
                if prog["percent"] == 100:
                    earned = True
                    break

        if earned:
            conn.execute(
                sa.text(f"INSERT INTO {S}.user_badges (user_id, badge_id) VALUES (:u, :b) ON CONFLICT DO NOTHING"),
                {"u": user_id, "b": badge["id"]},
            )
            awarded.append(dict(badge))

    return awarded


def get_discussions(conn, lesson_id: int) -> list[dict]:
    rows = conn.execute(
        sa.text(f"""
            SELECT d.*, u.display_name, u.avatar_url FROM {S}.discussions d
            JOIN {S}.users u ON u.id = d.user_id
            WHERE d.lesson_id = :l AND d.parent_id IS NULL
            ORDER BY d.created_at DESC
        """),
        {"l": lesson_id},
    ).mappings().all()
    return [dict(r) for r in rows]


def get_chat_history(conn, user_id: int, lesson_id: int | None, limit: int = 50) -> list[dict]:
    if lesson_id:
        rows = conn.execute(
            sa.text(f"""
                SELECT * FROM {S}.chat_messages
                WHERE user_id = :u AND lesson_id = :l
                ORDER BY created_at ASC LIMIT :lim
            """),
            {"u": user_id, "l": lesson_id, "lim": limit},
        ).mappings().all()
    else:
        rows = conn.execute(
            sa.text(f"""
                SELECT * FROM {S}.chat_messages
                WHERE user_id = :u AND lesson_id IS NULL
                ORDER BY created_at ASC LIMIT :lim
            """),
            {"u": user_id, "lim": limit},
        ).mappings().all()
    return [dict(r) for r in rows]
