"""Center-pane renderers for FastDocs — document list, block editor, templates,
version history, and the read-only / public article views."""
from __future__ import annotations

import re

import markdown as md

from fasthtml.common import (
    Div, H1, H2, H3, H4, P, Span, A, Form, Input, Textarea, Button, Select, Option,
    Ul, Ol, Li, Blockquote, Pre, Code, Hr, NotStr, Title, Link, Style,
)

import db
from web.layout import LAYOUT_CSS

# htmx kwargs that swap a fragment into the #doc-main wrapper
HX = {"hx_target": "#doc-main", "hx_swap": "innerHTML"}


def _title(title, sub="", *actions):
    return Div(Div(H1(title), P(sub, cls="sub") if sub else None),
               Div(*actions, cls="toolbar") if actions else None, cls="page-title")


# --- block rendering --------------------------------------------------------

def _render_md(text):
    return NotStr(md.markdown(text or "", extensions=["fenced_code", "nl2br", "tables"]))


def _inline(text):
    """Render Markdown but strip a single wrapping <p> — for headings / list items."""
    html = md.markdown(text or "").strip()
    if html.startswith("<p>") and html.endswith("</p>"):
        html = html[3:-4]
    return NotStr(html)


def _lines(content):
    return [ln for ln in (content or "").splitlines() if ln.strip()]


def render_block(b):
    t, c = b["type"], b["content"]
    if t == "divider":
        return Hr(cls="blk-hr")
    if t == "heading1":
        return H1(_inline(c) if c.strip() else "Untitled", cls="blk-h1")
    if t == "heading2":
        return H2(_inline(c) if c.strip() else "Untitled", cls="blk-h2")
    if t == "heading3":
        return H3(_inline(c) if c.strip() else "Untitled", cls="blk-h3")
    if t == "bullet":
        lns = _lines(c)
        return Ul(*[Li(_inline(ln)) for ln in lns]) if lns else P("Empty list", cls="blk-empty")
    if t == "numbered":
        lns = _lines(c)
        return Ol(*[Li(_inline(ln)) for ln in lns]) if lns else P("Empty list", cls="blk-empty")
    if t == "quote":
        return Blockquote(_render_md(c) if c.strip() else "Empty quote")
    if t == "code":
        return Pre(Code(c or ""))
    # paragraph
    if not (c or "").strip():
        return P("Empty paragraph — click ✎ to edit", cls="blk-p blk-empty")
    return Div(_render_md(c), cls="blk-p")


def _excerpt(doc_id):
    for b in db.blocks(doc_id):
        if b["type"] in ("divider", "heading1", "heading2", "heading3"):
            continue
        txt = re.sub(r"[#*`>\[\]()]|^[-\d.]+\s", " ", b["content"] or "")
        txt = re.sub(r"\s+", " ", txt).strip()
        if txt:
            return txt[:120] + ("…" if len(txt) > 120 else "")
    return "Empty document"


# --- document list ----------------------------------------------------------

def doc_card(d):
    badge = Span("Published", cls="badge live") if d.get("public_token") else None
    return A(H3(d["title"]),
             P(_excerpt(d["id"]), cls="excerpt"),
             Div(Span(f"{db.word_count(d['id'])} words"), badge, cls="meta"),
             href=f"/doc/{d['id']}", cls="doc-card")


def docs_list():
    folders = db.folders()
    all_docs = db.documents()
    by_folder = {}
    for d in all_docs:
        by_folder.setdefault(d["folder_id"], []).append(d)

    sections = []
    for f in folders:
        docs = by_folder.get(f["id"], [])
        if not docs:
            continue
        sections.append(Div(
            H4(Span("📁"), f["name"], Span(f"{len(docs)}", cls="count")),
            Div(*[doc_card(d) for d in docs], cls="doc-grid"), cls="folder-sec"))
    loose = by_folder.get(None, [])
    if loose:
        sections.append(Div(
            H4(Span("📄"), "Unfiled", Span(f"{len(loose)}", cls="count")),
            Div(*[doc_card(d) for d in loose], cls="doc-grid"), cls="folder-sec"))

    actions = Div(
        A("✨ Generate with AI", href="/generate", cls="btn"),
        Form(Input(name="name", placeholder="New folder…", style="padding:6px 10px;border:1px solid var(--border);border-radius:7px;"),
             Button("＋ Folder", cls="btn", type="submit"), method="post", action="/folder/new",
             style="display:flex;gap:6px;"),
        A("＋ New document", href="/new", cls="btn primary"),
        cls="toolbar")
    body = sections if sections else [P("No documents yet — create one or generate with AI.",
                                        style="color:var(--text-mute);padding:40px 0;")]
    return (_title("All documents", f"{len(all_docs)} documents · {len(folders)} folders", actions), *body)


