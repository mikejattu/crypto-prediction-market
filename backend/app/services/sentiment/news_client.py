# Fetches crypto news from CryptoPanic (crypto-specific) and NewsAPI (general news) - both are free APIs with rate limits.

import httpx
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from dataclasses import dataclass

from app.core.config import settings
from app.services.sentiment.exceptions import NewsClientError, RateLimitError

logger = logging.getLogger(__name__)

CRYPTOPANIC_BASE_URL = "https://cryptopanic.com/api/v1"
NEWSAPI_BASE_URL = "https://newsapi.org/v2"


@dataclass
class NewsArticle:
    title: str
    description: Optional[str]
    source: str
    published_at: datetime
    url: str

    @property
    def full_text(self) -> str:
        if self.description:
            return f"{self.title}. {self.description}"
        return self.title


class NewsClient:
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self._newsapi_calls_today = 0
        self._newsapi_reset_date = datetime.now(timezone.utc).date()

    def _check_newsapi_limit(self) -> bool:
        today = datetime.now(timezone.utc).date()
        if today != self._newsapi_reset_date:
            self._newsapi_calls_today = 0
            self._newsapi_reset_date = today

        return self._newsapi_calls_today < settings.NEWSAPI_DAILY_LIMIT

    async def fetch_cryptopanic(
        self, currencies: list[str], filter_type: str = "rising"
    ) -> list[NewsArticle]:
        if not settings.CRYPTOPANIC_API_KEY:
            logger.warning("CryptoPanic API key not configured")
            return []

        articles = []

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for currency in currencies:
                try:
                    params = {
                        "auth_token": settings.CRYPTOPANIC_API_KEY,
                        "currencies": currency,
                        "filter": filter_type,
                        "public": "true",
                    }

                    response = await client.get(
                        f"{CRYPTOPANIC_BASE_URL}/posts/", params=params
                    )
                    response.raise_for_status()
                    data = response.json()

                    for item in data.get("results", []):
                        try:
                            published = datetime.fromisoformat(
                                item["published_at"].replace("Z", "+00:00")
                            )
                            article = NewsArticle(
                                title=item.get("title", ""),
                                description=None,
                                source="cryptopanic",
                                published_at=published,
                                url=item.get("url", ""),
                            )
                            articles.append(article)
                        except (KeyError, ValueError) as e:
                            logger.warning(f"Error parsing CryptoPanic item: {e}")

                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429:
                        raise RateLimitError("CryptoPanic rate limit exceeded")
                    logger.error(f"CryptoPanic HTTP error for {currency}: {e}")
                except httpx.RequestError as e:
                    logger.error(f"CryptoPanic request error for {currency}: {e}")

        logger.info(f"Fetched {len(articles)} articles from CryptoPanic")
        return articles

    async def fetch_newsapi(
        self, keywords: list[str], from_date: Optional[datetime] = None
    ) -> list[NewsArticle]:
        if not settings.NEWSAPI_KEY:
            logger.warning("NewsAPI key not configured")
            return []

        if not self._check_newsapi_limit():
            logger.warning("NewsAPI daily limit reached")
            raise RateLimitError("NewsAPI daily limit exceeded")

        if from_date is None:
            from_date = datetime.now(timezone.utc) - timedelta(hours=24)

        articles = []

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            query = " OR ".join(keywords)

            try:
                params = {
                    "q": query,
                    "from": from_date.isoformat(),
                    "language": "en",
                    "sortBy": "publishedAt",
                    "pageSize": 100,
                    "apiKey": settings.NEWSAPI_KEY,
                }

                response = await client.get(
                    f"{NEWSAPI_BASE_URL}/everything", params=params
                )
                self._newsapi_calls_today += 1

                response.raise_for_status()
                data = response.json()

                for item in data.get("articles", []):
                    try:
                        published = datetime.fromisoformat(
                            item["publishedAt"].replace("Z", "+00:00")
                        )
                        article = NewsArticle(
                            title=item.get("title", ""),
                            description=item.get("description"),
                            source="newsapi",
                            published_at=published,
                            url=item.get("url", ""),
                        )
                        articles.append(article)
                    except (KeyError, ValueError) as e:
                        logger.warning(f"Error parsing NewsAPI item: {e}")

            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    raise RateLimitError("NewsAPI rate limit exceeded")
                logger.error(f"NewsAPI HTTP error: {e}")
                raise NewsClientError(f"NewsAPI error: {e}")
            except httpx.RequestError as e:
                logger.error(f"NewsAPI request error: {e}")
                raise NewsClientError(f"NewsAPI request failed: {e}")

        logger.info(f"Fetched {len(articles)} articles from NewsAPI")
        return articles


news_client = NewsClient()
