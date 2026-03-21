"""Code review tools — quality analysis, security scanning, improvement suggestions."""

from __future__ import annotations

import re
from typing import Annotated

from agent_framework import tool
from pydantic import Field

# --- Quality Analysis Patterns ---

_BARE_EXCEPT = re.compile(r"^\s*except\s*:", re.MULTILINE)
_MUTABLE_DEFAULT = re.compile(
    r"def\s+\w+\s*\([^)]*(?::\s*\w+\s*)?=\s*(\[\]|\{\}|\bset\(\))", re.MULTILINE
)
_UNUSED_IMPORT = re.compile(r"^import\s+(\w+)|^from\s+\w+\s+import\s+(\w+)", re.MULTILINE)
_MISSING_TYPE_HINT = re.compile(r"def\s+\w+\s*\(([^)]*)\)\s*:", re.MULTILINE)
_FUNCTION_DEF = re.compile(r"^([ \t]*)def\s+\w+", re.MULTILINE)


def _find_long_functions(code: str, threshold: int = 30) -> list[str]:
    lines = code.split("\n")
    findings: list[str] = []
    for match in _FUNCTION_DEF.finditer(code):
        indent = len(match.group(1).replace("\t", "    "))
        start_line = code[: match.start()].count("\n")
        func_name = re.search(r"def\s+(\w+)", match.group())
        if not func_name:
            continue
        body_lines = 0
        for i in range(start_line + 1, len(lines)):
            line = lines[i]
            if line.strip() == "":
                body_lines += 1
                continue
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= indent and line.strip():
                break
            body_lines += 1
        if body_lines > threshold:
            findings.append(
                f"[WARNING] Function '{func_name.group(1)}' is {body_lines} lines long "
                f"(threshold: {threshold}). Consider splitting it."
            )
    return findings


def _find_unused_imports(code: str) -> list[str]:
    findings: list[str] = []
    for match in _UNUSED_IMPORT.finditer(code):
        name = match.group(1) or match.group(2)
        rest = code[match.end() :]
        if not re.search(rf"\b{re.escape(name)}\b", rest):
            findings.append(
                f"[INFO] Import '{name}' appears unused."
            )
    return findings


def _find_missing_type_hints(code: str) -> list[str]:
    findings: list[str] = []
    for match in _MISSING_TYPE_HINT.finditer(code):
        params = match.group(1).strip()
        if not params or params == "self" or params == "cls":
            continue
        for param in params.split(","):
            param = param.strip()
            if not param or param in ("self", "cls", "*", "/"):
                continue
            if param.startswith("*") or param.startswith("**"):
                param = param.lstrip("*")
            if ":" not in param and "=" not in param:
                findings.append(
                    f"[INFO] Parameter '{param.split('=')[0].strip()}' "
                    f"is missing a type hint."
                )
    return findings


@tool
def analyze_code_quality(
    code: Annotated[str, Field(description="Source code to analyze")],
    language: Annotated[
        str, Field(description="Programming language (e.g. python)")
    ] = "python",
) -> str:
    """Analyze code for common quality issues like unused imports, bare excepts, and mutable defaults."""
    if language.lower() != "python":
        return f"Language '{language}' is not yet supported. Currently supports: python."

    findings: list[str] = []

    for match in _BARE_EXCEPT.finditer(code):
        line_num = code[: match.start()].count("\n") + 1
        findings.append(
            f"[WARNING] Bare 'except:' at line {line_num}. "
            f"Catch specific exceptions instead."
        )

    for match in _MUTABLE_DEFAULT.finditer(code):
        line_num = code[: match.start()].count("\n") + 1
        findings.append(
            f"[ERROR] Mutable default argument '{match.group(1)}' at line {line_num}. "
            f"Use None and assign inside the function body."
        )

    findings.extend(_find_unused_imports(code))
    findings.extend(_find_missing_type_hints(code))
    findings.extend(_find_long_functions(code))

    if not findings:
        return "No quality issues found."
    return "\n".join(findings)


