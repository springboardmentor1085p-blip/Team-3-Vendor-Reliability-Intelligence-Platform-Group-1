"""
FastAPI Router for Contracts endpoints.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EntityNotFoundError
from app.database import get_db
from app.schemas.contracts import (
    ContractCreate,
    ContractResponse,
    ContractUpdate,
)
from app.services.contract_service import contract_service

router = APIRouter(
    prefix="/contracts",
    tags=["Contracts"],
)


@router.post(
    "",
    response_model=ContractResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a contract",
    description="Create a new contract record for a vendor.",
)
async def create_contract(
    contract_in: ContractCreate,
    db: AsyncSession = Depends(get_db),
) -> ContractResponse:
    return await contract_service.create_contract(db, contract_in)


@router.get(
    "",
    response_model=List[ContractResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all contracts",
    description="Retrieve all contract records.",
)
async def get_all_contracts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> List[ContractResponse]:
    return await contract_service.get_all_contracts(db, skip=skip, limit=limit)


@router.get(
    "/{contract_id}",
    response_model=ContractResponse,
    status_code=status.HTTP_200_OK,
    summary="Get contract by ID",
    description="Retrieve details for a specific contract.",
)
async def get_contract_by_id(
    contract_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ContractResponse:
    try:
        return await contract_service.get_contract(db, contract_id)
    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )


@router.put(
    "/{contract_id}",
    response_model=ContractResponse,
    status_code=status.HTTP_200_OK,
    summary="Update contract",
    description="Update an existing contract record.",
)
async def update_contract(
    contract_id: UUID,
    contract_in: ContractUpdate,
    db: AsyncSession = Depends(get_db),
) -> ContractResponse:
    try:
        return await contract_service.update_contract(db, contract_id, contract_in)
    except EntityNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message,
        )
