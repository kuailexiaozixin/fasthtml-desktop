"""Seed FastMeet with synthetic meetings (deterministic)."""
from __future__ import annotations

import random
from datetime import timedelta

import db

RNG = random.Random(20260612)
NOW = db.NOW

PEOPLE = [
    ("Priya Nair", "priya@team.example"), ("Tom Becker", "tom@team.example"),
    ("Lena Sokolova", "lena@team.example"), ("Marco Bianchi", "marco@team.example"),
    ("Aisha Bello", "aisha@team.example"), ("Kenji Watanabe", "kenji@team.example"),
    ("Sara Lindholm", "sara@team.example"), ("Diego Ramos", "diego@team.example"),
    ("Nora Haddad", "nora@partner.example"), ("Felix Bauer", "felix@partner.example"),
]
TITLES = [
    ("Weekly Engineering Standup", "- Sprint progress\n- Blockers\n- Deploys this week"),
    ("Q3 Roadmap Review", "- Themes for Q3\n- Prioritisation\n- Resourcing\n- Risks"),
    ("Design Critique: Onboarding", "- Walkthrough of new flow\n- Open questions\n- Next iterations"),
    ("Customer Call — Northwind", "- Renewal terms\n- Feature requests\n- Support escalations"),
    ("1:1 with Priya", "- Wins this week\n- Career goals\n- Feedback"),
    ("Marketing Sync", "- Campaign performance\n- Content calendar\n- Budget"),
    ("All-Hands", "- Company update\n- Numbers\n- Q&A"),
    ("Sales Pipeline Review", "- Deals at risk\n- Forecast\n- Next steps"),
    ("Incident Retro: API outage", "- Timeline\n- Root cause\n- Action items"),
    ("Partner Onboarding — Helios", "- Integration plan\n- Timeline\n- Owners"),
    ("Hiring Debrief: Backend role", "- Candidate feedback\n- Decision\n- Next steps"),
    ("Product Demo — Aurora", "- Live demo\n- Pricing\n- Q&A"),
]
SUMMARIES = [
    "Team agreed to prioritise the analytics module; Priya to own the spec by Friday. Two blockers raised on the data pipeline.",
    "Renewal looks positive at a 2-year term; customer wants SSO and a security review. Follow-up scheduled.",
    "Root cause was a bad deploy; rollback restored service in 22 min. Three action items assigned to prevent recurrence.",
    "Strong demo, customer moving to a pilot. Pricing to be confirmed by sales. Intro to their security team requested.",
]


def _dt(days_offset, hour):
    return (NOW + timedelta(days=days_offset)).replace(hour=hour, minute=RNG.choice([0, 0, 30]), second=0).strftime("%Y-%m-%d %H:%M:%S")


def build():
    db.init_schema()
    with db.cursor() as conn:
        conn.execute("DELETE FROM participants")
        conn.execute("DELETE FROM meetings")
        conn.execute("DELETE FROM chat_messages")

    meetings = []
    # past meetings
    for i in range(8):
        title, agenda = RNG.choice(TITLES)
        days = -RNG.randint(1, 25)
        meetings.append((title, db.HOST, _dt(days, RNG.randint(9, 17)), RNG.choice([30, 45, 60]),
                         "Ended", f"room-{RNG.randint(1000,9999)}", agenda,
                         1 if RNG.random() < 0.7 else 0,
                         RNG.choice(SUMMARIES) if RNG.random() < 0.6 else None))
    # one live now
    title, agenda = RNG.choice(TITLES)
    meetings.append((title, db.HOST, NOW.strftime("%Y-%m-%d %H:%M:%S"), 30, "Live",
                     "room-live", agenda, 0, None))
    # upcoming (today + future)
    for i in range(11):
        title, agenda = RNG.choice(TITLES)
        if i < 3:
            days, hour = 0, RNG.randint(13, 18)  # later today
        else:
            days, hour = RNG.randint(1, 14), RNG.randint(9, 17)
        meetings.append((title, db.HOST, _dt(days, hour), RNG.choice([30, 45, 60]),
                         "Scheduled", f"room-{RNG.randint(1000,9999)}", agenda, 0, None))

    with db.cursor() as conn:
        conn.executemany(
            """INSERT INTO meetings(title,host,start_time,duration_min,status,room_code,agenda,has_recording,summary)
               VALUES (?,?,?,?,?,?,?,?,?)""", meetings)
        mids = [r[0] for r in conn.execute("SELECT id FROM meetings").fetchall()]

    parts = []
    for mid in mids:
        parts.append((mid, "You", db.HOST, "Host", "Accepted"))
        for nm, em in RNG.sample(PEOPLE, RNG.randint(2, 6)):
            parts.append((mid, nm, em, "Attendee", RNG.choices(db.RSVPS, weights=[55, 20, 10, 15])[0]))
    with db.cursor() as conn:
        conn.executemany("INSERT INTO participants(meeting_id,name,email,role,rsvp) VALUES (?,?,?,?,?)", parts)

    print(f"FastMeet seeded → {db.DB_PATH}")
    print(f"  {len(meetings)} meetings · {len(parts)} participant rows")


if __name__ == "__main__":
    build()
