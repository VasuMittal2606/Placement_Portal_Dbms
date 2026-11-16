"""Placement officer queries: monitoring, cleanup and audit trail."""

from __future__ import annotations

from database.connection import call_procedure, execute, fetch_all


def get_students(branch: str | None = None, batch_year: int | None = None) -> list[dict]:
    rows, _ = call_procedure("sp_list_student_profiles", (branch, batch_year, None))
    return rows


def get_companies() -> list[dict]:
    rows, _ = call_procedure("sp_company_hiring_stats", ())
    return rows


def get_jobs() -> list[dict]:
    rows, _ = call_procedure("sp_list_job_details", (None, None))
    return rows


def get_applications() -> list[dict]:
    rows, _ = call_procedure("sp_list_applications", (None, None, None, None, None))
    return rows


def get_offers() -> list[dict]:
    return fetch_all(
        """
        SELECT o.offer_id, o.ctc, o.joining_date, o.offer_date, o.status,
               j.job_title, c.company_name, u.full_name AS student_name
          FROM offer o
          JOIN application a ON a.application_id = o.application_id
          JOIN job j ON j.job_id = a.job_id
          JOIN company c ON c.company_id = j.company_id
          JOIN student s ON s.student_id = a.student_id
          JOIN app_user u ON u.user_id = s.user_id
         ORDER BY o.offer_date DESC, o.offer_id DESC
        """
    )


def delete_job(job_id: int) -> int:
    """Referential integrity: applications/interviews/offers cascade."""
    return execute("DELETE FROM job WHERE job_id = %s", (job_id,))


def get_audit_log(limit: int = 200) -> list[dict]:
    return fetch_all(
        """
        SELECT audit_id, table_name, action_type, record_id, changed_by,
               changed_at, details
          FROM audit_log
         ORDER BY audit_id DESC
         LIMIT %s
        """,
        (limit,),
    )


def get_unplaced_students(batch_year: int | None = None) -> list[dict]:
    sql = """
        SELECT u.full_name, s.roll_no, b.branch_name, s.cgpa, s.backlogs,
               (SELECT COUNT(*) FROM application a WHERE a.student_id = s.student_id) AS applications
          FROM student s
          JOIN app_user u ON u.user_id = s.user_id
          JOIN branch b ON b.branch_id = s.branch_id
         WHERE NOT EXISTS (
                SELECT 1 FROM placement p
                 WHERE p.student_id = s.student_id AND p.is_active = 1)
    """
    params: tuple = ()
    if batch_year:
        sql += " AND s.batch_year = %s"
        params = (batch_year,)
    sql += " ORDER BY s.cgpa DESC"
    return fetch_all(sql, params)


def get_pending_offers() -> list[dict]:
    return fetch_all(
        """
        SELECT o.offer_id, o.ctc, o.offer_date, j.job_title, c.company_name,
               u.full_name AS student_name
          FROM offer o
          JOIN application a ON a.application_id = o.application_id
          JOIN job j ON j.job_id = a.job_id
          JOIN company c ON c.company_id = j.company_id
          JOIN student s ON s.student_id = a.student_id
          JOIN app_user u ON u.user_id = s.user_id
         WHERE o.status = 'pending'
         ORDER BY o.offer_date
        """
    )


def get_branch_names() -> list[str]:
    rows = fetch_all("SELECT branch_name FROM branch ORDER BY branch_name")
    return [row["branch_name"] for row in rows]
