"""Deterministic synthetic seed for FastDocs — folders, documents, templates.

`python seed.py` wipes and repopulates. No PII; data is fixed (no RNG needed).
"""
from __future__ import annotations

import db

# folder name -> [ (title, [ (type, content), ... ]) ]
WORKSPACE = {
    "Product": [
        ("Q3 Product Plan", [
            ("heading1", "Q3 Product Plan"),
            ("paragraph", "This document outlines the **product priorities** for the third quarter. "
                          "It is the single source of truth for what we ship and why."),
            ("heading2", "Objectives"),
            ("bullet", "Ship the collaborative editor to general availability\n"
                       "Cut median page-load time below 200ms\n"
                       "Launch the public template gallery"),
            ("heading2", "Out of scope"),
            ("paragraph", "Real-time multiplayer cursors are explicitly deferred to Q4 — see the "
                          "[roadmap](#) for the rationale."),
            ("quote", "Do less, but ship it end to end."),
            ("heading2", "Open questions"),
            ("numbered", "How do we price the template gallery?\n"
                         "Which metric defines \"page-load\" — first paint or interactive?"),
        ]),
        ("Editor Architecture Notes", [
            ("heading1", "Editor Architecture Notes"),
            ("paragraph", "A document is an ordered list of typed *blocks*. The server renders each "
                          "block to HTML; the client only swaps fragments over HTMX."),
            ("heading3", "Block types"),
            ("bullet", "Headings (1–3)\nParagraph\nBulleted / numbered lists\nQuote\nCode\nDivider"),
            ("code", "def render_block(b):\n    if b['type'] == 'divider':\n        return Hr()\n    return TYPES[b['type']](b['content'])"),
        ]),
    ],
    "Company": [
        ("Engineering Handbook", [
            ("heading1", "Engineering Handbook"),
            ("paragraph", "Welcome to the team. This handbook collects the conventions we agree to "
                          "follow so the codebase stays legible as we grow."),
            ("heading2", "Principles"),
            ("numbered", "Optimise for the reader, not the writer.\n"
                         "Prefer boring, well-understood tools.\n"
                         "Leave the code better than you found it."),
            ("heading2", "Code review"),
            ("paragraph", "Every change is reviewed by at least one other engineer. Keep diffs small "
                          "and self-contained; a reviewer should hold the whole change in their head."),
            ("divider", ""),
            ("paragraph", "Questions? Ask in **#engineering** — no question is too small."),
        ]),
        ("Onboarding Checklist", [
            ("heading1", "Onboarding Checklist"),
            ("paragraph", "Your first week, step by step."),
            ("bullet", "Get accounts: email, repo, chat\n"
                       "Clone the monorepo and run the dev server\n"
                       "Pair with your onboarding buddy on a starter task\n"
                       "Read the Engineering Handbook"),
        ]),
    ],
    "Personal": [
        ("Meeting Notes — Kickoff", [
            ("heading1", "Kickoff — Meeting Notes"),
            ("paragraph", "**Attendees:** Ada, Grace, Linus. **Date:** synthetic."),
            ("heading2", "Decisions"),
            ("bullet", "Ship the MVP behind a feature flag\nWeekly demo every Friday"),
            ("heading2", "Action items"),
            ("numbered", "Ada to draft the API contract\nGrace to set up CI\nLinus to write the seed data"),
        ]),
    ],
}

# Reusable templates: (title, description, [ (type, content) ])
TEMPLATES = [
    ("Meeting Notes", "Agenda, decisions and action items.", [
        ("heading1", "Meeting Notes — <topic>"),
        ("paragraph", "**Attendees:** \n**Date:** "),
        ("heading2", "Agenda"),
        ("bullet", "Item one\nItem two"),
        ("heading2", "Decisions"),
        ("bullet", "…"),
        ("heading2", "Action items"),
        ("numbered", "Owner — task\nOwner — task"),
    ]),
    ("Project Brief", "One-page framing for a new project.", [
        ("heading1", "Project Brief — <name>"),
        ("heading2", "Problem"),
        ("paragraph", "What are we solving and for whom?"),
        ("heading2", "Goals"),
        ("bullet", "Goal one\nGoal two"),
        ("heading2", "Non-goals"),
        ("paragraph", "What this project deliberately will not do."),
        ("heading2", "Milestones"),
        ("numbered", "Milestone one\nMilestone two"),
    ]),
    ("Blog Post", "Draft scaffold for a public post.", [
        ("heading1", "<Headline>"),
        ("paragraph", "A one-sentence hook that makes the reader want to continue."),
        ("heading2", "The problem"),
        ("paragraph", "…"),
        ("heading2", "The idea"),
        ("paragraph", "…"),
        ("quote", "A pithy, quotable line."),
        ("heading2", "Takeaways"),
        ("bullet", "Point one\nPoint two"),
    ]),
]


def build():
    db.init_schema()
    with db.cursor() as conn:
        for tbl in ("chat_messages", "doc_versions", "template_blocks", "templates", "blocks", "documents", "folders"):
            conn.execute(f"DELETE FROM {tbl}")

    for fname, docs in WORKSPACE.items():
        fid = db.create_folder(fname)
        for title, blks in docs:
            db.create_document(fid, title, [{"type": t, "content": c} for t, c in blks])

    for title, desc, blks in TEMPLATES:
        db.create_template(title, desc, [{"type": t, "content": c} for t, c in blks])

    # one document published + one with a couple of saved versions, for the demo
    handbook = db.one("SELECT id FROM documents WHERE title='Engineering Handbook'")
    plan = db.one("SELECT id FROM documents WHERE title='Q3 Product Plan'")
    if handbook:
        db.publish(handbook["id"])
    if plan:
        db.snapshot_version(plan["id"], manual=True)
        db.snapshot_version(plan["id"], manual=True)

    print(f"FastDocs seeded → {db.DB_PATH}")


if __name__ == "__main__":
    build()
