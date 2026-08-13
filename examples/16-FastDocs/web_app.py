"""FastDocs — an open-source document editor built with FastHTML.

A server-side, HTMX-driven port of the core of Frappe Writer: a folder-organised
document library, a block editor (headings, lists, quotes, code), reusable
templates, version history, read-only public share links, and an AI writing
assistant that can draft a whole document from a prompt.

Run:
    python web_app.py            # http://localhost:5016

Login: admin@fastdocs.example / FastDocs2026$  (override via .env)
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
logger = logging.getLogger("fastdocs")

VALID_EMAIL = os.getenv("FASTDOCS_ADMIN_EMAIL", "admin@fastdocs.example")
VALID_PASSWORD = os.getenv("FASTDOCS_ADMIN_PASSWORD", "FastDocs2026$")
ENV_LABEL = os.getenv("FASTDOCS_ENV_LABEL", "FastDocs")
SECRET = os.getenv("FASTDOCS_SECRET", secrets.token_hex(32))
PORT = int(os.getenv("FASTDOCS_PORT", "5016"))

app, rt = fast_app(live=False, pico=False, secret_key=SECRET, hdrs=[Style(LAYOUT_CSS)])
app.mount("/api", api)


@rt("/swagger.json", methods=["GET"])
def swagger_schema():
    return JSONResponse(api.openapi())


@rt("/developers", methods=["GET"])
def developers():
    return developer_page()


account_auth.register_fasthtml_routes(rt, app_name="FastDocs", session_key="user", success_path="/")
# 离线演示：把文档口令种成**已验证**账号，并让登录弹窗给出一键填充按钮。
# 缺此两行时 accounts 表为空 -> 弹窗登录必报
#   "Invalid email, password, or unverified account"。
account_auth.accounts.ensure_account(VALID_EMAIL, VALID_PASSWORD, f"{ENV_LABEL} Admin", verified=True)
account_auth.set_demo_credentials(VALID_EMAIL, VALID_PASSWORD)


def _user(session):
    return session.get("user")


def _thread(session):
    if "thread" not in session:
        session["thread"] = uuid.uuid4().hex
    return session["thread"]


def _guard(session, active, builder, active_doc=None):
    if not _user(session):
        return RedirectResponse("/login", status_code=303)
    content = builder() if callable(builder) else builder
    if not isinstance(content, tuple):
        content = (content,)
    return page(active, ENV_LABEL, _user(session), _thread(session), *content, active_doc=active_doc)


def _authed(session):
    return bool(_user(session))


def _login_card(error="", email=""):
    return Title("FastDocs — Sign in"), Style(LAYOUT_CSS), Div(
        Form(H1("FastDocs"), P("Sign in to your documents"),
             Input(name="email", type="email", placeholder="Email", value=email, required=True),
             Input(name="password", type="password", placeholder="Password", required=True),
             P(error, cls="error") if error else None,
             Button("Sign in", cls="btn primary", type="submit"),
             P(NotStr("Demo: <code>admin@fastdocs.example</code> / <code>FastDocs2026$</code>"), cls="hint"),
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
    identity = suite_auth.redeem(ticket, "docs")
    if not identity:
        return RedirectResponse("/login?error=FastOffice+session+is+invalid+or+expired", status_code=303)
    account_auth.accounts.link_google(identity["email"], identity["name"])
    session["user"] = identity["email"]
    session["suite_identity"] = {key: identity[key] for key in ("sub", "org_id", "org_name", "role")}
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


# --- document library -------------------------------------------------------

@rt("/")
def get(session):
    if not _user(session):
        return landing_page()
    return _guard(session, "docs", views.docs_list)


@rt("/new")
def get(session):
    if not _authed(session):
        return RedirectResponse("/login", status_code=303)
    doc_id = db.create_blank_doc(None, "Untitled document")
    return RedirectResponse(f"/doc/{doc_id}", status_code=303)


@rt("/new")
def post(session, title: str = "", folder_id: str = ""):
    if not _authed(session):
        return RedirectResponse("/login", status_code=303)
    fid = int(folder_id) if folder_id else None
    doc_id = db.create_blank_doc(fid, title or "Untitled document")
    return RedirectResponse(f"/doc/{doc_id}", status_code=303)


@rt("/folder/new")
def post(session, name: str = ""):
    if not _authed(session):
        return RedirectResponse("/login", status_code=303)
    if (name or "").strip():
        db.create_folder(name)
    return RedirectResponse("/", status_code=303)


# --- editor -----------------------------------------------------------------

@rt("/doc/{doc_id}")
def get(session, doc_id: int):
    return _guard(session, "docs", lambda: views.doc_detail(doc_id), active_doc=doc_id)


@rt("/doc/{doc_id}/main")
def get(session, doc_id: int, editing: int | None = None):
    if not _authed(session):
        return RedirectResponse("/login", status_code=303)
    return views.doc_main(doc_id, editing)


@rt("/doc/{doc_id}/title")
def post(session, doc_id: int, title: str = ""):
    if not _authed(session):
        return Response("Unauthorized", status_code=401)
    db.rename_document(doc_id, title)
    return views.doc_main(doc_id)


@rt("/doc/{doc_id}/block/add")
def post(session, doc_id: int, type: str = "paragraph", after: int | None = None):
    if not _authed(session):
        return Response("Unauthorized", status_code=401)
    nbid = db.add_block(doc_id, after, type)
    editing = None if type == "divider" else nbid
    return views.doc_main(doc_id, editing)


@rt("/doc/{doc_id}/block/{bid}")
def post(session, doc_id: int, bid: int, content: str = "", type: str = "paragraph"):
    if not _authed(session):
        return Response("Unauthorized", status_code=401)
    db.update_block(bid, content, type)
    return views.doc_main(doc_id)


@rt("/doc/{doc_id}/block/{bid}/move")
def post(session, doc_id: int, bid: int, dir: int = 1):
    if not _authed(session):
        return Response("Unauthorized", status_code=401)
    db.move_block(bid, -1 if dir < 0 else 1)
    return views.doc_main(doc_id)


@rt("/doc/{doc_id}/block/{bid}/delete")
def post(session, doc_id: int, bid: int):
    if not _authed(session):
        return Response("Unauthorized", status_code=401)
    db.delete_block(bid)
    return views.doc_main(doc_id)


# --- publish / read / versions (plain forms → full-page redirects) ----------

@rt("/doc/{doc_id}/publish")
def post(session, doc_id: int):
    if not _authed(session):
        return RedirectResponse("/login", status_code=303)
    db.publish(doc_id)
    return RedirectResponse(f"/doc/{doc_id}", status_code=303)


@rt("/doc/{doc_id}/unpublish")
def post(session, doc_id: int):
    if not _authed(session):
        return RedirectResponse("/login", status_code=303)
    db.unpublish(doc_id)
    return RedirectResponse(f"/doc/{doc_id}", status_code=303)


@rt("/doc/{doc_id}/snapshot")
def post(session, doc_id: int):
    if not _authed(session):
        return RedirectResponse("/login", status_code=303)
    db.snapshot_version(doc_id, manual=True)
    return RedirectResponse(f"/doc/{doc_id}/versions", status_code=303)


@rt("/doc/{doc_id}/versions")
def get(session, doc_id: int):
    return _guard(session, "docs", lambda: views.versions_view(doc_id), active_doc=doc_id)


@rt("/version/{vid}/restore")
def post(session, vid: int):
    if not _authed(session):
        return RedirectResponse("/login", status_code=303)
    doc_id = db.restore_version(vid)
    return RedirectResponse(f"/doc/{doc_id}" if doc_id else "/", status_code=303)


@rt("/read/{doc_id}")
def get(session, doc_id: int):
    return _guard(session, "docs", lambda: views.read_view(doc_id), active_doc=doc_id)


# --- public (no auth) -------------------------------------------------------

@rt("/p/{token}")
def get(token: str):
    doc = db.document_by_token(token)
    if not doc:
        return Title("Not found"), Style(LAYOUT_CSS), Div(
            H1("Document not found"), P("This link is invalid or has been unpublished."),
            style="max-width:640px;margin:80px auto;text-align:center;color:var(--text-mute);")
    return views.public_article(doc)


# --- templates --------------------------------------------------------------

@rt("/templates")
def get(session):
    return _guard(session, "templates", views.templates_view)


@rt("/templates/{tid}/use")
def post(session, tid: int, folder_id: str = ""):
    if not _authed(session):
        return RedirectResponse("/login", status_code=303)
    fid = int(folder_id) if folder_id else None
    doc_id = db.create_doc_from_template(tid, fid)
    return RedirectResponse(f"/doc/{doc_id}" if doc_id else "/templates", status_code=303)


# --- AI generate ------------------------------------------------------------

@rt("/generate")
def get(session):
    return _guard(session, "docs", lambda: views.generate_view())


@rt("/generate")
def post(session, topic: str = "", folder_id: str = ""):
    if not _authed(session):
        return RedirectResponse("/login", status_code=303)
    topic = (topic or "").strip()
    if not topic:
        return _guard(session, "docs", lambda: views.generate_view("Please describe the document first."))
    try:
        title, blocks = ai.generate_doc(topic)
    except Exception as e:  # noqa: BLE001
        return _guard(session, "docs", lambda: views.generate_view(str(e)))
    fid = int(folder_id) if folder_id else None
    doc_id = db.create_document(fid, title, blocks)
    return RedirectResponse(f"/doc/{doc_id}", status_code=303)


@rt("/ai")
def get(session):
    body = (views._title("AI Assistant", "Chat lives in the right rail. Generate full documents from the Generate page."),
            Div(NotStr(
                "<div class='card'><h3>What you can ask</h3><ul style='line-height:1.9;'>"
                "<li>“Draft an introduction for an onboarding guide.”</li>"
                "<li>“Summarise the Q3 Product Plan in three bullets.”</li>"
                "<li>“Rewrite this paragraph to be more concise.”</li>"
                "<li><code>/docs</code> or <code>/templates</code> — work with no API key.</li></ul>"
                "<p>To build a complete document, use <a href='/generate'>Generate with AI</a> — it writes every "
                "block and drops you into the editor.</p></div>")))
    return _guard(session, "ai", body)


@rt("/guide")
def get(session):
    body = (views._title("User Guide", "How to drive FastDocs"), Div(NotStr("""
