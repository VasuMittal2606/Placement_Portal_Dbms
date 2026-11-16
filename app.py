"""CampusHire - access point and login.

All authentication and reporting logic is executed inside MySQL procedures;
this file only renders the form and routes to the role dashboard.
"""

from __future__ import annotations

import streamlit as st

from database import auth_db, connection as db
from theme import inject_css

st.set_page_config(
    page_title="CampusHire | Placement Portal",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

PAGES = {
    "student": "pages/student.py",
    "recruiter": "pages/recruiter.py",
    "officer": "pages/officer.py",
    "admin": "pages/officer.py",
}

with st.sidebar:
    st.markdown("<div class='brand'>Campus<span>Hire</span></div>", unsafe_allow_html=True)
    st.caption("College Placement Portal")
    st.divider()

    info = db.server_info()
    if info:
        version = str(info.get("version", "8.0")).split("-")[0]
        st.success(f"MySQL {version} connected")
        st.caption(f"Database: {info.get('db_name')}")
    else:
        st.error("Database unreachable")
        st.caption("Run `python init_db.py` to create and seed the schema.")

    st.divider()
    st.caption("Demo accounts (password: password123)")
    st.code(
        "student1@campus.edu\nhr@apexquantum.com\nmeera.iyer@campushire.edu",
        language=None,
    )

user = st.session_state.get("user")

if user:
    st.markdown(
        f"""
        <div class="hero">
            <h1>Welcome back, {user['full_name']}</h1>
            <p>Signed in as <b>{user['role']}</b>. Open your dashboard to continue.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    if st.button("Open dashboard", type="primary", use_container_width=True):
        st.switch_page(PAGES.get(user["role"], "pages/officer.py"))
    st.stop()

st.markdown(
    """
    <div class="hero">
        <h1>CampusHire</h1>
        <p>A database driven campus recruitment portal - students, recruiters and the
        placement cell working on one MySQL schema.</p>
    </div>
    """,
    unsafe_allow_html=True,
)
st.write("")

left, right = st.columns([1.05, 1])

with left:
    st.markdown("#### Sign in")
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="student1@campus.edu")
        password = st.text_input("Password", type="password", placeholder="password123")
        submitted = st.form_submit_button("Sign in", use_container_width=True)

    if submitted:
        if not email.strip() or not password:
            st.warning("Enter both email and password.")
        else:
            try:
                result = auth_db.verify_login(email.strip(), password)
            except Exception as exc:  # noqa: BLE001 - surface DB errors in UI
                st.error(f"Database error: {exc}")
            else:
                if result:
                    st.session_state["user"] = {
                        "user_id": result["user_id"],
                        "role": result["role"],
                        "full_name": result["full_name"],
                        "email": email.strip(),
                    }
                    st.switch_page(PAGES.get(result["role"], "pages/officer.py"))
                else:
                    st.error("Invalid email or password")

with right:
    st.markdown("#### Workflow handled by SQL")
    st.markdown(
        """
        1. Login - `sp_verify_login` (SHA-256 check in SQL)
        2. Apply - `sp_apply_for_job` + `fn_check_eligibility`
        3. Shortlist - `sp_shortlist_applicant`
        4. Interview - `sp_schedule_interview`
        5. Offer - `sp_make_offer`
        6. Accept - trigger creates the placement row
        """
    )
    st.info("Eligibility, workflow transitions and placement creation are enforced by "
            "stored procedures and triggers - not by Python.")
