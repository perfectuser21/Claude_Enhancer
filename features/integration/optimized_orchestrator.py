#!/usr/bin/env python3
"""
Perfect21 Optimized Orchestrator Integration
整合智能Agent选择、Artifact管理和工作流优化的统一调度器
"""

import logging
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Import our optimized systems
from ..agents.intelligent_selector import get_intelligent_selector, TaskComplexity, ExecutionMode as AgentExecutionMode
from ..storage.artifact_manager import get_artifact_manager
from ..workflow.optimization_engine import (
    get_workflow_optimizer, OptimizedTask, TaskPriority, ExecutionMode, TaskStatus
)

logger = logging.getLogger(__name__)

@dataclass
class OptimizedExecutionRequest:
    """优化执行请求"""
    task_description: str
    context: Optional[Dict[str, Any]] = None
    max_agents: int = 10
    priority: str = "normal"
    timeout: float = 300.0
    use_context: bool = True
    execution_preference: str = "adaptive"  # adaptive, parallel, sequential, hybrid

@dataclass
class OptimizedExecutionResult:
    """优化执行结果"""
    success: bool
    execution_id: str
    selected_agents: List[str]
    execution_mode: str
    total_execution_time: float
    parallel_efficiency: float
    completed_tasks: int
    failed_tasks: int
    artifacts_created: List[str]
    optimization_suggestions: List[str]
    detailed_results: Dict[str, Any]
    error_message: Optional[str] = None

