"""
图片转译端点
"""

import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from models import ImageTranslation
from models.image_translation import ImageTranslationStatus
from schemas.image_translation import (
    ImageTranslationResponse,
    ImageTranslationUploadResponse,
)
from schemas.common import ResponseModel
from services.image_translation_service import image_translation_service
from api.dependencies import get_current_user_id

router = APIRouter()


@router.post("/", response_model=ResponseModel[ImageTranslationUploadResponse])
async def upload_and_translate_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="图片文件"),
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """
    上传图片并进行转译

    支持的图片类型：JPG、PNG、GIF、WebP、BMP
    """
    try:
        # 1. 验证文件类型
        allowed_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
        file_ext = Path(file.filename).suffix.lower()

        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件类型: {file_ext}",
            )

        # 2. 读取文件内容
        file_content = await file.read()
        file_size = len(file_content)

        # 3. 检查文件大小（10MB 限制）
        from core.config import settings
        if file_size > settings.MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"文件大小超过限制 ({settings.MAX_IMAGE_SIZE_MB}MB)",
            )

        # 4. 创建转译任务
        translation = await image_translation_service.create_translation_task(
            original_filename=file.filename,
            image_content=file_content,
            owner_id=owner_id,
            db=db,
        )

        # 5. 添加后台任务（使用 FastAPI BackgroundTasks）
        background_tasks.add_task(
            image_translation_service.process_translation_background,
            translation_id=str(translation.id),
        )

        # 6. 立即返回响应（不等待转译完成）
        return ResponseModel(
            data=ImageTranslationUploadResponse(
                translation_id=str(translation.id),
                filename=translation.original_filename,
                status=translation.status,
                message="转译任务已创建，正在后台处理中",
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"图片转译失败: {str(e)}",
        )


@router.get("/", response_model=ResponseModel[list[ImageTranslationResponse]])
async def list_image_translations(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    status_filter: Optional[str] = Query(default=None, description="按状态筛选"),
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """
    获取图片转译列表
    """
    try:
        from sqlalchemy import select, desc

        # 构建查询
        stmt = select(ImageTranslation).where(
            ImageTranslation.owner_id == owner_id
        )

        if status_filter:
            stmt = stmt.where(ImageTranslation.status == status_filter)

        # 排序和分页
        stmt = stmt.order_by(desc(ImageTranslation.created_at))
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        # 执行查询
        result = await db.execute(stmt)
        translations = result.scalars().all()

        # 转换为响应模型
        translation_responses = [
            ImageTranslationResponse.model_validate(t) for t in translations
        ]

        return ResponseModel(data=translation_responses)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取转译列表失败: {str(e)}",
        )


@router.get("/{translation_id}", response_model=ResponseModel[ImageTranslationResponse])
async def get_image_translation(
    translation_id: str,
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """
    获取单个图片转译详情
    """
    try:
        from sqlalchemy import select

        result = await db.execute(
            select(ImageTranslation).where(
                ImageTranslation.id == translation_id,
                ImageTranslation.owner_id == owner_id,
            )
        )
        translation = result.scalar_one_or_none()

        if not translation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="转译任务不存在",
            )

        return ResponseModel(
            data=ImageTranslationResponse.model_validate(translation)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取转译任务失败: {str(e)}",
        )


@router.get("/{translation_id}/status", response_model=ResponseModel[dict])
async def get_translation_status(
    translation_id: str,
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """
    查询图片转译状态（用于轮询）

    返回状态和进度信息：
    - pending: 等待处理
    - processing: 正在转译中
    - completed: 转译完成
    - failed: 转译失败
    """
    try:
        from sqlalchemy import select

        result = await db.execute(
            select(ImageTranslation).where(
                ImageTranslation.id == translation_id,
                ImageTranslation.owner_id == owner_id,
            )
        )
        translation = result.scalar_one_or_none()

        if not translation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="转译任务不存在",
            )

        # 构建响应数据
        status_messages = {
            ImageTranslationStatus.PENDING.value: "任务已创建，等待处理",
            ImageTranslationStatus.PROCESSING.value: "正在转译中...",
            ImageTranslationStatus.COMPLETED.value: "转译完成",
            ImageTranslationStatus.FAILED.value: "转译失败",
        }

        response_data = {
            "translation_id": str(translation.id),
            "status": translation.status,
            "message": status_messages.get(translation.status, "未知状态"),
            "created_at": translation.created_at.isoformat(),
            "updated_at": translation.updated_at.isoformat(),
        }

        # 如果转译完成，提供图片 URL
        if translation.status == ImageTranslationStatus.COMPLETED.value:
            response_data["preview_url"] = f"/api/v1/image-translation/{translation_id}/preview"
            response_data["download_url"] = f"/api/v1/image-translation/{translation_id}/download"

        # 如果失败，提供错误信息
        if translation.status == ImageTranslationStatus.FAILED.value:
            response_data["error"] = translation.error_message

        return ResponseModel(data=response_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询转译状态失败: {str(e)}",
        )


@router.get("/{translation_id}/preview")
async def preview_translated_image(
    translation_id: str,
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """
    预览转译后的图片
    """
    try:
        from sqlalchemy import select

        result = await db.execute(
            select(ImageTranslation).where(
                ImageTranslation.id == translation_id,
                ImageTranslation.owner_id == owner_id,
            )
        )
        translation = result.scalar_one_or_none()

        if not translation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="转译任务不存在",
            )

        if not translation.translated_image_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="转译图片尚未生成",
            )

        # 使用 file_service 获取完整路径
        from services.file_service import file_service
        image_path = file_service.get_full_path(translation.translated_image_path)

        if not image_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"图片文件不存在: {translation.translated_image_path}",
            )

        # 返回图片文件
        return FileResponse(
            path=str(image_path),
            media_type=translation.mime_type,
            headers={
                "Content-Disposition": f"inline; filename=translated_{translation.original_filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"预览图片失败: {str(e)}",
        )


@router.get("/{translation_id}/download")
async def download_translated_image(
    translation_id: str,
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """
    下载转译后的图片
    """
    try:
        from sqlalchemy import select

        result = await db.execute(
            select(ImageTranslation).where(
                ImageTranslation.id == translation_id,
                ImageTranslation.owner_id == owner_id,
            )
        )
        translation = result.scalar_one_or_none()

        if not translation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="转译任务不存在",
            )

        if not translation.translated_image_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="转译图片尚未生成",
            )

        # 使用 file_service 获取完整路径
        from services.file_service import file_service
        image_path = file_service.get_full_path(translation.translated_image_path)

        if not image_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"图片文件不存在: {translation.translated_image_path}",
            )

        # 返回图片文件（下载）
        return FileResponse(
            path=str(image_path),
            media_type=translation.mime_type,
            headers={
                "Content-Disposition": f"attachment; filename=translated_{translation.original_filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"下载图片失败: {str(e)}",
        )


@router.get("/{translation_id}/original")
async def download_original_image(
    translation_id: str,
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """
    下载原始图片
    """
    try:
        from sqlalchemy import select

        result = await db.execute(
            select(ImageTranslation).where(
                ImageTranslation.id == translation_id,
                ImageTranslation.owner_id == owner_id,
            )
        )
        translation = result.scalar_one_or_none()

        if not translation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="转译任务不存在",
            )

        # 检查文件是否存在
        image_path = Path(translation.original_image_path)
        if not image_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="图片文件不存在",
            )

        # 返回图片文件（下载）
        return FileResponse(
            path=str(image_path),
            media_type=translation.mime_type,
            headers={
                "Content-Disposition": f"attachment; filename={translation.original_filename}"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"下载图片失败: {str(e)}",
        )


@router.delete("/{translation_id}", response_model=ResponseModel[dict])
async def delete_image_translation(
    translation_id: str,
    db: AsyncSession = Depends(get_db),
    owner_id: str = Depends(get_current_user_id),
):
    """
    删除图片转译记录
    """
    try:
        from sqlalchemy import select

        result = await db.execute(
            select(ImageTranslation).where(
                ImageTranslation.id == translation_id,
                ImageTranslation.owner_id == owner_id,
            )
        )
        translation = result.scalar_one_or_none()

        if not translation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="转译任务不存在",
            )

        # 删除图片文件
        from services.file_service import file_service

        file_service.delete_file(translation.original_image_path)

        if translation.translated_image_path:
            file_service.delete_file(translation.translated_image_path)

        # 删除数据库记录
        await db.delete(translation)
        await db.commit()

        return ResponseModel(data={"message": "转译记录删除成功"})

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除转译记录失败: {str(e)}",
        )
