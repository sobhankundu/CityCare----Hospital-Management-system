import streamlit as st

from utils.ui import inject_css, page_header

inject_css()
page_header("Facilities & Services", eyebrow="What We Offer")

SERVICES = [
    ("Ultrasound", "Room 1", "Diagnostic imaging"),
    ("X-Ray", "Room 2", "Diagnostic imaging"),
    ("CT Scan", "Room 3", "Diagnostic imaging"),
    ("MRI", "Room 4", "Diagnostic imaging"),
    ("Blood Collection", "Room 5", "Laboratory"),
    ("Dialysis", "Room 6", "Renal care"),
    ("ECG", "Room 7", "Cardiac diagnostics"),
    ("Pharmacy", "Room 8", "Chemist"),
    ("Laboratory", "Room 9", "Pathology & testing"),
]

cols = st.columns(3)
for i, (name, room, category) in enumerate(SERVICES):
    with cols[i % 3]:
        with st.container(border=True):
            st.markdown(f"**{name}**")
            st.caption(f"{room} · {category}")

st.divider()
st.markdown("To book any of these services, contact the front desk at **+91 98XXXXXX55**.")
