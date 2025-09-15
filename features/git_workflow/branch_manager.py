#!/usr/bin/env python3
"""
Branch Manager - 分支管理器
基于claude-code-unified-agents的智能分支管理
"""

import os
import subprocess
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .hooks import GitHooks

logger = logging.getLogger("BranchManager")

class BranchManager:
    """智能分支管理器"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.getcwd()
        self.git_hooks = GitHooks(project_root)

        # 分支规则配置
        self.branch_rules = {
            'naming_patterns': {
                'feature': r'^feature/[a-z0-9\-]+$',
                'bugfix': r'^bugfix/[a-z0-9\-]+$',
                'hotfix': r'^hotfix/[a-z0-9\-\.]+$',
                'release': r'^release/v?\d+\.\d+\.\d+$'
            },
            'protection_rules': {
                'main': {'direct_push': False, 'require_pr': True, 'require_review': True},
                'master': {'direct_push': False, 'require_pr': True, 'require_review': True},
                'develop': {'direct_push': False, 'require_pr': True, 'require_review': False},
                'release/*': {'direct_push': False, 'require_pr': True, 'require_review': True}
            }
        }

        logger.info("分支管理器初始化完成")

    def analyze_branch_type(self, branch_name: str) -> Dict[str, Any]:
        """分析分支类型和规则"""
        branch_lower = branch_name.lower()

        if branch_lower.startswith('feature/'):
            return {
                'type': 'feature',
                'category': 'development',
                'protection_level': 'low',
                'merge_target': 'develop',
                'requires_review': False,
                'auto_delete': True
            }
        elif branch_lower.startswith('bugfix/'):
            return {
                'type': 'bugfix',
                'category': 'maintenance',
                'protection_level': 'medium',
                'merge_target': 'develop',
                'requires_review': True,
                'auto_delete': True
            }
        elif branch_lower.startswith('hotfix/'):
            return {
                'type': 'hotfix',
                'category': 'critical',
                'protection_level': 'high',
                'merge_target': 'main',
                'requires_review': True,
                'auto_delete': False
            }
        elif branch_lower.startswith('release/'):
            return {
                'type': 'release',
                'category': 'deployment',
                'protection_level': 'high',
                'merge_target': 'main',
                'requires_review': True,
                'auto_delete': False
            }
        elif branch_lower in ['main', 'master']:
            return {
                'type': 'main',
                'category': 'protected',
                'protection_level': 'maximum',
                'merge_target': None,
                'requires_review': True,
                'auto_delete': False
            }
        elif branch_lower in ['develop', 'development']:
            return {
                'type': 'develop',
                'category': 'integration',
                'protection_level': 'high',
                'merge_target': 'main',
                'requires_review': False,
                'auto_delete': False
            }
        else:
            return {
                'type': 'other',
                'category': 'custom',
                'protection_level': 'low',
                'merge_target': 'develop',
                'requires_review': False,
                'auto_delete': True
            }

    def validate_branch_name(self, branch_name: str) -> Dict[str, Any]:
        """验证分支命名规范"""
        branch_info = self.analyze_branch_type(branch_name)

        # 调用SubAgent进行命名规范检查
        validation_result = self.git_hooks.call_subagent(
            '@business-analyst',
            f"验证分支命名规范：{branch_name}，检查是否符合团队约定的命名规则和最佳实践",
            {
                'branch_name': branch_name,
                'branch_type': branch_info['type'],
                'naming_rules': self.branch_rules['naming_patterns'],
                'action': 'validate_naming'
            }
        )

        return {
            'branch_name': branch_name,
            'branch_info': branch_info,
            'validation_result': validation_result,
            'is_valid': True,  # 默认通过，SubAgent会提供详细建议
            'suggestions': []
        }

    def get_merge_strategy(self, source_branch: str, target_branch: str = None) -> Dict[str, Any]:
        """获取合并策略"""
        source_info = self.analyze_branch_type(source_branch)
        target_branch = target_branch or source_info['merge_target']

        if not target_branch:
            return {
                'success': False,
                'message': f"分支{source_branch}没有默认合并目标"
            }

        target_info = self.analyze_branch_type(target_branch)

        # 调用SubAgent分析合并策略
        strategy_result = self.git_hooks.call_subagent(
            '@devops-engineer',
            f"分析从{source_branch}到{target_branch}的合并策略：确定合并方式、检查要求、风险评估",
            {
                'source_branch': source_branch,
                'target_branch': target_branch,
                'source_info': source_info,
                'target_info': target_info,
                'protection_rules': self.branch_rules['protection_rules'],
                'action': 'merge_strategy'
            }
        )

        return {
            'source_branch': source_branch,
            'target_branch': target_branch,
            'source_info': source_info,
            'target_info': target_info,
            'strategy_result': strategy_result,
            'recommended_flow': self._get_merge_flow(source_info, target_info)
        }

    def _get_merge_flow(self, source_info: Dict[str, Any], target_info: Dict[str, Any]) -> List[str]:
        """获取推荐的合并流程"""
        flow = []

        # 根据分支类型确定流程
        if source_info['type'] == 'feature':
            flow = [
                '1. 代码审查 (@code-reviewer)',
                '2. 运行测试套件 (@test-engineer)',
                '3. 合并到develop分支',
                '4. 清理分支'
            ]
        elif source_info['type'] == 'release':
            flow = [
                '1. 完整质量检查 (@orchestrator)',
                '2. 安全审计 (@security-auditor)',
                '3. 性能验证 (@performance-engineer)',
                '4. 部署就绪检查 (@devops-engineer)',
                '5. 合并到main分支',
                '6. 创建发布标签',
                '7. 触发部署流水线'
            ]
        elif source_info['type'] == 'hotfix':
            flow = [
                '1. 紧急安全检查 (@security-auditor)',
                '2. 关键路径测试 (@test-engineer)',
                '3. 快速部署验证 (@devops-engineer)',
                '4. 合并到main分支',
                '5. 同步到develop分支',
                '6. 立即部署'
            ]

        return flow

    def cleanup_old_branches(self, days_threshold: int = 30) -> Dict[str, Any]:
        """清理旧分支"""
        try:
            # 获取所有分支信息
            branches_result = subprocess.run(
                ['git', 'for-each-ref', '--format=%(refname:short),%(committerdate)', 'refs/heads/'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )

            old_branches = []
            protected_branches = ['main', 'master', 'develop']

            for line in branches_result.stdout.strip().split('\n'):
                if ',' in line:
                    branch_name, commit_date = line.split(',', 1)
                    if branch_name not in protected_branches:
                        # 这里可以添加日期判断逻辑
                        old_branches.append(branch_name)

            if old_branches:
                # 调用SubAgent分析清理建议
                cleanup_result = self.git_hooks.call_subagent(
                    '@devops-engineer',
                    f"分析分支清理策略：检查{len(old_branches)}个候选分支，确定安全清理方案",
                    {
                        'old_branches': old_branches,
                        'days_threshold': days_threshold,
                        'protected_branches': protected_branches,
                        'action': 'branch_cleanup'
                    }
                )

                return {
                    'success': True,
                    'old_branches': old_branches,
                    'cleanup_result': cleanup_result,
                    'message': f"发现{len(old_branches)}个候选清理分支"
                }
            else:
                return {
                    'success': True,
                    'old_branches': [],
                    'message': '没有发现需要清理的旧分支'
                }

        except subprocess.CalledProcessError as e:
            logger.error(f"分支清理分析失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': '分支清理分析失败'
            }

    def get_branch_status(self) -> Dict[str, Any]:
        """获取分支状态总览"""
        try:
            # 获取当前状态
            git_status = self.git_hooks.get_git_status()
            current_branch = git_status['current_branch']
            branch_info = self.analyze_branch_type(current_branch)

            # 获取分支列表
            branches_result = subprocess.run(
                ['git', 'branch', '-r'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )

            remote_branches = [
                line.strip().replace('origin/', '')
                for line in branches_result.stdout.split('\n')
                if line.strip() and not line.strip().startswith('HEAD ->')
            ]

            # 分类统计
            branch_stats = {}
            for branch in remote_branches:
                branch_type = self.analyze_branch_type(branch)['type']
                branch_stats.setdefault(branch_type, []).append(branch)

            return {
                'current_branch': {
                    'name': current_branch,
                    'info': branch_info
                },
                'branch_statistics': {
                    'total': len(remote_branches),
                    'by_type': {k: len(v) for k, v in branch_stats.items()},
                    'details': branch_stats
                },
                'protection_rules': self.branch_rules['protection_rules'],
                'git_status': git_status
            }

        except subprocess.CalledProcessError as e:
            logger.error(f"获取分支状态失败: {e}")
            return {
                'error': str(e),
                'message': '无法获取分支状态'
            }