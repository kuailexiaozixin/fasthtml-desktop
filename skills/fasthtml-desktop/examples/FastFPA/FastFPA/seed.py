"""Rebuild the deterministic FastFPA demonstration dataset."""
import db


def build() -> None:
    db.seed()


if __name__ == "__main__":
    build()
