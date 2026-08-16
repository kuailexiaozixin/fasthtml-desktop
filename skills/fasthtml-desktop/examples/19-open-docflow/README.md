# open-docflow

**Dokumentu darbo eigos valdymo sistema** -- atvirojo kodo dokumentu apdorojimo ir darbo eigos variklis, sukurtas su FastHTML ir PostgreSQL.

**Open-source document workflow management system** -- a document processing and workflow engine built with FastHTML and PostgreSQL.

---

## Apie / About

### LT

`open-docflow` yra lengva, bet funkcional dokumentu darbo eigos sistema, skirta valdyti dokumentu gyvavimo cikla nuo gavimo iki patvirtinimo arba atmetimo. Sistema palaiko:

- Dokumentu ikelta (PDF, DOCX)
- Darbo eigos busenu valdyma: Gautas -> Perziurimas -> Patvirtintas / Atmestas
- Suvestine su dokumentu statistika pagal busena
- Paieska pagal tipa, data, busena
- Dokumento detales su audito sekimu
- Busenu perejimo validacija

### EN

`open-docflow` is a lightweight but functional document workflow system for managing the document lifecycle from receipt through approval or rejection. The system supports:

- Document upload (PDF, DOCX)
- Workflow status management: Received -> Under Review -> Approved / Rejected
- Dashboard with document statistics by status
- Search by type, date, status
- Document detail view with audit trail
- Transition validation

## Technologijos / Tech stack

- [FastHTML](https://fastht.ml/) -- Python web framework
- [PostgreSQL](https://www.postgresql.org/) -- database
- [HTMX](https://htmx.org/) -- dynamic UI
- [SQLAlchemy](https://www.sqlalchemy.org/) -- ORM
- [Pico CSS](https://picocss.com/) -- minimal CSS framework

## Busenu diagrama / State machine

```
gautas --> perziurimas --> patvirtintas
                      \-> atmestas --> perziurimas (pakartotine perziura)
```

## Paleistis / Getting started

### Reikalavimai / Requirements

- Python 3.10+
- PostgreSQL 14+

### Diegimas / Installation

```bash
# Klonuoti repozitorija
git clone https://github.com/predictivelabsai/open-docflow.git
cd open-docflow

# Sukurti virtualu aplinka
python3 -m venv .venv
source .venv/bin/activate

# Idiegti priklausomybes
pip install -e .

# Nustatyti duomenu baze
export DOCFLOW_DATABASE_URL="postgresql://user:password@localhost:5432/docflow"

# Sukurti schema (pasirinkite viena is budu)
# a) Per SQL
psql $DOCFLOW_DATABASE_URL -f sql/schema.sql

# b) Per Python (sukuria lenteles automatiskai)
python -c "from src.models import init_db; init_db()"

# Sugeneruoti pavyzdinius duomenis (200 dokumentu)
python data/generate_sample.py

# Paleisti aplikacija
python app.py
```

Aplikacija pasiekiama adresu: http://localhost:5099

## Projekto struktura / Project structure

```
open-docflow/
  app.py                    # FastHTML aplikacija
  src/
    models.py               # SQLAlchemy modeliai
    workflow.py              # Darbo eigos variklis
  sql/
    schema.sql              # PostgreSQL schema
  data/
    generate_sample.py      # Pavyzdiniu duomenu generatorius
  uploads/                  # Ikelti failai
  pyproject.toml
  LICENSE                   # MIT
```

## Duomenu modelis / Data model

### document_types
| Stulpelis | Tipas | Aprasymas |
|-----------|-------|-----------|
| id | SERIAL | Pirminis raktas |
| name | VARCHAR(100) | Tipo pavadinimas |
| description | TEXT | Aprasymas |
| required_fields | JSONB | Privalomi laukai |

### documents
| Stulpelis | Tipas | Aprasymas |
|-----------|-------|-----------|
| id | SERIAL | Pirminis raktas |
| title | VARCHAR(500) | Dokumento pavadinimas |
| doc_type_id | INTEGER | Nuoroda i document_types |
| status | VARCHAR(50) | gautas / perziurimas / patvirtintas / atmestas |
| uploaded_at | TIMESTAMPTZ | Ikelimo laikas |
| updated_at | TIMESTAMPTZ | Atnaujinimo laikas |
| file_path | VARCHAR(1000) | Failo kelias |
| metadata | JSONB | Papildomi metaduomenys |

### workflow_steps
| Stulpelis | Tipas | Aprasymas |
|-----------|-------|-----------|
| id | SERIAL | Pirminis raktas |
| document_id | INTEGER | Nuoroda i documents |
| from_status | VARCHAR(50) | Pradine busena |
| to_status | VARCHAR(50) | Galutine busena |
| actor | VARCHAR(200) | Vykdytojas |
| comment | TEXT | Komentaras |
| created_at | TIMESTAMPTZ | Iraso laikas |

## Dokumentu tipai / Document types

| Tipas | Aprasymas |
|-------|-----------|
| Prasymas | Oficialus prasymas institucijoms |
| Leidimas | Leidimas vykdyti veikla |
| Pazymejimas | Kvalifikacijos ar fakto patvirtinimas |
| Sutartis | Dviesale ar daugiasale sutartis |
| Ataskaita | Periodine arba vienkartine ataskaita |
| Isakymas | Vadovo ar institucijos isakymas |
| Protokolas | Posedzio ar susirinkimo protokolas |
| Aktas | Patikrinimo arba perdavimo aktas |

## Licencija / License

MIT -- zr. [LICENSE](LICENSE)

## Autorius / Author

[Predictive Labs](https://predictivelabs.co.uk)
