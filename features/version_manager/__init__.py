#!/usr/bin/env python3
"""
Perfect21 Version Manager - 统一版本管理系统
"""

from .version_manager import VersionManager
from .semantic_version import SemanticVersion, Version

__version__ = "2.1.0"
__author__ = "Perfect21 Team"

# 导出主要类
__all__ = [
    'VersionManager',
    'SemanticVersion',
    'Version',
    'initialize',
    'get_global_version_manager'
]

# 全局版本管理器实例
_global_version_manager = None

def get_global_version_manager() -> VersionManager:
    """获取全局版本管理器实例"""
    global _global_version_manager
    if _global_version_manager is None:
        _global_version_manager = VersionManager()
    return _global_version_manager

def initialize() -> bool:
    """
    初始化version_manager功能
    由capability_discovery调用
    """
    import logging

    logger = logging.getLogger("Perfect21.VersionManager")

    try:
        logger.info("初始化version_manager功能...")

        # 创建全局版本管理器
        vm = get_global_version_manager()

        # 检查版本一致性
        consistency = vm.validate_version_consistency()
        if not consistency['success']:
            logger.warning(f"版本一致性检查失败: {consistency}")

        logger.info("version_manager功能初始化成功")
        return True

    except Exception as e:
        logger.error(f"version_manager功能初始化失败: {e}")
        return False