"""
Configuration management for FastAPI + Supabase Auth application.
Loads environment variables and provides application settings.
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
from typing import List, Union
from dotenv import load_dotenv
import os


load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "FastAPI Supabase SaaS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET: str
    SUPABASE_TOKEN: str = ""
    SUPABASE_ORG_ID: str = ""
    
    # Database (Supabase PostgreSQL)
    DATABASE_URL: str
    
    # Lemon Squeezy Webhook
    LEMON_SQUEEZY_WEBHOOK_SECRET: str = ""
    
    # API Key Security
    API_KEY_SECRET_KEY: str  # For hashing API keys
    
    # AWS S3 Configuration
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "eu-north-1")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "ugc-audio-images-store-s3")
    S3_BUCKET_URL: str = f"https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/"  # e.g., https://your-bucket.s3.amazonaws.com
    

    # Dodo Payments
    dodo_api_key: str =  os.getenv("DODO_API_KEY", "")
    dodo_api_secret: str = os.getenv("DODO_API_SECRET", "")
    dodo_webhook_secret: str = os.getenv("DODO_WEBHOOK_SECRET", "")
    dodo_base_url: str = os.getenv("DODO_BASE_URL", "https://api.dodopayments.com/v1")
    dodo_mode: str = os.getenv("DODO_MODE", "test")
    
    # Apple IAP
    apple_shared_secret: str = ""
    apple_bundle_id: str = ""
    apple_verify_receipt_url_sandbox: str = "https://sandbox.itunes.apple.com/verifyReceipt"
    apple_verify_receipt_url_production: str = "https://buy.itunes.apple.com/verifyReceipt"
    apple_mode: str = "sandbox"
    
    # Google Play
    google_service_account_json: str = ""
    google_package_name: str = ""
    google_publisher_api_version: str = "v3"
    
    # Webhooks
    webhook_base_url: str = ""
    dodo_webhook_path: str = "/api/webhooks/dodo"
    apple_webhook_path: str = "/api/webhooks/apple"
    google_webhook_path: str = "/api/webhooks/google"

    # CORS
    CORS_ORIGINS: Union[str, List[str]] = "*"
    
    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse comma-separated CORS origins into a list."""
        if v == "*":
            return ["*"]
        if isinstance(v, str):
            # Split by comma and strip whitespace
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        elif isinstance(v, list):
            # Already a list
            return v
        return []
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
