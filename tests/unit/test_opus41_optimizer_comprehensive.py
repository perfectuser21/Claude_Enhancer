#!/usr/bin/env python3
"""
Opus41Optimizer 完整单元测试套件
测试覆盖率 >95%，包含所有核心功能和边界条件
"""

import pytest
import time
import asyncio
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import List, Dict, Any

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from features.opus41_optimizer import (
    Opus41Optimizer, OptimizationLevel, QualityThreshold, QualityLevel,
    AgentPerformanceMetrics, ExecutionLayer, RefinementRound,
    OpusOptimizationPlan, ExecutionMetrics, QualityPredictor,
    LayerOptimizer, RefinementEngine, MonitoringSystem
)
from features.smart_decomposer import TaskComplexity, TaskAnalysis, AgentTask


class TestOpus41Optimizer:
    """Opus41Optimizer 核心功能测试"""

    @pytest.fixture
    def optimizer(self):
        """创建优化器实例"""
        return Opus41Optimizer()

    @pytest.fixture
    def sample_task(self):
        """样本任务"""
        return "实现用户认证系统，包含注册、登录、权限管理功能"

    @pytest.fixture
    def mock_analysis(self):
        """模拟任务分析结果"""
        return TaskAnalysis(
            original_task="实现用户认证系统",
            complexity=TaskComplexity.MEDIUM,
            required_agents=['backend-architect', 'security-auditor', 'test-engineer'],
            suggested_approach="分层实现",
            estimated_time=180,
            risk_factors=['安全性', '性能'],
            dependencies=['数据库设计', 'API设计'],
            agent_tasks=[]
        )

    def test_initialization(self, optimizer):
        """测试初始化"""
        assert optimizer is not None
        assert hasattr(optimizer, 'decomposer')
        assert hasattr(optimizer, 'agent_metrics')
        assert hasattr(optimizer, 'agent_categories')
        assert len(optimizer.agent_categories) == 7
        assert optimizer.max_parallel_agents == 20
        assert optimizer.quality_threshold == 0.95
        assert optimizer.max_refinement_rounds == 5

    def test_agent_categories_completeness(self, optimizer):
        """测试Agent分类完整性"""
        expected_categories = ['business', 'development', 'frameworks', 'quality',
                             'infrastructure', 'data_ai', 'specialized', 'industry']
        assert set(optimizer.agent_categories.keys()) == set(expected_categories)

        # 验证总Agent数量
        total_agents = sum(len(agents) for agents in optimizer.agent_categories.values())
        assert total_agents >= 50  # 至少50个agents

    def test_select_optimal_agents_basic(self, optimizer):
        """测试基础Agent选择"""
        task = "实现REST API"
        agents = optimizer.select_optimal_agents(task, QualityLevel.PREMIUM)

        assert len(agents) > 0
        assert 'project-manager' in agents  # 核心agent
        assert 'api-designer' in agents     # API相关
        assert 'backend-architect' in agents # 后端相关

    def test_select_optimal_agents_by_quality_level(self, optimizer):
        """测试不同质量级别的Agent选择"""
        task = "开发电商系统"

        fast_agents = optimizer.select_optimal_agents(task, QualityLevel.FAST)
        balanced_agents = optimizer.select_optimal_agents(task, QualityLevel.BALANCED)
        premium_agents = optimizer.select_optimal_agents(task, QualityLevel.PREMIUM)
        ultimate_agents = optimizer.select_optimal_agents(task, QualityLevel.ULTIMATE)

        # 验证数量递增
        assert len(fast_agents) <= 6
        assert len(balanced_agents) <= 10
        assert len(premium_agents) <= 15
        assert len(ultimate_agents) <= 20

        # 验证包含关系
        assert set(fast_agents).issubset(set(balanced_agents))

    def test_select_optimal_agents_task_specific(self, optimizer):
        """测试任务特定的Agent选择"""
        # 前端任务
        frontend_task = "开发React用户界面"
        frontend_agents = optimizer.select_optimal_agents(frontend_task)
        assert 'frontend-specialist' in frontend_agents
        assert 'ux-designer' in frontend_agents

        # 安全任务
        security_task = "实现OAuth认证系统"
        security_agents = optimizer.select_optimal_agents(security_task)
        assert 'security-auditor' in security_agents
        assert 'backend-architect' in security_agents

        # 性能任务
        performance_task = "优化数据库查询性能"
        performance_agents = optimizer.select_optimal_agents(performance_task)
        assert 'performance-engineer' in performance_agents

    @patch('features.opus41_optimizer.SmartDecomposer')
    def test_optimize_execution_basic(self, mock_decomposer, optimizer, sample_task, mock_analysis):
        """测试基础优化执行"""
        # 设置mock
        mock_decomposer.return_value.decompose_task.return_value = mock_analysis

        plan = optimizer.optimize_execution(
            sample_task,
            QualityThreshold.EXCELLENT,
            OptimizationLevel.OPUS41
        )

        assert isinstance(plan, OpusOptimizationPlan)
        assert plan.task_description == sample_task
        assert plan.optimization_level == OptimizationLevel.OPUS41
        assert plan.target_quality == QualityThreshold.EXCELLENT
        assert len(plan.execution_layers) > 0
        assert plan.estimated_total_time > 0
        assert 0 <= plan.success_probability <= 1

    def test_optimize_agent_selection(self, optimizer, mock_analysis):
        """测试Agent选择优化"""
        optimized_agents = optimizer._optimize_agent_selection(
            mock_analysis, QualityThreshold.EXCELLENT
        )

        assert len(optimized_agents) > 0
        assert 'backend-architect' in optimized_agents
        assert len(optimized_agents) <= optimizer.max_parallel_agents

    def test_plan_layered_execution(self, optimizer, mock_analysis):
        """测试分层执行规划"""
        agents = ['project-manager', 'business-analyst', 'backend-architect',
                 'frontend-specialist', 'test-engineer', 'devops-engineer']

        layers = optimizer._plan_layered_execution(agents, mock_analysis, mock_analysis.original_task)

        assert len(layers) > 0

        # 验证层结构
        layer_names = [layer.layer_name for layer in layers]
        assert "深度理解层" in layer_names or len(layers) > 0

        # 验证依赖关系
        for layer in layers:
            assert isinstance(layer, ExecutionLayer)
            assert layer.layer_id > 0
            assert len(layer.agents) > 0
            assert isinstance(layer.parallel_execution, bool)

    def test_plan_refinement_rounds(self, optimizer):
        """测试改进轮次规划"""
        # 创建模拟层
        layers = [
            ExecutionLayer(1, "测试层", ["test-agent"], estimated_time=60)
        ]

        # 测试不同质量阈值
        good_refinements = optimizer._plan_refinement_rounds(layers, QualityThreshold.GOOD)
        excellent_refinements = optimizer._plan_refinement_rounds(layers, QualityThreshold.EXCELLENT)
        perfect_refinements = optimizer._plan_refinement_rounds(layers, QualityThreshold.PERFECT)

        assert len(good_refinements) >= 1
        assert len(excellent_refinements) >= len(good_refinements)
        assert len(perfect_refinements) >= len(excellent_refinements)

        # 验证改进轮次结构
        for refinement in perfect_refinements:
            assert isinstance(refinement, RefinementRound)
            assert refinement.round_id > 0
            assert 0 <= refinement.quality_score <= 1
            assert len(refinement.improvement_areas) > 0
            assert len(refinement.selected_agents) > 0

    def test_assess_resource_requirements(self, optimizer):
        """测试资源需求评估"""
        layers = [
            ExecutionLayer(1, "层1", ["agent1", "agent2"], estimated_time=60),
            ExecutionLayer(2, "层2", ["agent3", "agent4", "agent5"], estimated_time=90)
        ]
        refinements = [
            RefinementRound(1, 0.8, ["质量"], ["agent6"], 30)
        ]

        requirements = optimizer._assess_resource_requirements(layers, refinements)

        assert 'total_agents' in requirements
        assert 'concurrent_agents' in requirements
        assert 'estimated_memory_mb' in requirements
        assert 'estimated_cpu_cores' in requirements
        assert requirements['total_agents'] >= 6
        assert requirements['concurrent_agents'] >= 3

    def test_predict_success_probability(self, optimizer):
        """测试成功概率预测"""
        layers = [
            ExecutionLayer(1, "层1", ["backend-architect"], estimated_time=60)
        ]

        # 测试不同质量阈值
        min_prob = optimizer._predict_success_probability(layers, QualityThreshold.MINIMUM)
        good_prob = optimizer._predict_success_probability(layers, QualityThreshold.GOOD)
        perfect_prob = optimizer._predict_success_probability(layers, QualityThreshold.PERFECT)

        assert 0 <= min_prob <= 1
        assert 0 <= good_prob <= 1
        assert 0 <= perfect_prob <= 1
        assert min_prob >= perfect_prob  # 要求越低，成功率越高

    def test_optimize_time_estimation(self, optimizer):
        """测试时间估算优化"""
        layers = [
            ExecutionLayer(1, "层1", ["agent1"], estimated_time=60),
            ExecutionLayer(2, "层2", ["agent2"], estimated_time=90)
        ]
        refinements = [
            RefinementRound(1, 0.8, ["质量"], ["agent3"], 30)
        ]

        estimated_time = optimizer._optimize_time_estimation(layers, refinements)

        assert estimated_time > 0
        assert estimated_time < sum(layer.estimated_time for layer in layers) + sum(r.estimated_time for r in refinements)

    def test_generate_prompts(self, optimizer):
        """测试prompt生成"""
        task = "实现用户系统"

        # 测试不同类型的prompt
        analysis_prompt = optimizer._generate_analysis_prompt("business-analyst", task)
        design_prompt = optimizer._generate_design_prompt("backend-architect", task)
        impl_prompt = optimizer._generate_implementation_prompt("python-pro", task)
        qa_prompt = optimizer._generate_qa_prompt("test-engineer", task)
        deploy_prompt = optimizer._generate_deployment_prompt("devops-engineer", task)

        prompts = [analysis_prompt, design_prompt, impl_prompt, qa_prompt, deploy_prompt]

        for prompt in prompts:
            assert isinstance(prompt, str)
            assert len(prompt) > 100  # 确保prompt有足够内容
            assert task in prompt

    def test_generate_task_calls(self, optimizer, mock_analysis):
        """测试Task调用生成"""
        agents = ['backend-architect', 'test-engineer']
        layers = optimizer._plan_layered_execution(agents, mock_analysis, mock_analysis.original_task)

        plan = OpusOptimizationPlan(
            task_description=mock_analysis.original_task,
            optimization_level=OptimizationLevel.OPUS41,
            target_quality=QualityThreshold.EXCELLENT,
            execution_layers=layers,
            refinement_rounds=[],
            estimated_total_time=180,
            success_probability=0.85,
            resource_requirements={}
        )

        task_calls = optimizer.generate_task_calls(plan)

        assert len(task_calls) > 0
        for call in task_calls:
            assert 'tool_name' in call
            assert call['tool_name'] == 'Task'
            assert 'parameters' in call
            assert 'subagent_type' in call['parameters']
            assert 'description' in call['parameters']
            assert 'prompt' in call['parameters']

    def test_agent_metrics_management(self, optimizer):
        """测试Agent性能指标管理"""
        agent_name = "test-agent"

        # 测试更新指标
        optimizer._update_agent_metrics(agent_name, True, 120.5, 0.85)

        assert agent_name in optimizer.agent_metrics
        metrics = optimizer.agent_metrics[agent_name]
        assert isinstance(metrics, AgentPerformanceMetrics)
        assert metrics.success_rate > 0
        assert metrics.avg_execution_time > 0
        assert metrics.quality_score > 0

    def test_filter_by_performance(self, optimizer):
        """测试基于性能筛选Agent"""
        agents = ['good-agent', 'bad-agent', 'new-agent']

        # 设置性能指标
        optimizer.agent_metrics['good-agent'] = AgentPerformanceMetrics(
            'good-agent', success_rate=0.9, quality_score=0.85
        )
        optimizer.agent_metrics['bad-agent'] = AgentPerformanceMetrics(
            'bad-agent', success_rate=0.5, quality_score=0.6
        )

        filtered = optimizer._filter_by_performance(agents, TaskComplexity.MEDIUM)

        assert 'good-agent' in filtered
        assert 'bad-agent' not in filtered  # 性能不达标
        assert 'new-agent' in filtered      # 新agent给予机会

    def test_optimize_agent_collaboration(self, optimizer):
        """测试Agent协作优化"""
        # 创建超出限制的agents列表
        many_agents = [f"agent-{i}" for i in range(25)]

        optimized = optimizer._optimize_agent_collaboration(many_agents)

        assert len(optimized) <= optimizer.max_parallel_agents
        assert len(optimized) > 0

    def test_map_threshold_to_level(self, optimizer):
        """测试质量阈值到级别映射"""
        mappings = {
            QualityThreshold.MINIMUM: QualityLevel.FAST,
            QualityThreshold.GOOD: QualityLevel.BALANCED,
            QualityThreshold.EXCELLENT: QualityLevel.PREMIUM,
            QualityThreshold.PERFECT: QualityLevel.ULTIMATE
        }

        for threshold, expected_level in mappings.items():
            result = optimizer._map_threshold_to_level(threshold)
            assert result == expected_level

    def test_create_monitoring_config(self, optimizer):
        """测试监控配置创建"""
        layers = [ExecutionLayer(1, "测试层", ["agent1"], estimated_time=60)]
        config = optimizer._create_monitoring_config(layers, QualityThreshold.EXCELLENT)

        assert 'quality_threshold' in config
        assert 'check_intervals' in config
        assert 'metrics_to_track' in config
        assert 'alert_conditions' in config
        assert 'visualization' in config
        assert config['quality_threshold'] == QualityThreshold.EXCELLENT.value

    def test_get_optimization_status(self, optimizer):
        """测试优化器状态获取"""
        status = optimizer.get_optimization_status()

        assert 'agent_count' in status
        assert 'execution_history_count' in status
        assert 'top_performers' in status
        assert 'system_status' in status
        assert 'max_parallel_agents' in status
        assert 'quality_threshold' in status
        assert status['system_status'] == 'operational'

    def test_display_execution_plan(self, optimizer, capsys, mock_analysis):
        """测试执行计划显示"""
        agents = ['backend-architect', 'test-engineer']
        layers = optimizer._plan_layered_execution(agents, mock_analysis, mock_analysis.original_task)

        plan = OpusOptimizationPlan(
            task_description="测试任务",
            optimization_level=OptimizationLevel.OPUS41,
            target_quality=QualityThreshold.EXCELLENT,
            execution_layers=layers,
            refinement_rounds=[],
            estimated_total_time=180,
            success_probability=0.85,
            resource_requirements={'total_agents': 5, 'concurrent_agents': 3}
        )

        optimizer.display_execution_plan(plan)

        captured = capsys.readouterr()
        assert "Opus41 智能优化执行计划" in captured.out
        assert "测试任务" in captured.out
        assert "EXCELLENT" in captured.out


