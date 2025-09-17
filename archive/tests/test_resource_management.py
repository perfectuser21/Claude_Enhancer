#!/usr/bin/env python3
"""
Perfect21 资源管理测试
验证资源管理器是否正确修复了内存泄漏问题
"""

import sys
import os
import gc
import time
import tracemalloc
from contextlib import suppress

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__)))

from modules.resource_manager import ResourceManager, managed_perfect21, ResourceTracker
from main.perfect21 import Perfect21

def test_resource_manager_basic():
    """测试基础资源管理功能"""
    print("🧪 测试基础资源管理功能...")

    rm = ResourceManager()

    # 测试资源注册
    test_resource = {"test": "data"}
    cleanup_called = False

    def cleanup_callback():
        nonlocal cleanup_called
        cleanup_called = True
        print("  ✅ 清理回调被调用")

    rm.register_resource("test_resource", test_resource, cleanup_callback)

    # 检查状态
    status = rm.get_status()
    print(f"  📊 资源数量: {status['resource_count']}")

    # 清理资源
    rm.unregister_resource("test_resource")

    if cleanup_called:
        print("  ✅ 资源管理器基础功能正常")
        return True
    else:
        print("  ❌ 清理回调未被调用")
        return False

def test_context_manager():
    """测试上下文管理器"""
    print("\n🧪 测试上下文管理器...")

    # 启动内存跟踪
    tracemalloc.start()

    # 记录初始内存
    initial_memory = tracemalloc.get_traced_memory()[0]
    print(f"  📊 初始内存: {initial_memory / 1024:.2f} KB")

    # 使用上下文管理器
    try:
        with managed_perfect21() as p21:
            # 执行一些操作
            status = p21.status()
            print(f"  ✅ Perfect21状态: {status['success']}")

            # 记录使用中的内存
            current_memory = tracemalloc.get_traced_memory()[0]
            print(f"  📊 使用中内存: {current_memory / 1024:.2f} KB")

        # 强制垃圾回收
        gc.collect()
        time.sleep(0.1)  # 给一点时间让清理完成

        # 记录清理后的内存
        final_memory = tracemalloc.get_traced_memory()[0]
        print(f"  📊 清理后内存: {final_memory / 1024:.2f} KB")

        # 计算内存差异
        memory_diff = final_memory - initial_memory
        print(f"  📊 内存差异: {memory_diff / 1024:.2f} KB")

        # 如果内存差异小于100KB，认为没有严重泄漏
        if abs(memory_diff) < 100 * 1024:
            print("  ✅ 无明显内存泄漏")
            return True
        else:
            print(f"  ⚠️ 可能存在内存泄漏，差异: {memory_diff / 1024:.2f} KB")
            return False

    except Exception as e:
        print(f"  ❌ 上下文管理器测试失败: {e}")
        traceback.print_exc()
        return False
    finally:
        tracemalloc.stop()

def test_multiple_instances():
    """测试多实例场景"""
    print("\n🧪 测试多实例场景...")

    instances = []
    try:
        # 创建多个实例
        for i in range(5):
            with managed_perfect21() as p21:
                instances.append(p21)
                print(f"  ✅ 实例 {i+1} 创建成功")

        # 清理所有实例
        Perfect21.cleanup_all_instances()
        print("  ✅ 所有实例已清理")

        return True

    except Exception as e:
        print(f"  ❌ 多实例测试失败: {e}")
        return False

def test_exception_safety():
    """测试异常安全性"""
    print("\n🧪 测试异常安全性...")

    try:
        with managed_perfect21() as p21:
            # 模拟异常
            raise ValueError("测试异常")
    except ValueError:
        print("  ✅ 异常被正确捕获")

        # 验证资源是否被正确清理
        rm = ResourceManager()
        status = rm.get_status()

        if status['resource_count'] == 0:
            print("  ✅ 异常情况下资源被正确清理")
            return True
        else:
            print(f"  ❌ 异常情况下仍有 {status['resource_count']} 个资源未清理")
            return False
    except Exception as e:
        print(f"  ❌ 异常安全性测试失败: {e}")
        return False

def test_cli_integration():
    """测试CLI集成"""
    print("\n🧪 测试CLI集成...")

    try:
        # 模拟CLI使用场景
        import subprocess

        # 测试status命令
        result = subprocess.run([
            sys.executable, 'main/cli.py', 'status'
        ], capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            print("  ✅ CLI status命令执行成功")
            print(f"  📊 输出预览: {result.stdout[:100]}...")
            return True
        else:
            print(f"  ❌ CLI命令执行失败: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("  ❌ CLI命令执行超时")
        return False
    except Exception as e:
        print(f"  ❌ CLI集成测试失败: {e}")
        return False

def run_comprehensive_test():
    """运行综合测试"""
    print("🚀 Perfect21 资源管理修复验证")
    print("=" * 50)

    tests = [
        ("基础资源管理", test_resource_manager_basic),
        ("上下文管理器", test_context_manager),
        ("多实例场景", test_multiple_instances),
        ("异常安全性", test_exception_safety),
        ("CLI集成", test_cli_integration),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: 通过")
            else:
                print(f"❌ {test_name}: 失败")
        except Exception as e:
            print(f"❌ {test_name}: 异常 - {e}")

    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")

    if passed == total:
        print("🎉 所有测试通过！资源管理问题已修复")
        return True
    else:
        print("⚠️ 部分测试失败，需要进一步检查")
        return False

if __name__ == '__main__':
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)