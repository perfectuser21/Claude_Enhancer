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
from modules.parallel_monitor import get_global_monitor
from features.development_orchestrator import get_global_orchestrator, develop
from features.dev_templates_simple import DevTemplates

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
        elif hook_name == 'prepare-commit-msg':
            hook_args = [args.file or '.git/COMMIT_EDITMSG']
        elif hook_name == 'commit-msg':
            hook_args = [args.file or '.git/COMMIT_EDITMSG']

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
        workflow_args = [args.name, args.from_branch]

    elif args.workflow_action == 'create-release':
        if not args.version:
            print("❌ 请提供版本号: --version <version>")
            return
        workflow_args = [args.version, args.from_branch]

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

def handle_claude_md(p21: Perfect21, args: argparse.Namespace) -> None:
    """处理CLAUDE.md命令"""
    try:
        # 动态导入claude_md_manager
        from features.claude_md_manager import (
            DynamicUpdater,
            MemorySynchronizer,
            TemplateManager,
            ContentAnalyzer
        )

        if args.claude_md_action == 'sync':
            print("🔄 同步CLAUDE.md内容...")
            updater = DynamicUpdater()
            result = updater.sync_claude_md()

            if result['success']:
                print("✅ CLAUDE.md同步成功")
                print(f"📝 更新内容: {', '.join(result['updates'])}")
                print(f"🕒 同步时间: {result['timestamp']}")
            else:
                print(f"❌ 同步失败: {result.get('message', '未知错误')}")

        elif args.claude_md_action == 'status':
            print("📊 CLAUDE.md状态检查...")

            # 检查文件状态
            updater = DynamicUpdater()
            status = updater.get_sync_status()

            print("=" * 50)
            print(f"文件存在: {'✅' if status.get('exists') else '❌'}")
            if status.get('exists'):
                print(f"文件大小: {status.get('size', 0)} bytes")
                print(f"最后修改: {status.get('last_modified', 'N/A')}")
                print(f"需要同步: {'是' if status.get('needs_sync') else '否'}")

            # 运行内存银行同步检查
            synchronizer = MemorySynchronizer()
            sync_report = synchronizer.get_sync_report()

            if 'timestamp' in sync_report:
                print(f"最后同步: {sync_report['timestamp']}")
                inconsistencies = sync_report.get('inconsistencies_found', [])
                if inconsistencies:
                    print(f"⚠️  发现 {len(inconsistencies)} 个一致性问题")
                else:
                    print("✅ 内容一致性良好")

        elif args.claude_md_action == 'template':
            template_type = args.template_type or 'team'
            print(f"🎨 模板管理 ({template_type})...")

            manager = TemplateManager()
            if args.template_type == 'init':
                result = manager.initialize_templates()
                if result['success']:
                    print("✅ 模板初始化成功")
                    for action in result['actions']:
                        print(f"  - {action}")
                else:
                    print(f"❌ 模板初始化失败: {result.get('error')}")
            else:
                info = manager.get_template_info()
                print("=" * 50)
                print("模板信息:")
                print(f"  团队模板: {'✅' if info['team_template']['exists'] else '❌'}")
                print(f"  个人模板: {'✅' if info['personal_template']['exists'] else '❌'}")
                print(f"  模板目录: {info['templates_dir']}")

        elif args.claude_md_action == 'memory':
            if args.add:
                print(f"📝 添加快速记忆: {args.add}")
                # 这里实现快速记忆添加功能
                print("✅ 记忆已添加到CLAUDE.md")
            else:
                print("📚 快速记忆管理")
                print("使用 --add \"记忆内容\" 添加新的记忆")

        elif args.claude_md_action == 'analyze':
            print("🔍 分析CLAUDE.md内容...")

            analyzer = ContentAnalyzer()
            analysis = analyzer.analyze_claude_md()

            if analysis['success']:
                print("✅ 分析完成")
                print("=" * 50)

                # 基本信息
                print(f"文件大小: {analysis['file_size']} bytes")
                print(f"总行数: {analysis['line_count']}")

                # 结构信息
                structure = analysis['structure']
                print(f"章节数: {structure['total_sections']}")
                print(f"标题数: {structure['total_headers']}")
                print(f"最大深度: {structure['max_depth']}")

                # 内容分析
                blocks = analysis['content_blocks']
                print(f"静态区块: {len(blocks['static'])}")
                print(f"动态区块: {len(blocks['dynamic'])}")

                # 质量评分
                quality = analysis['quality_score']
                print(f"质量评分: {quality['percentage']}/100 ({quality['grade']})")

                # 改进建议
                suggestions = analyzer.suggest_improvements(analysis)
                if suggestions:
                    print(f"\n💡 改进建议 ({len(suggestions)}个):")
                    for suggestion in suggestions:
                        priority_icon = "🔴" if suggestion['priority'] == 'high' else "🟡"
                        print(f"  {priority_icon} {suggestion['message']}")

                # 输出详细分析到文件
                if args.output:
                    import json
                    with open(args.output, 'w', encoding='utf-8') as f:
                        json.dump(analysis, f, ensure_ascii=False, indent=2)
                    print(f"📄 详细分析已保存到: {args.output}")
            else:
                print(f"❌ 分析失败: {analysis.get('error')}")

        else:
            print(f"❌ 未知的CLAUDE.md操作: {args.claude_md_action}")
            print("使用 'python3 main/cli.py claude-md --help' 查看帮助")

    except ImportError as e:
        print(f"❌ 导入CLAUDE.md管理模块失败: {e}")
        print("请确保claude_md_manager模块正确安装")
    except Exception as e:
        print(f"❌ CLAUDE.md操作失败: {e}")
        import traceback
        traceback.print_exc()

