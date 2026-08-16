"""FastSlides AI — deck generation, grounded chat, slash-commands."""
from __future__ import annotations

import json
import os
import re

import db

PROVIDER = os.getenv("MODEL_PROVIDER", "xai")
MODEL = os.getenv("MODEL_NAME", "grok-4-1-fast-reasoning")


def snapshot() -> str:
    decks = db.presentations()
    lines = ["DECK LIBRARY (synthetic):", f"- {len(decks)} decks."]
    for d in decks:
        lines.append(f"  - '{d['title']}' ({d['n']} slides, {d['theme']} theme)")
    return "\n".join(lines)


SYSTEM_PROMPT = """You are the FastSlides assistant, embedded in a presentation builder.
Help the user outline and improve slide decks. Be concise; use Markdown.
Base answers on the DECK LIBRARY below where relevant."""

DECK_SYSTEM = """You generate presentation slide decks. Return ONLY a JSON array (no prose, no
markdown fences). Each element is an object: {"title": str, "body": str, "layout": "title"|"section"|"content"}.
Rules:
- First slide: layout "title", body = a one-line subtitle.
- Use "content" for most slides; body is short Markdown bullet points ("- point").
- Optionally one "section" divider slide.
- Last slide: layout "title" (a closing/thank-you).
- Keep bullets punchy. Produce exactly the requested number of slides."""


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
        return ("**FastSlides shortcuts**\n\n- `/decks` — list your decks\n\n"
                "Use **Generate with AI** to create a full deck from a prompt, or ask here for slide ideas.")
    if cmd == "decks":
        d = db.presentations()
        return "**Your decks**\n\n" + _table(["Title", "Slides", "Theme"], [[x["title"], x["n"], x["theme"]] for x in d])
    return f"Unknown command `/{cmd}`. Try `/help`."


# --- deck generation --------------------------------------------------------

def generate_deck(topic: str, count: int = 6):
    """Return (title, subtitle, slides[]) or raise RuntimeError."""
    key_env = {"xai": "XAI_API_KEY", "openai": "OPENAI_API_KEY",
               "anthropic": "ANTHROPIC_API_KEY", "google": "GOOGLE_API_KEY"}.get(PROVIDER)
    if not key_env or not os.getenv(key_env):
        raise RuntimeError(f"No {key_env or 'LLM'} key set — add it to .env to generate decks with AI.")
    prompt = f"Create a {count}-slide deck about: {topic}"
    raw = _complete(DECK_SYSTEM, prompt)
    arr = _extract_json(raw)
    if not arr:
        raise RuntimeError("The model did not return a valid deck. Try rephrasing.")
    slides = []
    for s in arr:
        if not isinstance(s, dict):
            continue
        layout = s.get("layout", "content")
        if layout not in ("title", "section", "content"):
            layout = "content"
        slides.append({"title": str(s.get("title", "")), "body": str(s.get("body", "")), "layout": layout})
    if not slides:
        raise RuntimeError("The generated deck was empty. Try again.")
    title = slides[0]["title"] or topic[:60]
    subtitle = slides[0]["body"] or ""
    return title, subtitle, slides


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
                       json={"model": model, "max_tokens": 2000, "system": system,
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
    return f"⚠ No **{env}** set. Add it to `.env` and restart to use AI chat and deck generation."
