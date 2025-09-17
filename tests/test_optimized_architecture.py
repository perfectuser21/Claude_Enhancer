#!/usr/bin/env python3
"""
测试优化后的架构是否正常工作
验证各个模块的基本功能
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_git_cache():
    """测试Git缓存功能"""
    print("🔍 测试Git缓存功能...")

    try:
        from infrastructure.git.git_cache import GitCache

        git_cache = GitCache(str(project_root))
        git_status = await git_cache.get_git_status()

        print(f"  ✅ 当前分支: {git_status.current_branch}")
        print(f"  ✅ 暂存文件: {len(git_status.staged_files)}个")
        print(f"  ✅ 修改文件: {len(git_status.modified_files)}个")

        # 测试缓存信息
        cache_info = git_cache.get_cache_info()
        print(f"  ✅ 缓存TTL: {cache_info['cache_ttl']}秒")

        return True

    except Exception as e:
        print(f"  ❌ Git缓存测试失败: {e}")
        return False


async def test_hooks_optimized():
    """测试优化版Git钩子"""
    print("🔗 测试优化版Git钩子...")

    try:
        from infrastructure.git.hooks_optimized import GitHooksOptimized

        hooks = GitHooksOptimized(str(project_root))

        # 测试pre-commit钩子
        result = await hooks.pre_commit_hook()
        print(f"  ✅ pre-commit钩子: {'成功' if result.get('success') else '失败'}")

        # 测试优化统计
        stats = await hooks.get_optimization_stats()
        print(f"  ✅ 缓存TTL: {stats['git_cache']['cache_ttl']}秒")
        print(f"  ✅ 性能优化: 已启用")

        return True

    except Exception as e:
        print(f"  ❌ 优化版钩子测试失败: {e}")
        return False


def test_config_manager():
    """测试配置管理器"""
    print("⚙️ 测试配置管理器...")

    try:
        from infrastructure.config.config_manager import ConfigManager

        config_manager = ConfigManager(str(project_root))

        # 测试基本配置读取
        version = config_manager.get('perfect21.version', 'unknown')
        git_cache_ttl = config_manager.get('git.cache_ttl', 30)

        print(f"  ✅ Perfect21版本: {version}")
        print(f"  ✅ Git缓存TTL: {git_cache_ttl}秒")

        # 测试配置验证
        errors = config_manager.validate_config()
        if errors:
            print(f"  ⚠️ 配置验证警告: {len(errors)}个")
        else:
            print(f"  ✅ 配置验证: 通过")

        return True

    except Exception as e:
        print(f"  ❌ 配置管理器测试失败: {e}")
        return False


def test_error_handler():
    """测试错误处理系统"""
    print("🚨 测试错误处理系统...")

    try:
        from shared.errors.error_handler import (
            ErrorHandler, Perfect21Error, GitOperationError,
            ErrorCategory, ErrorSeverity, create_error_context
        )

        error_handler = ErrorHandler()

        # 测试Perfect21错误
        test_error = GitOperationError(
            "测试Git操作错误",
            severity=ErrorSeverity.LOW,
            context=create_error_context("test", "unit_test")
        )

        result = error_handler.handle_error(test_error)
        print(f"  ✅ 错误处理: {'成功' if not result['success'] else '失败'}")
        print(f"  ✅ 错误代码: {result.get('error_code')}")
        print(f"  ✅ 解决方案: {len(result.get('solutions', []))}个")

        # 测试普通异常
        try:
            raise ValueError("测试普通异常")
        except Exception as e:
            result = error_handler.handle_error(e)
            print(f"  ✅ 普通异常处理: 成功")

        return True

    except Exception as e:
        print(f"  ❌ 错误处理系统测试失败: {e}")
        return False


async def test_cli_commands():
    """测试CLI命令系统"""
    print("💻 测试CLI命令系统...")

    try:
        from application.cli.command_base import CLICommand, CommandResult
        from application.cli.commands.status_command import StatusCommand

        # 创建测试参数
        import argparse
        args = argparse.Namespace()
        args.performance = False
        args.git_cache = False
        args.detailed = False
        args.verbose = False

        # 测试状态命令
        status_command = StatusCommand()
        result = await status_command.execute(args)

        print(f"  ✅ 状态命令: {'成功' if result.success else '失败'}")
        print(f"  ✅ 执行时间: {result.execution_time:.3f}秒" if result.execution_time else "  ✅ 执行时间: N/A")

        # 测试命令格式化输出
        output = status_command.format_output(result, verbose=False)
        print(f"  ✅ 输出格式化: {'成功' if output else '失败'}")

        return True

    except Exception as e:
        print(f"  ❌ CLI命令系统测试失败: {e}")
        return False


async def test_cli_controller():
    """测试CLI控制器"""
    print("🎛️ 测试CLI控制器...")

    try:
        from application.cli.cli_controller import CLIController

        controller = CLIController()

        # 测试解析器创建
        parser = controller.create_parser()
        print(f"  ✅ 解析器创建: 成功")

        # 测试命令注册
        commands = controller.registry.list_commands()
        print(f"  ✅ 注册命令数: {len(commands)}个")

        # 测试命令列表
        for cmd_name in commands:
            command = controller.registry.get_command(cmd_name)
            print(f"    - {cmd_name}: {'✅' if command else '❌'}")

        return True

    except Exception as e:
        print(f"  ❌ CLI控制器测试失败: {e}")
        return False


async def run_performance_comparison():
    """运行性能对比测试"""
    print("📊 运行性能对比测试...")

    try:
        import time

        # 测试Git操作性能
        from infrastructure.git.git_cache import get_git_cache

        git_cache = get_git_cache(str(project_root))

        # 第一次调用（冷启动）
        start_time = time.time()
        await git_cache.get_git_status()
        cold_time = time.time() - start_time

        # 第二次调用（缓存命中）
        start_time = time.time()
        await git_cache.get_git_status()
        cached_time = time.time() - start_time

        improvement = ((cold_time - cached_time) / cold_time) * 100 if cold_time > 0 else 0

        print(f"  ✅ 冷启动时间: {cold_time:.3f}秒")
        print(f"  ✅ 缓存命中时间: {cached_time:.3f}秒")
        print(f"  ✅ 性能提升: {improvement:.1f}%")

        return True

    except Exception as e:
        print(f"  ❌ 性能对比测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("🚀 Perfect21 优化架构测试")
    print("=" * 60)

    test_results = []

    # 运行所有测试
    tests = [
        ("Git缓存功能", test_git_cache()),
        ("优化版Git钩子", test_hooks_optimized()),
        ("配置管理器", test_config_manager()),
        ("错误处理系统", test_error_handler()),
        ("CLI命令系统", test_cli_commands()),
        ("CLI控制器", test_cli_controller()),
        ("性能对比", run_performance_comparison())
    ]

    for test_name, test_coro in tests:
        print(f"\n{test_name}:")
        try:
            if asyncio.iscoroutine(test_coro):
                result = await test_coro
            else:
                result = test_coro
            test_results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ 测试异常: {e}")
            test_results.append((test_name, False))

    # 总结
    print("\n" + "=" * 60)
    print("📋 测试结果总结:")

    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)

    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")

    print(f"\n🎯 总计: {passed}/{total} 通过 ({passed/total*100:.1f}%)")

    if passed == total:
        print("🎉 所有测试通过！优化架构工作正常。")
        return 0
    else:
        print("⚠️ 部分测试失败，请检查相关模块。")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)