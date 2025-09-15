#!/usr/bin/env python3
"""
Git Hooks - SubAgent调用编排器
不重复实现功能，智能调用claude-code-unified-agents的现有SubAgent
"""

import os
import sys
import subprocess
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger("GitHooks")

class GitHooks:
    """Git钩子 - SubAgent调用编排器"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.getcwd()

        # SubAgent映射 - 调用claude-code-unified-agents的现有Agent
        self.subagent_mapping = {
            'code_review': '@code-reviewer',
            'security_audit': '@security-auditor',
            'test_execution': '@test-engineer',
            'performance_check': '@performance-engineer',
            'deployment_check': '@devops-engineer',
            'quality_gate': '@orchestrator'
        }

        logger.info("Git Hooks初始化完成 - 基于claude-code-unified-agents")

    def get_git_status(self) -> Dict[str, Any]:
        """获取Git状态"""
        try:
            # 获取当前分支
            branch_result = subprocess.run(
                ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )

            # 获取暂存文件
            staged_result = subprocess.run(
                ['git', 'diff', '--cached', '--name-only'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )

            # 获取修改文件
            modified_result = subprocess.run(
                ['git', 'diff', '--name-only'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )

            return {
                'current_branch': branch_result.stdout.strip(),
                'staged_files': [f for f in staged_result.stdout.strip().split('\n') if f],
                'modified_files': [f for f in modified_result.stdout.strip().split('\n') if f],
                'has_staged_changes': bool(staged_result.stdout.strip())
            }

        except subprocess.CalledProcessError as e:
            logger.error(f"获取Git状态失败: {e}")
            return {
                'current_branch': 'unknown',
                'staged_files': [],
                'modified_files': [],
                'has_staged_changes': False,
                'error': str(e)
            }

    def call_subagent(self, agent_name: str, task_description: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """调用claude-code-unified-agents的SubAgent"""
        try:
            # 构建调用命令 - 使用Claude Code原生机制
            if context:
                task_with_context = f"{task_description}\n\n上下文信息:\n"
                for key, value in context.items():
                    task_with_context += f"- {key}: {value}\n"
            else:
                task_with_context = task_description

            logger.info(f"调用SubAgent: {agent_name}")
            logger.info(f"任务描述: {task_description}")

            # 这里返回调用信息，实际调用由Claude Code处理
            return {
                'success': True,
                'agent': agent_name,
                'task': task_description,
                'message': f"已请求{agent_name}执行任务",
                'call_info': {
                    'command': f"请在Claude Code中执行: {agent_name} {task_description}",
                    'context': context
                }
            }

        except Exception as e:
            logger.error(f"调用SubAgent失败: {e}")
            return {
                'success': False,
                'agent': agent_name,
                'error': str(e),
                'message': f"调用{agent_name}失败"
            }

    def pre_commit_hook(self) -> Dict[str, Any]:
        """提交前钩子 - 调用代码审查和质量检查"""
        logger.info("执行pre-commit钩子")

        git_status = self.get_git_status()

        if not git_status['has_staged_changes']:
            return {
                'success': False,
                'message': '没有暂存的文件，无法提交',
                'should_abort': True
            }

        # 分析分支类型决定检查级别
        branch = git_status['current_branch']
        if branch in ['main', 'master', 'release']:
            # 严格检查 - 调用完整质量门禁
            return self.call_subagent(
                self.subagent_mapping['quality_gate'],
                f"对{branch}分支执行严格的提交前质量检查：代码审查、安全扫描、测试验证",
                {
                    'branch': branch,
                    'staged_files': git_status['staged_files'],
                    'check_level': 'strict',
                    'required_checks': ['code_review', 'security_audit', 'test_execution']
                }
            )
        else:
            # 基础检查 - 调用代码审查
            return self.call_subagent(
                self.subagent_mapping['code_review'],
                f"对{branch}分支执行代码审查：检查代码质量、格式、最佳实践",
                {
                    'branch': branch,
                    'staged_files': git_status['staged_files'],
                    'check_level': 'basic'
                }
            )

    def pre_push_hook(self, remote: str = 'origin', branch: str = None) -> Dict[str, Any]:
        """推送前钩子 - 调用测试和部署检查"""
        logger.info(f"执行pre-push钩子: {remote}")

        git_status = self.get_git_status()
        current_branch = branch or git_status['current_branch']

        # 保护主分支
        if current_branch in ['main', 'master']:
            return {
                'success': False,
                'message': '禁止直接推送到主分支，请使用Pull Request流程',
                'should_abort': True,
                'branch_protection': True
            }

        # 根据分支类型选择检查策略
        if current_branch.startswith('release/'):
            # 发布分支 - 完整检查
            return self.call_subagent(
                self.subagent_mapping['deployment_check'],
                f"对发布分支{current_branch}执行推送前完整检查：测试套件、性能验证、部署就绪检查",
                {
                    'branch': current_branch,
                    'remote': remote,
                    'check_type': 'release',
                    'required_checks': ['test_execution', 'performance_check', 'deployment_check']
                }
            )
        elif current_branch.startswith('hotfix/'):
            # 热修复分支 - 快速验证
            return self.call_subagent(
                self.subagent_mapping['test_execution'],
                f"对热修复分支{current_branch}执行快速测试验证",
                {
                    'branch': current_branch,
                    'remote': remote,
                    'check_type': 'hotfix',
                    'priority': 'high'
                }
            )
        else:
            # 功能分支 - 标准检查
            return self.call_subagent(
                self.subagent_mapping['test_execution'],
                f"对功能分支{current_branch}执行标准测试检查",
                {
                    'branch': current_branch,
                    'remote': remote,
                    'check_type': 'feature'
                }
            )

    def post_checkout_hook(self, old_ref: str, new_ref: str, branch_flag: str) -> Dict[str, Any]:
        """分支切换后钩子 - 调用环境配置和依赖检查"""
        logger.info("执行post-checkout钩子")

        # 只处理分支切换
        if branch_flag != "1":
            return {'success': True, 'message': '非分支切换，跳过处理'}

        git_status = self.get_git_status()
        current_branch = git_status['current_branch']

        # 调用DevOps Engineer配置环境
        return self.call_subagent(
            self.subagent_mapping['deployment_check'],
            f"分支切换到{current_branch}，检查开发环境配置、依赖状态、工具链设置",
            {
                'branch': current_branch,
                'old_ref': old_ref,
                'new_ref': new_ref,
                'action': 'branch_switch',
                'checks': ['dependencies', 'environment', 'configuration']
            }
        )

    def get_hook_status(self) -> Dict[str, Any]:
        """获取钩子状态"""
        git_status = self.get_git_status()

        return {
            'git_status': git_status,
            'available_subagents': self.subagent_mapping,
            'core_path': os.path.join(self.project_root, 'core/claude-code-unified-agents/.claude/agents'),
            'hooks_active': True
        }

    def cleanup(self) -> None:
        """清理GitHooks实例，释放内存"""
        try:
            # 清理映射配置
            if hasattr(self, 'subagent_mapping'):
                self.subagent_mapping.clear()

            # 清理项目根路径引用
            self.project_root = None

            # 强制垃圾回收
            import gc
            gc.collect()

            logger.info("GitHooks清理完成")

        except Exception as e:
            logger.error(f"GitHooks清理失败: {e}")

    def __del__(self):
        """析构函数，确保资源被清理"""
        try:
            self.cleanup()
        except:
            pass