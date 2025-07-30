"""User schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False
    company: Optional[str] = None
    job_title: Optional[str] = None
    phone: Optional[str] = None
    oauth_provider: Optional[str] = None
    oauth_provider_id: Optional[str] = None


# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    username: str
    password: Optional[str] = Field(None, min_length=8)  # Optional for OAuth users
    recaptcha_token: Optional[str] = Field(None, alias="recaptchaToken")
    marketing_opt_in: Optional[bool] = Field(False, alias="marketingOptIn")
    
    class Config:
        populate_by_name = True  # Allow both snake_case and camelCase


# Properties to receive via API on update
class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8)


# Properties shared by models stored in DB
class UserInDBBase(UserBase):
    id: UUID | str
    created_at: datetime
    updated_at: Optional[datetime]
    last_login: Optional[datetime] = None

    @field_validator('id', mode='before')
    def convert_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v

    class Config:
        from_attributes = True
        json_encoders = {
            UUID: lambda v: str(v),
            datetime: lambda v: v.isoformat() if v else None
        }


# Properties to return to client
class User(UserInDBBase):
    id: str  # Ensure id is always string in response


# Properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: Optional[str]  # Optional for OAuth users
    oauth_data: Optional[str] = None


# OAuth specific schemas
class OAuthUserInfo(BaseModel):
    email: EmailStr
    full_name: str
    provider: str
    provider_id: str
    picture: Optional[str] = None
    raw_data: dict