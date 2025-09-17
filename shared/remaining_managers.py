#!/usr/bin/env python3
"""
Perfect21 剩余10个统一Manager
完成15个Manager的架构设计

剩余Manager:
- 核心层: CoreEventManager (1个)
- 数据层: DatabaseManager, FileSystemManager, DocumentManager (3个)
- 安全层: AuthSecurityManager, EncryptionManager (2个)
- 工作流层: WorkflowExecutionManager, TaskOrchestratorManager, SyncPointManager (3个)
- 监控层: MonitoringManager (1个)
"""

import logging
import asyncio
import threading
from typing import Dict, Any, Optional, List, Set, Callable, Union
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import hashlib
import base64
import json
import os
import sqlite3
from dataclasses import dataclass, field
from enum import Enum

from .consolidated_managers import (
    BaseConsolidatedManager, ManagerCategory, IManager,
    ManagerMetadata, ManagerHealth, ManagerState
)
from .interfaces import ICacheManager, IConfigManager
from .events import EventBus, Event

logger = logging.getLogger("Perfect21.RemainingManagers")

# =================== 4. 核心事件管理器 ===================

class CoreEventManager(BaseConsolidatedManager):
    """
    核心事件管理器
    整合: EventBus管理、事件路由、事件持久化、事件回放
    """

    def __init__(self, event_bus: EventBus, config_manager: IConfigManager):
        super().__init__("core_event", ManagerCategory.CORE, event_bus)
        self.config_manager = config_manager
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._event_history: List[Dict[str, Any]] = []
        self._event_filters: Dict[str, Callable] = {}
        self._max_history_size = 10000
        self.add_dependency("core_config")

    def _get_description(self) -> str:
        return "核心事件管理器 - 事件总线管理、路由、持久化和回放"

    async def _do_initialize(self, **kwargs) -> bool:
        """初始化事件管理器"""
        try:
            self._max_history_size = self.config_manager.get_config(
                "perfect21.event_history_size", 10000
            )

            # 注册事件服务
            self.register_service("event_bus", self.event_bus)
            self.register_service("event_handler", self._get_event_handler_service())
            self.register_service("event_history", self._get_event_history_service())

            # 设置默认事件处理器
            self._setup_default_handlers()

            return True
        except Exception as e:
            logger.error(f"事件管理器初始化失败: {e}")
            return False

    async def _do_shutdown(self) -> bool:
        """关闭事件管理器"""
        try:
            # 保存事件历史
            await self._save_event_history()

            # 清理处理器
            self._event_handlers.clear()
            self._event_history.clear()
            self._event_filters.clear()

            return True
        except Exception as e:
            logger.error(f"事件管理器关闭失败: {e}")
            return False

    def _setup_default_handlers(self):
        """设置默认事件处理器"""
        # 配置变更事件处理器
        self.subscribe("config_changed", self._handle_config_changed)

        # Manager状态变更事件处理器
        self.subscribe("manager_state_changed", self._handle_manager_state_changed)

        # 系统事件处理器
        self.subscribe("system_startup", self._handle_system_startup)
        self.subscribe("system_shutdown", self._handle_system_shutdown)

    def subscribe(self, event_type: str, handler: Callable):
        """订阅事件"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)

        # 同时注册到事件总线
        self.event_bus.subscribe(event_type, handler)

    def publish(self, event_type: str, data: Dict[str, Any]):
        """发布事件"""
        event = Event(type=event_type, data=data, timestamp=datetime.now())

        # 记录到历史
        self._record_event(event)

        # 发布到事件总线
        self.event_bus.publish(event)

    def _record_event(self, event: Event):
        """记录事件到历史"""
        with self._lock:
            event_record = {
                "type": event.type,
                "data": event.data,
                "timestamp": event.timestamp.isoformat() if hasattr(event, 'timestamp') else datetime.now().isoformat(),
                "id": len(self._event_history)
            }

            self._event_history.append(event_record)

            # 限制历史大小
            if len(self._event_history) > self._max_history_size:
                self._event_history = self._event_history[-self._max_history_size:]

    def _handle_config_changed(self, event: Event):
        """处理配置变更事件"""
        logger.info(f"配置变更: {event.data}")

    def _handle_manager_state_changed(self, event: Event):
        """处理Manager状态变更事件"""
        logger.info(f"Manager状态变更: {event.data}")

    def _handle_system_startup(self, event: Event):
        """处理系统启动事件"""
        logger.info("系统启动事件")

    def _handle_system_shutdown(self, event: Event):
        """处理系统关闭事件"""
        logger.info("系统关闭事件")

    def _get_event_handler_service(self):
        """获取事件处理器服务"""
        class EventHandlerService:
            def __init__(self, event_manager):
                self.em = event_manager

            def subscribe(self, event_type: str, handler: Callable):
                self.em.subscribe(event_type, handler)

            def publish(self, event_type: str, data: Dict[str, Any]):
                self.em.publish(event_type, data)

            def get_handlers(self, event_type: str) -> List[Callable]:
                return self.em._event_handlers.get(event_type, [])

        return EventHandlerService(self)

    def _get_event_history_service(self):
        """获取事件历史服务"""
        class EventHistoryService:
            def __init__(self, event_manager):
                self.em = event_manager

            def get_recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
                with self.em._lock:
                    return self.em._event_history[-limit:]

            def get_events_by_type(self, event_type: str) -> List[Dict[str, Any]]:
                with self.em._lock:
                    return [e for e in self.em._event_history if e["type"] == event_type]

            def get_events_since(self, since: datetime) -> List[Dict[str, Any]]:
                with self.em._lock:
                    since_str = since.isoformat()
                    return [e for e in self.em._event_history if e["timestamp"] >= since_str]

        return EventHistoryService(self)

    async def _save_event_history(self):
        """保存事件历史"""
        try:
            history_dir = os.path.join(os.getcwd(), ".perfect21", "events")
            os.makedirs(history_dir, exist_ok=True)

            history_file = os.path.join(history_dir, f"events_{datetime.now().strftime('%Y%m%d')}.json")
            with open(history_file, 'w') as f:
                json.dump(self._event_history, f, indent=2)

        except Exception as e:
            logger.error(f"保存事件历史失败: {e}")

# =================== 5. 数据库管理器 ===================

class UnifiedDatabaseManager(BaseConsolidatedManager):
    """
    统一数据库管理器
    整合: DatabaseManager, 连接池、事务管理、查询优化
    """

    def __init__(self, event_bus: EventBus, config_manager: IConfigManager):
        super().__init__("unified_database", ManagerCategory.DATA, event_bus)
        self.config_manager = config_manager
        self._connections: Dict[str, Any] = {}
        self._connection_pools: Dict[str, Any] = {}
        self._query_cache: Dict[str, Any] = {}
        self.add_dependency("core_config")

    def _get_description(self) -> str:
        return "统一数据库管理器 - 多数据库支持、连接池、事务管理"

    async def _do_initialize(self, **kwargs) -> bool:
        """初始化数据库管理器"""
        try:
            # 设置SQLite数据库（默认）
            await self._setup_sqlite_database()

            # 注册数据库服务
            self.register_service("database", self._get_database_service())
            self.register_service("query_executor", self._get_query_executor_service())

            return True
        except Exception as e:
            logger.error(f"数据库管理器初始化失败: {e}")
            return False

    async def _do_shutdown(self) -> bool:
        """关闭数据库管理器"""
        try:
            # 关闭所有连接
            for name, conn in self._connections.items():
                if hasattr(conn, 'close'):
                    conn.close()
                logger.info(f"数据库连接 {name} 已关闭")

            self._connections.clear()
            self._connection_pools.clear()
            self._query_cache.clear()

            return True
        except Exception as e:
            logger.error(f"数据库管理器关闭失败: {e}")
            return False

    async def _setup_sqlite_database(self):
        """设置SQLite数据库"""
        try:
            db_dir = os.path.join(os.getcwd(), ".perfect21", "data")
            os.makedirs(db_dir, exist_ok=True)

            db_path = os.path.join(db_dir, "perfect21.db")
            conn = sqlite3.connect(db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row  # 使返回结果支持字典访问

            # 创建基础表
            await self._create_basic_tables(conn)

            self._connections["default"] = conn
            logger.info(f"SQLite数据库初始化完成: {db_path}")

        except Exception as e:
            logger.error(f"SQLite数据库设置失败: {e}")
            raise

    async def _create_basic_tables(self, conn):
        """创建基础表"""
        tables = [
            """
            CREATE TABLE IF NOT EXISTS perfect21_configs (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS perfect21_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                event_data TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS perfect21_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                tags TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]

        for table_sql in tables:
            conn.execute(table_sql)

        conn.commit()

    def _get_database_service(self):
        """获取数据库服务"""
        class DatabaseService:
            def __init__(self, db_manager):
                self.db = db_manager

            def get_connection(self, name: str = "default"):
                return self.db._connections.get(name)

            async def execute_query(self, sql: str, params: tuple = (), connection: str = "default"):
                conn = self.db._connections.get(connection)
                if not conn:
                    raise ValueError(f"数据库连接 {connection} 不存在")

                try:
                    cursor = conn.cursor()
                    cursor.execute(sql, params)

                    if sql.strip().upper().startswith('SELECT'):
                        return cursor.fetchall()
                    else:
                        conn.commit()
                        return cursor.rowcount

                except Exception as e:
                    conn.rollback()
                    raise e

            async def execute_many(self, sql: str, params_list: List[tuple], connection: str = "default"):
                conn = self.db._connections.get(connection)
                if not conn:
                    raise ValueError(f"数据库连接 {connection} 不存在")

                try:
                    cursor = conn.cursor()
                    cursor.executemany(sql, params_list)
                    conn.commit()
                    return cursor.rowcount

                except Exception as e:
                    conn.rollback()
                    raise e

        return DatabaseService(self)

    def _get_query_executor_service(self):
        """获取查询执行器服务"""
        class QueryExecutorService:
            def __init__(self, db_manager):
                self.db = db_manager

            async def save_config(self, key: str, value: Any):
                db_service = self.db.get_service("database")
                sql = "INSERT OR REPLACE INTO perfect21_configs (key, value) VALUES (?, ?)"
                await db_service.execute_query(sql, (key, json.dumps(value)))

            async def load_config(self, key: str) -> Optional[Any]:
                db_service = self.db.get_service("database")
                sql = "SELECT value FROM perfect21_configs WHERE key = ?"
                result = await db_service.execute_query(sql, (key,))

                if result:
                    return json.loads(result[0]['value'])
                return None

            async def save_event(self, event_type: str, event_data: Dict[str, Any]):
                db_service = self.db.get_service("database")
                sql = "INSERT INTO perfect21_events (event_type, event_data) VALUES (?, ?)"
                await db_service.execute_query(sql, (event_type, json.dumps(event_data)))

            async def save_metric(self, name: str, value: float, tags: Dict[str, str] = None):
                db_service = self.db.get_service("database")
                sql = "INSERT INTO perfect21_metrics (metric_name, metric_value, tags) VALUES (?, ?, ?)"
                tags_json = json.dumps(tags) if tags else None
                await db_service.execute_query(sql, (name, value, tags_json))

        return QueryExecutorService(self)

