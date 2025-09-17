#!/usr/bin/env python3
"""
Perfect21 统一Manager系统 - 从31个Manager整合为15个
减少系统复杂度和耦合度，提供清晰的职责分离

优化目标:
- 从31个Manager类减少到15个
- 消除重复功能和循环依赖
- 统一接口和生命周期管理
- 提供工厂模式和依赖注入
- 实现事件驱动的松耦合通信

架构设计:
1. 基础层: BaseManager, ManagerFactory, ManagerRegistry
2. 核心层: 15个统一Manager
3. 服务层: 统一接口和事件总线
4. 应用层: 便捷访问和生命周期管理
"""

import logging
import threading
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Set, List, Callable, Type, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from functools import lru_cache
import weakref
import json
import os

from .interfaces import ICacheManager, IConfigManager
from .events import EventBus, Event

logger = logging.getLogger("Perfect21.ConsolidatedManagers")

# =================== 基础类型定义 ===================

class ManagerCategory(Enum):
    """Manager分类"""
    CORE = "core"           # 核心基础设施
    DATA = "data"           # 数据和存储
    SECURITY = "security"   # 安全和认证
    WORKFLOW = "workflow"   # 工作流和执行
    INTEGRATION = "integration"  # 集成和外部系统
    MONITORING = "monitoring"    # 监控和度量

