#!/usr/bin/env python3
"""
Perfect21 CLI - 命令行接口
便捷的Git工作流操作命令
"""

import os
import sys
import argparse
from typing import Dict, Any

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# 导入Perfect21类
if __name__ == '__main__':
    from perfect21 import Perfect21
else:
    from .perfect21 import Perfect21
from modules.utils import format_execution_result
from modules.logger import log_info

def print_status(p21: Perfect21) -> None:
    """打印系统状态"""
    result = p21.status()

    if result['success']:
        status = result['status']
        print("🚀 Perfect21系统状态")
        print("=" * 50)

        # Perfect21信息
        p21_info = status['perfect21']
        print(f"版本: {p21_info['version']}")
        print(f"模式: {p21_info['mode']}")
        print(f"核心Agent: {'✅ 可用' if p21_info['core_agents_available'] else '❌ 不可用'}")
        print(f"Agent数量: {p21_info['agent_count']}")

        # 项目信息
        project = status['project']
        print(f"\n📁 项目信息")
        print(f"Git仓库: {'✅ 是' if project['is_git_repo'] else '❌ 否'}")
        print(f"当前分支: {project.get('current_branch', '未知')}")
        print(f"Perfect21结构: {'✅ 完整' if project['perfect21_structure'] else '❌ 不完整'}")

        # 分支状态
        if 'branches' in status and status['branches'].get('current_branch'):
            branch_info = status['branches']['current_branch']
            print(f"\n🌿 当前分支")
            print(f"名称: {branch_info['name']}")
            print(f"类型: {branch_info['info']['type']}")
            print(f"保护级别: {branch_info['info']['protection_level']}")

    else:
        print(f"❌ 获取状态失败: {result.get('message', '未知错误')}")

def handle_git_hooks(p21: Perfect21, args: argparse.Namespace) -> None:
    """处理Git钩子命令"""
    from features.git_workflow.hooks_manager import GitHooksManager

    hooks_manager = GitHooksManager()

    if args.hook_action == 'list':
        print("📋 Perfect21支持的Git钩子:")
        print("=" * 50)

        categories = {
            'commit_workflow': '📝 提交工作流',
            'push_workflow': '🚀 推送工作流',
            'branch_workflow': '🌿 分支工作流',
            'advanced': '🔧 高级钩子',
            'maintenance': '🧹 维护钩子',
            'patch_workflow': '📦 补丁工作流'
        }

        for category, title in categories.items():
            print(f"\n{title}:")
            for hook_name, config in hooks_manager.hooks_config.items():
                if config['category'] == category:
                    required_icon = "🔴" if config['required'] else "🟡"
                    print(f"  {hook_name}: {config['description']} {required_icon} ({config['subagent']})")

        print(f"\n🔴=必需 🟡=可选")
        print(f"\n📊 钩子组:")
        for group, hooks in hooks_manager.hook_groups.items():
            print(f"  {group}: {len(hooks)}个钩子")

    elif args.hook_action == 'status':
        hooks_manager.print_status()

    elif args.hook_action == 'install':
        target = args.target or 'standard'

        if target in hooks_manager.hook_groups:
            # 安装钩子组
            hooks_manager.install_hook_group(target, args.force)
        elif target in hooks_manager.hooks_config:
            # 安装单个钩子
            hooks_manager.install_hook(target, args.force)
        else:
            print(f"❌ 未知的钩子或组: {target}")
            print(f"可用组: {', '.join(hooks_manager.hook_groups.keys())}")
            print(f"可用钩子: {', '.join(hooks_manager.hooks_config.keys())}")

    elif args.hook_action == 'uninstall':
        hook_names = args.hooks if args.hooks else None
        hooks_manager.uninstall_hooks(hook_names)

    elif args.hook_action == 'execute':
        # 手动执行钩子 (用于测试)
        hook_name = args.hook_name

        # 执行钩子
        hook_args = []
        if hook_name == 'pre-push':
            hook_args = [args.remote or 'origin']
        elif hook_name == 'post-checkout':
            hook_args = [args.old_ref or '', args.new_ref or '', '1']

        result = p21.git_hook_handler(hook_name, *hook_args)

        if result['success']:
            print(f"✅ {hook_name}执行成功")
            if 'call_info' in result:
                print(f"📞 建议执行: {result['call_info']['command']}")
        else:
            print(f"❌ {hook_name}执行失败")
            print(f"错误: {result.get('message', '未知错误')}")

    else:
        print("❌ 未知的钩子操作")
        print("使用 'python3 main/cli.py hooks --help' 查看帮助")

