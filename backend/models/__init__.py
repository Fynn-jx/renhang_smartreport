"""
数据库模型
"""

from sqlalchemy import Column, String, ForeignKey, Table

from models.base import Base, BaseModel
from models.user import User
from models.tag import Tag
from models.document import Document, DocumentType
from models.official_document import OfficialDocument, DocumentSource
from models.task import Task, TaskStatus, TaskType
from models.image_translation import ImageTranslation, ImageTranslationStatus
from models.document_translation import DocumentTranslation, DocumentTranslationStatus

# 多对多关系表（文档-标签）
# 需要在 Tag 和 Document 模型都导入之后创建
document_tags = Table(
    "document_tags",
    Base.metadata,
    Column("document_id", String(36), ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", String(36), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    comment="文档-标签关联表",
)

__all__ = [
    # Base
    "Base",
    "BaseModel",
    # Models
    "User",
    "Document",
    "DocumentType",
    "OfficialDocument",
    "DocumentSource",
    "Tag",
    "Task",
    "TaskStatus",
    "TaskType",
    "ImageTranslation",
    "ImageTranslationStatus",
    "DocumentTranslation",
    "DocumentTranslationStatus",
    # Relationship Tables
    "document_tags",
]
