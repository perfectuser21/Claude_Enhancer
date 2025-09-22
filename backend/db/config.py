"""
数据库配置管理
==============

提供数据库和缓存的配置管理:
- 数据库连接配置
- 连接池配置
- Redis缓存配置
- 环境变量管理
"""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from urllib.parse import quote_plus

from pydantic import BaseSettings, validator
from pydantic_settings import SettingsConfigDict


class DatabaseConfig(BaseSettings):
    """
    数据库配置类
    ============

    管理PostgreSQL数据库连接配置
    """

    # 基本连接信息
    host: str = "localhost"
    port: int = 5432
    username: str = "postgres"
    password: str = ""
    database: str = "perfect21"

    # SSL配置
    ssl_mode: str = "prefer"  # disable, allow, prefer, require, verify-ca, verify-full
    ssl_cert: Optional[str] = None
    ssl_key: Optional[str] = None
    ssl_ca: Optional[str] = None

    # 连接池配置
    pool_size: int = 10              # 连接池大小
    max_overflow: int = 20           # 最大溢出连接数
    pool_timeout: int = 30           # 获取连接超时 (秒)
    pool_recycle: int = 3600         # 连接回收时间 (秒)
    pool_pre_ping: bool = True       # 连接前ping检查

    # 异步连接池配置
    async_pool_size: int = 20
    async_max_overflow: int = 30

    # 查询配置
    echo: bool = False               # 是否打印SQL语句
    echo_pool: bool = False          # 是否打印连接池信息
    query_timeout: int = 30          # 查询超时 (秒)

    # 重试配置
    max_retries: int = 3             # 最大重试次数
    retry_interval: float = 1.0      # 重试间隔 (秒)

    model_config = SettingsConfigDict(
        env_prefix="DB_",
        env_file=".env",
        case_sensitive=False
    )

    @validator('password')
    def encode_password(cls, v):
        """URL编码密码中的特殊字符"""
        return quote_plus(v) if v else v

    def get_sync_url(self) -> str:
        """
        获取同步数据库连接URL

        Returns:
            PostgreSQL连接URL
        """
        url = f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

        # 添加SSL参数
        params = []
        if self.ssl_mode != "prefer":
            params.append(f"sslmode={self.ssl_mode}")
        if self.ssl_cert:
            params.append(f"sslcert={self.ssl_cert}")
        if self.ssl_key:
            params.append(f"sslkey={self.ssl_key}")
        if self.ssl_ca:
            params.append(f"sslrootcert={self.ssl_ca}")

        if params:
            url += "?" + "&".join(params)

        return url

    def get_async_url(self) -> str:
        """
        获取异步数据库连接URL

        Returns:
            AsyncPG连接URL
        """
        return self.get_sync_url().replace("postgresql://", "postgresql+asyncpg://")

    def get_engine_kwargs(self) -> Dict[str, Any]:
        """
        获取SQLAlchemy引擎参数

        Returns:
            引擎配置字典
        """
        return {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "pool_pre_ping": self.pool_pre_ping,
            "echo": self.echo,
            "echo_pool": self.echo_pool,
            "connect_args": {
                "connect_timeout": self.query_timeout,
                "command_timeout": self.query_timeout,
            }
        }

    def get_async_engine_kwargs(self) -> Dict[str, Any]:
        """
        获取异步SQLAlchemy引擎参数

        Returns:
            异步引擎配置字典
        """
        kwargs = self.get_engine_kwargs()
        kwargs.update({
            "pool_size": self.async_pool_size,
            "max_overflow": self.async_max_overflow,
        })
        return kwargs


