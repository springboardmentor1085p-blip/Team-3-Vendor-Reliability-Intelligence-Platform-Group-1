"""
FastAPI Router for Invoice endpoints with Role-Based Access Control (RBAC).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InvalidInvoiceDataError,
    InvoiceDomainError,
    InvoiceNotFoundError,
    PurchaseOrderNotFoundError,
    VendorNotFoundError,
)
from app.database import get_db
from app.dependencies import get_current_user, get_invoice_service, require_roles
from app.models.invoices import InvoiceStatusEnum
from app.models.users import User
from app.schemas.invoices import (
    InvoiceCreate,
    InvoiceResponse,
    InvoiceUpdate,
)
from app.services.invoice_service import InvoiceService

router = APIRouter(
    prefix="/invoices",
    tags=["Invoices"],
)


@router.post(
    "",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an invoice",
    description="Creates a new invoice against an eligible Purchase Order. Auto-generates invoice number.",
)
async def create_invoice(
    invoice_in: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
    service: InvoiceService = Depends(get_invoice_service),
    current_user: User = Depends(get_current_user),
) -> InvoiceResponse:
    """
    Create a new invoice.
    """
    try:
        return await service.create_invoice(db, invoice_in)
    except (PurchaseOrderNotFoundError, VendorNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except (InvalidInvoiceDataError, InvoiceDomainError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.get(
    "",
    response_model=list[InvoiceResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all invoices",
    description="Returns a paginated list of invoices with optional filters for vendor_id, po_id, and status.",
)
async def get_all_invoices(
    skip: int = Query(0, ge=0, description="Number of records to skip."),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return."),
    vendor_id: UUID | None = Query(None, description="Filter by vendor ID."),
    po_id: UUID | None = Query(None, description="Filter by Purchase Order ID."),
    status_filter: InvoiceStatusEnum | None = Query(
        None, alias="status", description="Filter by invoice status."
    ),
    db: AsyncSession = Depends(get_db),
    service: InvoiceService = Depends(get_invoice_service),
    current_user: User = Depends(get_current_user),
) -> list[InvoiceResponse]:
    """
    Retrieve all invoices with optional query filters.
    """
    return await service.get_all_invoices(
        db,
        skip=skip,
        limit=limit,
        vendor_id=vendor_id,
        po_id=po_id,
        status=status_filter,
    )


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get invoice by ID",
    description="Returns invoice details for the given UUID.",
)
async def get_invoice_by_id(
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: InvoiceService = Depends(get_invoice_service),
    current_user: User = Depends(get_current_user),
) -> InvoiceResponse:
    """
    Retrieve an invoice by UUID.
    """
    try:
        return await service.get_invoice_by_id(db, invoice_id)
    except InvoiceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )


@router.patch(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    status_code=status.HTTP_200_OK,
    summary="Update invoice",
    description="Updates an existing invoice.",
)
async def update_invoice(
    invoice_id: UUID,
    invoice_in: InvoiceUpdate,
    db: AsyncSession = Depends(get_db),
    service: InvoiceService = Depends(get_invoice_service),
    current_user: User = Depends(get_current_user),
) -> InvoiceResponse:
    """
    Update invoice details.
    """
    try:
        return await service.update_invoice(db, invoice_id, invoice_in)
    except InvoiceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except (InvalidInvoiceDataError, InvoiceDomainError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.post(
    "/{invoice_id}/pay",
    response_model=InvoiceResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark invoice as paid",
    description="Updates invoice status to PAID and automatically assigns paid_date. Requires Admin or Finance role.",
)
async def pay_invoice(
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: InvoiceService = Depends(get_invoice_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "FINANCE", "FINANCE_MANAGER")
    ),
) -> InvoiceResponse:
    """
    Mark an invoice as PAID.
    """
    try:
        return await service.update_invoice_status(db, invoice_id, InvoiceStatusEnum.PAID)
    except InvoiceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except (InvalidInvoiceDataError, InvoiceDomainError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.post(
    "/{invoice_id}/dispute",
    response_model=InvoiceResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark invoice as disputed",
    description="Updates invoice status to DISPUTED. Requires Admin or Finance role.",
)
async def dispute_invoice(
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: InvoiceService = Depends(get_invoice_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "FINANCE", "FINANCE_MANAGER")
    ),
) -> InvoiceResponse:
    """
    Mark an invoice as DISPUTED.
    """
    try:
        return await service.update_invoice_status(db, invoice_id, InvoiceStatusEnum.DISPUTED)
    except InvoiceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except (InvalidInvoiceDataError, InvoiceDomainError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )
