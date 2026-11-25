"""Shared Streamlit styling helpers (SaaSUI-style dark dashboard)."""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

CSS = """
<style>
.stApp {
    background-color: #0A0E17;
    color: #CBD5E1;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}
.main .block-container { background-color: #0A0E17; }
section[data-testid="stSidebar"] {
    background-color: #0B1020;
    border-right: 1px solid #1E293B;
}
section[data-testid="stSidebar"] .stRadio > label {
    background: none;
    border-radius: 8px;
    color: #94A3B8;
    padding: 10px 14px;
    font-size: 14px;
    font-weight: 500;
}
section[data-testid="stSidebar"] .stRadio > label:hover {
    background-color: #1E293B;
    color: #F8FAFC;
}
.brand {
    font-size: 20px;
    font-weight: 800;
    letter-spacing: -0.02em;
    color: #F8FAFC;
    padding: 6px 0 2px 0;
}
.brand span { color: #14B8A6; }
.metric-card {
    background: linear-gradient(135deg, #0F172A, #1E293B);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 18px;
    position: relative;
    overflow: hidden;
    margin-bottom: 8px;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; right: 0;
    width: 44px; height: 4px;
    background: linear-gradient(90deg, #0D9488, #14B8A6);
}
.metric-title {
    color: #94A3B8;
    font-size: 11px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin: 0 0 8px 0;
}
.metric-value {
    color: #F8FAFC;
    font-size: 28px;
    font-weight: 700;
    margin: 0;
    line-height: 1.1;
}
.metric-hint { color: #14B8A6; font-size: 11px; font-weight: 600; }
.pill {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 600;
    line-height: 1.6;
}
h1, h2, h3 { color: #F8FAFC; font-weight: 600; }
.stButton > button {
    background-color: #0D9488;
    color: #0A0E17;
    border-radius: 8px;
    border: none;
    font-weight: 600;
}
.stButton > button:hover { background-color: #14B8A6; color: #0A0E17; }
.stDownloadButton > button {
    background-color: #1E293B;
    color: #E2E8F0;
    border: 1px solid #334155;
    border-radius: 8px;
}
[data-testid="stDataFrame"] { border: 1px solid #1E293B; border-radius: 10px; }
.hero {
    background: linear-gradient(135deg, #0F172A 0%, #111C33 55%, #0B3B36 100%);
    border: 1px solid #1E293B;
    border-radius: 16px;
    padding: 32px;
}
.hero h1 { margin: 0 0 6px 0; }
.hero p { color: #94A3B8; margin: 0; }
</style>
"""

STATUS_COLORS = {
    "applied": ("#1E3A8A", "#BFDBFE"),
    "shortlisted": ("#134E4A", "#99F6E4"),
    "interview": ("#78350F", "#FDE68A"),
    "offered": ("#4C1D95", "#DDD6FE"),
    "placed": ("#14532D", "#BBF7D0"),
    "rejected": ("#7F1D1D", "#FECACA"),
    "withdrawn": ("#334155", "#CBD5E1"),
    "pending": ("#78350F", "#FDE68A"),
    "accepted": ("#14532D", "#BBF7D0"),
    "declined": ("#7F1D1D", "#FECACA"),
    "selected": ("#14532D", "#BBF7D0"),
    "on_hold": ("#334155", "#CBD5E1"),
    "active": ("#14532D", "#BBF7D0"),
    "closed": ("#334155", "#CBD5E1"),
    "draft": ("#1E3A8A", "#BFDBFE"),
}


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def pillar(text: str) -> str:
    """Return an HTML status pill for a workflow state."""
    background, foreground = STATUS_COLORS.get(
        str(text).lower(), ("#334155", "#CBD5E1")
    )
    return (
        f"<span class='pill' style='background:{background};color:{foreground};'>"
        f"{text}</span>"
    )


