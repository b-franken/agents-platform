"""Legal advisor tools — mock data for demo purposes."""

from typing import Annotated

from agent_framework import tool
from pydantic import Field

COMPLIANCE_RULES: dict[str, dict[str, str]] = {
    "gdpr": {
        "name": "GDPR (General Data Protection Regulation)",
        "status": "Partially compliant",
        "details": (
            "Data processing agreements are in place. "
            "Cookie consent needs updating. "
            "Right-to-deletion workflow is implemented."
        ),
    },
    "hipaa": {
        "name": "HIPAA (Health Insurance Portability and Accountability Act)",
        "status": "Not applicable",
        "details": "The organization does not process protected health information.",
    },
    "sox": {
        "name": "SOX (Sarbanes-Oxley Act)",
        "status": "Compliant",
        "details": (
            "Financial reporting controls are in place. "
            "Audit trail is maintained. "
            "Last audit: Q4 2025 — no findings."
        ),
    },
    "pci-dss": {
        "name": "PCI DSS (Payment Card Industry Data Security Standard)",
        "status": "Compliant",
        "details": (
            "Cardholder data is encrypted at rest and in transit. "
            "Annual penetration testing completed."
        ),
    },
}

CONTRACT_TEMPLATES: dict[str, str] = {
    "nda": "Non-Disclosure Agreement — standard template, 2-year term, mutual.",
    "sla": "Service Level Agreement — 99.9% uptime, 4-hour response time.",
    "dpa": "Data Processing Agreement — GDPR-compliant, sub-processor list included.",
    "msa": "Master Service Agreement — standard terms, 1-year auto-renewal.",
}


@tool
def check_compliance(
    regulation: Annotated[
        str, Field(description="Regulation to check, e.g. 'GDPR', 'SOX', 'PCI-DSS'")
    ],
) -> str:
    """Check the organization's compliance status for a specific regulation."""
    rule = COMPLIANCE_RULES.get(regulation.lower())
    if not rule:
        available = ", ".join(COMPLIANCE_RULES)
        return f"No compliance data for '{regulation}'. Available: {available}"
    return (
        f"Compliance: {rule['name']}\n"
        f"  Status: {rule['status']}\n"
        f"  Details: {rule['details']}"
    )


@tool
def review_contract(
    contract_type: Annotated[
        str, Field(description="Contract type, e.g. 'NDA', 'SLA', 'DPA', 'MSA'")
    ],
) -> str:
    """Review a contract template and provide a summary."""
    template = CONTRACT_TEMPLATES.get(contract_type.lower())
    if not template:
        available = ", ".join(CONTRACT_TEMPLATES)
        return f"No template for '{contract_type}'. Available: {available}"
    return f"Contract review ({contract_type.upper()}): {template}"
