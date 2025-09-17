#!/usr/bin/env python3
"""
Workflow Orchestrator模块测试
测试工作流编排、任务协调和同步点管理功能
"""

import os
import sys
import pytest
import asyncio
import json
import tempfile
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from features.workflow_orchestrator.orchestrator import WorkflowOrchestrator
from features.workflow_orchestrator.task_manager import TaskManager
from features.sync_point_manager.sync_manager import SyncPointManager

class TestWorkflowOrchestrator:
    """工作流编排器测试类"""

    @pytest.fixture
    def orchestrator(self):
        """工作流编排器实例"""
        return WorkflowOrchestrator()

    @pytest.fixture
    def sample_workflow(self):
        """示例工作流配置"""
        return {
            "name": "test_workflow",
            "version": "1.0.0",
            "description": "Test workflow for unit testing",
            "stages": [
                {
                    "name": "analysis",
                    "agents": ["@business-analyst", "@project-manager"],
                    "execution_mode": "parallel",
                    "timeout": 300
                },
                {
                    "name": "design",
                    "agents": ["@api-designer", "@backend-architect"],
                    "execution_mode": "sequential",
                    "timeout": 600
                },
                {
                    "name": "implementation",
                    "agents": ["@backend-architect", "@frontend-specialist"],
                    "execution_mode": "parallel",
                    "timeout": 1200
                }
            ],
            "sync_points": [
                {
                    "after_stage": "analysis",
                    "type": "validation",
                    "criteria": ["requirements_complete", "stakeholder_approval"]
                },
                {
                    "after_stage": "design",
                    "type": "review",
                    "criteria": ["architecture_approved", "api_documented"]
                }
            ]
        }

    def test_orchestrator_initialization(self, orchestrator):
        """测试编排器初始化"""
        assert orchestrator is not None
        assert hasattr(orchestrator, 'execute_workflow')
        assert hasattr(orchestrator, 'create_task')
        assert hasattr(orchestrator, 'monitor_progress')

    def test_workflow_loading(self, orchestrator, sample_workflow):
        """测试工作流加载"""
        result = orchestrator.load_workflow(sample_workflow)

        assert result['success'] is True
        assert orchestrator.current_workflow is not None
        assert orchestrator.current_workflow['name'] == "test_workflow"

    def test_task_creation(self, orchestrator, sample_workflow):
        """测试任务创建"""
        orchestrator.load_workflow(sample_workflow)

        task = orchestrator.create_task(
            agent="@business-analyst",
            description="Analyze business requirements",
            stage="analysis"
        )

        assert task is not None
        assert task['agent'] == "@business-analyst"
        assert task['stage'] == "analysis"
        assert 'task_id' in task

    def test_parallel_execution_planning(self, orchestrator, sample_workflow):
        """测试并行执行规划"""
        orchestrator.load_workflow(sample_workflow)

        analysis_stage = sample_workflow['stages'][0]
        execution_plan = orchestrator.plan_stage_execution(analysis_stage)

        assert execution_plan['execution_mode'] == "parallel"
        assert len(execution_plan['tasks']) == 2
        assert execution_plan['estimated_duration'] <= analysis_stage['timeout']

    def test_sequential_execution_planning(self, orchestrator, sample_workflow):
        """测试顺序执行规划"""
        orchestrator.load_workflow(sample_workflow)

        design_stage = sample_workflow['stages'][1]
        execution_plan = orchestrator.plan_stage_execution(design_stage)

        assert execution_plan['execution_mode'] == "sequential"
        assert len(execution_plan['tasks']) == 2

    @patch('features.workflow_orchestrator.orchestrator.WorkflowOrchestrator.execute_agent_task')
    def test_stage_execution(self, mock_execute_task, orchestrator, sample_workflow):
        """测试阶段执行"""
        mock_execute_task.return_value = {
            'success': True,
            'result': 'Task completed successfully',
            'duration': 120
        }

        orchestrator.load_workflow(sample_workflow)
        analysis_stage = sample_workflow['stages'][0]

        result = orchestrator.execute_stage(analysis_stage)

        assert result['success'] is True
        assert mock_execute_task.call_count == 2  # 两个并行任务

    def test_sync_point_validation(self, orchestrator, sample_workflow):
        """测试同步点验证"""
        orchestrator.load_workflow(sample_workflow)

        # 模拟阶段完成后的同步点检查
        sync_point = sample_workflow['sync_points'][0]

        # 模拟验证条件
        validation_results = {
            'requirements_complete': True,
            'stakeholder_approval': True
        }

        result = orchestrator.validate_sync_point(sync_point, validation_results)

        assert result['success'] is True
        assert result['all_criteria_met'] is True

    def test_sync_point_failure(self, orchestrator, sample_workflow):
        """测试同步点失败"""
        orchestrator.load_workflow(sample_workflow)

        sync_point = sample_workflow['sync_points'][0]

        # 模拟验证失败
        validation_results = {
            'requirements_complete': True,
            'stakeholder_approval': False  # 失败条件
        }

        result = orchestrator.validate_sync_point(sync_point, validation_results)

        assert result['success'] is False
        assert result['all_criteria_met'] is False
        assert 'stakeholder_approval' in result['failed_criteria']

    @patch('asyncio.create_task')
    async def test_async_task_coordination(self, mock_create_task, orchestrator, sample_workflow):
        """测试异步任务协调"""
        # 创建模拟的异步任务
        mock_task1 = AsyncMock()
        mock_task1.return_value = {'success': True, 'agent': '@business-analyst'}

        mock_task2 = AsyncMock()
        mock_task2.return_value = {'success': True, 'agent': '@project-manager'}

        mock_create_task.side_effect = [mock_task1, mock_task2]

        orchestrator.load_workflow(sample_workflow)
        analysis_stage = sample_workflow['stages'][0]

        result = await orchestrator.execute_stage_async(analysis_stage)

        assert result['success'] is True
        assert mock_create_task.call_count == 2

    def test_workflow_progress_monitoring(self, orchestrator, sample_workflow):
        """测试工作流进度监控"""
        orchestrator.load_workflow(sample_workflow)

        # 模拟一些任务完成
        orchestrator.mark_task_completed("task_1", {"success": True})
        orchestrator.mark_task_completed("task_2", {"success": True})

        progress = orchestrator.get_workflow_progress()

        assert 'completion_percentage' in progress
        assert 'completed_stages' in progress
        assert 'current_stage' in progress
        assert progress['completion_percentage'] > 0

    def test_error_handling_in_workflow(self, orchestrator, sample_workflow):
        """测试工作流错误处理"""
        orchestrator.load_workflow(sample_workflow)

        # 模拟任务失败
        error_result = {
            'success': False,
            'error': 'Agent execution failed',
            'retry_count': 1
        }

        result = orchestrator.handle_task_error("task_1", error_result)

        assert 'retry_scheduled' in result
        assert 'error_logged' in result

    def test_workflow_rollback(self, orchestrator, sample_workflow):
        """测试工作流回滚"""
        orchestrator.load_workflow(sample_workflow)

        # 模拟执行到一半然后失败
        orchestrator.mark_stage_completed("analysis")

        # 触发回滚
        result = orchestrator.rollback_to_stage("analysis")

        assert result['success'] is True
        assert orchestrator.current_stage == "analysis"

