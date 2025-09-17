#!/usr/bin/env python3
"""
Git钩子命令处理器 - 性能优化版
使用新的GitHooksOptimized和命令模式
"""

import argparse
from typing import Dict, Any

from ..command_base import AsyncCLICommand, CommandResult, CompositeCLICommand


class HooksStatusCommand(AsyncCLICommand):
    """钩子状态命令"""

    def __init__(self):
        super().__init__('status', '查看钩子安装状态')

    async def execute(self, args: argparse.Namespace) -> CommandResult:
        """执行钩子状态查询"""
        try:
            # 延迟导入，提升启动性能
            from features.git_workflow.hooks_manager import GitHooksManager

            hooks_manager = GitHooksManager()
            status_info = hooks_manager.get_status_info()

            return CommandResult(
                success=True,
                message="钩子状态查询成功",
                data=status_info
            )

        except Exception as e:
            return CommandResult(
                success=False,
                message=f"获取钩子状态失败: {str(e)}",
                error_code="HOOKS_STATUS_ERROR"
            )

    def setup_parser(self, parser: argparse.ArgumentParser) -> None:
        """设置状态命令解析器"""
        pass  # 状态命令不需要额外参数

    def format_output(self, result: CommandResult, verbose: bool = False) -> str:
        """格式化钩子状态输出"""
        if not result.success:
            return super().format_output(result, verbose)

        data = result.data or {}
        output = ["📋 Perfect21 Git钩子状态", "=" * 50]

        # 已安装钩子
        installed = data.get('installed_hooks', [])
        output.append(f"已安装钩子: {len(installed)}个")
        for hook in installed:
            output.append(f"  ✅ {hook}")

        # 可用钩子组
        groups = data.get('hook_groups', {})
        output.append(f"\n📊 钩子组:")
        for group, hooks in groups.items():
            output.append(f"  {group}: {len(hooks)}个钩子")

        return "\n".join(output)


class HooksInstallCommand(AsyncCLICommand):
    """钩子安装命令"""

    def __init__(self):
        super().__init__('install', '安装Git钩子')

    async def execute(self, args: argparse.Namespace) -> CommandResult:
        """执行钩子安装"""
        try:
            from features.git_workflow.hooks_manager import GitHooksManager

            hooks_manager = GitHooksManager()
            target = args.target or 'standard'

            if target in hooks_manager.hook_groups:
                # 安装钩子组
                result = await hooks_manager.install_hook_group_async(target, args.force)
            elif target in hooks_manager.hooks_config:
                # 安装单个钩子
                result = await hooks_manager.install_hook_async(target, args.force)
            else:
                return CommandResult(
                    success=False,
                    message=f"未知的钩子或组: {target}",
                    error_code="UNKNOWN_HOOK_TARGET"
                )

            return CommandResult(
                success=result.get('success', False),
                message=result.get('message', '钩子安装完成'),
                data=result
            )

        except Exception as e:
            return CommandResult(
                success=False,
                message=f"钩子安装失败: {str(e)}",
                error_code="HOOKS_INSTALL_ERROR"
            )

    def setup_parser(self, parser: argparse.ArgumentParser) -> None:
        """设置安装命令解析器"""
        parser.add_argument(
            'target',
            nargs='?',
            help='钩子名称或组名 (essential/standard/advanced/complete)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制覆盖现有钩子'
        )


class HooksUninstallCommand(AsyncCLICommand):
    """钩子卸载命令"""

    def __init__(self):
        super().__init__('uninstall', '卸载Perfect21钩子')

    async def execute(self, args: argparse.Namespace) -> CommandResult:
        """执行钩子卸载"""
        try:
            from features.git_workflow.hooks_manager import GitHooksManager

            hooks_manager = GitHooksManager()
            hook_names = args.hooks if args.hooks else None

            result = await hooks_manager.uninstall_hooks_async(hook_names)

            return CommandResult(
                success=result.get('success', False),
                message=result.get('message', '钩子卸载完成'),
                data=result
            )

        except Exception as e:
            return CommandResult(
                success=False,
                message=f"钩子卸载失败: {str(e)}",
                error_code="HOOKS_UNINSTALL_ERROR"
            )

    def setup_parser(self, parser: argparse.ArgumentParser) -> None:
        """设置卸载命令解析器"""
        parser.add_argument(
            'hooks',
            nargs='*',
            help='要卸载的钩子名称'
        )


