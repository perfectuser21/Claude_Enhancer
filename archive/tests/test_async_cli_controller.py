#!/usr/bin/env python3
"""
测试修复后的异步CLI控制器
验证异步/同步混用问题是否解决
"""

import asyncio
import sys
import logging
import time
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("AsyncCLITest")


async def test_basic_async_operations():
    """测试基本异步操作"""
    logger.info("🧪 测试基本异步操作")

    try:
        from application.cli.cli_controller import get_cli_controller

        # 使用异步上下文管理器
        async with get_cli_controller() as controller:
            logger.info("✅ CLI控制器初始化成功")

            # 测试并发命令调度
            tasks = []
            for i in range(3):
                logger.info(f"📝 创建测试任务 {i+1}")
                # 模拟并发命令
                task = asyncio.create_task(
                    asyncio.sleep(0.1)  # 简单的异步操作
                )
                tasks.append(task)

            # 等待所有任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            logger.info(f"✅ 并发任务完成: {len(results)} 个")

        logger.info("✅ CLI控制器清理成功")
        return True

    except Exception as e:
        logger.error(f"❌ 基本异步操作测试失败: {e}", exc_info=True)
        return False


async def test_command_execution():
    """测试命令执行"""
    logger.info("🧪 测试命令执行")

    try:
        from application.cli.cli_controller import get_cli_controller
        import argparse

        async with get_cli_controller() as controller:
            # 创建模拟参数
            args = argparse.Namespace()
            args.command = 'status'
            args.verbose = False
            args.performance = False

            # 执行命令
            result = await controller.execute_command('status', args)

            if result.success:
                logger.info("✅ 状态命令执行成功")
                logger.info(f"📊 执行时间: {result.execution_time:.3f}秒")
            else:
                logger.warning(f"⚠️ 状态命令执行失败: {result.message}")

            return result.success

    except Exception as e:
        logger.error(f"❌ 命令执行测试失败: {e}", exc_info=True)
        return False


async def test_timeout_handling():
    """测试超时处理"""
    logger.info("🧪 测试超时处理")

    try:
        from application.cli.command_base import AsyncCLICommand, CommandResult
        import argparse

        class TimeoutTestCommand(AsyncCLICommand):
            def __init__(self):
                super().__init__('timeout_test', '超时测试命令')

            async def execute(self, args):
                # 模拟长时间运行的命令
                await asyncio.sleep(0.5)
                return CommandResult(success=True, message="超时测试完成")

            def setup_parser(self, parser):
                pass

        command = TimeoutTestCommand()
        args = argparse.Namespace()
        args.timeout = 0.1  # 设置100ms超时

        # 测试超时
        result = await command.execute_with_error_handling(args)

        if result.error_code == "COMMAND_TIMEOUT":
            logger.info("✅ 超时处理正常工作")
            return True
        else:
            logger.warning(f"⚠️ 超时处理异常: {result.message}")
            return False

    except Exception as e:
        logger.error(f"❌ 超时处理测试失败: {e}", exc_info=True)
        return False


async def test_cancellation_handling():
    """测试取消处理"""
    logger.info("🧪 测试取消处理")

    try:
        from application.cli.command_base import AsyncCLICommand, CommandResult
        import argparse

        class CancelTestCommand(AsyncCLICommand):
            def __init__(self):
                super().__init__('cancel_test', '取消测试命令')

            async def execute(self, args):
                try:
                    await asyncio.sleep(1.0)  # 长时间运行
                    return CommandResult(success=True, message="取消测试完成")
                except asyncio.CancelledError:
                    return CommandResult(
                        success=False,
                        message="命令被取消",
                        error_code="CANCELLED"
                    )

            def setup_parser(self, parser):
                pass

        command = CancelTestCommand()
        args = argparse.Namespace()

        # 创建任务并取消
        task = asyncio.create_task(command.execute_with_error_handling(args))
        await asyncio.sleep(0.1)  # 让任务开始执行
        task.cancel()

        result = await task

        if result.error_code == "COMMAND_CANCELLED":
            logger.info("✅ 取消处理正常工作")
            return True
        else:
            logger.warning(f"⚠️ 取消处理异常: {result.message}")
            return False

    except Exception as e:
        logger.error(f"❌ 取消处理测试失败: {e}", exc_info=True)
        return False


async def test_concurrent_commands():
    """测试并发命令处理"""
    logger.info("🧪 测试并发命令处理")

    try:
        from application.cli.cli_controller import get_cli_controller
        import argparse

        async with get_cli_controller() as controller:
            # 创建多个并发命令
            tasks = []
            for i in range(3):
                args = argparse.Namespace()
                args.command = 'status'
                args.verbose = False
                args.performance = False

                task = asyncio.create_task(
                    controller.execute_command('status', args)
                )
                tasks.append(task)

            # 并发执行
            results = await asyncio.gather(*tasks, return_exceptions=True)

            success_count = sum(1 for r in results if isinstance(r, object) and hasattr(r, 'success') and r.success)

            logger.info(f"✅ 并发命令完成: {success_count}/{len(results)} 成功")
            return success_count > 0

    except Exception as e:
        logger.error(f"❌ 并发命令测试失败: {e}", exc_info=True)
        return False


async def test_resource_cleanup():
    """测试资源清理"""
    logger.info("🧪 测试资源清理")

    try:
        from application.cli.cli_controller import get_cli_controller

        # 测试多次创建和销毁
        for i in range(3):
            async with get_cli_controller() as controller:
                logger.info(f"📝 创建控制器实例 {i+1}")
                # 简单操作
                await asyncio.sleep(0.01)
            logger.info(f"🗑️ 销毁控制器实例 {i+1}")

        logger.info("✅ 资源清理测试完成")
        return True

    except Exception as e:
        logger.error(f"❌ 资源清理测试失败: {e}", exc_info=True)
        return False


async def main():
    """运行所有测试"""
    logger.info("🚀 开始异步CLI控制器测试")
    start_time = time.time()

    tests = [
        ("基本异步操作", test_basic_async_operations),
        ("命令执行", test_command_execution),
        ("超时处理", test_timeout_handling),
        ("取消处理", test_cancellation_handling),
        ("并发命令处理", test_concurrent_commands),
        ("资源清理", test_resource_cleanup),
    ]

    results = {}

    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"🧪 运行测试: {test_name}")
        logger.info(f"{'='*50}")

        try:
            result = await test_func()
            results[test_name] = result
            status = "✅ 通过" if result else "❌ 失败"
            logger.info(f"📊 测试结果: {status}")
        except Exception as e:
            results[test_name] = False
            logger.error(f"❌ 测试异常: {e}", exc_info=True)

    # 总结
    total_time = time.time() - start_time
    passed = sum(1 for r in results.values() if r)
    total = len(results)

    logger.info(f"\n{'='*60}")
    logger.info(f"📊 测试总结")
    logger.info(f"{'='*60}")
    logger.info(f"✅ 通过: {passed}/{total}")
    logger.info(f"⏱️ 总时间: {total_time:.2f}秒")

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {test_name}: {status}")

    if passed == total:
        logger.info("🎉 所有测试通过！异步CLI控制器工作正常")
        return 0
    else:
        logger.error(f"💥 {total - passed} 个测试失败")
        return 1


if __name__ == '__main__':
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("👋 测试被用户中断")
        sys.exit(130)
    except Exception as e:
        logger.error(f"💥 测试运行失败: {e}", exc_info=True)
        sys.exit(1)