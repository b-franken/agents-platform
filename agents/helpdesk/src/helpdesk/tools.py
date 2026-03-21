"""IT helpdesk tools — KB search and ticket management."""

from __future__ import annotations

import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import yaml
from agent_framework import tool
from pydantic import Field

# --- Knowledge Base (loaded from YAML files) ---

_KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent.parent / "knowledge"


def _load_kb_articles() -> list[dict[str, str]]:
    """Load KB articles from YAML files in the knowledge/ directory."""
    articles: list[dict[str, str]] = []
    if not _KNOWLEDGE_DIR.exists():
        return articles
    for path in sorted(_KNOWLEDGE_DIR.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "id" in data:
            articles.append(data)
    return articles


KB_ARTICLES: list[dict[str, str]] = _load_kb_articles()

# --- Ticket Database (SQLite) ---

_DB_PATH = Path(__file__).resolve().parent / "tickets.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tickets (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    priority TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'OPEN',
    created_at TEXT NOT NULL
);
"""


def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(_SCHEMA)
    return conn


# --- Tools ---


def _score_article(article: dict[str, str], query: str) -> int:
    query_words = query.lower().split()
    searchable = (f"{article.get('title', '')} {article.get('keywords', '')}").lower()
    return sum(1 for word in query_words if word in searchable)


@tool
def search_knowledge_base(
    query: Annotated[
        str,
        Field(description="Search query describing the IT problem"),
    ],
) -> str:
    """Search the IT knowledge base for solutions to common problems."""
    scored = [(article, _score_article(article, query)) for article in KB_ARTICLES]
    matches = sorted(
        [(a, s) for a, s in scored if s > 0],
        key=lambda x: x[1],
        reverse=True,
    )[:3]

    if not matches:
        return "No matching articles found. Consider creating a support ticket."

    lines: list[str] = []
    for article, _score in matches:
        lines.append(
            f"[{article['id']}] {article['title']}\n"
            f"Solution: {article.get('solution', 'No solution available.')}"
        )
    return "\n\n".join(lines)


@tool(approval_mode="always_require")
def create_ticket(
    title: Annotated[str, Field(description="Short title for the ticket")],
    description: Annotated[str, Field(description="Detailed description of the issue")],
    priority: Annotated[
        str,
        Field(description="Priority: low, medium, high, critical"),
    ],
) -> str:
    """Create an IT support ticket. Requires human approval."""
    valid_priorities = {"low", "medium", "high", "critical"}
    if priority.lower() not in valid_priorities:
        return (
            f"Invalid priority '{priority}'. Use: {', '.join(sorted(valid_priorities))}"
        )

    ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
    timestamp = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC")

    conn = _get_db()
    try:
        conn.execute(
            "INSERT INTO tickets (id, title, description, priority, "
            "status, created_at) VALUES (?, ?, ?, ?, 'OPEN', ?)",
            (ticket_id, title, description, priority.upper(), timestamp),
        )
        conn.commit()
    finally:
        conn.close()

    return (
        f"Ticket created successfully.\n"
        f"ID: {ticket_id}\n"
        f"Title: {title}\n"
        f"Priority: {priority.upper()}\n"
        f"Created: {timestamp}\n"
        f"Status: OPEN\n"
        f"A technician will be assigned shortly."
    )


@tool
def list_tickets(
    status_filter: Annotated[
        str,
        Field(
            description="Filter by status: all, open, resolved",
            default="all",
        ),
    ] = "all",
) -> str:
    """List IT support tickets, optionally filtered by status."""
    conn = _get_db()
    try:
        query = "SELECT * FROM tickets"
        params: tuple[str, ...] = ()
        if status_filter.lower() != "all":
            query += " WHERE status = ?"
            params = (status_filter.upper(),)
        query += " ORDER BY created_at DESC"
        rows = conn.execute(query, params).fetchall()

        if not rows:
            return "No tickets found."

        lines = [
            f"[{row['id']}] {row['title']} "
            f"({row['priority']}, {row['status']}, "
            f"{row['created_at']})"
            for row in rows
        ]
        return "\n".join(lines)
    finally:
        conn.close()
