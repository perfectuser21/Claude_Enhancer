"""
会话和事务管理
==============

提供高级的数据库会话和事务管理功能:
- 事务上下文管理
- 只读事务
- 批量操作事务
- 嵌套事务
- 错误处理和重试
"""

import asyncio
import logging
from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator, Optional, Callable, Any, List
from functools import wraps
import time

from sqlalchemy import exc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from .database import get_db_session, get_async_db_session
from .config import get_database_config

# 配置日志
logger = logging.getLogger(__name__)


class TransactionError(Exception):
    """事务错误"""

    pass


class DatabaseSession:
    """
    数据库会话管理器
    ================

    提供会话的生命周期管理和错误处理
    """

    def __init__(self, session: Session, auto_commit: bool = True):
        """
        初始化会话管理器

        Args:
            session: 数据库会话
            auto_commit: 是否自动提交
        """
        self.session = session
        self.auto_commit = auto_commit
        self.transaction_depth = 0
        self.rollback_only = False

    def __enter__(self):
        """进入上下文"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        if exc_type is not None:
            self.rollback()
        elif self.auto_commit and not self.rollback_only:
            self.commit()
        else:
            self.rollback()

    def commit(self):
        """提交事务"""
        try:
            if not self.rollback_only:
                self.session.commit()
                logger.debug("事务提交成功")
            else:
                logger.warning("事务标记为回滚，跳过提交")
        except Exception as e:
            logger.error(f"事务提交失败: {e}")
            self.rollback()
            raise TransactionError(f"事务提交失败: {e}")

    def rollback(self):
        """回滚事务"""
        try:
            self.session.rollback()
            logger.debug("事务回滚成功")
        except Exception as e:
            logger.error(f"事务回滚失败: {e}")
            raise TransactionError(f"事务回滚失败: {e}")

    def flush(self):
        """刷新会话"""
        try:
            self.session.flush()
        except Exception as e:
            logger.error(f"会话刷新失败: {e}")
            self.mark_rollback_only()
            raise

    def mark_rollback_only(self):
        """标记事务为只能回滚"""
        self.rollback_only = True
        logger.warning("事务已标记为只能回滚")

    def add(self, instance):
        """添加实例到会话"""
        self.session.add(instance)

    def delete(self, instance):
        """从会话删除实例"""
        self.session.delete(instance)

    def query(self, *entities, **kwargs):
        """执行查询"""
        return self.session.query(*entities, **kwargs)

    def execute(self, statement, parameters=None):
        """执行SQL语句"""
        return self.session.execute(statement, parameters)


class AsyncDatabaseSession:
    """
    异步数据库会话管理器
    ====================

    提供异步会话的生命周期管理和错误处理
    """

    def __init__(self, session: AsyncSession, auto_commit: bool = True):
        """
        初始化异步会话管理器

        Args:
            session: 异步数据库会话
            auto_commit: 是否自动提交
        """
        self.session = session
        self.auto_commit = auto_commit
        self.transaction_depth = 0
        self.rollback_only = False

    async def __aenter__(self):
        """进入异步上下文"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出异步上下文"""
        if exc_type is not None:
            await self.rollback()
        elif self.auto_commit and not self.rollback_only:
            await self.commit()
        else:
            await self.rollback()

    async def commit(self):
        """提交事务"""
        try:
            if not self.rollback_only:
                await self.session.commit()
                logger.debug("异步事务提交成功")
            else:
                logger.warning("异步事务标记为回滚，跳过提交")
        except Exception as e:
            logger.error(f"异步事务提交失败: {e}")
            await self.rollback()
            raise TransactionError(f"异步事务提交失败: {e}")

    async def rollback(self):
        """回滚事务"""
        try:
            await self.session.rollback()
            logger.debug("异步事务回滚成功")
        except Exception as e:
            logger.error(f"异步事务回滚失败: {e}")
            raise TransactionError(f"异步事务回滚失败: {e}")

    async def flush(self):
        """刷新会话"""
        try:
            await self.session.flush()
        except Exception as e:
            logger.error(f"异步会话刷新失败: {e}")
            self.mark_rollback_only()
            raise

    def mark_rollback_only(self):
        """标记事务为只能回滚"""
        self.rollback_only = True
        logger.warning("异步事务已标记为只能回滚")

    def add(self, instance):
        """添加实例到会话"""
        self.session.add(instance)

    async def delete(self, instance):
        """从会话删除实例"""
        await self.session.delete(instance)

    async def execute(self, statement, parameters=None):
        """执行SQL语句"""
        return await self.session.execute(statement, parameters)

    async def refresh(self, instance, attribute_names=None):
        """刷新实例"""
        await self.session.refresh(instance, attribute_names)


