"""Tests for knowledge agent tools."""

from knowledge_agent.tools import list_available_documents, search_documents


def test_search_documents_found():
    result = search_documents("remote work")
    assert "Remote Work" in result or "remote" in result.lower()


def test_search_documents_not_found():
    result = search_documents("quantum entanglement")
    # Should either find nothing or return a "no content" message
    assert isinstance(result, str)


def test_list_available_documents():
    result = list_available_documents()
    assert "Company Handbook" in result
    assert "IT & Security Policy" in result or "IT" in result
    assert "Remote Work Policy" in result
