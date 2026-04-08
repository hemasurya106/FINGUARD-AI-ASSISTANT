# app/services/gemini_service.py
import os
import re
import json
import time
import traceback
from typing import Optional, Tuple, Any, Dict
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

# Gemini SDK
try:
    import google.generativeai as genai
except Exception:
    genai = None

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_AVAILABLE = False
if GEMINI_API_KEY and genai:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
    except Exception as e:
        print(f"Warning: Failed to configure Gemini API: {e}")
        GEMINI_AVAILABLE = False
else:
    print("Warning: GEMINI_API_KEY not found or gemini SDK unavailable")
    GEMINI_AVAILABLE = False

# -------------------------
# Price parsing helper
# -------------------------
_PRICE_RE = re.compile(
    r'(?P<currency>₹|Rs\.?|INR|\$|USD|€|EUR|£|USD)?\s*'
    r'(?P<number>\d{1,3}(?:[,.\s]\d{2,3})*(?:\.\d{1,2})?)'
    r'(?:\s*(?P<suffix>INR|USD|Rs\.?|₹))?',
    re.IGNORECASE
)


def parse_price(text: str) -> Tuple[Optional[float], Optional[str]]:
    """
    Try to parse a price string into (value: float or None, currency: str or None).
    Handles: "₹1,299", "Rs. 1,299", "1,299 INR", "$1299.99", "1299.00", "₹ 1,29,999"
    """
    if text is None:
        return None, None
    s = str(text).strip()
    if not s:
        return None, None
    s = s.replace('\xa0', ' ').replace('\u2009', ' ')  # Replace non-breaking spaces
    # Remove "Price:" prefixes, newlines, and common prefixes
    s = re.sub(r'^(?:[Pp]rice|MRP|M\.R\.P\.|Cost)[:\s]*', '', s)
    s = re.sub(r'\s+', ' ', s)  # Normalize whitespace
    
    # Try regex
    match = _PRICE_RE.search(s)
    if match:
        currency = match.group('currency') or match.group('suffix')
        num = match.group('number')
        # Normalize number - remove commas, spaces, but keep decimal point
        num = num.replace(',', '').replace(' ', '').replace('\u202f', '')
        try:
            price_val = float(num)
            # Normalize currency
            if currency:
                currency = currency.upper()
                if currency in ('₹', 'RS', 'RS.'):
                    currency = 'INR'
                elif currency == '$':
                    currency = 'USD'
            return price_val, currency
        except (ValueError, TypeError):
            return None, (currency.upper() if currency else None)
    
    # Fallback: find first number-like substring (more aggressive)
    num_match = re.search(r'\d{1,3}(?:[,.\s]\d{2,3})*(?:\.\d{1,2})?', s)
    if num_match:
        raw = num_match.group(0).replace(',', '').replace(' ', '').replace('\u202f', '')
        try:
            return float(raw), None
        except (ValueError, TypeError):
            return None, None
    return None, None


