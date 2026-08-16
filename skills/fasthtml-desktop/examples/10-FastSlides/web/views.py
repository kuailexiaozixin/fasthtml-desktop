"""Center-pane renderers for FastSlides."""
from __future__ import annotations

import markdown as md

from fasthtml.common import (
    Div, H1, H2, H3, P, Span, A, Form, Input, Textarea, Button, Select, Option, NotStr, Title,
)

import db


def _title(title, sub="", *actions):
    return Div(Div(H1(title), P(sub, cls="sub") if sub else None),
               Div(*actions) if actions else None, cls="page-title")


def _render_md(text):
    return NotStr(md.markdown(text or "", extensions=["fenced_code", "nl2br"]))


def slide_canvas(s, theme):
    layout = s["layout"]
    cls = f"slide theme-{theme} {layout}-layout"
    if layout == "title":
        return Div(H1(s["title"] or ""), Div(s["body"] or "", cls="sub"), cls=cls)
    if layout == "section":
        return Div(H1(s["title"] or ""), Div(_render_md(s["body"]), cls="body"), cls=cls)
    return Div(H2(s["title"] or ""), Div(_render_md(s["body"]), cls="body"), cls=cls)


# ---------- deck list -------------------------------------------------------

def decks_list():
    decks = db.presentations()
    cards = []
    for d in decks:
        cards.append(A(
            Div(H3(d["title"]), P(d["subtitle"] or ""), cls=f"deck-cover theme-{d['theme']}"),
            Div(Span(f"{d['n']} slides"), Span(d["theme"]), cls="deck-meta"),
            href=f"/deck/{d['id']}", cls="deck-card"))
    return (_title("My Decks", f"{len(decks)} presentations",
                   Div(Form(Button("＋ Blank deck", cls="btn", type="submit"), method="post", action="/deck/new", style="display:inline;"),
                       A("✨ New deck with AI", href="/generate", cls="btn primary"),
                       style="display:flex;gap:8px;")),
            Div(*cards, cls="deck-grid") if cards else Div(P("No decks yet — generate one with AI."), style="color:var(--text-mute);padding:40px;"))


# ---------- editor ----------------------------------------------------------

