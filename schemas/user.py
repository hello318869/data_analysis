import re

from pydantic import BaseModel, Field, field_validator


class UserRegister(BaseModel):
    """Schema for user registration request validation."""

    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)
    confirm_password: str = Field(..., min_length=6, max_length=128)

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Ensure username only contains alphanumeric characters and underscores."""
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("用户名只能包含字母、数字和下划线")
        return v

    @field_validator("confirm_password")
    @classmethod
    def validate_passwords_match(cls, v: str, info) -> str:
        """Ensure password and confirm_password fields match."""
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("两次输入的密码不一致")
        return v


class UserLogin(BaseModel):
    """Schema for user login request validation."""

    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    """Schema for user response to clients (excludes sensitive fields)."""

    id: int
    username: str
    created_at: str | None = None

    class Config:
        from_attributes = True
