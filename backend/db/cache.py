"""
缓存管理
========

提供Redis缓存的核心功能:
- Redis连接管理
- 集群支持
- 缓存操作封装
- 序列化支持
- 键管理和TTL
"""

import asyncio
import json
import pickle
import logging
from typing import Any, Optional, Dict, List, Union
from contextlib import asynccontextmanager
import time

import redis
import redis.asyncio as aioredis
from redis.cluster import RedisCluster
from redis.asyncio.cluster import RedisCluster as AsyncRedisCluster

from .config import get_cache_config

# 配置日志
logger = logging.getLogger(__name__)

# 全局Redis客户端实例
redis_client: Optional[redis.Redis] = None
async_redis_client: Optional[aioredis.Redis] = None
redis_cluster: Optional[RedisCluster] = None
async_redis_cluster: Optional[AsyncRedisCluster] = None


class CacheConnectionError(Exception):
    """缓存连接错误"""
    pass


class CacheSerializationError(Exception):
    """缓存序列化错误"""
    pass


class CacheKeyManager:
    """
    缓存键管理器
    ============

    提供统一的缓存键命名和管理
    """

    # 键前缀
    PREFIX = "perfect21"

    # 键分隔符
    SEPARATOR = ":"

    # 键模板
    USER_KEY = f"{PREFIX}{SEPARATOR}user{SEPARATOR}{{user_id}}"
    SESSION_KEY = f"{PREFIX}{SEPARATOR}session{SEPARATOR}{{session_id}}"
    AUTH_KEY = f"{PREFIX}{SEPARATOR}auth{SEPARATOR}{{token_hash}}"
    RATE_LIMIT_KEY = f"{PREFIX}{SEPARATOR}rate_limit{SEPARATOR}{{identifier}}"
    LOCK_KEY = f"{PREFIX}{SEPARATOR}lock{SEPARATOR}{{resource}}"

    @classmethod
    def user_key(cls, user_id: str) -> str:
        """生成用户缓存键"""
        return cls.USER_KEY.format(user_id=user_id)

    @classmethod
    def session_key(cls, session_id: str) -> str:
        """生成会话缓存键"""
        return cls.SESSION_KEY.format(session_id=session_id)

    @classmethod
    def auth_key(cls, token_hash: str) -> str:
        """生成认证缓存键"""
        return cls.AUTH_KEY.format(token_hash=token_hash)

    @classmethod
    def rate_limit_key(cls, identifier: str) -> str:
        """生成限流缓存键"""
        return cls.RATE_LIMIT_KEY.format(identifier=identifier)

    @classmethod
    def lock_key(cls, resource: str) -> str:
        """生成分布式锁键"""
        return cls.LOCK_KEY.format(resource=resource)

    @classmethod
    def custom_key(cls, *parts: str) -> str:
        """生成自定义键"""
        return cls.SEPARATOR.join([cls.PREFIX] + list(parts))


class CacheSerializer:
    """
    缓存序列化器
    ============

    支持多种序列化格式
    """

    @staticmethod
    def serialize_json(value: Any) -> str:
        """JSON序列化"""
        try:
            return json.dumps(value, ensure_ascii=False, default=str)
        except (TypeError, ValueError) as e:
            raise CacheSerializationError(f"JSON序列化失败: {e}")

    @staticmethod
    def deserialize_json(value: str) -> Any:
        """JSON反序列化"""
        try:
            return json.loads(value)
        except (TypeError, ValueError) as e:
            raise CacheSerializationError(f"JSON反序列化失败: {e}")

    @staticmethod
    def serialize_pickle(value: Any) -> bytes:
        """Pickle序列化"""
        try:
            return pickle.dumps(value)
        except (TypeError, pickle.PicklingError) as e:
            raise CacheSerializationError(f"Pickle序列化失败: {e}")

    @staticmethod
    def deserialize_pickle(value: bytes) -> Any:
        """Pickle反序列化"""
        try:
            return pickle.loads(value)
        except (TypeError, pickle.UnpicklingError) as e:
            raise CacheSerializationError(f"Pickle反序列化失败: {e}")


def create_redis_client() -> redis.Redis:
    """
    创建同步Redis客户端

    Returns:
        Redis客户端实例
    """
    config = get_cache_config()

    try:
        if config.cluster_enabled:
            # 集群模式
            nodes = config.get_cluster_nodes()
            if not nodes:
                raise CacheConnectionError("集群模式需要配置节点列表")

            client = RedisCluster(
                startup_nodes=nodes,
                max_connections_per_node=config.max_connections_per_node,
                **config.get_connection_kwargs()
            )
        else:
            # 单机模式
            client = redis.Redis(
                host=config.host,
                port=config.port,
                db=config.database,
                max_connections=config.max_connections,
                **config.get_connection_kwargs()
            )

        # 测试连接
        client.ping()
        logger.info(f"创建Redis客户端: {config.host}:{config.port}")

        return client

    except Exception as e:
        logger.error(f"创建Redis客户端失败: {e}")
        raise CacheConnectionError(f"无法创建Redis客户端: {e}")


