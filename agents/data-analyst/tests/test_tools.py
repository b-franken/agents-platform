"""Tests for data analyst agent tools."""

from data_analyst.tools import describe_tables, get_sample_rows, run_sql


def test_describe_tables():
    result = describe_tables()
    assert "employees" in result
    assert "projects" in result
    assert "tickets" in result


def test_run_sql_select():
    result = run_sql("SELECT COUNT(*) as cnt FROM employees")
    assert "cnt" in result


def test_run_sql_non_select():
    result = run_sql("DROP TABLE employees")
    assert "Only SELECT" in result or "not allowed" in result.lower()


def test_get_sample_rows():
    result = get_sample_rows("employees", 3)
    assert "employees" in result.lower() or "name" in result.lower()


def test_get_sample_rows_unknown_table():
    result = get_sample_rows("nonexistent", 5)
    assert "unknown table" in result.lower()
    assert "employees" in result.lower()  # suggests valid tables
