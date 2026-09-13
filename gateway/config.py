from functools import lru_cache

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bark_base_url: AnyHttpUrl = "http://host.docker.internal:8080"
    bark_device_key: str = Field(min_length=1)
    bark_timeout_seconds: float = Field(default=10, gt=0, le=60)

    tailscale_token: str = ""
    paseo_token: str = ""
    generic_token: str = ""
    tailscale_webhook_secret: str = ""
    tailscale_signature_tolerance_seconds: int = Field(default=300, ge=1, le=3600)

    log_level: str = "INFO"
    max_body_bytes: int = Field(default=1_048_576, ge=1024, le=10_485_760)

    def token_for(self, service: str) -> str:
        return {
            "tailscale": self.tailscale_token,
            "paseo": self.paseo_token,
            "generic": self.generic_token,
        }.get(service, "")


@lru_cache
def get_settings() -> Settings:
    return Settings()

