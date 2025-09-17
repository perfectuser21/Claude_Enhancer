#!/usr/bin/env python3
"""
Perfect21数据库配置和连接管理
支持SQLite、PostgreSQL、MySQL等数据库
增强版：连接池、资源管理、异步支持
"""

import os
import sys
import sqlite3
import asyncio
import threading
import time
from typing import Dict, Any, Optional, Union
from contextlib import contextmanager, asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
import logging
import atexit

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.logger import log_info, log_error
from modules.config import config
from modules.resource_manager import ResourceManager, ResourceType, ConnectionPool

logger = logging.getLogger(__name__)

@dataclass
class DatabaseLimits:
    """数据库连接限制"""
    max_connections: int = 20
    connection_timeout: int = 30
    idle_timeout: int = 300
    max_retries: int = 3
    health_check_interval: int = 60

class DatabaseConfig:
    """数据库配置类"""

    def __init__(self):
        """初始化数据库配置"""
        self.db_type = config.get('database.type', 'sqlite')
        self.db_host = config.get('database.host', 'localhost')
        self.db_port = config.get('database.port', 5432)
        self.db_name = config.get('database.name', 'perfect21')
        self.db_user = config.get('database.user', 'perfect21')
        self.db_password = config.get('database.password', '')
        self.db_path = config.get('database.path', 'data/perfect21.db')

        # 连接池配置
        self.pool_size = config.get('database.pool_size', 10)
        self.max_overflow = config.get('database.max_overflow', 20)
        self.pool_timeout = config.get('database.pool_timeout', 30)
        self.limits = DatabaseLimits(
            max_connections=self.pool_size + self.max_overflow,
            connection_timeout=self.pool_timeout
        )

        log_info(f"数据库配置初始化: 类型={self.db_type}, 连接池大小={self.pool_size}")

    def get_connection_string(self) -> str:
        """获取数据库连接字符串"""
        if self.db_type == 'sqlite':
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            return f"sqlite:///{self.db_path}"
        elif self.db_type == 'postgresql':
            return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        elif self.db_type == 'mysql':
            return f"mysql+pymysql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
        else:
            raise ValueError(f"不支持的数据库类型: {self.db_type}")

    def get_sqlite_connection(self) -> sqlite3.Connection:
        """获取SQLite连接"""
        if self.db_type != 'sqlite':
            raise ValueError("只能在SQLite数据库类型下使用此方法")

        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row

        # 启用外键约束
        conn.execute("PRAGMA foreign_keys = ON")

        # 性能优化设置
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA cache_size = 10000")
        conn.execute("PRAGMA temp_store = MEMORY")

        return conn

