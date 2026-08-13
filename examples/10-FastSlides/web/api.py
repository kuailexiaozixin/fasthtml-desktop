"""FastSlides public reads and token-gated integration writes."""

import db

from .api_core import Resource, SQLiteBackend, create_sqlite_api

RESOURCES = (
    Resource("presentations", "presentations", "Presentations", "Presentation decks and their visual themes.", write_fields=("title", "subtitle", "theme"), search_fields=("title", "subtitle", "theme")),
    Resource("slides", "slides", "Slides", "Ordered slide content and layouts.", search_fields=("title", "body", "layout")),
)

backend = SQLiteBackend(db.DB_PATH, RESOURCES, initialize=db.init_schema)
api = create_sqlite_api(
    product="FastSlides", version="1.0.0",
    description="Open integration access to FastSlides presentations and slides.",
    base_url="https://slides.fastsme.com", backend=backend, resources=RESOURCES,
)
