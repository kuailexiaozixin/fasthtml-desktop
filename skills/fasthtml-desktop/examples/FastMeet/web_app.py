"""FastMeet — an open-source meeting scheduler built with FastHTML.

A server-side, HTMX-driven port of the schedule/rooms half of Frappe Meet:
a dashboard, upcoming/past meetings, meeting detail with participants & agenda,
a (simulated) room lobby, scheduling, and AI agenda/summary. Live WebRTC video
is out of scope for a server-rendered app — see docs/ROADMAP.md.

Run:
    python web_app.py            # http://localhost:5015

Login: admin@fastmeet.example / FastMeet2026$  (override via .env)
"""
from __future__ import annotations

import os
import json
import secrets
import uuid
import logging
import random
from datetime import datetime

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
logger = logging.getLogger("fastmeet")

VALID_EMAIL = os.getenv("FASTMEET_ADMIN_EMAIL", "admin@fastmeet.example")
VALID_PASSWORD = os.getenv("FASTMEET_ADMIN_PASSWORD", "FastMeet2026$")
ENV_LABEL = os.getenv("FASTMEET_ENV_LABEL", "FastMeet")
SECRET = os.getenv("FASTMEET_SECRET", secrets.token_hex(32))
PORT = int(os.getenv("FASTMEET_PORT", "5015"))

app, rt = fast_app(live=False, pico=False, secret_key=SECRET, hdrs=[Style(LAYOUT_CSS)])
app.mount("/api", api)


@rt("/swagger.json", methods=["GET"])
def swagger_schema():
    return JSONResponse(api.openapi())


@rt("/developers", methods=["GET"])
def developers():
    return developer_page()


