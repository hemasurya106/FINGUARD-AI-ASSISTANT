from fastapi import FastAPI, UploadFile, File
import pandas as pd
import time
import random
import io
import json
import re
from PIL import Image
import pytesseract
from google import genai
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.sql import text
from backend.db import SessionLocal, engine
from backend.db import SessionLocal, engine
from backend.ml_pipeline import run_ml_pipeline, label_outcomes, train_decision_model
import joblib
import pandas as pd
import numpy as np

from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv()) # Load variables from .env

app = FastAPI(title="PDIS API")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # Allows specific origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.on_event("startup")
def startup_db():
    # Detect dialect from the live engine — respects test patches on backend.api.engine
    is_sqlite = engine.dialect.name == "sqlite"
    serial_type = "INTEGER PRIMARY KEY AUTOINCREMENT" if is_sqlite else "SERIAL PRIMARY KEY"

    db = SessionLocal()
    db.execute(text(f"""
        CREATE TABLE IF NOT EXISTS decisions (
            id {serial_type},
            user_id TEXT NOT NULL,
            decision_date TEXT NOT NULL,
            target_date TEXT NOT NULL,
            amount FLOAT NOT NULL,
            category TEXT,
            balance_at_decision FLOAT,
            burn_rate FLOAT,
            ai_verdict TEXT,
            confidence_score FLOAT,
            outcome_label TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """))
    db.commit()
    db.close()
    print("✅ Startup: Decisions table checked/created.")


import os

# Get the directory of the current file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load data with absolute paths
# Removed CSV imports as we now use DB
from pydantic import BaseModel
from datetime import date, timedelta
import subprocess 

class Expense(BaseModel):
    user_id: str
    date: str
    category: str
    amount: float
    payment_mode: str
    day_type: str

class UserProfile(BaseModel):
    user_id: str
    income: float
    est_fixed_costs: float
    target_daily_spend: float
    current_balance: float

class SimulationRequest(BaseModel):
    user_id: str
    amount: float
    target_date: str

@app.post("/register-user")
def register_user(user: dict):
    db = SessionLocal()

    query = text("""
        INSERT INTO users (user_id, email)
        VALUES (:user_id, :email)
        ON CONFLICT (user_id) DO NOTHING
    """)

    db.execute(query, user)
    db.commit()
    db.close()

    return {"message": "User registered"}

@app.post("/scan-bill")
async def scan_bill(file: UploadFile = File(...)):
    print(f"Analyzing bill: {file.filename}")
    
    try:
        # 1. Read Image — wrapped in try so malformed files return graceful fallback
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
    except Exception as e:
        print(f"Image Read Error: {e}")
        return {
            "amount": 0,
            "category": "Extraction Failed",
            "date": str(date.today())
        }
    
    # Check for API Key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not found in environment")
        return {
            "amount": 0,
            "category": "Error: Missing GEMINI_API_KEY",
            "date": str(date.today())
        }

    client = genai.Client(api_key=api_key)
    
    prompt = f"""
    Analyze this bill image. Extract the following details into a JSON object:
    - amount: (float, the total amount)
    - category: (string, one of ['Food', 'Travel', 'Shopping', 'Entertainment'])
    - date: (string, YYYY-MM-DD format, today is {str(date.today())}. If date is missing, unclear, or > 30 days old, use today's date)

    Return ONLY raw JSON. No markdown.
    """
    
    try:
        # Send image directly to Gemini 2.5 Flash (1.5 not available)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, image]
        )
        
        raw_text = response.text.strip()
        print(raw_text)
        clean_json = raw_text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)
        
        return {
            "amount": data.get("amount", 0),
            "category": data.get("category", "Food"),
            "date": data.get("date", str(date.today()))
        }
    except Exception as e:
        print(f"Gemini Vision Error: {e}")
        return {
            "amount": 0,
            "category": "Extraction Failed",
            "date": str(date.today())
        }

@app.get("/get-expenses")
def get_expenses(user_id: str, date: str = None):
    if not date:
        date = str(time.strftime("%Y-%m-%d"))
        
    db = SessionLocal()
    query = text("""
        SELECT category, amount, payment_mode 
        FROM expenses 
        WHERE user_id = :user_id AND date = :date
        ORDER BY id DESC
    """)
    rows = db.execute(query, {"user_id": user_id, "date": date}).fetchall()
    db.close()
    
    return [
        {"category": row[0], "amount": row[1], "payment_mode": row[2]} 
        for row in rows
    ]

