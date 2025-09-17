"""
Phase Executor - 阶段性并行执行框架
支持真正的多Agent并行执行和Git Hook集成
"""

from .phase_executor import PhaseExecutor
from .context_pool import ContextPool
from .phase_summarizer import PhaseSummarizer
from .git_integration import GitPhaseIntegration

__all__ = [
    'PhaseExecutor',
    'ContextPool',
    'PhaseSummarizer',
    'GitPhaseIntegration'
]