"""
数据库连接管理
==============

提供数据库连接的核心功能:
- 同步/异步数据库引擎
- 连接池管理
- 会话工厂
- 数据库初始化
- 健康检查
"""

import asyncio
import logging
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator, Optional
import time

from sqlalchemy import create_engine, Engine, text, event, pool, exc
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool, StaticPool

from ..models.base import Base
from .config import get_database_config

# 配置日志
logger = logging.getLogger(__name__)

# 全局引擎实例
engine: Optional[Engine] = None
async_engine: Optional[AsyncEngine] = None
SessionLocal: Optional[sessionmaker] = None
AsyncSessionLocal: Optional[async_sessionmaker] = None


class DatabaseConnectionError(Exception):
    """数据库连接错误"""

    pass


class DatabaseTimeoutError(Exception):
    """数据库超时错误"""

    pass


def create_database_engine() -> Engine:
    """
    创建同步数据库引擎

    Returns:
        SQLAlchemy Engine实例
    """
    config = get_database_config()

    try:
        pass  # Auto-fixed empty block
        # 创建引擎
        engine = create_engine(
            pool_pre_ping=True,  # 连接预检查
            config.get_sync_url(),
            **config.get_engine_kwargs(),
            poolclass=QueuePool,
            pool_reset_on_return="commit",
            future=True,  # 使用SQLAlchemy 2.0风格
        )

        # 注册事件监听器
        _register_engine_events(engine)

        logger.info(
            f"创建数据库引擎: {config.host}:{config.port}/{config.database} "
            f"(pool_size={config.pool_size})"
        )

        return engine

    except Exception as e:
        logger.error(f"创建数据库引擎失败: {e}")
        raise DatabaseConnectionError(f"无法创建数据库引擎: {e}")


def create_async_database_engine() -> AsyncEngine:
    """
    创建异步数据库引擎

    Returns:
        SQLAlchemy AsyncEngine实例
    """
    config = get_database_config()

    try:
        pass  # Auto-fixed empty block
        # 创建异步引擎
        async_engine = create_async_engine(
            config.get_async_url(),
            **config.get_async_engine_kwargs(),
            poolclass=QueuePool,
            pool_reset_on_return="commit",
            future=True,
        )

        # 注册事件监听器
        _register_async_engine_events(async_engine)

        logger.info(
            f"创建异步数据库引擎: {config.host}:{config.port}/{config.database} "
            f"(async_pool_size={config.async_pool_size})"
        )

        return async_engine

    except Exception as e:
        logger.error(f"创建异步数据库引擎失败: {e}")
        raise DatabaseConnectionError(f"无法创建异步数据库引擎: {e}")


def _register_engine_events(engine: Engine) -> None:
    """
    注册引擎事件监听器

    Args:
        engine: 数据库引擎
    """

    @event.listens_for(engine, "connect")
    def on_connect(dbapi_connection, connection_record):
        """连接建立时的回调"""
        logger.debug("建立新的数据库连接")

        # 设置连接参数
        with dbapi_connection.cursor() as cursor:
            pass  # Auto-fixed empty block
            # 设置时区
            cursor.execute("SET timezone TO 'UTC'")
            # 设置字符编码
            cursor.execute("SET client_encoding TO 'UTF8'")
            # 设置语句超时
            cursor.execute("SET statement_timeout TO '30s'")

    @event.listens_for(engine, "checkout")
    def on_checkout(dbapi_connection, connection_record, connection_proxy):
        """从连接池获取连接时的回调"""
        logger.debug("从连接池获取连接")

    @event.listens_for(engine, "checkin")
    def on_checkin(dbapi_connection, connection_record):
        """连接返回连接池时的回调"""
        logger.debug("连接返回连接池")

    @event.listens_for(engine, "invalidate")
    def on_invalidate(dbapi_connection, connection_record, exception):
        """连接失效时的回调"""
        logger.warning(f"数据库连接失效: {exception}")


def _register_async_engine_events(async_engine: AsyncEngine) -> None:
    """
    注册异步引擎事件监听器

    Args:
        async_engine: 异步数据库引擎
    """

    @event.listens_for(async_engine.sync_engine, "connect")
    def on_async_connect(dbapi_connection, connection_record):
        """异步连接建立时的回调"""
        logger.debug("建立新的异步数据库连接")


async def init_database() -> None:
    """
    初始化数据库
    - 创建引擎和会话工厂
    - 创建数据库表
    - 验证连接
    """
    global engine, async_engine, SessionLocal, AsyncSessionLocal

    try:
        pass  # Auto-fixed empty block
        # 创建引擎
        engine = create_database_engine()
        async_engine = create_async_database_engine()

        # 创建会话工厂
        SessionLocal = sessionmaker(
            bind=engine,
            class_=Session,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False,
        )

        AsyncSessionLocal = async_sessionmaker(
            bind=async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False,
        )

        # 测试连接
        await test_database_connection()

        logger.info("数据库初始化完成")

    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        await close_database()
        raise


async def close_database() -> None:
    """
    关闭数据库连接
    """
    global engine, async_engine, SessionLocal, AsyncSessionLocal

    try:
        if async_engine:
            await async_engine.dispose()
            async_engine = None
            logger.info("异步数据库引擎已关闭")

        if engine:
            engine.dispose()
            engine = None
            logger.info("数据库引擎已关闭")

        SessionLocal = None
        AsyncSessionLocal = None

    except Exception as e:
        logger.error(f"关闭数据库连接时出错: {e}")


