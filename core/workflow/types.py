"""
Claude Enhancer v2.0 - Workflow Types
======================================

Common types and enums used across workflow components.
This module prevents circular imports between engine and transitions.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


class Phase(Enum):
    """8-Phase workflow phases"""
    P0_DISCOVERY = "P0"
    P1_PLAN = "P1"
    P2_SKELETON = "P2"
    P3_IMPLEMENTATION = "P3"
    P4_TESTING = "P4"
    P5_REVIEW = "P5"
    P6_RELEASE = "P6"
    P7_MONITOR = "P7"

    @property
    def display_name(self) -> str:
        """Get display name for phase"""
        names = {
            "P0": "Discovery",
            "P1": "Planning",
            "P2": "Skeleton",
            "P3": "Implementation",
            "P4": "Testing",
            "P5": "Review",
            "P6": "Release",
            "P7": "Monitor"
        }
        return names.get(self.value, self.value)

    @property
    def description(self) -> str:
        """Get phase description"""
        descriptions = {
            "P0": "Explore feasibility and technical spikes",
            "P1": "Plan requirements and architecture",
            "P2": "Create skeleton and directory structure",
            "P3": "Implement features and functionality",
            "P4": "Test comprehensively (unit, integration, E2E)",
            "P5": "Code review and quality assurance",
            "P6": "Release documentation and deployment",
            "P7": "Monitor production and collect metrics"
        }
        return descriptions.get(self.value, "")

    def __str__(self) -> str:
        return f"{self.value}: {self.display_name}"


@dataclass
class PhaseContext:
    """Context for phase execution"""
    phase: Phase
    task: Dict[str, Any]
    config: Dict[str, Any]
    state: Dict[str, Any]


@dataclass
class PhaseResult:
    """Result of phase execution"""
    phase: str
    success: bool
    artifacts: Dict[str, Any]
    next_phase: Optional[str] = None
    errors: List[str] = None
    warnings: List[str] = None

    def __post_init__(self):
        """Initialize mutable defaults"""
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


@dataclass
class TransitionResult:
    """Result of phase transition"""
    success: bool
    from_phase: str
    to_phase: str
    message: str = ""
    validation_errors: List[str] = None

    def __post_init__(self):
        """Initialize mutable defaults"""
        if self.validation_errors is None:
            self.validation_errors = []


__all__ = [
    "Phase",
    "PhaseContext",
    "PhaseResult",
    "TransitionResult",
]