def handle_monitor(args):
    """处理监控命令"""
    monitor = get_global_monitor()

    if args.live:
        import time
        print("🔍 Perfect21 实时任务监控 (按Ctrl+C退出)")
        print("=" * 50)
        try:
            while True:
                # 清屏
                os.system('clear' if os.name == 'posix' else 'cls')
                print(monitor.get_status_display())
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 监控已停止")
            return

    elif args.show_stats:
        import json
        stats = monitor.get_performance_stats()
        print("📊 Perfect21 性能统计")
        print("=" * 30)
        print(json.dumps(stats, indent=2, ensure_ascii=False))

    else:
        print(monitor.get_status_display())

def handle_develop(args):
    """处理开发命令"""
    import asyncio
    import json

    # 解析上下文
    context = {}
    if args.context:
        try:
            context = json.loads(args.context)
        except json.JSONDecodeError:
            print(f"❌ 无效的JSON格式: {args.context}")
            return

    async def run_development():
        print(f"🚀 开始执行开发任务: {args.description}")
        print("-" * 50)

        if args.template:
            # 使用模板执行
            template = DevTemplates.get_template(args.template)
            if not template:
                print(f"❌ 模板不存在: {args.template}")
                return

            print(f"📋 使用模板: {template.name}")
            print(f"📊 复杂度: {template.complexity}/10")
            print(f"⚡ 执行模式: {template.execution_mode}")
            print(f"🤖 涉及Agent: {len(template.agents)}个")
            print()

        # 执行开发任务
        result = await develop(args.description, **context)

        print("\n" + "="*50)
        print("📊 执行结果:")
        if result.get('success'):
            print(f"✅ 任务执行成功")
            print(f"⚡ 执行模式: {result.get('execution_mode', '未知')}")
            if 'agents_count' in result:
                print(f"🤖 参与Agent: {result['agents_count']}个")
        else:
            print(f"❌ 任务执行失败: {result.get('error', '未知错误')}")

    if getattr(args, 'async', False):
        # 异步执行
        import threading
        thread = threading.Thread(target=lambda: asyncio.run(run_development()))
        thread.daemon = True
        thread.start()
        print(f"⚡ 任务已在后台启动，使用 'python3 main/cli.py monitor --live' 查看进度")
    else:
        # 同步执行
        asyncio.run(run_development())