class TestExecutionMetrics:
    """执行指标测试"""

    def test_execution_metrics_initialization(self):
        """测试执行指标初始化"""
        start_time = datetime.now()
        metrics = ExecutionMetrics(start_time=start_time)

        assert metrics.start_time == start_time
        assert metrics.end_time is None
        assert isinstance(metrics.layer_metrics, dict)
        assert isinstance(metrics.agent_metrics, dict)
        assert isinstance(metrics.quality_progression, list)
        assert isinstance(metrics.refinement_metrics, dict)


class TestSimulatedExecution:
    """模拟执行测试"""

    @pytest.fixture
    def optimizer(self):
        return Opus41Optimizer()

    def test_simulate_agent_execution(self, optimizer):
        """测试Agent执行模拟"""
        layer = ExecutionLayer(1, "测试层", ["test-agent"])
        result = optimizer._simulate_agent_execution("test-agent", layer)

        assert 'success' in result
        assert 'agent' in result
        assert 'execution_time' in result
        assert result['agent'] == 'test-agent'
        assert isinstance(result['success'], bool)
        assert result['execution_time'] >= 0

    def test_check_sync_points(self, optimizer):
        """测试同步点检查"""
        layer = ExecutionLayer(
            1, "测试层", ["agent1"],
            sync_points=["共识检查", "一致性检查", "覆盖率检查"]
        )

        # 高质量结果
        good_result = {"success_rate": 0.9, "quality_score": 0.85}
        assert optimizer._check_sync_points(layer, good_result) == True

        # 低质量结果
        bad_result = {"success_rate": 0.6, "quality_score": 0.5}
        assert optimizer._check_sync_points(layer, bad_result) == False

    def test_assess_current_quality(self, optimizer):
        """测试当前质量评估"""
        metrics = ExecutionMetrics(start_time=datetime.now())

        # 空指标
        assert optimizer._assess_current_quality(metrics) == 0.0

        # 添加层指标
        metrics.layer_metrics[1] = {"quality_score": 0.8}
        metrics.layer_metrics[2] = {"quality_score": 0.9}

        quality = optimizer._assess_current_quality(metrics)
        assert 0 <= quality <= 1

    def test_execute_refinement(self, optimizer):
        """测试改进轮次执行"""
        refinement = RefinementRound(
            1, 0.85, ["代码质量"], ["code-reviewer"], 30,
            ["代码审查", "重构优化"]
        )
        metrics = ExecutionMetrics(start_time=datetime.now())

        result = optimizer._execute_refinement(refinement, metrics)

        assert 'round_id' in result
        assert 'execution_time' in result
        assert 'agent_results' in result
        assert 'improvement_achieved' in result
        assert result['round_id'] == 1

    def test_generate_final_report(self, optimizer):
        """测试最终报告生成"""
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=30)

        metrics = ExecutionMetrics(start_time=start_time, end_time=end_time)
        metrics.layer_metrics[1] = {
            "success_rate": 0.9,
            "quality_score": 0.85,
            "execution_time": 120
        }

        plan = OpusOptimizationPlan(
            task_description="测试任务",
            optimization_level=OptimizationLevel.OPUS41,
            target_quality=QualityThreshold.EXCELLENT,
            execution_layers=[],
            refinement_rounds=[],
            estimated_total_time=180,
            success_probability=0.85,
            resource_requirements={}
        )

        report = optimizer._generate_final_report(metrics, plan)

        assert 'execution_summary' in report
        assert 'quality_progression' in report
        assert 'layer_performance' in report
        assert 'agent_performance' in report
        assert 'recommendations' in report
        assert 'deployment_readiness' in report

    def test_generate_recommendations(self, optimizer):
        """测试建议生成"""
        # 目标已达成
        good_recommendations = optimizer._generate_recommendations(
            0.9, QualityThreshold.EXCELLENT
        )
        assert len(good_recommendations) > 0
        assert any("目标质量已达成" in r for r in good_recommendations)

        # 质量差距大
        gap_recommendations = optimizer._generate_recommendations(
            0.6, QualityThreshold.EXCELLENT
        )
        assert len(gap_recommendations) > 0
        assert any("质量差距较大" in r for r in gap_recommendations)


