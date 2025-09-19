#!/usr/bin/env python3
"""
Perfect21 Workflow Optimization Engine
移除人工延迟、启用真正的并行执行、智能上下文管理
"""

import asyncio
import logging
import threading
import time
from typing import Dict, List, Any, Optional, Callable, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import concurrent.futures
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class ExecutionMode(Enum):
    """执行模式"""
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    HYBRID = "hybrid"
    ADAPTIVE = "adaptive"

class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING = "waiting"  # 等待依赖

class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class OptimizedTask:
    """优化任务定义"""
    task_id: str
    agent_name: str
    description: str
    prompt: str
    priority: TaskPriority = TaskPriority.NORMAL
    dependencies: List[str] = field(default_factory=list)
    timeout: float = 300.0  # 默认5分钟超时
    retry_count: int = 2
    context_requirements: List[str] = field(default_factory=list)  # 需要的上下文artifact IDs

    # 状态信息
    status: TaskStatus = TaskStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    attempt: int = 0
    context_data: Optional[Dict[str, Any]] = None
    execution_metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WorkflowOptimizationResult:
    """工作流优化结果"""
    workflow_id: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    total_execution_time: float
    parallel_efficiency: float  # 并行效率 0-1
    context_usage: Dict[str, Any]
    performance_metrics: Dict[str, float]
    optimization_suggestions: List[str]

class ContextOptimizer:
    """上下文优化器"""

    def __init__(self, artifact_manager):
        self.artifact_manager = artifact_manager
        self.context_cache = {}
        self.context_usage_stats = {}

    def prepare_context(self, task: OptimizedTask) -> Optional[str]:
        """为任务准备优化的上下文"""
        try:
            if not task.context_requirements:
                return None

            # 检查缓存
            cache_key = "_".join(sorted(task.context_requirements))
            if cache_key in self.context_cache:
                self.context_usage_stats[cache_key] = self.context_usage_stats.get(cache_key, 0) + 1
                return self.context_cache[cache_key]

            # 从artifact manager获取上下文
            context = self.artifact_manager.create_context_from_artifacts(
                task.context_requirements,
                max_context_size=6000  # 留出空间给任务本身的prompt
            )

            # 缓存上下文
            self.context_cache[cache_key] = context
            self.context_usage_stats[cache_key] = 1

            return context

        except Exception as e:
            logger.error(f"上下文准备失败 {task.task_id}: {e}")
            return None

    def optimize_context_for_batch(self, tasks: List[OptimizedTask]) -> Dict[str, str]:
        """为批量任务优化上下文"""
        # 找出共同的上下文需求
        common_contexts = {}
        all_requirements = set()

        for task in tasks:
            all_requirements.update(task.context_requirements)

        # 预加载所有需要的contexts
        context_map = {}
        for task in tasks:
            if task.context_requirements:
                context = self.prepare_context(task)
                if context:
                    context_map[task.task_id] = context

        return context_map

    def get_context_statistics(self) -> Dict[str, Any]:
        """获取上下文使用统计"""
        return {
            'cached_contexts': len(self.context_cache),
            'usage_stats': dict(self.context_usage_stats),
            'total_usage': sum(self.context_usage_stats.values())
        }


