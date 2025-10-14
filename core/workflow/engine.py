"""
Claude Enhancer v2.0 - Workflow Engine
=======================================

State machine engine for managing 8-Phase workflow transitions.
"""

from typing import Optional, Dict, Any, List
import logging

# Import types from centralized location to prevent circular imports
from core.workflow.types import Phase, PhaseContext, PhaseResult, TransitionResult
from core.workflow.transitions import TransitionRules
from core.state.manager import StateManager
from core.api.events import EventBus, Event


logger = logging.getLogger(__name__)


class InvalidTransitionError(Exception):
    """Raised when an invalid phase transition is attempted"""
    pass


class WorkflowEngine:
    """
    8-Phase Workflow Engine

    Manages the state machine for the complete development lifecycle:
    P0 (Discovery) -> P1 (Plan) -> P2 (Skeleton) -> P3 (Implementation)
    -> P4 (Testing) -> P5 (Review) -> P6 (Release) -> P7 (Monitor)

    Features:
    - State machine with strict transition rules
    - Event-driven architecture
    - Comprehensive validation at each transition
    - Support for hooks and plugins
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize workflow engine

        Args:
            config: Workflow configuration dictionary
        """
        self.config = config
        self.state_manager = StateManager(config.get('state_dir', '.workflow'))
        self.transition_rules = TransitionRules(config)
        self.event_bus = EventBus()

        # Phase implementations registry
        self._phase_implementations = {}
        self._load_phase_implementations()

        logger.info("WorkflowEngine initialized with config: %s", config.get('version'))

    def current_phase(self) -> Phase:
        """
        Get current phase

        Returns:
            Current Phase enum value
        """
        phase_str = self.state_manager.get_current_phase()
        if not phase_str:
            # Default to P1 if no phase set
            return Phase.P1_PLAN

        try:
            return Phase(phase_str)
        except ValueError:
            logger.error("Invalid phase in state: %s, defaulting to P1", phase_str)
            return Phase.P1_PLAN

    def transition_to(self, target_phase: Phase) -> TransitionResult:
        """
        Transition to target phase

        This method validates the transition, executes pre-transition hooks,
        performs the transition, and executes post-transition hooks.

        Args:
            target_phase: Target Phase to transition to

        Returns:
            TransitionResult with success status and details

        Raises:
            InvalidTransitionError: If transition is not allowed
        """
        current = self.current_phase()

        logger.info("Attempting transition from %s to %s", current.value, target_phase.value)

        # 1. Validate transition is allowed
        if not self.transition_rules.can_transition(current, target_phase):
            reason = self.transition_rules.get_rejection_reason(current, target_phase)
            logger.error("Transition rejected: %s", reason)
            raise InvalidTransitionError(reason)

        # 2. Execute pre-transition hooks
        self.event_bus.emit('pre_transition', Event(
            name='pre_transition',
            data={
                'from': current.value,
                'to': target_phase.value
            }
        ))

        # 3. Execute transition
        try:
            result = self._execute_transition(current, target_phase)
        except Exception as e:
            logger.exception("Transition execution failed")
            return TransitionResult(
                success=False,
                from_phase=current.value,
                to_phase=target_phase.value,
                reason=f"Execution error: {str(e)}"
            )

        # 4. Execute post-transition hooks
        self.event_bus.emit('post_transition', Event(
            name='post_transition',
            data={
                'from': current.value,
                'to': target_phase.value,
                'result': result
            }
        ))

        logger.info("Transition completed: %s -> %s", current.value, target_phase.value)
        return result

    def execute_phase(self, phase: Phase) -> PhaseResult:
        """
        Execute specified phase

        Args:
            phase: Phase to execute

        Returns:
            PhaseResult with execution details
        """
        logger.info("Executing phase: %s", phase.value)

        # Get phase implementation
        phase_impl = self._get_phase_implementation(phase)
        if not phase_impl:
            return PhaseResult(
                phase=phase.value,
                success=False,
                artifacts={},
                errors=[f"No implementation found for phase {phase.value}"]
            )

        # Get context
        context = self._build_phase_context(phase)

        # Execute phase
        try:
            result = phase_impl.execute(context)
            logger.info("Phase %s executed successfully", phase.value)
            return result
        except Exception as e:
            logger.exception("Phase execution failed")
            return PhaseResult(
                phase=phase.value,
                success=False,
                artifacts={},
                errors=[f"Execution error: {str(e)}"]
            )

    def get_phase_status(self, phase: Phase) -> Dict[str, Any]:
        """
        Get status of specified phase

        Args:
            phase: Phase to check

        Returns:
            Dictionary with phase status information
        """
        return self.state_manager.get_phase_status(phase.value)

    def _execute_transition(self, from_phase: Phase, to_phase: Phase) -> TransitionResult:
        """
        Execute the actual transition

        Args:
            from_phase: Source phase
            to_phase: Target phase

        Returns:
            TransitionResult
        """
        import datetime

        # Update state
        self.state_manager.set_current_phase(to_phase.value)

        # Record transition in history
        self.state_manager.record_transition(
            from_phase=from_phase.value,
            to_phase=to_phase.value,
            timestamp=datetime.datetime.now().isoformat()
        )

        return TransitionResult(
            success=True,
            from_phase=from_phase.value,
            to_phase=to_phase.value,
            reason="Transition completed successfully",
            timestamp=datetime.datetime.now().isoformat()
        )

    def _build_phase_context(self, phase: Phase) -> PhaseContext:
        """
        Build execution context for phase

        Args:
            phase: Phase to build context for

        Returns:
            PhaseContext
        """
        return PhaseContext(
            phase=phase,
            task=self.state_manager.get_current_task(),
            config=self.config,
            state=self.state_manager.get_all_state()
        )

    def _get_phase_implementation(self, phase: Phase):
        """
        Get implementation for specified phase

        Args:
            phase: Phase to get implementation for

        Returns:
            Phase implementation class or None
        """
        return self._phase_implementations.get(phase)

    def _load_phase_implementations(self):
        """Load all phase implementations"""
        # This will be implemented to dynamically load phase implementations
        # from core/workflow/phases/ directory

        try:
            from core.workflow.phases.p0_discovery import P0DiscoveryPhase
            from core.workflow.phases.p1_plan import P1PlanPhase
            from core.workflow.phases.p2_skeleton import P2SkeletonPhase
            from core.workflow.phases.p3_implementation import P3ImplementationPhase
            from core.workflow.phases.p4_testing import P4TestingPhase
            from core.workflow.phases.p5_review import P5ReviewPhase
            from core.workflow.phases.p6_release import P6ReleasePhase
            from core.workflow.phases.p7_monitor import P7MonitorPhase

            self._phase_implementations = {
                Phase.P0_DISCOVERY: P0DiscoveryPhase(),
                Phase.P1_PLAN: P1PlanPhase(),
                Phase.P2_SKELETON: P2SkeletonPhase(),
                Phase.P3_IMPLEMENTATION: P3ImplementationPhase(),
                Phase.P4_TESTING: P4TestingPhase(),
                Phase.P5_REVIEW: P5ReviewPhase(),
                Phase.P6_RELEASE: P6ReleasePhase(),
                Phase.P7_MONITOR: P7MonitorPhase(),
            }

            logger.info("Loaded %d phase implementations", len(self._phase_implementations))
        except ImportError as e:
            logger.warning("Could not load phase implementations: %s", e)
            # Will be implemented later
            pass
