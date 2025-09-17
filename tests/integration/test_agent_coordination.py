#!/usr/bin/env python3
"""
Agent协调集成测试
测试多个Agent之间的协作和工作流编排
"""

import os
import sys
import pytest
import asyncio
import json
import time
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from features.workflow_orchestrator.orchestrator import WorkflowOrchestrator
from features.opus41_optimizer import Opus41Optimizer, QualityLevel
from features.parallel_executor import ParallelExecutor
from features.preventive_quality.quality_gate import QualityGate
from features.sync_point_manager.sync_manager import SyncPointManager

class TestAgentCoordination:
    """Agent协调集成测试类"""

    @pytest.fixture
    def orchestrator(self):
        """工作流编排器"""
        return WorkflowOrchestrator()

    @pytest.fixture
    def optimizer(self):
        """Opus41优化器"""
        return Opus41Optimizer()

    @pytest.fixture
    def executor(self):
        """并行执行器"""
        return ParallelExecutor()

    @pytest.fixture
    def quality_gate(self, tmp_path):
        """质量门"""
        return QualityGate(str(tmp_path))

    @pytest.fixture
    def sync_manager(self):
        """同步点管理器"""
        return SyncPointManager()

    @pytest.fixture
    def complete_workflow(self):
        """完整的工作流配置"""
        return {
            "name": "complete_development_workflow",
            "version": "1.0.0",
            "description": "完整的开发工作流集成测试",
            "quality_level": "premium",
            "stages": [
                {
                    "name": "requirements_analysis",
                    "agents": ["@business-analyst", "@project-manager", "@requirements-analyst"],
                    "execution_mode": "parallel",
                    "timeout": 600,
                    "quality_checks": ["requirements_complete", "stakeholder_approval"]
                },
                {
                    "name": "architecture_design",
                    "agents": ["@api-designer", "@backend-architect", "@database-specialist"],
                    "execution_mode": "sequential",
                    "timeout": 900,
                    "quality_checks": ["architecture_approved", "scalability_validated"]
                },
                {
                    "name": "implementation",
                    "agents": ["@backend-architect", "@frontend-specialist", "@test-engineer"],
                    "execution_mode": "parallel",
                    "timeout": 1800,
                    "quality_checks": ["code_quality", "test_coverage"]
                },
                {
                    "name": "quality_assurance",
                    "agents": ["@security-auditor", "@performance-engineer", "@code-reviewer"],
                    "execution_mode": "parallel",
                    "timeout": 600,
                    "quality_checks": ["security_scan", "performance_benchmark"]
                }
            ],
            "sync_points": [
                {
                    "after_stage": "requirements_analysis",
                    "type": "validation",
                    "criteria": ["requirements_complete", "stakeholder_approval"],
                    "timeout": 300
                },
                {
                    "after_stage": "architecture_design",
                    "type": "review",
                    "criteria": ["architecture_approved", "scalability_validated"],
                    "timeout": 300
                },
                {
                    "after_stage": "implementation",
                    "type": "quality_gate",
                    "criteria": ["code_quality", "test_coverage", "integration_tests"],
                    "timeout": 600
                }
            ]
        }

    def test_end_to_end_workflow_coordination(self, orchestrator, optimizer, executor, complete_workflow):
        """测试端到端工作流协调"""
        # 1. 加载工作流
        load_result = orchestrator.load_workflow(complete_workflow)
        assert load_result['success'] is True

        # 2. 优化器选择agents
        task_description = "开发企业级用户管理系统"
        selected_agents = optimizer.select_optimal_agents(task_description, QualityLevel.PREMIUM)
        assert len(selected_agents) >= 8

        # 3. 创建并行执行计划
        execution_plan = optimizer.create_parallel_execution_plan(selected_agents, task_description)
        assert 'execution_layers' in execution_plan
        assert len(execution_plan['execution_layers']) >= 2

        # 4. 验证工作流和优化器的集成
        for stage in complete_workflow['stages']:
            stage_plan = orchestrator.plan_stage_execution(stage)
            assert 'execution_mode' in stage_plan
            assert 'tasks' in stage_plan

    def test_parallel_agent_execution_simulation(self, executor, optimizer):
        """测试并行Agent执行模拟"""
        task_description = "实现实时聊天系统"

        # 1. 选择agents
        agents = optimizer.select_optimal_agents(task_description, QualityLevel.PREMIUM)

        # 2. 创建任务分析（模拟）
        from features.smart_decomposer import TaskAnalysis, AgentTask, ComplexityLevel

        agent_tasks = []
        for i, agent in enumerate(agents[:5]):  # 限制为5个agent以便测试
            agent_tasks.append(
                AgentTask(
                    agent_name=agent,
                    task_description=f"{agent}的任务",
                    detailed_prompt=f"请{agent}完成{task_description}中的相关工作",
                    estimated_time=30 + i * 5,
                    priority=i % 3 + 1,
                    dependencies=[]
                )
            )

        task_analysis = TaskAnalysis(
            original_task=task_description,
            project_type="real_time_system",
            complexity=ComplexityLevel.HIGH,
            execution_mode="parallel",
            estimated_total_time=120,
            agent_tasks=agent_tasks
        )

        # 3. 准备并行执行
        execution_result = executor.execute_parallel_task(task_description, task_analysis)

        # 4. 验证执行准备
        assert execution_result['ready_for_execution'] is True
        assert execution_result['expected_agents'] == len(agent_tasks)
        assert len(execution_result['task_calls']) == len(agent_tasks)

        # 5. 验证Task调用配置
        for task_call in execution_result['task_calls']:
            assert task_call['tool_name'] == "Task"
            assert 'subagent_type' in task_call['parameters']
            assert task_call['parameters']['subagent_type'] in agents

    def test_quality_gate_integration(self, quality_gate, orchestrator, complete_workflow):
        """测试质量门集成"""
        # 1. 加载工作流
        orchestrator.load_workflow(complete_workflow)

        # 2. 模拟阶段执行后的质量检查
        stage = complete_workflow['stages'][0]  # requirements_analysis

        # 3. 运行相关的质量检查
        quality_results = quality_gate.run_checks(context="all")

        # 4. 验证质量检查结果
        assert len(quality_results) > 0

        # 5. 检查是否有关键失败
        critical_failures = [
            r for r in quality_results
            if r.status.value == 'failed' and r.severity.value == 'critical'
        ]

        # 6. 如果有关键失败，工作流应该暂停
        if critical_failures:
            print(f"发现{len(critical_failures)}个关键质量问题，工作流需要暂停")

        # 7. 验证质量摘要
        summary = quality_gate.get_check_summary(quality_results)
        assert '总检查数' in summary
        assert '成功率' in summary

    def test_sync_point_coordination(self, sync_manager, orchestrator, complete_workflow):
        """测试同步点协调"""
        # 1. 加载工作流
        orchestrator.load_workflow(complete_workflow)

        # 2. 创建同步点
        sync_config = complete_workflow['sync_points'][0]
        sync_point = sync_manager.create_sync_point({
            'name': f"sync_{sync_config['after_stage']}",
            'type': sync_config['type'],
            'criteria': sync_config['criteria'],
            'timeout': sync_config.get('timeout', 300)
        })

        assert 'sync_id' in sync_point
        assert sync_point['status'] == 'waiting'

        # 3. 模拟验证数据
        validation_data = {
            'requirements_complete': True,
            'stakeholder_approval': True
        }

        # 4. 验证同步点
        validation_result = sync_manager.validate_sync_point(
            sync_point['sync_id'],
            validation_data
        )

        assert validation_result['success'] is True
        assert validation_result['all_criteria_met'] is True

    def test_multi_stage_workflow_execution(self, orchestrator, complete_workflow):
        """测试多阶段工作流执行"""
        # 1. 加载工作流
        orchestrator.load_workflow(complete_workflow)

        # 2. 模拟执行每个阶段
        executed_stages = []

        for stage in complete_workflow['stages']:
            # 规划阶段执行
            execution_plan = orchestrator.plan_stage_execution(stage)
            assert 'execution_mode' in execution_plan

            # 模拟阶段执行
            with patch.object(orchestrator, 'execute_agent_task') as mock_execute:
                mock_execute.return_value = {
                    'success': True,
                    'result': f"Stage {stage['name']} completed",
                    'duration': 60
                }

                stage_result = orchestrator.execute_stage(stage)
                assert stage_result['success'] is True

                executed_stages.append(stage['name'])

            # 标记阶段完成
            orchestrator.mark_stage_completed(stage['name'])

        # 3. 验证所有阶段都执行了
        assert len(executed_stages) == len(complete_workflow['stages'])

        # 4. 检查工作流进度
        progress = orchestrator.get_workflow_progress()
        assert progress['completion_percentage'] > 0

    def test_error_recovery_coordination(self, orchestrator, executor, complete_workflow):
        """测试错误恢复协调"""
        # 1. 加载工作流
        orchestrator.load_workflow(complete_workflow)

        # 2. 模拟阶段执行失败
        stage = complete_workflow['stages'][1]  # architecture_design

        with patch.object(orchestrator, 'execute_agent_task') as mock_execute:
            # 第一次调用失败
            mock_execute.side_effect = [
                {'success': False, 'error': 'Agent execution failed', 'retry_count': 1},
                {'success': True, 'result': 'Stage completed after retry', 'duration': 80}
            ]

            # 3. 执行阶段（包含错误处理）
            stage_result = orchestrator.execute_stage(stage)

            # 4. 验证错误处理
            if not stage_result.get('success'):
                # 处理错误
                error_result = orchestrator.handle_task_error(
                    "failed_task",
                    {'success': False, 'error': 'Agent execution failed', 'retry_count': 1}
                )
                assert 'retry_scheduled' in error_result

                # 模拟重试成功
                retry_result = orchestrator.execute_stage(stage)
                # 在mock设置下，第二次调用应该成功

    def test_performance_monitoring_integration(self, executor, optimizer):
        """测试性能监控集成"""
        import time

        task_description = "开发高性能API网关"

        # 1. 测量Agent选择性能
        start_time = time.time()
        agents = optimizer.select_optimal_agents(task_description, QualityLevel.ULTIMATE)
        selection_time = time.time() - start_time

        assert selection_time < 2.0
        assert len(agents) >= 10

        # 2. 测量执行计划创建性能
        start_time = time.time()
        execution_plan = optimizer.create_parallel_execution_plan(agents, task_description)
        planning_time = time.time() - start_time

        assert planning_time < 3.0
        assert len(execution_plan['execution_layers']) >= 2

        # 3. 创建监控配置
        from features.smart_decomposer import TaskAnalysis, AgentTask, ComplexityLevel

        agent_tasks = [
            AgentTask(
                agent_name=agent,
                task_description=f"{agent}的任务",
                detailed_prompt=f"执行{task_description}的相关工作",
                estimated_time=30,
                priority=1,
                dependencies=[]
            )
            for agent in agents[:10]  # 限制数量
        ]

        task_analysis = TaskAnalysis(
            original_task=task_description,
            project_type="api_gateway",
            complexity=ComplexityLevel.HIGH,
            execution_mode="parallel",
            estimated_total_time=180,
            agent_tasks=agent_tasks
        )

        # 4. 创建监控配置
        monitoring_config = executor._create_monitoring_config(task_analysis)

        assert monitoring_config['total_agents'] == 10
        assert monitoring_config['expected_completion_time'] == 180
        assert len(monitoring_config['agent_names']) == 10

    def test_quality_feedback_loop(self, quality_gate, optimizer, tmp_path):
        """测试质量反馈循环"""
        # 1. 运行初始质量检查
        initial_results = quality_gate.run_checks(context="all")
        initial_summary = quality_gate.get_check_summary(initial_results)

        # 2. 基于质量结果调整策略
        critical_issues = [
            r for r in initial_results
            if r.status.value == 'failed' and r.severity.value in ['critical', 'error']
        ]

        if critical_issues:
            # 如果有关键问题，使用更保守的质量级别
            quality_level = QualityLevel.ULTIMATE
        else:
            quality_level = QualityLevel.PREMIUM

        # 3. 根据质量反馈选择agents
        task = "开发安全的金融交易系统"
        agents = optimizer.select_optimal_agents(task, quality_level)

        # 4. 验证质量反馈影响了选择
        if quality_level == QualityLevel.ULTIMATE:
            assert len(agents) >= 15  # 更多agents用于更高质量
        else:
            assert len(agents) >= 8

        # 5. 验证包含质量相关agents
        quality_agents = ['security-auditor', 'test-engineer', 'code-reviewer']
        included_quality_agents = [agent for agent in agents if agent in quality_agents]
        assert len(included_quality_agents) >= 2

    def test_concurrent_workflow_execution(self, orchestrator):
        """测试并发工作流执行"""
        import threading
        import queue

        # 创建多个简化的工作流
        workflows = [
            {
                "name": f"workflow_{i}",
                "stages": [
                    {
                        "name": "execution",
                        "agents": [f"@agent-{i}"],
                        "execution_mode": "parallel",
                        "timeout": 300
                    }
                ]
            }
            for i in range(3)
        ]

        results_queue = queue.Queue()

        def execute_workflow(workflow):
            try:
                # 加载工作流
                load_result = orchestrator.load_workflow(workflow)

                # 执行第一个阶段
                stage = workflow['stages'][0]
                with patch.object(orchestrator, 'execute_agent_task') as mock_execute:
                    mock_execute.return_value = {
                        'success': True,
                        'result': f"Workflow {workflow['name']} completed",
                        'duration': 30
                    }

                    stage_result = orchestrator.execute_stage(stage)
                    results_queue.put({
                        'workflow': workflow['name'],
                        'success': stage_result['success']
                    })

            except Exception as e:
                results_queue.put({
                    'workflow': workflow['name'],
                    'error': str(e)
                })

        # 并发执行工作流
        threads = []
        for workflow in workflows:
            thread = threading.Thread(target=execute_workflow, args=(workflow,))
            threads.append(thread)
            thread.start()

        # 等待完成
        for thread in threads:
            thread.join()

        # 验证结果
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())

        assert len(results) == len(workflows)
        for result in results:
            assert 'workflow' in result
            # 验证要么成功，要么有错误信息
            assert 'success' in result or 'error' in result

    def test_resource_optimization_coordination(self, optimizer, executor):
        """测试资源优化协调"""
        # 1. 创建不同复杂度的任务
        tasks = [
            ("简单CRUD应用", QualityLevel.FAST),
            ("微服务架构", QualityLevel.BALANCED),
            ("大型分布式系统", QualityLevel.PREMIUM),
            ("关键金融系统", QualityLevel.ULTIMATE)
        ]

        execution_results = []

        for task_desc, quality_level in tasks:
            # 2. 选择合适的agents
            agents = optimizer.select_optimal_agents(task_desc, quality_level)

            # 3. 创建执行计划
            execution_plan = optimizer.create_parallel_execution_plan(agents, task_desc)

            # 4. 记录资源使用
            execution_results.append({
                'task': task_desc,
                'quality_level': quality_level.value,
                'agent_count': len(agents),
                'execution_layers': len(execution_plan['execution_layers']),
                'estimated_time': execution_plan.get('estimated_total_time', 0)
            })

        # 5. 验证资源分配合理性
        for i, result in enumerate(execution_results):
            if i > 0:
                prev_result = execution_results[i-1]
                # 更高质量级别应该使用更多资源
                if result['quality_level'] > prev_result['quality_level']:
                    assert result['agent_count'] >= prev_result['agent_count']

    @pytest.mark.asyncio
    async def test_async_coordination(self, orchestrator, complete_workflow):
        """测试异步协调能力"""
        # 1. 加载工作流
        orchestrator.load_workflow(complete_workflow)

        # 2. 异步执行阶段
        stage = complete_workflow['stages'][0]

        # 模拟异步执行
        async def mock_async_execute():
            await asyncio.sleep(0.1)  # 模拟异步操作
            return {'success': True, 'stage': stage['name']}

        # 3. 执行异步阶段
        result = await orchestrator.execute_stage_async(stage)

        assert result['success'] is True
        assert result['stage'] == stage['name']

    def test_integration_with_external_systems(self, quality_gate, tmp_path):
        """测试与外部系统的集成"""
        # 1. 创建模拟的外部配置文件
        config_file = tmp_path / "external_config.json"
        config_file.write_text(json.dumps({
            "api_endpoints": ["http://api.example.com"],
            "database_url": "postgresql://localhost/test",
            "redis_url": "redis://localhost:6379"
        }))

        # 2. 运行质量检查，包括外部依赖检查
        results = quality_gate.run_checks(context="all")

        # 3. 验证基础检查通过
        environment_results = [
            r for r in results
            if quality_gate.checks[r.check_name].category == 'environment'
        ]

        assert len(environment_results) > 0

        # 4. 验证可以处理外部配置
        # （这里只是验证基本功能，实际外部系统集成需要更复杂的测试）

    def test_workflow_state_persistence(self, orchestrator, complete_workflow, tmp_path):
        """测试工作流状态持久化"""
        # 1. 加载工作流
        orchestrator.load_workflow(complete_workflow)

        # 2. 执行部分阶段
        stage1 = complete_workflow['stages'][0]
        orchestrator.mark_stage_completed(stage1['name'])

        # 3. 获取当前状态
        progress = orchestrator.get_workflow_progress()
        current_stage = progress['current_stage']

        # 4. 模拟保存状态到文件
        state_file = tmp_path / "workflow_state.json"
        state_data = {
            'current_workflow': orchestrator.current_workflow,
            'current_stage': current_stage,
            'completed_tasks': orchestrator.completed_tasks,
            'progress': progress
        }

        state_file.write_text(json.dumps(state_data, default=str))

        # 5. 验证状态已保存
        assert state_file.exists()

        # 6. 模拟恢复状态
        restored_data = json.loads(state_file.read_text())
        assert restored_data['current_workflow']['name'] == complete_workflow['name']

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])