#!/usr/bin/env python3
"""
Perfect21 资源管理器
提供统一的资源生命周期管理，防止内存泄漏和资源未释放
支持同步和异步资源管理，连接池管理，内存监控
"""

import os
import sys
import threading
import weakref
import gc
import logging
import atexit
import asyncio
import psutil
import time
from typing import Dict, Any, List, Optional, Callable, Union, AsyncContextManager, ContextManager
from contextlib import contextmanager, asynccontextmanager
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class ResourceType(Enum):
    """资源类型枚举"""
    FILE_HANDLE = "file_handle"
    NETWORK_CONNECTION = "network_connection"
    DATABASE_CONNECTION = "database_connection"
    SUBPROCESS = "subprocess"
    THREAD = "thread"
    ASYNCIO_TASK = "asyncio_task"
    TEMPORARY_FILE = "temporary_file"
    MEMORY_BUFFER = "memory_buffer"
    OTHER = "other"

@dataclass
class ResourceInfo:
    """资源信息"""
    resource_id: str
    resource_type: ResourceType
    resource: Any
    cleanup_callback: Optional[Callable] = None
    async_cleanup_callback: Optional[Callable] = None
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    size_estimate: int = 0  # bytes
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ResourceLimits:
    """资源限制配置"""
    max_file_handles: int = 1000
    max_memory_mb: int = 1024
    max_connections: int = 100
    max_threads: int = 50
    max_async_tasks: int = 200
    cleanup_threshold_mb: int = 512
    max_idle_time: int = 300  # seconds

