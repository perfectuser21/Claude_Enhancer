#!/usr/bin/env python3
"""
Perfect21高性能缓存层
专为Perfect21优化的多层缓存系统，支持Git操作、模块加载、数据库查询等缓存
"""

import os
import sys
import time
import json
import pickle
import hashlib
import asyncio
import threading
from typing import Dict, Any, Optional, Union, Callable, List
from datetime import datetime, timedelta
from functools import wraps, lru_cache
from contextlib import contextmanager
import weakref
import gc

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.logger import log_info, log_error
from modules.config import config

class AsyncLRUCache:
    """异步LRU缓存实现"""

    def __init__(self, maxsize: int = 256, ttl: int = 3600):
        self.maxsize = maxsize
        self.ttl = ttl
        self.cache = {}
        self.access_times = {}
        self.expire_times = {}
        self.lock = asyncio.Lock()

    async def get(self, key: str) -> Any:
        async with self.lock:
            if key not in self.cache:
                return None

            # 检查过期
            if time.time() > self.expire_times.get(key, 0):
                await self._remove(key)
                return None

            # 更新访问时间
            self.access_times[key] = time.time()
            return self.cache[key]

    async def set(self, key: str, value: Any, ttl: int = None) -> None:
        async with self.lock:
            # 如果缓存已满，删除最久未访问的项
            if len(self.cache) >= self.maxsize and key not in self.cache:
                await self._evict_lru()

            expire_time = time.time() + (ttl or self.ttl)
            self.cache[key] = value
            self.access_times[key] = time.time()
            self.expire_times[key] = expire_time

    async def _remove(self, key: str) -> None:
        """移除缓存项"""
        self.cache.pop(key, None)
        self.access_times.pop(key, None)
        self.expire_times.pop(key, None)

    async def _evict_lru(self) -> None:
        """移除最久未访问的项"""
        if not self.access_times:
            return

        lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        await self._remove(lru_key)

    async def clear(self) -> None:
        async with self.lock:
            self.cache.clear()
            self.access_times.clear()
            self.expire_times.clear()

class MemoryPool:
    """内存池管理器 - 重用对象减少GC压力"""

    def __init__(self, factory_func: Callable, initial_size: int = 10, max_size: int = 100):
        self.factory_func = factory_func
        self.max_size = max_size
        self.pool = []
        self.lock = threading.RLock()

        # 预分配对象
        for _ in range(initial_size):
            self.pool.append(factory_func())

    def acquire(self):
        """获取对象"""
        with self.lock:
            if self.pool:
                return self.pool.pop()
            else:
                return self.factory_func()

    def release(self, obj):
        """释放对象回池"""
        with self.lock:
            if len(self.pool) < self.max_size:
                # 重置对象状态
                if hasattr(obj, 'reset'):
                    obj.reset()
                self.pool.append(obj)

class LazyLoadCache:
    """懒加载缓存 - 避免启动时加载所有模块"""

    def __init__(self):
        self._cache = {}
        self._loading = set()
        self._lock = threading.RLock()

    def get_or_load(self, key: str, loader: Callable) -> Any:
        """获取或加载资源"""
        with self._lock:
            if key in self._cache:
                return self._cache[key]

            if key in self._loading:
                # 避免重复加载
                return None

            self._loading.add(key)

        try:
            # 在锁外执行加载避免阻塞
            value = loader()
            with self._lock:
                self._cache[key] = value
                self._loading.discard(key)
            return value
        except Exception as e:
            with self._lock:
                self._loading.discard(key)
            log_error(f"懒加载失败: {key}", e)
            return None

class GitOperationCache:
    """Git操作专用缓存 - 高频Git命令优化"""

    def __init__(self, cache_timeout: int = 30):
        self.cache_timeout = cache_timeout
        self._cache = {}
        self._lock = threading.RLock()

        # Git状态相关的缓存键
        self.status_keys = ['status', 'branch', 'remote', 'log']

    def get_cached_result(self, cmd_key: str, project_root: str = None) -> Optional[Any]:
        """获取缓存的Git命令结果"""
        cache_key = f"{project_root or '.'}:{cmd_key}"

        with self._lock:
            if cache_key in self._cache:
                result, timestamp = self._cache[cache_key]
                if time.time() - timestamp < self.cache_timeout:
                    return result
                else:
                    del self._cache[cache_key]

        return None

    def cache_result(self, cmd_key: str, result: Any, project_root: str = None) -> None:
        """缓存Git命令结果"""
        cache_key = f"{project_root or '.'}:{cmd_key}"

        with self._lock:
            self._cache[cache_key] = (result, time.time())

    def invalidate_status(self, project_root: str = None) -> None:
        """使状态相关缓存失效"""
        prefix = f"{project_root or '.'}:"

        with self._lock:
            keys_to_remove = [
                key for key in self._cache.keys()
                if key.startswith(prefix) and any(status_key in key for status_key in self.status_keys)
            ]
            for key in keys_to_remove:
                del self._cache[key]

