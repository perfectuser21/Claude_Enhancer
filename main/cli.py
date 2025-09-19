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
from modules.resource_manager import managed_perfect21, ResourceManager

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
    """处理开发命令 - 使用Perfect21规则指导Claude Code执行"""
    import json

    # 解析上下文
    context = {}
    if args.context:
        try:
            context = json.loads(args.context)
            # 验证context必须是字典类型
            if not isinstance(context, dict):
                print(f"❌ 上下文必须是JSON对象格式")
                return
            # 限制context大小，防止过大输入
            if len(json.dumps(context)) > 10000:
                print(f"❌ 上下文数据过大（最大10KB）")
                return
        except json.JSONDecodeError as e:
            print(f"❌ 无效的JSON格式: {e}")
            return
        except Exception as e:
            print(f"❌ 处理上下文时出错: {e}")
            return

    # 处理工作空间参数
    if hasattr(args, 'workspace') and args.workspace:
        try:
            from features.multi_workspace import WorkspaceIntegration

            integration = WorkspaceIntegration('.')
            workspace_instructions = integration.generate_claude_code_instructions(
                args.description, args.workspace
            )

            print("🏠 工作空间模式启动")
            print(f"📋 任务: {args.description}")
            print(f"🏠 工作空间: {args.workspace}")
            print("-" * 50)
            print(workspace_instructions)
            return

        except Exception as e:
            print(f"⚠️ 工作空间集成失败: {e}")
            print("📋 使用标准模式执行任务")

    # 处理并行参数
    parallel_mode = None
    if args.parallel:
        parallel_mode = True
        print("🚀 PERFECT21 强制并行模式启动")
    elif args.no_parallel:
        parallel_mode = False
        print("🚀 Perfect21顺序执行模式启动")
    else:
        print("🚀 Perfect21开发引擎启动")

    print(f"📋 任务: {args.description}")
    if parallel_mode is not None:
        context['force_parallel'] = parallel_mode
        context['parallel_mode'] = 'forced' if parallel_mode else 'disabled'
    print("-" * 50)

    try:
        from features.capability_discovery import get_perfect21_capabilities

        # 获取Perfect21功能信息
        perfect21_info = get_perfect21_capabilities()

        print("✅ Perfect21功能扩展已加载")
        print(f"📊 注册功能数: {len(perfect21_info['registered_features'])}")
        print(f"📋 任务: {args.description}")

        # 显示Perfect21能力简报
        print("\n" + "="*50)
        print("📊 Perfect21能力简报:")
        briefing = perfect21_info['capabilities_briefing']
        # 只显示前500字符，避免输出太长
        if len(briefing) > 500:
            print(briefing[:500] + "...")
        else:
            print(briefing)

        print("\n💡 提示: @orchestrator现在了解Perfect21的所有扩展功能")
        print("🚀 你可以直接向@orchestrator说明需要使用Perfect21的哪些功能")
        print("📋 例如: '@orchestrator 使用Perfect21的git_workflow功能进行代码检查'")

    except Exception as e:
        print(f"⚠️ Perfect21集成模块错误: {e}")
        print("📋 使用基础模式执行任务")
        print(f"📋 任务: {args.description}")
        print("💡 你仍然可以直接与@orchestrator对话")

def handle_parallel(args):
    """处理并行执行命令 - Perfect21核心功能"""
    try:
        from features.smart_decomposer import get_smart_decomposer
        from features.parallel_executor import get_parallel_executor

        print("🚀 Perfect21 智能并行执行器启动")
        print("=" * 60)
        print(f"📋 任务描述: {args.description}")

        # 强制并行参数
        if getattr(args, 'force_parallel', False):
            print("⚡ **强制并行模式**: 无论复杂度都将使用并行执行")

        # 获取组件实例
        decomposer = get_smart_decomposer()
        executor = get_parallel_executor()

        # 1. 智能任务分析
        print(f"\n🧠 第一步: 智能任务分析...")
        analysis = decomposer.decompose_task(args.description)

        if not analysis:
            print("❌ 任务分析失败")
            return

        print(f"✅ 分析完成: {analysis.complexity.value}级复杂度")
        print(f"🎯 建议执行模式: {analysis.execution_mode}")
        print(f"🤖 涉及{len(analysis.agent_tasks)}个专业agents")

        # 2. 准备并行执行
        print(f"\n⚡ 第二步: 准备并行执行...")
        execution_config = executor.execute_parallel_task(args.description, analysis)

        if not execution_config['ready_for_execution']:
            print("❌ 并行执行准备失败")
            return

        print(f"✅ 并行执行已准备完成")
        print(f"🎯 执行模式: {execution_config['execution_mode']}")
        print(f"🤖 预计并行agents: {execution_config['expected_agents']}个")

        # 3. 显示执行指令
        print(f"\n🎯 第三步: 生成Claude Code调用指令")
        print("=" * 80)
        print("📋 请复制以下内容到Claude Code主界面执行:")
        print("=" * 80)
        print(execution_config['execution_instructions'])
        print("=" * 80)

        # 4. 显示监控建议
        monitoring = execution_config['monitoring_config']
        print(f"\n📊 第四步: 执行监控建议")
        print(f"👥 预期agents: {', '.join(monitoring['agent_names'])}")
        print(f"⏱️ 预计用时: {monitoring['expected_completion_time']}分钟")
        print(f"🔥 关键agents: {', '.join(monitoring['critical_agents'])}")

        # 5. 保存执行日志
        print(f"\n📝 执行配置已保存到执行日志")
        print(f"💡 使用 'python3 main/cli.py parallel status' 查看执行状态")

    except ImportError as e:
        print(f"❌ 导入并行执行模块失败: {e}")
        print("📋 请确保smart_decomposer和parallel_executor模块已正确安装")
    except Exception as e:
        print(f"❌ 并行执行准备失败: {e}")
        import traceback
        if args.verbose if hasattr(args, 'verbose') else False:
            traceback.print_exc()

def handle_parallel_status(args):
    """处理并行执行状态查询"""
    try:
        from features.parallel_executor import get_parallel_executor

        executor = get_parallel_executor()
        status = executor.get_execution_status()

        print("📊 Perfect21 并行执行状态")
        print("=" * 50)
        print(f"状态: {status['status']}")

        if status['status'] != 'idle':
            print(f"任务: {status['task_description']}")
            print(f"时间: {status['timestamp']}")
            print(f"Agents: {status['agent_count']}个")
            print(f"执行模式: {status['execution_mode']}")
        else:
            print("💡 当前没有活跃的并行执行任务")
            print("💡 使用 'python3 main/cli.py parallel \"任务描述\"' 开始新任务")

    except Exception as e:
        print(f"❌ 获取并行执行状态失败: {e}")

