"""
Routes Package for Azories API

This package contains modular route handlers extracted from the monolithic server.py.
Each module handles a specific domain of functionality.

Modules:
- admin.py: Admin dashboard and management endpoints
- auth_routes.py: Authentication, login, registration, password reset

Usage:
    from routes import setup_routes
    setup_routes(app, db, email_funcs)
"""

from fastapi import FastAPI

# Import routers
from .admin import router as admin_router
from .auth_routes import router as auth_router, setup as setup_auth

# List of all routers
routers = [
    admin_router,
    auth_router,
]


def setup_routes(app: FastAPI, db, email_funcs: dict = None):
    """
    Setup all routes with database and service dependencies.
    
    Args:
        app: FastAPI application instance
        db: MongoDB database connection
        email_funcs: Dict of email functions (email_configured, send_email, etc.)
    """
    from . import admin
    
    # Setup admin routes
    admin.set_db(db)
    
    # Setup auth routes
    setup_auth(db, email_funcs or {})
    
    # Include all routers with /api prefix
    for router in routers:
        app.include_router(router, prefix="/api")
