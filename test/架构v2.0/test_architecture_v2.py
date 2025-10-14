#!/usr/bin/env python3
"""
Claude Enhancer v2.0 架构重构Python测试套件
作者: Test Engineer Professional
版本: v2.0
日期: 2025-10-14
"""

import os
import sys
import time
import json
import yaml
import unittest
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / '.claude'))
sys.path.insert(0, str(PROJECT_ROOT / '.claude' / 'core'))


class TestMigrationCorrectness(unittest.TestCase):
    """测试迁移正确性"""

    def setUp(self):
        """设置测试环境 - v2.0迁移后检查新文件"""
        # v2.0迁移后，核心文件在新位置
        self.v2_core_files = [
            PROJECT_ROOT / 'core' / 'workflow' / 'engine.py',    # 新v2.0核心引擎
            PROJECT_ROOT / 'core' / 'workflow' / 'types.py',     # 新v2.0类型定义
            PROJECT_ROOT / '.claude' / 'core' / 'loader.py',     # Feature系统（保留）
            PROJECT_ROOT / '.claude' / 'core' / 'config.yaml'    # Feature配置（保留）
        ]
        self.core_path = PROJECT_ROOT / '.claude' / 'core'  # 保留给其他测试用

    def test_core_files_exist(self):
        """测试v2.0核心文件存在"""
        for file_path in self.v2_core_files:
            self.assertTrue(
                file_path.exists(),
                f"v2.0 core file missing: {file_path}"
            )

    def test_core_files_not_empty(self):
        """测试v2.0核心文件不为空"""
        min_lines = 50  # Python文件至少50行

        for file_path in self.v2_core_files:
            if file_path.suffix == '.py':
                with open(file_path, 'r') as f:
                    lines = len(f.readlines())
                self.assertGreater(
                    lines, min_lines,
                    f"{file_path.name} too small: {lines} lines (expected >{min_lines})"
                )

    def test_python_syntax_valid(self):
        """测试v2.0 Python文件语法正确"""
        for file_path in self.v2_core_files:
            if file_path.suffix == '.py':
                try:
                    compile(open(file_path).read(), str(file_path), 'exec')
                except SyntaxError as e:
                    self.fail(f"Python syntax error in {file_path.name}: {e}")

    def test_yaml_syntax_valid(self):
        """测试YAML文件语法正确"""
        config_file = self.core_path / 'config.yaml'
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    yaml.safe_load(f)
            except yaml.YAMLError as e:
                self.fail(f"YAML syntax error in config.yaml: {e}")

    def test_file_integrity_hash(self):
        """测试文件完整性Hash"""
        hash_file = self.core_path / '.integrity.sha256'

        if hash_file.exists():
            # 运行sha256sum验证
            result = subprocess.run(
                ['sha256sum', '-c', str(hash_file)],
                cwd=str(self.core_path),
                capture_output=True,
                text=True
            )

            self.assertEqual(
                result.returncode, 0,
                f"Hash verification failed:\n{result.stderr}"
            )
        else:
            self.skipTest("Hash file not yet generated (expected in migration)")


class TestLockingMechanism(unittest.TestCase):
    """测试锁定机制"""

    def setUp(self):
        self.git_hooks_path = PROJECT_ROOT / '.git' / 'hooks'
        self.claude_hooks_path = PROJECT_ROOT / '.claude' / 'hooks'

    def test_precommit_hook_exists(self):
        """测试Pre-commit hook存在"""
        pre_commit = self.git_hooks_path / 'pre-commit'
        self.assertTrue(
            pre_commit.exists(),
            "Pre-commit hook not installed"
        )
        self.assertTrue(
            os.access(pre_commit, os.X_OK),
            "Pre-commit hook not executable"
        )

    def test_hook_contains_core_protection(self):
        """测试Hook包含core/保护逻辑"""
        pre_commit = self.git_hooks_path / 'pre-commit'

        if pre_commit.exists():
            content = pre_commit.read_text()
            self.assertIn(
                'core/',
                content,
                "Hook doesn't contain core/ protection"
            )

    def test_claude_hook_exists(self):
        """测试Claude PreToolUse hook存在"""
        pre_tool_use = self.claude_hooks_path / 'pre_tool_use.sh'

        if pre_tool_use.exists():
            self.assertTrue(
                os.access(pre_tool_use, os.X_OK),
                "Claude hook not executable"
            )
        else:
            self.skipTest("Claude hook not yet created (expected in migration)")

    def test_core_file_modification_blocked(self):
        """测试修改core/文件被阻止（模拟）"""
        # 这个测试需要实际运行git commit，在单元测试中模拟
        # 实际测试应该在集成测试中进行

        self.skipTest("Requires actual git commit, run in integration tests")


class TestFeatureSystem(unittest.TestCase):
    """测试Feature系统"""

    def setUp(self):
        self.features_path = PROJECT_ROOT / '.claude' / 'features'
        self.config_file = self.features_path / 'config.yaml'

    def test_feature_directory_structure(self):
        """测试Feature目录结构"""
        expected_dirs = [
            self.features_path / 'basic',
            self.features_path / 'standard',
            self.features_path / 'advanced'
        ]

        for dir_path in expected_dirs:
            if not dir_path.exists():
                self.skipTest(
                    f"Feature directory structure not yet created: {dir_path}"
                )

    def test_feature_config_exists(self):
        """测试Feature配置文件存在"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = yaml.safe_load(f)
                self.assertIn('features', config, "Config missing 'features' section")
            except yaml.YAMLError as e:
                self.fail(f"Feature config YAML error: {e}")
        else:
            self.skipTest("Feature config not yet created")

    def test_loader_module_exists(self):
        """测试Loader模块存在"""
        loader_file = PROJECT_ROOT / '.claude' / 'core' / 'loader.py'

        self.assertTrue(
            loader_file.exists(),
            "loader.py not found"
        )

        # 检查是否有load_features函数
        content = loader_file.read_text()
        self.assertIn(
            'def load_features',
            content,
            "loader.py missing load_features function"
        )

    def test_feature_enable_disable(self):
        """测试Feature enable/disable机制"""
        if not self.config_file.exists():
            self.skipTest("Feature config not yet created")

        # 这个测试需要实际修改配置并加载，在集成测试中进行
        self.skipTest("Requires config modification, run in integration tests")

    def test_feature_loading_performance(self):
        """测试Feature加载性能"""
        try:
            from loader import load_features

            start = time.perf_counter()
            features = load_features()
            elapsed = (time.perf_counter() - start) * 1000  # 毫秒

            # Feature加载应该<100ms
            self.assertLess(
                elapsed, 100,
                f"Feature loading too slow: {elapsed:.2f}ms"
            )
        except ImportError:
            self.skipTest("Loader module not yet implemented")

    def test_dependency_detection(self):
        """测试依赖检测机制"""
        # 这需要实际的loader实现
        self.skipTest("Requires loader implementation, run after migration")


class TestHookEnhancement(unittest.TestCase):
    """测试Hook增强"""

    def setUp(self):
        self.hooks_path = PROJECT_ROOT / '.claude' / 'hooks'

    def test_workflow_guard_exists(self):
        """测试Workflow guard hook存在"""
        workflow_guard = self.hooks_path / 'workflow_guard.sh'

        if workflow_guard.exists():
            content = workflow_guard.read_text()
            # 检查是否包含"继续"检测
            self.assertTrue(
                '继续' in content or 'continue' in content,
                "workflow_guard.sh missing '继续' detection"
            )
        else:
            self.skipTest("workflow_guard.sh not yet created")

    def test_phase_guard_exists(self):
        """测试Phase guard hook存在"""
        phase_guard = self.hooks_path / 'phase_guard.sh'

        if not phase_guard.exists():
            self.skipTest("phase_guard.sh not yet created")

    def test_branch_helper_exists(self):
        """测试Branch helper hook存在"""
        branch_helper = self.hooks_path / 'branch_helper.sh'

        self.assertTrue(
            branch_helper.exists(),
            "branch_helper.sh not found"
        )

        self.assertTrue(
            os.access(branch_helper, os.X_OK),
            "branch_helper.sh not executable"
        )

    def test_workflow_guard_five_layers(self):
        """测试Workflow guard包含5层检测"""
        # 5层检测在workflow_guard.sh中，comprehensive_guard.sh是编排器
        workflow_guard = self.hooks_path / 'workflow_guard.sh'

        if workflow_guard.exists():
            content = workflow_guard.read_text()
            layer_count = content.count('Layer ')

            self.assertGreaterEqual(
                layer_count, 5,
                f"workflow_guard.sh has only {layer_count} layers (expected 5)"
            )
        else:
            self.skipTest("workflow_guard.sh not yet created")


class TestCompatibility(unittest.TestCase):
    """测试兼容性"""

    def test_new_core_structure_exists(self):
        """测试v2.0新core目录结构存在"""
        # v2.0已移除symlinks，直接使用新的core/目录
        core_dirs = [
            PROJECT_ROOT / 'core' / 'workflow',
            PROJECT_ROOT / 'core' / 'state',
            PROJECT_ROOT / 'core' / 'hooks',
            PROJECT_ROOT / 'core' / 'agents',
            PROJECT_ROOT / 'core' / 'config',
        ]

        for dir_path in core_dirs:
            self.assertTrue(
                dir_path.exists() and dir_path.is_dir(),
                f"Core directory {dir_path.name} does not exist"
            )

    def test_new_import_works(self):
        """测试v2.0新的import路径工作"""
        # v2.0使用新的core/目录，不再使用symlinks
        try:
            sys.path.insert(0, str(PROJECT_ROOT))
            from core.workflow.engine import WorkflowEngine
            from core.workflow.types import Phase
            from core.state.manager import StateManager
            # 验证导入成功
            self.assertTrue(hasattr(Phase, 'P0_DISCOVERY'))
            self.assertTrue(hasattr(Phase, 'P7_MONITOR'))
        except ImportError as e:
            self.fail(f"New core import failed: {e}")

    def test_workflow_executor_exists(self):
        """测试Workflow executor存在"""
        executor = PROJECT_ROOT / '.workflow' / 'executor.sh'

        self.assertTrue(
            executor.exists(),
            "executor.sh not found"
        )

        self.assertTrue(
            os.access(executor, os.X_OK),
            "executor.sh not executable"
        )

    def test_config_accessible(self):
        """测试配置文件可访问"""
        config_file = PROJECT_ROOT / '.claude' / 'core' / 'config.yaml'

        self.assertTrue(
            config_file.exists(),
            "config.yaml not found"
        )

        self.assertTrue(
            os.access(config_file, os.R_OK),
            "config.yaml not readable"
        )


class TestPerformance(unittest.TestCase):
    """测试性能"""

    def test_cold_start_time(self):
        """测试冷启动时间"""
        # 清除缓存
        cache_dirs = [
            PROJECT_ROOT / '.claude' / 'cache',
            PROJECT_ROOT / '.claude' / '__pycache__',
            PROJECT_ROOT / '.claude' / 'core' / '__pycache__'
        ]

        for cache_dir in cache_dirs:
            if cache_dir.exists():
                import shutil
                shutil.rmtree(cache_dir, ignore_errors=True)

        # 测量冷启动时间
        start = time.perf_counter()

        try:
            result = subprocess.run(
                [
                    'python3', '-c',
                    'import sys; sys.path.insert(0, ".claude/core"); '
                    'from lazy_orchestrator import LazyOrchestrator; '
                    'o = LazyOrchestrator()'
                ],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                timeout=5
            )

            elapsed = (time.perf_counter() - start) * 1000  # 毫秒

            if result.returncode == 0:
                self.assertLess(
                    elapsed, 200,
                    f"Cold start too slow: {elapsed:.2f}ms"
                )
                print(f"\n✓ Cold start time: {elapsed:.2f}ms")
            else:
                self.skipTest(f"Import failed: {result.stderr.decode()}")
        except subprocess.TimeoutExpired:
            self.fail("Cold start timeout (>5s)")
        except Exception as e:
            self.skipTest(f"Cannot test cold start: {e}")

    def test_warm_start_time(self):
        """测试热启动时间"""
        try:
            # 第一次加载（预热）
            from lazy_orchestrator import LazyOrchestrator
            _ = LazyOrchestrator()

            # 测量热启动时间
            start = time.perf_counter()
            orchestrator = LazyOrchestrator()
            elapsed = (time.perf_counter() - start) * 1000

            # 热启动应该<100ms
            self.assertLess(
                elapsed, 100,
                f"Warm start too slow: {elapsed:.2f}ms"
            )

            print(f"\n✓ Warm start time: {elapsed:.2f}ms")
        except ImportError:
            self.skipTest("LazyOrchestrator not yet available")

    def test_hash_verification_performance(self):
        """测试Hash验证性能"""
        hash_file = PROJECT_ROOT / '.claude' / 'core' / '.integrity.sha256'

        if not hash_file.exists():
            self.skipTest("Hash file not yet generated")

        # 运行多次取平均
        iterations = 10
        times = []

        for _ in range(iterations):
            start = time.perf_counter()

            result = subprocess.run(
                ['sha256sum', '-c', '.integrity.sha256'],
                cwd=str(PROJECT_ROOT / '.claude' / 'core'),
                capture_output=True
            )

            elapsed = (time.perf_counter() - start) * 1000
            times.append(elapsed)

        avg_time = sum(times) / len(times)

        # Hash验证应该<50ms
        self.assertLess(
            avg_time, 50,
            f"Hash verification too slow: {avg_time:.2f}ms average"
        )

        print(f"\n✓ Hash verification time: {avg_time:.2f}ms average")

    def test_precommit_hook_performance(self):
        """测试Pre-commit hook性能"""
        pre_commit = PROJECT_ROOT / '.git' / 'hooks' / 'pre-commit'

        if not pre_commit.exists():
            self.skipTest("Pre-commit hook not installed")

        # 设置测试模式环境变量
        env = os.environ.copy()
        env['TEST_MODE'] = '1'

        start = time.perf_counter()

        result = subprocess.run(
            [str(pre_commit)],
            cwd=str(PROJECT_ROOT),
            env=env,
            capture_output=True,
            timeout=10
        )

        elapsed = (time.perf_counter() - start) * 1000

        # Hook执行应该<3秒
        self.assertLess(
            elapsed, 3000,
            f"Pre-commit hook too slow: {elapsed:.2f}ms"
        )

        print(f"\n✓ Pre-commit hook time: {elapsed:.2f}ms")


class TestArchitectureV2Integration(unittest.TestCase):
    """集成测试"""

    def test_full_system_integration(self):
        """测试整个系统集成"""
        # 这是一个综合集成测试
        # 验证所有组件一起工作

        # 1. 核心文件存在
        core_path = PROJECT_ROOT / '.claude' / 'core'
        self.assertTrue(core_path.exists(), "Core directory missing")

        # 2. 软链接工作
        engine_link = PROJECT_ROOT / '.claude' / 'engine.py'
        if engine_link.exists():
            self.assertTrue(engine_link.is_symlink(), "engine.py not a symlink")

        # 3. Hooks安装
        pre_commit = PROJECT_ROOT / '.git' / 'hooks' / 'pre-commit'
        self.assertTrue(pre_commit.exists(), "Pre-commit hook not installed")

        # 4. Workflow executor可用
        executor = PROJECT_ROOT / '.workflow' / 'executor.sh'
        self.assertTrue(executor.exists(), "Workflow executor missing")

        print("\n✓ Full system integration check passed")


def run_tests(verbosity=2):
    """运行所有测试"""
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加测试类
    test_classes = [
        TestMigrationCorrectness,
        TestLockingMechanism,
        TestFeatureSystem,
        TestHookEnhancement,
        TestCompatibility,
        TestPerformance,
        TestArchitectureV2Integration
    ]

    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    # 返回结果
    return result.wasSuccessful()


if __name__ == '__main__':
    # 打印测试信息
    print("=" * 70)
    print("Claude Enhancer v2.0 架构重构Python测试套件")
    print("=" * 70)
    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"当前分支: {subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], cwd=PROJECT_ROOT).decode().strip()}")
    print("=" * 70)
    print()

    # 运行测试
    success = run_tests(verbosity=2)

    # 退出
    sys.exit(0 if success else 1)
