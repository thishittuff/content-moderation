from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Database Configuration
    database_url: str = "sqlite+aiosqlite:///./content_moderation.db"
    redis_url: str = "redis://localhost:6379/0"
    
    # Google Gemini Configuration
    google_api_key: str
    gemini_model: str = "gemini-2.0-flash-lite"
    
    # Slack Configuration
    slack_bot_token: Optional[str] = None
    slack_channel_id: Optional[str] = None
    
    # Email Configuration (BrevoMail)
    brevo_api_key: Optional[str] = None
    brevo_sender_email: Optional[str] = None
    
    # Sentry Configuration
    sentry_dsn: Optional[str] = None
    sentry_environment: str = "development"
    
    # GitHub Configuration
    github_token: Optional[str] = None
    github_repo: Optional[str] = None
    
    # Application Configuration
    secret_key: str = "your-secret-key-change-in-production"
    debug: bool = True
    allowed_hosts: str = "localhost,127.0.0.1"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Validate required settings
if not settings.google_api_key:
    raise ValueError("GOOGLE_API_KEY is required. Please set it in your .env file.")
