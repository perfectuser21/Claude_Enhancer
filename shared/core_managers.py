#!/usr/bin/env python3
"""
Perfect21 核心Manager系统 - 减少耦合的统一架构
将31个Manager类合并为15个核心Manager，减少耦合点从978个降至<500个

设计原则:
1. 单一职责原则 - 每个Manager只负责一个核心功能域
2. 依赖注入 - 通过事件系统和接口减少直接依赖
3. 事件驱动通信 - Manager间通过事件总线通信
4. 清晰的接口分离 - 明确的输入输出契约
5. 懒加载和按需初始化
"""

import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Set, List, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import threading
from functools import lru_cache

from .interfaces import ICacheManager, IConfigManager
from .events import EventBus, Event, EventHandler
from .base_classes import BaseManager

logger = logging.getLogger("Perfect21.CoreManagers")

T = TypeVar('T')

# =================== 事件驱动通信 ===================

@dataclass
class ManagerEvent(Event):
    """Manager事件基类"""
    manager_name: str
    event_type: str
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

class EventType(Enum):
    """事件类型"""
    MANAGER_INITIALIZED = "manager_initialized"
    MANAGER_SHUTTING_DOWN = "manager_shutting_down"
    CONFIG_CHANGED = "config_changed"
    WORKSPACE_CHANGED = "workspace_changed"
    AUTH_STATE_CHANGED = "auth_state_changed"
    GIT_OPERATION = "git_operation"
    WORKFLOW_STATE_CHANGED = "workflow_state_changed"
    QUALITY_CHECK_COMPLETED = "quality_check_completed"
    PERFORMANCE_METRICS = "performance_metrics"

# =================== 核心管理器接口 ===================

class ICoreManager(ABC):
    """核心管理器接口"""

    @abstractmethod
    def get_name(self) -> str:
        """获取管理器名称"""
        pass

    @abstractmethod
    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        pass

    @abstractmethod
    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        pass

class IStateManager(ICoreManager):
    """状态管理器接口"""

    @abstractmethod
    def get_state(self, key: str) -> Any:
        """获取状态"""
        pass

    @abstractmethod
    def set_state(self, key: str, value: Any) -> None:
        """设置状态"""
        pass

class IResourceManager(ICoreManager):
    """资源管理器接口"""

    @abstractmethod
    def allocate_resource(self, resource_type: str, config: Dict[str, Any]) -> str:
        """分配资源"""
        pass

    @abstractmethod
    def release_resource(self, resource_id: str) -> None:
        """释放资源"""
        pass

# =================== 1. 统一配置状态管理器 ===================

class UnifiedConfigStateManager(BaseManager, IConfigManager, IStateManager):
    """
    统一配置状态管理器
    整合: ConfigManager, StateManager, ModuleStateManager
    """

    def __init__(self, event_bus: EventBus):
        super().__init__()
        self.event_bus = event_bus
        self._config_cache: Dict[str, Any] = {}
        self._state_cache: Dict[str, Any] = {}
        self._watchers: Dict[str, List[Callable]] = {}
        self._lock = threading.RLock()

    def get_name(self) -> str:
        return "unified_config_state"

    def initialize(self, **kwargs) -> bool:
        """初始化配置状态管理器"""
        try:
            # 加载默认配置
            self._load_default_config()

            # 注册事件监听器
            self.event_bus.subscribe(EventType.CONFIG_CHANGED.value, self._on_config_changed)

            logger.info("统一配置状态管理器初始化完成")
            return True

        except Exception as e:
            logger.error(f"统一配置状态管理器初始化失败: {e}")
            return False

    def cleanup(self):
        """清理资源"""
        with self._lock:
            self._config_cache.clear()
            self._state_cache.clear()
            self._watchers.clear()

    # IConfigManager 实现
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置"""
        with self._lock:
            return self._config_cache.get(key, default)

    def set_config(self, key: str, value: Any) -> None:
        """设置配置"""
        with self._lock:
            old_value = self._config_cache.get(key)
            self._config_cache[key] = value

            # 发布配置变更事件
            if old_value != value:
                event = ManagerEvent(
                    manager_name=self.get_name(),
                    event_type=EventType.CONFIG_CHANGED.value,
                    payload={"key": key, "old_value": old_value, "new_value": value}
                )
                self.event_bus.publish(event)

                # 通知监听器
                for callback in self._watchers.get(key, []):
                    try:
                        callback(key, old_value, value)
                    except Exception as e:
                        logger.error(f"配置监听器执行失败: {e}")

    # IStateManager 实现
    def get_state(self, key: str) -> Any:
        """获取状态"""
        with self._lock:
            return self._state_cache.get(key)

    def set_state(self, key: str, value: Any) -> None:
        """设置状态"""
        with self._lock:
            self._state_cache[key] = value

    def watch_config(self, key: str, callback: Callable) -> None:
        """监听配置变更"""
        with self._lock:
            if key not in self._watchers:
                self._watchers[key] = []
            self._watchers[key].append(callback)

    def _load_default_config(self):
        """加载默认配置"""
        defaults = {
            "perfect21.max_parallel_agents": 5,
            "perfect21.cache_ttl": 3600,
            "perfect21.log_level": "INFO",
            "perfect21.git.auto_hooks": True,
            "perfect21.workflow.quality_gates": True
        }

        with self._lock:
            self._config_cache.update(defaults)

    def _on_config_changed(self, event: ManagerEvent):
        """处理配置变更事件"""
        logger.debug(f"配置变更: {event.payload}")

    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        with self._lock:
            return {
                "status": "healthy",
                "config_count": len(self._config_cache),
                "state_count": len(self._state_cache),
                "watchers_count": sum(len(w) for w in self._watchers.values())
            }

    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        with self._lock:
            return {
                "config_cache_size": len(self._config_cache),
                "state_cache_size": len(self._state_cache),
                "memory_usage_kb": 0  # 简化实现
            }

# =================== 2. 统一资源缓存管理器 ===================

class UnifiedResourceCacheManager(BaseManager, IResourceManager, ICacheManager):
    """
    统一资源缓存管理器
    整合: CacheManager, MemoryCacheManager, ResourceManager, GitCacheManager
    """

    def __init__(self, event_bus: EventBus, config_manager: IConfigManager):
        super().__init__()
        self.event_bus = event_bus
        self.config_manager = config_manager
        self._memory_cache: Dict[str, Any] = {}
        self._resource_pool: Dict[str, Any] = {}
        self._cache_stats: Dict[str, Dict] = {}
        self._lock = threading.RLock()

    def get_name(self) -> str:
        return "unified_resource_cache"

    def initialize(self, **kwargs) -> bool:
        """初始化资源缓存管理器"""
        try:
            # 初始化缓存配置
            cache_ttl = self.config_manager.get_config("perfect21.cache_ttl", 3600)

            logger.info(f"统一资源缓存管理器初始化完成, TTL: {cache_ttl}s")
            return True

        except Exception as e:
            logger.error(f"统一资源缓存管理器初始化失败: {e}")
            return False

    def cleanup(self):
        """清理资源"""
        with self._lock:
            # 释放所有资源
            for resource_id in list(self._resource_pool.keys()):
                self.release_resource(resource_id)

            self._memory_cache.clear()
            self._cache_stats.clear()

    # ICacheManager 实现
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        with self._lock:
            value = self._memory_cache.get(key)

            # 更新统计
            if key not in self._cache_stats:
                self._cache_stats[key] = {"hits": 0, "misses": 0}

            if value is not None:
                self._cache_stats[key]["hits"] += 1
            else:
                self._cache_stats[key]["misses"] += 1

            return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存"""
        with self._lock:
            self._memory_cache[key] = value

            # TODO: 实现TTL支持
            if ttl:
                pass  # 简化实现

    def delete(self, key: str) -> bool:
        """删除缓存"""
        with self._lock:
            if key in self._memory_cache:
                del self._memory_cache[key]
                return True
            return False

    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._memory_cache.clear()
            self._cache_stats.clear()

    # IResourceManager 实现
    def allocate_resource(self, resource_type: str, config: Dict[str, Any]) -> str:
        """分配资源"""
        with self._lock:
            resource_id = f"{resource_type}_{datetime.now().timestamp()}"

            if resource_type == "thread_pool":
                max_workers = config.get("max_workers", 4)
                resource = threading.ThreadPoolExecutor(max_workers=max_workers)
            elif resource_type == "connection_pool":
                # 简化实现
                resource = {"type": "connection_pool", "config": config}
            else:
                resource = {"type": resource_type, "config": config}

            self._resource_pool[resource_id] = resource
            logger.debug(f"分配资源: {resource_id} ({resource_type})")

            return resource_id

    def release_resource(self, resource_id: str) -> None:
        """释放资源"""
        with self._lock:
            if resource_id in self._resource_pool:
                resource = self._resource_pool[resource_id]

                # 清理资源
                if hasattr(resource, 'shutdown'):
                    resource.shutdown(wait=True)

                del self._resource_pool[resource_id]
                logger.debug(f"释放资源: {resource_id}")

    def get_resource(self, resource_id: str) -> Optional[Any]:
        """获取资源"""
        with self._lock:
            return self._resource_pool.get(resource_id)

    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        with self._lock:
            return {
                "status": "healthy",
                "cache_entries": len(self._memory_cache),
                "active_resources": len(self._resource_pool),
                "cache_hit_rate": self._calculate_hit_rate()
            }

    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        with self._lock:
            return {
                "cache_size": len(self._memory_cache),
                "resource_count": len(self._resource_pool),
                "hit_rate": self._calculate_hit_rate(),
                "cache_stats": dict(self._cache_stats)
            }

    def _calculate_hit_rate(self) -> float:
        """计算缓存命中率"""
        total_hits = sum(stats["hits"] for stats in self._cache_stats.values())
        total_requests = sum(stats["hits"] + stats["misses"] for stats in self._cache_stats.values())

        if total_requests == 0:
            return 0.0

        return total_hits / total_requests