# --- Security Patterns ---

_SQL_INJECTION = re.compile(
    r"""(?:execute|cursor\.execute)\s*\(\s*(?:f["']|["'].*%s|["'].*\.format\()""",
    re.MULTILINE,
)
_HARDCODED_CREDS = re.compile(
    r"""(?:password|secret|api_key|apikey|token)\s*=\s*["'][^"']+["']""",
    re.IGNORECASE,
)
_UNSAFE_DESER = re.compile(
    r"\b(?:pickle\.loads?|eval|exec)\s*\(", re.MULTILINE
)


@tool
def check_security_patterns(
    code: Annotated[str, Field(description="Source code to scan for security issues")],
    language: Annotated[
        str, Field(description="Programming language (e.g. python)")
    ] = "python",
) -> str:
    """Scan code for security anti-patterns like SQL injection, hardcoded credentials, and unsafe deserialization."""
    if language.lower() != "python":
        return f"Language '{language}' is not yet supported. Currently supports: python."

    findings: list[str] = []

    for match in _SQL_INJECTION.finditer(code):
        line_num = code[: match.start()].count("\n") + 1
        findings.append(
            f"[CRITICAL] Potential SQL injection at line {line_num}. "
            f"Use parameterized queries instead."
        )

    for match in _HARDCODED_CREDS.finditer(code):
        line_num = code[: match.start()].count("\n") + 1
        findings.append(
            f"[CRITICAL] Hardcoded credential at line {line_num}. "
            f"Use environment variables or a secrets manager."
        )

    for match in _UNSAFE_DESER.finditer(code):
        line_num = code[: match.start()].count("\n") + 1
        func = match.group().rstrip("(").strip()
        findings.append(
            f"[CRITICAL] Unsafe call '{func}' at line {line_num}. "
            f"This can execute arbitrary code."
        )

    if not findings:
        return "No security issues found."
    return "\n".join(findings)


# --- Improvement Suggestions ---

_FOR_APPEND = re.compile(
    r"for\s+(\w+)\s+in\s+.+:\s*\n\s+\w+\.append\(", re.MULTILINE
)
_TRY_FINALLY_CLOSE = re.compile(
    r"try\s*:.*?finally\s*:\s*\n\s+\w+\.close\(\)", re.DOTALL
)
_FORMAT_CALL = re.compile(r'["\'].*["\']\.format\(')
_PERCENT_FORMAT = re.compile(r'["\'].*%[sd].*["\']\s*%\s*')
_STRING_CONCAT = re.compile(r'["\'].*["\']\s*\+\s*(?:str\()?')


@tool
def suggest_improvements(
    code: Annotated[str, Field(description="Source code to review for improvements")],
    language: Annotated[
        str, Field(description="Programming language (e.g. python)")
    ] = "python",
) -> str:
    """Suggest code improvements like list comprehensions, context managers, and f-strings."""
    if language.lower() != "python":
        return f"Language '{language}' is not yet supported. Currently supports: python."

    suggestions: list[str] = []

    if _FOR_APPEND.search(code):
        suggestions.append(
            "[SUGGESTION] Loop with .append() detected. "
            "Consider using a list comprehension for clarity and performance."
        )

    if _TRY_FINALLY_CLOSE.search(code):
        suggestions.append(
            "[SUGGESTION] try/finally with .close() detected. "
            "Consider using a context manager ('with' statement) instead."
        )

    if _FORMAT_CALL.search(code) or _PERCENT_FORMAT.search(code):
        suggestions.append(
            "[SUGGESTION] .format() or %-formatting detected. "
            "Consider using f-strings for readability."
        )

    if _STRING_CONCAT.search(code):
        suggestions.append(
            "[SUGGESTION] String concatenation detected. "
            "Consider using f-strings or str.join() instead."
        )

    if not suggestions:
        return "No improvement suggestions."
    return "\n".join(suggestions)
