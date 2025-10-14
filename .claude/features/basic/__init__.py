"""
Claude Enhancer v2.0 - Basic Features
======================================

Essential functionality for core workflow.
"""

__version__ = "2.0.0"
__all__ = ["BasicFeatures"]


class BasicFeatures:
    """
    Basic feature set - Essential functionality

    Provides core workflow management, branch handling,
    and fundamental quality checks.
    """

    def __init__(self):
        self.name = "basic"
        self.version = __version__
        self.enabled = True
        self.dependencies = []

    def initialize(self):
        """Initialize basic features"""
        return {
            "workflow_management": True,
            "branch_protection": True,
            "quality_gates": True,
            "git_integration": True
        }

    def get_capabilities(self):
        """Get basic feature capabilities"""
        return [
            "8-Phase Workflow (P0-P7)",
            "Branch Protection (Rule 0)",
            "Git Hooks Integration",
            "Quality Gate Checks"
        ]
