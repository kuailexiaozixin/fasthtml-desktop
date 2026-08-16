"""open-docflow: Dokumentu darbo eigos valdymo sistema.

FastHTML application for document workflow management.
Run: python app.py
"""

from __future__ import annotations

import os
import secrets
import shutil
from datetime import datetime, timezone

from fasthtml.common import *

from src.models import Document, DocumentType, WorkflowStep, get_session, init_db
from src.workflow import (
    ALL_STATUSES,
    STATUS_LABELS,
    get_allowed_transitions,
    get_audit_trail,
    get_status_counts,
    get_type_status_matrix,
    transition_document,
)
from web import account_auth
from web.account_auth import AUTH_CSS, AUTH_JS, auth_modal

# --- App setup ---
# Upstream called `fast_app(hdrs=[Style(CSS), ...])` right here, *before* the
# `CSS` string is defined further down, so importing this module raised
# `NameError: name 'CSS' is not defined`. The application is now built once,
# after the CSS block, together with the authentication layer.

APP_NAME = "open-docflow"
SESSION_KEY = "user"
VALID_EMAIL = os.getenv("DOCFLOW_ADMIN_EMAIL", "admin@docflow.example")
VALID_PASSWORD = os.getenv("DOCFLOW_ADMIN_PASSWORD", "DocFlow2026$")
SECRET = os.getenv("DOCFLOW_SECRET", secrets.token_hex(32))
PORT = int(os.getenv("DOCFLOW_PORT", "5022"))

# Frozen builds unpack the source tree into a read-only temp dir, so the upload
# target must be redirectable to a writable location next to the executable.
UPLOAD_DIR = os.environ.get("DOCFLOW_UPLOAD_DIR") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "uploads"
)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- CSS ---

CSS = """
:root {
    --color-gautas: #3b82f6;
    --color-perziurimas: #f59e0b;
    --color-patvirtintas: #10b981;
    --color-atmestas: #ef4444;
    /* consumed by the shared account modal (web/account_auth.py) */
    --accent: #3b82f6;
}

.status-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: 600;
    color: white;
}
.status-gautas { background: var(--color-gautas); }
.status-perziurimas { background: var(--color-perziurimas); }
.status-patvirtintas { background: var(--color-patvirtintas); }
.status-atmestas { background: var(--color-atmestas); }

.stat-card {
    text-align: center;
    padding: 1.5rem;
    border-radius: 0.75rem;
    background: var(--pico-card-background-color);
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}
.stat-card h2 { margin: 0; font-size: 2.5rem; }
.stat-card p { margin: 0.5rem 0 0; opacity: 0.7; }

.grid-4 {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 1rem;
    margin-bottom: 2rem;
}

.doc-table { width: 100%; }
.doc-table th, .doc-table td { padding: 0.6rem 0.8rem; text-align: left; }
.doc-table tbody tr:hover { background: var(--pico-muted-border-color); }

.audit-timeline { list-style: none; padding: 0; }
.audit-timeline li {
    padding: 0.75rem 0;
    border-bottom: 1px solid var(--pico-muted-border-color);
}
.audit-timeline li:last-child { border-bottom: none; }
.audit-time { font-size: 0.8rem; opacity: 0.6; }
.audit-actor { font-weight: 600; }

nav a { margin-right: 1.5rem; text-decoration: none; }
nav a:hover { text-decoration: underline; }

.search-bar { display: flex; gap: 0.75rem; flex-wrap: wrap; align-items: end; margin-bottom: 1.5rem; }
.search-bar label { font-size: 0.85rem; }

.flash-success { padding: 1rem; background: #d1fae5; color: #065f46; border-radius: 0.5rem; margin-bottom: 1rem; }
.flash-error { padding: 1rem; background: #fde2e2; color: #991b1b; border-radius: 0.5rem; margin-bottom: 1rem; }

.nav-right { float: right; margin-right: 0 !important; }
.nav-user { opacity: 0.65; font-size: 0.85rem; margin-right: 1rem; float: right; }

.login-wrap { min-height: 100vh; display: grid; place-items: center; padding: 24px; }
.login-card {
    width: min(430px, 100%);
    text-align: center;
    padding: 2.5rem 2rem;
    border-radius: 18px;
    background: #fff;
    border: 1px solid #e5e7eb;
    box-shadow: 0 24px 70px rgba(15, 23, 42, 0.12);
}
.login-card h1 { margin: 0 0 0.25rem; font-size: 1.9rem; }
.login-card .login-sub { margin: 0 0 1.75rem; color: #6b7280; font-size: 0.95rem; }
.login-cta { width: 100%; margin-bottom: 0.75rem; }
.login-hint { font-size: 0.8rem; color: #6b7280; margin: 0; line-height: 1.6; }
.login-hint code { font-size: 0.78rem; }
"""

