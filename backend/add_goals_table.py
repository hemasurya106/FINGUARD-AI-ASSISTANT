from sqlalchemy import create_engine, text
from backend.db import DATABASE_URL

engine = create_engine(DATABASE_URL)

def add_goals_table():
    with engine.connect() as conn:
        try:
            print("🔄 Creating 'goals' table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS goals (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT,
                    category TEXT,
                    limit_amount FLOAT,
                    period TEXT
                );
            """))
            conn.commit()
            print("✅ Goals table created successfully.")
        except Exception as e:
            print(f"❌ Error creating table: {e}")

if __name__ == "__main__":
    add_goals_table()