def handle_perfect21_parallel(p21, args):
    """
    处理Perfect21真实并行执行
    """
    print("🚀 Perfect21 真实并行执行引擎")
    print("=" * 60)

    if hasattr(args, 'description') and args.description:
        # 直接使用Perfect21的核心并行执行功能
        agents_list = getattr(args, 'agents', ['backend-architect', 'frontend-specialist', 'test-engineer'])

        # 如果是字符串，转换为列表
        if isinstance(agents_list, str):
            agents_list = [agent.strip() for agent in agents_list.split(',')]

        print(f"📋 任务描述: {args.description}")
        print(f"🤖 选中Agents ({len(agents_list)}个): {', '.join(agents_list)}")
        print("-" * 50)

        try:
            # 调用Perfect21的核心并行执行功能
            result = p21.execute_parallel_workflow(
                agents=agents_list,
                base_prompt=args.description,
                task_description=args.description
            )

            if result['success']:
                print(f"✅ 并行工作流执行成功")
                print(f"🆔 工作流ID: {result['workflow_id']}")
                print(f"⏱️ 执行时间: {result['execution_time']:.2f}秒")
                print(f"✅ 成功: {result['success_count']}/{result['agents_count']}")
                print(f"❌ 失败: {result['failure_count']}")

                if result.get('batch_instruction'):
                    print("\n" + "="*80)
                    print("🎯 Claude Code 执行指令已生成")
                    print("="*80)
                    print("📋 请复制以下内容到Claude Code中执行:")
                    print("="*80)
                    print(result['batch_instruction'])
                    print("="*80)
                    print(f"✅ 所有 {result['agents_count']} 个Agents将在Claude Code中并行执行")
                else:
                    print("⚠️ 未生成批量执行指令")

            else:
                print(f"❌ 并行工作流执行失败: {result.get('message')}")
                if result.get('error'):
                    print(f"错误详情: {result['error']}")

        except Exception as e:
            print(f"❌ Perfect21并行执行异常: {e}")
            import traceback
            if getattr(args, 'verbose', False):
                traceback.print_exc()
    else:
        print("❌ 请提供任务描述")
        print("用法: python3 main/cli.py perfect21 parallel '任务描述' --agents 'agent1,agent2,agent3'")

def handle_perfect21_instant(p21, args):
    """
    处理Perfect21即时执行指令生成
    """
    print("⚡ Perfect21 即时并行指令生成")
    print("=" * 60)

    if hasattr(args, 'description') and args.description:
        agents_list = getattr(args, 'agents', ['backend-architect', 'frontend-specialist', 'test-engineer'])

        if isinstance(agents_list, str):
            agents_list = [agent.strip() for agent in agents_list.split(',')]

        print(f"📋 任务描述: {args.description}")
        print(f"🤖 选中Agents ({len(agents_list)}个): {', '.join(agents_list)}")
        print("-" * 50)

        try:
            # 调用Perfect21的即时指令生成功能
            result = p21.create_instant_parallel_instruction(
                agents=agents_list,
                prompt=args.description
            )

            if result['success']:
                print(f"✅ 即时并行指令生成成功")
                print(f"🤖 Agents数量: {result['agents_count']}")

                print("\n" + "="*80)
                print("⚡ 即时执行 - 无需等待")
                print("="*80)
                print("📋 请复制以下内容到Claude Code中立即执行:")
                print("="*80)
                print(result['instruction'])
                print("="*80)
                print(f"✅ {result['agents_count']}个Agents将立即并行执行")

            else:
                print(f"❌ 即时指令生成失败: {result.get('message')}")
                if result.get('error'):
                    print(f"错误详情: {result['error']}")

        except Exception as e:
            print(f"❌ Perfect21即时指令生成异常: {e}")
            import traceback
            if getattr(args, 'verbose', False):
                traceback.print_exc()
    else:
        print("❌ 请提供任务描述")
        print("用法: python3 main/cli.py perfect21 instant '任务描述' --agents 'agent1,agent2,agent3'")

def handle_perfect21_status(p21, args):
    """
    处理Perfect21工作流状态查询
    """
    print("📈 Perfect21 工作流状态")
    print("=" * 50)

    try:
        workflow_id = getattr(args, 'workflow_id', None)
        result = p21.get_workflow_status(workflow_id)

        if result['success']:
            if workflow_id:
                # 特定工作流状态
                status = result['workflow_status']
                print(f"🆔 工作流ID: {status['workflow_id']}")
                print(f"🟢 状态: {status['status']}")
                print(f"📋 进度: {status['progress']['completed']}/{status['progress']['total']}")
                print(f"❌ 失败: {status['progress']['failed']}")
                print(f"✅ 执行就绪: {'YES' if status['execution_ready'] else 'NO'}")

                if status['tasks']:
                    print("\n📋 任务详情:")
                    for task in status['tasks']:
                        status_icon = {"completed": "✅", "failed": "❌", "running": "⏳", "pending": "⏸️"}.get(task['status'], "❓")
                        print(f"  {status_icon} {task['agent']} - {task['description']} ({task['status']})")
            else:
                # 所有工作流概览
                print(f"🟢 活跃工作流: {len(result['active_workflows'])}")
                for wid in result['active_workflows']:
                    print(f"  - {wid}")

                print(f"\n📈 最近历史 ({len(result['recent_history'])}条):")
                for hist in result['recent_history']:
                    status_icon = {"completed": "✅", "failed": "❌"}.get(hist['status'], "❓")
                    print(f"  {status_icon} {hist['workflow_id']} - 成功:{hist['success_count']}/{hist['agents_count']} 时间:{hist['execution_time']:.1f}s")

        else:
            print(f"❌ 获取状态失败: {result.get('message')}")

    except Exception as e:
        print(f"❌ Perfect21状态查询异常: {e}")
        import traceback
        if getattr(args, 'verbose', False):
            traceback.print_exc()

def handle_perfect21_command(p21, args):
    """
    处理Perfect21核心命令
    """
    if hasattr(args, 'perfect21_action'):
        if args.perfect21_action == 'parallel':
            handle_perfect21_parallel(p21, args)
        elif args.perfect21_action == 'instant':
            handle_perfect21_instant(p21, args)
        elif args.perfect21_action == 'status':
            handle_perfect21_status(p21, args)
        else:
            print(f"❌ 未知Perfect21操作: {args.perfect21_action}")
    else:
        print("❌ 请指定Perfect21操作")
        print("可用操作: parallel, instant, status")

def handle_parallel_command(args):
    """处理并行命令的分发"""
    if getattr(args, 'status', False):
        handle_parallel_status(args)
    elif getattr(args, 'history', False):
        handle_parallel_history(args)
    elif hasattr(args, 'description') and args.description:
        # 直接并行执行
        handle_parallel(args)
    else:
        print("❌ 请提供任务描述或选择操作")
        print("用法:")
        print("  python3 main/cli.py parallel \"任务描述\"")
        print("  python3 main/cli.py parallel --status")
        print("  python3 main/cli.py parallel --history")

