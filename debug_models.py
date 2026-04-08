
import os
from dotenv import load_dotenv, find_dotenv

# Try to find .env multiple ways
# 1. From backend/
load_dotenv(dotenv_path="backend/.env")
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    # 2. From CWD
    load_dotenv(find_dotenv())
    api_key = os.environ.get("GEMINI_API_KEY")

print(f"API Key found: {'Yes' if api_key else 'No'}")

# --- New SDK ---
print("\n--- Listing Models (New SDK: google.genai) ---")
try:
    from google import genai
    client = genai.Client(api_key=api_key)
    
    # client.models.list() returns a pager
    pager = client.models.list()
    
    count = 0
    for model in pager:
        print(f"  {model.name}  ({model.display_name})")
        count += 1
        if count > 20: break # Limit
        
except Exception as e:
    print(f"Error listing models with new SDK: {e}")

# --- Old SDK ---
print("\n--- Listing Models (Old SDK: google.generativeai) ---")
try:
    import google.generativeai as old_genai
    if api_key:
        old_genai.configure(api_key=api_key)
        for m in old_genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"  {m.name}")
except Exception as e2:
    print(f"Old SDK Error: {e2}")
