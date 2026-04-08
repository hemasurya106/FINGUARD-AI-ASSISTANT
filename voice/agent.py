import os
import json
import httpx
from google import genai
from google.genai import types
from deepgram import DeepgramClient
from dotenv import load_dotenv, find_dotenv
import base64
from sqlalchemy import text
from pathlib import Path
import sys
from datetime import date

# Ensure we can import from backend
sys.path.append(str(Path(__file__).parent.parent))
from backend.db import engine

# Explicitly load .env from the project root using find_dotenv
env_path = find_dotenv()
load_dotenv(dotenv_path=env_path, override=False)

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

BACKEND_URL = "http://127.0.0.1:8000"

SCHEMA_CONTEXT = """
Database Schema (PostgreSQL):
1. expenses (id, user_id, date, category, amount, payment_mode, day_type)
   - date is YYYY-MM-DD string.
2. goals (id, user_id, category, limit_amount, period)
3. user_profiles (user_id, income, est_fixed_costs, target_daily_spend, current_balance)
4. decisions (id, user_id, decision_date, target_date, amount, category, balance_at_decision, burn_rate, ai_verdict, confidence_score, outcome_label)
   - Do NOT query this unless asked about 'decisions' or 'history of approvals'.
5. recommendations (user_id, date, total_spend, cluster, anomaly, recommendation)
"""