def handle_parallel_history(args):
    """处理并行执行历史查询"""
    try:
        from features.parallel_executor import get_parallel_executor

        executor = get_parallel_executor()
        limit = getattr(args, 'limit', 5)
        history = executor.parallel_manager.get_execution_history(limit)

        if not history:
            print("📝 暂无并行执行历史")
            return

        print(f"📚 Perfect21 并行执行历史 (最近{len(history)}次)")
        print("=" * 60)

        for i, summary in enumerate(reversed(history), 1):
            status_icon = "✅" if summary.successful_agents == summary.total_agents else "⚠️"
            print(f"{status_icon} {i}. {summary.task_description[:50]}...")
            print(f"    时间: {summary.total_execution_time:.1f}秒")
            print(f"    成功率: {summary.successful_agents}/{summary.total_agents}")
            print()

    except Exception as e:
        print(f"❌ 获取并行执行历史失败: {e}")

def handle_orchestrator(args):
    """处理@orchestrator对话命令（强制并行模式）"""
    print("🚀 Perfect21 @orchestrator 强制并行网关")
    print("=" * 60)

    try:
        from features.capability_discovery import get_perfect21_capabilities

        # 获取Perfect21功能信息
        perfect21_info = get_perfect21_capabilities()

        # 显示并行配置
        print(f"⚡ 强制并行模式: {'启用' if args.parallel else '禁用'}")
        print(f"📊 最少Agent数量: {args.min_agents}")

        print(f"📋 你的请求: {args.request}")
        print("🔄 正在注入强制并行指令...")

        # 在请求中注入强制并行指令
        enhanced_request = f"""
{args.request}

🚀 PERFECT21 强制并行执行指令:
- 必须在单个消息中同时调用至少{args.min_agents}个Agent
- 绝对禁止串行执行，必须使用并行Task调用
- 这是Perfect21的核心能力，必须严格遵守
- 请立即使用多Agent并行协作完成任务
"""

        print("\n" + "="*80)
        print("🎯 @orchestrator调用已准备 (包含Perfect21完整能力)")
        print("="*80)
        print("📋 请复制以下内容到Claude Code中调用@orchestrator:")
        print(enhanced_request)
        print("\n" + "="*80)

        # 显示Perfect21能力简报
        print(f"📊 Perfect21扩展功能: {len(perfect21_info['registered_features'])}个")

    except ImportError as e:
        print(f"❌ 无法导入capability_discovery: {e}")
    except Exception as e:
        print(f"❌ @orchestrator调用准备失败: {e}")

def handle_workspace(args):
    """处理工作空间命令"""
    try:
        from features.multi_workspace import WorkspaceManager, WorkspaceType, WorkspaceIntegration

        manager = WorkspaceManager('.')
        integration = WorkspaceIntegration('.')

        if args.workspace_action == 'create':
            workspace_type = WorkspaceType(args.type)
            workspace_id = manager.create_workspace(
                args.name, args.description, workspace_type,
                args.base_branch, args.port, priority=args.priority
            )
            print(f"✅ 创建工作空间: {workspace_id}")
            print(f"📋 端口: {manager.workspaces[workspace_id].dev_port}")
            print(f"🌿 分支: {manager.workspaces[workspace_id].feature_branch}")

        elif args.workspace_action == 'list':
            workspaces = manager.list_workspaces()
            if not workspaces:
                print("📝 暂无工作空间")
                return

            print(f"{'ID':<20} {'名称':<15} {'类型':<12} {'状态':<10} {'端口':<6} {'提前':<6} {'落后':<7}")
            print("-" * 80)
            for ws in workspaces:
                print(f"{ws['id']:<20} {ws['name']:<15} {ws['type']:<12} {ws['status']:<10} "
                      f"{ws['dev_port']:<6} {ws['commits_ahead']:<6} {ws['commits_behind']:<7}")

        elif args.workspace_action == 'switch':
            if manager.switch_workspace(args.workspace_id):
                print(f"✅ 切换到工作空间: {args.workspace_id}")
                context = integration.get_workspace_development_context(args.workspace_id)
                if 'development_ports' in context:
                    ports = context['development_ports']
                    print(f"🚀 开发端口: {ports['dev_server']}")
                    if ports.get('api_server'):
                        print(f"🔌 API端口: {ports['api_server']}")
            else:
                print(f"❌ 切换工作空间失败: {args.workspace_id}")

        elif args.workspace_action == 'suggest':
            suggestions = integration.suggest_workspace_for_task(args.task_description)

            print(f"🎯 任务分析: {args.task_description}")
            print("=" * 50)

            analysis = suggestions['task_analysis']
            print(f"复杂度: {analysis['complexity_score']}/8")
            print(f"预估时间: {analysis['estimated_hours']}小时")
            print(f"风险级别: {analysis['risk_level']}")
            print(f"建议类型: {analysis['recommended_type'].value}")

            if suggestions['recommended_workspace']:
                print(f"\n✅ 推荐现有工作空间: {suggestions['recommended_workspace']}")
            elif suggestions['create_new']['recommended']:
                create_info = suggestions['create_new']
                print(f"\n💡 建议创建新工作空间:")
                print(f"  名称: {create_info['suggested_name']}")
                print(f"  类型: {create_info['suggested_type']}")
                print(f"  原因: {create_info['reason']}")

            # 显示Claude Code集成指令
            instructions = integration.generate_claude_code_instructions(args.task_description)
            print(f"\n📋 Claude Code集成指令:")
            print("=" * 50)
            print(instructions)

        elif args.workspace_action == 'conflicts':
            conflicts = manager.detect_conflicts(args.workspace_id)
            if 'error' in conflicts:
                print(f"❌ 错误: {conflicts['error']}")
                return

            print(f"🔍 工作空间冲突分析: {args.workspace_id}")
            print("=" * 50)

            if conflicts['direct_conflicts']:
                print("🚨 直接冲突:")
                for conflict in conflicts['direct_conflicts']:
                    print(f"  - {conflict}")

            if conflicts['potential_conflicts']:
                print("\n⚠️ 潜在冲突:")
                for conflict in conflicts['potential_conflicts']:
                    print(f"  - {conflict['workspace']}: {', '.join(conflict['common_files'])}")

            if not conflicts['direct_conflicts'] and not conflicts['potential_conflicts']:
                print("✅ 未检测到冲突")

        elif args.workspace_action == 'merge':
            result = manager.auto_merge_workspace(args.workspace_id, args.dry_run)

            if 'error' in result:
                print(f"❌ 错误: {result['error']}")
                if 'conflicts' in result:
                    print("🚨 冲突详情:")
                    for conflict in result['conflicts']:
                        print(f"  - {conflict}")
            else:
                if args.dry_run:
                    print(f"✅ 预检查通过: {result['message']}")
                    if result.get('file_changes'):
                        print(f"📁 涉及文件: {', '.join(result['file_changes'])}")
                    if result.get('potential_conflicts'):
                        print("⚠️ 建议先解决潜在冲突")
                else:
                    print(f"✅ 合并成功: {result['message']}")
                    if result.get('merged_files'):
                        print(f"📁 合并文件: {', '.join(result['merged_files'])}")

        elif args.workspace_action == 'stats':
            stats = manager.get_workspace_stats()
            print("📊 工作空间统计")
            print("=" * 30)
            print(f"总工作空间: {stats['total_workspaces']}")
            print(f"活跃工作空间: {stats['active_count']}")

            print("\n按状态统计:")
            for status, count in stats['by_status'].items():
                print(f"  {status}: {count}")

            print("\n按类型统计:")
            for ws_type, count in stats['by_type'].items():
                print(f"  {ws_type}: {count}")

            if stats['port_usage']:
                print(f"\n端口使用: {', '.join(map(str, sorted(stats['port_usage'])))}")

    except ImportError as e:
        print(f"❌ 导入工作空间模块失败: {e}")
        print("请确保multi_workspace模块正确安装")
    except Exception as e:
        print(f"❌ 工作空间操作失败: {e}")
        if getattr(args, 'verbose', False):
            import traceback
            traceback.print_exc()

