from app.database import SessionLocal
from app.models import PriceAlert
from sqlalchemy import text

def clear_alerts():
    db = SessionLocal()
    try:
        # Delete all alerts
        num_deleted = db.query(PriceAlert).delete()
        db.commit()
        
        # Reset ID sequence (optional, for postgres)
        try:
             db.execute(text("TRUNCATE TABLE price_alerts RESTART IDENTITY CASCADE;"))
             db.commit()
             print("✅ Truncated table and reset IDs.")
        except Exception:
             print(f"✅ Deleted {num_deleted} alerts.")

    except Exception as e:
        print(f"❌ Error clearing alerts: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    clear_alerts()
