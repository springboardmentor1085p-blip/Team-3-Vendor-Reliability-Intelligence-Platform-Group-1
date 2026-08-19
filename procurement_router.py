"""
FastAPI Router for Procurement endpoints with Role-Based Access Control (RBAC).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InvalidProcurementDataError,
    ProcurementDomainError,
    ProcurementRequestNotFoundError,
    PurchaseOrderNotFoundError,
    VendorNotFoundError,
)
from app.database import get_db
from app.dependencies import get_current_user, get_procurement_service, require_roles
from app.models.procurement import PurchaseOrderStatusEnum
from app.models.users import User
from app.schemas.procurement import (
    ProcurementRequestCreate,
    ProcurementRequestResponse,
    ProcurementRequestUpdate,
    PurchaseOrderCreate,
    PurchaseOrderResponse,
    PurchaseOrderUpdate,
)
from app.services.procurement_service import ProcurementService

router = APIRouter(
    prefix="/procurement",
    tags=["Procurement"],
)


# ======================================================================
# 1. PROCUREMENT REQUEST ENDPOINTS
# ======================================================================

@router.post(
    "/requests",
    response_model=ProcurementRequestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a procurement request",
    description="Creates a new procurement request. Auto-generates PR number.",
)
async def create_request(
    request_in: ProcurementRequestCreate,
    db: AsyncSession = Depends(get_db),
    service: ProcurementService = Depends(get_procurement_service),
    current_user: User = Depends(get_current_user),
) -> ProcurementRequestResponse:
    """
    Create a new procurement request.
    """
    try:
        return await service.create_request(db, request_in, current_user.user_id)
    except (InvalidProcurementDataError, ProcurementDomainError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.get(
    "/requests",
    response_model=list[ProcurementRequestResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all procurement requests",
    description="Returns a paginated list of procurement requests.",
)
async def get_all_requests(
    skip: int = Query(0, ge=0, description="Number of records to skip."),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return."),
    db: AsyncSession = Depends(get_db),
    service: ProcurementService = Depends(get_procurement_service),
    current_user: User = Depends(get_current_user),
) -> list[ProcurementRequestResponse]:
    """
    Retrieve all procurement requests.
    """
    return await service.get_all_requests(db, skip=skip, limit=limit)


@router.get(
    "/requests/{request_id}",
    response_model=ProcurementRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Get procurement request by ID",
    description="Returns procurement request details for the given UUID.",
)
async def get_request_by_id(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: ProcurementService = Depends(get_procurement_service),
    current_user: User = Depends(get_current_user),
) -> ProcurementRequestResponse:
    """
    Retrieve a procurement request by UUID.
    """
    try:
        return await service.get_request_by_id(db, request_id)
    except ProcurementRequestNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )


@router.patch(
    "/requests/{request_id}",
    response_model=ProcurementRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Update procurement request",
    description="Updates an existing procurement request.",
)
async def update_request(
    request_id: UUID,
    request_in: ProcurementRequestUpdate,
    db: AsyncSession = Depends(get_db),
    service: ProcurementService = Depends(get_procurement_service),
    current_user: User = Depends(get_current_user),
) -> ProcurementRequestResponse:
    """
    Update a procurement request.
    """
    try:
        return await service.update_request(db, request_id, request_in)
    except ProcurementRequestNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except (InvalidProcurementDataError, ProcurementDomainError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.post(
    "/requests/{request_id}/approve",
    response_model=ProcurementRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve procurement request",
    description="Approves a procurement request. Requires Admin or Procurement Manager role.",
)
async def approve_request(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: ProcurementService = Depends(get_procurement_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "PROCUREMENT MANAGER")
    ),
) -> ProcurementRequestResponse:
    """
    Approve a procurement request.
    """
    try:
        return await service.approve_request(db, request_id, current_user.user_id)
    except ProcurementRequestNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except (InvalidProcurementDataError, ProcurementDomainError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.post(
    "/requests/{request_id}/reject",
    response_model=ProcurementRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Reject procurement request",
    description="Rejects a procurement request. Requires Admin or Procurement Manager role.",
)
async def reject_request(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: ProcurementService = Depends(get_procurement_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "PROCUREMENT MANAGER")
    ),
) -> ProcurementRequestResponse:
    """
    Reject a procurement request.
    """
    try:
        return await service.reject_request(db, request_id)
    except ProcurementRequestNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except (InvalidProcurementDataError, ProcurementDomainError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.post(
    "/requests/{request_id}/cancel",
    response_model=ProcurementRequestResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel procurement request",
    description="Cancels a procurement request.",
)
async def cancel_request(
    request_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: ProcurementService = Depends(get_procurement_service),
    current_user: User = Depends(get_current_user),
) -> ProcurementRequestResponse:
    """
    Cancel a procurement request.
    """
    try:
        return await service.cancel_request(db, request_id)
    except ProcurementRequestNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except (InvalidProcurementDataError, ProcurementDomainError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


# ======================================================================
# 2. PURCHASE ORDER ENDPOINTS
# ======================================================================

@router.post(
    "/purchase-orders",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a purchase order",
    description="Creates a new purchase order with line items. Vendor must be APPROVED. Requires Admin or Procurement Manager role.",
)
async def create_purchase_order(
    po_in: PurchaseOrderCreate,
    db: AsyncSession = Depends(get_db),
    service: ProcurementService = Depends(get_procurement_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "PROCUREMENT MANAGER")
    ),
) -> PurchaseOrderResponse:
    """
    Create a new purchase order.
    """
    try:
        return await service.create_purchase_order(db, po_in, current_user.user_id)
    except (VendorNotFoundError, ProcurementRequestNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except (InvalidProcurementDataError, ProcurementDomainError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.get(
    "/purchase-orders",
    response_model=list[PurchaseOrderResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all purchase orders",
    description="Returns a paginated list of purchase orders with line items.",
)
async def get_all_pos(
    skip: int = Query(0, ge=0, description="Number of records to skip."),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return."),
    db: AsyncSession = Depends(get_db),
    service: ProcurementService = Depends(get_procurement_service),
    current_user: User = Depends(get_current_user),
) -> list[PurchaseOrderResponse]:
    """
    Retrieve all purchase orders.
    """
    return await service.get_all_pos(db, skip=skip, limit=limit)


@router.get(
    "/purchase-orders/{po_id}",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Get purchase order by ID",
    description="Returns purchase order details with line items for the given UUID.",
)
async def get_po_by_id(
    po_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: ProcurementService = Depends(get_procurement_service),
    current_user: User = Depends(get_current_user),
) -> PurchaseOrderResponse:
    """
    Retrieve a purchase order by UUID.
    """
    try:
        return await service.get_po_by_id(db, po_id)
    except PurchaseOrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )


@router.patch(
    "/purchase-orders/{po_id}",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Update purchase order",
    description="Updates an existing purchase order. Requires Admin or Procurement Manager role.",
)
async def update_purchase_order(
    po_id: UUID,
    po_in: PurchaseOrderUpdate,
    db: AsyncSession = Depends(get_db),
    service: ProcurementService = Depends(get_procurement_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "PROCUREMENT MANAGER")
    ),
) -> PurchaseOrderResponse:
    """
    Update purchase order details.
    """
    try:
        return await service.update_purchase_order(db, po_id, po_in)
    except PurchaseOrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except (InvalidProcurementDataError, ProcurementDomainError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.post(
    "/purchase-orders/{po_id}/approve",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve purchase order",
    description="Updates purchase order status to APPROVED. Requires Admin or Procurement Manager role.",
)
async def approve_po(
    po_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: ProcurementService = Depends(get_procurement_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "PROCUREMENT MANAGER")
    ),
) -> PurchaseOrderResponse:
    """
    Approve a purchase order.
    """
    try:
        return await service.update_po_status(db, po_id, PurchaseOrderStatusEnum.APPROVED)
    except PurchaseOrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except (InvalidProcurementDataError, ProcurementDomainError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.post(
    "/purchase-orders/{po_id}/order",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark purchase order as ordered",
    description="Updates purchase order status to ORDERED. Requires Admin or Procurement Manager role.",
)
async def order_po(
    po_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: ProcurementService = Depends(get_procurement_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "PROCUREMENT MANAGER")
    ),
) -> PurchaseOrderResponse:
    """
    Mark a purchase order as ORDERED.
    """
    try:
        return await service.update_po_status(db, po_id, PurchaseOrderStatusEnum.ORDERED)
    except PurchaseOrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except (InvalidProcurementDataError, ProcurementDomainError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.post(
    "/purchase-orders/{po_id}/deliver",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark purchase order as delivered",
    description="Updates purchase order status to DELIVERED. Requires Admin or Procurement Manager role.",
)
async def deliver_po(
    po_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: ProcurementService = Depends(get_procurement_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "PROCUREMENT MANAGER")
    ),
) -> PurchaseOrderResponse:
    """
    Mark a purchase order as DELIVERED.
    """
    try:
        return await service.update_po_status(db, po_id, PurchaseOrderStatusEnum.DELIVERED)
    except PurchaseOrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except (InvalidProcurementDataError, ProcurementDomainError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.post(
    "/purchase-orders/{po_id}/complete",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark purchase order as completed",
    description="Updates purchase order status to COMPLETED. Requires Admin or Procurement Manager role.",
)
async def complete_po(
    po_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: ProcurementService = Depends(get_procurement_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "PROCUREMENT MANAGER")
    ),
) -> PurchaseOrderResponse:
    """
    Mark a purchase order as COMPLETED.
    """
    try:
        return await service.update_po_status(db, po_id, PurchaseOrderStatusEnum.COMPLETED)
    except PurchaseOrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except (InvalidProcurementDataError, ProcurementDomainError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.post(
    "/purchase-orders/{po_id}/cancel",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel purchase order",
    description="Updates purchase order status to CANCELLED. Requires Admin or Procurement Manager role.",
)
async def cancel_po(
    po_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: ProcurementService = Depends(get_procurement_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "PROCUREMENT MANAGER")
    ),
) -> PurchaseOrderResponse:
    """
    Cancel a purchase order.
    """
    try:
        return await service.update_po_status(db, po_id, PurchaseOrderStatusEnum.CANCELLED)
    except PurchaseOrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except (InvalidProcurementDataError, ProcurementDomainError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )
