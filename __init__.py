"""
Routers package initialization.
"""

from app.routers.analytics_router import router as analytics_router
from app.routers.auth_router import router as auth_router
from app.routers.delivery_router import router as delivery_router
from app.routers.invoice_router import router as invoice_router
from app.routers.procurement_router import router as procurement_router
from app.routers.user_router import router as user_router
from app.routers.vendor_performance_router import (
    router as vendor_performance_router,
)
from app.routers.report_router import router as report_router
from app.routers.vendor_router import router as vendor_router

__all__ = [
    "auth_router",
    "user_router",
    "vendor_router",
    "procurement_router",
    "invoice_router",
    "delivery_router",
    "vendor_performance_router",
    "analytics_router",
    "report_router",
]