class DatabaseConnectionPool:
    """数据库连接池"""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._pool = []
        self._active_connections = {}
        self._lock = threading.RLock()
        self._created_count = 0
        self._last_health_check = time.time()

    def _create_connection(self) -> sqlite3.Connection:
        """创建新连接"""
        if self.config.db_type != 'sqlite':
            raise ValueError("只支持SQLite数据库")

        os.makedirs(os.path.dirname(self.config.db_path), exist_ok=True)
        conn = sqlite3.connect(
            self.config.db_path,
            check_same_thread=False,
            timeout=self.config.limits.connection_timeout
        )
        conn.row_factory = sqlite3.Row

        # 性能优化设置
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = NORMAL")
        conn.execute("PRAGMA cache_size = 10000")
        conn.execute("PRAGMA temp_store = MEMORY")

        self._created_count += 1
        return conn

    def acquire(self, timeout: float = None) -> sqlite3.Connection:
        """获取连接"""
        timeout = timeout or self.config.limits.connection_timeout

        with self._lock:
            # 尝试从池中获取
            if self._pool:
                return self._pool.pop()

            # 检查连接数限制
            if len(self._active_connections) < self.config.limits.max_connections:
                conn = self._create_connection()
                conn_id = f"conn_{self._created_count}"
                self._active_connections[conn_id] = {
                    'connection': conn,
                    'created_at': time.time(),
                    'last_used': time.time()
                }
                return conn

            raise RuntimeError("数据库连接池已满")

    def release(self, connection: sqlite3.Connection):
        """释放连接"""
        with self._lock:
            # 找到连接ID
            conn_id = None
            for cid, conn_info in self._active_connections.items():
                if conn_info['connection'] is connection:
                    conn_id = cid
                    break

            if conn_id:
                del self._active_connections[conn_id]

                # 检查连接是否仍然有效
                try:
                    connection.execute("SELECT 1")
                    # 连接有效，放回池中
                    if len(self._pool) < self.config.pool_size:
                        self._pool.append(connection)
                    else:
                        connection.close()
                except Exception:
                    # 连接无效，关闭它
                    try:
                        connection.close()
                    except Exception:
                        pass

    def close_all(self):
        """关闭所有连接"""
        with self._lock:
            # 关闭池中的连接
            for conn in self._pool:
                try:
                    conn.close()
                except Exception:
                    pass
            self._pool.clear()

            # 关闭活跃连接
            for conn_info in self._active_connections.values():
                try:
                    conn_info['connection'].close()
                except Exception:
                    pass
            self._active_connections.clear()

    def health_check(self):
        """健康检查"""
        current_time = time.time()
        if current_time - self._last_health_check < self.config.limits.health_check_interval:
            return

        with self._lock:
            # 检查闲置连接
            expired_connections = []
            for cid, conn_info in self._active_connections.items():
                if current_time - conn_info['last_used'] > self.config.limits.idle_timeout:
                    expired_connections.append(cid)

            # 关闭过期连接
            for cid in expired_connections:
                conn_info = self._active_connections.pop(cid)
                try:
                    conn_info['connection'].close()
                except Exception:
                    pass

            self._last_health_check = current_time

    def get_stats(self) -> Dict[str, Any]:
        """获取连接池统计"""
        with self._lock:
            return {
                'pool_size': len(self._pool),
                'active_connections': len(self._active_connections),
                'max_connections': self.config.limits.max_connections,
                'total_created': self._created_count
            }

