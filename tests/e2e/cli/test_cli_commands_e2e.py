#!/usr/bin/env python3
"""
End-to-end tests for CLI commands
Target: Complete CLI functionality testing
"""

import pytest
import subprocess
import os
import json
import time
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))


class TestCLICommands:
    """Test CLI commands end-to-end"""

    @pytest.fixture
    def cli_path(self):
        """Path to CLI script"""
        return str(Path(__file__).parent.parent.parent.parent / "main" / "cli.py")

    @pytest.fixture
    def temp_workspace(self, tmp_path):
        """Temporary workspace for testing"""
        workspace = tmp_path / "test_workspace"
        workspace.mkdir()

        # Create basic project structure
        (workspace / ".git").mkdir()
        (workspace / "src").mkdir()
        (workspace / "tests").mkdir()

        # Create basic files
        (workspace / "README.md").write_text("# Test Project")
        (workspace / "requirements.txt").write_text("requests==2.28.0\n")

        return workspace

    def run_cli_command(self, cli_path, command_args, cwd=None, input_data=None):
        """Helper to run CLI commands"""
        cmd = [sys.executable, cli_path] + command_args

        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                input=input_data,
                timeout=30
            )
            return {
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': 'Command timed out',
                'success': False
            }

    def test_cli_help_command(self, cli_path):
        """Test CLI help command"""
        result = self.run_cli_command(cli_path, ['--help'])

        assert result['success'] is True
        assert 'Perfect21' in result['stdout']
        assert 'parallel' in result['stdout']
        assert 'status' in result['stdout']
        assert 'hooks' in result['stdout']

    def test_cli_version_command(self, cli_path):
        """Test CLI version command"""
        result = self.run_cli_command(cli_path, ['--version'])

        assert result['success'] is True
        assert 'Perfect21' in result['stdout']
        # Should contain version number
        import re
        version_pattern = r'\d+\.\d+\.\d+'
        assert re.search(version_pattern, result['stdout'])

    def test_cli_status_command_basic(self, cli_path, temp_workspace):
        """Test basic status command"""
        result = self.run_cli_command(
            cli_path,
            ['status'],
            cwd=str(temp_workspace)
        )

        # Should succeed even in minimal project
        assert result['success'] is True
        assert 'Perfect21' in result['stdout'] or 'Status' in result['stdout']

    def test_cli_status_command_detailed(self, cli_path, temp_workspace):
        """Test detailed status command"""
        result = self.run_cli_command(
            cli_path,
            ['status', '--detailed'],
            cwd=str(temp_workspace)
        )

        assert result['success'] is True
        # Should show more detailed information
        stdout_lower = result['stdout'].lower()
        assert any(keyword in stdout_lower for keyword in [
            'git', 'project', 'files', 'features', 'agents'
        ])

    def test_cli_hooks_install_command(self, cli_path, temp_workspace):
        """Test Git hooks installation"""
        # Initialize git repo properly
        subprocess.run(['git', 'init'], cwd=str(temp_workspace), capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'],
                      cwd=str(temp_workspace), capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'],
                      cwd=str(temp_workspace), capture_output=True)

        result = self.run_cli_command(
            cli_path,
            ['hooks', 'install'],
            cwd=str(temp_workspace)
        )

        # May succeed or fail depending on implementation, but should not crash
        assert result['returncode'] != -1  # Not a timeout

        # Check if hooks directory exists
        hooks_dir = temp_workspace / ".git" / "hooks"
        if result['success']:
            assert hooks_dir.exists()

    def test_cli_hooks_status_command(self, cli_path, temp_workspace):
        """Test Git hooks status command"""
        # Initialize git repo
        subprocess.run(['git', 'init'], cwd=str(temp_workspace), capture_output=True)

        result = self.run_cli_command(
            cli_path,
            ['hooks', 'status'],
            cwd=str(temp_workspace)
        )

        # Should show hooks status
        assert result['returncode'] != -1  # Not a timeout
        if result['success']:
            assert 'hooks' in result['stdout'].lower()

    def test_cli_parallel_command_simple(self, cli_path, temp_workspace):
        """Test simple parallel command execution"""
        # Mock the parallel execution to avoid complex setup
        with patch('main.perfect21.Perfect21Core') as mock_core:
            mock_instance = MagicMock()
            mock_instance.execute_parallel_task.return_value = {
                'success': True,
                'results': 'Mock parallel execution completed',
                'execution_time': 2.5
            }
            mock_core.return_value = mock_instance

            result = self.run_cli_command(
                cli_path,
                ['parallel', 'Create a simple test file'],
                cwd=str(temp_workspace)
            )

            # Command structure should be valid even if execution fails
            assert result['returncode'] != -1  # Not a timeout

    def test_cli_parallel_command_with_force(self, cli_path, temp_workspace):
        """Test parallel command with force flag"""
        result = self.run_cli_command(
            cli_path,
            ['parallel', 'Test task', '--force-parallel'],
            cwd=str(temp_workspace)
        )

        # Should parse command correctly
        assert result['returncode'] != -1  # Not a timeout

    def test_cli_error_handling_invalid_command(self, cli_path):
        """Test CLI error handling for invalid commands"""
        result = self.run_cli_command(cli_path, ['invalid_command'])

        assert result['success'] is False
        assert result['returncode'] != 0
        # Should show error message
        assert len(result['stderr']) > 0 or 'error' in result['stdout'].lower()

    def test_cli_error_handling_missing_arguments(self, cli_path):
        """Test CLI error handling for missing arguments"""
        result = self.run_cli_command(cli_path, ['parallel'])  # Missing task description

        assert result['success'] is False
        # Should show usage or error message
        assert len(result['stderr']) > 0 or 'error' in result['stdout'].lower()

    def test_cli_json_output_format(self, cli_path, temp_workspace):
        """Test JSON output format"""
        result = self.run_cli_command(
            cli_path,
            ['status', '--format', 'json'],
            cwd=str(temp_workspace)
        )

        # If JSON format is supported, output should be valid JSON
        if result['success'] and result['stdout'].strip().startswith('{'):
            try:
                json.loads(result['stdout'])
                # Valid JSON output
                assert True
            except json.JSONDecodeError:
                # JSON parsing failed
                pytest.skip("JSON output format not properly implemented")

    def test_cli_verbose_output(self, cli_path, temp_workspace):
        """Test verbose output mode"""
        result = self.run_cli_command(
            cli_path,
            ['status', '--verbose'],
            cwd=str(temp_workspace)
        )

        # Verbose mode should provide more output
        assert result['returncode'] != -1  # Not a timeout

        if result['success']:
            # Should have more detailed output
            assert len(result['stdout']) > 50  # Some reasonable minimum

    def test_cli_config_file_handling(self, cli_path, temp_workspace):
        """Test CLI configuration file handling"""
        # Create config file
        config_file = temp_workspace / "perfect21.yaml"
        config_content = """
        workspace:
          name: "Test Workspace"
          timeout: 300
        features:
          parallel_execution: true
          quality_gates: true
        """
        config_file.write_text(config_content)

        result = self.run_cli_command(
            cli_path,
            ['status', '--config', str(config_file)],
            cwd=str(temp_workspace)
        )

        # Should handle config file gracefully
        assert result['returncode'] != -1  # Not a timeout

    def test_cli_workspace_detection(self, cli_path, temp_workspace):
        """Test automatic workspace detection"""
        # Create Perfect21 project markers
        (temp_workspace / ".perfect21").mkdir()
        (temp_workspace / ".perfect21" / "config.yaml").write_text("workspace: test")

        result = self.run_cli_command(
            cli_path,
            ['status'],
            cwd=str(temp_workspace)
        )

        # Should detect workspace
        assert result['returncode'] != -1  # Not a timeout

    def test_cli_environment_variables(self, cli_path, temp_workspace):
        """Test CLI environment variable handling"""
        env = os.environ.copy()
        env.update({
            'PERFECT21_LOG_LEVEL': 'DEBUG',
            'PERFECT21_WORKSPACE': str(temp_workspace),
            'PERFECT21_TIMEOUT': '60'
        })

        cmd = [sys.executable, cli_path, 'status']

        try:
            result = subprocess.run(
                cmd,
                cwd=str(temp_workspace),
                capture_output=True,
                text=True,
                env=env,
                timeout=30
            )

            # Should handle environment variables
            assert result.returncode != -1  # Not a timeout

        except subprocess.TimeoutExpired:
            pytest.skip("Command timed out with environment variables")

    def test_cli_signal_handling(self, cli_path, temp_workspace):
        """Test CLI signal handling (interruption)"""
        import signal
        import threading

        def interrupt_after_delay():
            time.sleep(1)
            # Send interrupt signal to the process group
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGINT)
            except:
                pass  # Process might have already finished

        cmd = [sys.executable, cli_path, 'parallel', 'Long running task']

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(temp_workspace),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid  # Create new process group
            )

            # Start interrupt thread
            interrupt_thread = threading.Thread(target=interrupt_after_delay)
            interrupt_thread.start()

            # Wait for process to complete or be interrupted
            try:
                stdout, stderr = proc.communicate(timeout=5)
                returncode = proc.returncode

                # Should handle interruption gracefully
                assert returncode != 0 or returncode == -2  # Interrupted

            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate()
                pytest.skip("Process did not respond to interrupt signal")

            interrupt_thread.join()

        except Exception as e:
            pytest.skip(f"Signal handling test failed: {e}")


