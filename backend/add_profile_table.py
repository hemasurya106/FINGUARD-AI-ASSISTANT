from sqlalchemy import create_engine, text
from backend.db import DATABASE_URL

engine = create_engine(DATABASE_URL)

def add_profile_table():
    with engine.connect() as conn:
        try:
            print("🔄 Creating 'user_profiles' table...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    income FLOAT,
                    est_fixed_costs FLOAT,
                    target_daily_spend FLOAT,
                    current_balance FLOAT
                );
            """))
            conn.commit()
            print("✅ User Profiles table created successfully.")
        except Exception as e:
            print(f"❌ Error creating table: {e}")

if __name__ == "__main__":
    add_profile_table()
