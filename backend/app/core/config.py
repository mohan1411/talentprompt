"""Application configuration settings."""

from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Project Info
    PROJECT_NAME: str = "Promtitude"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = Field(default=False)  # Must be False in production, can override for dev
    
    # Security
    SECRET_KEY: str = Field(min_length=32)  # No default - must be set via environment
    JWT_SECRET_KEY: Optional[str] = Field(default=None)  # Alias for SECRET_KEY if provided
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    @model_validator(mode='before')
    def set_secret_key(cls, values):
        """Use JWT_SECRET_KEY as SECRET_KEY if SECRET_KEY is not provided."""
        if not values.get('SECRET_KEY') and values.get('JWT_SECRET_KEY'):
            values['SECRET_KEY'] = values['JWT_SECRET_KEY']
        # Validate DEBUG is False in production
        import os
        if os.getenv('ENVIRONMENT') == 'production':
            debug_value = values.get('DEBUG', False)
            # Handle string values from environment variables
            if isinstance(debug_value, str):
                debug_value = debug_value.lower() in ('true', '1', 'yes', 'on')
            if debug_value:
                raise ValueError('DEBUG must be False in production environment')
        return values
    
    @model_validator(mode='after')
    def assemble_redis_url(self) -> 'Settings':
        """Construct Redis URL if not provided."""
        if not self.REDIS_URL:
            # Check for Railway Redis URL format
            import os
            railway_redis = os.getenv('REDIS_URL')
            if railway_redis:
                self.REDIS_URL = railway_redis
                print(f"Using Railway Redis URL: {railway_redis.split('@')[1] if '@' in railway_redis else 'configured'}")
            elif self.REDIS_PASSWORD:
                self.REDIS_URL = f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
            else:
                self.REDIS_URL = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return self
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:8000",
            "https://promtitude.com",
            "https://www.promtitude.com",
            "https://promtitude.vercel.app",
            "https://promtitude-backend-production.up.railway.app"
        ]
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode='before')
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Allowed Hosts - restrict in production
    ALLOWED_HOSTS: List[str] = Field(
        default=[
            "localhost",
            "127.0.0.1",
            "promtitude.com",
            "www.promtitude.com",
            "promtitude-backend-production.up.railway.app",
            "talentprompt-production.up.railway.app"
        ]
    )
    
    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "promtitude"
    DATABASE_URL: Optional[str] = None

    @model_validator(mode='after')
    def assemble_db_connection(self) -> 'Settings':
        # If DATABASE_URL is already set, ensure it uses asyncpg
        if self.DATABASE_URL:
            # Log the database URL (without password) for debugging
            import re
            safe_url = re.sub(r'://[^@]+@', '://***:***@', self.DATABASE_URL)
            print(f"Using DATABASE_URL: {safe_url}")
            
            # Ensure we use asyncpg driver
            if self.DATABASE_URL.startswith("postgresql://"):
                self.DATABASE_URL = self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
            elif self.DATABASE_URL.startswith("postgres://"):
                self.DATABASE_URL = self.DATABASE_URL.replace("postgres://", "postgresql+asyncpg://")
        else:
            # Build from individual components
            print("WARNING: DATABASE_URL not found, using default localhost settings")
            self.DATABASE_URL = (
                f"postgresql+asyncpg://{self.POSTGRES_USER}:"
                f"{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:"
                f"{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        return self
    
    # Redis
    REDIS_URL: Optional[str] = None
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # AI Services
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4.1-mini-2025-04-14"
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-sonnet-20240229"
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    ASSEMBLYAI_API_KEY: Optional[str] = None
    
    # Vector Database (Qdrant)
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_NAME: str = "promtitude_resumes"
    
    # Supabase
    SUPABASE_URL: Optional[str] = None
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SERVICE_KEY: Optional[str] = None
    
    # Email
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = Field(default="noreply@promtitude.com")
    EMAILS_FROM_NAME: Optional[str] = Field(default="Promtitude Team")
    
    # First User
    FIRST_SUPERUSER: str
    FIRST_SUPERUSER_PASSWORD: str
    
    # OAuth Settings
    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: Optional[str] = None
    
    # LinkedIn OAuth
    LINKEDIN_CLIENT_ID: Optional[str] = None
    LINKEDIN_CLIENT_SECRET: Optional[str] = None
    LINKEDIN_REDIRECT_URI: Optional[str] = None
    
    # Frontend URL for OAuth redirects
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Backend API URL for OAuth callbacks
    API_URL: str = "http://localhost:8000"
    
    # Other
    SENTRY_DSN: Optional[str] = None
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "production"  # development, staging, production
    
    # File Upload
    MAX_FILE_SIZE_MB: int = 10
    
    # Google reCAPTCHA
    RECAPTCHA_SECRET_KEY: Optional[str] = None
    RECAPTCHA_ENABLED: bool = True
    
    # Redis Configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_URL: Optional[str] = None
    
    # Extension Token Settings
    EXTENSION_TOKEN_LENGTH: int = 6
    EXTENSION_TOKEN_EXPIRE_SECONDS: int = 600  # 10 minutes
    EXTENSION_TOKEN_RATE_LIMIT: int = 3  # Max attempts per hour
    
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"  # Ignore extra fields in .env file
    )


settings = Settings()

# Debug logging for environment variables
import logging
logger = logging.getLogger(__name__)
logger.info(f"ASSEMBLYAI_API_KEY loaded: {'Yes' if settings.ASSEMBLYAI_API_KEY else 'No'}")
if settings.ASSEMBLYAI_API_KEY:
    logger.info(f"ASSEMBLYAI_API_KEY first 10 chars: {settings.ASSEMBLYAI_API_KEY[:10]}...")