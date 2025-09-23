"""
数据库连接和配置包
==================

这个包提供数据库相关的功能:
- 数据库连接管理
- 连接池配置
- 事务管理
- 缓存集成
- 查询优化工具

主要组件:
- database: 数据库连接和配置
- session: 会话管理
- cache: 缓存集成
- migrations: 数据库迁移
- utils: 数据库工具函数

使用示例:
    from backend.db import get_db_session, get_redis_client

    # 获取数据库会话
    async with get_db_session() as session:
        users = await session.execute(select(User))

    # 获取缓存客户端
    redis = await get_redis_client()
    await redis.set("key", "value")
"""

from .database import (
    engine,
    async_engine,
    SessionLocal,
    AsyncSessionLocal,
    get_db_session,
    get_async_db_session,
    init_database,
    close_database,
    create_tables,
    drop_tables,
)

from .cache import (
    redis_client,
    redis_cluster,
    get_redis_client,
    get_redis_cluster,
    init_cache,
    close_cache,
    cache_key,
    cache_ttl,
)

from .session import (
    DatabaseSession,
    TransactionManager,
    transaction,
    readonly_transaction,
    bulk_transaction,
)

from .config import DatabaseConfig, CacheConfig, get_database_config, get_cache_config

# 导出所有公共接口
__all__ = [
    # 数据库连接
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
    # 缓存连接
    "redis_client",
    "redis_cluster",
    "get_redis_client",
    "get_redis_cluster",
    "init_cache",
    "close_cache",
    "cache_key",
    "cache_ttl",
    # 会话管理
    "DatabaseSession",
    "TransactionManager",
    "transaction",
    "readonly_transaction",
    "bulk_transaction",
    # 配置
    "DatabaseConfig",
    "CacheConfig",
    "get_database_config",
    "get_cache_config",
]

# 版本信息
__version__ = "1.0.0"
__author__ = "Claude Enhancer Team"
__description__ = "数据库访问层 - 提供完整的数据库连接、缓存和事务管理功能"
