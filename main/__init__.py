"""
Claude Enhancer v2.0 - Main Entry Layer
========================================

This is the main entry point layer for Claude Enhancer.
It provides a thin interface to the core layer and manages
the overall application lifecycle.

Version: 2.0.0
"""

__version__ = "2.0.0"

# Import core APIs
from core import (
    WorkflowAPI,
    HookAPI,
    AgentAPI,
    ConfigAPI,
    EventBus,
    __core_version__
)

# Main entry points
class ClaudeEnhancer:
    """
    Main entry point for Claude Enhancer v2.0

    This class provides a simple interface to initialize and run
    the Claude Enhancer workflow system.
    """

    def __init__(self, config_path=None):
        """Initialize Claude Enhancer with optional config path"""
        self.workflow = WorkflowAPI()
        self.hooks = HookAPI()
        self.agents = AgentAPI()
        self.config = ConfigAPI(config_path)
        self.events = EventBus()

        self._version = __version__
        self._core_version = __core_version__

    def start_workflow(self, phase="P0"):
        """Start the 8-Phase workflow from specified phase"""
        return self.workflow.start(phase)

    def get_status(self):
        """Get current workflow status"""
        return self.workflow.get_status()

    @property
    def version(self):
        """Get version info"""
        return {
            "main": self._version,
            "core": self._core_version
        }

__all__ = [
    "__version__",
    "ClaudeEnhancer",
    "WorkflowAPI",
    "HookAPI",
    "AgentAPI",
    "ConfigAPI",
    "EventBus"
]
