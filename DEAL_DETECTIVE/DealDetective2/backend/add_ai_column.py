import sqlalchemy
from sqlalchemy import create_engine, text
from app.database import SQLALCHEMY_DATABASE_URL

def add_column():
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE products ADD COLUMN ai_analysis JSON DEFAULT '{}'::json;"))
            conn.commit()
            print("✅ Successfully added 'ai_analysis' column to 'products' table.")
        except Exception as e:
            if "duplicate column" in str(e).lower():
                print("ℹ️ Column 'ai_analysis' already exists.")
            else:
                print(f"❌ Error adding column: {e}")

if __name__ == "__main__":
    add_column()
