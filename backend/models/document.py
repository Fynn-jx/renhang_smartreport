"""
文档模型
"""

from typing import List, TYPE_CHECKING
from datetime import datetime
from enum import Enum

from sqlalchemy import String, Text, BigInteger, Boolean, ForeignKey, Column, Table, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from models.user import User
    from models.tag import Tag
    from models.task import Task


class DocumentType(str, Enum):
    """文档类型枚举"""

    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "markdown"
    IMAGE = "image"


class Document(Base, UUIDMixin, TimestampMixin):
    """
    文档模型
    存储 PDF、Word、��片等文件的元数据
    """

    # ==================== 基本信息 ====================
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
        comment="文档标题",
    )

    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="原始文件名",
    )

    document_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        comment="文档类型",
    )

    # ==================== 文件存储信息 ====================
    file_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="文件存储路径（相对路径）",
    )

    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="文件大小（字节）",
    )

    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="MIME 类型",
    )

    file_hash: Mapped[str | None] = mapped_column(
        String(64),
        unique=True,
        index=True,
        comment="文件 SHA256 哈希（用于去重）",
    )

    # ==================== 文档内容 ====================
    content: Mapped[str | None] = mapped_column(
        Text,
        comment="提取的文本内容（PDF、Word 等）",
    )

    content_preview: Mapped[str | None] = mapped_column(
        Text,
        comment="内容预览（前 500 字）",
    )

    page_count: Mapped[int | None] = mapped_column(
        BigInteger,
        comment="页数（PDF）",
    )

    # ==================== 元数据 ====================
    author: Mapped[str | None] = mapped_column(
        String(255),
        comment="作者",
    )

    subject: Mapped[str | None] = mapped_column(
        String(500),
        comment="主题",
    )

    keywords: Mapped[str | None] = mapped_column(
        Text,
        comment="关键词（逗号分隔）",
    )

    extra_metadata: Mapped[str | None] = mapped_column(
        Text,
        comment="额外元数据（JSON 格式）",
    )

    # ==================== 来源信息 ====================
    source_url: Mapped[str | None] = mapped_column(
        Text,
        comment="来源 URL（如果是从网页抓取）",
    )

    source_type: Mapped[str | None] = mapped_column(
        String(50),
        comment="来源类型（upload、browser_plugin、api）",
    )

    # ==================== 共享设置 ====================
    is_shared: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="是否共享给团队",
    )

    # ==================== 缩略图 ====================
    thumbnail_path: Mapped[str | None] = mapped_column(
        Text,
        comment="缩略图路径",
    )

    # ==================== 外键关系 ====================
    owner_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所有者 ID",
    )

    parent_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="CASCADE"),
        comment="父文档 ID（用于文档组织）",
    )

    # ==================== 关系 ====================
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="documents",
    )

    tags: Mapped[List["Tag"]] = relationship(
        "Tag",
        secondary="document_tags",
        back_populates="documents",
    )

    tasks: Mapped[List["Task"]] = relationship(
        "Task",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    children: Mapped[List["Document"]] = relationship(
        "Document",
        back_populates="parent",
        cascade="all, delete-orphan",
    )

    parent: Mapped["Document | None"] = relationship(
        "Document",
        back_populates="children",
        remote_side="Document.id",
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, title={self.title}, type={self.document_type})>"


# 注意：document_tags 关联表在 models/__init__.py 中定义
# 需要在 Tag 模型导入之后再创建
