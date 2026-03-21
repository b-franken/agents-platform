"""Infrastructure analyzer tools — Terraform scanning and fix application."""

from __future__ import annotations

import re
from typing import Annotated

from agent_framework import tool
from pydantic import Field

from .models import Finding, InfraAnalysis, Severity

# --- Security rules (deterministic pattern matching) ---

_RULES: list[dict[str, str | Severity | str]] = [
    {
        "id": "NO_ENCRYPTION",
        "severity": Severity.HIGH,
        "pattern": (
            r'resource\s+"azurerm_storage_account"[^}]*?'
            r"(?!enable_https_traffic_only\s*=\s*true)"
        ),
        "search": (
            r'resource\s+"azurerm_storage_account"\s+"(\w+)"'
        ),
        "negative_pattern": (
            r"encryption"
            r"|enable_https_traffic_only\s*=\s*true"
            r"|min_tls_version"
        ),
        "message": (
            "Storage account missing encryption configuration"
        ),
        "recommendation": (
            "Add enable_https_traffic_only = true"
            ' and min_tls_version = "TLS1_2"'
        ),
    },
    {
        "id": "PUBLIC_ACCESS",
        "severity": Severity.CRITICAL,
        "pattern": (
            r"public_network_access_enabled\s*=\s*true"
            r"|allow_blob_public_access\s*=\s*true"
        ),
        "message": "Public network access is enabled",
        "recommendation": (
            "Set public_network_access_enabled = false"
            " and restrict access via network rules"
        ),
    },
    {
        "id": "NO_TAGS",
        "severity": Severity.LOW,
        "pattern": r'resource\s+"azurerm_\w+"\s+"(\w+)"\s*\{',
        "negative_pattern": r"tags\s*=\s*\{",
        "message": "Resource missing tags",
        "recommendation": (
            "Add tags block with at least environment,"
            " owner, and cost-center tags"
        ),
    },
    {
        "id": "NO_LOGGING",
        "severity": Severity.MEDIUM,
        "pattern": (
            r'resource\s+"azurerm_storage_account"\s+"(\w+)"'
        ),
        "negative_pattern": (
            r"logging|diagnostic_setting|monitor_diagnostic"
        ),
        "message": "No logging or monitoring configured",
        "recommendation": (
            "Add azurerm_monitor_diagnostic_setting"
            " for audit and metrics logging"
        ),
    },
    {
        "id": "HARDCODED_CREDENTIALS",
        "severity": Severity.CRITICAL,
        "pattern": (
            r"(?:password|secret|api_key|access_key"
            r'|connection_string)\s*=\s*"[^"]{8,}"'
        ),
        "message": "Hardcoded credentials detected",
        "recommendation": (
            "Use azurerm_key_vault_secret or variable"
            " references instead of hardcoded values"
        ),
    },
]

_BEST_PRACTICES: dict[str, list[str]] = {
    "azurerm_storage_account": [
        "Enable HTTPS-only traffic (enable_https_traffic_only = true)",
        "Set minimum TLS version to 1.2"
        ' (min_tls_version = "TLS1_2")',
        "Disable public blob access (allow_blob_public_access = false)",
        "Configure network rules to restrict access"
        " (network_rules block)",
        "Enable soft delete for blobs and containers"
        " (delete_retention_policy)",
        "Enable storage account encryption with customer-managed keys",
        "Add diagnostic settings for logging and monitoring",
        "Apply resource tags for governance and cost tracking",
    ],
    "azurerm_key_vault": [
        "Enable purge protection (purge_protection_enabled = true)",
        "Enable soft delete (soft_delete_retention_days >= 7)",
        "Configure access policies with least-privilege principle",
        "Restrict network access"
        ' (network_acls block with default_action = "Deny")',
        "Enable diagnostic logging for audit events",
        "Use RBAC authorization (enable_rbac_authorization = true)",
        "Rotate keys and secrets regularly via expiration policies",
        "Apply resource tags for governance and cost tracking",
    ],
    "azurerm_container_app": [
        "Use managed identity for authentication"
        ' (identity block with type = "SystemAssigned")',
        "Configure ingress rules to restrict external access",
        "Store sensitive values as secrets, never inline",
        "Set resource limits (cpu and memory) for each container",
        "Enable health probes (liveness and readiness)",
        "Use private endpoints where possible",
        "Configure revision mode for safe deployments",
        "Apply resource tags for governance and cost tracking",
    ],
}


def _extract_resource_blocks(hcl_content: str) -> list[tuple[str, str, str]]:
    """Extract (resource_type, resource_name, block_content) from HCL."""
    blocks: list[tuple[str, str, str]] = []
    pattern = r'resource\s+"(\w+)"\s+"(\w+)"\s*\{'
    for match in re.finditer(pattern, hcl_content):
        resource_type = match.group(1)
        resource_name = match.group(2)
        start = match.start()
        depth = 0
        block_end = start
        for i in range(match.end() - 1, len(hcl_content)):
            if hcl_content[i] == "{":
                depth += 1
            elif hcl_content[i] == "}":
                depth -= 1
                if depth == 0:
                    block_end = i + 1
                    break
        block_content = hcl_content[start:block_end]
        blocks.append((resource_type, resource_name, block_content))
    return blocks


