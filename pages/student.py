"""Student dashboard - thin Streamlit UI over the SQL procedures."""

from __future__ import annotations

import pandas as pd
import plotly.express as px
import streamlit as st

from database import auth_db, student_db as sdb
from theme import (
    inject_css,
    login_gate,
    metric_card,
    page_header,
    show_message,
    sign_out_button,
    style_figure,
)

st.set_page_config(page_title="Student | CampusHire", page_icon="🎓", layout="wide")
inject_css()

login_gate("student")
user = st.session_state["user"]

if "student_id" not in st.session_state:
    st.session_state["student_id"] = auth_db.get_student_id(user["user_id"])
student_id = st.session_state["student_id"]

profile = sdb.get_profile(student_id)
if not profile:
    st.error("Student profile not found. Re-run python init_db.py.")
    st.stop()

with st.sidebar:
    st.markdown("<div class='brand'>Campus<span>Hire</span></div>", unsafe_allow_html=True)
    st.caption(f"{profile['full_name']} - {profile['roll_no']}")
    st.caption(f"{profile['branch_name']} | Batch {profile['batch_year']} | CGPA {profile['cgpa']}")
    st.divider()
    page = st.radio(
        "Menu",
        ["Overview", "Browse Jobs", "My Applications", "Interviews & Offers", "Profile & Skills"],
        label_visibility="collapsed",
    )
    st.divider()
    st.caption(profile["placement_status"])
    sign_out_button()