def create_async_redis_client() -> aioredis.Redis:
    """
    创建异步Redis客户端

    Returns:
        异步Redis客户端实例
    """
    config = get_cache_config()

    try:
        if config.cluster_enabled:
            # 异步集群模式
            nodes = config.get_cluster_nodes()
            if not nodes:
                raise CacheConnectionError("集群模式需要配置节点列表")

            client = AsyncRedisCluster(
                startup_nodes=nodes,
                max_connections_per_node=config.max_connections_per_node,
                **config.get_connection_kwargs()
            )
        else:
            # 异步单机模式
            client = aioredis.Redis(
                host=config.host,
                port=config.port,
                db=config.database,
                max_connections=config.max_connections,
                **config.get_connection_kwargs()
            )

        logger.info(f"创建异步Redis客户端: {config.host}:{config.port}")

        return client

    except Exception as e:
        logger.error(f"创建异步Redis客户端失败: {e}")
        raise CacheConnectionError(f"无法创建异步Redis客户端: {e}")


async def init_cache() -> None:
    """
    初始化缓存连接
    """
    global redis_client, async_redis_client, redis_cluster, async_redis_cluster

    try:
        config = get_cache_config()

        # 创建客户端
        redis_client = create_redis_client()
        async_redis_client = create_async_redis_client()

        # 如果是集群模式，设置集群客户端
        if config.cluster_enabled:
            redis_cluster = redis_client
            async_redis_cluster = async_redis_client

        # 测试连接
        await test_cache_connection()

        logger.info("缓存初始化完成")

    except Exception as e:
        logger.error(f"缓存初始化失败: {e}")
        await close_cache()
        raise


async def close_cache() -> None:
    """
    关闭缓存连接
    """
    global redis_client, async_redis_client, redis_cluster, async_redis_cluster

    try:
        if async_redis_client:
            await async_redis_client.close()
            async_redis_client = None
            logger.info("异步Redis客户端已关闭")

        if redis_client:
            redis_client.close()
            redis_client = None
            logger.info("Redis客户端已关闭")

        redis_cluster = None
        async_redis_cluster = None

    except Exception as e:
        logger.error(f"关闭缓存连接时出错: {e}")


def get_redis_client() -> redis.Redis:
    """
    获取同步Redis客户端

    Returns:
        Redis客户端实例

    Raises:
        CacheConnectionError: 客户端未初始化
    """
    if not redis_client:
        raise CacheConnectionError("Redis客户端未初始化")
    return redis_client


async def get_async_redis_client() -> aioredis.Redis:
    """
    获取异步Redis客户端

    Returns:
        异步Redis客户端实例

    Raises:
        CacheConnectionError: 客户端未初始化
    """
    if not async_redis_client:
        raise CacheConnectionError("异步Redis客户端未初始化")
    return async_redis_client


def get_redis_cluster() -> Optional[RedisCluster]:
    """
    获取Redis集群客户端

    Returns:
        Redis集群客户端 (如果启用)
    """
    return redis_cluster


async def get_async_redis_cluster() -> Optional[AsyncRedisCluster]:
    """
    获取异步Redis集群客户端

    Returns:
        异步Redis集群客户端 (如果启用)
    """
    return async_redis_cluster


async def test_cache_connection() -> bool:
    """
    测试缓存连接

    Returns:
        连接是否成功

    Raises:
        CacheConnectionError: 连接失败
    """
    try:
        # 测试同步连接
        client = get_redis_client()
        client.ping()

        # 测试异步连接
        async_client = await get_async_redis_client()
        await async_client.ping()

        logger.info("缓存连接测试成功")
        return True

    except Exception as e:
        logger.error(f"缓存连接测试失败: {e}")
        raise CacheConnectionError(f"缓存连接测试失败: {e}")


