# Routes package for Azories API
# Each module contains related endpoint handlers

from fastapi import APIRouter

# Import routers from modules
from .admin import router as admin_router

# List of all routers to be included
routers = [
    admin_router,
]

def setup_routes(app, db):
    """Setup all routes with database dependency"""
    from . import admin
    admin.set_db(db)
    
    # Include all routers
    for router in routers:
        app.include_router(router, prefix="/api")