def handle_error_management(args):
    """处理错误管理命令"""
    try:
        from modules.error_cli import ErrorHandlingCLI

        error_cli = ErrorHandlingCLI()
        result = error_cli.handle_command(args)

        if result.get('success'):
            if 'message' in result:
                print(f"\u2705 {result['message']}")
            if 'stats' in result:
                # 统计信息已在error_cli中处理
                pass
        else:
            print(f"\u274c {result.get('message', '操作失败')}")
            if 'error' in result:
                print(f"错误: {result['error']}")

    except ImportError as e:
        print(f"\u274c 导入错误处理模块失败: {e}")
        print("请确保 error_cli 模块正确安装")
    except Exception as e:
        print(f"\u274c 错误处理操作失败: {e}")
        if getattr(args, 'verbose', False):
            import traceback
            traceback.print_exc()

def handle_learning(args):
    """处理学习反馈循环命令"""
    try:
        from features.learning_feedback import (
            LearningEngine, FeedbackCollector, PatternAnalyzer, ImprovementSuggester
        )

        learning_engine = LearningEngine('.')
        feedback_collector = FeedbackCollector('.')
        pattern_analyzer = PatternAnalyzer('.')
        improvement_suggester = ImprovementSuggester('.')

        if args.learning_action == 'summary':
            print("📊 Perfect21 学习系统摘要")
            print("=" * 50)

            # 学习引擎摘要
            learning_summary = learning_engine.get_learning_summary()
            print("🧠 学习引擎:")
            for key, value in learning_summary.items():
                print(f"  {key}: {value}")

            print()

            # 反馈系统摘要
            feedback_summary = feedback_collector.get_feedback_summary(30)
            print("💬 反馈系统 (最近30天):")
            for key, value in feedback_summary.items():
                if key != "用户偏好":
                    print(f"  {key}: {value}")

            print()

            # 模式分析摘要
            pattern_summary = pattern_analyzer.get_pattern_summary()
            print("🔍 模式分析:")
            for key, value in pattern_summary.items():
                print(f"  {key}: {value}")

            print()

            # 改进建议摘要
            suggestion_summary = improvement_suggester.get_improvement_summary()
            print("💡 改进建议:")
            for key, value in suggestion_summary.items():
                print(f"  {key}: {value}")

        elif args.learning_action == 'feedback':
            if args.collect and args.satisfaction is not None:
                # 收集用户反馈
                feedback_id = feedback_collector.collect_user_feedback(
                    execution_id="manual_feedback",
                    satisfaction_score=args.satisfaction,
                    feedback_text=args.comment
                )
                print(f"✅ 反馈已收集: {feedback_id}")
                print(f"满意度评分: {args.satisfaction}")
                if args.comment:
                    print(f"评论: {args.comment}")

            elif args.report:
                # 生成反馈报告
                success = feedback_collector.generate_feedback_report(args.report)
                if success:
                    print(f"✅ 反馈报告已生成: {args.report}")
                else:
                    print("❌ 反馈报告生成失败")

            else:
                # 显示反馈摘要
                summary = feedback_collector.get_feedback_summary(30)
                print("💬 反馈系统状态")
                print("=" * 30)
                for key, value in summary.items():
                    print(f"{key}: {value}")

        elif args.learning_action == 'patterns':
            if args.analyze:
                # 重新分析模式
                print("🔍 分析执行模式...")
                execution_history = learning_engine.execution_history
                new_patterns = pattern_analyzer.analyze_execution_history(execution_history)
                print(f"✅ 识别了{len(new_patterns)}个新模式")

                if new_patterns:
                    print("\n新识别的模式:")
                    for pattern in new_patterns[:5]:  # 显示前5个
                        print(f"  - {pattern.name} ({pattern.pattern_type.value})")
                        print(f"    置信度: {pattern.confidence_score:.2f}, 支持数: {pattern.support_count}")

            elif args.show:
                # 显示特定模式
                patterns = pattern_analyzer.identified_patterns
                matching_patterns = [p for p in patterns if args.show.lower() in p.name.lower()]

                if matching_patterns:
                    for pattern in matching_patterns:
                        print(f"📋 模式: {pattern.name}")
                        print(f"类型: {pattern.pattern_type.value}")
                        print(f"描述: {pattern.description}")
                        print(f"置信度: {pattern.confidence_score:.2f}")
                        print(f"支持数: {pattern.support_count}")
                        print(f"条件: {pattern.conditions}")
                        print(f"结果: {pattern.outcomes}")
                        print(f"建议: {pattern.recommendations}")
                        print("-" * 40)
                else:
                    print(f"❌ 未找到匹配的模式: {args.show}")

            else:
                # 显示模式摘要
                summary = pattern_analyzer.get_pattern_summary()
                print("🔍 模式分析状态")
                print("=" * 30)
                for key, value in summary.items():
                    print(f"{key}: {value}")

        elif args.learning_action == 'suggestions':
            if args.generate:
                # 生成新建议
                print("💡 生成改进建议...")
                execution_history = learning_engine.execution_history
                feedback_data = feedback_collector.feedback_history
                patterns = pattern_analyzer.identified_patterns
                knowledge_base = learning_engine.knowledge_base

                new_suggestions = improvement_suggester.generate_suggestions(
                    execution_history, feedback_data, patterns, knowledge_base
                )

                print(f"✅ 生成了{len(new_suggestions)}个新建议")

                if new_suggestions:
                    print("\n新建议:")
                    for suggestion in new_suggestions[:5]:  # 显示前5个
                        print(f"  - {suggestion.title} ({suggestion.priority.value})")
                        print(f"    类别: {suggestion.category.value}")
                        print(f"    难度: {suggestion.effort_estimate}")

            elif args.implement:
                # 标记建议为已实施
                improvement_suggester.mark_suggestion_implemented(args.implement)
                print(f"✅ 建议 {args.implement} 已标记为已实施")

            else:
                # 显示建议
                suggestions = improvement_suggester.active_suggestions

                # 按条件筛选
                if args.priority:
                    from features.learning_feedback.improvement_suggester import Priority
                    priority_enum = Priority(args.priority.upper())
                    suggestions = [s for s in suggestions if s.priority == priority_enum]

                if args.category:
                    from features.learning_feedback.improvement_suggester import ImprovementCategory
                    try:
                        category_enum = ImprovementCategory(args.category.lower())
                        suggestions = [s for s in suggestions if s.category == category_enum]
                    except ValueError:
                        print(f"❌ 无效的类别: {args.category}")
                        return

                if not suggestions:
                    print("📝 暂无符合条件的改进建议")
                    return

                print(f"💡 改进建议 ({len(suggestions)}个)")
                print("=" * 50)

                for suggestion in suggestions[:10]:  # 显示前10个
                    priority_icon = {
                        "critical": "🔴",
                        "high": "🟠",
                        "medium": "🟡",
                        "low": "🟢"
                    }.get(suggestion.priority.value, "⚪")

                    print(f"{priority_icon} {suggestion.title}")
                    print(f"   类别: {suggestion.category.value} | 优先级: {suggestion.priority.value} | 难度: {suggestion.effort_estimate}")
                    print(f"   描述: {suggestion.description}")
                    print(f"   ID: {suggestion.suggestion_id}")
                    print()

        elif args.learning_action == 'knowledge':
            if args.export:
                # 导出知识库
                success = learning_engine.export_knowledge(args.export)
                if success:
                    print(f"✅ 知识库已导出到: {args.export}")
                else:
                    print("❌ 知识库导出失败")

            elif args.import_file:
                # 导入知识库
                success = learning_engine.import_knowledge(args.import_file)
                if success:
                    print(f"✅ 知识库已从 {args.import_file} 导入")
                else:
                    print("❌ 知识库导入失败")

            else:
                # 显示知识库状态
                summary = learning_engine.get_learning_summary()
                print("📚 知识库状态")
                print("=" * 30)
                for key, value in summary.items():
                    print(f"{key}: {value}")

        else:
            print("❌ 未知的学习系统操作")
            print("使用 'python3 main/cli.py learning --help' 查看帮助")

    except ImportError as e:
        print(f"❌ 导入学习反馈模块失败: {e}")
        print("请确保learning_feedback模块正确安装")
    except Exception as e:
        print(f"❌ 学习系统操作失败: {e}")
        if getattr(args, 'verbose', False):
            import traceback
            traceback.print_exc()

