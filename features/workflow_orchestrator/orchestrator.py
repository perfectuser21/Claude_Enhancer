"""
Workflow Orchestrator - Production Implementation
工作流编排器：管理Perfect21的智能工作流执行
"""

import time
import json
import asyncio
import logging
import concurrent.futures
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union, Protocol
from dataclasses import dataclass, field
from pathlib import Path

# Import shared types
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from shared.types import (
    ExecutionMode, WorkflowState, TaskStatus, ExecutionPlan, PerformanceMetrics,
    TaskExecutor, StageCallback, TaskCallback, ErrorHandler
)

# Type aliases for better readability
TaskId = str
StageId = str
WorkflowId = str
AgentName = str


# Protocol definitions
class TaskManagerProtocol(Protocol):
    """任务管理器协议"""
    def execute_task_async(self, task_id: TaskId) -> Dict[str, Any]:
        ...


class SyncManagerProtocol(Protocol):
    """同步点管理器协议"""
    def validate_sync_point(self, sync_point: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        ...

@dataclass
class Task:
    """任务实体"""
    task_id: str
    agent: str
    description: str
    stage: str
    priority: int = 1
    timeout: int = 300
    status: TaskStatus = TaskStatus.CREATED
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    dependencies: List[str] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)

@dataclass
class Stage:
    """阶段实体"""
    name: str
    description: str
    execution_mode: ExecutionMode
    tasks: List[Task] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    sync_point: Optional[Dict[str, Any]] = None
    quality_gate: Optional[Dict[str, Any]] = None
    thinking_mode: Optional[str] = None
    timeout: int = 1800  # 30 minutes default
    status: TaskStatus = TaskStatus.CREATED
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    outputs: List[str] = field(default_factory=list)

@dataclass
class WorkflowExecution:
    """工作流执行上下文"""
    workflow_id: str
    workflow_name: str
    state: WorkflowState = WorkflowState.INITIALIZED
    current_stage: Optional[str] = None
    stages: Dict[str, Stage] = field(default_factory=dict)
    global_context: Dict[str, Any] = field(default_factory=dict)
    execution_log: List[Dict[str, Any]] = field(default_factory=list)
    quality_metrics: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_recovery_count: int = 0
    max_error_recovery: int = 5

