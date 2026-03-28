"""
任务模型
用于记录 AI 工作流的执行历史
"""

from typing import TYPE_CHECKING
from datetime import datetime
from enum import Enum

from sqlalchemy import String, Text, BigInteger, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base, UUIDMixin, TimestampMixin

if TYPE_CHECKING:
    from models.user import User
    from models.document import Document


class TaskStatus(str, Enum):
    """任务状态枚举"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    """任务类型枚举"""

    ACADEMIC_TO_OFFICIAL = "academic_to_official"
    TRANSLATION = "translation"
    COUNTRY_RESEARCH = "country_research"
    QUARTERLY_REPORT = "quarterly_report"
    IMAGE_TRANSLATION = "image_translation"


class Task(Base, UUIDMixin, TimestampMixin):
    """
    任务模型
    记录 AI 工作流的执行历史
    """

    # ==================== 基本信息 ====================
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="任务标题",
    )

    task_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="任务类型",
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default=TaskStatus.PENDING.value,
        nullable=False,
        index=True,
        comment="任务状态",
    )

    # ==================== 输入输出 ====================
    input_data: Mapped[str | None] = mapped_column(
        Text,
        comment="输入数据（JSON 格式）",
    )

    output_text: Mapped[str | None] = mapped_column(
        Text,
        comment="输出文本（Markdown）",
    )

    output_reasoning: Mapped[str | None] = mapped_column(
        Text,
        comment="思维链内容（DeepSeek-R1）",
    )

    # ==================== 错误信息 ====================
    error_message: Mapped[str | None] = mapped_column(
        Text,
        comment="错误信息（如果失败）",
    )

    # ==================== 时间信息 ====================
    started_at: Mapped[datetime | None] = mapped_column(
        comment="开始时间",
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        comment="完成时间",
    )

    duration_ms: Mapped[int | None] = mapped_column(
        BigInteger,
        comment="执行耗时（毫秒）",
    )

    # ==================== 进度信息 ====================
    progress_current: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
        nullable=False,
        comment="当前进度",
    )

    progress_total: Mapped[int] = mapped_column(
        BigInteger,
        default=100,
        nullable=False,
        comment="总进度",
    )

    progress_message: Mapped[str | None] = mapped_column(
        String(500),
        comment="进度消息",
    )

    # ==================== 外键关系 ====================
    owner_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="创建者 ID",
    )

    document_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("documents.id", ondelete="SET NULL"),
        comment="关联文档 ID",
    )

    # ==================== 关系 ====================
    owner: Mapped["User"] = relationship(
        "User",
        back_populates="tasks",
    )

    document: Mapped["Document | None"] = relationship(
        "Document",
        back_populates="tasks",
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, type={self.task_type}, status={self.status})>"
