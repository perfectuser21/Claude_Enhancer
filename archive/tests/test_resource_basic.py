#!/usr/bin/env python3
"""
简单资源管理测试
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from modules.resource_manager import ResourceManager, ResourceType, ResourceLimits

def test_simple():
    """简单测试"""
    print("🔧 测试基本资源管理...")

    # 创建资源管理器
    limits = ResourceLimits(max_file_handles=50, max_memory_mb=100)
    rm = ResourceManager(limits)

    # 注册一个资源
    success = rm.register_resource(
        "test_resource",
        "test_data",
        ResourceType.OTHER
    )

    print(f"资源注册: {'成功' if success else '失败'}")

    # 检查状态
    status = rm.get_status()
    print(f"状态键: {list(status.keys())}")
    print(f"资源统计: {status['resource_stats']}")

    # 访问资源
    resource = rm.access_resource("test_resource")
    print(f"访问资源: {resource}")

    # 清理
    rm.cleanup_all()
    print("✅ 基本测试完成")

if __name__ == "__main__":
    test_simple()