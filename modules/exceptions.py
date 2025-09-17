#!/usr/bin/env python3
"""
Perfect21 Exception Hierarchy and Error Handling System
Comprehensive error handling with recovery mechanisms and retry logic
"""

import time
import logging
import traceback
from typing import Dict, Any, Optional, List, Callable, Union
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import functools
import json


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification"""
    SYSTEM = "system"
    NETWORK = "network"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    PERMISSION = "permission"
    TIMEOUT = "timeout"
    RESOURCE = "resource"
    EXTERNAL_API = "external_api"
    GIT_OPERATION = "git_operation"
    AGENT_EXECUTION = "agent_execution"
    WORKFLOW = "workflow"
    DATABASE = "database"
    FILE_SYSTEM = "file_system"
    CONFIGURATION = "configuration"


@dataclass
class ErrorContext:
    """Error context information"""
    component: str
    operation: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetryConfig:
    """Retry configuration"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_multiplier: float = 2.0
    jitter: bool = True
    retry_on_exceptions: tuple = (Exception,)


class Perfect21BaseException(Exception):
    """Base exception class for Perfect21"""

    def __init__(
        self,
        message: str,
        error_code: str = None,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: ErrorContext = None,
        original_exception: Exception = None,
        user_friendly_message: str = None,
        recovery_suggestions: List[str] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.category = category
        self.severity = severity
        self.context = context
        self.original_exception = original_exception
        self.user_friendly_message = user_friendly_message or self._generate_user_friendly_message()
        self.recovery_suggestions = recovery_suggestions or []
        self.timestamp = datetime.now()

    def _generate_user_friendly_message(self) -> str:
        """Generate a user-friendly error message"""
        return f"An error occurred in {self.category.value}: {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "user_friendly_message": self.user_friendly_message,
            "category": self.category.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context.__dict__ if self.context else None,
            "recovery_suggestions": self.recovery_suggestions,
            "original_exception": str(self.original_exception) if self.original_exception else None
        }


class ValidationError(Perfect21BaseException):
    """Validation errors"""

    def __init__(self, message: str, field_name: str = None, **kwargs):
        self.field_name = field_name
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            **kwargs
        )

    def _generate_user_friendly_message(self) -> str:
        if self.field_name:
            return f"Invalid value for '{self.field_name}': {self.message}"
        return f"Validation failed: {self.message}"


class NetworkError(Perfect21BaseException):
    """Network-related errors"""

    def __init__(self, message: str, status_code: int = None, **kwargs):
        self.status_code = status_code
        super().__init__(
            message=message,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            recovery_suggestions=[
                "Check your internet connection",
                "Verify the service is available",
                "Try again in a few moments"
            ],
            **kwargs
        )


