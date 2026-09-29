"""FastFPA server-rendered product views."""
from __future__ import annotations

from calendar import month_abbr

from fasthtml.common import *

import db


def money(value, compact=False) -> str:
    value = float(value or 0)
    if compact:
        if abs(value) >= 1_000_000:
            return f"£{value / 1_000_000:.2f}m"
        if abs(value) >= 1_000:
            return f"£{value / 1_000:.0f}k"
    return f"£{value:,.0f}"


def pct(value) -> str:
    return f"{float(value):.1f}%"


def page_head(title: str, description: str, *actions):
    return Div(
        Div(H1(title), P(description)),
        Div(*actions, cls="actions") if actions else None,
        cls="page-head",
    )


def scenario_tabs(active: str, route: str = "/"):
    return Div(
        *[
            A(
                row["name"],
                href=f"{route}?scenario={row['slug']}",
                cls=f"scenario-tab {'active' if row['slug'] == active else ''}",
            )
            for row in db.scenarios()
            if row["slug"] != "actual"
        ],
        cls="scenario-tabs",
    )


def kpi(label: str, value: str, delta: str, positive=True):
    return Article(
        Div(label, cls="kpi-label"),
        Div(value, cls="kpi-value"),
        Div(delta, cls=f"kpi-delta {'positive' if positive else 'negative'}"),
        cls="card",
    )


def _status(value: str):
    return Span(value, cls=f"status {value.replace(' ', '-')}")


def dashboard(scenario="baseline"):
    summary = db.annual_summary(scenario)
    versus = db.comparison(scenario, "budget")
    periods = db.financial_periods(scenario)
    chart_periods = periods[-12:]
    max_revenue = max((row["revenue"] for row in chart_periods), default=1)
    margin = summary["ebitda"] / summary["revenue"] * 100 if summary.get("revenue") else 0
    return (
        page_head(
            "Forward outlook",
            "A governed view of the operating plan and its linked financial statements.",
            A("Export CSV", href=f"/exports/financials.csv?scenario={scenario}", cls="btn"),
            A("Management pack", href=f"/report?scenario={scenario}", cls="btn primary"),
        ),
        scenario_tabs(scenario),
        Div(
            kpi("FY26 revenue", money(summary["revenue"], True), f"{money(versus['revenue']['variance'], True)} vs budget", versus["revenue"]["variance"] >= 0),
            kpi("EBITDA", money(summary["ebitda"], True), f"{margin:.1f}% margin", margin >= 15),
            kpi("Net income", money(summary["net_income"], True), f"{money(versus['net_income']['variance'], True)} vs budget", versus["net_income"]["variance"] >= 0),
            kpi("Year-end cash", money(summary["cash"], True), f"{money(versus['cash']['variance'], True)} vs budget", versus["cash"]["variance"] >= 0),
            cls="grid kpi-grid",
        ),
        Div(
            Article(
                Div(H2("Monthly revenue outlook"), Span("Actual + forecast", cls="muted"), cls="card-head"),
                Div(
                    *[
                        Div(
                            Div(cls=f"bar {'actual' if row['is_actual'] else ''}", style=f"height:{max(3, row['revenue'] / max_revenue * 100):.1f}%"),
                            Span(month_abbr[int(row["period"][5:7])], cls="bar-label"),
                            cls="bar-wrap",
                            title=f"{row['period']}: {money(row['revenue'])}",
                        )
                        for row in chart_periods
                    ],
                    cls="mini-chart",
                ),
                Div(Span("Forecast"), Span("Actual", cls="actual"), cls="legend"),
                cls="card",
            ),
            Article(
                Div(H2("Statement integrity"), Span("Every period", cls="muted"), cls="card-head"),
                Div(
                    Div(Strong(money(summary["balance_check"])), Span("Balance-sheet check"), cls="check"),
                    Div(Strong(money(summary["cash_check"])), Span("Cash-flow check"), cls="check"),
                    cls="integrity",
                ),
                P("Assets equal liabilities plus equity, and indirect cash flow reconciles to the change in cash.", cls="muted", style="line-height:1.6;margin-top:16px"),
                A("Inspect financial statements →", href=f"/financials?scenario={scenario}", cls="btn soft small"),
                cls="card",
            ),
            cls="grid two-col",
        ),
        Div(
            Article(
                Div(H2("Department submissions"), A("Open workflow", href="/workflow", cls="btn small"), cls="card-head"),
                Div(
                    Table(
                        Thead(Tr(Th("Department"), Th("Owner"), Th("Forecast FY"), Th("Status"))),
                        Tbody(*[
                            Tr(Td(row["name"]), Td(row["owner"]), Td(money(row["forecast_fy"])), Td(_status(row["status"])))
                            for row in db.departments()
                        ]),
                    ),
                    cls="table-wrap",
                ),
                cls="card",
            ),
            Article(
                Div(H2("Source readiness"), A("Manage", href="/integrations", cls="btn small"), cls="card-head"),
                Div(*[
                    Div(
                        Div(row["product"][4:5], cls="product-icon"),
                        Div(H3(row["product"]), P(row["detail"]), _status(row["status"])),
                        cls="integration-card",
                        style="margin-bottom:14px",
                    )
                    for row in db.integrations()
                ]),
                cls="card",
            ),
            cls="grid two-col",
            style="margin-top:15px",
        ),
    )


