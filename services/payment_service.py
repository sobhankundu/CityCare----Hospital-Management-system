"""
Counter payment service.

Payment is created automatically the moment an appointment is booked
(status "Pending", amount = the department's flat consultation fee), and
front-desk staff mark it "Paid" once the patient pays at the counter --
this module never talks to an external payment gateway.
"""
from datetime import date as date_cls, datetime, timezone

from config import DEPARTMENT_FEES, PAYMENT_METHODS
from database.models import Payment, Appointment


class PaymentError(Exception):
    pass


def fee_for_department(department: str) -> int:
    return DEPARTMENT_FEES.get(department, 500)  # sensible fallback if a department is missing a listed fee


def create_payment_for_appointment(session, appointment: Appointment) -> Payment:
    """Called from appointment_service.book_appointment() right after an
    appointment is created. Idempotent: if a payment already exists for this
    appointment (shouldn't normally happen), returns the existing one rather
    than creating a duplicate, since appointment_id is unique on Payment.
    """
    existing = session.query(Payment).filter_by(appointment_id=appointment.id).first()
    if existing:
        return existing

    payment = Payment(
        appointment_id=appointment.id,
        amount=fee_for_department(appointment.doctor.department),
        status="Pending",
    )
    session.add(payment)
    session.commit()
    session.refresh(payment)
    return payment


def get_payment(session, appointment_id: int):
    return session.query(Payment).filter_by(appointment_id=appointment_id).first()


def mark_paid(session, appointment_id: int, method: str, collected_by: str) -> Payment:
    if method not in PAYMENT_METHODS:
        raise PaymentError(f"Invalid payment method: {method}")

    payment = get_payment(session, appointment_id)
    if payment is None:
        raise PaymentError("No payment record found for this appointment.")
    if payment.status == "Paid":
        raise PaymentError("This payment has already been marked as paid.")

    payment.status = "Paid"
    payment.method = method
    payment.collected_by = collected_by
    payment.paid_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(payment)
    return payment


def waive_payment(session, appointment_id: int, collected_by: str) -> Payment:
    """For genuine no-charge cases (e.g. charity, staff family) -- keeps a
    record of who waived it rather than silently deleting the payment row."""
    payment = get_payment(session, appointment_id)
    if payment is None:
        raise PaymentError("No payment record found for this appointment.")
    payment.status = "Waived"
    payment.collected_by = collected_by
    payment.paid_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(payment)
    return payment


def appointments_with_payment_for_date(session, target_date=None):
    """Returns [(Appointment, Payment), ...] for the given date (default:
    today), ordered by doctor then token number -- the shape a front-desk
    billing screen actually wants to render."""
    target_date = target_date or date_cls.today()
    appointments = (
        session.query(Appointment)
        .filter_by(appointment_date=target_date)
        .filter(Appointment.status != "Cancelled")
        .all()
    )
    appointments.sort(key=lambda a: (a.doctor.name, a.token_no))
    return [(a, a.payment) for a in appointments]


def revenue_summary_for_date(session, target_date=None) -> dict:
    """Small aggregate used by the admin dashboard: collected vs pending
    amount for a given day (default: today)."""
    rows = appointments_with_payment_for_date(session, target_date)
    collected = sum(p.amount for _, p in rows if p and p.status == "Paid")
    pending = sum(p.amount for _, p in rows if p and p.status == "Pending")
    waived = sum(p.amount for _, p in rows if p and p.status == "Waived")
    return {
        "collected": collected,
        "pending": pending,
        "waived": waived,
        "paid_count": sum(1 for _, p in rows if p and p.status == "Paid"),
        "pending_count": sum(1 for _, p in rows if p and p.status == "Pending"),
    }