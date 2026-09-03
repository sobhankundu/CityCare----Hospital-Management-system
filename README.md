# CityCare — Hospital Management System 
 Click here --> https://citycare-hospital-sk.streamlit.app/

A full-stack hospital management web app: patient registration, appointment
booking with live token queues, a staff operations dashboard, and an
ML-powered symptom checker + triage chatbot that recommends which department
to see and how urgently.

Built with **Python, Streamlit, SQLAlchemy (SQLite), and scikit-learn**.

> This started as a Tkinter + raw-SQL desktop script. It was rebuilt from the
> ground up as a deployable web app with a proper service layer, real
> authentication, automated tests, and a machine learning component. See
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
- A synthetic-but-structured ML training pipeline (dataset generation → training → evaluation → inference) that's fully reproducible from source
- 35 automated tests (`pytest`) covering validators, services, booking edge cases, and the ML pipeline — including a regression test for a real bug caught during development (see below)

---

## Architecture

```
hospital_management_system/
├── app.py                     # Entrypoint: DB init, login/signup, role-based nav
├── config.py                  # Central constants (departments, blood groups, time slots...)
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

The database (`hospital.db`), an admin account, and a seed roster of doctors
are all created automatically on first run. A pre-trained model is shipped in
`ml/`, but if it's ever deleted, `ml/predictor.py` will regenerate the
dataset and retrain automatically the next time a prediction is requested.

**Demo login:** username `admin`, password `admin123` (change this before
any real deployment — see [Known limitations](#known-limitations-and-honest-next-steps)).
Patients can self sign-up from the login screen.

### Running the tests

```bash
pytest tests/ -v
```

### Deploying

This is a standard Streamlit app, so it deploys as-is to
[Streamlit Community Cloud](https://streamlit.io/cloud) (point it at `app.py`)
or any container host — a minimal `Dockerfile` would be:

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]
```

---

## What changed from the original version

| | Original script | This version |
|---|---|---|
| **Interface** | Tkinter desktop app, multiple `Tk()` root windows (unstable) | Streamlit web app — one link, deployable, works on mobile |
| **Database access** | Raw SQL strings built with `.format()`/f-strings | SQLAlchemy ORM — parameterised by construction |
| **Known bugs** | `%s` placeholders used with `sqlite3` (wrong syntax — these queries crashed); appointment numbers picked from a shared 6-value pool (guaranteed collisions) | Fixed; token numbers are sequential per-doctor-per-day |
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

- **The symptom-checker dataset is synthetic**, not real clinical data. It's
  built from an authored domain mapping (see `ml/symptom_data.py`), not
  patient records, and isn't a substitute for a clinically validated tool.
- **No doctor-role login/portal.** Doctors currently exist only as directory
  entries managed by admins; a natural next step is a doctor account that can
  log in and manage their own queue/notes directly, rather than going through
  the admin's "Manage Appointments" screen.
- **Default admin credentials ship in the repo** for demo convenience. A real
  deployment needs the admin password rotated on first login and the default
  credentials removed from `config.py`.
- **SQLite** is fine for a portfolio/demo deployment; a real multi-clinic
  system would move to Postgres (the SQLAlchemy layer makes that a
  `config.py` connection-string change, not a rewrite).
- **No email/SMS appointment reminders or payment integration** — out of
  scope for this project, but the `Appointment` model already has the fields
  a reminder job would need to query against.