class TestTaskManager:
    """任务管理器测试类"""

    @pytest.fixture
    def task_manager(self):
        """任务管理器实例"""
        return TaskManager()

    def test_task_manager_initialization(self, task_manager):
        """测试任务管理器初始化"""
        assert task_manager is not None
        assert hasattr(task_manager, 'create_task')
        assert hasattr(task_manager, 'execute_task')
        assert hasattr(task_manager, 'monitor_task')

    def test_task_creation(self, task_manager):
        """测试任务创建"""
        task_config = {
            'agent': '@business-analyst',
            'description': 'Analyze business requirements',
            'priority': 'high',
            'timeout': 300
        }

        task = task_manager.create_task(task_config)

        assert task is not None
        assert 'task_id' in task
        assert task['status'] == 'created'
        assert task['agent'] == '@business-analyst'

    def test_task_execution(self, task_manager):
        """测试任务执行"""
        task_config = {
            'agent': '@business-analyst',
            'description': 'Analyze business requirements',
            'priority': 'high',
            'timeout': 300
        }

        task = task_manager.create_task(task_config)

        with patch.object(task_manager, 'execute_agent') as mock_execute:
            mock_execute.return_value = {'success': True, 'result': 'Analysis completed'}

            result = task_manager.execute_task(task['task_id'])

            assert result['success'] is True
            assert mock_execute.called

    def test_task_monitoring(self, task_manager):
        """测试任务监控"""
        task_config = {
            'agent': '@business-analyst',
            'description': 'Analyze business requirements',
            'priority': 'high',
            'timeout': 300
        }

        task = task_manager.create_task(task_config)
        task_id = task['task_id']

        # 测试任务状态监控
        status = task_manager.get_task_status(task_id)
        assert status == 'created'

        # 模拟任务执行开始
        task_manager.update_task_status(task_id, 'running')
        status = task_manager.get_task_status(task_id)
        assert status == 'running'

    def test_task_timeout_handling(self, task_manager):
        """测试任务超时处理"""
        task_config = {
            'agent': '@business-analyst',
            'description': 'Long running analysis',
            'priority': 'high',
            'timeout': 1  # 1秒超时
        }

        task = task_manager.create_task(task_config)

        with patch('time.sleep') as mock_sleep:
            with patch.object(task_manager, 'execute_agent') as mock_execute:
                # 模拟长时间运行的任务
                mock_execute.side_effect = lambda: time.sleep(2)

                result = task_manager.execute_task_with_timeout(task['task_id'])

                assert result['success'] is False
                assert 'timeout' in result['error'].lower()