# --- editor fragment --------------------------------------------------------

def doc_detail(doc_id, editing=None):
    d = db.document(doc_id)
    if not d:
        return _title("Document not found"), P("No such document.", style="color:var(--text-mute);")
    return (Div(A("← All documents", href="/", cls="btn"), style="margin-bottom:10px;"),
            Div(doc_main(doc_id, editing), id="doc-main"))


def _edit_node(b, doc_id):
    bid = b["id"]
    opts = [Option(db.BLOCK_LABELS[t], value=t, selected=(t == b["type"])) for t in db.BLOCK_TYPES]
    return Div(Form(
        Select(*opts, name="type"),
        Textarea(b["content"], name="content", placeholder="Write… (Markdown supported)", autofocus=True),
        Div(Button("Save", cls="btn primary sm", type="submit"),
            Button("Cancel", cls="btn sm", type="button", hx_get=f"/doc/{doc_id}/main", **HX),
            Span("Markdown: **bold** · *italic* · `code` · [text](url). Lists: one item per line.",
                 style="color:var(--text-mute);font-size:11px;margin-left:auto;"),
            cls="row"),
        hx_post=f"/doc/{doc_id}/block/{bid}", **HX),
        cls="blk-edit")


def block_node(b, doc_id, is_first, is_last, only, editing):
    bid = b["id"]
    if editing == bid:
        return _edit_node(b, doc_id)
    tb = Div(
        Button("↑", title="Move up", disabled=is_first, hx_post=f"/doc/{doc_id}/block/{bid}/move?dir=-1", **HX),
        Button("↓", title="Move down", disabled=is_last, hx_post=f"/doc/{doc_id}/block/{bid}/move?dir=1", **HX),
        Button("＋", title="Add block below", hx_post=f"/doc/{doc_id}/block/add?after={bid}", **HX),
        Button("✎", title="Edit", hx_get=f"/doc/{doc_id}/main?editing={bid}", **HX),
        Button("🗑", title="Delete", cls="del", disabled=only, hx_post=f"/doc/{doc_id}/block/{bid}/delete", **HX),
        cls="blk-toolbar")
    return Div(tb, render_block(b), cls="block")


_QUICK = [("paragraph", "¶ Text"), ("heading2", "H Heading"), ("bullet", "• List"),
          ("numbered", "1. Numbered"), ("quote", "❝ Quote"), ("code", "</> Code"), ("divider", "— Divider")]


def _add_bar(doc_id, after_bid=None):
    suffix = f"&after={after_bid}" if after_bid else ""
    btns = [Button(label, cls="btn sm", hx_post=f"/doc/{doc_id}/block/add?type={t}{suffix}", **HX)
            for t, label in _QUICK]
    return Div(Span("Add block:", cls="lbl"), *btns, cls="addbar")


def doc_main(doc_id, editing=None):
    d = db.document(doc_id)
    if not d:
        return Div(P("Document not found."))
    blks = db.blocks(doc_id)
    token = d.get("public_token")

    if token:
        pub = Div(Span("🌐 Published"),
                  Span("Public link:"), Code(f"/p/{token}"),
                  A("Open", href=f"/p/{token}", target="_blank", cls="btn sm"),
                  Form(Button("Unpublish", cls="btn sm", type="submit"), method="post",
                       action=f"/doc/{doc_id}/unpublish", style="margin-left:auto;"),
                  cls="pub-box")
    else:
        pub = None

    bar = Div(
        Form(Button("🌐 Publish", cls="btn", type="submit"), method="post",
             action=f"/doc/{doc_id}/publish") if not token else None,
        A("📖 Read view", href=f"/read/{doc_id}", cls="btn"),
        A("🕑 Version history", href=f"/doc/{doc_id}/versions", cls="btn"),
        Form(Button("💾 Save version", cls="btn", type="submit"), method="post",
             action=f"/doc/{doc_id}/snapshot"),
        Span(f"{db.word_count(doc_id)} words · updated {d['updated'] or ''}",
             style="color:var(--text-mute);font-size:12px;margin-left:auto;"),
        cls="doc-bar")

    title_form = Form(
        Input(name="title", value=d["title"]),
        Button("Rename", cls="btn sm", type="submit"),
        hx_post=f"/doc/{doc_id}/title", **HX, cls="doc-title-form")

    n = len(blks)
    nodes = [block_node(b, doc_id, i == 0, i == n - 1, n <= 1, editing) for i, b in enumerate(blks)]
    inner = Div(*nodes, _add_bar(doc_id, blks[-1]["id"] if blks else None), cls="blocks")
    return Div(bar, pub, title_form, inner)


