"""
文件存储端点
"""

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from api.dependencies import get_current_user_id

router = APIRouter()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """上传文件"""
    # TODO: 实现文件上传逻辑
    return {
        "filename": file.filename,
        "message": "待实现",
    }


@router.get("/download/{file_id}")
async def download_file(
    file_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """下载文件"""
    # TODO: 实现文件下载逻辑
    return {
        "message": "待实现",
    }
