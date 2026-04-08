from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://localhost/pdis"
engine = create_engine(DATABASE_URL)

def init_db():
    with engine.connect() as conn:
        # Create users table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                email TEXT
            );
        """))
        
        # Create expenses table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS expenses (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(user_id),
                date TEXT NOT NULL,
                category TEXT,
                amount FLOAT,
                payment_mode TEXT,
                day_type TEXT
            );
        """))
        
        # Create recommendations table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS recommendations (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL REFERENCES users(user_id),
                date TEXT NOT NULL,
                total_spend FLOAT,
                cluster INTEGER,
                anomaly INTEGER,
                recommendation TEXT
            );
        """))
        
        conn.commit()
        print("✅ Tables created successfully.")

if __name__ == "__main__":
    init_db()
