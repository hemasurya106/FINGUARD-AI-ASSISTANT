import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# Format: postgresql://USER:PASSWORD@localhost/DATABASE_NAME
# Default user is often 'postgres' with password 'postgres' or empty
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost/dealdetective")

# Create the engine
# pool_pre_ping=True helps reconnect if the DB connection drops
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()