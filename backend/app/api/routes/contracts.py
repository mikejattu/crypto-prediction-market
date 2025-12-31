from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import Optional

from app.db.database import get_db
from app.db.models import Contract
from app.schemas.contract import (
    ContractCreate,
    ContractUpdate,
    ContractResponse,
    ContractListResponse
)

router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.post("/", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
async def create_contract(
    contract: ContractCreate,
    db: AsyncSession = Depends(get_db)
):
    db_contract = Contract(**contract.model_dump())
    db.add(db_contract)
    await db.commit()
    await db.refresh(db_contract)
    return db_contract


@router.get("/", response_model=ContractListResponse)
async def list_contracts(
    skip: int = 0,
    limit: int = 100,
    market_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(Contract)

    if market_id:
        query = query.where(Contract.market_id == market_id)

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    contracts = result.scalars().all()

    count_query = select(Contract)
    if market_id:
        count_query = count_query.where(Contract.market_id == market_id)

    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())

    return ContractListResponse(contracts=contracts, total=total)


@router.get("/{contract_id}", response_model=ContractResponse)
async def get_contract(
    contract_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    contract = await db.get(Contract, contract_id)

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with id {contract_id} not found"
        )

    return contract


@router.put("/{contract_id}", response_model=ContractResponse)
async def update_contract(
    contract_id: UUID,
    contract_update: ContractUpdate,
    db: AsyncSession = Depends(get_db)
):
    contract = await db.get(Contract, contract_id)

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with id {contract_id} not found"
        )

    update_data = contract_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(contract, field, value)

    await db.commit()
    await db.refresh(contract)

    return contract


@router.delete("/{contract_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contract(
    contract_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    contract = await db.get(Contract, contract_id)

    if not contract:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Contract with id {contract_id} not found"
        )

    await db.delete(contract)
    await db.commit()

    return None
