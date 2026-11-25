"""Recruiter dashboard - every workflow step is a stored procedure call."""

from __future__ import annotations

from datetime import date, datetime, time, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from database import auth_db, recruiter_db as rdb
from theme import (
    inject_css,
    login_gate,
    metric_card,
    page_header,
    show_message,
    sign_out_button,
    style_figure,
)

st.set_page_config(page_title="Recruiter | CampusHire", page_icon="🏢", layout="wide")
inject_css()

login_gate("recruiter")
user = st.session_state["user"]

if "recruiter_id" not in st.session_state:
    st.session_state["recruiter_id"] = auth_db.get_recruiter_id(user["user_id"])
recruiter = rdb.get_recruiter(user["user_id"])
if not recruiter:
    st.error("Recruiter profile not found. Re-run python init_db.py.")
    st.stop()

recruiter_id = recruiter["recruiter_id"]
company_id = recruiter["company_id"]

with st.sidebar:
    st.markdown("<div class='brand'>Campus<span>Hire</span></div>", unsafe_allow_html=True)
    st.caption(f"{recruiter['full_name']} - {recruiter['designation'] or 'Recruiter'}")
    st.caption(recruiter["company_name"])
    st.divider()
    page = st.radio(
        "Menu",
        ["Overview", "Post Job", "My Jobs", "Applicants", "Interviews", "Offers", "Company Profile"],
        label_visibility="collapsed",
    )
    st.divider()
    sign_out_button()

jobs = rdb.get_jobs(company_id)

# ------------------------------------------------------------------
if page == "Overview":
    page_header("Recruiter Overview", f"Hiring activity for {recruiter['company_name']}.")

    metrics = rdb.get_metrics(company_id)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Active jobs", metrics.get("active_jobs", 0), "currently open")
    with col2:
        metric_card("Applications", metrics.get("applications", 0), "all time")
    with col3:
        metric_card("In process", metrics.get("in_process", 0), "shortlisted / interviewing")
    with col4:
        metric_card("Placed", metrics.get("placed", 0), "offers accepted")

    st.write("")
    left, right = st.columns(2)

    with left:
        funnel = rdb.get_status_funnel(company_id)
        if funnel:
            frame = pd.DataFrame(funnel)
            fig = px.bar(frame, x="status", y="total", color="total",
                         color_continuous_scale=["#0F766E", "#14B8A6"],
                         labels={"status": "Application status", "total": "Candidates"})
            fig.update_layout(title="Application funnel", coloraxis_showscale=False)
            st.plotly_chart(style_figure(fig), use_container_width=True)
        else:
            st.info("No applications yet.")

    with right:
        per_job = rdb.get_applications_per_job(company_id)
        if per_job:
            frame = pd.DataFrame(per_job)
            fig = px.bar(frame, x="applications", y="job_title", orientation="h",
                         color="applications", color_continuous_scale=["#0F766E", "#14B8A6"],
                         labels={"applications": "Applications", "job_title": ""})
            fig.update_layout(title="Applications per job", coloraxis_showscale=False)
            st.plotly_chart(style_figure(fig), use_container_width=True)
        else:
            st.info("Post a job to see application counts.")

# ------------------------------------------------------------------
elif page == "Post Job":
    page_header("Post a Job", "sp_post_job inserts the opening and links mandatory skills.")

    with st.form("post_job_form"):
        col1, col2 = st.columns(2)
        with col1:
            title = st.text_input("Job title", placeholder="Software Engineer")
            description = st.text_area("Description", height=120)
            job_type = st.selectbox("Job type", ["Full-time", "Internship", "Internship + PPO"])
            location = st.text_input("Location", placeholder="Bengaluru")
            ctc = st.number_input("CTC (LPA)", min_value=0.5, max_value=100.0, value=10.0, step=0.5)
        with col2:
            min_cgpa = st.number_input("Minimum CGPA", 0.0, 10.0, 7.0, 0.1)
            max_backlogs = st.number_input("Max backlogs", 0, 10, 0, 1)
            openings = st.number_input("Openings", 1, 100, 1, 1)
            deadline = st.date_input("Application deadline", value=date.today() + timedelta(days=30))
            skills = st.text_input("Mandatory skills", placeholder="Python, SQL, Data Structures")
        submitted = st.form_submit_button("Publish job", use_container_width=True)

    if submitted:
        if not title.strip():
            st.warning("Job title is required.")
        else:
            try:
                job_id, message = rdb.post_job(
                    recruiter_id, title.strip(), description.strip(), job_type, location.strip(),
                    ctc, min_cgpa, int(max_backlogs), int(openings), deadline, skills,
                )
                show_message(message)
                if message.upper().startswith("SUCCESS"):
                    st.caption(f"Linked skills: {skills or 'none'}")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Database error: {exc}")

