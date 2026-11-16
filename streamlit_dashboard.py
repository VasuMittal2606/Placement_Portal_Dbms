#!/usr/bin/env python3
# CampusHire – Streamlit Dashboard with SaaSUI Design Reference
# Design inspired by Groq Cloud / Churnkey dashboard patterns from saasui.design
# Features KPI metric cards, chart cards, sidebar navigation, dark navy theme

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
from matplotlib.colors import LinearSegmentedColormap

# pandas resolves a *string* cmap against matplotlib's registered colormap
# names, so a hex colour can never be passed there directly. Build a real
# colormap from the CampusHire teal palette instead (kept dark enough for the
# light table text of the dashboard theme).
TEAL_CMAP = LinearSegmentedColormap.from_list(
    "campushire_teal", ["#0B3B36", "#0F766E"]
)

# ─────────────────────────────────────────────────────────────────────
# PAGE CONFIGURATION
# ─────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CampusHire | Placement Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────
# CUSTOM CSS STYLING (SaaSUI-inspired Dark Navy theme)
# Based on Groq Cloud / Churnkey patterns from saasui.design
# ─────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ========== GLOBAL CANVAS ========== */
    .stApp {
        background-color: #0A0E17;
        color: #CBD5E1;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Ensure main content area has the dark background */
    .main .block-container {
        background-color: #0A0E17;
    }

    /* ========== SIDEBAR ========== */
    section[data-testid="stSidebar"] {
        background-color: #0B1020;
        border-right: 1px solid #1E293B;
        color: #CBD5E1;
    }

    /* Sidebar logo/title area */
    .sidebar .logo {
        font-size: 18px;
        font-weight: 700;
        color: #F8FAFC;
        margin-bottom: 24px;
        padding: 12px 16px;
        background: linear-gradient(135deg, #0F172A, #1E293B);
        border-radius: 8px;
        text-align: center;
        border: 1px solid #1E293B;
    }

    /* Sidebar navigation items */
    section[data-testid="stSidebar"] .stRadio > label {
        background: none;
        border-radius: 8px;
        color: #94A3B8;
        padding: 12px 16px;
        margin: 4px 0;
        font-size: 14px;
        font-weight: 500;
        transition: all 0.2s ease;
    }

    section[data-testid="stSidebar"] .stRadio > label:hover {
        background-color: #1E293B;
        color: #F8FAFC;
    }

    section[data-testid="stSidebar"] .stRadio > label[data-selected="true"] {
        background-color: #0D9488;
        color: #0A0E17;
    }

    /* ========== CARDS ========== */
    .saas-card {
        background-color: #0F172A;
        border: 1px solid #1E293B;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        margin-bottom: 16px;
        transition: border-color 0.2s ease;
    }

    .saas-card:hover {
        border-color: #0D9488;
    }

    /* Metric card specific */
    .metric-card {
        background: linear-gradient(135deg, #0F172A, #1E293B);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        position: relative;
        overflow: hidden;
    }

    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 40px;
        height: 4px;
        background: linear-gradient(90deg, #0D9488, #14B8A6);
        border-radius: 12px 0 0 0;
    }

    /* ========== TYPOGRAPHY ========== */
    h1, h2, h3 {
        color: #F8FAFC;
        font-weight: 600;
    }

    h1 { font-size: 28px; margin-bottom: 8px; }
    h2 { font-size: 20px; margin-bottom: 4px; }
    h3 { font-size: 16px; }

    .text-muted { color: #94A3B8; font-size: 12px; }
    .text-subtle { color: #64748B; font-size: 13px; }

    /* Metric title and value */
    .metric-title {
        color: #94A3B8;
        font-size: 11px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin: 0 0 8px 0;
        display: block;
    }

    .metric-value {
        color: #F8FAFC;
        font-size: 32px;
        font-weight: 700;
        margin: 0 0 4px 0;
    }

    .metric-delta {
        color: #14B8A6;
        font-size: 11px;
        font-weight: 600;
    }

    /* ========== BUTTONS ========== */
    .stButton > button {
        background-color: #0D9488;
        color: #0A0E17;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 500;
        font-size: 14px;
        transition: all 0.2s ease;
        margin-top: 4px;
    }

    .stButton > button:hover {
        background-color: #14B8A6;
        color: #0A0E17;
        box-shadow: 0 4px 12px rgba(14, 184, 166, 0.3);
    }

    .stButton > button:focus-visible {
        outline: 2px solid #0D9488;
        outline-offset: 2px;
    }

    /* ========== PLOTLY CHART CONTAINERS ========== */
    .chart-card {
        background: #0F172A;
        border: 1px solid #1E293B;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
    }

    /* ========== DATA TABLE ========== */
    .dataframe thead th {
        background-color: #1E293B;
        border-bottom: 1px solid #334155;
        color: #94A3B8;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .dataframe tbody th, .dataframe tbody td {
        color: #CBD5E1;
        border-bottom: 1px solid #1E293B;
        font-size: 13px;
    }

    .dataframe tbody tr:hover {
        background-color: #1E293B;
    }

    /* ========== INPUTS ========== */
    .stSelectbox > label, .stNumber_input > label, .stText_input > label {
        color: #94A3B8;
        font-size: 13px;
        font-weight: 500;
        margin-bottom: 4px;
        display: block;
    }

    .stSelectbox > div > div, .stNumber_input > div > div, .stText_input > div > div {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 8px;
        color: #F8FAFC;
    }

    /* ========== LAYOUT ========== */
    .row-widget.stColumns > div {
        gap: 0;
    }

    .stMetric > label {
        display: none;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────
# DUMMY DATA (replace with MySQL queries later)
# ─────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=600)
def get_dummy_metrics():
    """KPI metrics matching the SaaS dashboard design."""
    return {
        "total_placed": 412,
        "total_registered": 580,
        "placement_rate": "71.0%",
        "avg_package": "₹11.4 LPA",
        "max_package": "₹45.0 LPA",
        "active_companies": 48,
        "applications_this_month": 342,
    }


@st.cache_data(ttl=600)
def get_dummy_department_distribution():
    """Department distribution DataFrame."""
    return pd.DataFrame({
        "branch": ["CSE", "IT", "ECE", "Mechanical", "Civil"],
        "students": [128, 92, 67, 43, 28],
        "placed": [180, 110, 75, 35, 12],
        "rate": [42.0, 28.0, 16.0, 10.0, 4.0],
        "avg_ctc": [13.5, 11.2, 9.0, 7.5, 6.2],
    })


@st.cache_data(ttl=600)
def get_dummy_company_data():
    """Company slot data."""
    return pd.DataFrame({
        "company": ["Apex Quantum", "Vanguard Systems", "Zenith Corp",
                    "Nexus Industries", "Optima Solutions"],
        "slots": [20, 25, 15, 18, 22],
        "offers": [18, 24, 8, 15, 20],
        "avg_ctc": [24.0, 14.5, 12.0, 18.5, 16.0],
        "status": ["Completed", "Completed", "Scheduled", "Completed", "Scheduled"],
    })


@st.cache_data(ttl=600)
def get_dummy_velocity_data():
    """Monthly placement velocity."""
    return pd.DataFrame({
        "month": ["Aug", "Sep", "Oct", "Nov", "Dec", "Jan"],
        "placements": [25, 60, 140, 95, 62, 30],
    })


@st.cache_data(ttl=600)
def get_dummy_student_data():
    """Student application data."""
    return pd.DataFrame({
        "roll_no": [f"CS2026{i:04d}" for i in range(1, 11)],
        "name": ["Aarav Sharma", "Priya Patel", "Karan Singh", "Simran Kaur",
                 "Rohit Das", "Ananya Roy", "Vikram Malhotra", "Nisha Gupta",
                 "Arjun Mehta", "Divya Singh"],
        "branch": ["CSE", "IT", "ECE", "Mechanical", "Civil", "CSE", "IT", "ECE",
                   "Mechanical", "Civil"],
        "company": ["Apex Quantum", "Vanguard", "Zenith", "Apex", "Vanguard",
                    "Apex Quantum", "Vanguard", "Zenith", "Apex", "Vanguard"],
        "status": ["Placed", "Shortlisted", "Interview", "Pending", "Rejected",
                   "Placed", "Shortlisted", "Interview", "Pending", "Rejected"],
        "ctc": ["12 LPA", "14.5 LPA", "24 LPA", "7.5 LPA", "11 LPA",
                "15 LPA", "13.2 LPA", "10 LPA", "11.5 LPA", "9.8 LPA"],
    })


# ─────────────────────────────────────────────────────────────────────
# SIDEBAR NAVIGATION (SaaSUI style)
# ─────────────────────────────────────────────────────────────────────
with st.sidebar:
    # Sidebar header/branding
    st.markdown(
        '<div class="sidebar"><span>CampusHire</span></div>',
        unsafe_allow_html=True,
    )
    st.markdown("---")

    nav = st.radio(
        "Navigation",
        [
            "Overview",
            "Departments",
            "Companies",
            "Velocity",
            "Students",
        ],
        label_visibility="hidden",
        help="Navigate between dashboard sections",
    )

    st.markdown("---")
    st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')}")

    # Quick stats in sidebar
    st.markdown("#### Quick Stats")
    metrics = get_dummy_metrics()
    st.metric("Placements", f"{metrics['total_placed']}+")
    st.metric("Rate", metrics['placement_rate'])


# ─────────────────────────────────────────────────────────────────────
# MAIN CONTENT
# ─────────────────────────────────────────────────────────────────────
st.markdown("# Placement Metrics & Analytics Dashboard")
st.markdown(
    f"<p style='color: #94A3B8; margin-top: -12px; font-size: 14px;'>Real-time hiring velocity, department conversion rates, and compensation spread.</p>",
    unsafe_allow_html=True,
)
st.markdown("---")

# Initialize metrics
metrics = get_dummy_metrics()

# ─────────────────────────────────────────────────────────────────────
# DASHBOARD PAGES (SaaSUI Design)
# ─────────────────────────────────────────────────────────────────────

if nav == "Overview":
    st.markdown("### Dashboard Overview")

    # --- KPI Metrics Row (4 columns) ---
    st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
    st.markdown("#### Key Performance Indicators")
    st.markdown("</div>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <p class="metric-title">Placement Rate</p>
                <p class="metric-value">{metrics['placement_rate']}</p>
                <p class="metric-delta">↑ +5.4% vs last year</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <p class="metric-title">Students Placed</p>
                <p class="metric-value">{metrics['total_placed']}</p>
                <p class="metric-delta">↑ 412 offers accepted</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <p class="metric-title">Average CTC</p>
                <p class="metric-value">{metrics['avg_package']}</p>
                <p class="metric-delta">↑ ₹1.8 LPA growth</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <p class="metric-title">Peak Package</p>
                <p class="metric-value">{metrics['max_package']}</p>
                <p class="metric-delta">★ Apex Quantum Tech</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # --- Middle Row: Two charts ---
    st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
    st.markdown("#### Monthly Placement Velocity")
    st.markdown("</div>", unsafe_allow_html=True)

    vel_df = get_dummy_velocity_data()

    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
        st.markdown("Monthly Placement Velocity")

        fig_line = px.line(
            vel_df,
            x="month",
            y="placements",
            markers=True,
            labels={"x": "Month", "y": "Placements"},
        )
        fig_line.update_traces(
            line_color="#0D9488",
            line_width=3,
            marker=dict(size=8, color="#1E293B", line=dict(width=2, color="#0D9488")),
        )
        fig_line.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#CBD5E1",
            margin=dict(l=20, r=20, t=20, b=20),
            height=280,
            showlegend=False,
        )
        st.plotly_chart(fig_line, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_chart2:
        st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
        st.markdown("Department Placement Share")

        dept_df = get_dummy_department_distribution()

        fig_pie = px.pie(
            dept_df,
            names="branch",
            values="placed",
            hole=0.6,
            color_discrete_sequence=["#0D9488", "#14B8A6", "#0F766E", "#334155", "#1E293B"],
        )
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#CBD5E1",
            margin=dict(l=20, r=20, t=20, b=20),
            height=280,
            showlegend=True,
            legend=dict(orientation="h", y=-0.15),
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

elif nav == "Departments":
    st.markdown("### Department-Wise Analytics")

    dept_df = get_dummy_department_distribution()

    # --- Bar chart: Placements by Department ---
    fig_bar = px.bar(
        dept_df,
        x="branch",
        y="placed",
        text="rate",
        color="rate",
        color_continuous_scale=["#0F766E", "#14B8A6"],
        labels={"placed": "Students Placed", "rate": "Placement Rate %"},
    )
    fig_bar.update_traces(
        texttemplate='Rate: %{text}%', textposition='outside'
    )
    fig_bar.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#CBD5E1",
        height=420,
        coloraxis_showscale=False,
        margin=dict(l=0, r=0, t=20, b=0),
        title_text="Placement Statistics by Department",
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # --- Secondary: Avg CTC by Department ---
    st.markdown("<div class='chart-card' style='margin-top: 20px;'>", unsafe_allow_html=True)
    st.markdown("#### Average CTC by Department")

    ct_data = {
        "Department": ["Computer Science", "Information Tech",
                       "Electronics & Comm", "Mechanical", "Civil"],
        "Avg CTC (LPA)": [13.5, 11.2, 9.0, 7.5, 6.2],
    }
    ct_df = pd.DataFrame(ct_data)

    fig_ct = px.bar(
        ct_df,
        x="Department",
        y="Avg CTC (LPA)",
        color="Avg CTC (LPA)",
        color_continuous_scale=["#0F766E", "#14B8A6"],
        text_auto=".1f",
    )
    fig_ct.update_traces(texttemplate='₹%{y} LPA', textposition='outside')
    fig_ct.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#CBD5E1",
        height=300,
        showlegend=False,
        margin=dict(l=0, r=0, t=20, b=0),
        title_text="Average Compensation by Department",
    )
    st.plotly_chart(fig_ct, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

elif nav == "Companies":
    st.markdown("### Top Recruiter Slots & Activity")

    comp_df = get_dummy_company_data()

    # Company table with status badges
    st.markdown("<div class='chart-card'>", unsafe_allow_html=True)
    st.markdown("#### Recruiter Slots Overview")

    # Table
    st.dataframe(
        comp_df.style
        .background_gradient(subset=["avg_ctc"], cmap=TEAL_CMAP)
        .highlight_max(subset=["offers"], color="#0D9488"),
        hide_index=True,
        use_container_width=True,
        column_config={
            "company": st.column_config.TextColumn("Company"),
            "slots": st.column_config.NumberColumn("Slots"),
            "offers": st.column_config.NumberColumn("Offers Made"),
            "avg_ctc": st.column_config.TextColumn("Avg CTC"),
            "status": st.column_config.TextColumn("Status"),
        },
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # Export buttons
    st.markdown("---")
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        csv_data = comp_df.to_csv(index=False)
        st.download_button(
            "Download Company Report",
            data=csv_data,
            file_name="company_report.csv",
        )
    with col_dl2:
        st.download_button(
            "Export Audit Log",
            data="Timestamp,Event,User,Company\n2026-10-26 15:40:00,Offer_Released,Placement_Officer,Apex Quantum Technologies",
            file_name="audit_log.csv",
        )

elif nav == "Velocity":
    st.markdown("### Monthly Placement Velocity Analysis")

    vel_df = get_dummy_velocity_data()

    fig_vel = px.bar(
        vel_df,
        x="month",
        y="placements",
        color="placements",
        color_continuous_scale=["#0F766E", "#14B8A6"],
        text_auto=True,
        labels={"placements": "Placements", "month": "Month"},
    )
    fig_vel.update_traces(texttemplate='%{text}', textposition='outside')
    fig_vel.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#CBD5E1",
        height=380,
        showlegend=False,
        margin=dict(l=0, r=0, t=20, b=0),
        title_text="Monthly Placement Velocity",
    )
    st.plotly_chart(fig_vel, use_container_width=True)

    st.markdown(
        f"<p style='color: #94A3B8; margin-top: 8px; font-size: 13px;'>"
        f"Total placements this period: <b>{vel_df['placements'].sum()}</b>"
        f"</p>",
        unsafe_allow_html=True,
    )

elif nav == "Students":
    st.markdown("### Student Applications & Outcomes")

    student_df = get_dummy_student_data()

    # Filters
    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        branch_filter = st.multiselect(
            "Filter by Branch",
            options=["All", "CSE", "IT", "ECE", "Mechanical", "Civil"],
            default=["All"],
            label_visibility="hidden",
        )
    with col_filter2:
        status_filter = st.multiselect(
            "Filter by Status",
            options=["All", "Placed", "Shortlisted", "Interview", "Pending", "Rejected"],
            default=["All"],
            label_visibility="hidden",
        )

    filtered_df = student_df.copy()
    if branch_filter != ["All"]:
        filtered_df = filtered_df[filtered_df["branch"].isin(branch_filter[1:])]
    if status_filter != ["All"]:
        filtered_df = filtered_df[filtered_df["status"].isin(status_filter)]

    # Student table
    st.dataframe(
        filtered_df,
        column_config={
            "roll_no": st.column_config.TextColumn("Roll No"),
            "name": st.column_config.TextColumn("Name"),
            "branch": st.column_config.TextColumn("Branch"),
            "company": st.column_config.TextColumn("Company"),
            "status": st.column_config.TextColumn("Status"),
            "ctc": st.column_config.TextColumn("Offer CTC"),
        },
        hide_index=True,
        use_container_width=True,
        height=420,
    )

# ─────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "CampusHire Dashboard | Design reference: SaaSUI (Groq Cloud / Churnkey patterns) | "
    "SQL backend endpoints can be connected using mysql.connector"
)