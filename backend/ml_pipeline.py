import pandas as pd
from sqlalchemy import text
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import make_pipeline
from backend.db import engine, SessionLocal

def run_ml_pipeline(user_id: str):
    print(f"🚀 Starting ML Pipeline for User: {user_id}")

    # 1. Load User Data from DB
    query = text("SELECT date, category, amount, day_type FROM expenses WHERE user_id = :user_id ORDER BY date")
    df = pd.read_sql(query, engine, params={"user_id": user_id})

    if df.empty:
        print("⚠ No data found for user.")
        return

    df["date"] = pd.to_datetime(df["date"])

    # 2. Preprocessing & Aggregation
    daily = df.groupby("date").agg(
        total_spend=("amount", "sum"),
        food_spend=("amount", lambda x: x[df.loc[x.index, "category"] == "Food"].sum()),
        shopping_spend=("amount", lambda x: x[df.loc[x.index, "category"] == "Shopping"].sum()),
        weekend=("day_type", lambda x: 1 if x.iloc[0] == "Weekend" else 0)
    ).reset_index()

    daily.fillna(0, inplace=True)
    num_days = len(daily)
    print(f"📊 User has {num_days} days of data.")

    # Initialize columns with defaults
    daily["cluster"] = 0
    daily["anomaly"] = 1 # 1 is Normal in IsolationForest, -1 is Anomaly. We'll use 1 as default 'Safe'. 
    daily["recommendation"] = ""

    # --- STAGE 1: NEW USER (0-2 Days) ---
    if num_days < 3:
        print("🔵 Stage 1: New User logic")
        daily["recommendation"] = "Welcome! Keep adding daily expenses to unlock personalized insights."
        # For the very last day (today), maybe distinct message?
        daily.loc[daily.index[-1], "recommendation"] = "Great start! add a few more days of data to see patterns."

    # --- STAGE 2: EARLY USER (3-14 Days) ---
    elif 3 <= num_days < 15:
        print("🟡 Stage 2: Early User logic (Statistical)")
        avg_spend = daily["total_spend"].mean()
        
        def simple_heuristic(row):
            if row["total_spend"] > 2 * avg_spend:
                return f"Spending is significantly higher than your average (₹{int(avg_spend)})."
            elif row["total_spend"] > 1.5 * avg_spend:
                return "Spending is a bit high today. Keep an eye on it."
            else:
                return "Spending is within a healthy range based on your recent history."
        
        daily["recommendation"] = daily.apply(simple_heuristic, axis=1)
        # We don't set cluster/anomaly here (remain 0/1) as data is too sparse for ML.

    # --- STAGE 3: MATURE USER (15+ Days) ---
    else:
        print("🟢 Stage 3: Mature User logic (Full ML)")
        X = daily[["total_spend", "food_spend", "shopping_spend", "weekend"]]
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        # Clustering
        kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
        daily["cluster"] = kmeans.fit_predict(X_scaled) 
        
        # Ensure Cluster 1 is "High Spend"
        cluster_means = daily.groupby("cluster")["total_spend"].mean()
        if cluster_means.get(0, 0) > cluster_means.get(1, 0):
            daily["cluster"] = daily["cluster"].map({0: 1, 1: 0})

        # Anomaly Detection
        iso = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
        daily["anomaly"] = iso.fit_predict(X_scaled) # -1 is anomaly, 1 is normal

        # Recommendation Generation
        def ml_recommendation(row):
            if row["cluster"] == 1 and row["anomaly"] == -1:
                return "⚠ High-risk spending detected (Anomaly + High Cluster). Delayed non-essentials recommended."
            elif row["cluster"] == 1:
                return "High spending day detected."
            elif row["anomaly"] == -1:
                return "Unusual spending pattern detected."
            else:
                return "Spending is structured and within normal predictive range."

        daily["recommendation"] = daily.apply(ml_recommendation, axis=1)


    # 6. Save Recommendations to DB
    # First, delete existing recommendations for this user to avoid duplicates/stale data
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM recommendations WHERE user_id = :user_id"), {"user_id": user_id})
        
        # Prepare data for insertion
        recs_to_save = []
        for _, row in daily.iterrows():
            recs_to_save.append({
                "user_id": user_id,
                "date": row["date"].strftime("%Y-%m-%d"),
                "total_spend": row["total_spend"],
                "cluster": int(row["cluster"]),
                "anomaly": int(row["anomaly"]),
                "recommendation": row["recommendation"]
            })
        
        if recs_to_save:
            conn.execute(text("""
                INSERT INTO recommendations (user_id, date, total_spend, cluster, anomaly, recommendation)
                VALUES (:user_id, :date, :total_spend, :cluster, :anomaly, :recommendation)
            """), recs_to_save)
            conn.commit()

    print(f"✅ Saved {len(recs_to_save)} recommendations for User: {user_id}")

