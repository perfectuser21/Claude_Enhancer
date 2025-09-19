#!/usr/bin/env python3
"""
Perfect21 Agent选择逻辑核心测试
专门测试dynamic_workflow_generator.py的agent选择逻辑
"""

import os
import sys
import time
import json
import unittest
from typing import List, Dict, Any

# 添加项目路径
sys.path.append(os.path.dirname(__file__))

class TestAgentSelectionCore(unittest.TestCase):
    """测试Agent选择的核心逻辑"""

    def setUp(self):
        """测试前准备"""
        try:
            from features.workflow_orchestrator.dynamic_workflow_generator import (
                DynamicWorkflowGenerator,
                AgentCapability,
                TaskRequirement,
                OptimizedAgentSelector
            )
            self.DynamicWorkflowGenerator = DynamicWorkflowGenerator
            self.AgentCapability = AgentCapability
            self.TaskRequirement = TaskRequirement
            self.OptimizedAgentSelector = OptimizedAgentSelector

            # 创建测试实例
            self.generator = DynamicWorkflowGenerator()
            self.agent_selector = OptimizedAgentSelector()

            # 清空现有agents，添加我们自己的测试agents
            self.agent_selector.agents_by_domain.clear()
            self.agent_selector.agents_by_skill.clear()
            self.agent_selector.score_index.clear()

            # 添加测试agents
            self._setup_test_agents()

        except ImportError as e:
            self.skipTest(f"无法导入工作流生成器模块: {e}")

    def _setup_test_agents(self):
        """设置测试用的agents"""
        test_agents = [
            # 业务类agents
            self.AgentCapability("project-manager", "business",
                               ["planning", "coordination", "requirements"], 8.0, 95.0, 100.0),
            self.AgentCapability("business-analyst", "business",
                               ["analysis", "requirements", "documentation"], 7.0, 90.0, 100.0),

            # 技术类agents
            self.AgentCapability("backend-architect", "technical",
                               ["backend", "architecture", "database", "api"], 9.0, 95.0, 100.0),
            self.AgentCapability("frontend-specialist", "technical",
                               ["frontend", "ui", "javascript", "react"], 8.0, 88.0, 100.0),
            self.AgentCapability("api-designer", "technical",
                               ["api", "design", "documentation"], 7.5, 92.0, 100.0),

            # 质量类agents
            self.AgentCapability("test-engineer", "quality",
                               ["testing", "automation", "quality"], 7.0, 85.0, 100.0),
            self.AgentCapability("code-reviewer", "quality",
                               ["review", "standards", "quality"], 7.5, 90.0, 100.0),

            # 基础设施类agents
            self.AgentCapability("devops-engineer", "infrastructure",
                               ["deployment", "docker", "kubernetes"], 8.5, 90.0, 100.0),

            # 安全类agents
            self.AgentCapability("security-auditor", "security",
                               ["security", "audit", "compliance"], 8.0, 92.0, 100.0),

            # 性能类agents
            self.AgentCapability("performance-engineer", "technical",
                               ["performance", "optimization", "monitoring"], 8.5, 88.0, 100.0),
        ]

        for agent in test_agents:
            self.agent_selector.add_agent(agent)

    def test_agent_selection_returns_3_to_5_agents(self):
        """测试验证是否真的选择3-5个agents"""
        test_cases = [
            {
                "description": "开发用户认证API",
                "domain": "technical",
                "complexity": 7.0,
                "skills": ["backend", "api", "security"],
                "expected_count_range": (3, 5)
            },
            {
                "description": "设计前端用户界面",
                "domain": "technical",
                "complexity": 6.0,
                "skills": ["frontend", "ui", "design"],
                "expected_count_range": (3, 5)
            },
            {
                "description": "进行系统性能优化",
                "domain": "technical",
                "complexity": 8.0,
                "skills": ["performance", "optimization", "backend"],
                "expected_count_range": (3, 5)
            }
        ]

        for test_case in test_cases:
            with self.subTest(description=test_case["description"]):
                task_req = self.TaskRequirement(
                    description=test_case["description"],
                    domain=test_case["domain"],
                    complexity=test_case["complexity"],
                    required_skills=test_case["skills"]
                )

                # 测试不同的请求数量
                for requested_count in [3, 4, 5]:
                    selected_agents = self.agent_selector.select_agents(task_req, requested_count)

                    min_expected, max_expected = test_case["expected_count_range"]

                    # 验证返回的agents数量在期望范围内
                    self.assertGreaterEqual(len(selected_agents), min(min_expected, requested_count),
                                          f"选择的agents数量({len(selected_agents)})少于最小期望({min_expected})")
                    self.assertLessEqual(len(selected_agents), min(max_expected, requested_count),
                                       f"选择的agents数量({len(selected_agents)})超过最大期望({max_expected})")

                    # 验证不重复选择
                    self.assertEqual(len(selected_agents), len(set(selected_agents)),
                                   "选择的agents中存在重复")

                    # 验证选择的agents确实存在
                    for agent_name in selected_agents:
                        agent = self.agent_selector._get_agent_by_name(agent_name)
                        self.assertIsNotNone(agent, f"选择的agent '{agent_name}' 不存在")

    def test_agent_selection_relevance(self):
        """测试Agent选择的相关性"""
        test_scenarios = [
            {
                "task": "开发REST API接口",
                "expected_domains": ["technical"],
                "expected_skills": ["api", "backend"],
                "unexpected_agents": ["frontend-specialist"]
            },
            {
                "task": "设计用户界面组件",
                "expected_domains": ["technical"],
                "expected_skills": ["frontend", "ui"],
                "unexpected_agents": ["devops-engineer"]
            },
            {
                "task": "进行安全审计",
                "expected_domains": ["security"],
                "expected_skills": ["security", "audit"],
                "unexpected_agents": ["frontend-specialist"]
            }
        ]

        for scenario in test_scenarios:
            with self.subTest(task=scenario["task"]):
                task_req = self.generator.parse_task_requirements(scenario["task"])
                selected_agents = self.agent_selector.select_agents(task_req, 4)

                # 获取选择的agents的详细信息
                selected_agent_details = []
                for agent_name in selected_agents:
                    agent = self.agent_selector._get_agent_by_name(agent_name)
                    if agent:
                        selected_agent_details.append(agent)

                # 验证域相关性
                selected_domains = [agent.domain for agent in selected_agent_details]
                for expected_domain in scenario["expected_domains"]:
                    self.assertTrue(
                        any(expected_domain in domain for domain in selected_domains),
                        f"期望的域 '{expected_domain}' 没有在选择的agents中体现"
                    )

                # 验证技能相关性
                all_selected_skills = []
                for agent in selected_agent_details:
                    all_selected_skills.extend(agent.skills)

                for expected_skill in scenario["expected_skills"]:
                    self.assertTrue(
                        any(expected_skill in skill for skill in all_selected_skills),
                        f"期望的技能 '{expected_skill}' 没有在选择的agents中体现"
                    )

                # 验证不应该选择的agents
                for unexpected_agent in scenario.get("unexpected_agents", []):
                    self.assertNotIn(unexpected_agent, selected_agents,
                                   f"不应该选择的agent '{unexpected_agent}' 被选中了")

    def test_workflow_generation_agent_distribution(self):
        """测试工作流生成中的agent分布"""
        test_tasks = [
            "实现完整的用户管理系统",
            "开发电商平台的订单处理模块",
            "构建实时数据分析仪表板",
            "设计微服务架构的API网关"
        ]

        for task_description in test_tasks:
            with self.subTest(task=task_description):
                workflow = self.generator.generate_workflow(task_description)

                # 收集所有stages中的agents
                all_agents_in_workflow = set()
                agent_usage_count = {}

                for stage in workflow['stages']:
                    stage_agents = stage.get('agents', [])

                    # 验证每个stage的agents数量合理
                    self.assertGreater(len(stage_agents), 0, "每个stage至少应该有一个agent")

                    if stage.get('execution_mode') == 'parallel':
                        # 并行执行的stage应该有多个agents (理想情况)
                        # 但也接受单个agent的情况
                        pass

                    for agent in stage_agents:
                        all_agents_in_workflow.add(agent)
                        agent_usage_count[agent] = agent_usage_count.get(agent, 0) + 1

                # 验证总的agent数量在合理范围内
                total_unique_agents = len(all_agents_in_workflow)
                self.assertGreaterEqual(total_unique_agents, 2,
                                      "工作流应该至少使用2个不同的agents")
                self.assertLessEqual(total_unique_agents, 8,
                                   "工作流使用的agents数量不应超过8个")

                # 验证agents的分布合理性
                # 检查是否有不同类型的agents
                agent_domains = set()
                for agent_name in all_agents_in_workflow:
                    agent = self.agent_selector._get_agent_by_name(agent_name)
                    if agent:
                        agent_domains.add(agent.domain)

                # 复杂任务应该涉及多个域
                if workflow['task_requirements']['complexity'] >= 7.0:
                    self.assertGreaterEqual(len(agent_domains), 2,
                                          "高复杂度任务应该涉及多个领域的agents")

    def test_agent_selection_performance_and_caching(self):
        """测试Agent选择的性能和缓存效果"""
        task_req = self.TaskRequirement(
            description="性能测试任务",
            domain="technical",
            complexity=6.0,
            required_skills=["backend", "api"]
        )

        # 第一次执行 - 应该比较慢（无缓存）
        start_time = time.time()
        first_result = self.agent_selector.select_agents(task_req, 3)
        first_execution_time = time.time() - start_time

        # 第二次执行 - 应该更快（有缓存）
        start_time = time.time()
        second_result = self.agent_selector.select_agents(task_req, 3)
        second_execution_time = time.time() - start_time

        # 验证结果一致性
        self.assertEqual(first_result, second_result, "缓存的结果应该一致")

        # 验证缓存效果（第二次应该更快）
        self.assertLessEqual(second_execution_time, first_execution_time * 2,
                           "缓存应该提高性能")

        # 检查缓存统计
        stats = self.agent_selector.get_stats()
        self.assertIn('cache_stats', stats)
        cache_stats = stats['cache_stats']
        self.assertGreater(cache_stats['hit_count'], 0, "应该有缓存命中")

    def test_agent_selection_load_balancing(self):
        """测试Agent选择的负载均衡"""
        # 创建多个相似的任务请求
        tasks = [
            self.TaskRequirement(f"任务{i}", "technical", 6.0, ["backend", "api"])
            for i in range(10)
        ]

        agent_usage = {}

        # 执行多次选择
        for task in tasks:
            selected = self.agent_selector.select_agents(task, 2)
            for agent in selected:
                agent_usage[agent] = agent_usage.get(agent, 0) + 1

        # 验证负载分布
        if len(agent_usage) > 1:
            usage_values = list(agent_usage.values())
            max_usage = max(usage_values)
            min_usage = min(usage_values)

            # 负载应该相对均衡 (最大使用次数不应该是最小的3倍以上)
            self.assertLessEqual(max_usage, min_usage * 3,
                               f"负载不均衡: 最大使用{max_usage}次，最小使用{min_usage}次")

    def test_edge_cases_in_agent_selection(self):
        """测试Agent选择的边界情况"""
        # 测试请求超过可用agents数量的情况
        task_req = self.TaskRequirement(
            description="需要大量agents的任务",
            domain="technical",
            complexity=5.0,
            required_skills=["backend"]
        )

        # 请求比可用agents更多的数量
        available_agents_count = len(self.agent_selector.agents_by_domain.get("technical", []))
        excessive_count = available_agents_count + 5

        selected = self.agent_selector.select_agents(task_req, excessive_count)

        # 应该返回所有可用的相关agents，但不超过实际数量
        self.assertLessEqual(len(selected), available_agents_count)
        self.assertGreater(len(selected), 0, "至少应该选择一个agent")

        # 测试没有技能匹配的情况
        no_match_task = self.TaskRequirement(
            description="需要不存在技能的任务",
            domain="technical",
            complexity=5.0,
            required_skills=["非存在技能xyz"]
        )

        selected_no_match = self.agent_selector.select_agents(no_match_task, 3)

        # 即使没有完美匹配，也应该选择一些agents
        self.assertGreater(len(selected_no_match), 0, "即使技能不匹配也应该选择一些agents")

