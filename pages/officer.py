"""Placement officer dashboard - monitoring, reporting and cleanup."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from database import application_db as adb
from database import officer_db as odb
from database import placement_db as pdb
from theme import (
    goto_login,
    inject_css,
    metric_card,
    page_header,
    show_message,
    sign_out_button,
    style_figure,
)

st.set_page_config(page_title="Placement Officer | CampusHire", page_icon="📊", layout="wide")
inject_css()

user = st.session_state.get("user")
if not user or user["role"] not in ("officer", "admin"):
    st.warning("Sign in as a placement officer from the home page.")
    if st.button("Go to login"):
        goto_login()
    st.stop()

batches = [row["batch_year"] for row in pdb.get_batches()] or [2027]

with st.sidebar:
    st.markdown("<div class='brand'>Campus<span>Hire</span></div>", unsafe_allow_html=True)
    st.caption(f"{user['full_name']} - Placement Cell")
    st.divider()
    page = st.radio(
        "Menu",
        ["Overview", "Students", "Companies", "Jobs", "Applications",
         "Placements", "Reports", "Audit Log"],
        label_visibility="collapsed",
    )
    st.divider()
    batch_year = st.selectbox("Batch year", batches)
    st.divider()
    sign_out_button()

# ------------------------------------------------------------------
if page == "Overview":
    page_header("Placement Overview", "KPIs aggregated by sp_get_placement_stats.")

    metrics = pdb.get_metrics()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Placement rate", f"{metrics.get('placement_rate', 0)}%",
                    f"{metrics.get('total_placed', 0)} of {metrics.get('total_students', 0)} students")
    with col2:
        metric_card("Average CTC", f"{metrics.get('avg_ctc', 0)} LPA",
                    f"peak {metrics.get('max_ctc', 0)} LPA")
    with col3:
        metric_card("Active jobs", metrics.get("active_jobs", 0),
                    f"{metrics.get('total_companies', 0)} companies")
    with col4:
        metric_card("Applications", metrics.get("total_applications", 0),
                    f"{metrics.get('pending_offers', 0)} offers pending")

    st.write("")
    departments = pdb.get_department_stats(batch_year)
    left, right = st.columns(2)

    with left:
        if departments:
            frame = pd.DataFrame(departments)
            fig = px.bar(frame, x="branch_name", y="placed_students", text="placement_rate",
                         color="placement_rate",
                         color_continuous_scale=["#0F766E", "#14B8A6"],
                         labels={"branch_name": "Branch", "placed_students": "Placed",
                                 "placement_rate": "Rate %"})
            fig.update_traces(texttemplate="%{text}%", textposition="outside")
            fig.update_layout(title="Placements by branch", coloraxis_showscale=False)
            st.plotly_chart(style_figure(fig), use_container_width=True)
        else:
            st.info("No branch data for this batch.")

    with right:
        monthly = pdb.get_monthly_stats(batch_year)
        if monthly:
            frame = pd.DataFrame(monthly)
            fig = px.line(frame, x="month", y="placements", markers=True,
                          labels={"month": "Month", "placements": "Placements"})
            fig.update_traces(line_color="#14B8A6", line_width=3)
            fig.update_layout(title="Placements over time")
            st.plotly_chart(style_figure(fig), use_container_width=True)
        else:
            st.info("No placements recorded yet.")

    companies = pdb.get_company_stats()
    if companies:
        frame = pd.DataFrame(companies)
        fig = px.bar(frame, x="company_name", y="placed_count", color="avg_ctc",
                     color_continuous_scale=["#0F766E", "#14B8A6"],
                     labels={"company_name": "", "placed_count": "Students placed",
                             "avg_ctc": "Avg CTC"})
        fig.update_layout(title="Hiring by company")
        st.plotly_chart(style_figure(fig, height=340), use_container_width=True)

# ------------------------------------------------------------------
elif page == "Students":
    page_header("Students", "Read from sp_list_student_profiles; placement status comes from SQL.")

    branches = ["All"] + odb.get_branch_names()
    col1, col2 = st.columns(2)
    with col1:
        branch = st.selectbox("Branch", branches)
    with col2:
        year = st.selectbox("Batch", ["All"] + [str(b) for b in batches])

    students = odb.get_students(
        None if branch == "All" else branch,
        None if year == "All" else int(year),
    )
    if not students:
        st.info("No students match the filters.")
        st.stop()

    st.dataframe(
        pd.DataFrame(students)[["roll_no", "full_name", "branch_name", "batch_year",
                                "cgpa", "backlogs", "skill_count", "placement_status"]].rename(
            columns={
                "roll_no": "Roll No",
                "full_name": "Student",
                "branch_name": "Branch",
                "batch_year": "Batch",
                "skill_count": "Skills",
                "placement_status": "Placement",
            }
        ),
        hide_index=True,
        use_container_width=True,
        height=520,
    )

    unplaced = odb.get_unplaced_students(None if year == "All" else int(year))
    if unplaced:
        st.markdown("#### Unplaced students")
        st.dataframe(pd.DataFrame(unplaced), hide_index=True, use_container_width=True)

# ------------------------------------------------------------------
elif page == "Companies":
    page_header("Companies", "Hiring aggregated by sp_company_hiring_stats.")

    companies = odb.get_companies()
    if not companies:
        st.info("No companies registered.")
        st.stop()

    st.dataframe(
        pd.DataFrame(companies)[["company_name", "industry", "location", "total_jobs",
                                 "total_applications", "placed_count", "avg_ctc"]].rename(
            columns={
                "company_name": "Company",
                "industry": "Industry",
                "location": "Location",
                "total_jobs": "Jobs",
                "total_applications": "Applications",
                "placed_count": "Placed",
                "avg_ctc": "Avg CTC (LPA)",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

# ------------------------------------------------------------------
elif page == "Jobs":
    page_header("Jobs", "Deleting a job cascades to applications, interviews and offers.")

    jobs = odb.get_jobs()
    if not jobs:
        st.info("No jobs posted.")
        st.stop()

    st.dataframe(
        pd.DataFrame(jobs)[["job_id", "job_title", "company_name", "status", "ctc",
                            "openings", "application_deadline", "application_count"]].rename(
            columns={
                "job_id": "Job #",
                "job_title": "Role",
                "company_name": "Company",
                "ctc": "CTC (LPA)",
                "application_deadline": "Deadline",
                "application_count": "Applications",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

    labels = {f"#{job['job_id']} - {job['job_title']} @ {job['company_name']}": job["job_id"]
              for job in jobs}
    choice = st.selectbox("Select job", list(labels))
    confirm = st.checkbox("I understand this removes all related applications")
    if st.button("Delete job", disabled=not confirm):
        try:
            removed = odb.delete_job(labels[choice])
            if removed:
                st.success("Job deleted.")
                st.rerun()
            else:
                st.warning("Job not found.")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Database error: {exc}")

# ------------------------------------------------------------------
elif page == "Applications":
    page_header("Applications", "Officer override uses a single UPDATE; triggers log every change.")

    col1, col2 = st.columns(2)
    with col1:
        status = st.selectbox("Status", ["All"] + adb.VALID_STATUSES)
    with col2:
        branch = st.selectbox("Branch", ["All"] + odb.get_branch_names())

    applications = adb.get_applications(
        None if status == "All" else status,
        None if branch == "All" else branch,
        batch_year,
    )
    if not applications:
        st.info("No applications match the filters.")
        st.stop()

    st.dataframe(
        pd.DataFrame(applications)[["application_id", "student_name", "roll_no", "branch_name",
                                    "job_title", "company_name", "status", "skill_match",
                                    "interview_count", "applied_at"]].rename(
            columns={
                "application_id": "App #",
                "student_name": "Student",
                "roll_no": "Roll No",
                "branch_name": "Branch",
                "job_title": "Role",
                "company_name": "Company",
                "status": "Status",
                "skill_match": "Skill match %",
                "interview_count": "Rounds",
                "applied_at": "Applied",
            }
        ),
        hide_index=True,
        use_container_width=True,
        height=460,
    )

    labels = {f"App #{row['application_id']} - {row['student_name']} ({row['status']})": row["application_id"]
              for row in applications}
    choice = st.selectbox("Select application", list(labels))
    new_status = st.selectbox("New status", adb.VALID_STATUSES)
    if st.button("Update status"):
        try:
            updated = adb.update_status(labels[choice], new_status)
            if updated:
                st.success(f"Application #{labels[choice]} set to {new_status}.")
                st.rerun()
            else:
                st.warning("No change applied.")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Database error: {exc}")

# ------------------------------------------------------------------
elif page == "Placements":
    page_header("Placements", "Created automatically when a student accepts an offer.")

    placements = pdb.get_placements(batch_year)
    if not placements:
        st.info("No placements for this batch.")
        st.stop()

    frame = pd.DataFrame(placements)
    st.dataframe(
        frame[["student_name", "roll_no", "branch_name", "company_name",
               "job_title", "ctc", "joining_date", "placed_at"]].rename(
            columns={
                "student_name": "Student",
                "roll_no": "Roll No",
                "branch_name": "Branch",
                "company_name": "Company",
                "job_title": "Role",
                "ctc": "CTC (LPA)",
                "joining_date": "Joining",
                "placed_at": "Recorded",
            }
        ),
        hide_index=True,
        use_container_width=True,
        height=460,
    )

    st.download_button(
        "Download placements CSV",
        data=frame.to_csv(index=False),
        file_name=f"placements_{batch_year}.csv",
    )

# ------------------------------------------------------------------
elif page == "Reports":
    page_header("Branch Report", "sp_generate_branch_report uses a cursor over branches.")

    if st.button("Generate report", type="primary"):
        try:
            rows = pdb.get_branch_report(batch_year)
            st.session_state["branch_report"] = rows
        except Exception as exc:  # noqa: BLE001
            st.error(f"Database error: {exc}")

    report = st.session_state.get("branch_report")
    if report:
        frame = pd.DataFrame(report)
        st.dataframe(
            frame.rename(columns={
                "batch_year": "Batch",
                "branch_name": "Branch",
                "total_students": "Students",
                "placed_students": "Placed",
                "placement_rate": "Rate %",
                "avg_ctc": "Avg CTC (LPA)",
            }),
            hide_index=True,
            use_container_width=True,
        )
        st.download_button(
            "Download report CSV",
            data=frame.to_csv(index=False),
            file_name=f"branch_report_{batch_year}.csv",
        )
    else:
        st.caption("Reports are cached in placement_report_cache by the procedure.")

# ------------------------------------------------------------------
else:
    page_header("Audit Log", "Written by triggers on application, offer and placement changes.")

    logs = odb.get_audit_log(300)
    if not logs:
        st.info("No audit entries yet.")
        st.stop()

    st.dataframe(
        pd.DataFrame(logs)[["audit_id", "table_name", "action_type", "record_id",
                            "changed_by", "changed_at", "details"]].rename(
            columns={
                "audit_id": "#",
                "table_name": "Table",
                "action_type": "Action",
                "record_id": "Record",
                "changed_by": "By",
                "changed_at": "When",
                "details": "Details",
            }
        ),
        hide_index=True,
        use_container_width=True,
        height=520,
    )
