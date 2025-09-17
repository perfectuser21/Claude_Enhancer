#!/usr/bin/env python3
"""
测试资源管理器但不包含managed_file
"""

import os
import sys
import asyncio

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from modules.resource_manager import ResourceManager, ResourceType, ResourceLimits

def test_basic():
    """基本测试"""
    print("🔧 测试基本资源管理...")

    rm = ResourceManager()
    success = rm.register_resource("test", "data", ResourceType.OTHER)
    print(f"注册: {success}")

    status = rm.get_status()
    print(f"资源数: {status['resource_stats']['total_count']}")

    rm.cleanup_all()
    print("✅ 基本测试完成")

async def test_async():
    """异步测试"""
    print("🚀 测试异步...")

    async with ResourceManager() as rm:
        success = await rm.register_resource_async("async_test", "data")
        print(f"异步注册: {success}")

    print("✅ 异步测试完成")

async def main():
    """主函数"""
    print("🧪 开始测试")
    print("=" * 30)

    test_basic()
    await test_async()

    print("=" * 30)
    print("🎉 测试完成")

if __name__ == "__main__":
    asyncio.run(main())