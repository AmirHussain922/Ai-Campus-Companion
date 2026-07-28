"""
Configuration settings for AI Campus Companion.

Provides centralized configuration management using Pydantic Settings,
including database connections, authentication, email, and security settings.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings configuration."""

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[1] / ".env"),
        extra="ignore",
    )

    # ============================================
    # Application Settings
    # ============================================
    app_name: str = Field(
        default="AI Campus Companion",
        alias="APP_NAME"
    )
    app_env: str = Field(
        default="development",
        alias="APP_ENV"
    )
    debug: bool = Field(
        default=True,
        alias="DEBUG"
    )

    # ============================================
    # Security Settings
    # ============================================
    secret_key: str = Field(
        default="your-secret-key-change-in-production-min-32-chars",
        alias="SECRET_KEY",
        min_length=32
    )
    algorithm: str = Field(
        default="HS256",
        alias="ALGORITHM"
    )
    access_token_expire_minutes: int = Field(
        default=15,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    refresh_token_expire_days: int = Field(
        default=7,
        alias="REFRESH_TOKEN_EXPIRE_DAYS"
    )

    # ============================================
    # Rate Limiting Settings
    # ============================================
    rate_limit_login_max: int = Field(
        default=5,
        alias="RATE_LIMIT_LOGIN_MAX"
    )
    rate_limit_login_window: int = Field(
        default=900,
        alias="RATE_LIMIT_LOGIN_WINDOW"
    )
    rate_limit_otp_resend_max: int = Field(
        default=3,
        alias="RATE_LIMIT_OTP_RESEND_MAX"
    )
    rate_limit_otp_resend_window: int = Field(
        default=3600,
        alias="RATE_LIMIT_OTP_RESEND_WINDOW"
    )
    rate_limit_general_max: int = Field(
        default=100,
        alias="RATE_LIMIT_GENERAL_MAX"
    )
    rate_limit_general_window: int = Field(
        default=60,
        alias="RATE_LIMIT_GENERAL_WINDOW"
    )

    # ============================================
    # CORS Settings
    # ============================================
    cors_allow_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        alias="CORS_ORIGINS"
    )
    
    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def validate_cors_origins(cls, v):
        if isinstance(v, str):
            # Split comma-separated string
            return [item.strip() for item in v.split(",") if item.strip()]
        return v
    cors_allow_credentials: bool = Field(
        default=True,
        alias="CORS_ALLOW_CREDENTIALS"
    )
    cors_allow_methods: list[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        alias="CORS_ALLOW_METHODS"
    )
    cors_allow_headers: list[str] = Field(
        default=["Content-Type", "Authorization"],
        alias="CORS_ALLOW_HEADERS"
    )

    # ============================================
    # SMTP/Email Settings
    # ============================================
    smtp_host: str = Field(
        default="smtp.gmail.com",
        alias="SMTP_HOST"
    )
    smtp_port: int = Field(
        default=587,
        alias="SMTP_PORT"
    )
    smtp_user: Optional[str] = Field(
        default=None,
        alias="SMTP_USER"
    )
    smtp_password: Optional[str] = Field(
        default=None,
        alias="SMTP_PASSWORD"
    )
    smtp_from_name: str = Field(
        default="AI Campus Companion",
        alias="SMTP_FROM_NAME"
    )
    smtp_from_email: str = Field(
        default="noreply@aicampus.com",
        alias="SMTP_FROM_EMAIL"
    )

    # ============================================
    # Security Configuration
    # ============================================
    bcrypt_rounds: int = Field(
        default=12,
        alias="BCRYPT_ROUNDS"
    )
    max_message_length: int = Field(
        default=10000,
        alias="MAX_MESSAGE_LENGTH"
    )
    account_lockout_minutes: int = Field(
        default=30,
        alias="ACCOUNT_LOCKOUT_MINUTES"
    )
    max_failed_logins: int = Field(
        default=5,
        alias="MAX_FAILED_LOGINS"
    )

    # ============================================
    # OpenRouter API Configuration
    # ============================================
    openrouter_api_key: Optional[str] = Field(
        default=None,
        alias="OPENROUTER_API_KEY"
    )
    openrouter_http_referer: Optional[str] = Field(
        default=None,
        alias="OPENROUTER_HTTP_REFERER"
    )
    openrouter_x_title: Optional[str] = Field(
        default=None,
        alias="OPENROUTER_X_TITLE"
    )
    openrouter_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        alias="OPENROUTER_BASE_URL"
    )
    openrouter_model: str = Field(
        default="openai/gpt-4o-mini",
        alias="OPENROUTER_MODEL"
    )
    openrouter_embedding_model: str = Field(
        default="openai/text-embedding-3-small",
        alias="OPENROUTER_EMBEDDING_MODEL"
    )

    # ============================================
    # Database Configuration
    # ============================================
    mongodb_uri: str = Field(
        default="mongodb://localhost:27017",
        alias="MONGODB_URI"
    )
    mongodb_db: str = Field(
        default="ai_companions",
        alias="MONGODB_DB"
    )

    # ============================================
    # Companion Classification
    # ============================================
    trainable_companions: list[str] = Field(
        default=["philosopher", "rival"],
        alias="TRAINABLE_COMPANIONS",
    )
    demo_companions: list[str] = Field(
        default=["study_buddy", "party_friend", "freshman"],
        alias="DEMO_COMPANIONS",
    )

    # Per-companion OpenRouter model routing.
    # Keys are backend personality IDs; values are OpenRouter model slugs.
    companion_models: dict[str, str] = Field(
        default={
            "philosopher": "openai/gpt-4o-mini",
            "rival": "openai/gpt-4o-mini",
            "study_buddy": "openai/gpt-4o-mini",
            "party_friend": "openai/gpt-4o-mini",
            "freshman": "openai/gpt-4o-mini",
        },
        alias="COMPANION_MODELS",
    )

    # RL training configuration
    rl_training_interval_minutes: int = Field(
        default=60,
        alias="RL_TRAINING_INTERVAL_MINUTES",
    )
    rl_min_transitions_for_training: int = Field(
        default=50,
        alias="RL_MIN_TRANSITIONS_FOR_TRAINING",
    )

    def is_trainable(self, companion_id: str) -> bool:
        """Return True if the companion uses the full RL pipeline."""
        return companion_id in self.trainable_companions

    def get_model_for_companion(self, companion_id: str) -> str:
        """Return the OpenRouter model slug for a given companion."""
        return self.companion_models.get(companion_id, self.openrouter_model)

    # ============================================
    # Data Management
    # ============================================
    reset_local_data_on_startup: bool = Field(
        default=False,
        alias="RESET_LOCAL_DATA_ON_STARTUP"
    )

    # ============================================
    # Validators
    # ============================================
    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key length."""
        if len(v) < 32:
            raise ValueError('SECRET_KEY must be at least 32 characters long for security')
        return v

    @field_validator('access_token_expire_minutes')
    @classmethod
    def validate_token_expiry(cls, v: int) -> int:
        """Validate token expiration."""
        if v < 5:
            raise ValueError('ACCESS_TOKEN_EXPIRE_MINUTES should be at least 5 minutes')
        if v > 60:
            raise ValueError('ACCESS_TOKEN_EXPIRE_MINUTES should not exceed 60 minutes for security')
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
