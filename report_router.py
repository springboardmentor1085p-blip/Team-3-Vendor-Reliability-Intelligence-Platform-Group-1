"""
FastAPI Router for Reports module endpoints with Role-Based Access Control (RBAC).
Executes thin routing logic, input validation, dependency injection, and returns Phase 2A DTOs.
No direct SQL queries, ORM operations, or business calculations.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user, get_report_service, require_roles
from app.models.users import User
from app.schemas.reports import (
    ComplianceReportResponse,
    ContractReportResponse,
    ProcurementReportResponse,
    PurchaseOrderReportResponse,
    ReportCategory,
    ReportDownloadRequest,
    ReportExportResponse,
    ReportFileType,
    ReportListResponse,
    ReportStatus,
    ReportSummaryResponse,
    VendorPerformanceReportResponse,
)
from app.services.report_service import ReportService

router = APIRouter(
    prefix="/reports",
    tags=["Reports & Intelligence"],
)


@router.get(
    "/vendor-performance",
    response_model=VendorPerformanceReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Vendor Performance Report",
    description="Returns detailed vendor performance scoring, risk level classifications, category averages, and top vendors. Requires Admin, Procurement Manager, Logistics Manager, or Auditor role.",
)
async def get_vendor_performance_report(
    search: Optional[str] = Query(None, description="Search filter by vendor company name or vendor code."),
    db: AsyncSession = Depends(get_db),
    service: ReportService = Depends(get_report_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "SUPPLY_CHAIN_MANAGER", "FINANCE_OFFICER", "LOGISTICS_MANAGER", "AUDITOR")
    ),
) -> VendorPerformanceReportResponse:
    """
    Endpoint retrieving Vendor Performance Report.
    """
    generated_by = current_user.full_name or current_user.email or "System"
    return await service.get_vendor_performance_report(db, search=search, generated_by=generated_by)


@router.get(
    "/procurement",
    response_model=ProcurementReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Procurement Spend & Request Report",
    description="Returns procurement request metrics, spend totals, department spend breakdowns, category spend, and monthly trends. Requires Admin, Procurement Manager, Logistics Manager, or Auditor role.",
)
async def get_procurement_report(
    search: Optional[str] = Query(None, description="Search filter by request item description."),
    db: AsyncSession = Depends(get_db),
    service: ReportService = Depends(get_report_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "SUPPLY_CHAIN_MANAGER", "FINANCE_OFFICER", "LOGISTICS_MANAGER", "AUDITOR")
    ),
) -> ProcurementReportResponse:
    """
    Endpoint retrieving Procurement Report.
    """
    generated_by = current_user.full_name or current_user.email or "System"
    return await service.get_procurement_report(db, search=search, generated_by=generated_by)


@router.get(
    "/purchase-orders",
    response_model=PurchaseOrderReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Purchase Order Fulfillment Report",
    description="Returns PO status breakdown, total order value, pending approval count, fulfillment rate %, and top suppliers. Requires Admin, Procurement Manager, Logistics Manager, or Auditor role.",
)
async def get_purchase_order_report(
    search: Optional[str] = Query(None, description="Search filter by vendor name or PO number."),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by PO status (e.g. pending, approved, completed)."),
    db: AsyncSession = Depends(get_db),
    service: ReportService = Depends(get_report_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "SUPPLY_CHAIN_MANAGER", "FINANCE_OFFICER", "LOGISTICS_MANAGER", "AUDITOR")
    ),
) -> PurchaseOrderReportResponse:
    """
    Endpoint retrieving Purchase Order Report.
    """
    generated_by = current_user.full_name or current_user.email or "System"
    return await service.get_purchase_order_report(
        db, search=search, status=status_filter, generated_by=generated_by
    )


@router.get(
    "/compliance",
    response_model=ComplianceReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Vendor Compliance & Risk Audit Report",
    description="Returns vendor compliance rate %, compliant/non-compliant counts, risk level breakdowns, and recent non-conformity violations. Requires Admin, Procurement Manager, Logistics Manager, or Auditor role.",
)
async def get_compliance_report(
    search: Optional[str] = Query(None, description="Search filter by vendor name or issue type."),
    db: AsyncSession = Depends(get_db),
    service: ReportService = Depends(get_report_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "SUPPLY_CHAIN_MANAGER", "FINANCE_OFFICER", "LOGISTICS_MANAGER", "AUDITOR")
    ),
) -> ComplianceReportResponse:
    """
    Endpoint retrieving Compliance Report.
    """
    generated_by = current_user.full_name or current_user.email or "System"
    return await service.get_compliance_report(db, search=search, generated_by=generated_by)


@router.get(
    "/contracts",
    response_model=ContractReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Vendor Contract Lifecycle & Renewal Report",
    description="Returns contract metrics, renewal rates, status distributions, and upcoming expiration items. Requires Admin, Procurement Manager, Logistics Manager, or Auditor role.",
)
async def get_contract_report(
    search: Optional[str] = Query(None, description="Search filter by vendor name or contract number."),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by contract status."),
    db: AsyncSession = Depends(get_db),
    service: ReportService = Depends(get_report_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "SUPPLY_CHAIN_MANAGER", "FINANCE_OFFICER", "LOGISTICS_MANAGER", "AUDITOR")
    ),
) -> ContractReportResponse:
    """
    Endpoint retrieving Contract Report.
    """
    generated_by = current_user.full_name or current_user.email or "System"
    return await service.get_contract_report(
        db, search=search, status=status_filter, generated_by=generated_by
    )


@router.get(
    "/summary",
    response_model=ReportSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Reports Dashboard Summary",
    description="Returns high-level report generation summary covering total reports, reports by category, reports by status, temporal counts, and recent reports. Requires Admin, Procurement Manager, Logistics Manager, or Auditor role.",
)
async def get_report_summary(
    db: AsyncSession = Depends(get_db),
    service: ReportService = Depends(get_report_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "SUPPLY_CHAIN_MANAGER", "FINANCE_OFFICER", "LOGISTICS_MANAGER", "AUDITOR")
    ),
) -> ReportSummaryResponse:
    """
    Endpoint retrieving Reports Dashboard Summary.
    """
    return await service.get_report_summary(db)


@router.get(
    "/history",
    response_model=ReportListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Report History & Catalogue",
    description="Returns paginated list of available generated reports and system report catalogue items. Supports search, category filter, and offset pagination. Requires Admin, Procurement Manager, Logistics Manager, or Auditor role.",
)
async def get_report_history(
    search: Optional[str] = Query(None, description="Search filter by report title or description."),
    category: Optional[ReportCategory] = Query(None, description="Filter by report category."),
    status_filter: Optional[ReportStatus] = Query(None, alias="status", description="Filter by report generation status."),
    page: int = Query(1, ge=1, description="Current page number (1-indexed)."),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)."),
    db: AsyncSession = Depends(get_db),
    service: ReportService = Depends(get_report_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "SUPPLY_CHAIN_MANAGER", "FINANCE_OFFICER", "LOGISTICS_MANAGER", "AUDITOR")
    ),
) -> ReportListResponse:
    """
    Endpoint retrieving paginated report history catalogue.
    """
    cat_str = category.value if category else None
    st_str = status_filter.value if status_filter else None
    return await service.get_report_history(
        db, search=search, category=cat_str, status=st_str, page=page, page_size=page_size
    )


@router.post(
    "/export",
    response_model=ReportExportResponse,
    status_code=status.HTTP_200_OK,
    summary="Export or Request Report Download",
    description="Generates export metadata and secure download token for a specified report category and file format (pdf, csv, xlsx, json). Requires Admin, Procurement Manager, Logistics Manager, or Auditor role.",
)
async def export_report(
    category: ReportCategory = Query(..., description="Report category to export."),
    file_type: ReportFileType = Query(ReportFileType.PDF, description="Export file format (pdf, csv, xlsx, json)."),
    search: Optional[str] = Query(None, description="Optional search filter for exported dataset."),
    db: AsyncSession = Depends(get_db),
    service: ReportService = Depends(get_report_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "SUPPLY_CHAIN_MANAGER", "FINANCE_OFFICER", "LOGISTICS_MANAGER", "AUDITOR")
    ),
) -> ReportExportResponse:
    """
    Endpoint exporting report metadata and signed download token.
    """
    generated_by = current_user.full_name or current_user.email or "System"
    return await service.export_report(
        db,
        category=category,
        file_type=file_type,
        generated_by=generated_by,
        user_id=current_user.user_id,
        search=search,
    )


@router.post(
    "/download",
    status_code=status.HTTP_200_OK,
    summary="Authenticated Streamed Report Download",
    description="Streams actual report file bytes (JSON, CSV, PDF) using cryptographically signed download context token. Requires Admin, Procurement Manager, Supply Chain Manager, Finance Officer, Logistics Manager, or Auditor role.",
)
async def download_report(
    payload: ReportDownloadRequest,
    db: AsyncSession = Depends(get_db),
    service: ReportService = Depends(get_report_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "SUPPLY_CHAIN_MANAGER", "FINANCE_OFFICER", "LOGISTICS_MANAGER", "AUDITOR")
    ),
):
    """
    Endpoint validating signed download token and streaming file content.
    """
    token_str = payload.download_token.strip()
    if not token_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Required download_token cannot be empty.",
        )

    # 1. Decode and verify signature & claims
    try:
        data = jwt.decode(
            token_str,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired report download token: {str(e)}",
        )

    # 2. Validate token subject claim
    if data.get("sub") != "report_download":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid download token subject.",
        )

    # 3. Validate presence of required token claims
    required_claims = ["report_id", "category", "file_type", "user_id", "exp", "iat"]
    missing_claims = [c for c in required_claims if c not in data]
    if missing_claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Missing required claims in download token: {missing_claims}",
        )

    # 4. User binding verification
    if str(data.get("user_id")) != str(current_user.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Report download token was issued to a different user.",
        )

    # 5. Extract category and file_type
    try:
        category = ReportCategory(data["category"])
        file_type = ReportFileType(data["file_type"])
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid category or file format in token: {str(e)}",
        )

    search_query = data.get("search") or None

    # 6. Check unsupported format (XLSX)
    if file_type == ReportFileType.XLSX:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="XLSX export format is not supported by backend.",
        )

    # 7. Synthesize report file bytes using existing generators
    try:
        content_bytes, mime_type, filename = await service.generate_report_file_content(
            db,
            category=category,
            file_type=file_type,
            search=search_query,
            generated_by=current_user.full_name or current_user.email or "System",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return Response(
        content=content_bytes,
        media_type=mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(content_bytes)),
        },
    )
