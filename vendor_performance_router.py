"""
FastAPI Router for Vendor Performance endpoints with Role-Based Access Control (RBAC).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InvalidVendorPerformanceDataError,
    PurchaseOrderNotFoundError,
    VendorIssueNotFoundError,
    VendorNotFoundError,
    VendorPerformanceDomainError,
    VendorRatingNotFoundError,
)
from app.database import get_db
from app.dependencies import (
    get_current_user,
    get_vendor_performance_service,
    require_roles,
)
from app.models.vendor_performance import IssueStatusEnum
from app.models.users import User
from app.schemas.vendor_performance import (
    VendorIssueCreate,
    VendorIssueResponse,
    VendorIssueUpdate,
    VendorPerformanceMetricCreate,
    VendorPerformanceMetricResponse,
    VendorPerformanceSummaryResponse,
    VendorRankingResponse,
    VendorRatingCreate,
    VendorRatingResponse,
)
from app.services.vendor_performance_service import VendorPerformanceService

router = APIRouter(
    prefix="/vendor-performance",
    tags=["Vendor Performance"],
)


# ======================================================================
# 1. VENDOR RATINGS ENDPOINTS
# ======================================================================

@router.post(
    "/ratings",
    response_model=VendorRatingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a vendor rating",
    description="Submits a quality, delivery, or communication rating for a vendor. Auto-calculates overall rating.",
)
async def create_rating(
    rating_in: VendorRatingCreate,
    db: AsyncSession = Depends(get_db),
    service: VendorPerformanceService = Depends(get_vendor_performance_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "LOGISTICS_MANAGER", "AUDITOR")
    ),
) -> VendorRatingResponse:
    """
    Submit a new vendor rating.
    """
    try:
        return await service.create_rating(db, rating_in, current_user.user_id)
    except (VendorNotFoundError, PurchaseOrderNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except (InvalidVendorPerformanceDataError, VendorPerformanceDomainError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.get(
    "/ratings",
    response_model=list[VendorRatingResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all vendor ratings",
    description="Returns a paginated list of vendor ratings with optional filters for vendor_id and po_id.",
)
async def get_all_ratings(
    skip: int = Query(0, ge=0, description="Number of records to skip."),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return."),
    vendor_id: UUID | None = Query(None, description="Filter by vendor ID."),
    po_id: UUID | None = Query(None, description="Filter by Purchase Order ID."),
    db: AsyncSession = Depends(get_db),
    service: VendorPerformanceService = Depends(get_vendor_performance_service),
    current_user: User = Depends(get_current_user),
) -> list[VendorRatingResponse]:
    """
    Retrieve all vendor ratings with optional query filters.
    """
    return await service.get_all_ratings(
        db,
        skip=skip,
        limit=limit,
        vendor_id=vendor_id,
        po_id=po_id,
    )


# ======================================================================
# 2. VENDOR ISSUES ENDPOINTS
# ======================================================================

@router.post(
    "/issues",
    response_model=VendorIssueResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Report a vendor issue",
    description="Logs a new issue against a vendor.",
)
async def create_issue(
    issue_in: VendorIssueCreate,
    db: AsyncSession = Depends(get_db),
    service: VendorPerformanceService = Depends(get_vendor_performance_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "LOGISTICS_MANAGER", "AUDITOR")
    ),
) -> VendorIssueResponse:
    """
    Log a new vendor issue.
    """
    try:
        return await service.create_issue(db, issue_in, current_user.user_id)
    except (VendorNotFoundError, PurchaseOrderNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except (InvalidVendorPerformanceDataError, VendorPerformanceDomainError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.get(
    "/issues",
    response_model=list[VendorIssueResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all vendor issues",
    description="Returns a paginated list of vendor issues with optional filters for vendor_id and status.",
)
async def get_all_issues(
    skip: int = Query(0, ge=0, description="Number of records to skip."),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return."),
    vendor_id: UUID | None = Query(None, description="Filter by vendor ID."),
    status_filter: IssueStatusEnum | None = Query(
        None, alias="status", description="Filter by issue status."
    ),
    db: AsyncSession = Depends(get_db),
    service: VendorPerformanceService = Depends(get_vendor_performance_service),
    current_user: User = Depends(get_current_user),
) -> list[VendorIssueResponse]:
    """
    Retrieve all vendor issues with optional query filters.
    """
    return await service.get_all_issues(
        db,
        skip=skip,
        limit=limit,
        vendor_id=vendor_id,
        status=status_filter,
    )


@router.patch(
    "/issues/{issue_id}",
    response_model=VendorIssueResponse,
    status_code=status.HTTP_200_OK,
    summary="Update or resolve vendor issue",
    description="Updates issue status or description. Setting status to RESOLVED automatically assigns resolved_at. Requires Admin or Procurement Manager role.",
)
async def update_issue(
    issue_id: UUID,
    issue_in: VendorIssueUpdate,
    db: AsyncSession = Depends(get_db),
    service: VendorPerformanceService = Depends(get_vendor_performance_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER")
    ),
) -> VendorIssueResponse:
    """
    Update or resolve a vendor issue.
    """
    try:
        return await service.update_issue(db, issue_id, issue_in)
    except VendorIssueNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except (InvalidVendorPerformanceDataError, VendorPerformanceDomainError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


# ======================================================================
# 3. VENDOR PERFORMANCE METRICS ENDPOINTS
# ======================================================================

@router.post(
    "/metrics",
    response_model=VendorPerformanceMetricResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a performance metric",
    description="Records a new performance metric entry for a vendor.",
)
async def create_metric(
    metric_in: VendorPerformanceMetricCreate,
    db: AsyncSession = Depends(get_db),
    service: VendorPerformanceService = Depends(get_vendor_performance_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "AUDITOR")
    ),
) -> VendorPerformanceMetricResponse:
    """
    Record a vendor performance metric entry.
    """
    try:
        return await service.create_metric(db, metric_in, current_user.user_id)
    except VendorNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except (InvalidVendorPerformanceDataError, VendorPerformanceDomainError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.get(
    "/metrics",
    response_model=list[VendorPerformanceMetricResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all performance metric entries",
    description="Returns a paginated list of recorded performance metric entries.",
)
async def get_all_metrics(
    skip: int = Query(0, ge=0, description="Number of records to skip."),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return."),
    vendor_id: UUID | None = Query(None, description="Filter by vendor ID."),
    metric_type: str | None = Query(None, description="Filter by metric type."),
    db: AsyncSession = Depends(get_db),
    service: VendorPerformanceService = Depends(get_vendor_performance_service),
    current_user: User = Depends(get_current_user),
) -> list[VendorPerformanceMetricResponse]:
    """
    Retrieve recorded performance metric entries.
    """
    return await service.get_all_metrics(
        db,
        skip=skip,
        limit=limit,
        vendor_id=vendor_id,
        metric_type=metric_type,
    )


# ======================================================================
# 4. PERFORMANCE SUMMARY & RANKINGS ENDPOINTS
# ======================================================================

@router.get(
    "/summary/{vendor_id}",
    response_model=VendorPerformanceSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get real-time vendor performance summary",
    description="Returns aggregated real-time performance summary metrics for a vendor. Requires Admin, Procurement Manager, or Auditor role.",
)
async def get_vendor_performance_summary(
    vendor_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: VendorPerformanceService = Depends(get_vendor_performance_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "SUPPLY_CHAIN_MANAGER", "FINANCE_OFFICER", "LOGISTICS_MANAGER", "AUDITOR")
    ),
) -> VendorPerformanceSummaryResponse:
    """
    Retrieve real-time performance summary for a vendor.
    """
    try:
        return await service.get_vendor_performance_summary(db, vendor_id)
    except VendorNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )


@router.get(
    "/rankings",
    response_model=list[VendorRankingResponse],
    status_code=status.HTTP_200_OK,
    summary="Get vendor performance rankings",
    description="Returns a leaderboard ranking of vendors ordered by overall composite performance score. Requires Admin, Procurement Manager, or Auditor role.",
)
async def get_vendor_rankings(
    skip: int = Query(0, ge=0, description="Number of records to skip."),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return."),
    db: AsyncSession = Depends(get_db),
    service: VendorPerformanceService = Depends(get_vendor_performance_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "SUPPLY_CHAIN_MANAGER", "FINANCE_OFFICER", "LOGISTICS_MANAGER", "AUDITOR")
    ),
) -> list[VendorRankingResponse]:
    """
    Retrieve vendor performance rankings leaderboard.
    """
    return await service.get_vendor_rankings(db, skip=skip, limit=limit)
