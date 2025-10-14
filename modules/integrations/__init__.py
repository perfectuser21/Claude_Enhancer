"""
Integration Modules
Integrations with external tools and services
"""

from .git import GitIntegration
from .npm import NPMIntegration

__all__ = [
    "GitIntegration",
    "NPMIntegration",
]
