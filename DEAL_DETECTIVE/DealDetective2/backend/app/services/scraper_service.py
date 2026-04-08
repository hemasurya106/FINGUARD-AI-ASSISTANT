import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from starlette.concurrency import run_in_threadpool
import time
import os
import asyncio
# Optional: Playwright for JavaScript-rendered content
PLAYWRIGHT_AVAILABLE = False
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    print("Playwright not available. Install with: pip install playwright && playwright install")

# Browser-like headers to avoid immediate blocking
# Transparent Bot Headers
HEADERS = {
    "User-Agent": "DealDetectiveBot/1.0 (+https://github.com/hemasurya106/DEAL_DETECTIVE)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Cache-Control": "max-age=0",
}

def _fetch_html(url: str):
    """Synchronous function to fetch HTML from a URL"""
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=0.5, status_forcelist=(429, 500, 502, 503, 504))
    session.mount("https://", HTTPAdapter(max_retries=retries))
    session.mount("http://", HTTPAdapter(max_retries=retries))
    
    try:
        # Polite delay
        time.sleep(1.0)
        # Reduced timeout for blocked sites - fail fast
        response = session.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        
        # If blocked explicitly
        if response.status_code == 403:
            print(f"Access forbidden (403) for {url}")
            return None
        
        # Check if we got a redirect to a blocked page
        if response.status_code == 200:
            text_lower = response.text.lower()
            # Very short response might be a blocking page
            if len(response.text) < 1000:
                if "blocked" in text_lower or "access denied" in text_lower:
                    print(f"Site appears to be blocking access: {url}")
                    return None
            


        response.raise_for_status()
        return response.text
    except requests.exceptions.Timeout:
        print(f"Request timeout for {url}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Scrape Fetch Error for {url}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error fetching {url}: {e}")
        return None

async def fetch_html_threadsafe(url: str):
    """Fetch HTML using requests (static HTML only)"""
    return await run_in_threadpool(_fetch_html, url)


async def fetch_html_with_browser(url: str):
    """
    Fetch HTML using Playwright (renders JavaScript).
    Use this when static HTML doesn't contain the data you need.
    Slower but captures JavaScript-rendered content.
    """
    if not PLAYWRIGHT_AVAILABLE:
        print("Playwright not available, falling back to static HTML")
        return await fetch_html_threadsafe(url)
    
    try:
        async with async_playwright() as p:
            # Launch browser (headless) - Standard Configuration
            browser = await p.chromium.launch(
                headless=True
            )
            
            # Standard Context (Identified as Bot)
            context = await browser.new_context(
                user_agent="DealDetectiveBot/1.0 (+https://github.com/hemasurya106/DEAL_DETECTIVE)",
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
                timezone_id="Asia/Kolkata",
                java_script_enabled=True,
                accept_downloads=False
            )
            
            # No stealth scripts injected

            page = await context.new_page()
            
            # Block resources to speed up and reduce ban risk
            await page.route("**/*.{png,jpg,jpeg,gif,webp,svg,woff,woff2}", lambda route: route.abort())

            # Navigate and wait for DOM
            try:
                # Add extra randomness to wait
                import random
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                await page.wait_for_timeout(3000) # Wait for potential redirects or dynamic loading
                
                # Scroll a bit to simulate user
                await page.evaluate("window.scrollTo(0, 500)")
                await page.wait_for_timeout(1000)
                
            except Exception as e:
                print(f"Page navigation warning: {e}")
                # Try to return content anyway in case it partially loaded
            
            # Get rendered HTML
            html = await page.content()
            
            await browser.close()
            return html, "playwright"
    except Exception as e:
        print(f"Browser fetch error: {e}")
        return None, None

