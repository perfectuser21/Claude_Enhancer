#!/usr/bin/env python3
"""
Perfect21连接池管理器
高性能数据库连接池、HTTP客户端池、进程池优化
"""

import os
import sys
import time
import asyncio
import threading
import multiprocessing
import sqlite3
import subprocess
from typing import Dict, Any, Optional, List, Callable, Union, ContextManager
from contextlib import contextmanager, asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from queue import Queue, Empty, Full
import weakref
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.logger import log_info, log_error
from modules.config import config

logger = logging.getLogger(__name__)

class PoolType(Enum):
    """连接池类型"""
    DATABASE = "database"
    HTTP_CLIENT = "http_client"
    SUBPROCESS = "subprocess"
    THREAD = "thread"
    ASYNCIO = "asyncio"

@dataclass
class PoolConfig:
    """连接池配置"""
    pool_type: PoolType
    min_size: int = 2
    max_size: int = 10
    timeout: float = 30.0
    max_idle_time: float = 300.0  # 5分钟
    health_check_interval: float = 60.0  # 1分钟
    retry_attempts: int = 3
    retry_delay: float = 1.0

@dataclass
class ConnectionInfo:
    """连接信息"""
    connection_id: str
    connection: Any
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    use_count: int = 0
    is_healthy: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

