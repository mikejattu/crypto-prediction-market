"""
CoinGecko API client for fetching cryptocurrency prices.

API: https://api.coingecko.com/api/v3/simple/price
Free tier: No API key needed, ~10-30 calls/minute limit
"""

import httpx
from datetime import datetime, timezone
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"


class CoinGeckoError(Exception):

    pass


class CoinGeckoClient:
    """Async client for CoinGecko API"""

    def __init__(self, timeout: float = 30.0):
        self.base_url = COINGECKO_BASE_URL
        self.timeout = timeout

    async def get_prices(self, coin_ids: list[str]) -> dict:
        params = {
            "ids": ",".join(coin_ids),
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_market_cap": "true",
            "include_24hr_vol": "true",
            "include_last_updated_at": "true",
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/simple/price",
                    params=params,
                )
                response.raise_for_status()
                return response.json()

            except httpx.TimeoutException as e:
                logger.error(f"CoinGecko timeout: {e}")
                raise CoinGeckoError(f"Request timeout: {e}")
            except httpx.HTTPStatusError as e:
                logger.error(f"CoinGecko HTTP error: {e.response.status_code}")
                raise CoinGeckoError(f"HTTP error {e.response.status_code}: {e}")
            except httpx.RequestError as e:
                logger.error(f"CoinGecko request error: {e}")
                raise CoinGeckoError(f"Request failed: {e}")

    @staticmethod
    def parse_price_data(coin_id: str, data: dict) -> dict:
        coin_data = data.get(coin_id, {})

        last_updated_ts = coin_data.get("last_updated_at")
        last_updated = (
            datetime.fromtimestamp(last_updated_ts, tz=timezone.utc)
            if last_updated_ts
            else datetime.now(timezone.utc)
        )

        return {
            "price_usd": Decimal(str(coin_data.get("usd", 0))),
            "price_change_24h": (
                Decimal(str(coin_data.get("usd_24h_change", 0)))
                if coin_data.get("usd_24h_change")
                else None
            ),
            "market_cap_usd": (
                Decimal(str(coin_data.get("usd_market_cap", 0)))
                if coin_data.get("usd_market_cap")
                else None
            ),
            "volume_24h_usd": (
                Decimal(str(coin_data.get("usd_24h_vol", 0)))
                if coin_data.get("usd_24h_vol")
                else None
            ),
            "last_updated_at": last_updated,
        }


coingecko_client = CoinGeckoClient()
