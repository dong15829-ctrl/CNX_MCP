from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "dev"
    api_prefix: str = "/api"
    database_url: str
    upload_dir: str = "./storage/uploads"
    app_cors_origins: str = "http://localhost:3000"

    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.app_cors_origins.split(",") if origin.strip()]


settings = Settings()

