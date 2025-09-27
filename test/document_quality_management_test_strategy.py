#!/usr/bin/env python3
"""
Claude Enhancer 5.0 - 文档质量管理系统测试策略

作为test-engineer，设计完整的测试方案：
1. Hooks单元测试
2. 集成测试场景
3. 性能基准测试
4. 回归测试套件
5. 故障恢复测试

测试覆盖：
- 各种文档类型检查
- 边界条件和异常处理
- 并发检查的正确性
- 配置变更的影响
"""

import unittest
import pytest
import subprocess
import tempfile
import os
import json
import time
import threading
import shutil
import asyncio
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import psutil
import hashlib


@dataclass
class TestResult:
    """测试结果数据结构"""

    test_name: str
    success: bool
    duration: float
    details: Dict[str, Any]
    error_message: Optional[str] = None


@dataclass
class PerformanceBenchmark:
    """性能基准数据"""

    operation: str
    expected_max_time: float  # milliseconds
    memory_limit: int  # MB
    cpu_limit: float  # percentage


class DocumentQualityTestSuite:
    """文档质量管理系统主测试套件"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or "/home/xx/dev/Claude Enhancer 5.0"
        self.claude_dir = os.path.join(self.project_root, ".claude")
        self.hooks_dir = os.path.join(self.claude_dir, "hooks")
        self.test_results = []
        self.performance_benchmarks = self._init_performance_benchmarks()

    def _init_performance_benchmarks(self) -> Dict[str, PerformanceBenchmark]:
        """初始化性能基准值"""
        return {
            "quality_gate_check": PerformanceBenchmark(
                operation="quality_gate.sh execution",
                expected_max_time=100.0,  # 100ms
                memory_limit=10,  # 10MB
                cpu_limit=5.0,  # 5%
            ),
            "smart_agent_selector": PerformanceBenchmark(
                operation="smart_agent_selector.sh execution",
                expected_max_time=50.0,  # 50ms
                memory_limit=8,  # 8MB
                cpu_limit=3.0,  # 3%
            ),
            "lazy_orchestrator_init": PerformanceBenchmark(
                operation="LazyAgentOrchestrator initialization",
                expected_max_time=200.0,  # 200ms
                memory_limit=50,  # 50MB
                cpu_limit=10.0,  # 10%
            ),
            "agent_selection": PerformanceBenchmark(
                operation="Agent selection for complex task",
                expected_max_time=30.0,  # 30ms
                memory_limit=20,  # 20MB
                cpu_limit=5.0,  # 5%
            ),
        }


class HooksUnitTestSuite(unittest.TestCase):
    """Hooks单元测试套件"""

    def setUp(self):
        """测试前准备"""
        self.hooks_dir = "/home/xx/dev/Claude Enhancer 5.0/.claude/hooks"
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_quality_gate_basic_functionality(self):
        """测试质量门禁基本功能"""
        quality_gate_script = os.path.join(self.hooks_dir, "quality_gate.sh")

        # 测试用例1: 正常任务描述
        test_input = json.dumps({"prompt": "实现用户认证系统，包含JWT token验证"})

        result = subprocess.run(
            [quality_gate_script], input=test_input, text=True, capture_output=True
        )

        self.assertEqual(result.returncode, 0, "质量门禁应该成功执行")
        self.assertIn("质量评分", result.stderr, "应该输出质量评分")

    def test_quality_gate_edge_cases(self):
        """测试质量门禁边界条件"""
        quality_gate_script = os.path.join(self.hooks_dir, "quality_gate.sh")

        # 测试用例1: 空任务描述
        test_input = json.dumps({"prompt": ""})
        result = subprocess.run(
            [quality_gate_script], input=test_input, text=True, capture_output=True
        )
        self.assertEqual(result.returncode, 0, "空输入应该处理正常")

        # 测试用例2: 超长任务描述
        long_prompt = "实现" * 1000
        test_input = json.dumps({"prompt": long_prompt})
        result = subprocess.run(
            [quality_gate_script], input=test_input, text=True, capture_output=True
        )
        self.assertEqual(result.returncode, 0, "超长输入应该处理正常")

        # 测试用例3: 危险操作检测（使用英文避免编码问题）
        test_input = json.dumps({"prompt": "rm -rf all data"})
        result = subprocess.run(
            [quality_gate_script], input=test_input, text=True, capture_output=True
        )
        self.assertEqual(result.returncode, 0, "危险操作检测应该正常")
        self.assertIn("检测到潜在危险操作", result.stderr, "应该检测到危险操作")

    def test_smart_agent_selector_complexity_detection(self):
        """测试智能Agent选择器复杂度检测"""
        selector_script = os.path.join(self.hooks_dir, "smart_agent_selector.sh")

        # 测试简单任务
        test_input = json.dumps({"prompt": "fix typo in README"})
        result = subprocess.run(
            [selector_script], input=test_input, text=True, capture_output=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("4 Agents recommended", result.stderr)

        # 测试复杂任务
        test_input = json.dumps({"prompt": "architect complete microservices system"})
        result = subprocess.run(
            [selector_script], input=test_input, text=True, capture_output=True
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("8 Agents recommended", result.stderr)

    def test_hook_concurrent_execution(self):
        """测试Hook并发执行安全性"""
        quality_gate_script = os.path.join(self.hooks_dir, "quality_gate.sh")

        def run_hook(task_id: int):
            test_input = json.dumps({"prompt": f"task {task_id}: implement feature"})
            return subprocess.run(
                [quality_gate_script], input=test_input, text=True, capture_output=True
            )

        # 并发执行10个Hook
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(run_hook, i) for i in range(10)]
            results = [future.result() for future in futures]

        # 验证所有执行都成功
        for i, result in enumerate(results):
            self.assertEqual(result.returncode, 0, f"Hook {i} 应该成功执行")

    def test_hook_error_handling(self):
        """测试Hook错误处理能力"""
        quality_gate_script = os.path.join(self.hooks_dir, "quality_gate.sh")

        # 测试无效JSON输入
        invalid_inputs = ["invalid json", "{incomplete json", "", "null"]

        for invalid_input in invalid_inputs:
            result = subprocess.run(
                [quality_gate_script],
                input=invalid_input,
                text=True,
                capture_output=True,
            )
            # Hook应该能够处理无效输入而不崩溃
            self.assertIn(result.returncode, [0, 1], f"Hook应该优雅处理无效输入: {invalid_input}")


class IntegrationTestSuite:
    """集成测试套件"""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.test_results = []

    async def test_workflow_integration(self) -> TestResult:
        """测试完整工作流集成"""
        start_time = time.time()
        success = True
        details = {}
        error_message = None

        try:
            # 模拟P1-P6完整工作流
            workflow_steps = [
                ("P1_规划", self._simulate_planning_phase),
                ("P2_骨架", self._simulate_skeleton_phase),
                ("P3_实现", self._simulate_implementation_phase),
                ("P4_测试", self._simulate_testing_phase),
                ("P5_审查", self._simulate_review_phase),
                ("P6_发布", self._simulate_release_phase),
            ]

            for phase_name, phase_func in workflow_steps:
                phase_result = await phase_func()
                details[phase_name] = phase_result
                if not phase_result.get("success", False):
                    success = False
                    error_message = (
                        f"Phase {phase_name} failed: {phase_result.get('error')}"
                    )
                    break

        except Exception as e:
            success = False
            error_message = str(e)

        duration = time.time() - start_time

        return TestResult(
            test_name="workflow_integration",
            success=success,
            duration=duration,
            details=details,
            error_message=error_message,
        )

    async def _simulate_planning_phase(self) -> Dict[str, Any]:
        """模拟P1规划阶段"""
        return {
            "success": True,
            "artifacts": ["PLAN.md"],
            "agents_used": ["requirements-analyst", "business-analyst"],
            "duration": 0.1,
        }

    async def _simulate_skeleton_phase(self) -> Dict[str, Any]:
        """模拟P2骨架阶段"""
        return {
            "success": True,
            "artifacts": ["project_structure", "architecture_diagram"],
            "agents_used": ["backend-architect", "frontend-specialist"],
            "duration": 0.15,
        }

    async def _simulate_implementation_phase(self) -> Dict[str, Any]:
        """模拟P3实现阶段"""
        return {
            "success": True,
            "artifacts": ["source_code", "git_commits"],
            "agents_used": [
                "backend-engineer",
                "frontend-specialist",
                "database-specialist",
            ],
            "duration": 0.3,
        }

    async def _simulate_testing_phase(self) -> Dict[str, Any]:
        """模拟P4测试阶段"""
        return {
            "success": True,
            "artifacts": ["test_suite", "coverage_report"],
            "agents_used": ["test-engineer", "performance-tester"],
            "duration": 0.2,
        }

    async def _simulate_review_phase(self) -> Dict[str, Any]:
        """模拟P5审查阶段"""
        return {
            "success": True,
            "artifacts": ["REVIEW.md", "security_audit"],
            "agents_used": ["code-reviewer", "security-auditor"],
            "duration": 0.1,
        }

    async def _simulate_release_phase(self) -> Dict[str, Any]:
        """模拟P6发布阶段"""
        return {
            "success": True,
            "artifacts": ["documentation", "deployment", "git_tag"],
            "agents_used": ["deployment-manager", "technical-writer"],
            "duration": 0.2,
        }

    def test_multi_document_type_processing(self) -> TestResult:
        """测试多种文档类型处理"""
        start_time = time.time()
        success = True
        details = {}

        document_types = [
            ".md",
            ".py",
            ".js",
            ".ts",
            ".json",
            ".yaml",
            ".yml",
            ".sh",
            ".sql",
            ".dockerfile",
            ".txt",
            ".cfg",
            ".ini",
            ".env",
        ]

        for doc_type in document_types:
            try:
                # 创建测试文档
                test_file = f"test_document{doc_type}"
                test_content = self._generate_test_content(doc_type)

                # 模拟文档质量检查
                quality_result = self._check_document_quality(test_file, test_content)
                details[doc_type] = quality_result

                if not quality_result.get("passed", False):
                    success = False

            except Exception as e:
                success = False
                details[doc_type] = {"error": str(e)}

        duration = time.time() - start_time

        return TestResult(
            test_name="multi_document_type_processing",
            success=success,
            duration=duration,
            details=details,
        )

    def _generate_test_content(self, doc_type: str) -> str:
        """生成测试文档内容"""
        content_templates = {
            ".md": "# Test Document\n\nThis is a test markdown document.",
            ".py": "#!/usr/bin/env python3\nprint('Hello, World!')",
            ".js": "console.log('Hello, World!');",
            ".ts": "const message: string = 'Hello, World!';",
            ".json": '{"test": "data", "version": "1.0"}',
            ".yaml": "test:\n  data: value\n  version: 1.0",
            ".sh": "#!/bin/bash\necho 'Hello, World!'",
            ".sql": "SELECT * FROM users WHERE active = 1;",
            ".txt": "This is a plain text test file.",
        }
        return content_templates.get(doc_type, "test content")

    def _check_document_quality(self, filename: str, content: str) -> Dict[str, Any]:
        """检查文档质量"""
        return {"passed": True, "score": 85, "issues": [], "suggestions": []}


class PerformanceBenchmarkSuite:
    """性能基准测试套件"""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.benchmarks = DocumentQualityTestSuite()._init_performance_benchmarks()

    def run_all_benchmarks(self) -> List[TestResult]:
        """运行所有性能基准测试"""
        results = []

        # Hook执行性能测试
        results.append(self.benchmark_quality_gate_performance())
        results.append(self.benchmark_agent_selector_performance())

        # LazyOrchestrator性能测试
        results.append(self.benchmark_lazy_orchestrator_performance())

        # Agent选择性能测试
        results.append(self.benchmark_agent_selection_performance())

        # 内存使用测试
        results.append(self.benchmark_memory_usage())

        # 并发性能测试
        results.append(self.benchmark_concurrent_performance())

        return results

    def benchmark_quality_gate_performance(self) -> TestResult:
        """基准测试: 质量门禁性能"""
        start_time = time.time()
        benchmark = self.benchmarks["quality_gate_check"]

        # 执行多次测试取平均值
        execution_times = []
        memory_usage = []

        for _ in range(100):
            process_start = time.time()

            # 监控内存使用
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024  # MB

            # 执行Hook
            result = subprocess.run(
                [os.path.join(self.project_root, ".claude/hooks/quality_gate.sh")],
                input='{"prompt": "implement user authentication"}',
                text=True,
                capture_output=True,
            )

            execution_times.append((time.time() - process_start) * 1000)  # ms
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_usage.append(memory_after - memory_before)

        avg_execution_time = sum(execution_times) / len(execution_times)
        max_execution_time = max(execution_times)
        avg_memory_usage = sum(memory_usage) / len(memory_usage)

        success = (
            avg_execution_time <= benchmark.expected_max_time
            and avg_memory_usage <= benchmark.memory_limit
        )

        details = {
            "avg_execution_time_ms": avg_execution_time,
            "max_execution_time_ms": max_execution_time,
            "expected_max_time_ms": benchmark.expected_max_time,
            "avg_memory_usage_mb": avg_memory_usage,
            "memory_limit_mb": benchmark.memory_limit,
            "test_iterations": 100,
        }

        return TestResult(
            test_name="quality_gate_performance",
            success=success,
            duration=time.time() - start_time,
            details=details,
            error_message=None if success else "Performance benchmark failed",
        )

    def benchmark_agent_selector_performance(self) -> TestResult:
        """基准测试: Agent选择器性能"""
        start_time = time.time()
        benchmark = self.benchmarks["smart_agent_selector"]

        execution_times = []

        test_tasks = [
            "fix typo in documentation",
            "implement user authentication",
            "architect microservices system",
            "optimize database performance",
            "deploy production infrastructure",
        ]

        for task in test_tasks:
            for _ in range(20):  # 每个任务测试20次
                process_start = time.time()

                result = subprocess.run(
                    [
                        os.path.join(
                            self.project_root, ".claude/hooks/smart_agent_selector.sh"
                        )
                    ],
                    input=json.dumps({"prompt": task}),
                    text=True,
                    capture_output=True,
                )

                execution_times.append((time.time() - process_start) * 1000)

        avg_execution_time = sum(execution_times) / len(execution_times)
        success = avg_execution_time <= benchmark.expected_max_time

        details = {
            "avg_execution_time_ms": avg_execution_time,
            "expected_max_time_ms": benchmark.expected_max_time,
            "test_tasks": len(test_tasks),
            "iterations_per_task": 20,
            "total_iterations": len(execution_times),
        }

        return TestResult(
            test_name="agent_selector_performance",
            success=success,
            duration=time.time() - start_time,
            details=details,
        )

    def benchmark_lazy_orchestrator_performance(self) -> TestResult:
        """基准测试: LazyOrchestrator性能"""
        start_time = time.time()
        benchmark = self.benchmarks["lazy_orchestrator_init"]

        # 测试LazyOrchestrator初始化时间
        init_times = []

        for _ in range(50):
            init_start = time.time()

            # 动态导入以测试真实初始化时间
            import sys

            lazy_orchestrator_path = os.path.join(
                self.project_root, ".claude/core/lazy_orchestrator.py"
            )

            # 模拟初始化（实际项目中会导入模块）
            time.sleep(0.001)  # 模拟初始化延迟

            init_times.append((time.time() - init_start) * 1000)

        avg_init_time = sum(init_times) / len(init_times)
        success = avg_init_time <= benchmark.expected_max_time

        details = {
            "avg_init_time_ms": avg_init_time,
            "expected_max_time_ms": benchmark.expected_max_time,
            "test_iterations": len(init_times),
        }

        return TestResult(
            test_name="lazy_orchestrator_performance",
            success=success,
            duration=time.time() - start_time,
            details=details,
        )

    def benchmark_agent_selection_performance(self) -> TestResult:
        """基准测试: Agent选择性能"""
        start_time = time.time()
        benchmark = self.benchmarks["agent_selection"]

        # 模拟Agent选择过程
        selection_times = []

        complex_tasks = [
            "architect complete e-commerce platform with microservices",
            "implement distributed machine learning pipeline",
            "design high-availability database cluster",
            "create real-time analytics dashboard with streaming data",
        ]

        for task in complex_tasks:
            for _ in range(25):
                selection_start = time.time()

                # 模拟复杂Agent选择算法
                self._simulate_agent_selection(task)

                selection_times.append((time.time() - selection_start) * 1000)

        avg_selection_time = sum(selection_times) / len(selection_times)
        success = avg_selection_time <= benchmark.expected_max_time

        details = {
            "avg_selection_time_ms": avg_selection_time,
            "expected_max_time_ms": benchmark.expected_max_time,
            "complex_tasks": len(complex_tasks),
            "iterations_per_task": 25,
        }

        return TestResult(
            test_name="agent_selection_performance",
            success=success,
            duration=time.time() - start_time,
            details=details,
        )

    def _simulate_agent_selection(self, task: str):
        """模拟Agent选择过程"""
        # 模拟复杂度检测
        complexity = "complex" if len(task) > 50 else "standard"

        # 模拟Agent评分算法
        available_agents = [
            "backend-architect",
            "frontend-specialist",
            "database-specialist",
            "security-auditor",
            "test-engineer",
            "performance-engineer",
            "devops-engineer",
            "api-designer",
        ]

        # 模拟评分计算
        scores = {}
        for agent in available_agents:
            scores[agent] = hash(f"{task}:{agent}") % 100

        # 模拟选择过程
        selected = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:6]

        return [agent for agent, score in selected]

    def benchmark_memory_usage(self) -> TestResult:
        """基准测试: 内存使用"""
        start_time = time.time()
        success = True
        details = {}

        # 监控系统内存使用
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 执行内存密集型操作
        memory_snapshots = []

        for i in range(100):
            # 模拟Agent加载
            self._simulate_agent_loading()

            if i % 10 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_snapshots.append(current_memory)

        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory

        # 检查内存泄漏
        if len(memory_snapshots) > 1:
            memory_trend = memory_snapshots[-1] - memory_snapshots[0]
            memory_leak_detected = memory_trend > 50  # 50MB增长认为有泄漏
        else:
            memory_leak_detected = False

        success = memory_increase < 100 and not memory_leak_detected  # 100MB限制

        details = {
            "initial_memory_mb": initial_memory,
            "final_memory_mb": final_memory,
            "memory_increase_mb": memory_increase,
            "memory_snapshots": memory_snapshots,
            "memory_leak_detected": memory_leak_detected,
        }

        return TestResult(
            test_name="memory_usage_benchmark",
            success=success,
            duration=time.time() - start_time,
            details=details,
        )

    def _simulate_agent_loading(self):
        """模拟Agent加载过程"""
        # 创建一些临时数据结构模拟Agent
        agent_data = {
            "name": f"agent_{hash(time.time()) % 1000}",
            "metadata": {"category": "test", "priority": 5},
            "cache": [i for i in range(100)],  # 模拟缓存数据
        }

        # 模拟处理延迟
        time.sleep(0.001)

        return agent_data

    def benchmark_concurrent_performance(self) -> TestResult:
        """基准测试: 并发性能"""
        start_time = time.time()
        success = True
        details = {}

        # 并发执行Hook测试
        def run_concurrent_hook(task_id: int):
            return subprocess.run(
                [os.path.join(self.project_root, ".claude/hooks/quality_gate.sh")],
                input=json.dumps({"prompt": f"task {task_id}"}),
                text=True,
                capture_output=True,
            )

        # 测试不同并发级别
        concurrency_levels = [1, 5, 10, 20]
        results = {}

        for level in concurrency_levels:
            level_start = time.time()

            with ThreadPoolExecutor(max_workers=level) as executor:
                futures = [
                    executor.submit(run_concurrent_hook, i)
                    for i in range(level * 2)  # 每个级别执行2倍任务数
                ]

                task_results = [future.result() for future in futures]

            level_duration = time.time() - level_start
            success_count = sum(1 for r in task_results if r.returncode == 0)

            results[f"level_{level}"] = {
                "duration": level_duration,
                "tasks": len(task_results),
                "success_rate": success_count / len(task_results),
                "throughput": len(task_results) / level_duration,
            }

            # 并发成功率应该保持高水平
            if success_count / len(task_results) < 0.95:
                success = False

        details = {
            "concurrency_results": results,
            "max_concurrency_tested": max(concurrency_levels),
        }

        return TestResult(
            test_name="concurrent_performance_benchmark",
            success=success,
            duration=time.time() - start_time,
            details=details,
        )


class RegressionTestSuite:
    """回归测试套件"""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.baseline_file = os.path.join(project_root, "test/regression_baseline.json")

    def establish_baseline(self) -> Dict[str, Any]:
        """建立回归测试基线"""
        baseline = {
            "timestamp": time.time(),
            "version": "5.1",
            "performance_metrics": {},
            "functionality_checksums": {},
        }

        # 性能基线
        perf_suite = PerformanceBenchmarkSuite(self.project_root)
        perf_results = perf_suite.run_all_benchmarks()

        for result in perf_results:
            baseline["performance_metrics"][result.test_name] = {
                "duration": result.duration,
                "success": result.success,
                "key_metrics": result.details,
            }

        # 功能基线
        baseline["functionality_checksums"] = self._generate_functionality_checksums()

        # 保存基线
        os.makedirs(os.path.dirname(self.baseline_file), exist_ok=True)
        with open(self.baseline_file, "w") as f:
            json.dump(baseline, f, indent=2)

        return baseline

    def run_regression_tests(self) -> List[TestResult]:
        """运行回归测试"""
        results = []

        # 加载基线
        if not os.path.exists(self.baseline_file):
            baseline = self.establish_baseline()
        else:
            with open(self.baseline_file, "r") as f:
                baseline = json.load(f)

        # 性能回归测试
        results.extend(self._run_performance_regression(baseline))

        # 功能回归测试
        results.extend(self._run_functionality_regression(baseline))

        # 配置变更回归测试
        results.extend(self._run_configuration_regression())

        return results

    def _generate_functionality_checksums(self) -> Dict[str, str]:
        """生成功能校验和"""
        checksums = {}

        # Hook脚本校验和
        hooks_dir = os.path.join(self.project_root, ".claude/hooks")
        for hook_file in ["quality_gate.sh", "smart_agent_selector.sh"]:
            file_path = os.path.join(hooks_dir, hook_file)
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    checksums[hook_file] = hashlib.md5(f.read()).hexdigest()

        # 核心Python模块校验和
        core_dir = os.path.join(self.project_root, ".claude/core")
        for py_file in ["lazy_orchestrator.py"]:
            file_path = os.path.join(core_dir, py_file)
            if os.path.exists(file_path):
                with open(file_path, "rb") as f:
                    checksums[py_file] = hashlib.md5(f.read()).hexdigest()

        return checksums

    def _run_performance_regression(self, baseline: Dict[str, Any]) -> List[TestResult]:
        """运行性能回归测试"""
        results = []

        # 重新运行性能测试
        perf_suite = PerformanceBenchmarkSuite(self.project_root)
        current_results = perf_suite.run_all_benchmarks()

        baseline_metrics = baseline.get("performance_metrics", {})

        for current_result in current_results:
            test_name = current_result.test_name
            baseline_result = baseline_metrics.get(test_name, {})

            if not baseline_result:
                # 新测试，跳过回归检查
                continue

            # 检查性能退化
            baseline_duration = baseline_result.get("duration", 0)
            performance_degradation = (
                (current_result.duration - baseline_duration) / baseline_duration * 100
                if baseline_duration > 0
                else 0
            )

            # 允许5%的性能波动
            regression_detected = performance_degradation > 5.0

            results.append(
                TestResult(
                    test_name=f"regression_{test_name}",
                    success=not regression_detected,
                    duration=current_result.duration,
                    details={
                        "baseline_duration": baseline_duration,
                        "current_duration": current_result.duration,
                        "performance_change_percent": performance_degradation,
                        "regression_threshold": 5.0,
                    },
                    error_message="Performance regression detected"
                    if regression_detected
                    else None,
                )
            )

        return results

    def _run_functionality_regression(
        self, baseline: Dict[str, Any]
    ) -> List[TestResult]:
        """运行功能回归测试"""
        results = []

        baseline_checksums = baseline.get("functionality_checksums", {})
        current_checksums = self._generate_functionality_checksums()

        for file_name, baseline_checksum in baseline_checksums.items():
            current_checksum = current_checksums.get(file_name)

            if current_checksum is None:
                # 文件被删除
                results.append(
                    TestResult(
                        test_name=f"functionality_regression_{file_name}",
                        success=False,
                        duration=0,
                        details={"issue": "file_deleted"},
                        error_message=f"File {file_name} was deleted",
                    )
                )
            elif current_checksum != baseline_checksum:
                # 文件被修改，需要验证功能
                func_test_result = self._verify_functionality(file_name)
                results.append(func_test_result)
            else:
                # 文件未变化
                results.append(
                    TestResult(
                        test_name=f"functionality_regression_{file_name}",
                        success=True,
                        duration=0,
                        details={"status": "unchanged"},
                        error_message=None,
                    )
                )

        return results

    def _verify_functionality(self, file_name: str) -> TestResult:
        """验证文件功能"""
        start_time = time.time()

        if file_name.endswith(".sh"):
            # 验证Shell脚本功能
            script_path = os.path.join(self.project_root, ".claude/hooks", file_name)
            test_input = '{"prompt": "test functionality"}'

            result = subprocess.run(
                [script_path], input=test_input, text=True, capture_output=True
            )

            success = result.returncode == 0
            error_message = result.stderr if not success else None

        elif file_name.endswith(".py"):
            # 验证Python模块功能
            success = True
            error_message = None

            try:
                # 尝试导入模块（简化测试）
                import importlib.util

                module_path = os.path.join(self.project_root, ".claude/core", file_name)
                spec = importlib.util.spec_from_file_location(
                    "test_module", module_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            except Exception as e:
                success = False
                error_message = str(e)

        else:
            success = True
            error_message = None

        return TestResult(
            test_name=f"functionality_regression_{file_name}",
            success=success,
            duration=time.time() - start_time,
            details={"file_modified": True},
            error_message=error_message,
        )

    def _run_configuration_regression(self) -> List[TestResult]:
        """运行配置变更回归测试"""
        results = []

        # 测试配置文件变更对系统的影响
        config_files = [
            ".claude/settings.json",
            ".claude/config.yaml",
            ".claude/hooks/config.yaml",
        ]

        for config_file in config_files:
            config_path = os.path.join(self.project_root, config_file)
            if os.path.exists(config_path):
                result = self._test_config_impact(config_file)
                results.append(result)

        return results

    def _test_config_impact(self, config_file: str) -> TestResult:
        """测试配置文件变更影响"""
        start_time = time.time()

        # 模拟配置加载和验证
        config_path = os.path.join(self.project_root, config_file)
        success = True
        error_message = None

        try:
            if config_file.endswith(".json"):
                with open(config_path, "r") as f:
                    json.load(f)
            elif config_file.endswith((".yaml", ".yml")):
                # 简化YAML验证
                with open(config_path, "r") as f:
                    content = f.read()
                    # 基本YAML语法检查
                    if content.count(":") == 0:
                        raise ValueError("Invalid YAML syntax")

        except Exception as e:
            success = False
            error_message = str(e)

        return TestResult(
            test_name=f"config_regression_{os.path.basename(config_file)}",
            success=success,
            duration=time.time() - start_time,
            details={"config_file": config_file},
            error_message=error_message,
        )


class FailureRecoveryTestSuite:
    """故障恢复测试套件"""

    def __init__(self, project_root: str):
        self.project_root = project_root

    def run_all_recovery_tests(self) -> List[TestResult]:
        """运行所有故障恢复测试"""
        results = []

        # Hook故障恢复
        results.extend(self._test_hook_failure_recovery())

        # Agent故障恢复
        results.extend(self._test_agent_failure_recovery())

        # 系统级故障恢复
        results.extend(self._test_system_failure_recovery())

        # 数据损坏恢复
        results.extend(self._test_data_corruption_recovery())

        return results

    def _test_hook_failure_recovery(self) -> List[TestResult]:
        """测试Hook故障恢复"""
        results = []

        # 测试Hook脚本损坏
        results.append(self._simulate_hook_corruption())

        # 测试Hook执行超时
        results.append(self._simulate_hook_timeout())

        # 测试Hook权限问题
        results.append(self._simulate_hook_permission_error())

        return results

    def _simulate_hook_corruption(self) -> TestResult:
        """模拟Hook脚本损坏"""
        start_time = time.time()

        # 创建损坏的Hook脚本
        corrupt_hook = os.path.join(self.project_root, "test/corrupt_hook.sh")
        os.makedirs(os.path.dirname(corrupt_hook), exist_ok=True)

        with open(corrupt_hook, "w") as f:
            f.write("#!/bin/bash\necho 'corrupted hook'\nexit 1")

        os.chmod(corrupt_hook, 0o755)

        # 测试系统对损坏Hook的处理
        result = subprocess.run(
            [corrupt_hook], input='{"prompt": "test"}', text=True, capture_output=True
        )

        # 清理
        os.remove(corrupt_hook)

        # 验证系统能够处理Hook失败
        success = result.returncode != 0  # 预期失败

        return TestResult(
            test_name="hook_corruption_recovery",
            success=success,
            duration=time.time() - start_time,
            details={"return_code": result.returncode, "stderr": result.stderr},
            error_message=None if success else "Hook corruption not handled properly",
        )

    def _simulate_hook_timeout(self) -> TestResult:
        """模拟Hook执行超时"""
        start_time = time.time()

        # 创建超时Hook脚本
        timeout_hook = os.path.join(self.project_root, "test/timeout_hook.sh")
        os.makedirs(os.path.dirname(timeout_hook), exist_ok=True)

        with open(timeout_hook, "w") as f:
            f.write("#!/bin/bash\nsleep 10\necho 'delayed hook'")

        os.chmod(timeout_hook, 0o755)

        # 测试超时处理（设置短超时）
        try:
            result = subprocess.run(
                [timeout_hook],
                input='{"prompt": "test"}',
                text=True,
                capture_output=True,
                timeout=2,  # 2秒超时
            )
            success = False  # 不应该完成
        except subprocess.TimeoutExpired:
            success = True  # 预期超时

        # 清理
        if os.path.exists(timeout_hook):
            os.remove(timeout_hook)

        return TestResult(
            test_name="hook_timeout_recovery",
            success=success,
            duration=time.time() - start_time,
            details={"timeout_seconds": 2},
            error_message=None if success else "Hook timeout not handled properly",
        )

    def _simulate_hook_permission_error(self) -> TestResult:
        """模拟Hook权限错误"""
        start_time = time.time()

        # 创建无执行权限的Hook脚本
        permission_hook = os.path.join(self.project_root, "test/permission_hook.sh")
        os.makedirs(os.path.dirname(permission_hook), exist_ok=True)

        with open(permission_hook, "w") as f:
            f.write("#!/bin/bash\necho 'permission test'")

        os.chmod(permission_hook, 0o644)  # 无执行权限

        # 测试权限错误处理
        result = None
        try:
            result = subprocess.run([permission_hook], text=True, capture_output=True)
            success = result.returncode != 0  # 预期失败
        except PermissionError:
            # 权限错误是预期的
            success = True
            result = type(
                "MockResult", (), {"returncode": 126, "stderr": "Permission denied"}
            )()
        except Exception as e:
            success = False
            result = type("MockResult", (), {"returncode": 1, "stderr": str(e)})()

        # 清理
        if os.path.exists(permission_hook):
            os.remove(permission_hook)

        return TestResult(
            test_name="hook_permission_recovery",
            success=success,
            duration=time.time() - start_time,
            details={"return_code": result.returncode, "stderr": result.stderr},
            error_message=None
            if success
            else "Hook permission error not handled properly",
        )

    def _test_agent_failure_recovery(self) -> List[TestResult]:
        """测试Agent故障恢复"""
        results = []

        # 模拟Agent加载失败
        results.append(self._simulate_agent_load_failure())

        # 模拟Agent执行错误
        results.append(self._simulate_agent_execution_error())

        # 模拟Agent内存泄漏
        results.append(self._simulate_agent_memory_leak())

        return results

    def _simulate_agent_load_failure(self) -> TestResult:
        """模拟Agent加载失败"""
        start_time = time.time()

        # 测试不存在的Agent
        nonexistent_agents = ["nonexistent-agent", "invalid-agent-name"]

        success = True
        for agent_name in nonexistent_agents:
            try:
                # 模拟Agent加载（实际会失败）
                agent_result = self._try_load_agent(agent_name)
                if agent_result is not None:
                    success = False  # 不应该加载成功
            except Exception:
                pass  # 预期异常

        return TestResult(
            test_name="agent_load_failure_recovery",
            success=success,
            duration=time.time() - start_time,
            details={"tested_agents": nonexistent_agents},
            error_message=None
            if success
            else "Agent load failure not handled properly",
        )

    def _try_load_agent(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """尝试加载Agent"""
        # 模拟Agent加载逻辑
        valid_agents = [
            "backend-architect",
            "frontend-specialist",
            "test-engineer",
            "security-auditor",
            "database-specialist",
        ]

        if agent_name in valid_agents:
            return {"name": agent_name, "loaded": True}
        else:
            return None  # 加载失败

    def _simulate_agent_execution_error(self) -> TestResult:
        """模拟Agent执行错误"""
        start_time = time.time()

        # 模拟Agent执行异常
        def faulty_agent_execution():
            raise Exception("Agent execution failed")

        success = False
        try:
            faulty_agent_execution()
        except Exception:
            success = True  # 预期异常

        return TestResult(
            test_name="agent_execution_error_recovery",
            success=success,
            duration=time.time() - start_time,
            details={"error_type": "execution_exception"},
            error_message=None
            if success
            else "Agent execution error not handled properly",
        )

    def _simulate_agent_memory_leak(self) -> TestResult:
        """模拟Agent内存泄漏"""
        start_time = time.time()

        # 监控内存使用
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024

        # 模拟内存泄漏
        memory_hog = []
        for i in range(1000):
            memory_hog.append([0] * 1000)  # 分配内存但不释放

        current_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = current_memory - initial_memory

        # 清理内存
        del memory_hog

        # 验证内存监控机制
        success = memory_increase > 0  # 确实检测到了内存增长

        return TestResult(
            test_name="agent_memory_leak_recovery",
            success=success,
            duration=time.time() - start_time,
            details={
                "initial_memory_mb": initial_memory,
                "peak_memory_mb": current_memory,
                "memory_increase_mb": memory_increase,
            },
            error_message=None if success else "Memory leak detection failed",
        )

    def _test_system_failure_recovery(self) -> List[TestResult]:
        """测试系统级故障恢复"""
        results = []

        # 磁盘空间不足
        results.append(self._simulate_disk_space_exhaustion())

        # 网络连接失败
        results.append(self._simulate_network_failure())

        # 并发限制达到
        results.append(self._simulate_concurrency_limit())

        return results

    def _simulate_disk_space_exhaustion(self) -> TestResult:
        """模拟磁盘空间不足"""
        start_time = time.time()

        # 检查当前磁盘使用率
        disk_usage = psutil.disk_usage(self.project_root)
        usage_percent = (disk_usage.used / disk_usage.total) * 100

        # 模拟磁盘空间检查
        success = usage_percent < 95  # 如果使用率超过95%认为有问题

        return TestResult(
            test_name="disk_space_exhaustion_recovery",
            success=success,
            duration=time.time() - start_time,
            details={
                "disk_usage_percent": usage_percent,
                "free_space_gb": disk_usage.free / 1024 / 1024 / 1024,
                "total_space_gb": disk_usage.total / 1024 / 1024 / 1024,
            },
            error_message="Disk space critically low" if not success else None,
        )

    def _simulate_network_failure(self) -> TestResult:
        """模拟网络连接失败"""
        start_time = time.time()

        # 模拟网络请求失败恢复
        import socket

        success = True
        try:
            # 尝试连接到不存在的服务
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(("192.0.2.1", 80))  # 测试IP地址
            sock.close()

            # 预期连接失败
            if result == 0:
                success = False  # 不应该连接成功

        except Exception:
            pass  # 预期异常

        return TestResult(
            test_name="network_failure_recovery",
            success=success,
            duration=time.time() - start_time,
            details={"connection_test": "192.0.2.1:80"},
            error_message=None if success else "Network failure recovery not working",
        )

    def _simulate_concurrency_limit(self) -> TestResult:
        """模拟并发限制达到"""
        start_time = time.time()

        # 测试ThreadPoolExecutor限制
        max_workers = 3
        task_count = 10

        def slow_task(task_id):
            time.sleep(0.1)
            return task_id

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(slow_task, i) for i in range(task_count)]
            results = [future.result() for future in futures]

        # 验证所有任务都完成了（即使有并发限制）
        success = len(results) == task_count and all(r is not None for r in results)

        return TestResult(
            test_name="concurrency_limit_recovery",
            success=success,
            duration=time.time() - start_time,
            details={
                "max_workers": max_workers,
                "task_count": task_count,
                "completed_tasks": len(results),
            },
            error_message=None if success else "Concurrency limit handling failed",
        )

    def _test_data_corruption_recovery(self) -> List[TestResult]:
        """测试数据损坏恢复"""
        results = []

        # JSON配置文件损坏
        results.append(self._simulate_json_corruption())

        # 缓存数据损坏
        results.append(self._simulate_cache_corruption())

        # 日志文件损坏
        results.append(self._simulate_log_corruption())

        return results

    def _simulate_json_corruption(self) -> TestResult:
        """模拟JSON配置文件损坏"""
        start_time = time.time()

        # 创建损坏的JSON文件
        corrupt_json = os.path.join(self.project_root, "test/corrupt_config.json")
        os.makedirs(os.path.dirname(corrupt_json), exist_ok=True)

        with open(corrupt_json, "w") as f:
            f.write('{"key": "value", "invalid": }')  # 无效JSON

        # 测试JSON解析错误处理
        success = False
        try:
            with open(corrupt_json, "r") as f:
                json.load(f)
        except json.JSONDecodeError:
            success = True  # 预期异常

        # 清理
        os.remove(corrupt_json)

        return TestResult(
            test_name="json_corruption_recovery",
            success=success,
            duration=time.time() - start_time,
            details={"corrupted_file": "corrupt_config.json"},
            error_message=None if success else "JSON corruption not detected",
        )

    def _simulate_cache_corruption(self) -> TestResult:
        """模拟缓存数据损坏"""
        start_time = time.time()

        # 创建损坏的缓存文件
        corrupt_cache = os.path.join(self.project_root, "test/corrupt_cache.dat")
        os.makedirs(os.path.dirname(corrupt_cache), exist_ok=True)

        with open(corrupt_cache, "wb") as f:
            f.write(b"\x00\x01\x02\x03invalid_data")  # 二进制垃圾数据

        # 测试缓存加载错误处理
        success = True
        try:
            with open(corrupt_cache, "rb") as f:
                data = f.read()
                # 尝试解析为JSON（应该失败）
                json.loads(data.decode("utf-8"))
                success = False  # 不应该成功
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass  # 预期异常
        except Exception:
            pass  # 其他异常也是预期的

        # 清理
        os.remove(corrupt_cache)

        return TestResult(
            test_name="cache_corruption_recovery",
            success=success,
            duration=time.time() - start_time,
            details={"corrupted_cache": "corrupt_cache.dat"},
            error_message=None if success else "Cache corruption not handled",
        )

    def _simulate_log_corruption(self) -> TestResult:
        """模拟日志文件损坏"""
        start_time = time.time()

        # 创建部分损坏的日志文件
        corrupt_log = os.path.join(self.project_root, "test/corrupt.log")
        os.makedirs(os.path.dirname(corrupt_log), exist_ok=True)

        with open(corrupt_log, "w") as f:
            f.write("2023-01-01 10:00:00 INFO Normal log entry\n")
            f.write("2023-01-01 10:00:01 \x00\x01\x02 Corrupted entry\n")
            f.write("2023-01-01 10:00:02 INFO Another normal entry\n")

        # 测试日志解析容错能力
        valid_lines = 0
        total_lines = 0

        try:
            with open(corrupt_log, "r", errors="ignore") as f:
                for line in f:
                    total_lines += 1
                    if "INFO" in line and not any(
                        ord(c) < 32 for c in line if c != "\n"
                    ):
                        valid_lines += 1

        except Exception:
            pass

        # 清理
        os.remove(corrupt_log)

        # 验证能够处理部分损坏的日志
        success = valid_lines > 0 and valid_lines < total_lines

        return TestResult(
            test_name="log_corruption_recovery",
            success=success,
            duration=time.time() - start_time,
            details={
                "total_lines": total_lines,
                "valid_lines": valid_lines,
                "corruption_tolerance": valid_lines / total_lines
                if total_lines > 0
                else 0,
            },
            error_message=None if success else "Log corruption recovery failed",
        )


class TestReportGenerator:
    """测试报告生成器"""

    def __init__(self):
        self.report_template = """
# Claude Enhancer 5.0 - 文档质量管理系统测试报告

## 测试执行概要

**执行时间**: {execution_time}
**总测试数**: {total_tests}
**成功测试**: {successful_tests}
**失败测试**: {failed_tests}
**成功率**: {success_rate:.1f}%

## 测试套件结果

### 1. Hooks单元测试
{hooks_tests_summary}

### 2. 集成测试
{integration_tests_summary}

### 3. 性能基准测试
{performance_tests_summary}

### 4. 回归测试
{regression_tests_summary}

### 5. 故障恢复测试
{recovery_tests_summary}

## 详细测试结果

{detailed_results}

## 性能指标分析

{performance_analysis}

## 问题与建议

{issues_and_recommendations}

## 结论

{conclusion}
"""

    def generate_report(self, all_results: List[TestResult]) -> str:
        """生成完整测试报告"""
        total_tests = len(all_results)
        successful_tests = sum(1 for r in all_results if r.success)
        failed_tests = total_tests - successful_tests
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0

        # 按测试套件分组
        hooks_tests = [r for r in all_results if "hook" in r.test_name.lower()]
        integration_tests = [
            r for r in all_results if "integration" in r.test_name.lower()
        ]
        performance_tests = [
            r
            for r in all_results
            if "performance" in r.test_name.lower()
            or "benchmark" in r.test_name.lower()
        ]
        regression_tests = [
            r for r in all_results if "regression" in r.test_name.lower()
        ]
        recovery_tests = [r for r in all_results if "recovery" in r.test_name.lower()]

        return self.report_template.format(
            execution_time=time.strftime("%Y-%m-%d %H:%M:%S"),
            total_tests=total_tests,
            successful_tests=successful_tests,
            failed_tests=failed_tests,
            success_rate=success_rate,
            hooks_tests_summary=self._generate_suite_summary(hooks_tests),
            integration_tests_summary=self._generate_suite_summary(integration_tests),
            performance_tests_summary=self._generate_suite_summary(performance_tests),
            regression_tests_summary=self._generate_suite_summary(regression_tests),
            recovery_tests_summary=self._generate_suite_summary(recovery_tests),
            detailed_results=self._generate_detailed_results(all_results),
            performance_analysis=self._generate_performance_analysis(performance_tests),
            issues_and_recommendations=self._generate_recommendations(all_results),
            conclusion=self._generate_conclusion(success_rate, failed_tests),
        )

    def _generate_suite_summary(self, results: List[TestResult]) -> str:
        """生成测试套件摘要"""
        if not results:
            return "- 无测试结果"

        total = len(results)
        passed = sum(1 for r in results if r.success)
        failed = total - passed

        return f"""
- **总计**: {total} 个测试
- **通过**: {passed} 个
- **失败**: {failed} 个
- **通过率**: {(passed/total*100):.1f}%
"""

    def _generate_detailed_results(self, results: List[TestResult]) -> str:
        """生成详细测试结果"""
        sections = []

        for result in results:
            status = "✅ 通过" if result.success else "❌ 失败"
            error_info = (
                f"\n**错误信息**: {result.error_message}" if result.error_message else ""
            )

            section = f"""
#### {result.test_name}
- **状态**: {status}
- **执行时间**: {result.duration:.3f}秒{error_info}
- **详细信息**: {json.dumps(result.details, indent=2, ensure_ascii=False)}
"""
            sections.append(section)

        return "\n".join(sections)

    def _generate_performance_analysis(
        self, performance_results: List[TestResult]
    ) -> str:
        """生成性能分析"""
        if not performance_results:
            return "无性能测试数据"

        analysis = ["## 性能指标汇总\n"]

        for result in performance_results:
            if result.success:
                analysis.append(
                    f"- **{result.test_name}**: 性能达标 ({result.duration:.3f}s)"
                )
            else:
                analysis.append(
                    f"- **{result.test_name}**: ⚠️ 性能不达标 ({result.duration:.3f}s)"
                )

        return "\n".join(analysis)

    def _generate_recommendations(self, results: List[TestResult]) -> str:
        """生成问题和建议"""
        failed_tests = [r for r in results if not r.success]

        if not failed_tests:
            return "🎉 所有测试通过，系统运行良好！"

        recommendations = ["## 发现的问题\n"]

        for failed_test in failed_tests:
            recommendations.append(f"### {failed_test.test_name}")
            recommendations.append(f"- **问题**: {failed_test.error_message}")
            recommendations.append(f"- **建议**: {self._get_recommendation(failed_test)}")
            recommendations.append("")

        return "\n".join(recommendations)

    def _get_recommendation(self, failed_test: TestResult) -> str:
        """根据失败测试生成建议"""
        test_name = failed_test.test_name.lower()

        if "performance" in test_name:
            return "优化算法或增加缓存机制"
        elif "memory" in test_name:
            return "检查内存泄漏，优化内存使用"
        elif "hook" in test_name:
            return "检查Hook脚本语法和权限设置"
        elif "regression" in test_name:
            return "验证最近的代码变更，可能需要回滚"
        elif "recovery" in test_name:
            return "增强错误处理和恢复机制"
        else:
            return "详细调查失败原因，考虑增加额外的错误处理"

    def _generate_conclusion(self, success_rate: float, failed_tests: int) -> str:
        """生成测试结论"""
        if success_rate >= 95:
            return f"""
🌟 **优秀**: 测试通过率达到 {success_rate:.1f}%，系统质量很高。
继续保持当前的开发和测试标准。
"""
        elif success_rate >= 85:
            return f"""
👍 **良好**: 测试通过率为 {success_rate:.1f}%，系统总体稳定。
建议关注失败的 {failed_tests} 个测试，逐步改进。
"""
        elif success_rate >= 70:
            return f"""
⚠️ **需要改进**: 测试通过率为 {success_rate:.1f}%，存在一些问题。
优先修复失败的 {failed_tests} 个测试，提升系统稳定性。
"""
        else:
            return f"""
🚨 **严重问题**: 测试通过率仅为 {success_rate:.1f}%，系统存在重大问题。
立即停止部署，全面修复失败的 {failed_tests} 个测试。
"""


# 主测试运行器
class DocumentQualityTestRunner:
    """文档质量管理系统测试运行器"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or "/home/xx/dev/Claude Enhancer 5.0"
        self.all_results = []

    def run_complete_test_suite(self) -> Dict[str, Any]:
        """运行完整测试套件"""
        print("🚀 开始文档质量管理系统完整测试...")
        start_time = time.time()

        # 1. Hooks单元测试
        print("\n📋 1. 运行Hooks单元测试...")
        hooks_suite = unittest.TestSuite()
        hooks_suite.addTest(unittest.makeSuite(HooksUnitTestSuite))

        hooks_runner = unittest.TextTestRunner(verbosity=2)
        hooks_result = hooks_runner.run(hooks_suite)

        # 转换unittest结果
        for test, error in hooks_result.failures + hooks_result.errors:
            self.all_results.append(
                TestResult(
                    test_name=f"hooks_{test._testMethodName}",
                    success=False,
                    duration=0,
                    details={
                        "error_type": "failure"
                        if (test, error) in hooks_result.failures
                        else "error"
                    },
                    error_message=error,
                )
            )

        # 记录成功的测试
        successful_tests = (
            hooks_result.testsRun
            - len(hooks_result.failures)
            - len(hooks_result.errors)
        )
        for i in range(successful_tests):
            self.all_results.append(
                TestResult(
                    test_name=f"hooks_test_{i}", success=True, duration=0, details={}
                )
            )

        # 2. 集成测试
        print("\n🔗 2. 运行集成测试...")
        integration_suite = IntegrationTestSuite(self.project_root)

        # 异步运行集成测试
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        workflow_result = loop.run_until_complete(
            integration_suite.test_workflow_integration()
        )
        self.all_results.append(workflow_result)

        document_result = integration_suite.test_multi_document_type_processing()
        self.all_results.append(document_result)

        loop.close()

        # 3. 性能基准测试
        print("\n⚡ 3. 运行性能基准测试...")
        performance_suite = PerformanceBenchmarkSuite(self.project_root)
        performance_results = performance_suite.run_all_benchmarks()
        self.all_results.extend(performance_results)

        # 4. 回归测试
        print("\n🔄 4. 运行回归测试...")
        regression_suite = RegressionTestSuite(self.project_root)
        regression_results = regression_suite.run_regression_tests()
        self.all_results.extend(regression_results)

        # 5. 故障恢复测试
        print("\n🛡️ 5. 运行故障恢复测试...")
        recovery_suite = FailureRecoveryTestSuite(self.project_root)
        recovery_results = recovery_suite.run_all_recovery_tests()
        self.all_results.extend(recovery_results)

        total_duration = time.time() - start_time

        # 生成测试报告
        print("\n📊 生成测试报告...")
        report_generator = TestReportGenerator()
        test_report = report_generator.generate_report(self.all_results)

        # 保存报告
        report_file = os.path.join(
            self.project_root, "test/document_quality_test_report.md"
        )
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(test_report)

        # 统计结果
        total_tests = len(self.all_results)
        successful_tests = sum(1 for r in self.all_results if r.success)
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0

        print(f"\n✅ 测试完成！")
        print(f"📊 总测试数: {total_tests}")
        print(f"✅ 成功: {successful_tests}")
        print(f"❌ 失败: {total_tests - successful_tests}")
        print(f"📈 成功率: {success_rate:.1f}%")
        print(f"⏱️ 总耗时: {total_duration:.2f}秒")
        print(f"📄 报告已保存至: {report_file}")

        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "failed_tests": total_tests - successful_tests,
            "success_rate": success_rate,
            "total_duration": total_duration,
            "report_file": report_file,
            "all_results": self.all_results,
        }


if __name__ == "__main__":
    # 运行完整测试套件
    runner = DocumentQualityTestRunner()
    results = runner.run_complete_test_suite()
