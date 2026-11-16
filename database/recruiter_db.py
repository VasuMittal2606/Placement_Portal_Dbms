"""Recruiter-side queries. Every state change is a stored procedure call."""

from __future__ import annotations

from database.connection import call_procedure, fetch_all, fetch_one


def get_recruiter(user_id: int) -> dict | None:
    return fetch_one(
        """
        SELECT r.recruiter_id, r.user_id, r.company_id, r.designation,
               u.full_name, u.email,
               c.company_name, c.industry, c.website, c.hr_contact,
               c.location AS company_location
          FROM recruiter r
          JOIN app_user u ON u.user_id = r.user_id
          JOIN company c ON c.company_id = r.company_id
         WHERE r.user_id = %s
        """,
        (user_id,),
    )


def update_company(company_id: int, name: str, industry: str, website: str,
                   contact: str, location: str) -> str:
    _, outs = call_procedure(
        "sp_update_company",
        (company_id, name, industry, website, contact, location),
        out_count=1,
    )
    return str(outs[-1])


def get_jobs(company_id: int) -> list[dict]:
    rows, _ = call_procedure("sp_list_job_details", (company_id, None))
    return rows


def post_job(recruiter_id: int, title: str, description: str, job_type: str,
             location: str, ctc: float, min_cgpa: float, max_backlogs: int,
             openings: int, deadline, skills: str) -> tuple[int | None, str]:
    _, outs = call_procedure(
        "sp_post_job",
        (recruiter_id, title, description, job_type, location, ctc, min_cgpa,
         max_backlogs, openings, deadline, skills),
        out_count=2,
    )
    job_id, message = outs
    return job_id, str(message)


def close_job(job_id: int, recruiter_id: int) -> str:
    _, outs = call_procedure("sp_close_job", (job_id, recruiter_id), out_count=1)
    return str(outs[-1])


def get_applicants(job_id: int, recruiter_id: int) -> list[dict]:
    return fetch_all(
        """
        SELECT a.application_id, a.status, a.applied_at,
               s.student_id, s.roll_no, u.full_name AS student_name,
               b.branch_name, s.cgpa, s.backlogs, s.batch_year,
               fn_student_skill_match(a.job_id, a.student_id) AS skill_match,
               (SELECT COUNT(*) FROM interview i
                 WHERE i.application_id = a.application_id) AS interview_count,
               (SELECT COUNT(*) FROM offer o
                 WHERE o.application_id = a.application_id) AS offer_count
          FROM application a
          JOIN job j ON j.job_id = a.job_id
          JOIN recruiter r ON r.company_id = j.company_id AND r.recruiter_id = %s
          JOIN student s ON s.student_id = a.student_id
          JOIN app_user u ON u.user_id = s.user_id
          JOIN branch b ON b.branch_id = s.branch_id
         WHERE a.job_id = %s
         ORDER BY a.applied_at
        """,
        (recruiter_id, job_id),
    )


def shortlist(application_id: int, recruiter_id: int) -> str:
    _, outs = call_procedure("sp_shortlist_applicant", (application_id, recruiter_id), out_count=1)
    return str(outs[-1])


def reject(application_id: int, recruiter_id: int) -> str:
    _, outs = call_procedure("sp_reject_applicant", (application_id, recruiter_id), out_count=1)
    return str(outs[-1])


def schedule_interview(application_id: int, recruiter_id: int, round_no: int,
                       interview_type: str, scheduled_at, mode: str, link: str) -> str:
    _, outs = call_procedure(
        "sp_schedule_interview",
        (application_id, recruiter_id, round_no, interview_type, scheduled_at, mode, link),
        out_count=1,
    )
    return str(outs[-1])


def get_interviews(company_id: int) -> list[dict]:
    return fetch_all(
        """
        SELECT i.interview_id, i.application_id, i.round_no, i.interview_type,
               i.scheduled_at, i.mode, i.result, i.feedback,
               j.job_title, u.full_name AS student_name
          FROM interview i
          JOIN application a ON a.application_id = i.application_id
          JOIN job j ON j.job_id = a.job_id
          JOIN student s ON s.student_id = a.student_id
          JOIN app_user u ON u.user_id = s.user_id
         WHERE j.company_id = %s
         ORDER BY i.scheduled_at DESC
        """,
        (company_id,),
    )


def update_interview_result(interview_id: int, recruiter_id: int,
                            result: str, feedback: str) -> str:
    _, outs = call_procedure(
        "sp_update_interview_result",
        (interview_id, recruiter_id, result, feedback),
        out_count=1,
    )
    return str(outs[-1])


def make_offer(application_id: int, recruiter_id: int, ctc: float, joining_date) -> str:
    _, outs = call_procedure(
        "sp_make_offer", (application_id, recruiter_id, ctc, joining_date), out_count=1
    )
    return str(outs[-1])


def auto_offer_selected(job_id: int, ctc: float, joining_date) -> tuple[int, str]:
    _, outs = call_procedure(
        "sp_auto_offer_selected", (job_id, ctc, joining_date), out_count=2
    )
    count, message = outs
    return int(count or 0), str(message)


def get_offers(company_id: int) -> list[dict]:
    return fetch_all(
        """
        SELECT o.offer_id, o.ctc, o.joining_date, o.offer_date, o.status,
               j.job_title, u.full_name AS student_name, a.status AS application_status
          FROM offer o
          JOIN application a ON a.application_id = o.application_id
          JOIN job j ON j.job_id = a.job_id
          JOIN student s ON s.student_id = a.student_id
          JOIN app_user u ON u.user_id = s.user_id
         WHERE j.company_id = %s
         ORDER BY o.offer_date DESC
        """,
        (company_id,),
    )


def get_metrics(company_id: int) -> dict:
    row = fetch_one(
        """
        SELECT
          (SELECT COUNT(*) FROM job WHERE company_id = %s AND status = 'active') AS active_jobs,
          (SELECT COUNT(*) FROM job WHERE company_id = %s) AS total_jobs,
          (SELECT COUNT(*) FROM application a JOIN job j ON j.job_id = a.job_id
            WHERE j.company_id = %s) AS applications,
          (SELECT COUNT(*) FROM application a JOIN job j ON j.job_id = a.job_id
            WHERE j.company_id = %s AND a.status IN ('shortlisted', 'interview')) AS in_process,
          (SELECT COUNT(*) FROM application a JOIN job j ON j.job_id = a.job_id
            WHERE j.company_id = %s AND a.status = 'placed') AS placed,
          (SELECT COUNT(DISTINCT a.student_id) FROM application a JOIN job j ON j.job_id = a.job_id
            WHERE j.company_id = %s) AS candidates
        """,
        (company_id,) * 6,
    )
    return row or {}


def get_status_funnel(company_id: int) -> list[dict]:
    return fetch_all(
        """
        SELECT a.status, COUNT(*) AS total
          FROM application a
          JOIN job j ON j.job_id = a.job_id
         WHERE j.company_id = %s
         GROUP BY a.status
         ORDER BY total DESC
        """,
        (company_id,),
    )


def get_applications_per_job(company_id: int) -> list[dict]:
    return fetch_all(
        """
        SELECT j.job_title, COUNT(a.application_id) AS applications
          FROM job j
          LEFT JOIN application a ON a.job_id = j.job_id
         WHERE j.company_id = %s
         GROUP BY j.job_id, j.job_title
         ORDER BY applications DESC
        """,
        (company_id,),
    )