class ConnectionPool:
    """通用连接池基类"""

    def __init__(self, config: PoolConfig, factory_func: Callable, health_check_func: Optional[Callable] = None):
        self.config = config
        self.factory_func = factory_func
        self.health_check_func = health_check_func

        # 连接存储
        self._connections = Queue(maxsize=config.max_size)
        self._all_connections: Dict[str, ConnectionInfo] = {}
        self._connection_lock = threading.RLock()

        # 状态管理
        self._created_count = 0
        self._is_closed = False
        self._health_check_task = None

        # 统计信息
        self._stats = {
            'created': 0,
            'acquired': 0,
            'released': 0,
            'health_checks': 0,
            'failures': 0,
            'timeouts': 0
        }
        self._stats_lock = threading.Lock()

        # 初始化最小连接数
        self._initialize_pool()

        # 启动健康检查
        if health_check_func:
            self._start_health_check()

    def _initialize_pool(self):
        """初始化连接池"""
        for _ in range(self.config.min_size):
            try:
                conn_info = self._create_connection()
                if conn_info:
                    self._connections.put_nowait(conn_info)
            except Exception as e:
                logger.error(f"初始化连接池失败: {e}")

    def _create_connection(self) -> Optional[ConnectionInfo]:
        """创建新连接"""
        if self._is_closed:
            return None

        try:
            with self._connection_lock:
                if self._created_count >= self.config.max_size:
                    return None

                connection = self.factory_func()
                conn_id = f"{self.config.pool_type.value}_{self._created_count}_{int(time.time())}"

                conn_info = ConnectionInfo(
                    connection_id=conn_id,
                    connection=connection,
                    metadata={'pool_type': self.config.pool_type.value}
                )

                self._all_connections[conn_id] = conn_info
                self._created_count += 1

                with self._stats_lock:
                    self._stats['created'] += 1

                logger.debug(f"创建新连接: {conn_id}")
                return conn_info

        except Exception as e:
            with self._stats_lock:
                self._stats['failures'] += 1
            logger.error(f"创建连接失败: {e}")
            return None

    @contextmanager
    def acquire(self, timeout: Optional[float] = None):
        """获取连接（上下文管理器）"""
        timeout = timeout or self.config.timeout
        conn_info = None

        try:
            # 尝试从池中获取连接
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    conn_info = self._connections.get_nowait()
                    break
                except Empty:
                    # 池为空，尝试创建新连接
                    new_conn = self._create_connection()
                    if new_conn:
                        conn_info = new_conn
                        break
                    else:
                        time.sleep(0.1)  # 短暂等待

            if not conn_info:
                with self._stats_lock:
                    self._stats['timeouts'] += 1
                raise TimeoutError(f"获取连接超时: {timeout}秒")

            # 健康检查
            if self.health_check_func and not self._check_connection_health(conn_info):
                self._remove_connection(conn_info)
                # 递归尝试获取新连接
                with self.acquire(timeout) as new_conn:
                    yield new_conn
                return

            # 更新连接信息
            conn_info.last_used = time.time()
            conn_info.use_count += 1

            with self._stats_lock:
                self._stats['acquired'] += 1

            yield conn_info.connection

        finally:
            # 释放连接
            if conn_info:
                self._release_connection(conn_info)

    def _release_connection(self, conn_info: ConnectionInfo):
        """释放连接回池"""
        try:
            # 检查连接是否仍然有效
            if self._is_closed or not conn_info.is_healthy:
                self._remove_connection(conn_info)
                return

            # 检查闲置时间
            if time.time() - conn_info.last_used > self.config.max_idle_time:
                self._remove_connection(conn_info)
                return

            # 放回池中
            try:
                self._connections.put_nowait(conn_info)
                with self._stats_lock:
                    self._stats['released'] += 1
            except Full:
                # 池已满，关闭多余连接
                self._remove_connection(conn_info)

        except Exception as e:
            logger.error(f"释放连接失败: {e}")
            self._remove_connection(conn_info)

    def _check_connection_health(self, conn_info: ConnectionInfo) -> bool:
        """检查连接健康状态"""
        if not self.health_check_func:
            return True

        try:
            is_healthy = self.health_check_func(conn_info.connection)
            conn_info.is_healthy = is_healthy

            with self._stats_lock:
                self._stats['health_checks'] += 1

            return is_healthy

        except Exception as e:
            logger.warning(f"健康检查失败: {e}")
            conn_info.is_healthy = False
            return False

    def _remove_connection(self, conn_info: ConnectionInfo):
        """移除连接"""
        try:
            with self._connection_lock:
                if conn_info.connection_id in self._all_connections:
                    del self._all_connections[conn_info.connection_id]
                    self._created_count -= 1

            # 清理连接资源
            if hasattr(conn_info.connection, 'close'):
                conn_info.connection.close()

            logger.debug(f"移除连接: {conn_info.connection_id}")

        except Exception as e:
            logger.error(f"移除连接失败: {e}")

    def _start_health_check(self):
        """启动健康检查任务"""
        def health_check_worker():
            while not self._is_closed:
                try:
                    self._perform_health_check()
                    time.sleep(self.config.health_check_interval)
                except Exception as e:
                    logger.error(f"健康检查任务异常: {e}")

        health_thread = threading.Thread(target=health_check_worker, daemon=True)
        health_thread.start()

    def _perform_health_check(self):
        """执行健康检查"""
        with self._connection_lock:
            unhealthy_connections = []

            for conn_info in self._all_connections.values():
                if not self._check_connection_health(conn_info):
                    unhealthy_connections.append(conn_info)

            # 移除不健康的连接
            for conn_info in unhealthy_connections:
                self._remove_connection(conn_info)

    def get_stats(self) -> Dict[str, Any]:
        """获取连接池统计信息"""
        with self._stats_lock:
            stats = self._stats.copy()

        with self._connection_lock:
            current_size = len(self._all_connections)
            available_size = self._connections.qsize()

        stats.update({
            'pool_type': self.config.pool_type.value,
            'current_size': current_size,
            'available_size': available_size,
            'max_size': self.config.max_size,
            'min_size': self.config.min_size
        })

        return stats

    def close(self):
        """关闭连接池"""
        self._is_closed = True

        with self._connection_lock:
            # 关闭所有连接
            for conn_info in list(self._all_connections.values()):
                self._remove_connection(conn_info)

            # 清空队列
            while not self._connections.empty():
                try:
                    self._connections.get_nowait()
                except Empty:
                    break

        logger.info(f"连接池已关闭: {self.config.pool_type.value}")

