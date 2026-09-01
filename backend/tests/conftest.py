"""
conftest.py — Shared pytest fixtures for FINGUARD backend tests.

Critical design note:
  api.py does `from backend.db import SessionLocal, engine` at module load time.
  Both names are resolved into backend.api's namespace immediately.
  Patching backend.db.SessionLocal AFTER import has zero effect on already-bound
  names in api.py. We must patch `backend.api.SessionLocal` and `backend.api.engine`
  — the names as they exist in the api module's own namespace.
"""

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient


# ---------------------------------------------------------------------------
# SQLite test engine — uses a named in-memory DB with shared cache so that
# ALL connections (conftest setup + route handler calls) see the SAME database.
# "sqlite:///:memory:" creates a fresh empty DB per connection — unusable here.
# "sqlite:///file::memory:?cache=shared" shares one DB across connections.
# ---------------------------------------------------------------------------

SQLITE_URL = "sqlite:///file::memory:?cache=shared&uri=true"

_test_engine = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},
)

_TestSessionLocal = sessionmaker(bind=_test_engine, autocommit=False, autoflush=False)


def _create_tables(engine):
    """Create all tables needed by the FINGUARD API in the test database."""
    is_sqlite = engine.url.get_dialect().name == "sqlite"
    serial_type = "INTEGER PRIMARY KEY AUTOINCREMENT" if is_sqlite else "SERIAL PRIMARY KEY"

    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT
            )
        """))
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS expenses (
                id {serial_type},
                user_id TEXT NOT NULL,
                date TEXT NOT NULL,
                category TEXT,
                amount REAL NOT NULL,
                payment_mode TEXT,
                day_type TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                user_id TEXT PRIMARY KEY,
                income REAL,
                est_fixed_costs REAL,
                target_daily_spend REAL,
                current_balance REAL
            )
        """))
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS goals (
                id {serial_type},
                user_id TEXT,
                category TEXT,
                limit_amount REAL,
                period TEXT
            )
        """))
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS decisions (
                id {serial_type},
                user_id TEXT NOT NULL,
                decision_date TEXT NOT NULL,
                target_date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT,
                balance_at_decision REAL,
                burn_rate REAL,
                ai_verdict TEXT,
                confidence_score REAL,
                outcome_label TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """))
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS recommendations (
                id {serial_type},
                user_id TEXT,
                date TEXT,
                total_spend REAL,
                cluster INTEGER,
                anomaly INTEGER,
                recommendation TEXT
            )
        """))
        conn.commit()


_create_tables(_test_engine)


# ---------------------------------------------------------------------------
# Global Gemini mock — autouse so NO test ever hits the real Gemini API
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True, scope="session")
def mock_gemini_globally():
    """
    Patch google.genai.Client at session scope before any import resolves it.
    All tests in this session will use a MagicMock for Gemini calls.
    """
    mock_client = MagicMock()
    # Default: generate_content returns a mock with .text attribute
    mock_response = MagicMock()
    mock_response.text = '{"amount": 100, "category": "Food", "date": "2024-01-01"}'
    mock_client.return_value.models.generate_content.return_value = mock_response

    with patch("google.genai.Client", mock_client):
        yield mock_client


# ---------------------------------------------------------------------------
# TestClient fixture — patches the CORRECT namespace in api.py
# ---------------------------------------------------------------------------

@pytest.fixture()
def client(monkeypatch):
    """
    Returns a FastAPI TestClient wired to SQLite.

    Patching backend.api.SessionLocal and backend.api.engine (not backend.db.*)
    because api.py already bound those names at import time via:
        from backend.db import SessionLocal, engine
    """
    # Patch the names as they live in the api module namespace
    monkeypatch.setattr("backend.api.SessionLocal", _TestSessionLocal)
    monkeypatch.setattr("backend.api.engine", _test_engine)

    # Also patch ml_pipeline's engine reference (used by run_ml_pipeline)
    monkeypatch.setattr("backend.ml_pipeline.engine", _test_engine)
    monkeypatch.setattr("backend.ml_pipeline.SessionLocal", _TestSessionLocal)

    # Suppress startup event DB calls (it uses SessionLocal() directly)
    from backend.api import app
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


# ---------------------------------------------------------------------------
# Postgres integration fixture — skipped locally, active in CI
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def pg_engine():
    """
    Real Postgres engine for integration tests.
    Skipped unless TEST_DATABASE_URL env var is set (set by GitHub Actions).
    """
    import os
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL not set — skipping Postgres integration test")

    eng = create_engine(url)
    _create_tables(eng)
    yield eng
    # Teardown: drop the test tables after the session
    with eng.connect() as conn:
        for table in ["recommendations", "decisions", "goals", "expenses", "user_profiles", "users"]:
            conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
        conn.commit()
    eng.dispose()
