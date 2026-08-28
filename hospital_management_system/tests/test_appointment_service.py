from datetime import date, timedelta

import pytest

from services.patient_service import register_patient
from services.appointment_service import book_appointment, BookingError
from database.models import Doctor


def _doctor_id(session):
    return session.query(Doctor).first().id


def test_book_appointment_success(session):
    register_patient(session, "123456789012", "Ravi Kumar", 30, "M", "9876543210", "O+")
    tomorrow = date.today() + timedelta(days=1)
    appt = book_appointment(session, "123456789012", _doctor_id(session), tomorrow, "10:00")
    assert appt.token_no == 1
    assert appt.status == "Scheduled"


def test_book_appointment_token_increments_per_doctor_per_day(session):
    register_patient(session, "111111111111", "Patient One", 25, "M", "9876500001", "O+")
    register_patient(session, "222222222222", "Patient Two", 26, "F", "9876500002", "A+")
    tomorrow = date.today() + timedelta(days=1)
    doc_id = _doctor_id(session)
    appt1 = book_appointment(session, "111111111111", doc_id, tomorrow, "10:00")
    appt2 = book_appointment(session, "222222222222", doc_id, tomorrow, "10:30")
    assert appt1.token_no == 1
    assert appt2.token_no == 2


def test_book_appointment_unknown_patient_rejected(session):
    tomorrow = date.today() + timedelta(days=1)
    with pytest.raises(BookingError):
        book_appointment(session, "000000000000", _doctor_id(session), tomorrow, "10:00")


def test_book_appointment_past_date_rejected(session):
    register_patient(session, "123456789012", "Ravi Kumar", 30, "M", "9876543210", "O+")
    yesterday = date.today() - timedelta(days=1)
    with pytest.raises(BookingError):
        book_appointment(session, "123456789012", _doctor_id(session), yesterday, "10:00")


def test_book_appointment_duplicate_slot_rejected(session):
    register_patient(session, "123456789012", "Ravi Kumar", 30, "M", "9876543210", "O+")
    tomorrow = date.today() + timedelta(days=1)
    doc_id = _doctor_id(session)
    book_appointment(session, "123456789012", doc_id, tomorrow, "10:00")
    with pytest.raises(BookingError):
        book_appointment(session, "123456789012", doc_id, tomorrow, "10:00")