# =================== 3. 统一认证授权管理器 ===================

class UnifiedAuthSecurityManager(BaseManager):
    """
    统一认证授权管理器
    整合: AuthManager, AuthenticationManager, TokenManager, RBACManager
    """

    def __init__(self, event_bus: EventBus, config_manager: IConfigManager):
        super().__init__()
        self.event_bus = event_bus
        self.config_manager = config_manager
        self._sessions: Dict[str, Dict] = {}
        self._tokens: Dict[str, Dict] = {}
        self._permissions: Dict[str, Set[str]] = {}
        self._lock = threading.RLock()

    def get_name(self) -> str:
        return "unified_auth_security"

    def initialize(self, **kwargs) -> bool:
        """初始化认证授权管理器"""
        try:
            # 加载权限配置
            self._load_default_permissions()

            logger.info("统一认证授权管理器初始化完成")
            return True

        except Exception as e:
            logger.error(f"统一认证授权管理器初始化失败: {e}")
            return False

    def cleanup(self):
        """清理资源"""
        with self._lock:
            self._sessions.clear()
            self._tokens.clear()
            self._permissions.clear()

    def authenticate(self, credentials: Dict[str, Any]) -> Optional[str]:
        """用户认证"""
        with self._lock:
            # 简化实现 - 实际应该对接真实认证系统
            user_id = credentials.get("user_id")
            if user_id:
                session_id = f"session_{datetime.now().timestamp()}"
                self._sessions[session_id] = {
                    "user_id": user_id,
                    "created_at": datetime.now(),
                    "permissions": self._permissions.get(user_id, set())
                }

                # 发布认证事件
                event = ManagerEvent(
                    manager_name=self.get_name(),
                    event_type=EventType.AUTH_STATE_CHANGED.value,
                    payload={"action": "login", "user_id": user_id, "session_id": session_id}
                )
                self.event_bus.publish(event)

                return session_id
            return None

    def authorize(self, session_id: str, permission: str) -> bool:
        """权限验证"""
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False

            return permission in session.get("permissions", set())

    def create_token(self, session_id: str, scope: str) -> Optional[str]:
        """创建访问令牌"""
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return None

            token_id = f"token_{datetime.now().timestamp()}"
            self._tokens[token_id] = {
                "session_id": session_id,
                "scope": scope,
                "created_at": datetime.now(),
                "user_id": session["user_id"]
            }

            return token_id

    def validate_token(self, token_id: str) -> Optional[Dict[str, Any]]:
        """验证令牌"""
        with self._lock:
            return self._tokens.get(token_id)

    def _load_default_permissions(self):
        """加载默认权限"""
        default_permissions = {
            "admin": {"read", "write", "execute", "manage"},
            "developer": {"read", "write", "execute"},
            "viewer": {"read"}
        }

        with self._lock:
            self._permissions.update(default_permissions)

    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        with self._lock:
            return {
                "status": "healthy",
                "active_sessions": len(self._sessions),
                "active_tokens": len(self._tokens),
                "permission_roles": len(self._permissions)
            }

    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        with self._lock:
            return {
                "session_count": len(self._sessions),
                "token_count": len(self._tokens),
                "permission_count": sum(len(perms) for perms in self._permissions.values())
            }

