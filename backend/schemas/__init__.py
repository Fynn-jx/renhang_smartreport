"""
Pydantic Schemas
"""

from schemas.common import (
    ResponseModel,
    PaginatedResponse,
    TimestampMixin,
    UUIDMixin,
    HealthResponse,
)

from schemas.document import (
    DocumentBase,
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
    DocumentUploadResponse,
    DocumentListQuery,
    DocumentContentExtractRequest,
    DocumentContentExtractResponse,
    TagBase,
    TagCreate,
    TagUpdate,
    TagResponse,
)

from schemas.task import (
    TaskBase,
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    WorkflowExecuteRequest,
    WorkflowExecuteResponse,
    SSEStatusEvent,
    SSEThinkingEvent,
    SSEContentEvent,
    SSEProgressEvent,
    SSEErrorEvent,
    SSEDoneEvent,
)

from schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    LoginRequest,
    LoginResponse,
    TokenPayload,
)

__all__ = [
    # Common
    "ResponseModel",
    "PaginatedResponse",
    "TimestampMixin",
    "UUIDMixin",
    "HealthResponse",
    # Document
    "DocumentBase",
    "DocumentCreate",
    "DocumentUpdate",
    "DocumentResponse",
    "DocumentUploadResponse",
    "DocumentListQuery",
    "DocumentContentExtractRequest",
    "DocumentContentExtractResponse",
    # Tag
    "TagBase",
    "TagCreate",
    "TagUpdate",
    "TagResponse",
    # Task
    "TaskBase",
    "TaskCreate",
    "TaskUpdate",
    "TaskResponse",
    "WorkflowExecuteRequest",
    "WorkflowExecuteResponse",
    "SSEStatusEvent",
    "SSEThinkingEvent",
    "SSEContentEvent",
    "SSEProgressEvent",
    "SSEErrorEvent",
    "SSEDoneEvent",
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "LoginRequest",
    "LoginResponse",
    "TokenPayload",
]
