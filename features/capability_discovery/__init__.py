#!/usr/bin/env python3
"""
Perfect21 Capability Discovery - 动态功能发现和集成系统
"""

from .scanner import CapabilityScanner
from .registry import CapabilityRegistry
from .loader import CapabilityLoader

__version__ = "2.1.0"
__author__ = "Perfect21 Team"

# 导出主要类
__all__ = [
    'CapabilityScanner',
    'CapabilityRegistry',
    'CapabilityLoader',
    'bootstrap_capability_discovery'
]

def bootstrap_capability_discovery(features_root: str = None, auto_reload: bool = True) -> dict:
    """
    启动Perfect21功能发现系统

    Args:
        features_root: features目录路径
        auto_reload: 是否启用自动重载

    Returns:
        dict: 启动结果
    """
    import logging

    logger = logging.getLogger("Perfect21.CapabilityDiscovery")
    logger.info("启动Perfect21功能发现系统...")

    try:
        # 创建加载器
        loader = CapabilityLoader(features_root, auto_reload)

        # 执行启动引导
        results = loader.bootstrap()

        # 获取统计信息
        stats = loader.get_statistics()

        return {
            'success': True,
            'loader': loader,
            'results': results,
            'statistics': stats,
            'message': f"功能发现系统启动成功，{len(results)}个功能可用"
        }

    except Exception as e:
        logger.error(f"启动功能发现系统失败: {e}")
        return {
            'success': False,
            'error': str(e),
            'message': "功能发现系统启动失败"
        }

# 全局实例（按需创建）
_global_loader = None

def get_global_loader() -> CapabilityLoader:
    """获取全局加载器实例"""
    global _global_loader
    if _global_loader is None:
        _global_loader = CapabilityLoader()
    return _global_loader

def initialize() -> bool:
    """
    初始化capability_discovery功能
    可以被其他模块调用
    """
    import logging

    logger = logging.getLogger("Perfect21.CapabilityDiscovery")

    try:
        logger.info("初始化capability_discovery功能...")

        # 这里可以添加功能初始化逻辑
        # 例如：创建必要的目录、配置文件等

        logger.info("capability_discovery功能初始化成功")
        return True

    except Exception as e:
        logger.error(f"capability_discovery功能初始化失败: {e}")
        return False