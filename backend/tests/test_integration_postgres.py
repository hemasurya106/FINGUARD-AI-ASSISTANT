"""
test_integration_postgres.py — Real Postgres integration test.

This test is the ONLY test that uses the GitHub Actions Postgres service container.
It is automatically skipped in local development unless TEST_DATABASE_URL is set.

Purpose: verify that an expense added via the API can be read back from a real
Postgres database — exercising the full stack (SQLAlchemy → Postgres → API response)
in a way that SQLite tests cannot, because Postgres has different type coercion,
transaction semantics, and serial primary key behavior.
"""

import pytest
import os
from unittest.mock import patch
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient


# pg_engine fixture is defined in conftest.py and is session-scoped.
# It automatically skips if TEST_DATABASE_URL is not set.

EXPENSE_PAYLOAD = {
    "user_id": "pg_integration_user",
    "date": "2024-07-20",
    "category": "Travel",
    "amount": 1200.0,
    "payment_mode": "Card",
    "day_type": "Weekend",
}


@pytest.fixture(scope="module")
def pg_client(pg_engine):
    """
    A TestClient wired to the real Postgres test engine.
    Patches backend.api.SessionLocal and backend.api.engine to use Postgres.
    """
    PGSession = sessionmaker(bind=pg_engine)

    # Import app AFTER patching so startup events don't try to use production DB
    with patch("backend.api.SessionLocal", PGSession), \
         patch("backend.api.engine", pg_engine), \
         patch("backend.ml_pipeline.engine", pg_engine), \
         patch("backend.ml_pipeline.SessionLocal", PGSession), \
         patch("backend.api.genai.Client"):

        from backend.api import app
        with TestClient(app, raise_server_exceptions=False) as client:
            yield client


class TestPostgresIntegration:
    def test_add_and_retrieve_expense_postgres(self, pg_client, pg_engine):
        """
        End-to-end round-trip against real Postgres:
          1. POST /add-expense with a valid payload
          2. GET /get-expenses and verify the inserted row is returned

        This catches issues that only appear on Postgres:
          - SERIAL vs AUTOINCREMENT primary keys
          - Strict type casting (e.g., TEXT vs VARCHAR)
          - Transaction isolation differences
        """
        with patch("backend.api.run_ml_pipeline"), \
             patch("backend.api.label_outcomes"), \
             patch("backend.api.train_decision_model"):
            add_resp = pg_client.post("/add-expense", json=EXPENSE_PAYLOAD)

        assert add_resp.status_code == 200, f"Add failed: {add_resp.text}"
        assert "Expense added" in add_resp.json().get("message", "")

        get_resp = pg_client.get(
            "/get-expenses",
            params={
                "user_id": EXPENSE_PAYLOAD["user_id"],
                "date": EXPENSE_PAYLOAD["date"],
            },
        )

        assert get_resp.status_code == 200
        rows = get_resp.json()
        assert len(rows) >= 1, "Expected at least one expense row after insert"

        match = next((r for r in rows if r["amount"] == EXPENSE_PAYLOAD["amount"]), None)
        assert match is not None, f"Inserted amount not found in response: {rows}"
        assert match["category"] == EXPENSE_PAYLOAD["category"]
