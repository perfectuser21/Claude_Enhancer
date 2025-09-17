#!/usr/bin/env python3
"""
CLI命令基类 - 命令模式实现
提供统一的命令接口和错误处理
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import argparse
from dataclasses import dataclass

logger = logging.getLogger("CLICommand")


@dataclass
class CommandResult:
    """命令执行结果"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    execution_time: Optional[float] = None


class CLICommand(ABC):
    """CLI命令基类"""

    def __init__(self, name: str, description: str):
        """
        初始化命令

        Args:
            name: 命令名称
            description: 命令描述
        """
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"Command.{name}")

    @abstractmethod
    async def execute(self, args: argparse.Namespace) -> CommandResult:
        """
        执行命令

        Args:
            args: 命令行参数

        Returns:
            CommandResult: 执行结果
        """
        pass

    @abstractmethod
    def setup_parser(self, parser: argparse.ArgumentParser) -> None:
        """
        设置参数解析器

        Args:
            parser: ArgumentParser实例
        """
        pass

    async def execute_with_error_handling(self, args: argparse.Namespace) -> CommandResult:
        """
        带错误处理的异步命令执行

        Args:
            args: 命令行参数

        Returns:
            CommandResult: 执行结果
        """
        import time
        start_time = time.time()

        try:
            self.logger.info(f"开始执行命令: {self.name}")

            # 使用超时保护
            timeout = getattr(args, 'timeout', 300)  # 默认5分钟超时

            result = await asyncio.wait_for(
                self.execute(args),
                timeout=timeout
            )

            result.execution_time = time.time() - start_time

            if result.success:
                self.logger.info(f"命令执行成功: {self.name} ({result.execution_time:.2f}s)")
            else:
                self.logger.warning(f"命令执行失败: {self.name} - {result.message}")

            return result

        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            self.logger.error(f"命令执行超时: {self.name} ({execution_time:.2f}s)")

            return CommandResult(
                success=False,
                message=f"命令执行超时 ({timeout}秒)",
                error_code="COMMAND_TIMEOUT",
                execution_time=execution_time
            )

        except asyncio.CancelledError:
            execution_time = time.time() - start_time
            self.logger.info(f"命令执行被取消: {self.name} ({execution_time:.2f}s)")

            return CommandResult(
                success=False,
                message="命令执行被取消",
                error_code="COMMAND_CANCELLED",
                execution_time=execution_time
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"命令执行异常: {self.name} - {e}", exc_info=True)

            return CommandResult(
                success=False,
                message=f"命令执行失败: {str(e)}",
                error_code="COMMAND_EXECUTION_ERROR",
                execution_time=execution_time
            )

    def validate_args(self, args: argparse.Namespace) -> CommandResult:
        """
        验证命令参数（同步版本）

        Args:
            args: 命令行参数

        Returns:
            CommandResult: 验证结果，成功时返回None
        """
        # 子类可以重写此方法进行自定义验证
        return CommandResult(success=True, message="参数验证通过")

    async def validate_args_async(self, args: argparse.Namespace) -> CommandResult:
        """
        异步验证命令参数

        Args:
            args: 命令行参数

        Returns:
            CommandResult: 验证结果
        """
        # 默认调用同步版本，子类可以重写进行异步验证
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.validate_args, args)

    def format_output(self, result: CommandResult, verbose: bool = False) -> str:
        """
        格式化输出

        Args:
            result: 命令执行结果
            verbose: 是否详细输出

        Returns:
            str: 格式化后的输出
        """
        if result.success:
            output = f"✅ {result.message}"
            if verbose and result.data:
                output += "\n" + self._format_data(result.data)
        else:
            output = f"❌ {result.message}"
            if verbose and result.error_code:
                output += f"\n错误代码: {result.error_code}"

        if verbose and result.execution_time:
            output += f"\n执行时间: {result.execution_time:.2f}秒"

        return output

    def _format_data(self, data: Dict[str, Any], indent: int = 0) -> str:
        """格式化数据输出"""
        lines = []
        prefix = "  " * indent

        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}{key}:")
                lines.append(self._format_data(value, indent + 1))
            elif isinstance(value, list):
                lines.append(f"{prefix}{key}: [{len(value)}项]")
                if len(value) <= 5:  # 只显示前5项
                    for item in value:
                        lines.append(f"{prefix}  - {item}")
            else:
                lines.append(f"{prefix}{key}: {value}")

        return "\n".join(lines)


