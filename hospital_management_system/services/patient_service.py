"""
Patient registration / lookup / update service.

Every write path here uses the ORM (parameterised by construction) instead of
formatted SQL strings -- this is the fix for the SQL-injection issue in the
original script's `entry()` and `do_modify()` functions.
"""
from config import BLOOD_GROUPS
from database.models import Patient
from utils.validators import validate_patient_form


class ValidationError(Exception):
    def __init__(self, errors):
        self.errors = errors
        super().__init__("; ".join(errors))


def register_patient(session, govt_id, name, age, gender, phone, blood_group, address=None) -> Patient:
    errors = validate_patient_form(govt_id, name, age, gender, phone, blood_group, BLOOD_GROUPS)
    if errors:
        raise ValidationError(errors)

    if session.query(Patient).filter_by(govt_id=govt_id).first() is not None:
        raise ValidationError([f"A patient with ID {govt_id} is already registered."])

    patient = Patient(
        govt_id=govt_id.strip(),
        name=name.strip(),
        age=int(age),
        gender=gender,
        phone=phone.strip(),
        blood_group=blood_group,
        address=(address or "").strip() or None,
    )
    session.add(patient)
    session.commit()
    session.refresh(patient)
    return patient


def find_patient_by_govt_id(session, govt_id: str):
    return session.query(Patient).filter_by(govt_id=govt_id.strip()).first()


def search_patients(session, query: str):
    """Search by govt_id (exact) or name (partial, case-insensitive)."""
    query = query.strip()
    if not query:
        return []
    exact = session.query(Patient).filter_by(govt_id=query).first()
    if exact:
        return [exact]
    return (
        session.query(Patient)
        .filter(Patient.name.ilike(f"%{query}%"))
        .limit(25)
        .all()
    )


FIELD_MAP = {
    "Name": "name",
    "Age": "age",
    "Gender": "gender",
    "Phone": "phone",
    "Blood Group": "blood_group",
    "Address": "address",
}


def update_patient_field(session, govt_id: str, field_label: str, new_value: str) -> Patient:
    patient = find_patient_by_govt_id(session, govt_id)
    if patient is None:
        raise ValidationError([f"No patient found with ID {govt_id}."])

    attr = FIELD_MAP.get(field_label)
    if attr is None:
        raise ValidationError([f"Unknown field: {field_label}"])

    # Reuse the same per-field validators the registration form uses, so an
    # update can't silently corrupt data the way the original app allowed.
    if attr == "age":
        from utils.validators import validate_age
        ok, msg = validate_age(new_value)
        if not ok:
            raise ValidationError([msg])
        new_value = int(new_value)
    elif attr == "gender":
        from utils.validators import validate_gender
        ok, msg = validate_gender(new_value)
        if not ok:
            raise ValidationError([msg])
    elif attr == "phone":
        from utils.validators import validate_phone
        ok, msg = validate_phone(new_value)
        if not ok:
            raise ValidationError([msg])
    elif attr == "blood_group":
        from utils.validators import validate_blood_group
        ok, msg = validate_blood_group(new_value, BLOOD_GROUPS)
        if not ok:
            raise ValidationError([msg])
    elif attr == "name":
        from utils.validators import validate_name
        ok, msg = validate_name(new_value)
        if not ok:
            raise ValidationError([msg])

    setattr(patient, attr, new_value)
    session.commit()
    session.refresh(patient)
    return patient


def all_patients(session):
    return session.query(Patient).order_by(Patient.created_at.desc()).all()
