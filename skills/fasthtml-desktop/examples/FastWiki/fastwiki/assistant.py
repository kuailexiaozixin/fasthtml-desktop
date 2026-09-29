from __future__ import annotations

import os
import re

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from . import db


SYSTEM_PROMPT = """You are the FastWiki AI Assistant. Answer using only the workspace pages supplied below.
Use concise, practical language. Cite factual statements with the numbered page references, such as [1].
If the pages do not contain the answer, say that clearly instead of guessing. Never reveal content from
another organisation or claim to have changed a page. You may propose page text or edits, but the user
must apply or approve them in FastWiki.
"""


def configured_admin(identity: dict) -> dict:
    admins={value.strip().lower() for value in os.getenv("FASTWIKI_ADMIN_EMAILS","").split(",") if value.strip()}
    if identity.get("email","").lower() in admins:
        identity={**identity,"role":"admin"}
    return identity


def query_limit(identity: dict) -> int | None:
    if db.is_admin(identity): return None
    try: value=int(os.getenv("FASTWIKI_AI_QUERY_LIMIT","5"))
    except ValueError: value=5
    return value if value>0 else None


def remaining_queries(identity: dict) -> int | None:
    limit=query_limit(identity)
    return None if limit is None else max(0,limit-db.assistant_queries_today(identity))


def _page_text(item: dict) -> str:
    text=(item.get("markdown") or item.get("plain_text") or "").strip()
    return re.sub(r"\s+"," ",text)


def source_pages(identity: dict,question: str,limit: int=6) -> list[dict]:
    terms={term for term in re.findall(r"[a-z0-9]{3,}",question.lower())}
    ranked=[]
    for item in db.visible_pages(identity):
        text=_page_text(item)
        haystack=f"{item['title']} {text}".lower()
        score=sum(3 if term in item["title"].lower() else 1 for term in terms if term in haystack)
        ranked.append((score,item.get("updated_at") or "",item,text))
    ranked.sort(key=lambda value:(value[0],value[1]),reverse=True)
    selected=ranked[:limit]
    return [{"id":item["id"],"title":item["title"],"status":item["status"],"excerpt":text[:420] or "No page text yet."} for _,_,item,text in selected]


def _model() -> ChatOpenAI:
    provider=os.getenv("FASTWIKI_AI_PROVIDER","xai").lower()
    if provider=="openai":
        key=os.getenv("OPENAI_API_KEY","")
        base_url=os.getenv("FASTWIKI_AI_BASE_URL") or None
        model=os.getenv("FASTWIKI_AI_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
    else:
        key=os.getenv("XAI_API_KEY","")
        base_url=os.getenv("FASTWIKI_AI_BASE_URL") or "https://api.x.ai/v1"
        model=os.getenv("FASTWIKI_AI_MODEL") or "grok-4.3"
    if not key: raise RuntimeError("The AI assistant is not configured.")
    return ChatOpenAI(
        api_key=key,
        base_url=base_url,
        model=model,
        temperature=0.2,
        timeout=60,
        max_retries=1,
        streaming=True,
    )


def stream_answer(identity: dict,question: str,history: list[dict],sources: list[dict]):
    context="\n\n".join(f"[{index}] {item['title']} ({item['status']})\n{item['excerpt']}" for index,item in enumerate(sources,1))
    messages=[SystemMessage(content=f"{SYSTEM_PROMPT}\n\nWORKSPACE PAGES:\n{context or 'No accessible pages.'}")]
    for message in history[-12:]:
        cls=HumanMessage if message["role"]=="user" else AIMessage
        messages.append(cls(content=message["content"]))
    messages.append(HumanMessage(content=question))
    for chunk in _model().stream(messages):
        content=chunk.content
        if isinstance(content,str) and content: yield content
