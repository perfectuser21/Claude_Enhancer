"""
Perfect21 多工作空间管理模块
============================

支持单人多功能并行开发的智能工作空间管理系统
"""

from .workspace_manager import WorkspaceManager, WorkspaceType, WorkspaceStatus, WorkspaceConfig
from .workspace_integration import WorkspaceIntegration

__all__ = ['WorkspaceManager', 'WorkspaceType', 'WorkspaceStatus', 'WorkspaceConfig', 'WorkspaceIntegration']