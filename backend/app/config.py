"""
Configuration settings for AI Campus Companion.

Provides centralized configuration management using Pydantic Settings,
including database connections, authentication, email, and security settings.
"""

from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator, model_validator
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
        ...,
        alias="SECRET_KEY",
        min_length=32
    )

    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate secret key is not using a default/placeholder value."""
        if len(v) < 32:
            raise ValueError('SECRET_KEY must be at least 32 characters long for security')

        # Check for known default/placeholder values
        known_defaults = [
            'your-secret-key-change-in-production-min-32-chars',
            'change-me',
            'your-super-secure-random-secret-key-min-32-characters-long-change-this',
            'your-secret-key-change-in-production',
            'test-secret-key-please-change-in-production',
            'development-secret-key-change-this',
        ]

        v_lower = v.lower()
        for default in known_defaults:
            if default in v_lower:
                raise ValueError('SECRET_KEY cannot use default/placeholder value. Please generate a secure key using: python -c "import secrets; print(secrets.token_urlsafe(32))"')

        return v

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
    otp_pepper: str = Field(
        default="rrdVtjVqFT3TImlRfEYoC1l93QhxqDpGL7cPxIowuoWs5b_z_tU0w2rCIDxwW8hs",
        alias="OTP_PEPPER",
        min_length=32,
        description="Secret pepper for OTP hashing (minimum 32 characters)"
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
        default=10,
        alias="RATE_LIMIT_LOGIN_MAX"
    )
    rate_limit_login_window: int = Field(
        default=120,
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
        default_factory=lambda: ["http://localhost:3000"],
        init=False
    )
    cors_origins: str = Field(
        default="http://localhost:*,http://localhost:3000,http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:5176,http://localhost:5177,http://localhost:5178,http://localhost:5179,http://localhost:5180,http://localhost:5181",
        alias="CORS_ORIGINS"
    )

    @model_validator(mode="before")
    @classmethod
    def validate_cors_origins(cls, values):
        """Validate and parse CORS origins from environment."""
        cors_origins = values.get("CORS_ORIGINS", "")

        if cors_origins:
            try:
                import json
                origins = json.loads(cors_origins)
                values["cors_allow_origins"] = origins
            except json.JSONDecodeError:
                # If not JSON, try comma-separated parsing
                origins = [item.strip() for item in cors_origins.split(",") if item.strip()]
                values["cors_allow_origins"] = origins

        return values

    @field_validator("cors_allow_origins")
    @classmethod
    def validate_cors_origins_prohibited_localhost(cls, v: list[str]) -> list[str]:
        """Validate that localhost is not used in production."""
        if cls.__dict__.get('_parent_class_name') == 'Settings' and v:
            app_env = get_settings().app_env
            if app_env != "development":
                localhost_origins = ["localhost", "127.0.0.1", "0.0.0.0"]
                for origin in v:
                    origin_lower = origin.lower()
                    for localhost in localhost_origins:
                        if localhost in origin_lower:
                            raise ValueError(
                                f"Localhost origins not allowed in production CORS. "
                                f"Found localhost in: {origin}. "
                                f"Please configure CORS_ORIGINS to production origins."
                            )
        return v

    @field_validator("cors_allow_methods")
    @classmethod
    def validate_cors_allow_methods(cls, v: str | list[str] | None) -> list[str]:
        """Validate and parse CORS allow methods."""
        if v is None or (isinstance(v, str) and not v.strip()):
            return ["GET", "POST", "PUT", "DELETE", "OPTIONS"]

        # If it's a string, try to parse as comma-separated list
        if isinstance(v, str):
            try:
                # Try parsing as JSON first
                import json
                parsed = json.loads(v)
                if isinstance(parsed, str):
                    return [method.strip().upper() for method in parsed.split(',')]
                elif isinstance(parsed, list):
                    return [str(item).strip().upper() for item in parsed]
                elif isinstance(parsed, dict):
                    return list(parsed.keys())
                return [v.strip().upper()]
            except json.JSONDecodeError:
                # If not JSON, try comma-separated
                return [method.strip().upper() for method in v.split(',')]

        # If it's already a list, return it
        if isinstance(v, list):
            return v

        return [str(v).strip().upper()]

    @field_validator("cors_allow_headers")
    @classmethod
    def validate_cors_allow_headers(cls, v: str | list[str] | None) -> list[str]:
        """Validate and parse CORS allow headers."""
        if v is None or (isinstance(v, str) and not v.strip()):
            return ["Content-Type", "Authorization"]

        # If it's a string, try to parse as comma-separated list
        if isinstance(v, str):
            try:
                # Try parsing as JSON first
                import json
                parsed = json.loads(v)
                if isinstance(parsed, str):
                    return [header.strip() for header in parsed.split(',')]
                elif isinstance(parsed, list):
                    return [str(item).strip() for item in parsed]
                elif isinstance(parsed, dict):
                    return list(parsed.values())
                return [v.strip()]
            except json.JSONDecodeError:
                # If not JSON, try comma-separated
                return [header.strip() for header in v.split(',')]

        # If it's already a list, return it
        if isinstance(v, list):
            return v

        return [str(v).strip()]

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
        default="openai/gpt-3.5-turbo",
        alias="OPENROUTER_MODEL"
    )

    get_model_for_companion: callable = None
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
    trainable_companions: list[str] | str = Field(
        default=["philosopher", "rival"],
        alias="TRAINABLE_COMPANIONS",
    )
    demo_companions: list[str] | str = Field(
        default=["party_friend", "freshman"],
        alias="DEMO_COMPANIONS",
    )

    # Per-companion OpenRouter model routing.
    # Keys are backend personality IDs; values are OpenRouter model slugs.
    companion_models: dict[str, str] = Field(
        default={
            "philosopher": "nvidia/nemotron-3-ultra-550b-a55b:free",
            "rival": "mistralai/mistral-small-3.1-24b-instruct:free",
            "party_friend": "google/gemma-4-31b-it:free",
            "freshman": "openai/gpt-oss-20b:free",
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
    @field_validator('access_token_expire_minutes')
    @classmethod
    def validate_token_expiry(cls, v: int) -> int:
        """Validate token expiration."""
        if v < 5:
            raise ValueError('ACCESS_TOKEN_EXPIRE_MINUTES should be at least 5 minutes')
        if v > 60:
            raise ValueError('ACCESS_TOKEN_EXPIRE_MINUTES should not exceed 60 minutes for security')
        return v

    @field_validator('companion_models')
    @classmethod
    def validate_companion_models(cls, v: dict[str, str] | str) -> dict[str, str]:
        """Validate and parse COMPANION_MODELS from environment variable."""
        # If it's a string, try to parse it as JSON
        if isinstance(v, str):
            # Check for empty or whitespace-only strings
            if not v or not v.strip():
                # Return default value if empty
                return {
                    "philosopher": "nvidia/nemotron-3-ultra-550b-a55b:free",
                    "rival": "mistralai/mistral-small-3.1-24b-instruct:free",
                    "party_friend": "google/gemma-4-31b-it:free",
                    "freshman": "openai/gpt-oss-20b:free",
                }
            try:
                parsed = json.loads(v)
                if isinstance(parsed, dict):
                    return parsed
                else:
                    raise ValueError(f'COMPANION_MODELS must be a JSON object (dictionary), got {type(parsed).__name__}')
            except json.JSONDecodeError as e:
                raise ValueError(f'COMPANION_MODELS must be valid JSON. Error: {e}')
        return v


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
