from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st

from config import PAYMENT_METHODS
from database.db import session_scope
from services.payment_service import (
    appointments_with_payment_for_date, mark_paid, waive_payment,
    revenue_summary_for_date, revenue_summary_for_year, available_years,
    PaymentError,
)
from utils.ui import inject_css, page_header, status_badge
from utils.upi import generate_upi_qr

inject_css()
page_header("Counter Billing", eyebrow="Front Desk / Staff")
st.caption(
    "Collect payment at the counter. UPI shows a real, scannable QR code -- "
    "there's no payment gateway hooked up, so confirm receipt by checking "
    "your own UPI app before marking it paid. Cash and card are settled on "
    "your usual cash drawer / card machine; this just records what was collected."
)

PLOTLY_TEMPLATE = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="IBM Plex Sans, sans-serif", color="#16241F"),
)

# --- Yearly overview: total billing for the year + a month-by-month trend ---
st.subheader("📈 Yearly Overview")
with session_scope() as session:
    years = available_years(session)
    selected_year = st.selectbox("Year", years, index=0)
    yearly = revenue_summary_for_year(session, selected_year)

    y1, y2, y3 = st.columns(3)
    y1.metric(f"Total Collected in {selected_year}", f"₹{yearly['collected']}")
    y2.metric("Pending", f"₹{yearly['pending']}")
    y3.metric("Waived", f"₹{yearly['waived']}")

    monthly_df = pd.DataFrame(yearly["monthly"])
    fig = px.bar(
        monthly_df, x="month", y="amount",
        labels={"month": "", "amount": "Collected (₹)"},
        color_discrete_sequence=["#0F6B62"],
    )
    fig.update_layout(**PLOTLY_TEMPLATE, height=320, margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Date-wise drill-down: the day-to-day billing/collection screen ---
st.subheader("📋 Day-by-Day Billing")
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
                with st.expander("💳 Collect payment", expanded=False):
                    method = st.radio(
                        "Payment method", PAYMENT_METHODS,
                        key=f"method_{payment.id}", horizontal=True,
                    )

                    if method == "UPI":
                        qr_img = generate_upi_qr(
                            amount=payment.amount,
                            note=f"CityCare Token {appt.token_no}",
                            txn_ref=f"APPT{appt.id}",
                        )
                        qcol, tcol = st.columns([1, 2])
                        with qcol:
                            st.image(qr_img, width=180)
                        with tcol:
                            st.markdown(f"**Ask the patient to scan and pay ₹{payment.amount}**")
                            st.caption(
                                "Check your own UPI app for the payment before confirming below -- "
                                "this app can't detect it automatically."
                            )
                    elif method == "Cash":
                        st.markdown(f"**Collect ₹{payment.amount} in cash.**")
                    else:  # Card
                        st.markdown(f"**Charge ₹{payment.amount} on your card machine.**")

                    pcol1, pcol2 = st.columns(2)
                    with pcol1:
                        confirm_label = "✅ Confirm payment received" if method != "Cash" else "✅ Confirm cash received"
                        if st.button(confirm_label, key=f"pay_{payment.id}", type="primary"):
                            try:
                                collector = st.session_state["user"]["username"]
                                mark_paid(session, appt.id, method, collected_by=collector)
                                st.success(f"₹{payment.amount} recorded via {method}.")
                                st.rerun()
                            except PaymentError as e:
                                st.error(str(e))
                    with pcol2:
                        if st.button("Waive fee", key=f"waive_{payment.id}"):
                            collector = st.session_state["user"]["username"]
                            waive_payment(session, appt.id, collected_by=collector)
                            st.info("Fee waived.")
                            st.rerun()