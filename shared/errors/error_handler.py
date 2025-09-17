#!/usr/bin/env python3
"""
统一错误处理系统
提供错误分类、处理、恢复和监控功能
"""

import logging
import traceback
from typing import Dict, Any, Optional, List, Type
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import json

logger = logging.getLogger("ErrorHandler")


class ErrorSeverity(Enum):
    """错误严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """错误类别"""
    SYSTEM = "system"
    CONFIGURATION = "configuration"
    GIT_OPERATION = "git_operation"
    CLI_COMMAND = "cli_command"
    PARALLEL_EXECUTION = "parallel_execution"
    NETWORK = "network"
    PERMISSION = "permission"
    VALIDATION = "validation"
    TIMEOUT = "timeout"


@dataclass
class ErrorContext:
    """错误上下文信息"""
    timestamp: str
    component: str
    operation: str
    user_action: Optional[str] = None
    environment: Optional[Dict[str, Any]] = None
    additional_data: Optional[Dict[str, Any]] = None


@dataclass
class ErrorSolution:
    """错误解决方案"""
    title: str
    description: str
    steps: List[str]
    auto_fix: bool = False
    fix_function: Optional[callable] = None


class Perfect21Error(Exception):
    """Perfect21基础异常类"""

    def __init__(
        self,
        message: str,
        error_code: str = None,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[ErrorContext] = None,
        details: Optional[Dict[str, Any]] = None,
        solutions: Optional[List[ErrorSolution]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or 'UNKNOWN_ERROR'
        self.category = category
        self.severity = severity
        self.context = context
        self.details = details or {}
        self.solutions = solutions or []
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'message': self.message,
            'error_code': self.error_code,
            'category': self.category.value,
            'severity': self.severity.value,
            'timestamp': self.timestamp,
            'context': self.context.__dict__ if self.context else None,
            'details': self.details,
            'solutions': [
                {
                    'title': sol.title,
                    'description': sol.description,
                    'steps': sol.steps,
                    'auto_fix': sol.auto_fix
                }
                for sol in self.solutions
            ]
        }


class GitOperationError(Perfect21Error):
    """Git操作异常"""

    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('category', ErrorCategory.GIT_OPERATION)
        kwargs.setdefault('error_code', 'GIT_OPERATION_ERROR')
        super().__init__(message, **kwargs)


class CLICommandError(Perfect21Error):
    """CLI命令异常"""

    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('category', ErrorCategory.CLI_COMMAND)
        kwargs.setdefault('error_code', 'CLI_COMMAND_ERROR')
        super().__init__(message, **kwargs)


class ParallelExecutionError(Perfect21Error):
    """并行执行异常"""

    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('category', ErrorCategory.PARALLEL_EXECUTION)
        kwargs.setdefault('error_code', 'PARALLEL_EXECUTION_ERROR')
        super().__init__(message, **kwargs)


class ConfigurationError(Perfect21Error):
    """配置异常"""

    def __init__(self, message: str, **kwargs):
        kwargs.setdefault('category', ErrorCategory.CONFIGURATION)
        kwargs.setdefault('error_code', 'CONFIGURATION_ERROR')
        super().__init__(message, **kwargs)


class ErrorHandler:
    """统一错误处理器"""

    def __init__(self):
        """初始化错误处理器"""
        self.error_solutions = self._init_error_solutions()
        self.error_stats = {
            'total_errors': 0,
            'by_category': {},
            'by_severity': {},
            'recent_errors': []
        }

    def _init_error_solutions(self) -> Dict[str, List[ErrorSolution]]:
        """初始化错误解决方案"""
        return {
            'GIT_OPERATION_ERROR': [
                ErrorSolution(
                    title="检查Git仓库状态",
                    description="Git操作失败，可能是仓库状态异常",
                    steps=[
                        "运行 'git status' 检查仓库状态",
                        "确保当前目录是Git仓库",
                        "检查文件权限",
                        "尝试 'git fetch' 更新远程信息"
                    ]
                ),
                ErrorSolution(
                    title="检查网络连接",
                    description="如果是推送/拉取操作失败",
                    steps=[
                        "检查网络连接",
                        "验证远程仓库地址",
                        "检查SSH密钥或访问令牌",
                        "尝试使用 'git remote -v' 检查远程配置"
                    ]
                )
            ],
            'CLI_COMMAND_ERROR': [
                ErrorSolution(
                    title="检查命令参数",
                    description="CLI命令执行失败，可能是参数错误",
                    steps=[
                        "使用 '--help' 查看命令帮助",
                        "检查必需参数是否提供",
                        "验证参数格式是否正确",
                        "查看详细错误信息"
                    ]
                )
            ],
            'PARALLEL_EXECUTION_ERROR': [
                ErrorSolution(
                    title="检查系统资源",
                    description="并行执行失败，可能是资源不足",
                    steps=[
                        "检查系统内存使用情况",
                        "减少并行执行的任务数量",
                        "检查磁盘空间",
                        "重启Perfect21服务"
                    ],
                    auto_fix=True,
                    fix_function=self._auto_fix_parallel_execution
                )
            ],
            'CONFIGURATION_ERROR': [
                ErrorSolution(
                    title="重置配置",
                    description="配置文件可能损坏或格式错误",
                    steps=[
                        "备份当前配置文件",
                        "使用默认配置",
                        "重新生成配置文件",
                        "验证配置格式"
                    ],
                    auto_fix=True,
                    fix_function=self._auto_fix_configuration
                )
            ]
        }

    def handle_error(self, error: Exception, context: Optional[ErrorContext] = None) -> Dict[str, Any]:
        """
        处理错误

        Args:
            error: 异常对象
            context: 错误上下文

        Returns:
            错误处理结果
        """
        try:
            # 更新统计
            self._update_error_stats(error)

            # 如果是Perfect21错误，直接处理
            if isinstance(error, Perfect21Error):
                return self._handle_perfect21_error(error, context)

            # 转换普通异常为Perfect21错误
            perfect21_error = self._convert_to_perfect21_error(error, context)
            return self._handle_perfect21_error(perfect21_error, context)

        except Exception as e:
            logger.error(f"错误处理器异常: {e}", exc_info=True)
            return self._create_fallback_response(error)

    def _handle_perfect21_error(self, error: Perfect21Error, context: Optional[ErrorContext]) -> Dict[str, Any]:
        """处理Perfect21错误"""
        # 记录错误
        self._log_error(error, context)

        # 获取解决方案
        solutions = self._get_solutions_for_error(error)
        error.solutions.extend(solutions)

        # 尝试自动修复
        auto_fix_result = None
        if any(sol.auto_fix for sol in error.solutions):
            auto_fix_result = self._attempt_auto_fix(error)

        return {
            'success': False,
            'error_code': error.error_code,
            'message': error.message,
            'category': error.category.value,
            'severity': error.severity.value,
            'timestamp': error.timestamp,
            'context': error.context.__dict__ if error.context else context.__dict__ if context else None,
            'details': error.details,
            'solutions': [sol.__dict__ for sol in error.solutions],
            'auto_fix_attempted': auto_fix_result is not None,
            'auto_fix_success': auto_fix_result.get('success', False) if auto_fix_result else False,
            'recovery_suggestions': self._get_recovery_suggestions(error)
        }

    def _convert_to_perfect21_error(self, error: Exception, context: Optional[ErrorContext]) -> Perfect21Error:
        """转换普通异常为Perfect21错误"""
        error_type = type(error).__name__
        error_message = str(error)

        # 根据异常类型确定类别和严重程度
        if 'subprocess' in error_message.lower() or 'git' in error_message.lower():
            category = ErrorCategory.GIT_OPERATION
            error_code = 'GIT_OPERATION_ERROR'
        elif 'permission' in error_message.lower() or 'access' in error_message.lower():
            category = ErrorCategory.PERMISSION
            error_code = 'PERMISSION_ERROR'
        elif 'timeout' in error_message.lower():
            category = ErrorCategory.TIMEOUT
            error_code = 'TIMEOUT_ERROR'
        elif 'network' in error_message.lower() or 'connection' in error_message.lower():
            category = ErrorCategory.NETWORK
            error_code = 'NETWORK_ERROR'
        else:
            category = ErrorCategory.SYSTEM
            error_code = 'SYSTEM_ERROR'

        # 确定严重程度
        if error_type in ['SystemExit', 'KeyboardInterrupt']:
            severity = ErrorSeverity.LOW
        elif error_type in ['MemoryError', 'OSError']:
            severity = ErrorSeverity.CRITICAL
        elif error_type in ['TimeoutError', 'ConnectionError']:
            severity = ErrorSeverity.HIGH
        else:
            severity = ErrorSeverity.MEDIUM

        return Perfect21Error(
            message=f"{error_type}: {error_message}",
            error_code=error_code,
            category=category,
            severity=severity,
            context=context,
            details={
                'original_type': error_type,
                'traceback': traceback.format_exc()
            }
        )

    def _get_solutions_for_error(self, error: Perfect21Error) -> List[ErrorSolution]:
        """获取错误的解决方案"""
        solutions = []

        # 从预定义解决方案中查找
        if error.error_code in self.error_solutions:
            solutions.extend(self.error_solutions[error.error_code])

        # 基于错误类别添加通用解决方案
        if error.category == ErrorCategory.GIT_OPERATION and not solutions:
            solutions.append(ErrorSolution(
                title="通用Git问题排查",
                description="Git操作通用故障排除",
                steps=[
                    "检查Git仓库状态",
                    "验证权限设置",
                    "检查网络连接",
                    "尝试重新初始化"
                ]
            ))

        return solutions

    def _attempt_auto_fix(self, error: Perfect21Error) -> Optional[Dict[str, Any]]:
        """尝试自动修复"""
        for solution in error.solutions:
            if solution.auto_fix and solution.fix_function:
                try:
                    logger.info(f"尝试自动修复: {solution.title}")
                    result = solution.fix_function(error)
                    if result.get('success'):
                        logger.info(f"自动修复成功: {solution.title}")
                        return result
                except Exception as e:
                    logger.warning(f"自动修复失败: {e}")

        return None

    def _auto_fix_parallel_execution(self, error: Perfect21Error) -> Dict[str, Any]:
        """自动修复并行执行问题"""
        try:
            # 清理并行执行状态
            from modules.parallel_monitor import get_global_monitor

            monitor = get_global_monitor()
            monitor.clear_failed_tasks()

            return {
                'success': True,
                'message': '已清理失败的并行任务',
                'actions': ['清理任务队列', '重置监控状态']
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _auto_fix_configuration(self, error: Perfect21Error) -> Dict[str, Any]:
        """自动修复配置问题"""
        try:
            from infrastructure.config.config_manager import get_config_manager

            config_manager = get_config_manager()

            # 重新加载配置
            if config_manager.reload():
                return {
                    'success': True,
                    'message': '配置已重新加载',
                    'actions': ['重新加载配置文件']
                }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _get_recovery_suggestions(self, error: Perfect21Error) -> List[str]:
        """获取恢复建议"""
        suggestions = []

        if error.severity == ErrorSeverity.CRITICAL:
            suggestions.extend([
                "立即停止当前操作",
                "检查系统资源",
                "联系系统管理员"
            ])
        elif error.category == ErrorCategory.GIT_OPERATION:
            suggestions.extend([
                "检查Git仓库状态",
                "验证文件权限",
                "尝试重新执行操作"
            ])
        elif error.category == ErrorCategory.CLI_COMMAND:
            suggestions.extend([
                "检查命令语法",
                "使用--help查看帮助",
                "检查参数格式"
            ])

        return suggestions

    def _log_error(self, error: Perfect21Error, context: Optional[ErrorContext]) -> None:
        """记录错误"""
        log_data = {
            'error_code': error.error_code,
            'message': error.message,
            'category': error.category.value,
            'severity': error.severity.value,
            'context': context.__dict__ if context else None
        }

        if error.severity in [ErrorSeverity.CRITICAL, ErrorSeverity.HIGH]:
            logger.error(f"Perfect21错误: {json.dumps(log_data, indent=2)}")
        else:
            logger.warning(f"Perfect21错误: {json.dumps(log_data, indent=2)}")

    def _update_error_stats(self, error: Exception) -> None:
        """更新错误统计"""
        self.error_stats['total_errors'] += 1

        if isinstance(error, Perfect21Error):
            category = error.category.value
            severity = error.severity.value
        else:
            category = 'unknown'
            severity = 'medium'

        # 更新分类统计
        self.error_stats['by_category'][category] = \
            self.error_stats['by_category'].get(category, 0) + 1

        self.error_stats['by_severity'][severity] = \
            self.error_stats['by_severity'].get(severity, 0) + 1

        # 保留最近的错误
        recent_error = {
            'timestamp': datetime.now().isoformat(),
            'type': type(error).__name__,
            'message': str(error)[:200],  # 限制长度
            'category': category,
            'severity': severity
        }

        self.error_stats['recent_errors'].append(recent_error)

        # 只保留最近50个错误
        if len(self.error_stats['recent_errors']) > 50:
            self.error_stats['recent_errors'] = self.error_stats['recent_errors'][-50:]

    def _create_fallback_response(self, error: Exception) -> Dict[str, Any]:
        """创建后备响应"""
        return {
            'success': False,
            'error_code': 'INTERNAL_ERROR',
            'message': f"内部错误: {str(error)}",
            'category': 'system',
            'severity': 'high',
            'timestamp': datetime.now().isoformat(),
            'details': {
                'type': type(error).__name__,
                'traceback': traceback.format_exc()
            },
            'solutions': [
                {
                    'title': '重启应用',
                    'description': '尝试重启Perfect21应用',
                    'steps': ['保存当前工作', '重启应用', '重新尝试操作'],
                    'auto_fix': False
                }
            ]
        }

    def get_error_stats(self) -> Dict[str, Any]:
        """获取错误统计"""
        return self.error_stats.copy()

    def clear_error_stats(self) -> None:
        """清空错误统计"""
        self.error_stats = {
            'total_errors': 0,
            'by_category': {},
            'by_severity': {},
            'recent_errors': []
        }


# 全局错误处理器实例
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """获取错误处理器实例（单例模式）"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler


def handle_error(error: Exception, context: Optional[ErrorContext] = None) -> Dict[str, Any]:
    """便捷函数：处理错误"""
    handler = get_error_handler()
    return handler.handle_error(error, context)


def create_error_context(component: str, operation: str, **kwargs) -> ErrorContext:
    """便捷函数：创建错误上下文"""
    return ErrorContext(
        timestamp=datetime.now().isoformat(),
        component=component,
        operation=operation,
        user_action=kwargs.get('user_action'),
        environment=kwargs.get('environment'),
        additional_data=kwargs.get('additional_data')
    )