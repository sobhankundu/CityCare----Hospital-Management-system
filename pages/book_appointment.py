from datetime import date, timedelta

import streamlit as st

from config import TIME_SLOTS
from database.db import session_scope
from services.doctor_service import doctors_by_department
from services.appointment_service import book_appointment, BookingError
from ml.predictor import predict
from ml.symptom_data import ALL_SYMPTOMS
from utils.ui import inject_css, page_header, urgency_badge, token_display

inject_css()
page_header("Book Appointment", eyebrow="Patient Portal")

govt_id = st.session_state.get("patient_govt_id")
if not govt_id:
    st.warning("No patient profile is linked to this account. Please contact the front desk.")
    st.stop()

if "recommended_department" not in st.session_state:
    st.session_state.recommended_department = None

with st.expander("🩺 Not sure which department? Get a quick recommendation", expanded=False):
    chosen_symptoms = st.multiselect("Select what you're experiencing", ALL_SYMPTOMS)
    if st.button("Recommend a department"):
        if chosen_symptoms:
            result = predict(chosen_symptoms)
            if result["error"]:
                st.warning(result["error"])
            else:
                st.session_state.recommended_department = result["department"]
                st.markdown(
                    f"**Suggested department: {result['department']}** "
                    f"({result['department_confidence']*100:.0f}% confidence) — "
                    f"Urgency: {urgency_badge(result['urgency'])}",
                    unsafe_allow_html=True,
                )
                if result["is_emergency_override"]:
                    st.error(
                        "This combination includes a red-flag symptom. Please seek "
                        "Emergency care directly instead of booking a routine appointment."
                    )
        else:
            st.info("Select at least one symptom.")

with session_scope() as session:
    grouped = doctors_by_department(session)

if not grouped:
    st.error("No doctors are currently registered in the system.")
    st.stop()

departments = sorted(grouped.keys())
default_idx = (
    departments.index(st.session_state.recommended_department)
    if st.session_state.recommended_department in departments
    else 0
)

# IMPORTANT: this selectbox must stay OUTSIDE st.form(). Widgets inside a
# form don't trigger a rerun until the form is submitted, so a department
# selector inside the form would never actually refresh the doctor list
# below it when changed -- it would stay stuck on whichever doctors matched
# the department that was selected when the page first loaded.
department = st.selectbox("Department", departments, index=default_idx)
doctor_options = {f"{d.name} (Room {d.room_no})": d.id for d in grouped[department]}

with st.form("book_form"):
    col1, col2 = st.columns(2)
    with col1:
        doctor_label = st.selectbox("Doctor", list(doctor_options.keys()))
        appt_date = st.date_input(
            "Date", value=date.today() + timedelta(days=1), min_value=date.today()
        )
    with col2:
        appt_time = st.selectbox("Time slot", TIME_SLOTS)
        reason = st.text_area("Reason for visit (optional)", max_chars=255)
    submitted = st.form_submit_button("Confirm booking", use_container_width=True)

if submitted:
    try:
        with session_scope() as session:
            appt = book_appointment(
                session, govt_id, doctor_options[doctor_label], appt_date, appt_time,
                reason=reason, predicted_department=st.session_state.recommended_department,
            )
            st.success(f"Appointment confirmed with {doctor_label} on {appt_date} at {appt_time}.")
            token_display(appt.token_no, label="YOUR TOKEN NUMBER")
        st.session_state.recommended_department = None
    except BookingError as e:
        st.error(str(e))