# --- Authentication (offline-friendly local accounts) ---

PUBLIC_PREFIXES = ("/login", "/logout", "/auth/", "/static/", "/favicon")
STATIC_SUFFIXES = (".css", ".js", ".ico", ".png", ".svg", ".woff", ".woff2")


def auth_before(req, sess):
    """Gate every business route behind the signed session cookie."""
    user = req.scope["auth"] = sess.get(SESSION_KEY)
    path = req.url.path
    if path.startswith(PUBLIC_PREFIXES) or path.endswith(STATIC_SUFFIXES):
        return None
    if not user:
        return RedirectResponse("/login", status_code=303)
    return None


bware = Beforeware(
    auth_before,
    skip=[r"/favicon\.ico", r"/static/.*", r".*\.css", r".*\.js", "/login", r"/auth/.*"],
)

app, rt = fast_app(
    hdrs=[
        Style(CSS),
        Style(AUTH_CSS),
        Meta(charset="utf-8"),
        Meta(name="viewport", content="width=device-width, initial-scale=1"),
    ],
    pico=True,
    before=bware,
    secret_key=SECRET,
)

account_auth.register_fasthtml_routes(
    rt, app_name=APP_NAME, session_key=SESSION_KEY, success_path="/"
)
# Offline demo: seed the documented credentials as a **verified** account and let
# the modal offer a one-click fill. Without these two calls the accounts table is
# empty and every sign-in fails with
#   "Invalid email, password, or unverified account".
account_auth.accounts.ensure_account(
    VALID_EMAIL, VALID_PASSWORD, f"{APP_NAME} Admin", verified=True
)
account_auth.set_demo_credentials(VALID_EMAIL, VALID_PASSWORD)


# --- Helpers ---


def db():
    return get_session()


def layout(*children, title="open-docflow", user=None):
    return Html(
        Head(
            Title(title),
            Meta(charset="utf-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1"),
            Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css"),
            Script(src="https://unpkg.com/htmx.org@2.0.4"),
            Style(CSS),
        ),
        Body(
            Nav(
                A("Pradzia", href="/"),
                A("Dokumentai", href="/documents"),
                A("Ikelti", href="/upload"),
                A("Statistika", href="/stats"),
                A("Atsijungti", href="/logout", cls="nav-right"),
                Span(user, cls="nav-user") if user else None,
                cls="container",
                style="padding: 1rem 0;",
            ),
            Main(*children, cls="container", style="padding-bottom: 3rem;"),
            Footer(
                P("open-docflow v0.1 | Predictive Labs UAB | MIT licencija"),
                cls="container",
                style="text-align: center; opacity: 0.5; padding: 2rem 0;",
            ),
        ),
    )


def status_badge(status: str):
    return Span(STATUS_LABELS.get(status, status), cls=f"status-badge status-{status}")


def format_dt(dt: datetime | None) -> str:
    if dt is None:
        return "-"
    return dt.strftime("%Y-%m-%d %H:%M")


def format_size(size: int | None) -> str:
    if size is None:
        return "-"
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    return f"{size / (1024 * 1024):.1f} MB"


# --- Auth routes ---


def login_page():
    return Html(
        Head(
            Title(f"{APP_NAME} | Prisijungimas"),
            Meta(charset="utf-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1"),
            Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css"),
            Style(CSS),
            Style(AUTH_CSS),
        ),
        Body(
            Div(
                Div(
                    H1(APP_NAME),
                    P("Dokumentu darbo eigos valdymo sistema", cls="login-sub"),
                    Button(
                        "Prisijungti arba registruotis",
                        type="button",
                        cls="login-cta",
                        onclick="authOpen('login')",
                    ),
                    P(
                        NotStr(
                            "Demo: <code>{email}</code> / <code>{pwd}</code>".format(
                                email=VALID_EMAIL, pwd=VALID_PASSWORD
                            )
                        ),
                        cls="login-hint",
                    ),
                    cls="login-card",
                ),
                cls="login-wrap",
            ),
            auth_modal(APP_NAME),
            Script(AUTH_JS),
            Script("window.addEventListener('DOMContentLoaded', () => authOpen('login'));"),
        ),
    )


