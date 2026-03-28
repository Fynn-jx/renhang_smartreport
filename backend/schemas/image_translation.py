"""
图片转译相关 Pydantic Schema
"""

from typing import Optional
from datetime import datetime

from uuid import UUID
from pydantic import BaseModel, Field

from schemas.common import TimestampMixin, UUIDMixin


# ==================== 响应 Schema ====================

class ImageTranslationResponse(UUIDMixin, TimestampMixin, BaseModel):
    """
    图片转译响应 Schema
    """

    original_filename: str = Field(description="原始文件名")
    original_image_path: str = Field(description="原图路径")
    translated_image_path: Optional[str] = Field(None, description="转译后图片路径")
    status: str = Field(description="转译状态")
    error_message: Optional[str] = Field(None, description="错误信息")
    file_size: int = Field(description="文件大小（字节）")
    mime_type: str = Field(description="MIME 类型")
    owner_id: str = Field(description="所有者 ID")

    class Config:
        from_attributes = True


# ==================== 上传响应 Schema ====================

class ImageTranslationUploadResponse(BaseModel):
    """
    图片上传响应 Schema
    """

    translation_id: str = Field(description="转译任务 ID")
    filename: str = Field(description="文件名")
    status: str = Field(description="当前状态")
    message: str = Field(default="图片上传成功，转译任务已创建", description="响应消息")
