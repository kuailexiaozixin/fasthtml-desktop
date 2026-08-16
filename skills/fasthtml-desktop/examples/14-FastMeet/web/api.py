"""FastMeet public reads and token-gated integration writes."""

import db

from .api_core import Resource, SQLiteBackend, create_sqlite_api

RESOURCES = (
    Resource("meetings", "meetings", "Meetings", "Scheduled meetings, agendas, rooms, and summaries.", write_fields=("title", "host", "start_time", "duration_min", "status", "room_code", "agenda", "has_recording", "summary"), search_fields=("title", "host", "status", "room_code", "agenda")),
    Resource("participants", "participants", "Participants", "Meeting participants, roles, and RSVP state.", search_fields=("name", "email", "role", "rsvp")),
)

backend = SQLiteBackend(db.DB_PATH, RESOURCES, initialize=db.init_schema)
api = create_sqlite_api(
    product="FastMeet", version="1.0.0",
    description="Open integration access to FastMeet meetings and participants.",
    base_url="https://meet.fastsme.com", backend=backend, resources=RESOURCES,
)
