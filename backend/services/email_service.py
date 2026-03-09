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
APP_URL = "https://azories.com"  # Hardcoded to prevent misconfigured env vars

# Prefer Resend if configured (Brevo has auth issues), fallback to Brevo
EMAIL_PROVIDER = "resend" if RESEND_API_KEY else ("brevo" if BREVO_API_KEY else None)

def is_configured() -> bool:
    """Check if any email service is properly configured"""
    return bool(RESEND_API_KEY or BREVO_API_KEY)

def get_provider() -> str:
    """Get the active email provider name"""
    return EMAIL_PROVIDER or "none"

async def send_email(to_email: str, subject: str, html_content: str) -> dict:
    """
    Send an email using configured provider (Resend preferred, Brevo fallback)
    Returns: {"success": bool, "email_id": str or None, "error": str or None}
    """
    if not is_configured():
        logger.warning("Email service not configured - no API keys found")
        return {"success": False, "email_id": None, "error": "Email service not configured"}
    
    # Try Resend first (preferred - Brevo has auth issues)
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
            
            logger.warning(f"Resend failed, trying Brevo fallback: {error_msg}")
    
    # Fallback to Brevo
    if BREVO_API_KEY and brevo_service:
        logger.info(f"Sending email via Brevo to {to_email}")
        result = await brevo_service(to_email, subject, html_content)
        if result["success"]:
            return {"success": True, "email_id": result.get("message_id"), "error": None, "provider": "brevo"}
        else:
            logger.error(f"Brevo also failed: {result.get('error')}")
    
    return {"success": False, "email_id": None, "error": "All email providers failed"}

# Email Templates

# Featured book covers for welcome email
FEATURED_BOOK_COVERS = [
    "https://res.cloudinary.com/dlbmjqmoy/image/upload/v1772217086/azories/books/the_dragons_secret_garden/cover.jpg",
    "https://res.cloudinary.com/dlbmjqmoy/image/upload/v1772223932/azories/books/robot_best_friend/cover.png",
    "https://res.cloudinary.com/dlbmjqmoy/image/upload/v1772217089/azories/books/the_case_of_the_missing_cookie/cover.jpg",
    "https://res.cloudinary.com/dlbmjqmoy/image/upload/v1772266491/azories/books/super_silly_superhero/cover_clean.jpg"
]

# Azora mascot image (official Cloudinary asset)
AZORA_MASCOT_URL = "https://res.cloudinary.com/dlbmjqmoy/image/upload/v1772279592/azories/mascot/azora_pose4_pointing.jpg"

