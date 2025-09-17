#!/usr/bin/env python3
"""
逐步测试资源管理器功能
"""

import os
import sys
import time

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_imports():
    """测试导入"""
    print("1. 测试导入...")
    try:
        from modules.resource_manager import ResourceManager, ResourceType, ResourceLimits
        print("✅ 导入成功")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_creation():
    """测试创建"""
    print("2. 测试创建资源管理器...")
    try:
        from modules.resource_manager import ResourceManager, ResourceLimits
        limits = ResourceLimits(max_file_handles=50, max_memory_mb=100)
        rm = ResourceManager(limits)
        print("✅ 创建成功")
        return rm
    except Exception as e:
        print(f"❌ 创建失败: {e}")
        return None

def test_register(rm):
    """测试注册"""
    print("3. 测试资源注册...")
    try:
        from modules.resource_manager import ResourceType
        success = rm.register_resource("test", "data", ResourceType.OTHER)
        print(f"✅ 注册{'成功' if success else '失败'}")
        return success
    except Exception as e:
        print(f"❌ 注册失败: {e}")
        return False

def test_async():
    """测试异步功能"""
    print("4. 测试异步功能...")
    try:
        import asyncio
        from modules.resource_manager import ResourceManager

        async def async_test():
            async with ResourceManager() as rm:
                # 简单的异步操作
                success = await rm.register_resource_async("async_test", "data")
                return success

        result = asyncio.run(async_test())
        print(f"✅ 异步测试{'成功' if result else '失败'}")
        return result
    except Exception as e:
        print(f"❌ 异步测试失败: {e}")
        return False

def test_database():
    """测试数据库模块"""
    print("5. 测试数据库模块...")
    try:
        from modules.database import DatabaseManager, DatabaseConfig
        print("✅ 数据库模块导入成功")

        # 不实际创建数据库，只测试导入
        return True
    except Exception as e:
        print(f"❌ 数据库模块测试失败: {e}")
        return False

def main():
    """主测试"""
    print("🧪 开始逐步测试")
    print("=" * 40)

    # 1. 测试导入
    if not test_imports():
        return False

    # 2. 测试创建
    rm = test_creation()
    if not rm:
        return False

    # 3. 测试注册
    if not test_register(rm):
        return False

    # 4. 测试异步
    if not test_async():
        return False

    # 5. 测试数据库
    if not test_database():
        return False

    print("=" * 40)
    print("🎉 所有测试通过！")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)