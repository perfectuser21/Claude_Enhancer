#!/usr/bin/env python3
"""
Perfect21 错误恢复策略
提供重试机制、熔断器和恢复策略
"""

import time
import random
import threading
from typing import Callable, Optional, Tuple, Dict, Any, List, Type
from datetime import datetime, timedelta
from enum import Enum
import logging

from .exceptions import Perfect21Exception, RetryableError


class RetryStrategy(Enum):
    """重试策略"""
    FIXED_DELAY = "fixed_delay"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    LINEAR_BACKOFF = "linear_backoff"
    RANDOM_JITTER = "random_jitter"


class CircuitBreakerState(Enum):
    """熔断器状态"""
    CLOSED = "closed"      # 正常状态
    OPEN = "open"          # 熔断状态
    HALF_OPEN = "half_open"  # 半开状态


class RetryConfig:
    """重试配置"""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF,
        retry_exceptions: Optional[Tuple[Type[Exception], ...]] = None
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        self.strategy = strategy
        self.retry_exceptions = retry_exceptions or (RetryableError,)


class RetryResult:
    """重试结果"""

    def __init__(
        self,
        success: bool,
        result: Any = None,
        attempts: int = 0,
        total_time: float = 0.0,
        last_exception: Optional[Exception] = None
    ):
        self.success = success
        self.result = result
        self.attempts = attempts
        self.total_time = total_time
        self.last_exception = last_exception


class RetryManager:
    """重试管理器"""

    def __init__(self, default_config: Optional[RetryConfig] = None):
        self.default_config = default_config or RetryConfig()
        self.logger = logging.getLogger('Perfect21.RetryManager')

    def execute_with_retry(
        self,
        func: Callable,
        config: Optional[RetryConfig] = None,
        **kwargs
    ) -> Any:
        """执行带重试的函数"""
        config = config or self.default_config
        result = self.execute_with_retry_detailed(func, config, **kwargs)

        if result.success:
            return result.result
        else:
            # 如果最后一次异常是Perfect21异常，直接抛出
            if isinstance(result.last_exception, Perfect21Exception):
                raise result.last_exception
            else:
                # 包装为重试失败异常
                raise RetryableError(
                    f"Function failed after {result.attempts} attempts",
                    details={
                        'attempts': result.attempts,
                        'total_time': result.total_time,
                        'last_error': str(result.last_exception)
                    },
                    cause=result.last_exception
                )

    def execute_with_retry_detailed(
        self,
        func: Callable,
        config: Optional[RetryConfig] = None,
        **kwargs
    ) -> RetryResult:
        """执行带重试的函数，返回详细结果"""
        config = config or self.default_config
        start_time = time.time()
        last_exception = None

        for attempt in range(1, config.max_attempts + 1):
            try:
                self.logger.debug(f"Executing attempt {attempt}/{config.max_attempts}")

                # 执行函数
                result = func(**kwargs) if kwargs else func()

                # 成功，返回结果
                total_time = time.time() - start_time
                self.logger.info(f"Function succeeded on attempt {attempt}")

                return RetryResult(
                    success=True,
                    result=result,
                    attempts=attempt,
                    total_time=total_time
                )

            except Exception as e:
                last_exception = e

                # 检查是否是可重试的异常
                if not self._should_retry(e, config):
                    self.logger.warning(f"Exception not retryable: {e}")
                    break

                # 如果不是最后一次尝试，等待后重试
                if attempt < config.max_attempts:
                    delay = self._calculate_delay(attempt, config)
                    self.logger.warning(
                        f"Attempt {attempt} failed: {e}. Retrying in {delay:.2f}s"
                    )
                    time.sleep(delay)
                else:
                    self.logger.error(f"Final attempt {attempt} failed: {e}")

        # 所有尝试都失败了
        total_time = time.time() - start_time
        return RetryResult(
            success=False,
            attempts=config.max_attempts,
            total_time=total_time,
            last_exception=last_exception
        )

    def _should_retry(self, exception: Exception, config: RetryConfig) -> bool:
        """判断是否应该重试"""
        # 检查异常类型
        if not isinstance(exception, config.retry_exceptions):
            return False

        # 如果是Perfect21异常，检查是否可恢复
        if isinstance(exception, Perfect21Exception):
            return exception.recoverable

        return True

    def _calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """计算延迟时间"""
        if config.strategy == RetryStrategy.FIXED_DELAY:
            delay = config.base_delay

        elif config.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = config.base_delay * (config.backoff_factor ** (attempt - 1))

        elif config.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = config.base_delay * attempt

        elif config.strategy == RetryStrategy.RANDOM_JITTER:
            delay = config.base_delay + random.uniform(0, config.base_delay)

        else:
            delay = config.base_delay

        # 应用抖动
        if config.jitter and config.strategy != RetryStrategy.RANDOM_JITTER:
            jitter = delay * 0.1 * random.uniform(-1, 1)
            delay += jitter

        # 限制最大延迟
        return min(delay, config.max_delay)


