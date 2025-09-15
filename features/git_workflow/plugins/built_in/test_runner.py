#!/usr/bin/env python3
"""
Perfect21 Git Hooks - Test Runner Plugin
测试运行插件，支持多种测试框架
"""

import os
import json
import subprocess
from typing import Dict, Any, List, Optional, Tuple

try:
    from ..base_plugin import (
        TestPlugin, PluginResult, PluginStatus, PluginMetadata, PluginPriority
    )
except ImportError:
    from features.git_workflow.plugins.base_plugin import (
        TestPlugin, PluginResult, PluginStatus, PluginMetadata, PluginPriority
    )


class TestRunnerPlugin(TestPlugin):
    """测试运行插件"""

    def _get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="test_runner",
            version="2.1.0",
            description="多测试框架支持的测试运行器",
            author="Perfect21 Team",
            category="testing",
            priority=PluginPriority.HIGH,
            dependencies=["python:subprocess"],
            supports_parallel=True,
            timeout=300
        )

    def execute(self, context: Dict[str, Any]) -> PluginResult:
        """执行测试"""
        staged_files = self.get_staged_files()

        # 检测项目类型和测试框架
        test_framework = self._detect_test_framework()

        if not test_framework:
            return PluginResult(
                status=PluginStatus.SKIPPED,
                message="未检测到支持的测试框架"
            )

        # 根据配置决定运行哪些测试
        test_scope = self._determine_test_scope(staged_files, context)

        if not test_scope['should_run']:
            return PluginResult(
                status=PluginStatus.SKIPPED,
                message=test_scope['reason']
            )

        # 运行测试
        test_results = []

        for test_command in test_scope['commands']:
            result = self._run_test_command(test_command, test_framework)
            test_results.append(result)

        # 分析结果
        overall_result = self._analyze_test_results(test_results)

        return overall_result

    def _detect_test_framework(self) -> Optional[Dict[str, Any]]:
        """检测测试框架"""
        frameworks = [
            {
                'name': 'pytest',
                'command': 'pytest',
                'config_files': ['pytest.ini', 'pyproject.toml', 'setup.cfg'],
                'test_patterns': ['test_*.py', '*_test.py'],
                'check_command': 'python -m pytest --version'
            },
            {
                'name': 'unittest',
                'command': 'python -m unittest',
                'config_files': [],
                'test_patterns': ['test_*.py', '*_test.py'],
                'check_command': 'python -c "import unittest"'
            },
            {
                'name': 'jest',
                'command': 'npm test',
                'config_files': ['jest.config.js', 'package.json'],
                'test_patterns': ['*.test.js', '*.spec.js'],
                'check_command': 'npm list jest'
            },
            {
                'name': 'mocha',
                'command': 'npx mocha',
                'config_files': ['.mocharc.json', 'mocha.opts'],
                'test_patterns': ['*.test.js', '*.spec.js'],
                'check_command': 'npm list mocha'
            },
            {
                'name': 'cargo_test',
                'command': 'cargo test',
                'config_files': ['Cargo.toml'],
                'test_patterns': ['**/tests/*.rs'],
                'check_command': 'cargo --version'
            },
            {
                'name': 'go_test',
                'command': 'go test',
                'config_files': ['go.mod'],
                'test_patterns': ['*_test.go'],
                'check_command': 'go version'
            }
        ]

        for framework in frameworks:
            if self._check_framework_available(framework):
                return framework

        return None

    def _check_framework_available(self, framework: Dict[str, Any]) -> bool:
        """检查测试框架是否可用"""
        # 检查配置文件
        for config_file in framework['config_files']:
            if os.path.exists(config_file):
                try:
                    # 尝试运行检查命令
                    subprocess.run(
                        framework['check_command'].split(),
                        capture_output=True,
                        timeout=10,
                        check=True
                    )
                    return True
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
                    continue

        # 检查是否有测试文件
        import glob
        for pattern in framework['test_patterns']:
            if glob.glob(pattern, recursive=True):
                try:
                    subprocess.run(
                        framework['check_command'].split(),
                        capture_output=True,
                        timeout=10,
                        check=True
                    )
                    return True
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
                    continue

        return False

    def _determine_test_scope(self, staged_files: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """确定测试范围"""
        test_mode = self.get_config_value('test_mode', 'auto')
        coverage_threshold = self.get_config_value('coverage_threshold', 80)
        parallel_jobs = self.get_config_value('parallel_jobs', 4)

        # 检查是否有代码更改
        code_files = [f for f in staged_files if self._is_code_file(f)]

        if not code_files and test_mode == 'auto':
            return {
                'should_run': False,
                'reason': '没有代码文件变更，跳过测试',
                'commands': []
            }

        # 根据文件变更确定测试命令
        commands = []

        if test_mode == 'all':
            # 运行所有测试
            base_command = self.get_config_value('test_command', 'python -m pytest')
            commands.append(f"{base_command} -n {parallel_jobs}")

        elif test_mode == 'affected':
            # 只运行相关测试
            affected_tests = self._find_affected_tests(code_files)
            if affected_tests:
                base_command = self.get_config_value('test_command', 'python -m pytest')
                for test_file in affected_tests:
                    commands.append(f"{base_command} {test_file}")
            else:
                return {
                    'should_run': False,
                    'reason': '没有找到相关的测试文件',
                    'commands': []
                }

        else:  # auto模式
            # 智能确定测试范围
            if len(code_files) > 10:
                # 大量文件变更，运行所有测试
                base_command = self.get_config_value('test_command', 'python -m pytest')
                commands.append(f"{base_command} -n {parallel_jobs}")
            else:
                # 少量文件变更，运行相关测试
                affected_tests = self._find_affected_tests(code_files)
                if affected_tests:
                    base_command = self.get_config_value('test_command', 'python -m pytest')
                    commands.extend(f"{base_command} {test_file}" for test_file in affected_tests)
                else:
                    # 没有相关测试，运行快速测试
                    base_command = self.get_config_value('test_command', 'python -m pytest')
                    commands.append(f"{base_command} -x --ff")

        return {
            'should_run': len(commands) > 0,
            'reason': f'将运行 {len(commands)} 个测试命令',
            'commands': commands
        }

    def _is_code_file(self, file_path: str) -> bool:
        """判断是否为代码文件"""
        code_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h', '.rs', '.go'}
        return any(file_path.endswith(ext) for ext in code_extensions)

    def _find_affected_tests(self, code_files: List[str]) -> List[str]:
        """查找受影响的测试文件"""
        affected_tests = []

        for code_file in code_files:
            # 基于文件名推断测试文件
            test_candidates = self._generate_test_candidates(code_file)

            for candidate in test_candidates:
                if os.path.exists(candidate) and candidate not in affected_tests:
                    affected_tests.append(candidate)

        return affected_tests

    def _generate_test_candidates(self, code_file: str) -> List[str]:
        """生成可能的测试文件路径"""
        candidates = []

        file_dir = os.path.dirname(code_file)
        file_name = os.path.basename(code_file)
        name_without_ext = os.path.splitext(file_name)[0]

        # 常见的测试文件命名模式
        patterns = [
            f"test_{file_name}",
            f"{name_without_ext}_test.py",
            f"test_{name_without_ext}.py",
        ]

        # 常见的测试目录
        test_dirs = [
            "tests",
            "test",
            "__tests__",
            file_dir,
            os.path.join(file_dir, "tests"),
            os.path.join(file_dir, "test"),
        ]

        for test_dir in test_dirs:
            for pattern in patterns:
                candidate = os.path.join(test_dir, pattern)
                candidates.append(candidate)

        return candidates

    def _run_test_command(self, command: str, framework: Dict[str, Any]) -> Dict[str, Any]:
        """运行单个测试命令"""
        import time

        start_time = time.time()

        try:
            result = subprocess.run(
                command.split(),
                capture_output=True,
                text=True,
                timeout=self.metadata.timeout
            )

            execution_time = time.time() - start_time

            # 解析测试结果
            parsed_result = self._parse_test_output(
                result.stdout, result.stderr, framework['name']
            )

            return {
                "command": command,
                "exit_code": result.returncode,
                "execution_time": execution_time,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0,
                "parsed": parsed_result
            }

        except subprocess.TimeoutExpired:
            return {
                "command": command,
                "exit_code": -1,
                "execution_time": time.time() - start_time,
                "stdout": "",
                "stderr": f"测试超时 ({self.metadata.timeout}s)",
                "success": False,
                "parsed": {"tests_run": 0, "failures": 1, "errors": 0}
            }

        except Exception as e:
            return {
                "command": command,
                "exit_code": -1,
                "execution_time": time.time() - start_time,
                "stdout": "",
                "stderr": f"测试执行错误: {str(e)}",
                "success": False,
                "parsed": {"tests_run": 0, "failures": 1, "errors": 0}
            }

    def _parse_test_output(self, stdout: str, stderr: str, framework: str) -> Dict[str, Any]:
        """解析测试输出"""
        if framework == 'pytest':
            return self._parse_pytest_output(stdout + stderr)
        elif framework == 'unittest':
            return self._parse_unittest_output(stdout + stderr)
        elif framework in ['jest', 'mocha']:
            return self._parse_js_test_output(stdout + stderr)
        else:
            return self._parse_generic_output(stdout + stderr)

    def _parse_pytest_output(self, output: str) -> Dict[str, Any]:
        """解析pytest输出"""
        result = {"tests_run": 0, "failures": 0, "errors": 0, "passed": 0, "skipped": 0}

        # 查找测试结果汇总行
        import re

        # pytest格式: "= 5 failed, 10 passed, 2 skipped in 1.23s ="
        summary_pattern = r'(\d+)\s+(failed|passed|skipped|error)'
        matches = re.findall(summary_pattern, output, re.IGNORECASE)

        for count, status in matches:
            count = int(count)
            status = status.lower()

            if status == 'passed':
                result['passed'] = count
            elif status == 'failed':
                result['failures'] = count
            elif status == 'error':
                result['errors'] = count
            elif status == 'skipped':
                result['skipped'] = count

        result['tests_run'] = result['passed'] + result['failures'] + result['errors'] + result['skipped']

        return result

    def _parse_unittest_output(self, output: str) -> Dict[str, Any]:
        """解析unittest输出"""
        result = {"tests_run": 0, "failures": 0, "errors": 0}

        import re

        # unittest格式: "Ran 10 tests in 1.234s"
        run_match = re.search(r'Ran (\d+) tests? in', output)
        if run_match:
            result['tests_run'] = int(run_match.group(1))

        # 查找失败和错误
        if 'FAILED (failures=' in output:
            failures_match = re.search(r'failures=(\d+)', output)
            if failures_match:
                result['failures'] = int(failures_match.group(1))

        if 'errors=' in output:
            errors_match = re.search(r'errors=(\d+)', output)
            if errors_match:
                result['errors'] = int(errors_match.group(1))

        return result

    def _parse_js_test_output(self, output: str) -> Dict[str, Any]:
        """解析JavaScript测试输出"""
        result = {"tests_run": 0, "failures": 0, "errors": 0, "passed": 0}

        import re

        # Jest/Mocha常见格式
        patterns = [
            r'(\d+) passing',
            r'(\d+) failing',
            r'(\d+) tests?.*passed',
            r'(\d+) tests?.*failed',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, output, re.IGNORECASE)
            for match in matches:
                count = int(match)
                if 'pass' in pattern:
                    result['passed'] = count
                elif 'fail' in pattern:
                    result['failures'] = count

        result['tests_run'] = result['passed'] + result['failures']

        return result

    def _parse_generic_output(self, output: str) -> Dict[str, Any]:
        """通用输出解析"""
        # 简单的启发式解析
        result = {"tests_run": 0, "failures": 0, "errors": 0}

        # 统计关键词出现次数
        output_lower = output.lower()
        result['failures'] = output_lower.count('fail')
        result['errors'] = output_lower.count('error')

        return result

    def _analyze_test_results(self, test_results: List[Dict[str, Any]]) -> PluginResult:
        """分析测试结果"""
        total_tests = sum(r['parsed']['tests_run'] for r in test_results)
        total_failures = sum(r['parsed']['failures'] for r in test_results)
        total_errors = sum(r['parsed']['errors'] for r in test_results)
        total_time = sum(r['execution_time'] for r in test_results)

        successful_commands = sum(1 for r in test_results if r['success'])
        total_commands = len(test_results)

        # 生成报告
        report = self._generate_test_report(test_results)

        # 判断结果
        if total_failures > 0 or total_errors > 0:
            status = PluginStatus.FAILURE
            message = f"测试失败: {total_failures} 个失败, {total_errors} 个错误"
        elif successful_commands < total_commands:
            status = PluginStatus.FAILURE
            message = f"测试命令执行失败: {successful_commands}/{total_commands}"
        elif total_tests == 0:
            status = PluginStatus.WARNING
            message = "没有运行任何测试"
        else:
            status = PluginStatus.SUCCESS
            message = f"所有测试通过: {total_tests} 个测试"

        return PluginResult(
            status=status,
            message=message,
            execution_time=total_time,
            details={
                "total_tests": total_tests,
                "total_failures": total_failures,
                "total_errors": total_errors,
                "successful_commands": successful_commands,
                "total_commands": total_commands,
                "execution_time": total_time,
                "report": report,
                "results": test_results
            }
        )

    def _generate_test_report(self, test_results: List[Dict[str, Any]]) -> str:
        """生成测试报告"""
        total_tests = sum(r['parsed']['tests_run'] for r in test_results)
        total_failures = sum(r['parsed']['failures'] for r in test_results)
        total_errors = sum(r['parsed']['errors'] for r in test_results)
        passed_tests = total_tests - total_failures - total_errors
        total_time = sum(r['execution_time'] for r in test_results)

        success_rate = (passed_tests / max(total_tests, 1)) * 100

        report = f"""
🧪 测试执行报告
==============
执行命令: {len(test_results)}
总测试数: {total_tests}
通过: {passed_tests} | 失败: {total_failures} | 错误: {total_errors}
成功率: {success_rate:.1f}%
执行时间: {total_time:.2f}s

📊 详细结果:
"""

        for i, result in enumerate(test_results, 1):
            status_icon = "✅" if result['success'] else "❌"
            parsed = result['parsed']

            report += f"""
{status_icon} 命令 {i}: {result['command'][:50]}...
  测试: {parsed.get('tests_run', 0)} | 失败: {parsed.get('failures', 0)} | 错误: {parsed.get('errors', 0)}
  时间: {result['execution_time']:.2f}s | 退出码: {result['exit_code']}
"""

            # 显示错误信息
            if not result['success'] and result['stderr']:
                error_lines = result['stderr'].split('\n')[:3]
                for line in error_lines:
                    if line.strip():
                        report += f"  🔍 {line.strip()}\n"

        return report.strip()