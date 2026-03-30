"""
工作流端点
提供学术报告转公文等工作流的 API 接口
支持 SSE 流式输出进度更新
"""

import uuid
import json
from typing import Optional
from pathlib import Path
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, HTTPException, Request
from fastapi.responses import StreamingResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from core.database import get_db
from api.dependencies import get_current_user_id
from models import Document
from services.file_service import file_service
from services.academic_to_official_service import (
    academic_to_official_service,
    ProgressUpdate,
    WorkflowStage
)
from services.country_research_service import (
    country_research_service,
    ProgressUpdate as CountryProgressUpdate,
    CountryResearchStage
)
from services.quarterly_report_service import (
    quarterly_report_service,
    ProgressUpdate as QuarterlyProgressUpdate,
    QuarterlyReportStage
)
from services.translation_workflow_service import (
    TranslationWorkflowService,
    TranslationProgressUpdate,
    TranslationStage
)
from configs.country_data_sources import CountryDataSourceRegistry

router = APIRouter()


@router.post("/translation/extract")
async def extract_document_content(
    file: UploadFile = File(None, description="文档文件（PDF/TXT）"),
    document_id: str = Form(None, description="已上传文档的ID（与file二选一）"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    提取文档内容（用于翻译前的预览）

    返回PDF/TXT文件的原始文本内容，用户可以编辑和清理后再翻译。

    Returns:
        {
            "content": "提取的文本内容",
            "metadata": {...},
            "stats": {"paragraphs": 10, "chars": 5000}
        }
    """
    from services.translation_workflow_service import TranslationWorkflowService

    translation_service = TranslationWorkflowService()

    # 获取文件内容
    if document_id:
        # 从数据库查询文档
        result = await db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.owner_id == user_id
            )
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在或无权访问")

        file_path = file_service.get_full_path(doc.file_path)
        with open(file_path, "rb") as f:
            file_content = f.read()
        original_filename = doc.original_filename

    elif file:
        file_content = await file.read()
        original_filename = file.filename
    else:
        raise HTTPException(status_code=400, detail="必须提供 file 或 document_id 参数")

    try:
        # 提取文本内容
        extracted_text = await translation_service._extract_text_from_document(
            file_content,
            original_filename
        )

        # 统计信息
        paragraphs = extracted_text.count('\n\n') + 1
        chars = len(extracted_text)

        logger.info(f"[文档提取] 成功: {original_filename}, {chars} 字符, {paragraphs} 段落")

        # 返回提取的内容（使用 ResponseModel 格式）
        from schemas.common import ResponseModel
        return ResponseModel(
            data={
                "content": extracted_text,
                "filename": original_filename,
                "stats": {
                    "paragraphs": paragraphs,
                    "chars": chars,
                    "estimated_time_minutes": max(1, chars / 3000)  # 估算翻译时间
                }
            }
        )

    except Exception as e:
        logger.error(f"[文档提取] 失败: {e}")
        raise HTTPException(status_code=500, detail=f"文档提取失败: {str(e)}")


@router.post("/academic-to-official")
async def run_academic_to_official(
    file: UploadFile = File(None, description="学术报告文件（PDF/TXT）"),
    document_id: str = Form(None, description="已上传文档的ID（与file二选一）"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    执行"学术报告转公文"工作流

    支持 SSE 流式输出，前端可以实时接收处理进度和思维链信息。

    **处理流程：**
    1. 文档提取 - 从上传的文件中提取文本内容
    2. 知识检索 - 从知识库检索相关参考资料
    3. 大纲生成 - 生成公文框架和章节结构
    4. 参数提取 - 提取各章节标题
    5. 章节写作 - 并发写作各章节内容
    6. 模板转换 - 整合各章节
    7. 内容整合 - 进行逻辑检查和语言润色
    8. 最终调整 - 格式规范化调整

    **返回格式（SSE）：**
    ```json
    {
        "stage": "outline_generation",
        "stage_name": "大纲生成",
        "progress": 30.0,
        "message": "正在生成公文大纲...",
        "timestamp": "2024-01-01T12:00:00",
        "data": {...}
    }
    ```

    **前端使用示例：**
    ```javascript
    const response = await fetch('/api/v1/workflows/academic-to-official', {
        method: 'POST',
        body: formData
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\\n');

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = JSON.parse(line.slice(6));
                console.log(data.progress, data.message);
            }
        }
    }
    ```
    """
    async def generate_progress_stream():
        """生成 SSE 进度流"""

        # 获取文件内容和文件名
        if document_id:
            # 从数据库查询文档
            result = await db.execute(
                select(Document).where(
                    Document.id == document_id,
                    Document.owner_id == user_id
                )
            )
            doc = result.scalar_one_or_none()
            if not doc:
                from services.translation_workflow_service import TranslationProgressUpdate, TranslationStage
                error_update = TranslationProgressUpdate(
                    stage=TranslationStage.FAILED,
                    stage_name="failed",
                    progress=-1,
                    message="文档不存在或无权访问",
                    data={"error": "文档不存在"}
                )
                yield error_update.to_sse()
                return

            file_path = file_service.get_full_path(doc.file_path)
            with open(file_path, "rb") as f:
                file_content = f.read()
            original_filename = doc.original_filename

            # 保存文件副本用于工作流处理
            saved_path, _, _ = await file_service.save_file(
                file_content=file_content,
                original_filename=original_filename,
                document_type="document",
            )

            logger.info(f"[工作流] 开始处理文档ID: {document_id}, 文件名: {original_filename}, 路径: {saved_path}")

        elif file:
            file_content = await file.read()
            original_filename = file.filename

            # 保存上传的文件
            saved_path, _, _ = await file_service.save_file(
                file_content=file_content,
                original_filename=original_filename,
                document_type="document",
            )

            logger.info(f"[工作流] 开始处理文件: {original_filename}, 路径: {saved_path}")
        else:
            from services.translation_workflow_service import TranslationProgressUpdate, TranslationStage
            error_update = TranslationProgressUpdate(
                stage=TranslationStage.FAILED,
                stage_name="failed",
                progress=-1,
                message="必须提供 file 或 document_id 参数",
                data={"error": "缺少文件参数"}
            )
            yield error_update.to_sse()
            return

        # 创建一个队列来收集进度更新
        progress_updates = []

        async def progress_callback(update: ProgressUpdate):
            """收集进度更新"""
            progress_updates.append(update)

        try:
            # 执行工作流
            async for update in academic_to_official_service.process_academic_to_official(
                file_path=saved_path,
                progress_callback=progress_callback,
                db=db,
            ):
                # 流式发送每个进度更新
                yield update.to_sse()

        except Exception as e:
            logger.error(f"[工作流] 处理失败: {e}")
            error_update = ProgressUpdate(
                stage=WorkflowStage.FAILED,
                stage_name="failed",
                progress=-1,
                message=f"处理失败: {str(e)}",
                data={"error": str(e)}
            )
            yield error_update.to_sse()

    return StreamingResponse(
        generate_progress_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # 禁用 Nginx 缓冲
        }
    )


@router.post("/academic-to-official/sync")
async def run_academic_to_official_sync(
    file: UploadFile = File(None, description="学术报告文件（PDF/TXT）"),
    document_id: str = Form(None, description="已上传文档的ID（与file二选一）"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    执行"学术报告转公文"工作流（同步版本）

    适用于不需要实时进度的场景，返回最终结果。

    **参数：**
    - `file`: 上传的文件（可选）
    - `document_id`: 已上传文档的ID（可选，与file二选一）

    **返回格式：**
    ```json
    {
        "success": true,
        "final_content": "转换后的公文内容",
        "stats": {
            "original_length": 10000,
            "final_length": 8000,
            "chapter_count": 5
        }
    }
    ```
    """
    # 获取文件内容和文件名
    if document_id:
        # 从数据库查询文档
        result = await db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.owner_id == user_id
            )
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在或无权访问")

        file_path = file_service.get_full_path(doc.file_path)
        with open(file_path, "rb") as f:
            file_content = f.read()
        original_filename = doc.original_filename

        # 保存文件副本用于工作流处理
        saved_path, _, _ = await file_service.save_file(
            file_content=file_content,
            original_filename=original_filename,
            document_type="document",
        )

        logger.info(f"[工作流] 开始同步处理文档ID: {document_id}, 文件名: {original_filename}")

    elif file:
        file_content = await file.read()
        original_filename = file.filename

        # 保存上传的文件
        saved_path, _, _ = await file_service.save_file(
            file_content=file_content,
            original_filename=original_filename,
            document_type="document",
        )

        logger.info(f"[工作流] 开始同步处理文件: {original_filename}")
    else:
        raise HTTPException(status_code=400, detail="必须提供 file 或 document_id")

    # 收集所有进度更新
    progress_updates = []

    async def collect_progress(update: ProgressUpdate):
        progress_updates.append(update)

    try:
        # 执行工作流
        context = await academic_to_official_service.process_academic_to_official(
            file_path=saved_path,
            progress_callback=collect_progress,
            db=db,
        )

        # 获取最终结果
        final_update = progress_updates[-1] if progress_updates else None

        return {
            "success": True,
            "final_content": context.get("final_content", ""),
            "stats": final_update.data.get("stats", {}) if final_update else {},
            "progress_history": [
                {
                    "stage": u.stage.value,
                    "message": u.message,
                    "progress": u.progress,
                }
                for u in progress_updates
            ]
        }

    except Exception as e:
        logger.error(f"[工作流] 同步处理失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "progress_history": [
                {
                    "stage": u.stage.value,
                    "message": u.message,
                    "progress": u.progress,
                }
                for u in progress_updates
            ]
        }


@router.get("/academic-to-official/stages")
async def get_workflow_stages():
    """
    获取工作流的所有阶段信息

    用于前端显示处理进度条和阶段说明。

    **返回格式：**
    ```json
    {
        "stages": [
            {
                "value": "doc_extraction",
                "name": "文档提取",
                "description": "从上传文件中提取文本内容"
            },
            ...
        ]
    }
    ```
    """
    return {
        "stages": [
            {
                "value": WorkflowStage.DOCUMENT_EXTRACTION.value,
                "name": "文档提取",
                "description": "从上传文件中提取文本内容",
                "icon": "📄"
            },
            {
                "value": WorkflowStage.KNOWLEDGE_RETRIEVAL.value,
                "name": "知识检索",
                "description": "从知识库检索相关参考资料",
                "icon": "🔍"
            },
            {
                "value": WorkflowStage.OUTLINE_GENERATION.value,
                "name": "大纲生成",
                "description": "生成公文框架和章节结构",
                "icon": "📋"
            },
            {
                "value": WorkflowStage.PARAMETER_EXTRACTION.value,
                "name": "参数提取",
                "description": "提取各章节标题",
                "icon": "🔖"
            },
            {
                "value": WorkflowStage.CHAPTER_WRITING.value,
                "name": "章节写作",
                "description": "并发写作各章节内容",
                "icon": "✍️"
            },
            {
                "value": WorkflowStage.TEMPLATE_TRANSFORM.value,
                "name": "模板转换",
                "description": "整合各章节内容",
                "icon": "🔄"
            },
            {
                "value": WorkflowStage.CONTENT_INTEGRATION.value,
                "name": "内容整合",
                "description": "进行逻辑检查和语言润色",
                "icon": "🔧"
            },
            {
                "value": WorkflowStage.FINAL_ADJUSTMENT.value,
                "name": "最终调整",
                "description": "格式规范化调整",
                "icon": "✨"
            },
        ]
    }


@router.post("/translation/text")
async def translate_text_content(
    content: str = Form(..., description="待翻译的文本内容"),
    source_language: str = Form(default="auto", description="源语言"),
    target_language: str = Form(default="zh", description="目标语言"),
    model: str = Form(default="deepseek-ai/DeepSeek-V3", description="翻译模型"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    翻译用户确认后的文本内容

    接收用户编辑确认后的文本，进行对照翻译。
    支持 SSE 流式输出进度更新。

    **使用场景：**
    1. 用户先调用 /translation/extract 提取文档内容
    2. 用户预览和编辑提取的文本
    3. 用户调用本接口开始翻译

    **请求参数：**
    - content: 用户确认后的文本内容

    **返回格式（SSE）：**
    ```
    data: {"stage": "translating", "progress": 50.0, "message": "正在翻译...", "data": {...}}
    ```
    """
    from services.translation_workflow_service import TranslationWorkflowService

    translation_service = TranslationWorkflowService()

    async def generate_progress_stream():
        """生成 SSE 进度流"""

        # 强制输出调试信息
        print(f"\n{'='*60}")
        print(f"[翻译工作流] 开始翻译用户提供的文本")
        print(f"[翻译工作流] 文本长度: {len(content)} 字符")
        print(f"{'='*60}\n")

        try:
            # 导入翻译服务
            from services.translation_workflow_service import TranslationStage

            # 执行翻译工作流（直接传入文本）
            async for update in translation_service.process_translation(
                file_content=content.encode('utf-8'),  # 文本转为字节
                original_filename="user_edited_text.txt",
                source_language=source_language,
                target_language=target_language,
                model=model,
                progress_callback=None,
                db=db,
            ):
                # 流式发送每个进度更新
                if isinstance(update, str):
                    yield update
                else:
                    yield update.to_sse()

        except Exception as e:
            logger.error(f"[翻译工作流] 处理失败: {e}")
            from services.translation_workflow_service import TranslationProgressUpdate, TranslationStage
            error_update = TranslationProgressUpdate(
                stage=TranslationStage.FAILED,
                stage_name="failed",
                progress=-1,
                message=f"处理失败: {str(e)}",
                data={"error": str(e)}
            )
            yield error_update.to_sse()
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate_progress_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/translation")
async def run_translation(
    file: UploadFile = File(None, description="文档文件（PDF/TXT）"),
    document_id: str = Form(None, description="已上传文档的ID（与file二选一）"),
    source_language: str = Form(default="auto", description="源语言"),
    target_language: str = Form(default="zh", description="目标语言"),
    model: str = Form(default="deepseek-ai/DeepSeek-V3", description="翻译模型"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    执行"公文对照翻译"工作流

    支持 SSE 流式输出，前端可以实时接收处理进度。

    **处理流程：**
    1. 文档提取 - 从上传的文件中提取文本内容
    2. 文本分析 - 分析文本长度和结构
    3. 翻译处理 - 调用 DeepSeek API 进行对照翻译
    4. 结果整理 - 格式化翻译结果

    **返回格式（SSE）：**
    ```json
    {
        "stage": "translating",
        "stage_name": "翻译处理",
        "progress": 50.0,
        "message": "正在翻译第 2/3 段...",
        "timestamp": "2024-01-01T12:00:00",
        "data": {...}
    }
    ```
    """
    async def generate_progress_stream():
        """生成 SSE 进度流"""

        # 强制输出调试信息
        print(f"\n{'='*60}")
        print(f"[翻译工作流] generate_progress_stream 开始执行")
        print(f"[翻译工作流] document_id: {document_id}")
        print(f"[翻译工作流] file: {file.filename if file else None}")
        print(f"{'='*60}\n")

        # 获取文件内容和文件名
        if document_id:
            # 从数据库查询文档
            logger.info(f"[翻译工作流] 使用 document_id 参数: {document_id}")
            result = await db.execute(
                select(Document).where(
                    Document.id == document_id,
                    Document.owner_id == user_id
                )
            )
            doc = result.scalar_one_or_none()
            if not doc:
                from services.translation_workflow_service import TranslationProgressUpdate, TranslationStage
                error_update = TranslationProgressUpdate(
                    stage=TranslationStage.FAILED,
                    stage_name="failed",
                    progress=-1,
                    message="文档不存在或无权访问",
                    data={"error": "文档不存在"}
                )
                yield error_update.to_sse()
                return

            file_path = file_service.get_full_path(doc.file_path)
            logger.info(f"[翻译工作流] 文件路径: {file_path}")
            logger.info(f"[翻译工作流] 文件是否存在: {Path(file_path).exists()}")

            with open(file_path, "rb") as f:
                file_content = f.read()

            logger.info(f"[翻译工作流] 读取文件大小: {len(file_content)} bytes")
            original_filename = doc.original_filename
            logger.info(f"[翻译工作流] 开始处理文档ID: {document_id}, 文件名: {original_filename}")

        elif file:
            file_content = await file.read()
            original_filename = file.filename
            logger.info(f"[翻译工作流] 使用 file 参数，直接上传文件: {original_filename}")
            logger.info(f"[翻译工作流] 文件大小: {len(file_content)} bytes")

            # 保存上传的文件
            saved_path, _, _ = await file_service.save_file(
                file_content=file_content,
                original_filename=original_filename,
                document_type="document",
            )
        else:
            from services.translation_workflow_service import TranslationProgressUpdate, TranslationStage
            error_update = TranslationProgressUpdate(
                stage=TranslationStage.FAILED,
                stage_name="failed",
                progress=-1,
                message="必须提供 file 或 document_id 参数",
                data={"error": "缺少文件参数"}
            )
            yield error_update.to_sse()
            return

        try:
            # 导入翻译服务
            from services.translation_workflow_service import TranslationWorkflowService
            from services.translation_workflow_service import TranslationStage

            translation_service = TranslationWorkflowService()

            # 定义进度回调
            async def progress_callback(update):
                """发送进度更新"""
                yield update.to_sse()

            # 执行翻译工作流
            async for update in translation_service.process_translation(
                file_content=file_content,
                original_filename=original_filename,
                source_language=source_language,
                target_language=target_language,
                model=model,
                progress_callback=None,
                db=db,
            ):
                # 流式发送每个进度更新
                # 如果是字符串（SSE结束信号），直接发送；否则调用 to_sse()
                if isinstance(update, str):
                    yield update
                else:
                    yield update.to_sse()

        except Exception as e:
            logger.error(f"[翻译工作流] 处理失败: {e}")
            from services.translation_workflow_service import TranslationProgressUpdate, TranslationStage
            error_update = TranslationProgressUpdate(
                stage=TranslationStage.FAILED,
                stage_name="failed",
                progress=-1,
                message=f"处理失败: {str(e)}",
                data={"error": str(e)}
            )
            yield error_update.to_sse()

    return StreamingResponse(
        generate_progress_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/country-research")
async def run_country_research(
    country_code: str = Form(..., description="国家代码 (如 EG, KE, NG)"),
    reference_file: Optional[UploadFile] = File(None, description="参考文件（可选）"),
    user_sources: Optional[str] = Form(None, description="用户补充数据源JSON数组（可选）"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    执行"国别研究"工作流

    支持数据源插拔式切换，提供关键节点思维链输出。

    **处理流程：**
    1. 配置加载 - 加载目标国家的数据源配置
    2. 数据采集 - 并发抓取各数据源内容（使用Firecrawl）
    3. 经济分析 - 分析GDP、通胀、货币政策等
    4. 政治分析 - 分析国家元首、政治体制
    5. 外交分析 - 重点分析对华关系
    6. 报告生成 - 整合分析结果生成报告
    7. 质量审核 - 检查完整性和规范性

    **参数：**
    - `country_code`: 国家代码 (EG=埃及, KE=肯尼亚, NG=尼日利亚 等)
    - `reference_file`: 参考文件（可选）
    - `user_sources`: 用户补充数据源，JSON数组格式
      ```json
      [
        {"name": "数据源名称", "url": "https://example.com"},
        {"name": "央行报告", "url": "https://centralbank.example.com/report"}
      ]
      ```

    **返回格式（SSE）：**
    ```json
    {
        "stage": "data_fetching",
        "stage_name": "数据采集",
        "progress": 15.0,
        "message": "正在采集: GDP增速",
        "timestamp": "2024-01-01T12:00:00",
        "thinking_node": {
            "stage": "data_fetching",
            "node_id": "fetch_0",
            "title": "采集数据源: GDP增速",
            "content": "URL: ...",
            "timestamp": "2024-01-01T12:00:00",
            "metadata": {...}
        }
    }
    ```
    """
    async def generate_progress_stream():
        """生成 SSE 进度流"""

        # 处理参考文件
        reference_path = None
        if reference_file:
            file_content = await reference_file.read()
            reference_path, _, _ = await file_service.save_file(
                file_content=file_content,
                original_filename=reference_file.filename,
                document_type="document",
            )

        # 解析用户补充数据源
        user_sources_list = None
        if user_sources:
            try:
                import json
                user_sources_list = json.loads(user_sources)
                logger.info(f"[国别研究] 用户补充 {len(user_sources_list)} 个数据源")
            except json.JSONDecodeError as e:
                logger.error(f"[国别研究] 解析user_sources失败: {e}")

        logger.info(f"[国别研究] 开始处理国家代码: {country_code}")

        try:
            # 执行工作流
            async for update in country_research_service.process_country_research(
                country_code=country_code,
                reference_file=reference_path,
                user_sources=user_sources_list,
                progress_callback=None,
                db=db,
            ):
                # 流式发送每个进度更新
                yield update.to_sse()

        except Exception as e:
            logger.error(f"[国别研究] 处理失败: {e}")
            error_update = CountryProgressUpdate(
                stage=CountryResearchStage.FAILED,
                stage_name="failed",
                progress=-1,
                message=f"处理失败: {str(e)}",
                data={"error": str(e)}
            )
            yield error_update.to_sse()

    return StreamingResponse(
        generate_progress_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/country-research/countries")
async def list_countries():
    """
    获取所有已注册的国家列表

    用于前端显示国家选择器。

    **返回格式：**
    ```json
    {
        "countries": [
            {
                "code": "EG",
                "name": "埃及",
                "name_en": "Egypt",
                "region": "中东, 北非",
                "income_level": "中等收入",
                "currency": "EGP",
                "data_source_count": 18
            },
            ...
        ]
    }
    ```
    """
    return {
        "countries": CountryDataSourceRegistry.list_countries()
    }


@router.get("/country-research/countries/{country_code}")
async def get_country_detail(country_code: str):
    """
    获取指定国家的详细配置

    用于前端显示数据源详情。

    **返回格式：**
    ```json
    {
        "country_code": "EG",
        "country_name": "埃及",
        "data_sources": [
            {
                "name": "GDP增速",
                "type": "trading_economics",
                "url": "...",
                "label": "GDP增速 (Trading Economics)",
                "enabled": true
            },
            ...
        ]
    }
    ```
    """
    country = CountryDataSourceRegistry.get_country(country_code)
    if not country:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"未找到国家代码: {country_code}")

    return {
        "country_code": country.country_code,
        "country_name": country.country_name,
        "country_name_en": country.country_name_en,
        "region": country.region,
        "income_level": country.income_level,
        "currency": country.currency,
        "data_sources": [
            {
                "name": ds.name,
                "type": ds.type.value,
                "url": ds.url,
                "label": ds.label,
                "description": ds.description,
                "enabled": ds.enabled,
                "data_format": ds.data_format
            }
            for ds in country.data_sources
        ]
    }


@router.get("/country-research/stages")
async def get_country_research_stages():
    """
    获取国别研究工作流的所有阶段信息

    用于前端显示处理进度条和阶段说明。
    """
    return {
        "stages": [
            {
                "value": CountryResearchStage.CONFIG_LOADING.value,
                "name": "配置加载",
                "description": "加载目标国家的数据源配置",
                "icon": "⚙️"
            },
            {
                "value": CountryResearchStage.DATA_FETCHING.value,
                "name": "数据采集",
                "description": "并发抓取各数据源内容",
                "icon": "🌐"
            },
            {
                "value": CountryResearchStage.ECONOMIC_ANALYSIS.value,
                "name": "经济分析",
                "description": "分析GDP、通胀、货币政策等",
                "icon": "📊"
            },
            {
                "value": CountryResearchStage.POLITICAL_ANALYSIS.value,
                "name": "政治分析",
                "description": "分析国家元首、政治体制",
                "icon": "🏛️"
            },
            {
                "value": CountryResearchStage.DIPLOMACY_ANALYSIS.value,
                "name": "外交分析",
                "description": "重点分析对华关系",
                "icon": "🤝"
            },
            {
                "value": CountryResearchStage.REPORT_GENERATION.value,
                "name": "报告生成",
                "description": "整合分析结果生成报告",
                "icon": "📝"
            },
            {
                "value": CountryResearchStage.QUALITY_REVIEW.value,
                "name": "质量审核",
                "description": "检查完整性和规范性",
                "icon": "✅"
            },
        ]
    }


@router.post("/quarterly-report")
async def run_quarterly_report(
    country_code: str = Form(..., description="国家代码 (如 EG, KE, NG)"),
    reference_file: Optional[UploadFile] = File(None, description="参考文件（可选）"),
    user_sources: Optional[str] = Form(None, description="用户补充数据源JSON数组（可选）"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    执行"季度报告"工作流

    支持动态国家选择、用户数据源、思维链输出。

    **处理流程：**
    1. 配置加载 - 加载目标国家的数据源配置
    2. 数据采集 - 并发抓取各数据源内容（使用Firecrawl）
    3. 宏观经济分析 - 分析GDP、通胀、就业、外贸等实体经济指标
    4. 金融市场分析 - 分析股市、债市、汇率等金融市场指标
    5. 政策分析 - 分析货币政策、财政政策动向
    6. 风险评估 - 评估经济前景与潜在风险
    7. 报告生成 - 整合分析结果生成季度报告
    8. 质量审核 - 检查完整性和规范性

    **参数：**
    - `country_code`: 国家代码 (EG=埃及, KE=肯尼亚, NG=尼日利亚 等)
    - `reference_file`: 参考文件（可选），用于参考报告风格
    - `user_sources`: 用户补充数据源，JSON数组格式
      ```json
      [
        {"name": "数据源名称", "url": "https://example.com"},
        {"name": "央行报告", "url": "https://centralbank.example.com/report"}
      ]
      ```

    **返回格式（SSE）：**
    ```json
    {
        "stage": "macro_analysis",
        "stage_name": "宏观经济分析",
        "progress": 35.0,
        "message": "正在进行宏观经济分析...",
        "timestamp": "2024-01-01T12:00:00",
        "thinking_node": {
            "stage": "macro_analysis",
            "node_id": "macro_analysis_start",
            "title": "宏观经济分析启动",
            "content": "开始分析埃及的实体经济运行情况...",
            "timestamp": "2024-01-01T12:00:00",
            "metadata": {"analysis_type": "macro_economic"}
        }
    }
    ```
    """
    async def generate_progress_stream():
        """生成 SSE 进度流"""

        # 处理参考文件
        reference_path = None
        if reference_file:
            file_content = await reference_file.read()
            reference_path, _, _ = await file_service.save_file(
                file_content=file_content,
                original_filename=reference_file.filename,
                document_type="document",
            )

        # 解析用户补充数据源
        user_sources_list = None
        if user_sources:
            try:
                user_sources_list = json.loads(user_sources)
                logger.info(f"[季度报告] 用户补充 {len(user_sources_list)} 个数据源")
            except json.JSONDecodeError as e:
                logger.error(f"[季度报告] 解析user_sources失败: {e}")

        logger.info(f"[季度报告] 开始处理国家代码: {country_code}")

        try:
            # 执行工作流
            async for update in quarterly_report_service.process_quarterly_report(
                country_code=country_code,
                reference_file=reference_path,
                user_sources=user_sources_list,
                progress_callback=None,
                db=db,
            ):
                # 流式发送每个进度更新
                yield update.to_sse()

        except Exception as e:
            logger.error(f"[季度报告] 处理失败: {e}")
            error_update = QuarterlyProgressUpdate(
                stage=QuarterlyReportStage.FAILED,
                stage_name="failed",
                progress=-1,
                message=f"处理失败: {str(e)}",
                data={"error": str(e)}
            )
            yield error_update.to_sse()

    return StreamingResponse(
        generate_progress_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/quarterly-report/stages")
async def get_quarterly_report_stages():
    """
    获取季度报告工作流的所有阶段信息

    用于前端显示处理进度条和阶段说明。

    **返回格式：**
    ```json
    {
        "stages": [
            {
                "value": "config_loading",
                "name": "配置加载",
                "description": "加载目标国家的数据源配置",
                "icon": "⚙️"
            },
            ...
        ]
    }
    ```
    """
    return {
        "stages": [
            {
                "value": QuarterlyReportStage.CONFIG_LOADING.value,
                "name": "配置加载",
                "description": "加载目标国家的数据源配置",
                "icon": "⚙️"
            },
            {
                "value": QuarterlyReportStage.DATA_FETCHING.value,
                "name": "数据采集",
                "description": "并发抓取各数据源内容",
                "icon": "🌐"
            },
            {
                "value": QuarterlyReportStage.MACRO_ANALYSIS.value,
                "name": "宏观经济分析",
                "description": "分析GDP、通胀、就业、外贸等实体经济指标",
                "icon": "📊"
            },
            {
                "value": QuarterlyReportStage.FINANCIAL_MARKET_ANALYSIS.value,
                "name": "金融市场分��",
                "description": "分析股市、债市、汇率等金融市场指标",
                "icon": "📈"
            },
            {
                "value": QuarterlyReportStage.POLICY_ANALYSIS.value,
                "name": "政策分析",
                "description": "分析货币政策、财政政策动向",
                "icon": "🏛️"
            },
            {
                "value": QuarterlyReportStage.RISK_ASSESSMENT.value,
                "name": "风险评估",
                "description": "评估经济前景与潜在风险",
                "icon": "⚠️"
            },
            {
                "value": QuarterlyReportStage.REPORT_GENERATION.value,
                "name": "报告生成",
                "description": "整合分析结果生成季度报告",
                "icon": "📝"
            },
            {
                "value": QuarterlyReportStage.QUALITY_REVIEW.value,
                "name": "质量审核",
                "description": "检查完整性和规范性",
                "icon": "✅"
            },
        ]
    }


@router.post("/image-translation")
async def run_image_translation(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    执行"图片转译"工作流

    使用 OpenRouter 的视觉模型
    """
    # TODO: 实现图片转译工作流
    return {
        "message": "待实现",
    }


@router.post("/mineru-parse")
async def mineru_parse(
    file: UploadFile = File(..., description="PDF文件"),
    model_version: str = Form("vlm", description="模型版本: vlm 或 pipeline"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    使用MinerU精准解析API将PDF转换为Markdown

    支持去除页眉、页脚、脚注，保留文档结构

    **参数：**
    - `file`: PDF文件（必填，最大200MB）
    - `model_version`: 模型版本，vlm（推荐）或 pipeline

    **返回格式（SSE）：**
    ```
    data: {"stage": "uploading", "progress": 10.0, "message": "上传文件..."}
    data: {"stage": "submitting", "progress": 30.0, "message": "提交解析任务..."}
    data: {"stage": "processing", "progress": 50.0, "message": "正在解析PDF..."}
    data: {"stage": "downloading", "progress": 90.0, "message": "下载解析结果..."}
    data: {"stage": "done", "progress": 100.0, "message": "解析完成"}
    ```
    """
    from services.mineru_service import MineruProgressUpdate

    async def generate_progress_stream():
        """生成 SSE 进度流"""
        try:
            # 保存上传的文件
            file_content = await file.read()
            original_filename = file.filename

            saved_path, _, _ = await file_service.save_file(
                file_content=file_content,
                original_filename=original_filename,
                document_type="document",
            )

            logger.info(f"[MinerU] 开始解析文件: {original_filename}, 路径: {saved_path}")

            # 调用MinerU服务
            from services.mineru_service import mineru_service

            async def progress_callback(update: MineruProgressUpdate):
                yield f"data: {update.to_dict()}\n\n"

            async for sse_data in mineru_service.parse_pdf_to_markdown(
                file_path=saved_path,
                progress_callback=progress_callback,
                model_version=model_version,
            ):
                yield sse_data

            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"[MinerU] 解析失败: {e}")
            error_update = MineruProgressUpdate(
                stage="failed",
                progress=-1,
                message=f"解析失败: {str(e)}",
                data={"error": str(e)}
            )
            yield f"data: {error_update.to_dict()}\n\n"

    return StreamingResponse(
        generate_progress_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/mineru-parse/url")
async def mineru_parse_url(
    request: Request,
    model_version: str = Form("vlm", description="模型版本: vlm 或 pipeline"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    使用MinerU精准解析API将URL的PDF转换为Markdown

    **参数：**
    - `pdf_url`: PDF的URL地址（必填）

    **返回格式（SSE）：**
    ```
    data: {"stage": "submitting", "progress": 20.0, "message": "提交解析任务..."}
    data: {"stage": "processing", "progress": 40.0, "message": "正在解析PDF..."}
    data: {"stage": "downloading", "progress": 80.0, "message": "下载解析结果..."}
    data: {"stage": "done", "progress": 100.0, "message": "解析完成"}
    ```
    """
    from services.mineru_service import MineruProgressUpdate

    try:
        body = await request.json()
        pdf_url = body.get("pdf_url")
        if not pdf_url:
            return {"success": False, "error": "pdf_url is required"}
    except:
        return {"success": False, "error": "Invalid JSON body"}

    async def generate_progress_stream():
        """生成 SSE 进度流"""
        try:
            from services.mineru_service import mineru_service

            logger.info(f"[MinerU-URL] 开始解析URL: {pdf_url}")

            async def progress_callback(update: MineruProgressUpdate):
                yield f"data: {update.to_dict()}\n\n"

            async for sse_data in mineru_service.parse_pdf_by_url(
                pdf_url=pdf_url,
                progress_callback=progress_callback,
                model_version=model_version,
            ):
                yield sse_data

            yield "data: [DONE]\n\n"

        except Exception as e:
            logger.error(f"[MinerU-URL] 解析失败: {e}")
            error_update = MineruProgressUpdate(
                stage="failed",
                progress=-1,
                message=f"解析失败: {str(e)}",
                data={"error": str(e)}
            )
            yield f"data: {error_update.to_dict()}\n\n"

    return StreamingResponse(
        generate_progress_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/mineru-parse/url/sync")
async def mineru_parse_url_sync(
    request: Request,
    model_version: str = Form("vlm", description="模型版本: vlm 或 pipeline"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    使用MinerU精准解析API将URL的PDF转换为Markdown（同步版本）

    **参数：**
    - `pdf_url`: PDF的URL地址（必填）

    **返回：**
    ```json
    {
        "success": true,
        "content": "Markdown内容",
        "stats": {"chars": 5000}
    }
    ```
    """
    from services.mineru_service import mineru_service

    try:
        body = await request.json()
        pdf_url = body.get("pdf_url")
        if not pdf_url:
            return {"success": False, "error": "pdf_url is required"}
    except:
        return {"success": False, "error": "Invalid JSON body"}

    try:
        logger.info(f"[MinerU-URL-SYNC] 开始解析URL: {pdf_url}")

        content = await mineru_service.parse_pdf_by_url(
            pdf_url=pdf_url,
            progress_callback=None,
            model_version=model_version,
        )

        return {
            "success": True,
            "content": content,
            "stats": {
                "chars": len(content),
            }
        }

    except Exception as e:
        logger.error(f"[MinerU-URL-SYNC] 解析失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/mineru-parse/sync")
async def mineru_parse_sync(
    file: UploadFile = File(..., description="PDF文件"),
    model_version: str = Form("vlm", description="模型版本: vlm 或 pipeline"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    使用MinerU精准解析API将PDF转换为Markdown（同步版本）

    **参数：**
    - `file`: PDF文件
    - `model_version`: 模型版本

    **返回：**
    ```json
    {
        "success": true,
        "content": "Markdown内容",
        "stats": {"chars": 5000, "pages": 10}
    }
    ```
    """
    from services.mineru_service import mineru_service

    try:
        # 保存上传的文件
        file_content = await file.read()
        original_filename = file.filename

        saved_path, _, _ = await file_service.save_file(
            file_content=file_content,
            original_filename=original_filename,
            document_type="document",
        )

        logger.info(f"[MinerU-SYNC] 开始解析文件: {original_filename}")

        # 调用MinerU服务
        content = await mineru_service.parse_pdf_to_markdown(
            file_path=saved_path,
            progress_callback=None,
            model_version=model_version,
        )

        return {
            "success": True,
            "content": content,
            "filename": original_filename,
            "stats": {
                "chars": len(content),
                "estimated_pages": len(content) // 3000  # 估算
            }
        }

    except Exception as e:
        logger.error(f"[MinerU-SYNC] 解析失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/academic-to-official/export-word")
async def export_to_word(
    content: str = Form(..., description="Markdown格式的内容"),
    filename: str = Form(..., description="输出文件名"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    将Markdown内容导出为Word文档

    **请求格式：**
    ```
    POST /api/v1/workflows/academic-to-official/export-word
    Content-Type: multipart/form-data

    content: <Markdown内容>
    filename: <文件名.docx>
    ```

    **返回：**
    - Word文档文件流
    """
    try:
        from utils.markdown_to_word import MarkdownToWordConverter

        converter = MarkdownToWordConverter()
        doc_bytes = converter.convert(content)

        # 确保文件名以.docx结尾
        if not filename.endswith('.docx'):
            filename = filename.rsplit('.', 1)[0] + '.docx'

        return Response(
            content=doc_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )

    except ImportError as e:
        logger.error(f"[ERROR] Word导出失败: {e}")
        return {
            "success": False,
            "error": "Word导出功能不可用，请安装 python-docx"
        }
    except Exception as e:
        logger.error(f"[ERROR] Word导出失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/academic-to-official/sync-with-word")
async def run_academic_to_official_sync_with_word(
    file: UploadFile = File(None, description="学术报告文件（PDF/TXT）"),
    document_id: str = Form(None, description="已上传文档的ID（与file二选一）"),
    export_format: str = Query("markdown", description="输出格式: markdown 或 word"),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """
    执行"学术报告转公文"工作流并导出

    支持导出为 Markdown 或 Word 格式。

    **参数：**
    - `file`: 上传的文件（可选）
    - `document_id`: 已上传文档的ID（可选，与file二选一）
    - `export_format`: 输出格式（markdown 或 word）

    **返回格式（Markdown）：**
    ```json
    {
        "success": true,
        "final_content": "转换后的公文内容",
        ...
    }
    ```

    **返回格式（Word）：**
    - 直接返回 Word 文档文件流
    """
    # 获取文件内容和文件名
    if document_id:
        # 从数据库查询文档
        result = await db.execute(
            select(Document).where(
                Document.id == document_id,
                Document.owner_id == user_id
            )
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=404, detail="文档不存在或无权访问")

        file_path = file_service.get_full_path(doc.file_path)
        with open(file_path, "rb") as f:
            file_content = f.read()
        original_filename = doc.original_filename

        # 保存文件副本用于工作流处理
        saved_path, _, _ = await file_service.save_file(
            file_content=file_content,
            original_filename=original_filename,
            document_type="document",
        )

        logger.info(f"[工作流] 开始同步处理文档ID: {document_id}, 导出格式: {export_format}")

    elif file:
        file_content = await file.read()
        original_filename = file.filename

        # 保存上传的文件
        saved_path, _, _ = await file_service.save_file(
            file_content=file_content,
            original_filename=original_filename,
            document_type="document",
        )

        logger.info(f"[工作流] 开始同步处理文件: {original_filename}, 导出格式: {export_format}")
    else:
        raise HTTPException(status_code=400, detail="必须提供 file 或 document_id")

    progress_updates = []

    async def collect_progress(update: ProgressUpdate):
        progress_updates.append(update)

    try:
        # 执行工作流
        context = await academic_to_official_service.process_academic_to_official(
            file_path=saved_path,
            progress_callback=collect_progress,
            db=db,
        )

        final_content = context.get("final_content", "")

        # 根据导出格式返回结果
        if export_format.lower() == "word":
            # 导出为Word
            from utils.markdown_to_word import MarkdownToWordConverter

            converter = MarkdownToWordConverter()
            doc_bytes = converter.convert(final_content)

            # 生成文件名
            output_filename = Path(original_filename).stem + "_converted.docx"

            return Response(
                content=doc_bytes,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={
                    "Content-Disposition": f'attachment; filename="{output_filename}"'
                }
            )
        else:
            # 返回Markdown内容
            final_update = progress_updates[-1] if progress_updates else None

            return {
                "success": True,
                "final_content": final_content,
                "stats": final_update.data.get("stats", {}) if final_update else {},
                "progress_history": [
                    {
                        "stage": u.stage.value,
                        "message": u.message,
                        "progress": u.progress,
                    }
                    for u in progress_updates
                ]
            }

    except Exception as e:
        logger.error(f"[工作流] 处理失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "progress_history": [
                {
                    "stage": u.stage.value,
                    "message": u.message,
                    "progress": u.progress,
                }
                for u in progress_updates
            ]
        }
