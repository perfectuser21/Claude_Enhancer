#!/usr/bin/env python3
"""
Perfect21 全局错误处理器
提供统一的错误处理、恢复和监控功能
"""

import sys
import threading
import traceback
from typing import Dict, Any, Callable, Optional, List, Type
from functools import wraps
from datetime import datetime, timedelta
import logging

from .exceptions import (
    Perfect21Exception, ErrorCode, ErrorSeverity,
    ExceptionConverter, ExceptionAggregator,
    RetryableError, NonRetryableError
)
from .context import ErrorContext, ErrorEnricher
from .recovery import RetryManager, CircuitBreaker
from .monitoring import ErrorMonitor


class ErrorHandlerConfig:
    """错误处理器配置"""

    def __init__(self):
        self.enable_global_handler = True
        self.enable_recovery = True
        self.enable_monitoring = True
        self.max_retry_attempts = 3
        self.retry_backoff_factor = 2.0
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_timeout = 60
        self.notification_webhook = None
        self.alert_thresholds = {
            ErrorSeverity.CRITICAL: 1,
            ErrorSeverity.HIGH: 3,
            ErrorSeverity.MEDIUM: 10,
            ErrorSeverity.LOW: 50
        }


class GlobalErrorHandler:
    """全局错误处理器"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, config: Optional[ErrorHandlerConfig] = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config: Optional[ErrorHandlerConfig] = None):
        if hasattr(self, '_initialized'):
            return

        self.config = config or ErrorHandlerConfig()
        self.logger = logging.getLogger('Perfect21.ErrorHandler')

        # 初始化组件
        self.error_enricher = ErrorEnricher()
        self.retry_manager = RetryManager()
        self.circuit_breaker = CircuitBreaker()
        self.error_monitor = ErrorMonitor()

        # 错误处理器注册表
        self.handlers: Dict[Type[Exception], List[Callable]] = {}
        self.global_handlers: List[Callable] = []

        # 统计信息
        self.stats = {
            'total_errors': 0,
            'handled_errors': 0,
            'recovered_errors': 0,
            'failed_recoveries': 0,
            'last_error_time': None
        }

        # 注册默认处理器
        self._register_default_handlers()

        # 安装全局异常钩子
        if self.config.enable_global_handler:
            self._install_global_hook()

        self._initialized = True

    def _install_global_hook(self):
        """安装全局异常钩子"""
        def global_exception_handler(exc_type, exc_value, exc_traceback):
            """全局异常处理函数"""
            if exc_type == KeyboardInterrupt:
                # 保持Ctrl+C的默认行为
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return

            try:
                # 转换为Perfect21异常
                if not isinstance(exc_value, Perfect21Exception):
                    exc_value = ExceptionConverter.convert(exc_value)

                # 处理异常
                self.handle_exception(exc_value, {
                    'source': 'global_hook',
                    'traceback': ''.join(traceback.format_exception(
                        exc_type, exc_value, exc_traceback
                    ))
                })

            except Exception as e:
                # 处理器本身出错时的fallback
                self.logger.error(f"Error in global exception handler: {e}")
                sys.__excepthook__(exc_type, exc_value, exc_traceback)

        # 替换默认的异常钩子
        sys.excepthook = global_exception_handler

    def _register_default_handlers(self):
        """注册默认错误处理器"""
        # 认证错误处理器
        self.register_handler(
            from .exceptions import AuthenticationError,
            self._handle_authentication_error
        )

        # 资源错误处理器
        self.register_handler(
            from .exceptions import ResourceError,
            self._handle_resource_error
        )

        # 外部服务错误处理器
        self.register_handler(
            from .exceptions import ExternalServiceError,
            self._handle_external_service_error
        )

        # 工作流错误处理器
        self.register_handler(
            from .exceptions import WorkflowError,
            self._handle_workflow_error
        )

    def register_handler(
        self,
        exception_type: Type[Exception],
        handler: Callable[[Exception, Dict[str, Any]], bool]
    ):
        """注册异常处理器"""
        if exception_type not in self.handlers:
            self.handlers[exception_type] = []
        self.handlers[exception_type].append(handler)

    def register_global_handler(self, handler: Callable[[Exception, Dict[str, Any]], bool]):
        """注册全局处理器"""
        self.global_handlers.append(handler)

    def handle_exception(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """处理异常"""
        try:
            self.stats['total_errors'] += 1
            self.stats['last_error_time'] = datetime.now()

            # 转换为Perfect21异常
            if not isinstance(exception, Perfect21Exception):
                exception = ExceptionConverter.convert(exception, context)

            # 丰富错误上下文
            enriched_context = self.error_enricher.enrich(exception, context)

            # 记录错误
            self._log_error(exception, enriched_context)

            # 监控错误
            if self.config.enable_monitoring:
                self.error_monitor.record_error(exception, enriched_context)

            # 尝试恢复
            recovered = False
            if self.config.enable_recovery and isinstance(exception, RetryableError):
                recovered = self._attempt_recovery(exception, enriched_context)

            # 运行注册的处理器
            handled = self._run_handlers(exception, enriched_context)

            if handled or recovered:
                self.stats['handled_errors'] += 1
                if recovered:
                    self.stats['recovered_errors'] += 1
            else:
                self.stats['failed_recoveries'] += 1

            # 检查是否需要告警
            self._check_alert_thresholds(exception)

            return handled or recovered

        except Exception as e:
            # 处理器本身出错时的fallback
            self.logger.error(f"Error in exception handler: {e}")
            return False

    def _log_error(self, exception: Perfect21Exception, context: Dict[str, Any]):
        """记录错误日志"""
        level = self._get_log_level(exception.severity)

        log_data = {
            'error_code': exception.error_code.name,
            'severity': exception.severity.value,
            'message': exception.message,
            'details': exception.details,
            'context': context,
            'recoverable': exception.recoverable
        }

        self.logger.log(level, f"Error occurred: {exception}", extra=log_data)

    def _get_log_level(self, severity: ErrorSeverity) -> int:
        """获取日志级别"""
        mapping = {
            ErrorSeverity.LOW: logging.INFO,
            ErrorSeverity.MEDIUM: logging.WARNING,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }
        return mapping.get(severity, logging.WARNING)

    def _attempt_recovery(
        self,
        exception: RetryableError,
        context: Dict[str, Any]
    ) -> bool:
        """尝试错误恢复"""
        try:
            # 检查熔断器状态
            if self.circuit_breaker.is_open(context.get('operation', 'default')):
                self.logger.warning("Circuit breaker is open, skipping recovery")
                return False

            # 执行重试
            recovery_func = context.get('recovery_function')
            if recovery_func:
                success = self.retry_manager.execute_with_retry(
                    recovery_func,
                    max_attempts=self.config.max_retry_attempts,
                    backoff_factor=self.config.retry_backoff_factor,
                    retry_exceptions=(type(exception),)
                )

                if success:
                    self.circuit_breaker.record_success(context.get('operation', 'default'))
                    return True
                else:
                    self.circuit_breaker.record_failure(context.get('operation', 'default'))

            return False

        except Exception as e:
            self.logger.error(f"Recovery attempt failed: {e}")
            return False

    def _run_handlers(
        self,
        exception: Perfect21Exception,
        context: Dict[str, Any]
    ) -> bool:
        """运行异常处理器"""
        handled = False

        # 运行特定类型的处理器
        for exc_type, handlers in self.handlers.items():
            if isinstance(exception, exc_type):
                for handler in handlers:
                    try:
                        if handler(exception, context):
                            handled = True
                    except Exception as e:
                        self.logger.error(f"Error in handler {handler}: {e}")

        # 运行全局处理器
        for handler in self.global_handlers:
            try:
                if handler(exception, context):
                    handled = True
            except Exception as e:
                self.logger.error(f"Error in global handler {handler}: {e}")

        return handled

    def _check_alert_thresholds(self, exception: Perfect21Exception):
        """检查告警阈值"""
        if not self.config.alert_thresholds:
            return

        threshold = self.config.alert_thresholds.get(exception.severity)
        if threshold is None:
            return

        # 检查是否超过阈值（这里简化实现）
        recent_errors = self.error_monitor.get_recent_errors(
            severity=exception.severity,
            time_window=timedelta(hours=1)
        )

        if len(recent_errors) >= threshold:
            self._send_alert(exception, recent_errors)

    def _send_alert(self, exception: Perfect21Exception, recent_errors: List[Dict]):
        """发送告警"""
        alert_data = {
            'alert_type': 'error_threshold_exceeded',
            'severity': exception.severity.value,
            'error_count': len(recent_errors),
            'latest_error': exception.to_dict(),
            'timestamp': datetime.now().isoformat()
        }

        self.logger.critical(f"Alert: {alert_data}")

        # 如果配置了webhook，发送通知
        if self.config.notification_webhook:
            try:
                import requests
                requests.post(self.config.notification_webhook, json=alert_data)
            except Exception as e:
                self.logger.error(f"Failed to send alert notification: {e}")

    # ============= 默认处理器实现 =============

    def _handle_authentication_error(
        self,
        exception: "AuthenticationError",
        context: Dict[str, Any]
    ) -> bool:
        """处理认证错误"""
        self.logger.warning(f"Authentication failed: {exception.message}")

        # 清除可能无效的token
        if 'token_manager' in context:
            token_manager = context['token_manager']
            if hasattr(token_manager, 'invalidate_token'):
                token_manager.invalidate_token(exception.details.get('user'))

        return True

    def _handle_resource_error(
        self,
        exception: "ResourceError",
        context: Dict[str, Any]
    ) -> bool:
        """处理资源错误"""
        resource_type = exception.details.get('resource_type')

        if resource_type == 'memory':
            # 触发垃圾回收
            import gc
            gc.collect()
            self.logger.info("Triggered garbage collection due to memory error")

        elif resource_type == 'file':
            # 检查磁盘空间
            self.logger.warning("File operation failed, checking disk space")

        return True

    def _handle_external_service_error(
        self,
        exception: "ExternalServiceError",
        context: Dict[str, Any]
    ) -> bool:
        """处理外部服务错误"""
        service = exception.details.get('service')

        # 记录服务不可用
        self.circuit_breaker.record_failure(service or 'unknown_service')

        # 可以在这里实现服务降级逻辑
        self.logger.warning(f"External service {service} is unavailable")

        return True

    def _handle_workflow_error(
        self,
        exception: "WorkflowError",
        context: Dict[str, Any]
    ) -> bool:
        """处理工作流错误"""
        workflow_name = exception.details.get('workflow_name')
        phase = exception.details.get('phase')

        self.logger.error(f"Workflow {workflow_name} failed at phase {phase}")

        # 可以在这里实现工作流回滚逻辑
        return True

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            'monitoring_stats': self.error_monitor.get_stats(),
            'circuit_breaker_stats': self.circuit_breaker.get_stats()
        }

    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'total_errors': 0,
            'handled_errors': 0,
            'recovered_errors': 0,
            'failed_recoveries': 0,
            'last_error_time': None
        }
        self.error_monitor.reset_stats()
        self.circuit_breaker.reset_stats()


class ErrorRecoveryManager:
    """错误恢复管理器"""

    def __init__(self, global_handler: Optional[GlobalErrorHandler] = None):
        self.global_handler = global_handler or GlobalErrorHandler()
        self.recovery_strategies: Dict[str, Callable] = {}

    def register_recovery_strategy(
        self,
        error_type: str,
        strategy: Callable[[Exception, Dict[str, Any]], bool]
    ):
        """注册恢复策略"""
        self.recovery_strategies[error_type] = strategy

    def recover(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """执行错误恢复"""
        context = context or {}

        if not isinstance(exception, Perfect21Exception):
            exception = ExceptionConverter.convert(exception, context)

        # 查找对应的恢复策略
        error_type = exception.error_code.name
        strategy = self.recovery_strategies.get(error_type)

        if strategy:
            try:
                return strategy(exception, context)
            except Exception as e:
                self.global_handler.logger.error(f"Recovery strategy failed: {e}")
                return False

        # 使用默认恢复逻辑
        return self._default_recovery(exception, context)

    def _default_recovery(
        self,
        exception: Perfect21Exception,
        context: Dict[str, Any]
    ) -> bool:
        """默认恢复逻辑"""
        if isinstance(exception, RetryableError):
            # 对于可重试错误，设置重试标记
            context['should_retry'] = True
            context['retry_after'] = exception.retry_after
            return True

        return False


# ============= 装饰器 =============

def handle_errors(
    ignore_errors: Optional[List[Type[Exception]]] = None,
    reraise_errors: Optional[List[Type[Exception]]] = None,
    default_return: Any = None,
    recovery_function: Optional[Callable] = None
):
    """错误处理装饰器"""
    ignore_errors = ignore_errors or []
    reraise_errors = reraise_errors or []

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 检查是否需要忽略
                if any(isinstance(e, exc_type) for exc_type in ignore_errors):
                    return default_return

                # 检查是否需要重新抛出
                if any(isinstance(e, exc_type) for exc_type in reraise_errors):
                    raise

                # 处理异常
                context = {
                    'function': func.__name__,
                    'args': args,
                    'kwargs': kwargs,
                    'recovery_function': recovery_function
                }

                handler = GlobalErrorHandler()
                handled = handler.handle_exception(e, context)

                if handled and recovery_function:
                    try:
                        return recovery_function(*args, **kwargs)
                    except Exception:
                        pass

                if handled:
                    return default_return
                else:
                    raise

        return wrapper
    return decorator


def retry_on_error(
    max_attempts: int = 3,
    backoff_factor: float = 1.0,
    retry_exceptions: Optional[List[Type[Exception]]] = None
):
    """重试装饰器"""
    retry_exceptions = retry_exceptions or [RetryableError]

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retry_manager = RetryManager()
            return retry_manager.execute_with_retry(
                lambda: func(*args, **kwargs),
                max_attempts=max_attempts,
                backoff_factor=backoff_factor,
                retry_exceptions=tuple(retry_exceptions)
            )
        return wrapper
    return decorator