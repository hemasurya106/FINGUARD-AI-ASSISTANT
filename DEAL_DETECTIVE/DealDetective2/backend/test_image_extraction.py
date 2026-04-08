
import sys
import os
import asyncio

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.gemini_service import _extract_relevant_html

def test_og_image():
    html = """
    <html>
        <head>
            <meta property="og:image" content="https://example.com/og-image.jpg" />
        </head>
        <body>
            <div id="productTitle">Test Product</div>
        </body>
    </html>
    """
    result = _extract_relevant_html(html, "https://example.com")
    print("\n--- Test OG Image ---")
    if "Image Candidate (Meta): https://example.com/og-image.jpg" in result:
        print("✅ OG Image extracted successfully")
    else:
        print("❌ OG Image Extraction Failed")
        print("Result snippet:", result[:500])

def test_amazon_landing_image():
    html = """
    <html>
        <body>
            <div id="centerCol">
                <div id="productTitle">Amazon Product</div>
                <img id="landingImage" src="https://amazon.com/landing.jpg" />
            </div>
        </body>
    </html>
    """
    result = _extract_relevant_html(html, "https://amazon.com/dp/123")
    print("\n--- Test Amazon Landing Image ---")
    if "https://amazon.com/landing.jpg" in result:
        print("✅ Amazon Landing Image extracted successfully")
    else:
        print("❌ Amazon Landing Image Extraction Failed")
        print("Result snippet:", result[:500])

def test_flipkart_image():
    html = """
    <html>
        <body>
            <div class="_1YokD2 _3Mn1Gg">
                <h1 class="yhB1nd">Flipkart Product</h1>
                <img class="_396cs4" src="https://flipkart.com/image.jpg" />
            </div>
        </body>
    </html>
    """
    result = _extract_relevant_html(html, "https://flipkart.com/p/123")
    print("\n--- Test Flipkart Image ---")
    if "https://flipkart.com/image.jpg" in result:
        print("✅ Flipkart Image extracted successfully")
    else:
        print("❌ Flipkart Image Extraction Failed")
        print("Result snippet:", result[:500])

if __name__ == "__main__":
    try:
        test_og_image()
        test_amazon_landing_image()
        test_flipkart_image()
    except Exception as e:
        print(f"Test Execution Error: {e}")
