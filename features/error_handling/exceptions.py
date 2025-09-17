#!/usr/bin/env python3
"""
Perfect21 异常层次结构
定义统一的业务异常类型和错误码
"""

from typing import Optional, Dict, Any, List
from enum import Enum
import traceback
from datetime import datetime


class ErrorCode(Enum):
    """错误码枚举"""
    # 通用错误 (1000-1999)
    UNKNOWN_ERROR = 1000
    VALIDATION_ERROR = 1001
    CONFIGURATION_ERROR = 1002
    PERMISSION_DENIED = 1003
    RESOURCE_NOT_FOUND = 1004
    TIMEOUT_ERROR = 1005

    # 工作流错误 (2000-2999)
    WORKFLOW_INIT_FAILED = 2000
    WORKFLOW_EXECUTION_FAILED = 2001
    SYNC_POINT_FAILED = 2002
    PHASE_EXECUTION_FAILED = 2003
    TASK_DECOMPOSITION_FAILED = 2004

    # Agent执行错误 (3000-3999)
    AGENT_NOT_FOUND = 3000
    AGENT_EXECUTION_FAILED = 3001
    AGENT_TIMEOUT = 3002
    AGENT_CONFIG_ERROR = 3003
    SUBAGENT_CALL_FAILED = 3004

    # Git操作错误 (4000-4999)
    GIT_HOOK_FAILED = 4000
    GIT_OPERATION_FAILED = 4001
    BRANCH_OPERATION_FAILED = 4002
    MERGE_CONFLICT = 4003
    REPOSITORY_ERROR = 4004

    # 认证授权错误 (5000-5999)
    AUTHENTICATION_FAILED = 5000
    AUTHORIZATION_FAILED = 5001
    TOKEN_INVALID = 5002
    TOKEN_EXPIRED = 5003
    RATE_LIMIT_EXCEEDED = 5004

    # 外部服务错误 (6000-6999)
    EXTERNAL_SERVICE_UNAVAILABLE = 6000
    API_CALL_FAILED = 6001
    NETWORK_ERROR = 6002
    SERVICE_TIMEOUT = 6003

    # 数据错误 (7000-7999)
    DATA_INTEGRITY_ERROR = 7000
    DATABASE_ERROR = 7001
    SERIALIZATION_ERROR = 7002
    VALIDATION_SCHEMA_ERROR = 7003

    # 资源错误 (8000-8999)
    RESOURCE_EXHAUSTED = 8000
    MEMORY_ERROR = 8001
    DISK_SPACE_ERROR = 8002
    FILE_OPERATION_ERROR = 8003


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Perfect21Exception(Exception):
    """Perfect21基础异常类"""

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.UNKNOWN_ERROR,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None,
        recoverable: bool = False,
        retry_after: Optional[int] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.severity = severity
        self.details = details or {}
        self.cause = cause
        self.context = context or {}
        self.recoverable = recoverable
        self.retry_after = retry_after
        self.timestamp = datetime.now()
        self.traceback_info = traceback.format_exc()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'message': self.message,
            'error_code': self.error_code.value,
            'error_name': self.error_code.name,
            'severity': self.severity.value,
            'details': self.details,
            'context': self.context,
            'recoverable': self.recoverable,
            'retry_after': self.retry_after,
            'timestamp': self.timestamp.isoformat(),
            'traceback': self.traceback_info,
            'cause': str(self.cause) if self.cause else None
        }

    def __str__(self) -> str:
        base = f"[{self.error_code.name}] {self.message}"
        if self.details:
            base += f" | Details: {self.details}"
        return base


class RetryableError(Perfect21Exception):
    """可重试错误基类"""

    def __init__(self, message: str, retry_after: int = 1, **kwargs):
        kwargs['recoverable'] = True
        kwargs['retry_after'] = retry_after
        super().__init__(message, **kwargs)


class NonRetryableError(Perfect21Exception):
    """不可重试错误基类"""

    def __init__(self, message: str, **kwargs):
        kwargs['recoverable'] = False
        super().__init__(message, **kwargs)


# ============= 具体业务异常类 =============

class ValidationError(NonRetryableError):
    """数据验证错误"""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Any = None,
        expected: Optional[str] = None,
        **kwargs
    ):
        details = {
            'field': field,
            'value': str(value) if value is not None else None,
            'expected': expected
        }
        kwargs.setdefault('error_code', ErrorCode.VALIDATION_ERROR)
        kwargs.setdefault('details', {}).update(details)
        super().__init__(message, **kwargs)


class ConfigurationError(NonRetryableError):
    """配置错误"""

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        config_file: Optional[str] = None,
        **kwargs
    ):
        details = {
            'config_key': config_key,
            'config_file': config_file
        }
        kwargs.setdefault('error_code', ErrorCode.CONFIGURATION_ERROR)
        kwargs.setdefault('details', {}).update(details)
        super().__init__(message, **kwargs)