class TestSyncPointManager:
    """同步点管理器测试类"""

    @pytest.fixture
    def sync_manager(self):
        """同步点管理器实例"""
        return SyncPointManager()

    def test_sync_manager_initialization(self, sync_manager):
        """测试同步点管理器初始化"""
        assert sync_manager is not None
        assert hasattr(sync_manager, 'create_sync_point')
        assert hasattr(sync_manager, 'validate_sync_point')
        assert hasattr(sync_manager, 'wait_for_sync_point')

    def test_sync_point_creation(self, sync_manager):
        """测试同步点创建"""
        sync_config = {
            'name': 'requirements_validation',
            'type': 'validation',
            'criteria': ['requirements_complete', 'stakeholder_approval'],
            'timeout': 300
        }

        sync_point = sync_manager.create_sync_point(sync_config)

        assert sync_point is not None
        assert 'sync_id' in sync_point
        assert sync_point['status'] == 'waiting'

    def test_sync_point_validation_success(self, sync_manager):
        """测试同步点验证成功"""
        sync_config = {
            'name': 'requirements_validation',
            'type': 'validation',
            'criteria': ['requirements_complete', 'stakeholder_approval'],
            'timeout': 300
        }

        sync_point = sync_manager.create_sync_point(sync_config)
        sync_id = sync_point['sync_id']

        # 提供验证数据
        validation_data = {
            'requirements_complete': True,
            'stakeholder_approval': True
        }

        result = sync_manager.validate_sync_point(sync_id, validation_data)

        assert result['success'] is True
        assert result['all_criteria_met'] is True

    def test_sync_point_validation_failure(self, sync_manager):
        """测试同步点验证失败"""
        sync_config = {
            'name': 'requirements_validation',
            'type': 'validation',
            'criteria': ['requirements_complete', 'stakeholder_approval'],
            'timeout': 300
        }

        sync_point = sync_manager.create_sync_point(sync_config)
        sync_id = sync_point['sync_id']

        # 提供不完整的验证数据
        validation_data = {
            'requirements_complete': True,
            'stakeholder_approval': False
        }

        result = sync_manager.validate_sync_point(sync_id, validation_data)

        assert result['success'] is False
        assert result['all_criteria_met'] is False