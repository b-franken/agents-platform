"""Data analyst tools — query a SQLite company database."""

from __future__ import annotations

import sqlite3
from typing import Annotated

from agent_framework import tool
from pydantic import Field

from .sample_db import DB_PATH, create_database


def _ensure_db() -> None:
    if not DB_PATH.exists():
        create_database()


def _connect() -> sqlite3.Connection:
    _ensure_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _get_table_names(conn: sqlite3.Connection) -> set[str]:
    """Return the set of actual table names in the database."""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    return {row["name"] for row in cursor.fetchall()}


def _validate_table_name(table_name: str, conn: sqlite3.Connection) -> str | None:
    """Validate table name against actual database tables.

    Returns an error message if invalid, None if valid.
    """
    allowed = _get_table_names(conn)
    if table_name not in allowed:
        return (
            f"Unknown table '{table_name}'. "
            f"Available tables: {', '.join(sorted(allowed))}"
        )
    return None


def _format_rows(
    rows: list[sqlite3.Row],
    max_rows: int = 50,
) -> str:
    if not rows:
        return "(no results)"

    columns = rows[0].keys()
    col_widths = {
        col: max(
            len(col),
            *(len(str(row[col])) for row in rows[:max_rows]),
        )
        for col in columns
    }

    header = " | ".join(col.ljust(col_widths[col]) for col in columns)
    separator = "-+-".join("-" * col_widths[col] for col in columns)
    data_lines = [
        " | ".join(str(row[col]).ljust(col_widths[col]) for col in columns)
        for row in rows[:max_rows]
    ]

    result = "\n".join([header, separator, *data_lines])
    if len(rows) > max_rows:
        result += f"\n... ({len(rows) - max_rows} more rows)"
    return result


@tool
def describe_tables() -> str:
    """Show all tables in the database with their columns and types."""
    conn = _connect()
    try:
        tables = sorted(_get_table_names(conn))

        parts: list[str] = []
        for table in tables:
            # table names come from sqlite_master, so they are safe
            cols = conn.execute(f"PRAGMA table_info([{table}])").fetchall()
            col_info = ", ".join(f"{c['name']} ({c['type']})" for c in cols)
            count = conn.execute(
                f"SELECT COUNT(*) as n FROM [{table}]"  # noqa: S608
            ).fetchone()["n"]
            parts.append(f"{table} ({count} rows): {col_info}")

        return "\n".join(parts)
    finally:
        conn.close()


@tool
def run_sql(
    sql: Annotated[
        str,
        Field(description="SQLite SELECT query to execute"),
    ],
) -> str:
    """Execute a read-only SQL query and return the results."""
    normalized = sql.strip().upper()
    if not normalized.startswith("SELECT"):
        return "Only SELECT queries are allowed (read-only access)."

    conn = _connect()
    try:
        rows = conn.execute(sql).fetchall()
        return _format_rows(list(rows))
    except sqlite3.Error as e:
        return f"SQL error: {e}"
    finally:
        conn.close()


@tool
def get_sample_rows(
    table_name: Annotated[
        str,
        Field(description="Table name to preview"),
    ],
    limit: Annotated[
        int,
        Field(description="Number of rows to show", default=5),
    ] = 5,
) -> str:
    """Show the first N rows of a table."""
    conn = _connect()
    try:
        error = _validate_table_name(table_name, conn)
        if error:
            return error
        rows = conn.execute(
            f"SELECT * FROM [{table_name}] LIMIT ?",  # noqa: S608
            (limit,),
        ).fetchall()
        return _format_rows(list(rows))
    except sqlite3.Error as e:
        return f"SQL error: {e}"
    finally:
        conn.close()
