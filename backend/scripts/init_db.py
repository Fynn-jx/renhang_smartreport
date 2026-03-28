"""
数据库初始化脚本
用于创建所有数据库表
"""

import asyncio
from loguru import logger

from core.config import settings
from core.database import engine
from models import Base


async def init_database():
    """
    初始化数据库
    创建所有表
    """
    try:
        logger.info("[DB] 开始初始化数据库...")

        # 导入所有模型（确保它们被注册到 Base.metadata）
        from models import user, document, tag, task

        # 创建所有表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("[OK] 数据库初始化成功！")
        logger.info(f"[INFO] 已创建 {len(Base.metadata.tables)} 个表：")
        for table_name in Base.metadata.tables:
            logger.info(f"   - {table_name}")

    except Exception as e:
        logger.error(f"[ERROR] 数据库初始化失败: {e}")
        raise


async def drop_database():
    """
    删除所有表（谨慎使用！）
    """
    try:
        logger.warning("[WARNING] 准备删除所有数据库表...")

        # 导入所有模型
        from models import user, document, tag, task

        # 删除所有表
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        logger.warning("[OK] 所有数据库表已删除")

    except Exception as e:
        logger.error(f"[ERROR] 删除数据库表失败: {e}")
        raise


async def reset_database():
    """
    重置数据库（删除所有表并重新创建）
    """
    try:
        logger.warning("[RESET] 开始重置数据库...")

        # 删除所有表
        await drop_database()

        # 重新创建所有表
        await init_database()

        logger.info("[OK] 数据库重置成功！")

    except Exception as e:
        logger.error(f"[ERROR] 数据库重置失败: {e}")
        raise


async def create_initial_data():
    """
    创建初始数据
    """
    try:
        logger.info("[DATA] 开始创建初始数据...")

        from core.database import AsyncSessionLocal
        from models import User, Tag
        from core.security import get_password_hash

        async with AsyncSessionLocal() as session:
            # 创建管理员用户
            admin_user = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
                full_name="系统管理员",
                is_active=True,
                is_superuser=True,
            )
            session.add(admin_user)

            # 创建一些常用标签
            tags = [
                Tag(name="宏观经济", color="#3498db", description="宏观经济相关文档"),
                Tag(name="货币政策", color="#e74c3c", description="货币政策相关文档"),
                Tag(name="金融稳定", color="#2ecc71", description="金融稳定相关文档"),
                Tag(name="国际金融", color="#9b59b6", description="国际金融相关文档"),
                Tag(name="监管政策", color="#f39c12", description="监管政策相关文档"),
            ]
            for tag in tags:
                session.add(tag)

            await session.commit()

        logger.info("[OK] 初始数据创建成功！")
        logger.info("[USER] 管理员账号：admin / admin123")

    except Exception as e:
        logger.error(f"[ERROR] 创建初始数据失败: {e}")
        raise


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "init":
            asyncio.run(init_database())

        elif command == "drop":
            confirm = input("[WARNING] 确定要删除所有数据库表吗？此操作不可恢复！(yes/no): ")
            if confirm.lower() == "yes":
                asyncio.run(drop_database())
            else:
                logger.info("[CANCEL] 操作已取消")

        elif command == "reset":
            confirm = input("[WARNING] 确定要重置数据库吗？所有数据将丢失！(yes/no): ")
            if confirm.lower() == "yes":
                asyncio.run(reset_database())
            else:
                logger.info("[CANCEL] 操作已取消")

        elif command == "seed":
            asyncio.run(create_initial_data())

        elif command == "all":
            confirm = input("[WARNING] 确定要初始化并创建初始数据吗？(yes/no): ")
            if confirm.lower() == "yes":
                asyncio.run(init_database())
                asyncio.run(create_initial_data())
            else:
                logger.info("[CANCEL] 操作已取消")

        else:
            logger.info(f"[ERROR] 未知命令: {command}")
            logger.info("使用方法:")
            logger.info("  python scripts/init_db.py init     # 初始化数据库")
            logger.info("  python scripts/init_db.py drop     # 删除所有表")
            logger.info("  python scripts/init_db.py reset    # 重置数据库")
            logger.info("  python scripts/init_db.py seed     # 创建初始数据")
            logger.info("  python scripts/init_db.py all      # 初始化 + 创建初始数据")

    else:
        logger.info("使用方法:")
        logger.info("  python scripts/init_db.py init     # 初始化数据库")
        logger.info("  python scripts/init_db.py drop     # 删除所有表")
        logger.info("  python scripts/init_db.py reset    # 重置数据库")
        logger.info("  python scripts/init_db.py seed     # 创建初始数据")
        logger.info("  python scripts/init_db.py all      # 初始化 + 创建初始数据")