class OptimizedOrchestrator:
    """优化的Perfect21调度器"""

    def __init__(self):
        # 初始化优化组件
        self.agent_selector = get_intelligent_selector()
        self.artifact_manager = get_artifact_manager()
        self.workflow_optimizer = get_workflow_optimizer(self.artifact_manager)

        # 执行历史和统计
        self.execution_history: List[OptimizedExecutionResult] = []
        self.performance_stats = {}

        logger.info("优化调度器初始化完成")

    def execute_optimized_workflow(self, request: OptimizedExecutionRequest) -> OptimizedExecutionResult:
        """
        执行优化的工作流

        Args:
            request: 执行请求

        Returns:
            OptimizedExecutionResult: 优化执行结果
        """
        execution_id = f"exec_{int(time.time())}"
        start_time = time.time()

        try:
            logger.info(f"开始优化执行: {execution_id} - {request.task_description[:100]}")

            # 1. 智能Agent选择
            agent_selection_result = self._select_optimal_agents(request)
            if not agent_selection_result['success']:
                return self._create_error_result(
                    execution_id, start_time, "Agent选择失败",
                    agent_selection_result.get('error', 'Unknown error')
                )

            selected_agents = agent_selection_result['selected_agents']
            agent_analysis = agent_selection_result['task_analysis']

            # 2. 准备上下文信息
            context_artifacts = []
            if request.use_context:
                context_artifacts = self._prepare_context_artifacts(
                    request.task_description, selected_agents
                )

            # 3. 创建优化任务
            optimized_tasks = self._create_optimized_tasks(
                selected_agents, request, agent_analysis, context_artifacts
            )

            # 4. 确定执行模式
            execution_mode = self._determine_execution_mode(
                request.execution_preference, agent_analysis.execution_mode
            )

            # 5. 执行工作流
            workflow_result = self.workflow_optimizer.optimize_and_execute(
                optimized_tasks, execution_mode
            )

            # 6. 保存结果artifacts
            created_artifacts = self._save_execution_artifacts(
                execution_id, optimized_tasks, workflow_result
            )

            # 7. 学习和优化
            self._learn_from_execution(request, workflow_result, selected_agents)

            # 8. 创建结果
            total_time = time.time() - start_time
            result = OptimizedExecutionResult(
                success=True,
                execution_id=execution_id,
                selected_agents=selected_agents,
                execution_mode=execution_mode.value,
                total_execution_time=total_time,
                parallel_efficiency=workflow_result.parallel_efficiency,
                completed_tasks=workflow_result.completed_tasks,
                failed_tasks=workflow_result.failed_tasks,
                artifacts_created=created_artifacts,
                optimization_suggestions=workflow_result.optimization_suggestions,
                detailed_results={
                    'agent_analysis': agent_analysis.__dict__,
                    'workflow_result': workflow_result.__dict__,
                    'context_artifacts': context_artifacts,
                    'performance_metrics': workflow_result.performance_metrics
                }
            )

            self._record_execution(result)
            logger.info(f"优化执行完成: {execution_id}, 效率: {workflow_result.parallel_efficiency:.2%}")

            return result

        except Exception as e:
            logger.error(f"优化执行失败: {execution_id} - {e}")
            return self._create_error_result(execution_id, start_time, "执行异常", str(e))

    def _select_optimal_agents(self, request: OptimizedExecutionRequest) -> Dict[str, Any]:
        """选择最优Agent组合"""
        try:
            context = request.context or {}

            # 添加优化参数
            if request.priority != "normal":
                context['priority'] = request.priority

            context['timeout'] = request.timeout

            result = self.agent_selector.get_optimal_agents(
                request.task_description,
                context,
                request.max_agents
            )

            return result

        except Exception as e:
            logger.error(f"Agent选择失败: {e}")
            return {'success': False, 'error': str(e)}

    def _prepare_context_artifacts(self, task_description: str, agents: List[str]) -> List[str]:
        """准备相关的上下文artifacts"""
        try:
            # 查找相关的历史artifacts
            related_artifacts = []

            # 按agent查找
            for agent in agents:
                artifacts = self.artifact_manager.find_related_artifacts(
                    agent_name=agent,
                    since_hours=24  # 最近24小时
                )
                related_artifacts.extend(artifacts[:2])  # 每个agent最多2个

            # 按任务关键词查找
            task_keywords = self._extract_keywords(task_description)
            if task_keywords:
                keyword_artifacts = self.artifact_manager.find_related_artifacts(
                    tags=task_keywords,
                    since_hours=48
                )
                related_artifacts.extend(keyword_artifacts[:3])

            # 去重并限制数量
            unique_artifacts = []
            seen_ids = set()
            for artifact in related_artifacts:
                if artifact['artifact_id'] not in seen_ids:
                    unique_artifacts.append(artifact['artifact_id'])
                    seen_ids.add(artifact['artifact_id'])
                if len(unique_artifacts) >= 5:  # 最多5个上下文
                    break

            return unique_artifacts

        except Exception as e:
            logger.warning(f"上下文准备失败: {e}")
            return []

    def _extract_keywords(self, text: str) -> List[str]:
        """从文本中提取关键词作为标签"""
        keywords = []
        text_lower = text.lower()

        # 技术关键词
        tech_keywords = [
            'api', 'database', 'frontend', 'backend', 'authentication', 'auth',
            'react', 'vue', 'python', 'javascript', 'docker', 'kubernetes',
            'test', 'security', 'performance', 'optimization'
        ]

        for keyword in tech_keywords:
            if keyword in text_lower:
                keywords.append(keyword)

        return keywords[:3]  # 最多3个关键词

    def _create_optimized_tasks(self, agents: List[str], request: OptimizedExecutionRequest,
                              agent_analysis, context_artifacts: List[str]) -> List[OptimizedTask]:
        """创建优化任务列表"""
        tasks = []

        # 映射优先级
        priority_map = {
            'low': TaskPriority.LOW,
            'normal': TaskPriority.NORMAL,
            'high': TaskPriority.HIGH,
            'critical': TaskPriority.CRITICAL
        }
        priority = priority_map.get(request.priority, TaskPriority.NORMAL)

        for i, agent in enumerate(agents):
            # 为每个agent创建专门的prompt
            specialized_prompt = self._create_specialized_prompt(
                agent, request.task_description, agent_analysis
            )

            task = OptimizedTask(
                task_id=f"task_{agent}_{int(time.time())}_{i}",
                agent_name=agent,
                description=f"{agent} - {request.task_description}",
                prompt=specialized_prompt,
                priority=priority,
                timeout=request.timeout,
                context_requirements=context_artifacts.copy()
            )

            tasks.append(task)

        # 设置依赖关系（如果agent_analysis中有依赖信息）
        if hasattr(agent_analysis, 'dependencies') and agent_analysis.dependencies:
            self._set_task_dependencies(tasks, agent_analysis.dependencies)

        return tasks

    def _create_specialized_prompt(self, agent: str, task_description: str, analysis) -> str:
        """为特定agent创建专门的prompt"""
        base_prompt = f"""作为 {agent}，请完成以下任务：

{task_description}

请按照你的专业领域提供：
1. 专业分析和建议
2. 具体的实现方案
3. 潜在风险和注意事项
4. 与其他team members的协作要求

任务复杂度: {analysis.complexity.value}
执行模式: {analysis.execution_mode.value}
预期时间: {analysis.estimated_time} 分钟

请确保你的输出格式化良好，便于与其他agents的结果整合。"""

        return base_prompt

    def _set_task_dependencies(self, tasks: List[OptimizedTask], dependencies: Dict[str, List[str]]):
        """设置任务依赖关系"""
        # 创建agent到task的映射
        agent_to_task = {task.agent_name: task for task in tasks}

        for dependent_agent, dependency_agents in dependencies.items():
            if dependent_agent in agent_to_task:
                dependent_task = agent_to_task[dependent_agent]
                for dep_agent in dependency_agents:
                    if dep_agent in agent_to_task:
                        dependent_task.dependencies.append(agent_to_task[dep_agent].task_id)

    def _determine_execution_mode(self, preference: str, agent_mode: AgentExecutionMode) -> ExecutionMode:
        """确定最终执行模式"""
        if preference == "parallel":
            return ExecutionMode.PARALLEL
        elif preference == "sequential":
            return ExecutionMode.SEQUENTIAL
        elif preference == "hybrid":
            return ExecutionMode.HYBRID
        elif preference == "adaptive":
            # 基于agent分析结果决定
            if agent_mode == AgentExecutionMode.PARALLEL:
                return ExecutionMode.PARALLEL
            elif agent_mode == AgentExecutionMode.SEQUENTIAL:
                return ExecutionMode.SEQUENTIAL
            else:
                return ExecutionMode.ADAPTIVE
        else:
            return ExecutionMode.ADAPTIVE

    def _save_execution_artifacts(self, execution_id: str, tasks: List[OptimizedTask],
                                workflow_result) -> List[str]:
        """保存执行结果为artifacts"""
        created_artifacts = []

        try:
            # 保存整体执行结果
            execution_summary = {
                'execution_id': execution_id,
                'workflow_result': workflow_result.__dict__,
                'tasks_summary': [
                    {
                        'task_id': task.task_id,
                        'agent_name': task.agent_name,
                        'status': task.status.value,
                        'result': task.result,
                        'execution_time': task.execution_metadata.get('actual_execution_time', 0)
                    }
                    for task in tasks
                ],
                'timestamp': datetime.now().isoformat()
            }

            summary_artifact_id = self.artifact_manager.store_agent_output(
                agent_name="orchestrator",
                task_description=f"执行总结 - {execution_id}",
                content=execution_summary,
                tags=['execution_summary', 'orchestrator'],
                expires_in_hours=168  # 保留7天
            )
            created_artifacts.append(summary_artifact_id)

            # 保存每个成功任务的结果
            for task in tasks:
                if task.status == TaskStatus.COMPLETED and task.result:
                    artifact_id = self.artifact_manager.store_agent_output(
                        agent_name=task.agent_name,
                        task_description=task.description,
                        content=task.result,
                        tags=['task_result', execution_id],
                        expires_in_hours=72  # 保留3天
                    )
                    created_artifacts.append(artifact_id)

        except Exception as e:
            logger.warning(f"保存执行artifacts失败: {e}")

        return created_artifacts

    def _learn_from_execution(self, request: OptimizedExecutionRequest,
                            workflow_result, selected_agents: List[str]):
        """从执行结果学习，优化未来选择"""
        try:
            success = workflow_result.completed_tasks > workflow_result.failed_tasks
            execution_time = workflow_result.total_execution_time

            # 更新agent选择器的学习数据
            self.agent_selector.learn_from_execution(
                request.task_description,
                selected_agents,
                success,
                execution_time
            )

            # 更新性能统计
            self._update_performance_stats(workflow_result)

        except Exception as e:
            logger.warning(f"学习更新失败: {e}")

    def _update_performance_stats(self, workflow_result):
        """更新性能统计"""
        if not hasattr(self, '_execution_count'):
            self._execution_count = 0

        self._execution_count += 1

        # 移动平均更新性能指标
        alpha = 0.1  # 学习率

        current_efficiency = workflow_result.parallel_efficiency
        if 'avg_parallel_efficiency' not in self.performance_stats:
            self.performance_stats['avg_parallel_efficiency'] = current_efficiency
        else:
            self.performance_stats['avg_parallel_efficiency'] = (
                (1 - alpha) * self.performance_stats['avg_parallel_efficiency'] +
                alpha * current_efficiency
            )

        # 成功率统计
        current_success_rate = (
            workflow_result.completed_tasks /
            (workflow_result.completed_tasks + workflow_result.failed_tasks)
            if (workflow_result.completed_tasks + workflow_result.failed_tasks) > 0 else 0
        )

        if 'avg_success_rate' not in self.performance_stats:
            self.performance_stats['avg_success_rate'] = current_success_rate
        else:
            self.performance_stats['avg_success_rate'] = (
                (1 - alpha) * self.performance_stats['avg_success_rate'] +
                alpha * current_success_rate
            )

    def _create_error_result(self, execution_id: str, start_time: float,
                           error_type: str, error_message: str) -> OptimizedExecutionResult:
        """创建错误结果"""
        return OptimizedExecutionResult(
            success=False,
            execution_id=execution_id,
            selected_agents=[],
            execution_mode="failed",
            total_execution_time=time.time() - start_time,
            parallel_efficiency=0.0,
            completed_tasks=0,
            failed_tasks=1,
            artifacts_created=[],
            optimization_suggestions=[f"{error_type}: {error_message}"],
            detailed_results={},
            error_message=f"{error_type}: {error_message}"
        )

    def _record_execution(self, result: OptimizedExecutionResult):
        """记录执行历史"""
        self.execution_history.append(result)

        # 限制历史记录数量
        if len(self.execution_history) > 100:
            self.execution_history = self.execution_history[-50:]

    def create_instant_execution_instruction(self, request: OptimizedExecutionRequest) -> Dict[str, Any]:
        """
        创建即时执行指令，无需等待完整工作流
        用于与现有Perfect21系统快速集成
        """
        try:
            # 快速Agent选择
            agent_selection = self.agent_selector.get_optimal_agents(
                request.task_description,
                request.context or {},
                request.max_agents
            )

            if not agent_selection['success']:
                return agent_selection

            selected_agents = agent_selection['selected_agents']

            # 生成Claude Code执行指令
            if request.execution_preference == "parallel":
                instruction = self._generate_parallel_instruction(selected_agents, request)
            else:
                instruction = self._generate_sequential_instruction(selected_agents, request)

            return {
                'success': True,
                'selected_agents': selected_agents,
                'execution_mode': request.execution_preference,
                'instruction': instruction,
                'agent_analysis': agent_selection.get('task_analysis', {}),
                'estimated_time': agent_selection.get('estimated_time', 0),
                'confidence': agent_selection.get('confidence', 0),
                'reasoning': agent_selection.get('reasoning', '')
            }

        except Exception as e:
            logger.error(f"即时指令生成失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _generate_parallel_instruction(self, agents: List[str], request: OptimizedExecutionRequest) -> str:
        """生成并行执行指令"""
        instruction_parts = ["<function_calls>"]

        for agent in agents:
            specialized_prompt = f"""请以 {agent} 的专业角度完成以下任务：

{request.task_description}

请提供专业的分析、建议和具体实现方案。确保输出格式清晰，便于与其他专家的结果整合。"""

            instruction_parts.extend([
                '<invoke name="Task">',
                f'<parameter name="subagent_type">{agent}</parameter>',
                f'<parameter name="prompt">{specialized_prompt}</parameter>',
                '</invoke>'
            ])

        instruction_parts.append("</function_calls>")
        return "\n".join(instruction_parts)

    def _generate_sequential_instruction(self, agents: List[str], request: OptimizedExecutionRequest) -> str:
        """生成顺序执行指令"""
        instruction_parts = [
            f"请按以下顺序执行任务：{request.task_description}\n"
        ]

        for i, agent in enumerate(agents, 1):
            instruction_parts.extend([
                f"{i}. 使用 {agent}:",
                f"   请以{agent}的专业角度分析和解决问题",
                f"   提供具体的实现建议和方案",
                ""
            ])

        return "\n".join(instruction_parts)

    def get_orchestrator_statistics(self) -> Dict[str, Any]:
        """获取调度器统计信息"""
        return {
            'total_executions': len(self.execution_history),
            'recent_success_rate': sum(
                1 for r in self.execution_history[-10:] if r.success
            ) / min(len(self.execution_history), 10) if self.execution_history else 0,
            'performance_stats': self.performance_stats,
            'agent_selector_stats': self.agent_selector.get_selection_statistics(),
            'artifact_manager_stats': self.artifact_manager.get_statistics(),
            'workflow_optimizer_stats': self.workflow_optimizer.get_optimization_statistics()
        }

    def cleanup_old_data(self, max_age_days: int = 7) -> Dict[str, int]:
        """清理旧数据"""
        cleanup_stats = {}

        try:
            # 清理artifacts
            artifact_cleanup = self.artifact_manager.cleanup_artifacts(max_age_days)
            cleanup_stats['artifacts_cleaned'] = artifact_cleanup['total_cleaned']

            # 清理执行历史
            cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 3600)
            old_count = len(self.execution_history)
            self.execution_history = [
                r for r in self.execution_history
                if float(r.execution_id.split('_')[1]) > cutoff_time
            ]
            cleanup_stats['execution_history_cleaned'] = old_count - len(self.execution_history)

        except Exception as e:
            logger.error(f"数据清理失败: {e}")
            cleanup_stats['error'] = str(e)

        return cleanup_stats