def scenarios_view(scenario="baseline"):
    cards = []
    budget = db.annual_summary("budget")
    for row in db.scenarios():
        if row["slug"] == "actual":
            continue
        summary = db.annual_summary(row["slug"])
        cards.append(
            Article(
                Div(Span(row["kind"], cls="kpi-label"), _status(row["status"]), cls="card-head"),
                H2(row["name"], style=f"color:{row['color']};font-size:20px"),
                P(row["description"], cls="muted", style="line-height:1.5;min-height:42px"),
                Div(money(summary["revenue"], True), cls="kpi-value"),
                P(f"Revenue · {money(summary['ebitda'], True)} EBITDA · {money(summary['cash'], True)} cash", cls="muted"),
                Div(
                    A("Edit drivers", href=f"/plans?scenario={row['slug']}", cls="btn small"),
                    A("Statements", href=f"/financials?scenario={row['slug']}", cls="btn soft small"),
                    cls="actions",
                ),
                cls="card",
            )
        )
    return (
        page_head("Scenario workspace", "Clone assumptions in bounded scenarios and compare the full financial impact.", A("Compare to budget", href="/variance", cls="btn primary")),
        Div(*cards, cls="grid two-col"),
        Article(
            Div(H2("Decision range"), Span("FY26", cls="muted"), cls="card-head"),
            Div(
                *[
                    Div(
                        Span(label, cls="kpi-label"),
                        Strong(money(value, True), style="display:block;font-size:23px;margin-top:8px"),
                        P(f"{money(value - budget[key], True)} vs budget", cls="muted"),
                        cls="check",
                    )
                    for label, key, value in (
                        ("Downside revenue", "revenue", db.annual_summary("downside")["revenue"]),
                        ("Upside revenue", "revenue", db.annual_summary("upside")["revenue"]),
                    )
                ],
                cls="integrity",
            ),
            cls="card",
            style="margin-top:15px",
        ),
    )


def scenario_editor(scenario="baseline", message=""):
    selected = db.get_scenario(scenario) or db.get_scenario("baseline")
    slug = selected["slug"]
    values = db.assumptions(slug)
    return Div(
        Div(message, cls="notice") if message else None,
        Article(
            Div(H2(f"{selected['name']} drivers"), _status(selected["status"]), cls="card-head"),
            P("Changes recalculate revenue, workforce, working capital, capex, debt, tax, retained earnings, and cash as one linked model.", cls="muted"),
            Form(
                Div(
                    *[
                        Div(
                            Label(row["label"], fr=f"assumption-{row['key']}"),
                            Div(
                                Input(id=f"assumption-{row['key']}", name=row["key"], value=f"{row['value']:g}", type="number", step="0.01"),
                                Span(row["unit"], cls="unit"),
                                cls="field-wrap",
                            ),
                            cls="field",
                        )
                        for row in values
                    ],
                    cls="form-grid",
                ),
                Button("Recalculate scenario", type="submit", cls="btn primary", style="margin-top:16px"),
                hx_post=f"/scenarios/{slug}/assumptions",
                hx_target="#scenario-editor",
                hx_swap="outerHTML",
            ),
            cls="card",
        ),
        id="scenario-editor",
    )


def plans_view(scenario="baseline"):
    scenario = scenario if scenario in {"budget", "baseline", "upside", "downside"} else "baseline"
    return (
        page_head("Driver-based plan", "Edit reviewable assumptions; calculated cells and published actuals remain governed.", A("View statements", href=f"/financials?scenario={scenario}", cls="btn")),
        scenario_tabs(scenario, "/plans"),
        scenario_editor(scenario),
    )


