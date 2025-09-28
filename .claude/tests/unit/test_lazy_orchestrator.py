#!/usr/bin/env python3
"""
Claude Enhancer Lazy Orchestrator 单元测试
测试 select_agents_intelligent 方法的核心逻辑
"""

import unittest
import json
import time
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../core"))

try:
    from lazy_orchestrator import LazyAgentOrchestrator, LazyAgentManager, AgentMetadata
except ImportError as e:
    print(f"Error importing lazy_orchestrator: {e}")
    print("Make sure the lazy_orchestrator.py file exists in the correct location")
    sys.exit(1)


class TestLazyAgentOrchestrator(unittest.TestCase):
    """测试 LazyAgentOrchestrator 核心功能"""

    def setUp(self):
        """测试前置设置"""
        self.orchestrator = LazyAgentOrchestrator()

        # 标准测试任务
        self.test_tasks = {
            "simple": "fix typo in user login form",
            "standard": "implement user authentication with JWT tokens",
            "complex": "design and implement complete microservices architecture with payment integration",
            "backend": "create REST API for order management system",
            "frontend": "build React dashboard with real-time analytics",
            "security": "implement OAuth2 security with vulnerability scanning",
            "performance": "optimize database queries for high-load performance",
        }

    def test_initialization_performance(self):
        """测试初始化性能"""
        start_time = time.time()
        orchestrator = LazyAgentOrchestrator()
        init_time = time.time() - start_time

        # 初始化应该很快（< 0.1秒）
        self.assertLess(init_time, 0.1, "初始化时间应该小于100ms")
        self.assertIsNotNone(orchestrator.agent_manager)
        self.assertEqual(
            len(orchestrator.agent_manager.agent_metadata), 24, "应该有24个Agent元数据"
        )

    def test_complexity_detection(self):
        """测试复杂度检测算法"""
        test_cases = [
            # (task_description, expected_complexity)
            ("fix typo", "simple"),
            ("quick bug fix", "simple"),
            ("small change in UI", "simple"),
            ("implement user authentication", "standard"),
            ("create REST API", "standard"),
            ("add payment integration", "standard"),
            ("design microservices architecture", "complex"),
            ("complete system migration", "complex"),
            ("full security audit with penetration testing", "complex"),
        ]

        for task_desc, expected_complexity in test_cases:
            with self.subTest(task=task_desc):
                detected_complexity = self.orchestrator.detect_complexity_advanced(
                    task_desc
                )
                self.assertEqual(
                    detected_complexity,
                    expected_complexity,
                    f"任务 '{task_desc}' 的复杂度应该是 {expected_complexity}，但检测到 {detected_complexity}",
                )

    def test_select_agents_intelligent_basic(self):
        """测试 select_agents_intelligent 基础功能"""
        task = self.test_tasks["standard"]

        result = self.orchestrator.select_agents_intelligent(task)

        # 检查返回结果结构
        required_keys = [
            "complexity",
            "agent_count",
            "selected_agents",
            "execution_mode",
            "estimated_time",
            "selection_time",
        ]
        for key in required_keys:
            self.assertIn(key, result, f"结果应该包含 {key}")

        # 检查Agent数量合理性
        self.assertGreaterEqual(result["agent_count"], 4, "至少应该选择4个Agent")
        self.assertLessEqual(result["agent_count"], 8, "最多应该选择8个Agent")

        # 检查执行模式
        self.assertEqual(result["execution_mode"], "parallel", "执行模式应该是并行")

    def test_select_agents_intelligent_performance(self):
        """测试 select_agents_intelligent 性能"""
        task = self.test_tasks["standard"]

        # 测试首次执行时间
        start_time = time.time()
        result1 = self.orchestrator.select_agents_intelligent(task)
        first_execution_time = time.time() - start_time

        # 测试缓存命中时间
        start_time = time.time()
        result2 = self.orchestrator.select_agents_intelligent(task)
        cached_execution_time = time.time() - start_time

        # 性能验证
        self.assertLess(first_execution_time, 0.05, "首次选择应该在50ms内完成")
        self.assertLess(cached_execution_time, 0.01, "缓存命中应该在10ms内完成")

        # 结果一致性
        self.assertEqual(
            result1["selected_agents"], result2["selected_agents"], "相同任务应该返回相同的Agent选择"
        )

    def test_complexity_based_agent_count(self):
        """测试基于复杂度的Agent数量选择"""
        test_cases = [
            (self.test_tasks["simple"], 4),
            (self.test_tasks["standard"], 6),
            (self.test_tasks["complex"], 8),
        ]

        for task, expected_count in test_cases:
            with self.subTest(task=task[:30]):
                result = self.orchestrator.select_agents_intelligent(task)
                self.assertEqual(
                    result["agent_count"],
                    expected_count,
                    f"复杂度 {result['complexity']} 的任务应该选择 {expected_count} 个Agent",
                )

    def test_domain_specific_agent_selection(self):
        """测试领域特定的Agent选择"""
        # 后端任务应该包含backend相关Agent
        backend_result = self.orchestrator.select_agents_intelligent(
            self.test_tasks["backend"]
        )
        backend_agents = backend_result["selected_agents"]

        self.assertTrue(
            any("backend" in agent for agent in backend_agents),
            "后端任务应该包含backend相关Agent",
        )

        # 前端任务应该包含frontend相关Agent
        frontend_result = self.orchestrator.select_agents_intelligent(
            self.test_tasks["frontend"]
        )
        frontend_agents = frontend_result["selected_agents"]

        self.assertTrue(
            any("frontend" in agent or "react" in agent for agent in frontend_agents),
            "前端任务应该包含frontend或react相关Agent",
        )

        # 安全任务应该包含security相关Agent
        security_result = self.orchestrator.select_agents_intelligent(
            self.test_tasks["security"]
        )
        security_agents = security_result["selected_agents"]

        self.assertTrue(
            any("security" in agent for agent in security_agents),
            "安全任务应该包含security相关Agent",
        )

    def test_required_agents_parameter(self):
        """测试必需Agent参数功能"""
        task = self.test_tasks["standard"]
        required_agents = ["custom-agent-1", "custom-agent-2"]

        result = self.orchestrator.select_agents_intelligent(
            task, required_agents=required_agents
        )

        # 检查必需的Agent是否被包含
        for agent in required_agents:
            self.assertIn(agent, result["selected_agents"], f"必需Agent {agent} 应该被包含")

    def test_execution_history_optimization(self):
        """测试基于执行历史的优化"""
        task = self.test_tasks["standard"]
        execution_history = [
            "backend-architect: success - authentication implemented",
            "security-auditor: success - security review passed",
            "test-engineer: success - all tests passing",
        ]

        result = self.orchestrator.select_agents_intelligent(
            task, execution_history=execution_history
        )

        # 应该包含优化标识
        self.assertTrue(result.get("optimization_applied", False), "应该应用历史优化")

        # 成功的Agent应该被优先选择
        selected_agents = result["selected_agents"]
        self.assertIn("backend-architect", selected_agents, "历史成功的Agent应该被优先选择")

    def test_feature_analysis(self):
        """测试任务特征分析"""
        complex_task = "implement secure payment system with real-time fraud detection and microservices architecture"

        result = self.orchestrator.select_agents_intelligent(complex_task)
        feature_analysis = result.get("feature_analysis", {})

        # 应该检测到多领域任务
        self.assertTrue(feature_analysis.get("multi_domain", False), "应该检测到多领域任务")

        # 应该检测到高风险任务
        self.assertTrue(feature_analysis.get("high_risk", False), "应该检测到高风险任务")

        # 应该检测到需要安全验证
        self.assertTrue(feature_analysis.get("requires_security", False), "应该检测到需要安全验证")

    def test_cache_functionality(self):
        """测试缓存功能"""
        task = self.test_tasks["standard"]

        # 清空缓存
        self.orchestrator.combination_cache.clear()
        initial_cache_size = len(self.orchestrator.combination_cache)

        # 执行第一次选择
        result1 = self.orchestrator.select_agents_intelligent(task)
        cache_size_after_first = len(self.orchestrator.combination_cache)

        # 执行第二次选择（应该命中缓存）
        result2 = self.orchestrator.select_agents_intelligent(task)
        cache_size_after_second = len(self.orchestrator.combination_cache)

        # 验证缓存行为
        self.assertEqual(
            cache_size_after_first, initial_cache_size + 1, "第一次执行应该增加缓存条目"
        )
        self.assertEqual(
            cache_size_after_second, cache_size_after_first, "第二次执行应该命中缓存，不增加条目"
        )

        # 验证结果一致性
        self.assertEqual(
            result1["selected_agents"], result2["selected_agents"], "缓存结果应该一致"
        )

    def test_edge_cases(self):
        """测试边界情况"""
        # 空任务描述
        empty_result = self.orchestrator.select_agents_intelligent("")
        self.assertIsNotNone(empty_result, "空任务应该返回默认结果")

        # 很长的任务描述
        very_long_task = "implement " + "very " * 100 + "complex system"
        long_result = self.orchestrator.select_agents_intelligent(very_long_task)
        self.assertIsNotNone(long_result, "长任务描述应该被正确处理")

        # 特殊字符
        special_char_task = (
            "implement user@auth #system $with %special ^characters &and *symbols"
        )
        special_result = self.orchestrator.select_agents_intelligent(special_char_task)
        self.assertIsNotNone(special_result, "包含特殊字符的任务应该被正确处理")

    def test_time_estimation(self):
        """测试时间估算功能"""
        for task_type, task in self.test_tasks.items():
            with self.subTest(task_type=task_type):
                result = self.orchestrator.select_agents_intelligent(task)
                estimated_time = result.get("estimated_time", "")

                # 时间估算应该包含合理的格式
                self.assertRegex(
                    estimated_time, r"\d+-\d+分钟", f"时间估算格式应该正确: {estimated_time}"
                )

    def test_concurrent_execution(self):
        """测试并发执行安全性"""
        import threading
        import queue

        results_queue = queue.Queue()
        task = self.test_tasks["standard"]

        def worker():
            try:
                result = self.orchestrator.select_agents_intelligent(task)
                results_queue.put(("success", result))
            except Exception as e:
                results_queue.put(("error", str(e)))

        # 启动多个并发线程
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=worker)
            thread.start()
            threads.append(thread)

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 收集结果
        results = []
        while not results_queue.empty():
            status, result = results_queue.get()
            self.assertEqual(status, "success", f"并发执行不应该出错: {result}")
            results.append(result)

        self.assertEqual(len(results), 5, "应该收到5个结果")

        # 所有结果应该一致（由于缓存）
        first_result = results[0]["selected_agents"]
        for result in results[1:]:
            self.assertEqual(result["selected_agents"], first_result, "并发执行结果应该一致")


