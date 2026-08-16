# Skills

Capability reference for FastSlides + the shared **Frappe → FastHTML migration
playbook** (same recipe across `fasthtml-oss-migrations`; see `FastCRM/SKILLS.md`).

---

## Part 1 — FastSlides capabilities

**Entry:** `python web_app.py` → http://localhost:5013
(login `admin@fastslides.example` / `FastSlides2026$`).

### Pages

| View | Route | What it shows |
|---|---|---|
| My Decks | `/` | themed cover tiles |
| Editor | `/deck/{id}?sid=` | thumbnails + live slide canvas + edit form |
| Present | `/present/{id}` | full-screen slideshow (← / → / space / Esc) |
| Generate | `/generate` | AI deck-from-prompt |
| AI Assistant | `/ai` | slide-idea chat (right rail) |

### Slide rendering (`web/views.py`)

`slide_canvas(slide, theme)` renders a 16:9 themed slide; the Markdown `body` is
rendered with the `markdown` package. Three layouts: `title`, `section`,
`content`. Present mode reuses the same canvas with a stepping JS + keyboard nav.

### AI (`web/ai.py`)

`generate_deck(topic, count)` → strict JSON array of slides, validated and
persisted via `db.create_presentation()`. Grounded chat + `/decks` slash-command.

---

## Part 2 — Frappe → FastHTML migration playbook

1. **Mine the schema** — `python scripts/frappe_doctype_to_schema.py /tmp/frappe-slides`.
2. **Tiny schema, rich UX** — Slides is 3 doctypes; the value is the editor +
   present + AI generation layered on `presentations`/`slides`.
3. **FastHTML shell** — `fast_app(pico=False, hdrs=[Style(CSS)])`; `page()`
   wrapper; the present route returns its **own** minimal HTML document (not the
   3-pane shell) for a clean full-screen show.
4. **HTMX over JS** — editor navigation is plain links (`?sid=`); the only JS is
   the present-mode stepper + keyboard handler.
5. **Synthetic data** — sample decks as nested tuples; self-seed on boot.
6. **LLM JSON output** — for structured generation, instruct "return ONLY a JSON
   array", then parse defensively (strip fences, regex the array). Reusable for
   any text→structured-object feature.
7. **Capture the demo** — Playwright MCP → frames → `build_demo_gif.sh`.
8. **Ship deploy paths** — `.env.sample`, `Dockerfile`, `docker-compose.yml`.

### Reusable assets

| File | Reuse |
|---|---|
| `scripts/frappe_doctype_to_schema.py` | DocType JSON → SQLite DDL |
| `scripts/build_demo_gif.sh` | frames → demo GIF |
| `web/ai.py` `generate_deck()` / `_extract_json()` | text → validated structured object |
| `web/views.py` `slide_canvas` + present CSS | themed 16:9 slide rendering |