class ParallelExecutor:
    """真正的并行执行器"""

    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.active_tasks = {}
        self.completed_tasks = {}
        self.failed_tasks = {}

    def execute_tasks_parallel(self, tasks: List[OptimizedTask],
                              context_map: Dict[str, str] = None) -> Dict[str, Any]:
        """真正的并行执行，无人工延迟"""
        context_map = context_map or {}
        futures = {}
        start_time = time.time()

        try:
            # 提交所有任务
            for task in tasks:
                if task.status == TaskStatus.PENDING:
                    # 准备任务上下文
                    task.context_data = {
                        'context': context_map.get(task.task_id),
                        'start_time': datetime.now()
                    }

                    # 提交任务到线程池
                    future = self.executor.submit(self._execute_single_task, task)
                    futures[future] = task
                    task.status = TaskStatus.RUNNING
                    task.start_time = datetime.now()
                    self.active_tasks[task.task_id] = task

            # 等待所有任务完成
            completed_count = 0
            failed_count = 0

            for future in concurrent.futures.as_completed(futures, timeout=600):
                task = futures[future]
                try:
                    result = future.result()
                    task.result = result
                    task.status = TaskStatus.COMPLETED
                    task.end_time = datetime.now()
                    completed_count += 1
                    self.completed_tasks[task.task_id] = task
                    logger.info(f"任务完成: {task.task_id} ({task.agent_name})")

                except Exception as e:
                    task.error = str(e)
                    task.status = TaskStatus.FAILED
                    task.end_time = datetime.now()
                    failed_count += 1
                    self.failed_tasks[task.task_id] = task
                    logger.error(f"任务失败: {task.task_id} - {e}")

                finally:
                    if task.task_id in self.active_tasks:
                        del self.active_tasks[task.task_id]

            end_time = time.time()
            total_time = end_time - start_time

            # 计算并行效率
            if tasks:
                # 理论顺序时间 vs 实际并行时间
                avg_task_time = total_time / min(len(tasks), self.max_workers)
                theoretical_sequential_time = avg_task_time * len(tasks)
                parallel_efficiency = min(theoretical_sequential_time / total_time, 1.0) if total_time > 0 else 1.0
            else:
                parallel_efficiency = 1.0

            return {
                'success': True,
                'total_tasks': len(tasks),
                'completed': completed_count,
                'failed': failed_count,
                'execution_time': total_time,
                'parallel_efficiency': parallel_efficiency,
                'active_tasks': len(self.active_tasks)
            }

        except Exception as e:
            logger.error(f"并行执行失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'execution_time': time.time() - start_time
            }

    def _execute_single_task(self, task: OptimizedTask) -> Any:
        """执行单个任务（模拟调用Claude Code Agent）"""
        try:
            # 在真实场景中，这里会调用实际的Claude Code API
            # 目前使用模拟执行来演示优化效果

            # 准备完整的prompt
            full_prompt = task.prompt
            if task.context_data and task.context_data.get('context'):
                full_prompt = f"""上下文信息:
{task.context_data['context']}

任务要求:
{task.prompt}"""

            # 模拟Agent执行时间（基于任务复杂度）
            complexity_factor = len(task.prompt) / 100
            base_time = max(0.5, min(complexity_factor, 5.0))  # 0.5-5秒之间

            # 添加随机性模拟真实场景
            import random
            execution_time = base_time * (0.8 + random.random() * 0.4)

            time.sleep(execution_time)

            # 模拟成功结果
            mock_result = {
                'agent': task.agent_name,
                'task_id': task.task_id,
                'status': 'completed',
                'execution_time': execution_time,
                'result': f"{task.agent_name} 已完成任务: {task.description}",
                'metadata': {
                    'prompt_length': len(full_prompt),
                    'context_used': bool(task.context_data and task.context_data.get('context')),
                    'timestamp': datetime.now().isoformat()
                }
            }

            # 记录执行元数据
            task.execution_metadata = {
                'actual_execution_time': execution_time,
                'prompt_length': len(full_prompt),
                'attempt': task.attempt + 1
            }

            return mock_result

        except Exception as e:
            task.attempt += 1
            if task.attempt < task.retry_count:
                logger.warning(f"任务 {task.task_id} 重试 {task.attempt}/{task.retry_count}")
                return self._execute_single_task(task)
            else:
                raise e

    def get_execution_statistics(self) -> Dict[str, Any]:
        """获取执行统计"""
        return {
            'max_workers': self.max_workers,
            'active_tasks': len(self.active_tasks),
            'completed_tasks': len(self.completed_tasks),
            'failed_tasks': len(self.failed_tasks),
            'executor_info': {
                'threads': self.executor._threads if hasattr(self.executor, '_threads') else 'N/A',
                'queue_size': self.executor._work_queue.qsize() if hasattr(self.executor, '_work_queue') else 0
            }
        }


