"""
Brevo (formerly Sendinblue) Email Service for Azories
Using SMTP relay for better deliverability
"""

import os
import asyncio
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List

logger = logging.getLogger(__name__)

# Brevo SMTP Configuration
BREVO_SMTP_KEY = os.environ.get("BREVO_API_KEY")  # This is actually the SMTP key
BREVO_ACCOUNT_EMAIL = os.environ.get("BREVO_ACCOUNT_EMAIL")  # Login email for SMTP
BREVO_SMTP_SERVER = "smtp-relay.brevo.com"
BREVO_SMTP_PORT = 587
SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL", "noreply@azories.com")
SENDER_NAME = os.environ.get("BREVO_SENDER_NAME", "Azories")
APP_NAME = "Azories"
APP_URL = os.environ.get("APP_URL", "https://azories.com")


def is_configured() -> bool:
    """Check if Brevo SMTP is properly configured"""
    return bool(BREVO_SMTP_KEY and BREVO_ACCOUNT_EMAIL)


async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    to_name: Optional[str] = None,
    reply_to: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> dict:
    """
    Send an email using Brevo SMTP relay
    Returns: {"success": bool, "message_id": str or None, "error": str or None}
    """
    if not is_configured():
        logger.warning("Brevo SMTP not configured - missing BREVO_API_KEY or BREVO_ACCOUNT_EMAIL")
        return {"success": False, "message_id": None, "error": "Brevo SMTP not configured"}
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        msg['To'] = to_email
        if reply_to:
            msg['Reply-To'] = reply_to
        
        # Attach HTML content
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # Send via SMTP in thread to avoid blocking
        def send_smtp():
            with smtplib.SMTP(BREVO_SMTP_SERVER, BREVO_SMTP_PORT) as server:
                server.starttls()
                # Use Brevo account email as username, SMTP key as password
                server.login(BREVO_ACCOUNT_EMAIL, BREVO_SMTP_KEY)
                server.send_message(msg)
                return True
        
        await asyncio.to_thread(send_smtp)
        
        logger.info(f"Brevo SMTP email sent to {to_email}: {subject}")
        return {"success": True, "message_id": "smtp-sent", "error": None}
        
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"Brevo SMTP auth error: {e}"
        logger.error(f"Failed to send email to {to_email}: {error_msg}")
        return {"success": False, "message_id": None, "error": error_msg}
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to send email to {to_email}: {error_msg}")
        return {"success": False, "message_id": None, "error": error_msg}


async def send_bulk_email(
    recipients: List[dict],
    subject: str,
    html_content: str,
    tags: Optional[List[str]] = None
) -> dict:
    """Send bulk emails using Brevo SMTP"""
    if not is_configured():
        return {"success": False, "message_ids": [], "errors": ["Brevo not configured"]}
    
    results = {"success": True, "message_ids": [], "errors": []}
    
    for recipient in recipients:
        result = await send_email(
            to_email=recipient["email"],
            subject=subject,
            html_content=html_content,
            to_name=recipient.get("name"),
            tags=tags
        )
        
        if result["success"]:
            results["message_ids"].append(result["message_id"])
        else:
            results["errors"].append(f"{recipient['email']}: {result['error']}")
            results["success"] = False
    
    return results


async def send_admin_notification(
    subject: str,
    html_content: str,
    admin_email: Optional[str] = None
) -> dict:
    """Send notification to admin email"""
    target_email = admin_email or os.environ.get("ADMIN_NOTIFY_EMAIL", "books@azories.com")
    return await send_email(
        to_email=target_email,
        subject=f"[Azories Admin] {subject}",
        html_content=html_content,
        tags=["admin", "notification"]
    )
