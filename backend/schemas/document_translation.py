"""
公文翻译相关 Pydantic Schema
"""

from typing import Optional
from datetime import datetime

from uuid import UUID
from pydantic import BaseModel, Field

from schemas.common import TimestampMixin, UUIDMixin


# ==================== 响应 Schema ====================

class DocumentTranslationResponse(UUIDMixin, TimestampMixin, BaseModel):
    """
    公文翻译响应 Schema
    """

    original_filename: str = Field(description="原始文件名")
    original_document_path: str = Field(description="原文档路径")
    translated_document_path: Optional[str] = Field(None, description="翻译后文档路径")
    status: str = Field(description="翻译状态")
    error_message: Optional[str] = Field(None, description="错误信息")
    original_text: Optional[str] = Field(None, description="提取的原文内容")
    translated_text: Optional[str] = Field(None, description="翻译后的文本内容")
    file_size: int = Field(description="文件大小（字节）")
    mime_type: str = Field(description="MIME 类型")
    source_language: str = Field(description="源语言")
    target_language: str = Field(description="目标语言")
    owner_id: str = Field(description="所有者 ID")

    class Config:
        from_attributes = True


# ==================== 上传响应 Schema ====================

class DocumentTranslationUploadResponse(BaseModel):
    """
    文档上传响应 Schema
    """

    translation_id: str = Field(description="翻译任务 ID")
    filename: str = Field(description="文件名")
    status: str = Field(description="当前状态")
    message: str = Field(default="文档上传成功，翻译任务已创建", description="响应消息")


# ==================== 翻译文本响应 Schema ====================

class DocumentTranslationTextResponse(BaseModel):
    """
    翻译文本响应 Schema
    """

    translation_id: str = Field(description="翻译任务 ID")
    translated_text: str = Field(description="翻译后的文本")
    original_text: Optional[str] = Field(None, description="原文内容")
