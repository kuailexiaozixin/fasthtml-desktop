"""FastFPA persistence and deterministic three-statement planning model."""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

DB_PATH = Path(os.getenv("FASTFPA_DB", "fastfpa.sqlite"))
CUTOFF = "2026-06"
MONEY = Decimal("0.01")


def dec(value) -> Decimal:
    return Decimal(str(value))


def q(value) -> Decimal:
    return dec(value).quantize(MONEY, rounding=ROUND_HALF_UP)


def connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH, timeout=20)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("PRAGMA journal_mode=WAL")
    return con


def rows(sql: str, params=()) -> list[dict]:
    with connection() as con:
        return [dict(row) for row in con.execute(sql, params).fetchall()]


def one(sql: str, params=()) -> dict | None:
    with connection() as con:
        row = con.execute(sql, params).fetchone()
        return dict(row) if row else None


SCHEMA = """
CREATE TABLE IF NOT EXISTS scenarios (
    id INTEGER PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    status TEXT NOT NULL,
    color TEXT NOT NULL,
    description TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS assumptions (
    scenario_id INTEGER NOT NULL REFERENCES scenarios(id) ON DELETE CASCADE,
    key TEXT NOT NULL,
    label TEXT NOT NULL,
    value REAL NOT NULL,
    unit TEXT NOT NULL,
    PRIMARY KEY (scenario_id, key)
);
CREATE TABLE IF NOT EXISTS financial_periods (
    scenario_id INTEGER NOT NULL REFERENCES scenarios(id) ON DELETE CASCADE,
    period TEXT NOT NULL,
    is_actual INTEGER NOT NULL DEFAULT 0,
    opening_cash REAL NOT NULL,
    revenue REAL NOT NULL,
    cogs REAL NOT NULL,
    payroll REAL NOT NULL,
    opex REAL NOT NULL,
    depreciation REAL NOT NULL,
    ebitda REAL NOT NULL,
    ebit REAL NOT NULL,
    interest REAL NOT NULL,
    tax REAL NOT NULL,
    net_income REAL NOT NULL,
    ar REAL NOT NULL,
    inventory REAL NOT NULL,
    fixed_assets REAL NOT NULL,
    cash REAL NOT NULL,
    ap REAL NOT NULL,
    debt REAL NOT NULL,
    equity REAL NOT NULL,
    cfo REAL NOT NULL,
    cfi REAL NOT NULL,
    cff REAL NOT NULL,
    balance_check REAL NOT NULL,
    cash_check REAL NOT NULL,
    PRIMARY KEY (scenario_id, period)
);
CREATE TABLE IF NOT EXISTS recurring_metrics (
    scenario_id INTEGER NOT NULL REFERENCES scenarios(id) ON DELETE CASCADE,
    period TEXT NOT NULL,
    opening_customers INTEGER NOT NULL,
    new_customers INTEGER NOT NULL,
    churned_customers INTEGER NOT NULL,
    ending_customers INTEGER NOT NULL,
    mrr REAL NOT NULL,
    arr REAL NOT NULL,
    PRIMARY KEY (scenario_id, period)
);
CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    owner TEXT NOT NULL,
    actual_ytd REAL NOT NULL,
    budget_ytd REAL NOT NULL,
    forecast_fy REAL NOT NULL,
    status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS integrations (
    key TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    product TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    status TEXT NOT NULL,
    last_sync TEXT,
    records INTEGER NOT NULL DEFAULT 0,
    detail TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS workflow (
    id INTEGER PRIMARY KEY,
    scope TEXT NOT NULL,
    owner TEXT NOT NULL,
    status TEXT NOT NULL,
    due_date TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS audit_events (
    id INTEGER PRIMARY KEY,
    created_at TEXT NOT NULL,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    detail TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS suite_ticket_redemptions (
    jti_hash TEXT PRIMARY KEY,
    expires_at INTEGER NOT NULL,
    redeemed_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_period_scenario ON financial_periods(scenario_id, period);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_events(created_at DESC);
"""


