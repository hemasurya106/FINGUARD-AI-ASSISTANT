
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging
from typing import List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL")

def send_price_alert_email(to_email: str, product_title: str, product_url: str, current_price: float, target_price: float):
    """
    Sends a price alert email to the user.
    """
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        logger.error("SMTP credentials not set. Cannot send email.")
        return False

    subject = f"Price Alert: {product_title} is now ₹{current_price}!"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8" />
        <title>Price Drop Alert - Deal Detective</title>
    </head>
    <body style="margin:0; padding:0; background-color:#f4f6f8; font-family: Arial, Helvetica, sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
            <td align="center" style="padding: 30px 10px;">
            
            <!-- Email Container -->
            <table width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff; border-radius:8px; overflow:hidden; box-shadow:0 4px 10px rgba(0,0,0,0.08);">
                
                <!-- Header -->
                <tr>
                <td style="background-color:#ff9900; padding:20px; text-align:center;">
                    <h1 style="margin:0; color:#ffffff; font-size:24px;">
                    Deal Detective 🔍
                    </h1>
                    <p style="margin:5px 0 0; color:#fff; font-size:14px;">
                    Smart Price Tracking. Smarter Shopping.
                    </p>
                </td>
                </tr>

                <!-- Body -->
                <tr>
                <td style="padding:25px; color:#333;">
                    <h2 style="margin-top:0; color:#222;">
                    🎉 Price Drop Alert!
                    </h2>

                    <p style="font-size:15px; line-height:1.6;">
                    Great news! The price of the product you’ve been tracking has just dropped.
                    </p>

                    <p style="font-size:16px; font-weight:bold; margin:20px 0 10px;">
                    {product_title}
                    </p>

                    <table width="100%" cellpadding="10" cellspacing="0" style="background-color:#f9fafb; border-radius:6px; margin:15px 0;">
                    <tr>
                        <td style="font-size:14px;">
                        <strong>Current Price:</strong>
                        </td>
                        <td style="font-size:14px; color:#27ae60; font-weight:bold;">
                        ₹{current_price}
                        </td>
                    </tr>
                    <tr>
                        <td style="font-size:14px;">
                        <strong>Your Target Price:</strong>
                        </td>
                        <td style="font-size:14px;">
                        ₹{target_price}
                        </td>
                    </tr>
                    </table>

                    <p style="text-align:center; margin:30px 0;">
                    <a href="{product_url}" 
                        style="background-color:#ff9900; color:#ffffff; padding:12px 24px; text-decoration:none; font-weight:bold; border-radius:6px; display:inline-block;">
                        🛒 Buy Now
                    </a>
                    </p>

                    <p style="font-size:14px; line-height:1.6; color:#555;">
                    Don’t miss this deal! Prices can change quickly, so grab it while it lasts.
                    </p>
                </td>
                </tr>

                <!-- Footer -->
                <tr>
                <td style="background-color:#f1f3f5; padding:15px; text-align:center; font-size:12px; color:#777;">
                    <p style="margin:0;">
                    You’re receiving this email because you set a price alert on <strong>Deal Detective</strong>.
                    </p>
                    <p style="margin:5px 0 0;">
                    © 2025 Deal Detective. All rights reserved.
                    </p>
                </td>
                </tr>

            </table>
            <!-- End Email Container -->

            </td>
        </tr>
        </table>
    </body>
    </html>
    """

    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = FROM_EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(html_content, 'html'))

        # Connect to server
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        
        # Send email
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Price alert email sent to {to_email} for {product_title}")
        return True
    
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False