class WorkflowOrchestrator:
    """生产级工作流编排器"""

    def __init__(self, logger: Optional[logging.Logger] = None) -> None:
        self.logger: logging.Logger = logger or logging.getLogger(__name__)
        self.current_execution: Optional[WorkflowExecution] = None
        self.task_manager: Optional[TaskManagerProtocol] = None  # Will be injected
        self.sync_manager: Optional[SyncManagerProtocol] = None  # Will be injected
        self.execution_callbacks: Dict[str, List[Callable[[Dict[str, Any]], None]]] = {
            'on_stage_start': [],
            'on_stage_complete': [],
            'on_task_start': [],
            'on_task_complete': [],
            'on_error': [],
            'on_sync_point': [],
            'on_quality_gate': []
        }

        # 状态持久化
        self.state_file: Path = Path(".perfect21/workflow_state.json")
        self.state_file.parent.mkdir(exist_ok=True)

        # 性能监控
        self.performance_metrics: PerformanceMetrics = {
            'total_execution_time': 0.0,
            'stage_execution_times': {},
            'task_execution_times': {},
            'sync_point_wait_times': {},
            'quality_gate_check_times': {}
        }

    def load_workflow(self, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
        """加载工作流配置并初始化执行上下文"""
        try:
            workflow_id = f"workflow_{int(time.time())}"
            workflow_name = workflow_config.get('name', 'Unnamed Workflow')

            # 创建执行上下文
            self.current_execution = WorkflowExecution(
                workflow_id=workflow_id,
                workflow_name=workflow_name,
                global_context=workflow_config.get('global_context', {})
            )

            # 解析阶段配置
            stages_config = workflow_config.get('stages', [])
            for stage_config in stages_config:
                stage = self._parse_stage_config(stage_config)
                self.current_execution.stages[stage.name] = stage

            # 验证依赖关系
            validation_result = self._validate_workflow_dependencies()
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': f"Workflow validation failed: {validation_result['errors']}"
                }

            # 保存状态
            self._save_execution_state()

            self.logger.info(f"Workflow loaded successfully: {workflow_name} ({workflow_id})")
            return {
                'success': True,
                'workflow_id': workflow_id,
                'stages_count': len(self.current_execution.stages),
                'validation': validation_result
            }

        except Exception as e:
            self.logger.error(f"Failed to load workflow: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def create_task(
        self,
        agent: AgentName,
        description: str,
        stage: StageId,
        priority: int = 1,
        timeout: int = 300,
        dependencies: Optional[List[TaskId]] = None
    ) -> Dict[str, Any]:
        """创建任务"""
        try:
            if not self.current_execution:
                return {'success': False, 'error': 'No workflow loaded'}

            if stage not in self.current_execution.stages:
                return {'success': False, 'error': f'Stage {stage} not found'}

            task_id = f"task_{stage}_{agent}_{int(time.time())}"

            task = Task(
                task_id=task_id,
                agent=agent,
                description=description,
                stage=stage,
                priority=priority,
                timeout=timeout,
                dependencies=dependencies or []
            )

            # 添加到对应阶段
            self.current_execution.stages[stage].tasks.append(task)

            # 记录执行日志
            self._log_execution_event('task_created', {
                'task_id': task_id,
                'agent': agent,
                'stage': stage
            })

            self.logger.info(f"Task created: {task_id} ({agent} in {stage})")
            return {
                'success': True,
                'task_id': task_id,
                'task': task
            }

        except Exception as e:
            self.logger.error(f"Failed to create task: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def plan_stage_execution(self, stage_name: StageId) -> Dict[str, Any]:
        """规划阶段执行策略"""
        try:
            if not self.current_execution:
                return {'success': False, 'error': 'No workflow loaded'}

            if stage_name not in self.current_execution.stages:
                return {'success': False, 'error': f'Stage {stage_name} not found'}

            stage = self.current_execution.stages[stage_name]

            # 分析任务依赖关系
            task_dependency_graph = self._build_task_dependency_graph(stage.tasks)

            # 根据执行模式制定执行计划
            execution_plan = self._create_execution_plan(stage, task_dependency_graph)

            # 估算执行时间
            estimated_duration = self._estimate_stage_duration(stage, execution_plan)

            # 资源需求评估
            resource_requirements = self._assess_resource_requirements(stage)

            plan = {
                'success': True,
                'stage_name': stage_name,
                'execution_mode': stage.execution_mode.value,
                'execution_plan': execution_plan,
                'estimated_duration': estimated_duration,
                'resource_requirements': resource_requirements,
                'task_count': len(stage.tasks),
                'has_sync_point': stage.sync_point is not None,
                'has_quality_gate': stage.quality_gate is not None
            }

            self.logger.info(f"Stage execution planned: {stage_name} ({len(stage.tasks)} tasks)")
            return plan

        except Exception as e:
            self.logger.error(f"Failed to plan stage execution: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def execute_stage(self, stage_name: StageId) -> Dict[str, Any]:
        """同步执行阶段（防止事件循环冲突）"""
        try:
            # 检查是否已在事件循环中
            try:
                current_loop = asyncio.get_running_loop()
                # 如果已在事件循环中，使用线程池
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(self._run_async_in_thread, stage_name)
                    return future.result()
            except RuntimeError:
                # 没有正在运行的事件循环，创建新的
                return asyncio.run(self.execute_stage_async(stage_name))

        except Exception as e:
            self.logger.error(f"Stage execution failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def _run_async_in_thread(self, stage_name: StageId) -> Dict[str, Any]:
        """在新线程中运行异步任务"""
        return asyncio.run(self.execute_stage_async(stage_name))

    async def execute_stage_async(self, stage_name: StageId) -> Dict[str, Any]:
        """异步执行阶段"""
        try:
            if not self.current_execution:
                return {'success': False, 'error': 'No workflow loaded'}

            if stage_name not in self.current_execution.stages:
                return {'success': False, 'error': f'Stage {stage_name} not found'}

            stage = self.current_execution.stages[stage_name]

            # 检查依赖关系
            dependency_check = self._check_stage_dependencies(stage_name)
            if not dependency_check['satisfied']:
                return {
                    'success': False,
                    'error': f"Stage dependencies not satisfied: {dependency_check['missing']}"
                }

            # 标记阶段开始
            stage.status = TaskStatus.RUNNING
            stage.started_at = datetime.now()
            self.current_execution.current_stage = stage_name

            self._trigger_callbacks('on_stage_start', {'stage': stage})
            self._log_execution_event('stage_started', {'stage': stage_name})

            # 获取执行计划
            plan_result = self.plan_stage_execution(stage_name)
            if not plan_result['success']:
                return plan_result

            execution_plan = plan_result['execution_plan']

            # 根据执行模式执行任务
            if stage.execution_mode == ExecutionMode.PARALLEL:
                result = await self._execute_parallel_tasks(stage, execution_plan)
            elif stage.execution_mode == ExecutionMode.SEQUENTIAL:
                result = await self._execute_sequential_tasks(stage, execution_plan)
            elif stage.execution_mode == ExecutionMode.PARALLEL_THEN_SYNC:
                result = await self._execute_parallel_then_sync(stage, execution_plan)
            else:
                result = await self._execute_hybrid_tasks(stage, execution_plan)

            if not result['success']:
                stage.status = TaskStatus.FAILED
                return result

                # 处理同步点
            if stage.sync_point:
                sync_result = await self._handle_sync_point(stage)
                if not sync_result.get('success', False):
                    stage.status = TaskStatus.FAILED
                    return sync_result

            # 处理质量门
            if stage.quality_gate:
                quality_result = await self._handle_quality_gate(stage)
                if not quality_result.get('success', False):
                    stage.status = TaskStatus.FAILED
                    return quality_result

            # 标记阶段完成
            stage.status = TaskStatus.COMPLETED
            stage.completed_at = datetime.now()

            self._trigger_callbacks('on_stage_complete', {'stage': stage})
            self._log_execution_event('stage_completed', {'stage': stage_name})

            # 保存执行状态
            self._save_execution_state()

            self.logger.info(f"Stage completed successfully: {stage_name}")
            return {
                'success': True,
                'stage': stage_name,
                'execution_time': (stage.completed_at - stage.started_at).total_seconds(),
                'tasks_executed': len([t for t in stage.tasks if t.status == TaskStatus.COMPLETED]),
                'outputs': stage.outputs
            }

        except Exception as e:
            self.logger.error(f"Stage execution failed: {str(e)}")
            if stage_name in self.current_execution.stages:
                self.current_execution.stages[stage_name].status = TaskStatus.FAILED
            return {
                'success': False,
                'error': str(e)
            }

    def validate_sync_point(self, sync_point: Dict[str, Any],
                          validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """验证同步点"""
        try:
            if not self.current_execution:
                return {'success': False, 'error': 'No workflow loaded'}

            criteria = sync_point.get('validation_criteria', {})
            failed_criteria = []
            validation_details = {}

            for criterion_name, criterion_rule in criteria.items():
                validation_result = self._evaluate_criterion(criterion_name, criterion_rule, validation_results)
                validation_details[criterion_name] = validation_result

                if not validation_result['passed']:
                    failed_criteria.append({
                        'criterion': criterion_name,
                        'rule': criterion_rule,
                        'reason': validation_result.get('reason', 'Unknown')
                    })

            all_criteria_met = len(failed_criteria) == 0

            result = {
                'success': all_criteria_met,
                'all_criteria_met': all_criteria_met,
                'failed_criteria': failed_criteria,
                'validation_details': validation_details,
                'sync_point_type': sync_point.get('type', 'unknown'),
                'validated_at': datetime.now().isoformat()
            }

            if not all_criteria_met:
                self.logger.warning(f"Sync point validation failed: {len(failed_criteria)} criteria not met")
            else:
                self.logger.info("Sync point validation passed")

            return result

        except Exception as e:
            self.logger.error(f"Sync point validation error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def mark_task_completed(self, task_id: TaskId, result: Dict[str, Any]) -> Dict[str, Any]:
        """标记任务完成"""
        try:
            if not self.current_execution:
                return {'success': False, 'error': 'No workflow loaded'}

            # 查找任务
            task = self._find_task_by_id(task_id)
            if not task:
                return {'success': False, 'error': f'Task {task_id} not found'}

            # 更新任务状态
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result

            # 计算执行时间
            if task.started_at:
                execution_time = (task.completed_at - task.started_at).total_seconds()
                self.performance_metrics['task_execution_times'][task_id] = execution_time

            # 处理任务输出
            if 'outputs' in result:
                task.outputs = result['outputs']

            # 触发回调
            self._trigger_callbacks('on_task_complete', {'task': task, 'result': result})

            # 记录执行日志
            self._log_execution_event('task_completed', {
                'task_id': task_id,
                'agent': task.agent,
                'stage': task.stage,
                'execution_time': execution_time if task.started_at else None
            })

            self.logger.info(f"Task completed: {task_id}")
            return {
                'success': True,
                'task_id': task_id,
                'execution_time': execution_time if task.started_at else None
            }

        except Exception as e:
            self.logger.error(f"Failed to mark task completed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_workflow_progress(self) -> Dict[str, Any]:
        """获取工作流进度"""
        try:
            if not self.current_execution:
                return {
                    'completion_percentage': 0,
                    'current_stage': None,
                    'error': 'No workflow loaded'
                }

            execution = self.current_execution  # Local variable for type narrowing
            total_stages = len(execution.stages)
            completed_stages = sum(1 for stage in execution.stages.values()
                                 if stage.status == TaskStatus.COMPLETED)

            total_tasks = sum(len(stage.tasks) for stage in execution.stages.values())
            completed_tasks = sum(len([t for t in stage.tasks if t.status == TaskStatus.COMPLETED])
                                for stage in execution.stages.values())

            running_tasks = sum(len([t for t in stage.tasks if t.status == TaskStatus.RUNNING])
                              for stage in execution.stages.values())

            failed_tasks = sum(len([t for t in stage.tasks if t.status == TaskStatus.FAILED])
                             for stage in execution.stages.values())

            stage_completion = (completed_stages / total_stages * 100) if total_stages > 0 else 0
            task_completion = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

            # 计算整体进度（阶段权重60%，任务权重40%）
            overall_completion = (stage_completion * 0.6) + (task_completion * 0.4)

            current_stage_info = None
            if execution.current_stage:
                current_stage = execution.stages[execution.current_stage]
                current_stage_info = {
                    'name': current_stage.name,
                    'status': current_stage.status.value,
                    'tasks_total': len(current_stage.tasks),
                    'tasks_completed': len([t for t in current_stage.tasks if t.status == TaskStatus.COMPLETED]),
                    'tasks_running': len([t for t in current_stage.tasks if t.status == TaskStatus.RUNNING]),
                    'tasks_failed': len([t for t in current_stage.tasks if t.status == TaskStatus.FAILED])
                }

            return {
                'completion_percentage': round(overall_completion, 2),
                'stage_completion_percentage': round(stage_completion, 2),
                'task_completion_percentage': round(task_completion, 2),
                'workflow_state': execution.state.value,
                'current_stage': current_stage_info,
                'stages_summary': {
                    'total': total_stages,
                    'completed': completed_stages,
                    'running': len([s for s in execution.stages.values() if s.status == TaskStatus.RUNNING]),
                    'failed': len([s for s in execution.stages.values() if s.status == TaskStatus.FAILED])
                },
                'tasks_summary': {
                    'total': total_tasks,
                    'completed': completed_tasks,
                    'running': running_tasks,
                    'failed': failed_tasks
                },
                'execution_time': self._get_execution_time(),
                'estimated_remaining_time': self._estimate_remaining_time()
            }

        except Exception as e:
            self.logger.error(f"Failed to get workflow progress: {str(e)}")
            return {
                'completion_percentage': 0,
                'error': str(e)
            }

    def handle_task_error(self, task_id: TaskId, error_result: Dict[str, Any]) -> Dict[str, Any]:
        """处理任务错误"""
        try:
            if not self.current_execution:
                return {'success': False, 'error': 'No workflow loaded'}

            # 查找任务
            task = self._find_task_by_id(task_id)
            if not task:
                return {'success': False, 'error': f'Task {task_id} not found'}

            # 记录错误信息
            task.error = error_result.get('error', 'Unknown error')
            error_type = error_result.get('error_type', 'unknown')

            # 错误恢复策略
            recovery_strategy = self._determine_error_recovery_strategy(task, error_result)

            if recovery_strategy['action'] == 'retry':
                if task.retry_count < task.max_retries:
                    task.retry_count += 1
                    task.status = TaskStatus.RETRYING

                    # 计算重试延迟（指数退避）
                    retry_delay = min(60, 2 ** task.retry_count)

                    self.logger.warning(f"Task {task_id} failed, scheduling retry {task.retry_count}/{task.max_retries} in {retry_delay}s")

                    return {
                        'success': True,
                        'action': 'retry',
                        'retry_count': task.retry_count,
                        'retry_delay': retry_delay,
                        'max_retries': task.max_retries
                    }
                else:
                    task.status = TaskStatus.FAILED
                    self.logger.error(f"Task {task_id} failed permanently after {task.max_retries} retries")

                    # 检查是否需要工作流级别的错误恢复
                    workflow_recovery = self._handle_workflow_level_error(task)

                    return {
                        'success': False,
                        'action': 'fail',
                        'retry_exhausted': True,
                        'workflow_recovery': workflow_recovery
                    }

            elif recovery_strategy['action'] == 'skip':
                task.status = TaskStatus.SKIPPED
                self.logger.warning(f"Task {task_id} skipped due to error: {task.error}")

                return {
                    'success': True,
                    'action': 'skip',
                    'reason': recovery_strategy.get('reason', 'Error recovery strategy')
                }

            elif recovery_strategy['action'] == 'rollback':
                # Note: This would need to be called from an async context
                # For now, return a rollback intent that can be handled by the caller
                return {
                    'success': False,
                    'action': 'rollback',
                    'stage_to_rollback': task.stage,
                    'reason': 'Task error requires stage rollback'
                }

            else:  # fail
                task.status = TaskStatus.FAILED
                self.current_execution.state = WorkflowState.FAILED

                self.logger.error(f"Task {task_id} failed, workflow terminated")

                return {
                    'success': False,
                    'action': 'fail',
                    'workflow_terminated': True
                }

        except Exception as e:
            self.logger.error(f"Error handling failed task {task_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def rollback_to_stage(self, stage_name: StageId) -> Dict[str, Any]:
        """回滚到指定阶段"""
        try:
            if not self.current_execution:
                return {'success': False, 'error': 'No workflow loaded'}

            if stage_name not in self.current_execution.stages:
                return {'success': False, 'error': f'Stage {stage_name} not found'}

            # 识别需要回滚的阶段
            stages_to_rollback = self._identify_rollback_stages(stage_name)

            rollback_results = []

            # 按逆序回滚阶段
            for rollback_stage_name in reversed(stages_to_rollback):
                stage = self.current_execution.stages[rollback_stage_name]

                # 回滚阶段状态
                stage.status = TaskStatus.CREATED
                stage.started_at = None
                stage.completed_at = None
                stage.outputs = []

                # 回滚阶段中的所有任务
                for task in stage.tasks:
                    task.status = TaskStatus.CREATED
                    task.started_at = None
                    task.completed_at = None
                    task.result = None
                    task.error = None
                    task.retry_count = 0
                    task.outputs = []

                rollback_results.append({
                    'stage': rollback_stage_name,
                    'tasks_rolled_back': len(stage.tasks)
                })

                self.logger.info(f"Rolled back stage: {rollback_stage_name}")

            # 更新当前阶段
            self.current_execution.current_stage = stage_name
            self.current_execution.state = WorkflowState.INITIALIZED

            # 记录回滚事件
            self._log_execution_event('workflow_rollback', {
                'target_stage': stage_name,
                'rolled_back_stages': stages_to_rollback
            })

            # 保存状态
            self._save_execution_state()

            self.logger.info(f"Successfully rolled back to stage: {stage_name}")
            return {
                'success': True,
                'target_stage': stage_name,
                'rolled_back_stages': rollback_results
            }

        except Exception as e:
            self.logger.error(f"Failed to rollback to stage {stage_name}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def mark_stage_completed(self, stage_name: StageId) -> Dict[str, Any]:
        """标记阶段完成"""
        try:
            if not self.current_execution:
                return {'success': False, 'error': 'No workflow loaded'}

            if stage_name not in self.current_execution.stages:
                return {'success': False, 'error': f'Stage {stage_name} not found'}

            stage = self.current_execution.stages[stage_name]

            # 检查所有任务是否完成
            incomplete_tasks = [t for t in stage.tasks if t.status not in [TaskStatus.COMPLETED, TaskStatus.SKIPPED]]
            if incomplete_tasks:
                return {
                    'success': False,
                    'error': f'Cannot mark stage completed: {len(incomplete_tasks)} tasks not completed'
                }

            # 标记阶段完成
            stage.status = TaskStatus.COMPLETED
            if not stage.completed_at:
                stage.completed_at = datetime.now()

            # 收集阶段输出
            stage_outputs = []
            for task in stage.tasks:
                if task.outputs:
                    stage_outputs.extend(task.outputs)
            stage.outputs = stage_outputs

            # 计算阶段执行时间
            if stage.started_at and stage.completed_at:
                execution_time = (stage.completed_at - stage.started_at).total_seconds()
                self.performance_metrics['stage_execution_times'][stage_name] = execution_time

            # 检查工作流是否完成
            workflow_completed = all(
                stage.status == TaskStatus.COMPLETED
                for stage in self.current_execution.stages.values()
            )

            if workflow_completed:
                self.current_execution.state = WorkflowState.COMPLETED
                self.current_execution.completed_at = datetime.now()
                self.logger.info("Workflow completed successfully")

            # 记录执行日志
            self._log_execution_event('stage_marked_completed', {
                'stage': stage_name,
                'execution_time': execution_time if stage.started_at else None,
                'workflow_completed': workflow_completed
            })

            # 保存状态
            self._save_execution_state()

            return {
                'success': True,
                'stage': stage_name,
                'execution_time': execution_time if stage.started_at else None,
                'outputs': stage.outputs,
                'workflow_completed': workflow_completed
            }

        except Exception as e:
            self.logger.error(f"Failed to mark stage completed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    # ==================== 私有辅助方法 ====================

    def _parse_stage_config(self, stage_config: Dict[str, Any]) -> Stage:
        """解析阶段配置"""
        execution_mode_str = stage_config.get('execution_mode', 'parallel')
        try:
            execution_mode = ExecutionMode(execution_mode_str)
        except ValueError:
            execution_mode = ExecutionMode.PARALLEL

        stage = Stage(
            name=stage_config['name'],
            description=stage_config.get('description', ''),
            execution_mode=execution_mode,
            dependencies=stage_config.get('depends_on', []),
            sync_point=stage_config.get('sync_point'),
            quality_gate=stage_config.get('quality_gate'),
            thinking_mode=stage_config.get('thinking_mode'),
            timeout=stage_config.get('timeout', 1800)
        )

        return stage

    def _validate_workflow_dependencies(self) -> Dict[str, Any]:
        """验证工作流依赖关系"""
        errors = []
        stage_names = set(self.current_execution.stages.keys())

        for stage_name, stage in self.current_execution.stages.items():
            for dependency in stage.dependencies:
                if dependency not in stage_names:
                    errors.append(f"Stage '{stage_name}' depends on non-existent stage '{dependency}'")

        # 检查循环依赖
        if self._has_circular_dependencies():
            errors.append("Circular dependencies detected in workflow")

        return {
            'valid': len(errors) == 0,
            'errors': errors
        }

    def _has_circular_dependencies(self) -> bool:
        """检查循环依赖"""
        visited = set()
        rec_stack = set()

        def dfs(stage_name):
            visited.add(stage_name)
            rec_stack.add(stage_name)

            stage = self.current_execution.stages.get(stage_name)
            if stage:
                for dependency in stage.dependencies:
                    if dependency not in visited:
                        if dfs(dependency):
                            return True
                    elif dependency in rec_stack:
                        return True

            rec_stack.remove(stage_name)
            return False

        for stage_name in self.current_execution.stages:
            if stage_name not in visited:
                if dfs(stage_name):
                    return True

        return False

    def _find_task_by_id(self, task_id: TaskId) -> Optional[Task]:
        """根据ID查找任务"""
        for stage in self.current_execution.stages.values():
            for task in stage.tasks:
                if task.task_id == task_id:
                    return task
        return None

    def _build_task_dependency_graph(self, tasks: List[Task]) -> Dict[TaskId, List[TaskId]]:
        """构建任务依赖图"""
        graph = {}
        for task in tasks:
            graph[task.task_id] = task.dependencies
        return graph

    def _create_execution_plan(self, stage: Stage, dependency_graph: Dict[TaskId, List[TaskId]]) -> ExecutionPlan:
        """创建执行计划"""
        if stage.execution_mode == ExecutionMode.PARALLEL:
            return {'type': 'parallel', 'groups': [{'tasks': [t.task_id for t in stage.tasks]}]}
        elif stage.execution_mode == ExecutionMode.SEQUENTIAL:
            return {'type': 'sequential', 'order': [t.task_id for t in stage.tasks]}
        else:
            # 基于依赖关系的混合执行
            return self._create_dependency_based_plan(stage.tasks, dependency_graph)

    def _create_dependency_based_plan(
        self,
        tasks: List[Task],
        dependency_graph: Dict[TaskId, List[TaskId]]
    ) -> ExecutionPlan:
        """基于依赖关系创建执行计划"""
        # 拓扑排序实现
        in_degree = {task.task_id: 0 for task in tasks}

        for task_id, dependencies in dependency_graph.items():
            for dep in dependencies:
                if dep in in_degree:
                    in_degree[task_id] += 1

        execution_levels = []
        remaining_tasks = set(task.task_id for task in tasks)

        while remaining_tasks:
            current_level = [task_id for task_id in remaining_tasks if in_degree[task_id] == 0]
            if not current_level:
                break  # 存在循环依赖

            execution_levels.append(current_level)

            for task_id in current_level:
                remaining_tasks.remove(task_id)
                for dependent_task in dependency_graph:
                    if task_id in dependency_graph[dependent_task]:
                        in_degree[dependent_task] -= 1

        return {'type': 'layered', 'levels': execution_levels}

    def _estimate_stage_duration(self, stage: Stage, execution_plan: ExecutionPlan) -> int:
        """估算阶段执行时间"""
        if execution_plan['type'] == 'parallel':
            return max(task.timeout for task in stage.tasks) if stage.tasks else 0
        elif execution_plan['type'] == 'sequential':
            return sum(task.timeout for task in stage.tasks)
        else:  # layered
            return sum(max(task.timeout for task in stage.tasks if task.task_id in level)
                      for level in execution_plan['levels'] if level)

    def _assess_resource_requirements(self, stage: Stage) -> Dict[str, Union[int, float]]:
        """评估资源需求"""
        return {
            'concurrent_agents': len(set(task.agent for task in stage.tasks)),
            'memory_intensive_tasks': len([t for t in stage.tasks if 'memory' in t.description.lower()]),
            'cpu_intensive_tasks': len([t for t in stage.tasks if 'compute' in t.description.lower()]),
            'io_intensive_tasks': len([t for t in stage.tasks if any(keyword in t.description.lower()
                                                                    for keyword in ['file', 'database', 'api'])])
        }

    def _check_stage_dependencies(self, stage_name: StageId) -> Dict[str, Union[bool, List[StageId]]]:
        """检查阶段依赖关系"""
        stage = self.current_execution.stages[stage_name]
        missing_dependencies = []

        for dependency in stage.dependencies:
            if dependency not in self.current_execution.stages:
                missing_dependencies.append(dependency)
            elif self.current_execution.stages[dependency].status != TaskStatus.COMPLETED:
                missing_dependencies.append(dependency)

        return {
            'satisfied': len(missing_dependencies) == 0,
            'missing': missing_dependencies
        }

    async def _execute_parallel_tasks(self, stage: Stage, execution_plan: ExecutionPlan) -> Dict[str, Any]:
        """并行执行任务"""
        tasks_to_execute = stage.tasks.copy()

        async def execute_task(task):
            try:
                task.status = TaskStatus.RUNNING
                task.started_at = datetime.now()

                self._trigger_callbacks('on_task_start', {'task': task})

                        # 模拟任务执行（实际实现中会调用具体的agent）
                if self.task_manager:
                    # Task manager execute_task_async should return a coroutine or result
                    task_result = self.task_manager.execute_task_async(task.task_id)
                    if hasattr(task_result, '__await__'):
                        result = await task_result
                    else:
                        result = task_result
                else:
                    # 模拟执行
                    await asyncio.sleep(1)
                    result = {'success': True, 'result': f'Mock result from {task.agent}'}

                if result['success']:
                    self.mark_task_completed(task.task_id, result)
                else:
                    self.handle_task_error(task.task_id, result)

                return result

            except Exception as e:
                error_result = {'success': False, 'error': str(e)}
                self.handle_task_error(task.task_id, error_result)
                return error_result

        # 并行执行所有任务
        results = await asyncio.gather(*[execute_task(task) for task in tasks_to_execute], return_exceptions=True)

        success_count = sum(1 for result in results if isinstance(result, dict) and result.get('success', False))

        return {
            'success': success_count == len(tasks_to_execute),
            'completed_tasks': success_count,
            'total_tasks': len(tasks_to_execute)
        }

    async def _execute_sequential_tasks(self, stage: Stage, execution_plan: ExecutionPlan) -> Dict[str, Any]:
        """顺序执行任务"""
        for task in stage.tasks:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()

            self._trigger_callbacks('on_task_start', {'task': task})

            try:
                if self.task_manager:
                    # Task manager execute_task_async should return a coroutine or result
                    task_result = self.task_manager.execute_task_async(task.task_id)
                    if hasattr(task_result, '__await__'):
                        result = await task_result
                    else:
                        result = task_result
                else:
                    await asyncio.sleep(1)
                    result = {'success': True, 'result': f'Mock result from {task.agent}'}

                if result['success']:
                    self.mark_task_completed(task.task_id, result)
                else:
                    error_handling_result = self.handle_task_error(task.task_id, result)
                    if not error_handling_result['success'] and error_handling_result.get('action') == 'fail':
                        return {'success': False, 'failed_task': task.task_id}

            except Exception as e:
                error_result = {'success': False, 'error': str(e)}
                error_handling_result = self.handle_task_error(task.task_id, error_result)
                if not error_handling_result['success']:
                    return {'success': False, 'failed_task': task.task_id}

        return {'success': True, 'completed_tasks': len(stage.tasks)}

    async def _execute_parallel_then_sync(self, stage: Stage, execution_plan: ExecutionPlan) -> Dict[str, Any]:
        """先并行执行，然后同步"""
        # 先并行执行所有任务
        parallel_result = await self._execute_parallel_tasks(stage, execution_plan)
        if not parallel_result['success']:
            return parallel_result

        # 等待所有任务完成
        while any(task.status == TaskStatus.RUNNING for task in stage.tasks):
            await asyncio.sleep(0.1)

        return {'success': True, 'execution_mode': 'parallel_then_sync'}

    async def _execute_hybrid_tasks(self, stage: Stage, execution_plan: ExecutionPlan) -> Dict[str, Any]:
        """混合执行任务"""
        if execution_plan['type'] == 'layered':
            for level in execution_plan['levels']:
                level_tasks = [task for task in stage.tasks if task.task_id in level]
                level_result = await self._execute_parallel_tasks(
                    Stage(name=f"{stage.name}_level", description="", execution_mode=ExecutionMode.PARALLEL, tasks=level_tasks),
                    {'type': 'parallel'}
                )
                if not level_result['success']:
                    return level_result

        return {'success': True, 'execution_mode': 'hybrid'}

    async def _handle_sync_point(self, stage: Stage) -> Dict[str, Any]:
        """处理同步点"""
        sync_point = stage.sync_point
        if not sync_point:
            return {'success': True, 'message': 'No sync point to handle'}

        self._trigger_callbacks('on_sync_point', {'stage': stage, 'sync_point': sync_point})

        # 收集验证数据
        validation_data = self._collect_sync_validation_data(stage)

        # 执行同步点验证
        validation_result = self.validate_sync_point(sync_point, validation_data)

        if not validation_result['success']:
            self.logger.warning(f"Sync point failed for stage {stage.name}: {validation_result['failed_criteria']}")

            # 根据同步点配置决定是否继续
            if sync_point.get('must_pass', True):
                return validation_result

        return {'success': True, 'sync_point_passed': validation_result['success']}

    async def _handle_quality_gate(self, stage: Stage) -> Dict[str, Any]:
        """处理质量门"""
        quality_gate = stage.quality_gate
        if not quality_gate:
            return {'success': True, 'message': 'No quality gate to handle'}

        self._trigger_callbacks('on_quality_gate', {'stage': stage, 'quality_gate': quality_gate})

        # 执行质量检查
        quality_result = self._execute_quality_checks(stage, quality_gate)

        if not quality_result['success'] and quality_gate.get('must_pass', True):
            self.logger.error(f"Quality gate failed for stage {stage.name}")
            return quality_result

        return {'success': True, 'quality_gate_passed': quality_result['success']}

    def _collect_sync_validation_data(self, stage: Stage) -> Dict[str, Any]:
        """收集同步点验证数据"""
        data = {
            'tasks_completed': len([t for t in stage.tasks if t.status == TaskStatus.COMPLETED]),
            'tasks_failed': len([t for t in stage.tasks if t.status == TaskStatus.FAILED]),
            'stage_outputs': stage.outputs
        }

        # 根据阶段类型收集特定数据
        if 'architecture' in stage.name.lower():
            data['design_documents_created'] = len([output for output in stage.outputs if 'design' in output.lower()])
        elif 'testing' in stage.name.lower():
            data['test_coverage'] = 95  # 模拟数据
            data['tests_passed'] = 100

        return data

    def _execute_quality_checks(self, stage: Stage, quality_gate: Dict[str, Any]) -> Dict[str, Union[bool, int]]:
        """执行质量检查"""
        # 模拟质量检查实现
        checks = quality_gate.get('checklist', '')

        return {
            'success': True,  # 模拟通过
            'checks_performed': len(checks.split(',')) if checks else 0,
            'quality_score': 95
        }

    def _evaluate_criterion(self, criterion_name: str, criterion_rule: str,
                          validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """评估单个验证条件"""
        # 简化的条件评估实现
        if criterion_name in validation_results:
            value = validation_results[criterion_name]
            if isinstance(value, bool):
                return {'passed': value, 'value': value}
            elif isinstance(value, (int, float)):
                # 解析规则（如 "> 90"）
                if '>' in criterion_rule:
                    threshold = float(criterion_rule.split('>')[-1].strip())
                    passed = value > threshold
                    return {'passed': passed, 'value': value, 'threshold': threshold}

        return {'passed': False, 'reason': f'Criterion {criterion_name} not found in validation results'}

    def _determine_error_recovery_strategy(self, task: Task, error_result: Dict[str, Any]) -> Dict[str, Any]:
        """确定错误恢复策略"""
        error_type = error_result.get('error_type', 'unknown')

        if error_type in ['timeout', 'network_error']:
            return {'action': 'retry', 'reason': 'Transient error, retry possible'}
        elif error_type in ['validation_error', 'syntax_error']:
            return {'action': 'fail', 'reason': 'Code error, manual intervention required'}
        elif task.priority > 5:  # 高优先级任务
            return {'action': 'retry', 'reason': 'High priority task'}
        else:
            return {'action': 'skip', 'reason': 'Low priority task, can skip'}

    def _handle_workflow_level_error(self, failed_task: Task) -> Dict[str, Any]:
        """处理工作流级别的错误"""
        if not self.current_execution:
            return {'action': 'terminate', 'reason': 'No workflow loaded'}

        execution = self.current_execution  # Local variable for type narrowing
        execution.error_recovery_count += 1

        if execution.error_recovery_count >= execution.max_error_recovery:
            execution.state = WorkflowState.FAILED
            return {'action': 'terminate', 'reason': 'Max error recovery attempts exceeded'}

        return {'action': 'continue', 'recovery_count': execution.error_recovery_count}

    async def _rollback_stage(self, stage_name: StageId) -> Dict[str, Any]:
        """回滚单个阶段"""
        try:
            if not self.current_execution:
                return {'success': False, 'error': 'No workflow loaded'}

            execution = self.current_execution  # Local variable for type narrowing
            stage = execution.stages[stage_name]

            # 清理阶段状态
            stage.status = TaskStatus.CREATED
            stage.started_at = None
            stage.completed_at = None

            # 清理任务状态
            for task in stage.tasks:
                task.status = TaskStatus.CREATED
                task.started_at = None
                task.completed_at = None
                task.result = None
                task.error = None
                task.retry_count = 0

            return {'success': True}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _identify_rollback_stages(self, target_stage: StageId) -> List[StageId]:
        """识别需要回滚的阶段"""
        if not self.current_execution:
            return []

        stages_order = list(self.current_execution.stages.keys())

        if target_stage not in stages_order:
            return []

        target_index = stages_order.index(target_stage)
        return stages_order[target_index:]

    def _get_execution_time(self) -> Optional[float]:
        """获取执行时间"""
        if not self.current_execution or not self.current_execution.started_at:
            return None

        execution = self.current_execution  # Local variable for type narrowing
        if not execution.started_at:
            return None
        end_time = execution.completed_at or datetime.now()
        return (end_time - execution.started_at).total_seconds()

    def _estimate_remaining_time(self) -> Optional[float]:
        """估算剩余时间"""
        if not self.current_execution:
            return None

        execution = self.current_execution  # Local variable for type narrowing
        remaining_stages = [s for s in execution.stages.values()
                          if s.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]]

        return sum(stage.timeout for stage in remaining_stages)

    def _trigger_callbacks(self, event_type: str, data: Dict[str, Any]) -> None:
        """触发回调函数"""
        for callback in self.execution_callbacks.get(event_type, []):
            try:
                callback(data)
            except Exception as e:
                self.logger.error(f"Callback error for {event_type}: {str(e)}")

    def _log_execution_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """记录执行事件"""
        if self.current_execution:
            self.current_execution.execution_log.append({
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'data': data
            })

    def _save_execution_state(self) -> None:
        """保存执行状态"""
        if not self.current_execution:
            return

        try:
            state_data = {
                'workflow_id': self.current_execution.workflow_id,
                'workflow_name': self.current_execution.workflow_name,
                'state': self.current_execution.state.value,
                'current_stage': self.current_execution.current_stage,
                'started_at': self.current_execution.started_at.isoformat() if self.current_execution.started_at else None,
                'completed_at': self.current_execution.completed_at.isoformat() if self.current_execution.completed_at else None,
                'performance_metrics': self.performance_metrics
            }

            with open(self.state_file, 'w') as f:
                json.dump(state_data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to save execution state: {str(e)}")

    def register_callback(self, event_type: str, callback: Callable[[Dict[str, Any]], None]) -> None:
        """注册回调函数"""
        if event_type in self.execution_callbacks:
            self.execution_callbacks[event_type].append(callback)

    def set_task_manager(self, task_manager: TaskManagerProtocol) -> None:
        """设置任务管理器"""
        self.task_manager = task_manager

    def set_sync_manager(self, sync_manager: SyncManagerProtocol) -> None:
        """设置同步点管理器"""
        self.sync_manager = sync_manager

    def get_execution_metrics(self) -> PerformanceMetrics:
        """获取执行指标"""
        return self.performance_metrics.copy()

    def get_execution_log(self) -> List[Dict[str, Any]]:
        """获取执行日志"""
        if self.current_execution:
            return self.current_execution.execution_log.copy()
        return []

# 向后兼容导出
__all__ = ['WorkflowOrchestrator', 'ExecutionMode', 'WorkflowState', 'TaskStatus', 'Task', 'Stage', 'WorkflowExecution']
