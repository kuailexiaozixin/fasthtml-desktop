"""Prompt version helpers — SQLite audit trail for system prompts.

Rows already arrive as dict-like objects from the shim in ``db/__init__.py``,
so there is no ``row_factory`` to configure. Timestamps are stored as ISO-8601
text by SQLite, so they are passed through as-is instead of being formatted.
"""

from __future__ import annotations

from db import connect


def save_prompt_version(slug: str, content: str, changed_by: str = "web-editor") -> int:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO prompt_versions (slug, content, changed_by) "
            "VALUES (%s, %s, %s) RETURNING id",
            (slug, content, changed_by),
        )
        row = cur.fetchone()
        conn.commit()
        return row[0]


def count_prompt_versions(slug: str) -> int:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) FROM prompt_versions WHERE slug = %s", (slug,)
        )
        return cur.fetchone()[0]


def get_prompt_versions(slug: str, limit: int = 50) -> list[dict]:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS total FROM prompt_versions WHERE slug = %s",
            (slug,),
        )
        total = cur.fetchone()["total"]

        cur.execute(
            "SELECT id, slug, content, changed_by, created_at "
            "FROM prompt_versions WHERE slug = %s ORDER BY id DESC LIMIT %s",
            (slug, limit),
        )
        rows = cur.fetchall()

        versions = []
        for i, r in enumerate(rows):
            versions.append({
                "id": r["id"],
                "version": total - i,
                "slug": r["slug"],
                "preview": r["content"][:200],
                "changed_by": r["changed_by"] or "",
                "created_at": str(r["created_at"] or ""),
            })
        return versions


def get_prompt_version(version_id: int) -> dict | None:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT id, slug, content, changed_by, created_at "
            "FROM prompt_versions WHERE id = %s",
            (version_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "slug": row["slug"],
            "content": row["content"],
            "changed_by": row["changed_by"] or "",
            "created_at": str(row["created_at"] or ""),
        }
