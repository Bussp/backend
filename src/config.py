"""
Application configuration using pydantic-settings.

This module centralizes all configuration settings for the application.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Create a .env file in the project root to override defaults.
    """

    # Application settings
    app_name: str = Field(
        default="BusSP - Gamified Public Transport Tracker",
        validation_alias="APP_NAME",
    )
    debug: bool = Field(default=False, validation_alias="DEBUG")

    # Database settings
    database_url: str = Field(
        default="sqlite+aiosqlite:///./bussp.db",
        validation_alias="DATABASE_URL",
    )

    # SPTrans API settings
    sptrans_api_token: str = Field(
        default="", validation_alias="SPTRANS_API_TOKEN"
    )
    sptrans_base_url: str = Field(
        default="http://api.olhovivo.sptrans.com.br/v2.1",
        validation_alias="SPTRANS_BASE_URL",
    )

    # Server settings
    host: str = Field(default="0.0.0.0", validation_alias="HOST")
    port: int = Field(default=8000, validation_alias="PORT")

    # JWT settings (mantidos com defaults; coloque no .env se quiser)
    secret_key: str = Field(
        default="your-secret-key-here-change-in-production",
        validation_alias="SECRET_KEY",
    )
    algorithm: str = Field(default="HS256", validation_alias="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30, validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # aceita APP_NAME/app_name/etc.
        extra="ignore",        # ignora envs desconhecidas
    )


# Global settings instance
settings = Settings()
