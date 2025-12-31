"""
Database seeding script for initial/test data.

Run this to populate the database with platforms and sample data.
Usage: python scripts/seed_data.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to Python path so we can import app modules
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.db.database import AsyncSessionLocal  # noqa: E402
from app.db.models import Platform, CryptoCategory, Market, Contract  # noqa: E402
from datetime import datetime  # noqa: E402
from decimal import Decimal  # noqa: E402


async def seed_platforms():
    """Create initial platforms (Kalshi, Polymarket)."""
    async with AsyncSessionLocal() as db:
        from sqlalchemy import text

        # Check if platforms already exist to avoid duplicates
        existing = await db.execute(text("SELECT COUNT(*) FROM platforms"))
        count = existing.scalar()

        if count > 0:
            print(f"⚠️  Platforms already exist ({count} found). Skipping.")
            return

        # Create platform records
        platforms = [
            Platform(name="Kalshi", api_base_url="https://api.kalshi.com/v1"),
            Platform(name="Polymarket", api_base_url="https://api.polymarket.com/v1"),
        ]

        # Add to database and commit
        db.add_all(platforms)
        await db.commit()

        print("✅ Seeded 2 platforms: Kalshi, Polymarket")


async def seed_crypto_categories():
    """Create initial crypto categories (BTC, ETH, SOL)."""
    async with AsyncSessionLocal() as db:
        from sqlalchemy import text

        # Check if categories already exist
        existing = await db.execute(text("SELECT COUNT(*) FROM crypto_categories"))
        count = existing.scalar()

        if count > 0:
            print(f"⚠️  Crypto categories already exist ({count} found). Skipping.")
            return

        # Create crypto category records
        categories = [
            CryptoCategory(
                name="Bitcoin",
                slug="bitcoin",
                description="Bitcoin and BTC-related markets",
                symbol="BTC",
                coingecko_id="bitcoin",  # For future price data integration
            ),
            CryptoCategory(
                name="Ethereum",
                slug="ethereum",
                description="Ethereum and ETH-related markets",
                symbol="ETH",
                coingecko_id="ethereum",
            ),
            CryptoCategory(
                name="Solana",
                slug="solana",
                description="Solana and SOL-related markets",
                symbol="SOL",
                coingecko_id="solana",
            ),
        ]

        db.add_all(categories)
        await db.commit()

        print("✅ Seeded 3 crypto categories: BTC, ETH, SOL")


async def seed_sample_market():
    """Create a sample binary market with YES/NO contracts for testing."""
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        # Get first platform (should be Kalshi from seed_platforms)
        platform_result = await db.execute(select(Platform).limit(1))
        platform = platform_result.scalar_one_or_none()

        if not platform:
            print("❌ No platforms found. Run seed_platforms first.")
            return

        # Get Bitcoin category
        btc_result = await db.execute(
            select(CryptoCategory).where(CryptoCategory.slug == "bitcoin")
        )
        btc_category = btc_result.scalar_one_or_none()

        # Create a sample binary market
        market = Market(
            platform_id=platform.id,
            crypto_category_id=btc_category.id if btc_category else None,
            platform_market_id="BTC-100K-2025",  # Platform's internal ID
            title="Will Bitcoin reach $100,000 by Dec 31, 2025?",
            description=(
                "This market resolves to YES if Bitcoin (BTC) reaches "
                "$100,000 USD on any major exchange by December 31, 2025, "
                "11:59 PM ET."
            ),
            question="Will Bitcoin reach $100,000 by Dec 31, 2025?",
            tags={"crypto": True, "bitcoin": True, "price": True},  # JSONB field
            market_type="binary",  # Binary = Yes/No market
            status="active",  # Market is currently open for trading
            close_time=datetime(2025, 12, 31, 23, 59, 0),  # When market closes
            total_volume=Decimal("125000.50"),  # Total trading volume in USD
        )

        db.add(market)
        await db.flush()  # Generate market.id without committing yet

        # Create YES contract (currently at 68.5 cents = 68.5% implied probability)
        yes_contract = Contract(
            market_id=market.id,
            platform_contract_id="BTC-100K-2025-YES",
            outcome_label="Yes",
            current_price=Decimal("68.50"),  # Price in cents (0-100)
            current_probability=Decimal("0.6850"),  # Probability (0.0-1.0)
        )

        # Create NO contract (currently at 31.5 cents = 31.5% implied probability)
        no_contract = Contract(
            market_id=market.id,
            platform_contract_id="BTC-100K-2025-NO",
            outcome_label="No",
            current_price=Decimal("31.50"),
            current_probability=Decimal("0.3150"),
        )

        db.add_all([yes_contract, no_contract])
        await db.commit()

        print("✅ Seeded sample market: Bitcoin $100k prediction")
        print(f"   Market ID: {market.id}")
        print(f"   YES contract: {yes_contract.id}")
        print(f"   NO contract: {no_contract.id}")


async def main():
    """Run all seeding functions in order."""
    print("🌱 Starting database seeding...\n")

    # Order matters: platforms must exist before markets can reference them
    await seed_platforms()
    await seed_crypto_categories()
    await seed_sample_market()

    print("\n✅ Database seeding complete!")


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())
