"""
Input validation. The original project trusted every field blindly (e.g. age
and phone were free-text with no checks), which let bad data into the
database and would crash downstream code. Each function here returns
(is_valid: bool, error_message: str).
"""
import re

GOVT_ID_RE = re.compile(r"^\d{12}$")          # 12-digit Aadhaar-style ID
PHONE_RE = re.compile(r"^[6-9]\d{9}$")        # 10-digit Indian mobile number
NAME_RE = re.compile(r"^[A-Za-z][A-Za-z .'-]{1,119}$")


def validate_govt_id(value: str):
    if not value or not GOVT_ID_RE.match(value.strip()):
        return False, "ID number must be exactly 12 digits."
    return True, ""


def validate_name(value: str):
    if not value or not NAME_RE.match(value.strip()):
        return False, "Name must be at least 2 letters and contain only letters, spaces, or - ' ."
    return True, ""


def validate_age(value):
    try:
        age = int(value)
    except (TypeError, ValueError):
        return False, "Age must be a whole number."
    if not (0 < age <= 130):
        return False, "Age must be between 1 and 130."
    return True, ""


def validate_gender(value: str):
    if value not in ("M", "F", "O"):
        return False, "Gender must be M, F, or O."
    return True, ""


def validate_phone(value: str):
    if not value or not PHONE_RE.match(value.strip()):
        return False, "Phone must be a valid 10-digit mobile number."
    return True, ""


def validate_blood_group(value: str, allowed):
    if value not in allowed:
        return False, f"Blood group must be one of {', '.join(allowed)}."
    return True, ""


def validate_patient_form(govt_id, name, age, gender, phone, blood_group, allowed_blood_groups):
    """Runs every field check and returns a list of error strings (empty = valid)."""
    checks = [
        validate_govt_id(govt_id),
        validate_name(name),
        validate_age(age),
        validate_gender(gender),
        validate_phone(phone),
        validate_blood_group(blood_group, allowed_blood_groups),
    ]
    return [msg for ok, msg in checks if not ok]
