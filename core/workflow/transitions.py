"""
Claude Enhancer v2.0 - Transition Rules
========================================

Rules and validation logic for phase transitions.
"""

from typing import Dict, Any, List, Optional
import logging

# Import from types to prevent circular imports
from core.workflow.types import Phase


logger = logging.getLogger(__name__)


class TransitionRules:
    """
    Phase transition rules and validation

    Defines the allowed transitions between phases and the conditions
    that must be met for each transition.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize transition rules

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.rules = self._define_transition_rules()
        self.preconditions = self._define_preconditions()
        self.quality_gates = self._define_quality_gates()

    def can_transition(self, from_phase: Phase, to_phase: Phase) -> bool:
        """
        Check if transition is allowed

        Args:
            from_phase: Source phase
            to_phase: Target phase

        Returns:
            True if transition is allowed, False otherwise
        """
        # 1. Check if sequence is valid
        if not self._is_valid_sequence(from_phase, to_phase):
            logger.debug("Invalid sequence: %s -> %s", from_phase.value, to_phase.value)
            return False

        # 2. Check preconditions
        if not self._check_preconditions(from_phase):
            logger.debug("Preconditions not met for %s", from_phase.value)
            return False

        # 3. Check quality gates
        if not self._check_quality_gates(from_phase):
            logger.debug("Quality gates not passed for %s", from_phase.value)
            return False

        return True

    def get_rejection_reason(self, from_phase: Phase, to_phase: Phase) -> str:
        """
        Get reason why transition was rejected

        Args:
            from_phase: Source phase
            to_phase: Target phase

        Returns:
            Human-readable rejection reason
        """
        if not self._is_valid_sequence(from_phase, to_phase):
            return (
                f"Invalid phase sequence: {from_phase.value} -> {to_phase.value}. "
                f"Phases must be executed in order: P0 -> P1 -> P2 -> P3 -> P4 -> P5 -> P6 -> P7"
            )

        if not self._check_preconditions(from_phase):
            preconditions = self.preconditions.get(from_phase, [])
            failed = [p for p in preconditions if not p.check()]
            return (
                f"Preconditions not met for phase {from_phase.value}:\n" +
                "\n".join([f"- {p.description}" for p in failed])
            )

        if not self._check_quality_gates(from_phase):
            gates = self.quality_gates.get(from_phase, [])
            failed = [g for g in gates if not g.check()]
            return (
                f"Quality gates not passed for phase {from_phase.value}:\n" +
                "\n".join([f"- {g.description}" for g in failed])
            )

        return "Unknown rejection reason"

    def _is_valid_sequence(self, from_phase: Phase, to_phase: Phase) -> bool:
        """
        Validate phase sequence

        Args:
            from_phase: Source phase
            to_phase: Target phase

        Returns:
            True if sequence is valid
        """
        allowed_transitions = self.rules.get(from_phase, [])
        return to_phase in allowed_transitions

    def _check_preconditions(self, phase: Phase) -> bool:
        """
        Check preconditions for phase

        Args:
            phase: Phase to check

        Returns:
            True if all preconditions are met
        """
        preconditions = self.preconditions.get(phase, [])
        return all(p.check() for p in preconditions)

    def _check_quality_gates(self, phase: Phase) -> bool:
        """
        Check quality gates for phase

        Args:
            phase: Phase to check

        Returns:
            True if all quality gates pass
        """
        gates = self.quality_gates.get(phase, [])
        return all(g.check() for g in gates)

    def _define_transition_rules(self) -> Dict[Phase, List[Phase]]:
        """
        Define allowed transitions between phases

        Returns:
            Dictionary mapping phases to their allowed next phases
        """
        return {
            Phase.P0_DISCOVERY: [Phase.P1_PLAN],
            Phase.P1_PLAN: [Phase.P2_SKELETON],
            Phase.P2_SKELETON: [Phase.P3_IMPLEMENTATION],
            Phase.P3_IMPLEMENTATION: [Phase.P4_TESTING],
            Phase.P4_TESTING: [Phase.P5_REVIEW],
            Phase.P5_REVIEW: [Phase.P6_RELEASE, Phase.P3_IMPLEMENTATION],  # Can go back to P3 for fixes
            Phase.P6_RELEASE: [Phase.P7_MONITOR],
            Phase.P7_MONITOR: [],  # Terminal phase
        }

    def _define_preconditions(self) -> Dict[Phase, List['Precondition']]:
        """
        Define preconditions for each phase

        Returns:
            Dictionary mapping phases to their preconditions
        """
        from core.workflow.conditions import (
            TechnicalFeasibilityConfirmed,
            PlanDocumentExists,
            SkeletonCreated,
            CodeCommitted,
            TestCoverageAdequate,
            ReviewCompleted,
            DocumentationReady,
            HealthCheckPassed
        )

        return {
            Phase.P0_DISCOVERY: [],  # No preconditions for P0
            Phase.P1_PLAN: [
                TechnicalFeasibilityConfirmed(),
            ],
            Phase.P2_SKELETON: [
                PlanDocumentExists(),
            ],
            Phase.P3_IMPLEMENTATION: [
                SkeletonCreated(),
            ],
            Phase.P4_TESTING: [
                CodeCommitted(),
            ],
            Phase.P5_REVIEW: [
                TestCoverageAdequate(),
            ],
            Phase.P6_RELEASE: [
                ReviewCompleted(),
            ],
            Phase.P7_MONITOR: [
                DocumentationReady(),
                HealthCheckPassed(),
            ],
        }

    def _define_quality_gates(self) -> Dict[Phase, List['QualityGate']]:
        """
        Define quality gates for each phase

        Returns:
            Dictionary mapping phases to their quality gates
        """
        # Quality gates will be implemented later
        # For now, return empty gates
        return {
            phase: [] for phase in Phase
        }


class Precondition:
    """Base class for preconditions"""

    def __init__(self, description: str):
        self.description = description

    def check(self) -> bool:
        """Check if precondition is met"""
        raise NotImplementedError


class QualityGate:
    """Base class for quality gates"""

    def __init__(self, description: str):
        self.description = description

    def check(self) -> bool:
        """Check if quality gate passes"""
        raise NotImplementedError
