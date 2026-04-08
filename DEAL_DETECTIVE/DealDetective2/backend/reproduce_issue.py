
import requests
import asyncio
from app.services import scraper_service
from app.services.robots_service import is_allowed
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# Failing URL
URL_FAIL = "https://www.amazon.in/Aquaminder-Bottle-Remind-Adults-Perfect/dp/B0DBZL2PTC/?_encoding=UTF8&pd_rd_w=3DXxr&content-id=amzn1.sym.47226dd1-3657-494d-8578-f5621c2124b3&pf_rd_p=47226dd1-3657-494d-8578-f5621c2124b3&pf_rd_r=KNGC5QVEHAQCB7FXVYPK&pd_rd_wg=mHQQP&pd_rd_r=62f7b921-47c9-4481-a559-cd9f66026eed&ref_=pd_hp_d_atf_dealz_cs&th=1"
# New URL to test
URL_NEW = "https://www.amazon.in/boAt-Airdopes-Plus-311-Bluetooth/dp/B0DZXX6SKP/?_encoding=UTF8&pd_rd_w=3DXxr&content-id=amzn1.sym.47226dd1-3657-494d-8578-f5621c2124b3&pf_rd_p=47226dd1-3657-494d-8578-f5621c2124b3&pf_rd_r=KNGC5QVEHAQCB7FXVYPK&pd_rd_wg=mHQQP&pd_rd_r=62f7b921-47c9-4481-a559-cd9f66026eed&ref_=pd_hp_d_atf_dealz_cstest"


async def test_url(url, label):
    print(f"\n==========================================")
    print(f"Testing {label}: {url}")
    print(f"==========================================")
    
    # 1. Check Robots.txt
    print("Checking robots.txt...")
    try:
        allowed = await is_allowed(url)
        print(f"Robots.txt Allowed: {allowed}")
    except Exception as e:
        print(f"Robots.txt check failed: {e}")
        allowed = False

    # 2. Try Fetch
    print("Fetching HTML...")
    html = await scraper_service.fetch_html_threadsafe(url)
    
    if html is None:
        print("⚠️ fetch_html_threadsafe returned None (Soft Block / Block)")
        print("Trying Browser Fetch (Fallback)...")
        html_browser = await scraper_service.fetch_html_with_browser(url)
        if html_browser:
            print(f"✅ Browser Fetch Success! Length: {len(html_browser)}")
        else:
            print("❌ Browser Fetch Failed (None).")
    else:
        print(f"✅ fetch_html_threadsafe Success! Length: {len(html)}")
        if "continue shopping" in html.lower() and "conditions of use" in html.lower():
             print("⚠️ (Wait, content looks like soft block but wasn't caught?)")

async def main():
    await test_url(URL_FAIL, "Failing URL (403)")
    await test_url(URL_NEW, "New URL")

if __name__ == "__main__":
    asyncio.run(main())
