# API endpoints for getting sentiment data - current scores, history, and a manual refresh trigger.

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_
from uuid import UUID
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import asyncio

from app.db.database import get_db
from app.db.models import SentimentScore, CryptoCategory
from app.schemas.sentiment import (
    SentimentScoreResponse,
    CurrentSentimentResponse,
    SentimentListResponse,
    SentimentHistoryResponse,
    SentimentScoreBase,
)
from app.tasks.sentiment_fetcher import fetch_and_store_sentiment

router = APIRouter(prefix="/sentiment", tags=["sentiment"])


@router.get("/current", response_model=SentimentListResponse)
async def get_current_sentiment(db: AsyncSession = Depends(get_db)):
    cat_result = await db.execute(
        select(CryptoCategory).where(CryptoCategory.symbol.isnot(None))
    )
    categories = cat_result.scalars().all()

    if not categories:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No crypto categories configured",
        )

    sentiments = []

    for category in categories:
        subquery = (
            select(
                SentimentScore.source,
                func.max(SentimentScore.window_start).label("max_window"),
            )
            .where(SentimentScore.crypto_category_id == category.id)
            .group_by(SentimentScore.source)
            .subquery()
        )

        query = select(SentimentScore).join(
            subquery,
            and_(
                SentimentScore.source == subquery.c.source,
                SentimentScore.window_start == subquery.c.max_window,
                SentimentScore.crypto_category_id == category.id,
            ),
        )

        result = await db.execute(query)
        scores = result.scalars().all()

        response = CurrentSentimentResponse(
            crypto_category_id=category.id,
            name=category.name,
            symbol=category.symbol,
        )

        total_composite = Decimal("0")
        total_weight = 0
        latest_update = None

        for score in scores:
            score_base = SentimentScoreBase(
                positive_score=score.positive_score,
                negative_score=score.negative_score,
                neutral_score=score.neutral_score,
                composite_score=score.composite_score,
                sample_count=score.sample_count,
            )

            if score.source == "reddit":
                response.reddit = score_base
            elif score.source == "cryptopanic":
                response.cryptopanic = score_base
            elif score.source == "newsapi":
                response.newsapi = score_base

            total_composite += score.composite_score * score.sample_count
            total_weight += score.sample_count

            if latest_update is None or score.window_end > latest_update:
                latest_update = score.window_end

        if total_weight > 0:
            response.combined_composite = total_composite / total_weight
            response.combined_sample_count = total_weight

        response.last_updated = latest_update
        sentiments.append(response)

    return SentimentListResponse(
        sentiments=sentiments, fetched_at=datetime.now(timezone.utc)
    )


@router.get("/current/{crypto_category_id}", response_model=CurrentSentimentResponse)
async def get_current_sentiment_for_crypto(
    crypto_category_id: UUID, db: AsyncSession = Depends(get_db)
):
    category = await db.get(CryptoCategory, crypto_category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crypto category {crypto_category_id} not found",
        )

    subquery = (
        select(
            SentimentScore.source,
            func.max(SentimentScore.window_start).label("max_window"),
        )
        .where(SentimentScore.crypto_category_id == crypto_category_id)
        .group_by(SentimentScore.source)
        .subquery()
    )

    query = select(SentimentScore).join(
        subquery,
        and_(
            SentimentScore.source == subquery.c.source,
            SentimentScore.window_start == subquery.c.max_window,
            SentimentScore.crypto_category_id == crypto_category_id,
        ),
    )

    result = await db.execute(query)
    scores = result.scalars().all()

    response = CurrentSentimentResponse(
        crypto_category_id=category.id,
        name=category.name,
        symbol=category.symbol,
    )

    total_composite = Decimal("0")
    total_weight = 0
    latest_update = None

    for score in scores:
        score_base = SentimentScoreBase(
            positive_score=score.positive_score,
            negative_score=score.negative_score,
            neutral_score=score.neutral_score,
            composite_score=score.composite_score,
            sample_count=score.sample_count,
        )

        if score.source == "reddit":
            response.reddit = score_base
        elif score.source == "cryptopanic":
            response.cryptopanic = score_base
        elif score.source == "newsapi":
            response.newsapi = score_base

        total_composite += score.composite_score * score.sample_count
        total_weight += score.sample_count

        if latest_update is None or score.window_end > latest_update:
            latest_update = score.window_end

    if total_weight > 0:
        response.combined_composite = total_composite / total_weight
        response.combined_sample_count = total_weight

    response.last_updated = latest_update

    return response


@router.get("/history/{crypto_category_id}", response_model=SentimentHistoryResponse)
async def get_sentiment_history(
    crypto_category_id: UUID,
    source: str = Query(default=None),
    hours: int = Query(default=24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
):
    category = await db.get(CryptoCategory, crypto_category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Crypto category {crypto_category_id} not found",
        )

    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    query = (
        select(SentimentScore)
        .where(SentimentScore.crypto_category_id == crypto_category_id)
        .where(SentimentScore.window_start >= since)
    )

    if source:
        query = query.where(SentimentScore.source == source)

    query = query.order_by(desc(SentimentScore.window_start))

    result = await db.execute(query)
    scores = result.scalars().all()

    return SentimentHistoryResponse(
        crypto_category_id=category.id,
        name=category.name,
        symbol=category.symbol,
        source=source,
        history=scores,
    )


@router.post("/refresh", status_code=status.HTTP_202_ACCEPTED)
async def trigger_sentiment_refresh():
    asyncio.create_task(fetch_and_store_sentiment())
    return {"message": "Sentiment refresh started", "status": "accepted"}
