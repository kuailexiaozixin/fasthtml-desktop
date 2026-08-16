"""FastSlides — an open-source presentation builder built with FastHTML.

A server-side, HTMX-driven port of the core of Frappe Slides: a deck library, a
slide editor, a present mode, and AI deck generation from a prompt.

Run:
    python web_app.py            # http://localhost:5013

Login: admin@fastslides.example / FastSlides2026$  (override via .env)
"""
from __future__ import annotations

import os
import json
import secrets
import uuid
import logging

from dotenv import load_dotenv
load_dotenv()

from fasthtml.common import (
    fast_app, serve, Div, H1, P, A, Form, Input, Button, NotStr,
    RedirectResponse, Script, Style, Link, Title,
)
from starlette.responses import StreamingResponse, Response
from starlette.responses import JSONResponse

import db
from web.layout import page, LAYOUT_CSS
from web import views, ai
from web.landing import landing_page
from web.developer import developer_page
from web import account_auth, google_auth, suite_auth
from web.api import api

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
logger = logging.getLogger("fastslides")

VALID_EMAIL = os.getenv("FASTSLIDES_ADMIN_EMAIL", "admin@fastslides.example")
VALID_PASSWORD = os.getenv("FASTSLIDES_ADMIN_PASSWORD", "FastSlides2026$")
ENV_LABEL = os.getenv("FASTSLIDES_ENV_LABEL", "FastSlides")
SECRET = os.getenv("FASTSLIDES_SECRET", secrets.token_hex(32))
PORT = int(os.getenv("FASTSLIDES_PORT", "5013"))

app, rt = fast_app(live=False, pico=False, secret_key=SECRET, hdrs=[Style(LAYOUT_CSS)])
app.mount("/api", api)


@rt("/swagger.json", methods=["GET"])
def swagger_schema():
    return JSONResponse(api.openapi())


@rt("/developers", methods=["GET"])
def developers():
    return developer_page()


account_auth.register_fasthtml_routes(rt, app_name="FastSlides", session_key="user", success_path="/")

# Provision the documented demo admin so the login modal works without an email
# verification round-trip (the auth store otherwise starts empty and registration
# cannot verify accounts locally). Override with FASTSLIDES_ADMIN_EMAIL/PASSWORD.
account_auth.accounts.ensure_account(VALID_EMAIL, VALID_PASSWORD, f"{ENV_LABEL} Admin", verified=True)
account_auth.set_demo_credentials(VALID_EMAIL, VALID_PASSWORD)


def _user(session):
    return session.get("user")


def _thread(session):
    if "thread" not in session:
        session["thread"] = uuid.uuid4().hex
    return session["thread"]


def _guard(session, active, builder):
    if not _user(session):
        return RedirectResponse("/login", status_code=303)
    content = builder() if callable(builder) else builder
    if not isinstance(content, tuple):
        content = (content,)
    return page(active, ENV_LABEL, _user(session), _thread(session), *content)


def _login_card(error="", email=""):
    return Title("FastSlides — Sign in"), Style(LAYOUT_CSS), Div(
        Form(H1("FastSlides"), P("Sign in to your decks"),
             Input(name="email", type="email", placeholder="Email", value=email, required=True),
             Input(name="password", type="password", placeholder="Password", required=True),
             P(error, cls="error") if error else None,
             Button("Sign in", cls="btn primary", type="submit"),
             P(NotStr("Demo: <code>admin@fastslides.example</code> / <code>FastSlides2026$</code>"), cls="hint"),
             method="post", action="/login", cls="login-card"), cls="login-wrap")


@rt("/login")
def get(session):
    if _user(session):
        return RedirectResponse("/", status_code=303)
    return _login_card()


@rt("/login")
def post(session, email: str = "", password: str = ""):
    if email.strip().lower() == VALID_EMAIL.lower() and password == VALID_PASSWORD:
        session["user"] = email.strip().lower()
        return RedirectResponse("/", status_code=303)
    return _login_card("Invalid email or password.", email)



