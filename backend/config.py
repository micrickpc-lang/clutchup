from functools import lru_cache

from pydantic import Field, HttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    redis_url: str = "redis://redis:6379/0"
    bot_token: str
    faceit_api_key: str = ""
    faceit_client_id: str = ""
    faceit_client_secret: str = ""
    faceit_redirect_uri: str = ""
    faceit_proxy_url: str = ""
    faceit_proxy_secret: str = ""
    frontend_url: str
    telegram_bot_username: str
    telegram_mini_app_short_name: str = ""
    auth_max_age_seconds: int = Field(default=3600, ge=60, le=86400)
    oauth_state_ttl_seconds: int = Field(default=600, ge=120, le=1800)
    presence_ttl_seconds: int = Field(default=105, ge=60, le=300)
    faceit_cache_ttl_seconds: int = Field(default=300, ge=30, le=3600)
    party_ttl_hours: int = Field(default=6, ge=1, le=48)
    environment: str = "production"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    @field_validator("frontend_url")
    @classmethod
    def valid_http_url(cls, value: str) -> str:
        parsed = HttpUrl(value)
        return str(parsed).rstrip("/")

    @model_validator(mode="after")
    def validate_oauth(self) -> "Settings":
        configured = any((self.faceit_client_id, self.faceit_client_secret, self.faceit_redirect_uri))
        if (
            self.environment == "production"
            and configured
            and not all((self.faceit_client_id, self.faceit_client_secret, self.faceit_redirect_uri))
        ):
            raise ValueError(
                "FACEIT OAuth configuration must provide client id, client secret and redirect URI together"
            )
        if self.faceit_redirect_uri:
            self.faceit_redirect_uri = str(HttpUrl(self.faceit_redirect_uri)).rstrip("/")
        expected = f"{self.frontend_url}/api/faceit/oauth/callback"
        if self.environment == "production" and configured and self.faceit_redirect_uri != expected:
            raise ValueError(f"FACEIT OAuth configuration invalid: FACEIT_REDIRECT_URI must equal {expected}")
        if self.faceit_proxy_url and not self.faceit_proxy_secret:
            raise ValueError(
                "FACEIT OAuth configuration invalid: FACEIT_PROXY_SECRET is required when proxy is enabled"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
