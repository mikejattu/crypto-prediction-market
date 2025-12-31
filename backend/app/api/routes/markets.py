from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import Optional

from app.db.database import get_db
from app.db.models import Market
from app.schemas.market import (
    MarketCreate,
    MarketUpdate,
    MarketResponse,
    MarketListResponse,
)

router = APIRouter(prefix="/markets", tags=["markets"])


@router.post("/", response_model=MarketResponse, status_code=status.HTTP_201_CREATED)
async def create_market(market: MarketCreate, db: AsyncSession = Depends(get_db)):
    db_market = Market(**market.model_dump())
    db.add(db_market)
    await db.commit()
    await db.refresh(db_market)
    return db_market


@router.get("/", response_model=MarketListResponse)
async def list_markets(
    skip: int = 0,
    limit: int = 100,
    platform_id: Optional[UUID] = None,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Market)

    if platform_id:
        query = query.where(Market.platform_id == platform_id)

    if status_filter:
        query = query.where(Market.status == status_filter)

    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    markets = result.scalars().all()

    count_query = select(Market)
    if platform_id:
        count_query = count_query.where(Market.platform_id == platform_id)
    if status_filter:
        count_query = count_query.where(Market.status == status_filter)

    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())

    return MarketListResponse(markets=markets, total=total)


@router.get("/{market_id}", response_model=MarketResponse)
async def get_market(market_id: UUID, db: AsyncSession = Depends(get_db)):
    market = await db.get(Market, market_id)

    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Market with id {market_id} not found",
        )

    return market


@router.put("/{market_id}", response_model=MarketResponse)
async def update_market(
    market_id: UUID, market_update: MarketUpdate, db: AsyncSession = Depends(get_db)
):
    market = await db.get(Market, market_id)

    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Market with id {market_id} not found",
        )

    update_data = market_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(market, field, value)

    await db.commit()
    await db.refresh(market)

    return market


@router.delete("/{market_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_market(market_id: UUID, db: AsyncSession = Depends(get_db)):
    market = await db.get(Market, market_id)

    if not market:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Market with id {market_id} not found",
        )

    await db.delete(market)
    await db.commit()

    return None
