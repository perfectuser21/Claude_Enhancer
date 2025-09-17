#!/usr/bin/env python3
"""
Perfect21工作流执行引擎
实现真正的多Agent并行协作和工作流管理
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger("WorkflowEngine")

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ExecutionMode(Enum):
    """执行模式枚举"""
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    DEPENDENCY_GRAPH = "dependency_graph"
    CONDITIONAL = "conditional"

@dataclass
class AgentTask:
    """Agent任务数据类"""
    task_id: str
    agent_name: str
    description: str
    prompt: str
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    dependencies: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

@dataclass
class WorkflowResult:
    """工作流执行结果"""
    workflow_id: str
    status: TaskStatus
    tasks: List[AgentTask]
    execution_time: float
    success_count: int
    failure_count: int
    integrated_result: Optional[Dict[str, Any]] = None

class WorkflowEngine:
    """Perfect21工作流执行引擎"""

    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.active_workflows: Dict[str, WorkflowResult] = {}
        self.execution_history: List[WorkflowResult] = []

        logger.info(f"WorkflowEngine初始化完成 - 最大并发: {max_workers}")

    def execute_parallel_tasks(self, tasks: List[Dict[str, Any]],
                             workflow_id: str = None) -> WorkflowResult:
        """
        并行执行多个agent任务

        Args:
            tasks: 任务列表，每个任务包含 agent_name, description, prompt
            workflow_id: 工作流ID，可选

        Returns:
            WorkflowResult: 工作流执行结果
        """
        if not workflow_id:
            workflow_id = f"parallel_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"开始并行执行工作流: {workflow_id}, 任务数: {len(tasks)}")

        # 创建AgentTask列表
        agent_tasks = []
        for i, task_data in enumerate(tasks):
            task = AgentTask(
                task_id=f"{workflow_id}_task_{i+1}",
                agent_name=task_data.get('agent_name'),
                description=task_data.get('description'),
                prompt=task_data.get('prompt')
            )
            agent_tasks.append(task)

        # 创建工作流结果
        workflow_result = WorkflowResult(
            workflow_id=workflow_id,
            status=TaskStatus.RUNNING,
            tasks=agent_tasks,
            execution_time=0.0,
            success_count=0,
            failure_count=0
        )

        self.active_workflows[workflow_id] = workflow_result
        start_time = datetime.now()

        try:
            # 使用线程池并行执行任务
            with ThreadPoolExecutor(max_workers=min(len(tasks), self.max_workers)) as executor:
                # 提交所有任务
                future_to_task = {}
                for task in agent_tasks:
                    future = executor.submit(self._execute_single_task, task)
                    future_to_task[future] = task

                # 收集结果
                for future in as_completed(future_to_task):
                    task = future_to_task[future]
                    try:
                        result = future.result()
                        task.status = TaskStatus.COMPLETED
                        task.result = result
                        workflow_result.success_count += 1
                        logger.info(f"任务完成: {task.task_id} ({task.agent_name})")
                    except Exception as e:
                        task.status = TaskStatus.FAILED
                        task.error = str(e)
                        workflow_result.failure_count += 1
                        logger.error(f"任务失败: {task.task_id} ({task.agent_name}) - {e}")

        except Exception as e:
            logger.error(f"工作流执行异常: {workflow_id} - {e}")
            workflow_result.status = TaskStatus.FAILED
        else:
            workflow_result.status = TaskStatus.COMPLETED if workflow_result.failure_count == 0 else TaskStatus.FAILED

        # 计算执行时间
        end_time = datetime.now()
        workflow_result.execution_time = (end_time - start_time).total_seconds()

        # 整合结果
        workflow_result.integrated_result = self._integrate_results(agent_tasks)

        # 移动到历史记录
        self.execution_history.append(workflow_result)
        if workflow_id in self.active_workflows:
            del self.active_workflows[workflow_id]

        logger.info(f"工作流执行完成: {workflow_id} - 成功:{workflow_result.success_count} 失败:{workflow_result.failure_count}")
        return workflow_result

    def execute_sequential_pipeline(self, pipeline: List[Dict[str, Any]],
                                  workflow_id: str = None) -> WorkflowResult:
        """
        顺序执行任务管道

        Args:
            pipeline: 任务管道，按顺序执行
            workflow_id: 工作流ID

        Returns:
            WorkflowResult: 执行结果
        """
        if not workflow_id:
            workflow_id = f"sequential_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"开始顺序执行工作流: {workflow_id}, 阶段数: {len(pipeline)}")

        agent_tasks = []
        for i, stage_data in enumerate(pipeline):
            task = AgentTask(
                task_id=f"{workflow_id}_stage_{i+1}",
                agent_name=stage_data.get('agent_name'),
                description=stage_data.get('description'),
                prompt=stage_data.get('prompt')
            )
            agent_tasks.append(task)

        workflow_result = WorkflowResult(
            workflow_id=workflow_id,
            status=TaskStatus.RUNNING,
            tasks=agent_tasks,
            execution_time=0.0,
            success_count=0,
            failure_count=0
        )

        self.active_workflows[workflow_id] = workflow_result
        start_time = datetime.now()

        # 顺序执行每个阶段
        previous_result = None
        for task in agent_tasks:
            try:
                # 将前一个任务的结果作为上下文传递
                if previous_result:
                    task.prompt += f"\n\n## 前一阶段结果:\n{json.dumps(previous_result, indent=2, ensure_ascii=False)}"

                task.start_time = datetime.now()
                task.status = TaskStatus.RUNNING

                result = self._execute_single_task(task)

                task.end_time = datetime.now()
                task.status = TaskStatus.COMPLETED
                task.result = result
                previous_result = result
                workflow_result.success_count += 1

                logger.info(f"阶段完成: {task.task_id} ({task.agent_name})")

            except Exception as e:
                task.end_time = datetime.now()
                task.status = TaskStatus.FAILED
                task.error = str(e)
                workflow_result.failure_count += 1
                logger.error(f"阶段失败: {task.task_id} ({task.agent_name}) - {e}")
                # 顺序执行中，如果一个阶段失败，停止后续执行
                break

        # 完成工作流
        end_time = datetime.now()
        workflow_result.execution_time = (end_time - start_time).total_seconds()
        workflow_result.status = TaskStatus.COMPLETED if workflow_result.failure_count == 0 else TaskStatus.FAILED
        workflow_result.integrated_result = self._integrate_results(agent_tasks)

        # 移动到历史记录
        self.execution_history.append(workflow_result)
        if workflow_id in self.active_workflows:
            del self.active_workflows[workflow_id]

        logger.info(f"顺序工作流完成: {workflow_id}")
        return workflow_result

    def handle_dependencies(self, task_graph: Dict[str, Dict[str, Any]]) -> WorkflowResult:
        """
        处理任务依赖关系的执行

        Args:
            task_graph: 任务依赖图

        Returns:
            WorkflowResult: 执行结果
        """
        workflow_id = f"dependency_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"开始依赖图执行: {workflow_id}")

        # 实现依赖图的拓扑排序和执行
        # 这里简化实现，实际可以使用更复杂的依赖解析算法
        return self._execute_dependency_graph(task_graph, workflow_id)

    def _execute_single_task(self, task: AgentTask) -> Dict[str, Any]:
        """
        执行单个Agent任务（模拟）

        在实际实现中，这里应该调用Task工具
        """
        logger.info(f"执行任务: {task.task_id} - {task.agent_name}")

        # 模拟任务执行
        import time
        time.sleep(1)  # 模拟执行时间

        # 模拟返回结果
        return {
            "agent": task.agent_name,
            "task_id": task.task_id,
            "status": "completed",
            "message": f"Task {task.description} completed successfully",
            "timestamp": datetime.now().isoformat()
        }

    def _integrate_results(self, tasks: List[AgentTask]) -> Dict[str, Any]:
        """整合多个任务的结果"""
        integrated = {
            "summary": f"集成了{len(tasks)}个Agent任务的结果",
            "agents_involved": [task.agent_name for task in tasks],
            "successful_tasks": [task.task_id for task in tasks if task.status == TaskStatus.COMPLETED],
            "failed_tasks": [task.task_id for task in tasks if task.status == TaskStatus.FAILED],
            "results": {}
        }

        for task in tasks:
            if task.result:
                integrated["results"][task.task_id] = task.result

        return integrated

    def _execute_dependency_graph(self, task_graph: Dict[str, Dict[str, Any]],
                                workflow_id: str) -> WorkflowResult:
        """执行依赖图（简化实现）"""
        # 简化实现：按照依赖关系顺序执行
        # 实际应该实现完整的拓扑排序

        tasks = []
        for task_id, task_data in task_graph.items():
            task = AgentTask(
                task_id=task_id,
                agent_name=task_data.get('agent_name'),
                description=task_data.get('description'),
                prompt=task_data.get('prompt'),
                dependencies=task_data.get('dependencies', [])
            )
            tasks.append(task)

        # 按依赖关系排序（简化实现）
        sorted_tasks = self._topological_sort(tasks)

        # 创建管道执行
        pipeline = []
        for task in sorted_tasks:
            pipeline.append({
                'agent_name': task.agent_name,
                'description': task.description,
                'prompt': task.prompt
            })

        return self.execute_sequential_pipeline(pipeline, workflow_id)

    def _topological_sort(self, tasks: List[AgentTask]) -> List[AgentTask]:
        """简化的拓扑排序实现"""
        # 简化实现：按依赖数量排序
        return sorted(tasks, key=lambda t: len(t.dependencies))

    def get_execution_status(self, workflow_id: str) -> Optional[WorkflowResult]:
        """获取工作流执行状态"""
        return self.active_workflows.get(workflow_id)

    def get_execution_history(self, limit: int = 10) -> List[WorkflowResult]:
        """获取执行历史"""
        return self.execution_history[-limit:]

    def monitor_execution(self, workflow_id: str) -> Dict[str, Any]:
        """监控工作流执行"""
        workflow = self.get_execution_status(workflow_id)
        if not workflow:
            return {"error": f"工作流 {workflow_id} 不存在或已完成"}

        status_summary = {
            "workflow_id": workflow_id,
            "status": workflow.status.value,
            "progress": {
                "completed": workflow.success_count,
                "failed": workflow.failure_count,
                "total": len(workflow.tasks)
            },
            "tasks": []
        }

        for task in workflow.tasks:
            task_info = {
                "task_id": task.task_id,
                "agent": task.agent_name,
                "status": task.status.value,
                "description": task.description
            }
            status_summary["tasks"].append(task_info)

        return status_summary