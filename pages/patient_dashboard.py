from datetime import date

import streamlit as st

from database.db import session_scope
from services.patient_service import find_patient_by_govt_id
from services.appointment_service import appointments_for_patient
from utils.ui import inject_css, page_header, status_badge, urgency_badge

inject_css()
page_header("My Dashboard", eyebrow="Patient Portal")

govt_id = st.session_state.get("patient_govt_id")
if not govt_id:
    st.warning("No patient profile is linked to this account. Please contact the front desk.")
    st.stop()

with session_scope() as session:
    patient = find_patient_by_govt_id(session, govt_id)
    if patient is None:
        st.error("Patient profile not found.")
        st.stop()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Name", patient.name)
    col2.metric("Age", patient.age)
    col3.metric("Blood Group", patient.blood_group)
    col4.metric("Patient ID", patient.govt_id)

    st.divider()
    st.subheader("Upcoming & recent appointments")

    appts = appointments_for_patient(session, govt_id)
    upcoming = [a for a in appts if a.appointment_date >= date.today() and a.status == "Scheduled"]
    past = [a for a in appts if a not in upcoming]

    if not appts:
        st.info("No appointments yet. Head to **Book Appointment** to schedule your first visit.")
    else:
        if upcoming:
            st.markdown("**Upcoming**")
            for a in upcoming:
                doc = a.doctor
                left, right = st.columns([3, 1])
                with left:
                    st.markdown(
                        f"**{doc.name}** · {doc.department} · Room {doc.room_no}  \n"
                        f"{a.appointment_date} at {a.appointment_time} — Token #{a.token_no:03d}"
                    )
                    if a.payment:
                        fee_line = f"Consultation fee: ₹{a.payment.amount} — "
                        fee_line += "✅ Paid" if a.payment.status == "Paid" else (
                            "⏳ Pay at the counter" if a.payment.status == "Pending" else "Waived"
                        )
                        st.caption(fee_line)
                with right:
                    st.markdown(status_badge(a.status), unsafe_allow_html=True)
                    if a.predicted_urgency:
                        st.markdown(urgency_badge(a.predicted_urgency), unsafe_allow_html=True)

        if past:
            with st.expander(f"History ({len(past)})"):
                for a in past:
                    doc = a.doctor
                    st.markdown(
                        f"{a.appointment_date} · {doc.name} ({doc.department}) — "
                        f"{status_badge(a.status)}",
                        unsafe_allow_html=True,
                    )