def metric_card(title: str, value, hint: str = "") -> None:
    hint_html = f"<p class='metric-hint'>{hint}</p>" if hint else ""
    st.markdown(
        f"""
        <div class="metric-card">
            <p class="metric-title">{title}</p>
            <p class="metric-value">{value}</p>
            {hint_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str = "") -> None:
    st.markdown(f"## {title}")
    if subtitle:
        st.markdown(
            f"<p style='color:#94A3B8;margin-top:-8px;font-size:14px;'>{subtitle}</p>",
            unsafe_allow_html=True,
        )


def style_figure(fig: go.Figure, height: int = 320) -> go.Figure:
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#CBD5E1",
        height=height,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", y=-0.15),
    )
    fig.update_xaxes(gridcolor="#1E293B", zerolinecolor="#1E293B")
    fig.update_yaxes(gridcolor="#1E293B", zerolinecolor="#1E293B")
    return fig


def show_message(message: str) -> None:
    """Render the SUCCESS/ERROR text returned by every procedure."""
    text = str(message or "")
    if text.upper().startswith("SUCCESS"):
        st.success(text)
    else:
        st.error(text or "Unexpected database response")


ROLE_LABELS = {
    "student": "student",
    "recruiter": "recruiter",
    "officer": "placement officer",
}
ROLE_PLACEHOLDERS = {
    "student": "student1@campus.edu",
    "recruiter": "hr@apexquantum.com",
    "officer": "meera.iyer@campushire.edu",
}
ALLOWED_ROLES = {
    "student": ("student",),
    "recruiter": ("recruiter",),
    "officer": ("officer", "admin"),
}


def _clear_session_user() -> None:
    for key in ("user", "student_id", "recruiter_id"):
        st.session_state.pop(key, None)


def login_gate(role: str) -> None:
    """Show the sign-in form for `role` and stop until that role is signed in.

    The role pages belong to both entrypoints (`app.py` and
    `streamlit_dashboard.py`), but `st.switch_page` can only reach pages of the
    app that is currently running. Navigating to a hard-coded "app.py"
    therefore fails whenever the dashboard is the entrypoint, so the login
    form is rendered on the page itself instead.
    """
    from database import auth_db

    allowed = ALLOWED_ROLES[role]
    label = ROLE_LABELS[role]
    user = st.session_state.get("user")
    if user and user.get("role") in allowed:
        return

    st.markdown(f"### Sign in as a {label}")
    st.caption("Credentials are verified inside MySQL (`sp_verify_login`, SHA-256).")
    if user:
        st.info(
            f"You are signed in as {user['full_name']} ({user['role']}). "
            f"Sign in with a {label} account to open this dashboard."
        )

    with st.form(f"{role}_login_form"):
        email = st.text_input("Email", placeholder=ROLE_PLACEHOLDERS[role])
        password = st.text_input("Password", type="password", placeholder="password123")
        submitted = st.form_submit_button("Sign in", use_container_width=True)

    if submitted:
        if not email.strip() or not password:
            st.warning("Enter both email and password.")
        else:
            try:
                result = auth_db.verify_login(email.strip(), password)
            except Exception as exc:  # noqa: BLE001 - surface DB errors in the UI
                st.error(f"Database error: {exc}")
            else:
                if result and result["role"] in allowed:
                    _clear_session_user()
                    st.session_state["user"] = {
                        "user_id": result["user_id"],
                        "role": result["role"],
                        "full_name": result["full_name"],
                        "email": email.strip(),
                    }
                    st.rerun()
                elif result:
                    st.error(
                        f"{email.strip()} is a {result['role']} account. "
                        f"Sign in with a {label} account to open this dashboard."
                    )
                else:
                    st.error("Invalid email or password")
    st.stop()


def sign_out_button() -> None:
    if st.sidebar.button("Sign out", use_container_width=True):
        _clear_session_user()
        # the role page re-renders and shows its sign-in form
        st.rerun()
