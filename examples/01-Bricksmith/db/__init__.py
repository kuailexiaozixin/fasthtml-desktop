"""SQLite data layer with a PostgreSQL-compatibility shim.

Upstream Bricksmith targets PostgreSQL (psycopg + pgvector). This desktop
example ships a zero-setup, fully offline stack instead:

* storage        -> one SQLite file (``data/bricksmith.db`` by default)
* vector search  -> the ``sqlite-vec`` extension (``vec0`` virtual tables)

Rather than rewriting the ~20 call sites that already speak PostgreSQL, every
cursor handed out here rewrites the SQL it receives on the fly:

===========================  ==========================================
PostgreSQL                   SQLite
===========================  ==========================================
``bricksmith.properties``    ``properties``      (SQLite has no schemas)
``bricksmith_rag.chunks``    ``chunks``
``%s`` / ``%(name)s``        ``?``               (ordered by appearance)
``now()``                    ``CURRENT_TIMESTAMP``
``x::jsonb`` ``y::date`` ...  ``x`` ``y``        (casts dropped)
``now() - (%s||' days')::interval``  ``date('now','-'||?||' days')``
``ILIKE``                    ``LIKE``            (already case-insensitive)
``... NULLS LAST``           ``...``             (same default ordering)
``a IS NOT DISTINCT FROM b`` ``a IS b``          (NULL-safe comparison)
``TRUNCATE TABLE t ...``     ``DELETE FROM t``
===========================  ==========================================

Two more things psycopg did for free and we reproduce here:

* rows behave like ``dict`` *and* like tuples (``row["id"]`` / ``row[0]``);
* ``JSONB`` columns come back as real Python objects, not raw strings.
"""

from __future__ import annotations

import json
import logging
import re
import sqlite3
import threading
from collections import namedtuple
from contextlib import contextmanager
from datetime import date, datetime
from decimal import Decimal
from functools import lru_cache
from pathlib import Path

from utils.config import settings

log = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_RELPATH = "data/bricksmith.db"

# Columns declared JSONB upstream. psycopg deserialised those automatically;
# SQLite stores them as TEXT, so we decode them on the way out.
JSON_COLUMNS = frozenset({
    "tool_calls", "units", "opex", "escalations", "options",
    "assumptions", "projections", "returns", "tranches",
    "metadata", "filters",
    "tools_used",  # `TEXT[]` upstream, stored as a JSON array here
})

# ---------------------------------------------------------------------------
# SQL translation
# ---------------------------------------------------------------------------

_PCT_SENTINEL = "\x00__pct__\x00"

# `now() - (%s || ' days')::interval` has no direct SQLite equivalent, so it is
# rewritten before the generic `now()` / cast rules get a chance to mangle it.
_INTERVAL_DAYS_RE = re.compile(
    r"\bnow\s*\(\s*\)\s*-\s*\(\s*%s\s*\|\|\s*'\s*days\s*'\s*\)\s*::\s*interval",
    re.I,
)
_TRUNCATE_RE = re.compile(
    r"\bTRUNCATE\s+(?:TABLE\s+)?([A-Za-z0-9_.\"]+)"
    r"(?:\s+RESTART\s+IDENTITY)?(?:\s+CASCADE)?",
    re.I,
)
_SCHEMA_RE = re.compile(r"\b(?:bricksmith_rag|bricksmith)\s*\.", re.I)
_CAST_RE = re.compile(
    r"::\s*[A-Za-z_][A-Za-z0-9_]*(?:\s*\(\s*\d+(?:\s*,\s*\d+)?\s*\))?"
)
_NOW_RE = re.compile(r"\bnow\s*\(\s*\)", re.I)
_ILIKE_RE = re.compile(r"\bILIKE\b", re.I)
_NULLS_ORDER_RE = re.compile(r"\s+NULLS\s+(?:FIRST|LAST)\b", re.I)
_NOT_DISTINCT_RE = re.compile(r"\bIS\s+NOT\s+DISTINCT\s+FROM\b", re.I)
_DISTINCT_RE = re.compile(r"\bIS\s+DISTINCT\s+FROM\b", re.I)
_NAMED_PARAM_RE = re.compile(r"%\(([A-Za-z_][A-Za-z0-9_]*)\)s")


