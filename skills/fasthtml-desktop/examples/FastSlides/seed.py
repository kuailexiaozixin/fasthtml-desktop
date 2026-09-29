"""Seed FastSlides with a few sample decks (deterministic)."""
from __future__ import annotations

import db

DECKS = [
    ("Q3 Business Review", "Operations & growth", "midnight", [
        ("Q3 Business Review", "Operations & growth · Synthetic demo deck", "title"),
        ("Agenda", "- Where we are\n- What worked\n- What's next\n- Asks", "content"),
        ("Headline numbers", "- Revenue **+18%** QoQ\n- Net new customers: **42**\n- Churn down to **2.1%**\n- NPS **54**", "content"),
        ("What worked", "- New onboarding cut time-to-value by 40%\n- Partner channel now 22% of pipeline\n- Support SLA hit 96%", "content"),
        ("Challenges", "- Hiring lag in engineering\n- Enterprise sales cycle lengthening\n- Infra costs up 12%", "content"),
        ("Next quarter", "Three bets", "section"),
        ("The bets", "1. Ship the analytics module\n2. Land 3 lighthouse accounts\n3. Automate tier-1 support", "content"),
        ("Asks", "- Approve 4 eng hires\n- £150k marketing budget\n- Exec intros to target accounts", "content"),
        ("Thank you", "Questions?", "title"),
    ]),
    ("Product Launch: Aurora", "Go-to-market plan", "coral", [
        ("Introducing Aurora", "The fastest way to ship insight · Synthetic demo deck", "title"),
        ("The problem", "Teams drown in data but starve for decisions. Reports take days; answers come too late.", "content"),
        ("Our solution", "- Ask in plain English\n- Get a chart in seconds\n- Share a live dashboard", "content"),
        ("Why now", "- AI makes natural-language querying real\n- Data volumes exploding\n- Buyers expect self-serve", "content"),
        ("Launch plan", "- Week 1: private beta (20 design partners)\n- Week 4: public beta\n- Week 8: GA + pricing", "content"),
        ("Pricing", "- Free: 1 workspace\n- Team: £20/user/mo\n- Enterprise: custom", "content"),
        ("Let's go", "Aurora — ship insight, not reports.", "title"),
    ]),
    ("Intro to FastHTML", "Server-rendered Python apps", "forest", [
        ("Intro to FastHTML", "Build web apps in pure Python · Synthetic demo deck", "title"),
        ("What is FastHTML?", "- Starlette + Uvicorn + HTMX + FastTags\n- Server-rendered hypermedia\n- No JS framework needed", "content"),
        ("Hello world", "```python\nfrom fasthtml.common import *\napp,rt = fast_app()\n@rt('/')\ndef get(): return Titled('Hi', P('Hello'))\nserve()\n```", "content"),
        ("Why it's nice", "- One language, front to back\n- HTMX for interactivity\n- Tiny, fast, hackable", "content"),
        ("Thanks", "fastht.ml", "title"),
    ]),
]


def build():
    db.init_schema()
    with db.cursor() as conn:
        conn.execute("DELETE FROM slides")
        conn.execute("DELETE FROM presentations")
        conn.execute("DELETE FROM chat_messages")
    for title, subtitle, theme, slides in DECKS:
        db.create_presentation(title, subtitle, theme,
                               [{"title": t, "body": b, "layout": l} for t, b, l in slides])
    print(f"FastSlides seeded → {db.DB_PATH}")
    print(f"  {len(DECKS)} decks")


if __name__ == "__main__":
    build()
