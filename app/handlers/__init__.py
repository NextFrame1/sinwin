from app.handlers.admin import admin_router
from app.handlers.default import default_router
from app.handlers.register import register_router

all = [register_router, default_router, admin_router]
