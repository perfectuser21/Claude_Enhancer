"""
CE Dashboard v2 - Data Models

Defines data structures for dashboard components using Python dataclasses.
All models are immutable (frozen=True) for thread safety.

Version: 7.2.0
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class ImportanceLevel(Enum):
    """Decision importance levels"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class ProjectStatus(Enum):
    """Project status values"""
    ACTIVE = "active"
    IDLE = "idle"
    COMPLETED = "completed"
    ERROR = "error"


class EventType(Enum):
    """Telemetry event types"""
    TASK_START = "task_start"
    TASK_END = "task_end"
    PHASE_START = "phase_start"
    PHASE_END = "phase_end"
    ERROR = "error"
    AGENT_CALL = "agent_call"


# ============================================================================
# CAPABILITY MODELS
# ============================================================================

@dataclass(frozen=True)
class Capability:
    """Represents a CE capability (C0-C9)"""

    id: str  # e.g., "C0", "C1"
    name: str  # e.g., "Force New Branch"
    name_en: Optional[str] = None
    type: str = "unknown"  # e.g., "protective", "operational"
    protection_level: int = 1  # 1-5 (5=critical)
    status: str = "active"  # active/idle/disabled
    description: str = ""
    verification_logic: str = ""
    failure_symptoms: List[str] = field(default_factory=list)
    remediation_actions: List[str] = field(default_factory=list)

    @property
    def level_name(self) -> str:
        """Human-readable protection level"""
        levels = {1: "low", 2: "medium", 3: "high", 4: "critical", 5: "critical"}
        return levels.get(self.protection_level, "unknown")


@dataclass(frozen=True)
class Feature:
    """Represents a CE feature (F001-F012)"""

    id: str  # e.g., "F001"
    name: str
    description: str = ""
    priority: str = "P2"  # P0/P1/P2
    category: str = "core"  # core/automation/security/quality
    status: str = "active"
    related_checkpoints: List[str] = field(default_factory=list)
    implementation_files: List[str] = field(default_factory=list)

    @property
    def is_critical(self) -> bool:
        """Check if feature is P0 (critical)"""
        return self.priority == "P0"


@dataclass(frozen=True)
class CoreStats:
    """CE core statistics"""

    total_phases: int = 7
    total_checkpoints: int = 97
    quality_gates: int = 2
    hard_blocks: int = 8
    branch_protection_rate: str = "100%"
    bdd_scenarios: int = 65
    performance_metrics: int = 90


# ============================================================================
# LEARNING SYSTEM MODELS
# ============================================================================

@dataclass(frozen=True)
class Decision:
    """Represents a decision from DECISIONS.md"""

    date: str  # ISO format: YYYY-MM-DD
    title: str
    decision: str
    reason: str
    importance: ImportanceLevel = ImportanceLevel.INFO
    do_not_revert: bool = False
    version: Optional[str] = None
    impact: str = ""
    forbidden_actions: List[str] = field(default_factory=list)
    allowed_actions: List[str] = field(default_factory=list)
    affected_files: List[str] = field(default_factory=list)

    @property
    def importance_str(self) -> str:
        """Get importance as string"""
        return self.importance.value


@dataclass(frozen=True)
class MemoryCacheEntry:
    """Represents an entry in memory-cache.json"""

    id: str
    content: str
    importance: ImportanceLevel
    added_date: str
    do_not_revert: bool = False
    affected_files: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class MemoryCache:
    """Represents the full memory cache"""

    total_entries: int
    cache_size_bytes: int
    cache_limit_bytes: int = 5120  # 5KB default
    entries: List[MemoryCacheEntry] = field(default_factory=list)

    @property
    def cache_usage_percentage(self) -> float:
        """Calculate cache usage percentage"""
        if self.cache_limit_bytes == 0:
            return 0.0
        return (self.cache_size_bytes / self.cache_limit_bytes) * 100

    @property
    def is_healthy(self) -> bool:
        """Check if cache is healthy (<90% full)"""
        return self.cache_usage_percentage < 90


