#!/usr/bin/env python3
"""
Perfect21 Integration Layer
"""

from .optimized_orchestrator import (
    OptimizedOrchestrator, OptimizedExecutionRequest, OptimizedExecutionResult,
    get_optimized_orchestrator, execute_optimized_parallel_workflow,
    create_instant_parallel_instruction
)

__all__ = [
    'OptimizedOrchestrator', 'OptimizedExecutionRequest', 'OptimizedExecutionResult',
    'get_optimized_orchestrator', 'execute_optimized_parallel_workflow',
    'create_instant_parallel_instruction'
]