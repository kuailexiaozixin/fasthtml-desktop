"""FastDocs public reads and token-gated integration writes."""

import db

from .api_core import Resource, SQLiteBackend, create_sqlite_api

RESOURCES = (
    Resource("documents", "documents", "Documents", "Block-based documents and their publishing identifiers.", search_fields=("title",)),
    Resource("folders", "folders", "Folders", "Document organisation folders.", write_fields=("name", "position"), search_fields=("name",)),
    Resource("templates", "templates", "Templates", "Reusable document structures.", search_fields=("title", "description")),
    Resource("versions", "doc_versions", "Versions", "Immutable document snapshots and version history.", search_fields=("title",)),
)

backend = SQLiteBackend(db.DB_PATH, RESOURCES, initialize=db.init_schema)
api = create_sqlite_api(
    product="FastDocs", version="1.0.0",
    description="Open integration access to FastDocs documents, folders, templates, and versions.",
    base_url="https://docs.fastsme.com", backend=backend, resources=RESOURCES,
)
