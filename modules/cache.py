#!/usr/bin/env python3
"""
Perfect21缓存管理器
提供内存缓存、Redis缓存等多种缓存策略
"""

import os
import sys
import time
import json
import pickle
import hashlib
from typing import Dict, Any, Optional, Union
from datetime import datetime, timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.logger import log_info, log_error
from modules.config import config

class MemoryCache:
    """内存缓存实现"""

    def __init__(self, default_ttl: int = 3600):
        """初始化内存缓存"""
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'evictions': 0
        }

    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """设置缓存"""
        try:
            ttl = ttl or self.default_ttl
            expires_at = time.time() + ttl

            self.cache[key] = {
                'value': value,
                'expires_at': expires_at,
                'created_at': time.time()
            }

            self._stats['sets'] += 1
            return True

        except Exception as e:
            log_error(f"内存缓存设置失败: {key}", e)
            return False

    def get(self, key: str) -> Any:
        """获取缓存"""
        try:
            if key not in self.cache:
                self._stats['misses'] += 1
                return None

            item = self.cache[key]

            # 检查过期
            if time.time() > item['expires_at']:
                del self.cache[key]
                self._stats['evictions'] += 1
                self._stats['misses'] += 1
                return None

            self._stats['hits'] += 1
            return item['value']

        except Exception as e:
            log_error(f"内存缓存获取失败: {key}", e)
            self._stats['misses'] += 1
            return None

    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            if key in self.cache:
                del self.cache[key]
                self._stats['deletes'] += 1
                return True
            return False

        except Exception as e:
            log_error(f"内存缓存删除失败: {key}", e)
            return False

    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        if key not in self.cache:
            return False

        item = self.cache[key]
        if time.time() > item['expires_at']:
            del self.cache[key]
            self._stats['evictions'] += 1
            return False

        return True

    def clear(self):
        """清空缓存"""
        count = len(self.cache)
        self.cache.clear()
        log_info(f"清空内存缓存: {count}个键")

    def cleanup_expired(self):
        """清理过期缓存"""
        current_time = time.time()
        expired_keys = []

        for key, item in self.cache.items():
            if current_time > item['expires_at']:
                expired_keys.append(key)

        for key in expired_keys:
            del self.cache[key]
            self._stats['evictions'] += 1

        if expired_keys:
            log_info(f"清理过期缓存: {len(expired_keys)}个键")

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total_requests = self._stats['hits'] + self._stats['misses']
        hit_rate = (self._stats['hits'] / total_requests * 100) if total_requests > 0 else 0

        return {
            'type': 'memory',
            'size': len(self.cache),
            'hit_rate': round(hit_rate, 2),
            **self._stats
        }

class FileCache:
    """文件缓存实现"""

    def __init__(self, cache_dir: str = "cache", default_ttl: int = 3600):
        """初始化文件缓存"""
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl
        os.makedirs(cache_dir, exist_ok=True)
        log_info(f"文件缓存初始化: {cache_dir}")

    def _get_cache_path(self, key: str) -> str:
        """获取缓存文件路径"""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{key_hash}.cache")

    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """设置缓存"""
        try:
            ttl = ttl or self.default_ttl
            expires_at = time.time() + ttl

            cache_data = {
                'value': value,
                'expires_at': expires_at,
                'created_at': time.time()
            }

            cache_path = self._get_cache_path(key)
            with open(cache_path, 'wb') as f:
                pickle.dump(cache_data, f)

            return True

        except Exception as e:
            log_error(f"文件缓存设置失败: {key}", e)
            return False

    def get(self, key: str) -> Any:
        """获取缓存"""
        try:
            cache_path = self._get_cache_path(key)
            if not os.path.exists(cache_path):
                return None

            with open(cache_path, 'rb') as f:
                cache_data = pickle.load(f)

            # 检查过期
            if time.time() > cache_data['expires_at']:
                os.unlink(cache_path)
                return None

            return cache_data['value']

        except Exception as e:
            log_error(f"文件缓存获取失败: {key}", e)
            return None

    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            cache_path = self._get_cache_path(key)
            if os.path.exists(cache_path):
                os.unlink(cache_path)
                return True
            return False

        except Exception as e:
            log_error(f"文件缓存删除失败: {key}", e)
            return False

    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        cache_path = self._get_cache_path(key)
        if not os.path.exists(cache_path):
            return False

        try:
            with open(cache_path, 'rb') as f:
                cache_data = pickle.load(f)

            if time.time() > cache_data['expires_at']:
                os.unlink(cache_path)
                return False

            return True

        except Exception:
            return False

    def clear(self):
        """清空缓存"""
        try:
            import glob
            cache_files = glob.glob(os.path.join(self.cache_dir, "*.cache"))
            for cache_file in cache_files:
                os.unlink(cache_file)
            log_info(f"清空文件缓存: {len(cache_files)}个文件")
        except Exception as e:
            log_error("清空文件缓存失败", e)

    def cleanup_expired(self):
        """清理过期缓存"""
        try:
            import glob
            current_time = time.time()
            cache_files = glob.glob(os.path.join(self.cache_dir, "*.cache"))
            expired_count = 0

            for cache_file in cache_files:
                try:
                    with open(cache_file, 'rb') as f:
                        cache_data = pickle.load(f)

                    if current_time > cache_data['expires_at']:
                        os.unlink(cache_file)
                        expired_count += 1

                except Exception:
                    # 如果文件损坏，直接删除
                    os.unlink(cache_file)
                    expired_count += 1

            if expired_count > 0:
                log_info(f"清理过期文件缓存: {expired_count}个文件")

        except Exception as e:
            log_error("清理过期文件缓存失败", e)