def translate_sql(sql: str) -> str:
    """Rewrite PostgreSQL-flavoured SQL to SQLite (placeholders untouched)."""
    sql = _INTERVAL_DAYS_RE.sub("date('now', '-' || %s || ' days')", sql)
    sql = _TRUNCATE_RE.sub(lambda m: f"DELETE FROM {m.group(1)}", sql)
    sql = _SCHEMA_RE.sub("", sql)
    sql = _CAST_RE.sub("", sql)
    sql = _NOW_RE.sub("CURRENT_TIMESTAMP", sql)
    sql = _ILIKE_RE.sub("LIKE", sql)
    sql = _NULLS_ORDER_RE.sub("", sql)
    # SQLite's `IS` / `IS NOT` are already NULL-safe, so they are exact
    # replacements for PostgreSQL's verbose spelling.
    sql = _NOT_DISTINCT_RE.sub("IS", sql)
    sql = _DISTINCT_RE.sub("IS NOT", sql)
    return sql


def _adapt(value):
    """Bind Python values sqlite3 refuses to take on its own."""
    if value is None or isinstance(value, (str, int, float, bytes, bytearray)):
        return value
    if isinstance(value, memoryview):
        return bytes(value)
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat(sep=" ") if isinstance(value, datetime) else value.isoformat()
    if isinstance(value, (dict, list)):
        return json.dumps(value, default=str)
    item = getattr(value, "item", None)  # numpy scalars
    if callable(item):
        try:
            return item()
        except Exception:  # pragma: no cover - defensive
            pass
    return value


def prepare(sql: str, params=None) -> tuple[str, tuple]:
    """Translate SQL + convert psycopg placeholders/params to sqlite3 form."""
    sql = sql.replace("%%", _PCT_SENTINEL)
    sql = translate_sql(sql)

    if isinstance(params, dict):
        order: list[str] = []

        def _collect(match: re.Match) -> str:
            order.append(match.group(1))
            return "?"

        sql = _NAMED_PARAM_RE.sub(_collect, sql)
        sql = sql.replace("%s", "?")
        bound = tuple(_adapt(params[name]) for name in order)
    else:
        sql = _NAMED_PARAM_RE.sub("?", sql)
        sql = sql.replace("%s", "?")
        bound = tuple(_adapt(v) for v in (params or ()))

    return sql.replace(_PCT_SENTINEL, "%"), bound


# ---------------------------------------------------------------------------
# Rows / cursors
# ---------------------------------------------------------------------------

Column = namedtuple(
    "Column",
    "name type_code display_size internal_size precision scale null_ok",
)


class Row(dict):
    """A dict row that also answers positional lookups, like psycopg's."""

    __slots__ = ()

    def __getitem__(self, key):
        if isinstance(key, int):
            try:
                return list(self.values())[key]
            except IndexError:
                raise IndexError(key) from None
        return dict.__getitem__(self, key)


def _build_row(columns: list[str], values) -> Row:
    row = Row()
    for name, value in zip(columns, values):
        if name in JSON_COLUMNS and isinstance(value, str):
            try:
                value = json.loads(value)
            except (TypeError, ValueError):
                pass
        row[name] = value
    return row


