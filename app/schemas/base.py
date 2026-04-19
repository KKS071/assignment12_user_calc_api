# app/schemas/base.py

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class UserBase(BaseModel):
    """Shared user fields used by create/login schemas."""
    first_name: str = Field(max_length=50, example="John")
    last_name: str = Field(max_length=50, example="Doe")
    email: EmailStr = Field(example="john.doe@example.com")
    username: str = Field(min_length=3, max_length=50, example="johndoe")

    model_config = ConfigDict(from_attributes=True)


class PasswordMixin(BaseModel):
    """Password field with strength validation (no special-char requirement)."""
    password: str = Field(..., min_length=8, example="SecurePass123")

    @model_validator(mode="after")
    def validate_password(self) -> "PasswordMixin":
        if not any(c.isupper() for c in self.password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in self.password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in self.password):
            raise ValueError("Password must contain at least one digit")
        return self

    model_config = ConfigDict(from_attributes=True)


class UserCreate(UserBase, PasswordMixin):
    """Schema for registering a new user (used by base schema tests)."""
    pass


class UserLogin(BaseModel):
    """Schema for user login credentials."""
    username: str = Field(min_length=3, max_length=50, example="johndoe")
    password: str = Field(min_length=8, example="SecurePass123")