class TestLazyAgentManager(unittest.TestCase):
    """测试 LazyAgentManager 组件"""

    def setUp(self):
        self.manager = LazyAgentManager()

    def test_agent_metadata_initialization(self):
        """测试Agent元数据初始化"""
        self.assertGreater(len(self.manager.agent_metadata), 20, "应该有足够的Agent元数据")

        # 检查必要的核心Agent
        required_agents = [
            "backend-architect",
            "test-engineer",
            "security-auditor",
            "api-designer",
        ]
        for agent in required_agents:
            self.assertIn(agent, self.manager.agent_metadata, f"应该包含核心Agent: {agent}")

    def test_lazy_loading(self):
        """测试懒加载功能"""
        agent_name = "backend-architect"

        # 初始状态应该没有加载任何Agent
        self.assertEqual(len(self.manager.loaded_agents), 0, "初始状态不应该有已加载的Agent")

        # 加载Agent
        agent = self.manager.load_agent(agent_name)
        self.assertIsNotNone(agent, "应该成功加载Agent")
        self.assertEqual(len(self.manager.loaded_agents), 1, "应该有1个已加载的Agent")

        # 再次加载相同Agent（应该命中缓存）
        agent2 = self.manager.load_agent(agent_name)
        self.assertEqual(agent, agent2, "相同Agent应该返回缓存的实例")
        self.assertEqual(len(self.manager.loaded_agents), 1, "缓存命中不应该增加加载计数")

    def test_category_indexing(self):
        """测试分类索引功能"""
        # 测试按分类获取Agent
        quality_agents = self.manager.get_agents_by_category_fast("quality")
        self.assertGreater(len(quality_agents), 0, "quality分类应该有Agent")

        development_agents = self.manager.get_agents_by_category_fast("development")
        self.assertGreater(len(development_agents), 0, "development分类应该有Agent")

        # 测试不存在的分类
        nonexistent_agents = self.manager.get_agents_by_category_fast("nonexistent")
        self.assertEqual(len(nonexistent_agents), 0, "不存在的分类应该返回空列表")

    def test_performance_metrics(self):
        """测试性能指标收集"""
        initial_metrics = self.manager.get_metrics()

        # 加载几个Agent
        self.manager.load_agent("backend-architect")
        self.manager.load_agent("test-engineer")

        final_metrics = self.manager.get_metrics()

        # 验证指标更新
        self.assertGreater(
            final_metrics["agents_loaded"],
            initial_metrics["agents_loaded"],
            "应该增加已加载Agent计数",
        )
        self.assertGreater(final_metrics["load_time_total"], 0, "应该记录加载时间")