def _statement_table(title: str, periods: list[dict], lines: list[tuple], stock=False):
    headers = [month_abbr[int(row["period"][5:7])] for row in periods]
    body = []
    for label, key, kind in lines:
        if kind == "section":
            body.append(Tr(Td(label, colspan=len(headers) + 2), cls="section-row"))
            continue
        values = [row[key] for row in periods]
        annual = values[-1] if stock else sum(values)
        body.append(
            Tr(
                Td(label),
                *[Td(money(value)) for value in values],
                Td(money(annual)),
                cls="total-row" if kind == "total" else "",
            )
        )
    return Article(
        Div(H2(title), Span("GBP · £", cls="muted"), cls="card-head"),
        Div(
            Table(
                Thead(Tr(Th("Account"), *[Th(header) for header in headers], Th("FY / End"))),
                Tbody(*body),
            ),
            cls="table-wrap",
        ),
        cls="card",
        style="margin-bottom:15px",
    )


def financials_view(scenario="baseline"):
    periods = db.financial_periods(scenario)
    for row in periods:
        row["net_cash"] = row["cfo"] + row["cfi"] + row["cff"]
    pnl = [
        ("Income statement", "", "section"),
        ("Revenue", "revenue", "line"),
        ("Cost of goods sold", "cogs", "line"),
        ("Payroll", "payroll", "line"),
        ("Operating expenses", "opex", "line"),
        ("EBITDA", "ebitda", "total"),
        ("Depreciation", "depreciation", "line"),
        ("EBIT", "ebit", "total"),
        ("Interest", "interest", "line"),
        ("Tax", "tax", "line"),
        ("Net income", "net_income", "total"),
    ]
    balance = [
        ("Assets", "", "section"),
        ("Cash", "cash", "line"),
        ("Accounts receivable", "ar", "line"),
        ("Inventory", "inventory", "line"),
        ("Fixed assets", "fixed_assets", "line"),
        ("Liabilities & equity", "", "section"),
        ("Accounts payable", "ap", "line"),
        ("Debt", "debt", "line"),
        ("Equity", "equity", "line"),
        ("Balance check", "balance_check", "total"),
    ]
    cash_flow = [
        ("Indirect cash flow", "", "section"),
        ("Cash from operations", "cfo", "line"),
        ("Cash from investing", "cfi", "line"),
        ("Cash from financing", "cff", "line"),
        ("Net cash movement", "net_cash", "total"),
        ("Reconciliation check", "cash_check", "total"),
    ]
    return (
        page_head(
            "Integrated financial statements",
            "One calculation graph links operating drivers to profit, financial position, and liquidity.",
            A("Print / PDF", href="javascript:window.print()", cls="btn"),
            A("Export CSV", href=f"/exports/financials.csv?scenario={scenario}", cls="btn primary"),
        ),
        scenario_tabs(scenario, "/financials"),
        _statement_table("Profit & loss", periods, pnl),
        _statement_table("Balance sheet", periods, balance, stock=True),
        _statement_table("Cash flow", periods, cash_flow),
    )


def variance_view(left="baseline", right="budget"):
    comp = db.comparison(left, right)
    left_periods = {row["period"]: row for row in db.financial_periods(left)}
    right_periods = {row["period"]: row for row in db.financial_periods(right)}
    period_keys = sorted(set(left_periods) & set(right_periods))
    return (
        page_head("Actual and scenario variance", "Explain movement with deterministic amounts before drafting management commentary."),
        Div(
            *[
                kpi(label, money(values["left"], True), f"{money(values['variance'], True)} vs {right}", values["variance"] >= 0)
                for label, key, values in (
                    ("Revenue", "revenue", comp["revenue"]),
                    ("EBITDA", "ebitda", comp["ebitda"]),
                    ("Net income", "net_income", comp["net_income"]),
                    ("Year-end cash", "cash", comp["cash"]),
                )
            ],
            cls="grid kpi-grid",
        ),
        Article(
            Div(H2("Monthly revenue bridge"), Span(f"{left.title()} vs {right.title()}", cls="muted"), cls="card-head"),
            Div(
                Table(
                    Thead(Tr(Th("Period"), Th(left.title()), Th(right.title()), Th("Variance"), Th("Variance %"))),
                    Tbody(*[
                        Tr(
                            Td(period),
                            Td(money(left_periods[period]["revenue"])),
                            Td(money(right_periods[period]["revenue"])),
                            Td(money(left_periods[period]["revenue"] - right_periods[period]["revenue"])),
                            Td(pct((left_periods[period]["revenue"] / right_periods[period]["revenue"] - 1) * 100)),
                        )
                        for period in period_keys
                    ]),
                ),
                cls="table-wrap",
            ),
            cls="card",
        ),
    )


