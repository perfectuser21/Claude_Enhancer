"""
Claude Enhancer v2.0 - Standard Features
=========================================

Common development tools and helpers.
"""

__version__ = "2.0.0"
__all__ = ["StandardFeatures"]


class StandardFeatures:
    """
    Standard feature set - Common development tools

    Provides agent selection, smart workflows, and
    enhanced productivity features.
    """

    def __init__(self):
        self.name = "standard"
        self.version = __version__
        self.enabled = True
        self.dependencies = ["basic"]

    def initialize(self):
        """Initialize standard features"""
        return {
            "smart_agent_selector": True,
            "workflow_automation": True,
            "smart_document_loading": True,
            "performance_monitoring": True
        }

    def get_capabilities(self):
        """Get standard feature capabilities"""
        return [
            "Smart Agent Selection (4-6-8 principle)",
            "Workflow Automation",
            "Smart Document Loading",
            "Performance Monitoring"
        ]
