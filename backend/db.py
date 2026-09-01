import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# In production: set DATABASE_URL env var to your Postgres connection string.
# In CI (Playwright job) or local dev without Postgres: falls back to SQLite.
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "sqlite:///./finguard_dev.db"
)

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
