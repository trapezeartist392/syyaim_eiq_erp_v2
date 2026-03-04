from pydantic_settings import BaseSettings
from typing import List
import secrets

class Settings(BaseSettings):
    # App
    COMPANY_NAME: str = "Syyaim EIQ ERP"
    ENVIRONMENT: str = "production"
    BASE_DOMAIN: str = "syyaimeiq.com"
    APP_URL: str = "https://syyaimeiq.com"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://miq_user:changeme@localhost:5432/syyaimeiq"

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(64)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:80",
        "http://localhost:3000",
        "https://syyaimeiq.com",
        "https://*.syyaimeiq.com",
    ]

    # Anthropic
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-opus-4-6"

    # Redis (for Celery background tasks)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Razorpay
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""
    RAZORPAY_PLAN_ID: str = ""

    # Trial
    TRIAL_DAYS: int = 14

    # Email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@syyaimeiq.com"

    # Super Admin
    SUPERADMIN_SECRET: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
