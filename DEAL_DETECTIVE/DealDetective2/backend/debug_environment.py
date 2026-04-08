import google.generativeai as genai
import os
from dotenv import load_dotenv, find_dotenv
import requests

load_dotenv(find_dotenv())

def list_models():
    print("Locked & Loaded Gemini Models:")
    try:
        if not os.getenv("GEMINI_API_KEY"):
            print("❌ GEMINI_API_KEY not found in .env")
            return

        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        models = genai.list_models()
        found = False
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                print(f"  - {m.name}")
                found = True
        if not found:
            print("  (No models found with generateContent capability)")
    except Exception as e:
        print(f"⚠️ Error listing models: {e}")

def test_serper_query(query):
    print(f"\nTesting Serper Query: '{query}'")
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        print("❌ SERPER_API_KEY not found in .env")
        return

    url = "https://google.serper.dev/search"
    payload = {"q": query, "num": 20, "gl": "in"}
    headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        results = data.get("organic", [])
        print(f"✅ Found {len(results)} raw results.")
        
        allowed_domains = ['amazon', 'flipkart', 'croma', 'reliancedigital', 'tatacliq', 'jiomart', 'vijaysales', 'nykaa', 'myntra']
        
        print("--- Filtering Check ---")
        passed = 0
        for r in results:
            link = r.get("link")
            title = r.get("title")
            is_allowed = any(d in link.lower() for d in allowed_domains)
            status = "✅ KEEP" if is_allowed else "❌ DROP"
            print(f"{status} : {link} ({title})")
            if is_allowed: passed += 1
            
        print(f"Total passed filtering: {passed}/{len(results)}")
        
    except Exception as e:
        print(f"⚠️ Serper Test Error: {e}")

if __name__ == "__main__":
    list_models()
    test_serper_query("alternatives to Sony WH-1000XM5 india")
