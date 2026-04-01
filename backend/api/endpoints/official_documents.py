"""
公文库 API 端点
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from schemas.official_document import (
    OfficialDocumentResponse,
    OfficialDocumentUploadResponse,
    OfficialDocumentUpdate,
    OfficialDocumentListQuery,
    OfficialDocumentCreate,
)
from schemas.common import PaginatedResponse, ResponseModel
from services.official_document_service import official_document_service
from api.dependencies import get_current_user_id

router = APIRouter()


@router.get("/", response_model=ResponseModel[PaginatedResponse[OfficialDocumentResponse]])
async def list_official_documents(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    source: Optional[str] = Query(default=None, description="按来源机构筛选"),
    keyword: Optional[str] = Query(default=None, description="按关键词搜索"),
    is_verified: Optional[bool] = Query(default=None, description="按审核状态筛选"),
    sort_by: str = Query(default="created_at", description="排序字段"),
    sort_order: str = Query(default="desc", regex="^(asc|desc)$", description="排序方向"),
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """
    获取公文列表

    支持分页、筛选、排序功能
    """
    try:
        # 构建查询参数
        query_params = OfficialDocumentListQuery(
            page=page,
            page_size=page_size,
            source=source,
            keyword=keyword,
            is_verified=is_verified,
            sort_by=sort_by,
            sort_order=sort_order,
        )

        # 获取公文列表
        documents, total = await official_document_service.list_documents(
            query_params=query_params,
            owner_id=owner_id,
            db=db,
        )

        # 转换为响应模型
        document_responses = [OfficialDocumentResponse.from_orm_obj(doc) for doc in documents]

        # 构建分页响应
        paginated = PaginatedResponse.create(
            items=document_responses,
            total=total,
            page=page,
            page_size=page_size,
        )

        return ResponseModel(data=paginated)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取公文列表失败: {str(e)}",
        )


@router.get("/{document_id}", response_model=ResponseModel[OfficialDocumentResponse])
async def get_official_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """
    获取单个公文详情
    """
    try:
        document = await official_document_service.get_document(
            document_id=document_id,
            owner_id=owner_id,
            db=db,
        )

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="公文不存在",
            )

        return ResponseModel(data=OfficialDocumentResponse.from_orm_obj(document))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取公文失败: {str(e)}",
        )


@router.post("/", response_model=ResponseModel[OfficialDocumentUploadResponse])
async def upload_official_document(
    file: UploadFile = File(..., description="文件"),
    title: str = Form(..., min_length=1, max_length=500, description="公文标题"),
    description: str = Form(None, max_length=1000, description="公文描述"),
    source: str = Form(..., description="来源机构"),
    is_verified: bool = Form(False, description="是否已审核"),
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """
    上传新公文

    支持的文件类型：PDF、DOCX、TXT、Markdown
    """
    try:
        # 1. 验证文件大小
        file_content = await file.read()
        file_size = len(file_content)

        # 检查文件大小限制 (50MB)
        max_size = 50 * 1024 * 1024
        if file_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"文件大小超过限制 (50MB)",
            )

        # 2. 构建公文创建数据
        document_data = OfficialDocumentCreate(
            title=title,
            description=description,
            source=source,
            is_verified=is_verified,
        )

        # 3. 创建公文
        document = await official_document_service.create_document(
            document_data=document_data,
            file_content=file_content,
            filename=file.filename,
            mime_type=file.content_type,
            owner_id=owner_id,
            db=db,
        )

        # 4. 返回响应
        return ResponseModel(
            data=OfficialDocumentUploadResponse(
                document_id=str(document.id),
                filename=document.original_filename,
                file_size=document.file_size,
                document_type=document.document_type,
                message="公文上传成功",
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"公文上传失败: {str(e)}",
        )


@router.patch("/{document_id}", response_model=ResponseModel[OfficialDocumentResponse])
async def update_official_document(
    document_id: str,
    title: str = Form(None, min_length=1, max_length=500),
    description: str = Form(None, max_length=1000),
    source: str = Form(None),
    is_verified: bool = Form(None),
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """
    更新公文元数据
    """
    try:
        # 构建更新数据
        update_data = OfficialDocumentUpdate(
            title=title,
            description=description,
            source=source,
            is_verified=is_verified,
        )

        # 更新公文
        document = await official_document_service.update_document(
            document_id=document_id,
            document_data=update_data,
            owner_id=owner_id,
            db=db,
        )

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="公文不存在",
            )

        return ResponseModel(data=OfficialDocumentResponse.from_orm_obj(document))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"公文更新失败: {str(e)}",
        )


@router.delete("/{document_id}", response_model=ResponseModel[dict])
async def delete_official_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """
    删除公文
    """
    try:
        success = await official_document_service.delete_document(
            document_id=document_id,
            owner_id=owner_id,
            db=db,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="公文不存在",
            )

        return ResponseModel(data={"message": "公文删除成功"})

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"公文删除失败: {str(e)}",
        )


@router.get("/{document_id}/content", response_model=ResponseModel[dict])
async def get_official_document_content(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """
    获取公文内容
    """
    try:
        document = await official_document_service.get_document(
            document_id=document_id,
            owner_id=owner_id,
            db=db,
        )

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="公文不存在",
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
            detail=f"获取公文内容失败: {str(e)}",
        )


@router.get("/{document_id}/download")
async def download_official_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """
    下载公文文件
    """
    try:
        from fastapi.responses import FileResponse
        from pathlib import Path

        document = await official_document_service.get_document(
            document_id=document_id,
            owner_id=owner_id,
            db=db,
        )

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="公文不存在",
            )

        file_path = Path(settings.STORAGE_ROOT) / document.file_path

        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="文件不存在",
            )

        return FileResponse(
            path=str(file_path),
            filename=document.original_filename,
            media_type=document.mime_type,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"下载公文失败: {str(e)}",
        )