# ------------------------------------------------------------------
elif page == "My Jobs":
    page_header("My Jobs", "Close a posting or auto-release offers to selected candidates.")

    if not jobs:
        st.info("No jobs posted yet.")
        st.stop()

    st.dataframe(
        pd.DataFrame(jobs)[["job_id", "job_title", "status", "openings", "ctc",
                            "application_deadline", "application_count", "shortlisted_count"]].rename(
            columns={
                "job_id": "Job #",
                "job_title": "Role",
                "status": "Status",
                "openings": "Openings",
                "ctc": "CTC (LPA)",
                "application_deadline": "Deadline",
                "application_count": "Applications",
                "shortlisted_count": "In process",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

    labels = {f"#{job['job_id']} - {job['job_title']} ({job['status']})": job["job_id"] for job in jobs}
    choice = st.selectbox("Select job", list(labels))
    job_id = labels[choice]

    left, right = st.columns(2)
    with left:
        st.markdown("#### Close posting")
        if st.button("Close selected job", use_container_width=True):
            try:
                show_message(rdb.close_job(job_id, recruiter_id))
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(f"Database error: {exc}")

    with right:
        st.markdown("#### Auto offers (cursor procedure)")
        st.caption("sp_auto_offer_selected loops selected candidates and releases offers.")
        with st.form("auto_offer_form"):
            ctc = st.number_input("Offer CTC (LPA)", 0.5, 100.0, 12.0, 0.5)
            joining = st.date_input("Joining date", value=date.today() + timedelta(days=200))
            if st.form_submit_button("Release offers", use_container_width=True):
                try:
                    count, message = rdb.auto_offer_selected(job_id, ctc, joining)
                    show_message(message)
                    if message.upper().startswith("SUCCESS"):
                        st.caption(f"Offers created: {count}")
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Database error: {exc}")

# ------------------------------------------------------------------
elif page == "Applicants":
    page_header("Applicants", "Move candidates through shortlist -> interview -> offer.")

    if not jobs:
        st.info("Post a job first.")
        st.stop()

    labels = {f"#{job['job_id']} - {job['job_title']}": job["job_id"] for job in jobs}
    choice = st.selectbox("Select job", list(labels))
    job_id = labels[choice]

    applicants = rdb.get_applicants(job_id, recruiter_id)
    if not applicants:
        st.info("No applications for this job yet.")
        st.stop()

    st.dataframe(
        pd.DataFrame(applicants)[["application_id", "student_name", "roll_no", "branch_name",
                                  "cgpa", "backlogs", "skill_match", "status",
                                  "interview_count", "offer_count"]].rename(
            columns={
                "application_id": "App #",
                "student_name": "Candidate",
                "roll_no": "Roll No",
                "branch_name": "Branch",
                "skill_match": "Skill match %",
                "status": "Status",
                "interview_count": "Rounds",
                "offer_count": "Offers",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

    options = {f"App #{row['application_id']} - {row['student_name']} ({row['status']})": row
               for row in applicants}
    selected = st.selectbox("Select application", list(options))
    application = options[selected]
    application_id = application["application_id"]

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Shortlist / reject")
        if st.button("Shortlist candidate", use_container_width=True):
            try:
                show_message(rdb.shortlist(application_id, recruiter_id))
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(f"Database error: {exc}")
        if st.button("Reject candidate", use_container_width=True):
            try:
                show_message(rdb.reject(application_id, recruiter_id))
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(f"Database error: {exc}")

    with col2:
        st.markdown("#### Schedule interview")
        with st.form("schedule_form"):
            round_no = st.number_input("Round", 1, 10, int(application["interview_count"]) + 1, 1)
            interview_type = st.selectbox("Type", ["Aptitude", "Technical", "HR", "Group Discussion"])
            interview_day = st.date_input("Date", value=date.today() + timedelta(days=3))
            interview_time = st.time_input("Time", value=time(10, 0))
            mode = st.selectbox("Mode", ["Online", "Offline"])
            link = st.text_input("Meeting link (optional)")
            if st.form_submit_button("Schedule", use_container_width=True):
                scheduled_at = datetime.combine(interview_day, interview_time)
                try:
                    show_message(
                        rdb.schedule_interview(
                            application_id, recruiter_id, int(round_no),
                            interview_type, scheduled_at, mode, link.strip(),
                        )
                    )
                    st.rerun()
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Database error: {exc}")

    st.divider()
    st.markdown("#### Interview results & offers")
    interviews = rdb.get_interviews(company_id)
    rounds = [row for row in interviews if row["application_id"] == application_id]
    if rounds:
        st.dataframe(
            pd.DataFrame(rounds)[["interview_id", "round_no", "interview_type",
                                  "scheduled_at", "mode", "result", "feedback"]].rename(
                columns={
                    "interview_id": "Interview #",
                    "round_no": "Round",
                    "interview_type": "Type",
                    "scheduled_at": "Scheduled",
                    "mode": "Mode",
                    "result": "Result",
                    "feedback": "Feedback",
                }
            ),
            hide_index=True,
            use_container_width=True,
        )
        with st.form("result_form"):
            round_labels = {f"Round {row['round_no']} ({row['interview_type']})": row["interview_id"]
                            for row in rounds}
            chosen = st.selectbox("Round", list(round_labels))
            result = st.selectbox("Result", ["pending", "selected", "rejected", "on_hold"])
            feedback = st.text_area("Feedback", height=80)
            if st.form_submit_button("Save result", use_container_width=True):
                try:
                    show_message(
                        rdb.update_interview_result(
                            round_labels[chosen], recruiter_id, result, feedback
                        )
                    )
                    st.rerun()
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Database error: {exc}")
    else:
        st.caption("No interview rounds scheduled for this application.")

    st.markdown("#### Release offer")
    with st.form("offer_form"):
        offer_ctc = st.number_input("Offered CTC (LPA)", 0.5, 100.0,
                                    value=float(application.get("cgpa", 0) or 10), step=0.5)
        joining = st.date_input("Joining date", value=date.today() + timedelta(days=200))
        if st.form_submit_button("Make offer", use_container_width=True):
            try:
                show_message(rdb.make_offer(application_id, recruiter_id, offer_ctc, joining))
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(f"Database error: {exc}")

# ------------------------------------------------------------------
elif page == "Interviews":
    page_header("Interview Schedule", "All rounds booked by your company.")

    interviews = rdb.get_interviews(company_id)
    if not interviews:
        st.info("No interviews scheduled yet.")
        st.stop()

    st.dataframe(
        pd.DataFrame(interviews)[["interview_id", "student_name", "job_title", "round_no",
                                  "interview_type", "scheduled_at", "mode", "result"]].rename(
            columns={
                "interview_id": "Interview #",
                "student_name": "Candidate",
                "job_title": "Role",
                "round_no": "Round",
                "interview_type": "Type",
                "scheduled_at": "Scheduled",
                "mode": "Mode",
                "result": "Result",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

# ------------------------------------------------------------------
elif page == "Offers":
    page_header("Offers", "Offers released by your company and their responses.")

    offers = rdb.get_offers(company_id)
    if not offers:
        st.info("No offers released yet.")
        st.stop()

    st.dataframe(
        pd.DataFrame(offers)[["offer_id", "student_name", "job_title", "ctc",
                              "joining_date", "offer_date", "status"]].rename(
            columns={
                "offer_id": "Offer #",
                "student_name": "Candidate",
                "job_title": "Role",
                "ctc": "CTC (LPA)",
                "joining_date": "Joining",
                "offer_date": "Released",
                "status": "Status",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

# ------------------------------------------------------------------
else:
    page_header("Company Profile", "sp_update_company keeps the recruiter record in sync.")

    with st.form("company_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Company name", value=recruiter["company_name"])
            industry = st.text_input("Industry", value=recruiter["industry"] or "")
            location = st.text_input("Location", value=recruiter["company_location"] or "")
        with col2:
            website = st.text_input("Website", value=recruiter["website"] or "")
            contact = st.text_input("HR contact", value=recruiter["hr_contact"] or "")
        if st.form_submit_button("Save changes", use_container_width=True):
            try:
                show_message(rdb.update_company(company_id, name, industry, website, contact, location))
                st.rerun()
            except Exception as exc:  # noqa: BLE001
                st.error(f"Database error: {exc}")
