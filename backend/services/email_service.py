"""
Email Service for Azories
Handles transactional emails: welcome, password reset, notifications
Supports both Resend and Brevo providers
"""

import os
import asyncio
import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# Check which email provider is configured
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
BREVO_API_KEY = os.environ.get("BREVO_API_KEY")

# Import providers
resend = None
brevo_service = None

if RESEND_API_KEY:
    import resend as resend_module
    resend = resend_module
    resend.api_key = RESEND_API_KEY
    
if BREVO_API_KEY:
    from services.brevo_email_service import send_email as brevo_send_email, is_configured as brevo_configured
    brevo_service = brevo_send_email

# Configuration
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "onboarding@resend.dev")
BREVO_SENDER_EMAIL = os.environ.get("BREVO_SENDER_EMAIL", "noreply@azories.com")
APP_NAME = "Azories"
APP_URL = os.environ.get("APP_URL", "https://azories.com")

# Prefer Resend since Brevo SMTP login is not configured correctly
# To use Brevo: set BREVO_SMTP_LOGIN to your Brevo SMTP login email (found in SMTP & API settings)
BREVO_SMTP_LOGIN = os.environ.get("BREVO_SMTP_LOGIN")  # e.g., xxxxx@smtp-brevo.com
EMAIL_PROVIDER = "brevo" if (BREVO_API_KEY and BREVO_SMTP_LOGIN) else ("resend" if RESEND_API_KEY else None)

def is_configured() -> bool:
    """Check if any email service is properly configured"""
    return bool(RESEND_API_KEY or BREVO_API_KEY)

def get_provider() -> str:
    """Get the active email provider name"""
    return EMAIL_PROVIDER or "none"

async def send_email(to_email: str, subject: str, html_content: str) -> dict:
    """
    Send an email using configured provider (Brevo preferred, Resend fallback)
    Returns: {"success": bool, "email_id": str or None, "error": str or None}
    """
    if not is_configured():
        logger.warning("Email service not configured - no API keys found")
        return {"success": False, "email_id": None, "error": "Email service not configured"}
    
    # Try Brevo first if configured
    if BREVO_API_KEY and brevo_service:
        logger.info(f"Sending email via Brevo to {to_email}")
        result = await brevo_service(to_email, subject, html_content)
        if result["success"]:
            return {"success": True, "email_id": result.get("message_id"), "error": None, "provider": "brevo"}
        else:
            logger.warning(f"Brevo failed, trying Resend fallback: {result.get('error')}")
    
    # Fallback to Resend
    if RESEND_API_KEY and resend:
        FALLBACK_EMAIL = os.environ.get("FALLBACK_NOTIFY_EMAIL", "jamesstephenbrooks@outlook.com")
        
        params = {
            "from": f"{APP_NAME} <{SENDER_EMAIL}>",
            "to": [to_email],
            "subject": subject,
            "html": html_content
        }
        
        try:
            email = await asyncio.to_thread(resend.Emails.send, params)
            logger.info(f"Email sent via Resend to {to_email}: {subject}")
            return {"success": True, "email_id": email.get("id"), "error": None, "provider": "resend"}
        except Exception as e:
            error_msg = str(e)
            # If domain not verified, try sending to fallback email
            if "verify a domain" in error_msg.lower() and to_email != FALLBACK_EMAIL:
                logger.warning(f"Domain not verified for {to_email}, trying fallback: {FALLBACK_EMAIL}")
                params["to"] = [FALLBACK_EMAIL]
                params["subject"] = f"[For: {to_email}] {subject}"
                try:
                    email = await asyncio.to_thread(resend.Emails.send, params)
                    logger.info(f"Email sent to fallback {FALLBACK_EMAIL}: {subject}")
                    return {"success": True, "email_id": email.get("id"), "error": None, "provider": "resend"}
                except Exception as e2:
                    logger.error(f"Failed to send to fallback email: {str(e2)}")
                    return {"success": False, "email_id": None, "error": str(e2)}
            
            logger.error(f"Failed to send email to {to_email}: {error_msg}")
            return {"success": False, "email_id": None, "error": error_msg}
    
    return {"success": False, "email_id": None, "error": "No email provider available"}

# Email Templates

