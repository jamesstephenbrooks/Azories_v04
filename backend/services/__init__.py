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
