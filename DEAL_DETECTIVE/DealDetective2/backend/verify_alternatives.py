import asyncio
import os
from dotenv import load_dotenv, find_dotenv
from app.services import search_agent_service

# Load env to ensure keys are present
load_dotenv(find_dotenv())

async def test_alternatives():
    product = "Sony WH-1000XM5 Noise Cancelling Headphones"
    print(f"🧪 Testing find_alternatives for: {product}")
    
    # We pass None for domain/url to test raw search
    results = await search_agent_service.find_alternatives(product)
    
    print(f"📊 Found {len(results)} alternatives:")
    for res in results:
        print(f"  - {res.get('title')} (Price: {res.get('price_hint')})")
        print(f"    Reason: {res.get('reason')}")
        print(f"    Link: {res.get('link')}")

if __name__ == "__main__":
    if not os.getenv("SERPER_API_KEY"):
        print("⚠️ SERPER_API_KEY not found. Skipping real test.")
    else:
        asyncio.run(test_alternatives())
