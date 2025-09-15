#!/usr/bin/env python3
"""
Perfect21 SDK - 编程集成接口
提供多种方式在其他程序中调用Perfect21进行开发任务
"""

import os
import sys
import json
import subprocess
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class Perfect21SDK:
    """Perfect21 编程集成SDK"""

    def __init__(self, project_root: str = None):
        """
        初始化Perfect21 SDK

        Args:
            project_root: Perfect21项目根目录，默认为当前目录
        """
        self.project_root = project_root or os.getcwd()
        self.perfect21_main = os.path.join(self.project_root, 'main')

        # 验证Perfect21安装
        if not self._is_perfect21_available():
            raise Exception("Perfect21未安装或不可用，请检查项目结构")

    def _is_perfect21_available(self) -> bool:
        """检查Perfect21是否可用"""
        try:
            # 检查核心文件
            required_files = [
                'vp.py',
                'main/cli.py',
                'core/claude-code-unified-agents'
            ]

            for file_path in required_files:
                if not os.path.exists(os.path.join(self.project_root, file_path)):
                    return False

            return True
        except:
            return False

    def task(self, description: str, **kwargs) -> Dict[str, Any]:
        """
        执行开发任务

        Args:
            description: 任务描述
            **kwargs: 额外参数

        Returns:
            Dict: 执行结果
        """
        try:
            # 构建命令
            cmd = [
                'python3',
                os.path.join(self.project_root, 'vp.py'),
                'task',
                description
            ]

            # 添加额外参数
            if kwargs.get('timeout'):
                cmd.extend(['--timeout', str(kwargs['timeout'])])
            if kwargs.get('verbose'):
                cmd.append('--verbose')

            # 执行命令
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=kwargs.get('timeout', 300)  # 默认5分钟超时
            )

            return {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'returncode': result.returncode
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Task execution timeout',
                'timeout': True
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def status(self) -> Dict[str, Any]:
        """获取Perfect21系统状态"""
        try:
            result = subprocess.run(
                ['python3', os.path.join(self.project_root, 'main/cli.py'), 'status'],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )

            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr if result.stderr else None
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def git_workflow(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        执行Git工作流操作

        Args:
            action: 工作流动作 (create-feature, create-release, merge-to-main等)
            **kwargs: 动作参数

        Returns:
            Dict: 执行结果
        """
        try:
            cmd = [
                'python3',
                os.path.join(self.project_root, 'main/cli.py'),
                'workflow',
                action
            ]

            # 添加参数
            if kwargs.get('name'):
                cmd.extend(['--name', kwargs['name']])
            if kwargs.get('version'):
                cmd.extend(['--version', kwargs['version']])
            if kwargs.get('source'):
                cmd.extend(['--source', kwargs['source']])
            if kwargs.get('branch'):
                cmd.extend(['--branch', kwargs['branch']])

            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )

            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr if result.stderr else None
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def install_hooks(self, hook_group: str = 'standard', force: bool = False) -> Dict[str, Any]:
        """
        安装Git钩子

        Args:
            hook_group: 钩子组 (essential/standard/advanced/complete)
            force: 是否强制覆盖现有钩子

        Returns:
            Dict: 安装结果
        """
        try:
            cmd = [
                'python3',
                os.path.join(self.project_root, 'main/cli.py'),
                'hooks',
                'install',
                hook_group
            ]

            if force:
                cmd.append('--force')

            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )

            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr if result.stderr else None
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def async_task(self, description: str, callback: callable = None, **kwargs) -> str:
        """
        异步执行任务

        Args:
            description: 任务描述
            callback: 完成回调函数
            **kwargs: 额外参数

        Returns:
            str: 任务ID
        """
        import threading
        import uuid

        task_id = str(uuid.uuid4())

        def run_task():
            result = self.task(description, **kwargs)
            if callback:
                callback(task_id, result)

        thread = threading.Thread(target=run_task)
        thread.daemon = True
        thread.start()

        return task_id

# 便捷函数
def create_sdk(project_root: str = None) -> Perfect21SDK:
    """创建Perfect21 SDK实例"""
    return Perfect21SDK(project_root)

def quick_task(description: str, project_root: str = None) -> Dict[str, Any]:
    """快速执行单个任务"""
    sdk = create_sdk(project_root)
    return sdk.task(description)

def quick_status(project_root: str = None) -> Dict[str, Any]:
    """快速获取状态"""
    sdk = create_sdk(project_root)
    return sdk.status()

# 上下文管理器
class Perfect21Context:
    """Perfect21上下文管理器，用于自动资源管理"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root
        self.sdk = None

    def __enter__(self) -> Perfect21SDK:
        self.sdk = create_sdk(self.project_root)
        return self.sdk

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 清理资源
        pass

# 示例用法
if __name__ == "__main__":
    # 1. 基本用法
    sdk = Perfect21SDK()

    # 执行开发任务
    result = sdk.task("创建用户登录API接口")
    print(f"任务执行结果: {result['success']}")

    # 2. 便捷函数
    result = quick_task("重构支付模块")

    # 3. 上下文管理器
    with Perfect21Context() as p21:
        status = p21.status()
        task_result = p21.task("优化数据库查询")

    # 4. 异步任务
    def task_complete(task_id, result):
        print(f"任务 {task_id} 完成: {result['success']}")

    task_id = sdk.async_task("生成测试用例", callback=task_complete)