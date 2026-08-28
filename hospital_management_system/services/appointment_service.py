"""
Appointment booking/lookup service.

The original project generated the "appointment number" with
`random.choice((23,34,12,67,53,72))` -- a fixed pool of six numbers shared by
every patient, guaranteed to collide constantly. Here the token number is the
next sequential number *for that doctor on that date*, which is how real
token/queue systems work (patient 1, 2, 3... for the day).
"""
from datetime import date as date_cls

from database.models import Appointment, Patient, Doctor


class BookingError(Exception):
    pass


def _next_token_no(session, doctor_id: int, appointment_date) -> int:
    count = (
        session.query(Appointment)
        .filter_by(doctor_id=doctor_id, appointment_date=appointment_date)
        .filter(Appointment.status != "Cancelled")
        .count()
    )
    return count + 1


def book_appointment(
    session, patient_govt_id: str, doctor_id: int, appointment_date, appointment_time: str,
    reason: str = None, predicted_department: str = None, predicted_urgency: str = None,
) -> Appointment:
    patient = session.query(Patient).filter_by(govt_id=patient_govt_id).first()
    if patient is None:
        raise BookingError(f"No patient found with ID {patient_govt_id}. Please register first.")

    doctor = session.query(Doctor).filter_by(id=doctor_id).first()
    if doctor is None:
        raise BookingError("Selected doctor was not found.")

    if isinstance(appointment_date, str):
        appointment_date = date_cls.fromisoformat(appointment_date)
    if appointment_date < date_cls.today():
        raise BookingError("Appointment date cannot be in the past.")

    # Prevent the exact same patient double-booking the exact same slot.
    clash = (
        session.query(Appointment)
        .filter_by(
            patient_id=patient.id, doctor_id=doctor_id,
            appointment_date=appointment_date, appointment_time=appointment_time,
        )
        .filter(Appointment.status != "Cancelled")
        .first()
    )
    if clash:
        raise BookingError("You already have an appointment with this doctor at this date/time.")

    token_no = _next_token_no(session, doctor_id, appointment_date)

    appt = Appointment(
        patient_id=patient.id,
        doctor_id=doctor_id,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        token_no=token_no,
        reason=(reason or "").strip() or None,
        predicted_department=predicted_department,
        predicted_urgency=predicted_urgency,
    )
    session.add(appt)
    session.commit()
    session.refresh(appt)
    return appt


def appointments_for_patient(session, govt_id: str):
    patient = session.query(Patient).filter_by(govt_id=govt_id).first()
    if patient is None:
        return []
    return (
        session.query(Appointment)
        .filter_by(patient_id=patient.id)
        .order_by(Appointment.appointment_date.desc())
        .all()
    )


def all_appointments(session, status: str = None):
    q = session.query(Appointment)
    if status:
        q = q.filter_by(status=status)
    return q.order_by(Appointment.appointment_date.desc()).all()


def update_status(session, appointment_id: int, status: str) -> Appointment:
    from config import APPOINTMENT_STATUSES
    if status not in APPOINTMENT_STATUSES:
        raise BookingError(f"Invalid status: {status}")
    appt = session.query(Appointment).filter_by(id=appointment_id).first()
    if appt is None:
        raise BookingError("Appointment not found.")
    appt.status = status
    session.commit()
    session.refresh(appt)
    return appt