@dataclass(frozen=True)
class DecisionArchive:
    """Represents a monthly decision archive"""

    month: str  # e.g., "2025-10"
    count: int
    size_bytes: int


@dataclass(frozen=True)
class DecisionIndex:
    """Represents decision-index.json"""

    total_archived: int
    archives: List[DecisionArchive] = field(default_factory=list)


@dataclass(frozen=True)
class LearningStatistics:
    """Learning system statistics"""

    total_decisions: int
    critical_count: int
    warning_count: int
    info_count: int
    memory_cache_size: int  # bytes
    cache_health_status: str  # healthy/warning/critical
    recent_30_days_count: int = 0
    average_per_week: float = 0.0


# ============================================================================
# PROJECT MONITORING MODELS
# ============================================================================

@dataclass(frozen=True)
class Event:
    """Represents a telemetry event"""

    timestamp: str  # ISO format
    event_type: EventType
    project_name: str
    task_name: Optional[str] = None
    phase_id: Optional[str] = None  # Phase1-Phase7
    phase_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def event_type_str(self) -> str:
        """Get event type as string"""
        return self.event_type.value

    @property
    def datetime_obj(self) -> Optional[datetime]:
        """Parse timestamp to datetime object"""
        try:
            return datetime.fromisoformat(self.timestamp.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None


@dataclass(frozen=True)
class Project:
    """Represents a monitored project"""

    name: str
    path: str
    branch: str
    status: ProjectStatus
    current_phase: Optional[str] = None  # Phase1-Phase7
    current_phase_name: Optional[str] = None
    task_name: Optional[str] = None
    progress_percentage: int = 0
    duration_seconds: int = 0
    start_time: Optional[str] = None
    last_event_time: Optional[str] = None
    agents_used: int = 0
    phases_completed: List[str] = field(default_factory=list)
    total_events: int = 0
    error_count: int = 0
    recent_events: List[Event] = field(default_factory=list)

    @property
    def status_str(self) -> str:
        """Get status as string"""
        return self.status.value

    @property
    def is_active(self) -> bool:
        """Check if project is currently active"""
        return self.status == ProjectStatus.ACTIVE

    @property
    def duration_formatted(self) -> str:
        """Format duration as human-readable string"""
        hours = self.duration_seconds // 3600
        minutes = (self.duration_seconds % 3600) // 60
        seconds = self.duration_seconds % 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"


@dataclass(frozen=True)
class ProjectSummary:
    """Summary statistics for all projects"""

    total_projects: int
    active_projects: int
    idle_projects: int
    completed_projects: int
    error_projects: int
    average_phase_time_seconds: float = 0.0

    @property
    def average_phase_time_formatted(self) -> str:
        """Format average phase time"""
        minutes = int(self.average_phase_time_seconds // 60)
        return f"{minutes}min" if minutes > 0 else "< 1min"


# ============================================================================
# API RESPONSE MODELS
# ============================================================================

@dataclass(frozen=True)
class APICapabilitiesResponse:
    """Response for /api/capabilities"""

    core_stats: CoreStats
    capabilities: List[Capability]
    features: List[Feature]
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class APILearningResponse:
    """Response for /api/learning"""

    decisions: List[Decision]
    memory_cache: MemoryCache
    decision_index: DecisionIndex
    statistics: LearningStatistics
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class APIProjectsResponse:
    """Response for /api/projects"""

    projects: List[Project]
    summary: ProjectSummary
    meta: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# PARSING RESULT MODEL
# ============================================================================

@dataclass(frozen=True)
class ParsingResult:
    """Generic result for parsing operations"""

    success: bool
    data: Any = None
    error_message: str = ""
    warnings: List[str] = field(default_factory=list)

    @property
    def is_partial_success(self) -> bool:
        """Check if parsing succeeded with warnings"""
        return self.success and len(self.warnings) > 0
