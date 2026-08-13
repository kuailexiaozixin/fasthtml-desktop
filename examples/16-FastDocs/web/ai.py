"""FastDocs AI — document generation, grounded chat, slash-commands.

Slash-commands (`/help`, `/docs`, `/templates`) work with no API key. Free-form
chat and `/generate` document authoring need MODEL_PROVIDER + a key in .env.
"""
from __future__ import annotations

import json
import os
import re

import db

PROVIDER = os.getenv("MODEL_PROVIDER", "xai")
MODEL = os.getenv("MODEL_NAME", "grok-4-1-fast-reasoning")


def snapshot() -> str:
    docs = db.documents()
    lines = ["DOCUMENT WORKSPACE (synthetic):",
             f"- {len(docs)} documents across {len(db.folders())} folders."]
    for d in docs[:12]:
        body = re.sub(r"\s+", " ", " ".join(b["content"] for b in db.blocks(d["id"]))).strip()[:400]
        fol = db.folder(d["folder_id"])["name"] if d["folder_id"] else "Unfiled"
        flag = " [published]" if d.get("public_token") else ""
        lines.append(f"\n## '{d['title']}' (folder: {fol}){flag}\n{body}")
    return "\n".join(lines)


SYSTEM_PROMPT = """You are the FastDocs writing assistant, embedded in a document editor.
You help the user draft, continue, rewrite, summarise and outline documents. Be concise and
use Markdown. Base answers on the DOCUMENT WORKSPACE below when the user refers to their docs."""

DOC_SYSTEM = """You generate documents as a JSON array of content blocks. Return ONLY a JSON array
(no prose, no markdown fences). Each element is an object: {"type": str, "content": str}.
Allowed "type" values: "heading1", "heading2", "heading3", "paragraph", "bullet", "numbered",
"quote", "code", "divider".
Rules:
- The FIRST block must be "heading1" whose content is the document title.
- Structure the document with "heading2"/"heading3" sections.
- For "bullet" and "numbered", put ONE item per line in content (no leading - or 1.).
- Paragraphs are short Markdown; you may use **bold**, *italic*, `code`, [links](url).
- "divider" content is an empty string.
- Produce between 6 and 14 blocks total. Make it genuinely useful, not placeholder text."""


def _table(headers, rows_):
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for r in rows_:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)


def handle_command(text):
    if not text.startswith("/"):
        return None
    cmd = text[1:].split()[0].lower() if len(text) > 1 else ""
    if cmd in ("help", "?"):
        return ("**FastDocs shortcuts**\n\n"
                "- `/docs` — list your documents\n"
                "- `/templates` — list available templates\n\n"
                "Ask me to **draft**, **continue**, **rewrite** or **summarise** any text, "
                "or use **Generate with AI** to create a whole document from a prompt.")
    if cmd == "docs":
        docs = db.documents()
        rows = [[d["title"],
                 (db.folder(d["folder_id"])["name"] if d["folder_id"] else "Unfiled"),
                 db.word_count(d["id"]),
                 "yes" if d.get("public_token") else "—"] for d in docs]
        return "**Your documents**\n\n" + _table(["Title", "Folder", "Words", "Published"], rows)
    if cmd == "templates":
        t = db.templates()
        return "**Templates**\n\n" + _table(["Title", "Blocks", "Description"],
                                            [[x["title"], x["n"], x["description"] or ""] for x in t])
    return f"Unknown command `/{cmd}`. Try `/help`."


# --- document generation ----------------------------------------------------

def generate_doc(topic: str):
    """Return (title, blocks[]) where blocks = [{type, content}], or raise RuntimeError."""
    key_env = {"xai": "XAI_API_KEY", "openai": "OPENAI_API_KEY",
               "anthropic": "ANTHROPIC_API_KEY", "google": "GOOGLE_API_KEY"}.get(PROVIDER)
    if not key_env or not os.getenv(key_env):
        raise RuntimeError(f"No {key_env or 'LLM'} key set — add it to .env to generate documents with AI.")
    raw = _complete(DOC_SYSTEM, f"Write a complete, useful document about: {topic}")
    arr = _extract_json(raw)
    if not arr:
        raise RuntimeError("The model did not return a valid document. Try rephrasing.")
    blocks = []
    for b in arr:
        if not isinstance(b, dict):
            continue
        t = b.get("type", "paragraph")
        if t not in db.BLOCK_TYPES:
            t = "paragraph"
        blocks.append({"type": t, "content": str(b.get("content", ""))})
    if not blocks:
        raise RuntimeError("The generated document was empty. Try again.")
    if blocks[0]["type"] != "heading1":
        blocks.insert(0, {"type": "heading1", "content": topic[:80]})
    title = blocks[0]["content"] or topic[:80]
    return title, blocks