class ShimCursor:
    """DB-API cursor that speaks PostgreSQL in and SQLite out."""

    def __init__(self, cursor: sqlite3.Cursor):
        self._cur = cursor

    # psycopg cursors are context managers; sqlite3 cursors are not.
    def __enter__(self) -> "ShimCursor":
        return self

    def __exit__(self, *_exc) -> bool:
        self.close()
        return False

    def __iter__(self):
        columns = self._columns()
        for values in self._cur:
            yield _build_row(columns, values)

    @property
    def description(self):
        raw = self._cur.description
        if not raw:
            return raw
        return [Column(c[0], *c[1:]) for c in raw]

    @property
    def rowcount(self) -> int:
        return self._cur.rowcount

    @property
    def lastrowid(self):
        return self._cur.lastrowid

    def _columns(self) -> list[str]:
        raw = self._cur.description
        return [c[0] for c in raw] if raw else []

    def execute(self, sql: str, params=None) -> "ShimCursor":
        stmt, bound = prepare(sql, params)
        try:
            self._cur.execute(stmt, bound)
        except sqlite3.Error as exc:
            raise sqlite3.Error(f"{exc}\n--- translated SQL ---\n{stmt}") from exc
        return self

    def executemany(self, sql: str, seq_of_params) -> "ShimCursor":
        rows = list(seq_of_params)
        if not rows:
            return self
        stmt, _ = prepare(sql, rows[0])
        self._cur.executemany(stmt, [prepare(sql, r)[1] for r in rows])
        return self

    def executescript(self, script: str) -> "ShimCursor":
        self._cur.executescript(script)
        return self

    def fetchone(self):
        values = self._cur.fetchone()
        return _build_row(self._columns(), values) if values is not None else None

    def fetchall(self) -> list[Row]:
        columns = self._columns()
        return [_build_row(columns, v) for v in self._cur.fetchall()]

    def fetchall_tuples(self) -> list[tuple]:
        """Positional rows, bypassing the dict wrapper.

        Useful for pandas: a query that selects two columns with the same name
        (``SELECT p.id, t.id ...``) would collapse into a single key on a dict
        row, silently losing a column.
        """
        return [tuple(v) for v in self._cur.fetchall()]

    def fetchmany(self, size: int | None = None) -> list[Row]:
        columns = self._columns()
        values = self._cur.fetchmany(size) if size is not None else self._cur.fetchmany()
        return [_build_row(columns, v) for v in values]

    def close(self) -> None:
        try:
            self._cur.close()
        except sqlite3.Error:
            pass


class ShimConnection:
    """Thin wrapper so `conn.cursor(row_factory=...)` keeps working."""

    def __init__(self, raw: sqlite3.Connection):
        self._raw = raw

    @property
    def raw(self) -> sqlite3.Connection:
        return self._raw

    def cursor(self, *_args, **_kwargs) -> ShimCursor:
        # `row_factory=...` is accepted and ignored: every row is already a
        # dict-like `Row`.
        return ShimCursor(self._raw.cursor())

    def execute(self, sql: str, params=None) -> ShimCursor:
        cur = self.cursor()
        cur.execute(sql, params)
        return cur

    def executescript(self, script: str):
        return self._raw.executescript(script)

    def commit(self) -> None:
        self._raw.commit()

    def rollback(self) -> None:
        self._raw.rollback()

    def close(self) -> None:
        self._raw.close()

    def __getattr__(self, name):
        return getattr(self._raw, name)


# ---------------------------------------------------------------------------
# Connection management
# ---------------------------------------------------------------------------

_local = threading.local()
_vec_loaded: bool | None = None


