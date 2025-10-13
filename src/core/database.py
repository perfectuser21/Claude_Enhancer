"""
数据库连接和会话管理
提供数据库连接池、会话管理、初始化等功能
"""

import uuid
import logging
from typing import Generator, Optional, AsyncGenerator
from contextlib import contextmanager, asynccontextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import SQLAlchemyError

import redis
from redis.connection import ConnectionPool

from .config import get_database_config
from ..models.base import BaseModel
from ..models import User, Project, Task, Label

# 设置日志
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    数据库管理器
    负责管理数据库连接、会话和生命周期
    """

    def __init__(self):
        self.config = get_database_config()
        self._sync_engine = None
        self._async_engine = None
        self._sync_session_factory = None
        self._async_session_factory = None
        self._redis_pool = None
        self._redis_client = None

    @property
    def sync_engine(self):
        """获取同步数据库引擎"""
        if self._sync_engine is None:
            self._sync_engine = create_engine(
                self.config.sync_database_url,
                poolclass=QueuePool,
                **self.config.engine_config,
            )
            logger.info("同步数据库引擎已创建")
        return self._sync_engine

    @property
    def async_engine(self):
        """获取异步数据库引擎"""
        if self._async_engine is None:
            self._async_engine = create_async_engine(
                self.config.async_database_url,
                poolclass=QueuePool,
                **self.config.engine_config,
            )
            logger.info("异步数据库引擎已创建")
        return self._async_engine

    @property
    def sync_session_factory(self):
        """获取同步会话工厂"""
        if self._sync_session_factory is None:
            self._sync_session_factory = scoped_session(
                sessionmaker(
                    bind=self.sync_engine,
                    autocommit=False,
                    autoflush=False,
                    expire_on_commit=False,
                )
            )
        return self._sync_session_factory

    @property
    def async_session_factory(self):
        """获取异步会话工厂"""
        if self._async_session_factory is None:
            self._async_session_factory = async_sessionmaker(
                bind=self.async_engine,
                class_=AsyncSession,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False,
            )
        return self._async_session_factory

    @property
    def redis_client(self):
        """获取Redis客户端"""
        if self._redis_client is None:
            if self._redis_pool is None:
                self._redis_pool = ConnectionPool.from_url(
                    self.config.redis_url, decode_responses=True, max_connections=20
                )
            self._redis_client = redis.Redis(connection_pool=self._redis_pool)
            logger.info("Redis客户端已创建")
        return self._redis_client

    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            with self.sync_engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                return result.scalar() == 1
        except SQLAlchemyError as e:
            logger.error(f"数据库连接测试失败: {e}")
            return False

    async def test_async_connection(self) -> bool:
        """测试异步数据库连接"""
        try:
            async with self.async_engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                return result.scalar() == 1
        except SQLAlchemyError as e:
            logger.error(f"异步数据库连接测试失败: {e}")
            return False

    def test_redis_connection(self) -> bool:
        """测试Redis连接"""
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis连接测试失败: {e}")
            return False

    def create_all_tables(self):
        """创建所有数据库表"""
        try:
            BaseModel.metadata.create_all(bind=self.sync_engine)
            logger.info("数据库表创建成功")
        except SQLAlchemyError as e:
            logger.error(f"创建数据库表失败: {e}")
            raise

    def drop_all_tables(self):
        """删除所有数据库表"""
        try:
            BaseModel.metadata.drop_all(bind=self.sync_engine)
            logger.info("数据库表删除成功")
        except SQLAlchemyError as e:
            logger.error(f"删除数据库表失败: {e}")
            raise

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        获取数据库会话的上下文管理器
        自动处理会话的提交、回滚和关闭
        """
        session = self.sync_session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            logger.error(f"数据库操作失败: {e}")
            session.rollback()
            raise
        finally:
            session.close()

    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        获取异步数据库会话的上下文管理器
        自动处理会话的提交、回滚和关闭
        """
        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                logger.error(f"异步数据库操作失败: {e}")
                await session.rollback()
                raise

    def close_all_connections(self):
        """关闭所有数据库连接"""
        if self._sync_engine:
            self._sync_engine.dispose()
            logger.info("同步数据库连接已关闭")

        if self._async_engine:
            self._async_engine.sync(self._async_engine.dispose())
            logger.info("异步数据库连接已关闭")

        if self._redis_client:
            self._redis_client.close()
            logger.info("Redis连接已关闭")

    def init_default_data(self):
        """初始化默认数据"""
        with self.get_session() as session:
            pass  # Auto-fixed empty block
            # 创建系统标签
            existing_labels = session.query(Label).filter_by(is_system=True).count()
            if existing_labels == 0:
                system_labels = Label.create_system_labels()
                for label in system_labels:
                    label.id = str(uuid.uuid4())
                    session.add(label)

                logger.info(f"已创建 {len(system_labels)} 个系统标签")

            # 可以在这里添加其他默认数据
            # 比如默认用户、项目模板等


# 全局数据库管理器实例
_db_manager = None


def get_db_manager() -> DatabaseManager:
    """获取数据库管理器实例（单例）"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话的依赖注入函数
    用于FastAPI等框架的依赖注入
    """
    db_manager = get_db_manager()
    with db_manager.get_session() as session:
        yield session


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取异步数据库会话的依赖注入函数
    用于FastAPI等框架的异步依赖注入
    """
    db_manager = get_db_manager()
    async with db_manager.get_async_session() as session:
        yield session


def init_db():
    """
    初始化数据库
    创建表和默认数据
    """
    db_manager = get_db_manager()

    # 测试连接
    if not db_manager.test_connection():
        raise Exception("数据库连接失败")

    # 创建表
    db_manager.create_all_tables()

    # 初始化默认数据
    db_manager.init_default_data()

    logger.info("数据库初始化完成")


def close_db():
    """关闭数据库连接"""
    db_manager = get_db_manager()
    db_manager.close_all_connections()
    logger.info("数据库连接已关闭")