def _extract_json(text: str):
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(.+?)```", text, re.IGNORECASE | re.DOTALL)
    if m:
        text = m.group(1).strip()
    m = re.search(r"(\[.*\])", text, re.DOTALL)
    if m:
        text = m.group(1)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


# --- chat -------------------------------------------------------------------

async def stream_chat(message):
    cmd = handle_command(message)
    if cmd is not None:
        yield f"data: {json.dumps({'token': cmd})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"
        return
    system = SYSTEM_PROMPT + "\n\n" + snapshot()
    try:
        async for tok in _provider_stream(system, message):
            yield f"data: {json.dumps({'token': tok})}\n\n"
    except Exception as e:  # noqa: BLE001
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
    yield f"data: {json.dumps({'done': True})}\n\n"


def _complete(system: str, user: str) -> str:
    import httpx
    provider, model = PROVIDER, MODEL
    if provider in ("xai", "openai"):
        url = "https://api.x.ai/v1/chat/completions" if provider == "xai" else "https://api.openai.com/v1/chat/completions"
        key = os.getenv("XAI_API_KEY" if provider == "xai" else "OPENAI_API_KEY", "")
        r = httpx.post(url, headers={"Authorization": f"Bearer {key}"},
                       json={"model": model, "messages": [{"role": "system", "content": system},
                                                          {"role": "user", "content": user}]}, timeout=90)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    if provider == "anthropic":
        key = os.getenv("ANTHROPIC_API_KEY", "")
        r = httpx.post("https://api.anthropic.com/v1/messages",
                       headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
                       json={"model": model, "max_tokens": 2500, "system": system,
                             "messages": [{"role": "user", "content": user}]}, timeout=90)
        r.raise_for_status()
        return r.json()["content"][0]["text"]
    if provider == "google":
        key = os.getenv("GOOGLE_API_KEY", "")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        r = httpx.post(url, json={"system_instruction": {"parts": [{"text": system}]},
                                  "contents": [{"role": "user", "parts": [{"text": user}]}]}, timeout=90)
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    raise RuntimeError(f"Unsupported provider '{provider}'.")


async def _provider_stream(system, message):
    import httpx
    provider, model = PROVIDER, MODEL
    if provider in ("xai", "openai"):
        url = "https://api.x.ai/v1/chat/completions" if provider == "xai" else "https://api.openai.com/v1/chat/completions"
        key = os.getenv("XAI_API_KEY" if provider == "xai" else "OPENAI_API_KEY", "")
        if not key:
            yield _no_key(provider); return
        async with httpx.AsyncClient(timeout=90) as client:
            async with client.stream("POST", url, headers={"Authorization": f"Bearer {key}"},
                                     json={"model": model, "stream": True,
                                           "messages": [{"role": "system", "content": system},
                                                        {"role": "user", "content": message}]}) as resp:
                async for line in resp.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        try:
                            tok = json.loads(line[6:])["choices"][0]["delta"].get("content", "")
                            if tok: yield tok
                        except (json.JSONDecodeError, KeyError, IndexError):
                            pass
    elif provider == "anthropic":
        key = os.getenv("ANTHROPIC_API_KEY", "")
        if not key:
            yield _no_key(provider); return
        async with httpx.AsyncClient(timeout=90) as client:
            async with client.stream("POST", "https://api.anthropic.com/v1/messages",
                                     headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
                                     json={"model": model, "max_tokens": 1500, "stream": True, "system": system,
                                           "messages": [{"role": "user", "content": message}]}) as resp:
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            ev = json.loads(line[6:])
                            if ev.get("type") == "content_block_delta":
                                tok = ev.get("delta", {}).get("text", "")
                                if tok: yield tok
                        except json.JSONDecodeError:
                            pass
    elif provider == "google":
        key = os.getenv("GOOGLE_API_KEY", "")
        if not key:
            yield _no_key(provider); return
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent?alt=sse&key={key}"
        async with httpx.AsyncClient(timeout=90) as client:
            async with client.stream("POST", url, json={"system_instruction": {"parts": [{"text": system}]},
                                                        "contents": [{"role": "user", "parts": [{"text": message}]}]}) as resp:
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            tok = json.loads(line[6:])["candidates"][0]["content"]["parts"][0].get("text", "")
                            if tok: yield tok
                        except (json.JSONDecodeError, KeyError, IndexError):
                            pass
    else:
        yield "No LLM provider configured. Set MODEL_PROVIDER + a key in .env."


def _no_key(provider):
    env = {"xai": "XAI_API_KEY", "openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY", "google": "GOOGLE_API_KEY"}[provider]
    return f"⚠ No **{env}** set. Add it to `.env` and restart to use AI chat and document generation."