# -------------------------
# HTML extraction helper
# -------------------------
def _extract_relevant_html(html_content: str, url: str) -> str:
    """Extract only relevant MAIN PRODUCT sections from HTML, excluding related products"""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html_content, "html.parser")
    relevant_parts = []

    # Find main product container (exclude related products sections)
    main_container = None
    for container_sel in [
        "#centerCol",  # Amazon main column
        "#rightCol",  # Amazon right column (price box)
        "#dp-container",  # Amazon product container
        "[data-automation-id='product-price']",  # Amazon price automation
        "._1YokD2._3Mn1Gg",  # Flipkart main container
        ".col.col-7-12",  # Flipkart product info column
        ".aMaAEs",  # Flipkart product pricing section
        ".product-comp-detail",  # Snapdeal product detail section
        ".product-detail-price",  # Snapdeal price section
        ".pdp-comp-product-price",  # Snapdeal product price
        ".product-main-info",  # Generic
        "#product-info",  # Generic
    ]:
        container = soup.select_one(container_sel)
        if container:
            main_container = container
            break

    # Title selectors (including schema.org) - from main container only
    title_elem = None
    if main_container:
        title_elem = main_container.select_one("#productTitle, h1, [itemprop='name']")
    if not title_elem:
        title_elem = soup.select_one("#productTitle, h1, title, [itemprop='name']")
    
    if title_elem:
        title_text = title_elem.get_text(strip=True)
        relevant_parts.append(f"Title: {title_text}")

    # Meta price tags (OG / schema / product:price:amount) - always reliable
    meta_price = None
    for sel in [
        "meta[property='product:price:amount']",
        "meta[property='og:price:amount']",
        "meta[name='product:price:amount']",
        "meta[itemprop='price']",
        "meta[property='product:price:amount:standard']",
    ]:
        m = soup.select_one(sel)
        if m and m.get('content'):
            meta_price = m.get('content')
            break

    meta_currency = None
    for sel in [
        "meta[property='product:price:currency']",
        "meta[itemprop='priceCurrency']",
        "meta[name='og:price:currency']",
        "meta[name='product:price:currency']",
    ]:
        m = soup.select_one(sel)
        if m and m.get('content'):
            meta_currency = m.get('content')
            break

    if meta_price:
        relevant_parts.append(f"MetaPrice (Structured Data): {meta_price} {meta_currency or ''}")

    # Extract ALL price-related text from main product area
    price_sections = []
    
    # Look for price elements in main container first, then fallback to full page
    search_scope = main_container if main_container else soup
    
    # Flipkart-specific price selectors (highest priority for Flipkart)
    flipkart_price_selectors = [
        "._30jeq3._16Jk6d",  # Flipkart current price
        "._30jeq3",  # Flipkart price (class)
        ".aMaAEs ._30jeq3",  # Flipkart price in pricing section
        "[class*='_30jeq3']",  # Flipkart price (any element with this class)
    ]
    
    # Flipkart MRP selectors (separate to ensure we capture both)
    flipkart_mrp_selectors = [
        "._3I9_wc",  # Flipkart MRP/Original price
        "._2p6lqe",  # Flipkart price variant
        "[class*='_3I9_wc']",  # Flipkart MRP (any element with this class)
        ".aMaAEs ._3I9_wc",  # Flipkart MRP in pricing section
    ]
    
    # Amazon-specific price selectors
    amazon_price_selectors = [
        "#priceblock_dealprice",  # Deal price
        "#priceblock_ourprice",  # Our price
        "#priceblock_saleprice",  # Sale price (MRP)
        ".a-price .a-offscreen",  # Hidden price (most accurate)
        ".a-price-whole",  # Whole number part
        ".a-price-fraction",  # Decimal part
        "[data-automation-id='product-price']",  # Amazon automation
    ]
    
    # Snapdeal-specific price selectors
    snapdeal_price_selectors = [
        ".pdp-comp-price .payBlkBig",  # Snapdeal current price
        ".pdp-comp-price .product-price",  # Snapdeal price
        ".payBlkBig",  # Snapdeal big price display
        ".product-price",  # Snapdeal generic price
        ".pdp-e-i-PAY-r",  # Snapdeal price container
        "[itemprop='price']",  # Schema.org price
    ]
    
    # Try platform-specific selectors first
    if "snapdeal" in url.lower():
        for sel in snapdeal_price_selectors:
            nodes = search_scope.select(sel) if "*" in sel or "[" in sel else [search_scope.select_one(sel)]
            nodes = [n for n in nodes if n]  # Filter None
            for node in nodes[:5]:  # Limit to first 5 matches
                text = node.get_text(separator=" ", strip=True)
                if text and ("Rs" in text or "₹" in text) and len(text) < 100:
                    if text not in price_sections:
                        price_sections.append(f"Price Element [{sel}]: {text}")
    elif "flipkart" in url.lower():
        # Extract current price
        for sel in flipkart_price_selectors:
            nodes = search_scope.select(sel)  # Use select (not select_one) for class-based selectors
            for node in nodes[:5]:  # Limit to first 5 matches
                text = node.get_text(separator=" ", strip=True)
                if text and "₹" in text and len(text) < 100:  # Flipkart prices contain ₹
                    if text not in price_sections:
                        price_sections.append(f"Price Element [{sel}]: {text}")
        # Extract MRP/original price separately
        for sel in flipkart_mrp_selectors:
            nodes = search_scope.select(sel) if "*" in sel or "[" in sel else [search_scope.select_one(sel)]
            nodes = [n for n in nodes if n]  # Filter None
            for node in nodes[:5]:  # Limit to first 5 matches
                text = node.get_text(separator=" ", strip=True)
                if text and ("₹" in text or "Rs" in text) and len(text) < 100:
                    if text not in price_sections:
                        price_sections.append(f"MRP/Original Price Element [{sel}]: {text}")
    
    # Try Amazon selectors
    for sel in amazon_price_selectors:
        node = search_scope.select_one(sel)
        if node:
            text = node.get_text(separator=" ", strip=True)
            if text and text not in price_sections:
                price_sections.append(f"Price Element [{sel}]: {text}")
    
    # Generic price selectors
    generic_price_selectors = [
        "#price", ".product-price", ".selling-price", ".offer-price",
        "[data-price]", "[data-product-price]", ".price-whole", ".priceText",
        ".a-text-price",  # Strikethrough price (MRP)
    ]
    
    for sel in generic_price_selectors:
        node = search_scope.select_one(sel)
        if node:
            text = node.get_text(separator=" ", strip=True)
            if text and len(text) < 200 and text not in [p.split(": ", 1)[-1] for p in price_sections]:
                price_sections.append(f"Price Element [{sel}]: {text}")
    
    # Also search for price patterns in text near title (fallback)
    if not price_sections and title_elem:
        # Look for price-like patterns in text content near title
        title_parent = title_elem.parent
        if title_parent:
            nearby_text = title_parent.get_text(separator=" ", strip=True)[:2000]  # First 2000 chars
            # Look for currency symbol followed by numbers (₹ or Rs)
            price_patterns = re.findall(r'(?:₹|Rs\.?)\s*[\d,]+(?:\.\d{2})?', nearby_text, re.IGNORECASE)
            for pattern in price_patterns[:5]:  # Limit to first 5 matches
                if pattern not in price_sections:
                    price_sections.append(f"Price Pattern (near title): {pattern}")
    
    # For Snapdeal: Also search more broadly in the page if still no price found
    if not price_sections and "snapdeal" in url.lower():
        # Look for common Snapdeal price patterns in the entire page
        page_text = soup.get_text(separator=" ", strip=True)
        # Find all price patterns (Rs. followed by numbers)
        all_price_patterns = re.findall(r'Rs\.\s*[\d,]+(?:\.\d{2})?', page_text, re.IGNORECASE)
        # Filter to reasonable prices (likely product prices, not spec numbers)
        for pattern in all_price_patterns[:10]:  # Check first 10 matches
            # Extract number
            num_match = re.search(r'[\d,]+', pattern.replace(',', ''))
            if num_match:
                try:
                    price_val = float(num_match.group(0).replace(',', ''))
                    # Filter out very small numbers (likely specs) and very large ones
                    if 10 <= price_val <= 1000000:  # Reasonable product price range
                        if pattern not in price_sections:
                            price_sections.append(f"Price Pattern (page-wide): {pattern}")
                            if len(price_sections) >= 5:  # Limit total
                                break
                except:
                    pass
    
    if price_sections:
        relevant_parts.append("=== PRICE INFORMATION ===")
        relevant_parts.extend(price_sections)
    
    # Look for MRP/Original price indicators near price
    mrp_selectors = [
        ".a-text-strike", ".a-text-price",  # Amazon
        "._3I9_wc", "[class*='_3I9_wc']",  # Flipkart MRP
        "._2p6lqe", "[class*='_2p6lqe']",  # Flipkart MRP variant
        ".pdp-comp-price .pdp-e-i-PAY-l",  # Snapdeal MRP container
        "[class*='strike']", ".mrp", ".original-price",
        "[class*='mrp']", "[class*='original']",
        "del", "s",  # HTML strikethrough elements
    ]
    mrp_texts = []
    for sel in mrp_selectors:
        mrp_nodes = search_scope.select(sel) if ("class" in sel and "*" in sel) or sel in ["del", "s"] else [search_scope.select_one(sel)] if search_scope.select_one(sel) else []
        for mrp_elem in mrp_nodes[:5]:  # Increased limit for better coverage
            if not mrp_elem:
                continue
            text = mrp_elem.get_text(strip=True)
            if text and ("₹" in text or "Rs" in text or re.search(r'\d', text)) and len(text) < 100:
                mrp_texts.append(f"MRP/Original Price [{sel}]: {text}")
    
    # Also look for discount percentage text (e.g., "84% off", "Save 84%")
    discount_texts = []
    if "flipkart" in url.lower():
        # Look for discount percentage in Flipkart pricing section
        discount_selectors = [
            "._3Ay6Sb",  # Flipkart discount percentage
            "[class*='_3Ay6Sb']",  # Flipkart discount variant
            ".aMaAEs",  # Flipkart pricing section (may contain discount)
        ]
        for sel in discount_selectors:
            discount_nodes = search_scope.select(sel) if "*" in sel else [search_scope.select_one(sel)] if search_scope.select_one(sel) else []
            for discount_elem in discount_nodes[:3]:
                if not discount_elem:
                    continue
                text = discount_elem.get_text(strip=True)
                # Look for percentage patterns like "84% off", "Save 84%", "84% discount"
                if text and re.search(r'\d+%\s*(?:off|discount|save)', text, re.IGNORECASE):
                    discount_texts.append(f"Discount Info [{sel}]: {text}")
    
    if mrp_texts:
        relevant_parts.extend(mrp_texts[:8])  # Increased limit for better MRP extraction
    if discount_texts:
        relevant_parts.append("=== DISCOUNT INFORMATION ===")
        relevant_parts.extend(discount_texts[:5])

    # JSON-LD structured data (extract price from script tags)
    jsonld_scripts = soup.select("script[type='application/ld+json']")
    if jsonld_scripts:
        relevant_parts.append("=== STRUCTURED DATA (JSON-LD) ===")
        for script in jsonld_scripts[:3]:  # Check more scripts
            try:
                script_text = script.string
                if script_text and ("price" in script_text.lower() or "offers" in script_text.lower() or "priceCurrency" in script_text):
                    # Extract more context (increase limit for better extraction)
                    if len(script_text) > 1500:
                        relevant_parts.append(f"JSON-LD (excerpt): {script_text[:1500]}...")
                    else:
                        relevant_parts.append(f"JSON-LD: {script_text}")
            except:
                pass
    
    # Also check for inline script tags with price data (common in Flipkart)
    inline_scripts = soup.select("script")
    for script in inline_scripts[:5]:
        try:
            script_text = script.string
            if script_text and ("price" in script_text.lower() or "offers" in script_text.lower()) and len(script_text) < 2000:
                # Look for price patterns in inline scripts
                if "₹" in script_text or "price" in script_text.lower():
                    relevant_parts.append(f"Inline Script (price data): {script_text[:800]}")
                    break  # Only add first match
        except:
            pass

    # Schema / specs
    specs_section = search_scope.select_one(
        "#productDetails_techSpec_section_1, #feature-bullets, .product-specs, [itemprop='description'], #specs"
    )
    if specs_section:
        specs_text = specs_section.get_text(separator=" | ", strip=True)[:1000]
        relevant_parts.append(f"Specs: {specs_text}")

    desc_section = search_scope.select_one(
        "#productDescription, .product-description, [data-feature-name='productDescription'], [itemprop='description']"
    )
    if desc_section:
        desc_text = desc_section.get_text(strip=True)[:800]
        relevant_parts.append(f"Description: {desc_text}")

    # Include URL hint at the start
    relevant_parts.insert(0, f"URL: {url}")

    # Add note about scope
    if main_container:
        relevant_parts.insert(1, "NOTE: Content extracted from MAIN PRODUCT section only (related products excluded)")

    result = "\n\n".join(relevant_parts)
    
    # ---------------------------------------------------------
    # FALLBACK: If extraction yielded very little data, include raw text
    # ---------------------------------------------------------
    # If we have very little content and NO price/meta info, append raw text
    # This happens when Amazon changes layout or we get a "mobile" view or similar
    if len(result) < 1000 and "Price" not in result and "MetaPrice" not in result:
        print(f"⚠️ Extraction yielded low content ({len(result)} chars). Appending raw text fallback.")
        try:
            # Get text from body, stripping scripts/styles
            body = soup.body
            if body:
                for script in body(["script", "style", "noscript"]):
                    script.extract()
                raw_text = body.get_text(separator=" ", strip=True)
                # Take first 10k chars (enough for title + price usually)
                raw_chunk = raw_text[:10000]
                result += f"\n\n=== FALLBACK RAW TEXT (Extraction failed to find specific sections) ===\n{raw_chunk}"
        except Exception as e:
            print(f"⚠️ Error appending raw text fallback: {e}")

    # Caption text from main container
        if main_container:
            for caption in main_container.select(".imgTagWrapper img, .a-dynamic-image"):
                 alt = caption.get("alt")
                 if alt:
                     relevant_parts.append(f"Image Alt Text: {alt}")

    # =================================================
    # IMAGE EXTRACTION STRATEGY
    # =================================================
    image_candidates = []
    
    # 1. Meta Tags (High Quality, Standard)
    for sel in [
        "meta[property='og:image']",
        "meta[property='twitter:image']", 
        "link[rel='image_src']",
        "meta[itemprop='image']"
    ]:
        for m in soup.select(sel):
            img_url = m.get("content") or m.get("href")
            if img_url:
                image_candidates.append(f"Image Candidate (Meta): {img_url}")
                
    # 2. Platform Specific Selectors (Main Product Image)
    platform_image_selectors = [
        # Amazon
        "#landingImage", "#imgBlkFront", "img#main-image", 
        ".a-dynamic-image", "[data-a-dynamic-image]",
        # Flipkart
        "img._396cs4", ".CXW8mj img", "._2r_T1I",
        # Myntra/Generic
        ".image-grid-image", ".product-image"
    ]
    
    for sel in platform_image_selectors:
        # Search in main container if available, else soup
        scope = main_container if main_container else soup
        for img in scope.select(sel):
            # Try src first
            src = img.get("src")
            # Amazon stores hi-res in data-a-dynamic-image/data-old-hires
            data_dynamic = img.get("data-a-dynamic-image")
            data_hires = img.get("data-old-hires")
            
            if data_dynamic:
                # It's a JSON dict string of url->dims
                try:
                    # simplistic extraction of the first key (url)
                    # format: {"https://...jpg":[x,y], ...}
                     # Find all http/https links
                     urls = re.findall(r'https?://[^"]+', data_dynamic)
                     for u in urls:
                         image_candidates.append(f"Image Candidate (Amazon Dynamic): {u}")
                except:
                    pass
            
            if data_hires:
                image_candidates.append(f"Image Candidate (Amazon HiRes): {data_hires}")
                
            if src and "base64" not in src[:30]: # Skip base64 placeholders
                image_candidates.append(f"Image Candidate (Selector {sel}): {src}")

    # 3. JSON-LD Image
    # (Already parsed somewhat in _parse_jsonld_prices but we can do a quick check here or rely on Gemini to see it if we included JSON-LD text)
    # The existing JSON-LD block in this function might contain "image": "url" which Gemini will see.
    
    if image_candidates:
        # Deduplicate
        unique_images = list(set(image_candidates))
        relevant_parts.append("=== DETECTED IMAGES ===")
        relevant_parts.extend(unique_images[:10]) # Limit to top 10 to avoid noise

    result = "\n\n".join(relevant_parts)
    
    # ---------------------------------------------------------
    # FALLBACK: If extraction yielded very little data, include raw text
    # ---------------------------------------------------------
    # If we have very little content and NO price/meta info, append raw text
    # This happens when Amazon changes layout or we get a "mobile" view or similar
    if len(result) < 1000 and "Price" not in result and "MetaPrice" not in result:
        print(f"⚠️ Extraction yielded low content ({len(result)} chars). Appending raw text fallback.")
        try:
            # Get text from body, stripping scripts/styles
            body = soup.body
            if body:
                for script in body(["script", "style", "noscript"]):
                    script.extract()
                raw_text = body.get_text(separator=" ", strip=True)
                # Take first 10k chars (enough for title + price usually)
                raw_chunk = raw_text[:10000]
                result += f"\n\n=== FALLBACK RAW TEXT (Extraction failed to find specific sections) ===\n{raw_chunk}"
        except Exception as e:
            print(f"⚠️ Error appending raw text fallback: {e}")

    # Check for Captcha/Blocking keywords
    lower_res = result.lower()
    if "robot check" in lower_res or "captcha" in lower_res or "enter the characters you see below" in lower_res:
        result = "⚠️ WARNING: PAGE APPEARS TO BE A CAPTCHA/BLOCKING PAGE\n\n" + result

    return result


