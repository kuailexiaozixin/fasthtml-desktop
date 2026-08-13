"""Generate 200 sample documents with realistic Lithuanian government document types.

Usage:
    python data/generate_sample.py

Writes to the SQLite file resolved by src/models.py (DOCFLOW_DB env var, or
<project>/data/open-docflow.sqlite by default). No database server required.
"""

from __future__ import annotations

import random
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, ".")

from src.models import Document, DocumentType, WorkflowStep, get_session, init_db

# --- Configuration ---

ACTORS = [
    "Jonas Kazlauskas",
    "Ruta Petrauskiene",
    "Andrius Balcius",
    "Asta Jonaite",
    "Marius Stankevicius",
    "Ieva Navickaite",
    "Tomas Grigas",
    "Giedre Paulauskaite",
]

ORGANIZATIONS = [
    "UAB Technologijos",
    "VsI Svietimo centras",
    "UAB Inovacijos",
    "MB Dokumentu sprendimai",
    "UAB Konsultacijos",
    "VsI Aplinkos projektai",
    "UAB Skaitmena",
    "MB Verslo paslaugos",
]

# (doc_type_name, title_templates)
DOC_TEMPLATES: list[tuple[str, list[str]]] = [
    (
        "Prasymas",
        [
            "Prasymas del {subject}",
            "Prasymas suteikti {subject}",
            "Prasymas perziureti {subject}",
        ],
    ),
    (
        "Leidimas",
        [
            "Leidimas vykdyti {subject}",
            "Leidimas Nr. {ref} — {subject}",
            "Statybos leidimas: {subject}",
        ],
    ),
    (
        "Pazymejimas",
        [
            "Pazymejimas apie {subject}",
            "Kvalifikacijos pazymejimas — {subject}",
            "Registracijos pazymejimas Nr. {ref}",
        ],
    ),
    (
        "Sutartis",
        [
            "Paslaugu teikimo sutartis — {subject}",
            "Bendradarbiavimo sutartis Nr. {ref}",
            "Pirkimo sutartis: {subject}",
        ],
    ),
    (
        "Ataskaita",
        [
            "Metine ataskaita: {subject}",
            "Ketvirtine ataskaita — {subject}",
            "Projekto ataskaita Nr. {ref}",
        ],
    ),
    (
        "Isakymas",
        [
            "Isakymas del {subject}",
            "Direktoriaus isakymas Nr. {ref}",
            "Isakymas del darbuotoju {subject}",
        ],
    ),
    (
        "Protokolas",
        [
            "Posedzio protokolas — {subject}",
            "Visuotinio susirinkimo protokolas Nr. {ref}",
            "Komisijos posedzio protokolas: {subject}",
        ],
    ),
    (
        "Aktas",
        [
            "Perdavimo-priemimo aktas — {subject}",
            "Patikrinimo aktas Nr. {ref}",
            "Inventorizacijos aktas: {subject}",
        ],
    ),
]

SUBJECTS = [
    "informaciniu sistemu atnaujinimo",
    "duomenu tvarkymo tvarkos",
    "darbuotoju kvalifikacijos kelimo",
    "biudzeto paskirstymo",
    "IT infrastrukturos modernizavimo",
    "viesuju pirkimu organizavimo",
    "aplinkosaugos reikalavimu",
    "projekto igyvendinimo eigos",
    "tarnybines veiklos vertinimo",
    "ilgalaikio turto nurasymo",
    "dokumentu valdymo sistemos diegimo",
    "kibernetinio saugumo priemoniu",
    "skaitmenizacijos programos",
    "kokybos valdymo standarto",
    "finansines ataskaitos pateikimo",
    "personalo atrankos tvarkos",
    "darbo organizavimo nuotoliniu budu",
    "vidaus audito rezultatu",
    "strateginio plano rengimo",
    "klientu aptarnavimo gerinimo",
]

