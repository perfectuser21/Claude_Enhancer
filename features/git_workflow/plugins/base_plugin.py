#!/usr/bin/env python3
"""
Perfect21 Git Hooks Plugin System - Base Plugin Classes
基于2024最佳实践的现代化插件架构
"""

import os
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("Perfect21.HooksPlugin")


class PluginStatus(Enum):
    """插件状态枚举"""
    SUCCESS = "success"
    FAILURE = "failure"
    WARNING = "warning"
    SKIPPED = "skipped"
    ERROR = "error"


class PluginPriority(Enum):
    """插件优先级枚举"""
    CRITICAL = 100
    HIGH = 80
    MEDIUM = 60
    LOW = 40
    OPTIONAL = 20


@dataclass
class PluginResult:
    """插件执行结果"""
    status: PluginStatus
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    exit_code: int = 0
    output: str = ""
    error: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "execution_time": self.execution_time,
            "exit_code": self.exit_code,
            "output": self.output,
            "error": self.error
        }


@dataclass
class PluginMetadata:
    """插件元数据"""
    name: str
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    category: str = "general"
    priority: PluginPriority = PluginPriority.MEDIUM
    dependencies: List[str] = field(default_factory=list)
    supports_parallel: bool = True
    timeout: int = 120
    min_perfect21_version: str = "2.0.0"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "category": self.category,
            "priority": self.priority.value,
            "dependencies": self.dependencies,
            "supports_parallel": self.supports_parallel,
            "timeout": self.timeout,
            "min_perfect21_version": self.min_perfect21_version
        }


class BasePlugin(ABC):
    """Git Hooks插件基类"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.metadata = self._get_metadata()
        self.enabled = self.config.get('enabled', True)
        self.logger = logging.getLogger(f"Perfect21.Plugin.{self.metadata.name}")

        # 执行上下文
        self.execution_context = {}

    @abstractmethod
    def _get_metadata(self) -> PluginMetadata:
        """获取插件元数据"""
        pass

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> PluginResult:
        """
        执行插件逻辑

        Args:
            context: 执行上下文，包含Git信息、文件列表等

        Returns:
            PluginResult: 执行结果
        """
        pass

    def validate_environment(self) -> bool:
        """
        验证执行环境

        Returns:
            bool: 环境是否满足要求
        """
        # 检查依赖
        for dependency in self.metadata.dependencies:
            if not self._check_dependency(dependency):
                self.logger.error(f"缺少依赖: {dependency}")
                return False

        return True

    def _check_dependency(self, dependency: str) -> bool:
        """检查单个依赖"""
        try:
            if dependency.startswith('command:'):
                # 检查命令是否存在
                cmd = dependency.replace('command:', '')
                return os.system(f"which {cmd} > /dev/null 2>&1") == 0
            elif dependency.startswith('python:'):
                # 检查Python包
                package = dependency.replace('python:', '')
                __import__(package)
                return True
            elif dependency.startswith('file:'):
                # 检查文件是否存在
                file_path = dependency.replace('file:', '')
                return os.path.exists(file_path)
            else:
                # 默认作为Python包检查
                __import__(dependency)
                return True
        except (ImportError, OSError):
            return False

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self.config.get(key, default)

    def setup(self) -> bool:
        """插件初始化设置"""
        return True

    def teardown(self) -> bool:
        """插件清理工作"""
        return True

    def should_skip(self, context: Dict[str, Any]) -> bool:
        """判断是否应该跳过执行"""
        if not self.enabled:
            return True

        # 可以基于上下文判断是否跳过
        # 例如：只在特定分支执行、只对特定文件类型执行等
        return False


class CommitWorkflowPlugin(BasePlugin):
    """提交工作流插件基类"""

    def get_staged_files(self) -> List[str]:
        """获取已暂存的文件列表"""
        import subprocess
        try:
            result = subprocess.run(
                ['git', 'diff', '--staged', '--name-only'],
                capture_output=True, text=True, check=True
            )
            return [f.strip() for f in result.stdout.split('\n') if f.strip()]
        except subprocess.CalledProcessError:
            return []

    def get_commit_message(self) -> str:
        """获取提交消息"""
        commit_msg_file = self.execution_context.get('commit_msg_file')

        # 尝试从文件读取
        if commit_msg_file and os.path.exists(commit_msg_file):
            try:
                with open(commit_msg_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            except Exception as e:
                self.logger.warning(f"读取提交消息文件失败: {e}")

        # 尝试从上下文获取
        context_message = self.execution_context.get('commit_message')
        if context_message:
            return context_message.strip()

        # 尝试从Git获取最近的提交消息（仅用于测试）
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'log', '-1', '--pretty=%B'],
                capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            pass

        return ""

    def filter_files_by_extension(self, files: List[str], extensions: List[str]) -> List[str]:
        """根据文件扩展名过滤文件"""
        filtered = []
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                filtered.append(file)
        return filtered


class QualityCheckPlugin(CommitWorkflowPlugin):
    """代码质量检查插件基类"""

    def check_file_quality(self, file_path: str) -> Dict[str, Any]:
        """检查单个文件的质量"""
        return {
            "file": file_path,
            "issues": [],
            "score": 100.0
        }

    def generate_quality_report(self, results: List[Dict[str, Any]]) -> str:
        """生成质量报告"""
        total_files = len(results)
        total_issues = sum(len(r.get('issues', [])) for r in results)
        avg_score = sum(r.get('score', 0) for r in results) / max(total_files, 1)

        return f"""
