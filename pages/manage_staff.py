import streamlit as st

from database.db import session_scope
from services.auth_service import create_user, all_staff, deactivate_user
from utils.ui import inject_css, page_header

# --- Page setup: title, styling, and a short explanation for whoever's using it ---
inject_css()
page_header("Manage Staff", eyebrow="Front Desk / Billing Employees")
st.caption(
    "Staff accounts can only access Counter Billing -- they can't view medical "
    "records, manage doctors, or see anything outside payment collection."
)

# --- Section 1: a collapsible form for creating a new staff login ---
# st.expander just makes a collapsible box (click to open/close) so the form
# doesn't take up space until an admin actually wants to add someone.
with st.expander("➕ Create a new staff account"):

    # st.form groups these three widgets together so nothing happens until
    # the "Create staff account" button is clicked -- without a form, every
    # single keystroke in the username/password boxes would re-run the page.
    with st.form("create_staff_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Create staff account", type="primary")

    # This block only runs AFTER the button above is clicked.
    if submitted:
        # Basic checks before we even touch the database.
        if not username or not password:
            st.error("Username and password are required.")
        elif len(password) < 6:
            st.error("Password must be at least 6 characters.")
        else:
            # session_scope() opens a database connection, and automatically
            # closes it when the "with" block ends (whether it succeeds or fails).
            try:
                with session_scope() as session:
                    # role="staff" is what makes app.py send this account to
                    # the Counter Billing-only page list instead of the full
                    # admin menu or the patient menu.
                    create_user(session, username, password, role="staff")
                st.success(f"Staff account '{username}' created.")
                st.rerun()  # refreshes the page so the new account shows up in the list below
            except ValueError as e:
                # create_user raises ValueError for things like "username already taken"
                st.error(str(e))

st.divider()  # just draws a horizontal line for visual separation
st.subheader("Current staff accounts")

# --- Section 2: list every existing staff account, with a Remove button ---
with session_scope() as session:
    staff = all_staff(session)  # fetches every User row where role == "staff"

    if not staff:
        st.info("No staff accounts yet. Create one above.")

    # Loop through each staff account and draw one row per account.
    for s in staff:
        # st.columns([2, 2, 1]) splits the row into 3 side-by-side sections,
        # with relative widths 2:2:1 (so the first two are wider than the third).
        col1, col2, col3 = st.columns([2, 2, 1])
        col1.markdown(f"**{s.username}**")
        col2.caption(f"Created {s.created_at.strftime('%d %b %Y')}")  # e.g. "Created 05 Sep 2026"

        with col3:
            # key=f"remove_{s.id}" gives each button a unique internal ID --
            # required because we're creating multiple buttons with the same
            # label ("Remove") in a loop, and Streamlit needs a way to tell
            # them apart.
            if st.button("Remove", key=f"remove_{s.id}"):
                try:
                    # Pass in who's currently logged in, so deactivate_user
                    # can refuse the request if an admin tries to remove
                    # their own account by mistake.
                    deactivate_user(session, s.id, st.session_state["user"]["username"])
                    st.success(f"Removed {s.username}.")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))