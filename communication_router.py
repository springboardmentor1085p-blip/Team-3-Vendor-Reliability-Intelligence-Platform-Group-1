"""
FastAPI Router for Communication / Messages endpoints.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundError
from app.database import get_db
from app.dependencies import get_current_user
from app.models.users import User
from app.schemas.communication import MessageCreate, MessageResponse
from app.services.communication_service import communication_service

router = APIRouter(
    prefix="/communications",
    tags=["Communication"],
)


@router.post(
    "",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a message",
    description="Send a message to a user or vendor.",
)
async def send_message(
    message_in: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    return await communication_service.send_message(db, current_user.user_id, message_in)


@router.get(
    "",
    response_model=List[MessageResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all messages",
    description="Retrieve all messages.",
)
async def get_all_messages(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> List[MessageResponse]:
    return await communication_service.get_all_messages(db, skip=skip, limit=limit)


@router.get(
    "/{message_id}",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Get message by ID",
    description="Retrieve a specific message by ID.",
)
async def get_message_by_id(
    message_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    try:
        return await communication_service.get_message(db, message_id)
    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