class DatabaseManager:
    """数据库管理器 - 带连接池和资源管理"""

    def __init__(self, config_instance: DatabaseConfig = None):
        """初始化数据库管理器"""
        self.config = config_instance or DatabaseConfig()
        self._connection_pool = None
        self._resource_manager = ResourceManager()
        self._initialized = False
        self._health_check_task = None
        self._cleanup_registered = False

        # 注册资源管理
        manager_id = f"db_manager_{id(self)}"
        self._resource_manager.register_resource(
            manager_id, self, ResourceType.OTHER,
            cleanup_callback=self._cleanup_resources
        )

        # 注册清理函数
        if not self._cleanup_registered:
            atexit.register(self._emergency_cleanup)
            self._cleanup_registered = True

        log_info("DatabaseManager初始化完成")

    def initialize(self):
        """初始化数据库"""
        try:
            if self.config.db_type == 'sqlite':
                # 初始化连接池
                self._connection_pool = DatabaseConnectionPool(self.config)
                self._init_sqlite()

                # 启动健康检查
                try:
                    if asyncio.get_running_loop():
                        self._health_check_task = asyncio.create_task(self._periodic_health_check())
                except RuntimeError:
                    # 没有运行的事件循环
                    pass
            else:
                self._init_other_db()

            self._initialized = True
            log_info("数据库初始化完成")

        except Exception as e:
            log_error("数据库初始化失败", e)
            raise

    def _init_sqlite(self):
        """初始化SQLite数据库"""
        if not self._connection_pool:
            self._connection_pool = DatabaseConnectionPool(self.config)

        conn = self._connection_pool.acquire()
        try:
            # 创建基础表结构
            self._create_base_tables(conn)
        finally:
            self._connection_pool.release(conn)

    def _init_other_db(self):
        """初始化其他类型数据库"""
        # 这里可以添加PostgreSQL、MySQL等数据库的初始化逻辑
        log_info(f"初始化{self.config.db_type}数据库（待实现）")

    def _create_base_tables(self, conn: sqlite3.Connection):
        """创建基础表结构"""
        cursor = conn.cursor()

        # 系统配置表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_config (
                key VARCHAR(100) PRIMARY KEY,
                value TEXT,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 操作日志表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS operation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                operation VARCHAR(100) NOT NULL,
                details TEXT,
                ip_address VARCHAR(45),
                user_agent TEXT,
                status VARCHAR(20) DEFAULT 'success',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_operation_logs_user_id ON operation_logs (user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_operation_logs_operation ON operation_logs (operation)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_operation_logs_created_at ON operation_logs (created_at)')

        # API调用统计表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                endpoint VARCHAR(200) NOT NULL,
                method VARCHAR(10) NOT NULL,
                status_code INTEGER NOT NULL,
                response_time REAL,
                user_id INTEGER,
                ip_address VARCHAR(45),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 创建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_api_stats_endpoint ON api_stats (endpoint)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_api_stats_user_id ON api_stats (user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_api_stats_created_at ON api_stats (created_at)')

        conn.commit()

    @contextmanager
    def get_connection(self, readonly: bool = False):
        """获取数据库连接（上下文管理器）"""
        if not self._initialized:
            self.initialize()

        if self.config.db_type == 'sqlite':
            conn = self._connection_pool.acquire()
            conn_id = f"temp_conn_{id(conn)}_{time.time()}"

            # 注册连接到资源管理器
            self._resource_manager.register_resource(
                conn_id, conn, ResourceType.DATABASE_CONNECTION,
                cleanup_callback=lambda: self._safe_release_connection(conn)
            )

            try:
                yield conn
            finally:
                # 注销并释放连接
                self._resource_manager.unregister_resource(conn_id)
                self._connection_pool.release(conn)
        else:
            # 其他数据库类型的连接获取逻辑
            raise NotImplementedError(f"暂不支持{self.config.db_type}数据库")

    @asynccontextmanager
    async def get_connection_async(self, readonly: bool = False):
        """异步获取数据库连接"""
        if not self._initialized:
            # 在executor中初始化
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.initialize)

        # 在executor中获取连接
        loop = asyncio.get_event_loop()
        conn = await loop.run_in_executor(None, self._connection_pool.acquire)

        conn_id = f"async_conn_{id(conn)}_{time.time()}"
        await self._resource_manager.register_resource_async(
            conn_id, conn, ResourceType.DATABASE_CONNECTION,
            async_cleanup_callback=lambda: self._async_release_connection(conn)
        )

        try:
            yield conn
        finally:
            await self._resource_manager.unregister_resource_async(conn_id)
            await loop.run_in_executor(None, self._connection_pool.release, conn)

    def execute_query(self, query: str, params: tuple = None,
                     fetch: bool = True) -> Union[list, int]:
        """执行查询"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if fetch:
                if query.strip().upper().startswith('SELECT'):
                    return [dict(row) for row in cursor.fetchall()]
                else:
                    return cursor.rowcount
            else:
                conn.commit()
                return cursor.rowcount

    def insert_record(self, table: str, data: Dict[str, Any]) -> int:
        """插入记录"""
        columns = list(data.keys())
        placeholders = ', '.join(['?' for _ in columns])
        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(data.values()))
            conn.commit()
            return cursor.lastrowid

    def update_record(self, table: str, data: Dict[str, Any],
                     where_clause: str, where_params: tuple = None) -> int:
        """更新记录"""
        set_clause = ', '.join([f"{col} = ?" for col in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"

        params = tuple(data.values())
        if where_params:
            params += where_params

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount

    def delete_record(self, table: str, where_clause: str,
                     where_params: tuple = None) -> int:
        """删除记录"""
        query = f"DELETE FROM {table} WHERE {where_clause}"

        with self.get_connection() as conn:
            cursor = conn.cursor()
            if where_params:
                cursor.execute(query, where_params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor.rowcount

    def get_table_info(self, table: str) -> list:
        """获取表结构信息"""
        if self.config.db_type == 'sqlite':
            query = f"PRAGMA table_info({table})"
        else:
            # 其他数据库的表结构查询
            raise NotImplementedError(f"暂不支持{self.config.db_type}数据库")

        return self.execute_query(query)

    def table_exists(self, table: str) -> bool:
        """检查表是否存在"""
        if self.config.db_type == 'sqlite':
            query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
            result = self.execute_query(query, (table,))
            return len(result) > 0
        else:
            raise NotImplementedError(f"暂不支持{self.config.db_type}数据库")

    def backup_database(self, backup_path: str) -> bool:
        """备份数据库"""
        try:
            if self.config.db_type == 'sqlite':
                import shutil
                shutil.copy2(self.config.db_path, backup_path)
                log_info(f"数据库备份完成: {backup_path}")
                return True
            else:
                # 其他数据库的备份逻辑
                log_info(f"备份{self.config.db_type}数据库（待实现）")
                return False

        except Exception as e:
            log_error("数据库备份失败", e)
            return False

    def optimize_database(self):
        """优化数据库"""
        try:
            if self.config.db_type == 'sqlite':
                with self.get_connection() as conn:
                    conn.execute("VACUUM")
                    conn.execute("ANALYZE")
                    conn.commit()
                log_info("SQLite数据库优化完成")
            else:
                log_info(f"优化{self.config.db_type}数据库（待实现）")

        except Exception as e:
            log_error("数据库优化失败", e)

    def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        try:
            stats = {
                'database_type': self.config.db_type,
                'database_path': self.config.db_path if self.config.db_type == 'sqlite' else None,
                'initialized': self._initialized,
                'connection_pool_stats': self.get_connection_pool_stats()
            }

            if self.config.db_type == 'sqlite' and os.path.exists(self.config.db_path):
                stats['database_size'] = os.path.getsize(self.config.db_path)

                # 获取表统计
                tables_query = "SELECT name FROM sqlite_master WHERE type='table'"
                tables = self.execute_query(tables_query)
                stats['table_count'] = len(tables)

                # 获取记录统计
                table_stats = {}
                for table in tables:
                    table_name = table['name']
                    count_query = f"SELECT COUNT(*) as count FROM {table_name}"
                    count_result = self.execute_query(count_query)
                    table_stats[table_name] = count_result[0]['count']

                stats['table_stats'] = table_stats

            return stats

        except Exception as e:
            log_error("获取数据库统计失败", e)
            return {'error': str(e)}

    def _safe_release_connection(self, conn: sqlite3.Connection):
        """安全释放连接"""
        try:
            if self._connection_pool:
                self._connection_pool.release(conn)
        except Exception as e:
            logger.warning(f"释放数据库连接失败: {e}")

    async def _async_release_connection(self, conn: sqlite3.Connection):
        """异步释放连接"""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._safe_release_connection, conn)
        except Exception as e:
            logger.warning(f"异步释放数据库连接失败: {e}")

    async def _periodic_health_check(self):
        """定期健康检查"""
        while self._connection_pool and self._initialized:
            try:
                await asyncio.sleep(self.config.limits.health_check_interval)
                if self._connection_pool:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, self._connection_pool.health_check)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"数据库健康检查失败: {e}")

    def _cleanup_resources(self):
        """清理资源"""
        try:
            # 停止健康检查
            if self._health_check_task and not self._health_check_task.done():
                self._health_check_task.cancel()

            # 关闭连接池
            if self._connection_pool:
                self._connection_pool.close_all()
                self._connection_pool = None

            self._initialized = False
            log_info("DatabaseManager清理完成")
        except Exception as e:
            log_error("DatabaseManager清理失败", e)

    def _emergency_cleanup(self):
        """紧急清理 - 程序退出时调用"""
        try:
            self._cleanup_resources()
        except Exception:
            pass  # 退出时忽略所有异常

    def cleanup(self):
        """公开清理方法"""
        self._cleanup_resources()

    def get_connection_pool_stats(self) -> Dict[str, Any]:
        """获取连接池统计"""
        if self._connection_pool:
            return self._connection_pool.get_stats()
        return {}

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self._cleanup_resources()

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        # 在executor中运行清理
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._cleanup_resources)

# 全局数据库管理器实例
_db_manager_instance = None

def get_db_manager(config: DatabaseConfig = None) -> DatabaseManager:
    """获取全局数据库管理器实例"""
    global _db_manager_instance
    if _db_manager_instance is None:
        _db_manager_instance = DatabaseManager(config)
    return _db_manager_instance

# 便捷访问
db_manager = get_db_manager()

# 数据库上下文管理器
@contextmanager
def managed_database(config: DatabaseConfig = None):
    """创建受管理的数据库管理器"""
    manager = None
    try:
        manager = DatabaseManager(config)
        manager.initialize()
        yield manager
    finally:
        if manager:
            manager._cleanup_resources()

@asynccontextmanager
async def managed_database_async(config: DatabaseConfig = None):
    """创建受管理的数据库管理器（异步）"""
    manager = None
    try:
        manager = DatabaseManager(config)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, manager.initialize)
        yield manager
    finally:
        if manager:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, manager._cleanup_resources)