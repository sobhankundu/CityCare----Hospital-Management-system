import streamlit as st

from config import BLOOD_GROUPS
from database.db import session_scope
from services.patient_service import register_patient, ValidationError
from utils.ui import inject_css, page_header

inject_css()
page_header("Register Patient", eyebrow="Front Desk")
st.caption("Walk-in / phone registration. This creates a patient record only -- "
           "the patient can separately sign up for portal access from the login screen if they want one.")

with st.form("register_patient_form"):
    col1, col2 = st.columns(2)
    with col1:
        govt_id = st.text_input("Government ID (12 digits)", max_chars=12)
        name = st.text_input("Full name")
        age = st.text_input("Age")
    with col2:
        gender = st.selectbox("Gender", ["M", "F", "O"])
        phone = st.text_input("Phone (10 digits)")
        blood_group = st.selectbox("Blood group", BLOOD_GROUPS)
    address = st.text_input("Address (optional)")
    submitted = st.form_submit_button("Register patient", type="primary", use_container_width=True)

if submitted:
    try:
        with session_scope() as session:
            patient = register_patient(session, govt_id, name, age, gender, phone, blood_group, address)
        st.success(f"Registered {patient.name} with ID {patient.govt_id}.")
    except ValidationError as e:
        for err in e.errors:
            st.error(err)