@rt("/login")
def get(sess):
    if sess.get(SESSION_KEY):
        return RedirectResponse("/", status_code=303)
    return login_page()


@rt("/logout")
def get(sess):
    sess.pop(SESSION_KEY, None)
    return RedirectResponse("/login", status_code=303)


# --- Routes ---


@rt("/")
def get(auth):
    session = db()
    try:
        counts = get_status_counts(session)
        total = sum(counts.values())

        cards = []
        for status in ALL_STATUSES:
            color_var = f"var(--color-{status})"
            cards.append(
                Div(
                    H2(str(counts[status]), style=f"color: {color_var};"),
                    P(STATUS_LABELS[status]),
                    cls="stat-card",
                )
            )

        # Recent documents
        recent = (
            session.query(Document)
            .order_by(Document.updated_at.desc())
            .limit(10)
            .all()
        )

        rows = []
        for doc in recent:
            type_name = doc.doc_type_rel.name if doc.doc_type_rel else "-"
            rows.append(
                Tr(
                    Td(A(f"#{doc.id}", href=f"/documents/{doc.id}")),
                    Td(doc.title[:60]),
                    Td(type_name),
                    Td(status_badge(doc.status)),
                    Td(format_dt(doc.updated_at)),
                )
            )

        return layout(
            H1(f"Dokumentu suvestine ({total})"),
            Div(*cards, cls="grid-4"),
            H3("Naujausi dokumentai"),
            Table(
                Thead(Tr(Th("Nr."), Th("Pavadinimas"), Th("Tipas"), Th("Busena"), Th("Atnaujintas"))),
                Tbody(*rows),
                cls="doc-table",
            ),
            title="open-docflow | Pradzia",
            user=auth,
        )
    finally:
        session.close()


@rt("/documents")
def get(auth, status: str = "", doc_type: str = "", q: str = ""):
    session = db()
    try:
        # Build query
        query = session.query(Document).join(DocumentType, isouter=True)

        if status:
            query = query.filter(Document.status == status)
        if doc_type:
            query = query.filter(DocumentType.name == doc_type)
        if q:
            query = query.filter(Document.title.ilike(f"%{q}%"))

        docs = query.order_by(Document.updated_at.desc()).limit(100).all()
        doc_types = session.query(DocumentType).order_by(DocumentType.name).all()

        # Search form
        status_options = [Option("Visos busenos", value="")] + [
            Option(STATUS_LABELS[s], value=s, selected=(s == status)) for s in ALL_STATUSES
        ]
        type_options = [Option("Visi tipai", value="")] + [
            Option(dt.name, value=dt.name, selected=(dt.name == doc_type)) for dt in doc_types
        ]

        search_form = Form(
            Div(
                Label("Paieska"),
                Input(name="q", value=q, placeholder="Ieskoti pagal pavadinima..."),
            ),
            Div(
                Label("Busena"),
                Select(*status_options, name="status"),
            ),
            Div(
                Label("Tipas"),
                Select(*type_options, name="doc_type"),
            ),
            Div(
                Label(Br()),  # spacer
                Button("Filtruoti", type="submit"),
            ),
            cls="search-bar",
            method="get",
            action="/documents",
        )

        rows = []
        for doc in docs:
            type_name = doc.doc_type_rel.name if doc.doc_type_rel else "-"
            rows.append(
                Tr(
                    Td(A(f"#{doc.id}", href=f"/documents/{doc.id}")),
                    Td(doc.title[:70]),
                    Td(type_name),
                    Td(status_badge(doc.status)),
                    Td(doc.submitted_by or "-"),
                    Td(format_dt(doc.uploaded_at)),
                    Td(format_size(doc.file_size)),
                )
            )

        return layout(
            H1(f"Dokumentai ({len(docs)})"),
            search_form,
            Table(
                Thead(
                    Tr(
                        Th("Nr."), Th("Pavadinimas"), Th("Tipas"),
                        Th("Busena"), Th("Pateike"), Th("Ikeltas"), Th("Dydis"),
                    )
                ),
                Tbody(*rows),
                cls="doc-table",
            ),
            title="open-docflow | Dokumentai",
            user=auth,
        )
    finally:
        session.close()


