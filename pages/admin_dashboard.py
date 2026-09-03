from collections import Counter
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from database.db import session_scope
from database.models import Patient, Doctor, Appointment, SymptomCheckLog
from ml.predictor import model_metadata
from utils.ui import inject_css, page_header, URGENCY_COLORS, STATUS_COLORS

inject_css()
page_header("Admin Dashboard", eyebrow="Operations Overview")

PLOTLY_TEMPLATE = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="IBM Plex Sans, sans-serif", color="#16241F"),
)

with session_scope() as session:
    n_patients = session.query(Patient).count()
    n_doctors = session.query(Doctor).filter_by(is_active=True).count()
    n_appts_today = session.query(Appointment).filter_by(appointment_date=date.today()).count()
    n_appts_total = session.query(Appointment).count()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Patients", n_patients)
    col2.metric("Active Doctors", n_doctors)
    col3.metric("Appointments Today", n_appts_today)
    col4.metric("Total Appointments", n_appts_total)

    st.divider()

    left, right = st.columns(2)

    with left:
        st.markdown("**Appointments by Department**")
        appts = session.query(Appointment).all()
        if appts:
            dept_counts = Counter(a.doctor.department for a in appts)
            df = pd.DataFrame(dept_counts.items(), columns=["Department", "Appointments"]).sort_values(
                "Appointments", ascending=True
            )
            fig = px.bar(df, x="Appointments", y="Department", orientation="h", color_discrete_sequence=["#0F6B62"])
            fig.update_layout(**PLOTLY_TEMPLATE, height=380, margin=dict(l=0, r=10, t=10, b=0))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No appointments booked yet.")

    with right:
        st.markdown("**Appointment Status Breakdown**")
        if appts:
            status_counts = Counter(a.status for a in appts)
            df2 = pd.DataFrame(status_counts.items(), columns=["Status", "Count"])
            fig2 = px.pie(
                df2, names="Status", values="Count", hole=0.55,
                color="Status", color_discrete_map=STATUS_COLORS,
            )
            fig2.update_layout(**PLOTLY_TEMPLATE, height=380, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No appointments booked yet.")

    st.divider()
    st.subheader("🤖 Symptom Checker — Model Usage")

    logs = session.query(SymptomCheckLog).all()
    meta = model_metadata()
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Checks Logged", len(logs))
    m2.metric("Department Model Accuracy", f"{meta['dept_accuracy']*100:.1f}%" if meta["dept_accuracy"] else "—")
    m3.metric("Urgency Model Accuracy", f"{meta['urgency_accuracy']*100:.1f}%" if meta["urgency_accuracy"] else "—")

    if logs:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Predicted Department (usage)**")
            dept_pred_counts = Counter(l.predicted_department for l in logs)
            df3 = pd.DataFrame(dept_pred_counts.items(), columns=["Department", "Checks"])
            fig3 = px.bar(df3, x="Department", y="Checks", color_discrete_sequence=["#0F6B62"])
            fig3.update_layout(**PLOTLY_TEMPLATE, height=320, margin=dict(l=0, r=0, t=10, b=0))
            fig3.update_xaxes(tickangle=-30)
            st.plotly_chart(fig3, use_container_width=True)
        with c2:
            st.markdown("**Predicted Urgency (usage)**")
            urg_counts = Counter(l.predicted_urgency for l in logs)
            df4 = pd.DataFrame(urg_counts.items(), columns=["Urgency", "Checks"])
            fig4 = px.pie(
                df4, names="Urgency", values="Checks", hole=0.55,
                color="Urgency", color_discrete_map=URGENCY_COLORS,
            )
            fig4.update_layout(**PLOTLY_TEMPLATE, height=320, margin=dict(l=0, r=0, t=10, b=0))
            st.plotly_chart(fig4, use_container_width=True)
    else:
        st.caption("No symptom checks logged yet -- try the Symptom Checker or Triage Chatbot pages.")