def handle_workflow(p21: Perfect21, args: argparse.Namespace) -> None:
    """处理工作流命令"""
    workflow_commands = {
        'create-feature': '创建功能分支',
        'create-release': '创建发布分支',
        'merge-to-main': '合并到主分支',
        'branch-info': '分支信息分析',
        'cleanup': '清理旧分支'
    }

    if args.workflow_action == 'list':
        print("📋 可用的工作流操作:")
        for cmd, desc in workflow_commands.items():
            print(f"  {cmd}: {desc}")
        return

    if args.workflow_action not in workflow_commands:
        print(f"❌ 不支持的工作流操作: {args.workflow_action}")
        print("使用 'list' 查看可用操作")
        return

    # 准备参数
    workflow_args = []
    if args.workflow_action == 'create-feature':
        if not args.name:
            print("❌ 请提供功能名称: --name <feature-name>")
            return
        workflow_args = [args.name, args.from_branch or 'develop']

    elif args.workflow_action == 'create-release':
        if not args.version:
            print("❌ 请提供版本号: --version <version>")
            return
        workflow_args = [args.version, args.from_branch or 'develop']

    elif args.workflow_action == 'merge-to-main':
        if not args.source:
            print("❌ 请提供源分支: --source <branch-name>")
            return
        workflow_args = [args.source, 'delete' if not args.keep else 'keep']

    elif args.workflow_action == 'branch-info':
        if args.branch:
            workflow_args = [args.branch]

    elif args.workflow_action == 'cleanup':
        workflow_args = [str(args.days or 30)]

    # 执行工作流操作
    result = p21.workflow_command(args.workflow_action, *workflow_args)

    if result.get('success', True):
        print(f"✅ {workflow_commands[args.workflow_action]}成功")
        if 'message' in result:
            print(f"📝 {result['message']}")

        # 特殊结果处理
        if args.workflow_action == 'branch-info' and 'branch_statistics' in result:
            stats = result['branch_statistics']
            print(f"\n📊 分支统计:")
            print(f"总分支数: {stats['total']}")
            for branch_type, count in stats['by_type'].items():
                print(f"  {branch_type}: {count}")

        # 显示SubAgent调用信息
        if 'call_info' in result:
            print(f"📞 建议执行: {result['call_info']['command']}")

    else:
        print(f"❌ {workflow_commands[args.workflow_action]}失败")
        print(f"错误: {result.get('message', '未知错误')}")

def handle_branch(p21: Perfect21, args: argparse.Namespace) -> None:
    """处理分支命令"""
    if args.branch_action == 'status':
        # 显示当前分支状态
        result = p21.status()
        if result['success']:
            status = result['status']

            print("🌿 分支状态")
            print("=" * 50)

            project = status['project']
            print(f"Git仓库: {'✅ 是' if project['is_git_repo'] else '❌ 否'}")
            print(f"当前分支: {project.get('current_branch', '未知')}")

            if 'branches' in status and status['branches'].get('current_branch'):
                branch_info = status['branches']['current_branch']
                print(f"分支类型: {branch_info['info']['type']}")
                print(f"保护级别: {branch_info['info']['protection_level']}")

                if branch_info['info'].get('subagent'):
                    print(f"建议Agent: {branch_info['info']['subagent']}")
        else:
            print(f"❌ 获取分支状态失败: {result.get('message', '未知错误')}")

    elif args.branch_action == 'list':
        # 列出所有分支
        print("🌿 分支列表")
        print("=" * 50)
        try:
            import subprocess
            result = subprocess.run(['git', 'branch', '-v'],
                                  capture_output=True, text=True, check=True)
            print(result.stdout)
        except subprocess.CalledProcessError:
            print("❌ 无法获取分支列表")

    elif args.branch_action == 'info':
        # 显示详细分支信息
        result = p21.workflow('branch-info')
        if result['success']:
            print("✅ 分支信息分析完成")
            print(result.get('message', ''))
        else:
            print(f"❌ 分支信息分析失败: {result.get('message', '未知错误')}")

