"""
数据库模型基类
提供所有模型的通用字段和方法
"""

from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class Base(DeclarativeBase):
    """
    所有模型的基类
    提供表名自动生成功能
    """

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """自动生成表名：类名转小写 + 下划线"""
        name = cls.__name__
        # 将驼峰命名转换为下划线命名
        result = [name[0].lower()]
        for char in name[1:]:
            if char.isupper():
                result.extend(["_", char.lower()])
            else:
                result.append(char)
        return "".join(result) + "s"  # 复数形式


class TimestampMixin:
    """
    时间戳混入类
    为模型提供 created_at 和 updated_at 字段
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间",
    )


class UUIDMixin:
    """
    UUID 混入类
    为模型提供 UUID 主键
    使用 String 类型以兼容 SQLite 和 PostgreSQL
    """

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
        nullable=False,
        comment="主键 ID",
    )


class BaseModel(UUIDMixin, TimestampMixin):
    """
    基础模型混入类
    包含 UUID 主键和时间戳
    注意：不继承 Base，避免创建 base_models 表
    """

    def to_dict(self) -> dict[str, Any]:
        """
        将模型转换为字典

        Returns:
            模型数据的字典表示
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    def __repr__(self) -> str:
        """模型的字符串表示"""
        class_name = self.__class__.__name__
        return f"<{class_name}(id={self.id})>"
