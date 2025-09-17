#!/usr/bin/env python3
"""
Perfect21 Git Hooks单元测试
"""

import unittest
import os
import sys
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock, call
import subprocess

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from features.git_workflow.hooks import GitHooks


class TestGitHooks(unittest.TestCase):
    """Git Hooks测试类"""

    def setUp(self):
        """测试前准备"""
        # 创建临时目录作为项目根目录
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = self.temp_dir

        # 创建mock的agent路径
        self.agents_path = os.path.join(self.temp_dir, "core/claude-code-unified-agents/.claude/agents")
        os.makedirs(self.agents_path, exist_ok=True)

        # 使用临时目录初始化GitHooks
        with patch('features.git_workflow.hooks.os.getcwd', return_value=self.temp_dir):
            self.git_hooks = GitHooks(project_root=self.temp_dir)

    def tearDown(self):
        """测试后清理"""
        if hasattr(self, 'git_hooks'):
            self.git_hooks.cleanup()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """测试初始化"""
        self.assertIsNotNone(self.git_hooks)
        self.assertEqual(self.git_hooks.project_root, self.temp_dir)
        self.assertIsNotNone(self.git_hooks.subagent_mapping)

    @patch('subprocess.run')
    def test_get_git_status(self, mock_run):
        """测试获取Git状态"""
        # Mock所有subprocess.run调用
        mock_result = Mock()
        mock_result.stdout = "feature/test\n"
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        status = self.git_hooks.get_git_status()

        self.assertIsNotNone(status)
        self.assertEqual(status['current_branch'], 'feature/test')
        # 修复: 使用实际返回的字段名
        self.assertIn('is_clean', status)
        self.assertIn('staged_files', status)

    @patch('subprocess.run')
    def test_get_git_status_error(self, mock_run):
        """测试获取Git状态错误处理"""
        mock_run.side_effect = subprocess.CalledProcessError(1, 'git')

        status = self.git_hooks.get_git_status()

        self.assertEqual(status['current_branch'], 'unknown')
        # 修复: 使用实际的字段名
        self.assertFalse(status.get('is_clean', True))
        self.assertEqual(status.get('staged_files', 0), 0)

    def test_generate_parallel_agents_instruction(self):
        """测试生成并行agents指令"""
        agents = ["@project-manager", "@business-analyst"]
        task = "分析需求"
        context = {"key": "value"}

        result = self.git_hooks.generate_parallel_agents_instruction(agents, task, context)

        self.assertTrue(result['success'])
        self.assertEqual(result['execution_mode'], 'parallel')
        self.assertEqual(len(result['agents_to_call']), 2)
        self.assertIn("@project-manager", result['agents_to_call'])
        self.assertIn("@business-analyst", result['agents_to_call'])
        self.assertEqual(result['task_description'], task)
        self.assertEqual(result['context'], context)
        # 修复: 适应新的指令格式
        instruction = result['instruction']
        self.assertTrue(
            "请在一个消息中同时调用" in instruction or
            "请在一个消息中并行调用" in instruction,
            f"Expected parallel instruction, got: {instruction}"
        )

    def test_generate_single_agent_instruction(self):
        """测试生成单个agent指令"""
        agents = ["@test-engineer"]
        task = "编写测试"

        result = self.git_hooks.generate_parallel_agents_instruction(agents, task)

        self.assertTrue(result['success'])
        self.assertEqual(result['execution_mode'], 'sequential')
        self.assertEqual(len(result['agents_to_call']), 1)

    @patch.object(GitHooks, 'get_git_status')
    @patch.object(GitHooks, 'generate_parallel_agents_instruction')
    def test_pre_commit_hook_feature_branch(self, mock_generate, mock_git_status):
        """测试feature分支的pre-commit钩子"""
        mock_git_status.return_value = {
            'current_branch': 'feature/test',
            'is_clean': False,
            'staged_files': 2,
            'modified_files': 1,
            'untracked_files': 0,
            'status_lines': ['M file1.py', 'A file2.py']
        }
        mock_generate.return_value = {'success': True, 'agents_to_call': []}

        result = self.git_hooks.pre_commit_hook()

        self.assertTrue(mock_generate.called)
        # 应该调用代码审查相关的agents
        call_args = mock_generate.call_args[0][0]
        # 修复: 适应实际的agent映射
        self.assertIn('@code-reviewer', call_args)
        # feature分支主要调用代码审查

    @patch.object(GitHooks, 'get_git_status')
    @patch.object(GitHooks, 'generate_parallel_agents_instruction')
    def test_pre_commit_hook_hotfix_branch(self, mock_generate, mock_git_status):
        """测试hotfix分支的pre-commit钩子"""
        mock_git_status.return_value = {
            'current_branch': 'hotfix/urgent',
            'is_clean': False,
            'staged_files': 1,
            'modified_files': 0,
            'untracked_files': 0,
            'status_lines': ['A file1.py']
        }
        mock_generate.return_value = {'success': True, 'agents_to_call': []}

        result = self.git_hooks.pre_commit_hook()

        # hotfix分支应该调用代码审查相关的agent
        call_args = mock_generate.call_args[0][0]
        # 修复: 适应实际的agent映射
        self.assertIn('@code-reviewer', call_args)
        # hotfix分支主要调用代码审查

    @patch.object(GitHooks, 'get_git_status')
    @patch.object(GitHooks, 'generate_parallel_agents_instruction')
    def test_pre_push_hook_feature_branch(self, mock_generate, mock_git_status):
        """测试feature分支的pre-push钩子"""
        mock_git_status.return_value = {'current_branch': 'feature/new-feature'}
        mock_generate.return_value = {'success': True, 'agents_to_call': []}

        with patch('subprocess.check_output', return_value="commit1\ncommit2\n"):
            result = self.git_hooks.pre_push_hook('origin', 'https://github.com/test/repo.git')

        # feature分支推送应该调用测试相关的agent
        call_args = mock_generate.call_args[0][0]
        self.assertIn('@test-engineer', call_args)
        # 注意：feature分支默认只调用@test-engineer

    @patch.object(GitHooks, 'get_git_status')
    @patch.object(GitHooks, 'generate_parallel_agents_instruction')
    def test_pre_push_hook_release_branch(self, mock_generate, mock_git_status):
        """测试release分支的pre-push钩子"""
        mock_git_status.return_value = {'current_branch': 'release/v1.0.0'}
        mock_generate.return_value = {'success': True, 'agents_to_call': []}

        with patch('subprocess.check_output', return_value="commit1\n"):
            result = self.git_hooks.pre_push_hook('origin', 'https://github.com/test/repo.git')

        # release分支也是调用测试相关的agent
        call_args = mock_generate.call_args[0][0]
        self.assertIn('@test-engineer', call_args)
        # 所有分支类型默认都调用@test-engineer进行测试

    @patch.object(GitHooks, 'get_git_status')
    @patch.object(GitHooks, 'generate_parallel_agents_instruction')
    def test_post_checkout_hook(self, mock_generate, mock_git_status):
        """测试post-checkout钩子"""
        mock_git_status.return_value = {'current_branch': 'develop'}
        mock_generate.return_value = {'success': True, 'agents_to_call': []}

        result = self.git_hooks.post_checkout_hook('old_ref', 'new_ref', '1')

        # 分支切换应该调用DevOps相关的agent
        self.assertTrue(mock_generate.called)
        call_args = mock_generate.call_args[0][0]
        self.assertIn(self.git_hooks.subagent_mapping['deployment_check'], call_args)

    def test_post_checkout_hook_not_branch_switch(self):
        """测试非分支切换的post-checkout"""
        result = self.git_hooks.post_checkout_hook('old_ref', 'new_ref', '0')

        self.assertTrue(result['success'])
        self.assertIn('非分支切换', result['message'])

    @patch.object(GitHooks, 'get_git_status')
    @patch.object(GitHooks, 'generate_parallel_agents_instruction')
    @patch('subprocess.check_output')
    def test_prepare_commit_msg_hook(self, mock_subprocess, mock_generate, mock_git_status):
        """测试prepare-commit-msg钩子"""
        mock_git_status.return_value = {'current_branch': 'feature/test'}
        mock_subprocess.return_value = "file1.py\nfile2.py\n"
        mock_generate.return_value = {'success': True, 'agents_to_call': []}

        result = self.git_hooks.prepare_commit_msg_hook('/tmp/commit_msg')

        # 应该调用Business Analyst优化提交消息
        call_args = mock_generate.call_args[0][0]
        self.assertIn('@business-analyst', call_args)

    @patch.object(GitHooks, 'get_git_status')
    @patch.object(GitHooks, 'generate_parallel_agents_instruction')
    def test_commit_msg_hook(self, mock_generate, mock_git_status):
        """测试commit-msg钩子"""
        mock_git_status.return_value = {'current_branch': 'feature/test'}
        mock_generate.return_value = {'success': True, 'agents_to_call': []}

        # 创建临时提交消息文件
        commit_msg_file = os.path.join(self.temp_dir, 'commit_msg')
        with open(commit_msg_file, 'w') as f:
            f.write("feat: add new feature\n\nDetailed description")

        result = self.git_hooks.commit_msg_hook(commit_msg_file)

        # 应该调用Business Analyst验证提交消息
        call_args = mock_generate.call_args[0][0]
        self.assertIn('@business-analyst', call_args)

    @patch.object(GitHooks, 'get_git_status')
    @patch.object(GitHooks, 'generate_parallel_agents_instruction')
    @patch('subprocess.check_output')
    def test_post_commit_hook(self, mock_subprocess, mock_generate, mock_git_status):
        """测试post-commit钩子"""
        mock_git_status.return_value = {'current_branch': 'develop'}
        mock_subprocess.return_value = "abc123|feat: new feature|John Doe"
        mock_generate.return_value = {'success': True, 'agents_to_call': []}

        result = self.git_hooks.post_commit_hook()

        # 应该调用DevOps Engineer处理提交后任务
        call_args = mock_generate.call_args[0][0]
        self.assertIn('@devops-engineer', call_args)

    def test_get_hook_status(self):
        """测试获取钩子状态"""
        with patch.object(self.git_hooks, 'get_git_status', return_value={'current_branch': 'main'}):
            status = self.git_hooks.get_hook_status()

        self.assertIn('git_status', status)
        self.assertIn('available_subagents', status)
        self.assertIn('hooks_active', status)
        self.assertTrue(status['hooks_active'])

    def test_cleanup(self):
        """测试清理方法"""
        self.git_hooks.cleanup()
        self.assertIsNone(self.git_hooks.project_root)

    def test_subagent_mapping(self):
        """测试SubAgent映射"""
        mapping = self.git_hooks.subagent_mapping

        # 检查关键映射是否存在（使用实际的键名）
        self.assertIn('code_review', mapping)
        self.assertIn('test_execution', mapping)
        self.assertIn('security_audit', mapping)
        self.assertIn('deployment_check', mapping)
        self.assertIn('quality_gate', mapping)

        # 检查映射值的格式
        self.assertTrue(mapping['code_review'].startswith('@'))


if __name__ == "__main__":
    unittest.main()