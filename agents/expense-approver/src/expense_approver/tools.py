"""Tools for the expense approver agent.

Demonstrates the human-in-the-loop pattern using approval_mode.
Budgets and expenses are persisted in SQLite.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Annotated

from agent_framework import tool
from pydantic import Field

_DB_PATH = Path(__file__).resolve().parent / "expenses.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS budgets (
    department TEXT PRIMARY KEY,
    total REAL NOT NULL,
    spent REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    department TEXT NOT NULL,
    amount REAL NOT NULL,
    description TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (department) REFERENCES budgets(department)
);
"""

_SEED_DATA = [
    ("engineering", 50000.00, 32450.00),
    ("marketing", 30000.00, 28900.00),
    ("sales", 40000.00, 15200.00),
    ("operations", 25000.00, 24100.00),
]


def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    # Seed if empty
    count = conn.execute("SELECT COUNT(*) as n FROM budgets").fetchone()["n"]
    if count == 0:
        conn.executemany(
            "INSERT INTO budgets (department, total, spent) VALUES (?, ?, ?)",
            _SEED_DATA,
        )
        conn.commit()
    return conn


@tool
def check_budget(
    department: Annotated[
        str,
        Field(description="Department name, e.g. 'engineering'"),
    ],
) -> str:
    """Check the remaining budget for a department."""
    conn = _get_db()
    try:
        row = conn.execute(
            "SELECT * FROM budgets WHERE department = ?",
            (department.lower(),),
        ).fetchone()
        if not row:
            depts = conn.execute("SELECT department FROM budgets").fetchall()
            available = ", ".join(r["department"] for r in depts)
            return f"Unknown department '{department}'. Available: {available}"
        remaining = row["total"] - row["spent"]
        return (
            f"Budget for {department}:\n"
            f"  Total:     ${row['total']:,.2f}\n"
            f"  Spent:     ${row['spent']:,.2f}\n"
            f"  Remaining: ${remaining:,.2f}"
        )
    finally:
        conn.close()


@tool(approval_mode="always_require")
def submit_expense(
    department: Annotated[str, Field(description="Department name")],
    amount: Annotated[
        float,
        Field(description="Expense amount in USD", gt=0),
    ],
    description: Annotated[str, Field(description="What the expense is for")],
) -> str:
    """Submit an expense. Requires human approval before processing."""
    conn = _get_db()
    try:
        row = conn.execute(
            "SELECT * FROM budgets WHERE department = ?",
            (department.lower(),),
        ).fetchone()
        if not row:
            return f"Unknown department '{department}'."

        remaining = row["total"] - row["spent"]
        if amount > remaining:
            return (
                f"REJECTED: ${amount:,.2f} exceeds remaining "
                f"budget of ${remaining:,.2f} for {department}."
            )

        conn.execute(
            "UPDATE budgets SET spent = spent + ? WHERE department = ?",
            (amount, department.lower()),
        )
        conn.execute(
            "INSERT INTO expenses "
            "(department, amount, description, created_at) "
            "VALUES (?, ?, ?, datetime('now'))",
            (department.lower(), amount, description),
        )
        conn.commit()

        new_remaining = remaining - amount
        return (
            f"APPROVED: ${amount:,.2f} expense for "
            f"'{description}' in {department}.\n"
            f"Remaining budget: ${new_remaining:,.2f}"
        )
    finally:
        conn.close()


@tool
def list_expenses(
    department: Annotated[
        str,
        Field(
            description="Department name, or 'all' for everything",
            default="all",
        ),
    ] = "all",
) -> str:
    """List submitted expenses, optionally filtered by department."""
    conn = _get_db()
    try:
        query = "SELECT * FROM expenses"
        params: tuple[str, ...] = ()
        if department.lower() != "all":
            query += " WHERE department = ?"
            params = (department.lower(),)
        query += " ORDER BY created_at DESC"
        rows = conn.execute(query, params).fetchall()

        if not rows:
            return "No expenses found."

        lines = [
            f"${row['amount']:,.2f} — {row['description']} "
            f"({row['department']}, {row['created_at']})"
            for row in rows
        ]
        return "\n".join(lines)
    finally:
        conn.close()
