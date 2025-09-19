#!/usr/bin/env python3
"""
Perfect21 Fault Tolerance System
故障容错和自动恢复系统
"""

import logging
import time
import threading
import traceback
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod
import weakref

logger = logging.getLogger("Perfect21.FaultTolerance")

class FaultLevel(Enum):
    """故障级别"""
    LOW = "low"          # 轻微故障，不影响主要功能
    MEDIUM = "medium"    # 中等故障，影响部分功能
    HIGH = "high"        # 严重故障，影响主要功能
    CRITICAL = "critical" # 严重故障，系统不可用

class RecoveryStrategy(Enum):
    """恢复策略"""
    RETRY = "retry"           # 重试
    FALLBACK = "fallback"     # 降级
    RESTART = "restart"       # 重启
    ISOLATE = "isolate"       # 隔离
    IGNORE = "ignore"         # 忽略

@dataclass
class FaultRecord:
    """故障记录"""
    module_name: str
    fault_type: str
    fault_level: FaultLevel
    error_message: str
    stack_trace: str
    timestamp: float
    context: Dict[str, Any]
    recovery_attempted: bool = False
    recovery_success: bool = False

class CircuitBreakerState(Enum):
    """断路器状态"""
    CLOSED = "closed"       # 关闭状态，正常工作
    OPEN = "open"          # 开启状态，阻止调用
    HALF_OPEN = "half_open" # 半开状态，尝试恢复

class CircuitBreaker:
    """断路器模式实现"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60,
                 expected_exception: type = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitBreakerState.CLOSED
        self._lock = threading.RLock()

    def call(self, func: Callable, *args, **kwargs):
        """执行受保护的调用"""
        with self._lock:
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                else:
                    raise Exception("断路器开启，服务不可用")

            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result

            except self.expected_exception as e:
                self._on_failure()
                raise e

    def _should_attempt_reset(self) -> bool:
        """是否应该尝试重置"""
        return (self.last_failure_time and
                time.time() - self.last_failure_time >= self.recovery_timeout)

    def _on_success(self):
        """成功调用处理"""
        self.failure_count = 0
        self.state = CircuitBreakerState.CLOSED

    def _on_failure(self):
        """失败调用处理"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN

class FaultHandler(ABC):
    """故障处理器接口"""

    @abstractmethod
    def can_handle(self, fault: FaultRecord) -> bool:
        """是否能处理此故障"""
        pass

    @abstractmethod
    def handle(self, fault: FaultRecord) -> bool:
        """处理故障，返回是否处理成功"""
        pass

class RetryHandler(FaultHandler):
    """重试处理器"""

    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def can_handle(self, fault: FaultRecord) -> bool:
        return fault.fault_level in [FaultLevel.LOW, FaultLevel.MEDIUM]

    def handle(self, fault: FaultRecord) -> bool:
        """重试处理"""
        retry_count = fault.context.get('retry_count', 0)
        if retry_count < self.max_retries:
            time.sleep(self.retry_delay * (retry_count + 1))  # 指数退避
            fault.context['retry_count'] = retry_count + 1
            logger.info(f"重试处理故障 {fault.module_name}: 第{retry_count + 1}次")
            return True
        return False

class FallbackHandler(FaultHandler):
    """降级处理器"""

    def __init__(self, fallback_functions: Dict[str, Callable]):
        self.fallback_functions = fallback_functions

    def can_handle(self, fault: FaultRecord) -> bool:
        return fault.module_name in self.fallback_functions

    def handle(self, fault: FaultRecord) -> bool:
        """降级处理"""
        try:
            fallback_func = self.fallback_functions[fault.module_name]
            fallback_func(fault.context)
            logger.info(f"降级处理故障 {fault.module_name}")
            return True
        except Exception as e:
            logger.error(f"降级处理失败 {fault.module_name}: {e}")
            return False

class IsolationHandler(FaultHandler):
    """隔离处理器"""

    def __init__(self):
        self.isolated_modules = set()

    def can_handle(self, fault: FaultRecord) -> bool:
        return fault.fault_level in [FaultLevel.HIGH, FaultLevel.CRITICAL]

    def handle(self, fault: FaultRecord) -> bool:
        """隔离处理"""
        self.isolated_modules.add(fault.module_name)
        logger.warning(f"隔离故障模块: {fault.module_name}")
        return True

    def is_isolated(self, module_name: str) -> bool:
        """检查模块是否被隔离"""
        return module_name in self.isolated_modules

    def restore_module(self, module_name: str) -> bool:
        """恢复被隔离的模块"""
        if module_name in self.isolated_modules:
            self.isolated_modules.remove(module_name)
            logger.info(f"恢复被隔离的模块: {module_name}")
            return True
        return False