class TransactionManager:
    """
    事务管理器
    ==========

    提供事务的高级管理功能
    """

    def __init__(self, max_retries: int = 3, retry_delay: float = 0.1):
        """
        初始化事务管理器

        Args:
            max_retries: 最大重试次数
            retry_delay: 重试延迟 (秒)
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    @contextmanager
    def transaction(
        self, read_only: bool = False
    ) -> Generator[DatabaseSession, None, None]:
        """
        同步事务上下文管理器

        Args:
            read_only: 是否为只读事务

        Yields:
            数据库会话管理器
        """
        retries = 0
        while retries <= self.max_retries:
            try:
                with get_db_session() as session:
                    # 设置只读模式
                    if read_only:
                        session.execute("SET TRANSACTION READ ONLY")

                    db_session = DatabaseSession(session, auto_commit=not read_only)
                    yield db_session
                    break

            except (exc.DisconnectionError, exc.TimeoutError) as e:
                retries += 1
                if retries > self.max_retries:
                    logger.error(f"事务重试失败，已达最大重试次数: {e}")
                    raise TransactionError(f"事务执行失败: {e}")

                logger.warning(f"事务失败，第{retries}次重试: {e}")
                time.sleep(self.retry_delay * retries)

            except Exception as e:
                logger.error(f"事务执行失败: {e}")
                raise TransactionError(f"事务执行失败: {e}")

    @asynccontextmanager
    async def async_transaction(
        self, read_only: bool = False
    ) -> AsyncGenerator[AsyncDatabaseSession, None]:
        """
        异步事务上下文管理器

        Args:
            read_only: 是否为只读事务

        Yields:
            异步数据库会话管理器
        """
        retries = 0
        while retries <= self.max_retries:
            try:
                async with get_async_db_session() as session:
                    # 设置只读模式
                    if read_only:
                        await session.execute("SET TRANSACTION READ ONLY")

                    db_session = AsyncDatabaseSession(
                        session, auto_commit=not read_only
                    )
                    yield db_session
                    break

            except (exc.DisconnectionError, exc.TimeoutError) as e:
                retries += 1
                if retries > self.max_retries:
                    logger.error(f"异步事务重试失败，已达最大重试次数: {e}")
                    raise TransactionError(f"异步事务执行失败: {e}")

                logger.warning(f"异步事务失败，第{retries}次重试: {e}")
                await asyncio.sleep(self.retry_delay * retries)

            except Exception as e:
                logger.error(f"异步事务执行失败: {e}")
                raise TransactionError(f"异步事务执行失败: {e}")

    @contextmanager
    def bulk_transaction(
        self, batch_size: int = 1000
    ) -> Generator[DatabaseSession, None, None]:
        """
        批量操作事务

        Args:
            batch_size: 批处理大小

        Yields:
            数据库会话管理器
        """
        with self.transaction() as session:
            # 设置批量操作优化
            session.session.execute("SET synchronous_commit = OFF")
            session.session.execute("SET wal_buffers = '16MB'")
            yield session


# 创建全局事务管理器
transaction_manager = TransactionManager()


# 便捷函数和装饰器


@contextmanager
def transaction(read_only: bool = False) -> Generator[DatabaseSession, None, None]:
    """
    事务上下文管理器 (便捷函数)

    Args:
        read_only: 是否为只读事务

    Yields:
        数据库会话管理器
    """
    with transaction_manager.transaction(read_only=read_only) as session:
        yield session


@asynccontextmanager
async def async_transaction(
    read_only: bool = False,
) -> AsyncGenerator[AsyncDatabaseSession, None]:
    """
    异步事务上下文管理器 (便捷函数)

    Args:
        read_only: 是否为只读事务

    Yields:
        异步数据库会话管理器
    """
    async with transaction_manager.async_transaction(read_only=read_only) as session:
        yield session


@contextmanager
def readonly_transaction() -> Generator[DatabaseSession, None, None]:
    """
    只读事务上下文管理器

    Yields:
        只读数据库会话管理器
    """
    with transaction(read_only=True) as session:
        yield session


@asynccontextmanager
async def async_readonly_transaction() -> AsyncGenerator[AsyncDatabaseSession, None]:
    """
    异步只读事务上下文管理器

    Yields:
        异步只读数据库会话管理器
    """
    async with async_transaction(read_only=True) as session:
        yield session


@contextmanager
def bulk_transaction(batch_size: int = 1000) -> Generator[DatabaseSession, None, None]:
    """
    批量操作事务上下文管理器

    Args:
        batch_size: 批处理大小

    Yields:
        数据库会话管理器
    """
    with transaction_manager.bulk_transaction(batch_size=batch_size) as session:
        yield session


def transactional(read_only: bool = False, retry: bool = True):
    """
    事务装饰器

    Args:
        read_only: 是否为只读事务
        retry: 是否启用重试

    Returns:
        装饰器函数
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 检查是否已经在事务中
            if hasattr(args[0], "session") and isinstance(args[0].session, Session):
                # 已在事务中，直接执行
                return func(*args, **kwargs)

            # 创建新事务
            manager = (
                TransactionManager() if retry else TransactionManager(max_retries=0)
            )
            with manager.transaction(read_only=read_only) as session:
                # 将会话注入到第一个参数（通常是self）
                if args and hasattr(args[0], "__dict__"):
                    original_session = getattr(args[0], "session", None)
                    args[0].session = session.session
                    try:
                        result = func(*args, **kwargs)
                        return result
                    finally:
                        if original_session:
                            args[0].session = original_session
                        else:
                            delattr(args[0], "session")
                else:
                    # 将会话作为关键字参数传递
                    kwargs["session"] = session.session
                    return func(*args, **kwargs)

        return wrapper

    return decorator


