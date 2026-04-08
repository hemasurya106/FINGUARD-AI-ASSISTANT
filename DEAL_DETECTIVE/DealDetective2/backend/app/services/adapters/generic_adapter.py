from bs4 import BeautifulSoup

def extract(html: str, url: str) -> dict:
    """
    Extracts Open Graph (OG) metadata.
    Used for sites that block deep scraping (Nykaa, Myntra).
    """
    if not html or len(html) < 100:
        # Very short HTML might be a blocking page
        return {
            "product_id": None,
            "platform": "generic",
            "title": None,
            "price": None,
            "currency": None,
            "specs": {"error": "Blocked or empty response"},
            "images": [],
            "scraped": True,
            "source": "generic_fallback"
        }
    
    soup = BeautifulSoup(html, "html.parser")
    
    # Detect platform
    platform = "generic"
    if "myntra" in url.lower():
        platform = "myntra"
    elif "nykaa" in url.lower():
        platform = "nykaa"
    elif "flipkart" in url.lower():
        platform = "flipkart"
    elif "amazon" in url.lower():
        platform = "amazon"
    
    data = {
        "product_id": None, 
        "platform": platform,
        "title": None,
        "price": None,
        "currency": None,
        "specs": {},
        "images": [],
        "scraped": True,
        "source": "generic_fallback"
    }

    # 1. Title - Try multiple sources
    og_title = soup.select_one("meta[property='og:title']")
    if og_title:
        data["title"] = og_title.get("content")
    else:
        # Try other title sources
        title_tag = soup.select_one("title")
        if title_tag:
            title_text = title_tag.get_text(strip=True)
            # Clean up title (remove site name, etc.)
            if "|" in title_text:
                title_text = title_text.split("|")[0].strip()
            data["title"] = title_text

    # 2. Image - Try multiple sources
    og_image = soup.select_one("meta[property='og:image']")
    if og_image:
        img_url = og_image.get("content")
        if img_url:
            data["images"].append(img_url)
    
    # Also try other image meta tags
    if not data["images"]:
        img_meta = soup.select_one("meta[property='og:image:secure_url'], meta[name='twitter:image']")
        if img_meta:
            img_url = img_meta.get("content") or img_meta.get("value")
            if img_url:
                data["images"].append(img_url)

    # 3. Price - Try multiple meta tag formats
    og_price = soup.select_one("meta[property='product:price:amount']")
    if og_price:
        try:
            data["price"] = float(og_price.get("content"))
        except:
            pass
    
    # Try currency
    og_currency = soup.select_one("meta[property='product:price:currency']")
    if og_currency:
        data["currency"] = og_currency.get("content")
    elif "myntra" in url.lower() or "nykaa" in url.lower() or "flipkart" in url.lower():
        data["currency"] = "INR"
    elif "amazon.in" in url.lower():
        data["currency"] = "INR"
            
    # 4. Description as Specs
    og_desc = soup.select_one("meta[property='og:description']")
    if og_desc:
        data["specs"] = {"description": og_desc.get("content")}
    else:
        # Try meta description
        meta_desc = soup.select_one("meta[name='description']")
        if meta_desc:
            data["specs"] = {"description": meta_desc.get("content")}

    return data