#!/usr/bin/env python3
"""
数据库连接和会话管理
支持PostgreSQL和SQLite
"""

import logging
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from backend.core.config import get_settings

# 获取配置
settings = get_settings()

# 创建数据库引擎
if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite配置
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=settings.DATABASE_ECHO
    )

    # SQLite外键约束支持
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

else:
    # PostgreSQL配置
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_timeout=settings.DATABASE_POOL_TIMEOUT,
        echo=settings.DATABASE_ECHO
    )

# 创建SessionLocal类
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类
Base = declarative_base()

# 日志记录器
logger = logging.getLogger(__name__)

def get_database_session() -> Generator[Session, None, None]:
    """
    获取数据库会话
    使用依赖注入模式，自动管理会话生命周期
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"数据库会话错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def create_tables():
    """创建数据库表"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建成功")
    except Exception as e:
        logger.error(f"数据库表创建失败: {e}")
        raise

def drop_tables():
    """删除数据库表（仅用于测试）"""
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("数据库表删除成功")
    except Exception as e:
        logger.error(f"数据库表删除失败: {e}")
        raise

class DatabaseManager:
    """数据库管理器"""

    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal

    def get_session(self) -> Session:
        """获取新的数据库会话"""
        return self.SessionLocal()

    def close_session(self, session: Session):
        """关闭数据库会话"""
        try:
            session.close()
        except Exception as e:
            logger.error(f"关闭数据库会话失败: {e}")

    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            with self.engine.connect() as connection:
                connection.execute("SELECT 1")
            logger.info("数据库连接测试成功")
            return True
        except Exception as e:
            logger.error(f"数据库连接测试失败: {e}")
            return False

    def get_engine_info(self) -> dict:
        """获取数据库引擎信息"""
        return {
            'url': str(self.engine.url),
            'driver': self.engine.driver,
            'dialect': self.engine.dialect.name,
            'pool_size': getattr(self.engine.pool, 'size', None),
            'max_overflow': getattr(self.engine.pool, 'max_overflow', None),
            'pool_timeout': getattr(self.engine.pool, 'timeout', None)
        }

# 全局数据库管理器实例
db_manager = DatabaseManager()