def db_path() -> Path:
    """Resolve `DB_URL` to a SQLite file path, creating its folder."""
    raw = (settings().db_url or "").strip()
    if raw.startswith(("postgres://", "postgresql://")):
        # A leftover upstream Postgres URL — fall back to the local file so a
        # stale .env never blocks startup.
        log.warning("DB_URL points at PostgreSQL; using local SQLite file instead.")
        raw = ""
    for prefix in ("sqlite+pysqlite:///", "sqlite:///", "sqlite://"):
        if raw.lower().startswith(prefix):
            raw = raw[len(prefix):]
            break
    path = Path(raw or DEFAULT_DB_RELPATH).expanduser()
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _load_sqlite_vec(conn: sqlite3.Connection) -> bool:
    """Load the sqlite-vec extension; returns False when unavailable."""
    try:
        import sqlite_vec
    except ImportError:
        log.warning("sqlite-vec is not installed — vector search is disabled.")
        return False
    try:
        conn.enable_load_extension(True)
    except AttributeError:
        log.warning("This Python's sqlite3 was built without extension support.")
        return False
    try:
        sqlite_vec.load(conn)
        return True
    except Exception as exc:  # pragma: no cover - platform specific
        log.warning("Could not load sqlite-vec: %s", exc)
        return False
    finally:
        try:
            conn.enable_load_extension(False)
        except Exception:
            pass


def _open() -> ShimConnection:
    global _vec_loaded
    raw = sqlite3.connect(str(db_path()), check_same_thread=False, timeout=30.0)
    loaded = _load_sqlite_vec(raw)
    if _vec_loaded is None:
        _vec_loaded = loaded
    for pragma in (
        "PRAGMA journal_mode=WAL",
        "PRAGMA synchronous=NORMAL",
        "PRAGMA busy_timeout=30000",
        "PRAGMA foreign_keys=ON",
    ):
        raw.execute(pragma)
    return ShimConnection(raw)


def vector_search_available() -> bool:
    """True when sqlite-vec loaded successfully (RAG degrades without it)."""
    if _vec_loaded is None:
        with connect():
            pass
    return bool(_vec_loaded)


@contextmanager
def connect():
    """Yield a connection, committing on success and rolling back on error.

    Mirrors psycopg's pooled `with pool().connection()` semantics, including
    re-entrancy: a nested `connect()` joins the outer transaction instead of
    committing early.
    """
    depth = getattr(_local, "depth", 0)
    if depth == 0:
        if getattr(_local, "conn", None) is None:
            _local.conn = _open()
    _local.depth = depth + 1
    conn: ShimConnection = _local.conn
    try:
        yield conn
    except Exception:
        if _local.depth == 1:
            conn.rollback()
        raise
    else:
        if _local.depth == 1:
            conn.commit()
    finally:
        _local.depth -= 1


class _Pool:
    """Kept for API parity with the upstream psycopg ConnectionPool."""

    @contextmanager
    def connection(self):
        with connect() as conn:
            yield conn

    def close(self) -> None:
        conn = getattr(_local, "conn", None)
        if conn is not None:
            conn.close()
            _local.conn = None


@lru_cache(maxsize=1)
def pool() -> _Pool:
    return _Pool()


# ---------------------------------------------------------------------------
# Query helpers (same signatures as upstream)
# ---------------------------------------------------------------------------

def fetch_all(sql: str, params: tuple | dict | None = None) -> list[dict]:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(sql, params or ())
        return list(cur.fetchall())


def fetch_one(sql: str, params: tuple | dict | None = None) -> dict | None:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(sql, params or ())
        return cur.fetchone()


def execute(sql: str, params: tuple | dict | None = None) -> None:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(sql, params or ())
        conn.commit()


def reset_tables(tables: list[str]) -> None:
    """Wipe tables and restart their AUTOINCREMENT counters.

    Foreign keys are suspended for the duration so callers do not have to care
    about delete order (upstream relied on `TRUNCATE ... CASCADE`).
    """
    with connect() as conn:
        raw = conn.raw
        raw.execute("PRAGMA foreign_keys=OFF")
        try:
            cur = conn.cursor()
            has_seq = bool(cur.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='sqlite_sequence'"
            ).fetchone())
            for table in tables:
                name = _SCHEMA_RE.sub("", table).strip('"')
                cur.execute(f'DELETE FROM "{name}"')
                if has_seq:
                    cur.execute("DELETE FROM sqlite_sequence WHERE name = ?", (name,))
            cur.close()
            conn.commit()
        finally:
            raw.execute("PRAGMA foreign_keys=ON")
