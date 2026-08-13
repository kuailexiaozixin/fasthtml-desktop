"""Apply schema.sql + rag_schema.sql idempotently.

Usage:
    python -m db.migrate          # apply both
    python -m db.migrate --drop   # DANGER: drops every table first

Both files are multi-statement DDL scripts, so they go through
``executescript`` rather than the translating cursor — they are already written
in plain SQLite dialect.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from db import connect, db_path, vector_search_available
from utils.config import settings

log = logging.getLogger(__name__)

SCHEMA_FILES = [
    Path(__file__).with_name("schema.sql"),
    Path(__file__).with_name("rag_schema.sql"),
]


def _apply(sql: str) -> None:
    with connect() as conn:
        conn.executescript(sql)
        conn.commit()


def _render(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    return text.replace("{{EMBEDDING_DIM}}", str(settings().embedding_dim))


def _drop_everything() -> None:
    """SQLite has no schemas, so wipe every user table instead."""
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' "
            "AND name NOT LIKE 'sqlite_%'"
        )
        names = [r["name"] for r in cur.fetchall()]
        if not names:
            print("nothing to drop")
            return
        conn.raw.execute("PRAGMA foreign_keys=OFF")
        try:
            for name in names:
                cur.execute(f'DROP TABLE IF EXISTS "{name}"')
            conn.commit()
        finally:
            conn.raw.execute("PRAGMA foreign_keys=ON")
        print(f"dropped {len(names)} tables")


def _seed_prompt_versions() -> None:
    """Insert v1 rows for every prompt file if the table is empty."""
    prompts_dir = Path(__file__).resolve().parent.parent / "prompts"
    system_dir = prompts_dir / "system"
    shared_file = prompts_dir / "shared" / "cre_context.md"

    with connect() as conn, conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM prompt_versions")
        if cur.fetchone()[0] > 0:
            return

        seeded = 0
        for md in sorted(system_dir.glob("*.md")):
            cur.execute(
                "INSERT INTO prompt_versions (slug, content, changed_by) "
                "VALUES (%s, %s, %s)",
                (md.stem, md.read_text(encoding="utf-8"), "seed"),
            )
            seeded += 1

        if shared_file.exists():
            cur.execute(
                "INSERT INTO prompt_versions (slug, content, changed_by) "
                "VALUES (%s, %s, %s)",
                ("__shared__", shared_file.read_text(encoding="utf-8"), "seed"),
            )
            seeded += 1

        conn.commit()
        print(f"seeded {seeded} prompt versions")


def migrate(drop: bool = False) -> None:
    print(f"database: {db_path()}")
    if drop:
        _drop_everything()

    for f in SCHEMA_FILES:
        if f.name == "rag_schema.sql" and not vector_search_available():
            print("sqlite-vec unavailable — skipping the vector table in rag_schema.sql")
            _apply(_render(f).split("-- >>> VECTOR TABLE")[0])
            continue
        print(f"applying {f.name} (embedding_dim={settings().embedding_dim})")
        _apply(_render(f))

    _seed_prompt_versions()
    print("migration complete")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--drop", action="store_true", help="drop every table first")
    args = ap.parse_args()
    migrate(drop=args.drop)