def _extract_price_from_html(html_content: str, url: str) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    """
    Fallback: Extract price directly from HTML using BeautifulSoup.
    Returns (price, original_price, currency) tuple.
    """
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")
        
        price = None
        original_price = None
        currency = None
        
        # Try meta tags first (most reliable)
        meta_price = None
        for sel in [
            "meta[property='product:price:amount']",
            "meta[property='og:price:amount']",
            "meta[name='product:price:amount']",
            "meta[itemprop='price']",
        ]:
            m = soup.select_one(sel)
            if m and m.get('content'):
                meta_price = m.get('content')
                break
        
        if meta_price:
            try:
                price = float(str(meta_price).replace(',', ''))
            except (ValueError, TypeError):
                pass
        
        # Try currency from meta
        for sel in [
            "meta[property='product:price:currency']",
            "meta[itemprop='priceCurrency']",
        ]:
            m = soup.select_one(sel)
            if m and m.get('content'):
                currency = m.get('content').upper()
                break
        
        # Try visible price elements
        if not price:
            price_selectors = [
                "#priceblock_ourprice", "#priceblock_dealprice", "#price",
                ".a-price-whole", ".a-price .a-offscreen",
                ".product-price", ".selling-price", ".offer-price",
                "[data-price]", "[data-product-price]"
            ]
            for sel in price_selectors:
                node = soup.select_one(sel)
                if node:
                    text = node.get_text(strip=True)
                    if text:
                        p, c = parse_price(text)
                        if p:
                            price = p
                            if c and not currency:
                                currency = c
                            break
        
        # Try to find MRP/original price
        mrp_selectors = [
            "#priceblock_saleprice", ".a-price.a-text-price",
            ".original-price", ".mrp", "[data-original-price]"
        ]
        for sel in mrp_selectors:
            node = soup.select_one(sel)
            if node:
                text = node.get_text(strip=True)
                if text:
                    p, _ = parse_price(text)
                    if p:
                        original_price = p
                        break
        
        # Infer currency from URL if not found
        if not currency and url:
            if any(domain in url.lower() for domain in ['amazon.in', 'flipkart', 'nykaa', 'myntra', 'croma']):
                currency = "INR"
            elif 'amazon.com' in url.lower():
                currency = "USD"
        
        return price, original_price, currency
    except Exception as e:
        print(f"⚠️ Error extracting price from HTML fallback: {e}")
        return None, None, None


# -------------------------
# JSON extraction helper (balanced braces)
# -------------------------
def _extract_first_json_object(text: str) -> Optional[str]:
    """
    Find the first balanced JSON object substring (from first '{' to matching '}').
    Returns the substring or None.
    """
    if not text:
        return None
    start = text.find('{')
    if start == -1:
        return None
    depth = 0
    in_string = False
    escaped = False
    for i in range(start, len(text)):
        ch = text[i]
        if ch == '"' and not escaped:
            in_string = not in_string
        if ch == '\\' and not escaped:
            escaped = True
            continue
        else:
            escaped = False
        if in_string:
            continue
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    # if we get here, incomplete JSON; return slice to end (caller can attempt fixes)
    return text[start:]