# --- templates --------------------------------------------------------------

def templates_view():
    tpls = db.templates()
    cards = [Div(H3(t["title"]), P(t["description"] or ""),
                 Div(Form(Button("Use template", cls="btn primary", type="submit"),
                          method="post", action=f"/templates/{t['id']}/use"),
                     Span(f"{t['n']} blocks", cls="badge"),
                     style="display:flex;align-items:center;gap:10px;"),
                 cls="tpl-card") for t in tpls]
    return (_title("Templates", "Start a new document from a reusable structure."),
            Div(*cards, cls="tpl-grid") if cards else P("No templates.", style="color:var(--text-mute);"))


# --- versions ---------------------------------------------------------------

def versions_view(doc_id):
    d = db.document(doc_id)
    if not d:
        return _title("Document not found"), P("No such document.")
    vers = db.versions(doc_id)
    rows = [Div(Div(Span(v["created"], cls="when"),
                    Span(" · manual save" if v["manual"] else " · auto (pre-restore)", cls="tag")),
                Form(Button("Restore", cls="btn sm", type="submit"), method="post",
                     action=f"/version/{v['id']}/restore"),
                cls="ver-row") for v in vers]
    return (_title(f"Version history", f"{d['title']} · {len(vers)} snapshots",
                   A("← Back to document", href=f"/doc/{doc_id}", cls="btn")),
            Div(*rows, cls="ver-list") if rows
            else P("No versions yet. Use “Save version” in the editor.", style="color:var(--text-mute);"))


# --- read + public ----------------------------------------------------------

def _article_nodes(doc_id):
    return [render_block(b) for b in db.blocks(doc_id)]


def read_view(doc_id):
    d = db.document(doc_id)
    if not d:
        return _title("Document not found"), P("No such document.")
    return (_title(d["title"], "Read view", A("← Edit", href=f"/doc/{doc_id}", cls="btn")),
            Div(*_article_nodes(doc_id), cls="blocks", style="margin-top:6px;"))


def public_article(doc):
    """Standalone, login-free page for a published document."""
    return (
        Title(f"{doc['title']} — FastDocs"),
        Link(rel="icon", type="image/svg+xml", href="/static/favicon.svg"),
        Style(LAYOUT_CSS),
        Div(
            Div(Span(cls="brand-dot"), Span("Fast", style="font-weight:800;"),
                Span("Docs", style="color:var(--accent);font-weight:700;"),
                Span("published document", cls="env-pill", style="margin-left:10px;"),
                cls="brand", style="padding:18px 0;border-bottom:1px solid var(--border);margin-bottom:24px;"),
            Div(H1(doc["title"], cls="blk-h1"), *_article_nodes(doc["id"]), cls="blocks"),
            P(NotStr("Published with <strong>FastDocs</strong> — a FastHTML document editor."),
              style="color:var(--text-mute);font-size:12px;margin-top:28px;text-align:center;"),
            style="max-width:840px;margin:0 auto;padding:0 20px 60px;"))


# --- generate ---------------------------------------------------------------

def generate_view(error="", folders=None):
    folders = folders or db.folders()
    return (_title("Generate a document with AI", "Describe what you need; AI drafts the whole document."),
            Div(NotStr(f"<div class='notice'>⚠ {error}</div>") if error else "",
                Form(
                    Div(Span("What should the document cover?", style="font-weight:600;display:block;margin-bottom:8px;")),
                    Textarea("", name="topic", cls="askbox",
                             placeholder="e.g. An onboarding guide for new backend engineers, with setup steps and conventions",
                             style="min-height:90px;"),
                    Div(Select(Option("Unfiled", value=""),
                               *[Option(f["name"], value=str(f["id"])) for f in folders], name="folder_id"),
                        Button("✨ Generate document", cls="btn primary", id="gen-btn", type="submit"),
                        cls="row"),
                    method="post", action="/generate", onsubmit="return genSubmit()"),
                cls="gen-card"),
            P("Without an API key the slash-commands still work; only generation and free-form chat need one.",
              style="color:var(--text-mute);font-size:12px;margin-top:14px;"))
