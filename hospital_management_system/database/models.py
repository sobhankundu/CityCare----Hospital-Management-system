"""
SQLAlchemy ORM models.

Using an ORM instead of hand-written SQL strings buys us two things that matter
for a "real world" system: (1) every query is parameterised by construction, so
SQL injection is not possible, and (2) the schema is defined once, in one place,
instead of being implied by scattered CREATE TABLE strings.
"""
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, DateTime, Date, Time, ForeignKey, Boolean, Text
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    """Login account. A User can be an admin, a doctor, or a patient.

    Patients and doctors each also get a matching Patient/Doctor profile row
    that holds domain-specific fields (blood group, specialisation, etc).
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    salt = Column(String(64), nullable=False)
    role = Column(String(16), nullable=False)  # admin | doctor | patient
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    patient_profile = relationship("Patient", back_populates="user", uselist=False)
    doctor_profile = relationship("Doctor", back_populates="user", uselist=False)


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    govt_id = Column(String(20), unique=True, nullable=False, index=True)  # Aadhaar-style ID
    name = Column(String(120), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(1), nullable=False)  # M | F | O
    phone = Column(String(15), nullable=False)
    blood_group = Column(String(3), nullable=False)
    address = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="patient_profile")
    appointments = relationship("Appointment", back_populates="patient")
    medical_records = relationship("MedicalRecord", back_populates="patient")


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String(120), nullable=False)
    department = Column(String(64), nullable=False)
    room_no = Column(String(10), nullable=False)
    phone = Column(String(15), nullable=True)
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="doctor_profile")
    appointments = relationship("Appointment", back_populates="doctor")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    appointment_date = Column(Date, nullable=False)
    appointment_time = Column(String(5), nullable=False)  # "HH:MM"
    token_no = Column(Integer, nullable=False)
    status = Column(String(16), default="Scheduled")
    reason = Column(String(255), nullable=True)
    predicted_department = Column(String(64), nullable=True)  # set by ML symptom checker, if used
    predicted_urgency = Column(String(16), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")


class MedicalRecord(Base):
    """A minimal EHR-style record: one row per visit/diagnosis note."""
    __tablename__ = "medical_records"

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    symptoms = Column(Text, nullable=True)
    diagnosis = Column(Text, nullable=True)
    prescription = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    patient = relationship("Patient", back_populates="medical_records")


class SymptomCheckLog(Base):
    """Every time the ML symptom checker is used, we log the input/output.

    This is what a real hospital system would do to (a) audit predictions and
    (b) eventually retrain the model on real usage data.
    """
    __tablename__ = "symptom_check_logs"

    id = Column(Integer, primary_key=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)
    symptoms_input = Column(Text, nullable=False)
    predicted_department = Column(String(64), nullable=False)
    confidence = Column(String(10), nullable=False)
    predicted_urgency = Column(String(16), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
