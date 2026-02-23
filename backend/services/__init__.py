"""
Services package initialization
"""
from .auth import (
    hash_password,
    verify_password,
    create_token,
    get_current_user,
    deduct_credits,
    is_vip_user
)

from .email_service import (
    send_email,
    is_configured as email_configured,
    get_welcome_email_html,
    get_password_reset_email_html,
    get_password_changed_email_html,
    generate_reset_token,
    get_token_expiry
)
