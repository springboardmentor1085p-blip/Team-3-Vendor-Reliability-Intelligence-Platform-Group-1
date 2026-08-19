"""
Application configuration module.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration.
    """

    # ---------------------------------------------------------
    # General
    # ---------------------------------------------------------

    APP_NAME: str = "Vendor Reliability Intelligence Platform"

    APP_DESCRIPTION: str = (
        "Enterprise Vendor Reliability Intelligence Platform API"
    )

    APP_VERSION: str = "0.1.0"

    API_V1_STR: str = "/api/v1"

    DEBUG: bool = False

    ENVIRONMENT: str = "development"

    # ---------------------------------------------------------
    # Database
    # ---------------------------------------------------------

    DATABASE_URL: str

    # ---------------------------------------------------------
    # JWT
    # ---------------------------------------------------------

    SECRET_KEY: str

    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    TOKEN_TYPE: str = "Bearer"

    # ---------------------------------------------------------
    # CORS & Frontend
    # ---------------------------------------------------------

    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:4200",
        "http://localhost:54250",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:4200",
        "http://127.0.0.1:54250",
        "http://0.0.0.0:4200",
        "http://0.0.0.0:54250",
    ]

    FRONTEND_URL: str = "http://localhost:4200"

    # ---------------------------------------------------------
    # SMTP / Email Service
    # ---------------------------------------------------------

    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@vendorplatform.com"
    RESET_TOKEN_EXPIRE_HOURS: int = 1


    # ---------------------------------------------------------
    # Pydantic
    # ---------------------------------------------------------

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """
    Return cached application settings.
    """
    return Settings()


settings = get_settings()