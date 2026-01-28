from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "marketpulse"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"

    DATABASE_URL: Optional[str] = None
    REDIS_URL: str = "redis://localhost:6379"

    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "MarketPulse"

    # Price fetching settings
    PRICE_FETCH_INTERVAL_HOURS: int = 12
    PRICE_FETCH_ENABLED: bool = True

    # Sentiment analysis settings
    SENTIMENT_FETCH_ENABLED: bool = True
    SENTIMENT_FETCH_INTERVAL_MINUTES: int = 60

    # Reddit API (free) - get from reddit.com/prefs/apps
    REDDIT_CLIENT_ID: Optional[str] = None
    REDDIT_CLIENT_SECRET: Optional[str] = None
    REDDIT_USER_AGENT: str = "MarketPulse Sentiment Bot 1.0"
    REDDIT_SUBREDDITS: list[str] = [
        "cryptocurrency",
        "bitcoin",
        "ethereum",
        "CryptoMarkets",
    ]

    # CryptoPanic API (free tier) - get from cryptopanic.com/developers/api
    CRYPTOPANIC_API_KEY: Optional[str] = None

    # NewsAPI (free, 100 req/day) - get from newsapi.org
    NEWSAPI_KEY: Optional[str] = None
    NEWSAPI_DAILY_LIMIT: int = 100

    # FinBERT model settings
    FINBERT_MODEL_NAME: str = "ProsusAI/finbert"
    FINBERT_MAX_LENGTH: int = 512
    FINBERT_BATCH_SIZE: int = 16

    model_config = SettingsConfigDict(
        env_file=".env.local", env_file_encoding="utf-8", case_sensitive=True
    )

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL

        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