def recurring_view(scenario="baseline"):
    data = db.recurring(scenario)
    return (
        page_head("Recurring-revenue model", "A reusable customer-movement template mapped into the same governed statements.", A("Open FastSheets", href="https://sheets.fastsme.com", target="_blank", cls="btn")),
        scenario_tabs(scenario, "/recurring"),
        Article(
            Div(H2("Customer and ARR movement"), Span("Template model", cls="badge"), cls="card-head"),
            Div(
                Table(
                    Thead(Tr(Th("Period"), Th("Opening"), Th("New"), Th("Churned"), Th("Ending"), Th("MRR"), Th("ARR"))),
                    Tbody(*[
                        Tr(Td(row["period"]), Td(row["opening_customers"]), Td(row["new_customers"]), Td(row["churned_customers"]), Td(row["ending_customers"]), Td(money(row["mrr"])), Td(money(row["arr"])))
                        for row in data
                    ]),
                ),
                cls="table-wrap",
            ),
            cls="card",
        ),
    )


def workflow_view():
    return (
        page_head("Planning workflow", "Department submissions move through an auditable draft, review, and approval sequence."),
        Article(
            Div(H2("FY26 Q3 forecast cycle"), Span("5 workstreams", cls="muted"), cls="card-head"),
            Div(
                Table(
                    Thead(Tr(Th("Scope"), Th("Owner"), Th("Due"), Th("Status"), Th("Action"))),
                    Tbody(*[
                        Tr(
                            Td(row["scope"]),
                            Td(row["owner"]),
                            Td(row["due_date"]),
                            Td(_status(row["status"])),
                            Td(
                                Button(
                                    "Advance",
                                    cls="btn small",
                                    hx_post=f"/workflow/{row['id']}/advance",
                                    hx_target="#workflow-table",
                                    hx_swap="outerHTML",
                                    disabled=row["status"] == "Approved",
                                )
                            ),
                        )
                        for row in db.workflow()
                    ]),
                ),
                id="workflow-table",
                cls="table-wrap",
            ),
            cls="card",
        ),
        Article(
            Div(H2("Recent audit events"), Span("Immutable activity history", cls="muted"), cls="card-head"),
            Div(*[
                Div(Strong(row["action"]), P(f"{row['actor']} · {row['detail']}", cls="muted"), cls="link-row")
                for row in db.audit_events()
            ], cls="link-list"),
            cls="card",
            style="margin-top:15px",
        ),
    )


def workflow_table():
    return Div(
        Table(
            Thead(Tr(Th("Scope"), Th("Owner"), Th("Due"), Th("Status"), Th("Action"))),
            Tbody(*[
                Tr(
                    Td(row["scope"]), Td(row["owner"]), Td(row["due_date"]), Td(_status(row["status"])),
                    Td(Button("Advance", cls="btn small", hx_post=f"/workflow/{row['id']}/advance", hx_target="#workflow-table", hx_swap="outerHTML", disabled=row["status"] == "Approved")),
                )
                for row in db.workflow()
            ]),
        ),
        id="workflow-table",
        cls="table-wrap",
    )


def integrations_view(message=""):
    return (
        page_head(
            "Connected planning",
            "FastFPA reads versioned product APIs and never opens a sister application's database.",
            Button("Refresh source APIs", cls="btn primary", hx_post="/integrations/refresh", hx_target="#integration-grid", hx_swap="outerHTML"),
        ),
        Div(
            Div(message, cls="notice") if message else None,
            Div(
                *[
                    Article(
                        Div(Div(row["product"][4:5], cls="product-icon"), Div(H3(row["product"]), P(row["name"])), cls="integration-card"),
                        P(row["detail"], cls="muted"),
                        Div(_status(row["status"]), Span(f"{row['records']} records", cls="muted"), cls="card-head", style="margin:15px 0 0"),
                        A("Open product →", href={"FastERP": "https://erp.fastsme.com", "FastHRM": "https://hrm.fastsme.com", "FastCRM": "https://crm.fastsme.com"}[row["product"]], target="_blank", cls="btn small"),
                        cls="card",
                    )
                    for row in db.integrations()
                ],
                cls="grid three-col",
            ),
            id="integration-grid",
        ),
        Article(
            Div(H2("Suite handoffs"), Span("Governed destinations", cls="muted"), cls="card-head"),
            Div(
                A(Span("FastSheets"), Span("Exchange planning workbooks →"), href="https://sheets.fastsme.com", target="_blank", cls="link-row"),
                A(Span("FastInsights"), Span("Open advanced visualisation →"), href="https://insights.fastsme.com", target="_blank", cls="link-row"),
                A(Span("FastOffice"), Span("Publish and collaborate →"), href="https://office.fastsme.com", target="_blank", cls="link-row"),
                cls="link-list",
            ),
            cls="card",
            style="margin-top:15px",
        ),
    )