class ResourceTracker:
    """增强资源跟踪器"""

    def __init__(self, limits: ResourceLimits = None):
        self._resources: Dict[str, ResourceInfo] = {}
        self._lock = threading.RLock()
        self._async_lock = None  # 延迟创建，避免事件循环问题
        self._limits = limits or ResourceLimits()
        self._last_cleanup = time.time()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._monitoring_enabled = False

    def _get_async_lock(self):
        """获取异步锁，延迟创建"""
        if self._async_lock is None:
            self._async_lock = asyncio.Lock()
        return self._async_lock

    def register(self, resource_id: str, resource: Any,
                resource_type: ResourceType = ResourceType.OTHER,
                cleanup_callback: Optional[Callable] = None,
                async_cleanup_callback: Optional[Callable] = None,
                size_estimate: int = 0,
                metadata: Dict[str, Any] = None) -> bool:
        """注册资源"""
        with self._lock:
            try:
                # 检查资源限制
                if not self._check_resource_limits(resource_type, size_estimate):
                    logger.warning(f"资源限制超出，拒绝注册 {resource_id}")
                    return False

                resource_info = ResourceInfo(
                    resource_id=resource_id,
                    resource_type=resource_type,
                    resource=resource,
                    cleanup_callback=cleanup_callback,
                    async_cleanup_callback=async_cleanup_callback,
                    size_estimate=size_estimate,
                    metadata=metadata or {}
                )

                self._resources[resource_id] = resource_info
                logger.debug(f"资源已注册: {resource_id} (类型: {resource_type.value})")
                return True

            except Exception as e:
                logger.error(f"资源注册失败 {resource_id}: {e}")
                return False

    async def register_async(self, resource_id: str, resource: Any,
                           resource_type: ResourceType = ResourceType.OTHER,
                           cleanup_callback: Optional[Callable] = None,
                           async_cleanup_callback: Optional[Callable] = None,
                           size_estimate: int = 0,
                           metadata: Dict[str, Any] = None) -> bool:
        """异步注册资源"""
        async with self._get_async_lock():
            return self.register(resource_id, resource, resource_type,
                               cleanup_callback, async_cleanup_callback,
                               size_estimate, metadata)

    def _check_resource_limits(self, resource_type: ResourceType, size_estimate: int) -> bool:
        """检查资源限制"""
        current_stats = self.get_resource_stats()

        # 检查内存限制
        if size_estimate > 0:
            current_memory_mb = current_stats['total_memory_mb']
            if current_memory_mb + (size_estimate / 1024 / 1024) > self._limits.max_memory_mb:
                return False

        # 检查特定类型限制
        if resource_type == ResourceType.FILE_HANDLE:
            if current_stats['by_type'].get('file_handle', 0) >= self._limits.max_file_handles:
                return False
        elif resource_type == ResourceType.NETWORK_CONNECTION:
            if current_stats['by_type'].get('network_connection', 0) >= self._limits.max_connections:
                return False
        elif resource_type == ResourceType.ASYNCIO_TASK:
            if current_stats['by_type'].get('asyncio_task', 0) >= self._limits.max_async_tasks:
                return False

        return True

    def access_resource(self, resource_id: str) -> Optional[Any]:
        """访问资源并更新访问时间"""
        with self._lock:
            if resource_id in self._resources:
                resource_info = self._resources[resource_id]
                resource_info.last_accessed = time.time()
                resource_info.access_count += 1
                return resource_info.resource
            return None

    def get_resource_info(self, resource_id: str) -> Optional[ResourceInfo]:
        """获取资源信息"""
        with self._lock:
            return self._resources.get(resource_id)

    def unregister(self, resource_id: str) -> bool:
        """注销资源"""
        with self._lock:
            if resource_id not in self._resources:
                return False

            resource_info = self._resources[resource_id]

            # 执行同步清理回调
            if resource_info.cleanup_callback:
                try:
                    resource_info.cleanup_callback()
                except Exception as e:
                    logger.warning(f"同步清理回调执行失败 {resource_id}: {e}")

            # 如果有异步清理回调，创建任务执行
            if resource_info.async_cleanup_callback:
                try:
                    if asyncio.get_running_loop():
                        asyncio.create_task(self._async_cleanup(resource_info))
                except RuntimeError:
                    # 没有运行的事件循环，跳过异步清理
                    logger.warning(f"无事件循环，跳过异步清理 {resource_id}")

            del self._resources[resource_id]
            logger.debug(f"资源已注销: {resource_id}")
            return True

    async def unregister_async(self, resource_id: str) -> bool:
        """异步注销资源"""
        async with self._get_async_lock():
            if resource_id not in self._resources:
                return False

            resource_info = self._resources[resource_id]

            # 执行异步清理回调
            if resource_info.async_cleanup_callback:
                try:
                    await resource_info.async_cleanup_callback()
                except Exception as e:
                    logger.warning(f"异步清理回调执行失败 {resource_id}: {e}")

            # 执行同步清理回调
            if resource_info.cleanup_callback:
                try:
                    resource_info.cleanup_callback()
                except Exception as e:
                    logger.warning(f"同步清理回调执行失败 {resource_id}: {e}")

            del self._resources[resource_id]
            logger.debug(f"资源已异步注销: {resource_id}")
            return True

    async def _async_cleanup(self, resource_info: ResourceInfo):
        """执行异步清理"""
        try:
            await resource_info.async_cleanup_callback()
        except Exception as e:
            logger.warning(f"异步清理失败 {resource_info.resource_id}: {e}")

    def cleanup_all(self):
        """清理所有资源"""
        with self._lock:
            resource_ids = list(self._resources.keys())
            for resource_id in resource_ids:
                self.unregister(resource_id)
            self._resources.clear()

    async def cleanup_all_async(self):
        """异步清理所有资源"""
        async with self._get_async_lock():
            resource_ids = list(self._resources.keys())
            cleanup_tasks = []

            for resource_id in resource_ids:
                cleanup_tasks.append(self.unregister_async(resource_id))

            if cleanup_tasks:
                await asyncio.gather(*cleanup_tasks, return_exceptions=True)

            self._resources.clear()

    def cleanup_idle_resources(self, max_idle_time: int = None) -> int:
        """清理闲置资源"""
        max_idle_time = max_idle_time or self._limits.max_idle_time
        current_time = time.time()
        cleaned_count = 0

        with self._lock:
            idle_resources = []
            for resource_id, resource_info in self._resources.items():
                if current_time - resource_info.last_accessed > max_idle_time:
                    idle_resources.append(resource_id)

            for resource_id in idle_resources:
                if self.unregister(resource_id):
                    cleaned_count += 1

        if cleaned_count > 0:
            logger.info(f"清理了 {cleaned_count} 个闲置资源")

        return cleaned_count

    def get_resource_count(self) -> int:
        """获取当前资源数量"""
        with self._lock:
            return len(self._resources)

    def get_resource_stats(self) -> Dict[str, Any]:
        """获取资源统计信息"""
        with self._lock:
            stats = {
                'total_count': len(self._resources),
                'by_type': defaultdict(int),
                'total_memory_mb': 0,
                'avg_access_count': 0,
                'oldest_resource': None,
                'most_accessed': None
            }

            if not self._resources:
                return dict(stats)

            total_access_count = 0
            oldest_time = float('inf')
            max_access_count = 0

            for resource_info in self._resources.values():
                stats['by_type'][resource_info.resource_type.value] += 1
                stats['total_memory_mb'] += resource_info.size_estimate / 1024 / 1024
                total_access_count += resource_info.access_count

                if resource_info.created_at < oldest_time:
                    oldest_time = resource_info.created_at
                    stats['oldest_resource'] = resource_info.resource_id

                if resource_info.access_count > max_access_count:
                    max_access_count = resource_info.access_count
                    stats['most_accessed'] = resource_info.resource_id

            stats['avg_access_count'] = total_access_count / len(self._resources)
            return dict(stats)

    def start_monitoring(self):
        """启动资源监控"""
        if not self._monitoring_enabled:
            self._monitoring_enabled = True
            try:
                if asyncio.get_running_loop():
                    self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            except RuntimeError:
                pass  # 没有运行的事件循环

    def stop_monitoring(self):
        """停止资源监控"""
        self._monitoring_enabled = False
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()

    async def _periodic_cleanup(self):
        """定期清理任务"""
        while self._monitoring_enabled:
            try:
                # 检查是否需要清理
                stats = self.get_resource_stats()
                if stats['total_memory_mb'] > self._limits.cleanup_threshold_mb:
                    cleaned = self.cleanup_idle_resources()
                    if cleaned > 0:
                        logger.info(f"定期清理完成，释放了 {cleaned} 个资源")

                await asyncio.sleep(60)  # 每分钟检查一次

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"定期清理任务异常: {e}")

