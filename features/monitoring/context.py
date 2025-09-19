#!/usr/bin/env python3
"""
Perfect21 错误上下文管理
提供错误上下文收集和丰富功能
"""

import os
import sys
import traceback
import platform
import threading
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import psutil

from .exceptions import Perfect21Exception


class ErrorContext:
    """错误上下文"""

    def __init__(self):
        self.timestamp = datetime.now()
        self.thread_id = threading.get_ident()
        self.process_id = os.getpid()
        self.system_info = self._collect_system_info()
        self.stack_trace = traceback.format_stack()
        self.environment = dict(os.environ)
        self.custom_data: Dict[str, Any] = {}

    def _collect_system_info(self) -> Dict[str, Any]:
        """收集系统信息"""
        try:
            return {
                'platform': platform.platform(),
                'python_version': sys.version,
                'cpu_count': os.cpu_count(),
                'memory_total': psutil.virtual_memory().total,
                'memory_available': psutil.virtual_memory().available,
                'disk_usage': {
                    'total': psutil.disk_usage('/').total,
                    'free': psutil.disk_usage('/').free
                }
            }
        except Exception:
            return {'error': 'Failed to collect system info'}

    def add_custom_data(self, key: str, value: Any):
        """添加自定义数据"""
        self.custom_data[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'thread_id': self.thread_id,
            'process_id': self.process_id,
            'system_info': self.system_info,
            'stack_trace': self.stack_trace,
            'environment': {k: v for k, v in self.environment.items()
                          if not k.startswith('SECRET_') and not k.startswith('PASSWORD_')},
            'custom_data': self.custom_data
        }