class CircuitBreakerConfig:
    """熔断器配置"""

    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 3,
        timeout_seconds: int = 60,
        monitor_window_seconds: int = 300
    ):
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout_seconds = timeout_seconds
        self.monitor_window_seconds = monitor_window_seconds


class CircuitBreakerStats:
    """熔断器统计"""

    def __init__(self):
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state_change_time: Optional[datetime] = None
        self.total_calls = 0
        self.total_failures = 0


class CircuitBreaker:
    """熔断器"""

    def __init__(self, config: Optional[CircuitBreakerConfig] = None):
        self.config = config or CircuitBreakerConfig()
        self.logger = logging.getLogger('Perfect21.CircuitBreaker')

        # 为每个服务/操作维护独立的状态
        self._services: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def _get_service_state(self, service: str) -> Dict[str, Any]:
        """获取服务状态"""
        with self._lock:
            if service not in self._services:
                self._services[service] = {
                    'state': CircuitBreakerState.CLOSED,
                    'stats': CircuitBreakerStats(),
                    'failures': [],  # 失败时间戳列表
                    'successes': [],  # 成功时间戳列表
                }
            return self._services[service]

    def is_open(self, service: str) -> bool:
        """检查熔断器是否开启"""
        service_state = self._get_service_state(service)
        current_state = service_state['state']

        if current_state == CircuitBreakerState.OPEN:
            # 检查是否应该进入半开状态
            stats = service_state['stats']
            if (stats.last_failure_time and
                datetime.now() - stats.last_failure_time >
                timedelta(seconds=self.config.timeout_seconds)):

                self._change_state(service, CircuitBreakerState.HALF_OPEN)
                return False

            return True

        return False

    def record_success(self, service: str):
        """记录成功调用"""
        with self._lock:
            service_state = self._get_service_state(service)
            stats = service_state['stats']
            current_time = datetime.now()

            stats.success_count += 1
            stats.total_calls += 1

            # 记录成功时间戳
            service_state['successes'].append(current_time)

            # 清理过期的成功记录
            cutoff_time = current_time - timedelta(
                seconds=self.config.monitor_window_seconds
            )
            service_state['successes'] = [
                t for t in service_state['successes'] if t > cutoff_time
            ]

            current_state = service_state['state']

            if current_state == CircuitBreakerState.HALF_OPEN:
                # 半开状态下，如果连续成功次数达到阈值，关闭熔断器
                if stats.success_count >= self.config.success_threshold:
                    self._change_state(service, CircuitBreakerState.CLOSED)
                    stats.failure_count = 0

    def record_failure(self, service: str):
        """记录失败调用"""
        with self._lock:
            service_state = self._get_service_state(service)
            stats = service_state['stats']
            current_time = datetime.now()

            stats.failure_count += 1
            stats.total_calls += 1
            stats.total_failures += 1
            stats.last_failure_time = current_time

            # 记录失败时间戳
            service_state['failures'].append(current_time)

            # 清理过期的失败记录
            cutoff_time = current_time - timedelta(
                seconds=self.config.monitor_window_seconds
            )
            service_state['failures'] = [
                t for t in service_state['failures'] if t > cutoff_time
            ]

            current_state = service_state['state']

            if current_state == CircuitBreakerState.CLOSED:
                # 检查是否应该开启熔断器
                recent_failures = len(service_state['failures'])
                if recent_failures >= self.config.failure_threshold:
                    self._change_state(service, CircuitBreakerState.OPEN)

            elif current_state == CircuitBreakerState.HALF_OPEN:
                # 半开状态下，任何失败都会重新开启熔断器
                self._change_state(service, CircuitBreakerState.OPEN)

    def _change_state(self, service: str, new_state: CircuitBreakerState):
        """改变熔断器状态"""
        service_state = self._get_service_state(service)
        old_state = service_state['state']
        service_state['state'] = new_state
        service_state['stats'].state_change_time = datetime.now()

        self.logger.info(f"Circuit breaker for {service} changed from {old_state.value} to {new_state.value}")

        # 重置计数器
        if new_state == CircuitBreakerState.CLOSED:
            service_state['stats'].failure_count = 0
            service_state['stats'].success_count = 0
        elif new_state == CircuitBreakerState.HALF_OPEN:
            service_state['stats'].success_count = 0

    def get_state(self, service: str) -> CircuitBreakerState:
        """获取熔断器状态"""
        return self._get_service_state(service)['state']

    def get_stats(self, service: Optional[str] = None) -> Dict[str, Any]:
        """获取统计信息"""
        if service:
            service_state = self._get_service_state(service)
            stats = service_state['stats']
            return {
                'state': service_state['state'].value,
                'failure_count': stats.failure_count,
                'success_count': stats.success_count,
                'total_calls': stats.total_calls,
                'total_failures': stats.total_failures,
                'last_failure_time': stats.last_failure_time.isoformat() if stats.last_failure_time else None,
                'state_change_time': stats.state_change_time.isoformat() if stats.state_change_time else None
            }
        else:
            # 返回所有服务的统计
            all_stats = {}
            for svc, state in self._services.items():
                all_stats[svc] = self.get_stats(svc)
            return all_stats

    def reset_stats(self, service: Optional[str] = None):
        """重置统计信息"""
        if service:
            with self._lock:
                if service in self._services:
                    del self._services[service]
        else:
            with self._lock:
                self._services.clear()


