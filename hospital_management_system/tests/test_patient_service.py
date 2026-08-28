import pytest

from services.patient_service import (
    register_patient, find_patient_by_govt_id, update_patient_field, ValidationError,
)


def test_register_patient_success(session):
    patient = register_patient(session, "123456789012", "Ravi Kumar", 30, "M", "9876543210", "O+")
    assert patient.id is not None
    assert find_patient_by_govt_id(session, "123456789012") is not None


def test_register_patient_duplicate_id_rejected(session):
    register_patient(session, "123456789012", "Ravi Kumar", 30, "M", "9876543210", "O+")
    with pytest.raises(ValidationError):
        register_patient(session, "123456789012", "Someone Else", 40, "F", "9876500000", "A+")


def test_register_patient_invalid_age_rejected(session):
    with pytest.raises(ValidationError):
        register_patient(session, "123456789012", "Ravi Kumar", 500, "M", "9876543210", "O+")


def test_register_patient_rejects_sql_injection_style_name(session):
    """Defense-in-depth, layer 1: input validation rejects a name containing
    SQL metacharacters before it ever reaches the database."""
    payload = '"); DROP TABLE appointments;--'
    with pytest.raises(ValidationError):
        register_patient(session, "999999999999", payload, 30, "M", "9876543210", "O+")


def test_orm_layer_never_builds_raw_sql_from_input(session):
    """Defense-in-depth, layer 2: even if a malicious string got past
    validation, the ORM binds it as a parameter rather than interpolating it
    into a SQL string, so the appointments table survives regardless."""
    from database.models import Appointment
    # bypass the name validator entirely to simulate a hostile raw insert
    from database.models import Patient
    session.add(Patient(
        govt_id="888888888888", name='Robert"); DROP TABLE appointments;--',
        age=30, gender="M", phone="9876543210", blood_group="O+",
    ))
    session.commit()
    assert find_patient_by_govt_id(session, "888888888888") is not None
    # table is untouched -- querying it doesn't raise
    assert session.query(Appointment).count() == 0


def test_update_patient_field(session):
    register_patient(session, "123456789012", "Ravi Kumar", 30, "M", "9876543210", "O+")
    updated = update_patient_field(session, "123456789012", "Age", "31")
    assert updated.age == 31


def test_update_patient_field_invalid_value_rejected(session):
    register_patient(session, "123456789012", "Ravi Kumar", 30, "M", "9876543210", "O+")
    with pytest.raises(ValidationError):
        update_patient_field(session, "123456789012", "Phone", "123")