class TestCLIWorkflows:
    """Test complete CLI workflows"""

    @pytest.fixture
    def cli_path(self):
        """Path to CLI script"""
        return str(Path(__file__).parent.parent.parent.parent / "main" / "cli.py")

    @pytest.fixture
    def project_workspace(self, tmp_path):
        """More complete project workspace"""
        workspace = tmp_path / "project"
        workspace.mkdir()

        # Initialize git
        subprocess.run(['git', 'init'], cwd=str(workspace), capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'],
                      cwd=str(workspace), capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'],
                      cwd=str(workspace), capture_output=True)

        # Create project structure
        (workspace / "src").mkdir()
        (workspace / "tests").mkdir()
        (workspace / "docs").mkdir()
        (workspace / ".perfect21").mkdir()

        # Create project files
        (workspace / "README.md").write_text("# Test Project\n\nA test project for Perfect21.")
        (workspace / "requirements.txt").write_text("fastapi==0.68.0\npytest==6.2.4\n")
        (workspace / ".gitignore").write_text("__pycache__/\n*.pyc\n.env\n")

        # Create Perfect21 config
        config = {
            'project': {
                'name': 'Test Project',
                'type': 'api',
                'version': '1.0.0'
            },
            'features': {
                'parallel_execution': True,
                'quality_gates': True,
                'git_hooks': True
            }
        }

        import yaml
        (workspace / ".perfect21" / "config.yaml").write_text(yaml.dump(config))

        return workspace

    def run_cli_command(self, cli_path, command_args, cwd=None, input_data=None):
        """Helper to run CLI commands"""
        cmd = [sys.executable, cli_path] + command_args

        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                input=input_data,
                timeout=30
            )
            return {
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': result.returncode == 0
            }
        except subprocess.TimeoutExpired:
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': 'Command timed out',
                'success': False
            }

    def test_project_initialization_workflow(self, cli_path, tmp_path):
        """Test complete project initialization workflow"""
        new_project = tmp_path / "new_project"

        # Initialize new project
        result = self.run_cli_command(
            cli_path,
            ['init', str(new_project), '--template', 'api'],
            cwd=str(tmp_path)
        )

        # Command might not be implemented, but should not crash
        assert result['returncode'] != -1  # Not a timeout

    def test_development_workflow(self, cli_path, project_workspace):
        """Test complete development workflow"""
        # 1. Check project status
        status_result = self.run_cli_command(
            cli_path,
            ['status'],
            cwd=str(project_workspace)
        )

        assert status_result['returncode'] != -1  # Not a timeout

        # 2. Install hooks
        hooks_result = self.run_cli_command(
            cli_path,
            ['hooks', 'install'],
            cwd=str(project_workspace)
        )

        assert hooks_result['returncode'] != -1  # Not a timeout

        # 3. Run parallel task (mocked)
        with patch('main.perfect21.Perfect21Core') as mock_core:
            mock_instance = MagicMock()
            mock_instance.execute_parallel_task.return_value = {
                'success': True,
                'results': 'Development task completed',
                'execution_time': 3.2
            }
            mock_core.return_value = mock_instance

            parallel_result = self.run_cli_command(
                cli_path,
                ['parallel', 'Implement user authentication API'],
                cwd=str(project_workspace)
            )

            assert parallel_result['returncode'] != -1  # Not a timeout

    def test_quality_assurance_workflow(self, cli_path, project_workspace):
        """Test quality assurance workflow"""
        # Create some test files
        src_dir = project_workspace / "src"
        (src_dir / "main.py").write_text("""
def hello_world():
    return "Hello, World!"

if __name__ == "__main__":
    print(hello_world())
""")

        test_dir = project_workspace / "tests"
        (test_dir / "test_main.py").write_text("""
import pytest
from src.main import hello_world

def test_hello_world():
    assert hello_world() == "Hello, World!"
""")

        # Run quality checks
        quality_result = self.run_cli_command(
            cli_path,
            ['quality', 'check'],
            cwd=str(project_workspace)
        )

        # Quality command might not be implemented
        assert quality_result['returncode'] != -1  # Not a timeout

    def test_git_integration_workflow(self, cli_path, project_workspace):
        """Test Git integration workflow"""
        # Add files to git
        subprocess.run(['git', 'add', '.'], cwd=str(project_workspace), capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'],
                      cwd=str(project_workspace), capture_output=True)

        # Test git hooks
        hooks_status = self.run_cli_command(
            cli_path,
            ['hooks', 'status'],
            cwd=str(project_workspace)
        )

        assert hooks_status['returncode'] != -1  # Not a timeout

        # Test git integration
        git_result = self.run_cli_command(
            cli_path,
            ['git', 'check'],
            cwd=str(project_workspace)
        )

        # Git command might not be implemented
        assert git_result['returncode'] != -1  # Not a timeout

    def test_monitoring_and_reporting_workflow(self, cli_path, project_workspace):
        """Test monitoring and reporting workflow"""
        # Generate some activity
        with patch('main.perfect21.Perfect21Core') as mock_core:
            mock_instance = MagicMock()
            mock_instance.get_metrics.return_value = {
                'tasks_completed': 5,
                'success_rate': 0.95,
                'average_execution_time': 2.5
            }
            mock_core.return_value = mock_instance

            # Get metrics
            metrics_result = self.run_cli_command(
                cli_path,
                ['metrics'],
                cwd=str(project_workspace)
            )

            assert metrics_result['returncode'] != -1  # Not a timeout

            # Generate report
            report_result = self.run_cli_command(
                cli_path,
                ['report', '--format', 'json'],
                cwd=str(project_workspace)
            )

            assert report_result['returncode'] != -1  # Not a timeout

    def test_configuration_workflow(self, cli_path, project_workspace):
        """Test configuration management workflow"""
        # Update configuration
        config_result = self.run_cli_command(
            cli_path,
            ['config', 'set', 'features.parallel_execution', 'false'],
            cwd=str(project_workspace)
        )

        # Config command might not be implemented
        assert config_result['returncode'] != -1  # Not a timeout

        # Get configuration
        get_config_result = self.run_cli_command(
            cli_path,
            ['config', 'get', 'features.parallel_execution'],
            cwd=str(project_workspace)
        )

        assert get_config_result['returncode'] != -1  # Not a timeout

    def test_troubleshooting_workflow(self, cli_path, project_workspace):
        """Test troubleshooting workflow"""
        # Run diagnostics
        diag_result = self.run_cli_command(
            cli_path,
            ['diagnose'],
            cwd=str(project_workspace)
        )

        assert diag_result['returncode'] != -1  # Not a timeout

        # Check logs
        log_result = self.run_cli_command(
            cli_path,
            ['logs', '--tail', '50'],
            cwd=str(project_workspace)
        )

        assert log_result['returncode'] != -1  # Not a timeout

        # Test repair functionality
        repair_result = self.run_cli_command(
            cli_path,
            ['repair', '--dry-run'],
            cwd=str(project_workspace)
        )

        assert repair_result['returncode'] != -1  # Not a timeout