class WorkflowError(Perfect21Exception):
    """工作流错误"""

    def __init__(
        self,
        message: str,
        workflow_name: Optional[str] = None,
        phase: Optional[str] = None,
        task_id: Optional[str] = None,
        **kwargs
    ):
        details = {
            'workflow_name': workflow_name,
            'phase': phase,
            'task_id': task_id
        }
        kwargs.setdefault('error_code', ErrorCode.WORKFLOW_EXECUTION_FAILED)
        kwargs.setdefault('details', {}).update(details)
        super().__init__(message, **kwargs)


class AgentExecutionError(RetryableError):
    """Agent执行错误"""

    def __init__(
        self,
        message: str,
        agent_name: Optional[str] = None,
        task: Optional[str] = None,
        execution_time: Optional[float] = None,
        **kwargs
    ):
        details = {
            'agent_name': agent_name,
            'task': task,
            'execution_time': execution_time
        }
        kwargs.setdefault('error_code', ErrorCode.AGENT_EXECUTION_FAILED)
        kwargs.setdefault('details', {}).update(details)
        super().__init__(message, **kwargs)


class GitOperationError(RetryableError):
    """Git操作错误"""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        repository: Optional[str] = None,
        branch: Optional[str] = None,
        **kwargs
    ):
        details = {
            'operation': operation,
            'repository': repository,
            'branch': branch
        }
        kwargs.setdefault('error_code', ErrorCode.GIT_OPERATION_FAILED)
        kwargs.setdefault('details', {}).update(details)
        super().__init__(message, **kwargs)


class AuthenticationError(NonRetryableError):
    """认证错误"""

    def __init__(
        self,
        message: str,
        user: Optional[str] = None,
        auth_method: Optional[str] = None,
        **kwargs
    ):
        details = {
            'user': user,
            'auth_method': auth_method
        }
        kwargs.setdefault('error_code', ErrorCode.AUTHENTICATION_FAILED)
        kwargs.setdefault('severity', ErrorSeverity.HIGH)
        kwargs.setdefault('details', {}).update(details)
        super().__init__(message, **kwargs)


class AuthorizationError(NonRetryableError):
    """授权错误"""

    def __init__(
        self,
        message: str,
        user: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        **kwargs
    ):
        details = {
            'user': user,
            'resource': resource,
            'action': action
        }
        kwargs.setdefault('error_code', ErrorCode.AUTHORIZATION_FAILED)
        kwargs.setdefault('severity', ErrorSeverity.HIGH)
        kwargs.setdefault('details', {}).update(details)
        super().__init__(message, **kwargs)


class RateLimitError(RetryableError):
    """速率限制错误"""

    def __init__(
        self,
        message: str,
        limit: Optional[int] = None,
        window: Optional[int] = None,
        retry_after: int = 60,
        **kwargs
    ):
        details = {
            'limit': limit,
            'window': window
        }
        kwargs.setdefault('error_code', ErrorCode.RATE_LIMIT_EXCEEDED)
        kwargs.setdefault('details', {}).update(details)
        super().__init__(message, retry_after=retry_after, **kwargs)


class ExternalServiceError(RetryableError):
    """外部服务错误"""

    def __init__(
        self,
        message: str,
        service: Optional[str] = None,
        endpoint: Optional[str] = None,
        status_code: Optional[int] = None,
        **kwargs
    ):
        details = {
            'service': service,
            'endpoint': endpoint,
            'status_code': status_code
        }
        kwargs.setdefault('error_code', ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE)
        kwargs.setdefault('details', {}).update(details)
        super().__init__(message, **kwargs)


class DataIntegrityError(NonRetryableError):
    """数据完整性错误"""

    def __init__(
        self,
        message: str,
        table: Optional[str] = None,
        constraint: Optional[str] = None,
        **kwargs
    ):
        details = {
            'table': table,
            'constraint': constraint
        }
        kwargs.setdefault('error_code', ErrorCode.DATA_INTEGRITY_ERROR)
        kwargs.setdefault('severity', ErrorSeverity.HIGH)
        kwargs.setdefault('details', {}).update(details)
        super().__init__(message, **kwargs)


class ResourceError(RetryableError):
    """资源错误"""

    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        **kwargs
    ):
        details = {
            'resource_type': resource_type,
            'resource_id': resource_id
        }
        kwargs.setdefault('error_code', ErrorCode.RESOURCE_EXHAUSTED)
        kwargs.setdefault('details', {}).update(details)
        super().__init__(message, **kwargs)


