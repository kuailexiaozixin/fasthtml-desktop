"""Anonymous FastFPA landing and sign-in surfaces."""
from fasthtml.common import *

from .layout import ACCENT, TINT
from .seo import seo_meta

PARTNERS = (
    ("SAASPASS", "https://saaspass.com/", "https://saaspass.com/_next/static/assets/0176aeff921f6359fee88e796be31ace.png", "Full-stack identity and access management spanning MFA, SSO, passwordless access and integration APIs."),
    ("Sixty Four", "https://sixtyfour.ee/", "https://sixtyfour.ee/favicon.ico", "A senior Tallinn technology studio delivering software, AI consultancy, service design and public-sector programmes."),
    ("EDI Labs", "https://edilabs.tech/", "https://edilabs.tech/static/favicon.svg", "AI and data engineering for document intelligence, forecasting, geospatial systems and agentic workflows."),
    ("Predictive Labs", "https://predictivelabs.ai/", "https://predictivelabs.ai/static/favicon.svg", "Auditable AI systems for health, defence, public management, mobility and financial services."),
    ("Consistente", "https://consistente.tech/", "https://consistente.tech/static/favicon.svg", "Enterprise AI delivery across financial services, healthcare, the public sector and technology."),
    ("Manmouna Technologies", "https://manmouna.tech/", "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='16' fill='%230B1E14'/%3E%3Cpath d='M32 12 52 32 32 52 12 32Z' fill='%2334D399'/%3E%3Cpath d='M32 22 42 32 32 42 22 32Z' fill='%230B1E14'/%3E%3C/svg%3E", "Auditable-by-design AI systems for European public services across health, defence, public management and mobility."),
)

