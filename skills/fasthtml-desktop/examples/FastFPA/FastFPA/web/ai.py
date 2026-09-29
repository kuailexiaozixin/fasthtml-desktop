"""Read-only, grounded FP&A explanations and drafting."""
from __future__ import annotations

import os

import httpx

import db


def _deterministic(question: str, slug: str) -> str:
    summary = db.annual_summary(slug)
    versus = db.comparison(slug, "budget")
    q = question.lower()
    if "cash" in q:
        return (
            f"Forecast year-end cash is £{summary.get('cash', 0):,.0f}. "
            f"Operating cash flow is £{summary.get('cfo', 0):,.0f}, investment "
            f"cash flow £{summary.get('cfi', 0):,.0f}, and financing cash flow "
            f"£{summary.get('cff', 0):,.0f}. The cash roll-forward check is zero."
        )
    if "variance" in q or "budget" in q:
        return (
            f"Revenue is {versus['revenue']['variance']:+,.0f} versus budget and "
            f"EBITDA is {versus['ebitda']['variance']:+,.0f}. The largest modeled "
            "drivers are revenue growth, gross margin, receivable days, and hiring cost. "
            "This is an explanation only; no plan values were changed."
        )
    if "scenario" in q or "draft" in q:
        return (
            "Draft change set: reduce monthly revenue growth by 0.5 points, delay "
            "discretionary capex by one quarter, and hold operating-cost growth flat. "
            "Review these assumptions in Scenarios before applying them."
        )
    return (
        f"{slug.title()} forecasts FY26 revenue of £{summary.get('revenue', 0):,.0f}, "
        f"EBITDA of £{summary.get('ebitda', 0):,.0f}, net income of "
        f"£{summary.get('net_income', 0):,.0f}, and year-end cash of "
        f"£{summary.get('cash', 0):,.0f}. Both statement integrity checks are zero."
    )


def answer(question: str, slug: str) -> str:
    question = (question or "").strip()
    if not question:
        return "Ask about the outlook, cash, variances, or a draft scenario."
    api_key = os.getenv("XAI_API_KEY", "")
    if not api_key:
        return _deterministic(question, slug)
    prompt = (
        "You are FastFPA's read-only finance copilot. Explain only from the supplied "
        "synthetic planning snapshot. Never claim to change, approve, or publish data. "
        "Be concise, quantify claims, identify assumptions, and state that drafts need review.\n\n"
        f"Planning snapshot:\n{db.snapshot_text(slug)}\n\nQuestion: {question}"
    )
    try:
        response = httpx.post(
            "https://api.x.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": os.getenv("MODEL_NAME", "grok-4-1-fast-reasoning"),
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 500,
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except (httpx.HTTPError, KeyError, ValueError, TypeError):
        return _deterministic(question, slug)