@app.post("/add-expense")
def add_expense(expense: Expense):
    db = SessionLocal()

    query = text("""
        INSERT INTO expenses
        (user_id, date, category, amount, payment_mode, day_type)
        VALUES
        (:user_id, :date, :category, :amount, :payment_mode, :day_type)
    """)

    db.execute(query, expense.dict())
    db.commit()
    db.close()

    # Run ML only for this user
    try:
        run_ml_pipeline(expense.user_id)
        # --- DOLE Learning Loop ---
        label_outcomes(expense.user_id)
        train_decision_model(expense.user_id)
    except Exception as e:
        print(f"ML Pipeline/DOLE Error: {e}")

    # Check against Goal
    goal_message = evaluate_goal(
        expense.user_id,
        expense.category,
        "daily"
    )

    return {
        "message": "Expense added and system updated",
        "goal_feedback": goal_message
    }

@app.post("/update-profile")
def update_profile(profile: UserProfile):
    db = SessionLocal()
    query = text("""
        INSERT INTO user_profiles (user_id, income, est_fixed_costs, target_daily_spend, current_balance)
        VALUES (:user_id, :income, :est_fixed_costs, :target_daily_spend, :current_balance)
        ON CONFLICT (user_id) DO UPDATE SET
            income = EXCLUDED.income,
            est_fixed_costs = EXCLUDED.est_fixed_costs,
            target_daily_spend = EXCLUDED.target_daily_spend,
            current_balance = EXCLUDED.current_balance
    """)
    db.execute(query, profile.dict())
    db.commit()
    db.close()
    return {"message": "Profile updated successfully"}

@app.get("/get-profile")
def get_profile(user_id: str):
    db = SessionLocal()
    query = text("SELECT * FROM user_profiles WHERE user_id = :user_id")
    row = db.execute(query, {"user_id": user_id}).fetchone()
    db.close()
    if row:
        return {
            "income": row[1],
            "est_fixed_costs": row[2],
            "target_daily_spend": row[3],
            "current_balance": row[4]
        }
    return {}

