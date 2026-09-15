"""
数据库连接管理
使用 SQLAlchemy 2.0 异步模式
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from loguru import logger

from core.config import settings
from models.base import Base


# 创建异步引擎
# SQLite 不支持连接池，PostgreSQL 支持
if settings.DATABASE_URL.startswith("sqlite"):
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
    )
else:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # 提交后不过期对象
    autocommit=False,
    autoflush=False,
)

_db_initialized = False


async def init_db():
    """初始化数据库"""
    global _db_initialized
    if _db_initialized:
        return

    try:
        # Ensure every model is registered on the shared metadata before
        # create_all runs. This is also required on serverless cold starts.
        import models  # noqa: F401

        async with engine.begin() as conn:
            # 创建所有表（开发环境）
            # 生产环境应该使用 Alembic 迁移
            if settings.ENVIRONMENT == "development":
                await conn.run_sync(Base.metadata.create_all)
                logger.info("[OK] 数据库表创建成功")
        _db_initialized = True
    except Exception as e:
        logger.error(f"[ERROR] 数据库初始化失败: {e}")
        raise


async def close_db():
    """关闭数据库连接"""
    try:
        await engine.dispose()
        logger.info("[OK] 数据库连接已关闭")
    except Exception as e:
        logger.error(f"[ERROR] 关闭数据库连接失败: {e}")


async def get_db() -> AsyncSession:
    """
    依赖注入：获取数据库会话
    用法：
        @router.get("/documents/{doc_id}")
        async def get_document(doc_id: str, db: AsyncSession = Depends(get_db)):
            ...
    """
    # Some serverless runtimes do not run ASGI lifespan hooks reliably.
    # create_all is idempotent and guarantees a fresh /tmp SQLite database is
    # usable before the first database-backed request.
    if settings.ENVIRONMENT == "development":
        await init_db()

    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()
