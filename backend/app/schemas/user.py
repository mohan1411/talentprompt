"""User schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False
    company: Optional[str] = None
    job_title: Optional[str] = None


# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    username: str
    password: str = Field(..., min_length=8)


# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = Field(None, min_length=8)


# Properties shared by models stored in DB
class UserInDBBase(UserBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Properties to return to client
class User(UserInDBBase):
    pass


# Properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str