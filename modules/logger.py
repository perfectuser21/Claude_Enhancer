#!/usr/bin/env python3
"""
Logger - 日志系统
Perfect21简化日志管理，集成错误处理系统
"""

import os
import logging
import logging.handlers
import json
import traceback
from typing import Optional, Dict, Any
from datetime import datetime

class Perfect21Logger:
    """Perfect21日志管理器"""

    def __init__(self, name: str = "Perfect21", log_dir: str = "logs"):
        self.name = name
        self.log_dir = log_dir
        self.logger = None
        self._setup_logger()

    def _setup_logger(self) -> None:
        """设置日志记录器"""
        # 创建日志目录
        os.makedirs(self.log_dir, exist_ok=True)

        # 创建logger
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.INFO)

        # 避免重复添加处理器
        if self.logger.handlers:
            return

        # 创建格式器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # 文件处理器 - 按大小轮转
        log_file = os.path.join(self.log_dir, f"{self.name.lower()}.log")
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Git操作专用日志
        git_log_file = os.path.join(self.log_dir, "git-workflow.log")
        git_handler = logging.handlers.RotatingFileHandler(
            git_log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        git_handler.setLevel(logging.INFO)
        git_handler.setFormatter(formatter)

        # 为Git操作创建专用logger
        git_logger = logging.getLogger("GitWorkflow")
        git_logger.setLevel(logging.INFO)
        git_logger.addHandler(git_handler)
        git_logger.addHandler(console_handler)  # 同时输出到控制台

    def info(self, message: str, extra_data: dict = None) -> None:
        """记录信息日志"""
        if extra_data:
            message = f"{message} | {extra_data}"
        self.logger.info(message)

    def error(self, message: str, exception: Exception = None, error_context: Dict[str, Any] = None) -> None:
        """记录错误日志，支持Perfect21异常"""
        try:
            # Import here to avoid circular imports
            from .exceptions import Perfect21BaseException, ErrorLogger

            if isinstance(exception, Perfect21BaseException):
                # Use Perfect21's error logging
                error_logger = ErrorLogger(self.logger)
                error_logger.log_error(exception)
            else:
                # Standard error logging
                if exception:
                    message = f"{message} | Exception: {exception}"
                    if error_context:
                        message += f" | Context: {json.dumps(error_context, default=str)}"
                    # Add traceback for debugging
                    self.logger.error(message)
                    if exception:
                        self.logger.debug(traceback.format_exc())
                else:
                    if error_context:
                        message += f" | Context: {json.dumps(error_context, default=str)}"
                    self.logger.error(message)
        except ImportError:
            # Fallback if exceptions module not available
            if exception:
                message = f"{message} | Exception: {exception}"
            self.logger.error(message)

    def warning(self, message: str) -> None:
        """记录警告日志"""
        self.logger.warning(message)

    def debug(self, message: str) -> None:
        """记录调试日志"""
        self.logger.debug(message)

    def log_git_operation(self, operation: str, details: dict = None) -> None:
        """记录Git操作"""
        git_logger = logging.getLogger("GitWorkflow")
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        log_message = f"[{timestamp}] Git操作: {operation}"
        if details:
            log_message += f" | 详情: {details}"

        git_logger.info(log_message)

    def log_subagent_call(self, agent_name: str, task: str, result: dict = None) -> None:
        """记录SubAgent调用"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        log_message = f"[{timestamp}] SubAgent调用: {agent_name} | 任务: {task}"
        if result:
            success = result.get('success', 'unknown')
            log_message += f" | 结果: {success}"

        self.logger.info(log_message)

    def get_recent_logs(self, lines: int = 50) -> list:
        """获取最近的日志条目"""
        try:
            log_file = os.path.join(self.log_dir, f"{self.name.lower()}.log")
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    all_lines = f.readlines()
                    return all_lines[-lines:] if len(all_lines) > lines else all_lines
            return []
        except Exception as e:
            self.error(f"读取日志文件失败: {e}", e)
            return []

    def log_parallel_error_aggregation(self, errors: list, context: Dict[str, Any] = None) -> None:
        """记录并行执行的错误聚合"""
        try:
            from .exceptions import ErrorAggregator, ErrorLogger

            aggregator = ErrorAggregator()
            for error in errors:
                if hasattr(error, 'add_error'):
                    aggregator.add_error(error)
                else:
                    # Convert to string if not a Perfect21 exception
                    aggregator.add_warning(str(error))

            if context:
                aggregator.context = context

            error_logger = ErrorLogger(self.logger)
            error_logger.log_error_aggregation(aggregator)

        except ImportError:
            # Fallback logging
            self.error(f"Parallel execution errors: {len(errors)} errors", context={'errors': [str(e) for e in errors]})

    def log_recovery_attempt(self, error_type: str, success: bool, details: Dict[str, Any] = None) -> None:
        """记录错误恢复尝试"""
        status = "成功" if success else "失败"
        message = f"错误恢复{status}: {error_type}"

        if details:
            message += f" | 详情: {json.dumps(details, default=str, ensure_ascii=False)}"

        if success:
            self.info(message)
        else:
            self.warning(message)

    def create_session_log(self, session_id: str, task_description: str) -> str:
        """创建会话日志文件"""
        session_dir = os.path.join(self.log_dir, "sessions")
        os.makedirs(session_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        session_file = os.path.join(session_dir, f"session_{session_id}_{timestamp}.log")

        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                f.write(f"Perfect21会话日志\n")
                f.write(f"会话ID: {session_id}\n")
                f.write(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"任务描述: {task_description}\n")
                f.write(f"{'='*50}\n\n")

            self.info(f"创建会话日志: {session_file}")
            return session_file

        except Exception as e:
            self.error(f"创建会话日志失败: {e}")
            return ""

# 全局日志实例
perfect21_logger = Perfect21Logger()

# 便捷函数
def log_info(message: str, extra_data: dict = None) -> None:
    """记录信息日志"""
    perfect21_logger.info(message, extra_data)

def log_error(message: str, exception: Exception = None, error_context: Dict[str, Any] = None) -> None:
    """记录错误日志"""
    perfect21_logger.error(message, exception, error_context)

def log_git_operation(operation: str, details: dict = None) -> None:
    """记录Git操作"""
    perfect21_logger.log_git_operation(operation, details)

def log_subagent_call(agent_name: str, task: str, result: dict = None) -> None:
    """记录SubAgent调用"""
    perfect21_logger.log_subagent_call(agent_name, task, result)

def log_warning(message: str) -> None:
    """记录警告日志"""
    perfect21_logger.warning(message)

def setup_logging(log_level: str = "INFO", log_file: str = None) -> None:
    """设置日志系统"""
    # 设置日志级别
    level = getattr(logging, log_level.upper(), logging.INFO)
    perfect21_logger.logger.setLevel(level)

    # 如果指定了日志文件，更新文件处理器
    if log_file:
        # 创建目录
        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        # 更新文件处理器
        for handler in perfect21_logger.logger.handlers[:]:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                perfect21_logger.logger.removeHandler(handler)

        # 添加新的文件处理器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        perfect21_logger.logger.addHandler(file_handler)