LANDING_CSS = f"""
:root{{--accent:{ACCENT};--tint:{TINT};--ink:#102a2e;--muted:#64748b;--line:#e2e8f0}}*{{box-sizing:border-box}}body{{margin:0;background:#fff;color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,sans-serif}}.lp-nav{{height:70px;display:flex;align-items:center;justify-content:space-between;max-width:1180px;margin:auto;padding:0 24px;border-bottom:1px solid var(--line)}}.lp-brand{{display:flex;align-items:center;gap:10px;font-weight:800;color:var(--ink);text-decoration:none}}.lp-mark{{width:32px;height:32px;border-radius:10px;background:var(--accent);display:grid;place-items:center;color:#fff}}.lp-nav-actions{{display:flex;gap:14px;align-items:center}}.lp-link{{color:var(--muted);text-decoration:none;font-size:13px;font-weight:700}}.lp-btn{{display:inline-flex;align-items:center;justify-content:center;border:1px solid var(--line);border-radius:999px;padding:10px 17px;text-decoration:none;color:var(--ink);font-size:13px;font-weight:750;background:#fff}}.lp-btn.primary{{background:var(--accent);color:#fff;border-color:var(--accent)}}.lp-hero{{max-width:1180px;margin:auto;padding:92px 24px 62px;display:grid;grid-template-columns:1.05fr .95fr;gap:64px;align-items:center}}.lp-kicker{{color:var(--accent);text-transform:uppercase;letter-spacing:.16em;font-size:11px;font-weight:800}}.lp-hero h1{{font-size:clamp(44px,6vw,72px);line-height:1.02;letter-spacing:-.055em;margin:18px 0 24px}}.lp-hero p{{font-size:19px;line-height:1.65;color:var(--muted);max-width:680px}}.lp-actions{{display:flex;gap:11px;flex-wrap:wrap;margin-top:30px}}.mock{{border:1px solid var(--line);border-radius:22px;padding:13px;background:#fff;box-shadow:0 28px 70px rgba(15,118,110,.13)}}.mock-inner{{background:#f7faf9;border-radius:14px;padding:18px}}.mock-top{{display:flex;justify-content:space-between;align-items:center;margin-bottom:18px}}.mock-brand{{font-weight:800}}.mock-pill{{background:var(--tint);color:var(--accent);font-size:10px;padding:5px 8px;border-radius:99px;font-weight:800}}.mock-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:9px}}.mock-card{{background:#fff;border:1px solid var(--line);border-radius:10px;padding:12px}}.mock-card span{{font-size:9px;color:var(--muted);text-transform:uppercase}}.mock-card strong{{display:block;font-size:20px;margin-top:5px}}.mock-chart{{height:120px;background:#fff;border:1px solid var(--line);border-radius:10px;margin-top:9px;padding:14px;display:flex;align-items:flex-end;gap:7px}}.mock-bar{{flex:1;background:var(--accent);border-radius:4px 4px 1px 1px;opacity:.82}}.lp-band{{background:var(--tint);border-block:1px solid #d6eee7}}.lp-grid{{max-width:1180px;margin:auto;padding:64px 24px;display:grid;grid-template-columns:repeat(3,1fr);gap:16px}}.lp-card{{background:rgba(255,255,255,.88);border:1px solid #d6eee7;border-radius:18px;padding:25px}}.lp-card b{{color:var(--accent);font-size:11px}}.lp-card h2{{font-size:19px;margin:26px 0 9px}}.lp-card p{{font-size:14px;line-height:1.6;color:var(--muted);margin:0}}.lp-partners{{max-width:1180px;margin:auto;padding:74px 24px;scroll-margin-top:80px}}.lp-partners h2{{font-size:34px;letter-spacing:-.035em;margin:10px 0 14px}}.lp-partners>p{{max-width:720px;color:var(--muted);line-height:1.7}}.lp-partner-grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-top:30px}}.lp-partner{{color:var(--ink);text-decoration:none;border:1px solid var(--line);border-radius:17px;padding:18px;min-width:0}}.lp-partner img{{width:44px;height:44px;object-fit:contain}}.lp-partner small{{display:block;color:var(--accent);font-weight:800;text-transform:uppercase;letter-spacing:.08em;margin-top:15px}}.lp-partner h3{{margin:8px 0}}.lp-partner p{{font-size:12px;line-height:1.55;color:var(--muted)}}.lp-section{{max-width:1180px;margin:auto;padding:74px 24px;display:grid;grid-template-columns:1fr 1fr;gap:50px}}.lp-section h2{{font-size:34px;letter-spacing:-.035em;margin:0 0 14px}}.lp-section p,.lp-list{{color:var(--muted);line-height:1.7}}.lp-list{{display:grid;gap:11px}}.lp-list div:before{{content:"✓";color:var(--accent);font-weight:900;margin-right:10px}}.lp-footer{{max-width:1180px;margin:auto;border-top:1px solid var(--line);padding:28px 24px 44px;display:flex;justify-content:space-between;color:var(--muted);font-size:12px}}.login{{min-height:100vh;display:grid;place-items:center;background:var(--tint);padding:20px}}.login-card{{width:min(430px,100%);background:#fff;border:1px solid #d6eee7;border-radius:20px;padding:30px;box-shadow:0 20px 60px rgba(15,118,110,.12)}}.login-card h1{{margin:0 0 8px}}.login-card>p{{color:var(--muted);line-height:1.5}}.login-actions{{display:grid;gap:10px;margin:24px 0}}.login-note{{font-size:11px;color:var(--muted);text-align:center}}.lp-pricing{{max-width:1180px;margin:auto;padding:72px 24px;scroll-margin-top:80px}}.lp-pricing-head{{max-width:720px}}.lp-pricing-head h2{{font-size:32px;letter-spacing:-.03em;margin:10px 0 12px}}.lp-pricing-head p{{color:var(--muted);line-height:1.65;margin:0}}.lp-pricing-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin-top:32px}}.lp-pricing-card{{border:1px solid var(--line);border-radius:18px;padding:26px;background:#fff}}.lp-pricing-eyebrow{{color:var(--accent);font-size:10px;font-weight:750;text-transform:uppercase;letter-spacing:.1em}}.lp-pricing-card h3{{font-size:22px;margin:14px 0 8px}}.lp-pricing-price{{font-size:36px;font-weight:750;letter-spacing:-.03em;margin:8px 0 12px}}.lp-pricing-card>p:last-child{{color:var(--muted);line-height:1.6;margin:0}}@media(max-width:980px){{.lp-partner-grid{{grid-template-columns:repeat(2,minmax(0,1fr))}}}}@media(max-width:820px){{.lp-hero,.lp-section{{grid-template-columns:1fr}}.lp-hero{{padding-top:66px}}.lp-grid,.lp-partner-grid,.lp-pricing-grid{{grid-template-columns:1fr}}.lp-nav .lp-link{{display:none}}.lp-footer{{display:grid;gap:10px}}}}
"""



def pricing_section():
    return Section(
        Div(
            Span("Pricing", cls="lp-kicker"),
            H2("Simple pricing for every FastSME product."),
            P("Every Fast* product uses the same two options: bring your own cloud for free, or host with us for €1 per month."),
            cls="lp-pricing-head",
        ),
        Div(
            Article(
                Span("BYOC", cls="lp-pricing-eyebrow"),
                H3("Bring Your Own Cloud"),
                P("Free", cls="lp-pricing-price"),
                P("Self-host on your own infrastructure or cloud. Full control of data and upgrades. No per-seat platform fee."),
                cls="lp-pricing-card",
            ),
            Article(
                Span("Hosted", cls="lp-pricing-eyebrow"),
                H3("Host with us"),
                P("€1 / month", cls="lp-pricing-price"),
                P("We run the product for you on FastSME-managed infrastructure. €1 per product per month."),
                cls="lp-pricing-card",
            ),
            cls="lp-pricing-grid",
        ),
        id="pricing", cls="lp-pricing",
    )

