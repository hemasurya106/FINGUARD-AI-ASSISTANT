from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
import traceback
import asyncio
from urllib.parse import urlparse
from sqlalchemy.orm import Session

# Internal Services
from app.services import gemini_service
from app.services import scraper_service
from app.services.robots_service import is_allowed as robots_is_allowed
from app.services.adapters import generic_adapter
from app.database import get_db
from app.models import Product, PriceHistory

router = APIRouter()



class JargonItem(BaseModel):
    term: str
    simple_explanation: str

class EcoAnalysis(BaseModel):
    score: Optional[str] = "Red"
    badge: Optional[str] = "Red" 
    reasoning: Optional[str] = None

class AIAnalysis(BaseModel):
    jargon_buster: List[JargonItem] = []
    eco_analysis: Optional[EcoAnalysis] = None

class AnalyzeResponse(BaseModel):
    product_id: Optional[str] = None
    platform: Optional[str] = "generic"
    title: Optional[str] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    discount_percentage: Optional[float] = None
    currency: Optional[str] = None
    specs: Dict[str, Any] = {}
    ai_analysis: Optional[AIAnalysis] = None
    images: List[str] = []
    source: str  # Which scraper worked (deep, generic, or vision)


def _is_number(x):
    return isinstance(x, (int, float))


def platform_from_url(url: Optional[str]) -> str:
    """Best-effort platform detection from domain."""
    if not url:
        return "generic"
    domain = urlparse(url).netloc.lower()
    if "amazon" in domain:
        return "amazon"
    if "flipkart" in domain:
        return "flipkart"
    if "nykaa" in domain:
        return "nykaa"
    if "myntra" in domain:
        return "myntra"
    if "croma" in domain:
        return "croma"
    return "generic"