class DatabaseConnectionPool(ConnectionPool):
    """数据库连接池"""

    def __init__(self, db_config: Dict[str, Any]):
        self.db_config = db_config

        pool_config = PoolConfig(
            pool_type=PoolType.DATABASE,
            min_size=db_config.get('pool_min_size', 2),
            max_size=db_config.get('pool_max_size', 10),
            timeout=db_config.get('pool_timeout', 30.0),
            max_idle_time=db_config.get('pool_max_idle_time', 300.0)
        )

        super().__init__(
            config=pool_config,
            factory_func=self._create_db_connection,
            health_check_func=self._check_db_health
        )

    def _create_db_connection(self):
        """创建数据库连接"""
        db_type = self.db_config.get('type', 'sqlite')

        if db_type == 'sqlite':
            db_path = self.db_config.get('path', 'data/perfect21.db')
            os.makedirs(os.path.dirname(db_path), exist_ok=True)

            conn = sqlite3.connect(db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row

            # 性能优化设置
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA cache_size = 10000")
            conn.execute("PRAGMA temp_store = MEMORY")

            return conn
        else:
            raise NotImplementedError(f"不支持的数据库类型: {db_type}")

    def _check_db_health(self, connection) -> bool:
        """检查数据库连接健康状态"""
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            return True
        except Exception:
            return False

    @contextmanager
    def execute_query(self, query: str, params: tuple = None, fetch: bool = True):
        """执行数据库查询"""
        with self.acquire() as conn:
            cursor = conn.cursor()
            try:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                if fetch and query.strip().upper().startswith('SELECT'):
                    result = [dict(row) for row in cursor.fetchall()]
                    yield result
                else:
                    conn.commit()
                    yield cursor.rowcount

            except Exception as e:
                conn.rollback()
                raise e
            finally:
                cursor.close()

class SubprocessPool(ConnectionPool):
    """子进程池"""

    def __init__(self, max_processes: int = None):
        max_processes = max_processes or min(32, (os.cpu_count() or 1) + 4)

        pool_config = PoolConfig(
            pool_type=PoolType.SUBPROCESS,
            min_size=2,
            max_size=max_processes,
            timeout=30.0,
            max_idle_time=300.0
        )

        super().__init__(
            config=pool_config,
            factory_func=self._create_subprocess_worker,
            health_check_func=self._check_subprocess_health
        )

    def _create_subprocess_worker(self):
        """创建子进程工作器"""
        # 这里创建一个可重用的Python子进程
        return {
            'type': 'subprocess_worker',
            'created_at': time.time(),
            'pid': None  # 延迟创建
        }

    def _check_subprocess_health(self, worker) -> bool:
        """检查子进程健康状态"""
        # 简单检查
        return worker.get('type') == 'subprocess_worker'

    def execute_command(self, cmd: List[str], cwd: str = None, timeout: float = 30.0) -> subprocess.CompletedProcess:
        """执行命令"""
        try:
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=cwd,
                timeout=timeout
            )
        except subprocess.TimeoutExpired as e:
            logger.error(f"命令执行超时: {' '.join(cmd)}")
            raise e
        except Exception as e:
            logger.error(f"命令执行失败: {' '.join(cmd)} - {e}")
            raise e

