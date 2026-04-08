import requests
import os
from dotenv import load_dotenv, find_dotenv
from app.services import gemini_service
from app.services import scraper_service
import asyncio
import json

load_dotenv(find_dotenv())
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

async def find_twins(product_title: str, source_domain: str = None, original_url: str = None):
    print(f"🕵️‍♀️ Twin Finder activated for: {product_title}")
    
    # Step 1: Brain (Gemini) decides the query
    query = await gemini_service.generate_search_query(product_title, source_domain)
    print(f"📡 Sending query to Serper: {query}")
    
    # Step 2: Eyes (Serper) performs the search
    url = "https://google.serper.dev/search"
    payload = {"q": query, "num": 100, "gl": "in"} # Increased to 100 to maximize candidate pool
    headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        results = data.get("organic", [])
        print(f"✅ Serper returned {len(results)} results")
        if not results:
             print(f"⚠️ Raw Serper Response: {data}")
    except Exception as e:
        print(f"⚠️ Serper API error: {e}")
        return []

    # Step 3: Filter Initial Candidates
    raw_candidates = []
    seen_links = set()
    
    print(f"🕵️ Filtering candidates from {len(results)} results...")
    for r in results:
        link = r.get("link")
        
        # Deduplicate against original URL (normalize by removing query params)
        if original_url:
            norm_link = link.split('?')[0].rstrip('/')
            norm_original = original_url.split('?')[0].rstrip('/')
            if norm_link == norm_original:
                # print(f"  Skipping original URL: {link}")
                continue

        if link in seen_links: continue
        seen_links.add(link)
        
        # Basic domain filtering to avoid blogs/news
        # Expanded domain filtering to ensure we find Top 3 candidates
        allowed_domains = ['amazon', 'flipkart', 'croma', 'reliancedigital', 'tatacliq', 'jiomart', 'vijaysales', 'nykaa', 'myntra']
        if not any(d in link.lower() for d in allowed_domains):
            # print(f"  Skipping non-allowed domain: {link}")
            continue

        print(f"  ✅ Accepted candidate: {link}")

        raw_candidates.append(r)
        if len(raw_candidates) >= 5: # Limit analysis to top 5 to save time/cost
            break
    
    # Step 4: Deep Analysis (The "Detective" Work)
    # Scrape and Analyze each candidate in parallel
    print(f"🕵️ Deep Analyzing {len(raw_candidates)} candidates...")
    
    verified_twins = []
    
    async def analyze_candidate(candidate):
        url = candidate.get("link")
        print(f"🔍 Inspecting: {url}")
        try:
            # 1. Scrape (Static first for speed)
            html = await scraper_service.fetch_html_threadsafe(url)
            source = "requests"
            
            if not html or len(html) < 2000:
                # Fallback to browser if static failed
                html, source = await scraper_service.fetch_html_with_browser(url)
            
            if not html:
                return None
            
            # 2. Analyze with Gemini
            # We reuse the existing Gemini analysis but maybe we want a "lighter" version?
            # For now, full analysis ensures accuracy.
            analysis_json = await gemini_service.analyze_html(html, url)
            
            if analysis_json:
                data = json.loads(analysis_json)
                price = data.get("price")
                if price:
                    return {
                        "title": data.get("title") or candidate.get("title"),
                        "link": url,
                        "source": source,
                        "price_hint": str(price), # Cast to string for Pydantic
                        "currency": data.get("currency", "INR")
                    }
        except Exception as e:
            print(f"⚠️ Failed to analyze {url}: {e}")
            return None

    # Run analysis concurrently
    tasks = [analyze_candidate(c) for c in raw_candidates]
    analyzed_results = await asyncio.gather(*tasks)
    
    # Filter successful ones
    verified_twins = [r for r in analyzed_results if r is not None]
    
    # AI Ranking (Gemini)
    final_twins = await gemini_service.rank_products(product_title, verified_twins)
    
    return final_twins[:3]

async def find_alternatives(product_title: str, source_domain: str = None, original_url: str = None):
    print(f"🔄 Alternative Finder activated for: {product_title}")
    
    # Step 1: Brain (Gemini) decides the query for ALTERNATIVES
    query = await gemini_service.generate_alternative_search_query(product_title)
    print(f"📡 Sending ALTERNATIVE query to Serper: {query}")
    
    # Step 2: Eyes (Serper) performs the search
    url = "https://google.serper.dev/search"
    payload = {"q": query, "num": 100, "gl": "in"}
    headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        data = response.json()
        results = data.get("organic", [])
    except Exception as e:
        print(f"⚠️ Serper API error (Alternatives): {e}")
        return []

    # Step 3: Filter Initial Candidates
    raw_candidates = []
    seen_links = set()
    
    for r in results:
        link = r.get("link")
        
        # Deduplicate internal set
        if link in seen_links: continue
        seen_links.add(link)
        
        # Exclude original URL (don't recommend the exact same page)
        if original_url:
            norm_link = link.split('?')[0].rstrip('/')
            norm_original = original_url.split('?')[0].rstrip('/')
            if norm_link == norm_original:
                continue

        # Allowed domains only
        allowed_domains = ['amazon', 'flipkart', 'croma', 'reliancedigital', 'tatacliq', 'jiomart', 'vijaysales', 'nykaa', 'myntra']
        if not any(d in link.lower() for d in allowed_domains):
            continue

        raw_candidates.append(r)
        if len(raw_candidates) >= 5: 
            break
    
    # Step 4: Deep Analysis
    print(f"🕵️ Deep Analyzing {len(raw_candidates)} alternative candidates...")
    
    async def analyze_candidate(candidate):
        url = candidate.get("link")
        try:
            # 1. Scrape
            html = await scraper_service.fetch_html_threadsafe(url)
            source = "requests"
            if not html or len(html) < 2000:
                html, source = await scraper_service.fetch_html_with_browser(url)
            
            if not html: return None
            
            # 2. Analyze
            analysis_json = await gemini_service.analyze_html(html, url)
            
            if analysis_json:
                data = json.loads(analysis_json)
                price = data.get("price")
                if price:
                    return {
                        "title": data.get("title") or candidate.get("title"),
                        "link": url,
                        "source": source,
                        "price_hint": str(price),
                        "currency": data.get("currency", "INR")
                    }
        except Exception as e:
             return None
        return None

    tasks = [analyze_candidate(c) for c in raw_candidates]
    analyzed_results = await asyncio.gather(*tasks)
    verified_candidates = [r for r in analyzed_results if r is not None]
    
    # AI Ranking for Alternatives
    final_alternatives = await gemini_service.rank_alternatives(product_title, verified_candidates)
    
    return final_alternatives