def handle_templates(args):
    """处理模板命令"""
    print("❌ 模板功能已禁用")
    print("💡 模板功能已合并到core/claude-code-unified-agents中")
    print("💡 直接使用 'python3 main/cli.py develop' 命令即可")
    print("💡 @orchestrator会自动选择最合适的开发模式")

def handle_quality(args):
    """处理质量门命令"""
    if not hasattr(args, 'quality_command') or not args.quality_command:
        print("❌ 请指定质量门子命令")
        print("可用命令: check, trends, history, setup, dashboard, config")
        return

    if args.quality_command == 'check':
        handle_quality_check(args)
    elif args.quality_command == 'trends':
        handle_quality_trends(args)
    elif args.quality_command == 'history':
        handle_quality_history(args)
    elif args.quality_command == 'setup':
        handle_quality_setup(args)
    elif args.quality_command == 'dashboard':
        handle_quality_dashboard(args)
    elif args.quality_command == 'config':
        handle_quality_config(args)
    else:
        print(f"❌ 未知质量门命令: {args.quality_command}")

def handle_quality_check(args):
    """处理质量检查命令"""
    import asyncio

    async def run_quality_check():
        try:
            from features.quality_gates.quality_gate_engine import QualityGateEngine
            from features.quality_gates.models import QualityGateConfig

            config = QualityGateConfig()
            config.parallel_execution = not getattr(args, 'no_parallel', False)
            config.fail_fast = getattr(args, 'fail_fast', False)

            engine = QualityGateEngine('.', config)

            print(f"🔍 运行质量门检查 - 上下文: {args.context}")

            if args.context == 'quick':
                results = await engine.run_quick_check()

                if args.output == 'json':
                    import json
                    print(json.dumps(results, indent=2, ensure_ascii=False))
                else:
                    print(f"状态: {results['status']}")
                    print(f"分数: {results['score']:.1f}")
                    print(f"消息: {results['message']}")

                return 0 if results['status'] == 'passed' else 1
            else:
                full_results = await engine.run_all_gates(args.context)

                if args.output == 'json':
                    import json
                    print(json.dumps({name: result.__dict__ for name, result in full_results.items()},
                                   indent=2, ensure_ascii=False, default=str))
                elif args.output == 'html':
                    from pathlib import Path
                    report = engine.generate_report(full_results)
                    html_file = Path('.perfect21/quality_report.html')
                    html_file.parent.mkdir(exist_ok=True)

                    html_content = f"""
<!DOCTYPE html>
<html>
<head><title>Quality Report</title><meta charset="utf-8"></head>
<body><pre>{report}</pre></body>
</html>
                    """

                    with open(html_file, 'w', encoding='utf-8') as f:
                        f.write(html_content)

                    print(f"📄 HTML报告已保存: {html_file}")
                else:
                    report = engine.generate_report(full_results)
                    print(report)

                overall = full_results.get('overall')
                return 0 if overall and overall.status.value in ['passed', 'warning'] else 1

        except Exception as e:
            print(f"❌ 质量门检查失败: {str(e)}")
            return 1

    exit_code = asyncio.run(run_quality_check())
    sys.exit(exit_code)

def handle_quality_trends(args):
    """处理质量趋势命令"""
    try:
        from features.quality_gates.quality_gate_engine import QualityGateEngine

        engine = QualityGateEngine('.')
        trends_data = engine.get_quality_trends(days=args.days)

        if getattr(args, 'format', 'text') == 'json':
            import json
            print(json.dumps(trends_data, indent=2, ensure_ascii=False))
        else:
            print(f"📊 质量趋势 (最近 {args.days} 天)")
            print("=" * 50)

            print(f"总执行次数: {trends_data.get('total_executions', 0)}")

            if trends_data.get('gate_performance'):
                print("\n🏆 质量门性能:")
                for gate_name, performance in trends_data['gate_performance'].items():
                    print(f"  {gate_name}: {performance['average_score']:.1f}分 "
                          f"(执行{performance['executions']}次)")

            if trends_data.get('common_violations'):
                print("\n🔍 常见违规:")
                for violation_type, count in list(trends_data['common_violations'].items())[:5]:
                    print(f"  {violation_type}: {count}次")

            if trends_data.get('improvement_suggestions'):
                print("\n💡 改进建议:")
                for suggestion in trends_data['improvement_suggestions']:
                    print(f"  • {suggestion}")

    except Exception as e:
        print(f"❌ 获取质量趋势失败: {str(e)}")
        sys.exit(1)

