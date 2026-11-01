from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "DEBUG"
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "127.0.0.1"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str
    JWT_SECRET_KEY: SecretStr | None = Field(default=None, min_length=32)
    JWT_ISSUER: str = "mec-system"
    JWT_AUDIENCE: str = "mec-system-api"
    JWT_ACCESS_TOKEN_MINUTES: int = Field(default=15, ge=1, le=60)
    JWT_REFRESH_TOKEN_DAYS: int = Field(default=7, ge=1, le=30)


    @staticmethod
    def viacep_url(cep: str) -> str:
        return f"https://viacep.com.br/ws/{cep}/json/"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
