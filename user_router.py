"""
FastAPI Router for User endpoints.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InvalidUserDataError,
    RoleNotFoundError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.database import get_db
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from app.services.user_service import UserService, user_service


def get_user_service() -> UserService:
    """
    Dependency provider for UserService.
    """
    return user_service


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Create a new user after validating username and email uniqueness.",
)
async def create_user(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Create a new user.
    """
    try:
        return await service.create_user(db, user_in)
    except RoleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )
    except InvalidUserDataError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.get(
    "",
    response_model=list[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all users",
    description="Retrieve paginated list of users.",
)
async def get_all_users(
    skip: int = Query(
        default=0,
        ge=0,
        description="Number of records to skip.",
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of records to return.",
    ),
    db: AsyncSession = Depends(get_db),
    service: UserService = Depends(get_user_service),
) -> list[UserResponse]:
    """
    Retrieve all users.
    """
    try:
        return await service.get_all_users(
            db=db,
            skip=skip,
            limit=limit,
        )
    except InvalidUserDataError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user by ID",
    description="Retrieve a single user using UUID.",
)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Retrieve a user by ID.
    """
    try:
        return await service.get_user(db, user_id)
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update user",
    description="Update an existing user's information.",
)
async def update_user(
    user_id: UUID,
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Update user information.
    """
    try:
        return await service.update_user(db, user_id, user_in)
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except RoleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message,
        )
    except InvalidUserDataError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )


@router.delete(
    "/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Soft delete user",
    description="Deactivate a user account by setting is_active to False.",
)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Soft delete a user.
    """
    try:
        return await service.delete_user(db, user_id)
    except UserNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
    except InvalidUserDataError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        )