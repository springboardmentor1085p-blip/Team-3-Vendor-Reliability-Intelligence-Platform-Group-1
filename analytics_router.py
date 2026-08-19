"""
FastAPI Router for Analytics and Reporting endpoints with Role-Based Access Control (RBAC).
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_analytics_service, require_roles
from app.models.users import User
from app.schemas.analytics import (
    DeliveryAnalyticsResponse,
    ExecutiveDashboardResponse,
    InvoiceAnalyticsResponse,
    ProcurementAnalyticsResponse,
    SystemAnalyticsResponse,
    VendorAnalyticsResponse,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics & Reporting"],
)


@router.get(
    "/dashboard",
    response_model=ExecutiveDashboardResponse,
    status_code=status.HTTP_200_OK,
    summary="Get executive dashboard analytics",
    description="Returns high-level executive KPI metrics covering vendors, spend, invoices, delivery rates, and open issues. Requires Admin, Procurement Manager, Logistics Manager, or Auditor role.",
)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "SUPPLY_CHAIN_MANAGER", "FINANCE_OFFICER", "LOGISTICS_MANAGER", "AUDITOR")
    ),
) -> ExecutiveDashboardResponse:
    """
    Retrieve executive dashboard KPIs.
    """
    return await service.get_dashboard(db)


@router.get(
    "/procurement",
    response_model=ProcurementAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get procurement analytics",
    description="Returns procurement metrics including request counts, PO status distributions, spend breakdowns, and monthly spend trends. Requires Admin, Procurement Manager, Logistics Manager, or Auditor role.",
)
async def get_procurement_analytics(
    db: AsyncSession = Depends(get_db),
    service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "SUPPLY_CHAIN_MANAGER", "FINANCE_OFFICER", "LOGISTICS_MANAGER", "AUDITOR")
    ),
) -> ProcurementAnalyticsResponse:
    """
    Retrieve procurement analytics.
    """
    return await service.get_procurement_analytics(db)


@router.get(
    "/invoices",
    response_model=InvoiceAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get invoice & financial analytics",
    description="Returns financial metrics including invoiced amounts, paid amounts, pending balances, overdue totals, and invoice status distributions. Requires Admin, Procurement Manager, Logistics Manager, or Auditor role.",
)
async def get_invoice_analytics(
    db: AsyncSession = Depends(get_db),
    service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "SUPPLY_CHAIN_MANAGER", "FINANCE_OFFICER", "LOGISTICS_MANAGER", "AUDITOR")
    ),
) -> InvoiceAnalyticsResponse:
    """
    Retrieve invoice & financial analytics.
    """
    return await service.get_invoice_analytics(db)


@router.get(
    "/deliveries",
    response_model=DeliveryAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get delivery & logistics analytics",
    description="Returns logistics metrics including shipment status breakdown, on-time delivery rates (%), success rates (%), return rates (%), and average delay in days. Requires Admin, Procurement Manager, Logistics Manager, or Auditor role.",
)
async def get_delivery_analytics(
    db: AsyncSession = Depends(get_db),
    service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "SUPPLY_CHAIN_MANAGER", "FINANCE_OFFICER", "LOGISTICS_MANAGER", "AUDITOR")
    ),
) -> DeliveryAnalyticsResponse:
    """
    Retrieve delivery & logistics analytics.
    """
    return await service.get_delivery_analytics(db)


@router.get(
    "/vendors",
    response_model=VendorAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get vendor analytics",
    description="Returns vendor metrics including status distributions, top 5 vendors by spend, and average rating scores. Requires Admin, Procurement Manager, Logistics Manager, or Auditor role.",
)
async def get_vendor_analytics(
    db: AsyncSession = Depends(get_db),
    service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "SUPPLY_CHAIN_MANAGER", "FINANCE_OFFICER", "LOGISTICS_MANAGER", "AUDITOR")
    ),
) -> VendorAnalyticsResponse:
    """
    Retrieve vendor analytics.
    """
    return await service.get_vendor_analytics(db)


@router.get(
    "/system",
    response_model=SystemAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get system & user management analytics",
    description="Returns system metrics including active user counts grouped by role and activity log statistics. Requires Admin or Auditor role.",
)
async def get_system_analytics(
    db: AsyncSession = Depends(get_db),
    service: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "AUDITOR")
    ),
) -> SystemAnalyticsResponse:
    """
    Retrieve system & user analytics.
    """
    return await service.get_system_analytics(db)
