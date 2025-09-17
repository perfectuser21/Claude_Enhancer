#!/usr/bin/env python3
"""
Perfect21 Error Handling Integration
Integrates the comprehensive error handling system throughout Perfect21
"""

import logging
import functools
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime

from .exceptions import (
    Perfect21BaseException, GitOperationError, AgentExecutionError,
    WorkflowError, ValidationError, NetworkError, AuthenticationError,
    ErrorAggregator, ErrorLogger, ErrorRecoveryManager, RetryHandler,
    ErrorSeverity, ErrorCategory, ErrorContext, RetryConfig,
    handle_exceptions, safe_execute, retry_on_failure
)
from .logger import Perfect21Logger

logger = logging.getLogger(__name__)


class Perfect21ErrorHandler:
    """Perfect21 central error handler"""

    def __init__(self):
        self.error_logger = ErrorLogger()
        self.recovery_manager = ErrorRecoveryManager()
        self.aggregator = ErrorAggregator()
        self.perfect21_logger = Perfect21Logger("ErrorHandler")
        self._setup_recovery_strategies()

    def _setup_recovery_strategies(self):
        """Setup default recovery strategies"""

        def git_operation_recovery(error: GitOperationError) -> bool:
            """Recovery strategy for Git operations"""
            try:
                logger.info(f"Attempting Git operation recovery: {error.git_command}")

                # Basic Git recovery strategies
                if "permission denied" in str(error.message).lower():
                    self.perfect21_logger.warning("Git permission error - suggest checking SSH keys")
                    return False

                if "not a git repository" in str(error.message).lower():
                    self.perfect21_logger.warning("Not a git repository - suggest git init")
                    return False

                if "conflict" in str(error.message).lower():
                    self.perfect21_logger.warning("Git conflict detected - suggest manual resolution")
                    return False

                return False
            except Exception as e:
                logger.error(f"Git recovery strategy failed: {e}")
                return False

        def agent_execution_recovery(error: AgentExecutionError) -> bool:
            """Recovery strategy for Agent execution"""
            try:
                logger.info(f"Attempting agent execution recovery: {error.agent_name}")

                # Agent-specific recovery
                if error.agent_name and "timeout" in str(error.message).lower():
                    self.perfect21_logger.info(f"Agent {error.agent_name} timeout - retry with extended timeout")
                    return True  # Indicate retry should be attempted

                if "network" in str(error.message).lower():
                    self.perfect21_logger.info("Network error in agent execution - retry after delay")
                    return True

                return False
            except Exception as e:
                logger.error(f"Agent recovery strategy failed: {e}")
                return False

        def workflow_recovery(error: WorkflowError) -> bool:
            """Recovery strategy for Workflow errors"""
            try:
                logger.info(f"Attempting workflow recovery: {error.workflow_name}")

                if error.step:
                    self.perfect21_logger.info(f"Workflow failure at step: {error.step}")
                    # Could implement step rollback here

                return False
            except Exception as e:
                logger.error(f"Workflow recovery strategy failed: {e}")
                return False

        # Register recovery strategies
        self.recovery_manager.register_recovery_strategy(ErrorCategory.GIT_OPERATION, git_operation_recovery)
        self.recovery_manager.register_recovery_strategy(ErrorCategory.AGENT_EXECUTION, agent_execution_recovery)
        self.recovery_manager.register_recovery_strategy(ErrorCategory.WORKFLOW, workflow_recovery)

    def handle_error(self, error: Perfect21BaseException, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Handle a Perfect21 error"""

        # Log the error
        self.error_logger.log_error(error)

        # Add to aggregator if it's part of a batch operation
        if context and context.get("batch_operation"):
            self.aggregator.add_error(error)

        # Attempt recovery
        recovery_attempted = False
        recovery_successful = False

        if error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            recovery_attempted = True
            recovery_successful = self.recovery_manager.attempt_recovery(error)

            self.perfect21_logger.log_recovery_attempt(
                error_type=error.error_code,
                success=recovery_successful,
                details={
                    "category": error.category.value,
                    "severity": error.severity.value,
                    "context": context
                }
            )

        return {
            "error_handled": True,
            "error_code": error.error_code,
            "severity": error.severity.value,
            "category": error.category.value,
            "user_message": error.user_friendly_message,
            "recovery_attempted": recovery_attempted,
            "recovery_successful": recovery_successful,
            "recovery_suggestions": error.recovery_suggestions,
            "timestamp": error.timestamp.isoformat()
        }

    def handle_multiple_errors(self, errors: List[Perfect21BaseException]) -> Dict[str, Any]:
        """Handle multiple errors from parallel operations"""

        # Reset aggregator
        self.aggregator = ErrorAggregator()

        # Add all errors
        for error in errors:
            self.aggregator.add_error(error)
            self.error_logger.log_error(error)

        # Log aggregation
        self.error_logger.log_error_aggregation(self.aggregator)

        # Get summary
        summary = self.aggregator.get_error_summary()

        # Attempt recovery for critical errors
        recovery_results = []
        for error in errors:
            if error.severity == ErrorSeverity.CRITICAL:
                result = self.recovery_manager.attempt_recovery(error)
                recovery_results.append({
                    "error_code": error.error_code,
                    "recovery_successful": result
                })

        return {
            "multiple_errors_handled": True,
            "error_summary": summary,
            "recovery_results": recovery_results,
            "recommendations": self._generate_batch_recovery_recommendations(errors)
        }

    def _generate_batch_recovery_recommendations(self, errors: List[Perfect21BaseException]) -> List[str]:
        """Generate recovery recommendations for batch errors"""
        recommendations = []

        # Group by category
        error_categories = {}
        for error in errors:
            category = error.category.value
            if category not in error_categories:
                error_categories[category] = []
            error_categories[category].append(error)

        # Generate category-specific recommendations
        if ErrorCategory.AGENT_EXECUTION.value in error_categories:
            agent_errors = error_categories[ErrorCategory.AGENT_EXECUTION.value]
            recommendations.append(f"🤖 Review {len(agent_errors)} agent execution failures")
            recommendations.append("🔄 Consider retrying failed agents with modified parameters")

        if ErrorCategory.NETWORK.value in error_categories:
            network_errors = error_categories[ErrorCategory.NETWORK.value]
            recommendations.append(f"🌐 Check network connectivity ({len(network_errors)} network errors)")

        if ErrorCategory.TIMEOUT.value in error_categories:
            timeout_errors = error_categories[ErrorCategory.TIMEOUT.value]
            recommendations.append(f"⏱️ Increase timeout values ({len(timeout_errors)} timeout errors)")

        # Critical error handling
        critical_errors = [e for e in errors if e.severity == ErrorSeverity.CRITICAL]
        if critical_errors:
            recommendations.append(f"🚨 Address {len(critical_errors)} critical errors immediately")

        # General recommendations
        if len(errors) > 10:
            recommendations.append("📊 Analyze error patterns for systematic issues")

        recommendations.append("📝 Review error logs for detailed information")

        return recommendations

    def create_error_context(self, component: str, operation: str, **kwargs) -> ErrorContext:
        """Create error context for Perfect21 operations"""
        return ErrorContext(
            component=component,
            operation=operation,
            timestamp=datetime.now(),
            **kwargs
        )

    def wrap_function_with_error_handling(
        self,
        func: Callable,
        component: str,
        operation: str,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        retry_config: RetryConfig = None
    ) -> Callable:
        """Wrap a function with comprehensive error handling"""

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            context = self.create_error_context(component, operation)

            try:
                # Apply retry if configured
                if retry_config:
                    retry_handler = RetryHandler(retry_config)
                    return retry_handler._execute_with_retry(func, *args, **kwargs)
                else:
                    return func(*args, **kwargs)

            except Perfect21BaseException as e:
                # Re-raise Perfect21 exceptions with additional context
                if not e.context:
                    e.context = context
                result = self.handle_error(e)
                raise e

            except Exception as e:
                # Convert to Perfect21 exception
                perfect21_error = Perfect21BaseException(
                    message=f"Error in {component}.{operation}: {str(e)}",
                    category=category,
                    severity=severity,
                    context=context,
                    original_exception=e,
                    recovery_suggestions=[
                        f"Check {component} configuration",
                        f"Verify {operation} parameters",
                        "Review system logs for details"
                    ]
                )

                result = self.handle_error(perfect21_error)
                raise perfect21_error from e

        return wrapper

    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error statistics"""
        if not self.aggregator.has_errors():
            return {
                "total_errors": 0,
                "error_distribution": {},
                "severity_distribution": {},
                "recommendations": ["No errors detected - system running smoothly"]
            }

        summary = self.aggregator.get_error_summary()

        # Add additional analysis
        severity_distribution = {}
        category_distribution = {}

        for error in self.aggregator.errors:
            # Severity distribution
            severity = error.severity.value
            if severity not in severity_distribution:
                severity_distribution[severity] = 0
            severity_distribution[severity] += 1

            # Category distribution
            category = error.category.value
            if category not in category_distribution:
                category_distribution[category] = 0
            category_distribution[category] += 1

        summary.update({
            "severity_distribution": severity_distribution,
            "category_distribution": category_distribution,
            "most_common_severity": max(severity_distribution.items(), key=lambda x: x[1])[0] if severity_distribution else None,
            "most_common_category": max(category_distribution.items(), key=lambda x: x[1])[0] if category_distribution else None
        })

        return summary


# Global error handler instance
_error_handler = None

def get_error_handler() -> Perfect21ErrorHandler:
    """Get the global error handler instance"""
    global _error_handler
    if _error_handler is None:
        _error_handler = Perfect21ErrorHandler()
    return _error_handler

def handle_perfect21_error(error: Perfect21BaseException, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Convenience function to handle a Perfect21 error"""
    handler = get_error_handler()
    return handler.handle_error(error, context)

def handle_multiple_perfect21_errors(errors: List[Perfect21BaseException]) -> Dict[str, Any]:
    """Convenience function to handle multiple Perfect21 errors"""
    handler = get_error_handler()
    return handler.handle_multiple_errors(errors)

def with_error_handling(
    component: str,
    operation: str,
    category: ErrorCategory = ErrorCategory.SYSTEM,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    retry_config: RetryConfig = None
):
    """Decorator for adding comprehensive error handling to functions"""
    def decorator(func: Callable) -> Callable:
        handler = get_error_handler()
        return handler.wrap_function_with_error_handling(
            func, component, operation, category, severity, retry_config
        )
    return decorator

# Convenience decorators for common operations
def with_git_error_handling(operation: str):
    """Decorator for Git operations"""
    return with_error_handling(
        component="GitWorkflow",
        operation=operation,
        category=ErrorCategory.GIT_OPERATION,
        severity=ErrorSeverity.MEDIUM,
        retry_config=RetryConfig(max_attempts=2, base_delay=1.0)
    )

def with_agent_error_handling(agent_name: str, operation: str):
    """Decorator for Agent operations"""
    return with_error_handling(
        component=f"Agent_{agent_name}",
        operation=operation,
        category=ErrorCategory.AGENT_EXECUTION,
        severity=ErrorSeverity.HIGH,
        retry_config=RetryConfig(max_attempts=3, base_delay=2.0, max_delay=30.0)
    )

def with_workflow_error_handling(workflow_name: str, step: str):
    """Decorator for Workflow operations"""
    return with_error_handling(
        component=f"Workflow_{workflow_name}",
        operation=step,
        category=ErrorCategory.WORKFLOW,
        severity=ErrorSeverity.HIGH,
        retry_config=RetryConfig(max_attempts=2, base_delay=3.0)
    )