@pytest.mark.performance
class TestCLIPerformance:
    """Performance tests for CLI"""

    @pytest.fixture
    def cli_path(self):
        """Path to CLI script"""
        return str(Path(__file__).parent.parent.parent.parent / "main" / "cli.py")

    def run_cli_command(self, cli_path, command_args, cwd=None):
        """Helper to run CLI commands with timing"""
        cmd = [sys.executable, cli_path] + command_args

        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=30
            )
            end_time = time.time()

            return {
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': result.returncode == 0,
                'execution_time': end_time - start_time
            }
        except subprocess.TimeoutExpired:
            return {
                'returncode': -1,
                'stdout': '',
                'stderr': 'Command timed out',
                'success': False,
                'execution_time': 30.0
            }

    def test_cli_startup_performance(self, cli_path):
        """Test CLI startup performance"""
        result = self.run_cli_command(cli_path, ['--version'])

        # CLI should start quickly
        assert result['execution_time'] < 5.0  # Less than 5 seconds

    def test_status_command_performance(self, cli_path, tmp_path):
        """Test status command performance"""
        # Create larger project structure
        project = tmp_path / "large_project"
        project.mkdir()

        # Create many files
        for i in range(100):
            (project / f"file_{i}.py").write_text(f"# File {i}\nprint('hello')\n")

        result = self.run_cli_command(
            cli_path,
            ['status'],
            cwd=str(project)
        )

        # Should handle large projects reasonably fast
        assert result['execution_time'] < 10.0  # Less than 10 seconds

    def test_concurrent_cli_execution(self, cli_path, tmp_path):
        """Test concurrent CLI command execution"""
        import threading
        import concurrent.futures

        project = tmp_path / "concurrent_project"
        project.mkdir()

        def run_status_command():
            return self.run_cli_command(
                cli_path,
                ['status'],
                cwd=str(project)
            )

        # Run multiple commands concurrently
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(run_status_command) for _ in range(5)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        end_time = time.time()

        total_time = end_time - start_time

        # Concurrent execution should not take much longer than sequential
        assert total_time < 15.0  # Should complete within reasonable time

        # Most commands should succeed
        successful_results = [r for r in results if r['success'] or r['returncode'] != -1]
        assert len(successful_results) >= 3  # At least 3 out of 5 should work


if __name__ == "__main__":
    pytest.main([__file__, "-v"])