"""Tests for helpdesk agent tools."""

import sqlite3

from helpdesk.tools import (
    _DB_PATH,
    KB_ARTICLES,
    create_ticket,
    list_tickets,
    search_knowledge_base,
)


def _clean_db():
    """Remove test tickets."""
    if _DB_PATH.exists():
        conn = sqlite3.connect(_DB_PATH)
        conn.execute("DELETE FROM tickets")
        conn.commit()
        conn.close()


class TestKnowledgeBase:
    def test_kb_loaded_from_yaml(self):
        assert len(KB_ARTICLES) > 0

    def test_kb_articles_have_required_fields(self):
        for article in KB_ARTICLES:
            assert "id" in article
            assert "title" in article
            assert "keywords" in article
            assert "solution" in article

    def test_search_kb_vpn(self):
        result = search_knowledge_base("vpn connection")
        assert "VPN" in result

    def test_search_kb_no_results(self):
        result = search_knowledge_base("quantum entanglement")
        assert "No matching articles" in result


class TestTickets:
    def setup_method(self):
        _clean_db()

    def teardown_method(self):
        _clean_db()

    def test_create_ticket(self):
        result = create_ticket("VPN broken", "Cannot connect to VPN", "high")
        assert "Ticket created" in result
        assert "TKT-" in result
        assert "HIGH" in result

    def test_create_ticket_invalid_priority(self):
        result = create_ticket("Test", "Test desc", "urgent")
        assert "Invalid priority" in result

    def test_create_ticket_persists(self):
        create_ticket("Persist test", "Testing persistence", "low")
        result = list_tickets("all")
        assert "Persist test" in result

    def test_list_tickets_empty(self):
        result = list_tickets("all")
        assert "No tickets found" in result

    def test_list_tickets_filter(self):
        create_ticket("Open ticket", "desc", "medium")
        result = list_tickets("open")
        assert "Open ticket" in result
        result_resolved = list_tickets("resolved")
        assert "No tickets found" in result_resolved
