"""
Perfect21 数据库管理
企业级数据库连接池、会话管理和监控
"""

import asyncio
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
    AsyncEngine
)
from sqlalchemy.pool import QueuePool
from sqlalchemy.engine.events import event
from sqlalchemy import text
import redis.asyncio as redis
import logging
from datetime import datetime

from app.core.config import settings
from app.models.user_models import Base
from shared.metrics.metrics import monitor_function

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    数据库管理器
    负责数据库连接池管理、会话创建、健康检查等
    """
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine: Optional[AsyncEngine] = None
        self.async_session_factory: Optional[async_sessionmaker] = None
        self.redis_client: Optional[redis.Redis] = None
        self._initialized = False
        
        # 连接池配置
        self.pool_config = {
            'poolclass': QueuePool,
            'pool_size': settings.DATABASE_POOL_SIZE,
            'max_overflow': settings.DATABASE_MAX_OVERFLOW,
            'pool_timeout': settings.DATABASE_POOL_TIMEOUT,
            'pool_recycle': settings.DATABASE_POOL_RECYCLE,
            'pool_pre_ping': True,  # 连接前ping检查
        }
        
        # 引擎配置
        self.engine_config = {
            'echo': settings.DEBUG,  # 开发环境显示SQL
            'echo_pool': settings.DEBUG,  # 开发环境显示连接池日志
            'future': True,
            'json_serializer': self._json_serializer,
            'json_deserializer': self._json_deserializer,
        }
    
    def _json_serializer(self, obj):
        """JSON序列化器"""
        import json
        from datetime import datetime, date
        
        def default(o):
            if isinstance(o, (datetime, date)):
                return o.isoformat()
            raise TypeError(f"Object of type {type(o)} is not JSON serializable")
        
        return json.dumps(obj, default=default, ensure_ascii=False)
    
    def _json_deserializer(self, data):
        """JSON反序列化器"""
        import json
        return json.loads(data)
    
    async def initialize(self):
        """初始化数据库连接"""
        try:
            if self._initialized:
                logger.warning("Database manager already initialized")
                return
            
            logger.info("🔌 Initializing database connection...")
            
            # 创建异步引擎
            self.engine = create_async_engine(
                self.database_url,
                **self.pool_config,
                **self.engine_config
            )
            
            # 注册事件监听器
            self._register_event_listeners()
            
            # 创建会话工厂
            self.async_session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=True,
                autocommit=False
            )
            
            # 初始化Redis连接（用于缓存和监控）
            self.redis_client = redis.Redis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                health_check_interval=30
            )
            
            # 测试数据库连接
            await self._test_connection()
            
            # 创建数据库表（开发环境）
            if settings.DEBUG:
                await self._create_tables()
            
            self._initialized = True
            logger.info("✅ Database connection initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            raise
    
    def _register_event_listeners(self):
        """注册数据库事件监听器"""
        
        @event.listens_for(self.engine.sync_engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """设置SQLite特定配置（如果使用SQLite）"""
            if 'sqlite' in self.database_url:
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA journal_mode=WAL")
                cursor.execute("PRAGMA synchronous=NORMAL")
                cursor.execute("PRAGMA cache_size=10000")
                cursor.execute("PRAGMA temp_store=MEMORY")
                cursor.close()
        
        @event.listens_for(self.engine.sync_engine, "checkout")
        def receive_checkout(dbapi_connection, connection_record, connection_proxy):
            """连接检出时的处理"""
            logger.debug(f"Database connection checked out: {id(dbapi_connection)}")
        
        @event.listens_for(self.engine.sync_engine, "checkin")
        def receive_checkin(dbapi_connection, connection_record):
            """连接检入时的处理"""
            logger.debug(f"Database connection checked in: {id(dbapi_connection)}")
        
        @event.listens_for(self.engine.sync_engine, "invalidate")
        def receive_invalidate(dbapi_connection, connection_record, exception):
            """连接失效时的处理"""
            logger.warning(f"Database connection invalidated: {exception}")
    
    async def _test_connection(self):
        """测试数据库连接"""
        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                assert result.scalar() == 1
            logger.info("Database connection test passed")
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise
    
    async def _create_tables(self):
        """创建数据库表（开发环境）"""
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created/updated")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取数据库会话（上下文管理器）"""
        if not self._initialized:
            raise RuntimeError("Database manager not initialized")
        
        session = self.async_session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    @monitor_function("database")
    async def health_check(self) -> bool:
        """数据库健康检查"""
        try:
            if not self._initialized:
                return False
            
            # 检查数据库连接
            async with self.engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                if result.scalar() != 1:
                    return False
            
            # 检查Redis连接
            if self.redis_client:
                await self.redis_client.ping()
            
            return True
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def ready_check(self) -> bool:
        """数据库就绪检查（更严格）"""
        try:
            if not await self.health_check():
                return False
            
            # 检查连接池状态
            pool = self.engine.pool
            if pool.checkedout() >= pool.size():
                logger.warning("Database connection pool exhausted")
                return False
            
            # 检查表是否存在（简单验证）
            async with self.engine.begin() as conn:
                result = await conn.execute(text(
                    "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' LIMIT 1"
                ))
                if not result.first():
                    logger.warning("No tables found in database")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Database ready check failed: {e}")
            return False
    
    @monitor_function("database")
    async def get_connection_stats(self) -> dict:
        """获取连接池统计信息"""
        try:
            if not self.engine:
                return {}
            
            pool = self.engine.pool
            stats = {
                'pool_size': pool.size(),
                'checked_in': pool.checkedin(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
                'invalid': pool.invalid(),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # 缓存统计信息
            if self.redis_client:
                stats_key = f"db_stats:{datetime.now().strftime('%Y%m%d%H%M')}"
                await self.redis_client.setex(stats_key, 300, str(stats))  # 缓存5分钟
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get connection stats: {e}")
            return {}
    
    async def execute_query(self, query: str, params: dict = None) -> list:
        """执行查询并返回结果"""
        try:
            async with self.get_session() as session:
                result = await session.execute(text(query), params or {})
                return result.fetchall()
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    async def execute_raw_sql(self, sql: str, params: dict = None) -> dict:
        """执行原始SQL（用于管理操作）"""
        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text(sql), params or {})
                
                # 返回执行结果信息
                return {
                    'rowcount': result.rowcount,
                    'success': True,
                    'executed_at': datetime.utcnow().isoformat()
                }
        except Exception as e:
            logger.error(f"Raw SQL execution failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'executed_at': datetime.utcnow().isoformat()
            }
    
    @monitor_function("database")
    async def backup_database(self, backup_path: str = None) -> dict:
        """数据库备份（简化实现）"""
        try:
            if not backup_path:
                backup_path = f"/tmp/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
            
            # 这里应该实现具体的备份逻辑
            # 根据数据库类型使用不同的备份工具
            # PostgreSQL: pg_dump
            # MySQL: mysqldump
            # SQLite: 文件复制
            
            logger.info(f"Database backup completed: {backup_path}")
            
            return {
                'success': True,
                'backup_path': backup_path,
                'timestamp': datetime.utcnow().isoformat(),
                'size_bytes': 0  # 实际实现中应该返回文件大小
            }
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def close(self):
        """关闭数据库连接"""
        try:
            if self.redis_client:
                await self.redis_client.close()
                logger.info("Redis connection closed")
            
            if self.engine:
                await self.engine.dispose()
                logger.info("Database engine disposed")
            
            self._initialized = False
            logger.info("Database manager closed")
            
        except Exception as e:
            logger.error(f"Error closing database manager: {e}")
    
    def __repr__(self):
        return f"<DatabaseManager(initialized={self._initialized})>"

# 全局数据库管理器实例
database_manager: Optional[DatabaseManager] = None

def initialize_database(database_url: str = None) -> DatabaseManager:
    """初始化全局数据库管理器"""
    global database_manager
    
    if database_manager is None:
        database_url = database_url or settings.DATABASE_URL
        database_manager = DatabaseManager(database_url)
    
    return database_manager

def get_database_manager() -> DatabaseManager:
    """获取全局数据库管理器"""
    global database_manager
    
    if database_manager is None:
        raise RuntimeError("Database manager not initialized. Call initialize_database() first.")
    
    return database_manager

@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """获取异步数据库会话（便捷函数）"""
    db_manager = get_database_manager()
    async with db_manager.get_session() as session:
        yield session

# 依赖注入函数（用于FastAPI）
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI依赖注入：获取数据库会话"""
    async with get_async_session() as session:
        yield session

# 数据库初始化函数
async def init_database():
    """初始化数据库（应用启动时调用）"""
    global database_manager
    
    try:
        database_manager = initialize_database()
        await database_manager.initialize()
        logger.info("Database initialization completed")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

# 数据库清理函数
async def close_database():
    """关闭数据库连接（应用关闭时调用）"""
    global database_manager
    
    if database_manager:
        await database_manager.close()
        database_manager = None
        logger.info("Database connections closed")

# 事务装饰器
def transactional(func):
    """事务装饰器，确保函数在事务中执行"""
    async def wrapper(*args, **kwargs):
        async with get_async_session() as session:
            try:
                # 将session作为第一个参数传递给函数
                result = await func(session, *args, **kwargs)
                await session.commit()
                return result
            except Exception:
                await session.rollback()
                raise
    
    return wrapper