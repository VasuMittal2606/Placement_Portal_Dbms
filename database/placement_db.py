"""Placement analytics. Aggregation is done by SQL stored procedures."""

from __future__ import annotations

from database.connection import call_procedure, fetch_all


def get_placements(batch_year: int | None = None) -> list[dict]:
    sql = """
        SELECT p.placement_id, u.full_name AS student_name, s.roll_no,
               b.branch_name, c.company_name, j.job_title,
               o.ctc, o.joining_date, o.offer_date, p.placed_at
          FROM placement p
          JOIN student s ON s.student_id = p.student_id
          JOIN app_user u ON u.user_id = s.user_id
          JOIN branch b ON b.branch_id = s.branch_id
          JOIN offer o ON o.offer_id = p.offer_id
          JOIN application a ON a.application_id = o.application_id
          JOIN job j ON j.job_id = a.job_id
          JOIN company c ON c.company_id = j.company_id
         WHERE p.is_active = 1
    """
    params: tuple = ()
    if batch_year:
        sql += " AND s.batch_year = %s"
        params = (batch_year,)
    sql += " ORDER BY o.ctc DESC"
    return fetch_all(sql, params)


def get_metrics() -> dict:
    """sp_get_placement_stats returns a single row of computed KPIs."""
    rows, _ = call_procedure("sp_get_placement_stats", (), out_count=0)
    return rows[0] if rows else {}


def get_department_stats(batch_year: int | None = None) -> list[dict]:
    rows, _ = call_procedure("sp_branch_placement_analytics", (batch_year,))
    return rows


def get_company_stats() -> list[dict]:
    rows, _ = call_procedure("sp_company_hiring_stats", ())
    return rows


def get_monthly_stats(batch_year: int | None = None) -> list[dict]:
    sql = """
        SELECT DATE_FORMAT(o.offer_date, '%%Y-%%m') AS month,
               COUNT(*) AS placements,
               ROUND(SUM(o.ctc), 2) AS total_ctc
          FROM placement p
          JOIN offer o ON o.offer_id = p.offer_id
          JOIN student s ON s.student_id = p.student_id
         WHERE p.is_active = 1
    """
    params: tuple = ()
    if batch_year:
        sql += " AND s.batch_year = %s"
        params = (batch_year,)
    sql += " GROUP BY month ORDER BY month"
    return fetch_all(sql, params)


def get_branch_report(batch_year: int) -> list[dict]:
    """Cursor based procedure: sp_generate_branch_report."""
    rows, _ = call_procedure("sp_generate_branch_report", (batch_year,), out_count=0)
    return rows


def get_batches() -> list[dict]:
    return fetch_all(
        "SELECT DISTINCT batch_year FROM student ORDER BY batch_year DESC"
    )
