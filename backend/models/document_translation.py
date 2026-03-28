"""
公文翻译模型
用于记录公文文档翻译任务
"""

from typing import TYPE_CHECKING
from enum import Enum

from sqlalchemy import String, Text, BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from models.user import User


class DocumentTranslationStatus(str, Enum):
    """公文翻译状态枚举"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentTranslation(Base, UUIDMixin, TimestampMixin):
    """
    公文翻译模型
    记录公文文档翻译任务的历史和结果
    """

    # ==================== 文件路径 ====================
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="原始文件名",
    )

    original_document_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="原文档存储路径",
    )

    translated_document_path: Mapped[str | None] = mapped_column(
        Text,
        comment="翻译后文档路径",
    )

    # ==================== 翻译信息 ====================
    status: Mapped[str] = mapped_column(
        String(20),
        default=DocumentTranslationStatus.PENDING,
        nullable=False,
        index=True,
        comment="翻译状态",
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        comment="错误信息",
    )

    # ==================== 原文和译文 ====================
    original_text: Mapped[str | None] = mapped_column(
        Text,
        comment="提取的原文内容",
    )

    translated_text: Mapped[str | None] = mapped_column(
        Text,
        comment="翻译后的文本内容",
    )

    # ==================== 元数据 ====================
    file_size: Mapped[int] = mapped_column(
        BigInteger,
        comment="文件大小（字节）",
    )

    mime_type: Mapped[str] = mapped_column(
        String(100),
        comment="MIME 类型",
    )

    source_language: Mapped[str] = mapped_column(
        String(20),
        default="auto",
        comment="源语言",
    )

    target_language: Mapped[str] = mapped_column(
        String(20),
        default="zh",
        comment="目标语言",
    )

    # ==================== 外键关系 ====================
    owner_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所有者 ID",
    )

    # ==================== 关系 ====================
    owner: Mapped["User"] = relationship(
        "User",
        backref="document_translations",
    )

    def __repr__(self) -> str:
        return f"<DocumentTranslation(id={self.id}, filename={self.original_filename}, status={self.status})>"