# ------------------------------------------------------------------
if page == "Overview":
    page_header("Student Overview", "Snapshot of applications, interviews and offers.")

    dashboard = sdb.get_dashboard(student_id) or {}
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Applications", dashboard.get("applications", 0), "total submitted")
    with col2:
        metric_card("In process", dashboard.get("in_progress", 0), "shortlisted / interviewing")
    with col3:
        metric_card("Interviews", dashboard.get("interviews", 0), "scheduled rounds")
    with col4:
        metric_card("Eligible jobs", dashboard.get("eligible_jobs", 0), "open right now")

    st.write("")
    st.markdown("#### Placement status")
    st.info(profile["placement_status"])

    if dashboard.get("pending_offers"):
        st.success(f"You have {dashboard['pending_offers']} pending offer(s) - respond in 'Interviews & Offers'.")

    st.markdown("#### Latest openings")
    jobs = sdb.list_jobs(student_id)
    if jobs:
        frame = pd.DataFrame(jobs)
        frame["eligible"] = frame["is_eligible"].apply(lambda value: "Yes" if value == 1 else "No")
        st.dataframe(
            frame[["job_title", "company_name", "ctc", "min_cgpa", "openings",
                   "application_deadline", "skill_match", "eligible"]].rename(
                columns={
                    "job_title": "Role",
                    "company_name": "Company",
                    "ctc": "CTC (LPA)",
                    "min_cgpa": "Min CGPA",
                    "openings": "Openings",
                    "application_deadline": "Deadline",
                    "skill_match": "Skill match %",
                    "eligible": "Eligible",
                }
            ),
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("No active job postings right now.")

# ------------------------------------------------------------------
elif page == "Browse Jobs":
    page_header("Browse Jobs", "Eligibility is evaluated by fn_check_eligibility inside MySQL.")

    jobs = sdb.list_jobs(student_id)
    if not jobs:
        st.info("No active job postings right now.")
        st.stop()

    only_eligible = st.toggle("Show eligible jobs only", value=False)
    visible = [job for job in jobs if job["is_eligible"] == 1] if only_eligible else jobs

    frame = pd.DataFrame(visible)
    frame["Eligible"] = frame["is_eligible"].apply(lambda value: "Yes" if value == 1 else "No")
    st.dataframe(
        frame[["job_title", "company_name", "job_type", "location", "ctc",
               "min_cgpa", "max_backlogs", "openings", "application_deadline",
               "skill_match", "Eligible"]].rename(
            columns={
                "job_title": "Role",
                "company_name": "Company",
                "job_type": "Type",
                "ctc": "CTC (LPA)",
                "min_cgpa": "Min CGPA",
                "max_backlogs": "Max backlogs",
                "application_deadline": "Deadline",
                "skill_match": "Skill match %",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

    options = {f"#{job['job_id']} - {job['job_title']} @ {job['company_name']}": job["job_id"]
               for job in visible}
    choice = st.selectbox("Select a job for details", list(options))
    job = sdb.get_job(options[choice])

    if job:
        left, right = st.columns([1.4, 1])
        with left:
            st.markdown(f"### {job['job_title']}")
            st.caption(f"{job['company_name']} | {job['job_type']} | {job['location']}")
            st.write(
                f"CTC **{job['ctc']} LPA** | Min CGPA **{job['min_cgpa']}** | "
                f"Max backlogs **{job['max_backlogs']}** | Openings **{job['openings']}**"
            )
            skills = sdb.get_job_skills(job["job_id"])
            if skills:
                st.markdown(
                    " ".join(
                        f"`{row['skill_name']}`" + (" (must)" if row["is_mandatory"] == 1 else "")
                        for row in skills
                    )
                )
            st.caption(f"Applications so far: {job['application_count']} | Deadline: {job['application_deadline']}")
        with right:
            already = any(
                app["job_id"] == job["job_id"]
                and app["status"] != "withdrawn"
                for app in sdb.get_applications(student_id)
            )
            if already:
                st.info("You have already applied to this job.")
            elif job["status"] != "active":
                st.warning("This posting is closed.")
            else:
                if st.button("Apply now", type="primary", use_container_width=True):
                    try:
                        show_message(sdb.apply_to_job(student_id, job["job_id"]))
                    except Exception as exc:  # noqa: BLE001
                        st.error(f"Database error: {exc}")

# ------------------------------------------------------------------
elif page == "My Applications":
    page_header("My Applications", "Every status change is written by SQL procedures and triggers.")

    applications = sdb.get_applications(student_id)
    if not applications:
        st.info("You have not applied to any job yet.")
        st.stop()

    frame = pd.DataFrame(applications)
    st.dataframe(
        frame[["application_id", "job_title", "company_name", "branch_name",
               "status", "skill_match", "interview_count", "applied_at"]].rename(
            columns={
                "application_id": "App #",
                "job_title": "Role",
                "company_name": "Company",
                "branch_name": "Branch",
                "status": "Status",
                "skill_match": "Skill match %",
                "interview_count": "Interviews",
                "applied_at": "Applied on",
            }
        ),
        hide_index=True,
        use_container_width=True,
    )

    options = {f"App #{app['application_id']} - {app['job_title']} ({app['status']})": app["application_id"]
               for app in applications}
    selected_label = st.selectbox("Select an application", list(options))
    application_id = options[selected_label]
    detail = next(app for app in applications if app["application_id"] == application_id)

    left, right = st.columns([1.2, 1])
    with left:
        interviews = sdb.get_interviews(student_id)
        rounds = [row for row in interviews if row["application_id"] == application_id]
        st.markdown("#### Interview rounds")
        if rounds:
            st.dataframe(
                pd.DataFrame(rounds)[["round_no", "interview_type", "scheduled_at",
                                      "mode", "result", "feedback"]].rename(
                    columns={
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
        else:
            st.caption("No interview rounds scheduled yet.")

    with right:
        st.markdown("#### Actions")
        if detail["status"] in ("applied", "shortlisted", "interview"):
            if st.button("Withdraw application", use_container_width=True):
                try:
                    show_message(sdb.withdraw_application(application_id, student_id))
                    st.rerun()
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Database error: {exc}")
        else:
            st.caption(f"Application is in '{detail['status']}' state - no student action available.")

# ------------------------------------------------------------------
elif page == "Interviews & Offers":
    page_header("Interviews & Offers", "Accepting an offer fires the trigger that records the placement.")

    interviews = sdb.get_interviews(student_id)
    st.markdown("#### Scheduled interviews")
    if interviews:
        st.dataframe(
            pd.DataFrame(interviews)[["company_name", "job_title", "round_no",
                                      "interview_type", "scheduled_at", "mode",
                                      "meeting_link", "result"]].rename(
                columns={
                    "company_name": "Company",
                    "job_title": "Role",
                    "round_no": "Round",
                    "interview_type": "Type",
                    "scheduled_at": "Scheduled",
                    "mode": "Mode",
                    "meeting_link": "Meeting link",
                    "result": "Result",
                }
            ),
            hide_index=True,
            use_container_width=True,
        )
    else:
        st.info("No interviews scheduled yet.")

    st.markdown("#### Offers")
    offers = sdb.get_offers(student_id)
    if not offers:
        st.info("No offers received yet.")
        st.stop()

    st.dataframe(
        pd.DataFrame(offers)[["offer_id", "company_name", "job_title", "ctc",
                              "joining_date", "offer_date", "status"]].rename(
            columns={
                "offer_id": "Offer #",
                "company_name": "Company",
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

    pending = [offer for offer in offers if offer["status"] == "pending"]
    if pending:
        labels = {f"Offer #{offer['offer_id']} - {offer['company_name']} ({offer['ctc']} LPA)": offer["offer_id"]
                  for offer in pending}
        choice = st.selectbox("Respond to a pending offer", list(labels))
        col_accept, col_decline = st.columns(2)
        with col_accept:
            if st.button("Accept offer", type="primary", use_container_width=True):
                try:
                    show_message(sdb.respond_to_offer(labels[choice], student_id, True))
                    st.rerun()
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Database error: {exc}")
        with col_decline:
            if st.button("Decline offer", use_container_width=True):
                try:
                    show_message(sdb.respond_to_offer(labels[choice], student_id, False))
                    st.rerun()
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Database error: {exc}")
    else:
        st.caption("No pending offers to respond to.")

# ------------------------------------------------------------------
else:
    page_header("Profile & Skills", "Updates go through sp_update_student_profile and sp_add_student_skill.")

    left, right = st.columns([1, 1.2])

    with left:
        st.markdown("#### Profile")
        with st.form("profile_form"):
            phone = st.text_input("Phone", value=profile["phone"] or "")
            cgpa = st.number_input("CGPA", min_value=0.0, max_value=10.0,
                                   value=float(profile["cgpa"]), step=0.01)
            backlogs = st.number_input("Active backlogs", min_value=0, max_value=20,
                                       value=int(profile["backlogs"]), step=1)
            resume = st.text_input("Resume link", value=profile["resume_url"] or "")
            if st.form_submit_button("Save profile", use_container_width=True):
                try:
                    show_message(sdb.update_profile(student_id, phone, cgpa, backlogs, resume))
                    st.rerun()
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Database error: {exc}")

    with right:
        st.markdown("#### Skills")
        skills = sdb.get_skills(student_id)
        if skills:
            st.dataframe(
                pd.DataFrame(skills)[["skill_name", "proficiency"]].rename(
                    columns={"skill_name": "Skill", "proficiency": "Proficiency"}
                ),
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.caption("No skills recorded yet.")

        with st.form("skill_form"):
            catalog = [row["skill_name"] for row in sdb.list_skill_catalog()]
            skill_name = st.selectbox("Skill", catalog if catalog else ["Python"])
            custom = st.text_input("Or type a new skill")
            proficiency = st.selectbox("Proficiency", ["Beginner", "Intermediate", "Advanced"],
                                       index=1)
            if st.form_submit_button("Add / update skill", use_container_width=True):
                try:
                    show_message(sdb.add_skill(student_id, custom or skill_name, proficiency))
                    st.rerun()
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Database error: {exc}")

        if skills:
            remove_options = {row["skill_name"]: row["skill_id"] for row in skills}
            to_remove = st.selectbox("Remove skill", list(remove_options))
            if st.button("Remove selected skill"):
                if sdb.remove_skill(student_id, remove_options[to_remove]):
                    st.success(f"Removed {to_remove}")
                    st.rerun()