<div class='card'><h3>Documents &amp; folders</h3><p>The home page groups your documents by folder. Create a document
(blank or from a template), or generate one with AI.</p></div>
<div class='card' style='margin-top:14px;'><h3>Block editor</h3><p>A document is an ordered list of blocks — headings,
paragraphs, lists, quotes, code and dividers. Hover a block for its toolbar: move up/down, add a block below, edit, or
delete. Editing a block lets you change its type and write <strong>Markdown</strong>. Add blocks of any type from the
“Add block” bar at the bottom.</p></div>
<div class='card' style='margin-top:14px;'><h3>Templates &amp; versions</h3><p>Start from a reusable template, and use
<strong>Save version</strong> to snapshot a document; restore any earlier snapshot from its version history.</p></div>
<div class='card' style='margin-top:14px;'><h3>Publish</h3><p><strong>Publish</strong> mints a read-only public link
(<code>/p/&lt;token&gt;</code>) that needs no login. Unpublish to revoke it.</p></div>
<div class='card' style='margin-top:14px;'><h3>AI</h3><p>The right-rail assistant drafts, rewrites and summarises;
<strong>Generate with AI</strong> writes a whole document. Needs <code>MODEL_PROVIDER</code> + a key in <code>.env</code>;
the <code>/docs</code> and <code>/templates</code> slash-commands work without one.</p></div>
""")))
    return _guard(session, "guide", body)


@rt("/chat/new")
def get(session):
    session["thread"] = uuid.uuid4().hex
    return P("Ask me to draft, rewrite or summarise.", cls="chat-empty-hint")


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
        logger.info("No database found — seeding sample documents…")
        import seed
        seed.build()
    else:
        db.init_schema()  # idempotent; reaches existing DBs with new tables/columns


_ensure_db()

if __name__ == "__main__":
    logger.info("FastDocs on http://localhost:%s  (login %s)", PORT, VALID_EMAIL)
    serve(port=PORT, reload=os.getenv("FASTDOCS_RELOAD", "0") == "1")
