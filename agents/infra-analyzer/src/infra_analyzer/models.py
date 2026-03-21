"""Structured output models for infrastructure analysis."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class Severity(StrEnum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class Finding(BaseModel):
    rule_id: str = Field(
        description="Unique identifier for the rule that was violated"
    )
    severity: Severity = Field(description="Severity level of the finding")
    resource: str = Field(
        description=(
            "The Terraform resource where the issue was found"
        )
    )
    message: str = Field(description="Human-readable description of the issue")
    recommendation: str = Field(description="Suggested fix for the issue")


class InfraAnalysis(BaseModel):
    findings: list[Finding] = Field(default_factory=list)
    summary: str = Field(description="Overall summary of the analysis")
    score: int = Field(
        ge=0, le=100, description="Infrastructure health score (0-100)"
    )
