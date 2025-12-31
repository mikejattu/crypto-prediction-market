from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional


class CryptoCategoryBase(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    symbol: Optional[str] = None
    coingecko_id: Optional[str] = None


class CryptoCategoryCreate(CryptoCategoryBase):
    pass


class CryptoCategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    symbol: Optional[str] = None
    coingecko_id: Optional[str] = None


class CryptoCategoryResponse(CryptoCategoryBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CryptoCategoryListResponse(BaseModel):
    categories: list[CryptoCategoryResponse]
    total: int