📊 代码质量报告
================
检查文件: {total_files}
发现问题: {total_issues}
平均分数: {avg_score:.1f}/100.0
        """.strip()


class SecurityPlugin(CommitWorkflowPlugin):
    """安全检查插件基类"""

    def scan_for_secrets(self, file_path: str) -> List[Dict[str, Any]]:
        """扫描文件中的敏感信息"""
        secrets = []

        # 常见的敏感信息模式
        secret_patterns = [
            (r'[A-Za-z0-9]{20,}', 'potential_token'),
            (r'password\s*=\s*["\']([^"\']+)["\']', 'password'),
            (r'api[_-]?key\s*=\s*["\']([^"\']+)["\']', 'api_key'),
        ]

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            import re
            for pattern, secret_type in secret_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    secrets.append({
                        "type": secret_type,
                        "line": content[:match.start()].count('\n') + 1,
                        "pattern": pattern
                    })
        except Exception as e:
            self.logger.warning(f"无法扫描文件 {file_path}: {e}")

        return secrets


class TestPlugin(CommitWorkflowPlugin):
    """测试插件基类"""

    def run_tests(self, test_command: str, working_dir: str = None) -> PluginResult:
        """运行测试命令"""
        import subprocess
        import time

        start_time = time.time()

        try:
            result = subprocess.run(
                test_command.split(),
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=self.metadata.timeout
            )

            execution_time = time.time() - start_time

            if result.returncode == 0:
                return PluginResult(
                    status=PluginStatus.SUCCESS,
                    message="测试通过",
                    execution_time=execution_time,
                    exit_code=result.returncode,
                    output=result.stdout,
                    error=result.stderr
                )
            else:
                return PluginResult(
                    status=PluginStatus.FAILURE,
                    message="测试失败",
                    execution_time=execution_time,
                    exit_code=result.returncode,
                    output=result.stdout,
                    error=result.stderr
                )

        except subprocess.TimeoutExpired:
            return PluginResult(
                status=PluginStatus.ERROR,
                message=f"测试超时 ({self.metadata.timeout}s)",
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return PluginResult(
                status=PluginStatus.ERROR,
                message=f"测试执行错误: {str(e)}",
                execution_time=time.time() - start_time
            )


class NotificationPlugin(BasePlugin):
    """通知插件基类"""

    def send_notification(self, message: str, level: str = "info") -> bool:
        """发送通知"""
        # 子类实现具体的通知方式
        return True

    def format_hook_result(self, hook_name: str, results: List[PluginResult]) -> str:
        """格式化hook执行结果为通知消息"""
        success_count = len([r for r in results if r.status == PluginStatus.SUCCESS])
        failure_count = len([r for r in results if r.status == PluginStatus.FAILURE])

        status_icon = "✅" if failure_count == 0 else "❌"

        return f"""
{status_icon} Perfect21 Git Hook: {hook_name}
成功: {success_count} | 失败: {failure_count}
总插件: {len(results)}
        """.strip()