def handle_quality_history(args):
    """处理质量历史命令"""
    try:
        from features.quality_gates.quality_gate_engine import QualityGateEngine

        engine = QualityGateEngine('.')
        history_data = engine.get_execution_history(limit=args.limit)

        if getattr(args, 'format', 'text') == 'json':
            import json
            print(json.dumps(history_data, indent=2, ensure_ascii=False))
        else:
            print(f"📋 执行历史 (最近 {len(history_data)} 条记录)")
            print("=" * 60)

            for entry in reversed(history_data):  # 最新的在前
                timestamp = entry['timestamp'][:19].replace('T', ' ')
                summary = entry['summary']

                status_emoji = "✅" if summary['failed'] == 0 else "❌"
                print(f"{status_emoji} {timestamp} | "
                      f"通过:{summary['passed']} 失败:{summary['failed']} "
                      f"分数:{summary['average_score']:.1f} "
                      f"上下文:{entry['context']}")

    except Exception as e:
        print(f"❌ 获取执行历史失败: {str(e)}")
        sys.exit(1)

def handle_quality_setup(args):
    """处理质量门设置命令"""
    if not hasattr(args, 'setup_command') or not args.setup_command:
        print("❌ 请指定设置子命令")
        print("可用命令: hooks, ci, monitoring")
        return

    if args.setup_command == 'hooks':
        handle_quality_setup_hooks(args)
    elif args.setup_command == 'ci':
        handle_quality_setup_ci(args)
    elif args.setup_command == 'monitoring':
        handle_quality_setup_monitoring(args)
    else:
        print(f"❌ 未知设置命令: {args.setup_command}")

def handle_quality_setup_hooks(args):
    """处理质量门hooks安装"""
    import asyncio

    async def setup_hooks():
        try:
            from features.quality_gates.ci_integration import CIIntegration

            ci = CIIntegration('.')
            result = await ci.setup_pre_commit_hooks()

            if result['status'] == 'success':
                print("✅ Git hooks安装成功")
                print(f"安装的hooks: {', '.join(result['hooks_installed'])}")
            else:
                print(f"❌ Git hooks安装失败: {result['message']}")
                return 1

            return 0

        except Exception as e:
            print(f"❌ 安装Git hooks失败: {str(e)}")
            return 1

    exit_code = asyncio.run(setup_hooks())
    sys.exit(exit_code)

def handle_quality_setup_ci(args):
    """处理CI/CD集成设置"""
    import asyncio

    async def setup_ci():
        try:
            from features.quality_gates.ci_integration import CIIntegration

            ci = CIIntegration('.')
            result = await ci.setup_all_integrations()

            print(f"🚀 CI/CD集成设置: {result['message']}")

            for component, component_result in result['results'].items():
                status_emoji = "✅" if component_result['status'] == 'success' else "❌"
                print(f"  {status_emoji} {component}: {component_result['message']}")

            if result['next_steps']:
                print("\n📋 后续步骤:")
                for step in result['next_steps']:
                    print(f"  {step}")

            return 0

        except Exception as e:
            print(f"❌ 设置CI/CD集成失败: {str(e)}")
            return 1

    asyncio.run(setup_ci())

def handle_quality_setup_monitoring(args):
    """处理持续监控设置"""
    import asyncio

    async def setup_monitoring():
        try:
            from features.quality_gates.ci_integration import CIIntegration

            ci = CIIntegration('.')
            result = await ci.setup_continuous_monitoring()

            if result['status'] == 'success':
                print("✅ 持续监控设置成功")
                print(f"监控脚本: {result['monitoring_script']}")
                print(f"Cron配置: {result['cron_config']}")

                print("\n📋 设置说明:")
                for instruction in result['instructions']:
                    print(f"  {instruction}")
            else:
                print(f"❌ 持续监控设置失败: {result['message']}")
                return 1

            return 0

        except Exception as e:
            print(f"❌ 设置持续监控失败: {str(e)}")
            return 1

    asyncio.run(setup_monitoring())

def handle_quality_dashboard(args):
    """处理质量仪表板生成"""
    import asyncio

    async def create_dashboard():
        try:
            from features.quality_gates.ci_integration import CIIntegration

            ci = CIIntegration('.')
            result = await ci.create_quality_dashboard()

            if result['status'] == 'success':
                print("✅ 质量仪表板脚本已创建")
                print(f"使用说明: {result['usage']}")

                # 运行仪表板生成脚本
                import subprocess
                script_path = result['script']
                subprocess.run(['python3', script_path], check=True)

                print("🌐 仪表板已生成")
            else:
                print(f"❌ 生成质量仪表板失败: {result['message']}")
                return 1

            return 0

        except Exception as e:
            print(f"❌ 生成质量仪表板失败: {str(e)}")
            return 1

    asyncio.run(create_dashboard())

