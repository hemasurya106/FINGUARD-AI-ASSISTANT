
import asyncio
import logging
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models import PriceAlert
from app.services import scraper_service, gemini_service, email_service
import os

logger = logging.getLogger(__name__)

CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "3600")) # Default 1 hour
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "10"))

async def process_alerts():
    """
    Main loop to check prices for active alerts.
    """
    logger.info("Starting Price Alert Monitor Check...")
    db = SessionLocal()
    try:
        # Get active alerts
        # Simple logic: Check all active alerts. In production, you'd verify "last_checked" 
        # to ensure we don't spam or check too frequently per product.
        # For now, we trust the Global Interval.
        
        alerts = db.query(PriceAlert).filter(PriceAlert.is_active == True).limit(BATCH_SIZE).all()
        
        if not alerts:
            logger.info("No active alerts to check.")
            return

        for alert in alerts:
            logger.info(f"Checking alert {alert.id} for {alert.product_url}")
            
            try:
                # 1. Fetch HTML
                # Use browser if needed (auto fallback logic is in analyze router, duplicating here or refactoring is best)
                # We'll use the scraper service directly for now.
                html = await scraper_service.fetch_html_threadsafe(alert.product_url)
                if not html:
                    # Try browser fallback
                    html = await scraper_service.fetch_html_with_browser(alert.product_url)
                
                if not html:
                    logger.warning(f"Failed to fetch content for {alert.product_url}")
                    continue

                # 2. Analyze with Gemini
                # Note: This is expensive/slow for many alerts. 
                # Optimization: Cache price by URL so we don't re-scrape same product for multiple users.
                result_raw = await gemini_service.analyze_html(html, alert.product_url)
                
                if not result_raw:
                     logger.warning(f"Gemini analysis failed for {alert.id}")
                     continue

                try:
                    import json
                    if isinstance(result_raw, dict):
                        result = result_raw
                    else:
                        result = json.loads(result_raw)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse Gemini response for {alert.id}: {result_raw[:100]}")
                    continue

                current_price = result.get("price")
                title = result.get("title", "Product")
                
                if current_price:
                    logger.info(f"Current price for {alert.id}: {current_price}, Target: {alert.target_price}")
                    
                    if current_price <= alert.target_price:
                        # TRIGGER ALERT
                        sent = email_service.send_price_alert_email(
                            to_email=alert.email,
                            product_title=title,
                            product_url=alert.product_url,
                            current_price=current_price,
                            target_price=alert.target_price
                        )
                        
                        if sent:
                            logger.info(f"Alert sent for {alert.id}. Deactivating/Updating.")
                             # Option A: Deactivate after send (Single Shot)
                            alert.is_active = False 
                            
                            # Option B: Keep active but update last_checked 
                            # (Real system needs 'last_notified' to avoid spamming every hour)
                            # pass 

                # Update timestamp
                alert.last_checked = datetime.utcnow()
                db.commit()

            except Exception as e:
                logger.error(f"Error checking alert {alert.id}: {e}")
                
    except Exception as e:
        logger.error(f"Error in process_alerts: {e}")
    finally:
        db.close()

async def start_monitor():
    """
    Background Task Loop
    """
    logger.info(f"Price Monitor Service Started (Interval: {CHECK_INTERVAL}s)")
    while True:
        await process_alerts()
        await asyncio.sleep(CHECK_INTERVAL)
