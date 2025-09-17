"""
Perfect21 工作流引擎
提供多Agent并行协作和工作流管理的核心功能
"""

from .engine import (
    WorkflowEngine,
    AgentTask,
    WorkflowResult,
    TaskStatus,
    ExecutionMode
)

from .capability import CAPABILITY

__all__ = [
    'WorkflowEngine',
    'AgentTask',
    'WorkflowResult',
    'TaskStatus',
    'ExecutionMode',
    'CAPABILITY'
]

def create_workflow_engine(max_workers: int = 10) -> WorkflowEngine:
    """
    创建工作流引擎实例

    Args:
        max_workers: 最大并发Agent数量

    Returns:
        WorkflowEngine: 工作流引擎实例
    """
    return WorkflowEngine(max_workers=max_workers)

def create_parallel_tasks(agent_tasks: list) -> list:
    """
    创建并行任务配置

    Args:
        agent_tasks: Agent任务列表 [(agent_name, description, prompt), ...]

    Returns:
        list: 格式化的任务配置列表
    """
    tasks = []
    for agent_name, description, prompt in agent_tasks:
        tasks.append({
            'agent_name': agent_name,
            'description': description,
            'prompt': prompt
        })
    return tasks

def create_sequential_pipeline(pipeline_steps: list) -> list:
    """
    创建顺序管道配置

    Args:
        pipeline_steps: 管道步骤列表 [(agent_name, description, prompt), ...]

    Returns:
        list: 格式化的管道配置列表
    """
    pipeline = []
    for agent_name, description, prompt in pipeline_steps:
        pipeline.append({
            'agent_name': agent_name,
            'description': description,
            'prompt': prompt
        })
    return pipeline

# 全局工作流引擎实例（可选用）
_global_engine = None

def get_global_engine() -> WorkflowEngine:
    """获取全局工作流引擎实例"""
    global _global_engine
    if _global_engine is None:
        _global_engine = create_workflow_engine()
    return _global_engine