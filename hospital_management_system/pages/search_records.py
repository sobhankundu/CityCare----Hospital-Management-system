import streamlit as st

from config import BLOOD_GROUPS
from database.db import session_scope
from services.patient_service import search_patients, update_patient_field, ValidationError, FIELD_MAP
from services.appointment_service import appointments_for_patient
from utils.ui import inject_css, page_header, status_badge

inject_css()
page_header("Search Patient Records", eyebrow="Front Desk")

query = st.text_input("Search by Government ID or name")

if query:
    with session_scope() as session:
        results = search_patients(session, query)

        if not results:
            st.warning("No matching patient found.")
        for patient in results:
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Name", patient.name)
                col2.metric("Age", patient.age)
                col3.metric("Gender", patient.gender)
                col4.metric("Blood Group", patient.blood_group)
                st.caption(f"ID: {patient.govt_id} · Phone: {patient.phone}")

                appts = appointments_for_patient(session, patient.govt_id)
                if appts:
                    st.markdown("**Appointment history**")
                    for a in appts:
                        st.markdown(
                            f"- {a.appointment_date} · {a.doctor.name} ({a.doctor.department}) — "
                            f"{status_badge(a.status)}",
                            unsafe_allow_html=True,
                        )

                with st.expander("Edit patient details"):
                    field = st.selectbox(
                        "Field to change", list(FIELD_MAP.keys()), key=f"field_{patient.id}"
                    )
                    if field == "Blood Group":
                        new_value = st.selectbox("New value", BLOOD_GROUPS, key=f"val_{patient.id}")
                    elif field == "Gender":
                        new_value = st.selectbox("New value", ["M", "F", "O"], key=f"val_{patient.id}")
                    else:
                        new_value = st.text_input("New value", key=f"val_{patient.id}")
                    if st.button("Save change", key=f"save_{patient.id}"):
                        try:
                            update_patient_field(session, patient.govt_id, field, new_value)
                            st.success("Updated.")
                            st.rerun()
                        except ValidationError as e:
                            for err in e.errors:
                                st.error(err)
else:
    st.caption("Enter a 12-digit Government ID or a patient name to search.")