class CacheConfig(BaseSettings):
    """
    缓存配置类
    ===========

    管理Redis缓存连接配置
    """

    # 基本连接信息
    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None
    database: int = 0

    # 集群配置
    cluster_enabled: bool = False
    cluster_nodes: str = ""          # 格式: "host1:port1,host2:port2"

    # 连接池配置
    max_connections: int = 100       # 最大连接数
    max_connections_per_node: int = 50  # 集群模式下每个节点的最大连接数

    # 超时配置
    socket_timeout: float = 5.0      # Socket超时
    socket_connect_timeout: float = 5.0  # 连接超时
    socket_keepalive: bool = True    # 保持连接
    socket_keepalive_options: Dict[str, Any] = field(default_factory=dict)

    # 重试配置
    retry_on_timeout: bool = True    # 超时重试
    health_check_interval: int = 30  # 健康检查间隔 (秒)

    # SSL配置
    ssl_enabled: bool = False
    ssl_cert_reqs: str = "required"  # none, optional, required
    ssl_ca_certs: Optional[str] = None
    ssl_certfile: Optional[str] = None
    ssl_keyfile: Optional[str] = None

    # 序列化配置
    serializer: str = "json"         # json, pickle, msgpack
    compression: bool = False        # 是否启用压缩

    # TTL配置 (秒)
    default_ttl: int = 3600          # 默认过期时间
    session_ttl: int = 86400         # 会话缓存过期时间
    user_ttl: int = 1800            # 用户缓存过期时间

    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        env_file=".env",
        case_sensitive=False
    )

    def get_redis_url(self) -> str:
        """
        获取Redis连接URL

        Returns:
            Redis连接URL
        """
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.database}"
        else:
            return f"redis://{self.host}:{self.port}/{self.database}"

    def get_cluster_nodes(self) -> list:
        """
        获取集群节点列表

        Returns:
            节点地址列表
        """
        if not self.cluster_nodes:
            return []

        nodes = []
        for node in self.cluster_nodes.split(","):
            if ":" in node:
                host, port = node.strip().split(":")
                nodes.append({"host": host, "port": int(port)})
            else:
                nodes.append({"host": node.strip(), "port": 6379})

        return nodes

    def get_connection_kwargs(self) -> Dict[str, Any]:
        """
        获取Redis连接参数

        Returns:
            连接配置字典
        """
        kwargs = {
            "socket_timeout": self.socket_timeout,
            "socket_connect_timeout": self.socket_connect_timeout,
            "socket_keepalive": self.socket_keepalive,
            "socket_keepalive_options": self.socket_keepalive_options,
            "retry_on_timeout": self.retry_on_timeout,
            "health_check_interval": self.health_check_interval,
        }

        if self.password:
            kwargs["password"] = self.password

        if self.ssl_enabled:
            kwargs.update({
                "ssl": True,
                "ssl_cert_reqs": self.ssl_cert_reqs,
                "ssl_ca_certs": self.ssl_ca_certs,
                "ssl_certfile": self.ssl_certfile,
                "ssl_keyfile": self.ssl_keyfile,
            })

        return kwargs

    def get_ttl(self, cache_type: str = "default") -> int:
        """
        根据缓存类型获取TTL

        Args:
            cache_type: 缓存类型

        Returns:
            TTL值 (秒)
        """
        ttl_map = {
            "default": self.default_ttl,
            "session": self.session_ttl,
            "user": self.user_ttl,
        }
        return ttl_map.get(cache_type, self.default_ttl)


@dataclass
class ConnectionInfo:
    """连接信息数据类"""
    host: str
    port: int
    database: str
    username: str
    pool_size: int
    max_connections: int
    ssl_enabled: bool


# 全局配置实例
_db_config: Optional[DatabaseConfig] = None
_cache_config: Optional[CacheConfig] = None


def get_database_config() -> DatabaseConfig:
    """
    获取数据库配置实例 (单例)

    Returns:
        数据库配置对象
    """
    global _db_config
    if _db_config is None:
        _db_config = DatabaseConfig()
    return _db_config


def get_cache_config() -> CacheConfig:
    """
    获取缓存配置实例 (单例)

    Returns:
        缓存配置对象
    """
    global _cache_config
    if _cache_config is None:
        _cache_config = CacheConfig()
    return _cache_config


def get_connection_info() -> ConnectionInfo:
    """
    获取连接信息摘要

    Returns:
        连接信息对象
    """
    db_config = get_database_config()
    cache_config = get_cache_config()

    return ConnectionInfo(
        host=db_config.host,
        port=db_config.port,
        database=db_config.database,
        username=db_config.username,
        pool_size=db_config.pool_size,
        max_connections=cache_config.max_connections,
        ssl_enabled=db_config.ssl_mode != "disable"
    )


def load_config_from_env() -> tuple[DatabaseConfig, CacheConfig]:
    """
    从环境变量加载配置

    Returns:
        数据库和缓存配置元组
    """
    return get_database_config(), get_cache_config()


# 导出配置类和函数
__all__ = [
    'DatabaseConfig',
    'CacheConfig',
    'ConnectionInfo',
    'get_database_config',
    'get_cache_config',
    'get_connection_info',
    'load_config_from_env'
]