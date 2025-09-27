"""
核心功能模块
包含数据库配置、连接管理等核心功能
"""

from .database import DatabaseManager, get_db, init_db
from .config import DatabaseConfig, get_database_config

__all__ = [
    "DatabaseManager",
    "get_db",
    "init_db",
    "DatabaseConfig",
    "get_database_config",
]
