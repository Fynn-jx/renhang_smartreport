"""
公文库模型
"""

from typing import TYPE_CHECKING
from datetime import datetime
from enum import Enum

from sqlalchemy import String, Text, BigInteger, ForeignKey, Column, Table, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, UUIDMixin

if TYPE_CHECKING:
    from models.user import User


class DocumentSource(str, Enum):
    """公文来源机构枚举"""
    WORLD_BANK = "世界银行"
    IMF = "IMF"
    UN = "联合国"
    UNECA = "联合国非洲经济委员会"
    AFRICAN_DEVELOPMENT_BANK = "非洲开发银行"
    WTO = "WTO"
    OECD = "OECD"
    PBOC = "中国人民银行"
    NBS = "国家统计局"
    OTHER = "其他"


class OfficialDocument(Base, UUIDMixin):
    """
    公文库模型

    用于存储经过人工审核的高质量公文模板，
    作为 AI 写作的风格参考库和知识积累库。
    """

    # ==================== 基本信息 ====================
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
        comment="公文标题",
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
        comment="文档类型 (pdf/docx/txt/md)",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        comment="公文描述",
    )

    # ==================== 时间戳 ====================
    created_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="创建时间（Unix 时间戳）",
    )

    updated_at: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="更新时间（Unix 时间戳）",
    )

    # ==================== 来源信息 ====================
    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="来源机构",
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
        Text(65535),
        comment="提取的文本内容",
    )

    content_preview: Mapped[str | None] = mapped_column(
        Text(65535),
        comment="内容预览（前 500 字）",
    )

    page_count: Mapped[int | None] = mapped_column(
        BigInteger,
        comment="页数",
    )

    # ==================== 审核信息 ====================
    verified_by: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="审核人 ID",
    )

    verified_at: Mapped[datetime | None] = mapped_column(
        BigInteger,
        comment="审核时间（Unix 时间戳）",
    )

    is_verified: Mapped[bool] = mapped_column(
        BigInteger,
        default=False,
        nullable=False,
        index=True,
        comment="是否已审核",
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

    # ==================== 关系 ====================
    owner: Mapped["User"] = relationship(
        "User",
        foreign_keys=[owner_id],
        back_populates="official_documents",
    )

    verifier: Mapped["User | None"] = relationship(
        "User",
        foreign_keys=[verified_by],
    )

    def __repr__(self) -> str:
        return f"<OfficialDocument(id={self.id}, title={self.title}, source={self.source})>"
