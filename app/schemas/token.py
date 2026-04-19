# app/schemas/token.py

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


class Token(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer")
    expires_at: datetime = Field(..., description="Token expiration time")

    model_config = ConfigDict(from_attributes=True)


class TokenData(BaseModel):
    user_id: UUID
    exp: datetime
    jti: str
    token_type: TokenType

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """Full token response returned after login."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_at: datetime
    user_id: UUID
    username: str
    email: str
    first_name: str
    last_name: str
    is_active: bool
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)