class AsyncConnectionPool:
    """异步连接池"""

    def __init__(self, config: PoolConfig, factory_func: Callable, health_check_func: Optional[Callable] = None):
        self.config = config
        self.factory_func = factory_func
        self.health_check_func = health_check_func

        # 连接存储
        self._connections = asyncio.Queue(maxsize=config.max_size)
        self._all_connections: Dict[str, ConnectionInfo] = {}
        self._connection_lock = asyncio.Lock()

        # 状态管理
        self._created_count = 0
        self._is_closed = False
        self._health_check_task = None

        # 统计信息
        self._stats = {
            'created': 0,
            'acquired': 0,
            'released': 0,
            'health_checks': 0,
            'failures': 0,
            'timeouts': 0
        }

        # 启动健康检查
        if health_check_func:
            self._start_health_check()

    async def _create_connection(self) -> Optional[ConnectionInfo]:
        """创建新连接"""
        if self._is_closed:
            return None

        try:
            async with self._connection_lock:
                if self._created_count >= self.config.max_size:
                    return None

                if asyncio.iscoroutinefunction(self.factory_func):
                    connection = await self.factory_func()
                else:
                    connection = self.factory_func()

                conn_id = f"async_{self.config.pool_type.value}_{self._created_count}_{int(time.time())}"

                conn_info = ConnectionInfo(
                    connection_id=conn_id,
                    connection=connection,
                    metadata={'pool_type': self.config.pool_type.value, 'async': True}
                )

                self._all_connections[conn_id] = conn_info
                self._created_count += 1
                self._stats['created'] += 1

                logger.debug(f"创建新异步连接: {conn_id}")
                return conn_info

        except Exception as e:
            self._stats['failures'] += 1
            logger.error(f"创建异步连接失败: {e}")
            return None

    @asynccontextmanager
    async def acquire(self, timeout: Optional[float] = None):
        """获取连接（异步上下文管理器）"""
        timeout = timeout or self.config.timeout
        conn_info = None

        try:
            # 尝试从池中获取连接
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    conn_info = await asyncio.wait_for(
                        self._connections.get(),
                        timeout=0.1
                    )
                    break
                except asyncio.TimeoutError:
                    # 池为空，尝试创建新连接
                    new_conn = await self._create_connection()
                    if new_conn:
                        conn_info = new_conn
                        break

            if not conn_info:
                self._stats['timeouts'] += 1
                raise TimeoutError(f"获取异步连接超时: {timeout}秒")

            # 健康检查
            if self.health_check_func and not await self._check_connection_health(conn_info):
                await self._remove_connection(conn_info)
                # 递归尝试获取新连接
                async with self.acquire(timeout) as new_conn:
                    yield new_conn
                return

            # 更新连接信息
            conn_info.last_used = time.time()
            conn_info.use_count += 1
            self._stats['acquired'] += 1

            yield conn_info.connection

        finally:
            # 释放连接
            if conn_info:
                await self._release_connection(conn_info)

    async def _release_connection(self, conn_info: ConnectionInfo):
        """释放连接回池"""
        try:
            # 检查连接是否仍然有效
            if self._is_closed or not conn_info.is_healthy:
                await self._remove_connection(conn_info)
                return

            # 检查闲置时间
            if time.time() - conn_info.last_used > self.config.max_idle_time:
                await self._remove_connection(conn_info)
                return

            # 放回池中
            try:
                await self._connections.put(conn_info)
                self._stats['released'] += 1
            except asyncio.QueueFull:
                # 池已满，关闭多余连接
                await self._remove_connection(conn_info)

        except Exception as e:
            logger.error(f"释放异步连接失败: {e}")
            await self._remove_connection(conn_info)

    async def _check_connection_health(self, conn_info: ConnectionInfo) -> bool:
        """检查连接健康状态"""
        if not self.health_check_func:
            return True

        try:
            if asyncio.iscoroutinefunction(self.health_check_func):
                is_healthy = await self.health_check_func(conn_info.connection)
            else:
                is_healthy = self.health_check_func(conn_info.connection)

            conn_info.is_healthy = is_healthy
            self._stats['health_checks'] += 1
            return is_healthy

        except Exception as e:
            logger.warning(f"异步健康检查失败: {e}")
            conn_info.is_healthy = False
            return False

    async def _remove_connection(self, conn_info: ConnectionInfo):
        """移除连接"""
        try:
            async with self._connection_lock:
                if conn_info.connection_id in self._all_connections:
                    del self._all_connections[conn_info.connection_id]
                    self._created_count -= 1

            # 清理连接资源
            if hasattr(conn_info.connection, 'close'):
                if asyncio.iscoroutinefunction(conn_info.connection.close):
                    await conn_info.connection.close()
                else:
                    conn_info.connection.close()

            logger.debug(f"移除异步连接: {conn_info.connection_id}")

        except Exception as e:
            logger.error(f"移除异步连接失败: {e}")

    def _start_health_check(self):
        """启动健康检查任务"""
        async def health_check_worker():
            while not self._is_closed:
                try:
                    await self._perform_health_check()
                    await asyncio.sleep(self.config.health_check_interval)
                except Exception as e:
                    logger.error(f"异步健康检查任务异常: {e}")

        self._health_check_task = asyncio.create_task(health_check_worker())

    async def _perform_health_check(self):
        """执行健康检查"""
        async with self._connection_lock:
            unhealthy_connections = []

            for conn_info in self._all_connections.values():
                if not await self._check_connection_health(conn_info):
                    unhealthy_connections.append(conn_info)

            # 移除不健康的连接
            for conn_info in unhealthy_connections:
                await self._remove_connection(conn_info)

    def get_stats(self) -> Dict[str, Any]:
        """获取连接池统计信息"""
        stats = self._stats.copy()
        current_size = len(self._all_connections)
        available_size = self._connections.qsize()

        stats.update({
            'pool_type': f"async_{self.config.pool_type.value}",
            'current_size': current_size,
            'available_size': available_size,
            'max_size': self.config.max_size,
            'min_size': self.config.min_size
        })

        return stats

    async def close(self):
        """关闭连接池"""
        self._is_closed = True

        # 停止健康检查任务
        if self._health_check_task and not self._health_check_task.done():
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        async with self._connection_lock:
            # 关闭所有连接
            for conn_info in list(self._all_connections.values()):
                await self._remove_connection(conn_info)

            # 清空队列
            while not self._connections.empty():
                try:
                    await asyncio.wait_for(self._connections.get(), timeout=0.1)
                except asyncio.TimeoutError:
                    break

        logger.info(f"异步连接池已关闭: {self.config.pool_type.value}")

