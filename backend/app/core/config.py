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