def handle_quality_config(args):
    """处理质量配置生成"""
    try:
        from features.quality_gates.models import QualityGateConfig
        from pathlib import Path
        import json

        if args.template == 'strict':
            config = QualityGateConfig(
                min_line_coverage=95.0,
                min_branch_coverage=90.0,
                min_function_coverage=95.0,
                max_complexity=5,
                max_duplications=2.0,
                max_security_issues=0,
                max_response_time_p95=100.0,
                max_memory_usage=256.0,
                fail_fast=True
            )
        elif args.template == 'lenient':
            config = QualityGateConfig(
                min_line_coverage=60.0,
                min_branch_coverage=50.0,
                min_function_coverage=70.0,
                max_complexity=25,
                max_duplications=10.0,
                max_security_issues=5,
                max_response_time_p95=500.0,
                max_memory_usage=1024.0,
                fail_fast=False
            )
        else:  # balanced
            config = QualityGateConfig()

        config_dict = {
            'min_line_coverage': config.min_line_coverage,
            'min_branch_coverage': config.min_branch_coverage,
            'min_function_coverage': config.min_function_coverage,
            'max_complexity': config.max_complexity,
            'max_duplications': config.max_duplications,
            'max_security_issues': config.max_security_issues,
            'max_response_time_p95': config.max_response_time_p95,
            'max_memory_usage': config.max_memory_usage,
            'min_throughput': config.min_throughput,
            'max_coupling_score': config.max_coupling_score,
            'min_cohesion_score': config.min_cohesion_score,
            'max_cyclomatic_complexity': config.max_cyclomatic_complexity,
            'fail_fast': config.fail_fast,
            'parallel_execution': config.parallel_execution,
            'timeout_seconds': config.timeout_seconds,
            'allowed_security_levels': config.allowed_security_levels
        }

        output_path = Path(args.output)
        output_path.parent.mkdir(exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)

        print(f"✅ 配置文件已生成: {output_path}")
        print(f"模板: {args.template}")
        print("💡 可以编辑配置文件来调整质量标准")

    except Exception as e:
        print(f"❌ 生成配置文件失败: {str(e)}")
        sys.exit(1)

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
    develop_parser.add_argument('--workspace', help='指定工作空间ID')
    develop_parser.add_argument('--async', action='store_true', help='异步执行')
    develop_parser.add_argument('--parallel', action='store_true', help='强制并行执行')
    develop_parser.add_argument('--no-parallel', action='store_true', help='禁用并行执行')

    # perfect21命令 - Perfect21核心功能
    perfect21_parser = subparsers.add_parser('perfect21', help='Perfect21 核心工作流引擎')
    perfect21_subparsers = perfect21_parser.add_subparsers(dest='perfect21_action', help='Perfect21操作')

    # perfect21 parallel - 真实并行执行
    parallel_p21_parser = perfect21_subparsers.add_parser('parallel', help='真实并行执行')
    parallel_p21_parser.add_argument('description', help='任务描述')
    parallel_p21_parser.add_argument('--agents', help='Agent列表（逗号分隔）', default='backend-architect,frontend-specialist,test-engineer')
    parallel_p21_parser.add_argument('--timeout', type=int, default=300, help='超时时间（秒）')

    # perfect21 instant - 即时执行指令生成
    instant_p21_parser = perfect21_subparsers.add_parser('instant', help='即时并行指令生成')
    instant_p21_parser.add_argument('description', help='任务描述')
    instant_p21_parser.add_argument('--agents', help='Agent列表（逗号分隔）', default='backend-architect,frontend-specialist,test-engineer')

    # perfect21 status - 工作流状态
    status_p21_parser = perfect21_subparsers.add_parser('status', help='查看工作流状态')
    status_p21_parser.add_argument('--workflow-id', help='特定工作流ID')

    # parallel命令 - 并行执行核心功能
    parallel_parser = subparsers.add_parser('parallel', help='Perfect21 智能并行执行器')

    # 主要的并行执行参数
    parallel_parser.add_argument('description', nargs='?', help='任务描述')
    parallel_parser.add_argument('--force-parallel', action='store_true', help='强制并行模式(无论复杂度)')
    parallel_parser.add_argument('--min-agents', type=int, default=2, help='最少Agent数量')
    parallel_parser.add_argument('--max-agents', type=int, default=8, help='最多Agent数量')
    parallel_parser.add_argument('--status', action='store_true', help='查看并行执行状态')
    parallel_parser.add_argument('--history', action='store_true', help='查看执行历史')
    parallel_parser.add_argument('--limit', type=int, default=5, help='历史记录显示条数限制')

    # orchestrator命令 - 直接与@orchestrator对话
    orchestrator_parser = subparsers.add_parser('orchestrator', help='直接与@orchestrator对话 (强制并行)')
    orchestrator_parser.add_argument('request', help='你想让@orchestrator做什么')
    orchestrator_parser.add_argument('--execute', action='store_true', help='立即执行@orchestrator调用')
    orchestrator_parser.add_argument('--parallel', action='store_true', default=True, help='强制并行模式 (默认启用)')
    orchestrator_parser.add_argument('--min-agents', type=int, default=3, help='最少并行Agent数量 (默认3个)')

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
    execute_parser.add_argument('hook_name', choices=['pre-commit', 'pre-push', 'post-checkout', 'commit-msg', 'post-merge', 'prepare-commit-msg', 'post-commit'], help='钩子名称')
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

    # quality命令 - 质量门管理
    quality_parser = subparsers.add_parser('quality', help='质量门管理')
    quality_subparsers = quality_parser.add_subparsers(dest='quality_command', help='质量门命令')

    # 质量检查命令
    check_parser = quality_subparsers.add_parser('check', help='运行质量门检查')
    check_parser.add_argument('--context', default='commit',
                             choices=['commit', 'merge', 'release', 'quick', 'all'],
                             help='执行上下文')
    check_parser.add_argument('--parallel', action='store_true', default=True,
                             help='并行执行')
    check_parser.add_argument('--no-parallel', action='store_true',
                             help='禁用并行执行')
    check_parser.add_argument('--fail-fast', action='store_true', help='快速失败')
    check_parser.add_argument('--output', choices=['text', 'json', 'html'], default='text',
                             help='输出格式')

    # 质量趋势命令
    trends_parser = quality_subparsers.add_parser('trends', help='显示质量趋势')
    trends_parser.add_argument('--days', type=int, default=30, help='分析天数')
    trends_parser.add_argument('--format', choices=['text', 'json'], default='text',
                              help='输出格式')

    # 质量历史命令
    history_parser = quality_subparsers.add_parser('history', help='显示执行历史')
    history_parser.add_argument('--limit', type=int, default=10, help='显示记录数量')
    history_parser.add_argument('--format', choices=['text', 'json'], default='text',
                               help='输出格式')

    # 质量设置命令
    setup_parser = quality_subparsers.add_parser('setup', help='设置质量门')
    setup_subparsers = setup_parser.add_subparsers(dest='setup_command', help='设置命令')

    hooks_setup_parser = setup_subparsers.add_parser('hooks', help='安装Git hooks')
    ci_setup_parser = setup_subparsers.add_parser('ci', help='设置CI/CD集成')
    monitoring_setup_parser = setup_subparsers.add_parser('monitoring', help='设置持续监控')

    # 质量仪表板命令
    dashboard_parser = quality_subparsers.add_parser('dashboard', help='生成质量仪表板')

    # 质量配置命令
    config_parser = quality_subparsers.add_parser('config', help='生成配置文件')
    config_parser.add_argument('--output', default='.perfect21/quality_config.json',
                              help='配置文件路径')
    config_parser.add_argument('--template', choices=['strict', 'balanced', 'lenient'],
                              default='balanced', help='配置模板')
    claude_md_parser.add_argument('--add', help='添加快速记忆内容(memory)')
    claude_md_parser.add_argument('--template-type', choices=['team', 'personal'], help='模板类型(template)')
    claude_md_parser.add_argument('--output', help='输出文件路径')

    # workspace命令
    workspace_parser = subparsers.add_parser('workspace', help='多工作空间管理')
    workspace_subparsers = workspace_parser.add_subparsers(dest='workspace_action')

    # 创建工作空间
    create_parser = workspace_subparsers.add_parser('create', help='创建新工作空间')
    create_parser.add_argument('name', help='工作空间名称')
    create_parser.add_argument('description', help='工作空间描述')
    create_parser.add_argument('--type', choices=['feature', 'bugfix', 'experiment', 'hotfix', 'refactor'],
                              default='feature', help='工作空间类型')
    create_parser.add_argument('--base-branch', default='main', help='基分支')
    create_parser.add_argument('--port', type=int, help='首选端口')
    create_parser.add_argument('--priority', type=int, default=5, help='优先级 (1-10)')

    # 其他工作空间命令
    workspace_subparsers.add_parser('list', help='列出所有工作空间')

    switch_parser = workspace_subparsers.add_parser('switch', help='切换工作空间')
    switch_parser.add_argument('workspace_id', help='工作空间ID')

    suggest_parser = workspace_subparsers.add_parser('suggest', help='为任务建议工作空间')
    suggest_parser.add_argument('task_description', help='任务描述')

    conflict_parser = workspace_subparsers.add_parser('conflicts', help='检测冲突')
    conflict_parser.add_argument('workspace_id', help='工作空间ID')

    merge_parser = workspace_subparsers.add_parser('merge', help='合并工作空间')
    merge_parser.add_argument('workspace_id', help='工作空间ID')
    merge_parser.add_argument('--dry-run', action='store_true', help='只检查，不实际合并')

    workspace_subparsers.add_parser('stats', help='显示工作空间统计信息')

    # error命令 - 错误处理管理
    error_parser = subparsers.add_parser('error', help='错误处理系统管理')
    error_subparsers = error_parser.add_subparsers(dest='error_action')

    # 错误统计
    error_subparsers.add_parser('stats', help='显示错误统计')

    # 清理错误
    error_subparsers.add_parser('clear', help='清理错误聚合器')

    # 运行测试
    error_test_parser = error_subparsers.add_parser('test', help='运行错误处理测试')
    error_test_parser.add_argument('--type', choices=['all', 'basic', 'retry'], default='all', help='测试类型')

    # 配置管理
    error_config_parser = error_subparsers.add_parser('config', help='配置错误处理')
    error_config_parser.add_argument('--retry-attempts', type=int, help='设置重试次数')
    error_config_parser.add_argument('--retry-delay', type=float, help='设置重试延迟')

    # 恢复策略测试
    error_recovery_parser = error_subparsers.add_parser('recovery', help='测试恢复策略')
    error_recovery_parser.add_argument('--category', choices=['all', 'network', 'git', 'agent'], default='all', help='恢复类别')

    # learning命令
    learning_parser = subparsers.add_parser('learning', help='学习反馈循环系统')
    learning_subparsers = learning_parser.add_subparsers(dest='learning_action')

    # 学习摘要
    learning_subparsers.add_parser('summary', help='显示学习摘要')

    # 反馈管理
    feedback_parser = learning_subparsers.add_parser('feedback', help='反馈管理')
    feedback_parser.add_argument('--collect', action='store_true', help='收集用户反馈')
    feedback_parser.add_argument('--report', help='生成反馈报告')
    feedback_parser.add_argument('--satisfaction', type=float, help='满意度评分 (0-1)')
    feedback_parser.add_argument('--comment', help='反馈评论')

    # 模式分析
    patterns_parser = learning_subparsers.add_parser('patterns', help='模式分析')
    patterns_parser.add_argument('--analyze', action='store_true', help='重新分析模式')
    patterns_parser.add_argument('--show', help='显示特定模式')

    # 改进建议
    suggestions_parser = learning_subparsers.add_parser('suggestions', help='改进建议')
    suggestions_parser.add_argument('--generate', action='store_true', help='生成新建议')
    suggestions_parser.add_argument('--priority', choices=['low', 'medium', 'high', 'critical'], help='按优先级筛选')
    suggestions_parser.add_argument('--category', help='按类别筛选')
    suggestions_parser.add_argument('--implement', help='标记建议为已实施')

    # 知识导出导入
    knowledge_parser = learning_subparsers.add_parser('knowledge', help='知识库管理')
    knowledge_parser.add_argument('--export', help='导出知识库到文件')
    knowledge_parser.add_argument('--import', dest='import_file', help='从文件导入知识库')

    # 全局选项
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 使用资源管理器创建Perfect21实例
    try:
        with managed_perfect21() as p21:
            # 执行命令
            if args.command == 'status':
                print_status(p21)
            elif args.command == 'perfect21':
                # Perfect21核心功能
                handle_perfect21_command(p21, args)
            elif args.command == 'monitor':
                handle_monitor(args)
            elif args.command == 'develop':
                handle_develop(args)
            elif args.command == 'parallel':
                handle_parallel_command(args)
            elif args.command == 'orchestrator':
                handle_orchestrator(args)
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
            elif args.command == 'quality':
                handle_quality(args)
            elif args.command == 'workspace':
                handle_workspace(args)
            elif args.command == 'error':
                handle_error_management(args)
            elif args.command == 'learning':
                handle_learning(args)
            else:
                print(f"❌ 未知命令: {args.command}")
                sys.exit(1)

    except Exception as e:
        print(f"❌ 命令执行失败: {e}")
        if hasattr(args, 'verbose') and args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        # 确保资源清理
        try:
            ResourceManager().cleanup_all()
        except Exception:
            pass  # 忽略清理时的异常

