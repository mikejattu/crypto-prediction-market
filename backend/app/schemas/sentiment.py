# Pydantic models for sentiment API responses - defines the shape of data we send back to clients.

from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional
from enum import Enum


class SentimentSourceEnum(str, Enum):
    REDDIT = "reddit"
    CRYPTOPANIC = "cryptopanic"
    NEWSAPI = "newsapi"
    COMBINED = "combined"


class SentimentScoreBase(BaseModel):
    positive_score: Decimal
    negative_score: Decimal
    neutral_score: Decimal
    composite_score: Decimal
    sample_count: int


class SentimentScoreResponse(SentimentScoreBase):
    id: UUID
    crypto_category_id: UUID
    source: str
    window_start: datetime
    window_end: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CurrentSentimentResponse(BaseModel):
    crypto_category_id: UUID
    name: str
    symbol: str
    reddit: Optional[SentimentScoreBase] = None
    cryptopanic: Optional[SentimentScoreBase] = None
    newsapi: Optional[SentimentScoreBase] = None
    combined_composite: Optional[Decimal] = None
    combined_sample_count: int = 0
    last_updated: Optional[datetime] = None


class SentimentListResponse(BaseModel):
    sentiments: list[CurrentSentimentResponse]
    fetched_at: datetime


class SentimentHistoryResponse(BaseModel):
    crypto_category_id: UUID
    name: str
    symbol: str
    source: Optional[str] = None
    history: list[SentimentScoreResponse]
