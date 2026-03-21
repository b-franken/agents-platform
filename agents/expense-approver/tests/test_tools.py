"""Tests for expense approver tools."""

import sqlite3

from expense_approver.tools import (
    _DB_PATH,
    check_budget,
    list_expenses,
    submit_expense,
)


def _reset_db():
    """Reset database to seed state."""
    if _DB_PATH.exists():
        conn = sqlite3.connect(_DB_PATH)
        conn.execute("DELETE FROM expenses")
        for dept, spent in [
            ("engineering", 32450.00),
            ("marketing", 28900.00),
            ("sales", 15200.00),
            ("operations", 24100.00),
        ]:
            conn.execute(
                "UPDATE budgets SET spent = ? WHERE department = ?",
                (spent, dept),
            )
        conn.commit()
        conn.close()


class TestBudget:
    def setup_method(self):
        _reset_db()

    def test_check_budget_known(self):
        result = check_budget("engineering")
        assert "50,000.00" in result
        assert "Remaining" in result

    def test_check_budget_unknown(self):
        result = check_budget("finance")
        assert "Unknown department" in result
        assert "engineering" in result


class TestExpenses:
    def setup_method(self):
        _reset_db()

    def teardown_method(self):
        _reset_db()

    def test_submit_within_budget(self):
        result = submit_expense("sales", 100.00, "Team lunch")
        assert "APPROVED" in result
        assert "100.00" in result

    def test_submit_exceeds_budget(self):
        result = submit_expense("operations", 999999.00, "Gold-plated desk")
        assert "REJECTED" in result
        assert "exceeds" in result

    def test_submit_unknown_department(self):
        result = submit_expense("finance", 50.00, "Coffee")
        assert "Unknown department" in result

    def test_expense_persists(self):
        submit_expense("sales", 50.00, "Persistence test")
        result = list_expenses("sales")
        assert "Persistence test" in result
        assert "50.00" in result

    def test_list_expenses_empty(self):
        result = list_expenses("all")
        assert "No expenses found" in result

    def test_budget_updates_after_expense(self):
        submit_expense("sales", 1000.00, "Equipment")
        result = check_budget("sales")
        assert "16,200.00" in result  # 15200 + 1000 spent
