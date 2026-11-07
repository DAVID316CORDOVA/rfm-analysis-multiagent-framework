"""
Configuration Management for RFM-LDE Multiagent

Loads environment variables and provides centralized config access.
Supports multiple environments: development, staging, production.
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from .env file or environment variables.

    Supports:
        - AWS credentials and region
        - Anthropic API configuration
        - Athena database settings
        - Feature flags and limits
        - Logging configuration
    """

    # Environment
    environment: str = os.getenv("ENVIRONMENT", "production")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    # AWS Configuration
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    aws_profile: Optional[str] = os.getenv("AWS_PROFILE", None)

    # Anthropic API
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    anthropic_model: str = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5")

    # Athena Configuration
    athena_database: str = os.getenv("ATHENA_DATABASE", "dwh_raw_pe")
    athena_output_location: str = os.getenv(
        "ATHENA_OUTPUT_LOCATION",
        "s3://dlk-olimpo/athena-results/"
    )

    # Lambda Configuration
    lambda_function_url: Optional[str] = os.getenv("LAMBDA_FUNCTION_URL", None)
    lambda_api_key: Optional[str] = os.getenv("LAMBDA_API_KEY", None)

    # Feature Flags
    enable_cache: bool = os.getenv("ENABLE_CACHE", "true").lower() == "true"
    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "300"))
    max_steps: int = int(os.getenv("MAX_STEPS", "8"))
    max_tokens: int = int(os.getenv("MAX_TOKENS", "4096"))

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = os.getenv("LOG_FORMAT", "json")

    class Config:
        """Pydantic config for settings"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == "production"

    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == "development"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses LRU cache to avoid reloading .env file on every access.
    In tests, clear cache with: get_settings.cache_clear()

    Returns:
        Settings instance with all configuration values
    """
    return Settings()
