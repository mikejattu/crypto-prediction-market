from sqlalchemy import (
    Column,
    String,
    Boolean,
    TIMESTAMP,
    Text,
    ForeignKey,
    DECIMAL,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.db.database import Base


class Platform(Base):
    __tablename__ = "platforms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), unique=True, nullable=False, index=True)
    api_base_url = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    markets = relationship(
        "Market", back_populates="platform", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Platform(name='{self.name}')>"


class CryptoCategory(Base):
    __tablename__ = "crypto_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    symbol = Column(String(20))
    coingecko_id = Column(String(100))
    created_at = Column(TIMESTAMP, server_default=func.now())

    markets = relationship("Market", back_populates="crypto_category")

    def __repr__(self):
        return f"<CryptoCategory(name='{self.name}', symbol='{self.symbol}')>"


class Market(Base):
    __tablename__ = "markets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    platform_id = Column(
        UUID(as_uuid=True), ForeignKey("platforms.id"), nullable=False, index=True
    )
    crypto_category_id = Column(
        UUID(as_uuid=True), ForeignKey("crypto_categories.id"), index=True
    )
    platform_market_id = Column(String(255), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    question = Column(Text, nullable=False)
    tags = Column(JSONB)
    market_type = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, index=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    close_time = Column(TIMESTAMP, nullable=False, index=True)
    resolution_time = Column(TIMESTAMP)
    last_updated = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    total_volume = Column(DECIMAL(20, 2))
    resolved_outcome_id = Column(
        UUID(as_uuid=True)
    )  # Removed FK to break circular dependency

    platform = relationship("Platform", back_populates="markets")
    crypto_category = relationship("CryptoCategory", back_populates="markets")
    contracts = relationship(
        "Contract",
        back_populates="market",
        cascade="all, delete-orphan",
        foreign_keys="Contract.market_id",
    )

    def __repr__(self):
        return f"<Market(title='{self.title[:50]}...', status='{self.status}')>"


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    market_id = Column(
        UUID(as_uuid=True), ForeignKey("markets.id"), nullable=False, index=True
    )
    platform_contract_id = Column(String(255), nullable=False)
    outcome_label = Column(String(255), nullable=False)
    is_winner = Column(Boolean)
    current_price = Column(DECIMAL(10, 4), nullable=False)
    current_probability = Column(DECIMAL(5, 4), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    last_trade_time = Column(TIMESTAMP)

    market = relationship(
        "Market", back_populates="contracts", foreign_keys=[market_id]
    )

    def __repr__(self):
        return f"<Contract(outcome='{self.outcome_label}', price={self.current_price})>"
