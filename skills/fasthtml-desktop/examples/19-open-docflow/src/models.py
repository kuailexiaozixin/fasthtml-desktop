"""SQLAlchemy models for open-docflow (SQLite edition).

Upstream open-docflow targets PostgreSQL. This example runs fully offline, so
the data layer was ported to SQLite. Three dialect differences were handled:

1. ``JSONB``       -> ``sqlalchemy.JSON``  (serialised to a TEXT column)
2. ``schema=...``  -> dropped              (SQLite has no CREATE SCHEMA)
3. FK enforcement  -> ``PRAGMA foreign_keys=ON`` (off by default in SQLite)

Everything else — the ORM models, queries in ``src/workflow.py`` and ``app.py`` —
is unchanged from upstream.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    event,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker


class Base(DeclarativeBase):
    pass


class DocumentType(Base):
    __tablename__ = "document_types"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    required_fields = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    documents = relationship("Document", back_populates="doc_type_rel")

    def __repr__(self) -> str:
        return f"<DocumentType {self.name}>"


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    doc_type_id = Column(Integer, ForeignKey("document_types.id"))
    status = Column(String(50), nullable=False, default="gautas")
    uploaded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    file_path = Column(String(1000))
    file_size = Column(Integer)
    # NOTE: the DB column stays "metadata" (see sql/schema.sql), but the Python
    # attribute must not be called `metadata` — that name is reserved by
    # SQLAlchemy's declarative base for the MetaData instance and raises
    # InvalidRequestError at import time.
    doc_metadata = Column("metadata", JSON, default=dict)
    submitted_by = Column(String(200))
    assigned_to = Column(String(200))

    doc_type_rel = relationship("DocumentType", back_populates="documents")
    # passive_deletes lets the DB-level ON DELETE CASCADE do the work. Without
    # it the ORM first issues `UPDATE workflow_steps SET document_id=NULL`,
    # which violates the NOT NULL constraint.
    workflow_steps = relationship(
        "WorkflowStep",
        back_populates="document",
        order_by="WorkflowStep.created_at",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Document {self.id}: {self.title[:40]}>"

    @property
    def status_label(self) -> str:
        labels = {
            "gautas": "Gautas",
            "perziurimas": "Perziurimas",
            "patvirtintas": "Patvirtintas",
            "atmestas": "Atmestas",
        }
        return labels.get(self.status, self.status)

    @property
    def status_color(self) -> str:
        colors = {
            "gautas": "#3b82f6",
            "perziurimas": "#f59e0b",
            "patvirtintas": "#10b981",
            "atmestas": "#ef4444",
        }
        return colors.get(self.status, "#6b7280")


class WorkflowStep(Base):
    __tablename__ = "workflow_steps"

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    from_status = Column(String(50))
    to_status = Column(String(50), nullable=False)
    actor = Column(String(200), nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    document = relationship("Document", back_populates="workflow_steps")

    def __repr__(self) -> str:
        return f"<WorkflowStep {self.from_status} -> {self.to_status}>"


# --- Database connection (SQLite, offline-first) ---
#
# Resolution order:
#   1. explicit ``url`` argument
#   2. DOCFLOW_DATABASE_URL  — full SQLAlchemy URL
#   3. DOCFLOW_DB            — absolute path to the .sqlite file (set by desktop.py)
#   4. <project>/data/open-docflow.sqlite

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_DB_PATH = os.path.join(_PROJECT_ROOT, "data", "open-docflow.sqlite")


def resolve_database_url() -> str:
    """Return the effective SQLAlchemy URL, honouring the environment."""
    url = os.environ.get("DOCFLOW_DATABASE_URL")
    if url:
        return url
    db_path = os.path.abspath(os.environ.get("DOCFLOW_DB") or _DEFAULT_DB_PATH)
    parent = os.path.dirname(db_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    return f"sqlite:///{db_path}"


# Kept for backwards compatibility with upstream imports.
DATABASE_URL = resolve_database_url()

_ENGINES: dict[str, Engine] = {}


@event.listens_for(Engine, "connect")
def _sqlite_pragmas(dbapi_connection, connection_record):
    """SQLite disables FK enforcement by default — turn it on so the
    ``ON DELETE CASCADE`` on workflow_steps.document_id actually fires."""
    if type(dbapi_connection).__module__.split(".")[0] != "sqlite3":
        return
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
    finally:
        cursor.close()


def get_engine(url: str | None = None) -> Engine:
    """Return a cached engine. Upstream built a fresh engine per session, which
    on SQLite means a new connection pool for every request."""
    resolved = url or resolve_database_url()
    engine = _ENGINES.get(resolved)
    if engine is None:
        kwargs: dict = {"echo": False}
        if resolved.startswith("sqlite"):
            kwargs["connect_args"] = {"check_same_thread": False}
        engine = create_engine(resolved, **kwargs)
        _ENGINES[resolved] = engine
    return engine


def get_session(url: str | None = None) -> Session:
    engine = get_engine(url)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


# Mirrors the seed rows in sql/schema.sql so a fresh SQLite file is immediately
# usable (upload form needs at least one document type).
DEFAULT_DOCUMENT_TYPES: list[tuple[str, str, list[str]]] = [
    ("Prasymas", "Oficialus prasymas institucijoms", ["tema", "prasytojas", "data"]),
    ("Leidimas", "Leidimas vykdyti veikla ar atlikti veiksmus", ["numeris", "galiojimo_data"]),
    ("Pazymejimas", "Kvalifikacijos arba fakto patvirtinimo dokumentas", ["numeris", "istaiga"]),
    ("Sutartis", "Dviesale ar daugiasale sutartis", ["salys", "suma", "galiojimo_laikotarpis"]),
    ("Ataskaita", "Periodine arba vienkartine ataskaita", ["laikotarpis", "rengejo_pareigos"]),
    ("Isakymas", "Vadovo ar institucijos isakymas", ["numeris", "data", "pasirases"]),
    ("Protokolas", "Posedzio ar susirinkimo protokolas", ["data", "dalyviai", "pirmininkas"]),
    ("Aktas", "Patikrinimo arba perdavimo aktas", ["data", "komisija"]),
]


def seed_document_types(url: str | None = None) -> int:
    """Insert the built-in document types that are still missing. Returns count."""
    session = get_session(url)
    try:
        existing = {name for (name,) in session.query(DocumentType.name).all()}
        added = 0
        for name, description, required in DEFAULT_DOCUMENT_TYPES:
            if name in existing:
                continue
            session.add(
                DocumentType(name=name, description=description, required_fields=required)
            )
            existing.add(name)
            added += 1
        if added:
            session.commit()
        return added
    finally:
        session.close()


def init_db(url: str | None = None):
    """Create all tables and seed the built-in document types."""
    engine = get_engine(url)
    Base.metadata.create_all(engine)
    seed_document_types(url)
