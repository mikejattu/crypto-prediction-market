"""add crypto_prices table

Revision ID: 0002_add_crypto_prices
Revises: 1825a2bfcb15
Create Date: 2025-01-14

"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0002_add_crypto_prices"
down_revision: str = "1825a2bfcb15"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "crypto_prices",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("crypto_category_id", sa.UUID(), nullable=False),
        sa.Column("price_usd", sa.DECIMAL(precision=20, scale=8), nullable=False),
        sa.Column("price_change_24h", sa.DECIMAL(precision=10, scale=4), nullable=True),
        sa.Column("market_cap_usd", sa.DECIMAL(precision=30, scale=2), nullable=True),
        sa.Column("volume_24h_usd", sa.DECIMAL(precision=30, scale=2), nullable=True),
        sa.Column("last_updated_at", sa.TIMESTAMP(), nullable=False),
        sa.Column(
            "fetched_at",
            sa.TIMESTAMP(),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["crypto_category_id"],
            ["crypto_categories.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_crypto_prices_crypto_category_id",
        "crypto_prices",
        ["crypto_category_id"],
        unique=False,
    )
    op.create_index(
        "ix_crypto_prices_fetched_at",
        "crypto_prices",
        ["fetched_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_crypto_prices_fetched_at", table_name="crypto_prices")
    op.drop_index("ix_crypto_prices_crypto_category_id", table_name="crypto_prices")
    op.drop_table("crypto_prices")