def run_performance_benchmark():
    """运行性能基准测试"""
    print("\n🏁 Running Performance Benchmark...")
    print("=" * 50)

    # 创建测试任务
    test_tasks = [
        "fix simple bug in login form",
        "implement complete user authentication system",
        "design microservices architecture with security",
        "optimize database performance for high load",
        "create React dashboard with real-time analytics",
    ]

    # 测试启动时间
    startup_times = []
    for i in range(10):
        start_time = time.time()
        orchestrator = LazyAgentOrchestrator()
        startup_time = time.time() - start_time
        startup_times.append(startup_time)

    avg_startup = sum(startup_times) / len(startup_times)
    print(f"📊 平均启动时间: {avg_startup*1000:.2f}ms")

    # 测试选择时间
    orchestrator = LazyAgentOrchestrator()
    selection_times = []

    for task in test_tasks * 4:  # 重复测试以测试缓存
        start_time = time.time()
        result = orchestrator.select_agents_intelligent(task)
        selection_time = time.time() - start_time
        selection_times.append(selection_time)

    avg_selection = sum(selection_times) / len(selection_times)
    print(f"📊 平均选择时间: {avg_selection*1000:.2f}ms")

    # 性能统计
    stats = orchestrator.get_performance_stats()
    print(f"📊 缓存命中率: {stats['cache_stats']['cache_hit_rate']}")
    print(f"📊 Agent加载时间: {stats['performance']['avg_agent_load_time']}")

    print("=" * 50)
    return {
        "avg_startup_ms": avg_startup * 1000,
        "avg_selection_ms": avg_selection * 1000,
        "cache_hit_rate": stats["cache_stats"]["cache_hit_rate"],
    }


if __name__ == "__main__":
    # 运行单元测试
    unittest.main(verbosity=2, exit=False)

    # 运行性能基准测试
    benchmark_results = run_performance_benchmark()

    print(f"\n🎯 性能基准测试结果:")
    print(f"   启动时间: {benchmark_results['avg_startup_ms']:.2f}ms")
    print(f"   选择时间: {benchmark_results['avg_selection_ms']:.2f}ms")
    print(f"   缓存命中率: {benchmark_results['cache_hit_rate']}")
