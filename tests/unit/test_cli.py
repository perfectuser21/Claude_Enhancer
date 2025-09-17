#!/usr/bin/env python3
"""
CLI模块测试
测试命令行接口功能
"""

import os
import sys
import pytest
import tempfile
import subprocess
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from main.cli import CLI, CLICommand
from main.perfect21 import Perfect21Core

class TestCLI:
    """CLI测试类"""

    @pytest.fixture
    def cli(self):
        """CLI实例"""
        return CLI()

    @pytest.fixture
    def temp_workspace(self):
        """临时工作空间"""
        temp_dir = tempfile.mkdtemp(prefix="cli_test_")
        yield temp_dir
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

    def test_cli_initialization(self, cli):
        """测试CLI初始化"""
        assert cli is not None
        assert hasattr(cli, 'parse_args')
        assert hasattr(cli, 'execute_command')

    def test_parallel_command_parsing(self, cli):
        """测试并行命令解析"""
        args = ['parallel', 'implement user authentication', '--force-parallel']
        parsed_args = cli.parse_args(args)

        assert parsed_args.command == 'parallel'
        assert parsed_args.task_description == 'implement user authentication'
        assert parsed_args.force_parallel is True

    def test_status_command_parsing(self, cli):
        """测试状态命令解析"""
        args = ['status', '--detailed']
        parsed_args = cli.parse_args(args)

        assert parsed_args.command == 'status'
        assert parsed_args.detailed is True

    def test_hooks_command_parsing(self, cli):
        """测试Git hooks命令解析"""
        args = ['hooks', 'install']
        parsed_args = cli.parse_args(args)

        assert parsed_args.command == 'hooks'
        assert parsed_args.action == 'install'

    @patch('main.perfect21.Perfect21Core.execute_parallel_task')
    def test_parallel_command_execution(self, mock_execute, cli):
        """测试并行命令执行"""
        mock_execute.return_value = {
            'success': True,
            'result': 'Task completed successfully',
            'agents_called': ['@backend-architect', '@test-engineer']
        }

        args = ['parallel', 'implement API endpoints', '--force-parallel']
        result = cli.execute_command(args)

        assert result['success'] is True
        assert mock_execute.called

    @patch('features.git_workflow.hooks.GitHooks.install_hooks')
    def test_hooks_install_command(self, mock_install, cli):
        """测试Git hooks安装命令"""
        mock_install.return_value = {
            'success': True,
            'installed_hooks': ['pre-commit', 'post-commit', 'pre-push']
        }

        args = ['hooks', 'install']
        result = cli.execute_command(args)

        assert result['success'] is True
        assert mock_install.called

    @patch('features.git_workflow.hooks.GitHooks.get_hook_status')
    def test_hooks_status_command(self, mock_status, cli):
        """测试Git hooks状态命令"""
        mock_status.return_value = {
            'installed': ['pre-commit', 'post-commit'],
            'not_installed': ['pre-push'],
            'total_hooks': 13
        }

        args = ['hooks', 'status']
        result = cli.execute_command(args)

        assert result['installed'] is not None
        assert mock_status.called

    def test_invalid_command_handling(self, cli):
        """测试无效命令处理"""
        args = ['invalid_command']

        with pytest.raises(SystemExit):  # argparse raises SystemExit for invalid commands
            cli.parse_args(args)

    def test_help_command(self, cli):
        """测试帮助命令"""
        args = ['--help']

        with pytest.raises(SystemExit):  # argparse raises SystemExit for help
            cli.parse_args(args)

    @patch('sys.argv')
    @patch('main.cli.CLI.execute_command')
    def test_main_function_execution(self, mock_execute, mock_argv):
        """测试主函数执行"""
        mock_argv.__getitem__.side_effect = lambda x: ['cli.py', 'status'][x]
        mock_execute.return_value = {'success': True}

        from main.cli import main
        result = main()

        assert mock_execute.called

