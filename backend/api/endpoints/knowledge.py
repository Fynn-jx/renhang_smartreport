"""
知识库端点
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from api.dependencies import get_current_user_id

router = APIRouter()


@router.post("/search")
async def search_knowledge(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """知识库向量检索"""
    # TODO: 实现知识库检索逻辑
    return {
        "results": [],
        "message": "待实现",
    }


@router.post("/upload")
async def upload_knowledge(
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """上传知识库文档"""
    # TODO: 实现知识库上传逻辑
    return {
        "message": "待实现",
    }


@router.delete("/{knowledge_id}")
async def delete_knowledge(
    knowledge_id: str,
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    """删除知识库条目"""
    # TODO: 实现知识库删除逻辑
    return {
        "message": "待实现",
    }