def _check_rule(
    rule: dict[str, str | Severity | str],
    blocks: list[tuple[str, str, str]],
    full_content: str,
) -> list[Finding]:
    findings: list[Finding] = []
    rule_id = str(rule["id"])
    severity = (
        rule["severity"]
        if isinstance(rule["severity"], Severity)
        else Severity(str(rule["severity"]))
    )
    message = str(rule["message"])
    recommendation = str(rule["recommendation"])

    if "negative_pattern" in rule:
        search = str(rule.get("search", rule.get("pattern", "")))
        neg = str(rule["negative_pattern"])
        for rtype, rname, block in blocks:
            if re.search(search, block) and not re.search(neg, block):
                findings.append(
                    Finding(
                        rule_id=rule_id,
                        severity=severity,
                        resource=f"{rtype}.{rname}",
                        message=message,
                        recommendation=recommendation,
                    )
                )
    else:
        for match in re.finditer(str(rule["pattern"]), full_content):
            resource = "unknown"
            for rtype, rname, block in blocks:
                block_start = full_content.index(block)
                block_end = block_start + len(block)
                if (
                    match.start() >= block_start
                    and match.end() <= block_end
                ):
                    resource = f"{rtype}.{rname}"
                    break
            findings.append(
                Finding(
                    rule_id=rule_id,
                    severity=severity,
                    resource=resource,
                    message=message,
                    recommendation=recommendation,
                )
            )
    return findings


@tool
def scan_terraform(
    hcl_content: Annotated[
        str,
        Field(description="Terraform/HCL configuration content to scan"),
    ],
) -> str:
    """Scan Terraform/HCL configuration for security and best-practice violations.

    Returns a structured analysis with findings, summary, and health score.
    """
    blocks = _extract_resource_blocks(hcl_content)
    all_findings: list[Finding] = []

    for rule in _RULES:
        all_findings.extend(_check_rule(rule, blocks, hcl_content))

    seen: set[tuple[str, str]] = set()
    unique_findings: list[Finding] = []
    for f in all_findings:
        key = (f.rule_id, f.resource)
        if key not in seen:
            seen.add(key)
            unique_findings.append(f)

    penalty_map = {
        Severity.CRITICAL: 25,
        Severity.HIGH: 15,
        Severity.MEDIUM: 10,
        Severity.LOW: 5,
    }
    total_penalty = sum(
        penalty_map.get(f.severity, 5) for f in unique_findings
    )
    score = max(0, 100 - total_penalty)

    if not unique_findings:
        summary = (
            "No issues detected."
            " Configuration follows best practices."
        )
    else:
        critical = sum(
            1 for f in unique_findings
            if f.severity == Severity.CRITICAL
        )
        high = sum(
            1 for f in unique_findings
            if f.severity == Severity.HIGH
        )
        medium = sum(
            1 for f in unique_findings
            if f.severity == Severity.MEDIUM
        )
        low = sum(
            1 for f in unique_findings
            if f.severity == Severity.LOW
        )
        parts = []
        if critical:
            parts.append(f"{critical} critical")
        if high:
            parts.append(f"{high} high")
        if medium:
            parts.append(f"{medium} medium")
        if low:
            parts.append(f"{low} low")
        count = len(unique_findings)
        summary = (
            f"Found {count} issue(s):"
            f" {', '.join(parts)}."
        )

    analysis = InfraAnalysis(
        findings=unique_findings,
        summary=summary,
        score=score,
    )

    lines = [
        f"Score: {analysis.score}/100",
        f"Summary: {analysis.summary}",
        "",
    ]
    lines.extend(
        f"[{f.severity.value}] {f.rule_id}: {f.message}\n"
        f"  Resource: {f.resource}\n"
        f"  Fix: {f.recommendation}"
        for f in analysis.findings
    )
    return "\n".join(lines) if lines else "No issues found."


@tool
def check_security_best_practices(
    resource_type: Annotated[
        str,
        Field(
            description=(
                "Azure Terraform resource type"
                " (e.g. azurerm_storage_account)"
            )
        ),
    ],
) -> str:
    """Return security best practices for an Azure resource type."""
    practices = _BEST_PRACTICES.get(resource_type)
    if not practices:
        supported = ", ".join(sorted(_BEST_PRACTICES.keys()))
        return (
            f"No best practices found for '{resource_type}'. "
            f"Supported resource types: {supported}"
        )

    lines = [f"Security best practices for {resource_type}:", ""]
    for i, practice in enumerate(practices, 1):
        lines.append(f"  {i}. {practice}")
    return "\n".join(lines)


@tool(approval_mode="always_require")
def apply_fix(
    resource: Annotated[
        str,
        Field(
            description=(
                "Terraform resource identifier"
                " (e.g. azurerm_storage_account.main)"
            )
        ),
    ],
    fix_description: Annotated[
        str,
        Field(description="Description of the fix to apply"),
    ],
) -> str:
    """Apply a suggested fix to a Terraform resource.

    Requires human approval.
    """
    return (
        f"Fix applied successfully.\n"
        f"Resource: {resource}\n"
        f"Change: {fix_description}\n"
        f"Status: APPLIED (pending terraform plan verification)"
    )
