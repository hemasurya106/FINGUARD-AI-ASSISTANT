from fastapi import APIRouter, HTTPException, Form
from pydantic import BaseModel
from typing import List, Optional
from urllib.parse import urlparse
from app.services import search_agent_service
from app.services import scraper_service
from app.services import gemini_service
import asyncio

router = APIRouter()

class TwinCandidate(BaseModel):
    title: str
    link: str
    source: str
    price_hint: Optional[str] = None

class AlternativeCandidate(TwinCandidate):
    reason: Optional[str] = "Good alternative"

class TwinResponse(BaseModel):
    original_url: str
    search_query_used: str = "Hidden (AI Generated)"
    candidates: List[TwinCandidate]
    alternatives: List[AlternativeCandidate] = []

@router.post("/find-twins", response_model=TwinResponse)
async def find_twins_endpoint(url: str = Form(...)):
    """
    Finds "twin" products on other e-commerce sites.
    """
    print(f"👯‍♀️ Finding twins for URL: {url}")
    
    # 1. Extract domain to exclude it
    domain = urlparse(url).netloc.replace("www.", "")
    
    try:
        # Fetch HTML
        html, source = await scraper_service.fetch_html_with_browser(url)
        if not html or len(html) < 500:
             # Fallback to simple requests
             html = await scraper_service.fetch_html_threadsafe(url)
             source = "requests"
        
        if not html:
            raise HTTPException(status_code=400, detail="Could not fetch product page")

        # Extract Title (reuse gemini logic or simple soup)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        product_title = soup.title.string.strip() if soup.title else None
        
        if product_title:
             for suffix in [" : Amazon.in", " : Flipkart.com", "Buy Online at Best Price"]:
                 product_title = product_title.split(suffix)[0]
        
        if not product_title or len(product_title) < 5:
             product_title = "Unknown Product"

        print(f"📌 Identified Base Product: {product_title}")

        # 3. Use Search Agent Service to find twins AND alternatives concurrently
        # We run both tasks in parallel to save time
        
        task_twins = search_agent_service.find_twins(product_title, source_domain=domain, original_url=url)
        task_alts = search_agent_service.find_alternatives(product_title, source_domain=domain, original_url=url)
        
        candidates, alternatives = await asyncio.gather(task_twins, task_alts)
        
        return {
            "original_url": url,
            "candidates": candidates,
            "alternatives": alternatives
        }

    except Exception as e:
        print(f"⚠️ Error in find-twins: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
