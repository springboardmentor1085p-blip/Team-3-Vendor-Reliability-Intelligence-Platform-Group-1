"""
Vendor Reliability Intelligence Platform
Application Entry Point
"""

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

from app.routers.analytics_router import router as analytics_router
from app.routers.auth_router import router as auth_router
from app.routers.communication_router import router as communication_router
from app.routers.contract_router import router as contract_router
from app.routers.delivery_router import router as delivery_router
from app.routers.invoice_router import router as invoice_router
from app.routers.procurement_router import router as procurement_router
from app.routers.report_router import router as report_router
from app.routers.settings_router import router as settings_router
from app.routers.user_router import router as user_router
from app.routers.vendor_performance_router import (
    router as vendor_performance_router,
)
from app.routers.vendor_router import router as vendor_router


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
Enterprise Vendor Reliability Intelligence Platform API.

Features:
• Vendor Management
• Authentication
• Analytics
• Procurement
• Risk Scoring
• Reports & Intelligence
• Contracts & Communication
""",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|0\.0\.0\.0)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Authentication
app.include_router(
    auth_router,
    prefix=settings.API_V1_STR,
)

# Users
app.include_router(
    user_router,
    prefix=settings.API_V1_STR,
)

# Vendors
app.include_router(
    vendor_router,
    prefix=settings.API_V1_STR,
)

# Procurement
app.include_router(
    procurement_router,
    prefix=settings.API_V1_STR,
)

# Invoices
app.include_router(
    invoice_router,
    prefix=settings.API_V1_STR,
)

# Delivery
app.include_router(
    delivery_router,
    prefix=settings.API_V1_STR,
)

# Vendor Performance
app.include_router(
    vendor_performance_router,
    prefix=settings.API_V1_STR,
)

# Analytics
app.include_router(
    analytics_router,
    prefix=settings.API_V1_STR,
)

# Reports
app.include_router(
    report_router,
    prefix=settings.API_V1_STR,
)

# Contracts
app.include_router(
    contract_router,
    prefix=settings.API_V1_STR,
)

# Communications
app.include_router(
    communication_router,
    prefix=settings.API_V1_STR,
)

# Settings
app.include_router(
    settings_router,
    prefix=settings.API_V1_STR,
)


@app.get(
    "/",
    tags=["General"],
    summary="Root Endpoint",
)
async def root():
    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
    }


@app.get(
    "/health",
    tags=["General"],
    summary="Health Check",
)
async def health():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "utc_time": datetime.now(timezone.utc).isoformat(),
    }