def report_view(scenario="baseline"):
    summary = db.annual_summary(scenario)
    return (
        page_head("Management pack", "Print-ready synthetic board summary with explicit version and as-of metadata.", A("Print / Save PDF", href="javascript:window.print()", cls="btn primary")),
        Article(
            Div(
                Span("FastFPA · FastSME", cls="kpi-label"),
                H1("FY26 outlook and decision brief"),
                Div(Span("Scenario: " + scenario.title()), Span("Actuals through: June 2026"), Span("Currency: GBP"), Span("Synthetic data"), cls="report-meta"),
                cls="report-title",
            ),
            Div(
                kpi("Revenue", money(summary["revenue"], True), "FY26"),
                kpi("EBITDA", money(summary["ebitda"], True), f"{summary['ebitda'] / summary['revenue'] * 100:.1f}% margin"),
                kpi("Net income", money(summary["net_income"], True), "After tax"),
                kpi("Year-end cash", money(summary["cash"], True), "Reconciled"),
                cls="grid kpi-grid",
            ),
            Div(
                Div(H2("Executive outlook"), P("The baseline plan remains profitable and liquid. Growth, gross margin, working-capital days, and hiring pace are the most material controllable drivers. Downside protection should prioritise receivable collection, phased capex, and discretionary operating spend.", cls="muted", style="line-height:1.8"), cls="card"),
                Div(H2("Governance"), P("All figures originate from a versioned scenario. Balance-sheet and cash-flow checks reconcile to zero. AI commentary is explanatory and cannot publish or approve this plan.", cls="muted", style="line-height:1.8"), cls="card"),
                cls="grid two-col",
            ),
            cls="card",
        ),
    )


def ai_response(text: str):
    return Div(P(text), P("Source: selected synthetic scenario · No values changed", cls="muted"), cls="prompt ai")


def developer_page():
    resources = (
        ("Scenarios", "/api/v1/scenarios"),
        ("Financial statements", "/api/v1/statements/{scenario}"),
        ("Variances", "/api/v1/variances"),
        ("Integrations", "/api/v1/integrations"),
        ("Recurring revenue", "/api/v1/recurring/{scenario}"),
    )
    return Html(
        Head(Title("FastFPA Developers"), Meta(name="viewport", content="width=device-width, initial-scale=1"), Style("""
        body{margin:0;font-family:Inter,system-ui;background:#fff;color:#102a2e}.dev{max-width:960px;margin:auto;padding:64px 24px}.dev h1{font-size:54px;letter-spacing:-.05em}.dev p{color:#64748b;line-height:1.7}.dev-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin:35px 0}.dev-card{border:1px solid #e2e8f0;border-radius:14px;padding:18px}.dev-card code{display:block;background:#102a2e;color:#d9eee8;padding:9px;border-radius:7px;margin-top:12px}.dev a{color:#0f766e;font-weight:700}@media(max-width:680px){.dev-grid{grid-template-columns:1fr}.dev h1{font-size:40px}}
        """)),
        Body(
            Main(
                A("← FastFPA", href="/"),
                H1("Build with FastFPA."),
                P("Public read access to deterministic synthetic plans, full financial statements, scenarios, variances, recurring-revenue metrics, and source status."),
                Div(*[Article(H2(title), Code("GET " + route), cls="dev-card") for title, route in resources], cls="dev-grid"),
                P(A("Open Swagger UI →", href="/api/docs"), " · ", A("Open ReDoc →", href="/api/redoc"), " · ", A("Download OpenAPI →", href="/api/openapi.json")),
                cls="dev",
            )
        ),
    )