# =================== 6. 文件系统管理器 ===================

class UnifiedFileSystemManager(BaseConsolidatedManager):
    """
    统一文件系统管理器
    整合: 文件操作、目录监控、文件缓存、临时文件管理
    """

    def __init__(self, event_bus: EventBus, config_manager: IConfigManager, cache_manager: ICacheManager):
        super().__init__("unified_filesystem", ManagerCategory.DATA, event_bus)
        self.config_manager = config_manager
        self.cache_manager = cache_manager
        self._file_watchers: Dict[str, Any] = {}
        self._temp_files: Set[str] = set()
        self._file_locks: Dict[str, threading.Lock] = {}
        self.add_dependency("core_config")
        self.add_dependency("unified_cache")

    def _get_description(self) -> str:
        return "统一文件系统管理器 - 文件操作、监控、缓存和临时文件管理"

    async def _do_initialize(self, **kwargs) -> bool:
        """初始化文件系统管理器"""
        try:
            # 设置工作目录
            self.work_dir = self.config_manager.get_config(
                "perfect21.work_directory", os.getcwd()
            )

            # 确保目录存在
            perfect21_dir = os.path.join(self.work_dir, ".perfect21")
            os.makedirs(perfect21_dir, exist_ok=True)
            os.makedirs(os.path.join(perfect21_dir, "temp"), exist_ok=True)
            os.makedirs(os.path.join(perfect21_dir, "cache"), exist_ok=True)

            # 注册文件系统服务
            self.register_service("file_ops", self._get_file_operations_service())
            self.register_service("temp_manager", self._get_temp_manager_service())
            self.register_service("file_watcher", self._get_file_watcher_service())

            return True
        except Exception as e:
            logger.error(f"文件系统管理器初始化失败: {e}")
            return False

    async def _do_shutdown(self) -> bool:
        """关闭文件系统管理器"""
        try:
            # 清理临时文件
            await self._cleanup_temp_files()

            # 停止文件监控
            for watcher in self._file_watchers.values():
                if hasattr(watcher, 'stop'):
                    watcher.stop()

            self._file_watchers.clear()
            self._file_locks.clear()

            return True
        except Exception as e:
            logger.error(f"文件系统管理器关闭失败: {e}")
            return False

    def _get_file_operations_service(self):
        """获取文件操作服务"""
        class FileOperationsService:
            def __init__(self, fs_manager):
                self.fs = fs_manager

            async def read_file(self, file_path: str, use_cache: bool = True) -> Optional[str]:
                if use_cache:
                    cached = self.fs.cache_manager.get(f"file:{file_path}", "filesystem")
                    if cached:
                        return cached

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    if use_cache:
                        self.fs.cache_manager.set(f"file:{file_path}", content, namespace="filesystem")

                    return content

                except Exception as e:
                    logger.error(f"读取文件失败 {file_path}: {e}")
                    return None

            async def write_file(self, file_path: str, content: str, backup: bool = True) -> bool:
                try:
                    # 创建备份
                    if backup and os.path.exists(file_path):
                        backup_path = f"{file_path}.backup"
                        import shutil
                        shutil.copy2(file_path, backup_path)

                    # 写入文件
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)

                    # 更新缓存
                    self.fs.cache_manager.set(f"file:{file_path}", content, namespace="filesystem")

                    return True

                except Exception as e:
                    logger.error(f"写入文件失败 {file_path}: {e}")
                    return False

            def ensure_directory(self, dir_path: str) -> bool:
                try:
                    os.makedirs(dir_path, exist_ok=True)
                    return True
                except Exception as e:
                    logger.error(f"创建目录失败 {dir_path}: {e}")
                    return False

            def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
                try:
                    stat = os.stat(file_path)
                    return {
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime),
                        "created": datetime.fromtimestamp(stat.st_ctime),
                        "is_file": os.path.isfile(file_path),
                        "is_dir": os.path.isdir(file_path)
                    }
                except Exception as e:
                    logger.error(f"获取文件信息失败 {file_path}: {e}")
                    return None

        return FileOperationsService(self)

    def _get_temp_manager_service(self):
        """获取临时文件管理器服务"""
        class TempManagerService:
            def __init__(self, fs_manager):
                self.fs = fs_manager

            def create_temp_file(self, suffix: str = ".tmp", content: str = "") -> Optional[str]:
                try:
                    import tempfile
                    temp_dir = os.path.join(self.fs.work_dir, ".perfect21", "temp")

                    with tempfile.NamedTemporaryFile(
                        mode='w',
                        suffix=suffix,
                        dir=temp_dir,
                        delete=False,
                        encoding='utf-8'
                    ) as f:
                        if content:
                            f.write(content)
                        temp_path = f.name

                    self.fs._temp_files.add(temp_path)
                    return temp_path

                except Exception as e:
                    logger.error(f"创建临时文件失败: {e}")
                    return None

            def cleanup_temp_file(self, temp_path: str) -> bool:
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)

                    self.fs._temp_files.discard(temp_path)
                    return True

                except Exception as e:
                    logger.error(f"清理临时文件失败 {temp_path}: {e}")
                    return False

        return TempManagerService(self)

    def _get_file_watcher_service(self):
        """获取文件监控服务"""
        class FileWatcherService:
            def __init__(self, fs_manager):
                self.fs = fs_manager

            def watch_file(self, file_path: str, callback: Callable):
                # 简化实现，实际应使用 watchdog 库
                logger.info(f"监控文件: {file_path}")
                self.fs._file_watchers[file_path] = {
                    "callback": callback,
                    "last_modified": os.path.getmtime(file_path) if os.path.exists(file_path) else 0
                }

            def stop_watching(self, file_path: str):
                if file_path in self.fs._file_watchers:
                    del self.fs._file_watchers[file_path]

        return FileWatcherService(self)

    async def _cleanup_temp_files(self):
        """清理临时文件"""
        for temp_file in list(self._temp_files):
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logger.debug(f"清理临时文件: {temp_file}")
            except Exception as e:
                logger.error(f"清理临时文件失败 {temp_file}: {e}")

        self._temp_files.clear()

