import os
import time
from google import genai
from dotenv import load_dotenv, find_dotenv

def main():
    load_dotenv(find_dotenv())
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("No GEMINI_API_KEY found.")
        return

    client = genai.Client(api_key=api_key)
    
    print("Testing Text-to-SQL Latency...")
    prompt = "Convert to SQL: show my total expenses for food this month"
    
    start_time = time.time()
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash-lite',
            contents=[prompt]
        )
        end_time = time.time()
        print(f"Text-to-SQL (Gemini 2.5 Flash-Lite) Latency: {end_time - start_time:.2f} seconds")
    except Exception as e:
        print(f"Error testing text-to-sql: {e}")

if __name__ == "__main__":
    main()
