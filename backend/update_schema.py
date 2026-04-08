from sqlalchemy import create_engine, text
from backend.db import DATABASE_URL

engine = create_engine(DATABASE_URL)

def update_schema():
    with engine.connect() as conn:
        try:
            print("🔄 Adding 'cluster' column...")
            conn.execute(text("ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS cluster INTEGER;"))
            
            print("🔄 Adding 'anomaly' column...")
            conn.execute(text("ALTER TABLE recommendations ADD COLUMN IF NOT EXISTS anomaly INTEGER;"))
            
            conn.commit()
            print("✅ Schema updated successfully.")
        except Exception as e:
            print(f"❌ Error updating schema: {e}")

if __name__ == "__main__":
    update_schema()
