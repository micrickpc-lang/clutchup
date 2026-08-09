from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://teamfinder:change_me@db:5432/teamfinder"
    redis_url: str = "redis://redis:6379/0"
    bot_token: str
    faceit_api_key: str
    faceit_client_id: str = ""
    faceit_client_secret: str = ""
    faceit_redirect_uri: str = "https://clutchup.tech/api/faceit/oauth/callback"
    faceit_proxy_url: str = ""
    faceit_proxy_secret: str = ""
    frontend_url: str = "http://localhost"
    auth_max_age_seconds: int = Field(default=86400, ge=60)
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