def init_schema() -> None:
    with connection() as con:
        con.executescript(SCHEMA)


def db_exists() -> bool:
    return DB_PATH.exists() and one(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='financial_periods'"
    ) is not None


SCENARIOS = (
    ("actual", "Actual", "Actual", "Locked", "#64748b", "Closed actuals through June 2026."),
    ("budget", "FY26 Budget", "Budget", "Published", "#2563eb", "Board-approved annual operating plan."),
    ("baseline", "Q3 Baseline", "Forecast", "Working", "#0f766e", "Latest driver-based rolling forecast."),
    ("upside", "Upside", "What-if", "Draft", "#16a34a", "Higher conversion and expansion scenario."),
    ("downside", "Downside", "What-if", "Draft", "#dc2626", "Lower demand and delayed hiring scenario."),
)

DEFAULTS = {
    "budget": {
        "monthly_growth": 1.20,
        "gross_margin": 42.0,
        "payroll_growth": 0.50,
        "opex_growth": 0.30,
        "dso": 42,
        "inventory_days": 48,
        "dpo": 38,
        "capex": 12000,
        "tax_rate": 19,
        "annual_interest": 5.5,
        "new_customers": 8,
        "churn_rate": 1.8,
        "mrr_per_customer": 2450,
    },
    "baseline": {
        "monthly_growth": 1.05,
        "gross_margin": 42.5,
        "payroll_growth": 0.45,
        "opex_growth": 0.20,
        "dso": 44,
        "inventory_days": 50,
        "dpo": 39,
        "capex": 11000,
        "tax_rate": 19,
        "annual_interest": 5.7,
        "new_customers": 9,
        "churn_rate": 1.7,
        "mrr_per_customer": 2500,
    },
    "upside": {
        "monthly_growth": 2.10,
        "gross_margin": 44.0,
        "payroll_growth": 0.65,
        "opex_growth": 0.30,
        "dso": 40,
        "inventory_days": 46,
        "dpo": 40,
        "capex": 15000,
        "tax_rate": 19,
        "annual_interest": 5.5,
        "new_customers": 13,
        "churn_rate": 1.2,
        "mrr_per_customer": 2600,
    },
    "downside": {
        "monthly_growth": -0.35,
        "gross_margin": 39.5,
        "payroll_growth": 0.10,
        "opex_growth": -0.40,
        "dso": 52,
        "inventory_days": 57,
        "dpo": 42,
        "capex": 6500,
        "tax_rate": 19,
        "annual_interest": 6.2,
        "new_customers": 5,
        "churn_rate": 2.8,
        "mrr_per_customer": 2380,
    },
}

ASSUMPTION_META = {
    "monthly_growth": ("Monthly revenue growth", "%"),
    "gross_margin": ("Gross margin", "%"),
    "payroll_growth": ("Monthly payroll growth", "%"),
    "opex_growth": ("Monthly operating cost growth", "%"),
    "dso": ("Receivable days", "days"),
    "inventory_days": ("Inventory days", "days"),
    "dpo": ("Payable days", "days"),
    "capex": ("Monthly capital expenditure", "GBP"),
    "tax_rate": ("Effective tax rate", "%"),
    "annual_interest": ("Annual debt interest", "%"),
    "new_customers": ("New recurring customers / month", "count"),
    "churn_rate": ("Monthly customer churn", "%"),
    "mrr_per_customer": ("MRR per customer", "GBP"),
}


def month_range(start_year=2025, start_month=1, end_year=2026, end_month=12):
    year, month = start_year, start_month
    while (year, month) <= (end_year, end_month):
        yield f"{year:04d}-{month:02d}"
        month += 1
        if month == 13:
            year += 1
            month = 1