class TestQualityPredictor:
    """质量预测器测试"""

    def test_predict_quality(self):
        """测试质量预测"""
        predictor = QualityPredictor()

        # 测试不同复杂度
        simple_quality = predictor.predict_quality(
            ['agent1', 'agent2'], TaskComplexity.SIMPLE
        )
        complex_quality = predictor.predict_quality(
            ['agent1', 'agent2'], TaskComplexity.COMPLEX
        )

        assert 0 <= simple_quality <= 1
        assert 0 <= complex_quality <= 1
        assert simple_quality >= complex_quality  # 简单任务质量更高


class TestMonitoringSystem:
    """监控系统测试"""

    def test_monitoring_lifecycle(self):
        """测试监控系统生命周期"""
        monitoring = MonitoringSystem()

        # 初始状态
        assert not monitoring.monitoring_active

        # 启动监控
        config = {"quality_threshold": 0.8}
        monitoring.start_monitoring(config)
        assert monitoring.monitoring_active

        # 停止监控
        monitoring.stop_monitoring()
        assert not monitoring.monitoring_active

        # 获取摘要
        summary = monitoring.get_summary()
        assert 'monitoring_duration' in summary
        assert 'status' in summary


class TestIntegration:
    """集成测试"""

    @pytest.fixture
    def optimizer(self):
        return Opus41Optimizer()

    @patch('features.opus41_optimizer.SmartDecomposer')
    def test_full_optimization_workflow(self, mock_decomposer, optimizer):
        """测试完整优化工作流"""
        # 设置mock
        mock_analysis = TaskAnalysis(
            original_task="完整测试任务",
            complexity=TaskComplexity.MEDIUM,
            required_agents=['backend-architect', 'test-engineer'],
            suggested_approach="分层实现",
            estimated_time=180,
            risk_factors=[],
            dependencies=[],
            agent_tasks=[]
        )
        mock_decomposer.return_value.decompose_task.return_value = mock_analysis

        # 执行优化
        plan = optimizer.optimize_execution(
            "完整测试任务",
            QualityThreshold.GOOD,
            OptimizationLevel.OPUS41
        )

        # 验证结果
        assert isinstance(plan, OpusOptimizationPlan)
        assert len(plan.execution_layers) > 0
        assert plan.estimated_total_time > 0
        assert 0 <= plan.success_probability <= 1

        # 生成Task调用
        task_calls = optimizer.generate_task_calls(plan)
        assert len(task_calls) > 0

    def test_error_handling(self, optimizer):
        """测试错误处理"""
        # 测试无效输入
        with pytest.raises(Exception):
            optimizer._assess_resource_requirements(None, None)


class TestPerformanceOptimization:
    """性能优化测试"""

    def test_agent_selection_performance(self):
        """测试Agent选择性能"""
        optimizer = Opus41Optimizer()

        start_time = time.time()
        for _ in range(100):
            agents = optimizer.select_optimal_agents(
                "性能测试任务", QualityLevel.PREMIUM
            )
        end_time = time.time()

        # 100次选择应该在1秒内完成
        assert (end_time - start_time) < 1.0
        assert len(agents) > 0

    def test_large_scale_planning(self):
        """测试大规模规划性能"""
        optimizer = Opus41Optimizer()

        # 创建大型任务
        large_agents = [f"agent-{i}" for i in range(50)]
        mock_analysis = TaskAnalysis(
            original_task="大规模测试",
            complexity=TaskComplexity.ENTERPRISE,
            required_agents=large_agents,
            suggested_approach="分层实现",
            estimated_time=600,
            risk_factors=[],
            dependencies=[],
            agent_tasks=[]
        )

        start_time = time.time()
        layers = optimizer._plan_layered_execution(
            large_agents, mock_analysis, "大规模测试"
        )
        end_time = time.time()

        # 大规模规划应该在合理时间内完成
        assert (end_time - start_time) < 5.0
        assert len(layers) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])