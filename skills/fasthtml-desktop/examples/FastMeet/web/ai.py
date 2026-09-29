"""FastMeet AI — grounded chat, slash-commands, agenda gen & meeting summary."""
from __future__ import annotations

import json
import os
import html

import db

PROVIDER = os.getenv("MODEL_PROVIDER", "xai")
MODEL = os.getenv("MODEL_NAME", "grok-4-1-fast-reasoning")


def snapshot() -> str:
    st = db.stats()
    today = db.NOW.strftime("%Y-%m-%d")
    todays = db.rows("SELECT title, start_time, status FROM meetings WHERE start_time LIKE ? AND status!='Cancelled' ORDER BY start_time", (today + "%",))
    upcoming = db.rows("SELECT title, start_time FROM meetings WHERE start_time>? AND status='Scheduled' ORDER BY start_time LIMIT 8",
                       (db.NOW.strftime("%Y-%m-%d %H:%M:%S"),))
    lines = [
        f"MEETINGS SNAPSHOT (synthetic; now = {db.NOW.strftime('%Y-%m-%d %H:%M')}):",
        f"- Today: {st['today']} meetings. Upcoming: {st['upcoming']}. Live now: {st['live']}. Recordings: {st['recordings']}.",
        "Today's meetings: " + (", ".join(f"{m['title']} @ {m['start_time'][11:16]} ({m['status']})" for m in todays) or "none"),
        "Next up: " + (", ".join(f"{m['title']} ({m['start_time'][:16]})" for m in upcoming) or "none"),
    ]
    return "\n".join(lines)


SYSTEM_PROMPT = """You are the FastMeet assistant, embedded in a meeting-scheduling app.
Help the user with their schedule, draft agendas, and summarise meetings. Be concise; use Markdown.
Base schedule answers on the MEETINGS SNAPSHOT below; if something isn't there, say so."""


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
        return ("**FastMeet shortcuts**\n\n- `/today` — today's meetings\n- `/upcoming` — next meetings\n\n"
                "Open a meeting to **generate an agenda** or **summarise** it with AI.")
    if cmd == "today":
        today = db.NOW.strftime("%Y-%m-%d")
        r = db.rows("SELECT title, start_time, status FROM meetings WHERE start_time LIKE ? AND status!='Cancelled' ORDER BY start_time", (today + "%",))
        if not r:
            return "Nothing scheduled today. 🎉"
        return "**Today**\n\n" + _table(["Time", "Meeting", "Status"], [[x["start_time"][11:16], x["title"], x["status"]] for x in r])
    if cmd == "upcoming":
        r = db.rows("SELECT title, start_time FROM meetings WHERE start_time>? AND status='Scheduled' ORDER BY start_time LIMIT 12",
                    (db.NOW.strftime("%Y-%m-%d %H:%M:%S"),))
        return "**Upcoming**\n\n" + _table(["When", "Meeting"], [[x["start_time"][:16], x["title"]] for x in r])
    return f"Unknown command `/{cmd}`. Try `/help`."


# --- agenda / summary (non-streaming) ---------------------------------------

def _need_key():
    env = {"xai": "XAI_API_KEY", "openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY", "google": "GOOGLE_API_KEY"}.get(PROVIDER)
    if not env or not os.getenv(env):
        raise RuntimeError(f"No {env or 'LLM'} key set — add it to .env to use AI agenda/summary.")


def generate_agenda(mid):
    _need_key()
    m = db.meeting(mid)
    parts = db.participants(mid)
    who = ", ".join(p["name"] for p in parts[:6])
    out = _complete("Draft a tight meeting agenda as 4-6 Markdown bullet points. Output only the bullets.",
                    f"Meeting: {m['title']}\nDuration: {m['duration_min']} min\nParticipants: {who}")
    # persist as the agenda
    with db.cursor() as conn:
        conn.execute("UPDATE meetings SET agenda=? WHERE id=?", (out, mid))
    return html.escape(out).replace("\n", "<br>")


def summarise_meeting(mid):
    _need_key()
    m = db.meeting(mid)
    out = _complete("Write a 2-3 sentence summary of this meeting with one 'Action items:' line. "
                    "Invent plausible but generic content from the title/agenda. Be concise.",
                    f"Meeting: {m['title']}\nAgenda:\n{m['agenda']}")
    with db.cursor() as conn:
        conn.execute("UPDATE meetings SET summary=? WHERE id=?", (out, mid))
    return html.escape(out).replace("\n", "<br>")


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
                                                          {"role": "user", "content": user}]}, timeout=60)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    if provider == "anthropic":
        key = os.getenv("ANTHROPIC_API_KEY", "")
        r = httpx.post("https://api.anthropic.com/v1/messages",
                       headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
                       json={"model": model, "max_tokens": 600, "system": system,
                             "messages": [{"role": "user", "content": user}]}, timeout=60)
        r.raise_for_status()
        return r.json()["content"][0]["text"].strip()
    if provider == "google":
        key = os.getenv("GOOGLE_API_KEY", "")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        r = httpx.post(url, json={"system_instruction": {"parts": [{"text": system}]},
                                  "contents": [{"role": "user", "parts": [{"text": user}]}]}, timeout=60)
        r.raise_for_status()
        return r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
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
        yield "No LLM provider configured. Slash-commands like /today work without a key."


def _no_key(provider):
    env = {"xai": "XAI_API_KEY", "openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY", "google": "GOOGLE_API_KEY"}[provider]
    return (f"⚠ No **{env}** set, so free-form chat is disabled. Add it to `.env` and restart. "
            "Slash-commands (`/today`, `/upcoming`) work without any key.")
