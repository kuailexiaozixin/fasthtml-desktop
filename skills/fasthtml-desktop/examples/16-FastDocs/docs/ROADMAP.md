# FastDocs roadmap — gap vs Frappe Writer

FastDocs is a compact FastHTML/HTMX port of the **document-editing core** of
[Frappe Writer](https://github.com/frappe/writer). Upstream is a Vue 3 +
TipTap/ProseMirror editor layered on Frappe Drive, with real-time collaborative
editing (Yjs). This port models one coherent vertical — authoring, organising,
templating, versioning and publishing documents — server-side, with no client
framework.

## Upstream DocTypes → FastDocs model

| Frappe Writer DocType | FastDocs equivalent |
|---|---|
| `Writer Document` (`content`, `settings`, `html`) | `documents` + ordered `blocks` (typed: heading/paragraph/list/quote/code/divider) |
| `Writer Template` | `templates` + `template_blocks` |
| `Writer Doc Version` / `Writer Version` (`snapshot`, `manual`) | `doc_versions` (JSON block snapshot, `manual` flag) |
| `Writer Document Update` (Yjs `updates`) | — *(real-time collab out of scope)* |
| `ycomments` (collaborative comments) | — *(out of scope)* |
| Drive `Team` / file tree | `folders` (single-level document grouping) |
| Public share (`/w/<id>`) | `documents.public_token` → read-only `/p/<token>` |

## What's implemented

- **Block editor** — add / edit / move / delete typed blocks via HTMX fragment
  swaps (`doc_main` / `doc_detail` pattern). Markdown per block, rendered server-side.
- **Folders & library** — documents grouped by folder; word counts; published badge.
- **Templates** — three reusable templates; "Use template" creates a pre-filled doc.
- **Version history** — manual snapshots + restore (restore snapshots first, so
  it's reversible).
- **Public links** — publish/unpublish a read-only tokenised page (no login).
- **AI** — grounded right-rail chat (draft / rewrite / summarise), `/docs` and
  `/templates` slash-commands (no key needed), and whole-document generation.

## Deliberate scope cuts

- **Real-time collaborative editing (Yjs / OT)** — the single biggest piece of
  upstream Writer. FastDocs is **single-user by design**, mirroring how FastSheets
  cut real-time multi-user collaboration. A server-rendered HTMX app can't
  meaningfully do CRDT cursor-level co-editing.
- **TipTap/ProseMirror WYSIWYG** — replaced with a block model + Markdown, which
  is what server-side rendering and clean AI block operations want.
- **Inline collaborative comments (`ycomments`)** — tied to the realtime layer.
- **Rich embeds, mathematics, page-break/tab extensions, media uploads** — the
  upstream editor's long tail of TipTap extensions.
- **Obsidian/markdown export, wiki links, blog publishing to Frappe** — the
  Drive/CMS integration surface.

## Possible future depth

- Document-level full-text search across blocks.
- Nested folders / drag-to-reorganise.
- Export to Markdown / HTML download.
- Comments as a non-realtime per-block thread.
- Inline "AI rewrite this block" action wired to the block toolbar.
