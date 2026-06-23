from functools import lru_cache

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = "Telegram to MT5 SaaS"
    environment: str = "development"
    database_url: str = "sqlite:///./dev.db"
    jwt_secret: str = "change-me-before-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    encryption_key: str | None = None
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    mt5_bridge_provider: str = "metaapi"
    mt5_bridge_base_url: AnyHttpUrl | str = "https://mt-client-api-v1.new-york.agiliumtrade.ai"
    mt5_bridge_api_key: str | None = None
    ai_parser_provider: str = "disabled"
    ai_parser_api_key: str | None = None
    bootstrap_admin_email: str = "admin@example.com"
    bootstrap_admin_password: str = Field(default="ChangeMe123!", min_length=8)

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
