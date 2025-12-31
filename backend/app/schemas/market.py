from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional
from decimal import Decimal


class MarketBase(BaseModel):
    platform_id: UUID
    crypto_category_id: Optional[UUID] = None
    platform_market_id: str
    title: str
    description: Optional[str] = None
    question: str
    tags: Optional[dict] = None
    market_type: str
    status: str
    close_time: datetime


class MarketCreate(MarketBase):
    pass


class MarketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    total_volume: Optional[Decimal] = None
    resolved_outcome_id: Optional[UUID] = None


class MarketResponse(MarketBase):
    id: UUID
    created_at: datetime
    resolution_time: Optional[datetime] = None
    last_updated: datetime
    total_volume: Optional[Decimal] = None
    resolved_outcome_id: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


class MarketListResponse(BaseModel):
    markets: list[MarketResponse]
    total: int
