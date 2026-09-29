# FastFPA

FastFPA is the open-source financial planning and analysis application in the
FastSME suite. It combines driver-based budgets, rolling forecasts, scenarios,
variance analysis, workflow, and linked P&L, balance sheet, and cash flow.

The public deployment at `https://fpa.fastsme.com` uses deterministic synthetic
data aligned with FastERP. No customer finance data or personal data is
included.

## Quickstart

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.sample .env
.venv/bin/python web_app.py
```

Open `http://localhost:5018` and choose **Explore synthetic demo**. Rebuild the
model with `.venv/bin/python seed.py`.

## Product tour

- **Dashboard** — revenue, EBITDA, net income, cash, workflow, source readiness.
- **Scenarios** — Budget, Baseline, Upside, and Downside decision ranges.
- **Drivers** — revenue, margin, payroll, opex, working capital, capex, debt,
  tax, and recurring-revenue assumptions.
- **Financials** — integrated monthly P&L, balance sheet, and cash flow with
  zero-balance integrity controls.
- **Variance** — scenario-versus-budget amounts and monthly bridges.
- **Recurring revenue** — customer movement, MRR, and ARR model template.
- **Workflow** — department submission, review, approval, and audit events.
- **Integrations** — FastERP, FastHRM, FastCRM, FastSheets, FastInsights, and
  FastOffice contracts.
- **Finance copilot** — xAI-backed explanations and drafting; it cannot approve
  or publish.

## API

Developer documentation is available at `/developers`, Swagger at `/api/docs`,
and the runtime OpenAPI schema at `/api/openapi.json`.

```bash
curl http://localhost:5018/api/v1/statements/baseline
```

## Verification

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m compileall web_app.py db.py seed.py web
docker build -t fastfpa .
```

See the [implementation plan](docs/IMPLEMENTATION_PLAN.md) for the complete
architecture, decisions, and roadmap.

MIT licensed.
