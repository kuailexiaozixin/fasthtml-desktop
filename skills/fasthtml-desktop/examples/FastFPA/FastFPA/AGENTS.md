# FastFPA repository guidelines

FastFPA is a Python 3.12 FastHTML application with a same-process FastAPI
integration surface. Keep route wiring in `web_app.py`, persistence and
financial invariants in `db.py`, and presentation under `web/`.

- Financial calculations must remain deterministic and reconcile the balance
  sheet and cash-flow roll-forward for every period.
- Use Decimal for authoritative calculations; do not use `eval` or arbitrary
  SQL/formulas.
- Keep all demo data synthetic and deterministic.
- Treat approved/published data and AI authority as separate concerns: AI may
  explain and draft, never approve or publish.
- Integrate sister products through versioned APIs, never shared databases.
- Do not commit `.env`, databases, secrets, browser state, or generated local
  artifacts.

Run:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall web_app.py db.py seed.py web
```