class VoiceAgent:
    def __init__(self):
        self.gemini_client = None
        self.deepgram_client = None
        self.chat_session = None # Persist chat session
        self.user_id = "test_user" # Default
        
        # Initialize Gemini
        if not GEMINI_API_KEY:
            print("⚠️ WARNING: GEMINI_API_KEY not found.")
        else:
            try:
                self.gemini_client = genai.Client(api_key=GEMINI_API_KEY)
                print(f"✅ Initialized Gemini client")
            except Exception as e:
                print(f"⚠️ Failed to configure Gemini API: {e}")
        
        # Initialize Deepgram
        if DEEPGRAM_API_KEY:
            try:
                self.deepgram_client = DeepgramClient(api_key=DEEPGRAM_API_KEY)
                print(f"✅ Initialized Deepgram TTS client")
            except Exception as e:
                print(f"⚠️ Failed to initialize Deepgram client: {e}")
        else:
            print("⚠️ WARNING: DEEPGRAM_API_KEY not found.")

    # --- Instance Methods for Tools ---

    def execute_sql_query(self, query: str):
        """
        Executes a SELECT SQL query against the database.
        Use this to retrieve financial data, expenses, or check goals.
        Returns the rows as a list of dicts or a string message.
        """
        print(f"🛠️ Tool Call: execute_sql_query('{query}') for user {self.user_id}")
        
        # Safety checks
        forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE"]
        if any(word in query.upper() for word in forbidden):
            return "Error: Read-only access. Cannot execute destructive queries."
        
        # Force user_id filter if missing (simple check)
        
        try:
            with engine.connect() as conn:
                result = conn.execute(text(query))
                rows = result.fetchall()
                if not rows:
                    return "No results found."
                
                # Convert to list of dicts for clearer consumption
                columns = result.keys()
                data = [dict(zip(columns, row)) for row in rows]
                return str(data)
        except Exception as e:
            return f"Database Error: {e}"

    def add_expense_tool(self, amount: float, category: str, description: str = ""):
        """
        Adds a new expense to the system.
        Args:
            amount: The cost of the item.
            category: The category (e.g., 'Food', 'Travel', 'Shopping').
            description: Optional details about the item.
        """
        print(f"🛠️ Tool Call: add_expense_tool({amount}, {category}, {description}) for user {self.user_id}")
        
        payload = {
            "user_id": self.user_id,
            "amount": float(amount),
            "category": category,
            "date": str(date.today()), # Default to today
            "payment_mode": "Voice",
            "day_type": "Weekday" if date.today().weekday() < 5 else "Weekend"
        }
        
        try:
            # Using synchronous calling for the tool execution
            response = httpx.post(f"{BACKEND_URL}/add-expense", json=payload, timeout=10.0)
            if response.status_code == 200:
                return f"Expense of ₹{amount} for {category} added successfully. Details: {description}."
            else:
                return f"Failed to add expense. Backend returned status {response.status_code}."
        except Exception as e:
            return f"Connection Failed: {e}"

    def simulate_purchase_tool(self, amount: float, target_date: str):
        """
        Checks if a future purchase is affordable/safe.
        Args:
            amount: Cost of the item.
            target_date: When you plan to buy it (YYYY-MM-DD).
        """
        print(f"🛠️ Tool Call: simulate_purchase({amount}, {target_date}) for {self.user_id}")
        payload = {
            "user_id": self.user_id,
            "amount": float(amount),
            "target_date": target_date
        }
        try:
            response = httpx.post(f"{BACKEND_URL}/simulate", json=payload, timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                safe_str = "SAFE" if data['safe'] else "UNSAFE"
                return f"Simulation Result: {safe_str}. {data['message']} Future Balance: ₹{data['future_balance']:.2f}."
            return f"Error: Simulation failed (Status {response.status_code})"
        except Exception as e:
            return f"Connection Failed: {e}"

    def set_goal_tool(self, category: str, limit_amount: float, period: str = "daily"):
        """
        Sets a spending limit/goal.
        Args:
            category: 'Food', 'Travel', 'Shopping', etc.
            limit_amount: Max amount to spend.
            period: 'daily' (default).
        """
        print(f"🛠️ Tool Call: set_goal({category}, {limit_amount}) for {self.user_id}")
        payload = {
            "user_id": self.user_id,
            "category": category,
            "limit_amount": float(limit_amount),
            "period": period
        }
        try:
            httpx.post(f"{BACKEND_URL}/set-goal", json=payload, timeout=5.0)
            return f"Goal set: Limit {category} spending to ₹{limit_amount} {period}."
        except Exception as e:
            return f"Failed to set goal: {e}"

    def get_financial_insights_tool(self):
        """
        Fetches AI financial insights and risky day alerts.
        """
        print(f"🛠️ Tool Call: get_financial_insights() for {self.user_id}")
        try:
            # Fetch recommendations
            rec_resp = httpx.get(f"{BACKEND_URL}/recommendations", params={"user_id": self.user_id})
            risky_resp = httpx.get(f"{BACKEND_URL}/risky-days", params={"user_id": self.user_id})
            
            recs = rec_resp.json() if rec_resp.status_code == 200 else []
            risks = risky_resp.json() if risky_resp.status_code == 200 else []
            
            # Summarize (take last 3 recs and all risks)
            recent_recs = [r['recommendation'] for r in recs[-3:]] if recs else ["No specific insights yet."]
            risk_dates = [f"{r['date']} (₹{r['total_spend']})" for r in risks[-3:]] if risks else ["No high-risk days detected."]
            
            return f"Insights: {'; '.join(recent_recs)}. \nRisky Days: {', '.join(risk_dates)}."
        except Exception as e:
            return f"Failed to fetch insights: {e}"

    async def process(self, user_text: str, user_id: str = "test_user"):
        """
        Process user input with ReAct/Tool-use loop using a persistent chat session.
        """
        print(f"Agent Processing: '{user_text}' for user '{user_id}'")
        self.user_id = user_id # Update instance user_id
        
        response_text = "I'm sorry, I couldn't process that."
        
        if not self.gemini_client:
            return {"text": "Gemini API not configured.", "audio_url": None}

        try:
            from datetime import date
            today = date.today()

            # Initialize chat session if it doesn't exist
            if not self.chat_session:
                # 1. Prepare Tools and Prompt
                # Bind methods to the list
                tools_list = [
                    self.execute_sql_query, 
                    self.add_expense_tool,
                    self.simulate_purchase_tool,
                    self.set_goal_tool,
                    self.get_financial_insights_tool
                ]
                
                system_instruction = f"""You are Jarvis, an intelligent financial assistant.
You have direct access to the database and can perform actions.

Current Date: {today} (YYYY-MM-DD)

{SCHEMA_CONTEXT}

Rules:
1. **Data Handling**:
   - If user asks for data, use `execute_sql_query`.
   - ALWAYS filter by user_id = '{self.user_id}'.
   - Date format is YYYY-MM-DD. Use PostgreSQL date syntax.
   - Return amounts in INR (₹).

2. **Response Style (CRITICAL)**:
   - **NEVER** mention the `user_id`.
   - **NEVER** read out raw JSON.
   - Synthesize the data into a natural conversation.
    - **ALWAYS** finish with a helpful, natural summary of what you found.
    - **NEVER** just say "Task completed". If you have data, explain it.

3. **Tool Usage**:
   - **Data**: `execute_sql_query` for expenses/totals.
   - **Add**: `add_expense_tool` for new spend.
   - **Simulate**: `simulate_purchase_tool` if user asks "Can I afford X?" or "Safe to buy Y?".
     - If `target_date` is missing, ASK the user for it (or assume 30 days if context implies "next month").
   - **Goals**: `set_goal_tool` to convert "Limit food to 500" -> Budget setting.
   - **Insights**: `get_financial_insights_tool` for "How am I doing?" or "Any risks?".
"""
                self.chat_session = self.gemini_client.chats.create(
                    model="gemini-2.5-flash",
                    config=types.GenerateContentConfig(
                        tools=tools_list,
                        system_instruction=system_instruction,
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(
                            disable=False,
                            maximum_remote_calls=15
                        )
                    )
                )
                print("✅ Created new Gemini chat session (2.5-flash).")

            # Send the message to the EXISTING session
            response = self.chat_session.send_message(user_text)
            
            if response.text:
                response_text = response.text.strip()
            else:
                # Fallback if text is empty (check candidates)
                try:
                    candidates = response.candidates
                    if candidates and candidates[0].content.parts:
                        parts = candidates[0].content.parts
                        # Look for text part
                        text_parts = [p.text for p in parts if p.text]
                        if text_parts:
                            response_text = " ".join(text_parts)
                        else:
                            response_text = "Task completed."
                    else:
                        response_text = "Task completed."
                except:
                    response_text = "Task completed."

            print(f"✅ Gemini Response: {response_text}")

        except Exception as e:
            print(f"❌ Gemini Processing Error: {e}")
            import traceback
            traceback.print_exc()
            response_text = f"I encountered an error processing your request."
            # Reset session on error to avoid sticking in a bad state
            self.chat_session = None

        # 2. Generate Audio
        audio_url = await self._generate_audio(response_text)
        
        return {
            "text": response_text,
            "audio_url": audio_url
        }

    async def _generate_audio(self, text):
        """Generate TTS using Deepgram."""
        if not self.deepgram_client or not text:
            return None
            
        try:
            import re
            clean_text = re.sub(r'[*#_`]', '', text)
            print(f"🎤 Generating audio for: {clean_text[:50]}...")
            audio_chunks = []
            # Deepgram speak.v1.audio.generate returns an iterator
            for chunk in self.deepgram_client.speak.v1.audio.generate(
                text=clean_text,
                model="aura-asteria-en",
                encoding="mp3"
            ):
                if chunk: audio_chunks.append(chunk)
            
            audio_data = b''.join(audio_chunks)
            if not audio_data: return None
            
            encoded_string = base64.b64encode(audio_data).decode('utf-8')
            return f"data:audio/mpeg;base64,{encoded_string}"
        except Exception as e:
            print(f"❌ TTS Error: {e}")
            return None