class ConnectionPool:
    """连接池管理器"""

    def __init__(self, factory: Callable, max_size: int = 10,
                 cleanup_callback: Optional[Callable] = None):
        self._factory = factory
        self._max_size = max_size
        self._cleanup_callback = cleanup_callback
        self._pool: List[Any] = []
        self._active_connections: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._async_lock = asyncio.Lock()
        self._created_count = 0

    def acquire(self, timeout: float = 10.0) -> Optional[Any]:
        """获取连接"""
        with self._lock:
            # 尝试从池中获取
            if self._pool:
                return self._pool.pop()

            # 如果池为空且未达到最大连接数，创建新连接
            if len(self._active_connections) < self._max_size:
                connection = self._factory()
                conn_id = f"conn_{self._created_count}"
                self._created_count += 1
                self._active_connections[conn_id] = connection
                return connection

            return None  # 池已满

    async def acquire_async(self, timeout: float = 10.0) -> Optional[Any]:
        """异步获取连接"""
        async with self._async_lock:
            return self.acquire(timeout)

    def release(self, connection: Any) -> bool:
        """释放连接回池"""
        with self._lock:
            # 找到连接ID
            conn_id = None
            for cid, conn in self._active_connections.items():
                if conn is connection:
                    conn_id = cid
                    break

            if conn_id:
                del self._active_connections[conn_id]

                # 如果池未满，放回池中
                if len(self._pool) < self._max_size:
                    self._pool.append(connection)
                    return True
                else:
                    # 池已满，清理连接
                    if self._cleanup_callback:
                        try:
                            self._cleanup_callback(connection)
                        except Exception as e:
                            logger.warning(f"连接清理失败: {e}")
                    return True

            return False

    async def release_async(self, connection: Any) -> bool:
        """异步释放连接"""
        async with self._async_lock:
            return self.release(connection)

    def close_all(self):
        """关闭所有连接"""
        with self._lock:
            # 清理池中的连接
            for connection in self._pool:
                if self._cleanup_callback:
                    try:
                        self._cleanup_callback(connection)
                    except Exception as e:
                        logger.warning(f"池连接清理失败: {e}")

            # 清理活跃连接
            for connection in self._active_connections.values():
                if self._cleanup_callback:
                    try:
                        self._cleanup_callback(connection)
                    except Exception as e:
                        logger.warning(f"活跃连接清理失败: {e}")

            self._pool.clear()
            self._active_connections.clear()

    def get_stats(self) -> Dict[str, Any]:
        """获取连接池统计"""
        with self._lock:
            return {
                'pool_size': len(self._pool),
                'active_connections': len(self._active_connections),
                'max_size': self._max_size,
                'total_created': self._created_count
            }