class AsyncCLICommand(CLICommand):
    """异步CLI命令基类 - 提供完整的异步上下文管理"""

    def __init__(self, name: str, description: str, max_concurrent: int = 1):
        super().__init__(name, description)
        self._semaphore = asyncio.Semaphore(max_concurrent)  # 防止并发执行
        self._shutdown_event = asyncio.Event()
        self._running_tasks = set()

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self._initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self._cleanup()

    async def _initialize(self) -> None:
        """异步初始化"""
        # 子类可以重写此方法进行自定义初始化
        pass

    async def _cleanup(self) -> None:
        """异步清理"""
        # 设置关闭信号
        self._shutdown_event.set()

        # 等待所有运行中的任务完成
        if self._running_tasks:
            self.logger.info(f"等待 {len(self._running_tasks)} 个任务完成...")
            await asyncio.gather(*self._running_tasks, return_exceptions=True)

    async def execute_with_concurrency_control(self, args: argparse.Namespace) -> CommandResult:
        """
        带并发控制的命令执行

        Args:
            args: 命令行参数

        Returns:
            CommandResult: 执行结果
        """
        # 检查是否正在关闭
        if self._shutdown_event.is_set():
            return CommandResult(
                success=False,
                message="命令正在关闭，无法执行",
                error_code="COMMAND_SHUTTING_DOWN"
            )

        async with self._semaphore:
            task = asyncio.create_task(self.execute_with_error_handling(args))
            self._running_tasks.add(task)

            try:
                return await task
            finally:
                self._running_tasks.discard(task)

    async def cancel_all_tasks(self) -> None:
        """取消所有运行中的任务"""
        self._shutdown_event.set()

        for task in self._running_tasks.copy():
            if not task.done():
                task.cancel()

        # 等待任务完成
        if self._running_tasks:
            await asyncio.gather(*self._running_tasks, return_exceptions=True)


class CompositeCLICommand(AsyncCLICommand):
    """复合CLI命令 - 支持子命令和异步上下文管理"""

    def __init__(self, name: str, description: str):
        super().__init__(name, description, max_concurrent=3)  # 允许多个子命令并发
        self.subcommands: Dict[str, CLICommand] = {}

    def add_subcommand(self, subcommand: CLICommand) -> None:
        """添加子命令"""
        self.subcommands[subcommand.name] = subcommand

    async def _initialize(self) -> None:
        """初始化所有子命令"""
        await super()._initialize()

        # 如果子命令是异步的，也初始化它们
        for subcommand in self.subcommands.values():
            if isinstance(subcommand, AsyncCLICommand):
                await subcommand._initialize()

    async def _cleanup(self) -> None:
        """清理所有子命令"""
        # 先清理子命令
        cleanup_tasks = []
        for subcommand in self.subcommands.values():
            if isinstance(subcommand, AsyncCLICommand):
                cleanup_tasks.append(subcommand._cleanup())

        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)

        # 然后清理自己
        await super()._cleanup()

    async def execute(self, args: argparse.Namespace) -> CommandResult:
        """执行复合命令"""
        subcommand_name = getattr(args, f'{self.name}_action', None)

        if not subcommand_name:
            return CommandResult(
                success=False,
                message=f"请指定{self.name}子命令",
                error_code="MISSING_SUBCOMMAND"
            )

        if subcommand_name not in self.subcommands:
            return CommandResult(
                success=False,
                message=f"未知的{self.name}子命令: {subcommand_name}",
                error_code="UNKNOWN_SUBCOMMAND"
            )

        subcommand = self.subcommands[subcommand_name]

        # 如果子命令支持并发控制，使用它
        if hasattr(subcommand, 'execute_with_concurrency_control'):
            return await subcommand.execute_with_concurrency_control(args)
        else:
            return await subcommand.execute_with_error_handling(args)

    def setup_parser(self, parser: argparse.ArgumentParser) -> None:
        """设置复合命令解析器"""
        subparsers = parser.add_subparsers(
            dest=f'{self.name}_action',
            help=f'{self.name}子命令'
        )

        for name, subcommand in self.subcommands.items():
            subparser = subparsers.add_parser(name, help=subcommand.description)
            subcommand.setup_parser(subparser)


class CLICommandRegistry:
    """CLI命令注册表"""

    def __init__(self):
        self.commands: Dict[str, CLICommand] = {}

    def register(self, command: CLICommand) -> None:
        """注册命令"""
        self.commands[command.name] = command
        logger.debug(f"注册命令: {command.name}")

    def get_command(self, name: str) -> Optional[CLICommand]:
        """获取命令"""
        return self.commands.get(name)

    def list_commands(self) -> Dict[str, str]:
        """列出所有命令"""
        return {name: cmd.description for name, cmd in self.commands.items()}

    def create_parser(self) -> argparse.ArgumentParser:
        """创建主解析器"""
        parser = argparse.ArgumentParser(
            description='Perfect21 CLI - 性能优化版',
            formatter_class=argparse.RawDescriptionHelpFormatter
        )

        # 全局选项
        parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
        parser.add_argument('--async', action='store_true', help='异步执行模式')

        # 子命令
        subparsers = parser.add_subparsers(dest='command', help='可用命令')

        for name, command in self.commands.items():
            cmd_parser = subparsers.add_parser(name, help=command.description)
            command.setup_parser(cmd_parser)

        return parser


# 全局命令注册表
command_registry = CLICommandRegistry()


def register_command(command: CLICommand) -> None:
    """注册命令的装饰器函数"""
    command_registry.register(command)
    return command