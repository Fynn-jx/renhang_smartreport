"""
业务常量定义
"""

from enum import Enum


class TaskType(str, Enum):
    """任务类型枚举"""

    ACADEMIC_TO_OFFICIAL = "academic_to_official"  # 学术报告转公文
    TRANSLATION = "translation"  # 公文翻译
    COUNTRY_RESEARCH = "country_research"  # 国别研究
    QUARTERLY_REPORT = "quarterly_report"  # 季度报告
    IMAGE_TRANSLATION = "image_translation"  # 图片转译


class TaskStatus(str, Enum):
    """任务状态枚举"""

    PENDING = "pending"  # 等待中
    RUNNING = "running"  # 运行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    CANCELLED = "cancelled"  # 已取消


class DocumentType(str, Enum):
    """文档类型枚举"""

    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "markdown"
    IMAGE = "image"


class SSEEventType(str, Enum):
    """SSE 事件类型枚举"""

    STATUS = "status"  # 状态更新
    THINKING = "thinking"  # 思维链（DeepSeek-R1）
    CONTENT = "content"  # 正文内容（打字机效果）
    PROGRESS = "progress"  # 进度更新
    ERROR = "error"  # 错误信息
    DONE = "done"  # 完成标记


# 文件类型映射
FILE_TYPE_MAP = {
    "application/pdf": DocumentType.PDF,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": DocumentType.DOCX,
    "text/plain": DocumentType.TXT,
    "text/markdown": DocumentType.MD,
    "image/jpeg": DocumentType.IMAGE,
    "image/png": DocumentType.IMAGE,
    "image/gif": DocumentType.IMAGE,
    "image/webp": DocumentType.IMAGE,
}

# 支持的文件类型
ALLOWED_FILE_TYPES = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "text/markdown",
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
]

# 文档扩展名映射
EXTENSION_MAP = {
    ".pdf": DocumentType.PDF,
    ".docx": DocumentType.DOCX,
    ".txt": DocumentType.TXT,
    ".md": DocumentType.MD,
    ".markdown": DocumentType.MD,
}
