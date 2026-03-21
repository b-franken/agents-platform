"""Tests for code-reviewer agent tools."""

from code_reviewer.tools import (
    analyze_code_quality,
    check_security_patterns,
    suggest_improvements,
)


class TestAnalyzeCodeQuality:
    def test_detects_bare_except(self):
        code = """\
try:
    risky()
except:
    pass
"""
        result = analyze_code_quality(code)
        assert "Bare 'except:'" in result
        assert "WARNING" in result

    def test_detects_mutable_default(self):
        code = """\
def add_item(item, items=[]):
    items.append(item)
    return items
"""
        result = analyze_code_quality(code)
        assert "Mutable default" in result
        assert "ERROR" in result

    def test_detects_unused_import(self):
        code = """\
import os
import sys

print(sys.argv)
"""
        result = analyze_code_quality(code)
        assert "os" in result
        assert "unused" in result.lower()

    def test_detects_missing_type_hint(self):
        code = """\
def greet(name):
    return f"Hello, {name}"
"""
        result = analyze_code_quality(code)
        assert "name" in result
        assert "type hint" in result.lower()

    def test_clean_code_no_issues(self):
        code = """\
def greet(name: str) -> str:
    return f"Hello, {name}"
"""
        result = analyze_code_quality(code)
        assert result == "No quality issues found."

    def test_unsupported_language(self):
        result = analyze_code_quality("console.log('hi')", language="javascript")
        assert "not yet supported" in result


class TestCheckSecurityPatterns:
    def test_detects_sql_injection(self):
        code = """\
def get_user(name):
    cursor.execute(f"SELECT * FROM users WHERE name = '{name}'")
"""
        result = check_security_patterns(code)
        assert "SQL injection" in result
        assert "CRITICAL" in result

    def test_detects_hardcoded_secret(self):
        code = """\
db_password = "super_secret_123"
"""
        result = check_security_patterns(code)
        assert "Hardcoded credential" in result
        assert "CRITICAL" in result

    def test_detects_unsafe_eval(self):
        code = """\
result = eval(user_input)
"""
        result = check_security_patterns(code)
        assert "Unsafe call" in result
        assert "eval" in result

    def test_detects_pickle_loads(self):
        code = """\
import pickle
data = pickle.loads(raw_bytes)
"""
        result = check_security_patterns(code)
        assert "Unsafe call" in result
        assert "pickle.loads" in result

    def test_no_security_issues_clean_code(self):
        code = """\
def get_user(name: str) -> dict:
    cursor.execute("SELECT * FROM users WHERE name = ?", (name,))
    return cursor.fetchone()
"""
        result = check_security_patterns(code)
        assert result == "No security issues found."


class TestSuggestImprovements:
    def test_suggests_list_comprehension(self):
        code = """\
results = []
for x in items:
    results.append(x * 2)
"""
        result = suggest_improvements(code)
        assert "list comprehension" in result.lower()

    def test_suggests_context_manager(self):
        code = """\
f = open("data.txt")
try:
    data = f.read()
finally:
    f.close()
"""
        result = suggest_improvements(code)
        assert "context manager" in result.lower()

    def test_suggests_fstrings_over_format(self):
        code = """\
msg = "Hello, {}".format(name)
"""
        result = suggest_improvements(code)
        assert "f-string" in result.lower()

    def test_no_suggestions_clean_code(self):
        code = """\
def greet(name: str) -> str:
    return f"Hello, {name}"
"""
        result = suggest_improvements(code)
        assert result == "No improvement suggestions."
