"""
学术报告处理工作流
高级封装，提供更简洁的调用接口
"""

from typing import Optional, Callable, Dict, Any, AsyncIterator
from pathlib import Path
from loguru import logger

from sqlalchemy.ext.asyncio import AsyncSession

from services.academic_to_official_service import (
    academic_to_official_service,
    ProgressUpdate,
    WorkflowStage,
)


class AcademicWorkflow:
    """
    学术报告处理工作流

    提供更高级的封装，支持多种调用方式：
    - 同步调用：等待完整结果返回
    - 异步流式：实时接收进度更新
    - 回调模式：通过回调函数处理进度
    """

    def __init__(self):
        """初始化工作流"""
        self.service = academic_to_official_service

    async def convert_to_official(
        self,
        file_path: str,
        db: Optional[AsyncSession] = None,
        progress_callback: Optional[Callable[[ProgressUpdate], None]] = None,
    ) -> Dict[str, Any]:
        """
        转换学术报告为公文（同步模式）

        Args:
            file_path: 输入文件路径
            db: 数据库会话（可选）
            progress_callback: 进度回调函数（可选）

        Returns:
            包含最终结果和统计信息的字典
        """
        logger.info(f"[工作流] 开始转换: {file_path}")

        context = await self.service.process_academic_to_official(
            file_path=file_path,
            progress_callback=progress_callback,
            db=db,
        )

        # 提取最终结果
        result = {
            "success": True,
            "final_content": context.get("final_content", ""),
            "outline": context.get("outline", ""),
            "chapters_count": len(context.get("chapters_content", [])),
            "stats": {
                "original_length": len(context.get("original_text", "")),
                "final_length": len(context.get("final_content", "")),
                "chapter_count": len(context.get("chapters_content", [])),
            }
        }

        logger.info(f"[工作流] 转换完成")
        return result

    async def convert_to_official_stream(
        self,
        file_path: str,
        db: Optional[AsyncSession] = None,
    ) -> AsyncIterator[ProgressUpdate]:
        """
        转换学术报告为公文（流式模式）

        Args:
            file_path: 输入文件路径
            db: 数据库会话（可选）

        Yields:
            ProgressUpdate: 进度更新
        """
        logger.info(f"[工作流] 开始流式转换: {file_path}")

        async for update in self.service.process_academic_to_official(
            file_path=file_path,
            progress_callback=None,
            db=db,
        ):
            yield update

        logger.info(f"[工作流] 流式转换完成")

    def get_stages(self) -> list[Dict[str, str]]:
        """
        获取工作流的所有阶段信息

        Returns:
            阶段信息列表
        """
        return [
            {
                "value": WorkflowStage.DOCUMENT_EXTRACTION.value,
                "name": "文档提取",
                "description": "从上传文件中提取文本内容",
                "icon": "📄",
                "progress_range": [5, 10],
            },
            {
                "value": WorkflowStage.KNOWLEDGE_RETRIEVAL.value,
                "name": "知识检索",
                "description": "从知识库检索相关参考资料",
                "icon": "🔍",
                "progress_range": [15, 20],
            },
            {
                "value": WorkflowStage.OUTLINE_GENERATION.value,
                "name": "大纲生成",
                "description": "生成公文框架和章节结构",
                "icon": "📋",
                "progress_range": [25, 30],
            },
            {
                "value": WorkflowStage.PARAMETER_EXTRACTION.value,
                "name": "参数提取",
                "description": "提取各章节标题",
                "icon": "🔖",
                "progress_range": [35, 40],
            },
            {
                "value": WorkflowStage.CHAPTER_WRITING.value,
                "name": "章节写作",
                "description": "并发写作各章节内容",
                "icon": "✍️",
                "progress_range": [45, 65],
            },
            {
                "value": WorkflowStage.TEMPLATE_TRANSFORM.value,
                "name": "模板转换",
                "description": "整合各章节内容",
                "icon": "🔄",
                "progress_range": [70, 75],
            },
            {
                "value": WorkflowStage.CONTENT_INTEGRATION.value,
                "name": "内容整合",
                "description": "进行逻辑检查和语言润色",
                "icon": "🔧",
                "progress_range": [80, 90],
            },
            {
                "value": WorkflowStage.FINAL_ADJUSTMENT.value,
                "name": "最终调整",
                "description": "格式规范化调整",
                "icon": "✨",
                "progress_range": [92, 95],
            },
        ]

    def get_stage_by_value(self, value: str) -> Optional[Dict[str, str]]:
        """
        根据值获取阶段信息

        Args:
            value: 阶段值

        Returns:
            阶段信息，如果不存在返回 None
        """
        for stage in self.get_stages():
            if stage["value"] == value:
                return stage
        return None


# 单例实例
academic_workflow = AcademicWorkflow()
