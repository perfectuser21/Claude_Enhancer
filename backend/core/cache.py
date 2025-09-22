"""
Performance Optimization: Redis Cache Layer
Redis缓存层 - 高性能缓存管理系统
"""

import redis.asyncio as redis
import json
import pickle
import asyncio
import logging
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
from functools import wraps
from contextlib import asynccontextmanager
import hashlib
import zlib
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class CacheStrategy(Enum):
    """缓存策略"""

    LRU = "lru"
    LFU = "lfu"
    TTL = "ttl"
    WRITE_THROUGH = "write_through"
    WRITE_BACK = "write_back"
    WRITE_AROUND = "write_around"


@dataclass
class CacheConfig:
    """缓存配置"""

    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None
    db: int = 0
    pool_size: int = 50
    timeout: int = 5
    retry_on_timeout: bool = True
    decode_responses: bool = False
    compression_enabled: bool = True
    compression_threshold: int = 1024  # 1KB
    default_ttl: int = 300  # 5分钟
    max_connections: int = 100


class CacheManager:
    """Redis缓存管理器 - 企业级高性能缓存系统"""

    def __init__(self, config: CacheConfig):
        self.config = config
        self.redis_pool = None
        self.local_cache = {}  # 本地L1缓存
        self.local_cache_ttl = {}
        self.stats = {"hits": 0, "misses": 0, "sets": 0, "deletes": 0, "errors": 0}
        self._lock = asyncio.Lock()

    async def initialize(self):
        """初始化Redis连接池"""
        try:
            self.redis_pool = redis.ConnectionPool(
                host=self.config.host,
                port=self.config.port,
                password=self.config.password,
                db=self.config.db,
                max_connections=self.config.max_connections,
                retry_on_timeout=self.config.retry_on_timeout,
                decode_responses=self.config.decode_responses,
            )

            # 测试连接
            async with self._get_connection() as conn:
                await conn.ping()

            logger.info(f"✅ Redis缓存管理器初始化成功 - {self.config.host}:{self.config.port}")

            # 启动后台任务
            asyncio.create_task(self._cleanup_local_cache())
            asyncio.create_task(self._periodic_stats_log())

        except Exception as e:
            logger.error(f"❌ Redis连接失败: {e}")
            raise

    @asynccontextmanager
    async def _get_connection(self):
        """获取Redis连接"""
        conn = redis.Redis(connection_pool=self.redis_pool)
        try:
            yield conn
        finally:
            await conn.close()

    def _serialize_value(self, value: Any) -> bytes:
        """序列化值"""
        # 使用pickle序列化，支持复杂对象
        serialized = pickle.dumps(value)

        # 压缩大数据
        if (
            self.config.compression_enabled
            and len(serialized) > self.config.compression_threshold
        ):
            serialized = zlib.compress(serialized)
            # 添加压缩标记
            serialized = b"COMPRESSED:" + serialized

        return serialized

    def _deserialize_value(self, data: bytes) -> Any:
        """反序列化值"""
        if data.startswith(b"COMPRESSED:"):
            # 解压缩
            data = zlib.decompress(data[11:])

        return pickle.loads(data)

    def _generate_key(self, namespace: str, key: str) -> str:
        """生成缓存键"""
        return f"perfect21:{namespace}:{key}"

    async def get(self, namespace: str, key: str, default: Any = None) -> Any:
        """获取缓存值"""
        cache_key = self._generate_key(namespace, key)

        # 1. 检查本地缓存 (L1)
        if cache_key in self.local_cache:
            if datetime.now() < self.local_cache_ttl.get(cache_key, datetime.min):
                self.stats["hits"] += 1
                logger.debug(f"🎯 L1缓存命中: {cache_key}")
                return self.local_cache[cache_key]
            else:
                # L1缓存过期
                self._remove_from_local_cache(cache_key)

        # 2. 检查Redis缓存 (L2)
        try:
            async with self._get_connection() as conn:
                data = await conn.get(cache_key)
                if data:
                    value = self._deserialize_value(data)

                    # 更新本地缓存
                    self._update_local_cache(cache_key, value)

                    self.stats["hits"] += 1
                    logger.debug(f"🎯 L2缓存命中: {cache_key}")
                    return value

        except Exception as e:
            logger.error(f"❌ Redis获取失败: {e}")
            self.stats["errors"] += 1

        self.stats["misses"] += 1
        logger.debug(f"❌ 缓存未命中: {cache_key}")
        return default

    async def set(
        self, namespace: str, key: str, value: Any, ttl: Optional[int] = None
    ) -> bool:
        """设置缓存值"""
        cache_key = self._generate_key(namespace, key)
        ttl = ttl or self.config.default_ttl

        try:
            # 序列化值
            serialized_value = self._serialize_value(value)

            # 设置Redis缓存
            async with self._get_connection() as conn:
                await conn.setex(cache_key, ttl, serialized_value)

            # 更新本地缓存
            self._update_local_cache(cache_key, value, ttl=min(ttl, 60))  # 本地缓存最多1分钟

            self.stats["sets"] += 1
            logger.debug(f"✅ 缓存设置成功: {cache_key} (TTL: {ttl}s)")
            return True

        except Exception as e:
            logger.error(f"❌ Redis设置失败: {e}")
            self.stats["errors"] += 1
            return False

    async def delete(self, namespace: str, key: str) -> bool:
        """删除缓存值"""
        cache_key = self._generate_key(namespace, key)

        try:
            # 删除Redis缓存
            async with self._get_connection() as conn:
                result = await conn.delete(cache_key)

            # 删除本地缓存
            self._remove_from_local_cache(cache_key)

            self.stats["deletes"] += 1
            logger.debug(f"🗑️ 缓存删除: {cache_key}")
            return bool(result)

        except Exception as e:
            logger.error(f"❌ Redis删除失败: {e}")
            self.stats["errors"] += 1
            return False

    async def delete_pattern(self, namespace: str, pattern: str) -> int:
        """批量删除缓存（支持通配符）"""
        full_pattern = self._generate_key(namespace, pattern)

        try:
            async with self._get_connection() as conn:
                keys = await conn.keys(full_pattern)
                if keys:
                    deleted = await conn.delete(*keys)

                    # 删除本地缓存中匹配的键
                    for key in keys:
                        self._remove_from_local_cache(
                            key.decode() if isinstance(key, bytes) else key
                        )

                    logger.info(f"🗑️ 批量删除缓存: {len(keys)}个键")
                    return deleted

        except Exception as e:
            logger.error(f"❌ 批量删除失败: {e}")
            self.stats["errors"] += 1

        return 0

    async def exists(self, namespace: str, key: str) -> bool:
        """检查缓存是否存在"""
        cache_key = self._generate_key(namespace, key)

        # 检查本地缓存
        if cache_key in self.local_cache:
            if datetime.now() < self.local_cache_ttl.get(cache_key, datetime.min):
                return True

        # 检查Redis缓存
        try:
            async with self._get_connection() as conn:
                return bool(await conn.exists(cache_key))
        except Exception as e:
            logger.error(f"❌ Redis检查存在失败: {e}")
            return False

    async def increment(
        self, namespace: str, key: str, amount: int = 1
    ) -> Optional[int]:
        """原子递增操作"""
        cache_key = self._generate_key(namespace, key)

        try:
            async with self._get_connection() as conn:
                result = await conn.incrby(cache_key, amount)
                return result
        except Exception as e:
            logger.error(f"❌ Redis递增失败: {e}")
            return None

    async def get_multiple(self, namespace: str, keys: List[str]) -> Dict[str, Any]:
        """批量获取缓存"""
        cache_keys = [self._generate_key(namespace, key) for key in keys]
        result = {}

        try:
            async with self._get_connection() as conn:
                values = await conn.mget(cache_keys)

                for i, (original_key, cache_key, value) in enumerate(
                    zip(keys, cache_keys, values)
                ):
                    if value:
                        try:
                            result[original_key] = self._deserialize_value(value)
                            # 更新本地缓存
                            self._update_local_cache(cache_key, result[original_key])
                        except Exception as e:
                            logger.error(f"❌ 反序列化失败: {e}")

        except Exception as e:
            logger.error(f"❌ 批量获取失败: {e}")

        return result

    async def set_multiple(
        self, namespace: str, mapping: Dict[str, Any], ttl: Optional[int] = None
    ) -> bool:
        """批量设置缓存"""
        ttl = ttl or self.config.default_ttl

        try:
            async with self._get_connection() as conn:
                pipe = conn.pipeline()

                for key, value in mapping.items():
                    cache_key = self._generate_key(namespace, key)
                    serialized_value = self._serialize_value(value)
                    pipe.setex(cache_key, ttl, serialized_value)

                    # 更新本地缓存
                    self._update_local_cache(cache_key, value, ttl=min(ttl, 60))

                await pipe.execute()

                self.stats["sets"] += len(mapping)
                logger.debug(f"✅ 批量设置缓存: {len(mapping)}个键")
                return True

        except Exception as e:
            logger.error(f"❌ 批量设置失败: {e}")
            return False

    def _update_local_cache(self, key: str, value: Any, ttl: int = 60):
        """更新本地缓存"""
        self.local_cache[key] = value
        self.local_cache_ttl[key] = datetime.now() + timedelta(seconds=ttl)

        # 限制本地缓存大小
        if len(self.local_cache) > 1000:
            # 移除最旧的条目
            oldest_key = min(
                self.local_cache_ttl.keys(), key=lambda k: self.local_cache_ttl[k]
            )
            self._remove_from_local_cache(oldest_key)

    def _remove_from_local_cache(self, key: str):
        """从本地缓存中移除"""
        self.local_cache.pop(key, None)
        self.local_cache_ttl.pop(key, None)

    async def _cleanup_local_cache(self):
        """定期清理本地缓存"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟清理一次

                now = datetime.now()
                expired_keys = [
                    key for key, expiry in self.local_cache_ttl.items() if now >= expiry
                ]

                for key in expired_keys:
                    self._remove_from_local_cache(key)

                if expired_keys:
                    logger.debug(f"🧹 清理本地缓存: {len(expired_keys)}个过期键")

            except Exception as e:
                logger.error(f"❌ 本地缓存清理失败: {e}")

    async def _periodic_stats_log(self):
        """定期记录缓存统计"""
        while True:
            try:
                await asyncio.sleep(300)  # 每5分钟记录一次

                total_operations = sum(self.stats.values())
                if total_operations > 0:
                    hit_rate = (
                        self.stats["hits"] / (self.stats["hits"] + self.stats["misses"])
                    ) * 100
                    logger.info(
                        f"📊 缓存统计 - "
                        f"命中率: {hit_rate:.2f}%, "
                        f"命中: {self.stats['hits']}, "
                        f"未命中: {self.stats['misses']}, "
                        f"设置: {self.stats['sets']}, "
                        f"删除: {self.stats['deletes']}, "
                        f"错误: {self.stats['errors']}"
                    )

            except Exception as e:
                logger.error(f"❌ 统计记录失败: {e}")

    async def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total_operations = self.stats["hits"] + self.stats["misses"]
        hit_rate = (
            (self.stats["hits"] / total_operations * 100) if total_operations > 0 else 0
        )

        return {
            **self.stats,
            "hit_rate": hit_rate,
            "local_cache_size": len(self.local_cache),
            "redis_connected": await self._check_redis_connection(),
        }

    async def _check_redis_connection(self) -> bool:
        """检查Redis连接状态"""
        try:
            async with self._get_connection() as conn:
                await conn.ping()
                return True
        except:
            return False

    async def health_check(self) -> bool:
        """健康检查"""
        return await self._check_redis_connection()

    async def ready_check(self) -> bool:
        """就绪检查"""
        return await self._check_redis_connection()

    async def close(self):
        """关闭连接"""
        if self.redis_pool:
            await self.redis_pool.disconnect()
            logger.info("📴 Redis连接池已关闭")


def cache_result(namespace: str, ttl: int = 300, key_func: Optional[callable] = None):
    """缓存装饰器 - 自动缓存函数结果"""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # 基于函数名和参数生成键
                key_parts = [func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()

            # 获取缓存管理器实例（需要从应用状态中获取）
            cache_manager = getattr(wrapper, "_cache_manager", None)
            if not cache_manager:
                # 如果没有缓存管理器，直接执行函数
                return await func(*args, **kwargs)

            # 尝试从缓存获取
            cached_result = await cache_manager.get(namespace, cache_key)
            if cached_result is not None:
                return cached_result

            # 执行函数并缓存结果
            result = await func(*args, **kwargs)
            await cache_manager.set(namespace, cache_key, result, ttl)

            return result

        return wrapper

    return decorator


# 缓存装饰器使用示例
@cache_result("user_profile", ttl=600, key_func=lambda user_id: f"user_{user_id}")
async def get_user_profile(user_id: int):
    """获取用户资料（带缓存）"""
    # 实际的数据库查询逻辑
    pass


@cache_result("permissions", ttl=300)
async def get_user_permissions(user_id: int, resource: str):
    """获取用户权限（带缓存）"""
    # 实际的权限查询逻辑
    pass
