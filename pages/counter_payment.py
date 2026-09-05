from datetime import date, timedelta

import streamlit as st

from config import PAYMENT_METHODS
from database.db import session_scope
from services.payment_service import (
    appointments_with_payment_for_date, mark_paid, waive_payment,
    revenue_summary_for_date, PaymentError,
)
from utils.ui import inject_css, page_header, status_badge

inject_css()
page_header("Counter Billing", eyebrow="Front Desk")
st.caption(
    "Payments are collected in person at the hospital counter -- this records "
    "what was paid, it doesn't process cards or take online payment."
)

col1, col2 = st.columns([1, 3])
with col1:
    target_date = st.date_input("Date", value=date.today())

with session_scope() as session:
    summary = revenue_summary_for_date(session, target_date)

    m1, m2, m3 = st.columns(3)
    m1.metric("Collected", f"₹{summary['collected']}", f"{summary['paid_count']} paid")
    m2.metric("Pending", f"₹{summary['pending']}", f"{summary['pending_count']} unpaid")
    m3.metric("Waived", f"₹{summary['waived']}")

    st.divider()

    rows = appointments_with_payment_for_date(session, target_date)
    if not rows:
        st.info("No appointments for this date.")

    for appt, payment in rows:
        if payment is None:
            continue  # shouldn't happen -- every booking auto-creates a payment
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 2, 2])
            with c1:
                st.markdown(f"**Token #{appt.token_no:03d} — {appt.patient.name}**")
                st.caption(f"{appt.doctor.name} · {appt.doctor.department} · {appt.appointment_time}")
            with c2:
                st.markdown(f"**₹{payment.amount}**")
                st.caption(f"Patient ID: {appt.patient.govt_id}")
            with c3:
                st.markdown(status_badge(payment.status), unsafe_allow_html=True)
                if payment.status == "Paid":
                    st.caption(f"{payment.method} · collected by {payment.collected_by}")

            if payment.status == "Pending":
                with st.expander("Collect payment"):
                    method = st.radio(
                        "Payment method", PAYMENT_METHODS,
                        key=f"method_{payment.id}", horizontal=True,
                    )
                    pcol1, pcol2 = st.columns(2)
                    with pcol1:
                        if st.button("Mark as paid", key=f"pay_{payment.id}", type="primary"):
                            try:
                                collector = st.session_state["user"]["username"]
                                mark_paid(session, appt.id, method, collected_by=collector)
                                st.success(f"Payment of ₹{payment.amount} recorded.")
                                st.rerun()
                            except PaymentError as e:
                                st.error(str(e))
                    with pcol2:
                        if st.button("Waive fee", key=f"waive_{payment.id}"):
                            collector = st.session_state["user"]["username"]
                            waive_payment(session, appt.id, collected_by=collector)
                            st.info("Fee waived.")
                            st.rerun()