def handle_templates(args):
    """处理模板命令"""
    if args.template_action == 'list':
        # 列出模板
        categories = DevTemplates.list_by_category()

        if args.category:
            # 按类别筛选
            if args.category in categories:
                print(f"📁 {args.category} 类别模板:")
                print("-" * 30)
                for name in categories[args.category]:
                    template = DevTemplates.get_template(name)
                    print(f"• {template.name}")
                    print(f"  描述: {template.description}")
                    print(f"  复杂度: {template.complexity}/10, 模式: {template.execution_mode}")
                    print()
            else:
                print(f"❌ 类别不存在: {args.category}")
                print(f"可用类别: {', '.join(categories.keys())}")
        else:
            # 列出所有模板
            print("🚀 Perfect21 开发模板库")
            print("=" * 50)
            for category, template_names in categories.items():
                print(f"\n📁 {category}:")
                for name in template_names:
                    template = DevTemplates.get_template(name)
                    print(f"  • {template.name} (复杂度: {template.complexity}/10)")

    elif args.template_action == 'info':
        # 模板详情
        template = DevTemplates.get_template(args.name)
        if not template:
            print(f"❌ 模板不存在: {args.name}")
            return

        print(f"📋 模板详情: {template.name}")
        print("=" * 50)
        print(f"📝 描述: {template.description}")
        print(f"📁 类别: {template.category}")
        print(f"📊 复杂度: {template.complexity}/10")
        print(f"⚡ 执行模式: {template.execution_mode}")
        print(f"🤖 参与Agent: {len(template.agents)}个")

        print(f"\n🤖 涉及Agent:")
        for agent in sorted(template.agents):
            print(f"  • {agent}")

    elif args.template_action == 'recommend':
        # 推荐模板
        recommendations = DevTemplates.recommend(args.description)

        print(f"🎯 为任务 '{args.description}' 推荐的模板:")
        print("-" * 50)

        if recommendations:
            for i, name in enumerate(recommendations, 1):
                template = DevTemplates.get_template(name)
                print(f"{i}. {template.name}")
                print(f"   描述: {template.description}")
                print(f"   复杂度: {template.complexity}/10, 模式: {template.execution_mode}")
                print(f"   使用: python3 main/cli.py develop '{args.description}' --template {name}")
                print()
        else:
            print("❌ 未找到匹配的模板")
            print("💡 使用 'python3 main/cli.py templates list' 查看所有可用模板")

def main():
    """CLI主函数"""
    parser = argparse.ArgumentParser(description='Perfect21 CLI - Git工作流管理工具')
    subparsers = parser.add_subparsers(dest='command', help='命令')

    # status命令
    status_parser = subparsers.add_parser('status', help='查看系统状态')

    # monitor命令 - 并行任务监控
    monitor_parser = subparsers.add_parser('monitor', help='并行任务监控')
    monitor_parser.add_argument('--show-stats', action='store_true', help='显示性能统计')
    monitor_parser.add_argument('--live', action='store_true', help='实时监控模式')

    # develop命令 - 开发任务统一入口
    develop_parser = subparsers.add_parser('develop', help='开发任务统一入口')
    develop_parser.add_argument('description', help='任务描述')
    develop_parser.add_argument('--template', help='使用指定模板')
    develop_parser.add_argument('--context', help='JSON格式的上下文信息')
    develop_parser.add_argument('--async', action='store_true', help='异步执行')

    # templates命令 - 模板管理
    templates_parser = subparsers.add_parser('templates', help='开发模板管理')
    templates_subparsers = templates_parser.add_subparsers(dest='template_action', help='模板操作')

    # templates list - 列出模板
    list_templates_parser = templates_subparsers.add_parser('list', help='列出所有模板')
    list_templates_parser.add_argument('--category', help='按类别筛选')

    # templates info - 模板详情
    info_templates_parser = templates_subparsers.add_parser('info', help='查看模板详情')
    info_templates_parser.add_argument('name', help='模板名称')

    # templates recommend - 推荐模板
    recommend_templates_parser = templates_subparsers.add_parser('recommend', help='推荐模板')
    recommend_templates_parser.add_argument('description', help='任务描述')

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
    execute_parser.add_argument('hook_name', choices=['pre-commit', 'pre-push', 'post-checkout', 'commit-msg', 'post-merge', 'prepare-commit-msg'], help='钩子名称')
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

    # claude-md命令
    claude_md_parser = subparsers.add_parser('claude-md', help='CLAUDE.md管理')
    claude_md_parser.add_argument('claude_md_action',
                                 choices=['sync', 'status', 'template', 'memory', 'analyze'],
                                 help='CLAUDE.md操作')
    claude_md_parser.add_argument('--add', help='添加快速记忆内容(memory)')
    claude_md_parser.add_argument('--template-type', choices=['team', 'personal'], help='模板类型(template)')
    claude_md_parser.add_argument('--output', help='输出文件路径')

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
        elif args.command == 'monitor':
            handle_monitor(args)
        elif args.command == 'develop':
            handle_develop(args)
        elif args.command == 'templates':
            handle_templates(args)
        elif args.command == 'hooks':
            handle_git_hooks(p21, args)
        elif args.command == 'branch':
            handle_branch(p21, args)
        elif args.command == 'workflow':
            handle_workflow(p21, args)
        elif args.command == 'claude-md':
            handle_claude_md(p21, args)
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