from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv, find_dotenv
from app.routers import analyze, alerts, twins
from app.database import engine, Base
from sqlalchemy import text
from app.services.alert_monitor import start_monitor
import asyncio

load_dotenv(find_dotenv())

app = FastAPI(title="DealDetective API", version="1.0.0")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(analyze.router)
app.include_router(alerts.router, prefix="/api")
app.include_router(twins.router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    # Start the price monitor in the background
    asyncio.create_task(start_monitor())


@app.get("/")
async def root():
    return {"message": "DealDetective API is running"}

@app.on_event("startup")
def startup_db():
    try:
        # 1. Enable Vector Extension (Safety check)
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
        
        # 2. Create Tables
        Base.metadata.create_all(bind=engine)
        print("✅ Database Tables & Vector Extension Ready")
    except Exception as e:
        print(f"❌ Database Init Failed: {e}")

app.include_router(analyze.router, prefix="/api")
@app.get("/health")
async def health():
    return {"status": "healthy"}