def _actual_driver(period: str) -> dict[str, Decimal]:
    index = (int(period[:4]) - 2025) * 12 + int(period[5:7]) - 1
    seasonal = dec((0.012, -0.004, 0.008, 0.016, 0.006, 0.011)[index % 6])
    return {
        "monthly_growth": dec("0.008") + seasonal,
        "gross_margin": dec("0.414") + dec((index % 4) - 1) * dec("0.002"),
        "payroll_growth": dec("0.004"),
        "opex_growth": dec("0.0025"),
        "dso": dec(43 + index % 4),
        "inventory_days": dec(49 + index % 5),
        "dpo": dec(38 + index % 3),
        "capex": dec(8500 + (index % 4) * 1400),
        "tax_rate": dec("0.19"),
        "annual_interest": dec("0.056"),
        "new_customers": dec(7 + index % 4),
        "churn_rate": dec("0.019"),
        "mrr_per_customer": dec(2400 + index * 8),
    }


def _configured_driver(slug: str) -> dict[str, Decimal]:
    params = {row["key"]: dec(row["value"]) for row in assumptions(slug)}
    return {
        "monthly_growth": params["monthly_growth"] / 100,
        "gross_margin": params["gross_margin"] / 100,
        "payroll_growth": params["payroll_growth"] / 100,
        "opex_growth": params["opex_growth"] / 100,
        "dso": params["dso"],
        "inventory_days": params["inventory_days"],
        "dpo": params["dpo"],
        "capex": params["capex"],
        "tax_rate": params["tax_rate"] / 100,
        "annual_interest": params["annual_interest"] / 100,
        "new_customers": params["new_customers"],
        "churn_rate": params["churn_rate"] / 100,
        "mrr_per_customer": params["mrr_per_customer"],
    }


