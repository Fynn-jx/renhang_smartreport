"""
标签模型
"""

from typing import List, TYPE_CHECKING
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from models.document import Document


class Tag(Base, UUIDMixin, TimestampMixin):
    """
    标签模型
    用于分类和组织文档
    """

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
        comment="标签名称",
    )

    color: Mapped[str | None] = mapped_column(
        String(7),
        comment="标签颜色（十六进制，如 #FF5733）",
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        comment="标签描述",
    )

    # 关系
    documents: Mapped[List["Document"]] = relationship(
        "Document",
        secondary="document_tags",  # 多对多关系表
        back_populates="tags",
    )

    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, name={self.name}, color={self.color})>"
