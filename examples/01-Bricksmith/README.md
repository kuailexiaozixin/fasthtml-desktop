# Bricksmith

Your CRE Deal AI Squad — a specialist team of agents that underwrite, close and manage your deals.

![Bricksmith demo](docs/bricksmith.gif)

- **Marketing landing** at `/` with hero, squad directory, how-it-works, pricing.
- **3-pane chat app** at `/app` with left squad/session browser, centre chat, right artifact pane.
- **A squad of specialist AI agents** across sourcing, underwriting, diligence, capital/LP, and asset management — routed by prefix (`triage:`, `pf:`, `memo:`…) or by keyword heuristics with an LLM fallback classifier.
- **xAI Grok** as the default LLM via OpenAI-compatible endpoint.
- **SQLite + sqlite-vec** — no database server required. The OLTP tables
  (`properties`, `rent_rolls`, `t12_statements`, `leases`, `comps`, `pro_formas`,
  `debt_stacks`, `investor_crm`, `market_signals`, …) live in a single local file
  `data/bricksmith.db`, and the RAG vectors are stored in a `vec0` virtual table
  backed by the **sqlite-vec** extension (KNN cosine search). The schema is created
  automatically on first launch — there is no `DB_URL` connection string to manage.
- **Synthetic CRE dataset** out of the box: 40 properties across 8 Sun Belt metros, ~2,600 rent-roll line items, 480 T12 months, 480 comps, 2,640 market-signal rows, 60 LP contacts, 237 indexed documents (leases, zoning memos, Phase I ESAs, PCRs, title commitments, market reports).
- **Local embeddings** via fastembed (no OpenAI key required) — BAAI/bge-small-en-v1.5 at 384 dim. The model (~100 MB) downloads on first use; set `EMBEDDING_PROVIDER=openai` + `OPENAI_API_KEY` to use OpenAI embeddings instead.

## Running locally

**Desktop (Windows, one click):** double-click `启动.bat` (or run `python launcher.py`).
The launcher installs any missing dependencies, then opens the app in a pywebview
window. No `pip` / venv steps needed.

**Headless / server / CI:** `python launcher.py server` (or `SERVER_ONLY=1 python main.py`)
runs the FastHTML server without a desktop window.

**Manual:**

```bash
cp .env.example .env                    # fill XAI_API_KEY (or OPENAI_API_KEY)
pip install -r requirements.txt
python -m db.migrate                    # creates data/bricksmith.db (schema + vec0 table + prompt versions)
python -m synthetic.generate --seed 42 # populate OLTP + RAG (~1 min, downloads embedding model on first run)
python main.py                          # serves on :5057 (desktop window) or use `launcher.py server`
```

Quality gate (no key / no network needed): `python dev_check.py` → exercises the
public routes and static assets, exits 0 when healthy. Health ping
`GET /app/_debug/ping` requires an LLM key, so it is intentionally excluded from
the gate. End-to-end tests: `pytest -q tests/`.

## Directory layout

```
main.py              entrypoint: pywebview + uvicorn desktop shell (auto-migrates SQLite on import)
app.py               FastHTML app, mounts landing + chat
launcher.py          config-driven one-click launcher (shared across all examples)
launcher.json        per-example launcher config (app name, startup notes)
启动.bat             Windows one-click dispatcher (calls launcher.py)
dev_check.py         process-internal quality gate (TestClient, no port/window)
landing/             / /platform /agents /agents/<slug> /how-it-works /pricing /contact
chat/                /app + /app/chat (SSE stream) + /app/auth/*
agents/              registry + router + 5 category packages (the full squad)
tools/               StructuredTools: properties, rentroll, financials, market, diligence, capital, asset, rag
db/                  schema.sql, rag_schema.sql, migrate.py, __init__.py (ShimCursor: PG→SQLite translation)
rag/                 embeddings (pluggable), indexer, retriever (sqlite-vec vec0 KNN)
synthetic/           40-property CRE dataset + doc generators + RAG ingest
prompts/             per-agent system prompts + shared CRE glossary
scripts/             capture_screenshots, make_gif, make_pdf
```

> **Database note (migration from upstream).** Upstream Bricksmith targets PostgreSQL
> (`psycopg` + `pgvector`). This example was ported to SQLite so it runs with zero
> external services. `db/__init__.py` ships a thin `ShimCursor` that translates the
> remaining PostgreSQL-flavoured SQL (`%s` params, `IS NOT DISTINCT FROM`, `now()`, …)
> into SQLite at call time, and `rag/retriever.py` replaces `pgvector` with a `vec0`
> KNN query. If the sqlite-vec extension cannot be loaded, `db.migrate` skips the
> vector table and retrieval falls back to keyword (`LIKE`) search instead of failing.

## Regenerating the demo artifacts

```bash
python -m scripts.capture_screenshots   # populates ./screenshots/ (10 frames)
python -m scripts.make_gif              # → docs/bricksmith.gif
python -m scripts.make_pdf              # → docs/bricksmith-product-tour.pdf
```

See [`docs/bricksmith-product-tour.pdf`](docs/bricksmith-product-tour.pdf) for the full product walkthrough.
