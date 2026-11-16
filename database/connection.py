"""Single MySQL connection factory.

Python only opens the connection and forwards calls to SQL. All business
rules, validation and aggregation live in the mysql/*.sql files.
"""

from __future__ import annotations

import os
import warnings

import mysql.connector
import streamlit as st
from mysql.connector import Error  # noqa: F401  (re-exported for callers)


def _config() -> dict:
    """Resolve connection settings: secrets -> environment -> defaults."""
    config = {
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "password": "vasu1234",
        "database": "campushire",
    }
    try:
        section = st.secrets["mysql"]
        config.update({key: section[key] for key in section})
    except Exception:
        pass
    config["host"] = os.getenv("CAMPUSHIRE_DB_HOST", config["host"])
    config["port"] = int(os.getenv("CAMPUSHIRE_DB_PORT", config["port"]))
    config["user"] = os.getenv("CAMPUSHIRE_DB_USER", config["user"])
    config["password"] = os.getenv("CAMPUSHIRE_DB_PASSWORD", config["password"])
    config["database"] = os.getenv("CAMPUSHIRE_DB_NAME", config["database"])
    return config


@st.cache_resource(show_spinner=False)
def get_connection() -> mysql.connector.MySQLConnection:
    """Cached connection; every statement runs with autocommit."""
    return mysql.connector.connect(**_config(), autocommit=True)


def _healthy_connection() -> mysql.connector.MySQLConnection:
    conn = get_connection()
    if not conn.is_connected():
        conn.reconnect(attempts=3, delay=1)
    return conn


def fetch_all(sql: str, params: tuple | None = None) -> list[dict]:
    cursor = _healthy_connection().cursor(dictionary=True)
    try:
        cursor.execute(sql, params or ())
        return cursor.fetchall()
    finally:
        cursor.close()


def fetch_one(sql: str, params: tuple | None = None) -> dict | None:
    cursor = _healthy_connection().cursor(dictionary=True)
    try:
        cursor.execute(sql, params or ())
        return cursor.fetchone()
    finally:
        cursor.close()


def execute(sql: str, params: tuple | None = None) -> int:
    """Run INSERT/UPDATE/DELETE and return the affected row count."""
    cursor = _healthy_connection().cursor()
    try:
        cursor.execute(sql, params or ())
        return cursor.rowcount
    finally:
        cursor.close()


def call_procedure(
    procedure: str,
    in_params: tuple = (),
    out_count: int = 0,
) -> tuple[list[dict], list]:
    """Call a stored procedure.

    Returns (rows_of_first_result_set, [out_param_values_in_order]).
    The last OUT parameter of every CampusHire procedure is a message.
    """
    conn = _healthy_connection()
    cursor = conn.cursor(dictionary=True)
    args = list(in_params) + [None] * out_count
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            returned = cursor.callproc(procedure, args)
            rows: list[dict] = []
            for result in cursor.stored_results():
                fetched = result.fetchall()
                if fetched:
                    rows = fetched

        outs: list = []
        if out_count:
            if isinstance(returned, dict) and returned:
                # Connector returns {proc_arg1: ..., proc_argN: ...} in order.
                outs = list(returned.values())[-out_count:]
            else:
                # Older connectors expose OUT values through session variables.
                for index in range(len(in_params), len(args)):
                    cursor.execute(f"SELECT @_{procedure}_{index} AS value")
                    row = cursor.fetchone()
                    outs.append(row["value"] if row else None)

        return rows, outs
    finally:
        cursor.close()


def message_of(outs: list) -> str:
    """Last OUT parameter is always the SUCCESS/ERROR message."""
    if not outs:
        return "ERROR: no response from database"
    return str(outs[-1] or "")


def server_info() -> dict | None:
    """Used by the UI footer/sidebar status badge."""
    try:
        return fetch_one("SELECT VERSION() AS version, DATABASE() AS db_name")
    except Exception:
        return None
