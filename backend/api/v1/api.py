"""
API v1 主路由
聚合所有端点
"""

from fastapi import APIRouter

from api.endpoints import documents, tasks, knowledge, workflows, storage, image_translation, document_translation

# 创建主路由
api_router = APIRouter()

# 注册各模块路由
api_router.include_router(
    documents.router,
    prefix="/documents",
    tags=["文档管理"],
)

api_router.include_router(
    tasks.router,
    prefix="/tasks",
    tags=["任务管理"],
)

api_router.include_router(
    knowledge.router,
    prefix="/knowledge",
    tags=["知识库"],
)

api_router.include_router(
    workflows.router,
    prefix="/workflows",
    tags=["工作流"],
)

api_router.include_router(
    storage.router,
    prefix="/storage",
    tags=["文件存储"],
)

api_router.include_router(
    image_translation.router,
    prefix="/image-translation",
    tags=["图片���译"],
)

api_router.include_router(
    document_translation.router,
    prefix="/document-translation",
    tags=["公文翻译"],
)


@api_router.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "公文写作AI系统",
        "version": "1.0.0",
    }
