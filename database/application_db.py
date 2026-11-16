"""Application-level queries shared by recruiters and the placement officer."""

from __future__ import annotations

from database.connection import call_procedure, execute, fetch_all

VALID_STATUSES = [
    "applied",
    "shortlisted",
    "interview",
    "offered",
    "placed",
    "rejected",
    "withdrawn",
]


def get_applications(status: str | None = None, branch: str | None = None,
                     batch_year: int | None = None) -> list[dict]:
    rows, _ = call_procedure(
        "sp_list_applications", (None, None, status, branch, batch_year)
    )
    return rows


def get_application(application_id: int) -> dict | None:
    rows, _ = call_procedure(
        "sp_list_applications", (application_id, None, None, None, None)
    )
    return rows[0] if rows else None


def get_interviews(application_id: int) -> list[dict]:
    return fetch_all(
        """
        SELECT interview_id, round_no, interview_type, scheduled_at, mode,
               meeting_link, result, feedback
          FROM interview
         WHERE application_id = %s
         ORDER BY round_no
        """,
        (application_id,),
    )


def get_history(application_id: int) -> list[dict]:
    return fetch_all(
        """
        SELECT audit_id, table_name, action_type, record_id, changed_by,
               changed_at, details
          FROM audit_log
         WHERE table_name = 'application' AND record_id = %s
         ORDER BY changed_at DESC
        """,
        (application_id,),
    )


def update_status(application_id: int, status: str) -> int:
    """Officer override. Triggers still validate downstream workflow."""
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {status}")
    return execute(
        "UPDATE application SET status = %s WHERE application_id = %s",
        (status, application_id),
    )


def get_status_counts() -> list[dict]:
    return fetch_all(
        "SELECT status, COUNT(*) AS total FROM application GROUP BY status ORDER BY total DESC"
    )
