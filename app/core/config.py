# app/core/config.py
from pydantic import field_validator
from pydantic import AnyHttpUrl, AnyUrl, field_validator, ValidationInfo
from typing import List, Optional

from pydantic_settings import BaseSettings
from pydantic import ValidationInfo


class Settings(BaseSettings):
    # General
    app_env: str = "development"
    debug: bool = False

    # Database
    database_url: AnyUrl

    # External integrations
    gemini_api_key: str
    resend_api_key: str
    resend_from_email: Optional[str] = None  # fallback "From" when workspace has no email config
    reply_to_email: Optional[str] = None  # reply-to address for customer emails
    # Twilio (optional; for SMS when configured)
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None

    # Frontend
    frontend_url: AnyHttpUrl | None = None

    # Security
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expires_minutes: int = 60 * 24

    # CORS
    cors_origins: List[AnyHttpUrl] = []

    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v, info: ValidationInfo):
        # pydantic-settings parses List from env as JSON; keep list or build from frontend_url
        origins = list(v) if isinstance(v, list) else []
        frontend = info.data.get("frontend_url") if info.data else None
        if frontend and str(frontend) not in origins:
            origins.append(str(frontend))
        return origins

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
print("GEMINI_API_KEY loaded:", bool(settings.gemini_api_key))
