from pathlib import Path


_lines = (Path(__file__).resolve().parent.parent / "VERSION").read_text().splitlines()
VERSION = _lines[0].strip()
RELEASE_DATE = _lines[1].strip() if len(_lines) > 1 else "unknown"
