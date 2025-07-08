"""Application configuration settings."""

from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Project Info
    PROJECT_NAME: str = "TalentPrompt"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = Field(..., min_length=32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Allowed Hosts
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Database
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URL: Optional[str] = None

    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            # Ensure we use asyncpg driver
            if v.startswith("postgresql://"):
                return v.replace("postgresql://", "postgresql+asyncpg://")
            return v
        return (
            f"postgresql+asyncpg://{values.get('POSTGRES_USER')}:"
            f"{values.get('POSTGRES_PASSWORD')}@{values.get('POSTGRES_SERVER')}:"
            f"{values.get('POSTGRES_PORT', 5432)}/{values.get('POSTGRES_DB')}"
        )
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # AI Services
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4-turbo"
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-sonnet-20240229"
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    
    # Vector Database (Qdrant)
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_NAME: str = "talentprompt_resumes"
    
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
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    # First User
    FIRST_SUPERUSER: str
    FIRST_SUPERUSER_PASSWORD: str
    
    # Other
    SENTRY_DSN: Optional[str] = None
    LOG_LEVEL: str = "INFO"
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()