class ErrorEnricher:
    """错误丰富器 - 为错误添加上下文信息"""

    def __init__(self):
        self.enrichers: List[Callable[[Perfect21Exception, Dict[str, Any]], Dict[str, Any]]] = []
        self._register_default_enrichers()

    def _register_default_enrichers(self):
        """注册默认丰富器"""
        self.enrichers.extend([
            self._enrich_with_git_info,
            self._enrich_with_perfect21_context,
            self._enrich_with_agent_context,
            self._enrich_with_performance_metrics
        ])

    def register_enricher(
        self,
        enricher: Callable[[Perfect21Exception, Dict[str, Any]], Dict[str, Any]]
    ):
        """注册自定义丰富器"""
        self.enrichers.append(enricher)

    def enrich(
        self,
        exception: Perfect21Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """丰富错误上下文"""
        enriched_context = context.copy() if context else {}

        # 添加基础错误上下文
        error_context = ErrorContext()
        enriched_context['error_context'] = error_context.to_dict()

        # 运行所有丰富器
        for enricher in self.enrichers:
            try:
                additional_context = enricher(exception, enriched_context)
                if additional_context:
                    enriched_context.update(additional_context)
            except Exception as e:
                # 丰富器失败不应该影响错误处理
                enriched_context['enricher_errors'] = enriched_context.get('enricher_errors', [])
                enriched_context['enricher_errors'].append({
                    'enricher': enricher.__name__,
                    'error': str(e)
                })

        return enriched_context

    def _enrich_with_git_info(
        self,
        exception: Perfect21Exception,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """添加Git信息"""
        try:
            import subprocess

            git_info = {}

            # 获取当前分支
            try:
                branch = subprocess.check_output(
                    ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                    cwd=os.getcwd(),
                    stderr=subprocess.DEVNULL
                ).decode().strip()
                git_info['current_branch'] = branch
            except subprocess.CalledProcessError:
                pass

            # 获取最新提交
            try:
                commit = subprocess.check_output(
                    ['git', 'rev-parse', 'HEAD'],
                    cwd=os.getcwd(),
                    stderr=subprocess.DEVNULL
                ).decode().strip()
                git_info['latest_commit'] = commit
            except subprocess.CalledProcessError:
                pass

            # 获取仓库状态
            try:
                status = subprocess.check_output(
                    ['git', 'status', '--porcelain'],
                    cwd=os.getcwd(),
                    stderr=subprocess.DEVNULL
                ).decode().strip()
                git_info['has_uncommitted_changes'] = bool(status)
            except subprocess.CalledProcessError:
                pass

            return {'git_info': git_info} if git_info else {}

        except Exception:
            return {}

    def _enrich_with_perfect21_context(
        self,
        exception: Perfect21Exception,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """添加Perfect21上下文信息"""
        try:
            perfect21_context = {}

            # 检查是否在Perfect21环境中
            if os.path.exists('main/perfect21.py'):
                perfect21_context['in_perfect21_project'] = True

                # 获取版本信息
                try:
                    from modules.config import config
                    perfect21_context['version'] = config.get('perfect21.version', 'unknown')
                    perfect21_context['mode'] = config.get('perfect21.mode', 'unknown')
                except ImportError:
                    pass

                # 检查核心agents
                if os.path.exists('core/claude-code-unified-agents'):
                    perfect21_context['has_core_agents'] = True

                # 检查功能模块
                features_dir = 'features'
                if os.path.exists(features_dir):
                    features = [d for d in os.listdir(features_dir)
                              if os.path.isdir(os.path.join(features_dir, d))]
                    perfect21_context['available_features'] = features

            return {'perfect21_context': perfect21_context} if perfect21_context else {}

        except Exception:
            return {}

    def _enrich_with_agent_context(
        self,
        exception: Perfect21Exception,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """添加Agent上下文信息"""
        try:
            agent_context = {}

            # 从上下文中提取agent信息
            if 'agent_name' in context:
                agent_context['agent_name'] = context['agent_name']

            if 'task' in context:
                agent_context['task'] = context['task']

            if 'function' in context:
                agent_context['function'] = context['function']

            # 检查是否有agent调用栈
            stack_info = traceback.extract_stack()
            agent_calls = []
            for frame in stack_info:
                if 'agent' in frame.filename.lower() or 'subagent' in frame.filename.lower():
                    agent_calls.append({
                        'file': frame.filename,
                        'line': frame.lineno,
                        'function': frame.name
                    })

            if agent_calls:
                agent_context['agent_call_stack'] = agent_calls

            return {'agent_context': agent_context} if agent_context else {}

        except Exception:
            return {}

    def _enrich_with_performance_metrics(
        self,
        exception: Perfect21Exception,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """添加性能指标"""
        try:
            import psutil

            performance_metrics = {
                'cpu_percent': psutil.cpu_percent(),
                'memory_percent': psutil.virtual_memory().percent,
                'load_average': os.getloadavg() if hasattr(os, 'getloadavg') else None,
                'disk_io': psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else None,
                'network_io': psutil.net_io_counters()._asdict() if psutil.net_io_counters() else None
            }

            # 检查进程特定的指标
            current_process = psutil.Process()
            performance_metrics['process'] = {
                'cpu_percent': current_process.cpu_percent(),
                'memory_info': current_process.memory_info()._asdict(),
                'num_threads': current_process.num_threads(),
                'num_fds': current_process.num_fds() if hasattr(current_process, 'num_fds') else None
            }

            return {'performance_metrics': performance_metrics}

        except Exception:
            return {}


class ContextualErrorHandler:
    """上下文化错误处理器"""

    def __init__(self):
        self.context_stack: List[Dict[str, Any]] = []
        self.enricher = ErrorEnricher()

    def push_context(self, context: Dict[str, Any]):
        """推入上下文"""
        self.context_stack.append(context)

    def pop_context(self):
        """弹出上下文"""
        if self.context_stack:
            return self.context_stack.pop()
        return {}

    def get_current_context(self) -> Dict[str, Any]:
        """获取当前上下文"""
        merged_context = {}
        for context in self.context_stack:
            merged_context.update(context)
        return merged_context

    def handle_with_context(self, exception: Exception) -> Dict[str, Any]:
        """带上下文处理异常"""
        current_context = self.get_current_context()

        # 转换为Perfect21异常
        if not isinstance(exception, Perfect21Exception):
            from .exceptions import ExceptionConverter
            exception = ExceptionConverter.convert(exception, current_context)

        # 丰富上下文
        enriched_context = self.enricher.enrich(exception, current_context)

        return enriched_context


class ErrorContextDecorator:
    """错误上下文装饰器"""

    def __init__(self, context: Dict[str, Any]):
        self.context = context

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            handler = ContextualErrorHandler()
            handler.push_context(self.context)
            try:
                return func(*args, **kwargs)
            except Exception as e:
                enriched_context = handler.handle_with_context(e)
                # 重新抛出异常，但保留上下文信息
                if hasattr(e, 'context'):
                    e.context.update(enriched_context)
                else:
                    # 如果原异常没有context属性，创建新的Perfect21异常
                    from .exceptions import ExceptionConverter
                    e = ExceptionConverter.convert(e, enriched_context)
                raise e
            finally:
                handler.pop_context()
        return wrapper


def with_error_context(**context_kwargs):
    """错误上下文装饰器工厂"""
    return ErrorContextDecorator(context_kwargs)


class ErrorContextManager:
    """错误上下文管理器"""

    def __init__(self, context: Dict[str, Any]):
        self.context = context
        self.handler = ContextualErrorHandler()

    def __enter__(self):
        self.handler.push_context(self.context)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.handler.pop_context()

        if exc_type and exc_val:
            # 处理异常并丰富上下文
            enriched_context = self.handler.handle_with_context(exc_val)

            # 更新异常的上下文信息
            if hasattr(exc_val, 'context'):
                exc_val.context.update(enriched_context)
            else:
                # 如果原异常没有context属性，创建新的Perfect21异常
                from .exceptions import ExceptionConverter
                new_exception = ExceptionConverter.convert(exc_val, enriched_context)
                # 替换异常
                exc_val = new_exception

        return False  # 不抑制异常


def error_context(**context_kwargs):
    """错误上下文管理器工厂"""
    return ErrorContextManager(context_kwargs)