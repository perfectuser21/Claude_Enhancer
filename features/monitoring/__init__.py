#!/usr/bin/env python3
"""
Perfect21 统一错误处理系统
提供企业级错误处理、恢复和监控能力
"""

from .exceptions import *
from .handler import GlobalErrorHandler, ErrorRecoveryManager
from .recovery import RetryManager, CircuitBreaker
from .monitoring import ErrorMonitor, ErrorMetrics
from .context import ErrorContext, ErrorEnricher

__all__ = [
    # 异常类
    'Perfect21Exception',
    'ValidationError',
    'ConfigurationError',
    'WorkflowError',
    'AgentExecutionError',
    'GitOperationError',
    'AuthenticationError',
    'AuthorizationError',
    'RateLimitError',
    'ExternalServiceError',
    'DataIntegrityError',
    'ResourceError',
    'TimeoutError',
    'RetryableError',
    'NonRetryableError',

    # 错误处理器
    'GlobalErrorHandler',
    'ErrorRecoveryManager',

    # 恢复策略
    'RetryManager',
    'CircuitBreaker',

    # 监控和度量
    'ErrorMonitor',
    'ErrorMetrics',

    # 上下文管理
    'ErrorContext',
    'ErrorEnricher',
]

# 版本信息
__version__ = '1.0.0'