@rt("/auth/google")
def google_start(session, request):
    if not google_auth.enabled():
        return RedirectResponse("/login?error=Google+sign-in+is+not+configured", status_code=303)
    state = google_auth.new_state()
    session["google_oauth_state"] = state
    return RedirectResponse(google_auth.authorize_url(request, state), status_code=303)

@rt("/auth/suite/callback")
def suite_callback(session, ticket: str = ""):
    identity = suite_auth.redeem(ticket, "slides")
    if not identity: return RedirectResponse("/login?error=FastOffice+session+is+invalid+or+expired", status_code=303)
    account_auth.accounts.link_google(identity["email"], identity["name"])
    session["user"], session["suite_identity"] = identity["email"], {k: identity[k] for k in ("sub","org_id","org_name","role")}
    return RedirectResponse("/", status_code=303)


@rt("/auth/google/callback")
def google_callback(session, request, code: str = "", state: str = "", error: str = ""):
    if error or not code or state != session.pop("google_oauth_state", None):
        return RedirectResponse("/login?error=Google+sign-in+failed", status_code=303)
    identity = google_auth.exchange(request, code)
    if not identity:
        return RedirectResponse("/login?error=Google+account+is+not+authorised", status_code=303)
    account_auth.accounts.link_google(identity["email"], identity["name"])
    session["user"] = identity["email"]
    return RedirectResponse("/", status_code=303)


@rt("/logout")
def get(session):
    session.pop("user", None)
    return RedirectResponse("/login", status_code=303)


@rt("/")
def get(session):
    if not _user(session):
        return landing_page()
    return _guard(session, "decks", views.decks_list)


@rt("/deck/{pid}")
def get(session, pid: int, sid: int | None = None):
    return _guard(session, "decks", lambda: views.deck_editor(pid, sid))


@rt("/deck/{pid}/slide/{sid}")
def post(session, pid: int, sid: int, title: str = "", body: str = "", layout: str = "content"):
    if not _user(session):
        return RedirectResponse("/login", status_code=303)
    with db.cursor() as conn:
        conn.execute("UPDATE slides SET title=?, body=?, layout=? WHERE id=? AND presentation_id=?",
                     (title, body, layout if layout in ("title", "section", "content") else "content", sid, pid))
    return RedirectResponse(f"/deck/{pid}?sid={sid}", status_code=303)


@rt("/deck/{pid}/add")
def post(session, pid: int, after: int | None = None):
    if not _user(session):
        return RedirectResponse("/login", status_code=303)
    nsid = db.add_slide(pid, after)
    return RedirectResponse(f"/deck/{pid}?sid={nsid}", status_code=303)


@rt("/deck/{pid}/slide/{sid}/delete")
def post(session, pid: int, sid: int):
    if not _user(session):
        return RedirectResponse("/login", status_code=303)
    db.delete_slide(sid)
    return RedirectResponse(f"/deck/{pid}", status_code=303)


@rt("/deck/{pid}/slide/{sid}/move")
def post(session, pid: int, sid: int, dir: int = 1):
    if not _user(session):
        return RedirectResponse("/login", status_code=303)
    db.move_slide(sid, -1 if dir < 0 else 1)
    return RedirectResponse(f"/deck/{pid}?sid={sid}", status_code=303)


@rt("/deck/new")
def post(session, title: str = ""):
    if not _user(session):
        return RedirectResponse("/login", status_code=303)
    pid = db.create_blank_deck(title)
    return RedirectResponse(f"/deck/{pid}", status_code=303)


@rt("/present/{pid}")
def get(session, pid: int):
    if not _user(session):
        return RedirectResponse("/login", status_code=303)
    return views.present_view(pid)


@rt("/generate")
def get(session):
    return _guard(session, "generate", lambda: views.generate_view())