@rt("/documents/{doc_id}")
def get(auth, doc_id: int):
    session = db()
    try:
        doc = session.get(Document, doc_id)
        if doc is None:
            return layout(
                H1("Dokumentas nerastas"),
                P(f"Dokumentas #{doc_id} neegzistuoja."),
                user=auth,
            )

        type_name = doc.doc_type_rel.name if doc.doc_type_rel else "-"
        trail = get_audit_trail(session, doc_id)
        allowed = get_allowed_transitions(doc.status)

        # Audit trail
        trail_items = []
        for step in trail:
            from_label = STATUS_LABELS.get(step.from_status, step.from_status or "Naujas")
            to_label = STATUS_LABELS.get(step.to_status, step.to_status)
            comment_text = f" -- {step.comment}" if step.comment else ""
            trail_items.append(
                Li(
                    Span(format_dt(step.created_at), cls="audit-time"),
                    Br(),
                    Span(step.actor, cls="audit-actor"),
                    f": {from_label} -> {to_label}{comment_text}",
                )
            )

        # Transition buttons
        transition_form = None
        if allowed:
            buttons = []
            for target in allowed:
                buttons.append(
                    Button(
                        f"Perkelti i: {STATUS_LABELS[target]}",
                        hx_post=f"/documents/{doc_id}/transition",
                        hx_vals=f'{{"to_status": "{target}"}}',
                        hx_target="#flash-area",
                        hx_swap="innerHTML",
                        style=f"margin-right: 0.5rem;",
                    )
                )
            transition_form = Div(
                H4("Keisti busena"),
                Div(
                    Input(name="actor", placeholder="Vykdytojo vardas", required=True, id="actor-input",
                          style="max-width: 300px; margin-bottom: 0.5rem;"),
                    Input(name="comment", placeholder="Komentaras (neprivaloma)", id="comment-input",
                          style="max-width: 400px; margin-bottom: 0.5rem;"),
                ),
                Div(*buttons),
                Script("""
                    document.querySelectorAll('[hx-post]').forEach(btn => {
                        btn.addEventListener('htmx:configRequest', function(e) {
                            e.detail.parameters['actor'] = document.getElementById('actor-input').value;
                            e.detail.parameters['comment'] = document.getElementById('comment-input').value;
                        });
                    });
                """),
            )

        meta_items = []
        # `Document.metadata` is renamed to `doc_metadata` in src/models.py because
        # `metadata` is reserved by SQLAlchemy's declarative base (the DB column is
        # still called "metadata").
        if doc.doc_metadata:
            for k, v in doc.doc_metadata.items():
                meta_items.append(Tr(Td(k), Td(str(v))))

        return layout(
            A("< Atgal i sarasa", href="/documents"),
            H1(doc.title),
            Div(id="flash-area"),
            Div(
                Table(
                    Tr(Td(Strong("Nr.")), Td(f"#{doc.id}")),
                    Tr(Td(Strong("Tipas")), Td(type_name)),
                    Tr(Td(Strong("Busena")), Td(status_badge(doc.status))),
                    Tr(Td(Strong("Pateike")), Td(doc.submitted_by or "-")),
                    Tr(Td(Strong("Priskirtas")), Td(doc.assigned_to or "-")),
                    Tr(Td(Strong("Ikeltas")), Td(format_dt(doc.uploaded_at))),
                    Tr(Td(Strong("Atnaujintas")), Td(format_dt(doc.updated_at))),
                    Tr(Td(Strong("Failo dydis")), Td(format_size(doc.file_size))),
                    Tr(Td(Strong("Failo kelias")), Td(doc.file_path or "-")),
                ),
            ),
            transition_form or "",
            H3("Metaduomenys") if meta_items else "",
            Table(*meta_items) if meta_items else "",
            H3("Audito sekimas"),
            Ul(*trail_items, cls="audit-timeline") if trail_items else P("Kol kas nera irasu."),
            title=f"open-docflow | #{doc.id}",
            user=auth,
        )
    finally:
        session.close()


@rt("/documents/{doc_id}/transition")
def post(doc_id: int, to_status: str = "", actor: str = "", comment: str = ""):
    session = db()
    try:
        if not actor.strip():
            return Div("Iveskite vykdytojo varda.", cls="flash-error")
        if not to_status:
            return Div("Nenurodyta busena.", cls="flash-error")

        result = transition_document(session, doc_id, to_status, actor.strip(), comment.strip() or None)
        if result.success:
            return Div(
                result.message,
                Script(f"setTimeout(() => window.location.reload(), 800);"),
                cls="flash-success",
            )
        return Div(result.message, cls="flash-error")
    finally:
        session.close()


