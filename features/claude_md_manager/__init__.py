#!/usr/bin/env python3
"""
CLAUDE.md Manager - CLAUDE.md自动更新管理器
基于Claude Code最佳实践的动态内存管理系统
"""

from .dynamic_updater import DynamicUpdater
from .memory_synchronizer import MemorySynchronizer
from .template_manager import TemplateManager
from .content_analyzer import ContentAnalyzer

__version__ = "2.3.0"
__author__ = "Perfect21 Team"

# 模块导出
__all__ = [
    "DynamicUpdater",
    "MemorySynchronizer",
    "TemplateManager",
    "ContentAnalyzer"
]

def get_claude_md_manager():
    """获取CLAUDE.md管理器实例"""
    from .dynamic_updater import DynamicUpdater
    return DynamicUpdater()

# Perfect21集成
def bootstrap_claude_md_management():
    """引导CLAUDE.md管理功能"""
    try:
        manager = get_claude_md_manager()
        return {
            'success': True,
            'manager': manager,
            'capabilities': ['dynamic_update', 'memory_sync', 'template_management'],
            'version': __version__
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'capabilities': []
        }