def partner_section():
    return Section(
        Span("Partners", cls="lp-kicker"),
        H2("Connect with trusted integration specialists."),
        P("Identity, software delivery, data engineering and applied-AI expertise for FastSME implementations."),
        Div(*[
            A(Img(src=logo, alt=f"{name} logo", loading="lazy"), Small("Integration Partner"), H3(name), P(description), href=url, target="_blank", rel="noopener noreferrer", cls="lp-partner")
            for name, url, logo, description in PARTNERS
        ], cls="lp-partner-grid"),
        id="partners", cls="lp-partners",
    )


def landing_page():
    heights = (38, 53, 47, 67, 61, 78, 72, 88, 81, 93, 86, 100)
    features = (
        ("01", "Plan the full financial picture", "Connect revenue, workforce, operating costs, working capital, capex, debt, tax, and cash in balanced statements."),
        ("02", "Compare decisions before making them", "Clone Baseline, Upside, and Downside scenarios, change governed assumptions, and see every monthly impact."),
        ("03", "Explain performance with evidence", "Trace actual-versus-plan variances to drivers, source systems, versions, and reviewable management commentary."),
    )
    return Html(
        Head(
            Title("FastFPA · Financial planning & analysis"),
            Meta(charset="utf-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1"),
            Meta(name="description", content="Driver-based budgets, forecasts, scenarios, full financial statements, and performance analysis for SMEs."),
            *seo_meta(title="FastFPA · Financial planning & analysis"),
            Link(rel="icon", href="/static/favicon.svg"),
            Link(rel="preconnect", href="https://fonts.googleapis.com"),
            Link(rel="stylesheet", href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"),
            Style(LANDING_CSS),
        ),
        Body(
            Nav(
                A(Span("F", cls="lp-mark"), Span("FastFPA"), href="/", cls="lp-brand"),
                Div(A("Pricing", href="#pricing", cls="lp-link"), A("Partners", href="#partners", cls="lp-link"), A("Developers", href="/developers", cls="lp-link"), A("FastSME suite", href="https://fastsme.com/products", cls="lp-link"), A("Sign In", href="/login", cls="lp-btn"), cls="lp-nav-actions"),
                cls="lp-nav",
            ),
            Main(
                Section(
                    Div(
                        Span("Financial planning & analysis", cls="lp-kicker"),
                        H1("Plan forward with numbers everyone can trust."),
                        P("Connect actuals, operational drivers, budgets, forecasts, scenarios, and performance reviews in one governed planning workspace."),
                        Div(A("Sign In with FastOffice", href="/auth/fastoffice", cls="lp-btn primary"), A("Explore synthetic demo", href="/demo", cls="lp-btn"), cls="lp-actions"),
                    ),
                    Div(
                        Div(
                            Div(Span("FastFPA", cls="mock-brand"), Span("Q3 Baseline", cls="mock-pill"), cls="mock-top"),
                            Div(
                                Div(Span("FY26 revenue"), Strong("£3.80m"), cls="mock-card"),
                                Div(Span("EBITDA margin"), Strong("9.1%"), cls="mock-card"),
                                cls="mock-grid",
                            ),
                            Div(*[Div(cls="mock-bar", style=f"height:{height}%") for height in heights], cls="mock-chart"),
                            cls="mock-inner",
                        ),
                        cls="mock",
                    ),
                    cls="lp-hero",
                ),
                Section(Div(*[Article(B(num), H2(title), P(copy), cls="lp-card") for num, title, copy in features], cls="lp-grid"), cls="lp-band"),
                pricing_section(),
                partner_section(),
                Section(
                    Div(H2("The planning layer above your systems of record."), P("FastFPA consumes synthetic FastERP financials, FastHRM workforce data, and FastCRM commercial pipeline. It exchanges governed workbooks with FastSheets, publishes through FastOffice, and opens advanced exploration in FastInsights.")),
                    Div(Div("Balanced P&L, balance sheet, and cash flow"), Div("Driver-based rolling forecast and scenarios"), Div("Department submissions, approvals, and audit trail"), Div("Explanatory AI that cannot approve or publish"), cls="lp-list"),
                    cls="lp-section",
                ),
            ),
            Footer(Span("FastFPA is open-source software in the FastSME suite."), A("View source on GitHub", href="https://github.com/predictivelabsai/FastFPA"), cls="lp-footer"),
        ),
    )


def login_page(error: str = ""):
    return Html(
        Head(Title("Sign in · FastFPA"), Meta(name="viewport", content="width=device-width, initial-scale=1"), Style(LANDING_CSS)),
        Body(
            Div(
                Div(
                    A("← FastFPA", href="/", cls="lp-brand"),
                    H1("Welcome to FastFPA"),
                    P("Use your FastOffice account for the connected suite experience."),
                    P(error, style="color:#b42318") if error else None,
                    Div(
                        A("Continue with FastOffice", href="/auth/fastoffice", cls="lp-btn primary"),
                        A("Continue with Google", href="/auth/google", cls="lp-btn"),
                        A("Explore synthetic demo", href="/demo", cls="lp-btn"),
                        cls="login-actions",
                    ),
                    P("The public demo contains deterministic synthetic data only.", cls="login-note"),
                    cls="login-card",
                ),
                cls="login",
            )
        ),
    )