class AuthenticationError(Perfect21BaseException):
    """Authentication errors"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.AUTHENTICATION,
            severity=ErrorSeverity.HIGH,
            recovery_suggestions=[
                "Check your credentials",
                "Re-authenticate if necessary",
                "Contact support if the issue persists"
            ],
            **kwargs
        )

    def _generate_user_friendly_message(self) -> str:
        return "Authentication failed. Please check your credentials."


class PermissionError(Perfect21BaseException):
    """Permission/authorization errors"""

    def __init__(self, message: str, required_permission: str = None, **kwargs):
        self.required_permission = required_permission
        super().__init__(
            message=message,
            category=ErrorCategory.PERMISSION,
            severity=ErrorSeverity.MEDIUM,
            recovery_suggestions=[
                "Contact an administrator for access",
                "Verify you have the required permissions"
            ],
            **kwargs
        )


class TimeoutError(Perfect21BaseException):
    """Timeout errors"""

    def __init__(self, message: str, timeout_value: float = None, **kwargs):
        self.timeout_value = timeout_value
        super().__init__(
            message=message,
            category=ErrorCategory.TIMEOUT,
            severity=ErrorSeverity.MEDIUM,
            recovery_suggestions=[
                "Try again with a longer timeout",
                "Check system performance",
                "Verify network connectivity"
            ],
            **kwargs
        )


class ResourceError(Perfect21BaseException):
    """Resource-related errors (memory, disk, etc.)"""

    def __init__(self, message: str, resource_type: str = None, **kwargs):
        self.resource_type = resource_type
        super().__init__(
            message=message,
            category=ErrorCategory.RESOURCE,
            severity=ErrorSeverity.HIGH,
            recovery_suggestions=[
                "Free up system resources",
                "Check available memory/disk space",
                "Contact system administrator"
            ],
            **kwargs
        )


class ExternalAPIError(Perfect21BaseException):
    """External API errors"""

    def __init__(self, message: str, api_name: str = None, status_code: int = None, **kwargs):
        self.api_name = api_name
        self.status_code = status_code
        super().__init__(
            message=message,
            category=ErrorCategory.EXTERNAL_API,
            severity=ErrorSeverity.HIGH,
            recovery_suggestions=[
                "Check API service status",
                "Verify API credentials",
                "Try again later if service is unavailable"
            ],
            **kwargs
        )


class GitOperationError(Perfect21BaseException):
    """Git operation errors"""

    def __init__(self, message: str, git_command: str = None, **kwargs):
        self.git_command = git_command
        super().__init__(
            message=message,
            category=ErrorCategory.GIT_OPERATION,
            severity=ErrorSeverity.MEDIUM,
            recovery_suggestions=[
                "Check git repository status",
                "Verify working directory",
                "Ensure proper git configuration"
            ],
            **kwargs
        )


class AgentExecutionError(Perfect21BaseException):
    """Agent execution errors"""

    def __init__(self, message: str, agent_name: str = None, task_description: str = None, **kwargs):
        self.agent_name = agent_name
        self.task_description = task_description
        super().__init__(
            message=message,
            category=ErrorCategory.AGENT_EXECUTION,
            severity=ErrorSeverity.HIGH,
            recovery_suggestions=[
                "Review agent configuration",
                "Check task parameters",
                "Try with different agent if available"
            ],
            **kwargs
        )


class WorkflowError(Perfect21BaseException):
    """Workflow execution errors"""

    def __init__(self, message: str, workflow_name: str = None, step: str = None, **kwargs):
        self.workflow_name = workflow_name
        self.step = step
        super().__init__(
            message=message,
            category=ErrorCategory.WORKFLOW,
            severity=ErrorSeverity.HIGH,
            recovery_suggestions=[
                "Review workflow configuration",
                "Check step dependencies",
                "Restart workflow from last successful step"
            ],
            **kwargs
        )


class DatabaseError(Perfect21BaseException):
    """Database operation errors"""

    def __init__(self, message: str, operation: str = None, **kwargs):
        self.operation = operation
        super().__init__(
            message=message,
            category=ErrorCategory.DATABASE,
            severity=ErrorSeverity.HIGH,
            recovery_suggestions=[
                "Check database connection",
                "Verify database credentials",
                "Contact database administrator"
            ],
            **kwargs
        )


class FileSystemError(Perfect21BaseException):
    """File system operation errors"""

    def __init__(self, message: str, file_path: str = None, operation: str = None, **kwargs):
        self.file_path = file_path
        self.operation = operation
        super().__init__(
            message=message,
            category=ErrorCategory.FILE_SYSTEM,
            severity=ErrorSeverity.MEDIUM,
            recovery_suggestions=[
                "Check file permissions",
                "Verify file path exists",
                "Ensure sufficient disk space"
            ],
            **kwargs
        )


class ConfigurationError(Perfect21BaseException):
    """Configuration errors"""

    def __init__(self, message: str, config_key: str = None, **kwargs):
        self.config_key = config_key
        super().__init__(
            message=message,
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.HIGH,
            recovery_suggestions=[
                "Check configuration file",
                "Verify configuration values",
                "Reset to default configuration if needed"
            ],
            **kwargs
        )


class ErrorAggregator:
    """Aggregates multiple errors for parallel operations"""

    def __init__(self):
        self.errors: List[Perfect21BaseException] = []
        self.warnings: List[str] = []
        self.context: Dict[str, Any] = {}

    def add_error(self, error: Perfect21BaseException):
        """Add an error to the aggregator"""
        self.errors.append(error)

    def add_warning(self, warning: str):
        """Add a warning to the aggregator"""
        self.warnings.append(warning)

    def has_errors(self) -> bool:
        """Check if there are any errors"""
        return len(self.errors) > 0

    def has_critical_errors(self) -> bool:
        """Check if there are any critical errors"""
        return any(error.severity == ErrorSeverity.CRITICAL for error in self.errors)

    def get_error_summary(self) -> Dict[str, Any]:
        """Get a summary of all errors"""
        return {
            "total_errors": len(self.errors),
            "critical_errors": len([e for e in self.errors if e.severity == ErrorSeverity.CRITICAL]),
            "high_severity_errors": len([e for e in self.errors if e.severity == ErrorSeverity.HIGH]),
            "warnings": len(self.warnings),
            "error_categories": list(set(e.category.value for e in self.errors)),
            "errors": [error.to_dict() for error in self.errors],
            "warnings_list": self.warnings
        }

    def raise_if_errors(self):
        """Raise an aggregated exception if there are errors"""
        if self.has_errors():
            error_summary = self.get_error_summary()
            raise WorkflowError(
                message=f"Multiple errors occurred: {len(self.errors)} errors, {len(self.warnings)} warnings",
                context=ErrorContext(component="ErrorAggregator", operation="parallel_execution"),
                recovery_suggestions=[
                    "Review individual error details",
                    "Fix critical errors first",
                    "Retry failed operations"
                ]
            )


class RetryHandler:
    """Handles retry logic with exponential backoff"""

    def __init__(self, config: RetryConfig = None, logger: logging.Logger = None):
        self.config = config or RetryConfig()
        self.logger = logger or logging.getLogger(__name__)

    def __call__(self, func: Callable) -> Callable:
        """Decorator for retry functionality"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return self._execute_with_retry(func, *args, **kwargs)
        return wrapper

    def _execute_with_retry(self, func: Callable, *args, **kwargs):
        """Execute function with retry logic"""
        last_exception = None

        for attempt in range(1, self.config.max_attempts + 1):
            try:
                result = func(*args, **kwargs)
                if attempt > 1:
                    self.logger.info(f"Function {func.__name__} succeeded on attempt {attempt}")
                return result

            except self.config.retry_on_exceptions as e:
                last_exception = e
                self.logger.warning(f"Attempt {attempt} failed for {func.__name__}: {str(e)}")

                if attempt == self.config.max_attempts:
                    break

                delay = self._calculate_delay(attempt)
                self.logger.info(f"Retrying {func.__name__} in {delay:.2f} seconds...")
                time.sleep(delay)

        # All attempts failed
        self.logger.error(f"All {self.config.max_attempts} attempts failed for {func.__name__}")
        raise last_exception

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for exponential backoff"""
        delay = self.config.base_delay * (self.config.exponential_multiplier ** (attempt - 1))
        delay = min(delay, self.config.max_delay)

        if self.config.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)  # Add 0-50% jitter

        return delay


class ErrorLogger:
    """Centralized error logging"""

    def __init__(self, logger: logging.Logger = None):
        self.logger = logger or logging.getLogger(__name__)

    def log_error(self, error: Perfect21BaseException):
        """Log a Perfect21 error"""
        log_data = {
            "error_code": error.error_code,
            "category": error.category.value,
            "severity": error.severity.value,
            "error_message": error.message,  # Changed from 'message' to avoid conflict
            "timestamp": error.timestamp.isoformat()
        }

        if error.context:
            log_data["context"] = error.context.__dict__

        if error.original_exception:
            log_data["original_exception"] = str(error.original_exception)
            log_data["traceback"] = traceback.format_exc()

        # Choose log level based on severity - use simple string messages
        if error.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(f"CRITICAL ERROR: {error.message}")
        elif error.severity == ErrorSeverity.HIGH:
            self.logger.error(f"HIGH SEVERITY: {error.message}")
        elif error.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(f"MEDIUM SEVERITY: {error.message}")
        else:
            self.logger.info(f"LOW SEVERITY: {error.message}")

    def log_error_aggregation(self, aggregator: ErrorAggregator):
        """Log aggregated errors"""
        summary = aggregator.get_error_summary()
        self.logger.error(f"Error aggregation: {summary['total_errors']} errors")


class ErrorRecoveryManager:
    """Manages error recovery strategies"""

    def __init__(self):
        self.recovery_strategies: Dict[ErrorCategory, Callable] = {}
        self.logger = logging.getLogger(__name__)

    def register_recovery_strategy(self, category: ErrorCategory, strategy: Callable):
        """Register a recovery strategy for an error category"""
        self.recovery_strategies[category] = strategy

    def attempt_recovery(self, error: Perfect21BaseException) -> bool:
        """Attempt to recover from an error"""
        strategy = self.recovery_strategies.get(error.category)
        if not strategy:
            self.logger.warning(f"No recovery strategy for {error.category.value}")
            return False

        try:
            self.logger.info(f"Attempting recovery for {error.category.value} error")
            result = strategy(error)
            if result:
                self.logger.info(f"Recovery successful for {error.category.value}")
            return result
        except Exception as e:
            self.logger.error(f"Recovery failed for {error.category.value}: {str(e)}")
            return False


# Utility functions for error handling
def handle_exceptions(
    exceptions: tuple = (Exception,),
    category: ErrorCategory = ErrorCategory.SYSTEM,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    recovery_suggestions: List[str] = None
):
    """Decorator to handle exceptions and convert them to Perfect21 exceptions"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Perfect21BaseException:
                raise  # Re-raise Perfect21 exceptions as-is
            except exceptions as e:
                raise Perfect21BaseException(
                    message=f"Error in {func.__name__}: {str(e)}",
                    category=category,
                    severity=severity,
                    original_exception=e,
                    recovery_suggestions=recovery_suggestions or []
                ) from e
        return wrapper
    return decorator


