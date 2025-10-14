"""
Claude Enhancer v2.0 - Core Layer
==================================

This is the core layer of Claude Enhancer, containing all essential
components for the 8-Phase workflow system.

Core Components:
- workflow: 8-Phase workflow engine
- hooks: Hook management and validation system
- agents: Agent selection and orchestration
- config: Configuration management
- api: Core API interfaces
- state: State management
- utils: Core utilities

Version: 2.0.0
License: MIT
"""

__version__ = "2.0.0"
__core_version__ = "2.0.0"

# Core API exports
from core.api.workflow_api import WorkflowAPI
from core.api.hook_api import HookAPI
from core.api.agent_api import AgentAPI
from core.api.config_api import ConfigAPI
from core.api.events import EventBus, Event

# Core classes
from core.workflow.engine import WorkflowEngine
from core.hooks.manager import HookManager
from core.agents.selector import AgentSelector
from core.config.loader import ConfigLoader
from core.state.manager import StateManager

__all__ = [
    # Version info
    "__version__",
    "__core_version__",

    # APIs
    "WorkflowAPI",
    "HookAPI",
    "AgentAPI",
    "ConfigAPI",
    "EventBus",
    "Event",

    # Core classes
    "WorkflowEngine",
    "HookManager",
    "AgentSelector",
    "ConfigLoader",
    "StateManager",
]
