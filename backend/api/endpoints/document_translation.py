"""
公文翻译端点
"""

import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models import DocumentTranslation, Document
from models.document_translation import DocumentTranslationStatus
from schemas.document_translation import (
    DocumentTranslationResponse,
    DocumentTranslationUploadResponse,
    DocumentTranslationTextResponse,
)
from schemas.common import ResponseModel
from services.document_translation_service import document_translation_service
from services.file_service import file_service
from utils.markdown_to_word import convert_markdown_to_word
from api.dependencies import get_current_user_id

router = APIRouter()


@router.post("/", response_model=ResponseModel[DocumentTranslationUploadResponse])
async def upload_and_translate_document(
    document_id: Optional[str] = Form(None, description="已有文档 ID（与 file 二选一）"),
    file: Optional[UploadFile] = File(None, description="文档文件"),
    source_language: str = Form(default="auto", description="源语言（auto自动检测）"),
    target_language: str = Form(default="zh", description="目标语言（zh中文）"),
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """
    上传文档或从已有文档创建翻译任务

    支持两种方式：
    1. 上传新文件（file 参数）
    2. 使用已有文档（document_id 参数）

    支持的文件类型：PDF、TXT、MD
    """
    from loguru import logger

    # 调试日志
    logger.info(f"[DEBUG] document_id={document_id}, file={file}, source_language={source_language}, target_language={target_language}")

    # 验证：file 和 document_id 必须提供其一
    if not file and not document_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须提供 file 或 document_id 参数",
        )
    if file and document_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="file 和 document_id 不能同时提供",
        )

    try:
        if document_id:
            # 方式1：从已有文档创建翻译任务
            from sqlalchemy import select

            result = await db.execute(
                select(Document).where(
                    Document.id == document_id,
                    Document.owner_id == owner_id,
                )
            )
            document = result.scalar_one_or_none()

            if not document:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="文档不存在",
                )

            # 从文件路径读取文件内容
            file_path = file_service.get_full_path(document.file_path)
            if not file_path.exists():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="文档文件不存在",
                )

            with open(file_path, "rb") as f:
                file_content = f.read()

            original_filename = document.original_filename

        else:
            # 方式2：上传新文件
            # 1. 验证文件类型
            allowed_extensions = {".pdf", ".txt", ".md"}
            file_ext = Path(file.filename).suffix.lower()

            if file_ext not in allowed_extensions:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"不支持的文件类型: {file_ext}，支持的类型: PDF, TXT, MD",
                )

            # 2. 读取文件内容
            file_content = await file.read()
            original_filename = file.filename

        # 3. 检查文件大小（50MB 限制）
        from core.config import settings
        max_size = 50 * 1024 * 1024  # 50MB
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"文件大小超过限制 (50MB)",
            )

        # 4. 创建翻译任务
        translation = await document_translation_service.create_translation_task(
            original_filename=original_filename,
            document_content=file_content,
            owner_id=owner_id,
            db=db,
            source_language=source_language,
            target_language=target_language,
        )

        # 5. 启动后台异步处理（不阻塞 HTTP 响应）
        import asyncio

        asyncio.create_task(
            document_translation_service.process_translation_background(
                translation_id=str(translation.id),
            )
        )

        # 6. 立即返回响应（不等待翻译完成）
        return ResponseModel(
            data=DocumentTranslationUploadResponse(
                translation_id=str(translation.id),
                filename=translation.original_filename,
                status=translation.status,
                message="翻译任务已创建，正在后台处理中",
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档翻译失败: {str(e)}",
        )


@router.get("/", response_model=ResponseModel[list[DocumentTranslationResponse]])
async def list_document_translations(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    status_filter: Optional[str] = Query(default=None, description="按状态筛选"),
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """
    获取公文翻译列表
    """
    try:
        from sqlalchemy import select, desc

        # 构建查询
        stmt = select(DocumentTranslation).where(
            DocumentTranslation.owner_id == owner_id
        )

        if status_filter:
            stmt = stmt.where(DocumentTranslation.status == status_filter)

        # 排序和分页
        stmt = stmt.order_by(desc(DocumentTranslation.created_at))
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        # 执行查询
        result = await db.execute(stmt)
        translations = result.scalars().all()

        # 转换为响应模型
        translation_responses = [
            DocumentTranslationResponse.model_validate(t) for t in translations
        ]

        return ResponseModel(data=translation_responses)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取翻译列表失败: {str(e)}",
        )


@router.get("/{translation_id}", response_model=ResponseModel[DocumentTranslationResponse])
async def get_document_translation(
    translation_id: str,
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """
    获取单个公文翻译详情
    """
    try:
        from sqlalchemy import select

        result = await db.execute(
            select(DocumentTranslation).where(
                DocumentTranslation.id == translation_id,
                DocumentTranslation.owner_id == owner_id,
            )
        )
        translation = result.scalar_one_or_none()

        if not translation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="翻译任务不存在",
            )

        return ResponseModel(
            data=DocumentTranslationResponse.model_validate(translation)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取翻译任务失败: {str(e)}",
        )


@router.get("/{translation_id}/status", response_model=ResponseModel[dict])
async def get_translation_status(
    translation_id: str,
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """
    查询公文翻译状态（用于轮询）

    返回状态和进度信息：
    - pending: 等待处理
    - processing: 正在翻译中
    - completed: 翻译完成
    - failed: 翻译失败
    """
    try:
        from sqlalchemy import select

        result = await db.execute(
            select(DocumentTranslation).where(
                DocumentTranslation.id == translation_id,
                DocumentTranslation.owner_id == owner_id,
            )
        )
        translation = result.scalar_one_or_none()

        if not translation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="翻译任务不存在",
            )

        # 构建响应数据
        status_messages = {
            DocumentTranslationStatus.PENDING.value: "任务已创建，等待处理",
            DocumentTranslationStatus.PROCESSING.value: "正在翻译中...",
            DocumentTranslationStatus.COMPLETED.value: "翻译完成",
            DocumentTranslationStatus.FAILED.value: "翻译失败",
        }

        response_data = {
            "translation_id": str(translation.id),
            "status": translation.status,
            "message": status_messages.get(translation.status, "未知状态"),
            "created_at": translation.created_at.isoformat(),
            "updated_at": translation.updated_at.isoformat(),
        }

        # 如果翻译完成，提供下载 URL 和文本内容
        if translation.status == DocumentTranslationStatus.COMPLETED.value:
            response_data["text_url"] = f"/api/v1/document-translation/{translation_id}/text"
            response_data["download_txt_url"] = f"/api/v1/document-translation/{translation_id}/download"
            response_data["download_word_url"] = f"/api/v1/document-translation/{translation_id}/download-word"
            response_data["download_markdown_url"] = f"/api/v1/document-translation/{translation_id}/download-markdown"
            # 直接返回翻译文本内容
            response_data["translated_text"] = translation.translated_text
            response_data["original_text"] = translation.original_text

        # 如果失败，提供错误信息
        if translation.status == DocumentTranslationStatus.FAILED.value:
            response_data["error"] = translation.error_message

        return ResponseModel(data=response_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询翻译状态失败: {str(e)}",
        )


@router.get("/{translation_id}/text", response_model=ResponseModel[DocumentTranslationTextResponse])
async def get_translation_text(
    translation_id: str,
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """
    获取翻译后的文本内容
    """
    try:
        from sqlalchemy import select

        result = await db.execute(
            select(DocumentTranslation).where(
                DocumentTranslation.id == translation_id,
                DocumentTranslation.owner_id == owner_id,
            )
        )
        translation = result.scalar_one_or_none()

        if not translation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="翻译任务不存在",
            )

        if translation.status != DocumentTranslationStatus.COMPLETED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="翻译尚未完成",
            )

        if not translation.translated_text:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="翻译内容不存在",
            )

        return ResponseModel(
            data=DocumentTranslationTextResponse(
                translation_id=str(translation.id),
                translated_text=translation.translated_text,
                original_text=translation.original_text,
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取翻译内容失败: {str(e)}",
        )


@router.get("/{translation_id}/download")
async def download_translation_text(
    translation_id: str,
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """
    下载翻译后的文本文件（TXT 格式）
    """
    try:
        from sqlalchemy import select

        result = await db.execute(
            select(DocumentTranslation).where(
                DocumentTranslation.id == translation_id,
                DocumentTranslation.owner_id == owner_id,
            )
        )
        translation = result.scalar_one_or_none()

        if not translation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="翻译任务不存在",
            )

        if translation.status != DocumentTranslationStatus.COMPLETED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="翻译尚未完成",
            )

        if not translation.translated_text:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="翻译内容��存在",
            )

        # 返回文本文件
        filename = f"translated_{Path(translation.original_filename).stem}.txt"
        return Response(
            content=translation.translated_text,
            media_type="text/plain",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"下载翻译内容失败: {str(e)}",
        )


