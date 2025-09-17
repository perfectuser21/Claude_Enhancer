#!/usr/bin/env python3
"""
ParallelExecutor 单元测试
测试并行执行控制器的核心功能
"""

import os
import sys
import pytest
import json
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from features.parallel_executor import ParallelExecutor, get_parallel_executor
from features.smart_decomposer import TaskAnalysis, AgentTask, TaskComplexity
from features.parallel_manager import ExecutionResult, ParallelExecutionSummary

class TestParallelExecutor:
    """ParallelExecutor 测试类"""

    @pytest.fixture
    def executor(self):
        """创建并行执行器实例"""
        return ParallelExecutor()

    @pytest.fixture
    def sample_task_analysis(self):
        """创建示例任务分析"""
        agent_tasks = [
            AgentTask(
                agent_name="project-manager",
                task_description="项目规划和管理",
                detailed_prompt="详细分析项目需求和时间线",
                estimated_time=30,
                priority=1,
                dependencies=[]
            ),
            AgentTask(
                agent_name="backend-architect",
                task_description="后端架构设计",
                detailed_prompt="设计可扩展的后端架构",
                estimated_time=45,
                priority=2,
                dependencies=["project-manager"]
            ),
            AgentTask(
                agent_name="test-engineer",
                task_description="测试策略制定",
                detailed_prompt="制定全面的测试策略",
                estimated_time=25,
                priority=3,
                dependencies=[]
            )
        ]

        return TaskAnalysis(
            original_task="开发用户管理系统",
            project_type="web_application",
            complexity=TaskComplexity.MEDIUM,
            execution_mode="parallel",
            estimated_total_time=60,
            agent_tasks=agent_tasks
        )

    def test_executor_initialization(self, executor):
        """测试执行器初始化"""
        assert executor is not None
        assert hasattr(executor, 'parallel_manager')
        assert hasattr(executor, 'execution_log')
        assert len(executor.execution_log) == 0

    def test_execute_parallel_task(self, executor, sample_task_analysis):
        """测试并行任务执行准备"""
        task_description = "开发用户管理系统"

        result = executor.execute_parallel_task(task_description, sample_task_analysis)

        # 验证返回结构
        assert result['ready_for_execution'] is True
        assert result['execution_mode'] == "parallel"
        assert result['expected_agents'] == 3
        assert 'task_calls' in result
        assert 'execution_instructions' in result
        assert 'monitoring_config' in result

        # 验证执行日志
        assert len(executor.execution_log) == 1
        log_entry = executor.execution_log[0]
        assert log_entry['task_description'] == task_description
        assert log_entry['status'] == 'prepared'

    def test_task_calls_generation(self, executor, sample_task_analysis):
        """测试Task调用生成"""
        task_calls = executor._generate_task_calls(sample_task_analysis)

        assert len(task_calls) == 3

        for task_call in task_calls:
            assert task_call['tool_name'] == "Task"
            assert 'parameters' in task_call
            assert 'subagent_type' in task_call['parameters']
            assert 'description' in task_call['parameters']
            assert 'prompt' in task_call['parameters']
            assert 'expected_duration' in task_call
            assert 'priority' in task_call

        # 验证特定agent
        pm_call = next(call for call in task_calls if call['parameters']['subagent_type'] == 'project-manager')
        assert pm_call['priority'] == 1
        assert pm_call['expected_duration'] == 30

    def test_execution_instructions_generation(self, executor, sample_task_analysis):
        """测试执行指令生成"""
        instructions = executor._create_execution_instructions(sample_task_analysis)

        # 验证关键内容
        assert "Perfect21 并行执行指令" in instructions
        assert "开发用户管理系统" in instructions
        assert "3" in instructions  # agent数量
        assert "Task(" in instructions
        assert "project-manager" in instructions
        assert "backend-architect" in instructions
        assert "test-engineer" in instructions

    def test_monitoring_config_creation(self, executor, sample_task_analysis):
        """测试监控配置创建"""
        config = executor._create_monitoring_config(sample_task_analysis)

        assert config['total_agents'] == 3
        assert config['expected_completion_time'] == 60
        assert len(config['agent_names']) == 3
        assert 'project-manager' in config['agent_names']
        assert len(config['critical_agents']) >= 1  # 至少有一个高优先级agent
        assert config['monitoring_intervals'] == 30
        assert config['timeout_threshold'] > 0

    def test_execution_results_processing(self, executor):
        """测试执行结果处理"""
        # 模拟agent执行结果
        agent_results = [
            {
                'agent_name': 'project-manager',
                'task_description': '项目规划',
                'success': True,
                'output': '项目计划已完成',
                'execution_time': 28.5,
                'start_time': datetime.now().isoformat(),
                'end_time': datetime.now().isoformat()
            },
            {
                'agent_name': 'backend-architect',
                'task_description': '架构设计',
                'success': True,
                'output': '后端架构已设计',
                'execution_time': 42.3,
                'start_time': datetime.now().isoformat(),
                'end_time': datetime.now().isoformat()
            },
            {
                'agent_name': 'test-engineer',
                'task_description': '测试策略',
                'success': False,
                'error': '缺少依赖信息',
                'execution_time': 15.2,
                'start_time': datetime.now().isoformat(),
                'end_time': datetime.now().isoformat()
            }
        ]

        # 先设置一个执行记录
        executor.execution_log.append({
            'task_description': '测试任务',
            'status': 'prepared'
        })

        summary = executor.process_execution_results(agent_results)

        # 验证摘要结构
        assert isinstance(summary, ParallelExecutionSummary)
        assert summary.total_agents == 3
        assert summary.successful_agents == 2
        assert summary.failed_agents == 1
        assert summary.total_execution_time > 0

        # 验证集成输出
        assert 'execution_summary' in summary.integrated_output
        assert 'agent_contributions' in summary.integrated_output
        assert 'project_assets' in summary.integrated_output
        assert 'quality_metrics' in summary.integrated_output

    def test_agent_output_summarization(self, executor):
        """测试Agent输出摘要"""
        result = ExecutionResult(
            agent_name="backend-architect",
            task_description="架构设计",
            success=True,
            result="完整的架构设计文档，包含API设计、数据库模式、服务架构等详细内容...",
            error_message=None,
            execution_time=45.0,
            start_time=datetime.now(),
            end_time=datetime.now()
        )

        summary = executor._summarize_agent_output(result)

        # 长输出应该被截断
        assert len(summary) <= 203  # 200 + "..."
        assert isinstance(summary, str)

        # 测试短输出
        result.result = "简短输出"
        summary = executor._summarize_agent_output(result)
        assert summary == "简短输出"

    def test_asset_extraction(self, executor):
        """测试资产提取"""
        results = [
            ExecutionResult(
                agent_name="backend-architect",
                task_description="后端开发",
                success=True,
                result="代码完成",
                error_message=None,
                execution_time=30.0,
                start_time=datetime.now(),
                end_time=datetime.now()
            ),
            ExecutionResult(
                agent_name="frontend-specialist",
                task_description="前端开发",
                success=True,
                result="界面完成",
                error_message=None,
                execution_time=25.0,
                start_time=datetime.now(),
                end_time=datetime.now()
            ),
            ExecutionResult(
                agent_name="test-engineer",
                task_description="测试",
                success=True,
                result="测试套件",
                error_message=None,
                execution_time=20.0,
                start_time=datetime.now(),
                end_time=datetime.now()
            )
        ]

        assets = executor._compile_project_assets(results)

        # 验证包含各种类型的资产
        assert len(assets) > 0
        backend_assets = ['API服务代码', '数据库架构', '接口文档']
        frontend_assets = ['用户界面', '组件库', '样式文件']
        test_assets = ['测试套件', '测试报告', '质量评估']

        # 至少应该包含一些期望的资产
        has_backend = any(asset in assets for asset in backend_assets)
        has_frontend = any(asset in assets for asset in frontend_assets)
        has_test = any(asset in assets for asset in test_assets)

        assert has_backend or has_frontend or has_test

    def test_quality_score_calculation(self, executor):
        """测试质量分数计算"""
        # 成功的结果
        success_result = ExecutionResult(
            agent_name="test-agent",
            task_description="测试任务",
            success=True,
            result="成功完成",
            error_message=None,
            execution_time=100.0,
            start_time=datetime.now(),
            end_time=datetime.now()
        )

        score = executor._calculate_quality_score(success_result)
        assert 0.8 <= score <= 1.0

        # 失败的结果
        fail_result = ExecutionResult(
            agent_name="test-agent",
            task_description="测试任务",
            success=False,
            result=None,
            error_message="执行失败",
            execution_time=50.0,
            start_time=datetime.now(),
            end_time=datetime.now()
        )

        score = executor._calculate_quality_score(fail_result)
        assert score == 0.0

    def test_overall_quality_calculation(self, executor):
        """测试整体质量计算"""
        results = [
            ExecutionResult(
                agent_name="agent1",
                task_description="任务1",
                success=True,
                result="完成",
                error_message=None,
                execution_time=30.0,
                start_time=datetime.now(),
                end_time=datetime.now()
            ),
            ExecutionResult(
                agent_name="agent2",
                task_description="任务2",
                success=True,
                result="完成",
                error_message=None,
                execution_time=40.0,
                start_time=datetime.now(),
                end_time=datetime.now()
            ),
            ExecutionResult(
                agent_name="agent3",
                task_description="任务3",
                success=False,
                result=None,
                error_message="失败",
                execution_time=20.0,
                start_time=datetime.now(),
                end_time=datetime.now()
            )
        ]

        quality_metrics = executor._calculate_overall_quality(results)

        assert 'overall_score' in quality_metrics
        assert 'quality_level' in quality_metrics
        assert 'success_rate' in quality_metrics
        assert quality_metrics['success_rate'] == 2/3  # 2 out of 3 succeeded
        assert quality_metrics['agent_count'] == 3
        assert quality_metrics['successful_agents'] == 2

    def test_deployment_readiness_assessment(self, executor):
        """测试部署就绪状态评估"""
        results = [
            ExecutionResult(
                agent_name="backend-architect",
                task_description="后端开发",
                success=True,
                result="完成",
                error_message=None,
                execution_time=30.0,
                start_time=datetime.now(),
                end_time=datetime.now()
            ),
            ExecutionResult(
                agent_name="frontend-specialist",
                task_description="前端开发",
                success=True,
                result="完成",
                error_message=None,
                execution_time=25.0,
                start_time=datetime.now(),
                end_time=datetime.now()
            ),
            ExecutionResult(
                agent_name="test-engineer",
                task_description="测试",
                success=True,
                result="完成",
                error_message=None,
                execution_time=20.0,
                start_time=datetime.now(),
                end_time=datetime.now()
            )
        ]

        readiness = executor._assess_deployment_readiness(results)

        assert 'readiness_score' in readiness
        assert 'available_components' in readiness
        assert 'missing_components' in readiness
        assert 'deployment_ready' in readiness

        # 应该检测到backend, frontend, test组件
        assert 'backend' in readiness['available_components']
        assert 'frontend' in readiness['available_components']
        assert 'test' in readiness['available_components']

    def test_next_actions_generation(self, executor):
        """测试下一步行动建议生成"""
        results = [
            ExecutionResult(
                agent_name="backend-architect",
                task_description="后端开发",
                success=True,
                result="完成",
                error_message=None,
                execution_time=30.0,
                start_time=datetime.now(),
                end_time=datetime.now()
            ),
            ExecutionResult(
                agent_name="test-engineer",
                task_description="测试",
                success=False,
                result=None,
                error_message="失败",
                execution_time=20.0,
                start_time=datetime.now(),
                end_time=datetime.now()
            )
        ]

        actions = executor._generate_next_actions(results)

        assert len(actions) > 0
        assert any("修复失败的agents" in action for action in actions)
        assert any("test-engineer" in action for action in actions)

    def test_execution_status_tracking(self, executor):
        """测试执行状态跟踪"""
        # 初始状态
        status = executor.get_execution_status()
        assert status['status'] == 'idle'

        # 添加执行记录
        executor.execution_log.append({
            'task_description': '测试任务',
            'timestamp': datetime.now().isoformat(),
            'analysis': {
                'agent_count': 3,
                'execution_mode': 'parallel'
            },
            'status': 'running'
        })

        status = executor.get_execution_status()
        assert status['status'] == 'running'
        assert status['task_description'] == '测试任务'
        assert status['agent_count'] == 3

    def test_save_execution_report(self, executor, tmp_path):
        """测试保存执行报告"""
        # 创建测试摘要
        results = [
            ExecutionResult(
                agent_name="test-agent",
                task_description="测试任务",
                success=True,
                result="完成",
                error_message=None,
                execution_time=30.0,
                start_time=datetime.now(),
                end_time=datetime.now()
            )
        ]

        summary = ParallelExecutionSummary(
            task_description="测试任务",
            total_agents=1,
            successful_agents=1,
            failed_agents=0,
            total_execution_time=30.0,
            results=results
        )

        # 保存到临时文件
        report_file = str(tmp_path / "test_report.json")
        saved_file = executor.save_execution_report(summary, report_file)

        assert saved_file == report_file
        assert Path(report_file).exists()

        # 验证文件内容
        with open(report_file, 'r', encoding='utf-8') as f:
            report_data = json.load(f)

        assert 'execution_summary' in report_data
        assert 'agent_results' in report_data
        assert report_data['execution_summary']['total_agents'] == 1

    def test_get_parallel_executor_singleton(self):
        """测试单例模式"""
        executor1 = get_parallel_executor()
        executor2 = get_parallel_executor()

        assert executor1 is executor2
        assert isinstance(executor1, ParallelExecutor)

    @pytest.mark.asyncio
    async def test_async_compatibility(self, executor):
        """测试异步兼容性"""
        # 虽然当前实现主要是同步的，但测试异步调用兼容性

        async def async_task():
            return executor.get_execution_status()

        result = await async_task()
        assert 'status' in result

    def test_error_handling(self, executor):
        """测试错误处理"""
        # 测试处理None结果
        summary = executor.process_execution_results([])
        assert summary.total_agents == 0
        assert summary.successful_agents == 0

        # 测试处理格式错误的结果
        invalid_results = [
            {'invalid': 'data'}
        ]

        try:
            summary = executor.process_execution_results(invalid_results)
            # 应该能处理无效数据
            assert summary.total_agents >= 0
        except Exception as e:
            pytest.fail(f"不应该抛出异常: {e}")

    def test_large_scale_execution(self, executor):
        """测试大规模执行"""
        # 创建大量agent任务
        agent_tasks = []
        for i in range(20):  # 20个agents
            agent_tasks.append(
                AgentTask(
                    agent_name=f"agent-{i}",
                    task_description=f"任务{i}",
                    detailed_prompt=f"执行任务{i}的详细说明",
                    estimated_time=30,
                    priority=i % 3 + 1,
                    dependencies=[]
                )
            )

        large_analysis = TaskAnalysis(
            original_task="大规模系统开发",
            project_type="enterprise_system",
            complexity=TaskComplexity.HIGH,
            execution_mode="parallel",
            estimated_total_time=120,
            agent_tasks=agent_tasks
        )

        result = executor.execute_parallel_task("大规模系统开发", large_analysis)

        assert result['ready_for_execution'] is True
        assert result['expected_agents'] == 20
        assert len(result['task_calls']) == 20

    def test_performance_metrics(self, executor, sample_task_analysis):
        """测试性能指标"""
        import time

        # 测试执行准备性能
        start_time = time.time()
        result = executor.execute_parallel_task("性能测试", sample_task_analysis)
        preparation_time = time.time() - start_time

        assert preparation_time < 1.0  # 应该在1秒内完成
        assert result['ready_for_execution'] is True

        # 测试结果处理性能
        agent_results = [
            {
                'agent_name': f'agent-{i}',
                'task_description': f'任务{i}',
                'success': True,
                'output': f'输出{i}',
                'execution_time': 30.0,
                'start_time': datetime.now().isoformat(),
                'end_time': datetime.now().isoformat()
            }
            for i in range(10)
        ]

        executor.execution_log.append({
            'task_description': '性能测试',
            'status': 'prepared'
        })

        start_time = time.time()
        summary = executor.process_execution_results(agent_results)
        processing_time = time.time() - start_time

        assert processing_time < 2.0  # 应该在2秒内完成
        assert summary.total_agents == 10

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])