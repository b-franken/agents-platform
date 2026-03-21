"""Pre-flight check — verifies Azure resources are configured.

Usage::

    uv run python scripts/preflight.py
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

from dotenv import load_dotenv

REQUIRED_ENV_VARS: dict[str, str] = {
    "AZURE_AI_PROJECT_ENDPOINT": "Azure AI Foundry project endpoint",
    "AZURE_OPENAI_RESPONSES_DEPLOYMENT_NAME": "Model deployment name (e.g., gpt-4.1)",
}

REQUIRED_PACKAGES: dict[str, str] = {
    "agent_framework": "agent-framework",
    "azure.identity": "azure-identity",
    "dotenv": "python-dotenv",
    "pydantic": "pydantic",
}


@dataclass
class CheckResult:
    name: str
    errors: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.errors


def _check_packages() -> CheckResult:
    result = CheckResult(name="Python packages")
    for module, pip_name in REQUIRED_PACKAGES.items():
        try:
            __import__(module)
        except ImportError:
            result.errors.append(f"{pip_name} not found (pip install {pip_name})")
    return result


def _check_env_vars() -> CheckResult:
    result = CheckResult(name="Environment variables")
    for var, desc in REQUIRED_ENV_VARS.items():
        if not os.getenv(var):
            result.errors.append(f"{var} — {desc}")
    return result


def _check_auth() -> CheckResult:
    result = CheckResult(name="Azure authentication")
    if os.getenv("AZURE_OPENAI_API_KEY"):
        return result
    try:
        from azure.identity import AzureCliCredential

        AzureCliCredential().get_token("https://cognitiveservices.azure.com/.default")
    except ImportError:
        result.errors.append("azure-identity not installed")
    except Exception as exc:
        result.errors.append(f"Azure CLI auth failed: {exc}")
        result.errors.append("Run 'az login' or set AZURE_OPENAI_API_KEY in .env")
    return result


def main() -> None:
    load_dotenv()

    checks: list[Callable[[], CheckResult]] = [
        _check_packages,
        _check_env_vars,
        _check_auth,
    ]

    print("=" * 60)
    print("Agent Platform — Pre-flight Check")
    print("=" * 60)
    print()

    results = [check() for check in checks]
    for i, r in enumerate(results, 1):
        status = "OK" if r.passed else "FAIL"
        print(f"[{i}/{len(results)}] {r.name}: {status}")
        for err in r.errors:
            print(f"  - {err}")
        print()

    total_errors = sum(len(r.errors) for r in results)
    if total_errors:
        print(f"NOT READY — {total_errors} issue(s)")
        sys.exit(1)
    else:
        print("READY — All checks passed!")
        print("\n  uv run --package router-agent python -m router.main")


if __name__ == "__main__":
    main()