def create_error_context(component: str, operation: str, **kwargs) -> ErrorContext:
    """Create an error context"""
    return ErrorContext(
        component=component,
        operation=operation,
        **kwargs
    )


def safe_execute(
    func: Callable,
    *args,
    default_return=None,
    log_errors: bool = True,
    error_logger: ErrorLogger = None,
    **kwargs
):
    """Safely execute a function and handle errors"""
    try:
        return func(*args, **kwargs)
    except Perfect21BaseException as e:
        if log_errors and error_logger:
            error_logger.log_error(e)
        return default_return
    except Exception as e:
        converted_error = Perfect21BaseException(
            message=f"Unexpected error in {func.__name__}: {str(e)}",
            original_exception=e,
            severity=ErrorSeverity.HIGH
        )
        if log_errors and error_logger:
            error_logger.log_error(converted_error)
        return default_return


# Global instances
_error_logger = ErrorLogger()
_recovery_manager = ErrorRecoveryManager()
_default_retry_handler = RetryHandler()

# Convenience functions
def log_error(error: Perfect21BaseException):
    """Log an error using the global error logger"""
    _error_logger.log_error(error)

def attempt_recovery(error: Perfect21BaseException) -> bool:
    """Attempt recovery using the global recovery manager"""
    return _recovery_manager.attempt_recovery(error)

def retry_on_failure(config: RetryConfig = None):
    """Decorator for retry functionality"""
    handler = RetryHandler(config) if config else _default_retry_handler
    return handler