def rebuild_scenario(slug: str) -> None:
    scenario = get_scenario(slug)
    if not scenario:
        raise ValueError("Unknown scenario")
    configured = _configured_driver(slug) if slug != "actual" else None

    revenue = dec("238000")
    payroll = dec("60500")
    opex = dec("37200")
    ar = dec("338000")
    inventory = dec("225000")
    fixed_assets = dec("220000")
    cash = dec("320000")
    ap = dec("192000")
    debt = dec("140000")
    equity = q(cash + ar + inventory + fixed_assets - ap - debt)
    customers = 118

    period_rows = []
    recurring_rows = []
    for period in month_range():
        if slug == "actual" and period > CUTOFF:
            break
        use_actual = period <= CUTOFF and slug != "budget" or period < "2026-01"
        driver = _actual_driver(period) if use_actual else configured
        assert driver is not None

        opening_cash = cash
        revenue = q(revenue * (1 + driver["monthly_growth"]))
        cogs = q(revenue * (1 - driver["gross_margin"]))
        payroll = q(payroll * (1 + driver["payroll_growth"]))
        opex = q(opex * (1 + driver["opex_growth"]))
        depreciation = q(fixed_assets / dec("84"))
        ebitda = q(revenue - cogs - payroll - opex)
        ebit = q(ebitda - depreciation)
        interest = q(debt * driver["annual_interest"] / 12)
        pretax = q(ebit - interest)
        tax = q(max(pretax, dec("0")) * driver["tax_rate"])
        net_income = q(pretax - tax)

        next_ar = q(revenue * driver["dso"] / dec("30"))
        next_inventory = q(cogs * driver["inventory_days"] / dec("30"))
        next_ap = q(cogs * driver["dpo"] / dec("30"))
        capex = q(driver["capex"])
        next_fixed_assets = q(fixed_assets + capex - depreciation)
        debt_repayment = q(dec("4000") if period.endswith(("03", "06", "09", "12")) else 0)
        debt_draw = q(dec("18000") if slug == "downside" and period.endswith("09") else 0)
        next_debt = q(debt + debt_draw - debt_repayment)

        cfo = q(net_income + depreciation - (next_ar - ar) - (next_inventory - inventory) + (next_ap - ap))
        cfi = q(-capex)
        cff = q(debt_draw - debt_repayment)
        next_cash = q(cash + cfo + cfi + cff)
        next_equity = q(equity + net_income)

        assets = q(next_cash + next_ar + next_inventory + next_fixed_assets)
        liabilities_equity = q(next_ap + next_debt + next_equity)
        balance_check = q(assets - liabilities_equity)
        cash_check = q((next_cash - cash) - (cfo + cfi + cff))

        period_rows.append((
            scenario["id"], period, int(use_actual), float(opening_cash),
            float(revenue), float(cogs), float(payroll), float(opex),
            float(depreciation), float(ebitda), float(ebit), float(interest),
            float(tax), float(net_income), float(next_ar), float(next_inventory),
            float(next_fixed_assets), float(next_cash), float(next_ap),
            float(next_debt), float(next_equity), float(cfo), float(cfi),
            float(cff), float(balance_check), float(cash_check),
        ))

        churned = max(1, round(customers * float(driver["churn_rate"])))
        new_customers = int(driver["new_customers"])
        ending_customers = customers + new_customers - churned
        mrr = q(ending_customers * driver["mrr_per_customer"])
        recurring_rows.append((
            scenario["id"], period, customers, new_customers, churned,
            ending_customers, float(mrr), float(q(mrr * 12)),
        ))

        ar, inventory, fixed_assets = next_ar, next_inventory, next_fixed_assets
        cash, ap, debt, equity = next_cash, next_ap, next_debt, next_equity
        customers = ending_customers

    with connection() as con:
        con.execute("DELETE FROM financial_periods WHERE scenario_id=?", (scenario["id"],))
        con.execute("DELETE FROM recurring_metrics WHERE scenario_id=?", (scenario["id"],))
        con.executemany(
            """INSERT INTO financial_periods VALUES
            (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            period_rows,
        )
        con.executemany(
            "INSERT INTO recurring_metrics VALUES (?,?,?,?,?,?,?,?)",
            recurring_rows,
        )
        con.execute(
            "UPDATE scenarios SET updated_at=? WHERE id=?",
            (datetime.now(timezone.utc).isoformat(), scenario["id"]),
        )


def seed() -> None:
    init_schema()
    now = datetime.now(timezone.utc).isoformat()
    with connection() as con:
        for table in (
            "audit_events", "workflow", "integrations", "departments",
            "recurring_metrics", "financial_periods", "assumptions", "scenarios",
        ):
            con.execute(f"DELETE FROM {table}")
        con.executemany(
            "INSERT INTO scenarios(slug,name,kind,status,color,description,updated_at) VALUES (?,?,?,?,?,?,?)",
            [(*scenario, now) for scenario in SCENARIOS],
        )
        for slug, values in DEFAULTS.items():
            scenario_id = con.execute("SELECT id FROM scenarios WHERE slug=?", (slug,)).fetchone()[0]
            con.executemany(
                "INSERT INTO assumptions(scenario_id,key,label,value,unit) VALUES (?,?,?,?,?)",
                [
                    (scenario_id, key, ASSUMPTION_META[key][0], value, ASSUMPTION_META[key][1])
                    for key, value in values.items()
                ],
            )
        actual_id = con.execute("SELECT id FROM scenarios WHERE slug='actual'").fetchone()[0]
        con.executemany(
            "INSERT INTO assumptions(scenario_id,key,label,value,unit) VALUES (?,?,?,?,?)",
            [
                (actual_id, key, label, 0, unit)
                for key, (label, unit) in ASSUMPTION_META.items()
            ],
        )
        con.executemany(
            "INSERT INTO departments(name,owner,actual_ytd,budget_ytd,forecast_fy,status) VALUES (?,?,?,?,?,?)",
            [
                ("Sales", "Maya Patel", 312000, 326000, 665000, "Submitted"),
                ("Delivery", "Liam Chen", 428000, 410000, 842000, "In review"),
                ("Product", "Sofia Novak", 286000, 279000, 575000, "Approved"),
                ("G&A", "Theo Martin", 194000, 188000, 384000, "Draft"),
                ("Finance", "Ava Williams", 121000, 124000, 251000, "Approved"),
            ],
        )
        con.executemany(
            "INSERT INTO integrations(key,name,product,endpoint,status,last_sync,records,detail) VALUES (?,?,?,?,?,?,?,?)",
            [
                ("erp", "Financial actuals", "FastERP", "https://erp.fastsme.com/api/v1/accounts", "Ready", None, 0, "Accounts, statements and operating actuals"),
                ("hrm", "Workforce plan", "FastHRM", "https://hrm.fastsme.com/api/v1/employees", "Ready", None, 0, "Employees, departments and payroll drivers"),
                ("crm", "Commercial pipeline", "FastCRM", "https://crm.fastsme.com/api/v1/opportunities", "Ready", None, 0, "Pipeline value, probability and expected close"),
            ],
        )
        con.executemany(
            "INSERT INTO workflow(scope,owner,status,due_date,updated_at) VALUES (?,?,?,?,?)",
            [
                ("Sales plan", "Maya Patel", "Submitted", "2026-07-30", now),
                ("Delivery capacity", "Liam Chen", "In review", "2026-07-30", now),
                ("Product investment", "Sofia Novak", "Approved", "2026-07-29", now),
                ("G&A budget", "Theo Martin", "Draft", "2026-07-31", now),
                ("Finance close", "Ava Williams", "Approved", "2026-07-29", now),
            ],
        )
        con.execute(
            "INSERT INTO audit_events(created_at,actor,action,detail) VALUES (?,?,?,?)",
            (now, "System", "Model seeded", "Created deterministic FastERP-aligned planning model"),
        )
    for slug, *_ in SCENARIOS:
        rebuild_scenario(slug)


def ensure_seeded() -> None:
    init_schema()
    if not one("SELECT 1 FROM scenarios LIMIT 1"):
        seed()


def scenarios() -> list[dict]:
    return rows("SELECT * FROM scenarios ORDER BY id")


def get_scenario(slug: str) -> dict | None:
    return one("SELECT * FROM scenarios WHERE slug=?", (slug,))


def assumptions(slug: str) -> list[dict]:
    return rows(
        """SELECT a.* FROM assumptions a JOIN scenarios s ON s.id=a.scenario_id
        WHERE s.slug=? ORDER BY a.rowid""",
        (slug,),
    )


def update_assumptions(slug: str, values: dict[str, str], actor: str) -> None:
    scenario = get_scenario(slug)
    if not scenario or scenario["kind"] == "Actual" or scenario["status"] == "Locked":
        raise ValueError("This scenario is not editable")
    allowed = {row["key"] for row in assumptions(slug)}
    with connection() as con:
        for key, raw in values.items():
            if key not in allowed or raw in (None, ""):
                continue
            value = float(raw)
            if key in {"gross_margin", "tax_rate", "churn_rate"} and not 0 <= value <= 100:
                raise ValueError(f"{key} must be between 0 and 100")
            con.execute(
                "UPDATE assumptions SET value=? WHERE scenario_id=? AND key=?",
                (value, scenario["id"], key),
            )
    rebuild_scenario(slug)
    audit(actor, "Scenario recalculated", f"{scenario['name']} assumptions updated")


def financial_periods(slug: str, year: int = 2026) -> list[dict]:
    return rows(
        """SELECT p.* FROM financial_periods p JOIN scenarios s ON s.id=p.scenario_id
        WHERE s.slug=? AND p.period LIKE ? ORDER BY p.period""",
        (slug, f"{year}-%"),
    )


def annual_summary(slug: str, year: int = 2026) -> dict:
    periods = financial_periods(slug, year)
    if not periods:
        return {}
    sums = {
        key: q(sum(dec(row[key]) for row in periods))
        for key in (
            "revenue", "cogs", "payroll", "opex", "depreciation", "ebitda",
            "ebit", "interest", "tax", "net_income", "cfo", "cfi", "cff",
        )
    }
    ending = periods[-1]
    return {
        **{key: float(value) for key, value in sums.items()},
        **{key: ending[key] for key in ("ar", "inventory", "fixed_assets", "cash", "ap", "debt", "equity")},
        "periods": len(periods),
        "balance_check": max(abs(row["balance_check"]) for row in periods),
        "cash_check": max(abs(row["cash_check"]) for row in periods),
    }


def comparison(left_slug: str, right_slug: str, year: int = 2026) -> dict:
    left, right = annual_summary(left_slug, year), annual_summary(right_slug, year)
    keys = ("revenue", "ebitda", "net_income", "cash")
    return {
        key: {
            "left": left.get(key, 0),
            "right": right.get(key, 0),
            "variance": float(q(dec(left.get(key, 0)) - dec(right.get(key, 0)))),
        }
        for key in keys
    }


def recurring(slug: str, year: int = 2026) -> list[dict]:
    return rows(
        """SELECT r.* FROM recurring_metrics r JOIN scenarios s ON s.id=r.scenario_id
        WHERE s.slug=? AND r.period LIKE ? ORDER BY r.period""",
        (slug, f"{year}-%"),
    )


def departments() -> list[dict]:
    return rows("SELECT * FROM departments ORDER BY id")


def integrations() -> list[dict]:
    return rows("SELECT * FROM integrations ORDER BY key")


def record_integration(key: str, status: str, records: int, detail: str) -> None:
    with connection() as con:
        con.execute(
            "UPDATE integrations SET status=?,last_sync=?,records=?,detail=? WHERE key=?",
            (status, datetime.now(timezone.utc).isoformat(), records, detail[:240], key),
        )


def workflow() -> list[dict]:
    return rows("SELECT * FROM workflow ORDER BY id")


def advance_workflow(item_id: int, actor: str) -> None:
    current = one("SELECT * FROM workflow WHERE id=?", (item_id,))
    if not current:
        return
    next_status = {
        "Draft": "Submitted",
        "Submitted": "In review",
        "In review": "Approved",
        "Approved": "Approved",
    }[current["status"]]
    now = datetime.now(timezone.utc).isoformat()
    with connection() as con:
        con.execute("UPDATE workflow SET status=?,updated_at=? WHERE id=?", (next_status, now, item_id))
    audit(actor, "Workflow advanced", f"{current['scope']}: {current['status']} → {next_status}")


def audit(actor: str, action: str, detail: str) -> None:
    with connection() as con:
        con.execute(
            "INSERT INTO audit_events(created_at,actor,action,detail) VALUES (?,?,?,?)",
            (datetime.now(timezone.utc).isoformat(), actor, action, detail),
        )


def audit_events(limit: int = 12) -> list[dict]:
    return rows("SELECT * FROM audit_events ORDER BY id DESC LIMIT ?", (limit,))


def api_snapshot(slug: str) -> dict:
    scenario = get_scenario(slug)
    return {
        "scenario": scenario,
        "summary": annual_summary(slug),
        "periods": financial_periods(slug),
        "assumptions": assumptions(slug) if slug != "actual" else [],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "currency": "GBP",
    }


def snapshot_text(slug: str) -> str:
    scenario = get_scenario(slug) or {}
    summary = annual_summary(slug)
    comparison_rows = comparison(slug, "budget")
    return json.dumps(
        {
            "scenario": scenario.get("name", slug),
            "summary": summary,
            "versus_budget": comparison_rows,
            "statement_integrity": {
                "balance_check": summary.get("balance_check", 0),
                "cash_check": summary.get("cash_check", 0),
            },
        },
        indent=2,
    )