@app.post("/simulate")
def simulate_purchase(req: SimulationRequest):
    db = SessionLocal()
    
    # 1. Fetch Profile
    prof_q = text("SELECT * FROM user_profiles WHERE user_id = :user_id")
    profile = db.execute(prof_q, {"user_id": req.user_id}).fetchone()
    
    if not profile:
        db.close()
        return {"safe": False, "message": "Please set up your profile first."}

    # Profile values: 0=id, 1=income, 2=fixed, 3=daily_target, 4=balance
    est_fixed_costs = profile[2]
    target_daily = profile[3]
    current_balance = profile[4]

    # 2. Check Data Maturity (Hybrid Logic)
    count_q = text("SELECT COUNT(*) FROM expenses WHERE user_id = :user_id")
    tx_count = db.execute(count_q, {"user_id": req.user_id}).scalar()
    
    source = ""
    burn_rate = 0.0
    fixed_costs = 0.0
    
    if tx_count >= 15:
        # STAGE 2: Real Data
        # Calculate real daily average (burn rate)
        avg_q = text("SELECT SUM(amount) / COUNT(DISTINCT date) FROM expenses WHERE user_id = :user_id")
        real_avg = db.execute(avg_q, {"user_id": req.user_id}).scalar() or 0
        
        burn_rate = real_avg
        fixed_costs = est_fixed_costs # We still use estimated fixed costs unless we have a way to tag bills
        source = f"Based on your actual spending habits ({tx_count} transactions)..."
    else:
        # STAGE 1: Estimates
        burn_rate = target_daily
        fixed_costs = est_fixed_costs
        source = "Based on your profile estimates..."
        
    db.close()

    # 3. Calculation
    today = date.today()
    target_dt = date.fromisoformat(req.target_date)
    days_until = (target_dt - today).days
    
    if days_until < 0:
        return {"safe": False, "message": "Target date is in the past!"}

    projected_spend = (days_until * burn_rate) + (days_until * (fixed_costs / 30))
    future_balance = current_balance - projected_spend - req.amount
    
    is_safe = future_balance > 0
    emoji = "✅" if is_safe else "❌"

    # --- DOLE: ML Inference (The "Brain") ---
    ml_risk_prob = 0.0
    dole_override = False
    try:
        if os.path.exists("dole_model.pkl"):
            model = joblib.load("dole_model.pkl")
            coverage = future_balance / req.amount if req.amount > 0 else 1.0
            confidence_score = min(1.0, max(0.0, coverage / 2))
            
            features = np.array([[req.amount, current_balance, burn_rate, confidence_score]])
            ml_risk_prob = model.predict_proba(features)[0][1] # Prob of class 1 (Bad/Risky)
            
            if is_safe and ml_risk_prob > 0.6:
                is_safe = False
                dole_override = True
                source += " + DOLE Risk Model"
                print(f"DOLE: Overrode verdict to RISK (Prob: {ml_risk_prob:.2f})")
    except Exception as e:
        print(f"DOLE Inference Error: {e}")

    # 4. AI Explanation (Gemini)
    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    dole_context = ""
    if dole_override:
        dole_context = f"\n- ⚠️ SYSTEM OVERRIDE: While mathematically safe, the internal DOLE ML engine has overridden this to HIGH RISK (Probability: {ml_risk_prob:.2f}) due to past behavioral spending patterns. You MUST firmly warn the user against the purchase."

    prompt = f"""
    You are a financial advisor. A user asks: "Can I afford a ₹{req.amount} purchase by {req.target_date}?"
    
    Context:
    - Current Balance: ₹{current_balance}
    - Estimated Monthly Fixed Costs: ₹{fixed_costs}
    - Daily Burn Rate: ₹{burn_rate:.2f} ({source})
    - Days until purchase: {days_until}
    - Projected Expenses until then: ₹{projected_spend:.2f}
    - Predicted Future Balance (after purchase): ₹{future_balance:.2f}{dole_context}
    
    Is it Safe? {"YES" if is_safe else "NO"}
    
    Task:
    Write a short, helpful response (2 sentences max). 
    If unsafe or overridden by the ML, explain why (e.g., "The math looks okay, but our ML system detected this is a highly risky pattern...").
    If completely safe, give a green light but a small caution.
    Use emoji. Add a newline between the main verdict and the explanation.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=[prompt]
        )
        ai_message = response.text.strip()
    except Exception as e:
        print(f"LLM Error: {e}")
        ai_message = f"{emoji} {source} you will have ₹{int(future_balance)} left."

    # --- DOLE: Log Decision ---
    try:
        # Simple Confidence: 1.0 if balance covers 2x amount, linear decay otherwise
        coverage = future_balance / req.amount if req.amount > 0 else 1.0
        confidence_score = min(1.0, max(0.0, coverage / 2)) # Normalize 0-1
        
        db = SessionLocal()
        log_q = text("""
            INSERT INTO decisions (user_id, decision_date, target_date, amount, category, balance_at_decision, burn_rate, ai_verdict, confidence_score)
            VALUES (:user_id, CURRENT_DATE, :target_date, :amount, :category, :balance, :burn_rate, :verdict, :confidence)
        """)
        db.execute(log_q, {
            "user_id": req.user_id,
            "target_date": req.target_date,
            "amount": req.amount,
            "category": "Simulation", # Generic category for now
            "balance": current_balance,
            "burn_rate": burn_rate,
            "verdict": "Safe" if is_safe else "Risky",
            "confidence": confidence_score
        })
        db.commit()
        db.close()
        print(f"DOLE: Logged decision (Confidence: {confidence_score:.2f})")
    except Exception as e:
        print(f"DOLE Logging Error: {e}")
    # --------------------------

    return {
        "safe": is_safe,
        "future_balance": future_balance,
        "message": ai_message,
        "dole_risk_prob": ml_risk_prob
    }



@app.post("/set-goal")
def set_goal(goal: dict):
    db = SessionLocal()

    query = text("""
        INSERT INTO goals (user_id, category, limit_amount, period)
        VALUES (:user_id, :category, :limit_amount, :period)
    """)

    db.execute(query, goal)
    db.commit()
    db.close()

    return {"message": "Goal set successfully"}

def evaluate_goal(user_id, category, period):
    db = SessionLocal()

    # Fetch goal
    goal_q = text("""
        SELECT limit_amount FROM goals
        WHERE user_id = :user_id
        AND category = :category
        AND period = :period
        ORDER BY id DESC
        LIMIT 1
    """)
    goal = db.execute(goal_q, {
        "user_id": user_id,
        "category": category,
        "period": period
    }).fetchone()

    if not goal:
        db.close()
        return None

    limit_amount = goal[0]

    # Calculate spent amount
    spend_q = text("""
        SELECT COALESCE(SUM(amount), 0)
        FROM expenses
        WHERE user_id = :user_id
        AND category = :category
        AND date = CURRENT_DATE
    """)
    spent = db.execute(spend_q, {
        "user_id": user_id,
        "category": category
    }).scalar()

    db.close()

    if spent <= limit_amount:
        return f"✅ You are within your {category} budget today (₹{spent} / ₹{limit_amount})"
    else:
        excess = spent - limit_amount
        return f"❌ You exceeded your {category} budget by ₹{excess} today"

@app.get("/overview")
def get_overview(user_id: str):
    query = text("SELECT date, SUM(amount) as amount FROM expenses WHERE user_id = :user_id GROUP BY date ORDER BY date")
    df = pd.read_sql(query, engine, params={"user_id": user_id})
    return df.to_dict(orient="records")

@app.get("/clusters")
def get_clusters(user_id: str):
    # Cluster info is now in recommendations table or re-computed?
    # User step 8 says "Store recommendations per user" and includes cluster/anomaly in table.
    # So we query recommendations table.
    query = text("SELECT date, cluster FROM recommendations WHERE user_id = :user_id")
    df = pd.read_sql(query, engine, params={"user_id": user_id})
    return df.to_dict(orient="records")

@app.get("/recommendations")
def get_recommendations(user_id: str):
    query = text("SELECT * FROM recommendations WHERE user_id = :user_id ORDER BY date")
    df = pd.read_sql(query, engine, params={"user_id": user_id})
    return df.to_dict(orient="records")

@app.get("/risky-days")
def get_risky_days(user_id: str):
    query = text("SELECT * FROM recommendations WHERE user_id = :user_id AND recommendation LIKE '%High-risk%'")
    df = pd.read_sql(query, engine, params={"user_id": user_id})
    return df.to_dict(orient="records")

# --- Chat Analytics (Text-to-SQL) ---

class ChatRequest(BaseModel):
    user_id: str
    question: str

SCHEMA_CONTEXT = """
You are a PostgreSQL expert. detailed analysis.
The database has these tables:
1. expenses (id, user_id, date, category, amount, payment_mode, day_type)
2. goals (id, user_id, category, limit_amount, period)
3. user_profiles (user_id, income, est_fixed_costs, target_daily_spend, current_balance)

