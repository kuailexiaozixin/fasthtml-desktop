"""FastFPA — synthetic financial planning and analysis for the FastSME suite."""
from __future__ import annotations

import csv
import io
import os
import secrets

from dotenv import load_dotenv

load_dotenv()

from fasthtml.common import Link, RedirectResponse, Response, Style, fast_app, serve
from starlette.responses import JSONResponse
from starlette.staticfiles import StaticFiles

import db
from web import ai, auth, integrations, views
from web.api import api
from web.developer import developer_page
from web.landing import landing_page, login_page
from web.seo import register_seo_routes
from web.layout import CSS, page

PORT = int(os.getenv("FASTFPA_PORT", "5018"))
SECRET = os.getenv("FASTFPA_SECRET") or secrets.token_hex(32)
ENV_LABEL = os.getenv("FASTFPA_ENV", "development")

db.ensure_seeded()

app, rt = fast_app(
    live=False,
    pico=False,
    secret_key=SECRET,
    hdrs=[Link(rel="icon", href="/static/favicon.svg"), Style(CSS)],
)
app.mount("/api", api)
app.mount("/static", StaticFiles(directory="static"), name="static")


def current_user(session) -> str | None:
    return session.get("user")


def selected_scenario(value: str) -> str:
    return value if db.get_scenario(value) and value != "actual" else "baseline"


def guarded(session, active: str, scenario: str, builder):
    user = current_user(session)
    if not user:
        return RedirectResponse("/login", status_code=303)
    slug = selected_scenario(scenario)
    content = builder(slug) if callable(builder) else builder
    if not isinstance(content, tuple):
        content = (content,)
    return page(active, user, slug, *content)


@rt("/healthz")
def get():
    return JSONResponse({
        "status": "ok",
        "product": "FastFPA",
        "environment": ENV_LABEL,
        "synthetic": True,
    })


@rt("/swagger.json")
def get():
    return JSONResponse(api.openapi())


@rt("/developers")
def get():
    return developer_page()


@rt("/login")
def get(session, error: str = ""):
    if current_user(session):
        return RedirectResponse("/", status_code=303)
    return login_page(error)


@rt("/demo")
def get(session):
    session["user"] = "demo@fastfpa.example"
    session["identity"] = {
        "name": "FastFPA Demo",
        "org_id": "synthetic",
        "org_name": "FastSME Planning Demo",
        "role": "viewer",
    }
    return RedirectResponse("/", status_code=303)


@rt("/auth/fastoffice")
def get():
    return RedirectResponse("https://office.fastsme.com/launch/fpa", status_code=303)


@rt("/auth/suite/callback")
def get(session, ticket: str = ""):
    identity = auth.redeem_suite_ticket(ticket)
    if not identity:
        return RedirectResponse("/login?error=FastOffice+session+is+invalid+or+expired", status_code=303)
    session["user"] = identity["email"]
    session["identity"] = {
        key: identity[key] for key in ("sub", "name", "org_id", "org_name", "role")
    }
    db.audit(identity["email"], "Suite sign-in", f"FastOffice organisation {identity['org_name']}")
    return RedirectResponse("/", status_code=303)


@rt("/auth/google")
def get(session, request):
    if not auth.google_enabled():
        return RedirectResponse("/login?error=Google+sign-in+is+not+configured", status_code=303)
    state = auth.new_state()
    session["google_oauth_state"] = state
    return RedirectResponse(auth.google_authorize_url(request, state), status_code=303)


@rt("/auth/google/callback")
def get(session, request, code: str = "", state: str = "", error: str = ""):
    expected = session.pop("google_oauth_state", None)
    if error or not code or not state or not secrets.compare_digest(state, expected or ""):
        return RedirectResponse("/login?error=Google+sign-in+failed", status_code=303)
    identity = auth.exchange_google(request, code)
    if not identity:
        return RedirectResponse("/login?error=Google+account+is+not+authorised", status_code=303)
    session["user"] = identity["email"]
    session["identity"] = {"name": identity["name"], "role": "planner"}
    db.audit(identity["email"], "Google sign-in", "Verified Google identity")
    return RedirectResponse("/", status_code=303)


@rt("/logout")
def get(session):
    session.clear()
    return RedirectResponse("/", status_code=303)


@rt("/")
def get(session, scenario: str = "baseline"):
    if not current_user(session):
        return landing_page()
    return guarded(session, "dashboard", scenario, views.dashboard)


