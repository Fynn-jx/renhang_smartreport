"""
工作流模块
提供各种学术报告处理工作流
"""

from workflows.academic_workflow import AcademicWorkflow
from services.academic_to_official_service import (
    academic_to_official_service,
    WorkflowStage,
    ProgressUpdate,
)

__all__ = [
    "AcademicWorkflow",
    "academic_to_official_service",
    "WorkflowStage",
    "ProgressUpdate",
]
