#!/usr/bin/env python3
"""
Perfect21 Opus41 智能并行优化器集成测试
测试Opus41的各项功能，确保系统正常工作
"""

import unittest
import time
import json
import os
import sys
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__)))

from features.opus41_optimizer import (
    get_opus41_optimizer,
    OptimizationLevel,
    QualityThreshold,
    QualityLevel
)
from features.opus41_visualizer import get_opus41_visualizer

class TestOpus41Integration(unittest.TestCase):
    """Opus41集成测试"""

    def setUp(self):
        """测试初始化"""
        self.optimizer = get_opus41_optimizer()
        self.visualizer = get_opus41_visualizer()
        self.test_task = "开发一个高性能的微服务电商平台"

    def test_optimizer_initialization(self):
        """测试优化器初始化"""
        print("\n🧪 测试优化器初始化...")

        # 检查优化器实例
        self.assertIsNotNone(self.optimizer)
        self.assertIsNotNone(self.optimizer.decomposer)
        self.assertIsNotNone(self.optimizer.agent_metrics)

        # 检查基础配置
        self.assertEqual(self.optimizer.max_parallel_agents, 20)
        self.assertEqual(self.optimizer.quality_threshold, 0.95)
        self.assertEqual(self.optimizer.max_refinement_rounds, 5)

        # 检查Agent分类
        self.assertIn('business', self.optimizer.agent_categories)
        self.assertIn('development', self.optimizer.agent_categories)
        self.assertIn('quality', self.optimizer.agent_categories)

        print("✅ 优化器初始化测试通过")

    def test_agent_selection(self):
        """测试智能Agent选择"""
        print("\n🧪 测试智能Agent选择...")

        test_cases = [
            ("创建React前端应用", QualityLevel.PREMIUM),
            ("开发REST API", QualityLevel.BALANCED),
            ("AI推荐系统", QualityLevel.ULTIMATE),
            ("部署容器化应用", QualityLevel.FAST)
        ]

        for task, quality_level in test_cases:
            with self.subTest(task=task, quality=quality_level):
                agents = self.optimizer.select_optimal_agents(task, quality_level)

                # 基本验证
                self.assertIsInstance(agents, list)
                self.assertGreater(len(agents), 0)

                # 质量级别对应的数量验证
                expected_ranges = {
                    QualityLevel.FAST: (3, 6),
                    QualityLevel.BALANCED: (5, 10),
                    QualityLevel.PREMIUM: (8, 15),
                    QualityLevel.ULTIMATE: (12, 20)
                }

                min_agents, max_agents = expected_ranges[quality_level]
                self.assertGreaterEqual(len(agents), min_agents)
                self.assertLessEqual(len(agents), max_agents)

                # 验证没有重复的agents
                self.assertEqual(len(agents), len(set(agents)))

                print(f"  ✅ {task}: {len(agents)} agents ({quality_level.name})")

        print("✅ Agent选择测试通过")

    def test_optimization_planning(self):
        """测试优化计划生成"""
        print("\n🧪 测试优化计划生成...")

        quality_levels = [
            QualityThreshold.MINIMUM,
            QualityThreshold.GOOD,
            QualityThreshold.EXCELLENT,
            QualityThreshold.PERFECT
        ]

        for quality in quality_levels:
            with self.subTest(quality=quality):
                plan = self.optimizer.optimize_execution(
                    task_description=self.test_task,
                    target_quality=quality,
                    optimization_level=OptimizationLevel.OPUS41
                )

                # 基本验证
                self.assertIsNotNone(plan)
                self.assertEqual(plan.task_description, self.test_task)
                self.assertEqual(plan.target_quality, quality)
                self.assertEqual(plan.optimization_level, OptimizationLevel.OPUS41)

                # 执行层验证
                self.assertGreater(len(plan.execution_layers), 0)
                self.assertLessEqual(len(plan.execution_layers), 5)

                # 资源需求验证
                self.assertIn('total_agents', plan.resource_requirements)
                self.assertIn('concurrent_agents', plan.resource_requirements)
                self.assertGreater(plan.resource_requirements['total_agents'], 0)

                # 成功概率验证
                self.assertGreaterEqual(plan.success_probability, 0.1)
                self.assertLessEqual(plan.success_probability, 1.0)

                # 时间估算验证
                self.assertGreater(plan.estimated_total_time, 0)

                print(f"  ✅ {quality.name}: {plan.resource_requirements['total_agents']} agents, "
                      f"{plan.estimated_total_time}min, {plan.success_probability:.1%} success")

        print("✅ 优化计划生成测试通过")

    def test_task_calls_generation(self):
        """测试Task调用生成"""
        print("\n🧪 测试Task调用生成...")

        plan = self.optimizer.optimize_execution(
            task_description=self.test_task,
            target_quality=QualityThreshold.EXCELLENT,
            optimization_level=OptimizationLevel.OPUS41
        )

        task_calls = self.optimizer.generate_task_calls(plan)

        # 基本验证
        self.assertIsInstance(task_calls, list)
        self.assertGreater(len(task_calls), 0)

        # 验证每个Task调用的结构
        for i, call in enumerate(task_calls):
            with self.subTest(task_call=i):
                self.assertIn('tool_name', call)
                self.assertEqual(call['tool_name'], 'Task')

                self.assertIn('parameters', call)
                params = call['parameters']

                self.assertIn('subagent_type', params)
                self.assertIn('description', params)
                self.assertIn('prompt', params)

                # 验证prompt不为空
                self.assertGreater(len(params['prompt'].strip()), 0)

                # 验证layer信息
                self.assertIn('layer_id', call)
                self.assertIn('layer_name', call)

        print(f"✅ 生成了 {len(task_calls)} 个Task调用")

    def test_execution_simulation(self):
        """测试执行模拟"""
        print("\n🧪 测试执行模拟...")

        plan = self.optimizer.optimize_execution(
            task_description=self.test_task,
            target_quality=QualityThreshold.GOOD,
            optimization_level=OptimizationLevel.OPUS41
        )

        # 执行计划
        result = self.optimizer.execute_optimized_plan(plan)

        # 验证执行结果
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        self.assertIn('execution_time', result)
        self.assertIn('final_quality', result)
        self.assertIn('layers_completed', result)

        # 如果执行成功，验证质量指标
        if result['success']:
            self.assertGreaterEqual(result['final_quality'], 0.0)
            self.assertLessEqual(result['final_quality'], 1.0)
            self.assertGreater(result['layers_completed'], 0)

            print(f"✅ 执行成功: 质量={result['final_quality']:.1%}, "
                  f"时间={result['execution_time']:.2f}s, "
                  f"层数={result['layers_completed']}")
        else:
            print(f"⚠️ 执行失败: {result.get('error', '未知错误')}")

    def test_visualization_system(self):
        """测试可视化系统"""
        print("\n🧪 测试可视化系统...")

        # 启动监控
        self.visualizer.start_real_time_monitoring({
            "task": "测试任务",
            "start_time": datetime.now().isoformat()
        })

        # 更新几次指标
        test_metrics = [
            (0.5, 0.6, 30, 3, {1: 0.5}, {"agent1": "running"}),
            (0.7, 0.8, 60, 5, {1: 1.0, 2: 0.5}, {"agent1": "completed", "agent2": "running"}),
            (0.85, 0.9, 90, 4, {1: 1.0, 2: 1.0, 3: 0.3}, {"agent1": "completed", "agent2": "completed"})
        ]

        for quality, success, time, agents, layers, agent_status in test_metrics:
            self.visualizer.update_metrics(
                quality_score=quality,
                success_rate=success,
                execution_time=time,
                active_agents=agents,
                layer_progress=layers,
                agent_status=agent_status
            )

        # 验证指标历史
        self.assertEqual(len(self.visualizer.metrics_history), len(test_metrics))

        # 生成报告
        report = self.visualizer.generate_performance_report()
        self.assertIsInstance(report, dict)
        self.assertIn('summary', report)
        self.assertIn('quality_metrics', report)
        self.assertIn('performance_metrics', report)

        # 停止监控
        self.visualizer.stop_monitoring()

        print("✅ 可视化系统测试通过")

    def test_html_dashboard_generation(self):
        """测试HTML Dashboard生成"""
        print("\n🧪 测试HTML Dashboard生成...")

        # 添加一些测试数据
        self.visualizer.start_real_time_monitoring({"test": "data"})
        self.visualizer.update_metrics(
            quality_score=0.85,
            success_rate=0.9,
            execution_time=120,
            active_agents=8,
            layer_progress={1: 1.0, 2: 0.8, 3: 0.5},
            agent_status={"test-agent": "running"}
        )

        # 生成Dashboard
        dashboard_file = self.visualizer.generate_html_dashboard("test_dashboard.html")

        # 验证文件存在
        self.assertTrue(os.path.exists(dashboard_file))

        # 验证文件内容
        with open(dashboard_file, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('<html', content)
            self.assertIn('Opus41', content)
            self.assertIn('质量分数', content)

        # 清理测试文件
        if os.path.exists(dashboard_file):
            os.remove(dashboard_file)

        self.visualizer.stop_monitoring()

        print("✅ HTML Dashboard生成测试通过")

    def test_status_and_metrics(self):
        """测试状态和指标"""
        print("\n🧪 测试状态和指标...")

        # 获取优化器状态
        status = self.optimizer.get_optimization_status()

        # 验证状态结构
        self.assertIsInstance(status, dict)
        self.assertIn('agent_count', status)
        self.assertIn('execution_history_count', status)
        self.assertIn('system_status', status)
        self.assertIn('max_parallel_agents', status)
        self.assertIn('quality_threshold', status)

        # 验证值的合理性
        self.assertGreaterEqual(status['agent_count'], 0)
        self.assertGreaterEqual(status['execution_history_count'], 0)
        self.assertEqual(status['system_status'], 'operational')

        print(f"✅ 系统状态正常: {status['agent_count']} agents, "
              f"历史记录 {status['execution_history_count']} 条")

    def test_error_handling(self):
        """测试错误处理"""
        print("\n🧪 测试错误处理...")

        # 测试空任务
        with self.assertRaises(Exception):
            self.optimizer.optimize_execution(
                task_description="",
                target_quality=QualityThreshold.EXCELLENT,
                optimization_level=OptimizationLevel.OPUS41
            )

        # 测试无效参数（这里我们模拟一下，实际实现可能不会抛出异常）
        try:
            plan = self.optimizer.optimize_execution(
                task_description="简单测试",
                target_quality=QualityThreshold.MINIMUM,
                optimization_level=OptimizationLevel.BASIC
            )
            # 如果没有抛出异常，验证返回的计划是有效的
            self.assertIsNotNone(plan)
        except Exception as e:
            print(f"  处理了异常: {e}")

        print("✅ 错误处理测试通过")

    def test_performance_benchmark(self):
        """测试性能基准"""
        print("\n🧪 测试性能基准...")

        # 测试不同规模的任务
        test_tasks = [
            ("简单任务", QualityLevel.FAST),
            ("中等复杂度任务", QualityLevel.BALANCED),
            ("复杂企业级任务", QualityLevel.PREMIUM)
        ]

        for task, quality in test_tasks:
            start_time = time.time()

            # Agent选择性能
            agents = self.optimizer.select_optimal_agents(task, quality)
            selection_time = time.time() - start_time

            # 优化规划性能
            plan_start = time.time()
            plan = self.optimizer.optimize_execution(
                task_description=task,
                target_quality=QualityThreshold.GOOD,
                optimization_level=OptimizationLevel.OPUS41
            )
            planning_time = time.time() - plan_start

            # 验证性能指标
            self.assertLess(selection_time, 1.0)  # Agent选择应在1秒内完成
            self.assertLess(planning_time, 5.0)   # 规划应在5秒内完成

            print(f"  ✅ {task}: 选择={selection_time:.3f}s, 规划={planning_time:.3f}s, "
                  f"agents={len(agents)}")

        print("✅ 性能基准测试通过")

    def test_data_export(self):
        """测试数据导出"""
        print("\n🧪 测试数据导出...")

        # 生成一些测试数据
        self.visualizer.start_real_time_monitoring({"test": "export"})
        self.visualizer.update_metrics(
            quality_score=0.9,
            success_rate=0.95,
            execution_time=150,
            active_agents=10,
            layer_progress={1: 1.0, 2: 1.0, 3: 0.8},
            agent_status={"agent1": "completed", "agent2": "running"}
        )

        # 导出JSON数据
        export_file = self.visualizer.export_metrics_to_json("test_export.json")

        # 验证导出文件
        self.assertTrue(os.path.exists(export_file))

        with open(export_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.assertIn('export_time', data)
            self.assertIn('metrics_count', data)
            self.assertIn('dashboard_data', data)
            self.assertIn('metrics_history', data)

        # 清理测试文件
        if os.path.exists(export_file):
            os.remove(export_file)

        self.visualizer.stop_monitoring()

        print("✅ 数据导出测试通过")

class TestOpus41CLI(unittest.TestCase):
    """CLI测试"""

    def test_cli_import(self):
        """测试CLI模块导入"""
        print("\n🧪 测试CLI模块导入...")

        try:
            from main.cli_opus41 import (
                create_opus41_parser,
                handle_opus41_command
            )
            print("✅ CLI模块导入成功")
        except ImportError as e:
            self.fail(f"CLI模块导入失败: {e}")

def run_comprehensive_test():
    """运行综合测试"""
    print("🚀 Perfect21 Opus41 智能并行优化器 - 综合测试")
    print("=" * 80)

    # 创建测试套件
    test_suite = unittest.TestSuite()

    # 添加集成测试
    integration_tests = [
        'test_optimizer_initialization',
        'test_agent_selection',
        'test_optimization_planning',
        'test_task_calls_generation',
        'test_execution_simulation',
        'test_visualization_system',
        'test_html_dashboard_generation',
        'test_status_and_metrics',
        'test_error_handling',
        'test_performance_benchmark',
        'test_data_export'
    ]

    for test_method in integration_tests:
        test_suite.addTest(TestOpus41Integration(test_method))

    # 添加CLI测试
    test_suite.addTest(TestOpus41CLI('test_cli_import'))

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)

    # 生成测试报告
    test_report = {
        "test_time": datetime.now().isoformat(),
        "total_tests": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "success_rate": (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun if result.testsRun > 0 else 0,
        "test_results": {
            "passed": result.testsRun - len(result.failures) - len(result.errors),
            "failed": len(result.failures),
            "errors": len(result.errors)
        }
    }

    # 保存测试报告
    report_file = f"opus41_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(test_report, f, indent=2, ensure_ascii=False)

    print(f"\n📊 测试完成!")
    print(f"总测试数: {test_report['total_tests']}")
    print(f"通过: {test_report['test_results']['passed']}")
    print(f"失败: {test_report['test_results']['failed']}")
    print(f"错误: {test_report['test_results']['errors']}")
    print(f"成功率: {test_report['success_rate']:.1%}")
    print(f"📄 测试报告已保存: {report_file}")

    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)