class CacheOperations:
    """
    缓存操作封装类
    ==============

    提供高级缓存操作方法
    """

    def __init__(self, client: Union[redis.Redis, aioredis.Redis]):
        """
        初始化缓存操作

        Args:
            client: Redis客户端
        """
        self.client = client
        self.is_async = isinstance(client, aioredis.Redis)
        self.serializer = CacheSerializer()
        self.key_manager = CacheKeyManager()

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        serializer: str = "json"
    ) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间 (秒)
            serializer: 序列化方式 (json/pickle)

        Returns:
            是否设置成功
        """
        try:
            # 序列化值
            if serializer == "json":
                serialized_value = self.serializer.serialize_json(value)
            elif serializer == "pickle":
                serialized_value = self.serializer.serialize_pickle(value)
            else:
                raise ValueError(f"不支持的序列化方式: {serializer}")

            # 设置缓存
            if self.is_async:
                result = await self.client.set(key, serialized_value, ex=ttl)
            else:
                result = self.client.set(key, serialized_value, ex=ttl)

            return bool(result)

        except Exception as e:
            logger.error(f"设置缓存失败 {key}: {e}")
            return False

    async def get(self, key: str, serializer: str = "json") -> Any:
        """
        获取缓存值

        Args:
            key: 缓存键
            serializer: 序列化方式 (json/pickle)

        Returns:
            缓存值或None
        """
        try:
            # 获取缓存
            if self.is_async:
                value = await self.client.get(key)
            else:
                value = self.client.get(key)

            if value is None:
                return None

            # 反序列化值
            if serializer == "json":
                return self.serializer.deserialize_json(value)
            elif serializer == "pickle":
                return self.serializer.deserialize_pickle(value)
            else:
                raise ValueError(f"不支持的序列化方式: {serializer}")

        except Exception as e:
            logger.error(f"获取缓存失败 {key}: {e}")
            return None

    async def delete(self, *keys: str) -> int:
        """
        删除缓存键

        Args:
            *keys: 要删除的键列表

        Returns:
            删除的键数量
        """
        try:
            if self.is_async:
                return await self.client.delete(*keys)
            else:
                return self.client.delete(*keys)

        except Exception as e:
            logger.error(f"删除缓存失败 {keys}: {e}")
            return 0

    async def exists(self, *keys: str) -> int:
        """
        检查键是否存在

        Args:
            *keys: 要检查的键列表

        Returns:
            存在的键数量
        """
        try:
            if self.is_async:
                return await self.client.exists(*keys)
            else:
                return self.client.exists(*keys)

        except Exception as e:
            logger.error(f"检查键存在性失败 {keys}: {e}")
            return 0

    async def expire(self, key: str, ttl: int) -> bool:
        """
        设置键过期时间

        Args:
            key: 缓存键
            ttl: 过期时间 (秒)

        Returns:
            是否设置成功
        """
        try:
            if self.is_async:
                return await self.client.expire(key, ttl)
            else:
                return self.client.expire(key, ttl)

        except Exception as e:
            logger.error(f"设置过期时间失败 {key}: {e}")
            return False

    async def ttl(self, key: str) -> int:
        """
        获取键剩余过期时间

        Args:
            key: 缓存键

        Returns:
            剩余时间 (秒)，-1表示永不过期，-2表示键不存在
        """
        try:
            if self.is_async:
                return await self.client.ttl(key)
            else:
                return self.client.ttl(key)

        except Exception as e:
            logger.error(f"获取TTL失败 {key}: {e}")
            return -2

    async def increment(self, key: str, amount: int = 1) -> int:
        """
        递增计数器

        Args:
            key: 计数器键
            amount: 递增量

        Returns:
            递增后的值
        """
        try:
            if self.is_async:
                return await self.client.incrby(key, amount)
            else:
                return self.client.incrby(key, amount)

        except Exception as e:
            logger.error(f"递增计数器失败 {key}: {e}")
            return 0


@asynccontextmanager
async def distributed_lock(
    key: str,
    timeout: int = 10,
    blocking_timeout: Optional[int] = None
):
    """
    分布式锁上下文管理器

    Args:
        key: 锁键
        timeout: 锁超时时间 (秒)
        blocking_timeout: 阻塞等待时间 (秒)

    Yields:
        锁对象
    """
    client = await get_async_redis_client()
    lock_key = CacheKeyManager.lock_key(key)

    # 创建锁
    lock = client.lock(
        lock_key,
        timeout=timeout,
        blocking_timeout=blocking_timeout
    )

    try:
        # 获取锁
        acquired = await lock.acquire()
        if not acquired:
            raise CacheConnectionError(f"无法获取分布式锁: {key}")

        yield lock

    finally:
        # 释放锁
        try:
            await lock.release()
        except Exception as e:
            logger.error(f"释放分布式锁失败 {key}: {e}")


# 便捷函数
def cache_key(*parts: str) -> str:
    """生成缓存键"""
    return CacheKeyManager.custom_key(*parts)


def cache_ttl(cache_type: str = "default") -> int:
    """获取缓存TTL"""
    config = get_cache_config()
    return config.get_ttl(cache_type)


# 导出公共接口
__all__ = [
    'redis_client',
    'async_redis_client',
    'redis_cluster',
    'async_redis_cluster',
    'get_redis_client',
    'get_async_redis_client',
    'get_redis_cluster',
    'get_async_redis_cluster',
    'init_cache',
    'close_cache',
    'test_cache_connection',
    'CacheOperations',
    'CacheKeyManager',
    'CacheSerializer',
    'distributed_lock',
    'cache_key',
    'cache_ttl',
    'CacheConnectionError',
    'CacheSerializationError',
]