class DatabaseQueryCache:
    """数据库查询缓存 - 优化重复查询"""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache = {}
        self._access_order = []
        self._lock = threading.RLock()

    def _make_key(self, query: str, params: tuple = None) -> str:
        """生成查询缓存键"""
        key_str = query
        if params:
            key_str += str(params)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, query: str, params: tuple = None) -> Optional[Any]:
        """获取缓存的查询结果"""
        key = self._make_key(query, params)

        with self._lock:
            if key in self._cache:
                result, expire_time = self._cache[key]
                if time.time() < expire_time:
                    # 更新访问顺序
                    if key in self._access_order:
                        self._access_order.remove(key)
                    self._access_order.append(key)
                    return result
                else:
                    del self._cache[key]
                    if key in self._access_order:
                        self._access_order.remove(key)

        return None

    def set(self, query: str, result: Any, params: tuple = None, ttl: int = None) -> None:
        """缓存查询结果"""
        key = self._make_key(query, params)
        expire_time = time.time() + (ttl or self.default_ttl)

        with self._lock:
            # 如果缓存已满，移除最旧的项
            if len(self._cache) >= self.max_size and key not in self._cache:
                if self._access_order:
                    oldest_key = self._access_order.pop(0)
                    self._cache.pop(oldest_key, None)

            self._cache[key] = (result, expire_time)
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)

