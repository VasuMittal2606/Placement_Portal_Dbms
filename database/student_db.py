"""Student-side queries. Validation and workflow rules live in SQL."""

from __future__ import annotations

from database.connection import call_procedure, execute, fetch_all


def get_profile(student_id: int) -> dict | None:
    rows, _ = call_procedure("sp_list_student_profiles", (None, None, student_id))
    return rows[0] if rows else None


def get_dashboard(student_id: int) -> dict | None:
    rows, _ = call_procedure("sp_get_student_dashboard", (student_id,))
    return rows[0] if rows else None


def update_profile(student_id: int, phone: str, cgpa: float, backlogs: int, resume_url: str) -> str:
    _, outs = call_procedure(
        "sp_update_student_profile",
        (student_id, phone, cgpa, backlogs, resume_url),
        out_count=1,
    )
    return str(outs[-1])


def list_branches() -> list[dict]:
    return fetch_all("SELECT branch_id, branch_name FROM branch ORDER BY branch_name")


def list_jobs(student_id: int) -> list[dict]:
    rows, _ = call_procedure("sp_list_open_jobs", (student_id,))
    return rows


def get_job(job_id: int) -> dict | None:
    rows, _ = call_procedure("sp_list_job_details", (None, job_id))
    return rows[0] if rows else None


def get_job_skills(job_id: int) -> list[dict]:
    return fetch_all(
        """
        SELECT s.skill_name, js.is_mandatory
          FROM job_skill js
          JOIN skill s ON s.skill_id = js.skill_id
         WHERE js.job_id = %s
         ORDER BY js.is_mandatory DESC, s.skill_name
        """,
        (job_id,),
    )


def apply_to_job(student_id: int, job_id: int) -> str:
    _, outs = call_procedure("sp_apply_for_job", (student_id, job_id), out_count=1)
    return str(outs[-1])


def withdraw_application(application_id: int, student_id: int) -> str:
    _, outs = call_procedure(
        "sp_withdraw_application", (application_id, student_id), out_count=1
    )
    return str(outs[-1])


def get_applications(student_id: int) -> list[dict]:
    rows, _ = call_procedure("sp_list_applications", (None, student_id, None, None, None))
    return rows


def get_interviews(student_id: int) -> list[dict]:
    return fetch_all(
        """
        SELECT i.interview_id, i.round_no, i.interview_type, i.scheduled_at, i.mode,
               i.meeting_link, i.result, i.feedback,
               j.job_title, c.company_name, a.application_id
          FROM interview i
          JOIN application a ON a.application_id = i.application_id
          JOIN job j ON j.job_id = a.job_id
          JOIN company c ON c.company_id = j.company_id
         WHERE a.student_id = %s
         ORDER BY i.scheduled_at DESC
        """,
        (student_id,),
    )


def get_offers(student_id: int) -> list[dict]:
    return fetch_all(
        """
        SELECT o.offer_id, o.ctc, o.joining_date, o.offer_date, o.status,
               j.job_title, c.company_name
          FROM offer o
          JOIN application a ON a.application_id = o.application_id
          JOIN job j ON j.job_id = a.job_id
          JOIN company c ON c.company_id = j.company_id
         WHERE a.student_id = %s
         ORDER BY o.offer_date DESC
        """,
        (student_id,),
    )


def respond_to_offer(offer_id: int, student_id: int, accept: bool) -> str:
    _, outs = call_procedure(
        "sp_respond_to_offer", (offer_id, student_id, 1 if accept else 0), out_count=1
    )
    return str(outs[-1])


def get_skills(student_id: int) -> list[dict]:
    return fetch_all(
        """
        SELECT s.skill_id, s.skill_name, ss.proficiency
          FROM student_skill ss
          JOIN skill s ON s.skill_id = ss.skill_id
         WHERE ss.student_id = %s
         ORDER BY s.skill_name
        """,
        (student_id,),
    )


def list_skill_catalog() -> list[dict]:
    return fetch_all("SELECT skill_id, skill_name FROM skill ORDER BY skill_name")


def add_skill(student_id: int, skill_name: str, proficiency: str) -> str:
    _, outs = call_procedure(
        "sp_add_student_skill", (student_id, skill_name, proficiency), out_count=1
    )
    return str(outs[-1])


def remove_skill(student_id: int, skill_id: int) -> int:
    return execute(
        "DELETE FROM student_skill WHERE student_id = %s AND skill_id = %s",
        (student_id, skill_id),
    )
