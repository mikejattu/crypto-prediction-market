from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from uuid import UUID
from datetime import datetime, timedelta
import asyncio

from app.db.database import get_db
from app.db.models import CryptoPrice, CryptoCategory
from app.schemas.crypto_price import (
    CryptoPriceWithCategory,
    LatestPricesResponse,
    PriceHistoryResponse,
)
from app.tasks.price_fetcher import fetch_and_store_prices

router = APIRouter(prefix="/prices", tags=["prices"])


@router.get("/latest", response_model=LatestPricesResponse)
async def get_latest_prices(db: AsyncSession = Depends(get_db)):
    subquery = (
        select(
            CryptoPrice.crypto_category_id,
            func.max(CryptoPrice.fetched_at).label("max_fetched"),
        )
        .group_by(CryptoPrice.crypto_category_id)
        .subquery()
    )

    query = (
        select(CryptoPrice, CryptoCategory)
        .join(CryptoCategory)
        .join(
            subquery,
            (CryptoPrice.crypto_category_id == subquery.c.crypto_category_id)
            & (CryptoPrice.fetched_at == subquery.c.max_fetched),
        )
    )

    result = await db.execute(query)
    rows = result.all()

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No price data yet. Try hitting /prices/refresh first.",
        )

    prices = []
    latest_fetch = None
    for price, category in rows:
        prices.append(
            CryptoPriceWithCategory(
                id=price.id,
                crypto_category_id=price.crypto_category_id,
                price_usd=price.price_usd,
                price_change_24h=price.price_change_24h,
                market_cap_usd=price.market_cap_usd,
                volume_24h_usd=price.volume_24h_usd,
                last_updated_at=price.last_updated_at,
                fetched_at=price.fetched_at,
                category_name=category.name,
                category_symbol=category.symbol,
            )
        )
        if latest_fetch is None or price.fetched_at > latest_fetch:
            latest_fetch = price.fetched_at

    return LatestPricesResponse(prices=prices, fetched_at=latest_fetch)


@router.get("/history/{crypto_category_id}", response_model=PriceHistoryResponse)
async def get_price_history(
    crypto_category_id: UUID,
    days: int = Query(default=7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    # Check the crypto exists
    category = await db.get(CryptoCategory, crypto_category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crypto category {crypto_category_id} not found",
        )

    # Get prices from the last N days
    since = datetime.utcnow() - timedelta(days=days)
    query = (
        select(CryptoPrice)
        .where(CryptoPrice.crypto_category_id == crypto_category_id)
        .where(CryptoPrice.fetched_at >= since)
        .order_by(desc(CryptoPrice.fetched_at))
    )

    result = await db.execute(query)
    prices = result.scalars().all()

    return PriceHistoryResponse(
        crypto_category_id=category.id,
        name=category.name,
        symbol=category.symbol,
        history=prices,
    )


@router.post("/refresh", status_code=status.HTTP_202_ACCEPTED)
async def trigger_price_refresh():
    asyncio.create_task(fetch_and_store_prices())
    return {"message": "Price refresh started", "status": "accepted"}