class TimeoutError(RetryableError):
    """超时错误"""

    def __init__(
        self,
        message: str,
        timeout_seconds: Optional[float] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        details = {
            'timeout_seconds': timeout_seconds,
            'operation': operation
        }
        kwargs.setdefault('error_code', ErrorCode.TIMEOUT_ERROR)
        kwargs.setdefault('details', {}).update(details)
        super().__init__(message, **kwargs)


# ============= 异常工厂函数 =============

def create_validation_error(
    field: str,
    value: Any,
    expected: str,
    message: Optional[str] = None
) -> ValidationError:
    """创建验证错误"""
    if not message:
        message = f"Validation failed for field '{field}'"

    return ValidationError(
        message=message,
        field=field,
        value=value,
        expected=expected
    )


def create_agent_error(
    agent_name: str,
    task: str,
    cause: Optional[Exception] = None,
    message: Optional[str] = None
) -> AgentExecutionError:
    """创建Agent执行错误"""
    if not message:
        message = f"Agent '{agent_name}' failed to execute task '{task}'"

    return AgentExecutionError(
        message=message,
        agent_name=agent_name,
        task=task,
        cause=cause
    )


def create_git_error(
    operation: str,
    details: Optional[str] = None,
    cause: Optional[Exception] = None
) -> GitOperationError:
    """创建Git操作错误"""
    message = f"Git operation '{operation}' failed"
    if details:
        message += f": {details}"

    return GitOperationError(
        message=message,
        operation=operation,
        cause=cause
    )


def create_timeout_error(
    operation: str,
    timeout_seconds: float,
    message: Optional[str] = None
) -> TimeoutError:
    """创建超时错误"""
    if not message:
        message = f"Operation '{operation}' timed out after {timeout_seconds} seconds"

    return TimeoutError(
        message=message,
        operation=operation,
        timeout_seconds=timeout_seconds
    )


# ============= 异常转换器 =============

class ExceptionConverter:
    """异常转换器 - 将标准异常转换为Perfect21异常"""

    @staticmethod
    def convert(exc: Exception, context: Optional[Dict[str, Any]] = None) -> Perfect21Exception:
        """转换标准异常为Perfect21异常"""
        context = context or {}

        # 如果已经是Perfect21异常，直接返回
        if isinstance(exc, Perfect21Exception):
            return exc

        # 根据异常类型进行转换
        if isinstance(exc, ValueError):
            return ValidationError(
                message=str(exc),
                cause=exc,
                context=context
            )

        elif isinstance(exc, FileNotFoundError):
            return ResourceError(
                message=str(exc),
                resource_type="file",
                cause=exc,
                context=context
            )

        elif isinstance(exc, PermissionError):
            return AuthorizationError(
                message=str(exc),
                cause=exc,
                context=context
            )

        elif isinstance(exc, ConnectionError):
            return ExternalServiceError(
                message=str(exc),
                cause=exc,
                context=context
            )

        elif isinstance(exc, OSError):
            return ResourceError(
                message=str(exc),
                cause=exc,
                context=context
            )

        else:
            # 默认转换为通用Perfect21异常
            return Perfect21Exception(
                message=str(exc),
                cause=exc,
                context=context
            )


# ============= 异常聚合器 =============

class ExceptionAggregator:
    """异常聚合器 - 用于收集和管理多个相关异常"""

    def __init__(self, context: str):
        self.context = context
        self.exceptions: List[Perfect21Exception] = []

    def add(self, exc: Exception, **kwargs):
        """添加异常"""
        if not isinstance(exc, Perfect21Exception):
            exc = ExceptionConverter.convert(exc, kwargs.get('context'))
        self.exceptions.append(exc)

    def has_errors(self) -> bool:
        """是否有错误"""
        return len(self.exceptions) > 0

    def get_summary(self) -> Dict[str, Any]:
        """获取错误摘要"""
        if not self.exceptions:
            return {'error_count': 0}

        severity_counts = {}
        error_codes = set()

        for exc in self.exceptions:
            # 统计严重程度
            severity = exc.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

            # 收集错误码
            error_codes.add(exc.error_code.name)

        return {
            'context': self.context,
            'error_count': len(self.exceptions),
            'severity_counts': severity_counts,
            'error_codes': list(error_codes),
            'highest_severity': max(
                [exc.severity for exc in self.exceptions],
                key=lambda s: ['low', 'medium', 'high', 'critical'].index(s.value)
            ).value
        }

    def create_aggregate_exception(self) -> Perfect21Exception:
        """创建聚合异常"""
        if not self.exceptions:
            return Perfect21Exception("No errors in aggregator")

        summary = self.get_summary()
        message = f"Multiple errors in {self.context}: {summary['error_count']} errors"

        return Perfect21Exception(
            message=message,
            severity=ErrorSeverity(summary['highest_severity']),
            details=summary,
            context={'aggregated_exceptions': [exc.to_dict() for exc in self.exceptions]}
        )