def get_welcome_email_html(user_name: str) -> str:
    """Generate magical welcome email HTML for new users with 3 free stories"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="margin: 0; padding: 0; font-family: 'Nunito', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(180deg, #F3E8FF 0%, #E0E7FF 100%);">
        <table width="100%" cellpadding="0" cellspacing="0" style="background: linear-gradient(180deg, #F3E8FF 0%, #E0E7FF 100%); padding: 40px 20px;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 24px; overflow: hidden; box-shadow: 0 20px 40px rgba(139, 92, 246, 0.15);">
                        
                        <!-- Magical Header with Azora -->
                        <tr>
                            <td style="background: linear-gradient(135deg, #7C3AED 0%, #A855F7 50%, #EC4899 100%); padding: 40px 30px; text-align: center; position: relative;">
                                <!-- Sparkles decoration -->
                                <div style="position: absolute; top: 10px; left: 20px; font-size: 24px;">✨</div>
                                <div style="position: absolute; top: 30px; right: 30px; font-size: 20px;">⭐</div>
                                <div style="position: absolute; bottom: 20px; left: 40px; font-size: 16px;">🌟</div>
                                
                                <!-- Azora Mascot -->
                                <img src="{AZORA_MASCOT_URL}" alt="Azora the Dragon" width="120" height="120" style="border-radius: 50%; border: 4px solid rgba(255,255,255,0.3); margin-bottom: 15px; background: rgba(255,255,255,0.1);">
                                
                                <h1 style="margin: 0; color: #ffffff; font-size: 28px; font-weight: bold; text-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                                    Welcome to Azories!
                                </h1>
                                <p style="margin: 10px 0 0; color: rgba(255,255,255,0.95); font-size: 16px;">
                                    Your magical storytelling adventure begins ✨
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Main Content -->
                        <tr>
                            <td style="padding: 35px 30px;">
                                <h2 style="margin: 0 0 15px; color: #1f2937; font-size: 22px; text-align: center;">
                                    Hi {user_name}! 🎉
                                </h2>
                                <p style="margin: 0 0 25px; color: #4b5563; font-size: 16px; line-height: 1.7; text-align: center;">
                                    Thank you for joining our magical world of stories! We're so excited to have you here.
                                </p>
                                
                                <!-- 3 Free Stories Gift Box -->
                                <table width="100%" cellpadding="0" cellspacing="0" style="background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%); border-radius: 16px; margin-bottom: 25px; border: 2px dashed #F59E0B;">
                                    <tr>
                                        <td style="padding: 25px; text-align: center;">
                                            <div style="font-size: 40px; margin-bottom: 10px;">🎁</div>
                                            <h3 style="margin: 0 0 8px; color: #92400E; font-size: 20px; font-weight: bold;">
                                                Your Special Gift!
                                            </h3>
                                            <p style="margin: 0; color: #B45309; font-size: 16px; font-weight: 600;">
                                                You have <span style="background: #FBBF24; padding: 2px 10px; border-radius: 20px; color: #78350F;">3 FREE</span> AI story creations waiting!
                                            </p>
                                            <p style="margin: 10px 0 0; color: #92400E; font-size: 14px;">
                                                Create magical illustrated stories with just a few clicks 🪄
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- What You Can Do -->
                                <p style="margin: 0 0 15px; color: #6B7280; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">
                                    What you can create:
                                </p>
                                
                                <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 25px;">
                                    <tr>
                                        <td style="padding: 12px 15px; background: #F3E8FF; border-radius: 12px; margin-bottom: 8px;">
                                            <span style="font-size: 20px; margin-right: 12px;">🐉</span>
                                            <span style="color: #5B21B6; font-size: 15px; font-weight: 500;">AI-powered illustrated storybooks</span>
                                        </td>
                                    </tr>
                                    <tr><td style="height: 8px;"></td></tr>
                                    <tr>
                                        <td style="padding: 12px 15px; background: #FCE7F3; border-radius: 12px;">
                                            <span style="font-size: 20px; margin-right: 12px;">🎨</span>
                                            <span style="color: #9D174D; font-size: 15px; font-weight: 500;">Beautiful artwork in multiple styles</span>
                                        </td>
                                    </tr>
                                    <tr><td style="height: 8px;"></td></tr>
                                    <tr>
                                        <td style="padding: 12px 15px; background: #DBEAFE; border-radius: 12px;">
                                            <span style="font-size: 20px; margin-right: 12px;">🎙️</span>
                                            <span style="color: #1E40AF; font-size: 15px; font-weight: 500;">Voice narration for read-aloud fun</span>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- Featured Books Section -->
                                <p style="margin: 0 0 15px; color: #6B7280; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; font-weight: 600; text-align: center;">
                                    Explore our magical library:
                                </p>
                                
                                <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 30px;">
                                    <tr>
                                        <td align="center">
                                            <table cellpadding="0" cellspacing="0">
                                                <tr>
                                                    <td style="padding: 5px;">
                                                        <img src="{FEATURED_BOOK_COVERS[0]}" alt="Dragon's Secret Garden" width="120" height="160" style="border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); object-fit: cover;">
                                                    </td>
                                                    <td style="padding: 5px;">
                                                        <img src="{FEATURED_BOOK_COVERS[1]}" alt="Robot Best Friend" width="120" height="160" style="border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); object-fit: cover;">
                                                    </td>
                                                    <td style="padding: 5px;">
                                                        <img src="{FEATURED_BOOK_COVERS[2]}" alt="Missing Cookies" width="120" height="160" style="border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); object-fit: cover;">
                                                    </td>
                                                    <td style="padding: 5px;">
                                                        <img src="{FEATURED_BOOK_COVERS[3]}" alt="Super Silly Superhero" width="120" height="160" style="border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); object-fit: cover;">
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- CTA Button -->
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td align="center">
                                            <a href="{APP_URL}" style="display: inline-block; background: linear-gradient(135deg, #7C3AED 0%, #EC4899 100%); color: #ffffff; text-decoration: none; padding: 16px 50px; border-radius: 50px; font-size: 18px; font-weight: bold; box-shadow: 0 8px 20px rgba(124, 58, 237, 0.35); letter-spacing: 0.5px;">
                                                ✨ Start Reading ✨
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        
                        <!-- Magical Footer -->
                        <tr>
                            <td style="background: linear-gradient(180deg, #F9FAFB 0%, #F3F4F6 100%); padding: 25px 30px; text-align: center; border-top: 1px solid #E5E7EB;">
                                <p style="margin: 0 0 8px; color: #6B7280; font-size: 14px;">
                                    Questions? Just reply to this email — we love hearing from you! 💌
                                </p>
                                <p style="margin: 0; color: #9CA3AF; font-size: 12px;">
                                    © 2026 Azories. Made with ❤️ for little storytellers everywhere.
                                </p>
                                <p style="margin: 10px 0 0; font-size: 20px;">
                                    🐉📚✨🌟🎨
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
