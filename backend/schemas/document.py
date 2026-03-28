"""
文档相关 Pydantic Schema
"""

from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, HttpUrl, validator

from schemas.common import TimestampMixin, UUIDMixin


# ==================== 基础 Schema ====================

class DocumentBase(BaseModel):
    """
    文档基础 Schema
    """

    title: str = Field(..., min_length=1, max_length=500, description="文档标题")
    author: Optional[str] = Field(None, max_length=255, description="作者")
    subject: Optional[str] = Field(None, max_length=500, description="主题")
    keywords: Optional[List[str]] = Field(None, description="关键词列表")


# ==================== 创建 Schema ====================

class DocumentCreate(DocumentBase):
    """
    创建文档请求 Schema
    """

    # 文件信息（由前端上传时自动提供）
    original_filename: str = Field(..., description="原始文件名")
    document_type: str = Field(..., description="文档类型")

    # 可选：如果是 URL 抓取
    source_url: Optional[str] = Field(None, description="来源 URL")
    source_type: Optional[str] = Field("upload", description="来源类型")

    # 可选：标签
    tag_ids: Optional[List[UUID]] = Field(None, description="标签 ID 列表")

    # 可选：父文档
    parent_id: Optional[UUID] = Field(None, description="父文档 ID")

    # 可选：共享设置
    is_shared: Optional[bool] = Field(False, description="是否共享给团队")


# ==================== 更新 Schema ====================

class DocumentUpdate(BaseModel):
    """
    更新文档请求 Schema
    """

    title: Optional[str] = Field(None, min_length=1, max_length=500, description="文档标题")
    author: Optional[str] = Field(None, max_length=255, description="作者")
    subject: Optional[str] = Field(None, max_length=500, description="主题")
    keywords: Optional[List[str]] = Field(None, description="关键词列表")
    tag_ids: Optional[List[UUID]] = Field(None, description="标签 ID 列表")
    is_shared: Optional[bool] = Field(None, description="是否共享给团队")


# ==================== 响应 Schema ====================

class DocumentResponse(UUIDMixin, TimestampMixin, DocumentBase):
    """
    文档响应 Schema
    """

    original_filename: str = Field(description="原始文件名")
    document_type: str = Field(description="文档类型")
    file_path: str = Field(description="文件路径")
    file_size: int = Field(description="文件大小（字节）")
    mime_type: str = Field(description="MIME 类型")

    # 内容相关
    content_preview: Optional[str] = Field(None, description="内容预览")
    page_count: Optional[int] = Field(None, description="页数")

    # 来源信息
    source_url: Optional[str] = Field(None, description="来源 URL")
    source_type: Optional[str] = Field(None, description="来源类型")

    # 缩略图
    thumbnail_path: Optional[str] = Field(None, description="缩略图路径")

    # 共享设置
    is_shared: bool = Field(description="是否共享给团队")

    # 关系
    owner_id: str = Field(description="所有者 ID")
    parent_id: Optional[str] = Field(None, description="父文档 ID")

    # 关联的标签
    tags: List["TagResponse"] = Field(default_factory=list, description="标签列表")

    class Config:
        from_attributes = True


# ==================== 文件上传响应 Schema ====================

class DocumentUploadResponse(BaseModel):
    """
    文档上传响应 Schema
    """

    document_id: str = Field(description="文档 ID")
    filename: str = Field(description="文件名")
    file_size: int = Field(description="文件大小")
    document_type: str = Field(description="文档类型")
    message: str = Field(default="文档上传成功", description="响应消息")


# ==================== 文档列表查询参数 ====================

class DocumentListQuery(BaseModel):
    """
    文档列表查询参数
    """

    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")

    # 筛选条件
    document_type: Optional[str] = Field(None, description="按文档类型筛选")
    tag_id: Optional[UUID] = Field(None, description="按标签筛选")
    keyword: Optional[str] = Field(None, description="按关键词搜索（标题、作者、主题）")
    owner_id: Optional[UUID] = Field(None, description="按所有者筛选")

    # 排序
    sort_by: str = Field(default="created_at", description="排序字段")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="排序方向")


# ==================== 标签 Schema ====================

class TagBase(BaseModel):
    """
    标签基础 Schema
    """

    name: str = Field(..., min_length=1, max_length=50, description="标签名称")
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$", description="标签颜色（如 #FF5733）")
    description: Optional[str] = Field(None, description="标签描述")


class TagCreate(TagBase):
    """
    创建标签请求 Schema
    """

    pass


class TagUpdate(BaseModel):
    """
    更新标签请求 Schema
    """

    name: Optional[str] = Field(None, min_length=1, max_length=50, description="标签名称")
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$", description="标签颜色")
    description: Optional[str] = Field(None, description="标签描述")


class TagResponse(UUIDMixin, TimestampMixin, TagBase):
    """
    标签响应 Schema
    """

    class Config:
        from_attributes = True


# 更新前向引用
DocumentResponse.model_rebuild()


# ==================== 内容提取请求 ====================

class DocumentContentExtractRequest(BaseModel):
    """
    文档内容提取请求 Schema
    """

    force_refresh: bool = Field(
        default=False,
        description="是否强制重新提取（即使已有缓存）"
    )


class DocumentContentExtractResponse(BaseModel):
    """
    文档内容提取响应 Schema
    """

    document_id: str = Field(description="文档 ID")
    content: str = Field(description="提取的文本内容")
    page_count: Optional[int] = Field(None, description="页数")
    message: str = Field(default="内容提取成功", description="响应消息")
