#!/usr/bin/env python3
"""
提交守护者
负责提交前的代码质量检查
"""

import os
import sys
import subprocess
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

logger = logging.getLogger("CommitGuardian")

class CommitGuardian:
    """提交守护者"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.getcwd()
        logger.info("提交守护者初始化完成")

    def check_staged_files(self) -> Dict[str, Any]:
        """检查暂存的文件"""
        try:
            # 获取暂存的文件
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )

            staged_files = result.stdout.strip().split('\n') if result.stdout.strip() else []

            # 分析文件类型
            file_analysis = self._analyze_staged_files(staged_files)

            return {
                'staged_files': staged_files,
                'file_count': len(staged_files),
                'file_analysis': file_analysis,
                'has_staged_files': bool(staged_files)
            }

        except subprocess.CalledProcessError as e:
            logger.error(f"检查暂存文件失败: {e}")
            return {
                'error': str(e),
                'staged_files': [],
                'file_count': 0,
                'has_staged_files': False
            }

    def _analyze_staged_files(self, files: List[str]) -> Dict[str, Any]:
        """分析暂存文件"""
        analysis = {
            'python_files': [],
            'config_files': [],
            'documentation': [],
            'test_files': [],
            'other_files': []
        }

        for file_path in files:
            if not file_path:
                continue

            path = Path(file_path)
            extension = path.suffix.lower()
            name = path.name.lower()

            if extension in ['.py']:
                analysis['python_files'].append(file_path)
            elif extension in ['.json', '.yaml', '.yml', '.toml', '.ini', '.conf']:
                analysis['config_files'].append(file_path)
            elif extension in ['.md', '.rst', '.txt']:
                analysis['documentation'].append(file_path)
            elif 'test' in name or extension in ['.test', '.spec']:
                analysis['test_files'].append(file_path)
            else:
                analysis['other_files'].append(file_path)

        return analysis

    def validate_commit_message(self, message: str) -> Dict[str, Any]:
        """验证提交消息"""
        issues = []

        if not message or not message.strip():
            issues.append("提交消息不能为空")
            return {'valid': False, 'issues': issues}

        message = message.strip()

        # 检查消息长度
        if len(message) < 10:
            issues.append("提交消息过短，应至少10个字符")

        if len(message) > 100:
            issues.append("提交消息过长，建议控制在100字符内")

        # 检查格式
        if message.endswith('.'):
            issues.append("提交消息不应以句号结尾")

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'message_length': len(message)
        }

    def get_commit_recommendations(self, branch_type: str, staged_files: List[str]) -> List[str]:
        """获取提交建议"""
        recommendations = []

        # 基于分支类型的建议
        if branch_type == 'feature':
            recommendations.append("功能分支提交应该包含完整的功能实现")
            recommendations.append("建议提交消息格式: feat: 简短描述功能")

        elif branch_type == 'bugfix':
            recommendations.append("修复分支应该包含问题描述和解决方案")
            recommendations.append("建议提交消息格式: fix: 简短描述修复内容")

        elif branch_type == 'hotfix':
            recommendations.append("热修复应该尽量小范围、低风险")
            recommendations.append("建议提交消息格式: hotfix: 紧急修复描述")

        # 基于文件类型的建议
        if any('.py' in f for f in staged_files):
            recommendations.append("Python文件变更应该通过代码质量检查")

        if any('test' in f.lower() for f in staged_files):
            recommendations.append("测试文件变更应该验证测试通过")

        if any(f.endswith('.md') for f in staged_files):
            recommendations.append("文档变更应该检查格式和内容准确性")

        return recommendations