def async_transactional(read_only: bool = False, retry: bool = True):
    """
    异步事务装饰器

    Args:
        read_only: 是否为只读事务
        retry: 是否启用重试

    Returns:
        异步装饰器函数
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 检查是否已经在事务中
            if hasattr(args[0], "session") and isinstance(
                args[0].session, AsyncSession
            ):
                # 已在事务中，直接执行
                return await func(*args, **kwargs)

            # 创建新事务
            manager = (
                TransactionManager() if retry else TransactionManager(max_retries=0)
            )
            async with manager.async_transaction(read_only=read_only) as session:
                # 将会话注入到第一个参数（通常是self）
                if args and hasattr(args[0], "__dict__"):
                    original_session = getattr(args[0], "session", None)
                    args[0].session = session.session
                    try:
                        result = await func(*args, **kwargs)
                        return result
                    finally:
                        if original_session:
                            args[0].session = original_session
                        else:
                            delattr(args[0], "session")
                else:
                    # 将会话作为关键字参数传递
                    kwargs["session"] = session.session
                    return await func(*args, **kwargs)

        return wrapper

    return decorator


class BatchProcessor:
    """
    批处理器
    ========

    用于处理大量数据的批量操作
    """

    def __init__(self, batch_size: int = 1000, commit_interval: int = 10):
        """
        初始化批处理器

        Args:
            batch_size: 批处理大小
            commit_interval: 提交间隔 (批次数)
        """
        self.batch_size = batch_size
        self.commit_interval = commit_interval

    def process_items(self, items: List[Any], processor_func: Callable):
        """
        批量处理项目

        Args:
            items: 要处理的项目列表
            processor_func: 处理函数
        """
        with bulk_transaction(self.batch_size) as session:
            for i, item in enumerate(items):
                processor_func(session, item)

                # 定期刷新和提交
                if (i + 1) % self.batch_size == 0:
                    session.flush()

                if (i + 1) % (self.batch_size * self.commit_interval) == 0:
                    session.commit()
                    logger.info(f"已处理 {i + 1} 个项目")

            # 最终提交
            session.commit()
            logger.info(f"批处理完成，共处理 {len(items)} 个项目")


# 导出公共接口
__all__ = [
    "DatabaseSession",
    "AsyncDatabaseSession",
    "TransactionManager",
    "transaction_manager",
    "transaction",
    "async_transaction",
    "readonly_transaction",
    "async_readonly_transaction",
    "bulk_transaction",
    "transactional",
    "async_transactional",
    "BatchProcessor",
    "TransactionError",
]