@router.get("/{translation_id}/download-word")
async def download_translation_word(
    translation_id: str,
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """
    下载翻译后的 Word 文档（DOCX 格式）

    将 Markdown 格式的翻译结果转换为 Word 文档下载
    """
    try:
        from sqlalchemy import select

        result = await db.execute(
            select(DocumentTranslation).where(
                DocumentTranslation.id == translation_id,
                DocumentTranslation.owner_id == owner_id,
            )
        )
        translation = result.scalar_one_or_none()

        if not translation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="翻译任务不存在",
            )

        if translation.status != DocumentTranslationStatus.COMPLETED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="翻译尚未完成",
            )

        if not translation.translated_text:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="翻译内容不存在",
            )

        # 转换为 Word 文档
        try:
            word_bytes = convert_markdown_to_word(
                translation.translated_text,
                use_bilingual_format=True
            )
        except ImportError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Word 导出功能不可用，请安装 python-docx",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Word 文档生成失败: {str(e)}",
            )

        # 返回 Word 文件
        filename = f"translated_{Path(translation.original_filename).stem}.docx"
        return Response(
            content=word_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"下载 Word 文档失败: {str(e)}",
        )


@router.get("/{translation_id}/download-markdown")
async def download_translation_markdown(
    translation_id: str,
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """
    下载翻译后的 Markdown 文件（MD 格式）

    直接下载 Markdown 格式的翻译结果
    """
    try:
        from sqlalchemy import select

        result = await db.execute(
            select(DocumentTranslation).where(
                DocumentTranslation.id == translation_id,
                DocumentTranslation.owner_id == owner_id,
            )
        )
        translation = result.scalar_one_or_none()

        if not translation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="翻译任务不存在",
            )

        if translation.status != DocumentTranslationStatus.COMPLETED.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="翻译尚未完成",
            )

        if not translation.translated_text:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="翻译内容不存在",
            )

        # 返回 Markdown 文件
        filename = f"translated_{Path(translation.original_filename).stem}.md"
        return Response(
            content=translation.translated_text,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"下载 Markdown 文件失败: {str(e)}",
        )


@router.delete("/{translation_id}", response_model=ResponseModel[dict])
async def delete_document_translation(
    translation_id: str,
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """
    删除公文翻译记录
    """
    try:
        from sqlalchemy import select

        result = await db.execute(
            select(DocumentTranslation).where(
                DocumentTranslation.id == translation_id,
                DocumentTranslation.owner_id == owner_id,
            )
        )
        translation = result.scalar_one_or_none()

        if not translation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="翻译任务不存在",
            )

        # 删除文档文件
        file_service.delete_file(translation.original_document_path)

        if translation.translated_document_path:
            file_service.delete_file(translation.translated_document_path)

        # 删除数据库记录
        await db.delete(translation)
        await db.commit()

        return ResponseModel(data={"message": "翻译记录删除成功"})

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除翻译记录失败: {str(e)}",
        )
