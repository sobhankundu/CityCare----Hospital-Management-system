# CityCare — Hospital Management System

**Live demo:** [citycare-hospital-sk.streamlit.app](https://citycare-hospital-sk.streamlit.app/)

A full-stack hospital management web app: patient registration, appointment
booking with live token queues, a staff operations dashboard, and an
ML-powered symptom checker + triage chatbot that recommends which department
to see and how urgently.

Built with **Python, Streamlit, SQLAlchemy (Postgres via Neon in production,
SQLite for zero-setup local development), and scikit-learn**.

> This started as a Tkinter + raw-SQL desktop script. It was rebuilt from the
> ground up as a deployed web app with a proper service layer, real
> authentication, a persistent cloud database, automated tests, and a machine
> learning component. See
> [What changed from the original version](#what-changed-from-the-original-version)
> for the full before/after.

---

## Features

**Patient portal**
- Self sign-up (creates both a login account and a patient record) or staff-assisted walk-in registration
- Book appointments with live, per-doctor sequential token/queue numbers
- AI Symptom Checker — select symptoms, get a recommended department + urgency level with model confidence scores
- Triage Chatbot — describe symptoms in plain language; typo-tolerant NLP extraction feeds the same ML model, with hard-coded emergency interrupts for red-flag symptoms
- Personal dashboard: upcoming appointments, visit history, medical records/prescriptions

**Staff / admin portal**
- Operations dashboard: patient/doctor/appointment KPIs, appointments-by-department and by-status charts, and live ML model-usage analytics (an "MLOps" touch — tracking how the model is actually being used, not just its offline accuracy)
- Manage appointments: update status, attach diagnosis/prescription notes on completion
- Search & edit patient records
- Doctor directory with roster management

**Engineering**
- Role-based authentication (admin / patient) with PBKDF2 password hashing — no plaintext passwords, ever
- Every database write goes through SQLAlchemy's ORM, so no query is ever built by string-formatting user input — this is what actually closes the SQL-injection hole in the original script
- Configurable persistence layer — SQLite locally for zero-setup development, managed Postgres (Neon) in production, switched entirely through a `DATABASE_URL` secret with no change to the ORM/service layer
- A synthetic-but-structured ML training pipeline (dataset generation → training → evaluation → inference) that's fully reproducible from source
- 35 automated tests (`pytest`) covering validators, services, booking edge cases, and the ML pipeline — including regression tests for two real bugs caught during development (see below)

---

## Architecture

```
hospital_management_system/
├── app.py                     # Entrypoint: DB init, login/signup, role-based nav
├── config.py                  # Central constants + DATABASE_URL resolution (env/secrets/local fallback)
├── database/
│   ├── models.py              # SQLAlchemy ORM schema
│   └── db.py                  # Engine/session management + first-run seeding
├── services/                  # Business logic, framework-agnostic & unit-testable
│   ├── auth_service.py
│   ├── patient_service.py
│   ├── doctor_service.py
│   └── appointment_service.py
├── ml/
│   ├── symptom_data.py        # Symptom vocabulary + department/emergency mappings (source of truth)
│   ├── generate_dataset.py    # Synthetic training data generator
│   ├── train_model.py         # Trains + evaluates the RandomForest classifiers
│   ├── predictor.py           # Inference wrapper used by the app
│   └── chatbot.py             # Rule-based NLP front-end + emergency interrupts
├── utils/
│   ├── validators.py          # Input validation (govt ID, phone, age, ...)
│   ├── security.py            # PBKDF2 password hashing
│   └── ui.py                  # Shared visual identity (theme, badges, components)
├── pages/                     # Streamlit multipage screens (11 pages)
└── tests/                     # 35 pytest tests across services + ML pipeline
```

**Why this layering:** `pages/` only ever calls into `services/`, never touches
the ORM directly. That means the actual business rules (can't book a past
date, token numbers increment per-doctor-per-day, an emergency symptom always
forces urgency to "Emergency" regardless of model confidence) are testable
without spinning up a browser, and are enforced identically whether the call
comes from the UI or a test.

---

## The ML component

There's no public "which hospital department does this symptom belong to"
dataset suitable for a portfolio project, so the training data is generated
programmatically from a hand-built `DEPARTMENT_SYMPTOMS` mapping (10
departments × 6-8 characteristic symptoms each), with weighted random
sampling, occasional cross-department "noise" symptoms (real patients don't
report cleanly), and urgency labels derived from a severity rule. This keeps
the entire pipeline — generation → training → inference — reproducible and
inspectable end to end, which is exactly what you want to be able to explain
in an interview instead of "I downloaded a Kaggle CSV."

Two `RandomForestClassifier`s are trained on a shared multi-hot symptom
feature matrix:
- **Department classifier** — ~99% test accuracy
- **Urgency classifier** — ~83% test accuracy (Low/Medium/High/Emergency)

Critically, **emergency symptoms hard-override the urgency classifier.** If a
patient mentions a red-flag symptom (e.g. "severe chest pain", "difficulty
breathing"), urgency is forced to `Emergency` regardless of what the model's
probability distribution says — a model's uncertainty should never be allowed
to downgrade a genuine red flag.

A rule-based (not LLM-based) chatbot sits on top of the same model, using
substring + typo-tolerant fuzzy matching to extract symptoms from free text.
This was a deliberate choice: a triage tool needs predictable, auditable
behavior, which a keyword-matching front end gives you and a general-purpose
LLM doesn't.

> **Disclaimer shown in-app:** this is a portfolio project. The symptom→department
> mapping was authored for demonstration purposes and is **not clinically
> validated**. It should never be presented as, or mistaken for, medical advice.

### A real bug this caught (worth mentioning in an interview)

While testing the chatbot, an early version of the typo-tolerant matcher
stripped severity words ("severe", "mild") before fuzzy-matching, so that a
patient typing **"chest pain"** would incorrectly match the vocabulary entry
**"severe chest pain"** — silently escalating a High-urgency case to a false
Emergency. It was caught by an end-to-end test that ran an actual chat
message through the pipeline and checked the resulting urgency level, not
just whether the code ran without crashing. The fix (require every word,
including severity qualifiers, to match) and the regression test that pins
this behavior are both in `tests/test_predictor.py`.

### A production lesson learned (also worth mentioning)

After the first deploy, patient and appointment data disappeared every time
the free-tier host put the app to sleep and restarted it. The cause wasn't a
code bug: SQLite was storing data as a file inside the container's own disk,
and a fresh container after a restart means a fresh, empty file — the
database was never actually persistent, it just looked that way during a
single continuous session. The fix was moving to a managed Postgres database
(Neon's free tier) with the connection string injected via environment-based
secrets, so the data now lives independently of the app container's
lifecycle. The code change itself was small — a `DATABASE_URL` resolver in
`config.py` and a couple of driver-specific lines in `database/db.py` — but
recognizing *why* a setup that worked perfectly on localhost breaks
specifically under ephemeral hosting, and fixing the actual constraint
instead of patching around the symptom, is the part worth being able to
explain.

---

## Setup

```bash
# 1. Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

With no `DATABASE_URL` configured, the app automatically falls back to a
local SQLite file (`hospital.db`), created on first run along with an admin
account and a seed roster of doctors — no external database needed for local
development. A pre-trained ML model is shipped in `ml/`, but if it's ever
deleted, `ml/predictor.py` regenerates the dataset and retrains automatically
the next time a prediction is requested.

**Local demo login:** username `admin`, password `admin123` (this is the
fallback default baked into `config.py` for local/SQLite runs only — see
[Known limitations](#known-limitations-and-honest-next-steps) for the caveat
on how the live deployment's admin password is currently handled). Patients
can self sign-up from the login screen.

### Running the tests

```bash
pytest tests/ -v
```

Tests always run against an isolated in-memory SQLite database regardless of
`DATABASE_URL`, so no external database is needed to run the suite.

### Deploying

The live demo runs on **Streamlit Community Cloud** with a **Neon** Postgres
database for persistent storage:

1. Push the repo to GitHub, then create an app on
   [share.streamlit.io](https://share.streamlit.io) pointing at `app.py`.
2. Create a free database at [neon.tech](https://neon.tech) and copy its
   connection string.
3. In the app's Settings → Secrets, add:
   ```toml
   DATABASE_URL = "postgresql://user:password@host/dbname?sslmode=require"
   ```
4. `config.py` picks this up automatically (env var or Streamlit secret, with
   `postgres://` normalised to `postgresql://` for compatibility) — no code
   changes needed between environments.

This also deploys as-is to any container host — a minimal `Dockerfile` is
included in the repo; just set `DATABASE_URL` as an environment variable on
whichever platform you use instead of a SQLite fallback if you want data to
survive restarts.

---

## What changed from the original version

| | Original script | This version |
|---|---|---|
| **Interface** | Tkinter desktop app, multiple `Tk()` root windows (unstable) | Streamlit web app — one link, deployed publicly, works on mobile |
| **Database access** | Raw SQL strings built with `.format()`/f-strings | SQLAlchemy ORM — parameterised by construction |
| **Known bugs** | `%s` placeholders used with `sqlite3` (wrong syntax — these queries crashed); appointment numbers picked from a shared 6-value pool (guaranteed collisions) | Fixed; token numbers are sequential per-doctor-per-day |
| **Data persistence** | N/A — single-user local file, no deployment | Managed Postgres (Neon) in production; survives restarts and redeploys |
| **Auth** | None — anyone could view/edit any record | Role-based login, PBKDF2-hashed passwords |
| **Validation** | None — age/phone/etc. accepted any text | Regex + range validation on every field, with tests |
| **Doctors/departments** | Hard-coded `if/elif` chains in the UI code | Data-driven from the database, editable via the admin UI |
| **Architecture** | One 500-line script, global variables | Layered: models / services / ml / pages, independently testable |
| **Tests** | None | 35 pytest tests |
| **AI/ML** | None | Symptom → department/urgency classifier + rule-based triage chatbot |

---

## Known limitations and honest next steps

Worth stating explicitly, because knowing the edges of what you built is part
of demonstrating seniority:

- **The live deployment's admin password currently lives in `config.py`,
  which is committed to this public repo.** It got set there directly during
  development rather than through a secret, the same way `DATABASE_URL` is
  handled. That's fine for a disposable local demo, but it means the
  password in this file *is* the live admin password right now — the
  immediate next step is moving `DEFAULT_ADMIN_PASSWORD` to a Streamlit
  secret/environment variable exactly like the database connection string,
  and rotating the live password once that's in place.
- **The symptom-checker dataset is synthetic**, not real clinical data. It's
  built from an authored domain mapping (see `ml/symptom_data.py`), not
  patient records, and isn't a substitute for a clinically validated tool.
- **No doctor-role login/portal.** Doctors currently exist only as directory
  entries managed by admins; a natural next step is a doctor account that can
  log in and manage their own queue/notes directly, rather than going through
  the admin's "Manage Appointments" screen.
- **No email/SMS appointment reminders or payment integration** — out of
  scope for this project, but the `Appointment` model already has the fields
  a reminder job would need to query against.