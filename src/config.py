"""
Application configuration using pydantic-settings.

This module centralizes all configuration settings for the application.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Create a .env file in the project root to override defaults.
    """

    # Application settings
    app_name: str = "BusSP - Gamified Public Transport Tracker"
    debug: bool = False

    # Database settings
    database_url: str = "sqlite+aiosqlite:///./bussp.db"

    # SPTrans API settings
    sptrans_api_token: str = ""
    sptrans_base_url: str = "http://api.olhovivo.sptrans.com.br/v2.1"

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# Global settings instance
settings = Settings()
