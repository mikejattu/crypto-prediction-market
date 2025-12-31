from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional
from decimal import Decimal


class ContractBase(BaseModel):
    market_id: UUID
    platform_contract_id: str
    outcome_label: str
    current_price: Decimal
    current_probability: Decimal


class ContractCreate(ContractBase):
    pass


class ContractUpdate(BaseModel):
    current_price: Optional[Decimal] = None
    current_probability: Optional[Decimal] = None
    is_winner: Optional[bool] = None
    last_trade_time: Optional[datetime] = None


class ContractResponse(ContractBase):
    id: UUID
    is_winner: Optional[bool] = None
    created_at: datetime
    updated_at: datetime
    last_trade_time: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ContractListResponse(BaseModel):
    contracts: list[ContractResponse]
    total: int
