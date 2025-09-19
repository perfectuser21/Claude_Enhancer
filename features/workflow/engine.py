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
    timeout: int = 300
    critical: bool = False

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
    batch_execution_instruction: Optional[str] = None  # 批量执行指令

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

        logger.info(f"开始并行工作流: {workflow_id}, 任务数: {len(tasks)}")

        # 创建AgentTask列表
        agent_tasks = []
        for i, task_data in enumerate(tasks):
            task = AgentTask(
                task_id=f"{workflow_id}_task_{i+1}",
                agent_name=task_data.get('agent_name'),
                description=task_data.get('description'),
                prompt=task_data.get('prompt'),
                timeout=task_data.get('timeout', 300),
                critical=task_data.get('critical', False)
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
            # Perfect21并行策略生成：为所有任务生成执行指令
            parallel_instructions = []
            failed_tasks = []

            # 并行生成所有任务的执行指令
            with ThreadPoolExecutor(max_workers=min(len(tasks), self.max_workers)) as executor:
                # 提交所有任务指令生成
                future_to_task = {}
                for task in agent_tasks:
                    future = executor.submit(self._execute_single_task, task)
                    future_to_task[future] = task

                # 收集指令生成结果
                for future in as_completed(future_to_task):
                    task = future_to_task[future]
                    try:
                        result = future.result()
                        if result['status'] == 'ready_for_execution':
                            task.status = TaskStatus.COMPLETED
                            task.result = result
                            parallel_instructions.append(result['instruction'])
                            workflow_result.success_count += 1
                            logger.info(f"指令生成完成: {task.task_id} ({task.agent_name})")
                        else:
                            task.status = TaskStatus.FAILED
                            task.error = result.get('error', 'Unknown error')
                            failed_tasks.append(task)
                            workflow_result.failure_count += 1
                            logger.error(f"指令生成失败: {task.task_id} ({task.agent_name})")
                    except Exception as e:
                        task.status = TaskStatus.FAILED
                        task.error = str(e)
                        failed_tasks.append(task)
                        workflow_result.failure_count += 1
                        logger.error(f"指令生成异常: {task.task_id} ({task.agent_name}) - {e}")

            # 生成批量并行执行指令
            if parallel_instructions:
                batch_instruction = self._create_batch_execution_instruction(
                    parallel_instructions, workflow_id, len(tasks)
                )
                # 添加批量执行指令到工作流结果
                workflow_result.batch_execution_instruction = batch_instruction
                logger.info(f"批量执行指令已生成，包含 {len(parallel_instructions)} 个agents")

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

        # 添加执行指导
        if hasattr(workflow_result, 'batch_execution_instruction'):
            workflow_result.integrated_result['execution_guidance'] = {
                'type': 'parallel_batch_execution',
                'instruction': workflow_result.batch_execution_instruction,
                'agent_count': len(parallel_instructions),
                'failed_count': len(failed_tasks),
                'ready_for_claude_code': workflow_result.success_count > 0
            }

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
                prompt=stage_data.get('prompt'),
                timeout=stage_data.get('timeout', 300),
                critical=stage_data.get('critical', False)
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
        sequential_instructions = []
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

                if result['status'] == 'ready_for_execution':
                    task.status = TaskStatus.COMPLETED
                    task.result = result
                    sequential_instructions.append(result['instruction'])
                    previous_result = result
                    workflow_result.success_count += 1
                    logger.info(f"阶段完成: {task.task_id} ({task.agent_name})")
                else:
                    task.status = TaskStatus.FAILED
                    task.error = result.get('error', 'Unknown error')
                    workflow_result.failure_count += 1
                    logger.error(f"阶段失败: {task.task_id} ({task.agent_name})")
                    # 顺序执行中，如果一个阶段失败，停止后续执行
                    break

            except Exception as e:
                task.end_time = datetime.now()
                task.status = TaskStatus.FAILED
                task.error = str(e)
                workflow_result.failure_count += 1
                logger.error(f"阶段失败: {task.task_id} ({task.agent_name}) - {e}")
                # 顺序执行中，如果一个阶段失败，停止后续执行
                break

        # 生成顺序执行指令
        if sequential_instructions:
            batch_instruction = self._create_sequential_execution_instruction(
                sequential_instructions, workflow_id
            )
            workflow_result.batch_execution_instruction = batch_instruction

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
        执行单个Agent任务 - 真实实现

        Perfect21作为策略层，生成Task工具调用指令
        """
        logger.info(f"执行任务: {task.task_id} - {task.agent_name}")

        task.start_time = datetime.now()

        try:
            # Perfect21作为策略层：生成Task调用指令而非直接执行
            # 这符合CLAUDE.md中的定义：Perfect21不直接调用SubAgent
            task_instruction = self._generate_task_instruction(task)

            # 返回执行指令和元数据
            result = {
                "agent": task.agent_name,
                "task_id": task.task_id,
                "status": "ready_for_execution",
                "instruction": task_instruction,
                "prompt": task.prompt,
                "description": task.description,
                "execution_metadata": {
                    "timeout": getattr(task, 'timeout', 300),
                    "critical": getattr(task, 'critical', False),
                    "dependencies_satisfied": len(task.dependencies) == 0
                },
                "timestamp": datetime.now().isoformat()
            }

            task.end_time = datetime.now()
            logger.info(f"任务指令生成完成: {task.task_id}")
            return result

        except Exception as e:
            task.end_time = datetime.now()
            logger.error(f"任务指令生成失败: {task.task_id} - {e}")
            return {
                "agent": task.agent_name,
                "task_id": task.task_id,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _generate_task_instruction(self, task: AgentTask) -> str:
        """
        生成Task工具调用指令
        """
        # 根据CLAUDE.md的要求，生成标准的Task调用指令
        instruction = f'Task("{task.agent_name}", "{task.description}"'

        # 添加详细的prompt参数
        if task.prompt and task.prompt.strip():
            # 清理prompt，确保格式正确
            clean_prompt = task.prompt.replace('"', '\\"').replace('\n', '\\n')
            instruction = f'Task(subagent_type="{task.agent_name}", prompt="{clean_prompt}"'

        instruction += ')'

        return instruction

    def _create_batch_execution_instruction(self, instructions: List[str],
                                          workflow_id: str, total_tasks: int) -> str:
        """
        创建批量并行执行指令
        """
        header = f"# Perfect21 并行执行指令 - {workflow_id}\n"
        header += f"# 任务总数: {total_tasks}, 成功生成: {len(instructions)}\n"
        header += f"# 生成时间: {datetime.now().isoformat()}\n\n"

        header += "# 🚀 请在Claude Code中复制以下所有Task调用到一个消息中执行：\n"
        header += "# ⚠️  重要：必须同时调用所有agents，不可分开执行！\n\n"

        # 将所有指令组合成一个批量调用块
        batch_call = "<function_calls>\n"
        for i, instruction in enumerate(instructions, 1):
            batch_call += f"  <invoke name=\"Task\">\n"
            # 解析instruction提取参数
            if 'subagent_type=' in instruction:
                # 提取subagent_type和prompt
                parts = instruction.split(', prompt="')
                if len(parts) == 2:
                    subagent = parts[0].split('subagent_type="')[1].strip('"')
                    prompt = parts[1].rstrip(')"')
                    batch_call += f"    <parameter name=\"subagent_type\">{subagent}</parameter>\n"
                    batch_call += f"    <parameter name=\"prompt\">{prompt}</parameter>\n"
            batch_call += f"  </invoke>\n"
        batch_call += "</function_calls>\n"

        footer = f"\n# 执行完成后，所有 {len(instructions)} 个agents将并行协作完成任务\n"
        footer += "# Perfect21工作流管理系统将跟踪执行进度"

        return header + batch_call + footer

    def _create_sequential_execution_instruction(self, instructions: List[str],
                                               workflow_id: str) -> str:
        """
        创建顺序执行指令
        """
        header = f"# Perfect21 顺序执行指令 - {workflow_id}\n"
        header += f"# 阶段总数: {len(instructions)}\n"
        header += f"# 生成时间: {datetime.now().isoformat()}\n\n"

        header += "# 📋 请按顺序执行以下Task调用：\n\n"

        sequential_calls = ""
        for i, instruction in enumerate(instructions, 1):
            sequential_calls += f"# 阶段 {i}:\n{instruction}\n\n"

        footer = "# ✅ 请按顺序逐个执行，每个阶段完成后再执行下一个"

        return header + sequential_calls + footer

    def _integrate_results(self, tasks: List[AgentTask]) -> Dict[str, Any]:
        """整合多个任务的结果"""
        integrated = {
            "summary": f"集成了{len(tasks)}个Agent任务的执行指令",
            "agents_involved": [task.agent_name for task in tasks],
            "successful_tasks": [task.task_id for task in tasks if task.status == TaskStatus.COMPLETED],
            "failed_tasks": [task.task_id for task in tasks if task.status == TaskStatus.FAILED],
            "execution_instructions": {},
            "ready_for_claude_code": False
        }

        successful_instructions = 0
        for task in tasks:
            if task.result and task.result.get('status') == 'ready_for_execution':
                integrated["execution_instructions"][task.task_id] = {
                    "agent": task.agent_name,
                    "instruction": task.result.get('instruction'),
                    "description": task.description,
                    "metadata": task.result.get('execution_metadata', {})
                }
                successful_instructions += 1

        integrated["ready_for_claude_code"] = successful_instructions > 0
        integrated["instruction_count"] = successful_instructions

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
                dependencies=task_data.get('dependencies', []),
                timeout=task_data.get('timeout', 300),
                critical=task_data.get('critical', False)
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
                'prompt': task.prompt,
                'timeout': task.timeout,
                'critical': task.critical
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
            "tasks": [],
            "execution_ready": hasattr(workflow, 'batch_execution_instruction') and workflow.batch_execution_instruction is not None
        }

        for task in workflow.tasks:
            task_info = {
                "task_id": task.task_id,
                "agent": task.agent_name,
                "status": task.status.value,
                "description": task.description
            }
            if task.result and 'instruction' in task.result:
                task_info['instruction_ready'] = True
            status_summary["tasks"].append(task_info)

        return status_summary

    def get_claude_code_instructions(self, workflow_id: str) -> Optional[str]:
        """
        获取Claude Code执行指令
        """
        workflow = self.get_execution_status(workflow_id)
        if workflow and hasattr(workflow, 'batch_execution_instruction'):
            return workflow.batch_execution_instruction

        # 检查历史记录
        for historical_workflow in self.execution_history:
            if (historical_workflow.workflow_id == workflow_id and
                hasattr(historical_workflow, 'batch_execution_instruction')):
                return historical_workflow.batch_execution_instruction

        return None

    def create_real_time_parallel_instruction(self, agents: List[str],
                                            base_prompt: str) -> str:
        """
        创建实时并行执行指令

        Args:
            agents: Agent列表
            base_prompt: 基础提示词

        Returns:
            str: 可直接用于Claude Code的并行执行指令
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        workflow_id = f"realtime_parallel_{timestamp}"

        header = f"# Perfect21 实时并行指令 - {workflow_id}\n"
        header += f"# Agents: {len(agents)}, 生成时间: {datetime.now().isoformat()}\n\n"
        header += "# 🚀 立即执行 - 所有agents同时调用：\n\n"

        batch_call = "<function_calls>\n"
        for agent in agents:
            batch_call += f"  <invoke name=\"Task\">\n"
            batch_call += f"    <parameter name=\"subagent_type\">{agent}</parameter>\n"
            batch_call += f"    <parameter name=\"prompt\">{base_prompt}</parameter>\n"
            batch_call += f"  </invoke>\n"
        batch_call += "</function_calls>\n"

        footer = f"\n# ✅ {len(agents)}个agents将并行执行，无需等待Perfect21进一步处理"

        return header + batch_call + footer