class ConnectionPoolManager:
    """连接池管理器"""

    def __init__(self):
        self._pools: Dict[str, Union[ConnectionPool, AsyncConnectionPool]] = {}
        self._lock = threading.RLock()

    def create_database_pool(self, pool_name: str, db_config: Dict[str, Any]) -> DatabaseConnectionPool:
        """创建数据库连接池"""
        with self._lock:
            if pool_name in self._pools:
                raise ValueError(f"连接池已存在: {pool_name}")

            pool = DatabaseConnectionPool(db_config)
            self._pools[pool_name] = pool

            log_info(f"创建数据库连接池: {pool_name}")
            return pool

    def create_subprocess_pool(self, pool_name: str, max_processes: int = None) -> SubprocessPool:
        """创建子进程池"""
        with self._lock:
            if pool_name in self._pools:
                raise ValueError(f"连接池已存在: {pool_name}")

            pool = SubprocessPool(max_processes)
            self._pools[pool_name] = pool

            log_info(f"创建子进程池: {pool_name}")
            return pool

    def create_async_pool(self, pool_name: str, config: PoolConfig,
                         factory_func: Callable, health_check_func: Optional[Callable] = None) -> AsyncConnectionPool:
        """创建异步连接池"""
        with self._lock:
            if pool_name in self._pools:
                raise ValueError(f"连接池已存在: {pool_name}")

            pool = AsyncConnectionPool(config, factory_func, health_check_func)
            self._pools[pool_name] = pool

            log_info(f"创建异步连接池: {pool_name}")
            return pool

    def get_pool(self, pool_name: str) -> Optional[Union[ConnectionPool, AsyncConnectionPool]]:
        """获取连接池"""
        with self._lock:
            return self._pools.get(pool_name)

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有连接池统计信息"""
        with self._lock:
            stats = {}
            for name, pool in self._pools.items():
                try:
                    stats[name] = pool.get_stats()
                except Exception as e:
                    stats[name] = {'error': str(e)}
            return stats

    def close_pool(self, pool_name: str):
        """关闭指定连接池"""
        with self._lock:
            if pool_name in self._pools:
                pool = self._pools[pool_name]
                if hasattr(pool, 'close'):
                    if asyncio.iscoroutinefunction(pool.close):
                        # 异步池需要在事件循环中关闭
                        try:
                            loop = asyncio.get_event_loop()
                            loop.run_until_complete(pool.close())
                        except RuntimeError:
                            # 没有事件循环，创建新的
                            asyncio.run(pool.close())
                    else:
                        pool.close()

                del self._pools[pool_name]
                log_info(f"关闭连接池: {pool_name}")

    def close_all(self):
        """关闭所有连接池"""
        with self._lock:
            pool_names = list(self._pools.keys())
            for pool_name in pool_names:
                try:
                    self.close_pool(pool_name)
                except Exception as e:
                    log_error(f"关闭连接池失败: {pool_name}", e)

# 全局连接池管理器实例
connection_pool_manager = ConnectionPoolManager()

# 便捷函数
def get_database_pool(pool_name: str = 'default') -> Optional[DatabaseConnectionPool]:
    """获取数据库连接池"""
    return connection_pool_manager.get_pool(pool_name)

def get_subprocess_pool(pool_name: str = 'default') -> Optional[SubprocessPool]:
    """获取子进程池"""
    return connection_pool_manager.get_pool(pool_name)

def create_default_pools():
    """创建默认连接池"""
    try:
        # 创建默认数据库连接池
        db_config = {
            'type': config.get('database.type', 'sqlite'),
            'path': config.get('database.path', 'data/perfect21.db'),
            'pool_min_size': config.get('database.pool_min_size', 2),
            'pool_max_size': config.get('database.pool_max_size', 10),
            'pool_timeout': config.get('database.pool_timeout', 30.0)
        }
        connection_pool_manager.create_database_pool('default', db_config)

        # 创建默认子进程池
        max_processes = config.get('subprocess.max_processes', None)
        connection_pool_manager.create_subprocess_pool('default', max_processes)

        log_info("默认连接池创建完成")

    except Exception as e:
        log_error("创建默认连接池失败", e)

# 在模块加载时创建默认连接池
create_default_pools()