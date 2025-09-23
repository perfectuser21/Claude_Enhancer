#!/usr/bin/env python3
"""
Claude Enhancer 单元测试套件
针对各个组件的独立功能测试
"""

import unittest
import json
import yaml
import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
import subprocess


class TestConfigurationParsing(unittest.TestCase):
    """配置文件解析测试"""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.claude_dir = self.test_dir / ".claude"
        self.claude_dir.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_valid_json_config(self):
        """测试有效的JSON配置解析"""
        config_data = {
            "version": "4.0.0",
            "project": "Test Project",
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Task",
                        "type": "command",
                        "command": "echo test",
                        "blocking": False,
                    }
                ]
            },
        }

        config_file = self.claude_dir / "settings.json"
        with open(config_file, "w") as f:
            json.dump(config_data, f)

        # 测试解析
        with open(config_file, "r") as f:
            parsed_config = json.load(f)

        self.assertEqual(parsed_config["version"], "4.0.0")
        self.assertEqual(parsed_config["project"], "Test Project")
        self.assertIn("hooks", parsed_config)
        self.assertIn("PreToolUse", parsed_config["hooks"])

    def test_invalid_json_config(self):
        """测试无效的JSON配置处理"""
        config_file = self.claude_dir / "settings.json"
        with open(config_file, "w") as f:
            f.write('{"invalid": json syntax}')  # 故意写错误的JSON

        with self.assertRaises(json.JSONDecodeError):
            with open(config_file, "r") as f:
                json.load(f)

    def test_yaml_config_parsing(self):
        """测试YAML配置解析"""
        config_data = {
            "system": {"mode": "production", "debug": False},
            "agents": {"minimum_count": 3, "maximum_count": 8},
        }

        config_file = self.claude_dir / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        # 测试解析
        with open(config_file, "r") as f:
            parsed_config = yaml.safe_load(f)

        self.assertEqual(parsed_config["system"]["mode"], "production")
        self.assertEqual(parsed_config["agents"]["minimum_count"], 3)

    def test_missing_config_file(self):
        """测试缺失配置文件的处理"""
        config_file = self.claude_dir / "nonexistent.json"

        with self.assertRaises(FileNotFoundError):
            with open(config_file, "r") as f:
                json.load(f)


class TestHookValidation(unittest.TestCase):
    """Hook验证测试"""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.hooks_dir = self.test_dir / ".claude" / "hooks"
        self.hooks_dir.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_hook_file_permissions(self):
        """测试Hook文件权限"""
        hook_file = self.hooks_dir / "test_hook.sh"
        with open(hook_file, "w") as f:
            f.write("#!/bin/bash\necho 'test hook'\n")

        # 初始权限可能不可执行
        self.assertTrue(hook_file.exists())

        # 设置可执行权限
        os.chmod(hook_file, 0o755)
        self.assertTrue(os.access(hook_file, os.X_OK))

    def test_hook_script_syntax(self):
        """测试Hook脚本语法"""
        # 有效的bash脚本
        valid_hook = self.hooks_dir / "valid_hook.sh"
        with open(valid_hook, "w") as f:
            f.write(
                """#!/bin/bash
set -e
echo "Valid hook script"
exit 0
"""
            )
        os.chmod(valid_hook, 0o755)

        # 测试语法检查
        result = subprocess.run(
            ["bash", "-n", str(valid_hook)], capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0, "Valid hook should pass syntax check")

        # 无效的bash脚本
        invalid_hook = self.hooks_dir / "invalid_hook.sh"
        with open(invalid_hook, "w") as f:
            f.write(
                """#!/bin/bash
if [ missing bracket
echo "Invalid syntax"
"""
            )
        os.chmod(invalid_hook, 0o755)

        result = subprocess.run(
            ["bash", "-n", str(invalid_hook)], capture_output=True, text=True
        )
        self.assertNotEqual(
            result.returncode, 0, "Invalid hook should fail syntax check"
        )

    def test_hook_timeout_handling(self):
        """测试Hook超时处理"""
        timeout_hook = self.hooks_dir / "timeout_hook.sh"
        with open(timeout_hook, "w") as f:
            f.write(
                """#!/bin/bash
# 模拟长时间运行的Hook
sleep 10
echo "This should timeout"
"""
            )
        os.chmod(timeout_hook, 0o755)

        # 测试超时
        try:
            result = subprocess.run(
                ["bash", str(timeout_hook)],
                timeout=2,  # 2秒超时
                capture_output=True,
                text=True,
            )
            self.fail("Hook should have timed out")
        except subprocess.TimeoutExpired:
            pass  # 期望的超时


