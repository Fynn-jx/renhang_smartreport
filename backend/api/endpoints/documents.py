"""
文档管理端点
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.config import settings
from schemas.document import (
    DocumentResponse,
    DocumentUploadResponse,
    DocumentUpdate,
    DocumentListQuery,
)
from schemas.common import PaginatedResponse, ResponseModel
from services.document_service import document_service
from api.dependencies import get_current_user_id

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[DocumentResponse])
async def list_documents(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    document_type: Optional[str] = Query(default=None, description="按文档类型筛选"),
    tag_id: Optional[str] = Query(default=None, description="按标签筛选（字符串格式）"),
    keyword: Optional[str] = Query(default=None, description="按关键词搜索"),
    sort_by: str = Query(default="created_at", description="排序字段"),
    sort_order: str = Query(default="desc", regex="^(asc|desc)$", description="排序方向"),
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """
    获取文档列表

    支持分页、筛选、排序功能
    """
    try:
        # 构建查询参数
        query_params = DocumentListQuery(
            page=page,
            page_size=page_size,
            document_type=document_type,
            tag_id=tag_id,
            keyword=keyword,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        # 获取文档列表
        documents, total = await document_service.list_documents(
            query_params=query_params,
            owner_id=owner_id,
            db=db,
        )

        # 转换为响应模型
        document_responses = [DocumentResponse.model_validate(doc) for doc in documents]

        # 构建分页响应
        return PaginatedResponse.create(
            items=document_responses,
            total=total,
            page=page,
            page_size=page_size,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档列表失败: {str(e)}",
        )


@router.get("/{document_id}", response_model=ResponseModel[DocumentResponse])
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """
    获取单个文档详情
    """
    try:
        document = await document_service.get_document(
            document_id=document_id,
            owner_id=owner_id,
            db=db,
        )

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在",
            )

        return ResponseModel(data=DocumentResponse.model_validate(document))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档失败: {str(e)}",
        )


@router.post("/", response_model=ResponseModel[DocumentUploadResponse])
async def upload_document(
    file: UploadFile = File(..., description="文件"),
    title: str = Form(..., min_length=1, max_length=500, description="文档标题"),
    author: Optional[str] = Form(None, max_length=255, description="作者"),
    subject: Optional[str] = Form(None, max_length=500, description="主题"),
    keywords: Optional[str] = Form(None, description="关键词（逗号分隔）"),
    tag_ids: Optional[str] = Form(None, description="标签 ID（逗号分隔）"),
    source_url: Optional[str] = Form(None, description="来源 URL"),
    parent_id: Optional[uuid.UUID] = Form(None, description="父文档 ID"),
    is_shared: Optional[bool] = Form(False, description="是否共享给团队"),
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """
    上传新文档

    支持的文件类型：PDF、DOCX、TXT、Markdown、图片
    """
    try:
        # 1. 验证文件大小
        file_content = await file.read()
        file_size = len(file_content)

        # 判断文件类型
        document_type = _get_document_type(file.content_type, file.filename)

        # 检查文件大小限制
        max_size = settings.MAX_FILE_SIZE if document_type != "image" else settings.MAX_IMAGE_SIZE
        if file_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"文件大小超过限制 ({max_size // (1024 * 1024)}MB)",
            )

        # 2. 构建文档创建数据
        from schemas.document import DocumentCreate

        keyword_list = keywords.split(",") if keywords else None
        tag_id_list = [uuid.UUID(tid.strip()) for tid in tag_ids.split(",")] if tag_ids else None

        document_data = DocumentCreate(
            title=title,
            original_filename=file.filename,
            document_type=document_type,
            author=author,
            subject=subject,
            keywords=keyword_list,
            tag_ids=tag_id_list,
            source_url=source_url,
            source_type="upload",
            parent_id=parent_id,
            is_shared=is_shared,
        )

        # 3. 创建文档
        document = await document_service.create_document(
            document_data=document_data,
            file_content=file_content,
            owner_id=owner_id,
            db=db,
        )

        # 4. 返回响应
        return ResponseModel(
            data=DocumentUploadResponse(
                document_id=str(document.id),
                filename=document.original_filename,
                file_size=document.file_size,
                document_type=document.document_type,
                message="文档上传成功",
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档上传失败: {str(e)}",
        )


@router.patch("/{document_id}", response_model=ResponseModel[DocumentResponse])
async def update_document(
    document_id: uuid.UUID,
    title: Optional[str] = Form(None, min_length=1, max_length=500),
    author: Optional[str] = Form(None, max_length=255),
    subject: Optional[str] = Form(None, max_length=500),
    keywords: Optional[str] = Form(None, description="关键词（逗号分隔）"),
    tag_ids: Optional[str] = Form(None, description="标签 ID（逗号分隔）"),
    is_shared: Optional[bool] = Form(None, description="是否共享给团队"),
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """
    更新文档元数据（标题、标签等）
    """
    try:
        # 构建更新数据
        keyword_list = keywords.split(",") if keywords else None
        tag_id_list = [uuid.UUID(tid.strip()) for tid in tag_ids.split(",")] if tag_ids else None

        update_data = DocumentUpdate(
            title=title,
            author=author,
            subject=subject,
            keywords=keyword_list,
            tag_ids=tag_id_list,
            is_shared=is_shared,
        )

        # 更新文档
        document = await document_service.update_document(
            document_id=document_id,
            document_data=update_data,
            owner_id=owner_id,
            db=db,
        )

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在",
            )

        return ResponseModel(data=DocumentResponse.model_validate(document))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档更新失败: {str(e)}",
        )


@router.delete("/{document_id}", response_model=ResponseModel[dict])
async def delete_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """
    删除文档
    """
    try:
        success = await document_service.delete_document(
            document_id=document_id,
            owner_id=owner_id,
            db=db,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在",
            )

        return ResponseModel(data={"message": "文档删除成功"})

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档删除失败: {str(e)}",
        )


@router.get("/{document_id}/content", response_model=ResponseModel[dict])
async def get_document_content(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """
    获取文档内容
    """
    try:
        document = await document_service.get_document(
            document_id=document_id,
            owner_id=owner_id,
            db=db,
        )

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文档不存在",
            )

        return ResponseModel(
            data={
                "content": document.content,
                "content_preview": document.content_preview,
                "page_count": document.page_count,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文档内容失败: {str(e)}",
        )


def _get_document_type(content_type: str, filename: str) -> str:
    """
    根据内容类型和文件名确定文档类型

    Args:
        content_type: MIME 类型
        filename: 文件名

    Returns:
        文档类型字符串
    """
    # 首先根据 MIME 类型判断
    if content_type == "application/pdf":
        return "pdf"
    elif content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return "docx"
    elif content_type == "text/plain":
        return "txt"
    elif content_type.startswith("image/"):
        return "image"

    # 根据文件扩展名判断
    if filename.endswith(".pdf"):
        return "pdf"
    elif filename.endswith(".docx"):
        return "docx"
    elif filename.endswith((".txt", ".text")):
        return "txt"
    elif filename.endswith((".md", ".markdown")):
        return "markdown"

    # 默认返回 txt
    return "txt"
