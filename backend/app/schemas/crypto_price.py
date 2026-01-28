from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional


class CryptoPriceBase(BaseModel):
    price_usd: Decimal
    price_change_24h: Optional[Decimal] = None
    market_cap_usd: Optional[Decimal] = None
    volume_24h_usd: Optional[Decimal] = None


class CryptoPriceResponse(CryptoPriceBase):
    id: UUID
    crypto_category_id: UUID
    last_updated_at: datetime
    fetched_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CryptoPriceWithCategory(CryptoPriceResponse):
    category_name: str
    category_symbol: str


class LatestPricesResponse(BaseModel):

    prices: list[CryptoPriceWithCategory]
    fetched_at: datetime


class PriceHistoryResponse(BaseModel):

    crypto_category_id: UUID
    name: str
    symbol: str
    history: list[CryptoPriceResponse]
