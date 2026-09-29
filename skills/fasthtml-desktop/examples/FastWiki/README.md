# FastWiki

FastWiki is the open-source knowledge workspace in FastOffice: a lightweight
Confluence-style wiki for SMEs with a Tiptap rich editor, portable JSON content,
optional Markdown, comments, attachments, search, page history, tenant-safe APIs,
hierarchical draft/published pages, a workspace-grounded LangChain assistant,
threaded discussions, visible publication provenance, and links to the wider
FastOffice suite.

## Run locally

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.sample .env
.venv/bin/python app.py
```

Open `http://localhost:5022/auth/dev`. Production disables this development
entry point and uses short-lived FastOffice suite tickets.

The AI Assistant uses the OpenAI-compatible xAI endpoint through LangChain by
default. Configure `FASTWIKI_AI_PROVIDER`, `FASTWIKI_AI_MODEL`,
`FASTWIKI_AI_BASE_URL`, and either `XAI_API_KEY` or `OPENAI_API_KEY`. Set
`FASTWIKI_AI_QUERY_LIMIT=5` for a daily per-user allowance or `0` for unlimited
queries. Emails listed in `FASTWIKI_ADMIN_EMAILS` are administrators and bypass
the query limit.

## Architecture

- FastHTML application shell with a browser-side Tiptap editor island.
- SQLite metadata and content with `org_id` enforced in every resource query.
- Tiptap JSON is canonical. Markdown is retained as an optional editable view.
- Autosave uses optimistic locking and returns HTTP 409 for stale versions.
- Attachments use `local` volumes, Cloudflare R2, or a configurable FastDrive
  upload endpoint through `FASTWIKI_ATTACHMENT_BACKEND`.
- FastAPI is mounted at `/api`; Swagger is at `/api/docs`, and compatibility
  schemas are exposed at `/openapi.json` and `/swagger.json`.

## Storage

Set `FASTWIKI_ATTACHMENT_BACKEND=local` for self-hosted volumes, `r2` with the
standard `R2_*` variables, or `fastdrive` with `FASTDRIVE_UPLOAD_URL` and
`FASTDRIVE_SERVICE_TOKEN`. Local and R2 downloads are handled directly by
FastWiki. A FastDrive deployment should expose a binary upload/download adapter.

## Collaboration roadmap

The initial release uses debounced autosave and optimistic locking, which is
predictable and inexpensive for SME teams. Real-time co-editing is intentionally
reserved for a later Y.js/Hocuspocus service so it can be added without changing
the canonical Tiptap JSON format.
