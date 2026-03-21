"""Create and seed the sample SQLite database."""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "company.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    department TEXT NOT NULL,
    role TEXT NOT NULL,
    start_date TEXT NOT NULL,
    salary INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    department TEXT NOT NULL,
    status TEXT NOT NULL,
    budget INTEGER NOT NULL,
    start_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    status TEXT NOT NULL,
    priority TEXT NOT NULL,
    assigned_to TEXT NOT NULL,
    created_at TEXT NOT NULL,
    resolved_at TEXT
);
"""

EMPLOYEES = [
    (1, "Lisa van den Berg", "Engineering", "Team Lead", "2020-03-15", 85000),
    (2, "Ahmed Khalil", "Engineering", "Backend Developer", "2021-06-01", 72000),
    (3, "Sophie Mulder", "Engineering", "Backend Developer", "2022-01-10", 68000),
    (4, "Daan Visser", "Engineering", "DevOps Engineer", "2021-09-01", 74000),
    (5, "Priya Sharma", "Engineering", "Frontend Developer", "2023-02-15", 65000),
    (6, "Mark de Vries", "Frontend", "Team Lead", "2019-11-01", 88000),
    (7, "Emma Jansen", "Frontend", "UX Designer", "2022-04-01", 62000),
    (8, "Youssef Amrani", "Frontend", "Frontend Developer", "2023-07-01", 60000),
    (9, "Chen Wei", "Data", "Team Lead", "2020-08-01", 90000),
    (10, "Fatima Hassan", "Data", "Data Engineer", "2021-03-15", 76000),
    (11, "Jan Willems", "Data", "Data Analyst", "2022-11-01", 64000),
    (12, "Olga Petrova", "Data", "ML Engineer", "2023-01-15", 78000),
    (13, "Tom Peters", "Sales", "Sales Manager", "2018-06-01", 82000),
    (14, "Nina de Boer", "Sales", "Account Executive", "2021-09-15", 58000),
    (15, "Carlos Mendez", "Sales", "Account Executive", "2022-05-01", 56000),
    (16, "Sarah Johnson", "HR", "HR Manager", "2019-01-15", 80000),
    (17, "Bas van Dijk", "HR", "Recruiter", "2023-03-01", 52000),
    (18, "Anna Kowalski", "Marketing", "Marketing Manager", "2020-02-01", 78000),
    (19, "James O'Brien", "Marketing", "Content Specialist", "2022-08-15", 54000),
    (20, "Maria Garcia", "Finance", "Finance Manager", "2019-07-01", 86000),
]

PROJECTS = [
    (1, "Cloud Migration", "Engineering", "in_progress", 250000, "2025-01-15"),
    (2, "Mobile App v2", "Frontend", "in_progress", 180000, "2025-03-01"),
    (3, "Data Lake", "Data", "completed", 320000, "2024-06-01"),
    (4, "CRM Integration", "Sales", "in_progress", 95000, "2025-06-01"),
    (5, "Brand Refresh", "Marketing", "completed", 45000, "2025-01-01"),
    (6, "API Gateway", "Engineering", "planning", 120000, "2026-04-01"),
    (7, "ML Pipeline", "Data", "in_progress", 200000, "2025-09-01"),
    (8, "Intranet Redesign", "Frontend", "planning", 80000, "2026-06-01"),
]

TICKETS = [
    (
        1,
        "VPN disconnects frequently",
        "open",
        "high",
        "Daan Visser",
        "2026-03-01",
        None,
    ),
    (
        2,
        "Deploy pipeline stuck",
        "resolved",
        "critical",
        "Daan Visser",
        "2026-02-28",
        "2026-02-28",
    ),
    (
        3,
        "Landing page typo",
        "resolved",
        "low",
        "Emma Jansen",
        "2026-03-02",
        "2026-03-03",
    ),
    (4, "API latency spike", "open", "high", "Ahmed Khalil", "2026-03-05", None),
    (5, "Dashboard filter broken", "open", "medium", "Jan Willems", "2026-03-06", None),
    (
        6,
        "Email template rendering",
        "resolved",
        "medium",
        "Sophie Mulder",
        "2026-02-20",
        "2026-02-22",
    ),
    (
        7,
        "Database backup failed",
        "resolved",
        "critical",
        "Daan Visser",
        "2026-03-10",
        "2026-03-10",
    ),
    (8, "SSO login error", "open", "high", "Ahmed Khalil", "2026-03-12", None),
    (
        9,
        "Mobile app crash on iOS",
        "open",
        "critical",
        "Youssef Amrani",
        "2026-03-14",
        None,
    ),
    (
        10,
        "Slow query performance",
        "in_progress",
        "high",
        "Fatima Hassan",
        "2026-03-08",
        None,
    ),
    (11, "Missing translations", "open", "low", "James O'Brien", "2026-03-15", None),
    (
        12,
        "Payment gateway timeout",
        "resolved",
        "critical",
        "Sophie Mulder",
        "2026-03-01",
        "2026-03-02",
    ),
    (
        13,
        "Search index outdated",
        "resolved",
        "medium",
        "Fatima Hassan",
        "2026-02-25",
        "2026-02-26",
    ),
    (
        14,
        "User export CSV broken",
        "open",
        "medium",
        "Priya Sharma",
        "2026-03-16",
        None,
    ),
    (15, "CI flaky test", "in_progress", "low", "Ahmed Khalil", "2026-03-10", None),
    (
        16,
        "SSL certificate expiring",
        "resolved",
        "high",
        "Daan Visser",
        "2026-03-05",
        "2026-03-05",
    ),
    (
        17,
        "Memory leak in worker",
        "in_progress",
        "high",
        "Sophie Mulder",
        "2026-03-13",
        None,
    ),
    (18, "Logo wrong on print", "open", "low", "Anna Kowalski", "2026-03-17", None),
    (
        19,
        "New hire laptop setup",
        "resolved",
        "medium",
        "Daan Visser",
        "2026-03-11",
        "2026-03-12",
    ),
    (
        20,
        "Staging env down",
        "resolved",
        "critical",
        "Daan Visser",
        "2026-03-09",
        "2026-03-09",
    ),
    (21, "CORS error on API", "open", "medium", "Priya Sharma", "2026-03-18", None),
    (
        22,
        "Report generation slow",
        "open",
        "medium",
        "Olga Petrova",
        "2026-03-15",
        None,
    ),
    (
        23,
        "Broken link in docs",
        "resolved",
        "low",
        "James O'Brien",
        "2026-03-06",
        "2026-03-07",
    ),
    (
        24,
        "Data sync mismatch",
        "in_progress",
        "high",
        "Fatima Hassan",
        "2026-03-14",
        None,
    ),
    (
        25,
        "Button not clickable",
        "open",
        "medium",
        "Youssef Amrani",
        "2026-03-19",
        None,
    ),
]


def create_database(path: Path | None = None) -> Path:
    db_path = path or DB_PATH
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.executemany(
            "INSERT OR IGNORE INTO employees VALUES (?,?,?,?,?,?)",
            EMPLOYEES,
        )
        conn.executemany(
            "INSERT OR IGNORE INTO projects VALUES (?,?,?,?,?,?)",
            PROJECTS,
        )
        conn.executemany(
            "INSERT OR IGNORE INTO tickets VALUES (?,?,?,?,?,?,?)",
            TICKETS,
        )
        conn.commit()
    finally:
        conn.close()
    return db_path