class PerformanceCache:
    """Perfect21高性能缓存系统"""

    def __init__(self):
        self.async_cache = AsyncLRUCache(
            maxsize=config.get('performance.cache.async_maxsize', 512),
            ttl=config.get('performance.cache.async_ttl', 3600)
        )

        self.git_cache = GitOperationCache(
            cache_timeout=config.get('performance.cache.git_timeout', 30)
        )

        self.db_cache = DatabaseQueryCache(
            max_size=config.get('performance.cache.db_maxsize', 1000),
            default_ttl=config.get('performance.cache.db_ttl', 300)
        )

        self.lazy_loader = LazyLoadCache()

        # 内存池
        self.dict_pool = MemoryPool(dict, initial_size=50, max_size=200)
        self.list_pool = MemoryPool(list, initial_size=50, max_size=200)

        # 性能统计
        self._stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'lazy_loads': 0,
            'memory_pool_reuses': 0
        }

        self._lock = threading.RLock()

        log_info("高性能缓存系统初始化完成")

    # 异步缓存方法
    async def async_get(self, key: str) -> Any:
        """异步获取缓存"""
        result = await self.async_cache.get(key)
        with self._lock:
            if result is not None:
                self._stats['cache_hits'] += 1
            else:
                self._stats['cache_misses'] += 1
        return result

    async def async_set(self, key: str, value: Any, ttl: int = None) -> None:
        """异步设置缓存"""
        await self.async_cache.set(key, value, ttl)

    # Git缓存方法
    def get_git_result(self, cmd_key: str, project_root: str = None) -> Optional[Any]:
        """获取Git操作缓存结果"""
        result = self.git_cache.get_cached_result(cmd_key, project_root)
        with self._lock:
            if result is not None:
                self._stats['cache_hits'] += 1
            else:
                self._stats['cache_misses'] += 1
        return result

    def cache_git_result(self, cmd_key: str, result: Any, project_root: str = None) -> None:
        """缓存Git操作结果"""
        self.git_cache.cache_result(cmd_key, result, project_root)

    def invalidate_git_status(self, project_root: str = None) -> None:
        """使Git状态缓存失效"""
        self.git_cache.invalidate_status(project_root)

    # 数据库缓存方法
    def get_db_result(self, query: str, params: tuple = None) -> Optional[Any]:
        """获取数据库查询缓存结果"""
        result = self.db_cache.get(query, params)
        with self._lock:
            if result is not None:
                self._stats['cache_hits'] += 1
            else:
                self._stats['cache_misses'] += 1
        return result

    def cache_db_result(self, query: str, result: Any, params: tuple = None, ttl: int = None) -> None:
        """缓存数据库查询结果"""
        self.db_cache.set(query, result, params, ttl)

    # 懒加载方法
    def lazy_load(self, key: str, loader: Callable) -> Any:
        """懒加载资源"""
        result = self.lazy_loader.get_or_load(key, loader)
        if result is not None:
            with self._lock:
                self._stats['lazy_loads'] += 1
        return result

    # 内存池方法
    @contextmanager
    def get_dict(self):
        """从内存池获取字典"""
        obj = self.dict_pool.acquire()
        with self._lock:
            self._stats['memory_pool_reuses'] += 1
        try:
            yield obj
        finally:
            obj.clear()  # 清空内容
            self.dict_pool.release(obj)

    @contextmanager
    def get_list(self):
        """从内存池获取列表"""
        obj = self.list_pool.acquire()
        with self._lock:
            self._stats['memory_pool_reuses'] += 1
        try:
            yield obj
        finally:
            obj.clear()  # 清空内容
            self.list_pool.release(obj)

    # 装饰器
    def cache_function(self, ttl: int = 3600, key_func: Callable = None):
        """函数结果缓存装饰器"""
        def decorator(func):
            cache_dict = {}
            cache_times = {}

            @wraps(func)
            def wrapper(*args, **kwargs):
                # 生成缓存键
                if key_func:
                    cache_key = key_func(*args, **kwargs)
                else:
                    cache_key = f"{func.__name__}:{hash((args, tuple(sorted(kwargs.items()))))}"

                # 检查缓存
                if cache_key in cache_dict:
                    if time.time() - cache_times[cache_key] < ttl:
                        with self._lock:
                            self._stats['cache_hits'] += 1
                        return cache_dict[cache_key]
                    else:
                        del cache_dict[cache_key]
                        del cache_times[cache_key]

                # 执行函数并缓存结果
                result = func(*args, **kwargs)
                cache_dict[cache_key] = result
                cache_times[cache_key] = time.time()

                with self._lock:
                    self._stats['cache_misses'] += 1

                return result

            return wrapper
        return decorator

    def async_cache_function(self, ttl: int = 3600):
        """异步函数缓存装饰器"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                cache_key = f"{func.__name__}:{hash((args, tuple(sorted(kwargs.items()))))}"

                # 尝试从缓存获取
                cached_result = await self.async_get(cache_key)
                if cached_result is not None:
                    return cached_result

                # 执行函数并缓存结果
                result = await func(*args, **kwargs)
                await self.async_set(cache_key, result, ttl)

                return result

            return wrapper
        return decorator

    # 性能监控
    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        with self._lock:
            total_requests = self._stats['cache_hits'] + self._stats['cache_misses']
            hit_rate = (self._stats['cache_hits'] / total_requests * 100) if total_requests > 0 else 0

            return {
                'cache_hit_rate': f"{hit_rate:.2f}%",
                'total_cache_requests': total_requests,
                'lazy_loads': self._stats['lazy_loads'],
                'memory_pool_reuses': self._stats['memory_pool_reuses'],
                'async_cache_size': len(self.async_cache.cache),
                'git_cache_size': len(self.git_cache._cache),
                'db_cache_size': len(self.db_cache._cache),
                'memory_usage_mb': self._estimate_memory_usage()
            }

    def _estimate_memory_usage(self) -> float:
        """估算内存使用量"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except:
            return 0.0

    # 清理方法
    async def cleanup_expired(self) -> None:
        """清理过期缓存"""
        await self.async_cache.clear()
        # Git和DB缓存会自动清理过期项

        with self._lock:
            # 重置部分统计避免数字过大
            if self._stats['cache_hits'] > 1000000:
                self._stats['cache_hits'] = 0
                self._stats['cache_misses'] = 0

        # 强制垃圾回收
        gc.collect()

        log_info("缓存清理完成")

    def clear_all(self) -> None:
        """清空所有缓存"""
        # 异步缓存需要在事件循环中清理
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self.async_cache.clear())
        except:
            # 如果没有事件循环，直接清理
            self.async_cache.cache.clear()
            self.async_cache.access_times.clear()
            self.async_cache.expire_times.clear()

        self.git_cache._cache.clear()
        self.db_cache._cache.clear()
        self.db_cache._access_order.clear()
        self.lazy_loader._cache.clear()

        with self._lock:
            self._stats = {
                'cache_hits': 0,
                'cache_misses': 0,
                'lazy_loads': 0,
                'memory_pool_reuses': 0
            }

        log_info("所有缓存已清空")

# 全局高性能缓存实例
performance_cache = PerformanceCache()

# 便捷装饰器导出
cache_function = performance_cache.cache_function
async_cache_function = performance_cache.async_cache_function

# 便捷方法
def get_cached_git_result(cmd_key: str, project_root: str = None) -> Optional[Any]:
    """便捷方法：获取Git缓存结果"""
    return performance_cache.get_git_result(cmd_key, project_root)

def cache_git_result(cmd_key: str, result: Any, project_root: str = None) -> None:
    """便捷方法：缓存Git结果"""
    performance_cache.cache_git_result(cmd_key, result, project_root)

def get_cached_db_result(query: str, params: tuple = None) -> Optional[Any]:
    """便捷方法：获取数据库缓存结果"""
    return performance_cache.get_db_result(query, params)

def cache_db_result(query: str, result: Any, params: tuple = None, ttl: int = None) -> None:
    """便捷方法：缓存数据库结果"""
    performance_cache.cache_db_result(query, result, params, ttl)

def lazy_load_module(module_name: str, import_func: Callable) -> Any:
    """便捷方法：懒加载模块"""
    return performance_cache.lazy_load(module_name, import_func)