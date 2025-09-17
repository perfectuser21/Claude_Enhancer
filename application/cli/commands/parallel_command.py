#!/usr/bin/env python3
"""
并行执行命令处理器 - 性能优化版
使用新的架构和异步执行
"""

import argparse
from typing import Dict, Any

from ..command_base import AsyncCLICommand, CommandResult, CompositeCLICommand


class ParallelExecuteCommand(AsyncCLICommand):
    """并行执行命令"""

    def __init__(self):
        super().__init__('execute', '执行并行任务')

    async def execute(self, args: argparse.Namespace) -> CommandResult:
        """执行并行任务"""
        try:
            # 延迟导入
            from features.smart_decomposer import get_smart_decomposer
            from features.parallel_executor import get_parallel_executor

            if not args.description:
                return CommandResult(
                    success=False,
                    message="请提供任务描述",
                    error_code="MISSING_TASK_DESCRIPTION"
                )

            decomposer = get_smart_decomposer()
            executor = get_parallel_executor()

            # 1. 智能任务分析
            self.logger.info("开始智能任务分析...")
            analysis = await decomposer.decompose_task_async(args.description)

            if not analysis:
                return CommandResult(
                    success=False,
                    message="任务分析失败",
                    error_code="TASK_ANALYSIS_FAILED"
                )

            # 2. 准备并行执行
            self.logger.info("准备并行执行...")
            execution_config = await executor.execute_parallel_task_async(
                args.description,
                analysis,
                force_parallel=getattr(args, 'force_parallel', False)
            )

            if not execution_config.get('ready_for_execution'):
                return CommandResult(
                    success=False,
                    message="并行执行准备失败",
                    error_code="PARALLEL_EXECUTION_NOT_READY"
                )

            return CommandResult(
                success=True,
                message="并行执行配置生成成功",
                data={
                    'analysis': {
                        'complexity': analysis.complexity.value,
                        'execution_mode': analysis.execution_mode,
                        'agent_count': len(analysis.agent_tasks)
                    },
                    'execution_config': execution_config,
                    'instructions': execution_config.get('execution_instructions'),
                    'monitoring': execution_config.get('monitoring_config')
                }
            )

        except Exception as e:
            return CommandResult(
                success=False,
                message=f"并行执行失败: {str(e)}",
                error_code="PARALLEL_EXECUTION_ERROR"
            )

    def setup_parser(self, parser: argparse.ArgumentParser) -> None:
        """设置并行执行命令解析器"""
        parser.add_argument('description', help='任务描述')
        parser.add_argument(
            '--force-parallel',
            action='store_true',
            help='强制并行模式(无论复杂度)'
        )
        parser.add_argument(
            '--min-agents',
            type=int,
            default=2,
            help='最少Agent数量'
        )
        parser.add_argument(
            '--max-agents',
            type=int,
            default=8,
            help='最多Agent数量'
        )

    def format_output(self, result: CommandResult, verbose: bool = False) -> str:
        """格式化并行执行输出"""
        if not result.success:
            return super().format_output(result, verbose)

        data = result.data or {}
        analysis = data.get('analysis', {})
        execution_config = data.get('execution_config', {})

        output = [
            "🚀 Perfect21 智能并行执行器",
            "=" * 60,
            f"📋 任务复杂度: {analysis.get('complexity', 'unknown')}",
            f"🎯 执行模式: {analysis.get('execution_mode', 'unknown')}",
            f"🤖 涉及Agents: {analysis.get('agent_count', 0)}个"
        ]

        if execution_config.get('execution_mode'):
            output.extend([
                f"\n⚡ 并行执行模式: {execution_config['execution_mode']}",
                f"🤖 预计并行agents: {execution_config.get('expected_agents', 0)}个"
            ])

        # 显示执行指令
        instructions = data.get('instructions')
        if instructions and verbose:
            output.extend([
                "\n🎯 Claude Code调用指令:",
                "=" * 80,
                instructions,
                "=" * 80
            ])

        # 显示监控信息
        monitoring = data.get('monitoring')
        if monitoring and verbose:
            output.extend([
                f"\n📊 执行监控信息:",
                f"👥 预期agents: {', '.join(monitoring.get('agent_names', []))}",
                f"⏱️ 预计用时: {monitoring.get('expected_completion_time', 0)}分钟",
                f"🔥 关键agents: {', '.join(monitoring.get('critical_agents', []))}"
            ])

        return "\n".join(output)


class ParallelStatusCommand(AsyncCLICommand):
    """并行执行状态命令"""

    def __init__(self):
        super().__init__('status', '查看并行执行状态')

    async def execute(self, args: argparse.Namespace) -> CommandResult:
        """执行状态查询"""
        try:
            from features.parallel_executor import get_parallel_executor

            executor = get_parallel_executor()
            status = await executor.get_execution_status_async()

            return CommandResult(
                success=True,
                message="并行执行状态查询成功",
                data=status
            )

        except Exception as e:
            return CommandResult(
                success=False,
                message=f"获取并行执行状态失败: {str(e)}",
                error_code="PARALLEL_STATUS_ERROR"
            )

    def setup_parser(self, parser: argparse.ArgumentParser) -> None:
        """设置状态命令解析器"""
        pass

    def format_output(self, result: CommandResult, verbose: bool = False) -> str:
        """格式化状态输出"""
        if not result.success:
            return super().format_output(result, verbose)

        data = result.data or {}
        output = [
            "📊 Perfect21 并行执行状态",
            "=" * 50,
            f"状态: {data.get('status', 'unknown')}"
        ]

        if data.get('status') != 'idle':
            output.extend([
                f"任务: {data.get('task_description', 'unknown')}",
                f"时间: {data.get('timestamp', 'unknown')}",
                f"Agents: {data.get('agent_count', 0)}个",
                f"执行模式: {data.get('execution_mode', 'unknown')}"
            ])
        else:
            output.extend([
                "💡 当前没有活跃的并行执行任务",
                "💡 使用 'python3 main/cli.py parallel execute \"任务描述\"' 开始新任务"
            ])

        return "\n".join(output)


