"""
用户相关 Pydantic Schema
"""

from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator

from schemas.common import UUIDMixin, TimestampMixin


# ==================== 用户 Schema ====================

class UserBase(BaseModel):
    """
    用户基础 Schema
    """

    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")


class UserCreate(UserBase):
    """
    创建用户请求 Schema
    """

    password: str = Field(..., min_length=8, max_length=100, description="密码")

    @validator("password")
    def validate_password(cls, v):
        """验证密码强度"""
        if len(v) < 8:
            raise ValueError("密码长度至少为 8 位")
        return v


class UserUpdate(BaseModel):
    """
    更新用户请求 Schema
    """

    email: Optional[EmailStr] = Field(None, description="邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    password: Optional[str] = Field(None, min_length=8, max_length=100, description="密码")


class UserResponse(UUIDMixin, TimestampMixin, UserBase):
    """
    用户响应 Schema
    """

    is_active: bool = Field(description="是否激活")
    is_superuser: bool = Field(description="是否超级管理员")

    class Config:
        from_attributes = True


# ==================== 认证 Schema ====================

class LoginRequest(BaseModel):
    """
    登录请求 Schema
    """

    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class LoginResponse(BaseModel):
    """
    登录响应 Schema
    """

    access_token: str = Field(..., description="访问令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    user: UserResponse = Field(..., description="用户信息")


class TokenPayload(BaseModel):
    """
    令牌载荷 Schema
    """

    sub: str = Field(..., description="用户 ID")
    exp: int = Field(..., description="过期时间（Unix 时间戳）")
