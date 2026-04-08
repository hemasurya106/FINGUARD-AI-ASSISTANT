# 🧠 AI FINANCIAL ASSISTANT WITH RISK ANALYSIS AND DEAL DETECTIVE SYSTEM

**Jarvis Financial OS** is a comprehensive personal finance dashboard integrated with a Voice AI Agent and a Smart Deal Detective module. It combines expense tracking, risk analysis, and voice control into a single glassmorphism-styled interface.

## 🚀 Key Features

### 1. Smart Expense Tracking
*   **Manual & OCR Entry**: Users can manually enter expenses or upload bill images. The system automatically extracts amount and category using **OCR**.
*   **Instant Feedback**: Provides immediate "Decision Insights" (e.g., "Safe to spend" or "High Risk") based on your current balance and goals.

### 2. Predictive Risk Analysis (DOLE)
*   **AI Forecasting**: Using past spending behavior and machine learning, the system predicts whether a planned expense will cause future financial stress.
*   **"What-If" Simulator**: Ask questions like *"Can I spend ₹5000 on a watch?"* and get a **Safe** or **Risky** verdict with a confidence score.

### 3. Analytics & Spending Insights
*   **Visual Trends**: Interactive charts showing daily and monthly spending trends.
*   **Behavior Clustering**: AI automatically groups your days into patterns (e.g., "Normal Spending" vs. "High-Spend Days"), helping you understand your habits.

### 4. 🎙️ Voice-Controlled AI Assistant
*   **Hands-Free Interaction**: An always-on voice agent powered by **Gemini 2.0** (Brain) and **Deepgram** (Voice).
*   **Natural Language**: Commands like *"Add ₹300 for lunch"* or *"Show my spending insights"* are understood instantly.
*   **Vocal Response**: The assistant updates the database and speaks back to you in a human-like voice.

### 5. 🕵️ Smart Deal Detection (Deal Detective)
*   **Brand Tax Analysis**: Paste a product link (e.g., Amazon) to detect if you are overpaying for a brand name.
*   **Twin Finder**: Finds cheaper OEM or generic alternatives with identical specifications.
*   **Price Alerts**: Set targets and get notified when prices drop.

---

## 🛠️ Tech Stack
*   **Frontend**: React.js, Chart.js, Tailwind CSS
*   **Backend**: FastAPI, PostgreSQL/SQLite, SQLAlchemy
*   **AI/ML**: Google Gemini 2.0, Deepgram Aura, Scikit-Learn (DOLE Model)
*   **Voice**: PicoVoice (Wake Word), WebSockets
# Make sure you are in the root 'sf' folder
cd /Users/hemasurya/Desktop/sf

# Run the server
uvicorn backend.api:app --reload
# Navigate to the frontend folder
cd /Users/hemasurya/Desktop/sf/frontend/pdis-dashboard

# Start the development server
npm start
# Make sure you are in the root 'sf' folder
uvicorn voice.server:app --reload --port 8001
#   deal detective cd backend
uvicorn app.main:app --reload --port 8002
# deal detective frontend
cd /Users/hemasurya/Desktop/sf/DEAL_DETECTIVE/DealDetective2/frontend
npm run dev# AI-FINANCIAL-ASSISTANT