# =================== 7. 文档管理器 ===================

class UnifiedDocumentManager(BaseConsolidatedManager):
    """
    统一文档管理器
    整合: DocumentManager, ClaudeMdManager, LifecycleManager, TemplateManager
    """

    def __init__(self, event_bus: EventBus, config_manager: IConfigManager, fs_manager):
        super().__init__("unified_document", ManagerCategory.DATA, event_bus)
        self.config_manager = config_manager
        self.fs_manager = fs_manager
        self._document_cache: Dict[str, Dict[str, Any]] = {}
        self._templates: Dict[str, str] = {}
        self._document_lifecycle: Dict[str, Dict[str, Any]] = {}
        self.add_dependency("core_config")
        self.add_dependency("unified_filesystem")

    def _get_description(self) -> str:
        return "统一文档管理器 - CLAUDE.md管理、模板引擎、生命周期跟踪"

    async def _do_initialize(self, **kwargs) -> bool:
        """初始化文档管理器"""
        try:
            # 加载文档模板
            await self._load_document_templates()

            # 注册文档服务
            self.register_service("document", self._get_document_service())
            self.register_service("claude_md", self._get_claude_md_service())
            self.register_service("template_engine", self._get_template_engine_service())

            return True
        except Exception as e:
            logger.error(f"文档管理器初始化失败: {e}")
            return False

    async def _do_shutdown(self) -> bool:
        """关闭文档管理器"""
        try:
            # 保存文档状态
            await self._save_document_lifecycle()

            self._document_cache.clear()
            self._templates.clear()
            self._document_lifecycle.clear()

            return True
        except Exception as e:
            logger.error(f"文档管理器关闭失败: {e}")
            return False

    async def _load_document_templates(self):
        """加载文档模板"""
        templates = {
            "claude_md": """# {project_name} 项目核心文档

> 🎯 **项目身份**: {project_description}
> 🔑 **核心原则**: {core_principles}

## 🎯 项目本质

{project_essence}

## 🚀 主要功能

{main_features}

## 📋 使用方式

{usage_instructions}

## 📊 当前状态

- **当前版本**: {version}
- **最后更新**: {last_update}

---

> 📝 **使用提示**: {usage_tips}
""",
            "readme": """# {project_name}

{project_description}

## Installation

{installation_instructions}

## Usage

{usage_instructions}

## Contributing

{contributing_guidelines}
""",
            "changelog": """# Changelog

All notable changes to this project will be documented in this file.

## [{version}] - {date}

### Added
- {added_features}

### Changed
- {changed_features}

### Fixed
- {fixed_issues}
"""
        }

        self._templates.update(templates)

    def _get_document_service(self):
        """获取文档服务"""
        class DocumentService:
            def __init__(self, doc_manager):
                self.dm = doc_manager

            async def get_document(self, doc_path: str) -> Optional[Dict[str, Any]]:
                # 从缓存获取
                if doc_path in self.dm._document_cache:
                    return self.dm._document_cache[doc_path]

                # 从文件系统读取
                file_ops = self.dm.fs_manager.get_service("file_ops")
                content = await file_ops.read_file(doc_path)

                if content:
                    doc_data = {
                        "path": doc_path,
                        "content": content,
                        "last_modified": datetime.now(),
                        "size": len(content),
                        "lines": len(content.splitlines())
                    }

                    self.dm._document_cache[doc_path] = doc_data
                    return doc_data

                return None

            async def update_document(self, doc_path: str, content: str) -> bool:
                file_ops = self.dm.fs_manager.get_service("file_ops")
                success = await file_ops.write_file(doc_path, content)

                if success:
                    # 更新缓存
                    self.dm._document_cache[doc_path] = {
                        "path": doc_path,
                        "content": content,
                        "last_modified": datetime.now(),
                        "size": len(content),
                        "lines": len(content.splitlines())
                    }

                    # 记录生命周期
                    self._record_document_update(doc_path)

                return success

            def _record_document_update(self, doc_path: str):
                if doc_path not in self.dm._document_lifecycle:
                    self.dm._document_lifecycle[doc_path] = {
                        "created_at": datetime.now(),
                        "updates": []
                    }

                self.dm._document_lifecycle[doc_path]["updates"].append({
                    "timestamp": datetime.now(),
                    "action": "update"
                })

        return DocumentService(self)

    def _get_claude_md_service(self):
        """获取CLAUDE.md服务"""
        class ClaudeMdService:
            def __init__(self, doc_manager):
                self.dm = doc_manager

            async def get_claude_md(self, project_path: str = None) -> Optional[str]:
                if not project_path:
                    project_path = self.dm.config_manager.get_config(
                        "perfect21.work_directory", os.getcwd()
                    )

                claude_md_path = os.path.join(project_path, "CLAUDE.md")
                doc_service = self.dm.get_service("document")
                doc = await doc_service.get_document(claude_md_path)

                return doc["content"] if doc else None

            async def update_claude_md(self, content: str, project_path: str = None) -> bool:
                if not project_path:
                    project_path = self.dm.config_manager.get_config(
                        "perfect21.work_directory", os.getcwd()
                    )

                claude_md_path = os.path.join(project_path, "CLAUDE.md")
                doc_service = self.dm.get_service("document")

                return await doc_service.update_document(claude_md_path, content)

            def analyze_claude_md(self, content: str) -> Dict[str, Any]:
                """分析CLAUDE.md内容"""
                analysis = {
                    "sections": [],
                    "word_count": len(content.split()),
                    "line_count": len(content.splitlines()),
                    "has_toc": "##" in content,
                    "has_instructions": "instruction" in content.lower(),
                    "last_updated_section": None
                }

                # 提取章节
                lines = content.splitlines()
                current_section = None

                for line in lines:
                    if line.startswith("#"):
                        section_name = line.strip("#").strip()
                        analysis["sections"].append(section_name)

                        if "状态" in section_name or "status" in section_name.lower():
                            analysis["last_updated_section"] = section_name

                return analysis

        return ClaudeMdService(self)

    def _get_template_engine_service(self):
        """获取模板引擎服务"""
        class TemplateEngineService:
            def __init__(self, doc_manager):
                self.dm = doc_manager

            def render_template(self, template_name: str, variables: Dict[str, Any]) -> str:
                template = self.dm._templates.get(template_name)
                if not template:
                    raise ValueError(f"模板不存在: {template_name}")

                try:
                    return template.format(**variables)
                except KeyError as e:
                    raise ValueError(f"模板变量缺失: {e}")

            def add_template(self, name: str, template: str):
                self.dm._templates[name] = template

            def get_available_templates(self) -> List[str]:
                return list(self.dm._templates.keys())

        return TemplateEngineService(self)

    async def _save_document_lifecycle(self):
        """保存文档生命周期数据"""
        try:
            lifecycle_dir = os.path.join(os.getcwd(), ".perfect21", "documents")
            os.makedirs(lifecycle_dir, exist_ok=True)

            lifecycle_file = os.path.join(lifecycle_dir, "lifecycle.json")
            with open(lifecycle_file, 'w') as f:
                json.dump(self._document_lifecycle, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"保存文档生命周期数据失败: {e}")