Task:
Convert the user's question into a LIST of SQL queries to get a complete picture.
Return a raw JSON list of strings. Example: ["SELECT...", "SELECT..."]

Rules:
- Return ONLY the raw JSON list. No markdown.
- Always filter by 'user_id' = :user_id.
- Do NOT use destructive commands (DROP, DELETE).
- Max 3 queries.
- **Currency is INR (₹). Do not convert to USD/EUR.**
- Prefer simple, separate queries over complex JOINs.
"""

@app.post("/chat/analyze")
async def analyze_data(request: ChatRequest):
    # 1. Text-to-SQL (Multi-Query)
    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
    
    prompt = f"{SCHEMA_CONTEXT}\n\nUser Question: {request.question}\nJSON List of SQL Queries:"
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=[prompt]
        )
        if not response.text:
             return {"answer": "I'm sorry, I couldn't generate a query. Please try again."}

        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        queries = json.loads(clean_text)
        
        if not isinstance(queries, list):
            queries = [queries] # fallback if single string
            
    except Exception as e:
        print(f"Gen Error: {e}")
        return {"answer": f"I couldn't understand that. Error: {e}"}

    # 2. Execution (Batch)
    aggregated_results = []
    
    try:
        with engine.connect() as connection:
            for i, sql in enumerate(queries):
                # Safety
                if any(x in sql.upper() for x in ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]):
                    continue
                
                try:
                    result = connection.execute(text(sql), {"user_id": request.user_id})
                    rows = result.fetchall()
                    aggregated_results.append(f"Query {i+1} ({sql}): {str(rows)}")
                except Exception as ex:
                    aggregated_results.append(f"Query {i+1} Failed: {ex}")
            
    except Exception as e:
        print(f"SQL Error: {e}")
        return {"answer": "I tried to check the database but the query was invalid."}

    # 3. Data-to-Human (Synthesis)
    data_context = "\n".join(aggregated_results)
    
    summary_prompt = f"""
    User asked: "{request.question}"
    
    Data retrieved from database:
    {data_context}
    
    Task:
    Provide a comprehensive, professional financial summary.
    - **ALWAYS use the Indian Rupee symbol (₹) for money.**
    - If specific numbers are found, cite them.
    - If multiple datasets exist (e.g., total + category), weave them into a narrative.
    - Use bullet points if helpful.
    - Keep it under 4 sentences.
    - Use Emoji.
    """
    
    try:
        final_resp = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=[summary_prompt]
        )
        answer = final_resp.text.strip() if final_resp.text else "Here is the data: " + data_context
    except Exception as e:
        answer = f"Here is the raw data: {data_context}"

    return {
        "sql_generated": str(queries),
        "answer": answer
    }

# --- DEBUG ENDPOINTS (For Verification) ---
@app.get("/debug/dole-setup")
def debug_dole_setup(user_id: str = "test_user"):
    db = SessionLocal()
    try:
        # 1. Inject 6 Past Decisions (8-10 days ago)
        # We need mixed outcomes (Good & Bad) for training to work.
        decisions_data = [
            (8, 5000, 'Safe', 0.9, False), # Should be Good
            (9, 12000, 'Risky', 0.6, True), # Should be Bad (High spend follows)
            (10, 3000, 'Safe', 0.95, False), # Good
            (8, 20000, 'Risky', 0.4, True), # Bad
            (9, 4500, 'Safe', 0.85, False), # Good
            (10, 6000, 'Safe', 0.9, False) # Good
        ]
        
        for days_ago, amt, verdict, conf, make_bad in decisions_data:
            past_date = date.today() - timedelta(days=days_ago)
            
            # Log Decision
            db.execute(text("""
                INSERT INTO decisions 
                (user_id, decision_date, target_date, amount, category, balance_at_decision, burn_rate, ai_verdict, confidence_score, outcome_label)
                VALUES 
                (:uid, :d_date, CURRENT_DATE, :amt, 'Test', 50000, 1000, :verdict, :conf, NULL)
            """), {
                "uid": user_id, 
                "d_date": past_date,
                "amt": amt,
                "verdict": verdict,
                "conf": conf
            })
            
            # If we want this to be "Bad", inject a huge expense the next day
            if make_bad:
                expense_date = past_date + timedelta(days=1)
                db.execute(text("""
                    INSERT INTO expenses (user_id, date, category, amount, payment_mode, day_type)
                    VALUES (:uid, :e_date, 'Impulse Buy', 40000, 'UPI', 'Weekday')
                """), {"uid": user_id, "e_date": str(expense_date)})
            
        db.commit()
        return {"status": "success", "message": f"Injected 6 decisions + expenses for mixed outcomes."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

@app.get("/debug/dole-trigger")
def debug_dole_trigger(user_id: str = "test_user"):
    try:
        # 1. Trigger Labeling
        label_outcomes(user_id)
        # 2. Trigger Training
        train_decision_model(user_id)
        
        # 3. Check Result
        db = SessionLocal()
        labeled_count = db.execute(text("SELECT COUNT(*) FROM decisions WHERE user_id=:uid AND outcome_label IS NOT NULL"), {"uid": user_id}).scalar()
        model_exists = os.path.exists("dole_model.pkl")
        db.close()
        
        return {
            "status": "success",
            "labeled_decisions_now": labeled_count,
            "model_created": model_exists,
            "message": "Learning loop executed."
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
