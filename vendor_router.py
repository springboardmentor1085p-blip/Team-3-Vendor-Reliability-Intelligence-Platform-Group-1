"""
FastAPI Router for Vendor endpoints with Role-Based Access Control (RBAC).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InvalidVendorDataError,
    UserNotFoundError,
    VendorAlreadyExistsError,
    VendorCategoryNotFoundError,
    VendorDomainError,
    VendorNotFoundError,
)
from app.database import get_db
from app.dependencies import get_current_user, get_vendor_service, require_roles
from app.models.users import User
from app.schemas.vendor import (
    VendorCreate,
    VendorResponse,
    VendorUpdate,
)
from app.services.vendor_service import VendorService

router = APIRouter(
    prefix="/vendors",
    tags=["Vendors"],
)


@router.post(
    "",
    response_model=VendorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new vendor",
    description="Creates a new vendor after validating business rules. Requires Admin or Procurement Manager role.",
)
async def create_vendor(
    vendor_in: VendorCreate,
    db: AsyncSession = Depends(get_db),
    service: VendorService = Depends(get_vendor_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "PROCUREMENT MANAGER")
    ),
) -> VendorResponse:
    """
    Create a new vendor.
    """
    try:
        return await service.create_vendor(db, vendor_in)

    except VendorAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )

    except (VendorCategoryNotFoundError, UserNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )

    except (InvalidVendorDataError, VendorDomainError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.get(
    "",
    response_model=list[VendorResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all vendors",
    description="Returns a paginated list of vendors. Requires authentication.",
)
async def get_all_vendors(
    skip: int = Query(
        0,
        ge=0,
        description="Number of records to skip.",
    ),
    limit: int = Query(
        100,
        ge=1,
        le=1000,
        description="Maximum number of records to return.",
    ),
    db: AsyncSession = Depends(get_db),
    service: VendorService = Depends(get_vendor_service),
    current_user: User = Depends(get_current_user),
) -> list[VendorResponse]:
    """
    Retrieve all vendors.
    """
    return await service.get_all_vendors(
        db,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/code/{vendor_code}",
    response_model=VendorResponse,
    status_code=status.HTTP_200_OK,
    summary="Get vendor by code",
    description="Returns vendor details for the given unique vendor code. Requires authentication.",
)
async def get_vendor_by_code(
    vendor_code: str,
    db: AsyncSession = Depends(get_db),
    service: VendorService = Depends(get_vendor_service),
    current_user: User = Depends(get_current_user),
) -> VendorResponse:
    """
    Retrieve a vendor by unique vendor code.
    """
    try:
        return await service.get_vendor_by_code(
            db,
            vendor_code,
        )

    except VendorNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )


@router.get(
    "/{vendor_id}",
    response_model=VendorResponse,
    status_code=status.HTTP_200_OK,
    summary="Get vendor by ID",
    description="Returns vendor details for the given vendor ID. Requires authentication.",
)
async def get_vendor_by_id(
    vendor_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: VendorService = Depends(get_vendor_service),
    current_user: User = Depends(get_current_user),
) -> VendorResponse:
    """
    Retrieve a vendor by UUID.
    """
    try:
        return await service.get_vendor_by_id(
            db,
            vendor_id,
        )

    except VendorNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )


@router.put(
    "/{vendor_id}",
    response_model=VendorResponse,
    status_code=status.HTTP_200_OK,
    summary="Update vendor",
    description="Updates an existing vendor. Requires Admin or Procurement Manager role.",
)
async def update_vendor(
    vendor_id: UUID,
    vendor_in: VendorUpdate,
    db: AsyncSession = Depends(get_db),
    service: VendorService = Depends(get_vendor_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "PROCUREMENT MANAGER")
    ),
) -> VendorResponse:
    """
    Update vendor information.
    """
    try:
        return await service.update_vendor(
            db,
            vendor_id,
            vendor_in,
        )

    except (VendorNotFoundError, VendorCategoryNotFoundError, UserNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )

    except VendorAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )

    except (InvalidVendorDataError, VendorDomainError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.delete(
    "/{vendor_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete vendor",
    description="Deletes an existing vendor. Requires Admin role.",
)
async def delete_vendor(
    vendor_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: VendorService = Depends(get_vendor_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "PROCUREMENT MANAGER")
    ),
):
    """
    Delete a vendor.
    """
    try:
        await service.delete_vendor(
            db,
            vendor_id,
        )
        return {"message": "Vendor deleted successfully", "vendor_id": str(vendor_id)}

    except VendorNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )

    except (InvalidVendorDataError, VendorDomainError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.post(
    "/{vendor_id}/approve",
    response_model=VendorResponse,
    status_code=status.HTTP_200_OK,
    summary="Approve vendor",
    description="Approves a vendor. Requires Admin or Procurement Manager role.",
)
async def approve_vendor(
    vendor_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: VendorService = Depends(get_vendor_service),
    current_user: User = Depends(
        require_roles("ADMIN", "ADMINISTRATOR", "PROCUREMENT_MANAGER", "PROCUREMENT MANAGER")
    ),
) -> VendorResponse:
    """
    Approve a vendor.
    """
    try:
        return await service.approve_vendor(
            db,
            vendor_id,
            current_user.user_id,
        )
    except VendorNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except (InvalidVendorDataError, VendorDomainError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )