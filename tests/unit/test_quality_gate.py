#!/usr/bin/env python3
"""
QualityGate 单元测试
测试质量门检查系统的所有功能
"""

import os
import sys
import pytest
import tempfile
import shutil
import subprocess
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from features.preventive_quality.quality_gate import (
    QualityGate, QualityCheck, CheckResult, CheckStatus, CheckSeverity
)

class TestQualityGate:
    """QualityGate 测试类"""

    @pytest.fixture
    def temp_project_dir(self):
        """创建临时项目目录"""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)

        # 创建基本项目结构
        (project_path / "main").mkdir()
        (project_path / "features").mkdir()
        (project_path / "modules").mkdir()
        (project_path / "core").mkdir()

        # 创建基本文件
        (project_path / "main" / "cli.py").write_text("#!/usr/bin/env python3\nprint('CLI')")
        (project_path / "main" / "perfect21.py").write_text("#!/usr/bin/env python3\nprint('Perfect21')")
        (project_path / "CLAUDE.md").write_text("# Perfect21 Documentation")

        # 设置执行权限
        os.chmod(project_path / "main" / "cli.py", 0o755)
        os.chmod(project_path / "main" / "perfect21.py", 0o755)

        yield project_path

        # 清理
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def quality_gate(self, temp_project_dir):
        """创建质量门实例"""
        return QualityGate(str(temp_project_dir))

    def test_quality_gate_initialization(self, quality_gate):
        """测试质量门初始化"""
        assert quality_gate is not None
        assert hasattr(quality_gate, 'checks')
        assert hasattr(quality_gate, 'project_root')
        assert len(quality_gate.checks) > 0

    def test_check_categories_complete(self, quality_gate):
        """测试检查类别完整性"""
        expected_categories = [
            'git', 'code_quality', 'workspace', 'environment',
            'dependencies', 'security'
        ]

        found_categories = set()
        for check in quality_gate.checks.values():
            found_categories.add(check.category)

        for category in expected_categories:
            assert category in found_categories

    def test_git_status_clean_check(self, quality_gate, temp_project_dir):
        """测试Git状态检查"""
        # 初始化Git仓库
        subprocess.run(['git', 'init'], cwd=str(temp_project_dir), capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'],
                      cwd=str(temp_project_dir), capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'],
                      cwd=str(temp_project_dir), capture_output=True)

        # 测试干净状态
        result = quality_gate._check_git_status_clean()
        assert isinstance(result, CheckResult)
        assert result.check_name == "git_status_clean"

        # 添加未跟踪文件
        (temp_project_dir / "untracked.txt").write_text("untracked content")

        result = quality_gate._check_git_status_clean()
        assert result.status == CheckStatus.FAILED
        assert result.severity == CheckSeverity.WARNING

    def test_git_branch_valid_check(self, quality_gate, temp_project_dir):
        """测试Git分支有效性检查"""
        # 初始化Git仓库
        subprocess.run(['git', 'init'], cwd=str(temp_project_dir), capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'],
                      cwd=str(temp_project_dir), capture_output=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'],
                      cwd=str(temp_project_dir), capture_output=True)

        # 创建初始提交
        subprocess.run(['git', 'add', '.'], cwd=str(temp_project_dir), capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit'],
                      cwd=str(temp_project_dir), capture_output=True)

        # 创建符合规范的分支
        subprocess.run(['git', 'checkout', '-b', 'feature/test-branch'],
                      cwd=str(temp_project_dir), capture_output=True)

        result = quality_gate._check_git_branch_valid()
        assert isinstance(result, CheckResult)
        assert result.check_name == "git_branch_valid"

        # 测试无效分支名
        subprocess.run(['git', 'checkout', '-b', 'invalid-branch-name'],
                      cwd=str(temp_project_dir), capture_output=True)

        result = quality_gate._check_git_branch_valid()
        assert result.status == CheckStatus.FAILED
        assert result.severity == CheckSeverity.WARNING

    def test_python_syntax_check(self, quality_gate, temp_project_dir):
        """测试Python语法检查"""
        # 创建语法正确的Python文件
        (temp_project_dir / "valid.py").write_text("""
def hello():
    print("Hello, World!")

if __name__ == "__main__":
    hello()
""")

        # 创建语法错误的Python文件
        (temp_project_dir / "invalid.py").write_text("""
def hello(
    print("Syntax error - missing closing parenthesis")
""")

        result = quality_gate._check_python_syntax()
        assert isinstance(result, CheckResult)
        assert result.check_name == "syntax_check"
        assert result.status == CheckStatus.FAILED
        assert result.severity == CheckSeverity.ERROR
        assert len(result.details['syntax_errors']) > 0

        # 删除错误文件，再次测试
        (temp_project_dir / "invalid.py").unlink()

        result = quality_gate._check_python_syntax()
        assert result.status == CheckStatus.PASSED

    def test_python_imports_check(self, quality_gate, temp_project_dir):
        """测试Python导入检查"""
        # 创建有效的导入
        (temp_project_dir / "main" / "cli.py").write_text("""
import os
import sys
print("Valid imports")
""")

        result = quality_gate._check_python_imports()
        assert isinstance(result, CheckResult)
        assert result.check_name == "import_check"

        # 创建无效的导入
        (temp_project_dir / "main" / "cli.py").write_text("""
import nonexistent_module
print("Invalid import")
""")

        result = quality_gate._check_python_imports()
        assert result.status == CheckStatus.FAILED
        assert result.severity == CheckSeverity.ERROR

    def test_file_structure_check(self, quality_gate):
        """测试文件结构检查"""
        result = quality_gate._check_file_structure()
        assert isinstance(result, CheckResult)
        assert result.check_name == "file_structure"
        assert result.status == CheckStatus.PASSED

    def test_disk_space_check(self, quality_gate):
        """测试磁盘空间检查"""
        result = quality_gate._check_disk_space()
        assert isinstance(result, CheckResult)
        assert result.check_name == "disk_space"
        # 在正常系统上应该通过
        assert result.status in [CheckStatus.PASSED, CheckStatus.FAILED]

    def test_python_version_check(self, quality_gate):
        """测试Python版本检查"""
        result = quality_gate._check_python_version()
        assert isinstance(result, CheckResult)
        assert result.check_name == "python_version"
        # 应该检测到当前Python版本
        assert 'current_version' in result.details

    def test_perfect21_structure_check(self, quality_gate):
        """测试Perfect21结构检查"""
        result = quality_gate._check_perfect21_structure()
        assert isinstance(result, CheckResult)
        assert result.check_name == "perfect21_structure"
        # 基本结构应该存在
        assert result.status == CheckStatus.PASSED

    def test_core_agents_available_check(self, quality_gate, temp_project_dir):
        """测试核心Agent可用性检查"""
        # 创建agents目录结构
        agents_dir = temp_project_dir / "core" / "claude-code-unified-agents" / ".claude" / "agents"
        agents_dir.mkdir(parents=True)

        # 创建一些agent文件
        business_dir = agents_dir / "business"
        business_dir.mkdir()
        (business_dir / "project-manager.md").write_text("# Project Manager")
        (business_dir / "business-analyst.md").write_text("# Business Analyst")

        development_dir = agents_dir / "development"
        development_dir.mkdir()
        (development_dir / "backend-architect.md").write_text("# Backend Architect")

        result = quality_gate._check_core_agents_available()
        assert isinstance(result, CheckResult)
        assert result.check_name == "core_agents_available"
        # 由于只有少量agents，应该失败
        assert result.status == CheckStatus.FAILED

    def test_sensitive_files_check(self, quality_gate, temp_project_dir):
        """测试敏感文件检查"""
        # 创建一些敏感文件
        (temp_project_dir / "secret.key").write_text("secret content")
        (temp_project_dir / ".env").write_text("API_KEY=secret")

        result = quality_gate._check_sensitive_files()
        assert isinstance(result, CheckResult)
        assert result.check_name == "sensitive_files"
        assert result.status == CheckStatus.FAILED
        assert len(result.details['sensitive_files']) > 0

        # 删除敏感文件
        (temp_project_dir / "secret.key").unlink()
        (temp_project_dir / ".env").unlink()

        result = quality_gate._check_sensitive_files()
        assert result.status == CheckStatus.PASSED

    def test_file_permissions_check(self, quality_gate):
        """测试文件权限检查"""
        result = quality_gate._check_file_permissions()
        assert isinstance(result, CheckResult)
        assert result.check_name == "permissions"
        # 在正常设置下应该通过
        assert result.status in [CheckStatus.PASSED, CheckStatus.FAILED]

    def test_run_checks_all(self, quality_gate):
        """测试运行所有检查"""
        results = quality_gate.run_checks()
        assert len(results) > 0

        # 验证结果结构
        for result in results:
            assert isinstance(result, CheckResult)
            assert hasattr(result, 'check_name')
            assert hasattr(result, 'status')
            assert hasattr(result, 'severity')
            assert hasattr(result, 'message')
            assert hasattr(result, 'execution_time')

    def test_run_checks_by_category(self, quality_gate):
        """测试按类别运行检查"""
        # 只运行Git相关检查
        results = quality_gate.run_checks(categories=['git'])
        assert len(results) > 0

        # 验证所有结果都是Git类别
        git_check_names = ['git_status_clean', 'git_branch_valid', 'git_remote_sync']
        for result in results:
            check = quality_gate.checks[result.check_name]
            assert check.category == 'git'

    def test_run_checks_by_context(self, quality_gate):
        """测试按上下文运行检查"""
        # 运行Python相关检查
        results = quality_gate.run_checks(context='python')
        assert len(results) > 0

        # 验证包含Python相关检查
        python_related = ['syntax_check', 'import_check', 'python_version']
        found_python_checks = [r.check_name for r in results if r.check_name in python_related]
        assert len(found_python_checks) > 0

    def test_run_checks_enabled_only(self, quality_gate):
        """测试只运行启用的检查"""
        # 禁用一个检查
        quality_gate.checks['git_status_clean'].enabled = False

        results = quality_gate.run_checks(enabled_only=True)

        # 验证禁用的检查不在结果中
        check_names = [r.check_name for r in results]
        assert 'git_status_clean' not in check_names

    def test_check_dependency_sorting(self, quality_gate):
        """测试检查依赖关系排序"""
        # 创建有依赖的检查列表
        checks = [
            quality_gate.checks['git_remote_sync'],  # 依赖 git_branch_valid
            quality_gate.checks['git_branch_valid'],  # 无依赖
            quality_gate.checks['import_check'],      # 依赖 syntax_check
            quality_gate.checks['syntax_check']      # 无依赖
        ]

        sorted_checks = quality_gate._sort_checks_by_dependencies(checks)

        # 验证依赖顺序
        check_names = [c.name for c in sorted_checks]
        git_branch_index = check_names.index('git_branch_valid')
        git_remote_index = check_names.index('git_remote_sync')
        assert git_branch_index < git_remote_index

        syntax_index = check_names.index('syntax_check')
        import_index = check_names.index('import_check')
        assert syntax_index < import_index

    def test_get_check_summary(self, quality_gate):
        """测试检查摘要生成"""
        # 运行一些检查
        results = quality_gate.run_checks(categories=['environment'])
        summary = quality_gate.get_check_summary(results)

        # 验证摘要结构
        assert '总检查数' in summary
        assert '通过' in summary
        assert '失败' in summary
        assert '跳过' in summary
        assert '成功率' in summary
        assert '按严重程度统计' in summary
        assert '按类别统计' in summary
        assert '总执行时间' in summary

        # 验证数值正确
        total = summary['总检查数']
        passed = summary['通过']
        failed = summary['失败']
        skipped = summary['跳过']
        assert total == passed + failed + skipped

    def test_workspace_checks_unavailable(self, quality_gate):
        """测试工作空间检查不可用时的处理"""
        # 工作空间模块可能不存在，检查应该被跳过
        result = quality_gate._check_workspace_conflicts()
        assert isinstance(result, CheckResult)
        assert result.check_name == "workspace_conflicts"
        # 应该被跳过或失败，但不应该抛出异常

        result = quality_gate._check_workspace_ports()
        assert isinstance(result, CheckResult)
        assert result.check_name == "workspace_ports"

    def test_check_result_structure(self, quality_gate):
        """测试检查结果结构"""
        result = quality_gate._check_python_version()

        # 验证CheckResult的所有字段
        assert hasattr(result, 'check_name')
        assert hasattr(result, 'status')
        assert hasattr(result, 'severity')
        assert hasattr(result, 'message')
        assert hasattr(result, 'details')
        assert hasattr(result, 'suggestions')
        assert hasattr(result, 'execution_time')
        assert hasattr(result, 'timestamp')

        # 验证字段类型
        assert isinstance(result.check_name, str)
        assert isinstance(result.status, CheckStatus)
        assert isinstance(result.severity, CheckSeverity)
        assert isinstance(result.message, str)
        assert isinstance(result.details, dict)
        assert isinstance(result.suggestions, list)
        assert isinstance(result.execution_time, (int, float))
        assert isinstance(result.timestamp, str)

    def test_error_handling_in_checks(self, quality_gate):
        """测试检查中的错误处理"""
        # 模拟文件系统错误
        with patch('pathlib.Path.rglob') as mock_rglob:
            mock_rglob.side_effect = PermissionError("Access denied")

            result = quality_gate._check_python_syntax()
            # 应该处理错误而不崩溃
            assert isinstance(result, CheckResult)

    def test_performance_of_checks(self, quality_gate):
        """测试检查性能"""
        import time

        start_time = time.time()
        results = quality_gate.run_checks(categories=['environment'])
        execution_time = time.time() - start_time

        # 环境检查应该很快完成
        assert execution_time < 5.0  # 5秒内完成
        assert len(results) > 0

        # 验证每个检查的执行时间都被记录
        for result in results:
            assert result.execution_time >= 0

    def test_concurrent_checks(self, quality_gate):
        """测试并发检查能力"""
        import threading
        import queue

        results_queue = queue.Queue()

        def run_category_checks(category):
            results = quality_gate.run_checks(categories=[category])
            results_queue.put(results)

        # 并发运行不同类别的检查
        categories = ['environment', 'code_quality', 'security']
        threads = []

        for category in categories:
            thread = threading.Thread(target=run_category_checks, args=(category,))
            threads.append(thread)
            thread.start()

        # 等待完成
        for thread in threads:
            thread.join()

        # 收集结果
        all_results = []
        while not results_queue.empty():
            results = results_queue.get()
            all_results.extend(results)

        assert len(all_results) > 0

    @patch('subprocess.run')
    def test_git_command_failure_handling(self, mock_run, quality_gate):
        """测试Git命令失败处理"""
        # 模拟Git命令失败
        mock_run.side_effect = subprocess.CalledProcessError(1, 'git', stderr='Not a git repository')

        result = quality_gate._check_git_status_clean()
        assert result.status == CheckStatus.FAILED
        assert result.severity == CheckSeverity.ERROR

    def test_quality_check_object_creation(self):
        """测试QualityCheck对象创建"""
        def dummy_check():
            return CheckResult(
                check_name="test_check",
                status=CheckStatus.PASSED,
                severity=CheckSeverity.INFO,
                message="Test message",
                details={},
                suggestions=[],
                execution_time=0.1,
                timestamp="2023-01-01T00:00:00"
            )

        check = QualityCheck(
            name="test_check",
            description="A test check",
            category="test",
            severity=CheckSeverity.INFO,
            enabled=True,
            check_function=dummy_check,
            dependencies=[],
            applicable_contexts=["test"]
        )

        assert check.name == "test_check"
        assert check.enabled is True
        assert callable(check.check_function)

        # 测试执行
        result = check.check_function()
        assert isinstance(result, CheckResult)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])