def get_welcome_email_html(user_name: str) -> str:
    """Generate welcome email HTML for new users"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 40px 20px;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #8B5CF6 0%, #EC4899 100%); padding: 40px 30px; text-align: center;">
                                <h1 style="margin: 0; color: #ffffff; font-size: 32px; font-weight: bold;">Welcome to Azories!</h1>
                                <p style="margin: 10px 0 0; color: rgba(255,255,255,0.9); font-size: 16px;">Your magical storytelling journey begins</p>
                            </td>
                        </tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding: 40px 30px;">
                                <h2 style="margin: 0 0 20px; color: #1f2937; font-size: 24px;">Hi {user_name}! 👋</h2>
                                <p style="margin: 0 0 20px; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                    Thank you for joining Azories! We're thrilled to have you as part of our creative community.
                                </p>
                                
                                <p style="margin: 0 0 20px; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                    With Azories, you can:
                                </p>
                                
                                <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 20px;">
                                    <tr>
                                        <td style="padding: 10px 0;">
                                            <span style="color: #8B5CF6; font-size: 18px;">✨</span>
                                            <span style="color: #4b5563; font-size: 15px; margin-left: 10px;">Create beautiful illustrated books</span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 10px 0;">
                                            <span style="color: #8B5CF6; font-size: 18px;">🎨</span>
                                            <span style="color: #4b5563; font-size: 15px; margin-left: 10px;">Generate AI artwork in our Art Studio</span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 10px 0;">
                                            <span style="color: #8B5CF6; font-size: 18px;">🎙️</span>
                                            <span style="color: #4b5563; font-size: 15px; margin-left: 10px;">Add voice narration to your stories</span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 10px 0;">
                                            <span style="color: #8B5CF6; font-size: 18px;">📚</span>
                                            <span style="color: #4b5563; font-size: 15px; margin-left: 10px;">Explore the magical 3D Library</span>
                                        </td>
                                    </tr>
                                </table>
                                
                                <p style="margin: 0 0 30px; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                    You have a <strong>30-day Pro trial</strong> to explore all our premium features!
                                </p>
                                
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td align="center">
                                            <a href="{APP_URL}/dashboard" style="display: inline-block; background: linear-gradient(135deg, #8B5CF6 0%, #EC4899 100%); color: #ffffff; text-decoration: none; padding: 14px 40px; border-radius: 50px; font-size: 16px; font-weight: 600;">
                                                Start Creating
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f9fafb; padding: 30px; text-align: center; border-top: 1px solid #e5e7eb;">
                                <p style="margin: 0 0 10px; color: #6b7280; font-size: 14px;">
                                    Questions? Reply to this email or visit our help center.
                                </p>
                                <p style="margin: 0; color: #9ca3af; font-size: 12px;">
                                    © 2026 Azories. All rights reserved.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

def get_password_reset_email_html(user_name: str, reset_token: str, reset_url: str) -> str:
    """Generate password reset email HTML"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 40px 20px;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%); padding: 40px 30px; text-align: center;">
                                <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: bold;">Password Reset Request</h1>
                            </td>
                        </tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding: 40px 30px;">
                                <h2 style="margin: 0 0 20px; color: #1f2937; font-size: 22px;">Hi {user_name},</h2>
                                <p style="margin: 0 0 20px; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                    We received a request to reset your password for your Azories account.
                                </p>
                                
                                <p style="margin: 0 0 30px; color: #4b5563; font-size: 16px; line-height: 1.6;">
                                    Click the button below to set a new password. This link will expire in <strong>1 hour</strong>.
                                </p>
                                
                                <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 30px;">
                                    <tr>
                                        <td align="center">
                                            <a href="{reset_url}" style="display: inline-block; background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%); color: #ffffff; text-decoration: none; padding: 14px 40px; border-radius: 50px; font-size: 16px; font-weight: 600;">
                                                Reset Password
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                                
                                <p style="margin: 0 0 10px; color: #6b7280; font-size: 14px;">
                                    Or copy and paste this link into your browser:
                                </p>
                                <p style="margin: 0 0 30px; color: #8B5CF6; font-size: 13px; word-break: break-all;">
                                    {reset_url}
                                </p>
                                
                                <div style="background-color: #fef3c7; border-radius: 8px; padding: 15px; margin-bottom: 20px;">
                                    <p style="margin: 0; color: #92400e; font-size: 14px;">
                                        ⚠️ If you didn't request this password reset, please ignore this email. Your password will remain unchanged.
                                    </p>
                                </div>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f9fafb; padding: 30px; text-align: center; border-top: 1px solid #e5e7eb;">
                                <p style="margin: 0 0 10px; color: #6b7280; font-size: 14px;">
                                    Need help? Contact us at books@azories.com
                                </p>
                                <p style="margin: 0; color: #9ca3af; font-size: 12px;">
                                    © 2026 Azories. All rights reserved.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

def get_password_changed_email_html(user_name: str) -> str:
    """Generate password changed confirmation email HTML"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f5;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 40px 20px;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                        <!-- Header -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #10B981 0%, #059669 100%); padding: 40px 30px; text-align: center;">
                                <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: bold;">Password Changed Successfully</h1>
                            </td>
                        </tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding: 40px 30px;">
                                <div style="text-align: center; margin-bottom: 30px;">
                                    <span style="font-size: 60px;">✅</span>
                                </div>
                                
                                <h2 style="margin: 0 0 20px; color: #1f2937; font-size: 22px; text-align: center;">Hi {user_name},</h2>
                                <p style="margin: 0 0 20px; color: #4b5563; font-size: 16px; line-height: 1.6; text-align: center;">
                                    Your Azories account password has been successfully changed.
                                </p>
                                
                                <div style="background-color: #fef3c7; border-radius: 8px; padding: 15px; margin: 30px 0;">
                                    <p style="margin: 0; color: #92400e; font-size: 14px; text-align: center;">
                                        ⚠️ If you didn't make this change, please contact us immediately at books@azories.com
                                    </p>
                                </div>
                                
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td align="center">
                                            <a href="{APP_URL}/auth" style="display: inline-block; background: linear-gradient(135deg, #10B981 0%, #059669 100%); color: #ffffff; text-decoration: none; padding: 14px 40px; border-radius: 50px; font-size: 16px; font-weight: 600;">
                                                Sign In Now
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f9fafb; padding: 30px; text-align: center; border-top: 1px solid #e5e7eb;">
                                <p style="margin: 0; color: #9ca3af; font-size: 12px;">
                                    © 2026 Azories. All rights reserved.
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

# Helper functions

def generate_reset_token() -> str:
    """Generate a secure password reset token"""
    return secrets.token_urlsafe(32)

def get_token_expiry() -> datetime:
    """Get expiry time for reset token (1 hour from now)"""
    return datetime.utcnow() + timedelta(hours=1)