class DependencyResolver:
    """依赖关系解析器"""

    def __init__(self):
        self.dependency_graph = {}

    def build_dependency_graph(self, tasks: List[OptimizedTask]) -> Dict[str, List[str]]:
        """构建依赖图"""
        graph = {}
        for task in tasks:
            graph[task.task_id] = task.dependencies.copy()

        self.dependency_graph = graph
        return graph

    def get_execution_order(self, tasks: List[OptimizedTask]) -> List[List[str]]:
        """获取执行顺序（拓扑排序）"""
        graph = self.build_dependency_graph(tasks)

        # 计算入度
        in_degree = {task_id: 0 for task_id in graph}
        for task_id, deps in graph.items():
            for dep in deps:
                if dep in in_degree:
                    in_degree[task_id] += 1

        # 执行层次
        execution_levels = []
        remaining_tasks = set(graph.keys())

        while remaining_tasks:
            # 找到当前可以执行的任务（入度为0）
            current_level = []
            for task_id in remaining_tasks:
                if in_degree[task_id] == 0:
                    current_level.append(task_id)

            if not current_level:
                # 出现循环依赖
                logger.warning(f"检测到循环依赖，剩余任务: {remaining_tasks}")
                current_level = list(remaining_tasks)  # 强制执行剩余任务

            execution_levels.append(current_level)

            # 更新入度
            for completed_task in current_level:
                remaining_tasks.remove(completed_task)
                for task_id in remaining_tasks:
                    if completed_task in graph[task_id]:
                        in_degree[task_id] -= 1

        return execution_levels

    def validate_dependencies(self, tasks: List[OptimizedTask]) -> List[str]:
        """验证依赖关系，返回问题列表"""
        issues = []
        task_ids = {task.task_id for task in tasks}

        for task in tasks:
            for dep in task.dependencies:
                if dep not in task_ids:
                    issues.append(f"任务 {task.task_id} 依赖不存在的任务 {dep}")

        # 检查循环依赖
        if self._has_cycle(tasks):
            issues.append("存在循环依赖")

        return issues

    def _has_cycle(self, tasks: List[OptimizedTask]) -> bool:
        """检查是否存在循环依赖"""
        graph = self.build_dependency_graph(tasks)
        visited = set()
        rec_stack = set()

        def dfs(node):
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for task_id in graph:
            if task_id not in visited:
                if dfs(task_id):
                    return True

        return False


