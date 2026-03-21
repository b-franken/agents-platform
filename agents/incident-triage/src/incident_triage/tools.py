"""Incident triage tools — classification, runbooks, and history."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Annotated

from agent_framework import tool
from pydantic import Field

# --- Keyword mappings for deterministic classification ---

_SEVERITY_KEYWORDS: dict[str, list[str]] = {
    "P1": [
        "outage",
        "down",
        "unavailable",
        "critical",
        "breach",
        "data loss",
        "production down",
    ],
    "P2": [
        "degraded",
        "slow",
        "intermittent",
        "partial",
        "high latency",
        "errors spiking",
    ],
    "P3": ["minor", "cosmetic", "workaround", "low impact", "single user"],
    "P4": ["question", "request", "enhancement", "documentation", "informational"],
}

_IMPACT_KEYWORDS: dict[str, list[str]] = {
    "infrastructure": [
        "database",
        "server",
        "network",
        "dns",
        "load balancer",
        "disk",
        "cpu",
        "memory",
    ],
    "application": [
        "api",
        "deployment",
        "service",
        "endpoint",
        "timeout",
        "error rate",
        "500",
    ],
    "security": [
        "breach",
        "unauthorized",
        "vulnerability",
        "exploit",
        "credentials",
        "leaked",
    ],
    "networking": [
        "network",
        "dns",
        "connectivity",
        "latency",
        "packet loss",
        "firewall",
    ],
}

_TEAM_MAPPING: dict[str, str] = {
    "infrastructure": "Platform Engineering",
    "application": "Application Support",
    "security": "Security Operations",
    "networking": "Network Operations",
}

_RUNBOOK_MAPPING: dict[str, str] = {
    "infrastructure": "database_outage",
    "application": "api_degradation",
    "security": "security_breach",
    "networking": "network_issue",
}

# --- Runbook definitions ---

_RUNBOOKS: dict[str, list[str]] = {
    "database_outage": [
        "1. Check database cluster health and replication status",
        "2. Verify connection pool utilization",
        "3. Review slow query logs for the last 15 minutes",
        "4. Check disk space and IOPS metrics",
        "5. If replica lag > 30s, initiate failover procedure",
        "6. Notify dependent service owners via #incidents channel",
    ],
    "network_issue": [
        "1. Run connectivity checks between affected zones",
        "2. Verify DNS resolution for internal and external domains",
        "3. Check firewall rules for recent changes",
        "4. Review BGP peering status with upstream providers",
        "5. Inspect load balancer health checks and traffic distribution",
        "6. Escalate to network vendor if issue persists beyond 30 minutes",
    ],
    "deployment_failure": [
        "1. Check CI/CD pipeline logs for the failed deployment",
        "2. Verify container image availability in the registry",
        "3. Review Kubernetes pod events and restart counts",
        "4. Compare configuration diff between current and previous release",
        "5. Initiate rollback if health checks fail after 10 minutes",
        "6. Post-mortem: update deployment checklist with root cause",
    ],
    "security_breach": [
        "1. Isolate affected systems from the network immediately",
        "2. Rotate all credentials and API keys for compromised services",
        "3. Capture forensic snapshots of affected instances",
        "4. Review audit logs for unauthorized access patterns",
        "5. Notify CISO and initiate incident response plan",
        "6. Engage external forensics team if data exfiltration is confirmed",
    ],
    "api_degradation": [
        "1. Check error rates and p99 latency in monitoring dashboard",
        "2. Review recent deployments for correlation with degradation onset",
        "3. Inspect upstream dependency health (databases, caches, queues)",
        "4. Scale horizontally if CPU/memory utilization exceeds 80%",
        "5. Enable circuit breakers for non-critical downstream calls",
        "6. Communicate status to API consumers via status page",
    ],
}

# --- In-memory incident store ---

_incident_history: list[dict[str, str]] = []


def _match_severity(description: str) -> str:
    text = description.lower()
    for severity, keywords in _SEVERITY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return severity
    return "P3"


def _match_impact_area(description: str) -> str:
    text = description.lower()
    best_area = "application"
    best_score = 0
    for area, keywords in _IMPACT_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > best_score:
            best_score = score
            best_area = area
    return best_area


# --- Tools ---


@tool
def classify_incident(
    description: Annotated[
        str,
        Field(description="Description of the incident to classify"),
    ],
) -> str:
    """Classify an incident based on its description and record it in history."""
    severity = _match_severity(description)
    impact_area = _match_impact_area(description)
    team = _TEAM_MAPPING.get(impact_area, "Platform Engineering")
    runbook = _RUNBOOK_MAPPING.get(impact_area, "api_degradation")

    resolution_times = {
        "P1": "1 hour",
        "P2": "4 hours",
        "P3": "24 hours",
        "P4": "72 hours",
    }
    est_time = resolution_times[severity]

    incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
    timestamp = datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC")

    _incident_history.append(
        {
            "id": incident_id,
            "description": description,
            "severity": severity,
            "impact_area": impact_area,
            "team": team,
            "runbook": runbook,
            "created_at": timestamp,
        }
    )

    return (
        f"Incident classified.\n"
        f"ID: {incident_id}\n"
        f"Severity: {severity}\n"
        f"Impact area: {impact_area}\n"
        f"Responsible team: {team}\n"
        f"Suggested runbook: {runbook}\n"
        f"Estimated resolution time: {est_time}\n"
        f"Recorded at: {timestamp}"
    )


@tool
def get_runbook(
    incident_type: Annotated[
        str,
        Field(
            description="Type of incident: database_outage, network_issue, "
            "deployment_failure, security_breach, api_degradation"
        ),
    ],
) -> str:
    """Retrieve runbook steps for a specific incident type."""
    steps = _RUNBOOKS.get(incident_type)
    if steps is None:
        available = ", ".join(sorted(_RUNBOOKS.keys()))
        return f"Unknown incident type '{incident_type}'. Available types: {available}"
    return f"Runbook: {incident_type}\n\n" + "\n".join(steps)


@tool
def list_recent_incidents(
    hours: Annotated[
        int,
        Field(description="Number of hours to look back", default=24),
    ] = 24,
) -> str:
    """List recent incidents from the in-memory history."""
    if not _incident_history:
        return "No incidents recorded."

    now = datetime.now(tz=UTC)
    lines: list[str] = []
    for incident in reversed(_incident_history):
        created = datetime.strptime(
            incident["created_at"], "%Y-%m-%d %H:%M UTC"
        ).replace(tzinfo=UTC)
        age_hours = (now - created).total_seconds() / 3600
        if age_hours <= hours:
            lines.append(
                f"[{incident['id']}] "
                f"{incident['severity']} — "
                f"{incident['impact_area']} — "
                f"{incident['description'][:80]} "
                f"({incident['created_at']})"
            )

    if not lines:
        return f"No incidents in the last {hours} hour(s)."
    return "\n".join(lines)
