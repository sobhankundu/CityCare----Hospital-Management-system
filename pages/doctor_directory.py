import streamlit as st

from config import DEPARTMENTS
from database.db import session_scope
from database.models import Doctor
from services.doctor_service import doctors_by_department
from utils.ui import inject_css, page_header

inject_css()
page_header("Doctor Directory", eyebrow="Our Specialists")

with session_scope() as session:
    grouped = doctors_by_department(session)

if not grouped:
    st.info("No doctors registered yet.")
else:
    for dept in sorted(grouped.keys()):
        st.markdown(f"### {dept}")
        cols = st.columns(3)
        for i, doc in enumerate(grouped[dept]):
            with cols[i % 3]:
                with st.container(border=True):
                    st.markdown(f"**{doc.name}**")
                    st.caption(f"Room {doc.room_no}")

is_admin = st.session_state.get("user", {}).get("role") == "admin"
if is_admin:
    st.divider()
    with st.expander("➕ Add a doctor to the roster"):
        with st.form("add_doctor_form"):
            name = st.text_input("Doctor name (e.g. \"Dr. A. Sharma\")")
            department = st.selectbox("Department", DEPARTMENTS)
            room_no = st.text_input("Room number")
            phone = st.text_input("Phone (optional)")
            submitted = st.form_submit_button("Add doctor")
        if submitted:
            if not name.strip() or not room_no.strip():
                st.error("Doctor name and room number are required.")
            else:
                with session_scope() as session:
                    session.add(Doctor(
                        name=name.strip(), department=department,
                        room_no=room_no.strip(), phone=phone.strip() or None,
                    ))
                st.success(f"{name} added to {department}.")
                st.rerun()