# --- DOLE: Decision Outcome Learning Engine ---

def label_outcomes(user_id: str):
    """Labels past decisions as Good/Bad based on subsequent spending."""
    print("🧠 DOLE: Labeling outcomes...")
    db = SessionLocal()
    
    # 1. Fetch simulation decisions > 7 days old that are unlabeled
    try:
        decisions_q = text("""
            SELECT id, decision_date, balance_at_decision 
            FROM decisions 
            WHERE user_id = :user_id 
            AND outcome_label IS NULL
            AND decision_date <= CURRENT_DATE - INTERVAL '7 days'
        """)
        decisions = db.execute(decisions_q, {"user_id": user_id}).fetchall()
        
        for d in decisions:
            d_id = d[0]
            d_date_str = d[1] # date object
            balance = d[2]
            
            # 2. Check expenses in the 7 days AFTER decision
            # Note: d_date_str is date, we might need to cast or format
            start_date = d_date_str
            end_date = start_date + timedelta(days=7)
            
            exp_q = text("""
                SELECT SUM(amount) FROM expenses 
                WHERE user_id = :user_id 
                AND date >= :start_date 
                AND date <= :end_date
            """)
            total_spent_next_week = db.execute(exp_q, {
                "user_id": user_id, 
                "start_date": start_date, 
                "end_date": end_date
            }).scalar() or 0.0
            
            # Simple Rule: If spent > 50% of balance (aggressive) or > 80% (safe), label Bad
            # Or if "High risk" days detected (we can query recommendations)
            
            outcome = "Good"
            if total_spent_next_week > (balance * 0.5):
                outcome = "Bad"
            elif total_spent_next_week > (balance * 0.3):
                outcome = "Risky"
                
            # Update Label
            update_q = text("UPDATE decisions SET outcome_label = :outcome WHERE id = :id")
            db.execute(update_q, {"outcome": outcome, "id": d_id})
            
        db.commit()
    except Exception as e:
        print(f"DOLE Labeling Error: {e}")
    finally:
        db.close()

def train_decision_model(user_id: str):
    """Trains a model to predict 'Bad' outcomes."""
    print("🧠 DOLE: Training model...")
    try:
        query = text("""
            SELECT amount, balance_at_decision, burn_rate, confidence_score, outcome_label
            FROM decisions
            WHERE user_id = :user_id 
            AND outcome_label IS NOT NULL
        """)
        df = pd.read_sql(query, engine, params={"user_id": user_id})
        
        if len(df) < 5:
            print("⚠ DOLE: Not enough labeled data to train.")
            return

        # Features & Target
        X = df[["amount", "balance_at_decision", "burn_rate", "confidence_score"]]
        # Target: 1 if Bad/Risky, 0 if Good
        y = df["outcome_label"].apply(lambda x: 1 if str(x).lower() in ["bad", "risky", "true"] else 0)
        
        from sklearn.ensemble import RandomForestClassifier
        model = RandomForestClassifier(n_estimators=50, min_samples_leaf=2, random_state=42)
        model.fit(X, y)
        
        # Save Model
        joblib.dump(model, "dole_model.pkl")
        print("✅ DOLE: Model trained and saved to dole_model.pkl")
        
    except Exception as e:
        print(f"DOLE Training Error: {e}")
