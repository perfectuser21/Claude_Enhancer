"""
Perfect21 Workflow System
支持真正的多Agent并行执行和工作流管理
"""

# 导入核心引擎（无依赖）
from .engine import WorkflowEngine, WorkflowResult, AgentTask, TaskStatus, ExecutionMode

# 尝试导入其他组件（可能有依赖）
try:
    from .phase_executor import PhaseExecutor
    from .context_pool import ContextPool
    from .phase_summarizer import PhaseSummarizer
    from .git_integration import GitPhaseIntegration

    __all__ = [
        'WorkflowEngine',
        'WorkflowResult',
        'AgentTask',
        'TaskStatus',
        'ExecutionMode',
        'PhaseExecutor',
        'ContextPool',
        'PhaseSummarizer',
        'GitPhaseIntegration'
    ]
except ImportError as e:
    # 如果其他组件导入失败，只导出核心引擎
    __all__ = [
        'WorkflowEngine',
        'WorkflowResult',
        'AgentTask',
        'TaskStatus',
        'ExecutionMode'
    ]