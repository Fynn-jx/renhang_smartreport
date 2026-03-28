"""
数据库连接管理
使用 SQLAlchemy 2.0 异步模式
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from loguru import logger

from core.config import settings


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


class Base(DeclarativeBase):
    """所有模型的基类"""

    pass


async def init_db():
    """初始化数据库"""
    try:
        async with engine.begin() as conn:
            # 创建所有表（开发环境）
            # 生产环境应该使用 Alembic 迁移
            if settings.ENVIRONMENT == "development":
                await conn.run_sync(Base.metadata.create_all)
                logger.info("[OK] 数据库表创建成功")
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
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()
