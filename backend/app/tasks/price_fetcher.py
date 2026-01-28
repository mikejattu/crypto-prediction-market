"""
Background task that fetches crypto prices and saves them to the database.
Runs every 12 hours (configurable).
"""

import logging
from sqlalchemy import select

from app.db.database import AsyncSessionLocal
from app.db.models import CryptoCategory, CryptoPrice
from app.services.coingecko import coingecko_client, CoinGeckoError

logger = logging.getLogger(__name__)


async def fetch_and_store_prices() -> dict:
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(CryptoCategory).where(CryptoCategory.coingecko_id.isnot(None))
            )
            categories = result.scalars().all()

            if not categories:
                logger.warning("No crypto categories found with coingecko_id")
                return {"status": "skipped", "reason": "no_categories"}

            id_to_category = {cat.coingecko_id: cat for cat in categories}
            coin_ids = list(id_to_category.keys())

            logger.info(f"Fetching prices for: {coin_ids}")

            price_data = await coingecko_client.get_prices(coin_ids)

            prices_created = 0
            for coin_id, category in id_to_category.items():
                if coin_id not in price_data:
                    logger.warning(f"No price data returned for {coin_id}")
                    continue

                parsed = coingecko_client.parse_price_data(coin_id, price_data)

                crypto_price = CryptoPrice(
                    crypto_category_id=category.id,
                    **parsed,
                )
                db.add(crypto_price)
                prices_created += 1

            await db.commit()

            logger.info(f"Saved {prices_created} price records")
            return {"status": "success", "prices_created": prices_created}

        except CoinGeckoError as e:
            logger.error(f"CoinGecko API error: {e}")
            return {"status": "error", "error": str(e)}
        except Exception as e:
            logger.exception(f"Unexpected error fetching prices: {e}")
            await db.rollback()
            return {"status": "error", "error": str(e)}
