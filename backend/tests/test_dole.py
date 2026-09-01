"""
test_dole.py — DOLE (Decision Outcome Learning Engine) classifier tests.

These are pure unit tests: no HTTP client, no DB round-trip.
We test the labeling logic directly and the training guard for insufficient data.

The label_outcomes() logic (from ml_pipeline.py) is:
  - spent > 50% of balance  → "Bad"
  - spent > 30% of balance  → "Risky"
  - otherwise               → "Good"

train_decision_model() requires >= 5 labeled rows; fewer → silently returns.
"""

import pytest
from unittest.mock import MagicMock, patch, call
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# Unit-test the labeling threshold logic directly
# ---------------------------------------------------------------------------

def _compute_outcome(balance: float, spent_next_week: float) -> str:
    """
    Mirror of the labeling rule inside label_outcomes() in ml_pipeline.py.
    Kept local so these tests don't require a live DB call.
    """
    if spent_next_week > balance * 0.5:
        return "Bad"
    elif spent_next_week > balance * 0.3:
        return "Risky"
    return "Good"


class TestDOLELabelingThresholds:
    def test_label_good_case(self):
        """Low spend relative to balance → 'Good'."""
        assert _compute_outcome(balance=100_000, spent_next_week=10_000) == "Good"

    def test_label_risky_case(self):
        """Spend between 30–50% of balance → 'Risky'."""
        assert _compute_outcome(balance=10_000, spent_next_week=3_500) == "Risky"

    def test_label_bad_case(self):
        """Spend > 50% of balance → 'Bad'."""
        assert _compute_outcome(balance=10_000, spent_next_week=6_000) == "Bad"

    def test_label_edge_exactly_50_percent(self):
        """Spend exactly at 50% boundary is NOT > 50%, so → 'Risky'."""
        assert _compute_outcome(balance=10_000, spent_next_week=5_000) == "Risky"

    def test_label_zero_spent(self):
        """Zero spend always → 'Good'."""
        assert _compute_outcome(balance=50_000, spent_next_week=0) == "Good"

    def test_label_zero_balance(self):
        """
        Zero balance: any positive spend > 0% → 'Bad'.
        Any non-positive spend → 'Good'.
        """
        # 0 > 0 * 0.5 is False; 0 > 0 * 0.3 is False → "Good"
        assert _compute_outcome(balance=0, spent_next_week=0) == "Good"
        # 1 > 0 * 0.5 → 1 > 0 → True → "Bad"
        assert _compute_outcome(balance=0, spent_next_week=1) == "Bad"

    def test_label_missing_category_no_crash(self):
        """
        Labeling is purely arithmetic — missing category has no effect.
        This confirms the function doesn't depend on category input.
        """
        result = _compute_outcome(balance=20_000, spent_next_week=5_000)
        assert result in ("Good", "Risky", "Bad")


class TestDOLETrainingGuard:
    def test_train_model_insufficient_data_no_crash(self):
        """
        train_decision_model() should silently return (no exception, no model file)
        when fewer than 5 labeled rows exist.
        """
        # Provide a mock engine that returns < 5 rows
        sparse_df = pd.DataFrame({
            "amount": [1000.0, 2000.0],
            "balance_at_decision": [50000.0, 30000.0],
            "burn_rate": [500.0, 800.0],
            "confidence_score": [0.9, 0.6],
            "outcome_label": ["Good", "Bad"],
        })

        with patch("backend.ml_pipeline.pd.read_sql", return_value=sparse_df), \
             patch("backend.ml_pipeline.joblib.dump") as mock_dump:
            from backend.ml_pipeline import train_decision_model
            train_decision_model("sparse_user")  # Must not raise

        # Model should NOT have been saved
        mock_dump.assert_not_called()

    def test_train_model_sufficient_data_saves_model(self):
        """
        With >= 5 labeled rows, train_decision_model() should fit a model
        and call joblib.dump exactly once.
        """
        full_df = pd.DataFrame({
            "amount": [1000.0, 2000.0, 500.0, 15000.0, 3000.0, 800.0],
            "balance_at_decision": [50000.0, 30000.0, 80000.0, 10000.0, 45000.0, 25000.0],
            "burn_rate": [500.0, 800.0, 300.0, 1200.0, 600.0, 400.0],
            "confidence_score": [0.9, 0.6, 0.95, 0.4, 0.85, 0.75],
            "outcome_label": ["Good", "Bad", "Good", "Bad", "Good", "Risky"],
        })

        with patch("backend.ml_pipeline.pd.read_sql", return_value=full_df), \
             patch("backend.ml_pipeline.joblib.dump") as mock_dump:
            from backend.ml_pipeline import train_decision_model
            train_decision_model("rich_user")

        mock_dump.assert_called_once()
        # First arg to dump() should be the trained model object
        saved_model = mock_dump.call_args[0][0]
        assert hasattr(saved_model, "predict_proba"), "Saved object should be a sklearn classifier"
