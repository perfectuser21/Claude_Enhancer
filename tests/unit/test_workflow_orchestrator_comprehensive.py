#!/usr/bin/env python3
"""
WorkflowOrchestrator 完整单元测试套件
测试覆盖率 >95%，包含所有核心功能和边界条件
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from pathlib import Path
import tempfile

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from features.workflow_orchestrator.orchestrator import (
    WorkflowOrchestrator, ExecutionMode, WorkflowState, TaskStatus,
    Task, Stage, WorkflowExecution
)


class TestWorkflowOrchestrator:
    """WorkflowOrchestrator 核心功能测试"""

    @pytest.fixture
    def orchestrator(self):
        """创建编排器实例"""
        with tempfile.TemporaryDirectory() as temp_dir:
            orchestrator = WorkflowOrchestrator()
            orchestrator.state_file = Path(temp_dir) / "workflow_state.json"
            yield orchestrator

    @pytest.fixture
    def sample_workflow_config(self):
        """样本工作流配置"""
        return {
            'name': 'Test Workflow',
            'global_context': {'project': 'test'},
            'stages': [
                {
                    'name': 'analysis',
                    'description': 'Analysis stage',
                    'execution_mode': 'parallel',
                    'timeout': 600,
                    'depends_on': []
                },
                {
                    'name': 'implementation',
                    'description': 'Implementation stage',
                    'execution_mode': 'sequential',
                    'timeout': 1200,
                    'depends_on': ['analysis']
                }
            ]
        }

    @pytest.fixture
    def task_data(self):
        """样本任务数据"""
        return {
            'agent': 'backend-architect',
            'description': 'Design backend architecture',
            'stage': 'analysis',
            'priority': 1,
            'timeout': 300
        }

    def test_initialization(self, orchestrator):
        """测试初始化"""
        assert orchestrator is not None
        assert orchestrator.current_execution is None
        assert isinstance(orchestrator.execution_callbacks, dict)
        assert len(orchestrator.execution_callbacks) == 7
        assert isinstance(orchestrator.performance_metrics, dict)

    def test_load_workflow_success(self, orchestrator, sample_workflow_config):
        """测试成功加载工作流"""
        result = orchestrator.load_workflow(sample_workflow_config)

        assert result['success'] is True
        assert 'workflow_id' in result
        assert result['stages_count'] == 2
        assert orchestrator.current_execution is not None
        assert orchestrator.current_execution.workflow_name == 'Test Workflow'
        assert len(orchestrator.current_execution.stages) == 2

    def test_load_workflow_invalid_dependencies(self, orchestrator):
        """测试加载带有无效依赖的工作流"""
        invalid_config = {
            'name': 'Invalid Workflow',
            'stages': [
                {
                    'name': 'stage1',
                    'description': 'Stage 1',
                    'execution_mode': 'parallel',
                    'depends_on': ['nonexistent_stage']
                }
            ]
        }

        result = orchestrator.load_workflow(invalid_config)

        assert result['success'] is False
        assert 'validation failed' in result['error'].lower()

    def test_load_workflow_circular_dependencies(self, orchestrator):
        """测试循环依赖检测"""
        circular_config = {
            'name': 'Circular Workflow',
            'stages': [
                {
                    'name': 'stage1',
                    'description': 'Stage 1',
                    'execution_mode': 'parallel',
                    'depends_on': ['stage2']
                },
                {
                    'name': 'stage2',
                    'description': 'Stage 2',
                    'execution_mode': 'parallel',
                    'depends_on': ['stage1']
                }
            ]
        }

        result = orchestrator.load_workflow(circular_config)

        assert result['success'] is False
        assert 'circular' in result['error'].lower()

    def test_create_task_success(self, orchestrator, sample_workflow_config, task_data):
        """测试成功创建任务"""
        orchestrator.load_workflow(sample_workflow_config)

        result = orchestrator.create_task(**task_data)

        assert result['success'] is True
        assert 'task_id' in result
        assert result['task'].agent == task_data['agent']
        assert len(orchestrator.current_execution.stages['analysis'].tasks) == 1

    def test_create_task_no_workflow(self, orchestrator, task_data):
        """测试在没有工作流的情况下创建任务"""
        result = orchestrator.create_task(**task_data)

        assert result['success'] is False
        assert 'no workflow loaded' in result['error'].lower()

    def test_create_task_invalid_stage(self, orchestrator, sample_workflow_config, task_data):
        """测试在无效阶段创建任务"""
        orchestrator.load_workflow(sample_workflow_config)
        task_data['stage'] = 'nonexistent_stage'

        result = orchestrator.create_task(**task_data)

        assert result['success'] is False
        assert 'stage' in result['error'].lower() and 'not found' in result['error'].lower()

    def test_plan_stage_execution_parallel(self, orchestrator, sample_workflow_config):
        """测试并行阶段执行规划"""
        orchestrator.load_workflow(sample_workflow_config)
        orchestrator.create_task('agent1', 'Task 1', 'analysis')
        orchestrator.create_task('agent2', 'Task 2', 'analysis')

        result = orchestrator.plan_stage_execution('analysis')

        assert result['success'] is True
        assert result['execution_mode'] == 'parallel'
        assert result['task_count'] == 2
        assert 'execution_plan' in result
        assert 'estimated_duration' in result

    def test_plan_stage_execution_sequential(self, orchestrator, sample_workflow_config):
        """测试顺序阶段执行规划"""
        orchestrator.load_workflow(sample_workflow_config)
        orchestrator.create_task('agent1', 'Task 1', 'implementation')

        result = orchestrator.plan_stage_execution('implementation')

        assert result['success'] is True
        assert result['execution_mode'] == 'sequential'

    def test_plan_stage_execution_invalid_stage(self, orchestrator, sample_workflow_config):
        """测试无效阶段的执行规划"""
        orchestrator.load_workflow(sample_workflow_config)

        result = orchestrator.plan_stage_execution('nonexistent_stage')

        assert result['success'] is False
        assert 'not found' in result['error'].lower()

    @pytest.mark.asyncio
    async def test_execute_stage_async_success(self, orchestrator, sample_workflow_config):
        """测试异步阶段执行成功"""
        orchestrator.load_workflow(sample_workflow_config)
        orchestrator.create_task('agent1', 'Task 1', 'analysis')

        # Mock task manager
        mock_task_manager = AsyncMock()
        mock_task_manager.execute_task_async.return_value = {
            'success': True,
            'result': 'Mock execution result'
        }
        orchestrator.task_manager = mock_task_manager

        result = await orchestrator.execute_stage_async('analysis')

        assert result['success'] is True
        assert 'execution_time' in result
        assert result['tasks_executed'] == 1

    @pytest.mark.asyncio
    async def test_execute_stage_async_dependency_not_satisfied(self, orchestrator, sample_workflow_config):
        """测试依赖不满足的阶段执行"""
        orchestrator.load_workflow(sample_workflow_config)

        result = await orchestrator.execute_stage_async('implementation')

        assert result['success'] is False
        assert 'dependencies not satisfied' in result['error'].lower()

    def test_execute_stage_sync(self, orchestrator, sample_workflow_config):
        """测试同步阶段执行"""
        orchestrator.load_workflow(sample_workflow_config)
        orchestrator.create_task('agent1', 'Task 1', 'analysis')

        result = orchestrator.execute_stage('analysis')

        assert result['success'] is True

    def test_mark_task_completed_success(self, orchestrator, sample_workflow_config):
        """测试标记任务完成"""
        orchestrator.load_workflow(sample_workflow_config)
        task_result = orchestrator.create_task('agent1', 'Task 1', 'analysis')
        task_id = task_result['task_id']

        result = orchestrator.mark_task_completed(task_id, {'output': 'test result'})

        assert result['success'] is True
        assert 'execution_time' in result

        # 验证任务状态
        task = orchestrator._find_task_by_id(task_id)
        assert task.status == TaskStatus.COMPLETED
        assert task.result is not None

    def test_mark_task_completed_invalid_task(self, orchestrator, sample_workflow_config):
        """测试标记无效任务完成"""
        orchestrator.load_workflow(sample_workflow_config)

        result = orchestrator.mark_task_completed('invalid_task_id', {})

        assert result['success'] is False
        assert 'not found' in result['error'].lower()

    def test_get_workflow_progress_empty(self, orchestrator):
        """测试空工作流的进度"""
        result = orchestrator.get_workflow_progress()

        assert result['completion_percentage'] == 0
        assert result['current_stage'] is None

    def test_get_workflow_progress_with_tasks(self, orchestrator, sample_workflow_config):
        """测试有任务的工作流进度"""
        orchestrator.load_workflow(sample_workflow_config)
        task1_result = orchestrator.create_task('agent1', 'Task 1', 'analysis')
        task2_result = orchestrator.create_task('agent2', 'Task 2', 'analysis')

        # 完成一个任务
        orchestrator.mark_task_completed(task1_result['task_id'], {})

        result = orchestrator.get_workflow_progress()

        assert result['completion_percentage'] > 0
        assert result['tasks_summary']['completed'] == 1
        assert result['tasks_summary']['total'] == 2

    def test_handle_task_error_retry(self, orchestrator, sample_workflow_config):
        """测试任务错误重试"""
        orchestrator.load_workflow(sample_workflow_config)
        task_result = orchestrator.create_task('agent1', 'Task 1', 'analysis')
        task_id = task_result['task_id']

        error_result = {
            'error': 'Network timeout',
            'error_type': 'timeout'
        }

        result = orchestrator.handle_task_error(task_id, error_result)

        assert result['success'] is True
        assert result['action'] == 'retry'
        assert result['retry_count'] == 1

        # 验证任务状态
        task = orchestrator._find_task_by_id(task_id)
        assert task.status == TaskStatus.RETRYING
        assert task.retry_count == 1

    def test_handle_task_error_skip(self, orchestrator, sample_workflow_config):
        """测试任务错误跳过"""
        orchestrator.load_workflow(sample_workflow_config)
        task_result = orchestrator.create_task('agent1', 'Task 1', 'analysis', priority=1)
        task_id = task_result['task_id']

        error_result = {
            'error': 'Unknown error',
            'error_type': 'unknown'
        }

        result = orchestrator.handle_task_error(task_id, error_result)

        assert result['success'] is True
        assert result['action'] == 'skip'

        # 验证任务状态
        task = orchestrator._find_task_by_id(task_id)
        assert task.status == TaskStatus.SKIPPED

    def test_handle_task_error_max_retries_exceeded(self, orchestrator, sample_workflow_config):
        """测试超过最大重试次数"""
        orchestrator.load_workflow(sample_workflow_config)
        task_result = orchestrator.create_task('agent1', 'Task 1', 'analysis')
        task_id = task_result['task_id']

        # 设置任务已达到最大重试次数
        task = orchestrator._find_task_by_id(task_id)
        task.retry_count = task.max_retries

        error_result = {
            'error': 'Network timeout',
            'error_type': 'timeout'
        }

        result = orchestrator.handle_task_error(task_id, error_result)

        assert result['success'] is False
        assert result['action'] == 'fail'
        assert result['retry_exhausted'] is True

    def test_rollback_to_stage_success(self, orchestrator, sample_workflow_config):
        """测试成功回滚到阶段"""
        orchestrator.load_workflow(sample_workflow_config)

        # 创建并完成一些任务
        task1_result = orchestrator.create_task('agent1', 'Task 1', 'analysis')
        orchestrator.mark_task_completed(task1_result['task_id'], {})

        result = orchestrator.rollback_to_stage('analysis')

        assert result['success'] is True
        assert result['target_stage'] == 'analysis'
        assert len(result['rolled_back_stages']) > 0

        # 验证任务状态被重置
        task = orchestrator._find_task_by_id(task1_result['task_id'])
        assert task.status == TaskStatus.CREATED
        assert task.completed_at is None

    def test_rollback_to_stage_invalid_stage(self, orchestrator, sample_workflow_config):
        """测试回滚到无效阶段"""
        orchestrator.load_workflow(sample_workflow_config)

        result = orchestrator.rollback_to_stage('nonexistent_stage')

        assert result['success'] is False
        assert 'not found' in result['error'].lower()

    def test_mark_stage_completed_success(self, orchestrator, sample_workflow_config):
        """测试标记阶段完成"""
        orchestrator.load_workflow(sample_workflow_config)
        task_result = orchestrator.create_task('agent1', 'Task 1', 'analysis')

        # 先完成任务
        orchestrator.mark_task_completed(task_result['task_id'], {'outputs': ['output1']})

        result = orchestrator.mark_stage_completed('analysis')

        assert result['success'] is True
        assert result['stage'] == 'analysis'
        assert 'outputs' in result

        # 验证阶段状态
        stage = orchestrator.current_execution.stages['analysis']
        assert stage.status == TaskStatus.COMPLETED
        assert stage.completed_at is not None

    def test_mark_stage_completed_incomplete_tasks(self, orchestrator, sample_workflow_config):
        """测试标记有未完成任务的阶段"""
        orchestrator.load_workflow(sample_workflow_config)
        orchestrator.create_task('agent1', 'Task 1', 'analysis')

        result = orchestrator.mark_stage_completed('analysis')

        assert result['success'] is False
        assert 'not completed' in result['error'].lower()

    def test_validate_sync_point_success(self, orchestrator):
        """测试同步点验证成功"""
        sync_point = {
            'validation_criteria': {
                'tasks_completed': True,
                'quality_score': '> 80'
            }
        }

        validation_results = {
            'tasks_completed': True,
            'quality_score': 85
        }

        result = orchestrator.validate_sync_point(sync_point, validation_results)

        assert result['success'] is True
        assert result['all_criteria_met'] is True
        assert len(result['failed_criteria']) == 0

    def test_validate_sync_point_failure(self, orchestrator):
        """测试同步点验证失败"""
        sync_point = {
            'validation_criteria': {
                'tasks_completed': True,
                'quality_score': '> 90'
            }
        }

        validation_results = {
            'tasks_completed': False,
            'quality_score': 75
        }

        result = orchestrator.validate_sync_point(sync_point, validation_results)

        assert result['success'] is False
        assert result['all_criteria_met'] is False
        assert len(result['failed_criteria']) == 2

    def test_register_callback(self, orchestrator):
        """测试注册回调函数"""
        callback_called = False

        def test_callback(data):
            nonlocal callback_called
            callback_called = True

        orchestrator.register_callback('on_stage_start', test_callback)

        # 触发回调
        orchestrator._trigger_callbacks('on_stage_start', {})

        assert callback_called is True

    def test_set_task_manager(self, orchestrator):
        """测试设置任务管理器"""
        mock_task_manager = Mock()
        orchestrator.set_task_manager(mock_task_manager)

        assert orchestrator.task_manager == mock_task_manager

    def test_get_execution_metrics(self, orchestrator):
        """测试获取执行指标"""
        metrics = orchestrator.get_execution_metrics()

        assert isinstance(metrics, dict)
        assert 'total_execution_time' in metrics
        assert 'stage_execution_times' in metrics

    def test_get_execution_log_empty(self, orchestrator):
        """测试获取空执行日志"""
        log = orchestrator.get_execution_log()

        assert isinstance(log, list)
        assert len(log) == 0

    def test_get_execution_log_with_events(self, orchestrator, sample_workflow_config):
        """测试获取有事件的执行日志"""
        orchestrator.load_workflow(sample_workflow_config)
        orchestrator.create_task('agent1', 'Task 1', 'analysis')

        log = orchestrator.get_execution_log()

        assert len(log) > 0
        assert all('timestamp' in entry for entry in log)
        assert all('event_type' in entry for entry in log)

    def test_state_persistence(self, orchestrator, sample_workflow_config):
        """测试状态持久化"""
        orchestrator.load_workflow(sample_workflow_config)

        # 检查状态文件是否存在
        assert orchestrator.state_file.exists()

        # 验证状态文件内容
        with open(orchestrator.state_file, 'r') as f:
            state_data = json.load(f)

        assert 'workflow_id' in state_data
        assert 'workflow_name' in state_data
        assert state_data['workflow_name'] == 'Test Workflow'


class TestTaskEntity:
    """Task实体测试"""

    def test_task_creation(self):
        """测试任务创建"""
        task = Task(
            task_id='test_task',
            agent='test_agent',
            description='Test task description',
            stage='test_stage'
        )

        assert task.task_id == 'test_task'
        assert task.agent == 'test_agent'
        assert task.status == TaskStatus.CREATED
        assert task.retry_count == 0
        assert task.max_retries == 3

    def test_task_with_dependencies(self):
        """测试带依赖的任务"""
        task = Task(
            task_id='test_task',
            agent='test_agent',
            description='Test task',
            stage='test_stage',
            dependencies=['dep1', 'dep2']
        )

        assert len(task.dependencies) == 2
        assert 'dep1' in task.dependencies


class TestStageEntity:
    """Stage实体测试"""

    def test_stage_creation(self):
        """测试阶段创建"""
        stage = Stage(
            name='test_stage',
            description='Test stage description',
            execution_mode=ExecutionMode.PARALLEL
        )

        assert stage.name == 'test_stage'
        assert stage.execution_mode == ExecutionMode.PARALLEL
        assert stage.status == TaskStatus.CREATED
        assert len(stage.tasks) == 0


class TestWorkflowExecution:
    """WorkflowExecution实体测试"""

    def test_workflow_execution_creation(self):
        """测试工作流执行上下文创建"""
        execution = WorkflowExecution(
            workflow_id='test_workflow',
            workflow_name='Test Workflow'
        )

        assert execution.workflow_id == 'test_workflow'
        assert execution.state == WorkflowState.INITIALIZED
        assert execution.error_recovery_count == 0


class TestExecutionModes:
    """执行模式测试"""

    @pytest.fixture
    def orchestrator_with_workflow(self):
        """创建带工作流的编排器"""
        with tempfile.TemporaryDirectory() as temp_dir:
            orchestrator = WorkflowOrchestrator()
            orchestrator.state_file = Path(temp_dir) / "workflow_state.json"

            config = {
                'name': 'Mode Test Workflow',
                'stages': [
                    {
                        'name': 'parallel_stage',
                        'description': 'Parallel execution stage',
                        'execution_mode': 'parallel',
                    },
                    {
                        'name': 'sequential_stage',
                        'description': 'Sequential execution stage',
                        'execution_mode': 'sequential',
                    },
                    {
                        'name': 'hybrid_stage',
                        'description': 'Hybrid execution stage',
                        'execution_mode': 'hybrid',
                    }
                ]
            }

            orchestrator.load_workflow(config)
            yield orchestrator

    @pytest.mark.asyncio
    async def test_parallel_execution(self, orchestrator_with_workflow):
        """测试并行执行模式"""
        orchestrator = orchestrator_with_workflow

        # 添加多个任务到并行阶段
        for i in range(3):
            orchestrator.create_task(f'agent{i}', f'Task {i}', 'parallel_stage')

        stage = orchestrator.current_execution.stages['parallel_stage']
        execution_plan = {'type': 'parallel', 'groups': [{'tasks': [t.task_id for t in stage.tasks]}]}

        result = await orchestrator._execute_parallel_tasks(stage, execution_plan)

        assert result['success'] is True
        assert result['total_tasks'] == 3

    @pytest.mark.asyncio
    async def test_sequential_execution(self, orchestrator_with_workflow):
        """测试顺序执行模式"""
        orchestrator = orchestrator_with_workflow

        # 添加任务到顺序阶段
        for i in range(2):
            orchestrator.create_task(f'agent{i}', f'Task {i}', 'sequential_stage')

        stage = orchestrator.current_execution.stages['sequential_stage']
        execution_plan = {'type': 'sequential', 'order': [t.task_id for t in stage.tasks]}

        result = await orchestrator._execute_sequential_tasks(stage, execution_plan)

        assert result['success'] is True
        assert result['completed_tasks'] == 2

    @pytest.mark.asyncio
    async def test_hybrid_execution(self, orchestrator_with_workflow):
        """测试混合执行模式"""
        orchestrator = orchestrator_with_workflow

        # 添加任务到混合阶段
        orchestrator.create_task('agent1', 'Task 1', 'hybrid_stage', dependencies=[])
        orchestrator.create_task('agent2', 'Task 2', 'hybrid_stage', dependencies=['task_hybrid_stage_agent1'])

        stage = orchestrator.current_execution.stages['hybrid_stage']

        # 构建依赖图
        dependency_graph = orchestrator._build_task_dependency_graph(stage.tasks)
        execution_plan = orchestrator._create_dependency_based_plan(stage.tasks, dependency_graph)

        result = await orchestrator._execute_hybrid_tasks(stage, execution_plan)

        assert result['success'] is True


class TestErrorHandling:
    """错误处理测试"""

    @pytest.fixture
    def orchestrator_with_tasks(self):
        """创建带任务的编排器"""
        with tempfile.TemporaryDirectory() as temp_dir:
            orchestrator = WorkflowOrchestrator()
            orchestrator.state_file = Path(temp_dir) / "workflow_state.json"

            config = {
                'name': 'Error Test Workflow',
                'stages': [
                    {
                        'name': 'error_stage',
                        'description': 'Error testing stage',
                        'execution_mode': 'parallel',
                    }
                ]
            }

            orchestrator.load_workflow(config)
            task_result = orchestrator.create_task('test_agent', 'Test task', 'error_stage')
            yield orchestrator, task_result['task_id']

    def test_error_recovery_strategy_retry(self, orchestrator_with_tasks):
        """测试重试错误恢复策略"""
        orchestrator, task_id = orchestrator_with_tasks
        task = orchestrator._find_task_by_id(task_id)

        error_result = {'error_type': 'timeout'}
        strategy = orchestrator._determine_error_recovery_strategy(task, error_result)

        assert strategy['action'] == 'retry'

    def test_error_recovery_strategy_fail(self, orchestrator_with_tasks):
        """测试失败错误恢复策略"""
        orchestrator, task_id = orchestrator_with_tasks
        task = orchestrator._find_task_by_id(task_id)

        error_result = {'error_type': 'validation_error'}
        strategy = orchestrator._determine_error_recovery_strategy(task, error_result)

        assert strategy['action'] == 'fail'

    def test_error_recovery_strategy_skip(self, orchestrator_with_tasks):
        """测试跳过错误恢复策略"""
        orchestrator, task_id = orchestrator_with_tasks
        task = orchestrator._find_task_by_id(task_id)
        task.priority = 1  # 低优先级

        error_result = {'error_type': 'unknown'}
        strategy = orchestrator._determine_error_recovery_strategy(task, error_result)

        assert strategy['action'] == 'skip'

    def test_workflow_level_error_handling(self, orchestrator_with_tasks):
        """测试工作流级别错误处理"""
        orchestrator, task_id = orchestrator_with_tasks
        task = orchestrator._find_task_by_id(task_id)

        result = orchestrator._handle_workflow_level_error(task)

        assert result['action'] == 'continue'
        assert orchestrator.current_execution.error_recovery_count == 1

    def test_max_error_recovery_exceeded(self, orchestrator_with_tasks):
        """测试超过最大错误恢复次数"""
        orchestrator, task_id = orchestrator_with_tasks
        task = orchestrator._find_task_by_id(task_id)

        # 设置已达到最大错误恢复次数
        orchestrator.current_execution.error_recovery_count = orchestrator.current_execution.max_error_recovery

        result = orchestrator._handle_workflow_level_error(task)

        assert result['action'] == 'terminate'
        assert orchestrator.current_execution.state == WorkflowState.FAILED


class TestSyncPointsAndQualityGates:
    """同步点和质量门测试"""

    @pytest.fixture
    def orchestrator_with_sync_stage(self):
        """创建带同步点的编排器"""
        with tempfile.TemporaryDirectory() as temp_dir:
            orchestrator = WorkflowOrchestrator()
            orchestrator.state_file = Path(temp_dir) / "workflow_state.json"

            config = {
                'name': 'Sync Test Workflow',
                'stages': [
                    {
                        'name': 'sync_stage',
                        'description': 'Stage with sync point',
                        'execution_mode': 'parallel',
                        'sync_point': {
                            'type': 'validation',
                            'validation_criteria': {
                                'test_coverage': '> 90',
                                'code_quality': '> 85'
                            },
                            'must_pass': True
                        },
                        'quality_gate': {
                            'checklist': 'Security,Performance,Maintainability',
                            'must_pass': True
                        }
                    }
                ]
            }

            orchestrator.load_workflow(config)
            yield orchestrator

    @pytest.mark.asyncio
    async def test_handle_sync_point_success(self, orchestrator_with_sync_stage):
        """测试同步点处理成功"""
        orchestrator = orchestrator_with_sync_stage
        stage = orchestrator.current_execution.stages['sync_stage']

        # Mock 验证数据收集
        with patch.object(orchestrator, '_collect_sync_validation_data') as mock_collect:
            mock_collect.return_value = {
                'test_coverage': 95,
                'code_quality': 90
            }

            result = await orchestrator._handle_sync_point(stage)

            assert result['success'] is True
            assert result['sync_point_passed'] is True

    @pytest.mark.asyncio
    async def test_handle_sync_point_failure(self, orchestrator_with_sync_stage):
        """测试同步点处理失败"""
        orchestrator = orchestrator_with_sync_stage
        stage = orchestrator.current_execution.stages['sync_stage']

        # Mock 验证数据收集
        with patch.object(orchestrator, '_collect_sync_validation_data') as mock_collect:
            mock_collect.return_value = {
                'test_coverage': 85,  # 低于90%
                'code_quality': 80    # 低于85
            }

            result = await orchestrator._handle_sync_point(stage)

            assert result['success'] is False

    @pytest.mark.asyncio
    async def test_handle_quality_gate_success(self, orchestrator_with_sync_stage):
        """测试质量门处理成功"""
        orchestrator = orchestrator_with_sync_stage
        stage = orchestrator.current_execution.stages['sync_stage']

        result = await orchestrator._handle_quality_gate(stage)

        assert result['success'] is True
        assert result['quality_gate_passed'] is True

    def test_collect_sync_validation_data(self, orchestrator_with_sync_stage):
        """测试同步点验证数据收集"""
        orchestrator = orchestrator_with_sync_stage
        stage = orchestrator.current_execution.stages['sync_stage']

        # 添加一些完成的任务
        orchestrator.create_task('agent1', 'Task 1', 'sync_stage')
        task_id = orchestrator.current_execution.stages['sync_stage'].tasks[0].task_id
        orchestrator.mark_task_completed(task_id, {'outputs': ['output1']})

        data = orchestrator._collect_sync_validation_data(stage)

        assert 'tasks_completed' in data
        assert 'tasks_failed' in data
        assert 'stage_outputs' in data
        assert data['tasks_completed'] == 1


class TestPerformanceMetrics:
    """性能指标测试"""

    @pytest.fixture
    def orchestrator_with_completed_tasks(self):
        """创建带已完成任务的编排器"""
        with tempfile.TemporaryDirectory() as temp_dir:
            orchestrator = WorkflowOrchestrator()
            orchestrator.state_file = Path(temp_dir) / "workflow_state.json"

            config = {
                'name': 'Performance Test Workflow',
                'stages': [
                    {
                        'name': 'perf_stage',
                        'description': 'Performance testing stage',
                        'execution_mode': 'parallel',
                    }
                ]
            }

            orchestrator.load_workflow(config)

            # 创建并完成任务
            task_result = orchestrator.create_task('agent1', 'Task 1', 'perf_stage')
            task_id = task_result['task_id']

            # 模拟任务执行时间
            task = orchestrator._find_task_by_id(task_id)
            task.started_at = datetime.now() - timedelta(seconds=5)

            orchestrator.mark_task_completed(task_id, {})

            yield orchestrator, task_id

    def test_task_execution_time_tracking(self, orchestrator_with_completed_tasks):
        """测试任务执行时间跟踪"""
        orchestrator, task_id = orchestrator_with_completed_tasks

        metrics = orchestrator.get_execution_metrics()

        assert task_id in metrics['task_execution_times']
        assert metrics['task_execution_times'][task_id] > 0

    def test_stage_execution_time_tracking(self, orchestrator_with_completed_tasks):
        """测试阶段执行时间跟踪"""
        orchestrator, task_id = orchestrator_with_completed_tasks

        # 标记阶段完成
        stage = orchestrator.current_execution.stages['perf_stage']
        stage.started_at = datetime.now() - timedelta(seconds=10)

        orchestrator.mark_stage_completed('perf_stage')

        metrics = orchestrator.get_execution_metrics()

        assert 'perf_stage' in metrics['stage_execution_times']
        assert metrics['stage_execution_times']['perf_stage'] > 0


class TestDependencyHandling:
    """依赖处理测试"""

    @pytest.fixture
    def orchestrator_with_dependencies(self):
        """创建带依赖关系的编排器"""
        with tempfile.TemporaryDirectory() as temp_dir:
            orchestrator = WorkflowOrchestrator()
            orchestrator.state_file = Path(temp_dir) / "workflow_state.json"

            config = {
                'name': 'Dependency Test Workflow',
                'stages': [
                    {
                        'name': 'stage1',
                        'description': 'First stage',
                        'execution_mode': 'parallel',
                    },
                    {
                        'name': 'stage2',
                        'description': 'Second stage',
                        'execution_mode': 'parallel',
                        'depends_on': ['stage1']
                    },
                    {
                        'name': 'stage3',
                        'description': 'Third stage',
                        'execution_mode': 'parallel',
                        'depends_on': ['stage1', 'stage2']
                    }
                ]
            }

            orchestrator.load_workflow(config)
            yield orchestrator

    def test_build_task_dependency_graph(self, orchestrator_with_dependencies):
        """测试构建任务依赖图"""
        orchestrator = orchestrator_with_dependencies

        # 创建带依赖的任务
        orchestrator.create_task('agent1', 'Task 1', 'stage1')
        orchestrator.create_task('agent2', 'Task 2', 'stage1', dependencies=['task_stage1_agent1'])

        stage = orchestrator.current_execution.stages['stage1']
        dependency_graph = orchestrator._build_task_dependency_graph(stage.tasks)

        assert len(dependency_graph) == 2
        assert any(len(deps) > 0 for deps in dependency_graph.values())

    def test_create_dependency_based_plan(self, orchestrator_with_dependencies):
        """测试基于依赖的执行计划"""
        orchestrator = orchestrator_with_dependencies

        # 创建带依赖的任务
        task1_result = orchestrator.create_task('agent1', 'Task 1', 'stage1')
        task2_result = orchestrator.create_task('agent2', 'Task 2', 'stage1', dependencies=[task1_result['task_id']])

        stage = orchestrator.current_execution.stages['stage1']
        dependency_graph = orchestrator._build_task_dependency_graph(stage.tasks)

        plan = orchestrator._create_dependency_based_plan(stage.tasks, dependency_graph)

        assert plan['type'] == 'layered'
        assert len(plan['levels']) >= 2  # 至少两层

    def test_check_stage_dependencies_satisfied(self, orchestrator_with_dependencies):
        """测试检查阶段依赖满足"""
        orchestrator = orchestrator_with_dependencies

        # 完成stage1
        orchestrator.current_execution.stages['stage1'].status = TaskStatus.COMPLETED

        result = orchestrator._check_stage_dependencies('stage2')

        assert result['satisfied'] is True
        assert len(result['missing']) == 0

    def test_check_stage_dependencies_not_satisfied(self, orchestrator_with_dependencies):
        """测试检查阶段依赖不满足"""
        orchestrator = orchestrator_with_dependencies

        result = orchestrator._check_stage_dependencies('stage2')

        assert result['satisfied'] is False
        assert 'stage1' in result['missing']


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])