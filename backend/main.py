"""
公文写作 AI 系统 - 主入口
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from core.config import settings
from core.database import init_db, close_db
from api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("[START] 应用启动中...")
    await init_db()
    logger.info("[OK] 数据库连接成功")
    yield
    # 关闭时执行
    logger.info("[STOP] 应用关闭中...")
    await close_db()
    logger.info("[OK] 数据库连接已关闭")


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Zotero 式文档管理 + AI 深度处理平台",
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=settings.ALLOWED_METHODS,
        allow_headers=settings.ALLOWED_HEADERS,
    )

    # 注册 API 路由
    app.include_router(api_router, prefix=settings.API_PREFIX)

    # 静态文件服务（用于访问上传的文件）
    app.mount("/storage", StaticFiles(directory="storage"), name="storage")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info",
    )
