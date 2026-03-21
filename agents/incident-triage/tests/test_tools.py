"""Tests for incident triage agent tools."""

from incident_triage.tools import (
    _incident_history,
    classify_incident,
    get_runbook,
    list_recent_incidents,
)


def _clear_history():
    _incident_history.clear()


class TestClassifyIncident:
    def setup_method(self):
        _clear_history()

    def teardown_method(self):
        _clear_history()

    def test_classify_incident_database(self):
        result = classify_incident("Database cluster is down, production outage")
        assert "P1" in result
        assert "infrastructure" in result
        assert "INC-" in result

    def test_classify_incident_network(self):
        result = classify_incident("Network latency is high, DNS resolution failing")
        assert "networking" in result
        assert "INC-" in result

    def test_classify_incident_security(self):
        result = classify_incident("Unauthorized access detected, possible security breach")
        assert "P1" in result
        assert "security" in result
        assert "Security Operations" in result

    def test_classify_incident_low_severity(self):
        result = classify_incident("Question about API documentation update")
        assert "P4" in result

    def test_classify_incident_records_history(self):
        classify_incident("Server outage in us-east-1")
        assert len(_incident_history) == 1
        assert _incident_history[0]["severity"] == "P1"


class TestGetRunbook:
    def test_get_runbook_known_type(self):
        result = get_runbook("database_outage")
        assert "Runbook: database_outage" in result
        assert "Check database cluster health" in result

    def test_get_runbook_security(self):
        result = get_runbook("security_breach")
        assert "Isolate affected systems" in result

    def test_get_runbook_unknown_type(self):
        result = get_runbook("alien_invasion")
        assert "Unknown incident type" in result
        assert "Available types:" in result


class TestListRecentIncidents:
    def setup_method(self):
        _clear_history()

    def teardown_method(self):
        _clear_history()

    def test_list_recent_incidents_empty(self):
        result = list_recent_incidents()
        assert "No incidents recorded" in result

    def test_list_recent_incidents_with_data(self):
        classify_incident("Database outage in production")
        classify_incident("API degradation on checkout service")
        result = list_recent_incidents(24)
        assert "INC-" in result
        assert "infrastructure" in result