@router.post("/analyze-input", response_model=AnalyzeResponse)
async def analyze_input(
    url: Optional[str] = Form(None),
    product_name: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
):
    final_data = None
    source = "unknown"

    try:
        # ==========================================
        # SCENARIO 1: User Provided a URL
        # ==========================================
        if url:
            print(f"🔍 Analyzing URL: {url}")

            # Step A: Check Safety (Robots.txt) - with timeout
            try:
                robots_allowed = await asyncio.wait_for(
                    robots_is_allowed(url),
                    timeout=8.0  # 8 second timeout for robots.txt check
                )
            except asyncio.TimeoutError:
                print(f"⚠️ Robots.txt check timeout for {url}, defaulting to blocked")
                robots_allowed = False
            
            if not robots_allowed:
                print(f"🚫 Robots.txt blocked {url}. Strict Compliance Mode: Aborting.")
                raise HTTPException(
                    status_code=403, 
                    detail="Access denied by site's robots.txt protocol. This bot operates in Strict Compliance Mode."
                )
            else:
                # Robots allowed -> Use Gemini
                print(f"✅ Robots.txt allowed. Using Gemini AI to extract product info from HTML.")
                try:
                    html = await scraper_service.fetch_html_threadsafe(url)
                    
                    # If static fetch failed/blocked, try browser (Playwright)
                    if not html:
                        print(f"⚠️ Static fetch failed/blocked. Retrying with Browser (Playwright)...")
                        html = await scraper_service.fetch_html_with_browser(url)
                    
                    if not html:
                        raise Exception("Failed to fetch HTML")
                    
                    # Run Gemini Analysis
                    gemini_response = await gemini_service.analyze_html(html, url)

                    if gemini_response:
                        # gemini_response could be JSON string or dict
                        try:
                            if isinstance(gemini_response, dict):
                                parsed = gemini_response
                            else:
                                parsed = json.loads(gemini_response)
                            final_data = parsed
                            source = "gemini_html_parser"

                            # Validate title presence
                            if not final_data.get("title"):
                                print(f"⚠️ Gemini returned empty title. Response preview: {str(gemini_response)[:400]}")
                                raise Exception("Gemini returned empty title")
                            print(f"✅ Gemini successfully extracted product info: {final_data.get('title', 'N/A')[:50]}...")
                            
                            # --- THE BRAIN: AI Analytics ---
                            # Check if Gemini already returned valid AI analysis
                            ai_analysis = final_data.get("ai_analysis")
                            has_jargon = ai_analysis and isinstance(ai_analysis.get("jargon_buster"), list) and len(ai_analysis.get("jargon_buster")) > 0
                            has_eco = ai_analysis and isinstance(ai_analysis.get("eco_analysis"), dict) and ai_analysis.get("eco_analysis").get("score")
                            
                            if has_jargon and has_eco:
                                print(f"🧠 AI Analytics already present in Gemini response. Skipping extra calls.")
                            else:
                                # Fallback: Run individual agents if missing
                                print(f"🧠 Missing some AI Analytics, running fallback agents...")
                                specs_text = json.dumps(final_data.get("specs", {}))
                                full_desc = f"{final_data.get('title')} {specs_text}"
                                
                                task_jargon = None
                                task_eco = None
                                
                                if not has_jargon:
                                    print("   - Running Jargon Buster agent...")
                                    task_jargon = gemini_service.clean_jargon(full_desc)
                                
                                if not has_eco:
                                     print("   - Running Eco-Meter agent...")
                                     task_eco = gemini_service.calculate_eco_score(full_desc)
                                
                                # Run concurrently
                                tasks = []
                                if task_jargon: tasks.append(task_jargon)
                                if task_eco: tasks.append(task_eco)
                                
                                if tasks:
                                    results = await asyncio.gather(*tasks)
                                    
                                    # Map results back
                                    res_idx = 0
                                    if not final_data.get("ai_analysis"):
                                        final_data["ai_analysis"] = {}
                                        
                                    if task_jargon:
                                        final_data["ai_analysis"]["jargon_buster"] = results[res_idx]
                                        res_idx += 1
                                    
                                    if task_eco:
                                        final_data["ai_analysis"]["eco_analysis"] = results[res_idx]
                            # -------------------------------

                        except json.JSONDecodeError as e:
                            print(f"⚠️ Gemini returned invalid JSON: {e}")
                            print(f"Raw response (first 500 chars): {gemini_response[:500] if isinstance(gemini_response, str) else str(gemini_response)[:500]}")
                            raise Exception("Gemini JSON parse failed")
                    else:
                        print("⚠️ Gemini returned None/empty response")
                        raise Exception("Gemini analysis returned None")

                except Exception as e:
                    print(f"⚠️ Gemini HTML Analysis Failed ({e}). Falling back to manual scraper.")
                    # Fallback: Try manual scraping
                    try:
                        final_data = await scraper_service.scrape_product_url(url)
                        source = "deep_scraper"
                        if not final_data.get("title"):
                            raise Exception("Manual scraper returned empty result")
                    except Exception as e2:
                        print(f"⚠️ Manual Scraper also failed ({e2}). Using Generic Adapter.")
                        html = await scraper_service.fetch_html_threadsafe(url)
                        if html:
                            final_data = generic_adapter.extract(html, url)
                            source = "generic_fallback"
                        else:
                            # If even generic adapter can't fetch (likely 403 block), return a clear error
                            raise HTTPException(
                                status_code=403,
                                detail="Site blocked (403). Try providing a product name or image instead."
                            )

        # ==========================================
        # SCENARIO 2: User Uploaded an Image
        # ==========================================
        elif image:
            print("📷 Analyzing Image...")
            contents = await image.read()
            raw_json = await gemini_service.analyze_image(contents)
            if raw_json:
                try:
                    if isinstance(raw_json, dict):
                        final_data = raw_json
                    else:
                        # Try parse JSON, else place raw text into specs
                        try:
                            final_data = json.loads(raw_json)
                        except Exception:
                            final_data = {
                                "title": (raw_json[:200] if isinstance(raw_json, str) else "Image Analysis"),
                                "specs": {"raw_response": raw_json},
                                "images": []
                            }
                    # Vision rarely returns URLs; ensure images is list
                    final_data.setdefault("images", [])
                    source = "gemini_vision"
                except Exception:
                    final_data = {"title": "Image Analysis Failed", "specs": {"error": "Gemini API returned invalid data"}, "images": []}
                    source = "gemini_vision_error"
            else:
                final_data = {"title": "Image Analysis Failed", "specs": {"error": "Gemini API unavailable or failed"}, "images": []}
                source = "gemini_error"

        # ==========================================
        # SCENARIO 3: User Provided Product Name Only
        # ==========================================
        elif product_name:
            print(f"🔍 Analyzing Product Name: {product_name}")
            prompt = f"Provide product information for: {product_name}. Return JSON with keys: title, price (estimated), specs (object), currency."
            raw_json = await gemini_service.ask_gemini(prompt)
            if raw_json:
                try:
                    if isinstance(raw_json, dict):
                        final_data = raw_json
                    else:
                        final_data = json.loads(raw_json)
                    source = "gemini_text_search"
                except Exception:
                    final_data = {
                        "title": product_name,
                        "specs": {"description": raw_json},
                        "price": None
                    }
                    source = "gemini_text_search_fallback"
            else:
                final_data = {
                    "title": product_name,
                    "specs": {},
                    "price": None
                }
                source = "product_name_only"

        # ==========================================
        # FINALIZATION
        # ==========================================
        if not final_data:
            raise HTTPException(status_code=400, detail="Please provide either a URL, image, or product name.")

        # Ensure final_data is a dict
        if not isinstance(final_data, dict):
            try:
                final_data = json.loads(final_data)
            except Exception:
                # fallback wrap
                final_data = {"title": str(final_data)}

        # Ensure platform is set based on URL if missing
        if url:
            final_data.setdefault("platform", platform_from_url(url))

        # Validate price fields - trust Gemini to return numbers
        # Only do minimal validation/cleaning if absolutely necessary
        for key in ("price", "original_price"):
            v = final_data.get(key)
            if isinstance(v, str):
                # Gemini should have returned a number, but if it's a string, try simple conversion
                try:
                    cleaned = str(v).replace(',', '').replace('₹', '').replace('Rs', '').replace('Rs.', '').replace('$', '').replace(' ', '').strip()
                    if cleaned and cleaned.lower() not in ('null', 'none', 'n/a', '-'):
                        converted = float(cleaned)
                        if converted > 0:
                            final_data[key] = converted
                            print(f"⚠️ Converted {key} from string '{v}' to number {converted}")
                        else:
                            final_data[key] = None
                    else:
                        final_data[key] = None
                except (ValueError, TypeError):
                    print(f"⚠️ Could not convert {key} string '{v}' to number, setting to None")
                    final_data[key] = None

        price = final_data.get("price")
        original_price = final_data.get("original_price")
        discount_percentage = None

        if _is_number(price) and _is_number(original_price) and original_price > price:
            discount_percentage = round(((original_price - price) / original_price) * 100, 2)

        # Ensure outputs for Pydantic model
        response = {
            "product_id": final_data.get("product_id"),
            "platform": final_data.get("platform", "generic"),
            "title": final_data.get("title"),
            "price": price,
            "original_price": original_price,
            "discount_percentage": discount_percentage,
            "currency": final_data.get("currency"),
            "specs": final_data.get("specs", {}) or {},
            "specs": final_data.get("specs", {}) or {},
            "ai_analysis": final_data.get("ai_analysis", {}),
            "images": final_data.get("images", []) or [],
            "source": source
        }

        # Debug logs if price missing (helps troubleshooting)
        if response["price"] is None:
            preview = None
            try:
                preview = json.dumps(final_data)[:500]
            except Exception:
                preview = str(final_data)[:500]
            print("⚠️ Price missing in final parsed result. Source:", source)
            
            # Enhanced Debugging for missing price
            if 'html' in locals() and html:
                try:
                    from bs4 import BeautifulSoup
                    debug_soup = BeautifulSoup(html, "html.parser")
                    page_title = debug_soup.title.string if debug_soup.title else "No Title"
                    print(f"⚠️ Debug Info - HTML Length: {len(html)}")
                    print(f"⚠️ Debug Info - Page Title: {page_title.strip() if page_title else 'None'}")
                    body_text = debug_soup.body.get_text(separator=' ', strip=True)[:200] if debug_soup.body else "No Body"
                    print(f"⚠️ Debug Info - Body Start: {body_text}")
                except Exception as e:
                    print(f"⚠️ Error getting debug info: {e}")
            
            print("Preview of parsed data:", preview)

        # Persist to Database
        try:
            if response["title"] and response.get("product_id"):
                # Check if product already exists
                product = db.query(Product).filter(
                    Product.product_id == response["product_id"],
                    Product.platform == response["platform"]
                ).first()
                
                if product:
                    # Update existing product
                    product.title = response["title"]
                    product.specs = response["specs"]
                    product.ai_analysis = response.get("ai_analysis", {})
                    product.images = response["images"]
                    product.source_url = url
                    print(f"🔄 Updating existing product: {response['title'][:50]}...")
                else:
                    # Create new product
                    product = Product(
                        product_id=response["product_id"],
                        platform=response["platform"],
                        title=response["title"],
                        specs=response["specs"],
                        ai_analysis=response.get("ai_analysis", {}),
                        images=response["images"],
                        source_url=url,
                        fingerprint=None  # TODO: Generate fingerprint with Gemini embeddings
                    )
                    db.add(product)
                    db.flush()  # Flush to get the ID
                    print(f"🆕 Creating new product: {response['title'][:50]}...")
                
                # Save price point if price exists
                if response["price"] is not None:
                    price_history = PriceHistory(
                        product_id=product.id,
                        price=response["price"],
                        currency=response.get("currency", "INR"),
                        title=response.get("title"),  # Store product title at time of recording
                        list_price=response.get("original_price")  # Store original_price as list_price
                    )
                    db.add(price_history)
                    print(f"📈 Saving Price Point: {response['price']} for product: {response.get('title', 'N/A')[:50]}")
                
                db.commit()
                print(f"✅ Successfully saved product and price to database")
                
            elif response["title"] and not response.get("product_id"):
                # Product without product_id - can't save without unique identifier
                print(f"⚠️ Skipping database save: Product has no product_id")
        except Exception as e:
            db.rollback()
            print(f"⚠️ Error saving to database: {e}")
            traceback.print_exc()
            # Don't fail the request if DB save fails

        return response

    except HTTPException:
        raise
    except Exception as e:
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