def _extract_json_from_response(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON-like object from Gemini response safely and return parsed Python dict.
    Handles markdown code blocks and incomplete JSON.
    Returns None if parsing fails.
    """
    if not text or not text.strip():
        return None

    # First, remove markdown code blocks completely
    # Handle both ```json and ``` patterns
    cleaned_text = text
    # Remove opening ```json or ```
    cleaned_text = re.sub(r'^```(?:json)?\s*\n?', '', cleaned_text, flags=re.MULTILINE)
    # Remove closing ```
    cleaned_text = re.sub(r'\n?```\s*$', '', cleaned_text, flags=re.MULTILINE)
    cleaned_text = cleaned_text.strip()

    # Try to locate first balanced JSON substring
    candidate = _extract_first_json_object(cleaned_text)
    if candidate is None:
        # If still nothing, try original text
        candidate = _extract_first_json_object(text)
        if candidate is None:
            return None

    # Clean up trailing commas before closing braces/brackets
    candidate = re.sub(r',\s*}', '}', candidate)
    candidate = re.sub(r',\s*]', ']', candidate)

    # Attempt parse; if fails, attempt fixes and retry
    tries = 0
    while tries < 5:  # More retries for better recovery
        try:
            parsed = json.loads(candidate)
            return parsed
        except json.JSONDecodeError as e:
            # Store original for debugging
            original_candidate = candidate
            
            # common quick fixes:
            candidate = candidate.rstrip()
            
            # Close unclosed objects/arrays by counting braces
            open_braces = candidate.count('{')
            close_braces = candidate.count('}')
            if open_braces > close_braces:
                candidate = candidate + ('}' * (open_braces - close_braces))
            
            open_brackets = candidate.count('[')
            close_brackets = candidate.count(']')
            if open_brackets > close_brackets:
                candidate = candidate + (']' * (open_brackets - close_brackets))
            
            # Fix unterminated string values such as :"}, :",] which Gemini sometimes emits
            candidate = re.sub(r':\s*"(?=[}\],])', ':""', candidate)
            
            # Replace " : nu" style with null (incomplete null)
            candidate = re.sub(r':\s*nu(?=[,}\]])', ': null', candidate)
            
            # Fix trailing commas in objects/arrays (more aggressive)
            candidate = re.sub(r',(\s*[}\]])', r'\1', candidate)
            
            # Remove problematic control characters (but keep newlines in strings)
            # Only remove truly problematic ones
            candidate = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', candidate)
            
            # If still the same after fixes, try to find and close incomplete specs object
            if candidate == original_candidate or tries >= 2:
                # Try to detect incomplete specs object and close it
                if '"specs"' in candidate and candidate.count('{') > candidate.count('}'):
                    # Find the specs opening brace
                    specs_match = re.search(r'"specs"\s*:\s*\{', candidate)
                    if specs_match:
                        # Count braces after specs
                        after_specs = candidate[specs_match.end():]
                        open_count = after_specs.count('{')
                        close_count = after_specs.count('}')
                        if open_count >= close_count:
                            # Add missing closing braces
                            missing = open_count - close_count
                            candidate = candidate + ('}' * missing)
            
            tries += 1
            continue
    
    # final attempt failed - try one more time with aggressive cleanup
    try:
        # Remove everything after last complete object structure
        last_brace = candidate.rfind('}')
        if last_brace > 0:
            # Ensure it's balanced
            test_candidate = candidate[:last_brace+1]
            open_test = test_candidate.count('{')
            close_test = test_candidate.count('}')
            if open_test == close_test:
                parsed = json.loads(test_candidate)
                print(f"⚠️ Recovered JSON by truncating incomplete content")
                return parsed
    except:
        pass
    
    print("Failed to parse JSON from Gemini response (preview):", candidate[:400])
    return None


# -------------------------
# Gemini wrappers
# -------------------------
def _ask_gemini_sync(prompt: str) -> Optional[str]:
    """Synchronous wrapper for Gemini text API"""
    if not GEMINI_AVAILABLE:
        return None
    try:
        model = genai.GenerativeModel("gemini-2.5-flash-lite")
        response = model.generate_content(prompt)
        # response may be object with .text or str
        return getattr(response, "text", str(response))
    except Exception as e:
        print(f"Gemini Error: {e}")
        return None


async def ask_gemini(prompt: str, json_mode: bool = False) -> Optional[str]:
    """Async wrapper for Gemini API (uses run_in_threadpool from caller)"""
    # Note: caller should run this in threadpool
    return _ask_gemini_sync(prompt)


def _analyze_image_sync(image_bytes: bytes) -> Optional[str]:
    """Synchronous wrapper for Gemini Vision API - returns JSON string if possible"""
    if not GEMINI_AVAILABLE:
        return None
    try:
        model = genai.GenerativeModel("gemini-2.5-flash-lite")
        prompt = "Extract product title, estimated price, and 5 key technical specs from this image. Return JSON format with keys: title, price, specs (as object)."

        from PIL import Image
        import io
        image = Image.open(io.BytesIO(image_bytes))

        # Depending on SDK, passing a list with prompt and image may work.
        # We try to call generate_content with multimodal input; this may vary by SDK version.
        try:
            response = model.generate_content([prompt, image])
        except TypeError:
            # Fallback: pass bytes if SDK expects that
            try:
                response = model.generate_content([prompt, image_bytes])
            except Exception as e:
                raise

        raw = getattr(response, "text", str(response))
        # Try to extract JSON object if present
        parsed = _extract_json_from_response(raw)
        if parsed:
            return json.dumps(parsed, ensure_ascii=False)
        # otherwise return raw text so caller can fallback
        return raw
    except Exception as e:
        print(f"Gemini Vision Error: {e}\n{traceback.format_exc()}")
        return None


async def analyze_image(image_bytes: bytes) -> Optional[str]:
    """Async wrapper for image analysis"""
    return _analyze_image_sync(image_bytes)


def _analyze_html_sync(html_content: str, url: str) -> Optional[str]:
    """Synchronous wrapper for Gemini HTML analysis that returns a JSON string"""
    if not GEMINI_AVAILABLE:
        return None
    if not html_content or not isinstance(html_content, (str, bytes)):
        return None
    try:
        model = genai.GenerativeModel("gemini-2.5-flash-lite")

        extracted_content = _extract_relevant_html(html_content, url)
        # Allow more content for better context (Gemini can handle more)
        if len(extracted_content) > 8000:
            extracted_content = extracted_content[:8000]
        
        # Debug: Log if price information is found in extracted content
        if "PRICE INFORMATION" in extracted_content or "MetaPrice" in extracted_content or "Price Element" in extracted_content:
            print(f"✅ Price information detected in extracted HTML content")
        else:
            print(f"⚠️ No price information found in extracted HTML content (length: {len(extracted_content)})")

        prompt = (
            "You are an expert e-commerce product data extraction agent. Extract product information with HIGH PRECISION.\n\n"
            "=== CRITICAL: MAIN PRODUCT ONLY ===\n"
            "- Extract information ONLY for the MAIN PRODUCT described in the URL and title\n"
            "- IGNORE all related products, recommended products, sponsored products, or other products on the page\n"
            "- Focus ONLY on the product whose title matches the main product section\n"
            "- Do NOT extract prices from 'Customers also viewed', 'Frequently bought together', or similar sections\n"
            "\n"
            "=== PRICE EXTRACTION STRATEGY ===\n"
            "1. PRIMARY SOURCES (in order of priority - MAIN PRODUCT ONLY):\n"
            "   - MetaPrice fields (meta tags - always for main product)\n"
            "   - Price Section visible text near the product title (current selling price)\n"
            "   - Schema.org/JSON-LD structured data for the main product\n"
            "   - Price Element sections (may contain multiple price formats)\n"
            "   - HTML data attributes (data-price, data-product-price) in main product container\n"
            "\n"
            "2. PLATFORM-SPECIFIC PRICE PATTERNS:\n"
            "   - SNAPDEAL: Look for '.payBlkBig', '.pdp-comp-price' classes (current price). MRP often in strikethrough\n"
            "   - FLIPKART: Look for elements with '_30jeq3' class (current price) and '_3I9_wc' class (MRP)\n"
            "   - AMAZON: Look for '.a-price .a-offscreen', '#priceblock_ourprice', etc.\n"
            "   - Prices are often formatted as: ₹229.00, ₹88,081, Rs. 228, Rs. 1,299\n"
            "   - IMPORTANT: Current selling price is usually LOWER than MRP. MRP is often struck through.\n"
            "\n"
            "3. PRICE IDENTIFICATION RULES:\n"
            "   - CURRENT PRICE: Look for 'price', 'selling price', 'offer price', 'deal price', 'special price'\n"
            "   - ORIGINAL PRICE (CRITICAL - MUST EXTRACT IF AVAILABLE):\n"
            "     * Look for 'MRP', 'M.R.P.', 'original price', 'list price', 'was', 'strikethrough price'\n"
            "     * For FLIPKART: Look for elements with '_3I9_wc' class (MRP/original price)\n"
            "     * Look for prices that are HIGHER than the current price (usually struck through)\n"
            "     * Check 'MRP/Original Price' sections in the extracted content\n"
            "     * If you see a discount percentage (e.g., '84% off'), calculate original_price if needed\n"
            "   - DISCOUNT PERCENTAGE: If you see text like '84% off', 'Save 84%', extract the percentage\n"
            "   - Extract ONLY prices that appear near the main product title and description\n"
            "   - Extract numeric value ONLY (remove currency symbols, commas, spaces)\n"
            "   - Handle formats: ₹1,299.99, Rs. 1,29,999, ₹229.00, ₹2,499, $129.99, 1299.00, 1,299 INR\n"
            "   - Convert to pure number: 1299.99 (no formatting)\n"
            "   - IMPORTANT: Look in 'Price Element' and 'MRP/Original Price' sections - they contain the actual price values\n"
            "   - CRITICAL: If current price is ₹389 and you see ₹2,499 struck through, original_price MUST be 2499.0\n"
            "\n"
            "3. AVOID THESE PRICE SOURCES:\n"
            "   - Prices from product grids or carousels\n"
            "   - Prices from 'Related Products' or 'You may also like' sections\n"
            "   - Prices from 'Customers who bought this also bought' sections\n"
            "   - Prices from sponsored product listings\n"
            "   - Prices that appear far from the main product title\n"
            "\n"
            "4. CURRENCY DETECTION:\n"
            "   - Extract from price text (₹, Rs, INR, $, USD, etc.)\n"
            "   - Check MetaPrice currency fields\n"
            "   - Infer from URL domain (.in → INR, .com → USD)\n"
            "   - Standardize: ₹/Rs/INR → 'INR', $ → 'USD'\n"
            "\n"
            "6. AI ANALYTICS (THE BRAIN):\n"
            "   - JARGON BUSTER: Identify 2-3 complex/technical terms in the specs (e.g., 'Snapdragon 8 Gen 2', 'OLED', 'Thunderbolt').\n"
            "     Provide a simple, consumer-friendly explanation for each. Focus on the BENEFIT.\n"
            "   - ECO-METER: Analyze the product description and specs for sustainability keywords (e.g., 'recycled', 'energy efficient', 'carbon neutral', 'BPA free').\n"
            "     Assign a 'score' (High/Medium/Low) and a 'badge' (Green/Yellow/Red).\n"
            "       * High/Green: Explicit sustainability features (e.g., '100% recycled aluminum').\n"
            "       * Medium/Yellow: Vague claims or minor features (e.g., 'energy saving mode').\n"
            "       * Low/Red: No mention of sustainability.\n"
            "\n"
            "=== OUTPUT FORMAT ===\n"
            "Return ONLY valid JSON (no markdown, no code blocks, no explanations):\n"
            "{\n"
            '  "title": "Product Title or null",\n'
            '  "price": 1299.99 or null,  // MUST be number, not string - MAIN PRODUCT ONLY\n'
            '  "original_price": 1999.99 or null,  // MUST be number, not string - MAIN PRODUCT ONLY (CRITICAL: Extract if available!)\n'
            '  "discount_percentage": 35.0 or null,  // MUST be number, not string - Calculate if original_price > price\n'
            '  "currency": "INR" or "USD" or null,\n'
            '  "specs": {"key": "value"},\n'
            '  "images": ["url1", "url2"],\n'
            '  "platform": "amazon/flipkart/nykaa/myntra/generic",\n'
            '  "product_id": "ID123" or null,\n'
            '  "ai_analysis": {\n'
            '      "jargon_buster": [\n'
            '          {"term": "Term", "simple_explanation": "Simple explanation"}\n'
            '      ],\n'
            '      "eco_analysis": {\n'
            '          "score": "High/Medium/Low",\n'
            '          "badge": "Green/Yellow/Red",\n'
            '          "reasoning": "Reason..."\n'
            '      }\n'
            '  }\n'
            "}\n\n"
            f"=== PAGE DATA ===\nURL: {url}\n\nExtracted Content:\n{extracted_content}\n\n"
            "=== CRITICAL INSTRUCTIONS ===\n"
            "- Extract prices as NUMERIC VALUES (float/int), NEVER as strings\n"
            "- Parse all price formats intelligently (₹1,29,999 → 129999.0, ₹229.00 → 229.0, ₹2,499 → 2499.0)\n"
            "- Extract ONLY from MAIN PRODUCT section, ignore all related/recommended products\n"
            "- Verify prices are associated with the product in the URL and title\n"
            "- Use MetaPrice and JSON-LD structured data as PRIMARY sources (most reliable)\n"
            "- Then use Price Section visible text that appears near the product title\n"
            "- For original_price/MRP (CRITICAL - MUST EXTRACT IF PRESENT):\n"
            "  * Look for strikethrough prices, 'M.R.P.', 'was', or prices higher than current price\n"
            "  * Check 'MRP/Original Price' sections in extracted content\n"
            "  * For FLIPKART: Elements with '_3I9_wc' class contain MRP\n"
            "  * If you see discount text like '84% off' and current price, calculate: original_price = price / (1 - discount/100)\n"
            "  * Example: If price=389 and discount=84%, then original_price = 389 / 0.16 = 2431.25 (round to nearest)\n"
            "- For discount_percentage: Extract from text like '84% off', 'Save 84%', or calculate: ((original_price - price) / original_price) * 100\n"
            "- If price cannot be determined, use null (not 0, not empty string)\n"
            "- Return ONLY raw JSON - NO markdown code blocks (```json), NO explanations, NO additional text\n"
            "- Start with { and end with } - return ONLY the JSON object itself\n"
            "- Ensure ALL objects and arrays are properly closed with matching braces/brackets\n"
            "- Be extremely precise: double-check prices match the main product title\n"
            "- CRITICAL: If you see both current price and original price on the page, you MUST extract BOTH\n"
        )

        max_retries = 2
        for attempt in range(max_retries):
            try:
                # Generate content with optimized config
                # Note: response_mime_type not supported in current SDK version
                try:
                    response = model.generate_content(
                        prompt,
                        generation_config={
                            "temperature": 0.0,  # Lower temperature for more precise extraction
                            "max_output_tokens": 3000,  # More tokens for complete JSON
                            "top_p": 0.8,
                            "top_k": 40,
                        }
                    )
                except Exception as api_err:
                    print(f"⚠️ Gemini API Error (Quota Exceeded or other): {api_err}")
                    return None
                raw_response = getattr(response, "text", str(response))
                if not raw_response or not raw_response.strip():
                    print("Gemini returned empty response")
                    return None
                parsed_json = _extract_json_from_response(raw_response)
                if parsed_json:
                    # Simple validation - trust Gemini to return numbers, just validate
                    def _validate_price_field(obj, key):
                        if not obj or key not in obj:
                            return
                        val = obj.get(key)
                        # Already a number - validate it's positive
                        if isinstance(val, (int, float)):
                            if val < 0 or val == 0:  # Negative or zero prices don't make sense
                                obj[key] = None
                            return
                        # If it's a string, Gemini should have converted it - log warning
                        if isinstance(val, str):
                            val = val.strip()
                            if not val or val.lower() in ('null', 'none', 'n/a', '-', ''):
                                obj[key] = None
                            else:
                                # Gemini should have converted this, but try one simple parse
                                try:
                                    # Remove common formatting and try to parse
                                    cleaned = val.replace(',', '').replace('₹', '').replace('Rs', '').replace('Rs.', '').replace('$', '').replace(' ', '').replace('INR', '').replace('USD', '')
                                    parsed_val = float(cleaned)
                                    if parsed_val > 0:
                                        obj[key] = parsed_val
                                        print(f"⚠️ Gemini returned price as string '{val}', converted to {parsed_val}")
                                    else:
                                        obj[key] = None
                                except (ValueError, TypeError):
                                    print(f"⚠️ Could not parse price string from Gemini: '{val}'")
                                    obj[key] = None
                            return
                        # Handle null/None - keep as is
                        if val is None:
                            return
                        # Try to convert other types (shouldn't happen, but defensive)
                        try:
                            if isinstance(val, bool):
                                obj[key] = None
                            else:
                                v = float(val)
                                obj[key] = v if v > 0 else None
                        except (ValueError, TypeError):
                            obj[key] = None

                    _validate_price_field(parsed_json, "price")
                    _validate_price_field(parsed_json, "original_price")
                    
                    # Validate discount_percentage if present
                    if "discount_percentage" in parsed_json:
                        discount = parsed_json.get("discount_percentage")
                        if isinstance(discount, (int, float)):
                            if discount < 0 or discount > 100:
                                parsed_json["discount_percentage"] = None
                        elif isinstance(discount, str):
                            try:
                                cleaned = discount.replace('%', '').strip()
                                discount_val = float(cleaned)
                                if 0 <= discount_val <= 100:
                                    parsed_json["discount_percentage"] = discount_val
                                else:
                                    parsed_json["discount_percentage"] = None
                            except (ValueError, TypeError):
                                parsed_json["discount_percentage"] = None
                    
                    # Calculate discount_percentage if we have both prices but no discount
                    price = parsed_json.get("price")
                    original_price = parsed_json.get("original_price")
                    if price and original_price and original_price > price and not parsed_json.get("discount_percentage"):
                        discount_calc = round(((original_price - price) / original_price) * 100, 2)
                        if 0 < discount_calc <= 100:
                            parsed_json["discount_percentage"] = discount_calc
                    
                    # Ensure currency is set if we have prices but no currency
                    if (parsed_json.get("price") or parsed_json.get("original_price")) and not parsed_json.get("currency"):
                        # Try to infer from URL or default to INR for Indian sites
                        if url and any(domain in url.lower() for domain in ['amazon.in', 'flipkart', 'nykaa', 'myntra', 'croma']):
                            parsed_json["currency"] = "INR"
                        else:
                            parsed_json["currency"] = None
                    
                    # Log if prices are missing (for debugging)
                    if not parsed_json.get("price") and not parsed_json.get("original_price"):
                        print("⚠️ Gemini didn't extract any prices from the content.")
                    elif not parsed_json.get("price"):
                        print("⚠️ Gemini extracted original_price but not current price.")
                    elif not parsed_json.get("original_price"):
                        print("ℹ️ Gemini extracted price but not original_price (this is OK if product has no MRP).")
                    
                    # Ensure minimal keys exist
                    for k in ["title", "price", "original_price", "discount_percentage", "currency", "specs", "images", "platform", "product_id", "ai_analysis"]:
                        if k not in parsed_json or parsed_json[k] is None: 
                            if k == "images":
                                parsed_json[k] = []
                            elif k == "specs":
                                parsed_json[k] = {}
                            elif k == "ai_analysis":
                                parsed_json[k] = {}
                            elif k == "ai_analysis":
                                parsed_json[k] = {"jargon_buster": [], "eco_analysis": None}
                            else:
                                parsed_json[k] = None
                    
                    # Debug logging for price extraction
                    if parsed_json.get("price"):
                        print(f"✅ Final extracted price: {parsed_json.get('price')} {parsed_json.get('currency', '')}")
                        if parsed_json.get("original_price"):
                            print(f"✅ Final extracted original_price: {parsed_json.get('original_price')} {parsed_json.get('currency', '')}")
                            if parsed_json.get("discount_percentage"):
                                print(f"✅ Final extracted discount_percentage: {parsed_json.get('discount_percentage')}%")
                        else:
                            print(f"⚠️ Original price not extracted (MRP may not be available on this page)")
                    else:
                        print(f"⚠️ No price extracted after all attempts")
                    
                    if parsed_json.get("ai_analysis"):
                         print(f"✅ AI Analysis found: {len(parsed_json['ai_analysis'].get('jargon_buster', []))} items")
                    else:
                         print("⚠️ No AI Analysis found in response")

                    return json.dumps(parsed_json, ensure_ascii=False)
                else:
                    print(f"Failed to extract JSON from response (attempt {attempt+1}): preview:\n{raw_response[:400]}")
                    # If not last attempt, try again
                    if attempt < max_retries - 1:
                        time.sleep((attempt + 1) * 2)
                        continue
                    return None
            except Exception as e:
                if "timeout" in str(e).lower() or "504" in str(e):
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 2
                        print(f"Gemini timeout, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                print(f"Gemini HTML Analysis Error: {e}\n{traceback.format_exc()}")
                return None
    except Exception as e:
        print(f"Gemini HTML Analysis Error (outer): {e}\n{traceback.format_exc()}")
        return None

def _parse_jsonld_prices(soup):
    """Parse application/ld+json blocks for price/priceCurrency/offers."""
    prices = []
    for script in soup.select("script[type='application/ld+json']"):
        try:
            txt = script.string
            if not txt:
                continue
            # Some pages include multiple JSON-LD objects concatenated -> try loads safely
            for candidate in json.loads(re.sub(r'\s+$', '', txt.strip())) if txt.strip().startswith('[') else [json.loads(txt)]:
                # If it's a product with offers
                if isinstance(candidate, dict):
                    # offers could be dict or list
                    offers = candidate.get("offers")
                    if isinstance(offers, list):
                        for o in offers:
                            p = o.get("price") or o.get("priceSpecification", {}).get("price")
                            c = o.get("priceCurrency") or o.get("currency")
                            if p:
                                prices.append((float(p), str(c).upper() if c else None, script.sourceline if hasattr(script, 'sourceline') else None))
                    elif isinstance(offers, dict):
                        p = offers.get("price") or offers.get("priceSpecification", {}).get("price")
                        c = offers.get("priceCurrency") or offers.get("currency")
                        if p:
                            prices.append((float(p), str(c).upper() if c else None, script.sourceline if hasattr(script, 'sourceline') else None))
                    # direct price field
                    if "price" in candidate and candidate.get("price"):
                        c = candidate.get("priceCurrency") or candidate.get("currency")
                        prices.append((float(candidate["price"]), str(c).upper() if c else None, script.sourceline if hasattr(script, 'sourceline') else None))
        except Exception:
            continue
    return prices

def _extract_price_from_html(html_content: str, url: str) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    """
    Extract price from HTML with strict filtering to avoid related product prices.
    Only searches within main product container, not in related/recommended sections.
    """
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Find main product container - exclude related/recommended products
        main_container = None
        main_container_selectors = [
            "#centerCol", "#rightCol", "#dp-container",  # Amazon
            "[data-automation-id='product-price']",  # Amazon
            ".product-price-info", ".product-main-info",  # Generic
            "#product-info", ".product-details", ".product-main",  # Generic
        ]
        
        # Exclude sections that contain related products
        exclude_selectors = [
            "[data-component-type='s-search-result']",  # Amazon search results
            "#HLCXComparisonWidget", "#similarities_feature_div",  # Amazon related
            ".s-widget-container", ".s-card-container",  # Amazon cards
            "[data-index]",  # Amazon grid items (often related products)
            ".recommended-products", ".related-products", ".similar-products",
            "[id*='sponsored']", "[id*='recommended']", "[id*='similar']",
            "[class*='sponsored']", "[class*='recommended']", "[class*='similar']",
            "#desktop_qualifiedBuyBox",  # Sometimes contains multiple products
        ]
        
        # Try to find main product container
        for sel in main_container_selectors:
            container = soup.select_one(sel)
            if container:
                main_container = container
                break
        
        # If no specific container found, use body but exclude related sections
        if not main_container:
            main_container = soup.find('body') or soup
        
        # Remove excluded sections from consideration
        if main_container:
            for excl_sel in exclude_selectors:
                for excl_elem in main_container.select(excl_sel):
                    excl_elem.decompose()  # Remove from tree
        
        candidates = []  # (value: float, currency: str|None, score: int, label: str, element)
        
        # Helper to check if element is in excluded section
        def is_excluded(elem):
            if not elem:
                return True
            parent = elem.parent
            depth = 0
            while parent and depth < 10:
                parent_id = parent.get('id', '')
                parent_class = ' '.join(parent.get('class', []))
                if any(excl in parent_id.lower() or excl in parent_class.lower() 
                       for excl in ['sponsored', 'recommended', 'similar', 'related', 's-search-result']):
                    return True
                parent = parent.parent
                depth += 1
            return False
        
        # Helper to add candidate with smart scoring
        def add_candidate(text, label, element=None, priority=0):
            if not text or not text.strip():
                return
            p, c = parse_price(text)
            if not p or p <= 0:
                return
            # Skip if element is in excluded section
            if element and is_excluded(element):
                return
            
            score = priority  # Start with priority
            # Meta tags get highest priority
            if label.startswith("meta:"):
                score += 1000
            # JSON-LD is very reliable
            elif label == "jsonld":
                score += 900
            # Visible selectors from main product area
            elif label.startswith("visible:"):
                score += 800
                # Amazon-specific price selectors are most reliable
                if any(sel in label for sel in ["priceblock", "a-price", "a-offscreen"]):
                    score += 100
            # Currency presence is strong signal
            if c:
                score += 50
            # Avoid regex candidates (less reliable)
            if "regex" in label.lower() or "generic" in label.lower():
                score -= 200
            
            candidates.append((float(p), c, score, label, element))

        # 1) Meta tags (highest priority - always from main product)
        meta_currency = None
        for sel in [
            "meta[property='product:price:amount']",
            "meta[property='og:price:amount']",
            "meta[name='product:price:amount']",
            "meta[itemprop='price']",
        ]:
            m = soup.select_one(sel)
            if m and m.get('content'):
                add_candidate(m.get('content'), f"meta:{sel}", m, priority=1000)

        # Meta currency
        for sel in [
            "meta[property='product:price:currency']",
            "meta[itemprop='priceCurrency']",
            "meta[name='og:price:currency']",
        ]:
            m = soup.select_one(sel)
            if m and m.get('content'):
                meta_currency = m.get('content').upper()
                break

        # 2) JSON-LD (application/ld+json) - parse structured data
        try:
            jsonld_prices = _parse_jsonld_prices(soup)
            for p, c, pos in jsonld_prices:
                candidates.append((float(p), c or meta_currency, 900, "jsonld", None))
        except Exception:
            pass

        # 3) Visible price selectors - ONLY from main product container
        if main_container:
            price_selectors = [
                "#priceblock_dealprice", "#priceblock_ourprice", "#priceblock_saleprice",
                ".a-price .a-offscreen", ".a-price-whole",  # Amazon specific (most reliable)
                "[data-automation-id='product-price']",  # Amazon
                "#price", ".product-price", ".selling-price", ".offer-price",
                "[data-price]", "[data-product-price]", ".price-whole"
            ]
            for sel in price_selectors:
                # Search only in main container
                node = main_container.select_one(sel) if main_container != soup else soup.select_one(sel)
                if node and not is_excluded(node):
                    text = node.get_text(" ", strip=True)
                    if text:
                        add_candidate(text, f"visible:{sel}", node, priority=800)

        # 4) Look for M.R.P. or original price (usually near main price)
        if main_container:
            mrp_selectors = [
                "#priceblock_saleprice", ".a-price.a-text-price .a-offscreen",
                ".a-text-strike", "[class*='strike']", ".original-price", ".mrp"
            ]
            original_price_candidates = []
            for sel in mrp_selectors:
                node = main_container.select_one(sel) if main_container != soup else soup.select_one(sel)
                if node and not is_excluded(node):
                    text = node.get_text(" ", strip=True)
                    if text:
                        p, c = parse_price(text)
                        if p and p > 0:
                            original_price_candidates.append((float(p), c or meta_currency))
            
            # If we find candidates, use the scoring system above to pick best price
            # Original price logic is handled after main price selection

        # Score and select best candidate
        if candidates:
            # Remove duplicates (same price value)
            seen = set()
            unique_candidates = []
            for val, cur, score, label, elem in candidates:
                key = (val, cur)
                if key not in seen:
                    seen.add(key)
                    unique_candidates.append((val, cur, score, label, elem))
            
            # Sort by score (highest first)
            unique_candidates.sort(key=lambda x: x[2], reverse=True)
            
            if unique_candidates:
                # Get best price
                best_price, price_cur, best_score, best_label, _ = unique_candidates[0]
                
                # Infer currency if missing
                if not price_cur:
                    if url and any(domain in url.lower() for domain in ['amazon.in', 'flipkart', 'nykaa', 'myntra', 'croma']):
                        price_cur = "INR"
                    elif url and 'amazon.com' in url.lower():
                        price_cur = "USD"
                    else:
                        price_cur = meta_currency
                
                # Find original price (MRP) - look for prices higher than current
                original_price = None
                for val, cur, score, label, _ in unique_candidates[1:]:
                    # Prefer prices significantly higher (at least 10% more)
                    if val > best_price and val / best_price >= 1.10:
                        # Check if label suggests it's MRP/original
                        if any(term in label.lower() for term in ['mrp', 'original', 'saleprice', 'text-price', 'strike']):
                            original_price = val
                            break
                
                # If no clear MRP found, check if we have any higher prices
                if not original_price:
                    for val, cur, score, label, _ in unique_candidates[1:]:
                        if val > best_price and val / best_price >= 1.10:
                            original_price = val
                            break
                
                return best_price, original_price, price_cur

        # Nothing found - infer currency from URL
        currency = None
        if url:
            if any(domain in url.lower() for domain in ['amazon.in', 'flipkart', 'nykaa', 'myntra', 'croma']):
                currency = "INR"
            elif 'amazon.com' in url.lower():
                currency = "USD"
        
        return None, None, currency
    except Exception as e:
        print(f"⚠️ Error extracting price from HTML fallback: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None


async def analyze_html(html_content: str, url: str) -> Optional[str]:
    return _analyze_html_sync(html_content, url)

async def generate_search_query(product_title: str, source_domain: str = None) -> str:
    """
    Generates a targeted search query to find instances of a product on OTHER Indian e-commerce sites.
    Excludes the source domain to avoid finding the same page.
    """
    # Create the prompt
    # We will NOT use site: operators as they seem to trigger Serper 400 errors.
    # We will rely on Python-side filtering in search_agent_service.py
    
    # Define generic domain exclusion
    domain_exclusion = f"-site:{source_domain}" if source_domain else ""

    prompt = (
        f"I have a product titled: '{product_title}'.\n"
        f"I want to find this product OR similar products with matching specifications on Indian e-commerce sites.\n"
        f"Generate a single, precise Google search query.\n"
        f"Rules:\n"
        f"1. Include key identifiers (Brand, Series) but you can be slightly broader to find variants.\n"
        f"2. Exclude generic words that might bring up accessories (cases, covers).\n"
        f"3. Target India ('price india').\n"
        f"4. Do NOT use 'site:' operators (we filter later).\n"
        f"5. LIMIT to the search string only. No explanation.\n"
    )

    try:
        # Use a faster/cheaper model if available, but Flash 1.5 is fine
        if GEMINI_AVAILABLE and genai:
             model = genai.GenerativeModel("gemini-2.5-flash")
             # Using await if the method supports it, otherwise sync
             # genai python client is sync by default for generate_content but let's wrap or assume sync is fine for now
             # Actually, this function is async, so we'll just call it synchronously as the library is blocking
             response = model.generate_content(prompt)
             query = response.text.strip().replace('"', '').replace("'", "")
             print(f"🧠 Gemini Generated Query: {query}")
             return query
        else:
             print("⚠️ Gemini not available for query generation")
             return f"{product_title} price india {domain_exclusion}"

    except Exception as e:
        print(f"⚠️ Error generating search query: {e}")
        # Fallback query - Clean title to avoid Serper 400 errors
        import re
        clean_title = re.sub(r'[^\w\s]', '', product_title)
        return f"{clean_title} price india {domain_exclusion}"



async def rank_products(original_title: str, candidates: list) -> list:
    """
    Uses Gemini to compare candidates with the original product and pick the best matches.
    Sorts by relevance (Exact Match > Variant Match) and then Price.
    """
    if not candidates:
        return []

    # Prepare context for LLM
    candidate_list_str = ""
    for idx, c in enumerate(candidates):
        candidate_list_str += f"{idx}. Title: {c['title']} | Price: {c['price_hint']} | Link: {c['link']}\n"

    prompt = (
        f"I am looking for this product: '{original_title}'\n"
        f"Here are the candidates I found on other sites:\n"
        f"{candidate_list_str}\n"
        f"TASK: Identify the top 3 best matches (Exact Twins OR Similar Competitors).\n"
        f"Rules:\n"
        f"1. Prioritize Exact Matches first.\n"
        f"2. If no exact match, accept Similar Products (same specs, same series).\n"
        f"3. Exclude accessories (cases, covers).\n"
        f"4. Return a JSON list of indices of the best matches, e.g. [0, 2, 1].\n"
        f"5. LIMIT to top 3.\n"
        f"Return ONLY the JSON list."
    )

    try:
        # Use a smart model
        if GEMINI_AVAILABLE and genai:
             # Using 1.5-flash as it is smart enough for ranking and fast/cheap
             model = genai.GenerativeModel("gemini-2.5-flash")
             # Making it synchronous but running in threadpool usually preferred, but for now direct call
             response = model.generate_content(prompt)
             text = response.text.strip().replace("```json", "").replace("```", "")
             
             import json
             indices = json.loads(text)
             
             # Reorder candidates based on AI selection
             ranked_candidates = []
             for i in indices:
                 if 0 <= i < len(candidates):
                     ranked_candidates.append(candidates[i])
             
             # If AI returns nothing valid, fallback to price sort
             if not ranked_candidates:
                 return sorted(candidates, key=lambda x: float(x['price_hint']))
                 
             return ranked_candidates
        else:
             # Fallback
             return sorted(candidates, key=lambda x: float(x['price_hint']))

    except Exception as e:
        print(f"⚠️ Error ranking products: {e}")
        # Fallback to price sort
        return sorted(candidates, key=lambda x: float(x['price_hint']))




async def generate_alternative_search_query(product_title: str) -> str:
    """
    Generates a search query to find ALTERNATIVE products (competitors, better value).
    """
    prompt = (
        f"I have a product titled: '{product_title}'.\n"
        f"I want to find a SPECIFIC alternative product (Competitor) available in India.\n"
        f"Task: Identify the #1 best direct competitor model.\n"
        f"Then generate a search query to find the price/buy page for THAT competitor.\n"
        f"Examples:\n"
        f" - If product is 'Sony WH-1000XM5', query should be 'buy Sennheiser Momentum 4 india online'\n"
        f" - If product is 'iPhone 15', query should be 'Samsung Galaxy S23 price india'\n"
        f"Rules: Limit to the search string only. No quotes. Do not include 'alternatives to'.\n"
    )

    try:
        if GEMINI_AVAILABLE and genai:
             model = genai.GenerativeModel("gemini-2.5-flash")
             response = model.generate_content(prompt) # ... rest of the code is implicit in context match? 
             # Wait, replace_file_content replaces the BLOCK. I need to include the next lines too if I touch them.
             query = response.text.strip().replace('"', '').replace("'", "")
             print(f"🧠 Gemini Alternative Query: {query}")
             return query
        else:
             return f"buy alternatives to {product_title} india"
    except Exception as e:
        print(f"⚠️ Error generating alternative query: {e}")
        return f"buy alternatives to {product_title} india"

async def rank_alternatives(original_title: str, candidates: list) -> list:
    """
    Analyzes potential alternatives and selects the best ones with a reason.
    Returns list of dicts: { ...candidate_data, "reason": "Why it's good" }
    """
    if not candidates:
        return []

    candidate_list_str = ""
    for idx, c in enumerate(candidates):
        candidate_list_str += f"{idx}. Title: {c['title']} | Price: {c['price_hint']} | Link: {c['link']}\n"

    prompt = (
        f"Original Product: '{original_title}'\n"
        f"Potential Alternatives found:\n{candidate_list_str}\n"
        f"TASK: Select the top 3 items that are GOOD alternatives (similar function, better price/specs).\n"
        f"For each selected item, provide a short 'reason' (e.g. 'Cheaper with similar bass', 'Newer model').\n"
        f"Return a JSON list of objects: [{{ 'index': 0, 'reason': '...' }}, ...]\n"
        f"Return ONLY the JSON."
    )

    try:
        if GEMINI_AVAILABLE and genai:
             model = genai.GenerativeModel("gemini-2.5-flash") # Use 2.5 flash
             response = model.generate_content(prompt)
             text = response.text.strip().replace("```json", "").replace("```", "")
             
             import json
             selections = json.loads(text)
             
             final_results = []
             for item in selections:
                 idx = item.get("index")
                 if idx is not None and 0 <= idx < len(candidates):
                     cand = candidates[idx].copy()
                     cand["reason"] = item.get("reason", "Good alternative")
                     final_results.append(cand)
             
             return final_results
        else:
             # Fallback: take first 3, label as generic
             return [ {**c, "reason": "Potential alternative"} for c in candidates[:3] ]
    except Exception as e:
        print(f"⚠️ Error ranking alternatives: {e}")
        # Robust Fallback: Return top 3 anyway
        return [ {**c, "reason": "Potential alternative"} for c in candidates[:3] ]


async def clean_jargon(text: str) -> list:
    """
    Jargon Buster: Translates complex technical specs into simple consumer benefits.
    Returns: List of dicts [{"term": "Term", "simple_explanation": "Benefit"}]
    """
    prompt = (
        f"Here is a product description/spec sheet:\n{text[:2500]}\n"
        f"TASK: Identify up to 3 complex technical terms (e.g. 'Snapdragon 8 Gen 2', '4800x1200 dpi', 'Active Noise Cancellation').\n"
        f"For each, provide a very short, simple explanation of the BENEFIT to the user.\n"
        f"Return ONLY a JSON list of objects: [{{ 'term': '...', 'simple_explanation': '...' }}]\n"
    )

    try:
        if GEMINI_AVAILABLE and genai:
             model = genai.GenerativeModel("gemini-2.5-flash")
             response = model.generate_content(prompt)
             clean_text = response.text.strip().replace("```json", "").replace("```", "")
             import json
             return json.loads(clean_text)
        else:
             return [{"term": "Jargon Buster", "simple_explanation": "Unavailable (Gemini disabled)."}]
    except Exception as e:
        print(f"⚠️ Error in Jargon Buster: {e}")
        return []

async def calculate_eco_score(text: str) -> dict:
    """
    Eco-Meter: Analyzes sustainability and assigns a badge.
    Returns: { "score": "Green"|"Yellow"|"Red", "badge": "Green"|"Yellow"|"Red", "reasoning": "..." }
    """
    prompt = (
        f"Product Info:\n{text[:2500]}\n"
        f"TASK: Analyze for sustainability/eco-friendliness.\n"
        f"Look for keywords like: 'recycled', 'energy efficient', 'carbon neutral', 'biodegradable', 'refurbished'.\n"
        f"Assign a badge: 'Green' (Highly Eco-friendly), 'Yellow' (Some eco features), or 'Red' (No mention/Standard).\n"
        f"Return JSON: {{ 'score': 'Green/Yellow/Red', 'badge': 'Green/Yellow/Red', 'reasoning': 'Short explanation' }}\n"
    )

    try:
        if GEMINI_AVAILABLE and genai:
             model = genai.GenerativeModel("gemini-2.5-flash")
             response = model.generate_content(prompt)
             clean_text = response.text.strip().replace("```json", "").replace("```", "")
             import json
             return json.loads(clean_text)
        else:
             return {"score": "Red", "badge": "Red", "reasoning": "Eco analysis unavailable."}
    except Exception as e:
        print(f"⚠️ Error in Eco-Meter: {e}")
        return {"score": "Red", "badge": "Red", "reasoning": "Standard product."}
