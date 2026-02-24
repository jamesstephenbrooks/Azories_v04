"""
Brevo (formerly Sendinblue) Email Service for Azories
Alternative to Resend - for better deliverability
"""

import os
import asyncio
import logging
from typing import Optional, List
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

logger = logging.getLogger(__name__)

# Initialize Brevo
BREVO_API_KEY = os.environ.get("BREVO_API_KEY")
SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL", "noreply@azories.com")
SENDER_NAME = os.environ.get("BREVO_SENDER_NAME", "Azories")
APP_NAME = "Azories"
APP_URL = os.environ.get("APP_URL", "https://azories.com")

# Configure API client
configuration = None
api_instance = None

if BREVO_API_KEY:
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = BREVO_API_KEY
    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))


def is_configured() -> bool:
    """Check if Brevo email service is properly configured"""
    return bool(BREVO_API_KEY)


async def send_email(
    to_email: str,
    subject: str,
    html_content: str,
    to_name: Optional[str] = None,
    reply_to: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> dict:
    """
    Send an email using Brevo API
    Returns: {"success": bool, "message_id": str or None, "error": str or None}
    """
    if not is_configured():
        logger.warning("Brevo email service not configured - BREVO_API_KEY missing")
        return {"success": False, "message_id": None, "error": "Brevo email service not configured"}
    
    try:
        # Prepare sender
        sender = sib_api_v3_sdk.SendSmtpEmailSender(
            name=SENDER_NAME,
            email=SENDER_EMAIL
        )
        
        # Prepare recipient
        to = [sib_api_v3_sdk.SendSmtpEmailTo(
            email=to_email,
            name=to_name or to_email.split('@')[0]
        )]
        
        # Prepare email
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            sender=sender,
            to=to,
            subject=subject,
            html_content=html_content
        )
        
        # Add optional reply-to
        if reply_to:
            send_smtp_email.reply_to = sib_api_v3_sdk.SendSmtpEmailReplyTo(email=reply_to)
        
        # Add tags for tracking
        if tags:
            send_smtp_email.tags = tags
        
        # Send email in thread to avoid blocking
        response = await asyncio.to_thread(api_instance.send_transac_email, send_smtp_email)
        
        logger.info(f"Brevo email sent to {to_email}: {subject} (ID: {response.message_id})")
        return {"success": True, "message_id": response.message_id, "error": None}
        
    except ApiException as e:
        error_msg = f"Brevo API error: {e.status} - {e.body}"
        logger.error(f"Failed to send email to {to_email}: {error_msg}")
        return {"success": False, "message_id": None, "error": error_msg}
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to send email to {to_email}: {error_msg}")
        return {"success": False, "message_id": None, "error": error_msg}


async def send_bulk_email(
    recipients: List[dict],  # List of {"email": str, "name": str}
    subject: str,
    html_content: str,
    tags: Optional[List[str]] = None
) -> dict:
    """
    Send bulk emails using Brevo API
    Returns: {"success": bool, "message_ids": list, "errors": list}
    """
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


# Admin notification helper
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