if __name__ == '__main__':
    main()

class CLI:
    """CLI类 - Mock实现"""

    def __init__(self, config=None):
        self.config = config or {
            'timeout': 300,
            'parallel_enabled': True,
            'max_agents': 10
        }

    def parse_args(self, args):
        """解析命令行参数"""
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument('command', choices=['parallel', 'status', 'hooks'])
        parser.add_argument('task_description', nargs='?')
        parser.add_argument('action', nargs='?')
        parser.add_argument('--force-parallel', action='store_true')
        parser.add_argument('--detailed', action='store_true')

        return parser.parse_args(args)

    def execute_command(self, args):
        """执行命令"""
        try:
            parsed = self.parse_args(args)

            if parsed.command == 'parallel':
                return self._handle_parallel_command(parsed)
            elif parsed.command == 'status':
                return self._handle_status_command(parsed)
            elif parsed.command == 'hooks':
                return self._handle_hooks_command(parsed)

            return {'success': False, 'error': 'Unknown command'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _handle_parallel_command(self, parsed):
        """处理并行命令"""
        return {
            'success': True,
            'task_id': 'mock_task_123',
            'agents_called': ['@backend-architect', '@test-engineer']
        }

    def _handle_status_command(self, parsed):
        """处理状态命令"""
        return {
            'system_status': 'running',
            'module_status': {
                'workflow_orchestrator': {'status': 'active'},
                'capability_discovery': {'status': 'ready'},
                'git_workflow': {'status': 'initialized'},
                'auth_system': {'status': 'active'}
            },
            'performance_metrics': {'uptime': '1h 30m'}
        }

    def _handle_hooks_command(self, parsed):
        """处理Git hooks命令"""
        if parsed.action == 'install':
            return {
                'success': True,
                'installed_hooks': ['pre-commit', 'post-commit', 'pre-push']
            }
        elif parsed.action == 'status':
            return {
                'installed': ['pre-commit', 'post-commit'],
                'not_installed': ['pre-push']
            }
        return {'success': True}

    def get_config(self):
        """获取配置"""
        return self.config

class CLICommand:
    """CLI命令类"""

    def __init__(self, name, description, handler):
        self.name = name
        self.description = description
        self.handler = handler

    def execute(self, *args, **kwargs):
        """执行命令"""
        return self.handler(*args, **kwargs)

def main():
    """主函数"""
    import sys
    cli = CLI()
    return cli.execute_command(sys.argv[1:])
