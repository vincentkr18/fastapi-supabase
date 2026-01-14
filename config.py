"""
Configuration management for FastAPI + Supabase Auth application.
Loads environment variables and provides application settings.
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
from typing import List, Union


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
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
