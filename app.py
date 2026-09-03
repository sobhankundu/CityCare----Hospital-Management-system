"""
Entrypoint / router for the CityCare Hospital Management System.

Run with:  streamlit run app.py

This file owns: DB initialisation, the login/sign-up screen, and building the
role-filtered navigation menu. Each actual screen lives in pages/ and is
plugged in here via st.Page so visibility can depend on who's logged in --
plain folder-based multipage routing can't do that.
"""
import streamlit as st

from config import APP_NAME, APP_ICON
from database.db import init_db, session_scope
from services.auth_service import authenticate, create_user, username_exists
from services.patient_service import register_patient, ValidationError
from utils.ui import inject_css, page_header

st.set_page_config(page_title=APP_NAME, page_icon=APP_ICON, layout="wide")


@st.cache_resource
def _bootstrap_db():
    init_db()
    return True


_bootstrap_db()
inject_css()

if "user" not in st.session_state:
    st.session_state.user = None
if "patient_govt_id" not in st.session_state:
    st.session_state.patient_govt_id = None


def _login_form():
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Log in", use_container_width=True)
    if submitted:
        with session_scope() as session:
            user = authenticate(session, username, password)
            if user is None:
                st.error("Invalid username or password.")
            else:
                st.session_state.user = {"id": user.id, "username": user.username, "role": user.role}
                if user.role == "patient" and user.patient_profile:
                    st.session_state.patient_govt_id = user.patient_profile.govt_id
                st.rerun()


def _signup_form():
    st.caption("Creates both your login account and your patient record in one step.")
    with st.form("signup_form"):
        col1, col2 = st.columns(2)
        with col1:
            govt_id = st.text_input("Government ID (12 digits)", max_chars=12)
            name = st.text_input("Full name")
            age = st.text_input("Age")
            gender = st.selectbox("Gender", ["M", "F", "O"])
        with col2:
            phone = st.text_input("Phone (10 digits)")
            from config import BLOOD_GROUPS
            blood_group = st.selectbox("Blood group", BLOOD_GROUPS)
            username = st.text_input("Choose a username")
            password = st.text_input("Choose a password", type="password")
        submitted = st.form_submit_button("Create account", use_container_width=True)

    if submitted:
        if not username or not password:
            st.error("Username and password are required.")
            return
        if len(password) < 6:
            st.error("Password must be at least 6 characters.")
            return
        try:
            with session_scope() as session:
                if username_exists(session, username):
                    st.error(f"Username '{username}' is already taken.")
                    return
                patient = register_patient(session, govt_id, name, age, gender, phone, blood_group)
                user = create_user(session, username, password, role="patient")
                patient.user_id = user.id
                session.add(patient)
            st.success("Account created! Please log in from the Login tab.")
        except ValidationError as e:
            for err in e.errors:
                st.error(err)
        except Exception as e:
            st.error(f"Could not create account: {e}")


def _landing_page():
    inject_css()
    left, right = st.columns([1.1, 1])
    with left:
        page_header(APP_NAME, eyebrow="Patient & Staff Portal")
        st.markdown(
            "A full-stack hospital management system: patient registration, "
            "appointment booking with live token queues, a staff dashboard, "
            "and an ML-powered symptom checker + triage chatbot that "
            "recommends the right department and urgency level."
        )
    with right:
        tab1, tab2 = st.tabs(["Log in", "Patient sign-up"])
        with tab1:
            _login_form()
        with tab2:
            _signup_form()


if st.session_state.user is None:
    _landing_page()
    st.stop()

# ---- Authenticated area: build role-filtered navigation ----
role = st.session_state.user["role"]

patient_pages = [
    st.Page("pages/patient_dashboard.py", title="My Dashboard", icon="🏠"),
    st.Page("pages/book_appointment.py", title="Book Appointment", icon="📅"),
    st.Page("pages/symptom_checker.py", title="Symptom Checker", icon="🩺"),
    st.Page("pages/triage_chatbot.py", title="Triage Chatbot", icon="💬"),
    st.Page("pages/my_records.py", title="My Records", icon="📋"),
    st.Page("pages/doctor_directory.py", title="Doctor Directory", icon="👨‍⚕️"),
    st.Page("pages/facilities.py", title="Facilities", icon="🏥"),
]

admin_pages = [
    st.Page("pages/admin_dashboard.py", title="Dashboard", icon="📊"),
    st.Page("pages/register_patient.py", title="Register Patient", icon="📝"),
    st.Page("pages/manage_appointments.py", title="Manage Appointments", icon="📅"),
    st.Page("pages/search_records.py", title="Search Records", icon="🔍"),
    st.Page("pages/doctor_directory.py", title="Doctor Directory", icon="👨‍⚕️"),
    st.Page("pages/symptom_checker.py", title="Symptom Checker", icon="🩺"),
    st.Page("pages/triage_chatbot.py", title="Triage Chatbot", icon="💬"),
    st.Page("pages/facilities.py", title="Facilities", icon="🏥"),
]

pages = admin_pages if role == "admin" else patient_pages

with st.sidebar:
    st.markdown(f"**{APP_ICON} {APP_NAME}**")
    st.caption(f"Logged in as `{st.session_state.user['username']}` ({role})")
    if st.button("Log out", use_container_width=True):
        st.session_state.user = None
        st.session_state.patient_govt_id = None
        st.rerun()
    st.divider()

nav = st.navigation(pages)
nav.run()