from datetime import date, timedelta

import pytest

from services.patient_service import register_patient
from services.appointment_service import book_appointment
from services.payment_service import (
    get_payment, mark_paid, waive_payment, fee_for_department,
    revenue_summary_for_date, PaymentError,
)
from database.models import Doctor


def _doctor_id(session):
    return session.query(Doctor).first().id


def test_booking_auto_creates_pending_payment(session):
    register_patient(session, "123456789012", "Ravi Kumar", 30, "M", "9876543210", "O+")
    tomorrow = date.today() + timedelta(days=1)
    appt = book_appointment(session, "123456789012", _doctor_id(session), tomorrow, "10:00")

    payment = get_payment(session, appt.id)
    assert payment is not None
    assert payment.status == "Pending"
    assert payment.amount == fee_for_department(appt.doctor.department)


def test_mark_paid_updates_status_and_metadata(session):
    register_patient(session, "123456789012", "Ravi Kumar", 30, "M", "9876543210", "O+")
    tomorrow = date.today() + timedelta(days=1)
    appt = book_appointment(session, "123456789012", _doctor_id(session), tomorrow, "10:00")

    payment = mark_paid(session, appt.id, "Cash", collected_by="admin")
    assert payment.status == "Paid"
    assert payment.method == "Cash"
    assert payment.collected_by == "admin"
    assert payment.paid_at is not None


def test_mark_paid_twice_rejected(session):
    register_patient(session, "123456789012", "Ravi Kumar", 30, "M", "9876543210", "O+")
    tomorrow = date.today() + timedelta(days=1)
    appt = book_appointment(session, "123456789012", _doctor_id(session), tomorrow, "10:00")
    mark_paid(session, appt.id, "Cash", collected_by="admin")
    with pytest.raises(PaymentError):
        mark_paid(session, appt.id, "Card", collected_by="admin")


def test_mark_paid_invalid_method_rejected(session):
    register_patient(session, "123456789012", "Ravi Kumar", 30, "M", "9876543210", "O+")
    tomorrow = date.today() + timedelta(days=1)
    appt = book_appointment(session, "123456789012", _doctor_id(session), tomorrow, "10:00")
    with pytest.raises(PaymentError):
        mark_paid(session, appt.id, "Bitcoin", collected_by="admin")


def test_waive_payment(session):
    register_patient(session, "123456789012", "Ravi Kumar", 30, "M", "9876543210", "O+")
    tomorrow = date.today() + timedelta(days=1)
    appt = book_appointment(session, "123456789012", _doctor_id(session), tomorrow, "10:00")
    payment = waive_payment(session, appt.id, collected_by="admin")
    assert payment.status == "Waived"
    assert payment.collected_by == "admin"


def test_revenue_summary_reflects_paid_and_pending(session):
    register_patient(session, "111111111111", "Patient One", 25, "M", "9876500001", "O+")
    register_patient(session, "222222222222", "Patient Two", 26, "F", "9876500002", "A+")
    today = date.today()
    doc_id = _doctor_id(session)

    appt1 = book_appointment(session, "111111111111", doc_id, today, "10:00")
    appt2 = book_appointment(session, "222222222222", doc_id, today, "10:30")
    mark_paid(session, appt1.id, "UPI", collected_by="admin")

    summary = revenue_summary_for_date(session, today)
    assert summary["paid_count"] == 1
    assert summary["pending_count"] == 1
    assert summary["collected"] == fee_for_department(appt1.doctor.department)
    assert summary["pending"] == fee_for_department(appt2.doctor.department)


def test_fee_for_unknown_department_has_fallback():
    assert fee_for_department("Some Made Up Department") == 500