"""
Redis 连接管理
"""

from redis.asyncio import Redis, ConnectionPool
from loguru import logger

from core.config import settings


# 创建连接池
pool = ConnectionPool.from_url(
    settings.REDIS_URL,
    decode_responses=True,  # 自动解码为字符串
    max_connections=20,
)


async def init_redis():
    """初始化 Redis 连接"""
    try:
        redis = Redis(connection_pool=pool)
        await redis.ping()
        logger.info("[OK] Redis 连接成功")
        return redis
    except Exception as e:
        logger.error(f"[ERROR] Redis 连接失败: {e}")
        raise


async def close_redis():
    """关闭 Redis 连接"""
    try:
        await pool.disconnect()
        logger.info("[OK] Redis 连接已关闭")
    except Exception as e:
        logger.error(f"[ERROR] 关闭 Redis 连接失败: {e}")


async def get_redis() -> Redis:
    """
    依赖注入：获取 Redis 客户端
    """
    return Redis(connection_pool=pool)
