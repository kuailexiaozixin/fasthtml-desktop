#!/usr/bin/env python3
"""Increment FastWiki's SemVer and stamp its ISO release date."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VERSION_FILE = ROOT / "VERSION"


def read_release(path: Path = VERSION_FILE) -> tuple[tuple[int, int, int], str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ValueError(f"VERSION cannot be read: {exc}") from exc
    if len(lines) != 2:
        raise ValueError("VERSION must contain exactly a SemVer line and an ISO date line")
    parts = lines[0].strip().split(".")
    if len(parts) != 3 or not all(part.isdigit() for part in parts):
        raise ValueError(f"VERSION must start with MAJOR.MINOR.PATCH, got {lines[0]!r}")
    try:
        date.fromisoformat(lines[1].strip())
    except ValueError as exc:
        raise ValueError(f"VERSION release date must be YYYY-MM-DD, got {lines[1]!r}") from exc
    return tuple(map(int, parts)), lines[1].strip()  # type: ignore[return-value]


def bump(current: tuple[int, int, int], level: str) -> tuple[int, int, int]:
    major, minor, patch = current
    if level == "major":
        return major + 1, 0, 0
    if level == "minor":
        return major, minor + 1, 0
    return major, minor, patch + 1


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("level", nargs="?", choices=("major", "minor", "patch"))
    parser.add_argument("--check", action="store_true", help="validate VERSION without changing it")
    args = parser.parse_args()

    try:
        current, release_date = read_release()
    except ValueError as exc:
        raise SystemExit(str(exc)) from None
    current_text = ".".join(map(str, current))
    if args.check:
        print(f"FastWiki v{current_text} ({release_date})")
        return
    if not args.level:
        parser.error("level is required unless --check is used")

    new = bump(current, args.level)
    new_text = ".".join(map(str, new))
    new_date = date.today().isoformat()
    VERSION_FILE.write_text(f"{new_text}\n{new_date}\n", encoding="utf-8")
    print(f"FastWiki {current_text} ({release_date}) -> {new_text} ({new_date})")


if __name__ == "__main__":
    main()