class RecoveryStrategy:
    """恢复策略基类"""

    def can_recover(self, exception: Exception, context: Dict[str, Any]) -> bool:
        """判断是否可以恢复"""
        raise NotImplementedError

    def recover(self, exception: Exception, context: Dict[str, Any]) -> bool:
        """执行恢复"""
        raise NotImplementedError


class DefaultRecoveryStrategy(RecoveryStrategy):
    """默认恢复策略"""

    def can_recover(self, exception: Exception, context: Dict[str, Any]) -> bool:
        """判断是否可以恢复"""
        return isinstance(exception, RetryableError)

    def recover(self, exception: Exception, context: Dict[str, Any]) -> bool:
        """执行恢复"""
        if isinstance(exception, RetryableError):
            # 设置重试标记
            context['should_retry'] = True
            context['retry_after'] = getattr(exception, 'retry_after', 1)
            return True
        return False


class GradualRecoveryStrategy(RecoveryStrategy):
    """渐进式恢复策略"""

    def __init__(self, max_recovery_attempts: int = 3):
        self.max_recovery_attempts = max_recovery_attempts

    def can_recover(self, exception: Exception, context: Dict[str, Any]) -> bool:
        """判断是否可以恢复"""
        attempts = context.get('recovery_attempts', 0)
        return attempts < self.max_recovery_attempts

    def recover(self, exception: Exception, context: Dict[str, Any]) -> bool:
        """执行恢复"""
        attempts = context.get('recovery_attempts', 0)
        context['recovery_attempts'] = attempts + 1

        # 渐进式延迟
        delay = 2 ** attempts
        context['retry_after'] = delay

        return True


class FallbackRecoveryStrategy(RecoveryStrategy):
    """降级恢复策略"""

    def __init__(self, fallback_function: Callable):
        self.fallback_function = fallback_function

    def can_recover(self, exception: Exception, context: Dict[str, Any]) -> bool:
        """判断是否可以恢复"""
        return callable(self.fallback_function)

    def recover(self, exception: Exception, context: Dict[str, Any]) -> bool:
        """执行恢复"""
        try:
            # 执行降级函数
            result = self.fallback_function(exception, context)
            context['fallback_result'] = result
            return True
        except Exception:
            return False


class RecoveryOrchestrator:
    """恢复编排器"""

    def __init__(self):
        self.strategies: List[RecoveryStrategy] = []
        self.logger = logging.getLogger('Perfect21.RecoveryOrchestrator')

    def add_strategy(self, strategy: RecoveryStrategy):
        """添加恢复策略"""
        self.strategies.append(strategy)

    def attempt_recovery(
        self,
        exception: Exception,
        context: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """尝试恢复"""
        recovery_context = context.copy()

        for strategy in self.strategies:
            try:
                if strategy.can_recover(exception, recovery_context):
                    self.logger.info(f"Attempting recovery with {strategy.__class__.__name__}")

                    if strategy.recover(exception, recovery_context):
                        self.logger.info(f"Recovery successful with {strategy.__class__.__name__}")
                        return True, recovery_context

            except Exception as e:
                self.logger.error(f"Recovery strategy {strategy.__class__.__name__} failed: {e}")

        return False, recovery_context