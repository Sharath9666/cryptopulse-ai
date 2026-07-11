"""
Configuration module for the CryptoPulse AI application.
Uses pydantic-settings to manage environment variables.
"""

from typing import List, Union
from urllib.parse import quote_plus
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables and/or .env file.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # App settings
    APP_NAME: str = "CryptoPulse AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"

    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Backtest settings
    BACKTEST_SPEED_MODE: bool = True

    # Performance Evaluation settings
    PERFORMANCE_EVALUATION_PERIOD_SECONDS: int = 10

    # CORS settings
    ALLOWED_HOSTS: Union[str, List[str]] = ["*"]

    # Database settings
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "cryptopulse"
    POSTGRES_PORT: int = 5432
    
    # Optional full database URL (allows overriding default construction)
    DATABASE_URL: Union[str, None] = None

    # Connection pool settings
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """
        Dynamically constructs or formats the asynchronous database connection URL.
        Converts standard postgres:// or postgresql:// schemes to postgresql+asyncpg:// if needed.
        Special characters in the password (e.g. @) are percent-encoded to prevent URL parsing errors.
        """
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if url.startswith("postgresql://"):
                url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql+asyncpg://", 1)
            return url
        encoded_password = quote_plus(self.POSTGRES_PASSWORD)
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{encoded_password}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Union[str, None] = None
    REDIS_DATABASE: int = 0
    
    # Optional full Redis connection string
    REDIS_URL: Union[str, None] = None

    @property
    def ASYNC_REDIS_URL(self) -> str:
        """
        Constructs the Redis connection URL.
        """
        if self.REDIS_URL:
            return self.REDIS_URL
        
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DATABASE}"

    # Binance Market Data settings
    BINANCE_WS_URL: str = "wss://stream.binance.com:9443/stream"
    MARKET_SYMBOLS: Union[str, List[str]] = ["BTCUSDT", "ETHUSDT", "DOGEUSDT", "SOLUSDT", "XRPUSDT"]

    @field_validator("MARKET_SYMBOLS", mode="before")
    @classmethod
    def assemble_market_symbols(cls, v: Union[str, List[str]]) -> List[str]:
        """
        Parses comma-separated symbols from environment variables and converts them to uppercase.
        """
        if isinstance(v, str):
            return [item.strip().upper() for item in v.split(",") if item.strip()]
        return [item.upper() for item in v]

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """
        Parses a comma-separated string of origins from environment variables into a list.
        """
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return v


# Global settings instance
settings = Settings()