COMMENTS = [
    "Dokumentas atitinka reikalavimus.",
    "Reikia papildyti informacija.",
    "Visos salygos isvykdytos.",
    "Persiusta perziurai.",
    "Prideti trukstami priedai.",
    "Suderintas su skyriaus vadovu.",
    "Pateikta pagal nustatyta tvarka.",
    "Pastabos istaisytos, pateikiama pakartotinai.",
    None,
    None,
    None,
]

STATUSES = ["gautas", "perziurimas", "patvirtintas", "atmestas"]
STATUS_WEIGHTS = [0.15, 0.25, 0.40, 0.20]


def random_ref() -> str:
    return f"{random.randint(1, 999):03d}-{random.randint(2024, 2026)}/{random.randint(1, 12):02d}"


def generate_documents(n: int = 200) -> None:
    db = get_session()

    # Ensure schema + tables exist
    init_db()

    # Load document types (must exist from schema.sql or init_db)
    doc_types = {dt.name: dt for dt in db.query(DocumentType).all()}

    # Seed any missing types
    for type_name, _ in DOC_TEMPLATES:
        if type_name not in doc_types:
            dt = DocumentType(name=type_name, description=f"{type_name} dokumentas")
            db.add(dt)
            db.flush()
            doc_types[type_name] = dt

    db.commit()

    now = datetime.now(timezone.utc)

    for i in range(n):
        type_name, templates = random.choice(DOC_TEMPLATES)
        template = random.choice(templates)
        title = template.format(
            subject=random.choice(SUBJECTS),
            ref=random_ref(),
        )

        # Random dates within the past 180 days
        days_ago = random.randint(0, 180)
        uploaded_at = now - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))

        final_status = random.choices(STATUSES, weights=STATUS_WEIGHTS, k=1)[0]

        doc = Document(
            title=title,
            doc_type_id=doc_types[type_name].id,
            status=final_status,
            uploaded_at=uploaded_at,
            updated_at=uploaded_at,
            file_path=f"uploads/{type_name.lower()}_{i + 1:04d}.pdf",
            file_size=random.randint(50_000, 5_000_000),
            # DB column is still "metadata"; the Python attribute is renamed
            # because `metadata` is reserved on SQLAlchemy declarative classes.
            doc_metadata={
                "organizacija": random.choice(ORGANIZATIONS),
                "puslapiai": random.randint(1, 50),
            },
            submitted_by=random.choice(ACTORS),
            assigned_to=random.choice(ACTORS),
        )
        db.add(doc)
        db.flush()

        # Generate workflow steps for the document's history
        steps_timeline = _build_step_history(final_status, uploaded_at)
        last_updated = uploaded_at
        for from_s, to_s, step_time in steps_timeline:
            step = WorkflowStep(
                document_id=doc.id,
                from_status=from_s,
                to_status=to_s,
                actor=random.choice(ACTORS),
                comment=random.choice(COMMENTS),
                created_at=step_time,
            )
            db.add(step)
            last_updated = step_time

        doc.updated_at = last_updated

    db.commit()
    db.close()
    print(f"Sukurti {n} pavyzdiniai dokumentai.")


def _build_step_history(
    final_status: str, start: datetime
) -> list[tuple[str | None, str, datetime]]:
    """Build a realistic step history leading to the final status."""
    steps: list[tuple[str | None, str, datetime]] = []
    t = start + timedelta(minutes=random.randint(1, 30))

    # Initial receipt
    steps.append((None, "gautas", t))

    if final_status == "gautas":
        return steps

    # Move to review
    t += timedelta(hours=random.randint(1, 72))
    steps.append(("gautas", "perziurimas", t))

    if final_status == "perziurimas":
        return steps

    # Final decision
    t += timedelta(hours=random.randint(4, 168))
    steps.append(("perziurimas", final_status, t))

    return steps


if __name__ == "__main__":
    generate_documents(200)