class ParallelHistoryCommand(AsyncCLICommand):
    """并行执行历史命令"""

    def __init__(self):
        super().__init__('history', '查看执行历史')

    async def execute(self, args: argparse.Namespace) -> CommandResult:
        """执行历史查询"""
        try:
            from features.parallel_executor import get_parallel_executor

            executor = get_parallel_executor()
            limit = getattr(args, 'limit', 5)
            history = await executor.get_execution_history_async(limit)

            return CommandResult(
                success=True,
                message="并行执行历史查询成功",
                data={'history': history, 'limit': limit}
            )

        except Exception as e:
            return CommandResult(
                success=False,
                message=f"获取并行执行历史失败: {str(e)}",
                error_code="PARALLEL_HISTORY_ERROR"
            )

    def setup_parser(self, parser: argparse.ArgumentParser) -> None:
        """设置历史命令解析器"""
        parser.add_argument(
            '--limit',
            type=int,
            default=5,
            help='历史记录显示条数限制'
        )

    def format_output(self, result: CommandResult, verbose: bool = False) -> str:
        """格式化历史输出"""
        if not result.success:
            return super().format_output(result, verbose)

        data = result.data or {}
        history = data.get('history', [])
        limit = data.get('limit', 5)

        if not history:
            return "📝 暂无并行执行历史"

        output = [
            f"📚 Perfect21 并行执行历史 (最近{len(history)}次)",
            "=" * 60
        ]

        for i, summary in enumerate(reversed(history), 1):
            status_icon = "✅" if summary.get('successful_agents') == summary.get('total_agents') else "⚠️"
            task_desc = summary.get('task_description', 'unknown')[:50]

            output.extend([
                f"{status_icon} {i}. {task_desc}...",
                f"    时间: {summary.get('total_execution_time', 0):.1f}秒",
                f"    成功率: {summary.get('successful_agents', 0)}/{summary.get('total_agents', 0)}",
                ""
            ])

        return "\n".join(output)


class ParallelMonitorCommand(AsyncCLICommand):
    """并行执行监控命令"""

    def __init__(self):
        super().__init__('monitor', '实时监控并行执行')

    async def execute(self, args: argparse.Namespace) -> CommandResult:
        """执行监控"""
        try:
            from modules.parallel_monitor import get_global_monitor
            import asyncio

            monitor = get_global_monitor()

            if args.live:
                # 实时监控模式
                return await self._run_live_monitor(monitor)
            else:
                # 单次状态查询
                status_display = monitor.get_status_display()
                return CommandResult(
                    success=True,
                    message="监控状态获取成功",
                    data={'status_display': status_display}
                )

        except Exception as e:
            return CommandResult(
                success=False,
                message=f"并行监控失败: {str(e)}",
                error_code="PARALLEL_MONITOR_ERROR"
            )

    async def _run_live_monitor(self, monitor) -> CommandResult:
        """运行实时监控"""
        import os
        import asyncio

        try:
            print("🔍 Perfect21 实时任务监控 (按Ctrl+C退出)")
            print("=" * 50)

            while True:
                # 清屏
                os.system('clear' if os.name == 'posix' else 'cls')
                print(monitor.get_status_display())
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            return CommandResult(
                success=True,
                message="实时监控已停止"
            )

    def setup_parser(self, parser: argparse.ArgumentParser) -> None:
        """设置监控命令解析器"""
        parser.add_argument(
            '--live',
            action='store_true',
            help='实时监控模式'
        )
        parser.add_argument(
            '--show-stats',
            action='store_true',
            help='显示性能统计'
        )


class ParallelCommand(CompositeCLICommand):
    """并行执行主命令"""

    def __init__(self):
        super().__init__('parallel', 'Perfect21 智能并行执行器')

        # 添加子命令
        self.add_subcommand(ParallelExecuteCommand())
        self.add_subcommand(ParallelStatusCommand())
        self.add_subcommand(ParallelHistoryCommand())
        self.add_subcommand(ParallelMonitorCommand())

    async def execute(self, args: argparse.Namespace) -> CommandResult:
        """重写execute方法支持直接执行"""
        # 如果提供了description但没有子命令，默认执行execute
        if hasattr(args, 'description') and args.description and not hasattr(args, 'parallel_action'):
            # 创建临时的execute命令参数
            execute_command = self.subcommands['execute']
            return await execute_command.execute_with_error_handling(args)

        # 否则使用默认的复合命令逻辑
        return await super().execute(args)

    def setup_parser(self, parser: argparse.ArgumentParser) -> None:
        """设置并行命令解析器"""
        # 先添加直接执行的参数
        parser.add_argument('description', nargs='?', help='任务描述（直接执行模式）')
        parser.add_argument('--force-parallel', action='store_true', help='强制并行模式')

        # 然后添加子命令
        super().setup_parser(parser)


# 注册并行命令
from ..command_base import register_command
register_command(ParallelCommand())