async def create_tables() -> None:
    """
    创建所有数据库表
    """
    if not async_engine:
        raise DatabaseConnectionError("数据库引擎未初始化")

    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("数据库表创建完成")

    except Exception as e:
        logger.error(f"创建数据库表失败: {e}")
        raise


async def drop_tables() -> None:
    """
    删除所有数据库表 (谨慎使用!)
    """
    if not async_engine:
        raise DatabaseConnectionError("数据库引擎未初始化")

    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        logger.info("数据库表删除完成")

    except Exception as e:
        logger.error(f"删除数据库表失败: {e}")
        raise


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    获取同步数据库会话 (上下文管理器)

    Yields:
        数据库会话对象

    Raises:
        DatabaseConnectionError: 连接失败
    """
    if not SessionLocal:
        raise DatabaseConnectionError("数据库会话工厂未初始化")

    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"数据库操作失败: {e}")
        raise
    finally:
        session.close()


@asynccontextmanager
async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    获取异步数据库会话 (异步上下文管理器)

    Yields:
        异步数据库会话对象

    Raises:
        DatabaseConnectionError: 连接失败
    """
    if not AsyncSessionLocal:
        raise DatabaseConnectionError("异步数据库会话工厂未初始化")

    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        logger.error(f"异步数据库操作失败: {e}")
        raise
    finally:
        await session.close()


async def test_database_connection() -> bool:
    """
    测试数据库连接

    Returns:
        连接是否成功

    Raises:
        DatabaseConnectionError: 连接失败
    """
    try:
        pass  # Auto-fixed empty block
        # 测试同步连接
        with get_db_session() as session:
            result = session.execute(text("SELECT 1 as test"))
            assert result.scalar() == 1

        # 测试异步连接
        async with get_async_db_session() as session:
            result = await session.execute(text("SELECT 1 as test"))
            assert result.scalar() == 1

        logger.info("数据库连接测试成功")
        return True

    except Exception as e:
        logger.error(f"数据库连接测试失败: {e}")
        raise DatabaseConnectionError(f"数据库连接测试失败: {e}")


async def get_database_info() -> dict:
    """
    获取数据库信息

    Returns:
        数据库信息字典
    """
    if not async_engine:
        raise DatabaseConnectionError("数据库引擎未初始化")

    try:
        async with get_async_db_session() as session:
            # 获取PostgreSQL版本
            version_result = await session.execute(text("SELECT version()"))
            version = version_result.scalar()

            # 获取当前数据库
            db_result = await session.execute(text("SELECT current_database()"))
            current_db = db_result.scalar()

            # 获取当前用户
            user_result = await session.execute(text("SELECT current_user"))
            current_user = user_result.scalar()

            # 获取连接池信息
            pool_info = {
                "pool_size": engine.pool.size() if engine else None,
                "checked_in": engine.pool.checkedin() if engine else None,
                "checked_out": engine.pool.checkedout() if engine else None,
                "invalid": engine.pool.invalid() if engine else None,
            }

            return {
                "version": version,
                "database": current_db,
                "user": current_user,
                "pool_info": pool_info,
                "engine_url": str(
                    async_engine.url.render_as_string(hide_password=True)
                ),
            }

    except Exception as e:
        logger.error(f"获取数据库信息失败: {e}")
        raise


class ConnectionMonitor:
    """
    数据库连接监控器
    ================

    监控数据库连接的健康状态
    """

    def __init__(self, check_interval: int = 30):
        """
        初始化监控器

        Args:
            check_interval: 检查间隔 (秒)
        """
        self.check_interval = check_interval
        self.is_monitoring = False
        self.last_check_time = 0
        self.connection_errors = 0
        self.max_errors = 5

    async def start_monitoring(self) -> None:
        """开始监控"""
        if self.is_monitoring:
            return

        self.is_monitoring = True
        logger.info(f"开始数据库连接监控 (间隔: {self.check_interval}秒)")

        while self.is_monitoring:
            try:
                await self._check_connection()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"连接监控出错: {e}")
                await asyncio.sleep(5)  # 出错时缩短等待时间

    def stop_monitoring(self) -> None:
        """停止监控"""
        self.is_monitoring = False
        logger.info("停止数据库连接监控")

    async def _check_connection(self) -> None:
        """检查连接健康状态"""
        try:
            start_time = time.time()
            await test_database_connection()
            response_time = (time.time() - start_time) * 1000  # 毫秒

            self.connection_errors = 0
            self.last_check_time = time.time()

            if response_time > 1000:  # 响应时间超过1秒
                logger.warning(f"数据库响应较慢: {response_time:.2f}ms")

        except Exception as e:
            self.connection_errors += 1
            logger.error(f"数据库连接检查失败 ({self.connection_errors}/{self.max_errors}): {e}")

            if self.connection_errors >= self.max_errors:
                logger.critical("数据库连接持续失败，请检查数据库服务")
                # 这里可以添加告警逻辑


# 创建全局监控器实例
connection_monitor = ConnectionMonitor()


# 导出公共接口
__all__ = [
    "engine",
    "async_engine",
    "SessionLocal",
    "AsyncSessionLocal",
    "get_db_session",
    "get_async_db_session",
    "init_database",
    "close_database",
    "create_tables",
    "drop_tables",
    "test_database_connection",
    "get_database_info",
    "ConnectionMonitor",
    "connection_monitor",
    "DatabaseConnectionError",
    "DatabaseTimeoutError",
]