@rt("/generate")
def post(session, topic: str = "", theme: str = "midnight", count: str = "6"):
    if not _user(session):
        return RedirectResponse("/login", status_code=303)
    topic = (topic or "").strip()
    if not topic:
        return _guard(session, "generate", lambda: views.generate_view("Please describe your deck first."))
    try:
        n = max(3, min(12, int(count)))
    except ValueError:
        n = 6
    try:
        title, subtitle, slides = ai.generate_deck(topic, n)
    except Exception as e:  # noqa: BLE001
        return _guard(session, "generate", lambda: views.generate_view(str(e)))
    pid = db.create_presentation(title, subtitle, theme, slides)
    return RedirectResponse(f"/deck/{pid}", status_code=303)


@rt("/ai")
def get(session):
    body = (views._title("AI Assistant", "Chat lives in the right rail. Generate full decks from the Generate page."),
            Div(NotStr(
                "<div class='gen-card'><h3>What you can ask</h3><ul style='line-height:1.8;'>"
                "<li>“Outline a 6-slide deck on remote-work culture.”</li>"
                "<li>“Suggest a strong closing slide for a sales pitch.”</li>"
                "<li>“Rewrite these bullets to be punchier.”</li></ul>"
                "<p>To build a complete deck, use <a href='/generate'>Generate with AI</a> — it writes every slide "
                "and drops you into the editor.</p></div>")))
    return _guard(session, "ai", body)


@rt("/guide")
def get(session):
    body = (views._title("User Guide", "How to drive FastSlides"), Div(NotStr("""
<div class='gen-card'><h3>My Decks</h3><p>Your presentations as themed cover tiles. Click one to edit.</p></div>
<div class='gen-card' style='margin-top:14px;'><h3>Editor</h3><p>Thumbnails on the left, the live slide canvas in the
centre, and an edit form (layout, title, Markdown body). Save to update the slide.</p></div>
<div class='gen-card' style='margin-top:14px;'><h3>Present</h3><p>Full-screen slide show — arrow keys / space to advance,
Esc to exit.</p></div>
<div class='gen-card' style='margin-top:14px;'><h3>Generate with AI</h3><p>Describe a deck and pick a theme + slide count;
AI writes the whole deck and opens it in the editor. Needs <code>MODEL_PROVIDER</code> + a key in <code>.env</code>.</p></div>
""")))
    return _guard(session, "guide", body)


@rt("/chat/new")
def get(session):
    session["thread"] = uuid.uuid4().hex
    return P("Ask for slide ideas and outlines.", cls="chat-empty-hint")


@rt("/chat/stream")
async def post(session, message: str = "", thread_id: str = ""):
    if not _user(session):
        return Response("Unauthorized", status_code=401)
    message = (message or "").strip()
    if not message:
        return Response("No message", status_code=400)
    tid = thread_id or _thread(session)

    async def gen():
        with db.cursor() as conn:
            conn.execute("INSERT INTO chat_messages(thread_id,role,content,created) VALUES(?,?,?,datetime('now'))",
                         (tid, "user", message))
        full = []
        async for chunk in ai.stream_chat(message):
            if chunk.startswith("data: "):
                try:
                    tok = json.loads(chunk[6:]).get("token")
                    if tok:
                        full.append(tok)
                except Exception:
                    pass
            yield chunk
        with db.cursor() as conn:
            conn.execute("INSERT INTO chat_messages(thread_id,role,content,created) VALUES(?,?,?,datetime('now'))",
                         (tid, "assistant", "".join(full)))

    return StreamingResponse(gen(), media_type="text/event-stream")


def _ensure_db():
    if not db.db_exists():
        logger.info("No database found — seeding sample decks…")
        import seed
        seed.build()


_ensure_db()

if __name__ == "__main__":
    logger.info("FastSlides on http://localhost:%s  (login %s)", PORT, VALID_EMAIL)
    serve(port=PORT, reload=os.getenv("FASTSLIDES_RELOAD", "0") == "1")
