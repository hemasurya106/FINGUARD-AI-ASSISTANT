"""
test_expenses.py — Expense CRUD endpoint tests.

Covers:
  - POST /add-expense  (success, missing field, invalid amount)
  - GET  /get-expenses (empty result, result after add)
"""

import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_EXPENSE = {
    "user_id": "test_user",
    "date": "2024-06-15",
    "category": "Food",
    "amount": 250.0,
    "payment_mode": "UPI",
    "day_type": "Weekday",
}


def _add_expense(client, overrides=None):
    payload = {**VALID_EXPENSE, **(overrides or {})}
    return client.post("/add-expense", json=payload)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestAddExpense:
    def test_add_expense_success(self, client):
        """Valid expense payload returns 200 and confirmation message."""
        # Suppress ML pipeline side-effects (they try to read lots of data)
        with patch("backend.api.run_ml_pipeline"), \
             patch("backend.api.label_outcomes"), \
             patch("backend.api.train_decision_model"):
            resp = client.post("/add-expense", json=VALID_EXPENSE)

        assert resp.status_code == 200
        body = resp.json()
        assert "Expense added" in body["message"]

    def test_add_expense_missing_amount(self, client):
        """Missing required 'amount' field → 422 Unprocessable Entity."""
        payload = {k: v for k, v in VALID_EXPENSE.items() if k != "amount"}
        resp = client.post("/add-expense", json=payload)
        assert resp.status_code == 422

    def test_add_expense_invalid_amount_string(self, client):
        """Non-numeric 'amount' value → 422 Unprocessable Entity."""
        resp = client.post("/add-expense", json={**VALID_EXPENSE, "amount": "two-fifty"})
        assert resp.status_code == 422

    def test_add_expense_missing_user_id(self, client):
        """Missing required 'user_id' field → 422 Unprocessable Entity."""
        payload = {k: v for k, v in VALID_EXPENSE.items() if k != "user_id"}
        resp = client.post("/add-expense", json=payload)
        assert resp.status_code == 422

    def test_add_expense_negative_amount(self, client):
        """
        Negative amounts are technically valid floats; the endpoint currently
        accepts them (no domain-level validation). This test documents that
        behavior — update if validation is added later.
        """
        with patch("backend.api.run_ml_pipeline"), \
             patch("backend.api.label_outcomes"), \
             patch("backend.api.train_decision_model"):
            resp = client.post("/add-expense", json={**VALID_EXPENSE, "amount": -50.0})
        # Document current behavior: no 4xx, amount stored as-is
        assert resp.status_code == 200


class TestGetExpenses:
    def test_get_expenses_empty_db(self, client):
        """GET /get-expenses for a user with no data returns an empty list."""
        resp = client.get("/get-expenses", params={"user_id": "nobody_user", "date": "2024-01-01"})
        assert resp.status_code == 200
        assert resp.json() == []

    def test_get_expenses_returns_added_entry(self, client):
        """After adding an expense, GET returns it for the same user+date."""
        with patch("backend.api.run_ml_pipeline"), \
             patch("backend.api.label_outcomes"), \
             patch("backend.api.train_decision_model"):
            add_resp = client.post("/add-expense", json=VALID_EXPENSE)
        assert add_resp.status_code == 200

        get_resp = client.get(
            "/get-expenses",
            params={"user_id": VALID_EXPENSE["user_id"], "date": VALID_EXPENSE["date"]},
        )
        assert get_resp.status_code == 200
        rows = get_resp.json()
        assert len(rows) >= 1
        # Verify the returned row matches what we inserted
        match = next((r for r in rows if r["amount"] == VALID_EXPENSE["amount"]), None)
        assert match is not None, f"Expected amount {VALID_EXPENSE['amount']} not found in {rows}"
        assert match["category"] == VALID_EXPENSE["category"]