class WorkflowOptimizer:
    """工作流优化引擎主类"""

    def __init__(self, artifact_manager=None, max_workers: int = 10):
        self.artifact_manager = artifact_manager
        self.context_optimizer = ContextOptimizer(artifact_manager) if artifact_manager else None
        self.parallel_executor = ParallelExecutor(max_workers)
        self.dependency_resolver = DependencyResolver()

        # 性能监控
        self.execution_history = []
        self.performance_metrics = {}

        logger.info(f"工作流优化引擎初始化完成，最大工作线程: {max_workers}")

    def optimize_and_execute(self, tasks: List[OptimizedTask],
                           execution_mode: ExecutionMode = ExecutionMode.ADAPTIVE) -> WorkflowOptimizationResult:
        """
        优化并执行工作流

        Args:
            tasks: 任务列表
            execution_mode: 执行模式

        Returns:
            WorkflowOptimizationResult: 优化执行结果
        """
        workflow_id = f"workflow_{int(time.time())}"
        start_time = time.time()

        try:
            # 1. 验证依赖关系
            dependency_issues = self.dependency_resolver.validate_dependencies(tasks)
            if dependency_issues:
                logger.warning(f"依赖关系问题: {dependency_issues}")

            # 2. 决定最优执行模式
            optimal_mode = self._determine_optimal_execution_mode(tasks, execution_mode)

            # 3. 准备上下文
            context_map = {}
            if self.context_optimizer:
                context_map = self.context_optimizer.optimize_context_for_batch(tasks)

            # 4. 执行工作流
            execution_result = self._execute_optimized_workflow(tasks, optimal_mode, context_map)

            # 5. 生成优化结果
            end_time = time.time()
            total_execution_time = end_time - start_time

            result = WorkflowOptimizationResult(
                workflow_id=workflow_id,
                total_tasks=len(tasks),
                completed_tasks=execution_result.get('completed', 0),
                failed_tasks=execution_result.get('failed', 0),
                total_execution_time=total_execution_time,
                parallel_efficiency=execution_result.get('parallel_efficiency', 0.0),
                context_usage=self.context_optimizer.get_context_statistics() if self.context_optimizer else {},
                performance_metrics=self._calculate_performance_metrics(tasks, execution_result),
                optimization_suggestions=self._generate_optimization_suggestions(tasks, execution_result)
            )

            # 6. 记录执行历史
            self._record_execution(result)

            logger.info(f"工作流优化完成: {workflow_id}, 效率: {result.parallel_efficiency:.2%}")
            return result

        except Exception as e:
            logger.error(f"工作流优化执行失败: {e}")
            return WorkflowOptimizationResult(
                workflow_id=workflow_id,
                total_tasks=len(tasks),
                completed_tasks=0,
                failed_tasks=len(tasks),
                total_execution_time=time.time() - start_time,
                parallel_efficiency=0.0,
                context_usage={},
                performance_metrics={},
                optimization_suggestions=[f"执行失败: {str(e)}"]
            )

    def _determine_optimal_execution_mode(self, tasks: List[OptimizedTask],
                                        requested_mode: ExecutionMode) -> ExecutionMode:
        """确定最优执行模式"""
        if requested_mode != ExecutionMode.ADAPTIVE:
            return requested_mode

        # 自适应模式决策逻辑
        has_dependencies = any(task.dependencies for task in tasks)
        task_count = len(tasks)

        if has_dependencies:
            if task_count > 5:
                return ExecutionMode.HYBRID  # 混合模式处理复杂依赖
            else:
                return ExecutionMode.SEQUENTIAL
        else:
            if task_count >= 3:
                return ExecutionMode.PARALLEL  # 并行处理独立任务
            else:
                return ExecutionMode.SEQUENTIAL  # 少量任务顺序处理

    def _execute_optimized_workflow(self, tasks: List[OptimizedTask],
                                  mode: ExecutionMode,
                                  context_map: Dict[str, str]) -> Dict[str, Any]:
        """执行优化的工作流"""
        if mode == ExecutionMode.PARALLEL:
            return self.parallel_executor.execute_tasks_parallel(tasks, context_map)

        elif mode == ExecutionMode.SEQUENTIAL:
            return self._execute_sequential(tasks, context_map)

        elif mode == ExecutionMode.HYBRID:
            return self._execute_hybrid(tasks, context_map)

        else:
            # 默认并行执行
            return self.parallel_executor.execute_tasks_parallel(tasks, context_map)

    def _execute_sequential(self, tasks: List[OptimizedTask],
                          context_map: Dict[str, str]) -> Dict[str, Any]:
        """顺序执行"""
        start_time = time.time()
        completed = 0
        failed = 0

        for task in tasks:
            try:
                result = self.parallel_executor._execute_single_task(task)
                task.result = result
                task.status = TaskStatus.COMPLETED
                completed += 1
            except Exception as e:
                task.error = str(e)
                task.status = TaskStatus.FAILED
                failed += 1
                logger.error(f"顺序任务失败: {task.task_id} - {e}")

        execution_time = time.time() - start_time

        return {
            'success': True,
            'total_tasks': len(tasks),
            'completed': completed,
            'failed': failed,
            'execution_time': execution_time,
            'parallel_efficiency': 1.0 / len(tasks) if tasks else 1.0  # 顺序执行的效率
        }

    def _execute_hybrid(self, tasks: List[OptimizedTask],
                       context_map: Dict[str, str]) -> Dict[str, Any]:
        """混合执行（考虑依赖关系）"""
        start_time = time.time()
        execution_levels = self.dependency_resolver.get_execution_order(tasks)

        total_completed = 0
        total_failed = 0
        task_map = {task.task_id: task for task in tasks}

        for level_tasks_ids in execution_levels:
            level_tasks = [task_map[task_id] for task_id in level_tasks_ids if task_id in task_map]

            if not level_tasks:
                continue

            # 每个level内部并行执行
            level_result = self.parallel_executor.execute_tasks_parallel(level_tasks, context_map)
            total_completed += level_result.get('completed', 0)
            total_failed += level_result.get('failed', 0)

        execution_time = time.time() - start_time

        return {
            'success': True,
            'total_tasks': len(tasks),
            'completed': total_completed,
            'failed': total_failed,
            'execution_time': execution_time,
            'parallel_efficiency': self._calculate_hybrid_efficiency(execution_levels, execution_time)
        }

    def _calculate_hybrid_efficiency(self, execution_levels: List[List[str]], total_time: float) -> float:
        """计算混合模式的并行效率"""
        if not execution_levels or total_time <= 0:
            return 1.0

        total_tasks = sum(len(level) for level in execution_levels)
        levels_count = len(execution_levels)

        # 估算效率：考虑并行度和依赖层次
        avg_parallel_tasks = total_tasks / levels_count
        max_theoretical_parallel = min(avg_parallel_tasks, self.parallel_executor.max_workers)
        efficiency = max_theoretical_parallel / total_tasks if total_tasks > 0 else 1.0

        return min(efficiency, 1.0)

    def _calculate_performance_metrics(self, tasks: List[OptimizedTask],
                                     execution_result: Dict[str, Any]) -> Dict[str, float]:
        """计算性能指标"""
        metrics = {}

        if tasks:
            # 任务完成率
            completed = execution_result.get('completed', 0)
            total = len(tasks)
            metrics['success_rate'] = completed / total if total > 0 else 0

            # 平均执行时间
            completed_tasks = [task for task in tasks if task.status == TaskStatus.COMPLETED]
            if completed_tasks:
                avg_task_time = sum(
                    task.execution_metadata.get('actual_execution_time', 0)
                    for task in completed_tasks
                ) / len(completed_tasks)
                metrics['avg_task_execution_time'] = avg_task_time

            # 总执行时间
            metrics['total_execution_time'] = execution_result.get('execution_time', 0)

            # 并行效率
            metrics['parallel_efficiency'] = execution_result.get('parallel_efficiency', 0)

            # 上下文使用率
            context_used_count = sum(
                1 for task in tasks
                if task.context_data and task.context_data.get('context')
            )
            metrics['context_usage_rate'] = context_used_count / total if total > 0 else 0

        return metrics

    def _generate_optimization_suggestions(self, tasks: List[OptimizedTask],
                                         execution_result: Dict[str, Any]) -> List[str]:
        """生成优化建议"""
        suggestions = []

        # 基于成功率的建议
        success_rate = execution_result.get('completed', 0) / len(tasks) if tasks else 0
        if success_rate < 0.8:
            suggestions.append("任务成功率较低，建议检查任务定义和依赖关系")

        # 基于并行效率的建议
        parallel_efficiency = execution_result.get('parallel_efficiency', 0)
        if parallel_efficiency < 0.5:
            suggestions.append("并行效率较低，建议减少任务间依赖或增加并行工作线程")

        # 基于执行时间的建议
        execution_time = execution_result.get('execution_time', 0)
        if execution_time > 600:  # 超过10分钟
            suggestions.append("执行时间较长，建议拆分大任务或优化任务逻辑")

        # 基于上下文使用的建议
        if self.context_optimizer:
            context_stats = self.context_optimizer.get_context_statistics()
            if context_stats.get('cached_contexts', 0) > 50:
                suggestions.append("上下文缓存较多，建议定期清理过期缓存")

        # 基于失败任务的建议
        failed_count = execution_result.get('failed', 0)
        if failed_count > 0:
            suggestions.append(f"有{failed_count}个任务失败，建议检查错误日志和重试策略")

        # 基于任务数量的建议
        task_count = len(tasks)
        if task_count > 20:
            suggestions.append("任务数量较多，建议分批执行或使用混合执行模式")

        if not suggestions:
            suggestions.append("工作流执行良好，无特殊优化建议")

        return suggestions

    def _record_execution(self, result: WorkflowOptimizationResult):
        """记录执行历史"""
        self.execution_history.append(result)

        # 限制历史记录数量
        if len(self.execution_history) > 100:
            self.execution_history = self.execution_history[-50:]

        # 更新性能指标
        self.performance_metrics = {
            'avg_parallel_efficiency': sum(
                r.parallel_efficiency for r in self.execution_history
            ) / len(self.execution_history),
            'avg_success_rate': sum(
                r.completed_tasks / r.total_tasks if r.total_tasks > 0 else 0
                for r in self.execution_history
            ) / len(self.execution_history),
            'total_workflows': len(self.execution_history)
        }

    def create_optimized_tasks_from_agents(self, agents: List[str], base_prompt: str,
                                         task_description: str = None) -> List[OptimizedTask]:
        """从Agent列表创建优化任务"""
        tasks = []

        for i, agent in enumerate(agents):
            task = OptimizedTask(
                task_id=f"task_{agent}_{int(time.time())}_{i}",
                agent_name=agent,
                description=task_description or f"{agent} 执行任务",
                prompt=f"{base_prompt}\n\n请以{agent}的专业角度完成这个任务。",
                priority=TaskPriority.NORMAL
            )
            tasks.append(task)

        return tasks

    def get_optimization_statistics(self) -> Dict[str, Any]:
        """获取优化统计信息"""
        stats = {
            'total_workflows_processed': len(self.execution_history),
            'performance_metrics': self.performance_metrics,
            'executor_statistics': self.parallel_executor.get_execution_statistics()
        }

        if self.context_optimizer:
            stats['context_statistics'] = self.context_optimizer.get_context_statistics()

        return stats

    def generate_claude_code_instruction(self, tasks: List[OptimizedTask],
                                       execution_mode: ExecutionMode = ExecutionMode.PARALLEL) -> str:
        """生成Claude Code可执行的指令"""
        if execution_mode == ExecutionMode.PARALLEL:
            # 生成并行执行指令
            instruction_parts = ["<function_calls>"]

            for task in tasks:
                instruction_parts.append(f'<invoke name="Task">')
                instruction_parts.append(f'<parameter name="subagent_type">{task.agent_name}</parameter>')

                # 合并上下文和prompt
                full_prompt = task.prompt
                if task.context_data and task.context_data.get('context'):
                    full_prompt = f"{task.context_data['context']}\n\n{task.prompt}"

                instruction_parts.append(f'<parameter name="prompt">{full_prompt}</parameter>')
                instruction_parts.append('</invoke>')

            instruction_parts.append("</function_calls>")

            return "\n".join(instruction_parts)

        else:
            # 生成顺序执行说明
            instruction_parts = ["请按以下顺序执行任务：\n"]

            for i, task in enumerate(tasks, 1):
                instruction_parts.append(f"{i}. 使用{task.agent_name}:")
                instruction_parts.append(f"   任务: {task.description}")
                instruction_parts.append(f"   要求: {task.prompt}")
                if task.dependencies:
                    instruction_parts.append(f"   依赖: {', '.join(task.dependencies)}")
                instruction_parts.append("")

            return "\n".join(instruction_parts)


# 全局实例
_workflow_optimizer = None

def get_workflow_optimizer(artifact_manager=None, max_workers: int = 10) -> WorkflowOptimizer:
    """获取全局工作流优化器实例"""
    global _workflow_optimizer
    if _workflow_optimizer is None:
        _workflow_optimizer = WorkflowOptimizer(artifact_manager, max_workers)
    return _workflow_optimizer