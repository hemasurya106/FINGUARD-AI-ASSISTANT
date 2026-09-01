import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from datetime import date, timedelta
import joblib

DATABASE_URL = "postgresql://localhost/pdis"

def main():
    try:
        engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(bind=engine)
        db = SessionLocal()
        print("Connected to DB successfully.")
    except Exception as e:
        print(f"Failed to connect to DB: {e}")
        return

    user_id = "eval_user"
    
    # Check if table exists
    try:
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS decisions (
                id SERIAL PRIMARY KEY,
                user_id TEXT NOT NULL,
                decision_date DATE NOT NULL,
                target_date DATE NOT NULL,
                amount FLOAT NOT NULL,
                category TEXT,
                balance_at_decision FLOAT,
                burn_rate FLOAT,
                ai_verdict TEXT,
                confidence_score FLOAT,
                outcome_label TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        db.commit()
    except Exception as e:
        print(f"Error creating table: {e}")

    try:
        # Clear old data for this user
        db.execute(text("DELETE FROM decisions WHERE user_id = :uid"), {"uid": user_id})
        db.commit()

        # Generate Synthetic Data (50 samples)
        print("Generating 100 synthetic decisions...")
        np.random.seed(42)
        decisions = []
        for i in range(100):
            amount = np.random.uniform(500, 30000)
            balance = np.random.uniform(1000, 100000)
            burn_rate = np.random.uniform(500, 5000)
            
            coverage = balance / amount if amount > 0 else 1.0
            confidence = min(1.0, max(0.0, coverage / 2))
            
            # Simulated outcome rule
            is_bad = 0
            # Let's say if amount > 0.4 * balance or burn_rate is very high relative to balance, it's bad
            if amount > 0.4 * balance or (burn_rate * 7 > balance * 0.5):
                is_bad = 1
                
            # Add some noise
            if np.random.rand() < 0.1:
                is_bad = 1 - is_bad
                
            label = "Bad" if is_bad else "Good"
            
            decisions.append({
                "user_id": user_id,
                "amount": amount,
                "balance": balance,
                "burn_rate": burn_rate,
                "confidence": confidence,
                "label": label
            })
            
        for d in decisions:
            db.execute(text("""
                INSERT INTO decisions 
                (user_id, decision_date, target_date, amount, category, balance_at_decision, burn_rate, ai_verdict, confidence_score, outcome_label)
                VALUES 
                (:uid, CURRENT_DATE, CURRENT_DATE, :amt, 'Test', :balance, :burn_rate, 'Safe', :conf, :label)
            """), {
                "uid": user_id, 
                "amt": d["amount"],
                "balance": d["balance"],
                "burn_rate": d["burn_rate"],
                "conf": d["confidence"],
                "label": d["label"]
            })
        db.commit()
        print("Synthetic data injected.")

        # Train & Evaluate Model
        query = text("""
            SELECT amount, balance_at_decision, burn_rate, confidence_score, outcome_label
            FROM decisions
            WHERE user_id = :user_id 
            AND outcome_label IS NOT NULL
        """)
        with engine.connect() as conn:
            result = conn.execute(query, {"user_id": user_id})
            rows = result.fetchall()
            df = pd.DataFrame(rows, columns=["amount", "balance_at_decision", "burn_rate", "confidence_score", "outcome_label"])
        
        X = df[["amount", "balance_at_decision", "burn_rate", "confidence_score"]]
        y = df["outcome_label"].apply(lambda x: 1 if str(x).lower() in ["bad", "risky", "true"] else 0)
        
        # Split into train/test (80/20) for realistic metrics
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        model = RandomForestClassifier(n_estimators=50, min_samples_leaf=2, random_state=42)
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        
        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        
        print("\n--- METRICS ---")
        print(f"DOLE Model Accuracy: {acc * 100:.1f}%")
        print(f"DOLE Model F1-Score: {f1:.2f}")
        print("----------------\n")
        
    except Exception as e:
        print(f"Error during eval: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
