"""Token schemas."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, field_validator


class Token(BaseModel):
    """Token response schema."""
    
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Token payload schema."""
    
    sub: UUID | str
    exp: Optional[int] = None
    
    @field_validator('sub', mode='before')
    def convert_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v