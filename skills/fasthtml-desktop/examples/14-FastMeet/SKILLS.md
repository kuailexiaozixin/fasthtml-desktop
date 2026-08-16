# Skills

Capability reference for FastMeet + the shared **Frappe → FastHTML migration
playbook** (same recipe across `fasthtml-oss-migrations`; see `FastCRM/SKILLS.md`).

---

## Part 1 — FastMeet capabilities

**Entry:** `python web_app.py` → http://localhost:5015
(login `admin@fastmeet.example` / `FastMeet2026$`).

### Pages

| View | Route | What it shows |
|---|---|---|
| Dashboard | `/` | today / upcoming / live / recordings |
| Meetings | `/meetings?scope=upcoming|past` | meeting lists |
| Meeting | `/meeting/{id}` | details, participants+RSVP, agenda, summary |
| Room | `/room/{id}` | simulated lobby (tiles + controls) |
| Schedule | `/schedule` | create + invite |
| AI Assistant | `/ai` | schedule chat (right rail) |

### AI (`web/ai.py`)

- `generate_agenda(mid)` — drafts + persists an agenda from title/participants
  (HTMX-swapped on the meeting page).
- `summarise_meeting(mid)` — writes + persists a summary for ended meetings.
- Grounded chat over `snapshot()` (today/upcoming). Slash-commands (no key):
  `/today`, `/upcoming`.

### Data (`db.py`)

`meetings` (status incl. `Live`) + `participants` (role, RSVP). Rebuild with
`python seed.py` (seeds one live meeting + recordings so the UI is lively).

---

## Part 2 — Frappe → FastHTML migration playbook

1. **Mine the schema** — `python scripts/frappe_doctype_to_schema.py /tmp/frappe-meet`.
2. **Name the un-portable core** — Meet *is* WebRTC; a server-rendered app can't
   carry live media. Build everything **around** the call (schedule, rooms,
   agendas, summaries) and document the media-layer integration in the roadmap.
   Honesty in the UI (the room notice) beats faking it.
3. **FastHTML shell** — `fast_app(pico=False, hdrs=[Style(CSS)])`; `page()` wrapper.
4. **HTMX over JS** — per-meeting "generate agenda" / "summarise" are `hx-post`
   into an `#ai-panel`; lists and detail are plain navigation.
5. **Lively synthetic data** — seed a *live-now* meeting + recordings so the
   dashboard demonstrates every state; fixed RNG seed; self-seed on boot.
6. **LLM, key-optional** — `_complete()` for agenda/summary, `_provider_stream`
   for chat; slash-commands work with no key.
7. **Capture the demo** — Playwright MCP → frames → `build_demo_gif.sh`.
8. **Ship deploy paths** — `.env.sample`, `Dockerfile`, `docker-compose.yml`.

### Reusable assets

| File | Reuse |
|---|---|
| `scripts/frappe_doctype_to_schema.py` | DocType JSON → SQLite DDL |
| `scripts/build_demo_gif.sh` | frames → demo GIF |
| `web/ai.py` `generate_*` / `summarise_*` | per-item LLM actions via HTMX |
| `web/layout.py` room/video-tile CSS | a media-free conferencing lobby |