def main():
    """CLI主函数"""
    parser = argparse.ArgumentParser(description='Perfect21 CLI - Git工作流管理工具')
    subparsers = parser.add_subparsers(dest='command', help='命令')

    # status命令
    status_parser = subparsers.add_parser('status', help='查看系统状态')

    # git-hooks命令
    hooks_parser = subparsers.add_parser('hooks', help='Git钩子管理')
    hooks_subparsers = hooks_parser.add_subparsers(dest='hook_action', help='钩子操作')

    # hooks list - 列出可用钩子
    list_parser = hooks_subparsers.add_parser('list', help='列出可用钩子')

    # hooks status - 查看钩子状态
    status_parser = hooks_subparsers.add_parser('status', help='查看钩子安装状态')

    # hooks install - 安装钩子
    install_parser = hooks_subparsers.add_parser('install', help='安装Git钩子')
    install_parser.add_argument('target', nargs='?', help='钩子名称或组名 (essential/standard/advanced/complete)')
    install_parser.add_argument('--force', action='store_true', help='强制覆盖现有钩子')

    # hooks uninstall - 卸载钩子
    uninstall_parser = hooks_subparsers.add_parser('uninstall', help='卸载Perfect21钩子')
    uninstall_parser.add_argument('hooks', nargs='*', help='要卸载的钩子名称')

    # hooks execute - 手动执行钩子 (用于测试)
    execute_parser = hooks_subparsers.add_parser('execute', help='手动执行钩子 (测试用)')
    execute_parser.add_argument('hook_name', choices=['pre-commit', 'pre-push', 'post-checkout', 'commit-msg', 'post-merge'], help='钩子名称')
    execute_parser.add_argument('--remote', default='origin', help='远程仓库名(pre-push)')
    execute_parser.add_argument('--old-ref', help='旧引用(post-checkout)')
    execute_parser.add_argument('--new-ref', help='新引用(post-checkout)')
    execute_parser.add_argument('--file', help='提交消息文件(commit-msg)')

    # branch命令
    branch_parser = subparsers.add_parser('branch', help='分支管理')
    branch_parser.add_argument('branch_action',
                              choices=['status', 'list', 'info'],
                              help='分支操作')

    # workflow命令
    workflow_parser = subparsers.add_parser('workflow', help='工作流管理')
    workflow_parser.add_argument('workflow_action',
                               choices=['list', 'create-feature', 'create-release', 'merge-to-main', 'branch-info', 'cleanup'],
                               help='工作流操作')
    workflow_parser.add_argument('--name', help='功能名称(create-feature)')
    workflow_parser.add_argument('--version', help='版本号(create-release)')
    workflow_parser.add_argument('--from-branch', help='源分支(create-*)')
    workflow_parser.add_argument('--source', help='源分支(merge-to-main)')
    workflow_parser.add_argument('--keep', action='store_true', help='保留源分支(merge-to-main)')
    workflow_parser.add_argument('--branch', help='分支名称(branch-info)')
    workflow_parser.add_argument('--days', type=int, help='天数阈值(cleanup)')

    # 全局选项
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 创建Perfect21实例
    try:
        p21 = Perfect21()
    except Exception as e:
        print(f"❌ Perfect21初始化失败: {e}")
        sys.exit(1)

    # 执行命令
    try:
        if args.command == 'status':
            print_status(p21)
        elif args.command == 'hooks':
            handle_git_hooks(p21, args)
        elif args.command == 'branch':
            handle_branch(p21, args)
        elif args.command == 'workflow':
            handle_workflow(p21, args)
        else:
            print(f"❌ 未知命令: {args.command}")
            sys.exit(1)

    except Exception as e:
        print(f"❌ 命令执行失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()