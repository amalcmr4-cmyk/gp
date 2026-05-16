from datetime import datetime
from pydantic import BaseModel, EmailStr, validator
from typing import Optional


class UserCreate(BaseModel):
    email: EmailStr
    password: str

    @validator("password")
    def password_strength(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not any(char.islower() for char in value):
            raise ValueError("Password must include at least one lowercase letter.")
        if not any(char.isupper() for char in value):
            raise ValueError("Password must include at least one uppercase letter.")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must include at least one digit.")
        return value


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        orm_mode = True


class MessageResponse(BaseModel):
    detail: str


class ForgotPasswordRequest(BaseModel):
    """Request model for forgot-password endpoint"""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Request model for reset-password endpoint with password strength validation"""
    token: str
    new_password: str

    @validator("new_password")
    def password_strength(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        if not any(char.islower() for char in value):
            raise ValueError("Password must include at least one lowercase letter.")
        if not any(char.isupper() for char in value):
            raise ValueError("Password must include at least one uppercase letter.")
        if not any(char.isdigit() for char in value):
            raise ValueError("Password must include at least one digit.")
        return value
