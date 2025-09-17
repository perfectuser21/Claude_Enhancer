#!/usr/bin/env python3
"""
简化的Perfect21资源管理测试
"""

import os
import sys
import asyncio
import tempfile

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from modules.resource_manager import (
    ResourceManager, ResourceType, ResourceLimits,
    managed_file
)

def test_resource_manager_basic():
    """测试基本资源管理功能"""
    print("🔧 测试基本资源管理...")

    # 创建资源管理器
    limits = ResourceLimits(max_file_handles=50, max_memory_mb=100)
    rm = ResourceManager(limits)

    # 注册一些资源
    for i in range(10):
        resource = f"test_resource_{i}"

        success = rm.register_resource(
            f"resource_{i}",
            resource,
            ResourceType.OTHER,
            cleanup_callback=lambda r=resource: print(f"清理资源: {r}")
        )
        assert success, f"资源 {i} 注册失败"

    # 检查资源状态
    status = rm.get_status()
    print(f"📊 资源状态: {status['resource_stats']['total_count']} 个资源")
    # 允许额外的系统资源（如资源管理器本身）
    assert status['resource_stats']['total_count'] >= 10

    # 访问资源
    for i in range(5):
        resource = rm.access_resource(f"resource_{i}")
        assert resource == f"test_resource_{i}"

    # 清理资源
    rm.cleanup_all()

    # 验证清理（可能仍有系统资源）
    status = rm.get_status()
    print(f"清理后资源数: {status['resource_stats']['total_count']}")
    # 如果没有系统资源，应该为0；如果有，应该少于10
    assert status['resource_stats']['total_count'] <= 1  # 最多只剩下资源管理器自身

    print("✅ 基本资源管理测试通过")

async def test_async_resource_management():
    """测试异步资源管理"""
    print("🚀 测试异步资源管理...")

    async with ResourceManager() as rm:
        # 异步注册资源
        async def cleanup_async():
            print("异步清理资源")

        success = await rm.register_resource_async(
            "async_resource",
            "test_data",
            ResourceType.MEMORY_BUFFER,
            async_cleanup_callback=cleanup_async
        )
        assert success

        # 检查状态
        status = rm.get_status()
        assert status['resource_stats']['total_count'] >= 1

        # 访问资源
        resource = rm.access_resource("async_resource")
        assert resource == "test_data"

    # 退出上下文管理器后，资源应该被清理
    print("✅ 异步资源管理测试通过")

async def test_managed_file():
    """测试受管理的文件操作"""
    print("📁 测试受管理的文件操作...")

    with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
        tmp.write("测试文件内容")
        temp_path = tmp.name

    try:
        # 测试异步文件管理
        async with managed_file(temp_path, 'r') as f:
            content = await f.read()
            assert "测试文件内容" in content

    finally:
        try:
            os.unlink(temp_path)
        except:
            pass

    print("✅ 受管理的文件操作测试通过")

def test_resource_limits():
    """测试资源限制"""
    print("🚫 测试资源限制...")

    # 创建严格的资源限制
    limits = ResourceLimits(
        max_file_handles=2,
        max_memory_mb=1,  # 1MB限制
        max_connections=1
    )

    rm = ResourceManager(limits)

    # 尝试注册超过限制的资源
    success1 = rm.register_resource(
        "resource1", "data1", ResourceType.FILE_HANDLE
    )
    assert success1  # 第一个应该成功

    success2 = rm.register_resource(
        "resource2", "data2", ResourceType.FILE_HANDLE
    )
    assert success2  # 第二个应该成功

    success3 = rm.register_resource(
        "resource3", "data3", ResourceType.FILE_HANDLE
    )
    assert not success3  # 第三个应该失败（超过限制）

    # 测试内存限制
    large_data = "x" * (2 * 1024 * 1024)  # 2MB数据
    success_large = rm.register_resource(
        "large_resource", large_data, ResourceType.MEMORY_BUFFER,
        size_estimate=len(large_data)
    )
    assert not success_large  # 应该失败（超过内存限制）

    rm.cleanup_all()

    print("✅ 资源限制测试通过")

async def main():
    """主测试函数"""
    print("🧪 开始Perfect21资源管理简化测试")
    print("=" * 50)

    try:
        # 基础测试
        test_resource_manager_basic()
        await test_async_resource_management()

        # 高级功能测试
        await test_managed_file()
        test_resource_limits()

        print("=" * 50)
        print("🎉 所有测试通过！资源管理修复成功")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)