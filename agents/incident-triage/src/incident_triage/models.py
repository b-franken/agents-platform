"""Structured output models for incident classification."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Severity(str, Enum):
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


class IncidentClassification(BaseModel):
    """Structured classification of an incident, used as response_format."""

    severity: Severity = Field(description="Incident severity level")
    impact_area: str = Field(description="Area of impact (e.g., infrastructure, application, security)")
    affected_systems: list[str] = Field(description="List of affected systems or services")
    responsible_team: str = Field(description="Team responsible for resolution")
    suggested_runbook: str = Field(description="Name of the recommended runbook")
    estimated_resolution_time: str = Field(description="Estimated time to resolve (e.g., '30 minutes', '2 hours')")