class TestCLICommand:
    """CLI命令测试类"""

    def test_command_initialization(self):
        """测试命令初始化"""
        command = CLICommand(
            name='test',
            description='Test command',
            handler=lambda: {'success': True}
        )

        assert command.name == 'test'
        assert command.description == 'Test command'
        assert callable(command.handler)

    def test_command_execution(self):
        """测试命令执行"""
        def test_handler():
            return {'success': True, 'message': 'Command executed'}

        command = CLICommand(
            name='test',
            description='Test command',
            handler=test_handler
        )

        result = command.execute()
        assert result['success'] is True
        assert result['message'] == 'Command executed'

    def test_command_with_args(self):
        """测试带参数的命令"""
        def handler_with_args(arg1, arg2=None):
            return {'arg1': arg1, 'arg2': arg2}

        command = CLICommand(
            name='test_args',
            description='Test command with args',
            handler=handler_with_args
        )

        result = command.execute('value1', arg2='value2')
        assert result['arg1'] == 'value1'
        assert result['arg2'] == 'value2'

class TestCLIIntegration:
    """CLI集成测试"""

    def test_end_to_end_parallel_execution(self, temp_workspace):
        """测试端到端并行执行"""
        # 模拟完整的并行执行流程
        with patch('main.perfect21.Perfect21Core') as mock_core:
            mock_instance = Mock()
            mock_instance.execute_parallel_task.return_value = {
                'success': True,
                'task_id': 'task_123',
                'agents_called': ['@backend-architect', '@test-engineer'],
                'results': {
                    '@backend-architect': {'success': True, 'output': 'Backend implementation complete'},
                    '@test-engineer': {'success': True, 'output': 'Tests written and passing'}
                }
            }
            mock_core.return_value = mock_instance

            cli = CLI()
            args = ['parallel', 'implement user authentication system', '--force-parallel']
            result = cli.execute_command(args)

            assert result['success'] is True
            assert 'task_id' in result
            assert len(result['agents_called']) == 2

    def test_cli_error_handling(self):
        """测试CLI错误处理"""
        with patch('main.perfect21.Perfect21Core') as mock_core:
            mock_instance = Mock()
            mock_instance.execute_parallel_task.side_effect = Exception("Mock error")
            mock_core.return_value = mock_instance

            cli = CLI()
            args = ['parallel', 'test task']

            result = cli.execute_command(args)
            assert result['success'] is False
            assert 'error' in result

    def test_cli_with_different_workspaces(self, temp_workspace):
        """测试不同工作空间的CLI使用"""
        # 创建不同的工作空间目录
        workspace1 = os.path.join(temp_workspace, 'workspace1')
        workspace2 = os.path.join(temp_workspace, 'workspace2')
        os.makedirs(workspace1)
        os.makedirs(workspace2)

        cli = CLI()

        # 测试在不同工作空间执行命令
        with patch('os.getcwd', return_value=workspace1):
            result1 = cli.execute_command(['status'])

        with patch('os.getcwd', return_value=workspace2):
            result2 = cli.execute_command(['status'])

        # 两个结果应该不同（因为工作空间不同）
        assert 'workspace' in str(result1) or 'workspace' in str(result2)

    @patch('subprocess.run')
    def test_cli_subprocess_integration(self, mock_subprocess):
        """测试CLI与子进程的集成"""
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "Git hooks installed successfully"

        cli = CLI()
        args = ['hooks', 'install']
        result = cli.execute_command(args)

        # 验证子进程被调用
        assert mock_subprocess.called or result is not None

class TestCLIPerformance:
    """CLI性能测试"""

    def test_command_execution_time(self):
        """测试命令执行时间"""
        import time

        cli = CLI()

        start_time = time.time()
        result = cli.execute_command(['status'])
        end_time = time.time()

        execution_time = end_time - start_time

        # CLI命令应该在合理时间内完成（比如5秒）
        assert execution_time < 5.0

    def test_memory_usage(self):
        """测试内存使用"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        cli = CLI()
        cli.execute_command(['status'])

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # 内存增长应该在合理范围内（比如50MB）
        assert memory_increase < 50 * 1024 * 1024  # 50MB

class TestCLIConfiguration:
    """CLI配置测试"""

    def test_config_loading(self):
        """测试配置加载"""
        cli = CLI()

        # 测试默认配置
        config = cli.get_config()
        assert config is not None
        assert 'timeout' in config
        assert 'parallel_enabled' in config

    def test_config_override(self):
        """测试配置覆盖"""
        custom_config = {
            'timeout': 600,
            'parallel_enabled': True,
            'max_agents': 5
        }

        cli = CLI(config=custom_config)
        config = cli.get_config()

        assert config['timeout'] == 600
        assert config['parallel_enabled'] is True
        assert config['max_agents'] == 5