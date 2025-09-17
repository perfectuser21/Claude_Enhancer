#!/usr/bin/env python3
"""
Perfect21 事件系统 - 减少Manager间耦合的事件驱动通信
提供发布-订阅模式，让Manager通过事件总线通信而不是直接依赖
"""

import logging
import threading
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Callable, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
from concurrent.futures import ThreadPoolExecutor
import weakref

logger = logging.getLogger("Perfect21.Events")

# =================== 事件基础类型 ===================

@dataclass
class Event:
    """事件基类"""
    type: str
    source: str
    timestamp: datetime = field(default_factory=datetime.now)
    data: Dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: f"event_{datetime.now().timestamp()}")

class EventPriority(Enum):
    """事件优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class PriorityEvent(Event):
    """带优先级的事件"""
    priority: EventPriority = EventPriority.NORMAL

# =================== 事件处理器 ===================

class EventHandler(ABC):
    """事件处理器基类"""

    @abstractmethod
    def handle(self, event: Event) -> bool:
        """
        处理事件

        Args:
            event: 要处理的事件

        Returns:
            bool: 是否成功处理
        """
        pass

    def can_handle(self, event: Event) -> bool:
        """
        检查是否可以处理该事件

        Args:
            event: 要检查的事件

        Returns:
            bool: 是否可以处理
        """
        return True

class FunctionEventHandler(EventHandler):
    """函数式事件处理器"""

    def __init__(self, handler_func: Callable[[Event], bool],
                 can_handle_func: Optional[Callable[[Event], bool]] = None):
        self.handler_func = handler_func
        self.can_handle_func = can_handle_func or (lambda e: True)

    def handle(self, event: Event) -> bool:
        """处理事件"""
        try:
            return self.handler_func(event)
        except Exception as e:
            logger.error(f"事件处理函数执行失败: {e}")
            return False

    def can_handle(self, event: Event) -> bool:
        """检查是否可以处理该事件"""
        try:
            return self.can_handle_func(event)
        except Exception as e:
            logger.error(f"事件处理能力检查失败: {e}")
            return False

# =================== 事件过滤器 ===================

class EventFilter(ABC):
    """事件过滤器基类"""

    @abstractmethod
    def should_process(self, event: Event) -> bool:
        """判断是否应该处理该事件"""
        pass

class TypeEventFilter(EventFilter):
    """按事件类型过滤"""

    def __init__(self, allowed_types: Set[str]):
        self.allowed_types = allowed_types

    def should_process(self, event: Event) -> bool:
        return event.type in self.allowed_types

class SourceEventFilter(EventFilter):
    """按事件源过滤"""

    def __init__(self, allowed_sources: Set[str]):
        self.allowed_sources = allowed_sources

    def should_process(self, event: Event) -> bool:
        return event.source in self.allowed_sources

class CompositeEventFilter(EventFilter):
    """组合事件过滤器"""

    def __init__(self, filters: List[EventFilter], mode: str = "and"):
        self.filters = filters
        self.mode = mode  # "and" 或 "or"

    def should_process(self, event: Event) -> bool:
        if not self.filters:
            return True

        if self.mode == "and":
            return all(f.should_process(event) for f in self.filters)
        else:  # "or"
            return any(f.should_process(event) for f in self.filters)

# =================== 事件总线 ===================

class EventBus:
    """
    事件总线 - 核心事件分发系统

    特性:
    - 支持同步和异步事件处理
    - 支持事件优先级
    - 支持事件过滤
    - 支持弱引用避免内存泄漏
    - 支持处理器的热插拔
    - 提供性能统计
    """

    def __init__(self, max_workers: int = 4):
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._filters: Dict[str, List[EventFilter]] = {}
        self._async_handlers: Dict[str, List[EventHandler]] = {}

        # 使用弱引用集合避免内存泄漏
        self._weak_handlers: Dict[str, weakref.WeakSet] = {}

        # 线程池用于异步处理
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="EventBus")

        # 事件队列和处理统计
        self._event_queue: List[PriorityEvent] = []
        self._processing_stats: Dict[str, Dict] = {}

        # 线程锁
        self._lock = threading.RLock()
        self._queue_lock = threading.Lock()

        # 控制标志
        self._running = True
        self._processing_thread = None

        # 启动事件处理线程
        self._start_processing_thread()

        logger.info("事件总线初始化完成")

    def _start_processing_thread(self):
        """启动事件处理线程"""
        def process_events():
            while self._running:
                try:
                    events_to_process = []

                    with self._queue_lock:
                        if self._event_queue:
                            # 按优先级排序
                            self._event_queue.sort(key=lambda e: e.priority.value, reverse=True)
                            events_to_process = self._event_queue.copy()
                            self._event_queue.clear()

                    for event in events_to_process:
                        self._process_event_internal(event)

                    # 避免CPU过度占用
                    threading.Event().wait(0.01)

                except Exception as e:
                    logger.error(f"事件处理线程错误: {e}")

        self._processing_thread = threading.Thread(target=process_events, daemon=True)
        self._processing_thread.start()

    def subscribe(self, event_type: str, handler: EventHandler,
                  event_filter: Optional[EventFilter] = None,
                  async_handler: bool = False) -> str:
        """
        订阅事件

        Args:
            event_type: 事件类型
            handler: 事件处理器
            event_filter: 事件过滤器
            async_handler: 是否异步处理

        Returns:
            str: 订阅ID
        """
        with self._lock:
            # 选择合适的处理器集合
            handlers_dict = self._async_handlers if async_handler else self._handlers

            if event_type not in handlers_dict:
                handlers_dict[event_type] = []
                self._filters[event_type] = []

            handlers_dict[event_type].append(handler)

            if event_filter:
                self._filters[event_type].append(event_filter)

            # 初始化统计
            if event_type not in self._processing_stats:
                self._processing_stats[event_type] = {
                    "total_events": 0,
                    "successful_events": 0,
                    "failed_events": 0,
                    "handlers_count": 0
                }

            self._processing_stats[event_type]["handlers_count"] = len(handlers_dict[event_type])

            subscription_id = f"{event_type}_{len(handlers_dict[event_type])}"

            logger.debug(f"订阅事件: {event_type}, 处理器: {subscription_id}, 异步: {async_handler}")

            return subscription_id

    def subscribe_function(self, event_type: str, handler_func: Callable[[Event], bool],
                          event_filter: Optional[EventFilter] = None,
                          async_handler: bool = False) -> str:
        """
        使用函数订阅事件

        Args:
            event_type: 事件类型
            handler_func: 处理函数
            event_filter: 事件过滤器
            async_handler: 是否异步处理

        Returns:
            str: 订阅ID
        """
        handler = FunctionEventHandler(handler_func)
        return self.subscribe(event_type, handler, event_filter, async_handler)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> bool:
        """
        取消订阅

        Args:
            event_type: 事件类型
            handler: 要移除的处理器

        Returns:
            bool: 是否成功移除
        """
        with self._lock:
            removed = False

            # 从同步处理器中移除
            if event_type in self._handlers:
                if handler in self._handlers[event_type]:
                    self._handlers[event_type].remove(handler)
                    removed = True

            # 从异步处理器中移除
            if event_type in self._async_handlers:
                if handler in self._async_handlers[event_type]:
                    self._async_handlers[event_type].remove(handler)
                    removed = True

            # 更新统计
            if removed and event_type in self._processing_stats:
                total_handlers = len(self._handlers.get(event_type, [])) + len(self._async_handlers.get(event_type, []))
                self._processing_stats[event_type]["handlers_count"] = total_handlers

            if removed:
                logger.debug(f"取消订阅事件: {event_type}")

            return removed

    def publish(self, event: Event, priority: EventPriority = EventPriority.NORMAL) -> bool:
        """
        发布事件

        Args:
            event: 要发布的事件
            priority: 事件优先级

        Returns:
            bool: 是否成功发布
        """
        try:
            # 创建优先级事件
            if isinstance(event, PriorityEvent):
                priority_event = event
            else:
                priority_event = PriorityEvent(
                    type=event.type,
                    source=event.source,
                    timestamp=event.timestamp,
                    data=event.data,
                    event_id=event.event_id,
                    priority=priority
                )

            # 添加到队列
            with self._queue_lock:
                self._event_queue.append(priority_event)

            # 立即处理高优先级事件
            if priority == EventPriority.CRITICAL:
                self._process_event_internal(priority_event)

            logger.debug(f"发布事件: {event.type}, 优先级: {priority.name}")

            return True

        except Exception as e:
            logger.error(f"发布事件失败: {e}")
            return False

    def publish_sync(self, event: Event) -> Dict[str, Any]:
        """
        同步发布事件并等待所有处理完成

        Args:
            event: 要发布的事件

        Returns:
            Dict[str, Any]: 处理结果摘要
        """
        return self._process_event_internal(event)

    def _process_event_internal(self, event: Event) -> Dict[str, Any]:
        """
        内部事件处理方法

        Args:
            event: 要处理的事件

        Returns:
            Dict[str, Any]: 处理结果
        """
        event_type = event.type
        processing_result = {
            "event_id": event.event_id,
            "event_type": event_type,
            "processed_handlers": 0,
            "successful_handlers": 0,
            "failed_handlers": 0,
            "errors": []
        }

        # 更新统计
        with self._lock:
            if event_type in self._processing_stats:
                self._processing_stats[event_type]["total_events"] += 1

        try:
            # 获取处理器和过滤器
            handlers = self._handlers.get(event_type, [])
            async_handlers = self._async_handlers.get(event_type, [])
            filters = self._filters.get(event_type, [])

            # 应用过滤器
            should_process = True
            for event_filter in filters:
                if not event_filter.should_process(event):
                    should_process = False
                    break

            if not should_process:
                logger.debug(f"事件被过滤器阻止: {event_type}")
                return processing_result

            # 处理同步处理器
            for handler in handlers:
                if handler.can_handle(event):
                    try:
                        success = handler.handle(event)
                        processing_result["processed_handlers"] += 1

                        if success:
                            processing_result["successful_handlers"] += 1
                        else:
                            processing_result["failed_handlers"] += 1

                    except Exception as e:
                        processing_result["failed_handlers"] += 1
                        processing_result["errors"].append(str(e))
                        logger.error(f"同步处理器执行失败: {e}")

            # 处理异步处理器
            if async_handlers:
                futures = []
                for handler in async_handlers:
                    if handler.can_handle(event):
                        future = self._executor.submit(self._handle_async_event, handler, event)
                        futures.append(future)

                # 等待异步处理完成
                for future in futures:
                    try:
                        success = future.result(timeout=5.0)  # 5秒超时
                        processing_result["processed_handlers"] += 1

                        if success:
                            processing_result["successful_handlers"] += 1
                        else:
                            processing_result["failed_handlers"] += 1

                    except Exception as e:
                        processing_result["failed_handlers"] += 1
                        processing_result["errors"].append(str(e))
                        logger.error(f"异步处理器执行失败: {e}")

            # 更新成功统计
            with self._lock:
                if event_type in self._processing_stats:
                    if processing_result["failed_handlers"] == 0:
                        self._processing_stats[event_type]["successful_events"] += 1
                    else:
                        self._processing_stats[event_type]["failed_events"] += 1

            logger.debug(f"事件处理完成: {event_type}, 成功: {processing_result['successful_handlers']}, 失败: {processing_result['failed_handlers']}")

        except Exception as e:
            logger.error(f"事件处理过程发生错误: {e}")
            processing_result["errors"].append(str(e))

        return processing_result

    def _handle_async_event(self, handler: EventHandler, event: Event) -> bool:
        """异步事件处理包装器"""
        try:
            return handler.handle(event)
        except Exception as e:
            logger.error(f"异步事件处理器执行失败: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """获取事件总线统计信息"""
        with self._lock:
            stats = {
                "total_event_types": len(self._processing_stats),
                "queue_size": len(self._event_queue),
                "running": self._running,
                "executor_active": not self._executor._shutdown,
                "event_type_stats": dict(self._processing_stats)
            }

            # 计算总体统计
            total_events = sum(s["total_events"] for s in self._processing_stats.values())
            total_successful = sum(s["successful_events"] for s in self._processing_stats.values())
            total_failed = sum(s["failed_events"] for s in self._processing_stats.values())

            stats.update({
                "total_events_processed": total_events,
                "total_successful_events": total_successful,
                "total_failed_events": total_failed,
                "success_rate": (total_successful / total_events) if total_events > 0 else 0.0
            })

            return stats

    def get_health_status(self) -> Dict[str, Any]:
        """获取事件总线健康状态"""
        stats = self.get_stats()

        health_status = {
            "status": "healthy",
            "issues": []
        }

        # 检查队列积压
        if stats["queue_size"] > 100:
            health_status["status"] = "degraded"
            health_status["issues"].append(f"事件队列积压: {stats['queue_size']} 个事件")

        # 检查成功率
        if stats["success_rate"] < 0.9 and stats["total_events_processed"] > 10:
            health_status["status"] = "degraded"
            health_status["issues"].append(f"事件处理成功率过低: {stats['success_rate']:.2%}")

        # 检查线程池状态
        if not stats["running"] or not stats["executor_active"]:
            health_status["status"] = "unhealthy"
            health_status["issues"].append("事件总线或线程池已停止")

        return health_status

    def shutdown(self):
        """关闭事件总线"""
        logger.info("开始关闭事件总线...")

        self._running = False

        # 等待处理线程结束
        if self._processing_thread and self._processing_thread.is_alive():
            self._processing_thread.join(timeout=5.0)

        # 关闭线程池
        self._executor.shutdown(wait=True)

        # 清理资源
        with self._lock:
            self._handlers.clear()
            self._async_handlers.clear()
            self._filters.clear()
            self._processing_stats.clear()

        with self._queue_lock:
            self._event_queue.clear()

        logger.info("事件总线已关闭")

    def __del__(self):
        """析构函数"""
        if hasattr(self, '_running') and self._running:
            self.shutdown()

# =================== 便捷装饰器 ===================

def event_handler(event_type: str, event_bus: Optional[EventBus] = None,
                 async_handler: bool = False):
    """
    事件处理器装饰器

    Args:
        event_type: 事件类型
        event_bus: 事件总线实例
        async_handler: 是否异步处理
    """
    def decorator(func: Callable[[Event], bool]):
        if event_bus:
            event_bus.subscribe_function(event_type, func, async_handler=async_handler)
        return func
    return decorator

# =================== 全局事件总线 ===================

# 创建全局事件总线实例
global_event_bus = EventBus()

def get_global_event_bus() -> EventBus:
    """获取全局事件总线"""
    return global_event_bus

# =================== 使用示例 ===================

def main():
    """使用示例"""

    # 创建事件总线
    bus = EventBus()

    # 定义事件处理器
    def config_change_handler(event: Event) -> bool:
        logger.info(f"配置变更: {event.data}")
        return True

    def auth_change_handler(event: Event) -> bool:
        logger.info(f"认证状态变更: {event.data}")
        return True

    # 订阅事件
    bus.subscribe_function("config_changed", config_change_handler)
    bus.subscribe_function("auth_state_changed", auth_change_handler, async_handler=True)

    # 发布事件
    config_event = Event(
        type="config_changed",
        source="config_manager",
        data={"key": "test_key", "value": "test_value"}
    )

    auth_event = Event(
        type="auth_state_changed",
        source="auth_manager",
        data={"user_id": "test_user", "action": "login"}
    )

    # 发布事件
    bus.publish(config_event)
    bus.publish(auth_event, priority=EventPriority.HIGH)

    # 等待处理完成
    import time
    time.sleep(1)

    # 获取统计信息
    stats = bus.get_stats()
    logger.info(f"事件统计: {stats}")

    # 获取健康状态
    health = bus.get_health_status()
    logger.info(f"健康状态: {health}")

    # 关闭事件总线
    bus.shutdown()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()