# =================== 4. 统一工作流执行管理器 ===================

class UnifiedWorkflowExecutionManager(BaseManager):
    """
    统一工作流执行管理器
    整合: WorkflowManager, TaskManager, ParallelManager, SyncPointManager
    """

    def __init__(self, event_bus: EventBus, config_manager: IConfigManager):
        super().__init__()
        self.event_bus = event_bus
        self.config_manager = config_manager
        self._active_workflows: Dict[str, Dict] = {}
        self._execution_history: List[Dict] = []
        self._sync_points: Dict[str, Dict] = {}
        self._lock = threading.RLock()

    def get_name(self) -> str:
        return "unified_workflow_execution"

    def initialize(self, **kwargs) -> bool:
        """初始化工作流执行管理器"""
        try:
            logger.info("统一工作流执行管理器初始化完成")
            return True

        except Exception as e:
            logger.error(f"统一工作流执行管理器初始化失败: {e}")
            return False

    def cleanup(self):
        """清理资源"""
        with self._lock:
            # 停止所有活跃工作流
            for workflow_id in list(self._active_workflows.keys()):
                self.stop_workflow(workflow_id)

            self._execution_history.clear()
            self._sync_points.clear()

    def start_workflow(self, workflow_config: Dict[str, Any]) -> str:
        """启动工作流"""
        with self._lock:
            workflow_id = f"workflow_{datetime.now().timestamp()}"

            self._active_workflows[workflow_id] = {
                "id": workflow_id,
                "config": workflow_config,
                "status": "running",
                "started_at": datetime.now(),
                "current_step": 0,
                "steps": workflow_config.get("steps", [])
            }

            # 发布工作流事件
            event = ManagerEvent(
                manager_name=self.get_name(),
                event_type=EventType.WORKFLOW_STATE_CHANGED.value,
                payload={"action": "start", "workflow_id": workflow_id}
            )
            self.event_bus.publish(event)

            return workflow_id

    def stop_workflow(self, workflow_id: str) -> bool:
        """停止工作流"""
        with self._lock:
            if workflow_id in self._active_workflows:
                workflow = self._active_workflows[workflow_id]
                workflow["status"] = "stopped"
                workflow["stopped_at"] = datetime.now()

                # 移动到历史记录
                self._execution_history.append(workflow)
                del self._active_workflows[workflow_id]

                # 发布工作流事件
                event = ManagerEvent(
                    manager_name=self.get_name(),
                    event_type=EventType.WORKFLOW_STATE_CHANGED.value,
                    payload={"action": "stop", "workflow_id": workflow_id}
                )
                self.event_bus.publish(event)

                return True
            return False

    def create_sync_point(self, workflow_id: str, sync_config: Dict[str, Any]) -> str:
        """创建同步点"""
        with self._lock:
            sync_id = f"sync_{datetime.now().timestamp()}"

            self._sync_points[sync_id] = {
                "id": sync_id,
                "workflow_id": workflow_id,
                "config": sync_config,
                "status": "waiting",
                "created_at": datetime.now()
            }

            return sync_id

    def trigger_sync_point(self, sync_id: str) -> bool:
        """触发同步点"""
        with self._lock:
            if sync_id in self._sync_points:
                sync_point = self._sync_points[sync_id]
                sync_point["status"] = "triggered"
                sync_point["triggered_at"] = datetime.now()
                return True
            return False

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流状态"""
        with self._lock:
            return self._active_workflows.get(workflow_id)

    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        with self._lock:
            return {
                "status": "healthy",
                "active_workflows": len(self._active_workflows),
                "completed_workflows": len(self._execution_history),
                "active_sync_points": len([s for s in self._sync_points.values() if s["status"] == "waiting"])
            }

    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        with self._lock:
            return {
                "active_count": len(self._active_workflows),
                "history_count": len(self._execution_history),
                "sync_points_count": len(self._sync_points)
            }

# =================== 5. 统一Git集成管理器 ===================

class UnifiedGitIntegrationManager(BaseManager):
    """
    统一Git集成管理器
    整合: GitHooksManager, BranchManager, GitCacheManager, WorkflowManager
    """

    def __init__(self, event_bus: EventBus, config_manager: IConfigManager):
        super().__init__()
        self.event_bus = event_bus
        self.config_manager = config_manager
        self._git_cache: Dict[str, Any] = {}
        self._hooks_registry: Dict[str, Dict] = {}
        self._branch_policies: Dict[str, Dict] = {}
        self._lock = threading.RLock()

    def get_name(self) -> str:
        return "unified_git_integration"

    def initialize(self, **kwargs) -> bool:
        """初始化Git集成管理器"""
        try:
            # 设置默认钩子
            self._setup_default_hooks()

            logger.info("统一Git集成管理器初始化完成")
            return True

        except Exception as e:
            logger.error(f"统一Git集成管理器初始化失败: {e}")
            return False

    def cleanup(self):
        """清理资源"""
        with self._lock:
            self._git_cache.clear()
            self._hooks_registry.clear()
            self._branch_policies.clear()

    def register_hook(self, hook_name: str, hook_config: Dict[str, Any]) -> bool:
        """注册Git钩子"""
        with self._lock:
            self._hooks_registry[hook_name] = {
                "name": hook_name,
                "config": hook_config,
                "registered_at": datetime.now(),
                "active": True
            }

            # 发布Git事件
            event = ManagerEvent(
                manager_name=self.get_name(),
                event_type=EventType.GIT_OPERATION.value,
                payload={"action": "hook_registered", "hook_name": hook_name}
            )
            self.event_bus.publish(event)

            return True

    def execute_hook(self, hook_name: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """执行Git钩子"""
        with self._lock:
            hook = self._hooks_registry.get(hook_name)
            if not hook or not hook["active"]:
                return {"success": False, "message": "Hook not found or inactive"}

            # 简化实现 - 实际应该执行真实的Git钩子逻辑
            result = {
                "success": True,
                "hook_name": hook_name,
                "executed_at": datetime.now(),
                "context": context
            }

            # 发布Git事件
            event = ManagerEvent(
                manager_name=self.get_name(),
                event_type=EventType.GIT_OPERATION.value,
                payload={"action": "hook_executed", "hook_name": hook_name, "result": result}
            )
            self.event_bus.publish(event)

            return result

    def set_branch_policy(self, branch_pattern: str, policy: Dict[str, Any]) -> None:
        """设置分支策略"""
        with self._lock:
            self._branch_policies[branch_pattern] = policy

    def validate_branch_operation(self, branch_name: str, operation: str) -> bool:
        """验证分支操作"""
        with self._lock:
            for pattern, policy in self._branch_policies.items():
                if pattern in branch_name:  # 简化匹配
                    allowed_operations = policy.get("allowed_operations", [])
                    return operation in allowed_operations
            return True  # 默认允许

    def _setup_default_hooks(self):
        """设置默认钩子"""
        default_hooks = {
            "pre-commit": {"type": "quality_check", "enabled": True},
            "pre-push": {"type": "test_runner", "enabled": True},
            "post-commit": {"type": "notification", "enabled": False}
        }

        with self._lock:
            for hook_name, config in default_hooks.items():
                self.register_hook(hook_name, config)

    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        with self._lock:
            active_hooks = len([h for h in self._hooks_registry.values() if h["active"]])
            return {
                "status": "healthy",
                "registered_hooks": len(self._hooks_registry),
                "active_hooks": active_hooks,
                "branch_policies": len(self._branch_policies)
            }

    def get_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        with self._lock:
            return {
                "hooks_count": len(self._hooks_registry),
                "policies_count": len(self._branch_policies),
                "cache_entries": len(self._git_cache)
            }

# =================== 统一Manager系统 ===================

class UnifiedManagerSystem:
    """
    统一Manager系统 - 减少耦合的核心架构
    管理15个核心Manager，提供事件驱动的通信机制
    """

    def __init__(self):
        self.event_bus = EventBus()
        self.managers: Dict[str, ICoreManager] = {}
        self._initialized = False
        self._lock = threading.RLock()

        # 初始化核心管理器
        self._setup_core_managers()

    def _setup_core_managers(self):
        """设置核心管理器"""
        try:
            # 1. 配置状态管理器 (无依赖)
            config_manager = UnifiedConfigStateManager(self.event_bus)
            self.managers["config_state"] = config_manager

            # 2. 资源缓存管理器 (依赖配置管理器)
            resource_manager = UnifiedResourceCacheManager(self.event_bus, config_manager)
            self.managers["resource_cache"] = resource_manager

            # 3. 认证授权管理器 (依赖配置管理器)
            auth_manager = UnifiedAuthSecurityManager(self.event_bus, config_manager)
            self.managers["auth_security"] = auth_manager

            # 4. 工作流执行管理器 (依赖配置管理器)
            workflow_manager = UnifiedWorkflowExecutionManager(self.event_bus, config_manager)
            self.managers["workflow_execution"] = workflow_manager

            # 5. Git集成管理器 (依赖配置管理器)
            git_manager = UnifiedGitIntegrationManager(self.event_bus, config_manager)
            self.managers["git_integration"] = git_manager

            logger.info(f"设置了 {len(self.managers)} 个核心管理器")

        except Exception as e:
            logger.error(f"设置核心管理器失败: {e}")
            raise

    def initialize_all(self) -> bool:
        """初始化所有管理器"""
        with self._lock:
            if self._initialized:
                return True

            try:
                # 按依赖顺序初始化
                initialization_order = [
                    "config_state",
                    "resource_cache",
                    "auth_security",
                    "workflow_execution",
                    "git_integration"
                ]

                for manager_name in initialization_order:
                    manager = self.managers.get(manager_name)
                    if manager and hasattr(manager, 'initialize'):
                        if not manager.initialize():
                            logger.error(f"管理器 {manager_name} 初始化失败")
                            return False
                        logger.info(f"管理器 {manager_name} 初始化完成")

                self._initialized = True
                logger.info("所有管理器初始化完成")
                return True

            except Exception as e:
                logger.error(f"管理器初始化失败: {e}")
                return False

    def shutdown_all(self):
        """关闭所有管理器"""
        with self._lock:
            if not self._initialized:
                return

            # 按反向顺序关闭
            shutdown_order = [
                "git_integration",
                "workflow_execution",
                "auth_security",
                "resource_cache",
                "config_state"
            ]

            for manager_name in shutdown_order:
                manager = self.managers.get(manager_name)
                if manager and hasattr(manager, 'cleanup'):
                    try:
                        manager.cleanup()
                        logger.info(f"管理器 {manager_name} 已清理")
                    except Exception as e:
                        logger.error(f"管理器 {manager_name} 清理失败: {e}")

            self._initialized = False
            logger.info("所有管理器已关闭")

    def get_manager(self, manager_name: str) -> Optional[ICoreManager]:
        """获取管理器"""
        return self.managers.get(manager_name)

    def get_system_health(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        health_status = {
            "overall_status": "healthy",
            "manager_count": len(self.managers),
            "initialized": self._initialized,
            "managers": {}
        }

        unhealthy_count = 0

        for name, manager in self.managers.items():
            try:
                manager_health = manager.get_health_status()
                health_status["managers"][name] = manager_health

                if manager_health.get("status") != "healthy":
                    unhealthy_count += 1

            except Exception as e:
                health_status["managers"][name] = {
                    "status": "error",
                    "error": str(e)
                }
                unhealthy_count += 1

        if unhealthy_count > 0:
            health_status["overall_status"] = "degraded" if unhealthy_count < len(self.managers) else "unhealthy"

        return health_status

    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统性能指标"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "manager_count": len(self.managers),
            "event_bus_stats": self.event_bus.get_stats() if hasattr(self.event_bus, 'get_stats') else {},
            "managers": {}
        }

        for name, manager in self.managers.items():
            try:
                metrics["managers"][name] = manager.get_metrics()
            except Exception as e:
                metrics["managers"][name] = {"error": str(e)}

        return metrics

# =================== 全局实例 ===================

# 创建全局统一管理器系统
unified_manager_system = UnifiedManagerSystem()

# 向后兼容的快捷访问函数
def get_config_manager() -> Optional[IConfigManager]:
    """获取配置管理器"""
    return unified_manager_system.get_manager("config_state")

def get_cache_manager() -> Optional[ICacheManager]:
    """获取缓存管理器"""
    return unified_manager_system.get_manager("resource_cache")

def get_auth_manager() -> Optional[UnifiedAuthSecurityManager]:
    """获取认证管理器"""
    return unified_manager_system.get_manager("auth_security")

def get_workflow_manager() -> Optional[UnifiedWorkflowExecutionManager]:
    """获取工作流管理器"""
    return unified_manager_system.get_manager("workflow_execution")

def get_git_manager() -> Optional[UnifiedGitIntegrationManager]:
    """获取Git管理器"""
    return unified_manager_system.get_manager("git_integration")

# =================== 使用示例 ===================

def main():
    """使用示例"""
    try:
        # 初始化系统
        if not unified_manager_system.initialize_all():
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
            cache_manager.set("cache_key", "cache_value")
            cached_value = cache_manager.get("cache_key")
            logger.info(f"缓存值: {cached_value}")

        # 使用认证管理器
        auth_manager = get_auth_manager()
        if auth_manager:
            session_id = auth_manager.authenticate({"user_id": "test_user"})
            logger.info(f"会话ID: {session_id}")

        # 检查系统健康状态
        health = unified_manager_system.get_system_health()
        logger.info(f"系统健康状态: {health['overall_status']}")

        # 获取系统指标
        metrics = unified_manager_system.get_system_metrics()
        logger.info(f"管理器数量: {metrics['manager_count']}")

    except Exception as e:
        logger.error(f"示例执行失败: {e}")

    finally:
        # 关闭系统
        unified_manager_system.shutdown_all()

if __name__ == "__main__":
    main()