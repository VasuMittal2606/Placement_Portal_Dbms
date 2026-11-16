#!/usr/bin/env python3
"""Create and seed the CampusHire MySQL database.

Usage:
    python init_db.py

Connection settings (defaults match a local MySQL install):
    CAMPUSHIRE_DB_HOST      localhost
    CAMPUSHIRE_DB_PORT      3306
    CAMPUSHIRE_DB_USER      root
    CAMPUSHIRE_DB_PASSWORD  vasu1234
    CAMPUSHIRE_DB_NAME      campushire

Execution order:
    schema -> functions -> procedures -> triggers -> sample_data
"""

from __future__ import annotations

import os
from pathlib import Path

import mysql.connector
from mysql.connector import Error

BASE_DIR = Path(__file__).resolve().parent
SQL_DIR = BASE_DIR / "mysql"

DB_NAME = os.getenv("CAMPUSHIRE_DB_NAME", "campushire")
FILES = [
    "schema.sql",
    "functions.sql",
    "procedures.sql",
    "triggers.sql",
    "sample_data.sql",
]


def split_sql_script(script: str) -> list[str]:
    """Split a .sql file into statements, honouring DELIMITER directives."""
    statements: list[str] = []
    buffer: list[str] = []
    delimiter = ";"

    for line in script.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("DELIMITER "):
            delimiter = stripped.split(None, 1)[1]
            continue
        if not buffer and not stripped:
            continue
        buffer.append(line)
        joined = "\n".join(buffer).rstrip()
        if joined.endswith(delimiter):
            statement = joined[: -len(delimiter)].strip()
            if statement:
                statements.append(statement)
            buffer = []

    tail = "\n".join(buffer).strip()
    if tail:
        statements.append(tail)
    return statements


def run_file(cursor, path: Path) -> int:
    statements = split_sql_script(path.read_text(encoding="utf-8"))
    for statement in statements:
        cursor.execute(statement)
    return len(statements)


def main() -> None:
    config = {
        "host": os.getenv("CAMPUSHIRE_DB_HOST", "localhost"),
        "port": int(os.getenv("CAMPUSHIRE_DB_PORT", "3306")),
        "user": os.getenv("CAMPUSHIRE_DB_USER", "root"),
        "password": os.getenv("CAMPUSHIRE_DB_PASSWORD", "vasu1234"),
    }

    try:
        conn = mysql.connector.connect(**config, autocommit=True)
    except Error as exc:
        raise SystemExit(f"Could not connect to MySQL: {exc}")

    cursor = conn.cursor()
    try:
        try:
            cursor.execute("SET GLOBAL log_bin_trust_function_creators = 1")
        except Error:
            pass  # optional, needs elevated privileges

        for filename in FILES:
            path = SQL_DIR / filename
            if not path.exists():
                raise SystemExit(f"Missing SQL file: {path}")
            count = run_file(cursor, path)
            print(f"[ok] {filename:<15} {count:>3} statements")

        cursor.execute(f"USE {DB_NAME}")
        cursor.execute("SELECT COUNT(*) FROM app_user")
        users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM job")
        jobs = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM placement WHERE is_active = 1")
        placements = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM application")
        applications = cursor.fetchone()[0]

        print(f"\nDatabase '{DB_NAME}' ready:")
        print(f"  users={users}  jobs={jobs}  applications={applications}  placements={placements}")
        print("\nDemo logins (password: password123)")
        print("  student    student1@campus.edu")
        print("  recruiter  hr@apexquantum.com")
        print("  officer    meera.iyer@campushire.edu")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
