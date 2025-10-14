"""
Claude Enhancer v2.0 - Workflow API
====================================

Public API for workflow operations.
"""

from typing import Dict, Any
import logging

from core.workflow.engine import WorkflowEngine, Phase, PhaseResult, TransitionResult


logger = logging.getLogger(__name__)


class WorkflowAPI:
    """
    Public API for workflow operations

    This is the stable, versioned API that features and modules should use
    to interact with the workflow engine.

    Version: 2.0.0
    """

    def __init__(self, engine: WorkflowEngine):
        """
        Initialize workflow API

        Args:
            engine: WorkflowEngine instance
        """
        self.engine = engine
        logger.info("WorkflowAPI initialized")

    def get_current_phase(self) -> str:
        """
        Get current phase

        Returns:
            Current phase as string (e.g., "P3")
        """
        return self.engine.current_phase().value

    def transition_to(self, phase: str) -> Dict[str, Any]:
        """
        Transition to specified phase

        Args:
            phase: Target phase (e.g., "P3")

        Returns:
            Dictionary with transition result

        Raises:
            ValueError: If phase is invalid
        """
        try:
            target_phase = Phase(phase)
        except ValueError:
            raise ValueError(f"Invalid phase: {phase}")

        result = self.engine.transition_to(target_phase)

        return {
            'success': result.success,
            'from_phase': result.from_phase,
            'to_phase': result.to_phase,
            'reason': result.reason,
            'timestamp': result.timestamp
        }

    def execute_phase(self, phase: str) -> Dict[str, Any]:
        """
        Execute specified phase

        Args:
            phase: Phase to execute (e.g., "P3")

        Returns:
            Dictionary with execution result
        """
        try:
            phase_enum = Phase(phase)
        except ValueError:
            raise ValueError(f"Invalid phase: {phase}")

        result = self.engine.execute_phase(phase_enum)

        return {
            'phase': result.phase,
            'success': result.success,
            'artifacts': result.artifacts,
            'next_phase': result.next_phase,
            'errors': result.errors,
            'warnings': result.warnings
        }

    def get_phase_status(self, phase: str) -> Dict[str, Any]:
        """
        Get status of specified phase

        Args:
            phase: Phase to check (e.g., "P3")

        Returns:
            Dictionary with phase status
        """
        try:
            phase_enum = Phase(phase)
        except ValueError:
            raise ValueError(f"Invalid phase: {phase}")

        return self.engine.get_phase_status(phase_enum)

    def get_all_phases(self) -> list:
        """
        Get list of all phases

        Returns:
            List of phase names
        """
        return [p.value for p in Phase]

    def is_phase_complete(self, phase: str) -> bool:
        """
        Check if phase is complete

        Args:
            phase: Phase to check (e.g., "P3")

        Returns:
            True if phase is complete
        """
        status = self.get_phase_status(phase)
        return status.get('completed', False)
