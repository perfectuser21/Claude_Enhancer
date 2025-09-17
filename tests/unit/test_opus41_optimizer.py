#!/usr/bin/env python3
"""
Opus41Optimizer 单元测试
测试质量优先工作流优化器的所有核心功能
"""

import os
import sys
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from features.opus41_optimizer import Opus41Optimizer, QualityLevel

class TestOpus41Optimizer:
    """Opus41Optimizer 测试类"""

    @pytest.fixture
    def optimizer(self):
        """创建优化器实例"""
        return Opus41Optimizer()

    def test_optimizer_initialization(self, optimizer):
        """测试优化器初始化"""
        assert optimizer is not None
        assert optimizer.max_parallel_agents == 20
        assert optimizer.quality_threshold == 0.95
        assert optimizer.max_refinement_rounds == 5
        assert len(optimizer.agent_categories) >= 8

    def test_agent_categories_complete(self, optimizer):
        """测试Agent分类完整性"""
        expected_categories = [
            'business', 'development', 'frameworks', 'quality',
            'infrastructure', 'data_ai', 'specialized', 'industry', 'orchestration'
        ]

        for category in expected_categories:
            assert category in optimizer.agent_categories
            assert len(optimizer.agent_categories[category]) > 0

    @pytest.mark.parametrize("task,expected_agents", [
        ("实现用户认证API", ['project-manager', 'orchestrator', 'api-designer', 'backend-architect', 'test-engineer']),
        ("开发React前端界面", ['project-manager', 'orchestrator', 'frontend-specialist', 'ux-designer', 'react-pro']),
        ("数据库设计优化", ['project-manager', 'orchestrator', 'backend-architect', 'database-specialist', 'devops-engineer']),
        ("安全审计系统", ['project-manager', 'orchestrator', 'security-auditor', 'backend-architect']),
    ])
    def test_select_optimal_agents_by_task(self, optimizer, task, expected_agents):
        """测试基于任务类型选择最优Agent"""
        agents = optimizer.select_optimal_agents(task, QualityLevel.PREMIUM)

        # 验证核心agents都包含在内
        for agent in expected_agents:
            assert agent in agents

        # 验证Agent数量合理
        assert 8 <= len(agents) <= 12

    def test_select_agents_quality_levels(self, optimizer):
        """测试不同质量级别的Agent选择"""
        task = "实现完整的电商系统"

        # 快速模式
        fast_agents = optimizer.select_optimal_agents(task, QualityLevel.FAST)
        assert len(fast_agents) <= 5

        # 平衡模式
        balanced_agents = optimizer.select_optimal_agents(task, QualityLevel.BALANCED)
        assert len(balanced_agents) <= 8

        # 优质模式
        premium_agents = optimizer.select_optimal_agents(task, QualityLevel.PREMIUM)
        assert len(premium_agents) <= 12

        # 极致模式
        ultimate_agents = optimizer.select_optimal_agents(task, QualityLevel.ULTIMATE)
        assert len(ultimate_agents) <= 20

    def test_create_parallel_execution_plan(self, optimizer):
        """测试并行执行计划创建"""
        task = "开发用户管理系统"
        agents = ["project-manager", "business-analyst", "api-designer", "backend-architect", "test-engineer"]

        plan = optimizer.create_parallel_execution_plan(agents, task)

        # 验证计划结构
        assert 'task' in plan
        assert 'total_agents' in plan
        assert 'execution_layers' in plan
        assert 'sync_points' in plan
        assert 'quality_checks' in plan

        assert plan['task'] == task
        assert plan['total_agents'] == len(agents)
        assert len(plan['execution_layers']) >= 1

    def test_execution_layers_structure(self, optimizer):
        """测试执行层结构"""
        task = "构建AI推荐系统"
        agents = [
            "project-manager", "business-analyst", "requirements-analyst",
            "api-designer", "backend-architect", "ai-engineer",
            "test-engineer", "security-auditor"
        ]

        plan = optimizer.create_parallel_execution_plan(agents, task)

        # 验证第一层（深度理解）
        if plan['execution_layers']:
            layer1 = plan['execution_layers'][0]
            assert layer1['name'] == '深度理解'
            assert layer1['parallel'] is True
            assert 'agents' in layer1
            assert 'prompts' in layer1

    def test_sync_points_creation(self, optimizer):
        """测试同步点创建"""
        task = "开发区块链钱包"
        agents = [
            "project-manager", "business-analyst", "api-designer",
            "backend-architect", "security-auditor", "test-engineer"
        ]

        plan = optimizer.create_parallel_execution_plan(agents, task)

        # 验证同步点设置
        sync_points = plan['sync_points']
        assert len(sync_points) >= 1

        for sync_point in sync_points:
            assert 'after_layer' in sync_point
            assert 'type' in sync_point
            assert 'description' in sync_point

    def test_prompt_generation(self, optimizer):
        """测试Prompt生成"""
        task = "实现微服务架构"

        # 测试分析阶段prompt
        analysis_prompt = optimizer._generate_analysis_prompt("project-manager", task)
        assert task in analysis_prompt
        assert "项目范围" in analysis_prompt
        assert "时间线" in analysis_prompt

        # 测试设计阶段prompt
        design_prompt = optimizer._generate_design_prompt("api-designer", task)
        assert task in design_prompt
        assert "架构方案" in design_prompt
        assert "技术选型" in design_prompt

        # 测试实现阶段prompt
        impl_prompt = optimizer._generate_implementation_prompt("backend-architect", task)
        assert task in impl_prompt
        assert "核心功能代码" in impl_prompt
        assert "测试覆盖率>90%" in impl_prompt

        # 测试QA阶段prompt
        qa_prompt = optimizer._generate_qa_prompt("security-auditor", task)
        assert task in qa_prompt
        assert "安全漏洞" in qa_prompt
        assert "认证授权" in qa_prompt

    def test_quality_evaluation(self, optimizer):
        """测试质量评估"""
        # 高质量结果
        high_quality_results = {
            'test_coverage': 95,
            'code_quality': 90,
            'documentation': True,
            'security_check': 'passed'
        }

        score = optimizer._evaluate_quality(high_quality_results)
        assert score >= 0.9

        # 低质量结果
        low_quality_results = {
            'test_coverage': 60,
            'code_quality': 70,
            'documentation': False,
            'security_check': 'failed'
        }

        score = optimizer._evaluate_quality(low_quality_results)
        assert score < 0.8

    def test_identify_improvements(self, optimizer):
        """测试改进识别"""
        # 需要改进的结果
        poor_results = {
            'test_coverage': 70,
            'code_quality': 80,
            'documentation': False,
            'performance_issues': True
        }

        improvements = optimizer._identify_improvements(poor_results)

        assert 'increase_test_coverage' in improvements
        assert 'improve_code_quality' in improvements
        assert 'add_documentation' in improvements
        assert 'optimize_performance' in improvements

    def test_select_refinement_agents(self, optimizer):
        """测试选择改进Agents"""
        improvements = [
            'increase_test_coverage',
            'improve_code_quality',
            'add_documentation',
            'optimize_performance'
        ]

        agents = optimizer._select_refinement_agents(improvements)

        # 验证选择的agents符合改进需求
        assert 'test-engineer' in agents
        assert 'code-reviewer' in agents
        assert 'technical-writer' in agents
        assert 'performance-engineer' in agents

    def test_generate_refinement_prompts(self, optimizer):
        """测试生成改进Prompts"""
        improvements = ['increase_test_coverage', 'improve_code_quality']
        current_results = {
            'test_coverage': 75,
            'code_quality': 80
        }

        prompts = optimizer._generate_refinement_prompts(improvements, current_results)

        assert 'test-engineer' in prompts
        assert 'code-reviewer' in prompts

        # 验证prompt包含当前状态信息
        assert '75' in prompts['test-engineer']
        assert '80' in prompts['code-reviewer']

    def test_merge_results(self, optimizer):
        """测试结果合并"""
        current = {
            'test_coverage': 80,
            'code_quality': 85
        }

        refinement = {
            'round': 1,
            'test_coverage': 95,
            'code_quality': 90
        }

        merged = optimizer._merge_results(current, refinement)

        # 验证取最大值
        assert merged['test_coverage'] == 95
        assert merged['code_quality'] == 90

        # 验证添加历史记录
        assert 'refinement_history' in merged
        assert len(merged['refinement_history']) == 1

    def test_optimize_with_refinement(self, optimizer):
        """测试多轮优化"""
        task = "开发企业级应用"
        initial_results = {
            'test_coverage': 70,
            'code_quality': 75,
            'documentation': False,
            'security_check': 'passed'
        }

        with patch.object(optimizer, '_evaluate_quality') as mock_eval:
            with patch.object(optimizer, '_identify_improvements') as mock_identify:
                with patch.object(optimizer, '_select_refinement_agents') as mock_select:

                    # 设置模拟返回值
                    mock_eval.side_effect = [0.8, 0.9, 0.96]  # 逐步提升质量
                    mock_identify.return_value = ['increase_test_coverage']
                    mock_select.return_value = ['test-engineer']

                    result = optimizer.optimize_with_refinement(task, initial_results, rounds=3)

                    assert 'final_results' in result
                    assert 'quality_score' in result
                    assert 'refinement_rounds' in result
                    assert 'success' in result

    def test_generate_ultimate_workflow(self, optimizer):
        """测试生成极致工作流"""
        task = "构建分布式系统监控平台"

        workflow = optimizer.generate_ultimate_workflow(task)

        # 验证工作流包含关键元素
        assert task in workflow
        assert "Perfect21极致质量工作流" in workflow
        assert "Opus 4.1专属" in workflow
        assert "质量优先" in workflow
        assert "大规模并行" in workflow
        assert "多轮优化" in workflow
        assert "代码覆盖率 > 95%" in workflow

    def test_workflow_contains_execution_plan(self, optimizer):
        """测试工作流包含执行计划"""
        task = "实现智能客服系统"

        workflow = optimizer.generate_ultimate_workflow(task)

        # 验证包含执行计划结构
        assert "执行计划" in workflow
        assert "第1层" in workflow or "第2层" in workflow
        assert "@" in workflow  # 包含Agent引用
        assert "同步点" in workflow

    @pytest.mark.parametrize("quality_level", [
        QualityLevel.FAST,
        QualityLevel.BALANCED,
        QualityLevel.PREMIUM,
        QualityLevel.ULTIMATE
    ])
    def test_different_quality_levels(self, optimizer, quality_level):
        """测试不同质量级别的配置"""
        task = "开发在线教育平台"

        agents = optimizer.select_optimal_agents(task, quality_level)
        plan = optimizer.create_parallel_execution_plan(agents, task)

        # 验证基本结构
        assert len(agents) > 0
        assert plan['total_agents'] == len(agents)

        # 验证质量级别影响
        if quality_level == QualityLevel.ULTIMATE:
            assert len(agents) >= 12
        elif quality_level == QualityLevel.PREMIUM:
            assert len(agents) >= 8
        elif quality_level == QualityLevel.BALANCED:
            assert len(agents) >= 5
        else:  # FAST
            assert len(agents) >= 3

    def test_agent_prompt_personalization(self, optimizer):
        """测试Agent Prompt个性化"""
        task = "开发移动应用"

        # 测试不同Agent的个性化prompt
        pm_prompt = optimizer._generate_analysis_prompt("project-manager", task)
        ba_prompt = optimizer._generate_analysis_prompt("business-analyst", task)
        ra_prompt = optimizer._generate_analysis_prompt("requirements-analyst", task)

        # 验证每个agent有特定的关注点
        assert "项目范围" in pm_prompt
        assert "业务价值" in ba_prompt
        assert "功能需求" in ra_prompt

        # 验证基础内容都包含
        for prompt in [pm_prompt, ba_prompt, ra_prompt]:
            assert task in prompt
            assert "分析" in prompt

    def test_error_handling(self, optimizer):
        """测试错误处理"""
        # 测试空任务
        agents = optimizer.select_optimal_agents("", QualityLevel.PREMIUM)
        assert len(agents) >= 2  # 至少有核心agents

        # 测试无效质量级别（通过枚举保证不会发生）
        try:
            agents = optimizer.select_optimal_agents("test task", QualityLevel.PREMIUM)
            assert True  # 正常情况
        except Exception:
            pytest.fail("不应该抛出异常")

    def test_performance_metrics(self, optimizer):
        """测试性能指标"""
        import time

        task = "开发大型电商平台"

        # 测试Agent选择性能
        start_time = time.time()
        agents = optimizer.select_optimal_agents(task, QualityLevel.ULTIMATE)
        selection_time = time.time() - start_time

        assert selection_time < 1.0  # 应该在1秒内完成
        assert len(agents) > 0

        # 测试执行计划创建性能
        start_time = time.time()
        plan = optimizer.create_parallel_execution_plan(agents, task)
        planning_time = time.time() - start_time

        assert planning_time < 2.0  # 应该在2秒内完成
        assert len(plan['execution_layers']) > 0

    def test_concurrent_optimization(self, optimizer):
        """测试并发优化能力"""
        import threading
        import queue

        tasks = [
            "开发用户系统",
            "构建支付平台",
            "实现消息队列",
            "设计数据分析"
        ]

        results_queue = queue.Queue()

        def optimize_task(task):
            agents = optimizer.select_optimal_agents(task, QualityLevel.PREMIUM)
            plan = optimizer.create_parallel_execution_plan(agents, task)
            results_queue.put({'task': task, 'agents': len(agents), 'plan': plan})

        # 并发执行
        threads = []
        for task in tasks:
            thread = threading.Thread(target=optimize_task, args=(task,))
            threads.append(thread)
            thread.start()

        # 等待完成
        for thread in threads:
            thread.join()

        # 验证结果
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())

        assert len(results) == len(tasks)
        for result in results:
            assert result['agents'] > 0
            assert len(result['plan']['execution_layers']) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])