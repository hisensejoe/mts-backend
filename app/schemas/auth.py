from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    phone: str = Field(min_length=10, max_length=20)


class VerifyOtpRequest(BaseModel):
    phone: str = Field(min_length=10, max_length=20)
    otp: str = Field(min_length=4, max_length=8)


class OtpChallengeResponse(BaseModel):
    message: str
    expires_in: int


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserContext(BaseModel):
    id: UUID
    phone: str
    full_name: str
    role: str
    customer_id: Optional[UUID] = None
    last_login_at: Optional[datetime] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserContext
