"""Login is a stored procedure: sp_verify_login does the credential check."""

from __future__ import annotations

from database.connection import call_procedure, fetch_one


def verify_login(email: str, password: str) -> dict | None:
    """Return {user_id, role, full_name} on success, else None."""
    _, outs = call_procedure("sp_verify_login", (email, password), out_count=4)
    user_id, role, full_name, message = outs
    if user_id is None:
        return None
    return {"user_id": user_id, "role": role, "full_name": full_name, "message": message}


def get_student_id(user_id: int) -> int | None:
    row = fetch_one("SELECT student_id FROM student WHERE user_id = %s", (user_id,))
    return row["student_id"] if row else None


def get_recruiter_id(user_id: int) -> int | None:
    row = fetch_one("SELECT recruiter_id FROM recruiter WHERE user_id = %s", (user_id,))
    return row["recruiter_id"] if row else None


def get_officer_id(user_id: int) -> int | None:
    row = fetch_one("SELECT officer_id FROM placement_officer WHERE user_id = %s", (user_id,))
    return row["officer_id"] if row else None
