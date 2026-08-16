# Skills

Capability reference for FastDocs + a pointer to the shared **Frappe → FastHTML
migration playbook** (the canonical recipe lives in the umbrella repo's
`SKILLS.md`; the same recipe is followed across `fasthtml-oss-migrations`).

---

## Part 1 — FastDocs capabilities

**Entry:** `python web_app.py` → http://localhost:5016
(login `admin@fastdocs.example` / `FastDocs2026$`).

### Pages

| View | Route | What it shows |
|---|---|---|
| Library | `/` | documents grouped by folder, word counts, published badge |
| Editor | `/doc/{id}` | block editor (title + block list + add bar + toolbar) |
| Read view | `/read/{id}` | clean read-only render (logged in) |
| Versions | `/doc/{id}/versions` | snapshot list + restore |
| Templates | `/templates` | reusable structures → "Use template" |
| Generate | `/generate` | AI document-from-prompt |
| Public | `/p/{token}` | read-only published page, **no login** |
| AI Assistant | `/ai` | draft / rewrite / summarise chat (right rail) |

### Block model (`db.py` + `web/views.py`)

A document is an ordered list of rows in `blocks` (`type`, `content`, `position`).
`BLOCK_TYPES` = heading1/2/3, paragraph, bullet, numbered, quote, code, divider.
`render_block(b)` maps each type to an FT component; `_inline()` renders Markdown
and strips a wrapping `<p>` for headings / list items.

### Editing surface — the HTMX fragment pattern

The whole editor is the **`doc_main(id)` / `doc_detail(id)`** swap pattern:

- `doc_detail(id)` wraps `doc_main(id)` in `Div(..., id="doc-main")` (rendered once
  in the full page).
- Every block control (`↑ ↓ ＋ ✎ 🗑`), the title form, and the add-bar carry
  `hx_target="#doc-main", hx_swap="innerHTML"` (the shared `HX` dict).
- Write routes (`/doc/{id}/block/...`, `/doc/{id}/title`) do their DB work then
  `return views.doc_main(id, editing)` — HTMX swaps just the fragment, no reload.
- Editing a block re-renders that block as an inline `<select type>` + `<textarea>`
  form (`_edit_node`); **Cancel** is an `hx_get` back to `/doc/{id}/main`.
- Add-block returns `doc_main(editing=<new id>)` so the user lands straight in the
  new block's editor (except dividers, which need no editing).

Plain `Form(method="post")` (publish, unpublish, save-version, use-template,
restore, new folder/doc) **redirect** to a full page instead — only the granular
block edits are fragment swaps.

### Templates, versions, publishing (`db.py`)

- `create_doc_from_template(tid)` copies `template_blocks` into a new document.
- `snapshot_version(doc_id)` stores blocks as JSON; `restore_version(vid)` snapshots
  current state first (reversible), then replaces blocks.
- `publish(doc_id)` mints `secrets.token_urlsafe(9)` into `documents.public_token`;
  `/p/{token}` renders `public_article()` — a standalone page with no auth/nav.

### AI (`web/ai.py`)

`generate_doc(topic)` → strict JSON array of `{type, content}` blocks, validated
against `BLOCK_TYPES` and persisted via `db.create_document()`. Grounded chat via
`snapshot()` (document titles + truncated content); `/docs` and `/templates`
slash-commands work with **no API key**.

---

## Part 2 — Frappe → FastHTML migration playbook

The canonical step-by-step recipe (porting **and** deepening, with the gotchas)
is the umbrella repo's `SKILLS.md`. FastDocs-specific notes on top of it:

1. **Collapse the editor, keep the value.** Upstream Writer is a TipTap/Yjs
   collaborative editor; the demonstrator value is the block model + templates +
   versions + publish, all server-rendered. Real-time collab is the scope cut.
2. **Block ops are the slide pattern.** Add/move/delete blocks reuses FastSlides'
   add/move/delete-slide logic almost verbatim (position re-packing in `db.py`).
3. **Fragment, don't reload.** Granular edits return `doc_main` fragments; only
   coarse actions redirect. Keep that split.
4. **`init_schema()` on every boot.** `_ensure_db()` calls it for the
   `public_token` migration guard — mirror this when adding tables/columns.
5. **LLM → structured blocks.** Same "return ONLY a JSON array" + defensive parse
   used across the suite (`_extract_json`).

### Reusable assets

| File | Reuse |
|---|---|
| `web/views.py` `render_block` / `_inline` | Markdown block → FT component rendering |
| `web/views.py` `doc_main` / `doc_detail` + `HX` | granular HTMX fragment-swap editor |
| `web/ai.py` `generate_doc()` / `_extract_json()` | text → validated structured blocks |
| `db.py` block CRUD (`add/move/delete_block`) | ordered-children position management |
