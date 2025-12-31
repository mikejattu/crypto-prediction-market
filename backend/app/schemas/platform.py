from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional


class PlatformBase(BaseModel):
    name: str
    api_base_url: str


class PlatformCreate(PlatformBase):
    pass


class PlatformUpdate(BaseModel):
    name: Optional[str] = None
    api_base_url: Optional[str] = None
    is_active: Optional[bool] = None


class PlatformResponse(PlatformBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class PlatformListResponse(BaseModel):
    platforms: list[PlatformResponse]
    total: int
