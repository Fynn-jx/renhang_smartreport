"""
API 依赖注入
"""

import uuid
from typing import AsyncGenerator
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.config import settings


async def get_current_user_id(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
) -> str:
    """
    获取当前用户 ID（简化版）

    开发阶段：返回默认用户 ID
    生产阶段：从 JWT Token 解析

    Args:
        authorization: Authorization 头（可选）
        db: 数据库会话

    Returns:
        用户 ID（字符串格式）
    """
    # 简化方案：返回默认用户 ID
    # 从环境变量读取，或使用固定的默认值
    default_user_id = getattr(settings, "DEFAULT_USER_ID", "00000000-0000-0000-0000-000000000001")

    # 直接返回字符串，不转换为 UUID 对象（SQLite 不支持 UUID）
    return str(default_user_id)


async def get_current_user_optional(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
) -> str | None:
    """
    获取当前用户 ID（可选版本）

    始终返回用户 ID，简化认证流程
    """
    return await get_current_user_id(authorization, db)