class CacheManager:
    """缓存管理器"""

    def __init__(self):
        """初始化缓存管理器"""
        self.cache_type = config.get('cache.type', 'memory')
        self.default_ttl = config.get('cache.default_ttl', 3600)

        # 初始化缓存后端
        if self.cache_type == 'memory':
            self.backend = MemoryCache(self.default_ttl)
        elif self.cache_type == 'file':
            cache_dir = config.get('cache.file_dir', 'cache')
            self.backend = FileCache(cache_dir, self.default_ttl)
        elif self.cache_type == 'redis':
            self.backend = self._init_redis_cache()
        else:
            log_error(f"不支持的缓存类型: {self.cache_type}")
            # 回退到内存缓存
            self.backend = MemoryCache(self.default_ttl)
            self.cache_type = 'memory'

        log_info(f"缓存管理器初始化: 类型={self.cache_type}")

    def _init_redis_cache(self):
        """初始化Redis缓存"""
        try:
            # 这里可以实现Redis缓存
            # import redis
            # redis_host = config.get('cache.redis_host', 'localhost')
            # redis_port = config.get('cache.redis_port', 6379)
            # redis_db = config.get('cache.redis_db', 0)
            # return redis.Redis(host=redis_host, port=redis_port, db=redis_db)

            # 暂时返回内存缓存作为回退
            log_info("Redis缓存未实现，回退到内存缓存")
            return MemoryCache(self.default_ttl)
        except Exception as e:
            log_error("Redis缓存初始化失败", e)
            return MemoryCache(self.default_ttl)

    def set(self, key: str, value: Any, ttl: int = None, namespace: str = None) -> bool:
        """设置缓存"""
        cache_key = self._build_key(key, namespace)
        return self.backend.set(cache_key, value, ttl)

    def get(self, key: str, namespace: str = None) -> Any:
        """获取缓存"""
        cache_key = self._build_key(key, namespace)
        return self.backend.get(cache_key)

    def delete(self, key: str, namespace: str = None) -> bool:
        """删除缓存"""
        cache_key = self._build_key(key, namespace)
        return self.backend.delete(cache_key)

    def exists(self, key: str, namespace: str = None) -> bool:
        """检查缓存是否存在"""
        cache_key = self._build_key(key, namespace)
        return self.backend.exists(cache_key)

    def get_or_set(self, key: str, callback, ttl: int = None, namespace: str = None) -> Any:
        """获取缓存，如果不存在则通过回调函数设置"""
        value = self.get(key, namespace)
        if value is not None:
            return value

        # 执行回调函数获取值
        try:
            value = callback()
            if value is not None:
                self.set(key, value, ttl, namespace)
            return value
        except Exception as e:
            log_error(f"缓存回调函数执行失败: {key}", e)
            return None

    def _build_key(self, key: str, namespace: str = None) -> str:
        """构建缓存键"""
        if namespace:
            return f"{namespace}:{key}"
        return key

    def clear_namespace(self, namespace: str):
        """清空命名空间下的缓存"""
        # 这里需要根据不同的缓存后端实现
        if hasattr(self.backend, 'cache') and isinstance(self.backend.cache, dict):
            # 内存缓存
            keys_to_delete = [k for k in self.backend.cache.keys() if k.startswith(f"{namespace}:")]
            for key in keys_to_delete:
                self.backend.delete(key)
            log_info(f"清空命名空间缓存: {namespace} ({len(keys_to_delete)}个键)")

    def cache_function(self, ttl: int = None, namespace: str = None):
        """函数缓存装饰器"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                # 构建缓存键
                func_name = f"{func.__module__}.{func.__name__}"
                args_str = str(args) + str(sorted(kwargs.items()))
                cache_key = hashlib.md5((func_name + args_str).encode()).hexdigest()

                # 尝试从缓存获取
                cached_result = self.get(cache_key, namespace)
                if cached_result is not None:
                    return cached_result

                # 执行函数并缓存结果
                result = func(*args, **kwargs)
                self.set(cache_key, result, ttl, namespace)
                return result

            return wrapper
        return decorator

    def cleanup_expired(self):
        """清理过期缓存"""
        if hasattr(self.backend, 'cleanup_expired'):
            self.backend.cleanup_expired()

    def clear(self):
        """清空所有缓存"""
        if hasattr(self.backend, 'clear'):
            self.backend.clear()

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        if hasattr(self.backend, 'get_stats'):
            return self.backend.get_stats()
        return {'type': self.cache_type}

    def health_check(self) -> Dict[str, Any]:
        """缓存健康检查"""
        try:
            # 测试设置和获取
            test_key = "health_check"
            test_value = {"timestamp": time.time()}

            if self.set(test_key, test_value, 10):
                retrieved_value = self.get(test_key)
                self.delete(test_key)

                if retrieved_value == test_value:
                    return {
                        'status': 'healthy',
                        'type': self.cache_type,
                        'message': '缓存系统正常'
                    }

            return {
                'status': 'unhealthy',
                'type': self.cache_type,
                'message': '缓存系统异常'
            }

        except Exception as e:
            return {
                'status': 'error',
                'type': self.cache_type,
                'message': f'缓存健康检查失败: {str(e)}'
            }

    def cleanup(self):
        """清理资源"""
        try:
            if hasattr(self.backend, 'cleanup'):
                self.backend.cleanup()
            log_info("CacheManager清理完成")
        except Exception as e:
            log_error("CacheManager清理失败", e)

# 全局缓存管理器实例
cache_manager = CacheManager()