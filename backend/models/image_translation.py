"""
图片转译模型
用于记录图片转译任务
"""

from typing import TYPE_CHECKING
from enum import Enum

from sqlalchemy import String, Text, BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from models.user import User


class ImageTranslationStatus(str, Enum):
    """图片转译状态枚举"""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ImageTranslation(Base, UUIDMixin, TimestampMixin):
    """
    图片转译模型
    记录图片转译任务的历史和结果
    """

    # ==================== 文件路径 ====================
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="原始文件名",
    )

    original_image_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="原图存储路径",
    )

    translated_image_path: Mapped[str | None] = mapped_column(
        Text,
        comment="转译后图片路径",
    )

    # ==================== 转译信息 ====================
    status: Mapped[str] = mapped_column(
        String(20),
        default=ImageTranslationStatus.PENDING,
        nullable=False,
        index=True,
        comment="转译状态",
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        comment="错误信息",
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
        backref="image_translations",
    )

    def __repr__(self) -> str:
        return f"<ImageTranslation(id={self.id}, filename={self.original_filename}, status={self.status})>"