class FaultToleranceManager:
    """故障容错管理器"""

    def __init__(self):
        self.fault_history: List[FaultRecord] = []
        self.handlers: List[FaultHandler] = []
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.health_checks: Dict[str, Callable] = {}
        self._lock = threading.RLock()
        self._monitoring_thread = None
        self._monitoring_active = False

        # 默认处理器
        self.retry_handler = RetryHandler()
        self.isolation_handler = IsolationHandler()
        self.fallback_handler = FallbackHandler({})

        self.handlers.extend([
            self.retry_handler,
            self.fallback_handler,
            self.isolation_handler
        ])

    def register_health_check(self, module_name: str, health_check: Callable[[], bool]):
        """注册健康检查"""
        self.health_checks[module_name] = health_check

    def register_fallback(self, module_name: str, fallback_func: Callable):
        """注册降级函数"""
        self.fallback_handler.fallback_functions[module_name] = fallback_func

    def get_circuit_breaker(self, module_name: str) -> CircuitBreaker:
        """获取断路器"""
        if module_name not in self.circuit_breakers:
            self.circuit_breakers[module_name] = CircuitBreaker()
        return self.circuit_breakers[module_name]

    def report_fault(self, module_name: str, fault_type: str, fault_level: FaultLevel,
                    error: Exception, context: Dict[str, Any] = None) -> None:
        """报告故障"""
        fault = FaultRecord(
            module_name=module_name,
            fault_type=fault_type,
            fault_level=fault_level,
            error_message=str(error),
            stack_trace=traceback.format_exc(),
            timestamp=time.time(),
            context=context or {}
        )

        with self._lock:
            self.fault_history.append(fault)
            # 保持历史记录不超过1000条
            if len(self.fault_history) > 1000:
                self.fault_history.pop(0)

        # 尝试自动恢复
        self._attempt_recovery(fault)

        logger.error(f"故障报告 [{fault_level.value}] {module_name}.{fault_type}: {error}")

    def _attempt_recovery(self, fault: FaultRecord) -> bool:
        """尝试自动恢复"""
        for handler in self.handlers:
            if handler.can_handle(fault):
                try:
                    if handler.handle(fault):
                        fault.recovery_attempted = True
                        fault.recovery_success = True
                        logger.info(f"故障自动恢复成功: {fault.module_name}")
                        return True
                except Exception as e:
                    logger.error(f"故障恢复失败: {e}")

        fault.recovery_attempted = True
        fault.recovery_success = False
        return False

    def start_health_monitoring(self, check_interval: int = 30):
        """启动健康监控"""
        if self._monitoring_active:
            return

        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(
            target=self._health_monitor_loop,
            args=(check_interval,),
            daemon=True
        )
        self._monitoring_thread.start()
        logger.info("健康监控已启动")

    def stop_health_monitoring(self):
        """停止健康监控"""
        self._monitoring_active = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
        logger.info("健康监控已停止")

    def _health_monitor_loop(self, check_interval: int):
        """健康监控循环"""
        while self._monitoring_active:
            try:
                self._perform_health_checks()
                time.sleep(check_interval)
            except Exception as e:
                logger.error(f"健康检查异常: {e}")

    def _perform_health_checks(self):
        """执行健康检查"""
        for module_name, health_check in self.health_checks.items():
            try:
                if not health_check():
                    self.report_fault(
                        module_name=module_name,
                        fault_type="health_check_failed",
                        fault_level=FaultLevel.MEDIUM,
                        error=Exception("健康检查失败"),
                        context={'check_type': 'periodic'}
                    )
            except Exception as e:
                self.report_fault(
                    module_name=module_name,
                    fault_type="health_check_error",
                    fault_level=FaultLevel.HIGH,
                    error=e,
                    context={'check_type': 'periodic'}
                )

    def get_fault_statistics(self) -> Dict[str, Any]:
        """获取故障统计"""
        with self._lock:
            if not self.fault_history:
                return {'total_faults': 0}

            stats = {
                'total_faults': len(self.fault_history),
                'faults_by_level': {},
                'faults_by_module': {},
                'recent_faults': len([f for f in self.fault_history
                                    if time.time() - f.timestamp < 3600]),  # 1小时内
                'recovery_rate': len([f for f in self.fault_history if f.recovery_success]) / len(self.fault_history)
            }

            for fault in self.fault_history:
                # 按级别统计
                level = fault.fault_level.value
                stats['faults_by_level'][level] = stats['faults_by_level'].get(level, 0) + 1

                # 按模块统计
                module = fault.module_name
                stats['faults_by_module'][module] = stats['faults_by_module'].get(module, 0) + 1

            return stats

    def get_system_health(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        stats = self.get_fault_statistics()
        isolated_modules = list(self.isolation_handler.isolated_modules)

        circuit_breaker_states = {
            name: breaker.state.value
            for name, breaker in self.circuit_breakers.items()
        }

        return {
            'overall_health': 'healthy' if stats.get('recent_faults', 0) < 5 else 'degraded',
            'fault_statistics': stats,
            'isolated_modules': isolated_modules,
            'circuit_breaker_states': circuit_breaker_states,
            'monitoring_active': self._monitoring_active
        }

# 全局故障容错管理器
fault_manager = FaultToleranceManager()

def setup_perfect21_fault_tolerance():
    """设置Perfect21故障容错"""
    # 注意：modules层不能直接依赖features层
    # 健康检查应该由上层注册，而不是在这里硬编码
    pass

    # 注册降级函数
    def git_workflow_fallback(context):
        logger.warning("Git工作流降级: 使用基础Git操作")

    fault_manager.register_fallback('git_workflow', git_workflow_fallback)

    # 启动健康监控
    fault_manager.start_health_monitoring()

    logger.info("Perfect21故障容错系统设置完成")

if __name__ == "__main__":
    # 测试故障容错系统
    setup_perfect21_fault_tolerance()
    health = fault_manager.get_system_health()
    print("故障容错系统状态:", health)