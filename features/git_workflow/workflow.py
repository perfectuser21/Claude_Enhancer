#!/usr/bin/env python3
"""
Git Workflow Manager - 工作流自动化
基于claude-code-unified-agents的工作流编排
"""

import os
import subprocess
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from .hooks import GitHooks

logger = logging.getLogger("WorkflowManager")

class WorkflowManager:
    """Git工作流管理器"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.getcwd()
        self.git_hooks = GitHooks(project_root)

        # 工作流配置
        self.workflow_config = {
            'branch_naming': {
                'feature': 'feature/',
                'bugfix': 'bugfix/',
                'hotfix': 'hotfix/',
                'release': 'release/'
            },
            'protection_rules': {
                'protected_branches': ['main', 'master', 'develop'],
                'require_review': True,
                'require_tests': True
            }
        }

        logger.info("Git工作流管理器初始化完成")

    def _get_default_base_branch(self) -> str:
        """智能选择默认基础分支"""
        try:
            # 获取所有分支
            result = subprocess.run(
                ['git', 'branch', '-a'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )

            branches = [
                line.strip().replace('* ', '').replace('remotes/origin/', '')
                for line in result.stdout.split('\n')
                if line.strip() and not line.strip().startswith('HEAD ->')
            ]

            # 按优先级选择基础分支
            for preferred_branch in ['develop', 'main', 'master']:
                if preferred_branch in branches:
                    logger.info(f"选择基础分支: {preferred_branch}")
                    return preferred_branch

            # 如果没有找到标准分支，返回当前分支
            current_result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            current_branch = current_result.stdout.strip()
            logger.warning(f"未找到标准分支，使用当前分支: {current_branch}")
            return current_branch

        except subprocess.CalledProcessError as e:
            logger.error(f"获取分支信息失败: {e}")
            return 'main'  # 默认回退到main

    def create_feature_branch(self, feature_name: str, from_branch: str = None) -> Dict[str, Any]:
        """创建功能分支"""
        try:
            branch_name = f"feature/{feature_name}"

            # 智能选择源分支
            if from_branch is None:
                from_branch = self._get_default_base_branch()

            # 切换到源分支并更新
            subprocess.run(['git', 'checkout', from_branch], cwd=self.project_root, check=True)

            # 尝试拉取更新，但如果没有remote tracking分支则跳过
            try:
                subprocess.run(['git', 'pull'], cwd=self.project_root, check=True)
                logger.info(f"更新分支{from_branch}成功")
            except subprocess.CalledProcessError:
                logger.warning(f"无法拉取{from_branch}分支更新，可能是本地仓库或无upstream配置")

            # 创建新分支
            subprocess.run(['git', 'checkout', '-b', branch_name], cwd=self.project_root, check=True)

            logger.info(f"创建功能分支: {branch_name}")

            # 调用SubAgent设置开发环境
            setup_result = self.git_hooks.call_subagent(
                '@devops-engineer',
                f"为新功能分支{branch_name}设置开发环境：检查依赖、配置工具、设置最佳实践",
                {
                    'branch_name': branch_name,
                    'branch_type': 'feature',
                    'source_branch': from_branch,
                    'action': 'branch_setup'
                }
            )

            return {
                'success': True,
                'branch_name': branch_name,
                'message': f"功能分支{branch_name}创建成功",
                'setup_result': setup_result
            }

        except subprocess.CalledProcessError as e:
            logger.error(f"创建功能分支失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"创建功能分支{feature_name}失败"
            }

    def create_release_branch(self, version: str, from_branch: str = None) -> Dict[str, Any]:
        """创建发布分支"""
        try:
            branch_name = f"release/{version}"

            # 智能选择源分支
            if from_branch is None:
                from_branch = self._get_default_base_branch()

            # 切换到源分支并更新
            subprocess.run(['git', 'checkout', from_branch], cwd=self.project_root, check=True)

            # 尝试拉取更新，但如果没有remote tracking分支则跳过
            try:
                subprocess.run(['git', 'pull'], cwd=self.project_root, check=True)
                logger.info(f"更新分支{from_branch}成功")
            except subprocess.CalledProcessError:
                logger.warning(f"无法拉取{from_branch}分支更新，可能是本地仓库或无upstream配置")

            # 创建发布分支
            subprocess.run(['git', 'checkout', '-b', branch_name], cwd=self.project_root, check=True)

            logger.info(f"创建发布分支: {branch_name}")

            # 调用SubAgent进行发布准备
            release_result = self.git_hooks.call_subagent(
                '@orchestrator',
                f"为发布分支{branch_name}执行发布准备流程：版本检查、构建验证、部署准备、文档更新",
                {
                    'branch_name': branch_name,
                    'version': version,
                    'branch_type': 'release',
                    'source_branch': from_branch,
                    'required_tasks': ['version_check', 'build_verification', 'deployment_prep', 'documentation']
                }
            )

            return {
                'success': True,
                'branch_name': branch_name,
                'version': version,
                'message': f"发布分支{branch_name}创建成功",
                'release_result': release_result
            }

        except subprocess.CalledProcessError as e:
            logger.error(f"创建发布分支失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"创建发布分支{version}失败"
            }

    def merge_to_main(self, source_branch: str, delete_source: bool = True) -> Dict[str, Any]:
        """合并到主分支"""
        try:
            # 执行合并前检查
            pre_merge_result = self.git_hooks.call_subagent(
                '@orchestrator',
                f"执行{source_branch}到main的合并前完整检查：代码审查、测试验证、安全扫描、部署就绪检查",
                {
                    'source_branch': source_branch,
                    'target_branch': 'main',
                    'action': 'pre_merge_check',
                    'required_checks': ['code_review', 'security_audit', 'test_execution', 'deployment_check']
                }
            )

            if not pre_merge_result.get('success', True):
                return {
                    'success': False,
                    'message': '合并前检查失败，无法合并到主分支',
                    'pre_merge_result': pre_merge_result
                }

            # 切换到主分支并更新
            subprocess.run(['git', 'checkout', 'main'], cwd=self.project_root, check=True)
            subprocess.run(['git', 'pull'], cwd=self.project_root, check=True)

            # 执行合并
            subprocess.run(['git', 'merge', source_branch, '--no-ff'], cwd=self.project_root, check=True)

            # 删除源分支(如果需要)
            if delete_source and not source_branch.startswith(('main', 'master', 'develop')):
                subprocess.run(['git', 'branch', '-d', source_branch], cwd=self.project_root, check=True)

            logger.info(f"合并{source_branch}到main成功")

            # 执行合并后任务
            post_merge_result = self.git_hooks.call_subagent(
                '@deployment-manager',
                f"执行{source_branch}合并到main后的部署任务：构建、测试、部署流水线",
                {
                    'merged_branch': source_branch,
                    'target_branch': 'main',
                    'action': 'post_merge_deployment',
                    'delete_source': delete_source
                }
            )

            return {
                'success': True,
                'message': f"{source_branch}成功合并到main",
                'source_branch': source_branch,
                'source_deleted': delete_source,
                'pre_merge_result': pre_merge_result,
                'post_merge_result': post_merge_result
            }

        except subprocess.CalledProcessError as e:
            logger.error(f"合并到主分支失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': f"合并{source_branch}到main失败"
            }

    def get_workflow_status(self) -> Dict[str, Any]:
        """获取工作流状态"""
        git_status = self.git_hooks.get_git_status()

        try:
            # 获取分支列表
            branches_result = subprocess.run(
                ['git', 'branch', '-a'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )

            branches = [
                line.strip().replace('* ', '').replace('remotes/origin/', '')
                for line in branches_result.stdout.split('\n')
                if line.strip() and not line.strip().startswith('HEAD ->')
            ]

            # 分析分支类型
            branch_analysis = {}
            for branch in branches:
                if branch.startswith('feature/'):
                    branch_analysis.setdefault('feature', []).append(branch)
                elif branch.startswith('release/'):
                    branch_analysis.setdefault('release', []).append(branch)
                elif branch.startswith('hotfix/'):
                    branch_analysis.setdefault('hotfix', []).append(branch)
                elif branch in ['main', 'master', 'develop']:
                    branch_analysis.setdefault('main', []).append(branch)

            return {
                'git_status': git_status,
                'branches': {
                    'all': branches,
                    'by_type': branch_analysis,
                    'current': git_status['current_branch']
                },
                'workflow_config': self.workflow_config,
                'hooks_available': True
            }

        except subprocess.CalledProcessError as e:
            logger.error(f"获取工作流状态失败: {e}")
            return {
                'git_status': git_status,
                'error': str(e),
                'message': '无法获取完整工作流状态'
            }