class HooksExecuteCommand(AsyncCLICommand):
    """钩子执行命令（测试用）"""

    def __init__(self):
        super().__init__('execute', '手动执行钩子（测试用）')

    async def execute(self, args: argparse.Namespace) -> CommandResult:
        """执行钩子测试"""
        try:
            # 使用优化版钩子系统
            from infrastructure.git.hooks_optimized import GitHooksOptimized

            hooks = GitHooksOptimized()
            hook_name = args.hook_name

            # 根据钩子类型执行
            if hook_name == 'pre-commit':
                result = await hooks.pre_commit_hook()
            elif hook_name == 'pre-push':
                remote = args.remote or 'origin'
                result = await hooks.pre_push_hook(remote)
            elif hook_name == 'post-checkout':
                old_ref = args.old_ref or ''
                new_ref = args.new_ref or ''
                result = await hooks.post_checkout_hook(old_ref, new_ref, '1')
            elif hook_name == 'prepare-commit-msg':
                commit_msg_file = args.file or '.git/COMMIT_EDITMSG'
                result = await hooks.prepare_commit_msg_hook(commit_msg_file)
            elif hook_name == 'commit-msg':
                commit_msg_file = args.file or '.git/COMMIT_EDITMSG'
                result = await hooks.commit_msg_hook(commit_msg_file)
            elif hook_name == 'post-commit':
                result = await hooks.post_commit_hook()
            else:
                return CommandResult(
                    success=False,
                    message=f"不支持的钩子类型: {hook_name}",
                    error_code="UNSUPPORTED_HOOK_TYPE"
                )

            return CommandResult(
                success=result.get('success', False),
                message=f"{hook_name}钩子执行完成",
                data=result
            )

        except Exception as e:
            return CommandResult(
                success=False,
                message=f"钩子执行失败: {str(e)}",
                error_code="HOOKS_EXECUTE_ERROR"
            )

    def setup_parser(self, parser: argparse.ArgumentParser) -> None:
        """设置执行命令解析器"""
        parser.add_argument(
            'hook_name',
            choices=[
                'pre-commit', 'pre-push', 'post-checkout',
                'commit-msg', 'post-merge', 'prepare-commit-msg', 'post-commit'
            ],
            help='钩子名称'
        )
        parser.add_argument('--remote', default='origin', help='远程仓库名(pre-push)')
        parser.add_argument('--old-ref', help='旧引用(post-checkout)')
        parser.add_argument('--new-ref', help='新引用(post-checkout)')
        parser.add_argument('--file', help='提交消息文件(commit-msg)')


class HooksListCommand(AsyncCLICommand):
    """钩子列表命令"""

    def __init__(self):
        super().__init__('list', '列出可用钩子')

    async def execute(self, args: argparse.Namespace) -> CommandResult:
        """执行钩子列表查询"""
        try:
            from features.git_workflow.hooks_manager import GitHooksManager

            hooks_manager = GitHooksManager()

            return CommandResult(
                success=True,
                message="钩子列表查询成功",
                data={
                    'hooks_config': hooks_manager.hooks_config,
                    'hook_groups': hooks_manager.hook_groups
                }
            )

        except Exception as e:
            return CommandResult(
                success=False,
                message=f"获取钩子列表失败: {str(e)}",
                error_code="HOOKS_LIST_ERROR"
            )

    def setup_parser(self, parser: argparse.ArgumentParser) -> None:
        """设置列表命令解析器"""
        pass

    def format_output(self, result: CommandResult, verbose: bool = False) -> str:
        """格式化钩子列表输出"""
        if not result.success:
            return super().format_output(result, verbose)

        data = result.data or {}
        hooks_config = data.get('hooks_config', {})
        hook_groups = data.get('hook_groups', {})

        output = ["📋 Perfect21支持的Git钩子:", "=" * 50]

        # 按类别分组显示
        categories = {
            'commit_workflow': '📝 提交工作流',
            'push_workflow': '🚀 推送工作流',
            'branch_workflow': '🌿 分支工作流',
            'advanced': '🔧 高级钩子',
            'maintenance': '🧹 维护钩子',
            'patch_workflow': '📦 补丁工作流'
        }

        for category, title in categories.items():
            output.append(f"\n{title}:")
            for hook_name, config in hooks_config.items():
                if config.get('category') == category:
                    required_icon = "🔴" if config.get('required') else "🟡"
                    subagent = config.get('subagent', 'unknown')
                    description = config.get('description', 'No description')
                    output.append(f"  {hook_name}: {description} {required_icon} ({subagent})")

        output.append(f"\n🔴=必需 🟡=可选")
        output.append(f"\n📊 钩子组:")
        for group, hooks in hook_groups.items():
            output.append(f"  {group}: {len(hooks)}个钩子")

        return "\n".join(output)


class HooksCommand(CompositeCLICommand):
    """Git钩子主命令"""

    def __init__(self):
        super().__init__('hooks', 'Git钩子管理')

        # 添加子命令
        self.add_subcommand(HooksListCommand())
        self.add_subcommand(HooksStatusCommand())
        self.add_subcommand(HooksInstallCommand())
        self.add_subcommand(HooksUninstallCommand())
        self.add_subcommand(HooksExecuteCommand())


# 注册钩子命令
from ..command_base import register_command
register_command(HooksCommand())