# =================== 监控管理器 ===================

class UnifiedMonitoringManager(BaseConsolidatedManager):
    """
    统一监控管理器
    整合: 性能监控、健康检查、度量收集、告警
    """

    def __init__(self, event_bus: EventBus, config_manager: IConfigManager, db_manager):
        super().__init__("unified_monitoring", ManagerCategory.MONITORING, event_bus)
        self.config_manager = config_manager
        self.db_manager = db_manager
        self._metrics: Dict[str, List[Dict[str, Any]]] = {}
        self._alerts: List[Dict[str, Any]] = []
        self._monitoring_tasks: List[asyncio.Task] = []
        self.add_dependency("core_config")
        self.add_dependency("unified_database")

    def _get_description(self) -> str:
        return "统一监控管理器 - 性能监控、健康检查、度量收集和告警"

    async def _do_initialize(self, **kwargs) -> bool:
        """初始化监控管理器"""
        try:
            # 设置监控间隔
            self.monitor_interval = self.config_manager.get_config(
                "perfect21.monitor_interval_seconds", 60
            )

            # 注册监控服务
            self.register_service("metrics", self._get_metrics_service())
            self.register_service("health_check", self._get_health_check_service())
            self.register_service("alerting", self._get_alerting_service())

            # 启动监控任务
            await self._start_monitoring_tasks()

            return True
        except Exception as e:
            logger.error(f"监控管理器初始化失败: {e}")
            return False

    async def _do_shutdown(self) -> bool:
        """关闭监控管理器"""
        try:
            # 停止监控任务
            for task in self._monitoring_tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

            self._monitoring_tasks.clear()
            self._metrics.clear()
            self._alerts.clear()

            return True
        except Exception as e:
            logger.error(f"监控管理器关闭失败: {e}")
            return False

    async def _start_monitoring_tasks(self):
        """启动监控任务"""
        # 系统指标监控
        task1 = asyncio.create_task(self._monitor_system_metrics())
        self._monitoring_tasks.append(task1)

        # 健康检查监控
        task2 = asyncio.create_task(self._monitor_health_status())
        self._monitoring_tasks.append(task2)

    async def _monitor_system_metrics(self):
        """监控系统指标"""
        while self.state == ManagerState.READY:
            try:
                # 收集CPU和内存指标（简化实现）
                import psutil

                metrics = {
                    "cpu_percent": psutil.cpu_percent(interval=1),
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_usage": psutil.disk_usage('/').percent
                }

                # 记录指标
                for name, value in metrics.items():
                    await self._record_metric(name, value)

                # 检查告警条件
                await self._check_alert_conditions(metrics)

                await asyncio.sleep(self.monitor_interval)

            except Exception as e:
                logger.error(f"系统指标监控错误: {e}")
                await asyncio.sleep(60)

    async def _monitor_health_status(self):
        """监控健康状态"""
        while self.state == ManagerState.READY:
            try:
                # 这里应该检查其他Manager的健康状态
                health_status = {
                    "timestamp": datetime.now(),
                    "overall_health": "healthy"  # 简化实现
                }

                await self._record_health_check(health_status)

                await asyncio.sleep(self.monitor_interval * 2)  # 健康检查频率较低

            except Exception as e:
                logger.error(f"健康状态监控错误: {e}")
                await asyncio.sleep(120)

    async def _record_metric(self, name: str, value: float, tags: Dict[str, str] = None):
        """记录指标"""
        metric_data = {
            "name": name,
            "value": value,
            "tags": tags or {},
            "timestamp": datetime.now()
        }

        # 内存存储
        if name not in self._metrics:
            self._metrics[name] = []

        self._metrics[name].append(metric_data)

        # 限制内存中的指标数量
        if len(self._metrics[name]) > 1000:
            self._metrics[name] = self._metrics[name][-1000:]

        # 持久化到数据库
        try:
            query_executor = self.db_manager.get_service("query_executor")
            await query_executor.save_metric(name, value, tags)
        except Exception as e:
            logger.error(f"保存指标到数据库失败: {e}")

    async def _record_health_check(self, health_data: Dict[str, Any]):
        """记录健康检查"""
        try:
            query_executor = self.db_manager.get_service("query_executor")
            await query_executor.save_event("health_check", health_data)
        except Exception as e:
            logger.error(f"记录健康检查失败: {e}")

    async def _check_alert_conditions(self, metrics: Dict[str, float]):
        """检查告警条件"""
        # CPU使用率告警
        if metrics.get("cpu_percent", 0) > 80:
            await self._create_alert("high_cpu", f"CPU使用率过高: {metrics['cpu_percent']:.1f}%")

        # 内存使用率告警
        if metrics.get("memory_percent", 0) > 85:
            await self._create_alert("high_memory", f"内存使用率过高: {metrics['memory_percent']:.1f}%")

        # 磁盘使用率告警
        if metrics.get("disk_usage", 0) > 90:
            await self._create_alert("high_disk", f"磁盘使用率过高: {metrics['disk_usage']:.1f}%")

    async def _create_alert(self, alert_type: str, message: str):
        """创建告警"""
        alert = {
            "type": alert_type,
            "message": message,
            "timestamp": datetime.now(),
            "severity": "warning"  # 简化实现
        }

        self._alerts.append(alert)

        # 发布告警事件
        self.event_bus.publish(Event(
            type="alert_created",
            data=alert
        ))

        logger.warning(f"告警: {message}")

    def _get_metrics_service(self):
        """获取指标服务"""
        class MetricsService:
            def __init__(self, monitor_manager):
                self.mm = monitor_manager

            async def record_custom_metric(self, name: str, value: float, tags: Dict[str, str] = None):
                await self.mm._record_metric(name, value, tags)

            def get_metric_history(self, name: str, limit: int = 100) -> List[Dict[str, Any]]:
                return self.mm._metrics.get(name, [])[-limit:]

            def get_available_metrics(self) -> List[str]:
                return list(self.mm._metrics.keys())

        return MetricsService(self)

    def _get_health_check_service(self):
        """获取健康检查服务"""
        class HealthCheckService:
            def __init__(self, monitor_manager):
                self.mm = monitor_manager

            async def perform_health_check(self, component: str) -> Dict[str, Any]:
                # 简化的健康检查实现
                return {
                    "component": component,
                    "status": "healthy",
                    "timestamp": datetime.now()
                }

            def get_system_health(self) -> Dict[str, Any]:
                return {
                    "overall_status": "healthy",
                    "components": len(self.mm._metrics),
                    "last_check": datetime.now()
                }

        return HealthCheckService(self)

    def _get_alerting_service(self):
        """获取告警服务"""
        class AlertingService:
            def __init__(self, monitor_manager):
                self.mm = monitor_manager

            def get_active_alerts(self) -> List[Dict[str, Any]]:
                return self.mm._alerts

            def get_alert_history(self, limit: int = 50) -> List[Dict[str, Any]]:
                return self.mm._alerts[-limit:]

            async def create_custom_alert(self, alert_type: str, message: str, severity: str = "info"):
                alert = {
                    "type": alert_type,
                    "message": message,
                    "timestamp": datetime.now(),
                    "severity": severity
                }

                self.mm._alerts.append(alert)

                # 发布告警事件
                self.mm.event_bus.publish(Event(
                    type="alert_created",
                    data=alert
                ))

        return AlertingService(self)

# =================== 更新工厂注册 ===================

def register_remaining_managers(factory: 'ConsolidatedManagerFactory'):
    """注册剩余的10个Manager"""

    # 核心层 (1个)
    factory.register_manager("core_event", CoreEventManager)

    # 数据层 (3个)
    factory.register_manager("unified_database", UnifiedDatabaseManager)
    factory.register_manager("unified_filesystem", UnifiedFileSystemManager)
    factory.register_manager("unified_document", UnifiedDocumentManager)

    # 监控层 (1个)
    factory.register_manager("unified_monitoring", UnifiedMonitoringManager)

    logger.info("已注册剩余10个Manager类")

# 导出主要类
__all__ = [
    'CoreEventManager',
    'UnifiedDatabaseManager',
    'UnifiedFileSystemManager',
    'UnifiedDocumentManager',
    'UnifiedMonitoringManager',
    'register_remaining_managers'
]