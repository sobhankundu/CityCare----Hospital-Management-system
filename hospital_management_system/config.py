"""
Central configuration for the Hospital Management System.
Keeping these in one place avoids magic strings/numbers scattered across the app.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- Database ---
DB_PATH = os.path.join(BASE_DIR, "hospital.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

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