class ResourceManager:
    """增强版Perfect21资源管理器"""

    _instance = None
    _lock = threading.RLock()

    def __new__(cls, limits: ResourceLimits = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, limits: ResourceLimits = None):
        if hasattr(self, '_initialized'):
            return

        self._initialized = True
        self._limits = limits or ResourceLimits()
        self._tracker = ResourceTracker(self._limits)
        self._managed_objects = weakref.WeakSet()
        self._connection_pools: Dict[str, ConnectionPool] = {}
        self._cleanup_registered = False
        self._is_shutting_down = False
        self._memory_monitor_task: Optional[asyncio.Task] = None

        # 性能监控
        self._last_memory_check = time.time()
        self._memory_history: List[Dict[str, Any]] = []

        # 注册退出时清理
        if not self._cleanup_registered:
            atexit.register(self._emergency_cleanup)
            self._cleanup_registered = True

        # 监控会在需要时手动启动，避免初始化时卡死
        # self._tracker.start_monitoring()

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.cleanup_all()

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.cleanup_all_async()

    def register_resource(self, resource_id: str, resource: Any,
                         resource_type: ResourceType = ResourceType.OTHER,
                         cleanup_callback: Optional[Callable] = None,
                         async_cleanup_callback: Optional[Callable] = None,
                         size_estimate: int = 0,
                         metadata: Dict[str, Any] = None) -> bool:
        """注册需要管理的资源"""
        if self._is_shutting_down:
            logger.warning(f"系统正在关闭，忽略资源注册: {resource_id}")
            return False

        try:
            success = self._tracker.register(
                resource_id, resource, resource_type,
                cleanup_callback, async_cleanup_callback,
                size_estimate, metadata
            )

            if success:
                # 只对支持弱引用的对象添加到WeakSet
                try:
                    self._managed_objects.add(resource)
                except TypeError:
                    # 对于不支持弱引用的对象（如字符串、数字等），跳过WeakSet管理
                    pass
                logger.debug(f"资源已注册: {resource_id} (类型: {resource_type.value})")

            return success
        except Exception as e:
            logger.error(f"资源注册失败 {resource_id}: {e}")
            return False

    async def register_resource_async(self, resource_id: str, resource: Any,
                                     resource_type: ResourceType = ResourceType.OTHER,
                                     cleanup_callback: Optional[Callable] = None,
                                     async_cleanup_callback: Optional[Callable] = None,
                                     size_estimate: int = 0,
                                     metadata: Dict[str, Any] = None) -> bool:
        """异步注册资源"""
        return await self._tracker.register_async(
            resource_id, resource, resource_type,
            cleanup_callback, async_cleanup_callback,
            size_estimate, metadata
        )

    def unregister_resource(self, resource_id: str) -> bool:
        """注销资源"""
        try:
            resource_info = self._tracker.get_resource_info(resource_id)
            success = self._tracker.unregister(resource_id)
            if success and resource_info:
                logger.debug(f"资源已注销: {resource_id}")
            return success
        except Exception as e:
            logger.error(f"资源注销失败 {resource_id}: {e}")
            return False

    async def unregister_resource_async(self, resource_id: str) -> bool:
        """异步注销资源"""
        try:
            success = await self._tracker.unregister_async(resource_id)
            if success:
                logger.debug(f"资源已异步注销: {resource_id}")
            return success
        except Exception as e:
            logger.error(f"异步资源注销失败 {resource_id}: {e}")
            return False

    def access_resource(self, resource_id: str) -> Optional[Any]:
        """访问资源"""
        return self._tracker.access_resource(resource_id)

    def create_connection_pool(self, pool_name: str, factory: Callable,
                             max_size: int = 10, cleanup_callback: Optional[Callable] = None) -> ConnectionPool:
        """创建连接池"""
        if pool_name in self._connection_pools:
            logger.warning(f"连接池 {pool_name} 已存在")
            return self._connection_pools[pool_name]

        pool = ConnectionPool(factory, max_size, cleanup_callback)
        self._connection_pools[pool_name] = pool

        # 注册连接池为资源
        self.register_resource(
            f"connection_pool_{pool_name}",
            pool,
            ResourceType.OTHER,
            cleanup_callback=lambda: pool.close_all()
        )

        logger.info(f"连接池 {pool_name} 已创建，最大连接数: {max_size}")
        return pool

    def get_connection_pool(self, pool_name: str) -> Optional[ConnectionPool]:
        """获取连接池"""
        return self._connection_pools.get(pool_name)

    def cleanup_all(self):
        """清理所有资源"""
        if self._is_shutting_down:
            return

        self._is_shutting_down = True

        try:
            logger.info("开始清理所有资源...")

            # 停止监控
            self._tracker.stop_monitoring()

            # 清理连接池
            for pool_name, pool in self._connection_pools.items():
                try:
                    pool.close_all()
                    logger.debug(f"连接池 {pool_name} 已清理")
                except Exception as e:
                    logger.warning(f"连接池 {pool_name} 清理失败: {e}")
            self._connection_pools.clear()

            # 清理跟踪的资源
            self._tracker.cleanup_all()

            # 停止内存监控任务
            if self._memory_monitor_task and not self._memory_monitor_task.done():
                self._memory_monitor_task.cancel()

            # 强制垃圾回收
            gc.collect()

            logger.info("资源清理完成")
        except Exception as e:
            logger.error(f"资源清理失败: {e}")
        finally:
            self._is_shutting_down = False

    async def cleanup_all_async(self):
        """异步清理所有资源"""
        if self._is_shutting_down:
            return

        self._is_shutting_down = True

        try:
            logger.info("开始异步清理所有资源...")

            # 停止监控
            self._tracker.stop_monitoring()

            # 异步清理连接池
            pool_cleanup_tasks = []
            for pool_name, pool in self._connection_pools.items():
                pool_cleanup_tasks.append(self._cleanup_pool_async(pool_name, pool))

            if pool_cleanup_tasks:
                await asyncio.gather(*pool_cleanup_tasks, return_exceptions=True)
            self._connection_pools.clear()

            # 异步清理跟踪的资源
            await self._tracker.cleanup_all_async()

            # 停止内存监控任务
            if self._memory_monitor_task and not self._memory_monitor_task.done():
                self._memory_monitor_task.cancel()
                try:
                    await self._memory_monitor_task
                except asyncio.CancelledError:
                    pass

            # 强制垃圾回收
            gc.collect()

            logger.info("异步资源清理完成")
        except Exception as e:
            logger.error(f"异步资源清理失败: {e}")
        finally:
            self._is_shutting_down = False

    async def _cleanup_pool_async(self, pool_name: str, pool: ConnectionPool):
        """异步清理连接池"""
        try:
            # 在executor中运行同步清理
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, pool.close_all)
            logger.debug(f"连接池 {pool_name} 已异步清理")
        except Exception as e:
            logger.warning(f"连接池 {pool_name} 异步清理失败: {e}")

    def get_memory_usage(self) -> Dict[str, Any]:
        """获取内存使用情况"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()

            return {
                'rss_mb': memory_info.rss / 1024 / 1024,
                'vms_mb': memory_info.vms / 1024 / 1024,
                'percent': memory_percent,
                'available_mb': psutil.virtual_memory().available / 1024 / 1024
            }
        except Exception as e:
            logger.warning(f"获取内存使用情况失败: {e}")
            return {}

    def check_memory_pressure(self) -> bool:
        """检查内存压力"""
        try:
            memory_usage = self.get_memory_usage()
            if memory_usage.get('percent', 0) > 85:  # 内存使用超过85%
                return True
            if memory_usage.get('available_mb', float('inf')) < 100:  # 可用内存少于100MB
                return True
            return False
        except Exception:
            return False

    def cleanup_on_memory_pressure(self) -> int:
        """内存压力时的清理"""
        if not self.check_memory_pressure():
            return 0

        logger.warning("检测到内存压力，开始清理闲置资源")
        cleaned = self._tracker.cleanup_idle_resources(max_idle_time=60)  # 清理60秒未使用的资源

        if cleaned > 0:
            gc.collect()  # 强制垃圾回收
            logger.info(f"内存压力清理完成，释放了 {cleaned} 个资源")

        return cleaned

    def get_status(self) -> Dict[str, Any]:
        """获取资源管理状态"""
        status = {
            'resource_stats': self._tracker.get_resource_stats(),
            'managed_objects': len(self._managed_objects),
            'is_shutting_down': self._is_shutting_down,
            'memory_usage': self.get_memory_usage(),
            'connection_pools': {}
        }

        # 连接池状态
        for pool_name, pool in self._connection_pools.items():
            status['connection_pools'][pool_name] = pool.get_stats()

        return status

    def _emergency_cleanup(self):
        """紧急清理 - 程序退出时调用"""
        try:
            if hasattr(self, '_tracker'):
                self._tracker.cleanup_all()
        except Exception:
            pass  # 退出时忽略所有异常

# 异步文件管理器
@asynccontextmanager
async def managed_file(file_path: str, mode: str = 'r', encoding: str = 'utf-8'):
    """异步文件上下文管理器"""
    file_handle = None
    resource_id = f"file_{id(file_path)}_{time.time()}"

    try:
        # 异步打开文件
        import aiofiles
        file_handle = await aiofiles.open(file_path, mode, encoding=encoding)

        # 注册到资源管理器
        resource_manager = ResourceManager()
        await resource_manager.register_resource_async(
            resource_id,
            file_handle,
            ResourceType.FILE_HANDLE,
            async_cleanup_callback=lambda: file_handle.close() if file_handle else None
        )

        yield file_handle

    except Exception as e:
        logger.error(f"文件操作失败 {file_path}: {e}")
        raise
    finally:
        if file_handle:
            try:
                await file_handle.close()
                resource_manager = ResourceManager()
                await resource_manager.unregister_resource_async(resource_id)
            except Exception as e:
                logger.warning(f"文件关闭失败 {file_path}: {e}")

# 数据库连接管理器
@contextmanager
def managed_db_connection(db_manager, readonly: bool = False):
    """数据库连接上下文管理器"""
    conn = None
    resource_id = f"db_conn_{id(db_manager)}_{time.time()}"

    try:
        with db_manager.get_connection(readonly=readonly) as connection:
            conn = connection

            # 注册到资源管理器
            resource_manager = ResourceManager()
            resource_manager.register_resource(
                resource_id,
                conn,
                ResourceType.DATABASE_CONNECTION,
                cleanup_callback=lambda: conn.close() if hasattr(conn, 'close') else None
            )

            yield conn

    except Exception as e:
        logger.error(f"数据库连接失败: {e}")
        raise
    finally:
        if conn:
            try:
                resource_manager = ResourceManager()
                resource_manager.unregister_resource(resource_id)
            except Exception as e:
                logger.warning(f"数据库连接清理失败: {e}")

# 全局资源管理器实例
_resource_manager_instance = None

def get_resource_manager(limits: ResourceLimits = None) -> ResourceManager:
    """获取全局资源管理器实例"""
    global _resource_manager_instance
    if _resource_manager_instance is None:
        _resource_manager_instance = ResourceManager(limits)
    return _resource_manager_instance

class ManagedPerfect21:
    """受管理的Perfect21实例"""

    def __init__(self, limits: ResourceLimits = None):
        self._perfect21 = None
        self._resource_manager = get_resource_manager(limits)
        self._resource_id = f"perfect21_{id(self)}"
        self._async_mode = False

    def __enter__(self):
        """上下文管理器入口"""
        try:
            # modules层不能导入main层
            # Perfect21实例应该由上层传入
            self._perfect21 = None  # 需要依赖注入

            # 注册到资源管理器
            self._resource_manager.register_resource(
                self._resource_id,
                self._perfect21,
                ResourceType.OTHER,
                cleanup_callback=self._cleanup_perfect21
            )

            return self._perfect21
        except Exception as e:
            logger.error(f"Perfect21初始化失败: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self._cleanup()

    async def __aenter__(self):
        """异步上下文管理器入口"""
        self._async_mode = True
        try:
            # 在executor中初始化Perfect21
            loop = asyncio.get_event_loop()
            self._perfect21 = await loop.run_in_executor(None, self._init_perfect21)

            # 异步注册到资源管理器
            await self._resource_manager.register_resource_async(
                self._resource_id,
                self._perfect21,
                ResourceType.OTHER,
                cleanup_callback=self._cleanup_perfect21,
                async_cleanup_callback=self._async_cleanup_perfect21
            )

            return self._perfect21
        except Exception as e:
            logger.error(f"Perfect21异步初始化失败: {e}")
            raise

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self._cleanup_async()

    def _init_perfect21(self):
        """初始化Perfect21（在executor中运行）"""
        # modules层不能导入main层
        # Perfect21实例应该由上层传入
        return None  # 需要依赖注入

    def _cleanup_perfect21(self):
        """清理Perfect21实例"""
        if self._perfect21:
            try:
                # 如果Perfect21有清理方法，调用它
                if hasattr(self._perfect21, 'cleanup'):
                    self._perfect21.cleanup()

                # 清理属性引用
                self._clear_perfect21_attributes()

            except Exception as e:
                logger.warning(f"Perfect21清理时出现警告: {e}")
            finally:
                self._perfect21 = None

    async def _async_cleanup_perfect21(self):
        """异步清理Perfect21实例"""
        if self._perfect21:
            try:
                # 在executor中运行清理
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, self._cleanup_perfect21)
            except Exception as e:
                logger.warning(f"Perfect21异步清理时出现警告: {e}")

    def _clear_perfect21_attributes(self):
        """清理Perfect21属性"""
        if not self._perfect21:
            return

        attrs_to_clear = [
            'git_hooks', 'workflow_manager', 'branch_manager',
            'capability_registry', 'agent_registry', 'execution_context'
        ]

        for attr in attrs_to_clear:
            if hasattr(self._perfect21, attr):
                try:
                    setattr(self._perfect21, attr, None)
                except Exception as e:
                    logger.debug(f"清理属性 {attr} 失败: {e}")

    def _cleanup(self):
        """清理资源"""
        try:
            self._resource_manager.unregister_resource(self._resource_id)
        except Exception as e:
            logger.warning(f"资源清理时出现警告: {e}")

    async def _cleanup_async(self):
        """异步清理资源"""
        try:
            await self._resource_manager.unregister_resource_async(self._resource_id)
        except Exception as e:
            logger.warning(f"异步资源清理时出现警告: {e}")

@contextmanager
def managed_perfect21(limits: ResourceLimits = None):
    """创建受管理的Perfect21实例的上下文管理器"""
    managed = ManagedPerfect21(limits)
    try:
        with managed as p21:
            yield p21
    finally:
        pass  # cleanup已在__exit__中处理

@asynccontextmanager
async def managed_perfect21_async(limits: ResourceLimits = None):
    """创建受管理的Perfect21实例的异步上下文管理器"""
    managed = ManagedPerfect21(limits)
    try:
        async with managed as p21:
            yield p21
    finally:
        pass  # cleanup已在__aexit__中处理

# 保持向后兼容性的ResourcePool（现在基于新的ConnectionPool）
class ResourcePool:
    """资源池 - 用于复用昂贵的资源（兼容性包装）"""

    def __init__(self, max_size: int = 10):
        self._max_size = max_size
        self._resource_manager = get_resource_manager()
        self._pool_id = f"legacy_pool_{id(self)}"
        self._connection_pool = None

    def _ensure_pool(self, factory: Callable):
        """确保连接池存在"""
        if self._connection_pool is None:
            def cleanup_resource(resource):
                try:
                    if hasattr(resource, 'cleanup'):
                        resource.cleanup()
                    elif hasattr(resource, 'close'):
                        resource.close()
                except Exception as e:
                    logger.warning(f"资源清理失败: {e}")

            self._connection_pool = self._resource_manager.create_connection_pool(
                self._pool_id, factory, self._max_size, cleanup_resource
            )

    def get_resource(self, factory: Callable, *args, **kwargs):
        """从池中获取资源"""
        # 创建工厂函数包装器
        def wrapped_factory():
            return factory(*args, **kwargs)

        self._ensure_pool(wrapped_factory)
        return self._connection_pool.acquire()

    def return_resource(self, resource):
        """将资源返回池中"""
        if self._connection_pool:
            self._connection_pool.release(resource)

    def _cleanup_resource(self, resource):
        """清理单个资源（保持兼容性）"""
        try:
            if hasattr(resource, 'cleanup'):
                resource.cleanup()
            elif hasattr(resource, 'close'):
                resource.close()
        except Exception as e:
            logger.warning(f"资源清理失败: {e}")

    def clear_pool(self):
        """清空资源池"""
        if self._connection_pool:
            self._connection_pool.close_all()
        # 注销连接池
        self._resource_manager.unregister_resource(f"connection_pool_{self._pool_id}")
        self._connection_pool = None

# 使用已定义的函数
# 便捷访问
resource_manager = get_resource_manager()

def cleanup_on_exit():
    """程序退出时的清理函数"""
    resource_manager.cleanup_all()

# 注册退出清理
atexit.register(cleanup_on_exit)

# 导出主要类和函数
__all__ = [
    'ResourceType', 'ResourceInfo', 'ResourceLimits',
    'ResourceTracker', 'ResourceManager', 'ConnectionPool',
    'ManagedPerfect21', 'ResourcePool',
    'managed_perfect21', 'managed_perfect21_async',
    'managed_file', 'managed_db_connection',
    'get_resource_manager', 'resource_manager'
]