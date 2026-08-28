import streamlit as st

from config import APPOINTMENT_STATUSES
from database.db import session_scope
from database.models import MedicalRecord
from services.appointment_service import all_appointments, update_status
from utils.ui import inject_css, page_header, status_badge, urgency_badge

inject_css()
page_header("Manage Appointments", eyebrow="Front Desk")

status_filter = st.selectbox("Filter by status", ["All"] + APPOINTMENT_STATUSES)

with session_scope() as session:
    appts = all_appointments(session, status=None if status_filter == "All" else status_filter)

    if not appts:
        st.info("No appointments match this filter.")
    for a in appts:
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 2, 2])
            with c1:
                st.markdown(f"**{a.patient.name}** ({a.patient.govt_id})")
                st.caption(f"{a.doctor.name} · {a.doctor.department} · Room {a.doctor.room_no}")
            with c2:
                st.markdown(f"{a.appointment_date} at {a.appointment_time}")
                st.caption(f"Token #{a.token_no:03d}")
            with c3:
                st.markdown(status_badge(a.status), unsafe_allow_html=True)
                if a.predicted_urgency:
                    st.markdown(urgency_badge(a.predicted_urgency), unsafe_allow_html=True)

            if a.reason:
                st.caption(f"Reason: {a.reason}")

            with st.expander("Update"):
                new_status = st.selectbox(
                    "Status", APPOINTMENT_STATUSES,
                    index=APPOINTMENT_STATUSES.index(a.status),
                    key=f"status_{a.id}",
                )
                diagnosis = st.text_input("Diagnosis (optional)", key=f"diag_{a.id}")
                prescription = st.text_input("Prescription (optional)", key=f"presc_{a.id}")
                notes = st.text_area("Notes (optional)", key=f"notes_{a.id}")
                if st.button("Save", key=f"save_{a.id}"):
                    update_status(session, a.id, new_status)
                    if diagnosis or prescription or notes:
                        session.add(MedicalRecord(
                            patient_id=a.patient_id, appointment_id=a.id,
                            symptoms=a.reason, diagnosis=diagnosis or None,
                            prescription=prescription or None, notes=notes or None,
                        ))
                    st.success("Updated.")
                    st.rerun()
