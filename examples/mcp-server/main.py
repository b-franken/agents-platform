"""Helpdesk Knowledge Base — MCP server example.

Exposes the helpdesk knowledge base as an MCP server that any
MCP-compatible client (including agents on this platform) can connect to.

Usage::

    uv run python examples/mcp-server/main.py
    # MCP server on http://localhost:8100/mcp

Then connect from an agent via the factory::

    tools = ["mcp:helpdesk-kb:http://localhost:8100/mcp"]
"""

from __future__ import annotations

import os
from pathlib import Path

import uvicorn
import yaml
from mcp.server.fastmcp import FastMCP

KNOWLEDGE_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "agents"
    / "helpdesk"
    / "knowledge"
)

mcp = FastMCP("helpdesk-kb")


def _load_articles() -> list[dict[str, str]]:
    articles: list[dict[str, str]] = []
    if not KNOWLEDGE_DIR.exists():
        return articles
    for path in sorted(KNOWLEDGE_DIR.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and "id" in data:
            articles.append(data)
    return articles


ARTICLES = _load_articles()


@mcp.tool()
def search_knowledge_base(query: str) -> str:
    """Search the IT knowledge base for solutions to common problems."""
    query_words = query.lower().split()
    scored = []
    for article in ARTICLES:
        searchable = f"{article.get('title', '')} {article.get('keywords', '')}".lower()
        score = sum(1 for word in query_words if word in searchable)
        if score > 0:
            scored.append((article, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    matches = scored[:3]

    if not matches:
        return "No matching articles found."

    lines: list[str] = []
    for article, _ in matches:
        lines.append(
            f"[{article['id']}] {article['title']}\n"
            f"Solution: {article.get('solution', 'No solution available.')}"
        )
    return "\n\n".join(lines)


@mcp.tool()
def list_articles() -> str:
    """List all available knowledge base articles."""
    if not ARTICLES:
        return "No articles available."
    return "\n".join(
        f"[{a['id']}] {a['title']}" for a in ARTICLES
    )


if __name__ == "__main__":
    port = int(os.getenv("MCP_PORT", "8100"))
    print(f"Helpdesk KB MCP server on http://localhost:{port}/mcp")
    uvicorn.run(
        mcp.streamable_http_app(),
        host="0.0.0.0",
        port=port,
    )
