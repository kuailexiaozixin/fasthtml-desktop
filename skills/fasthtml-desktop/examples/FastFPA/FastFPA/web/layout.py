"""FastFPA application shell and visual system."""
from __future__ import annotations

from fasthtml.common import *

ACCENT = "#0f766e"
TINT = "#f0fdfa"

CSS = """
:root{--accent:#0f766e;--accent2:#115e59;--tint:#f0fdfa;--ink:#102a2e;--muted:#64748b;--line:#e2e8f0;--panel:#fff;--bg:#f7faf9;--good:#15803d;--bad:#b42318;--warn:#b45309}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:Inter,ui-sans-serif,system-ui,-apple-system,sans-serif;font-size:14px}a{color:inherit}.app{min-height:100vh;display:grid;grid-template-columns:230px minmax(0,1fr) 300px}.sidebar{position:sticky;top:0;height:100vh;background:#0b2f31;color:#d8eeee;padding:22px 15px;display:flex;flex-direction:column}.brand{display:flex;align-items:center;gap:11px;color:#fff;text-decoration:none;font-size:17px;font-weight:800;padding:4px 8px 24px}.brand-mark{width:34px;height:34px;border-radius:11px;background:#21a179;display:grid;place-items:center;font-weight:900}.nav-label{font-size:10px;text-transform:uppercase;letter-spacing:.13em;color:#80a9aa;margin:18px 10px 7px}.nav-link{display:flex;align-items:center;gap:10px;padding:10px 11px;border-radius:10px;color:#bdd4d5;text-decoration:none;font-weight:650;margin:2px 0}.nav-link:hover,.nav-link.active{background:rgba(255,255,255,.11);color:#fff}.nav-icon{width:24px;color:#7fd5bd;font-weight:800}.sidebar-foot{margin-top:auto;border-top:1px solid rgba(255,255,255,.12);padding:16px 8px 0;color:#91b4b5;font-size:12px}.main{min-width:0}.topbar{height:68px;background:#fff;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;padding:0 28px;position:sticky;top:0;z-index:4}.top-title{font-weight:760;font-size:16px}.top-actions{display:flex;align-items:center;gap:12px}.badge{display:inline-flex;align-items:center;gap:6px;padding:6px 9px;border-radius:999px;background:var(--tint);color:var(--accent);font-size:11px;font-weight:750}.dot{width:7px;height:7px;border-radius:50%;background:#16a34a}.avatar{width:34px;height:34px;border-radius:50%;background:#d9eee8;display:grid;place-items:center;color:var(--accent);font-weight:800}.content{padding:26px 28px 56px;max-width:1450px;margin:auto}.page-head{display:flex;align-items:flex-start;justify-content:space-between;gap:18px;margin-bottom:22px}.page-head h1{margin:0 0 5px;font-size:28px;letter-spacing:-.035em}.page-head p{margin:0;color:var(--muted);line-height:1.5}.actions{display:flex;gap:9px;flex-wrap:wrap}.btn{display:inline-flex;align-items:center;justify-content:center;gap:7px;border:1px solid var(--line);border-radius:9px;background:#fff;color:var(--ink);padding:9px 13px;text-decoration:none;font:inherit;font-weight:700;cursor:pointer}.btn:hover{border-color:#9dbab4}.btn.primary{background:var(--accent);color:#fff;border-color:var(--accent)}.btn.soft{background:var(--tint);color:var(--accent);border-color:#cce7df}.btn.small{padding:6px 9px;font-size:12px}.scenario-tabs{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:20px}.scenario-tab{padding:7px 11px;border:1px solid var(--line);border-radius:999px;text-decoration:none;background:#fff;color:var(--muted);font-weight:700;font-size:12px}.scenario-tab.active{background:var(--ink);border-color:var(--ink);color:#fff}.grid{display:grid;gap:15px}.kpi-grid{grid-template-columns:repeat(4,minmax(0,1fr));margin-bottom:15px}.two-col{grid-template-columns:minmax(0,1.55fr) minmax(280px,.85fr)}.three-col{grid-template-columns:repeat(3,minmax(0,1fr))}.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:18px;box-shadow:0 1px 2px rgba(15,23,42,.03)}.card h2,.card h3{margin:0}.card-head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:16px}.card-head h2{font-size:15px}.kpi-label{color:var(--muted);font-size:12px;font-weight:700}.kpi-value{font-size:27px;letter-spacing:-.035em;font-weight:800;margin:8px 0 5px}.kpi-delta{font-size:12px;font-weight:700}.positive{color:var(--good)}.negative{color:var(--bad)}.muted{color:var(--muted)}.mini-chart{height:212px;display:flex;align-items:flex-end;gap:7px;padding:12px 2px 24px;border-bottom:1px solid var(--line);position:relative}.bar-wrap{height:100%;flex:1;display:flex;align-items:flex-end;position:relative}.bar{width:100%;min-height:3px;background:linear-gradient(180deg,#2cb98f,var(--accent));border-radius:5px 5px 1px 1px}.bar.actual{background:#94a3b8}.bar-label{position:absolute;top:calc(100% + 6px);width:100%;text-align:center;font-size:10px;color:var(--muted)}.legend{display:flex;gap:14px;margin-top:14px;color:var(--muted);font-size:11px}.legend span:before{content:"";width:8px;height:8px;border-radius:2px;display:inline-block;background:var(--accent);margin-right:5px}.legend span.actual:before{background:#94a3b8}.integrity{display:grid;grid-template-columns:1fr 1fr;gap:10px}.check{border:1px solid #cce7df;background:var(--tint);border-radius:11px;padding:13px}.check strong{display:block;color:var(--accent);font-size:18px;margin-bottom:3px}.table-wrap{overflow:auto;border:1px solid var(--line);border-radius:12px;background:#fff}table{border-collapse:collapse;width:100%;font-size:12px}th,td{padding:10px 12px;border-bottom:1px solid #edf1f4;text-align:right;white-space:nowrap}th{background:#f8fafc;color:#64748b;font-size:10px;text-transform:uppercase;letter-spacing:.05em;position:sticky;top:0}th:first-child,td:first-child{text-align:left;position:sticky;left:0;background:inherit}tbody tr:hover{background:#fbfdfc}.section-row td{font-weight:800;background:#f0fdfa;color:var(--accent)}.total-row td{font-weight:800;border-top:1px solid #9dbab4;background:#fbfdfc}.status{display:inline-flex;padding:4px 7px;border-radius:999px;font-size:10px;font-weight:800;background:#eef2f7;color:#475569}.status.Approved,.status.Connected{background:#dcfce7;color:#166534}.status.Submitted,.status.Ready{background:#dbeafe;color:#1d4ed8}.status.In-review,.status.Working{background:#fef3c7;color:#92400e}.status.Draft,.status.Fixture-fallback{background:#f1f5f9;color:#475569}.form-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.field label{display:block;color:var(--muted);font-size:11px;font-weight:750;margin-bottom:5px}.field-wrap{display:flex}.field input,.question{width:100%;border:1px solid #cbd5e1;border-radius:8px;padding:9px 10px;font:inherit;background:#fff}.field input{border-radius:8px 0 0 8px}.unit{border:1px solid #cbd5e1;border-left:0;border-radius:0 8px 8px 0;padding:9px;background:#f8fafc;color:var(--muted);font-size:11px}.notice{border-left:3px solid var(--accent);background:var(--tint);padding:11px 13px;border-radius:6px;margin-bottom:14px;color:var(--accent2)}.integration-card{display:flex;gap:13px;align-items:flex-start}.product-icon{width:38px;height:38px;border-radius:11px;background:var(--tint);color:var(--accent);display:grid;place-items:center;font-weight:900;flex:none}.integration-card h3{font-size:14px;margin-bottom:4px}.integration-card p{font-size:12px;color:var(--muted);margin:0;line-height:1.45}.rail{position:sticky;top:0;height:100vh;background:#fff;border-left:1px solid var(--line);display:flex;flex-direction:column}.rail-head{padding:22px 20px 14px;border-bottom:1px solid var(--line)}.rail-head h2{font-size:15px;margin:0 0 4px}.rail-head p{font-size:11px;color:var(--muted);margin:0;line-height:1.4}.rail-body{padding:18px;overflow:auto;flex:1}.prompt{border:1px solid var(--line);border-radius:12px;padding:12px;margin-bottom:10px;background:#f8fafc;line-height:1.5;font-size:12px}.prompt.ai{background:var(--tint);border-color:#cce7df}.rail-form{padding:14px;border-top:1px solid var(--line)}.rail-form textarea{width:100%;resize:none;border:1px solid #cbd5e1;border-radius:9px;padding:9px;font:inherit;min-height:70px}.rail-form button{width:100%;margin-top:8px}.empty{padding:34px;text-align:center;color:var(--muted)}.link-list{display:grid;gap:8px}.link-row{display:flex;align-items:center;justify-content:space-between;text-decoration:none;padding:10px;border:1px solid var(--line);border-radius:9px;background:#fff}.link-row:hover{border-color:#9dbab4}.report-title{text-align:center;padding:20px}.report-title h1{font-size:25px}.report-meta{display:flex;justify-content:center;gap:18px;flex-wrap:wrap;color:var(--muted);font-size:11px}.mobile-menu{display:none}
@media(max-width:1180px){.app{grid-template-columns:210px minmax(0,1fr)}.rail{display:none}.kpi-grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:760px){.app{display:block}.sidebar{position:relative;height:auto;padding:12px}.brand{padding-bottom:8px}.nav-label,.sidebar-foot{display:none}.sidebar nav{display:flex;overflow:auto}.nav-link{white-space:nowrap}.nav-icon{display:none}.topbar{padding:0 16px}.content{padding:18px 14px 40px}.page-head{display:block}.actions{margin-top:14px}.kpi-grid,.two-col,.three-col,.form-grid{grid-template-columns:1fr}.kpi-value{font-size:24px}.card{padding:14px}.mini-chart{height:180px}}
@media print{.sidebar,.topbar,.rail,.actions,.scenario-tabs{display:none!important}.app{display:block}.content{padding:0}.card{box-shadow:none;break-inside:avoid}.table-wrap{overflow:visible}}
"""