account_auth.register_fasthtml_routes(rt, app_name="FastMeet", session_key="user", success_path="/")


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
    return Title("FastMeet — Sign in"), Style(LAYOUT_CSS), Div(
        Form(H1("FastMeet"), P("Sign in to your meetings"),
             Input(name="email", type="email", placeholder="Email", value=email, required=True),
             Input(name="password", type="password", placeholder="Password", required=True),
             P(error, cls="error") if error else None,
             Button("Sign in", cls="btn primary", type="submit"),
             P(NotStr("Demo: <code>admin@fastmeet.example</code> / <code>FastMeet2026$</code>"), cls="hint"),
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
    identity = suite_auth.redeem(ticket, "meet")
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
    return _guard(session, "dashboard", views.dashboard)


@rt("/meetings")
def get(session, scope: str = "upcoming"):
    return _guard(session, scope if scope in ("upcoming", "past") else "upcoming",
                  lambda: views.meetings_list(scope))


@rt("/meeting/{mid}")
def get(session, mid: int):
    return _guard(session, "upcoming", lambda: views.meeting_detail(mid))


@rt("/rsvp/{pid}")
def post(session, pid: int, rsvp: str = ""):
    if not _user(session):
        return Response("Unauthorized", status_code=401)
    mid = db.set_rsvp(pid, rsvp)
    return views.participants_card(mid) if mid else Response("ok")


@rt("/room/{mid}")
def get(session, mid: int):
    return _guard(session, "upcoming", lambda: views.room_view(mid))


@rt("/schedule")
def get(session):
    return _guard(session, "schedule", lambda: views.schedule_view())


@rt("/schedule")
def post(session, title: str = "", start: str = "", duration: str = "30", invites: str = "", agenda: str = ""):
    if not _user(session):
        return RedirectResponse("/login", status_code=303)
    title = (title or "").strip()
    if not title:
        return _guard(session, "schedule", lambda: views.schedule_view(error="Please give the meeting a title."))
    try:
        dur = max(5, min(480, int(duration)))
    except ValueError:
        dur = 30
    # parse datetime-local (YYYY-MM-DDTHH:MM); default to tomorrow 10:00
    start_time = None
    if start:
        try:
            start_time = datetime.strptime(start[:16], "%Y-%m-%dT%H:%M").strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            start_time = None
    if not start_time:
        start_time = (db.NOW.replace(hour=10, minute=0)).strftime("%Y-%m-%d %H:%M:%S")
    room = f"room-{random.randint(1000, 9999)}"
    with db.cursor() as conn:
        conn.execute("""INSERT INTO meetings(title,host,start_time,duration_min,status,room_code,agenda,has_recording)
                        VALUES (?,?,?,?,'Scheduled',?,?,0)""",
                     (title, db.HOST, start_time, dur, room, agenda.strip()))
        mid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("INSERT INTO participants(meeting_id,name,email,role,rsvp) VALUES (?,?,?,?,?)",
                     (mid, "You", db.HOST, "Host", "Accepted"))
        for em in [e.strip() for e in invites.split(",") if e.strip()]:
            nm = em.split("@")[0].replace(".", " ").title()
            conn.execute("INSERT INTO participants(meeting_id,name,email,role,rsvp) VALUES (?,?,?,?,?)",
                         (mid, nm, em, "Attendee", "No response"))
    return _guard(session, "schedule", lambda: views.schedule_view(done_id=mid))


@rt("/ai/agenda/{mid}")
def post(session, mid: int):
    if not _user(session):
        return Response("Unauthorized", status_code=401)
    try:
        return views.ai_panel(ai.generate_agenda(mid))
    except Exception as e:  # noqa: BLE001
        return views.ai_panel(str(e))


@rt("/ai/summary/{mid}")
def post(session, mid: int):
    if not _user(session):
        return Response("Unauthorized", status_code=401)
    try:
        return views.ai_panel(ai.summarise_meeting(mid))
    except Exception as e:  # noqa: BLE001
        return views.ai_panel(str(e))


@rt("/ai")
def get(session):
    body = (views._title("AI Assistant", "Chat lives in the right rail. Open a meeting for agenda & summary."),
            Div(NotStr(
                "<div class='gen-card'><h3>What you can ask</h3><ul style='line-height:1.8;'>"
                "<li>“What's on my schedule today?”</li><li>“Draft an agenda for a project kickoff.”</li>"
                "<li>“Summarise the API outage retro.”</li></ul>"
                "<p style='color:var(--text-mute)'>Slash-commands (no API key): "
                "<code>/today</code> <code>/upcoming</code>. Open any meeting to <b>generate an agenda</b> "
                "or <b>summarise</b> it.</p></div>")))
    return _guard(session, "ai", body)


@rt("/guide")
def get(session):
    body = (views._title("User Guide", "How to drive FastMeet"), Div(NotStr("""
<div class='gen-card'><h3>Dashboard</h3><p>Today's and upcoming meetings, live-now and recordings at a glance.</p></div>
<div class='gen-card' style='margin-top:14px;'><h3>Meetings</h3><p>Browse Upcoming and Past & Recordings. Open a meeting for
participants (with RSVPs), the agenda, the room code, and the recording/summary if it has ended.</p></div>
<div class='gen-card' style='margin-top:14px;'><h3>Room</h3><p>A lobby that shows who's present. Live audio/video needs WebRTC,
which a server-rendered app doesn't carry — the roadmap covers embedding a media layer.</p></div>
<div class='gen-card' style='margin-top:14px;'><h3>Schedule & AI</h3><p>Create meetings and invite people. AI can <b>generate an
agenda</b> from the title/participants and <b>summarise</b> past meetings. Needs <code>MODEL_PROVIDER</code> + a key in <code>.env</code>.</p></div>
""")))
    return _guard(session, "guide", body)


@rt("/chat/new")
def get(session):
    session["thread"] = uuid.uuid4().hex
    return P("Ask about your schedule, draft agendas or summarise meetings — or use /today /upcoming /help.", cls="chat-empty-hint")


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
        logger.info("No database found — seeding synthetic meetings…")
        import seed
        seed.build()


_ensure_db()

if __name__ == "__main__":
    logger.info("FastMeet on http://localhost:%s  (login %s)", PORT, VALID_EMAIL)
    serve(port=PORT, reload=os.getenv("FASTMEET_RELOAD", "0") == "1")