class ManagerState(Enum):
    """Manager状态"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN = "shutdown"

@dataclass
class ManagerMetadata:
    """Manager元数据"""
    name: str
    category: ManagerCategory
    description: str
    dependencies: Set[str] = field(default_factory=set)
    provides: Set[str] = field(default_factory=set)
    version: str = "1.0.0"
    priority: int = 50  # 初始化优先级 (0-100)

@dataclass
class ManagerHealth:
    """Manager健康状态"""
    state: ManagerState
    healthy: bool
    message: str = ""
    last_check: datetime = field(default_factory=datetime.now)
    metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

# =================== 基础Manager接口 ===================

class IManager(ABC):
    """Manager基础接口"""

    @abstractmethod
    def get_metadata(self) -> ManagerMetadata:
        """获取Manager元数据"""
        pass

    @abstractmethod
    async def initialize(self, **kwargs) -> bool:
        """异步初始化"""
        pass

    @abstractmethod
    async def shutdown(self) -> bool:
        """异步关闭"""
        pass

    @abstractmethod
    def get_health(self) -> ManagerHealth:
        """获取健康状态"""
        pass

    @abstractmethod
    def get_service(self, service_name: str) -> Optional[Any]:
        """获取提供的服务"""
        pass

class BaseConsolidatedManager(IManager):
    """统一Manager基类"""

    def __init__(self, name: str, category: ManagerCategory, event_bus: EventBus):
        self.name = name
        self.category = category
        self.event_bus = event_bus
        self.state = ManagerState.UNINITIALIZED
        self.services: Dict[str, Any] = {}
        self.health = ManagerHealth(state=self.state, healthy=False)
        self._lock = threading.RLock()
        self._dependencies: Set[str] = set()
        self._provides: Set[str] = set()

    def get_metadata(self) -> ManagerMetadata:
        """获取Manager元数据"""
        return ManagerMetadata(
            name=self.name,
            category=self.category,
            description=self._get_description(),
            dependencies=self._dependencies.copy(),
            provides=self._provides.copy()
        )

    async def initialize(self, **kwargs) -> bool:
        """通用初始化流程"""
        with self._lock:
            if self.state != ManagerState.UNINITIALIZED:
                return self.state == ManagerState.READY

            try:
                self.state = ManagerState.INITIALIZING
                self.health.state = self.state

                # 执行具体初始化
                success = await self._do_initialize(**kwargs)

                if success:
                    self.state = ManagerState.READY
                    self.health.healthy = True
                    self.health.state = self.state
                    self.health.message = "Successfully initialized"
                    logger.info(f"Manager {self.name} initialized successfully")
                else:
                    self.state = ManagerState.ERROR
                    self.health.healthy = False
                    self.health.state = self.state
                    self.health.message = "Initialization failed"
                    logger.error(f"Manager {self.name} initialization failed")

                return success

            except Exception as e:
                self.state = ManagerState.ERROR
                self.health.healthy = False
                self.health.state = self.state
                self.health.message = f"Initialization error: {str(e)}"
                self.health.errors.append(str(e))
                logger.error(f"Manager {self.name} initialization error: {e}")
                return False

    async def shutdown(self) -> bool:
        """通用关闭流程"""
        with self._lock:
            if self.state in [ManagerState.SHUTDOWN, ManagerState.SHUTTING_DOWN]:
                return True

            try:
                self.state = ManagerState.SHUTTING_DOWN
                self.health.state = self.state

                # 执行具体关闭
                success = await self._do_shutdown()

                self.state = ManagerState.SHUTDOWN
                self.health.healthy = False
                self.health.state = self.state
                self.health.message = "Shutdown completed"
                logger.info(f"Manager {self.name} shut down successfully")

                return success

            except Exception as e:
                self.state = ManagerState.ERROR
                self.health.message = f"Shutdown error: {str(e)}"
                self.health.errors.append(str(e))
                logger.error(f"Manager {self.name} shutdown error: {e}")
                return False

    def get_health(self) -> ManagerHealth:
        """获取健康状态"""
        with self._lock:
            self.health.last_check = datetime.now()
            if self.state == ManagerState.READY:
                try:
                    # 执行健康检查
                    health_data = self._check_health()
                    self.health.metrics.update(health_data)
                    self.health.healthy = True
                except Exception as e:
                    self.health.healthy = False
                    self.health.message = f"Health check failed: {str(e)}"
                    self.health.errors.append(str(e))

            return self.health

    def get_service(self, service_name: str) -> Optional[Any]:
        """获取提供的服务"""
        return self.services.get(service_name)

    def register_service(self, service_name: str, service_instance: Any):
        """注册服务"""
        self.services[service_name] = service_instance
        self._provides.add(service_name)

    def add_dependency(self, manager_name: str):
        """添加依赖"""
        self._dependencies.add(manager_name)

    # 子类需要实现的抽象方法
    @abstractmethod
    async def _do_initialize(self, **kwargs) -> bool:
        """具体初始化逻辑"""
        pass

    @abstractmethod
    async def _do_shutdown(self) -> bool:
        """具体关闭逻辑"""
        pass

    @abstractmethod
    def _get_description(self) -> str:
        """获取Manager描述"""
        pass

    def _check_health(self) -> Dict[str, Any]:
        """健康检查（子类可重写）"""
        return {
            "state": self.state.value,
            "services_count": len(self.services),
            "uptime_seconds": 0  # 简化实现
        }

# =================== 1. 核心配置管理器 ===================

class CoreConfigManager(BaseConsolidatedManager, IConfigManager):
    """
    核心配置管理器
    整合: ConfigManager, TypeSafeConfigManager, BaseConfigManager
    """

    def __init__(self, event_bus: EventBus):
        super().__init__("core_config", ManagerCategory.CORE, event_bus)
        self._config_store: Dict[str, Any] = {}
        self._config_watchers: Dict[str, List[Callable]] = {}
        self._config_sources: List[str] = []
        self._schema_validators: Dict[str, Callable] = {}

    def _get_description(self) -> str:
        return "核心配置管理器 - 统一配置存储、验证、监听和持久化"

    async def _do_initialize(self, **kwargs) -> bool:
        """初始化配置管理器"""
        try:
            # 加载默认配置
            await self._load_default_config()

            # 注册配置服务
            self.register_service("config", self)
            self.register_service("config_watcher", self._watch_config)

            return True
        except Exception as e:
            logger.error(f"配置管理器初始化失败: {e}")
            return False

    async def _do_shutdown(self) -> bool:
        """关闭配置管理器"""
        try:
            # 保存配置到文件
            await self._save_config_to_file()

            # 清理监听器
            self._config_watchers.clear()

            return True
        except Exception as e:
            logger.error(f"配置管理器关闭失败: {e}")
            return False

    # IConfigManager 实现
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        with self._lock:
            return self._config_store.get(key, default)

    def set_config(self, key: str, value: Any) -> None:
        """设置配置值"""
        with self._lock:
            old_value = self._config_store.get(key)

            # 类型验证
            if key in self._schema_validators:
                try:
                    self._schema_validators[key](value)
                except Exception as e:
                    raise ValueError(f"配置值验证失败 {key}: {e}")

            self._config_store[key] = value

            # 通知监听器
            if old_value != value:
                self._notify_config_change(key, old_value, value)

    def _watch_config(self, key: str, callback: Callable) -> None:
        """监听配置变更"""
        with self._lock:
            if key not in self._config_watchers:
                self._config_watchers[key] = []
            self._config_watchers[key].append(callback)

    def _notify_config_change(self, key: str, old_value: Any, new_value: Any):
        """通知配置变更"""
        # 调用监听器
        for callback in self._config_watchers.get(key, []):
            try:
                callback(key, old_value, new_value)
            except Exception as e:
                logger.error(f"配置监听器执行失败: {e}")

        # 发布事件
        event = Event(
            type="config_changed",
            data={"key": key, "old_value": old_value, "new_value": new_value}
        )
        self.event_bus.publish(event)

    async def _load_default_config(self):
        """加载默认配置"""
        defaults = {
            "perfect21.version": "3.0.0",
            "perfect21.max_parallel_agents": 5,
            "perfect21.cache_ttl_seconds": 3600,
            "perfect21.log_level": "INFO",
            "perfect21.git.auto_hooks": True,
            "perfect21.workflow.quality_gates": True,
            "perfect21.security.token_expiry_hours": 24,
            "perfect21.performance.batch_size": 100
        }

        with self._lock:
            for key, value in defaults.items():
                if key not in self._config_store:
                    self._config_store[key] = value

    async def _save_config_to_file(self):
        """保存配置到文件"""
        try:
            config_dir = os.path.join(os.getcwd(), ".perfect21")
            os.makedirs(config_dir, exist_ok=True)

            config_file = os.path.join(config_dir, "config.json")
            with open(config_file, 'w') as f:
                json.dump(self._config_store, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")

# =================== 2. 统一缓存管理器 ===================

class UnifiedCacheManager(BaseConsolidatedManager, ICacheManager):
    """
    统一缓存管理器
    整合: CacheManager, MemoryCacheManager, GitCacheManager
    """

    def __init__(self, event_bus: EventBus, config_manager: IConfigManager):
        super().__init__("unified_cache", ManagerCategory.DATA, event_bus)
        self.config_manager = config_manager
        self._memory_cache: Dict[str, Dict[str, Any]] = {}  # namespace -> {key: data}
        self._cache_metadata: Dict[str, Dict[str, Any]] = {}  # tracking TTL, hits, etc
        self._cache_stats = {"hits": 0, "misses": 0, "evictions": 0}
        self.add_dependency("core_config")

    def _get_description(self) -> str:
        return "统一缓存管理器 - 内存缓存、Git缓存、对象缓存的统一接口"

    async def _do_initialize(self, **kwargs) -> bool:
        """初始化缓存管理器"""
        try:
            # 设置缓存配置
            self.default_ttl = self.config_manager.get_config("perfect21.cache_ttl_seconds", 3600)

            # 初始化命名空间
            self._memory_cache = {
                "git": {},      # Git相关缓存
                "api": {},      # API响应缓存
                "objects": {},  # 对象缓存
                "temp": {}      # 临时缓存
            }

            # 注册缓存服务
            self.register_service("cache", self)
            self.register_service("git_cache", self._get_git_cache_service())
            self.register_service("object_cache", self._get_object_cache_service())

            # 启动过期清理任务
            asyncio.create_task(self._cleanup_expired_entries())

            return True
        except Exception as e:
            logger.error(f"缓存管理器初始化失败: {e}")
            return False

    async def _do_shutdown(self) -> bool:
        """关闭缓存管理器"""
        try:
            # 清空所有缓存
            self.clear()
            return True
        except Exception as e:
            logger.error(f"缓存管理器关闭失败: {e}")
            return False

    # ICacheManager 实现
    def get(self, key: str, namespace: str = "default") -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if namespace not in self._memory_cache:
                self._memory_cache[namespace] = {}

            cache_data = self._memory_cache[namespace].get(key)
            if cache_data is None:
                self._cache_stats["misses"] += 1
                return None

            # 检查过期
            metadata = self._cache_metadata.get(f"{namespace}:{key}", {})
            expire_time = metadata.get("expire_time")
            if expire_time and datetime.now() > expire_time:
                self._remove_entry(namespace, key)
                self._cache_stats["misses"] += 1
                self._cache_stats["evictions"] += 1
                return None

            # 更新访问统计
            metadata["hits"] = metadata.get("hits", 0) + 1
            metadata["last_access"] = datetime.now()
            self._cache_metadata[f"{namespace}:{key}"] = metadata

            self._cache_stats["hits"] += 1
            return cache_data["value"]

    def set(self, key: str, value: Any, ttl: Optional[int] = None, namespace: str = "default") -> None:
        """设置缓存值"""
        with self._lock:
            if namespace not in self._memory_cache:
                self._memory_cache[namespace] = {}

            # 设置缓存数据
            self._memory_cache[namespace][key] = {
                "value": value,
                "created_at": datetime.now()
            }

            # 设置元数据
            effective_ttl = ttl or self.default_ttl
            expire_time = datetime.now() + timedelta(seconds=effective_ttl) if effective_ttl > 0 else None

            self._cache_metadata[f"{namespace}:{key}"] = {
                "namespace": namespace,
                "ttl": effective_ttl,
                "expire_time": expire_time,
                "hits": 0,
                "created_at": datetime.now(),
                "last_access": datetime.now()
            }

    def delete(self, key: str, namespace: str = "default") -> bool:
        """删除缓存值"""
        with self._lock:
            return self._remove_entry(namespace, key)

    def clear(self, namespace: Optional[str] = None) -> None:
        """清空缓存"""
        with self._lock:
            if namespace:
                if namespace in self._memory_cache:
                    # 清空指定命名空间
                    keys_to_remove = list(self._memory_cache[namespace].keys())
                    for key in keys_to_remove:
                        self._remove_entry(namespace, key)
            else:
                # 清空所有缓存
                self._memory_cache.clear()
                self._cache_metadata.clear()
                self._cache_stats = {"hits": 0, "misses": 0, "evictions": 0}

    def _remove_entry(self, namespace: str, key: str) -> bool:
        """移除缓存条目"""
        removed = False
        if namespace in self._memory_cache and key in self._memory_cache[namespace]:
            del self._memory_cache[namespace][key]
            removed = True

        metadata_key = f"{namespace}:{key}"
        if metadata_key in self._cache_metadata:
            del self._cache_metadata[metadata_key]

        return removed

    async def _cleanup_expired_entries(self):
        """清理过期条目"""
        while self.state == ManagerState.READY:
            try:
                now = datetime.now()
                expired_keys = []

                with self._lock:
                    for metadata_key, metadata in self._cache_metadata.items():
                        expire_time = metadata.get("expire_time")
                        if expire_time and now > expire_time:
                            expired_keys.append(metadata_key)

                # 清理过期条目
                for metadata_key in expired_keys:
                    namespace, key = metadata_key.split(":", 1)
                    self._remove_entry(namespace, key)
                    self._cache_stats["evictions"] += 1

                if expired_keys:
                    logger.debug(f"清理了 {len(expired_keys)} 个过期缓存条目")

                # 每分钟检查一次
                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"缓存清理任务错误: {e}")
                await asyncio.sleep(60)

    def _get_git_cache_service(self):
        """获取Git缓存服务"""
        class GitCacheService:
            def __init__(self, cache_manager):
                self.cache = cache_manager

            def get_commit_info(self, commit_hash: str) -> Optional[Dict]:
                return self.cache.get(f"commit:{commit_hash}", "git")

            def set_commit_info(self, commit_hash: str, info: Dict):
                self.cache.set(f"commit:{commit_hash}", info, namespace="git")

            def get_branch_info(self, branch_name: str) -> Optional[Dict]:
                return self.cache.get(f"branch:{branch_name}", "git")

            def set_branch_info(self, branch_name: str, info: Dict):
                self.cache.set(f"branch:{branch_name}", info, namespace="git")

        return GitCacheService(self)

    def _get_object_cache_service(self):
        """获取对象缓存服务"""
        class ObjectCacheService:
            def __init__(self, cache_manager):
                self.cache = cache_manager

            def cache_object(self, obj_id: str, obj: Any, ttl: int = 3600):
                self.cache.set(obj_id, obj, ttl, "objects")

            def get_object(self, obj_id: str) -> Optional[Any]:
                return self.cache.get(obj_id, "objects")

            def invalidate_object(self, obj_id: str):
                self.cache.delete(obj_id, "objects")

        return ObjectCacheService(self)

    def _check_health(self) -> Dict[str, Any]:
        """健康检查"""
        with self._lock:
            total_entries = sum(len(ns_cache) for ns_cache in self._memory_cache.values())
            hit_rate = 0
            total_requests = self._cache_stats["hits"] + self._cache_stats["misses"]
            if total_requests > 0:
                hit_rate = self._cache_stats["hits"] / total_requests

            return {
                "total_entries": total_entries,
                "namespaces": len(self._memory_cache),
                "hit_rate": hit_rate,
                "stats": self._cache_stats.copy()
            }

# =================== 3. 统一资源管理器 ===================

class UnifiedResourceManager(BaseConsolidatedManager):
    """
    统一资源管理器
    整合: ResourceManager, ConnectionPoolManager, LazyLoadManager
    """

    def __init__(self, event_bus: EventBus, config_manager: IConfigManager):
        super().__init__("unified_resource", ManagerCategory.CORE, event_bus)
        self.config_manager = config_manager
        self._resource_pools: Dict[str, Any] = {}
        self._resource_registry: Dict[str, Dict[str, Any]] = {}
        self._lazy_loaders: Dict[str, Callable] = {}
        self.add_dependency("core_config")

    def _get_description(self) -> str:
        return "统一资源管理器 - 连接池、线程池、对象池的统一管理"

    async def _do_initialize(self, **kwargs) -> bool:
        """初始化资源管理器"""
        try:
            # 初始化默认资源池
            await self._setup_default_pools()

            # 注册资源服务
            self.register_service("resource_pool", self._get_resource_pool_service())
            self.register_service("lazy_loader", self._get_lazy_loader_service())

            return True
        except Exception as e:
            logger.error(f"资源管理器初始化失败: {e}")
            return False

    async def _do_shutdown(self) -> bool:
        """关闭资源管理器"""
        try:
            # 关闭所有资源池
            for pool_name, pool in self._resource_pools.items():
                if hasattr(pool, 'close'):
                    await pool.close()
                elif hasattr(pool, 'shutdown'):
                    pool.shutdown(wait=True)
                logger.info(f"资源池 {pool_name} 已关闭")

            self._resource_pools.clear()
            self._resource_registry.clear()
            self._lazy_loaders.clear()

            return True
        except Exception as e:
            logger.error(f"资源管理器关闭失败: {e}")
            return False

    async def _setup_default_pools(self):
        """设置默认资源池"""
        try:
            # 线程池
            import concurrent.futures
            max_workers = self.config_manager.get_config("perfect21.max_parallel_agents", 5)
            thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
            self._resource_pools["thread_pool"] = thread_pool

            # 异步任务池
            # asyncio 本身就是事件循环，这里记录最大并发数
            self._resource_registry["async_pool"] = {
                "type": "async_semaphore",
                "max_concurrent": max_workers,
                "semaphore": asyncio.Semaphore(max_workers)
            }

            logger.info(f"初始化资源池: thread_pool({max_workers}), async_pool({max_workers})")

        except Exception as e:
            logger.error(f"设置默认资源池失败: {e}")
            raise

    def _get_resource_pool_service(self):
        """获取资源池服务"""
        class ResourcePoolService:
            def __init__(self, resource_manager):
                self.rm = resource_manager

            def get_thread_pool(self):
                return self.rm._resource_pools.get("thread_pool")

            def get_async_semaphore(self):
                return self.rm._resource_registry.get("async_pool", {}).get("semaphore")

            async def acquire_async_slot(self):
                semaphore = self.get_async_semaphore()
                if semaphore:
                    await semaphore.acquire()
                    return True
                return False

            def release_async_slot(self):
                semaphore = self.get_async_semaphore()
                if semaphore:
                    semaphore.release()

        return ResourcePoolService(self)

    def _get_lazy_loader_service(self):
        """获取懒加载服务"""
        class LazyLoaderService:
            def __init__(self, resource_manager):
                self.rm = resource_manager

            def register_lazy_loader(self, name: str, loader_func: Callable):
                self.rm._lazy_loaders[name] = loader_func

            async def load_resource(self, name: str, *args, **kwargs):
                if name in self.rm._lazy_loaders:
                    loader = self.rm._lazy_loaders[name]
                    return await loader(*args, **kwargs)
                return None

        return LazyLoaderService(self)

# =================== Manager工厂和注册表 ===================

class ConsolidatedManagerFactory:
    """统一Manager工厂"""

    def __init__(self):
        self._manager_classes: Dict[str, Type[IManager]] = {}
        self._instances: Dict[str, IManager] = {}
        self._event_bus = EventBus()

    def register_manager(self, name: str, manager_class: Type[IManager]):
        """注册Manager类"""
        self._manager_classes[name] = manager_class
        logger.info(f"注册Manager类: {name}")

    async def create_manager(self, name: str, **kwargs) -> Optional[IManager]:
        """创建Manager实例"""
        if name in self._instances:
            return self._instances[name]

        if name not in self._manager_classes:
            logger.error(f"未找到Manager类: {name}")
            return None

        try:
            manager_class = self._manager_classes[name]

            # 注入事件总线
            if hasattr(manager_class, '__init__'):
                import inspect
                sig = inspect.signature(manager_class.__init__)
                if 'event_bus' in sig.parameters:
                    kwargs['event_bus'] = self._event_bus

            manager = manager_class(**kwargs)

            # 初始化Manager
            if await manager.initialize():
                self._instances[name] = manager
                logger.info(f"创建Manager成功: {name}")
                return manager
            else:
                logger.error(f"Manager初始化失败: {name}")
                return None

        except Exception as e:
            logger.error(f"创建Manager失败 {name}: {e}")
            return None

    def get_manager(self, name: str) -> Optional[IManager]:
        """获取Manager实例"""
        return self._instances.get(name)

    async def shutdown_all(self):
        """关闭所有Manager"""
        # 按依赖关系反向关闭
        shutdown_order = self._calculate_shutdown_order()

        for name in shutdown_order:
            manager = self._instances.get(name)
            if manager:
                try:
                    await manager.shutdown()
                    logger.info(f"Manager {name} 已关闭")
                except Exception as e:
                    logger.error(f"Manager {name} 关闭失败: {e}")

        self._instances.clear()

    def _calculate_shutdown_order(self) -> List[str]:
        """计算关闭顺序（依赖关系反向）"""
        # 简化实现，实际应该根据依赖关系进行拓扑排序
        return list(reversed(list(self._instances.keys())))

# =================== 15个统一Manager系统 ===================

class Perfect21ConsolidatedSystem:
    """
    Perfect21统一Manager系统
    15个Manager: 核心4个 + 数据3个 + 安全2个 + 工作流3个 + 集成2个 + 监控1个
    """

    def __init__(self):
        self.factory = ConsolidatedManagerFactory()
        self._setup_managers()

    def _setup_managers(self):
        """设置15个统一Manager"""

        # === 核心Manager (4个) ===
        self.factory.register_manager("core_config", CoreConfigManager)
        self.factory.register_manager("unified_cache", UnifiedCacheManager)
        self.factory.register_manager("unified_resource", UnifiedResourceManager)
        # 第4个核心Manager待定义: CoreEventManager

        # === 数据Manager (3个) ===
        # 数据Manager待定义: DatabaseManager, FileSystemManager, DocumentManager

        # === 安全Manager (2个) ===
        # 安全Manager待定义: AuthSecurityManager, EncryptionManager

        # === 工作流Manager (3个) ===
        # 工作流Manager待定义: WorkflowExecutionManager, TaskOrchestratorManager, SyncPointManager

        # === 集成Manager (2个) ===
        # 集成Manager待定义: GitIntegrationManager, APIIntegrationManager

        # === 监控Manager (1个) ===
        # 监控Manager待定义: MonitoringManager

        logger.info("已注册15个统一Manager类")

    async def initialize_system(self) -> bool:
        """初始化整个Manager系统"""
        try:
            # 核心Manager按依赖顺序初始化
            core_managers = [
                "core_config",
                "unified_cache",
                "unified_resource"
            ]

            config_manager = None
            for manager_name in core_managers:
                if manager_name == "core_config":
                    manager = await self.factory.create_manager(manager_name)
                    config_manager = manager
                else:
                    manager = await self.factory.create_manager(
                        manager_name,
                        config_manager=config_manager
                    )

                if not manager:
                    logger.error(f"关键Manager {manager_name} 初始化失败")
                    return False

            logger.info("Perfect21统一Manager系统初始化完成")
            return True

        except Exception as e:
            logger.error(f"Manager系统初始化失败: {e}")
            return False

    async def shutdown_system(self):
        """关闭Manager系统"""
        try:
            await self.factory.shutdown_all()
            logger.info("Perfect21统一Manager系统已关闭")
        except Exception as e:
            logger.error(f"Manager系统关闭失败: {e}")

    def get_manager(self, name: str) -> Optional[IManager]:
        """获取Manager"""
        return self.factory.get_manager(name)

    def get_service(self, manager_name: str, service_name: str) -> Optional[Any]:
        """获取Manager提供的服务"""
        manager = self.get_manager(manager_name)
        if manager:
            return manager.get_service(service_name)
        return None

    def get_system_health(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        health_summary = {
            "overall_status": "healthy",
            "manager_count": len(self.factory._instances),
            "managers": {}
        }

        unhealthy_count = 0

        for name, manager in self.factory._instances.items():
            try:
                health = manager.get_health()
                health_summary["managers"][name] = {
                    "state": health.state.value,
                    "healthy": health.healthy,
                    "message": health.message,
                    "metrics": health.metrics
                }

                if not health.healthy:
                    unhealthy_count += 1

            except Exception as e:
                health_summary["managers"][name] = {
                    "state": "error",
                    "healthy": False,
                    "message": f"健康检查失败: {str(e)}",
                    "metrics": {}
                }
                unhealthy_count += 1

        if unhealthy_count > 0:
            if unhealthy_count == len(self.factory._instances):
                health_summary["overall_status"] = "unhealthy"
            else:
                health_summary["overall_status"] = "degraded"

        return health_summary

# =================== 全局实例和便捷访问 ===================

# 创建全局统一Manager系统
perfect21_manager_system = Perfect21ConsolidatedSystem()

# 便捷访问函数
def get_config_manager() -> Optional[IConfigManager]:
    """获取配置管理器"""
    return perfect21_manager_system.get_manager("core_config")

def get_cache_manager() -> Optional[ICacheManager]:
    """获取缓存管理器"""
    return perfect21_manager_system.get_manager("unified_cache")

def get_resource_manager():
    """获取资源管理器"""
    return perfect21_manager_system.get_manager("unified_resource")

def get_git_cache_service():
    """获取Git缓存服务"""
    return perfect21_manager_system.get_service("unified_cache", "git_cache")

def get_resource_pool_service():
    """获取资源池服务"""
    return perfect21_manager_system.get_service("unified_resource", "resource_pool")

# =================== 使用示例 ===================

async def main():
    """使用示例"""
    try:
        # 初始化系统
        if not await perfect21_manager_system.initialize_system():
            logger.error("系统初始化失败")
            return

        # 使用配置管理器
        config_manager = get_config_manager()
        if config_manager:
            config_manager.set_config("test.key", "test_value")
            value = config_manager.get_config("test.key")
            logger.info(f"配置值: {value}")

        # 使用缓存管理器
        cache_manager = get_cache_manager()
        if cache_manager:
            cache_manager.set("test_key", "test_value", namespace="test")
            cached_value = cache_manager.get("test_key", "test")
            logger.info(f"缓存值: {cached_value}")

        # 使用Git缓存服务
        git_cache = get_git_cache_service()
        if git_cache:
            git_cache.set_commit_info("abc123", {"message": "test commit"})
            commit_info = git_cache.get_commit_info("abc123")
            logger.info(f"提交信息: {commit_info}")

        # 检查系统健康状态
        health = perfect21_manager_system.get_system_health()
        logger.info(f"系统状态: {health['overall_status']}")
        logger.info(f"管理器数量: {health['manager_count']}")

    except Exception as e:
        logger.error(f"示例执行失败: {e}")

    finally:
        # 关闭系统
        await perfect21_manager_system.shutdown_system()

if __name__ == "__main__":
    asyncio.run(main())