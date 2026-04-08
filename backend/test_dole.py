
from sqlalchemy import text
from datetime import date, timedelta
from backend.db import SessionLocal

def inject_past_decision(user_id="test_user"):
    db = SessionLocal()
    
    # 1. Create a "Past Decision" (8 days ago)
    # Scenario: Prediction was "Safe", but we will spend a lot to make it "Bad"
    past_date = date.today() - timedelta(days=8)
    
    print(f"Injecting past decision for {user_id} on {past_date}...")
    
    query = text("""
        INSERT INTO decisions 
        (user_id, decision_date, target_date, amount, category, 
         balance_at_decision, burn_rate, ai_verdict, confidence_score, outcome_label)
        VALUES 
        (:user_id, :d_date, :t_date, 5000, 'Test', 
         50000, 1000, 'Safe', 0.9, NULL)
    """)
    
    db.execute(query, {
        "user_id": user_id,
        "d_date": past_date,
        "t_date": date.today(),
    })
    db.commit()
    db.close()
    print("✅ Injected 'Past Decision' (Safe). Now add expenses to trigger labeling!")

if __name__ == "__main__":
    # You can change the user_id if needed, using a default for safety
    inject_past_decision(user_id="user_2r9k7x...") # Replace with your actual user_id if known, or generic
