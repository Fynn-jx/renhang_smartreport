"""
通用 Pydantic Schema
"""

from typing import Any, Generic, TypeVar, Optional
from pydantic import BaseModel, Field
from datetime import datetime

DataT = TypeVar("DataT")


class ResponseModel(BaseModel, Generic[DataT]):
    """
    通用响应模型
    """

    code: int = Field(default=200, description="状态码")
    message: str = Field(default="success", description="响应消息")
    data: Optional[DataT] = Field(default=None, description="响应数据")


class PaginatedResponse(BaseModel, Generic[DataT]):
    """
    分页响应模型
    """

    items: list[DataT] = Field(description="数据列表")
    total: int = Field(description="总数量")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页数量")
    total_pages: int = Field(description="总页数")

    @classmethod
    def create(
        cls,
        items: list[DataT],
        total: int,
        page: int = 1,
        page_size: int = 20,
    ) -> "PaginatedResponse[DataT]":
        """
        创建分页响应

        Args:
            items: 数据列表
            total: 总数量
            page: 当前页码
            page_size: 每页数量

        Returns:
            分页响应对象
        """
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0

        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class TimestampMixin(BaseModel):
    """
    时间戳混入类
    """

    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")


class UUIDMixin(BaseModel):
    """
    UUID 混入类
    """

    id: str = Field(description="主键 ID")


class HealthResponse(BaseModel):
    """
    健康检查响应
    """

    status: str = Field(description="服务状态")
    service: str = Field(description="服务名称")
    version: str = Field(description="版本号")
