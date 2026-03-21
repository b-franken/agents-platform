"""Company knowledge search tools."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

from agent_framework import tool
from pydantic import Field

_KNOWLEDGE_DIR = Path(__file__).resolve().parents[2] / "knowledge"

DOCUMENT_INDEX: list[dict[str, str]] = [
    {
        "file": "company-handbook.md",
        "title": "Company Handbook",
        "description": (
            "Working hours, leave policy, sick leave, "
            "onboarding, dress code, company culture"
        ),
    },
    {
        "file": "it-policy.md",
        "title": "IT & Security Policy",
        "description": (
            "Password rules, VPN, BYOD, security, acceptable use, data classification"
        ),
    },
    {
        "file": "remote-work-policy.md",
        "title": "Remote Work Policy",
        "description": (
            "Work from home rules, equipment budget, "
            "availability expectations, hybrid schedule"
        ),
    },
]


def _load_document(filename: str) -> str | None:
    path = _KNOWLEDGE_DIR / filename
    if not path.is_file():
        return None
    return path.read_text(encoding="utf-8")


def _search_content(
    query: str,
    text: str,
    context_chars: int = 300,
) -> list[str]:
    query_lower = query.lower()
    text_lower = text.lower()
    results: list[str] = []
    words = query_lower.split()

    for word in words:
        start = 0
        while True:
            idx = text_lower.find(word, start)
            if idx == -1:
                break
            snippet_start = max(0, idx - context_chars // 2)
            snippet_end = min(len(text), idx + context_chars // 2)
            snippet = text[snippet_start:snippet_end].strip()
            if snippet not in results:
                results.append(snippet)
            start = idx + 1
            if len(results) >= 3:
                return results

    return results


@tool
def search_documents(
    query: Annotated[
        str,
        Field(
            description=(
                "Search query, e.g. 'remote work policy' or 'how many leave days'"
            ),
        ),
    ],
) -> str:
    """Search company documents for relevant information."""
    all_results: list[str] = []

    for doc in DOCUMENT_INDEX:
        content = _load_document(doc["file"])
        if content is None:
            continue

        snippets = _search_content(query, content)
        if snippets:
            all_results.extend(
                f"[{doc['title']}]\n...{snippet}..." for snippet in snippets
            )

    if not all_results:
        query_lower = query.lower()
        for doc in DOCUMENT_INDEX:
            if any(w in doc["description"].lower() for w in query_lower.split()):
                all_results.extend(
                    [
                        f"[{doc['title']}] — "
                        f"This document may be relevant: "
                        f"{doc['description']}"
                    ]
                )

    if not all_results:
        return "No matching content found in company documents."

    return "\n\n".join(all_results[:5])


@tool
def list_available_documents() -> str:
    """List all available company documents."""
    return "\n".join(
        f"- {doc['title']}: {doc['description']}" for doc in DOCUMENT_INDEX
    )
