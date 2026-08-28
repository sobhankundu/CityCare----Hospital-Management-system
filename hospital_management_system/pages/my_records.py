import streamlit as st

from database.db import session_scope
from services.patient_service import find_patient_by_govt_id
from utils.ui import inject_css, page_header

inject_css()
page_header("My Records", eyebrow="Patient Portal")

govt_id = st.session_state.get("patient_govt_id")
if not govt_id:
    st.warning("No patient profile is linked to this account. Please contact the front desk.")
    st.stop()

with session_scope() as session:
    patient = find_patient_by_govt_id(session, govt_id)
    if patient is None:
        st.error("Patient profile not found.")
        st.stop()

    records = sorted(patient.medical_records, key=lambda r: r.created_at, reverse=True)

    if not records:
        st.info(
            "No medical records yet. After a completed appointment, your doctor's notes, "
            "diagnosis, and prescription will appear here."
        )
    else:
        for r in records:
            with st.container(border=True):
                st.caption(r.created_at.strftime("%d %b %Y"))
                if r.symptoms:
                    st.markdown(f"**Symptoms:** {r.symptoms}")
                if r.diagnosis:
                    st.markdown(f"**Diagnosis:** {r.diagnosis}")
                if r.prescription:
                    st.markdown(f"**Prescription:** {r.prescription}")
                if r.notes:
                    st.markdown(f"**Notes:** {r.notes}")