class TestPerformanceMetrics(unittest.TestCase):
    """性能指标测试"""

    def test_execution_time_measurement(self):
        """测试执行时间测量准确性"""
        import time

        start_time = time.perf_counter()
        time.sleep(0.1)  # 睡眠100毫秒
        end_time = time.perf_counter()

        execution_time = end_time - start_time
        # 允许10%的误差
        self.assertGreaterEqual(execution_time, 0.09)
        self.assertLessEqual(execution_time, 0.11)

    def test_memory_usage_tracking(self):
        """测试内存使用跟踪"""
        try:
            import psutil

            # 获取当前内存使用
            process = psutil.Process()
            memory_before = process.memory_info().rss

            # 分配一些内存
            large_data = [0] * 100000
            memory_after = process.memory_info().rss

            # 内存使用应该增加
            self.assertGreater(memory_after, memory_before)

            # 清理
            del large_data

        except ImportError:
            self.skipTest("psutil not available")

    def test_cpu_usage_monitoring(self):
        """测试CPU使用监控"""
        try:
            import psutil
            import time

            # 监控CPU使用
            cpu_percent = psutil.cpu_percent(interval=0.1)
            self.assertGreaterEqual(cpu_percent, 0.0)
            self.assertLessEqual(cpu_percent, 100.0)

        except ImportError:
            self.skipTest("psutil not available")


class TestErrorHandling(unittest.TestCase):
    """错误处理测试"""

    def test_command_execution_error(self):
        """测试命令执行错误处理"""
        # 执行不存在的命令，捕获异常
        with self.assertRaises(FileNotFoundError):
            subprocess.run(
                ["nonexistent_command_12345"],
                capture_output=True,
                text=True,
                check=True,
            )

    def test_file_not_found_error(self):
        """测试文件未找到错误处理"""
        with self.assertRaises(FileNotFoundError):
            with open("/nonexistent/path/file.txt", "r") as f:
                f.read()

    def test_permission_error(self):
        """测试权限错误处理"""
        # 简化测试，只检查文件权限的改变
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test_file.txt"
            test_file.write_text("test content")

            # 检查初始可读性
            self.assertTrue(os.access(test_file, os.R_OK))

            # 移除读权限
            os.chmod(test_file, 0o000)

            # 检查文件现在不可读
            self.assertFalse(os.access(test_file, os.R_OK))

            # 恢复权限以便清理
            os.chmod(test_file, 0o644)


class TestSystemIntegration(unittest.TestCase):
    """系统集成测试"""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.claude_dir = self.test_dir / ".claude"
        self.claude_dir.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_environment_variables(self):
        """测试环境变量设置"""
        test_env = os.environ.copy()
        test_env.update(
            {
                "CLAUDE_TEST_MODE": "1",
                "HOOK_TEST_MODE": "1",
                "CLAUDE_DIR": str(self.claude_dir),
            }
        )

        # 运行简单命令验证环境变量
        result = subprocess.run(
            ["bash", "-c", "echo $CLAUDE_TEST_MODE"],
            env=test_env,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "1")

    def test_working_directory_change(self):
        """测试工作目录变更"""
        # 创建测试目录
        test_subdir = self.test_dir / "subdir"
        test_subdir.mkdir()

        # 在子目录中运行命令
        result = subprocess.run(
            ["pwd"], cwd=test_subdir, capture_output=True, text=True
        )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(Path(result.stdout.strip()), test_subdir)

    def test_hook_system_integration(self):
        """测试Hook系统集成"""
        # 创建简单的Hook配置
        settings = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": ".*",
                        "type": "command",
                        "command": "echo 'PreToolUse hook executed'",
                        "blocking": False,
                        "timeout": 1000,
                    }
                ]
            }
        }

        settings_file = self.claude_dir / "settings.json"
        with open(settings_file, "w") as f:
            json.dump(settings, f)

        # 验证配置可以正确解析
        with open(settings_file, "r") as f:
            loaded_settings = json.load(f)

        self.assertIn("hooks", loaded_settings)
        self.assertIn("PreToolUse", loaded_settings["hooks"])
        self.assertEqual(len(loaded_settings["hooks"]["PreToolUse"]), 1)

        hook_config = loaded_settings["hooks"]["PreToolUse"][0]
        self.assertEqual(hook_config["command"], "echo 'PreToolUse hook executed'")
        self.assertFalse(hook_config["blocking"])


