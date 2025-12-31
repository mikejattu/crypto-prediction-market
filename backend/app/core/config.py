#Configuration settings for the application


from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    #Enforces type - crashes immediately if value is missing or of wrong type
    #enironment variables for the application

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "marketpulse"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password_dev_password"
    
    DATABASE_URL: Optional[str] = None
    REDIS_URL: str = "redis://localhost:6379"

    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    #API settings
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "MarketPulse"
    
    model_config = SettingsConfigDict(
        env_file=".env.local",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    @property
    def database_url(self) -> str:
        #Construct the database URL if not provided directly
        if self.DATABASE_URL:
            return self.DATABASE_URL
        
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
settings = Settings()

