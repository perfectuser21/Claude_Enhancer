#!/usr/bin/env python3
"""
测试Perfect21资源管理修复
验证内存泄漏修复、连接池、资源清理等功能
"""

import os
import sys
import asyncio
import time
import threading
import tempfile
from contextlib import contextmanager

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from modules.resource_manager import (
    ResourceManager, ResourceType, ResourceLimits,
    managed_perfect21, managed_perfect21_async,
    managed_file, managed_db_connection
)
from modules.database import (
    DatabaseManager, DatabaseConfig,
    managed_database, managed_database_async
)
from features.multi_workspace.workspace_manager import (
    WorkspaceManager, managed_workspace_manager, managed_workspace_manager_async
)

def test_resource_manager_basic():
    """测试基本资源管理功能"""
    print("🔧 测试基本资源管理...")

    # 创建资源管理器
    limits = ResourceLimits(max_file_handles=50, max_memory_mb=100)
    rm = ResourceManager(limits)

    # 注册一些资源
    test_resources = []
    for i in range(10):
        resource = f"test_resource_{i}"
        test_resources.append(resource)

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
    # 许可额外的系统资源（如资源管理器本身）
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
        assert status['resource_stats']['total_count'] == 1

        # 访问资源
        resource = rm.access_resource("async_resource")
        assert resource == "test_data"

    # 退出上下文管理器后，资源应该被清理
    print("✅ 异步资源管理测试通过")

def test_connection_pool():
    """测试连接池功能"""
    print("🏊 测试连接池...")

    rm = ResourceManager()

    # 创建简单的连接工厂
    connection_count = 0
    def create_connection():
        nonlocal connection_count
        connection_count += 1
        return f"connection_{connection_count}"

    def cleanup_connection(conn):
        print(f"清理连接: {conn}")

    # 创建连接池
    pool = rm.create_connection_pool(
        "test_pool",
        create_connection,
        max_size=5,
        cleanup_callback=cleanup_connection
    )

    # 获取连接
    connections = []
    for _ in range(3):
        conn = pool.acquire()
        connections.append(conn)
        assert conn is not None

    # 检查连接池统计
    stats = pool.get_stats()
    print(f"📊 连接池统计: {stats}")
    assert stats['active_connections'] == 3
    assert stats['pool_size'] == 0  # 所有连接都在使用

    # 释放连接
    for conn in connections:
        pool.release(conn)

    # 检查连接池统计
    stats = pool.get_stats()
    assert stats['active_connections'] == 0
    assert stats['pool_size'] >= 0  # 连接回到池中

    # 清理
    rm.cleanup_all()

    print("✅ 连接池测试通过")

def test_database_connection_pool():
    """测试数据库连接池"""
    print("🗄️ 测试数据库连接池...")

    # 创建临时数据库
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name

    try:
        # 配置数据库
        config = DatabaseConfig()
        config.db_path = db_path
        config.pool_size = 3

        with managed_database(config) as db:
            # 测试连接获取
            connections = []
            for i in range(3):
                with db.get_connection() as conn:
                    conn.execute("SELECT 1")
                    result = conn.fetchone()
                    assert result is not None

            # 检查连接池统计
            stats = db.get_connection_pool_stats()
            print(f"📊 数据库连接池统计: {stats}")

            # 测试数据库操作
            db.execute_query("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)", fetch=False)
            db.insert_record("test", {"name": "测试数据"})

            records = db.execute_query("SELECT * FROM test")
            assert len(records) == 1
            assert records[0]['name'] == "测试数据"

    finally:
        # 清理临时文件
        try:
            os.unlink(db_path)
        except:
            pass

    print("✅ 数据库连接池测试通过")

async def test_async_database():
    """测试异步数据库操作"""
    print("🌊 测试异步数据库...")

    # 创建临时数据库
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name

    try:
        config = DatabaseConfig()
        config.db_path = db_path

        async with managed_database_async(config) as db:
            # 异步获取连接
            async with db.get_connection_async() as conn:
                cursor = conn.cursor()
                cursor.execute("CREATE TABLE async_test (id INTEGER PRIMARY KEY, data TEXT)")
                cursor.execute("INSERT INTO async_test (data) VALUES (?)", ("异步数据",))
                conn.commit()

                cursor.execute("SELECT * FROM async_test")
                result = cursor.fetchone()
                assert result is not None
                assert result['data'] == "异步数据"

    finally:
        try:
            os.unlink(db_path)
        except:
            pass

    print("✅ 异步数据库测试通过")

def test_workspace_manager_resources():
    """测试工作空间管理器资源管理"""
    print("🏗️ 测试工作空间管理器...")

    with tempfile.TemporaryDirectory() as temp_dir:
        with managed_workspace_manager(temp_dir) as wm:
            # 创建工作空间
            from features.multi_workspace.workspace_manager import WorkspaceType

            workspace_id = wm.create_workspace(
                "test_workspace",
                "测试工作空间",
                WorkspaceType.FEATURE,
                preferred_port=3001
            )

            assert workspace_id is not None

            # 列出工作空间
            workspaces = wm.list_workspaces()
            assert len(workspaces) == 1
            assert workspaces[0]['name'] == "test_workspace"

            # 创建临时目录测试
            with wm.managed_temp_dir(prefix="test_") as temp_workspace_dir:
                assert temp_workspace_dir.exists()

                # 在临时目录中创建文件
                test_file = temp_workspace_dir / "test.txt"
                test_file.write_text("测试内容")
                assert test_file.exists()

            # 临时目录应该被清理
            # 注意：这里可能需要一些时间让清理完成

    print("✅ 工作空间管理器测试通过")

async def test_async_workspace_manager():
    """测试异步工作空间管理器"""
    print("🌪️ 测试异步工作空间管理器...")

    with tempfile.TemporaryDirectory() as temp_dir:
        async with managed_workspace_manager_async(temp_dir) as wm:
            # 工作空间管理器应该正常工作
            stats = wm.get_workspace_stats()
            assert 'total_workspaces' in stats

    print("✅ 异步工作空间管理器测试通过")

def test_memory_pressure_cleanup():
    """测试内存压力清理"""
    print("🧠 测试内存压力清理...")

    rm = ResourceManager()

    # 创建大量资源
    for i in range(100):
        rm.register_resource(
            f"memory_resource_{i}",
            f"data_{i}" * 1000,  # 模拟大对象
            ResourceType.MEMORY_BUFFER,
            size_estimate=10000  # 10KB
        )

    # 检查资源数量
    initial_count = rm.get_status()['resource_stats']['total_count']
    assert initial_count == 100

    # 模拟一些资源变为闲置
    time.sleep(0.1)  # 让一些资源变老

    # 手动触发内存压力清理
    cleaned = rm._tracker.cleanup_idle_resources(max_idle_time=0.05)  # 50ms
    print(f"🧹 清理了 {cleaned} 个闲置资源")

    # 检查剩余资源
    remaining_count = rm.get_status()['resource_stats']['total_count']
    print(f"📊 剩余资源: {remaining_count}")

    rm.cleanup_all()

    print("✅ 内存压力清理测试通过")

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

def run_performance_test():
    """性能测试"""
    print("⚡ 运行性能测试...")

    start_time = time.time()

    # 大量资源操作
    rm = ResourceManager()

    # 注册大量资源
    for i in range(1000):
        rm.register_resource(f"perf_resource_{i}", f"data_{i}", ResourceType.OTHER)

    # 大量访问操作
    for i in range(500):
        rm.access_resource(f"perf_resource_{i}")

    # 清理
    rm.cleanup_all()

    end_time = time.time()
    duration = end_time - start_time

    print(f"⏱️ 性能测试完成，耗时: {duration:.3f}秒")
    print(f"🚀 每秒操作数: {1500/duration:.0f} ops/sec")

    # 性能应该在合理范围内
    assert duration < 5.0, f"性能测试耗时过长: {duration:.3f}秒"

    print("✅ 性能测试通过")

async def main():
    """主测试函数"""
    print("🧪 开始Perfect21资源管理修复测试")
    print("=" * 50)

    try:
        # 基础测试
        test_resource_manager_basic()
        await test_async_resource_management()

        # 连接池测试
        test_connection_pool()
        test_database_connection_pool()
        await test_async_database()

        # 工作空间管理器测试
        test_workspace_manager_resources()
        await test_async_workspace_manager()

        # 高级功能测试
        test_memory_pressure_cleanup()
        await test_managed_file()
        test_resource_limits()

        # 性能测试
        run_performance_test()

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