@rt("/scenarios")
def get(session, scenario: str = "baseline"):
    return guarded(session, "scenarios", scenario, views.scenarios_view)


@rt("/plans")
def get(session, scenario: str = "baseline"):
    return guarded(session, "plans", scenario, views.plans_view)


@rt("/financials")
def get(session, scenario: str = "baseline"):
    return guarded(session, "financials", scenario, views.financials_view)


@rt("/variance")
def get(session, scenario: str = "baseline"):
    return guarded(session, "variance", scenario, lambda slug: views.variance_view(slug, "budget"))


@rt("/recurring")
def get(session, scenario: str = "baseline"):
    return guarded(session, "recurring", scenario, views.recurring_view)


@rt("/workflow")
def get(session, scenario: str = "baseline"):
    return guarded(session, "workflow", scenario, lambda _slug: views.workflow_view())


@rt("/integrations")
def get(session, scenario: str = "baseline"):
    return guarded(session, "integrations", scenario, lambda _slug: views.integrations_view())


@rt("/report")
def get(session, scenario: str = "baseline"):
    return guarded(session, "report", scenario, views.report_view)


@rt("/scenarios/{slug}/assumptions")
def post(
    session,
    slug: str,
    monthly_growth: str = "",
    gross_margin: str = "",
    payroll_growth: str = "",
    opex_growth: str = "",
    dso: str = "",
    inventory_days: str = "",
    dpo: str = "",
    capex: str = "",
    tax_rate: str = "",
    annual_interest: str = "",
    new_customers: str = "",
    churn_rate: str = "",
    mrr_per_customer: str = "",
):
    user = current_user(session)
    if not user:
        return Response("Unauthorized", status_code=401)
    values = {
        "monthly_growth": monthly_growth,
        "gross_margin": gross_margin,
        "payroll_growth": payroll_growth,
        "opex_growth": opex_growth,
        "dso": dso,
        "inventory_days": inventory_days,
        "dpo": dpo,
        "capex": capex,
        "tax_rate": tax_rate,
        "annual_interest": annual_interest,
        "new_customers": new_customers,
        "churn_rate": churn_rate,
        "mrr_per_customer": mrr_per_customer,
    }
    try:
        db.update_assumptions(slug, values, user)
        return views.scenario_editor(slug, "Scenario recalculated. Both financial integrity checks reconcile to zero.")
    except (ValueError, TypeError) as exc:
        return views.scenario_editor(slug, str(exc))


@rt("/workflow/{item_id}/advance")
def post(session, item_id: int):
    user = current_user(session)
    if not user:
        return Response("Unauthorized", status_code=401)
    db.advance_workflow(item_id, user)
    return views.workflow_table()


@rt("/integrations/refresh")
def post(session):
    if not current_user(session):
        return Response("Unauthorized", status_code=401)
    integrations.refresh_all()
    db.audit(current_user(session), "Sources refreshed", "FastERP, FastHRM, and FastCRM API probes completed")
    result = views.integrations_view("Source refresh completed. Live results or explicit fixture fallback are shown below.")
    return result[1]


@rt("/ai")
def post(session, question: str = "", scenario: str = "baseline"):
    if not current_user(session):
        return Response("Unauthorized", status_code=401)
    return views.ai_response(ai.answer(question, selected_scenario(scenario)))


@rt("/exports/financials.csv")
def get(session, scenario: str = "baseline"):
    if not current_user(session):
        return RedirectResponse("/login", status_code=303)
    slug = selected_scenario(scenario)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["FastFPA synthetic export", slug, "GBP", "Actuals through June 2026"])
    writer.writerow([
        "period", "actual", "revenue", "cogs", "payroll", "opex", "ebitda",
        "net_income", "cash", "ar", "inventory", "fixed_assets", "ap", "debt",
        "equity", "cfo", "cfi", "cff", "balance_check", "cash_check",
    ])
    for row in db.financial_periods(slug):
        writer.writerow([row[key] for key in (
            "period", "is_actual", "revenue", "cogs", "payroll", "opex",
            "ebitda", "net_income", "cash", "ar", "inventory", "fixed_assets",
            "ap", "debt", "equity", "cfo", "cfi", "cff", "balance_check", "cash_check",
        )])
    return Response(
        output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="fastfpa-{slug}-fy26.csv"'},
    )



register_seo_routes(app)

if __name__ == "__main__":
    serve(host="0.0.0.0", port=PORT, reload=False)
