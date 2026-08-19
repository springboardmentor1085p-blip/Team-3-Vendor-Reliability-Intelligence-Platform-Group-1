"""
FastAPI Router for Delivery Tracking endpoints with Role-Based Access Control (RBAC).
"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    DeliveryDomainError,
    DeliveryNotFoundError,
    InvalidDeliveryDataError,
    PurchaseOrderNotFoundError,
)
from app.database import get_db
from app.dependencies import get_current_user, get_delivery_service, require_roles
from app.models.delivery import DeliveryStatusEnum
from app.models.users import User
from app.schemas.delivery import (
    DeliveryTrackingCreate,
    DeliveryTrackingResponse,
    DeliveryTrackingUpdate,
)
from app.services.delivery_service import DeliveryService

router = APIRouter(
    prefix="/deliveries",
    tags=["Delivery Tracking"],
)


@router.post(
    "",
    response_model=DeliveryTrackingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create delivery tracking record",
    description="Creates a new delivery tracking record for an eligible Purchase Order.",
)
async def create_delivery(
    delivery_in: DeliveryTrackingCreate,
    db: AsyncSession = Depends(get_db),
    service: DeliveryService = Depends(get_delivery_service),
    current_user: User = Depends(get_current_user),
) -> DeliveryTrackingResponse:
    """
    Create a new delivery tracking record.
    """
    try:
        return await service.create_delivery(db, delivery_in)
    except PurchaseOrderNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except (InvalidDeliveryDataError, DeliveryDomainError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.get(
    "",
    response_model=list[DeliveryTrackingResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all delivery tracking records",
    description="Returns a paginated list of delivery tracking records with optional query filters.",
)
async def get_all_deliveries(
    skip: int = Query(0, ge=0, description="Number of records to skip."),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return."),
    po_id: UUID | None = Query(None, description="Filter by Purchase Order ID."),
    status_filter: DeliveryStatusEnum | None = Query(
        None, alias="status", description="Filter by delivery status."
    ),
    carrier: str | None = Query(None, description="Filter by logistics carrier."),
    db: AsyncSession = Depends(get_db),
    service: DeliveryService = Depends(get_delivery_service),
    current_user: User = Depends(get_current_user),
) -> list[DeliveryTrackingResponse]:
    """
    Retrieve all delivery tracking records with optional query filters.
    """
    return await service.get_all_deliveries(
        db,
        skip=skip,
        limit=limit,
        po_id=po_id,
        status=status_filter,
        carrier=carrier,
    )


@router.get(
    "/{delivery_id}",
    response_model=DeliveryTrackingResponse,
    status_code=status.HTTP_200_OK,
    summary="Get delivery record by ID",
    description="Returns delivery tracking details for the given UUID.",
)
async def get_delivery_by_id(
    delivery_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: DeliveryService = Depends(get_delivery_service),
    current_user: User = Depends(get_current_user),
) -> DeliveryTrackingResponse:
    """
    Retrieve a delivery tracking record by UUID.
    """
    try:
        return await service.get_delivery_by_id(db, delivery_id)
    except DeliveryNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )


@router.patch(
    "/{delivery_id}",
    response_model=DeliveryTrackingResponse,
    status_code=status.HTTP_200_OK,
    summary="Update delivery tracking record",
    description="Updates tracking number, carrier, expected date, or remarks for a delivery record.",
)
async def update_delivery(
    delivery_id: UUID,
    delivery_in: DeliveryTrackingUpdate,
    db: AsyncSession = Depends(get_db),
    service: DeliveryService = Depends(get_delivery_service),
    current_user: User = Depends(get_current_user),
) -> DeliveryTrackingResponse:
    """
    Update delivery tracking details.
    """
    try:
        return await service.update_delivery(db, delivery_id, delivery_in)
    except DeliveryNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except (InvalidDeliveryDataError, DeliveryDomainError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.post(
    "/{delivery_id}/dispatch",
    response_model=DeliveryTrackingResponse,
    status_code=status.HTTP_200_OK,
    summary="Dispatch shipment",
    description="Updates delivery status to IN_TRANSIT and automatically assigns dispatch_date. Requires Admin or Logistics role.",
)
async def dispatch_delivery(
    delivery_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: DeliveryService = Depends(get_delivery_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "LOGISTICS", "LOGISTICS_MANAGER")
    ),
) -> DeliveryTrackingResponse:
    """
    Dispatch a shipment.
    """
    try:
        return await service.dispatch_delivery(db, delivery_id)
    except DeliveryNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except (InvalidDeliveryDataError, DeliveryDomainError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.post(
    "/{delivery_id}/deliver",
    response_model=DeliveryTrackingResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark shipment as delivered",
    description="Updates delivery status to DELIVERED, automatically assigns delivered_date, and synchronizes Purchase Order status when all shipments complete. Requires Admin or Logistics role.",
)
async def mark_delivered(
    delivery_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: DeliveryService = Depends(get_delivery_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "LOGISTICS", "LOGISTICS_MANAGER")
    ),
) -> DeliveryTrackingResponse:
    """
    Mark a shipment as DELIVERED.
    """
    try:
        return await service.mark_delivered(db, delivery_id)
    except DeliveryNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except (InvalidDeliveryDataError, DeliveryDomainError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.post(
    "/{delivery_id}/delay",
    response_model=DeliveryTrackingResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark shipment as delayed",
    description="Updates delivery status to DELAYED and optionally updates expected date or remarks. Requires Admin or Logistics role.",
)
async def mark_delayed(
    delivery_id: UUID,
    new_expected_date: date | None = Query(None, description="Optional new expected delivery date."),
    remarks: str | None = Query(None, description="Optional delay remarks."),
    db: AsyncSession = Depends(get_db),
    service: DeliveryService = Depends(get_delivery_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "LOGISTICS", "LOGISTICS_MANAGER")
    ),
) -> DeliveryTrackingResponse:
    """
    Mark a shipment as DELAYED.
    """
    try:
        return await service.mark_delayed(
            db, delivery_id, new_expected_date=new_expected_date, remarks=remarks
        )
    except DeliveryNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except (InvalidDeliveryDataError, DeliveryDomainError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.post(
    "/{delivery_id}/return",
    response_model=DeliveryTrackingResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark shipment as returned",
    description="Updates delivery status to RETURNED. Requires Admin or Logistics role.",
)
async def mark_returned(
    delivery_id: UUID,
    remarks: str | None = Query(None, description="Optional return remarks."),
    db: AsyncSession = Depends(get_db),
    service: DeliveryService = Depends(get_delivery_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "LOGISTICS", "LOGISTICS_MANAGER")
    ),
) -> DeliveryTrackingResponse:
    """
    Mark a shipment as RETURNED.
    """
    try:
        return await service.mark_returned(db, delivery_id, remarks=remarks)
    except DeliveryNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except (InvalidDeliveryDataError, DeliveryDomainError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )
