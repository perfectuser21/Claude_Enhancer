#!/usr/bin/env python3
"""
Perfect21 资源管理使用示例
展示如何正确使用资源管理器防止内存泄漏
"""

import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.resource_manager import (
    ResourceManager,
    managed_perfect21,
    ResourcePool
)
from main.perfect21 import Perfect21

def example_1_basic_usage():
    """示例1: 基本使用方法（推荐）"""
    print("📝 示例1: 使用上下文管理器（推荐方法）")

    # 使用上下文管理器自动管理资源
    with managed_perfect21() as p21:
        # 执行Perfect21操作
        status = p21.status()
        print(f"  状态: {status['success']}")

        # 执行其他操作...

    # 退出上下文时自动清理资源
    print("  ✅ 资源已自动清理")

def example_2_manual_management():
    """示例2: 手动资源管理"""
    print("\n📝 示例2: 手动资源管理")

    # 获取资源管理器
    rm = ResourceManager()

    try:
        # 创建Perfect21实例
        p21 = Perfect21()

        # 手动注册到资源管理器
        rm.register_resource("my_perfect21", p21, p21.cleanup)

        # 使用实例
        status = p21.status()
        print(f"  状态: {status['success']}")

    finally:
        # 手动清理
        rm.unregister_resource("my_perfect21")
        print("  ✅ 手动清理完成")

def example_3_custom_resource():
    """示例3: 自定义资源管理"""
    print("\n📝 示例3: 自定义资源管理")

    class CustomResource:
        def __init__(self, name):
            self.name = name
            print(f"  创建资源: {name}")

        def cleanup(self):
            print(f"  清理资源: {self.name}")

    rm = ResourceManager()

    # 创建自定义资源
    resource = CustomResource("测试资源")

    # 注册到资源管理器
    rm.register_resource(
        "custom_resource",
        resource,
        resource.cleanup
    )

    # 获取状态
    status = rm.get_status()
    print(f"  当前资源数量: {status['resource_count']}")

    # 清理
    rm.cleanup_all()
    print("  ✅ 自定义资源已清理")

def example_4_resource_pool():
    """示例4: 资源池使用"""
    print("\n📝 示例4: 资源池使用")

    # 创建资源池
    pool = ResourcePool(max_size=3)

    def create_perfect21():
        return Perfect21()

    # 从池中获取资源
    p21_1 = pool.get_resource(create_perfect21)
    p21_2 = pool.get_resource(create_perfect21)

    print(f"  获取了2个Perfect21实例")

    # 使用资源
    status1 = p21_1.status()
    status2 = p21_2.status()

    print(f"  实例1状态: {status1['success']}")
    print(f"  实例2状态: {status2['success']}")

    # 返回到池中
    pool.return_resource(p21_1)
    pool.return_resource(p21_2)

    # 清空池
    pool.clear_pool()
    print("  ✅ 资源池已清理")

def example_5_error_handling():
    """示例5: 错误处理最佳实践"""
    print("\n📝 示例5: 错误处理")

    try:
        with managed_perfect21() as p21:
            # 模拟一些可能失败的操作
            status = p21.status()

            if not status['success']:
                raise RuntimeError("Perfect21状态检查失败")

            # 模拟异常
            raise ValueError("模拟异常情况")

    except ValueError as e:
        print(f"  捕获异常: {e}")
        print("  ✅ 即使发生异常，资源也会被正确清理")

    except Exception as e:
        print(f"  意外异常: {e}")

def example_6_monitoring():
    """示例6: 资源监控"""
    print("\n📝 示例6: 资源状态监控")

    rm = ResourceManager()

    # 监控初始状态
    initial_status = rm.get_status()
    print(f"  初始资源数量: {initial_status['resource_count']}")

    # 创建一些资源
    resources = []
    for i in range(3):
        with managed_perfect21() as p21:
            resources.append(p21)
            current_status = rm.get_status()
            print(f"  创建资源{i+1}后: {current_status['resource_count']}个资源")

    # 最终清理
    rm.cleanup_all()
    final_status = rm.get_status()
    print(f"  清理后资源数量: {final_status['resource_count']}")

def example_7_cli_integration():
    """示例7: CLI集成示例"""
    print("\n📝 示例7: CLI集成最佳实践")

    def cli_command_with_resource_management(command, *args):
        """模拟CLI命令的资源管理"""
        try:
            with managed_perfect21() as p21:
                if command == 'status':
                    return p21.status()
                elif command == 'hooks':
                    # 模拟hooks操作
                    return {"success": True, "message": "Hooks操作完成"}
                else:
                    return {"success": False, "error": f"未知命令: {command}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # 测试不同命令
    commands = ['status', 'hooks', 'unknown']

    for cmd in commands:
        result = cli_command_with_resource_management(cmd)
        print(f"  命令 '{cmd}': {result['success']}")

    print("  ✅ CLI集成示例完成")

def run_all_examples():
    """运行所有示例"""
    print("🚀 Perfect21 资源管理使用示例")
    print("=" * 60)

    examples = [
        example_1_basic_usage,
        example_2_manual_management,
        example_3_custom_resource,
        example_4_resource_pool,
        example_5_error_handling,
        example_6_monitoring,
        example_7_cli_integration,
    ]

    for example in examples:
        try:
            example()
        except Exception as e:
            print(f"  ❌ 示例执行失败: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("✅ 所有示例执行完成")

    # 显示最终资源状态
    rm = ResourceManager()
    final_status = rm.get_status()
    print(f"📊 最终资源状态: {final_status}")

if __name__ == '__main__':
    run_all_examples()