# 全局实例
_optimized_orchestrator = None

def get_optimized_orchestrator() -> OptimizedOrchestrator:
    """获取全局优化调度器实例"""
    global _optimized_orchestrator
    if _optimized_orchestrator is None:
        _optimized_orchestrator = OptimizedOrchestrator()
    return _optimized_orchestrator


# 便利函数，用于与现有系统集成
def execute_optimized_parallel_workflow(task_description: str, max_agents: int = 10,
                                      context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    便利函数：执行优化的并行工作流
    与现有的Perfect21系统兼容
    """
    orchestrator = get_optimized_orchestrator()
    request = OptimizedExecutionRequest(
        task_description=task_description,
        context=context,
        max_agents=max_agents,
        execution_preference="parallel"
    )

    result = orchestrator.execute_optimized_workflow(request)

    # 转换为兼容格式
    return {
        'success': result.success,
        'execution_id': result.execution_id,
        'agents_count': len(result.selected_agents),
        'selected_agents': result.selected_agents,
        'execution_time': result.total_execution_time,
        'parallel_efficiency': result.parallel_efficiency,
        'success_count': result.completed_tasks,
        'failure_count': result.failed_tasks,
        'optimization_suggestions': result.optimization_suggestions,
        'message': f"优化工作流完成，效率: {result.parallel_efficiency:.1%}",
        'error': result.error_message
    }


def create_instant_parallel_instruction(task_description: str, max_agents: int = 10) -> Dict[str, Any]:
    """
    便利函数：创建即时并行指令
    用于快速集成到现有Perfect21命令
    """
    orchestrator = get_optimized_orchestrator()
    request = OptimizedExecutionRequest(
        task_description=task_description,
        max_agents=max_agents,
        execution_preference="parallel"
    )

    return orchestrator.create_instant_execution_instruction(request)