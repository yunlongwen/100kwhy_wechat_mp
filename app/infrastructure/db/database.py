"""数据库连接和会话管理"""

import os
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from loguru import logger

from .models import Base

# 数据库文件路径（项目根目录下的 data.db）
_project_root = Path(__file__).resolve().parent.parent.parent.parent
DATABASE_URL = f"sqlite+aiosqlite:///{_project_root / 'data.db'}"

# 创建异步引擎
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # 设置为True可以查看SQL语句
    future=True,
    connect_args={"check_same_thread": False}  # SQLite需要这个参数
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db():
    """初始化数据库（创建表）"""
    try:
        async with engine.begin() as conn:
            # 创建所有表
            await conn.run_sync(Base.metadata.create_all)
        logger.info("[数据库] 数据库表创建成功")
    except Exception as e:
        logger.error(f"[数据库] 数据库初始化失败: {e}")
        raise


async def get_db():
    """
    获取数据库会话（依赖注入，用于FastAPI）
    
    Usage in FastAPI:
        @app.get("/items")
        async def read_items(db: AsyncSession = Depends(get_db)):
            # 使用db进行数据库操作
            pass
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()
    logger.info("[数据库] 数据库连接已关闭")

