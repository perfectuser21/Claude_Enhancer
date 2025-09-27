"""
数据库配置管理
包含数据库连接参数、连接池配置等
"""

import os
from typing import Optional
from pydantic import BaseSettings, validator
from functools import lru_cache


class DatabaseConfig(BaseSettings):
    """
    数据库配置类
    从环境变量或配置文件读取数据库连接参数
    """

    # PostgreSQL连接参数
    database_url: str = "postgresql://postgres:password@localhost:5432/task_management"
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "task_management"
    database_user: str = "postgres"
    database_password: str = "password"

    # 连接池配置
    pool_size: int = 20
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    pool_pre_ping: bool = True

    # 连接超时配置
    connect_timeout: int = 10
    command_timeout: int = 60

    # 是否启用SQL日志
    echo_sql: bool = False
    echo_pool: bool = False

    # 是否启用SSL
    ssl_mode: str = "prefer"

    # Redis配置（用于缓存和会话）
    redis_url: str = "redis://localhost:6379/0"
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None

    class Config:
        env_file = ".env"
        env_prefix = "DB_"
        case_sensitive = False

    @validator("database_url")
    def validate_database_url(cls, v):
        """验证数据库URL格式"""
        if not v.startswith(
            ("postgresql://", "postgresql+psycopg2://", "postgresql+asyncpg://")
        ):
            raise ValueError("数据库URL必须以postgresql://开头")
        return v

    @validator("pool_size")
    def validate_pool_size(cls, v):
        """验证连接池大小"""
        if v < 1 or v > 100:
            raise ValueError("连接池大小必须在1-100之间")
        return v

    @property
    def sync_database_url(self) -> str:
        """同步数据库URL"""
        if self.database_url.startswith("postgresql+asyncpg://"):
            return self.database_url.replace(
                "postgresql+asyncpg://", "postgresql+psycopg2://"
            )
        elif self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+psycopg2://")
        return self.database_url

    @property
    def async_database_url(self) -> str:
        """异步数据库URL"""
        if self.database_url.startswith("postgresql+psycopg2://"):
            return self.database_url.replace(
                "postgresql+psycopg2://", "postgresql+asyncpg://"
            )
        elif self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://")
        return self.database_url

    @property
    def connection_params(self) -> dict:
        """数据库连接参数"""
        return {
            "host": self.database_host,
            "port": self.database_port,
            "database": self.database_name,
            "user": self.database_user,
            "password": self.database_password,
            "connect_timeout": self.connect_timeout,
            "command_timeout": self.command_timeout,
            "sslmode": self.ssl_mode,
        }

    @property
    def pool_config(self) -> dict:
        """连接池配置参数"""
        return {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "pool_pre_ping": self.pool_pre_ping,
        }

    @property
    def engine_config(self) -> dict:
        """SQLAlchemy引擎配置"""
        return {
            "echo": self.echo_sql,
            "echo_pool": self.echo_pool,
            "future": True,
            **self.pool_config,
        }


@lru_cache()
def get_database_config() -> DatabaseConfig:
    """
    获取数据库配置实例
    使用LRU缓存避免重复创建
    """
    return DatabaseConfig()