def deck_editor(pid, sid=None):
    d = db.presentation(pid)
    if not d:
        return _title("Deck not found"), P("No such deck.")
    slides = db.slides(pid)
    if not slides:
        return _title(d["title"]), P("This deck has no slides.")
    current = next((s for s in slides if s["id"] == sid), slides[0])

    thumbs = [A(Span(str(i + 1), cls="n"), Span(s["title"] or "(untitled)", cls="t"),
                href=f"/deck/{pid}?sid={s['id']}", cls=f"thumb {'active' if s['id'] == current['id'] else ''}")
              for i, s in enumerate(slides)]
    thumbs.append(Form(Button("＋ Add slide", cls="btn sm", type="submit", style="width:100%;"),
                       method="post", action=f"/deck/{pid}/add?after={current['id']}", style="margin-top:6px;"))

    edit = Form(
        Div(Span("Slide layout", style="font-size:11px;text-transform:uppercase;color:var(--text-mute);font-weight:600;")),
        Select(*[Option(l.title(), value=l, selected=(l == current["layout"]))
                 for l in ("title", "section", "content")], name="layout"),
        Div(Span("Title"), style="margin-top:8px;font-size:11px;text-transform:uppercase;color:var(--text-mute);font-weight:600;"),
        Input(name="title", value=current["title"] or ""),
        Div(Span("Body (Markdown)"), style="margin-top:8px;font-size:11px;text-transform:uppercase;color:var(--text-mute);font-weight:600;"),
        Textarea(current["body"] or "", name="body"),
        Div(Button("Save slide", cls="btn primary", type="submit"), style="margin-top:10px;"),
        method="post", action=f"/deck/{pid}/slide/{current['id']}", cls="edit-form")

    pos = [s["id"] for s in slides].index(current["id"])
    def _mv(label, direction, disabled):
        return Form(Button(label, cls="btn sm", type="submit", disabled=disabled),
                    method="post", action=f"/deck/{pid}/slide/{current['id']}/move?dir={direction}",
                    style="display:inline;")
    center = Div(
        Div(A("▶ Present", href=f"/present/{pid}", cls="btn primary"),
            _mv("↑", -1, pos == 0), _mv("↓", 1, pos == len(slides) - 1),
            Form(Button("🗑 Delete slide", cls="btn sm danger", type="submit", disabled=len(slides) <= 1),
                 method="post", action=f"/deck/{pid}/slide/{current['id']}/delete", style="display:inline;"),
            Span(f"Slide {pos+1} of {len(slides)}", style="color:var(--text-mute);margin-left:8px;"),
            cls="toolbar", style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;"),
        slide_canvas(current, d["theme"]),
        edit)
    return (_title(d["title"], d["subtitle"] or "", A("← All decks", href="/", cls="btn")),
            Div(Div(*thumbs, cls="thumbs"), center, cls="editor"))


# ---------- present ---------------------------------------------------------

def present_view(pid):
    d = db.presentation(pid)
    slides = db.slides(pid)
    if not d or not slides:
        return Div(P("Nothing to present."))
    deck = [Div(slide_canvas(s, d["theme"]), cls="present-slide",
                style="display:" + ("flex" if i == 0 else "none") + ";")
            for i, s in enumerate(slides)]
    js = """
var _i=0, _n=%d;
function _show(i){var sl=document.querySelectorAll('.present-slide');
  _i=Math.max(0,Math.min(_n-1,i));sl.forEach(function(s,j){s.style.display=(j===_i)?'flex':'none';});
  document.getElementById('pcount').textContent=(_i+1)+' / '+_n;}
document.addEventListener('keydown',function(e){
  if(e.key==='ArrowRight'||e.key===' ')_show(_i+1);
  else if(e.key==='ArrowLeft')_show(_i-1);
  else if(e.key==='Escape')window.location='/deck/%d';});
""" % (len(slides), pid)
    return (
        Title("FastSlides — Present"),
        NotStr("<style>" + _PRESENT_CSS + "</style>"),
        Div(*deck,
            Div(Button("‹", cls="pbtn", onclick="_show(_i-1)"),
                Span("1 / %d" % len(slides), id="pcount", cls="pcount"),
                Button("›", cls="pbtn", onclick="_show(_i+1)"),
                A("✕ Exit", href=f"/deck/{pid}", cls="pexit"), cls="pbar"),
            cls="present-stage"),
        NotStr(f"<script>{js}</script>"))


_PRESENT_CSS = """
*{box-sizing:border-box;} body{margin:0;background:#0b1020;height:100vh;font-family:ui-sans-serif,system-ui,sans-serif;}
.present-stage{height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;padding:24px;gap:16px;}
.present-slide{width:min(94vw,1280px);}
.slide{aspect-ratio:16/9;border-radius:16px;color:#fff;padding:52px 64px;display:flex;flex-direction:column;justify-content:center;width:100%;box-shadow:0 20px 60px rgba(0,0,0,.5);}
.slide.title-layout{align-items:center;text-align:center;} .slide.section-layout{justify-content:center;}
.slide h1{font-size:46px;margin:0 0 12px;line-height:1.1;} .slide h2{font-size:34px;margin:0 0 18px;}
.slide .body{font-size:24px;line-height:1.5;} .slide .body ul,.slide .body ol{padding-left:28px;} .slide .body li{margin:10px 0;}
.slide .body code{background:rgba(255,255,255,.15);padding:2px 6px;border-radius:5px;} .slide .body pre{background:rgba(0,0,0,.3);padding:16px;border-radius:8px;font-size:18px;}
.slide .sub{font-size:20px;opacity:.85;}
.theme-midnight{background:linear-gradient(135deg,#0f172a,#1e293b);} .theme-coral{background:linear-gradient(135deg,#db2777,#9d174d);}
.theme-forest{background:linear-gradient(135deg,#065f46,#047857);} .theme-mono{background:linear-gradient(135deg,#1f2937,#374151);}
.pbar{display:flex;align-items:center;gap:14px;color:#fff;}
.pbtn{background:rgba(255,255,255,.12);color:#fff;border:none;width:42px;height:42px;border-radius:50%;font-size:22px;cursor:pointer;}
.pbtn:hover{background:rgba(255,255,255,.25);} .pcount{color:#cbd5e1;font-size:14px;min-width:64px;text-align:center;}
.pexit{color:#cbd5e1;text-decoration:none;font-size:13px;margin-left:8px;border:1px solid rgba(255,255,255,.2);padding:6px 12px;border-radius:8px;}
"""


# ---------- generate --------------------------------------------------------

def generate_view(error=""):
    return (_title("Generate a deck with AI", "Describe your presentation; AI writes the slides."),
            Div(NotStr(f"<div class='notice'>⚠ {error}</div>") if error else "",
                Form(
                    Div(Span("What's the deck about?", style="font-weight:600;display:block;margin-bottom:8px;")),
                    Textarea("", name="topic", cls="askbox",
                             placeholder="e.g. A 6-slide pitch for a meal-kit startup targeting busy families",
                             style="min-height:90px;"),
                    Div(
                        Select(*[Option(t.title(), value=t) for t in db.THEMES], name="theme"),
                        Select(*[Option(f"{n} slides", value=str(n)) for n in (5, 6, 7, 8, 10)], name="count", selected="6"),
                        Button("✨ Generate deck", cls="btn primary", id="gen-btn", type="submit"),
                        cls="row"),
                    method="post", action="/generate", onsubmit="return genSubmit()"),
                cls="gen-card"),
            P("Without an API key, you can still create decks by hand from existing ones.",
              style="color:var(--text-mute);font-size:12px;margin-top:14px;"))
