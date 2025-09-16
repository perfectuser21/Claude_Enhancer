#!/usr/bin/env python3
"""
Perfect21 State Management System
统一状态管理和数据流控制
"""

import logging
import threading
import time
import json
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
from enum import Enum
import weakref

logger = logging.getLogger("Perfect21.StateManager")

class StateScope(Enum):
    """状态作用域"""
    GLOBAL = "global"
    MODULE = "module"
    SESSION = "session"
    REQUEST = "request"

class StateChangeType(Enum):
    """状态变更类型"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    RESET = "reset"

@dataclass
class StateChange:
    """状态变更记录"""
    scope: StateScope
    key: str
    old_value: Any
    new_value: Any
    change_type: StateChangeType
    timestamp: float
    source: str

class StateListener(ABC):
    """状态监听器接口"""

    @abstractmethod
    def on_state_changed(self, change: StateChange) -> None:
        """状态变更回调"""
        pass

class CachePolicy:
    """缓存策略"""

    def __init__(self, ttl: int = 300, max_size: int = 1000):
        self.ttl = ttl  # 生存时间（秒）
        self.max_size = max_size
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._timestamps: Dict[str, float] = {}
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            if key in self._cache:
                if time.time() - self._timestamps[key] < self.ttl:
                    return self._cache[key]['value']
                else:
                    # 过期删除
                    del self._cache[key]
                    del self._timestamps[key]
            return None

    def set(self, key: str, value: Any) -> None:
        """设置缓存值"""
        with self._lock:
            # 检查缓存大小
            if len(self._cache) >= self.max_size:
                self._evict_oldest()

            self._cache[key] = {'value': value}
            self._timestamps[key] = time.time()

    def _evict_oldest(self) -> None:
        """驱逐最旧的缓存项"""
        if self._timestamps:
            oldest_key = min(self._timestamps.keys(), key=lambda k: self._timestamps[k])
            del self._cache[oldest_key]
            del self._timestamps[oldest_key]

    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()

class StateManager:
    """统一状态管理器"""

    def __init__(self):
        self._states: Dict[StateScope, Dict[str, Any]] = {
            scope: {} for scope in StateScope
        }
        self._listeners: List[StateListener] = []
        self._cache = CachePolicy()
        self._lock = threading.RLock()
        self._change_history: List[StateChange] = []
        self._max_history = 1000

    def set_state(self, scope: StateScope, key: str, value: Any, source: str = "unknown") -> None:
        """设置状态"""
        with self._lock:
            old_value = self._states[scope].get(key)
            self._states[scope][key] = value

            # 更新缓存
            cache_key = f"{scope.value}:{key}"
            self._cache.set(cache_key, value)

            # 记录变更
            change = StateChange(
                scope=scope,
                key=key,
                old_value=old_value,
                new_value=value,
                change_type=StateChangeType.UPDATE if old_value is not None else StateChangeType.CREATE,
                timestamp=time.time(),
                source=source
            )
            self._record_change(change)

            # 通知监听器
            self._notify_listeners(change)

    def get_state(self, scope: StateScope, key: str, default: Any = None) -> Any:
        """获取状态"""
        # 先检查缓存
        cache_key = f"{scope.value}:{key}"
        cached_value = self._cache.get(cache_key)
        if cached_value is not None:
            return cached_value

        # 从状态存储获取
        with self._lock:
            value = self._states[scope].get(key, default)
            if value is not None:
                self._cache.set(cache_key, value)
            return value

    def delete_state(self, scope: StateScope, key: str, source: str = "unknown") -> bool:
        """删除状态"""
        with self._lock:
            if key in self._states[scope]:
                old_value = self._states[scope][key]
                del self._states[scope][key]

                # 清除缓存
                cache_key = f"{scope.value}:{key}"
                self._cache.set(cache_key, None)

                # 记录变更
                change = StateChange(
                    scope=scope,
                    key=key,
                    old_value=old_value,
                    new_value=None,
                    change_type=StateChangeType.DELETE,
                    timestamp=time.time(),
                    source=source
                )
                self._record_change(change)
                self._notify_listeners(change)
                return True
            return False

    def get_all_states(self, scope: StateScope) -> Dict[str, Any]:
        """获取作用域内所有状态"""
        with self._lock:
            return self._states[scope].copy()

    def clear_scope(self, scope: StateScope, source: str = "unknown") -> None:
        """清空作用域"""
        with self._lock:
            old_states = self._states[scope].copy()
            self._states[scope].clear()

            # 清除相关缓存
            self._cache.clear()

            # 记录变更
            change = StateChange(
                scope=scope,
                key="*",
                old_value=old_states,
                new_value={},
                change_type=StateChangeType.RESET,
                timestamp=time.time(),
                source=source
            )
            self._record_change(change)
            self._notify_listeners(change)

    def add_listener(self, listener: StateListener) -> None:
        """添加状态监听器"""
        self._listeners.append(listener)

    def remove_listener(self, listener: StateListener) -> None:
        """移除状态监听器"""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _notify_listeners(self, change: StateChange) -> None:
        """通知监听器"""
        for listener in self._listeners[:]:  # 复制列表避免并发修改
            try:
                listener.on_state_changed(change)
            except Exception as e:
                logger.error(f"状态监听器通知失败: {e}")

    def _record_change(self, change: StateChange) -> None:
        """记录状态变更"""
        self._change_history.append(change)
        if len(self._change_history) > self._max_history:
            self._change_history.pop(0)

    def get_change_history(self, limit: int = 100) -> List[StateChange]:
        """获取状态变更历史"""
        with self._lock:
            return self._change_history[-limit:]

    def get_health_status(self) -> Dict[str, Any]:
        """获取状态管理器健康状态"""
        with self._lock:
            total_states = sum(len(states) for states in self._states.values())
            return {
                'total_states': total_states,
                'states_by_scope': {scope.value: len(states) for scope, states in self._states.items()},
                'cache_size': len(self._cache._cache),
                'listeners_count': len(self._listeners),
                'change_history_size': len(self._change_history),
                'uptime': time.time() - getattr(self, '_start_time', time.time())
            }

class ModuleStateManager(StateListener):
    """模块状态管理器"""

    def __init__(self, module_name: str, global_state_manager: StateManager):
        self.module_name = module_name
        self.global_manager = global_state_manager
        self.global_manager.add_listener(self)

    def set(self, key: str, value: Any) -> None:
        """设置模块状态"""
        module_key = f"{self.module_name}.{key}"
        self.global_manager.set_state(StateScope.MODULE, module_key, value, self.module_name)

    def get(self, key: str, default: Any = None) -> Any:
        """获取模块状态"""
        module_key = f"{self.module_name}.{key}"
        return self.global_manager.get_state(StateScope.MODULE, module_key, default)

    def delete(self, key: str) -> bool:
        """删除模块状态"""
        module_key = f"{self.module_name}.{key}"
        return self.global_manager.delete_state(StateScope.MODULE, module_key, self.module_name)

    def get_all(self) -> Dict[str, Any]:
        """获取模块所有状态"""
        all_states = self.global_manager.get_all_states(StateScope.MODULE)
        prefix = f"{self.module_name}."
        return {
            key[len(prefix):]: value
            for key, value in all_states.items()
            if key.startswith(prefix)
        }

    def on_state_changed(self, change: StateChange) -> None:
        """响应状态变更"""
        if change.scope == StateScope.MODULE and change.key.startswith(f"{self.module_name}."):
            # 模块内状态变更处理
            logger.debug(f"模块 {self.module_name} 状态变更: {change.key}")

# 全局状态管理器
global_state_manager = StateManager()

def get_module_state_manager(module_name: str) -> ModuleStateManager:
    """获取模块状态管理器"""
    return ModuleStateManager(module_name, global_state_manager)

def setup_perfect21_states():
    """设置Perfect21初始状态"""
    # 设置全局状态
    global_state_manager.set_state(StateScope.GLOBAL, "perfect21.version", "2.3.0", "system")
    global_state_manager.set_state(StateScope.GLOBAL, "perfect21.mode", "production", "system")
    global_state_manager.set_state(StateScope.GLOBAL, "perfect21.start_time", time.time(), "system")

    # 设置模块状态
    modules = ['capability_discovery', 'version_manager', 'git_workflow', 'claude_md_manager']
    for module in modules:
        module_sm = get_module_state_manager(module)
        module_sm.set("status", "initialized")
        module_sm.set("version", "2.3.0")

    logger.info("Perfect21状态初始化完成")

if __name__ == "__main__":
    # 测试状态管理
    setup_perfect21_states()
    status = global_state_manager.get_health_status()
    print("状态管理器状态:", status)