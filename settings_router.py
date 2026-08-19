"""
FastAPI Router for Settings endpoints with PostgreSQL persistence.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.users import User
from app.schemas.settings import UserSettingsResponse, UserSettingsUpdate
from app.services.settings_service import settings_service

router = APIRouter(
    prefix="/settings",
    tags=["Settings"],
)


@router.get(
    "",
    response_model=UserSettingsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user and system settings",
    description="Retrieve preferences, company settings, and security options from PostgreSQL.",
)
async def get_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserSettingsResponse:
    """
    Retrieve settings persisted in PostgreSQL for the current authenticated user.
    """
    return await settings_service.get_settings(db, current_user)


@router.put(
    "",
    response_model=UserSettingsResponse,
    status_code=status.HTTP_200_OK,
    summary="Update settings",
    description="Update user settings and preferences in PostgreSQL.",
)
async def update_settings(
    settings_in: UserSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserSettingsResponse:
    """
    Update settings in PostgreSQL for the current authenticated user.
    """
    return await settings_service.update_settings(db, current_user, settings_in)