async def scrape_product_url(url: str, use_browser: bool = False):
    """
    Main entry point. Currently focuses on Amazon logic.
    Returns a dictionary with product information.
    
    Args:
        url: Product URL to scrape
        use_browser: If True, use Playwright to render JavaScript (slower but more accurate)
    """
    # Try static HTML first (faster)
    if use_browser:
        html = await fetch_html_with_browser(url)
    else:
        html = await fetch_html_threadsafe(url)
    
    if not html:
        # If static HTML failed and we haven't tried browser yet, try browser
        if not use_browser:
            print("Static HTML failed, trying browser rendering...")
            html = await fetch_html_with_browser(url)
        
        if not html:
            raise Exception("Failed to fetch HTML")
        
    soup = BeautifulSoup(html, "html.parser")
    
    # Initialize variables
    title = None
    price = None
    original_price = None
    currency = None
    
    # Detect platform
    platform = "generic"
    if "amazon" in url.lower():
        platform = "amazon"
    elif "flipkart" in url.lower():
        platform = "flipkart"
    elif "nykaa" in url.lower():
        platform = "nykaa"
    elif "myntra" in url.lower():
        platform = "myntra"
    
    # Amazon-specific extraction
    if platform == "amazon":
        title_tag = soup.select_one("#productTitle") or soup.select_one("h1.a-size-large")
        
        title = title_tag.get_text(strip=True) if title_tag else None
        
        # Extract current price (discounted price)
        price = None
        original_price = None
        currency = "INR" if "amazon.in" in url else "USD"
        
        import re
        
        # Find the price block container first (helps us find related prices)
        price_block = soup.select_one("#price, #priceblock_dealprice, #priceblock_ourprice, .a-price, [data-asin-price]")
        
        # Try multiple selectors for current price
        price_selectors = [
            ".a-price-whole",  # Most common - shows current price
            ".a-price .a-offscreen",
            "#priceblock_dealprice",
            "#priceblock_ourprice",
            "#priceblock_saleprice",
            ".a-price-now",
            "span.a-price:not(.a-text-price)"  # Current price, not strikethrough
        ]
        
        for selector in price_selectors:
            price_tag = soup.select_one(selector)
            if price_tag:
                price_text = price_tag.get_text(strip=True)
                # Extract numbers
                numbers = re.findall(r'\d+\.?\d*', price_text.replace(",", "").replace("₹", "").replace("$", "").replace("€", "").replace("£", ""))
                if numbers:
                    try:
                        price = float(numbers[0])
                        break
                    except ValueError:
                        continue
        
        # Extract original price (strikethrough/list price)
        # Amazon shows: MRP (highest, often 999), List Price (original, e.g., 399), Current Price (discounted, e.g., 284)
        # We want the List Price (399), not MRP (999)
        # Priority: Look for list price near current price first, avoid MRP
        original_price_selectors = [
            # List price (usually shown near current price, not MRP)
            ".basisPrice .a-offscreen",  # Basis/list price - most reliable
            ".a-price.a-text-price span.a-offscreen",  # Strikethrough price near current
            "span.a-price.a-text-price .a-offscreen",  # Alternative strikethrough
            ".a-text-strike .a-offscreen",  # Generic strikethrough
            "#priceblock_saleprice + .a-text-strike .a-offscreen",
            "span.a-text-strike span.a-offscreen"
        ]
        
        found_prices = []
        for selector in original_price_selectors:
            original_price_tags = soup.select(selector)
            for tag in original_price_tags:
                original_price_text = tag.get_text(strip=True)
                numbers = re.findall(r'\d+\.?\d*', original_price_text.replace(",", "").replace("₹", "").replace("$", "").replace("€", "").replace("£", ""))
                if numbers:
                    try:
                        found_price = float(numbers[0])
                        found_prices.append(found_price)
                    except ValueError:
                        continue
        
        # If we found multiple prices, choose the one closest to current price but higher
        # This filters out MRP (999) and picks list price (399)
        if found_prices:
            if price:
                # Filter out prices that are too high (likely MRP)
                # Reasonable range: current price < original < current price * 2.5
                # This ensures we get list price (399) not MRP (999) when current is 284
                valid_prices = [p for p in found_prices if price < p <= price * 2.5]
                if valid_prices:
                    # Pick the smallest valid price (list price, not MRP)
                    original_price = min(valid_prices)
                else:
                    # If no prices in reasonable range, try a wider range but still filter
                    wider_range = [p for p in found_prices if price < p <= price * 4]
                    if wider_range:
                        # Among wider range, pick closest to current price * 1.5 (typical discount)
                        target = price * 1.5
                        original_price = min(wider_range, key=lambda x: abs(x - target))
                    else:
                        # Last resort: smallest price that's still higher than current
                        higher_prices = [p for p in found_prices if p > price]
                        if higher_prices:
                            original_price = min(higher_prices)
            else:
                # If we don't have current price, just use the smallest (likely list price)
                original_price = min(found_prices)
        
        # Alternative: Look for "List Price" text explicitly (not MRP)
        if not original_price or (price and original_price > price * 2.5):
            # Find elements containing "List Price" text
            for elem in soup.find_all(text=re.compile(r'List Price', re.I)):
                parent = elem.find_parent()
                if parent:
                    # Look for price in the same element or nearby
                    price_elem = parent.select_one('.a-offscreen, .a-price, span')
                    if price_elem:
                        price_text = price_elem.get_text()
                    else:
                        price_text = parent.get_text()
                    numbers = re.findall(r'\d+\.?\d*', price_text.replace(",", "").replace("₹", "").replace("$", "").replace("€", "").replace("£", ""))
                    if numbers:
                        try:
                            candidate_price = float(numbers[0])
                            # If it's reasonable compared to current price, use it
                            if not price or (price < candidate_price < price * 2.5):
                                original_price = candidate_price
                                break
                        except ValueError:
                            continue
        
        # If we found original price but not current price, check for price range or other patterns
        if original_price and not price:
            # Sometimes the current price is in a different format
            savings_tag = soup.select_one(".a-size-large.a-color-price.savingsPercentage")
            if savings_tag:
                savings_text = savings_tag.get_text(strip=True)
                savings_match = re.search(r'(\d+)%', savings_text)
                if savings_match:
                    savings_pct = float(savings_match.group(1))
                    price = round(original_price * (1 - savings_pct / 100), 2)
    else:
        # Generic extraction
        title_tag = soup.select_one("h1") or soup.select_one("title")
        title = title_tag.get_text(strip=True) if title_tag else None

    # Extract Images
    images = []
    # 1. Meta tags
    for sel in ["meta[property='og:image']", "meta[property='twitter:image']", "link[rel='image_src']"]:
        for m in soup.select(sel):
            img = m.get("content") or m.get("href")
            if img: images.append(img)
            
    # 2. Platform selectors
    if platform == "amazon":
         for img in soup.select("#landingImage, #imgBlkFront, .a-dynamic-image, [data-a-dynamic-image]"):
             src = img.get("src")
             if src: images.append(src)
             # Dynamic
             dyn = img.get("data-a-dynamic-image")
             if dyn:
                 try:
                     urls = re.findall(r'https?://[^"]+', dyn)
                     images.extend(urls)
                 except: pass
    elif platform == "flipkart":
         for img in soup.select("img._396cs4, .CXW8mj img, ._2r_T1I"):
             src = img.get("src")
             if src: images.append(src)
    
    # Generic fallback
    if not images:
        for img in soup.select("img"):
            src = img.get("src")
            if src and "http" in src and ("product" in src or "cache" in src) and "pixel" not in src:
                # Basic heuristic for product images
                width = img.get("width")
                if width and width.isdigit() and int(width) > 200:
                    images.append(src)

    # Deduplicate
    images = list(set(images))

    return {
        "title": title,
        "price": price,
        "original_price": original_price,
        "currency": currency,
        "specs": {}, # In Phase 2 we use AI to fill this
        "images": images,
        "platform": platform,
        "scraped": True
    }