NAV = (
    ("Overview", (("dashboard", "◫", "Dashboard", "/"), ("scenarios", "◇", "Scenarios", "/scenarios"), ("financials", "≡", "Financials", "/financials"), ("recurring", "↻", "Recurring revenue", "/recurring"))),
    ("Plan & review", (("plans", "✎", "Drivers", "/plans"), ("variance", "↕", "Variance", "/variance"), ("workflow", "✓", "Workflow", "/workflow"))),
    ("Connect", (("integrations", "⇄", "Integrations", "/integrations"), ("report", "▤", "Management pack", "/report"))),
)


def page(active: str, user: str, scenario: str, *content):
    links = []
    for label, items in NAV:
        links.append(Div(label, cls="nav-label"))
        links.extend(
            A(Span(icon, cls="nav-icon"), title, href=href, cls=f"nav-link {'active' if key == active else ''}")
            for key, icon, title, href in items
        )
    return (
        Title(f"FastFPA · {active.title()}"),
        Div(
            Aside(
                A(Span("F", cls="brand-mark"), Span("FastFPA"), href="/", cls="brand"),
                Nav(*links),
                Div(P("FastSME suite"), A("Open FastOffice →", href="https://office.fastsme.com", target="_blank"), cls="sidebar-foot"),
                cls="sidebar",
            ),
            Main(
                Header(
                    Div(active.replace("-", " ").title(), cls="top-title"),
                    Div(
                        Span(Span(cls="dot"), "Synthetic data", cls="badge"),
                        Div((user[:1] or "F").upper(), cls="avatar", title=user),
                        cls="top-actions",
                    ),
                    cls="topbar",
                ),
                Div(*content, cls="content"),
                cls="main",
            ),
            Aside(
                Div(H2("Finance copilot"), P("Explains and drafts only · grounded in the selected scenario"), cls="rail-head"),
                Div(
                    Div("Try “Explain the cash outlook” or “Draft a downside response”.", cls="prompt"),
                    Div(id="ai-response"),
                    cls="rail-body",
                ),
                Form(
                    Textarea(name="question", placeholder="Ask about this plan…"),
                    Input(type="hidden", name="scenario", value=scenario),
                    Button("Ask FastFPA", type="submit", cls="btn primary"),
                    hx_post="/ai", hx_target="#ai-response", hx_swap="innerHTML",
                    cls="rail-form",
                ),
                cls="rail",
            ),
            cls="app",
        ),
    )
