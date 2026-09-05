"""
Central configuration for the Hospital Management System.
Keeping these in one place avoids magic strings/numbers scattered across the app.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Database ---
# Local development / tests: falls back to a SQLite file automatically, no
# setup needed. Deployed app: set DATABASE_URL as a Streamlit Cloud "secret"
# (or an environment variable) to point at a real persistent Postgres
# instance -- this is what makes patient/appointment data survive the app
# sleeping and restarting, unlike a SQLite file living in the container.
DB_PATH = os.path.join(BASE_DIR, "hospital.db")


def _resolve_database_url() -> str:
    # 1. Environment variable (works on most hosts: Render, Railway, Docker, etc.)
    env_url = os.environ.get("DATABASE_URL")

    # 2. Streamlit Cloud's "Secrets" manager, if available. Wrapped in
    #    try/except because st.secrets raises if no secrets.toml exists at
    #    all (e.g. during local pytest runs, or local dev without one) --
    #    that's an expected, harmless case here, not an error worth surfacing.
    if not env_url:
        try:
            import streamlit as st
            if "DATABASE_URL" in st.secrets:
                env_url = st.secrets["DATABASE_URL"]
        except Exception:
            pass

    if env_url:
        # Neon/Supabase/Render/Heroku-style connection strings often start
        # with "postgres://" for legacy reasons; modern SQLAlchemy only
        # accepts the "postgresql://" scheme, so normalise it here rather
        # than making every deployer remember to edit their copied string.
        if env_url.startswith("postgres://"):
            env_url = env_url.replace("postgres://", "postgresql://", 1)
        return env_url

    # 3. Fallback: local SQLite file. Used for local development and for
    #    every automated test, so nobody needs a real database just to run
    #    `pytest` or `streamlit run app.py` on their own machine.
    return f"sqlite:///{DB_PATH}"


DATABASE_URL = _resolve_database_url()

# --- ML artifacts ---
ML_DIR = os.path.join(BASE_DIR, "ml")
MODEL_PATH = os.path.join(ML_DIR, "department_model.joblib")
DATASET_PATH = os.path.join(ML_DIR, "data", "symptom_dataset.csv")

# --- Domain constants ---
DEPARTMENTS = [
    "General Medicine",
    "Cardiology",
    "Orthopaedics",
    "Neurology",
    "Gynaecology",
    "Dermatology",
    "ENT",
    "Pediatrics",
    "Pulmonology",
    "Gastroenterology",
]

BLOOD_GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

URGENCY_LEVELS = ["Low", "Medium", "High", "Emergency"]

APPOINTMENT_STATUSES = ["Scheduled", "Completed", "Cancelled", "No-show"]

PAYMENT_METHODS = ["Cash", "Card", "UPI"]
PAYMENT_STATUSES = ["Pending", "Paid", "Waived"]

DEPARTMENT_FEES = {
    "General Medicine": 400,
    "Cardiology": 800,
    "Orthopaedics": 700,
    "Neurology": 900,
    "Gynaecology": 600,
    "Dermatology": 500,
    "ENT": 500,
    "Pediatrics": 450,
    "Pulmonology": 700,
    "Gastroenterology": 750,
}

USER_ROLES = ["admin", "doctor", "patient"]

TIME_SLOTS = [
    "09:00", "09:30", "10:00", "10:30", "11:00", "11:30",
    "12:00", "12:30", "14:00", "14:30", "15:00", "15:30",
    "16:00", "16:30", "17:00",
]

# --- App metadata ---
APP_NAME = "CityCare Hospital Management System"
APP_ICON = "🏥"

# Default admin account created on first run (change immediately in production)
DEFAULT_ADMIN_USERNAME = "admin_sobhan"
DEFAULT_ADMIN_PASSWORD = "sobhankundu1377"