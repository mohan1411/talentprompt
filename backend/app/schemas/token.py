"""Token schemas."""

from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    """Token response schema."""
    
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """JWT token payload."""
    
    sub: Optional[str] = None