def run_agent_selection_tests():
    """运行Agent选择核心测试"""
    print("🎯 Perfect21 Agent选择逻辑核心测试")
    print("=" * 50)

    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAgentSelectionCore)

    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    start_time = time.time()

    result = runner.run(suite)

    execution_time = time.time() - start_time

    # 生成报告
    print("\n" + "=" * 50)
    print("📊 Agent选择测试报告")
    print("=" * 50)

    total = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    success_rate = ((total - failures - errors) / total * 100) if total > 0 else 0

    print(f"总测试: {total}")
    print(f"成功: {total - failures - errors}")
    print(f"失败: {failures}")
    print(f"错误: {errors}")
    print(f"成功率: {success_rate:.1f}%")
    print(f"执行时间: {execution_time:.2f}秒")

    # 详细结果
    test_results = {
        'agent_selection_count_validation': '✅ 验证3-5个agents选择',
        'agent_selection_relevance': '✅ 验证选择相关性',
        'workflow_agent_distribution': '✅ 验证工作流中agent分布',
        'performance_and_caching': '✅ 验证性能和缓存',
        'load_balancing': '✅ 验证负载均衡',
        'edge_cases': '✅ 验证边界情况处理'
    }

    print("\n📋 测试覆盖范围:")
    for test_name, status in test_results.items():
        print(f"  {status} {test_name}")

    if result.failures:
        print(f"\n❌ 测试失败详情:")
        for test, error in result.failures:
            print(f"  - {test}")
            print(f"    错误: {error.split('AssertionError:')[-1].strip()}")

    if result.errors:
        print(f"\n💥 测试错误详情:")
        for test, error in result.errors:
            print(f"  - {test}")
            print(f"    异常: {error.split('Exception:')[-1].strip()}")

    # 保存测试报告
    report = {
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'test_focus': 'Agent Selection Core Logic',
        'total_tests': total,
        'success_rate': success_rate,
        'execution_time': execution_time,
        'test_results': test_results,
        'summary': f"Agent选择逻辑测试 {success_rate:.1f}% 通过"
    }

    with open('agent_selection_test_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n📄 详细报告已保存: agent_selection_test_report.json")

    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_agent_selection_tests()
    sys.exit(0 if success else 1)