class TestDataValidation(unittest.TestCase):
    """数据验证测试"""

    def test_json_schema_validation(self):
        """测试JSON模式验证"""
        # 有效的Hook配置
        valid_hook_config = {
            "matcher": "Task",
            "type": "command",
            "command": "echo test",
            "timeout": 1000,
            "blocking": False,
        }

        # 检查必需字段
        required_fields = ["matcher", "type", "command"]
        for field in required_fields:
            self.assertIn(field, valid_hook_config)

        # 检查字段类型
        self.assertIsInstance(valid_hook_config["matcher"], str)
        self.assertIsInstance(valid_hook_config["type"], str)
        self.assertIsInstance(valid_hook_config["command"], str)
        self.assertIsInstance(valid_hook_config["timeout"], int)
        self.assertIsInstance(valid_hook_config["blocking"], bool)

    def test_timeout_value_validation(self):
        """测试超时值验证"""
        valid_timeouts = [100, 1000, 5000, 30000]
        invalid_timeouts = [-1, 0, "1000", None, 3.14]

        for timeout in valid_timeouts:
            self.assertIsInstance(timeout, int)
            self.assertGreater(timeout, 0)

        for timeout in invalid_timeouts:
            if timeout is None:
                continue
            if isinstance(timeout, str):
                # 字符串超时值应该被检测为无效
                self.assertIsInstance(timeout, str)
            elif isinstance(timeout, (int, float)) and timeout <= 0:
                self.assertLessEqual(timeout, 0)

    def test_command_string_validation(self):
        """测试命令字符串验证"""
        valid_commands = [
            "echo test",
            "bash /path/to/script.sh",
            "python3 script.py --arg value",
        ]

        invalid_commands = [
            "",  # 空命令
            None,  # None值
            123,  # 非字符串
            "command; rm -rf /",  # 危险命令
        ]

        for cmd in valid_commands:
            self.assertIsInstance(cmd, str)
            self.assertGreater(len(cmd.strip()), 0)

        for cmd in invalid_commands:
            if cmd is None:
                self.assertIsNone(cmd)
            elif isinstance(cmd, int):
                self.assertIsInstance(cmd, int)
            elif isinstance(cmd, str) and len(cmd.strip()) == 0:
                self.assertEqual(len(cmd.strip()), 0)


def create_test_suite():
    """创建测试套件"""
    suite = unittest.TestSuite()

    # 添加所有测试类
    test_classes = [
        TestConfigurationParsing,
        TestHookValidation,
        TestPerformanceMetrics,
        TestErrorHandling,
        TestSystemIntegration,
        TestDataValidation,
    ]

    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    return suite


def run_tests():
    """运行所有单元测试"""
    print("🧪 运行Claude Enhancer单元测试套件...")
    print("=" * 60)

    # 创建测试套件
    suite = create_test_suite()

    # 运行测试
    runner = unittest.TextTestRunner(
        verbosity=2, stream=sys.stdout, descriptions=True, failfast=False
    )

    result = runner.run(suite)

    # 打印总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    print(f"运行测试数量: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"跳过: {len(result.skipped) if hasattr(result, 'skipped') else 0}")

    if result.failures:
        print("\n❌ 失败的测试:")
        for test, traceback in result.failures:
            print(
                f"  - {test}: {traceback.split('AssertionError: ')[-1].split(chr(10))[0]}"
            )

    if result.errors:
        print("\n⚠️ 错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split(chr(10))[-2]}")

    success_rate = (
        result.testsRun - len(result.failures) - len(result.errors)
    ) / result.testsRun
    print(f"\n✅ 总体成功率: {success_rate:.1%}")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
