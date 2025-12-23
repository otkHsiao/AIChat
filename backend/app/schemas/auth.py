"""Authentication related schemas."""

# Optional: 类型注解，表示可选值
from typing import Optional

# BaseModel: Pydantic 的数据模型基类，提供数据验证和序列化功能
# EmailStr: Pydantic 的邮箱类型，自动验证邮箱格式
# Field: 字段声明器，用于定义字段的验证规则和元数据
from pydantic import BaseModel, EmailStr, Field


class UserSettings(BaseModel):
    """User settings schema."""

    defaultModel: str = "gpt-4o"
    theme: str = "light"


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user data in responses."""

    id: str
    email: str
    username: str
    createdAt: str
    settings: Optional[UserSettings] = None

    class Config:
        from_attributes = True


class UserInDB(UserResponse):
    """Schema for user data including password hash (internal use)."""

    passwordHash: str


class TokenResponse(BaseModel):
    """Schema for authentication token response."""

    user: UserResponse
    accessToken: str
    refreshToken: str
    expiresIn: int = Field(default=86400, description="Token expiration in seconds")


class TokenRefresh(BaseModel):
    """Schema for token refresh request."""

    refreshToken: str


class TokenPayload(BaseModel):
    """Schema for decoded JWT token payload."""

    sub: str
    exp: int
    iat: int
    type: str


class PasswordChange(BaseModel):
    """Schema for password change request."""

    currentPassword: str
    newPassword: str = Field(..., min_length=8, max_length=100)


class UserSettingsUpdate(BaseModel):
    """Schema for updating user settings."""

    defaultModel: Optional[str] = None
    theme: Optional[str] = None