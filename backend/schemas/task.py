"""
任务相关 Pydantic Schema
"""

from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

from schemas.common import UUIDMixin, TimestampMixin


# ==================== 任务 Schema ====================

class TaskBase(BaseModel):
    """
    任务基础 Schema
    """

    title: str = Field(..., min_length=1, max_length=500, description="任务标题")


class TaskCreate(TaskBase):
    """
    创建任务请求 Schema
    """

    task_type: str = Field(..., description="任务类型")
    document_id: Optional[UUID] = Field(None, description="关联文档 ID")
    input_data: Optional[Dict[str, Any]] = Field(None, description="输入数据")


class TaskUpdate(BaseModel):
    """
    更新任务请求 Schema
    """

    title: Optional[str] = Field(None, min_length=1, max_length=500, description="任务标题")
    status: Optional[str] = Field(None, description="任务状态")


class TaskResponse(UUIDMixin, TimestampMixin, TaskBase):
    """
    任务响应 Schema
    """

    task_type: str = Field(description="任务类型")
    status: str = Field(description="任务状态")

    # 输入输出
    input_data: Optional[Dict[str, Any]] = Field(None, description="输入数据")
    output_text: Optional[str] = Field(None, description="输出文本")
    output_reasoning: Optional[str] = Field(None, description="思维链内容")

    # 错误信息
    error_message: Optional[str] = Field(None, description="错误信息")

    # 时间信息
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时���")
    duration_ms: Optional[int] = Field(None, description="执行耗时（毫秒）")

    # 进度信息
    progress_current: int = Field(description="当前进度")
    progress_total: int = Field(description="总进度")
    progress_message: Optional[str] = Field(None, description="进度消息")

    # 关联
    owner_id: str = Field(description="创建者 ID")
    document_id: Optional[str] = Field(None, description="关联文档 ID")

    class Config:
        from_attributes = True


# ==================== 工作流执行请求 ====================

class WorkflowExecuteRequest(TaskBase):
    """
    工作流执行请求 Schema
    """

    task_type: str = Field(..., description="任务类型")
    document_id: Optional[UUID] = Field(None, description="关联文档 ID")
    input_data: Optional[Dict[str, Any]] = Field(None, description="输入数据")
    stream: bool = Field(
        default=True,
        description="是否使用流式输出（SSE）"
    )


class WorkflowExecuteResponse(BaseModel):
    """
    工作流执行响应 Schema
    """

    task_id: str = Field(description="任务 ID")
    status: str = Field(description="任务状态")
    message: str = Field(default="任务已创建", description="响应消息")
    stream_url: Optional[str] = Field(None, description="SSE 流式输出 URL")


# ==================== SSE 事件 Schema ====================

class SSEStatusEvent(BaseModel):
    """
    SSE 状态事件
    """

    type: str = Field(default="status", description="事件类型")
    message: str = Field(..., description="状态消息")


class SSEThinkingEvent(BaseModel):
    """
    SSE 思维链事件（DeepSeek-R1）
    """

    type: str = Field(default="thinking", description="事件类型")
    content: str = Field(..., description="思维链内容")


class SSEContentEvent(BaseModel):
    """
    SSE 内容事件（打字机效果）
    """

    type: str = Field(default="content", description="事件类型")
    content: str = Field(..., description="正文内容片段")


class SSEProgressEvent(BaseModel):
    """
    SSE 进度事件
    """

    type: str = Field(default="progress", description="事件类型")
    step: int = Field(..., description="当前步骤")
    total: int = Field(..., description="总步骤数")
    message: str = Field(..., description="进度消息")


class SSEErrorEvent(BaseModel):
    """
    SSE 错误事件
    """

    type: str = Field(default="error", description="事件类型")
    message: str = Field(..., description="错误消息")


class SSEDoneEvent(BaseModel):
    """
    SSE 完成事件
    """

    type: str = Field(default="done", description="事件类型")
    task_id: str = Field(..., description="任务 ID")