@rt("/upload")
def get(auth):
    session = db()
    try:
        doc_types = session.query(DocumentType).order_by(DocumentType.name).all()
        type_options = [Option(dt.name, value=str(dt.id)) for dt in doc_types]

        return layout(
            H1("Ikelti dokumenta"),
            Form(
                Div(
                    Label("Pavadinimas *"),
                    Input(name="title", required=True, placeholder="Dokumento pavadinimas"),
                ),
                Div(
                    Label("Dokumento tipas *"),
                    Select(*type_options, name="doc_type_id", required=True),
                ),
                Div(
                    Label("Pateikejo vardas"),
                    Input(name="submitted_by", placeholder="Vardas Pavarde"),
                ),
                Div(
                    Label("Failas (PDF arba DOCX)"),
                    Input(name="file", type="file", accept=".pdf,.docx"),
                ),
                Button("Ikelti", type="submit"),
                method="post",
                action="/upload",
                enctype="multipart/form-data",
            ),
            title="open-docflow | Ikelti",
            user=auth,
        )
    finally:
        session.close()


@rt("/upload")
async def post(auth, title: str = "", doc_type_id: int = 0, submitted_by: str = "", file: UploadFile = None):
    session = db()
    try:
        if not title.strip():
            return layout(
                H1("Klaida"),
                P("Pavadinimas privalomas."),
                A("Atgal", href="/upload"),
                user=auth,
            )

        file_path = None
        file_size = None
        if file and file.filename:
            safe_name = f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}_{file.filename}"
            file_path = os.path.join(UPLOAD_DIR, safe_name)
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            file_size = len(content)
            file_path = f"uploads/{safe_name}"

        doc = Document(
            title=title.strip(),
            doc_type_id=doc_type_id or None,
            status="gautas",
            uploaded_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            file_path=file_path,
            file_size=file_size,
            submitted_by=submitted_by.strip() or None,
        )
        session.add(doc)
        session.flush()

        # Log initial workflow step
        step = WorkflowStep(
            document_id=doc.id,
            from_status=None,
            to_status="gautas",
            actor=submitted_by.strip() or "Sistema",
            comment="Dokumentas ikeltas.",
        )
        session.add(step)
        session.commit()

        return RedirectResponse(f"/documents/{doc.id}", status_code=303)
    finally:
        session.close()


@rt("/stats")
def get(auth):
    session = db()
    try:
        counts = get_status_counts(session)
        total = sum(counts.values())
        matrix = get_type_status_matrix(session)

        # Summary cards
        cards = [
            Div(H2(str(total)), P("Viso dokumentu"), cls="stat-card"),
        ]
        for status in ALL_STATUSES:
            color_var = f"var(--color-{status})"
            pct = f"{counts[status] / total * 100:.0f}%" if total > 0 else "0%"
            cards.append(
                Div(
                    H2(str(counts[status]), style=f"color: {color_var};"),
                    P(f"{STATUS_LABELS[status]} ({pct})"),
                    cls="stat-card",
                )
            )

        # Type x status matrix
        matrix_rows = []
        for row in matrix:
            matrix_rows.append(
                Tr(
                    Td(Strong(row["type"])),
                    *[Td(str(row.get(s, 0))) for s in ALL_STATUSES],
                    Td(Strong(str(sum(row.get(s, 0) for s in ALL_STATUSES)))),
                )
            )

        return layout(
            H1("Statistika"),
            Div(*cards, cls="grid-4"),
            H3("Dokumentai pagal tipa ir busena"),
            Table(
                Thead(
                    Tr(Th("Tipas"), *[Th(STATUS_LABELS[s]) for s in ALL_STATUSES], Th("Viso"))
                ),
                Tbody(*matrix_rows),
                cls="doc-table",
            ),
            title="open-docflow | Statistika",
            user=auth,
        )
    finally:
        session.close()


# --- Init & run ---

# Create the SQLite schema and seed the eight built-in document types on import so
# both `python app.py` and the desktop shell (desktop.py) get a ready database.
init_db()


if __name__ == "__main__":
    serve(port=PORT)
