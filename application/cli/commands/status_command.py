#!/usr/bin/env python3
"""
状态命令处理器 - 性能优化版
提供系统状态查询和性能监控
"""

import argparse
from typing import Dict, Any

from ..command_base import AsyncCLICommand, CommandResult


class StatusCommand(AsyncCLICommand):
    """系统状态命令"""

    def __init__(self):
        super().__init__('status', '查看Perfect21系统状态')

    async def execute(self, args: argparse.Namespace) -> CommandResult:
        """执行状态查询"""
        try:
            # 延迟导入，提升启动性能
            from main.perfect21 import Perfect21

            # 创建Perfect21实例
            p21 = Perfect21()

            # 获取系统状态
            status_result = p21.status()

            if not status_result.get('success'):
                return CommandResult(
                    success=False,
                    message=status_result.get('message', '获取系统状态失败'),
                    error_code="SYSTEM_STATUS_ERROR"
                )

            # 如果启用了性能监控，获取额外信息
            additional_info = {}
            if getattr(args, 'performance', False):
                additional_info = await self._get_performance_info()

            if getattr(args, 'git_cache', False):
                additional_info['git_cache'] = await self._get_git_cache_info()

            return CommandResult(
                success=True,
                message="系统状态查询成功",
                data={
                    'system_status': status_result['status'],
                    'additional_info': additional_info
                }
            )

        except Exception as e:
            return CommandResult(
                success=False,
                message=f"获取系统状态失败: {str(e)}",
                error_code="STATUS_QUERY_ERROR"
            )

    async def _get_performance_info(self) -> Dict[str, Any]:
        """获取性能信息"""
        try:
            from infrastructure.git.git_cache import GitCacheManager
            from modules.parallel_monitor import get_global_monitor

            cache_manager = GitCacheManager()
            monitor = get_global_monitor()

            return {
                'git_cache_instances': len(cache_manager._cache_instances),
                'parallel_monitor': monitor.get_performance_stats(),
                'optimization_features': {
                    'git_cache_enabled': True,
                    'async_operations': True,
                    'parallel_commands': True
                }
            }

        except Exception as e:
            self.logger.warning(f"获取性能信息失败: {e}")
            return {'error': str(e)}

    async def _get_git_cache_info(self) -> Dict[str, Any]:
        """获取Git缓存信息"""
        try:
            from infrastructure.git.git_cache import get_git_cache

            git_cache = get_git_cache()
            cache_info = git_cache.get_cache_info()

            # 获取当前Git状态
            git_status = await git_cache.get_git_status()

            return {
                'cache_info': cache_info,
                'current_status': {
                    'branch': git_status.current_branch,
                    'staged_files': len(git_status.staged_files),
                    'modified_files': len(git_status.modified_files),
                    'has_changes': git_status.has_uncommitted_changes
                }
            }

        except Exception as e:
            self.logger.warning(f"获取Git缓存信息失败: {e}")
            return {'error': str(e)}

    def setup_parser(self, parser: argparse.ArgumentParser) -> None:
        """设置状态命令解析器"""
        parser.add_argument(
            '--performance',
            action='store_true',
            help='显示性能监控信息'
        )
        parser.add_argument(
            '--git-cache',
            action='store_true',
            help='显示Git缓存信息'
        )
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='显示详细信息'
        )

    def format_output(self, result: CommandResult, verbose: bool = False) -> str:
        """格式化状态输出"""
        if not result.success:
            return super().format_output(result, verbose)

        data = result.data or {}
        system_status = data.get('system_status', {})
        additional_info = data.get('additional_info', {})

        output = [
            "🚀 Perfect21系统状态",
            "=" * 50
        ]

        # Perfect21信息
        p21_info = system_status.get('perfect21', {})
        output.extend([
            f"版本: {p21_info.get('version', 'unknown')}",
            f"模式: {p21_info.get('mode', 'unknown')}",
            f"核心Agent: {'✅ 可用' if p21_info.get('core_agents_available') else '❌ 不可用'}",
            f"Agent数量: {p21_info.get('agent_count', 0)}"
        ])

        # 项目信息
        project = system_status.get('project', {})
        output.extend([
            f"\n📁 项目信息",
            f"Git仓库: {'✅ 是' if project.get('is_git_repo') else '❌ 否'}",
            f"当前分支: {project.get('current_branch', '未知')}",
            f"Perfect21结构: {'✅ 完整' if project.get('perfect21_structure') else '❌ 不完整'}"
        ])

        # 分支状态
        branches = system_status.get('branches', {})
        if branches.get('current_branch'):
            branch_info = branches['current_branch']
            output.extend([
                f"\n🌿 当前分支",
                f"名称: {branch_info.get('name', 'unknown')}",
                f"类型: {branch_info.get('info', {}).get('type', 'unknown')}",
                f"保护级别: {branch_info.get('info', {}).get('protection_level', 'unknown')}"
            ])

        # 性能信息
        if additional_info.get('parallel_monitor'):
            monitor_stats = additional_info['parallel_monitor']
            output.extend([
                f"\n📊 并行监控",
                f"活跃任务: {monitor_stats.get('active_tasks', 0)}",
                f"总执行次数: {monitor_stats.get('total_executions', 0)}",
                f"平均响应时间: {monitor_stats.get('avg_response_time', 0):.2f}ms"
            ])

        # Git缓存信息
        git_cache_info = additional_info.get('git_cache')
        if git_cache_info:
            cache_info = git_cache_info.get('cache_info', {})
            current_status = git_cache_info.get('current_status', {})

            output.extend([
                f"\n💾 Git缓存",
                f"缓存TTL: {cache_info.get('cache_ttl', 0)}秒",
                f"缓存状态: {'✅ 有效' if cache_info.get('is_valid') else '❌ 过期'}",
                f"最后刷新: {cache_info.get('time_since_refresh', 0):.1f}秒前",
                f"当前分支: {current_status.get('branch', 'unknown')}",
                f"暂存文件: {current_status.get('staged_files', 0)}个",
                f"修改文件: {current_status.get('modified_files', 0)}个"
            ])

        # 优化特性
        optimization = additional_info.get('optimization_features')
        if optimization:
            output.extend([
                f"\n⚡ 优化特性",
                f"Git缓存: {'✅ 启用' if optimization.get('git_cache_enabled') else '❌ 禁用'}",
                f"异步操作: {'✅ 启用' if optimization.get('async_operations') else '❌ 禁用'}",
                f"并行命令: {'✅ 启用' if optimization.get('parallel_commands') else '❌ 禁用'}"
            ])

        return "\n".join(output)


# 注册状态命令
from ..command_base import register_command
register_command(StatusCommand())