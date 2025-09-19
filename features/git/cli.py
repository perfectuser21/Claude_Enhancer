#!/usr/bin/env python3
"""
Perfect21 Git CLI - 统一的Git工作流命令行接口
个人编程助手的Git自动化工具
"""

import asyncio
import argparse
import json
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from features.git.git_hooks import GitHooksManager, HookType
from features.git.git_integration import GitWorkflowManager, WorkflowType
from features.git.workflow_manager import AdvancedGitWorkflowManager, TaskPriority, WorkflowStage


class GitCLI:
    """
Perfect21 Git CLI - 主命令行接口
    """
    
    def __init__(self):
        self.project_root = os.getcwd()
        self.advanced_manager = AdvancedGitWorkflowManager(self.project_root)
        self.git_workflow = GitWorkflowManager(self.project_root)
        self.hooks_manager = GitHooksManager(self.project_root)
    
    def create_parser(self) -> argparse.ArgumentParser:
        """创建命令行解析器"""
        parser = argparse.ArgumentParser(
            prog='perfect21-git',
            description='🤖 Perfect21 Git智能工作流管理器',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""  
使用示例:
  perfect21-git task create "实现用户登录功能" --priority high
  perfect21-git session start task_20250101_120000
  perfect21-git commit --smart
  perfect21-git dashboard
  perfect21-git hooks install --all
  perfect21-git cleanup --branches

更多信息请访问: https://github.com/perfect21/git-workflow
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='可用命令')
        
        # 任务管理
        self._add_task_commands(subparsers)
        
        # 编程会话
        self._add_session_commands(subparsers)
        
        # Git操作
        self._add_git_commands(subparsers)
        
        # Hooks管理
        self._add_hooks_commands(subparsers)
        
        # 分析和仪表板
        self._add_analytics_commands(subparsers)
        
        # 工具命令
        self._add_utility_commands(subparsers)
        
        return parser
    
    def _add_task_commands(self, subparsers):
        """添加任务管理命令"""
        task_parser = subparsers.add_parser('task', help='任务管理')
        task_subparsers = task_parser.add_subparsers(dest='task_action', help='任务操作')
        
        # 创建任务
        create_parser = task_subparsers.add_parser('create', help='创建新任务')
        create_parser.add_argument('title', help='任务标题')
        create_parser.add_argument('description', nargs='?', default='', help='任务描述')
        create_parser.add_argument('--priority', choices=['urgent', 'high', 'medium', 'low'], 
                                 default='medium', help='任务优先级')
        create_parser.add_argument('--type', choices=['feature', 'bugfix', 'hotfix', 'maintenance'], 
                                 default='feature', help='任务类型')
        create_parser.add_argument('--hours', type=float, help='估计工时')
        create_parser.add_argument('--tags', nargs='*', help='任务标签')
        
        # 更新任务
        update_parser = task_subparsers.add_parser('update', help='更新任务进度')
        update_parser.add_argument('task_id', help='任务ID')
        update_parser.add_argument('--progress', type=float, help='进度百分比 (0-100)')
        update_parser.add_argument('--stage', choices=['planning', 'development', 'testing', 'review', 'deployment', 'completed'], 
                                 help='任务阶段')
        update_parser.add_argument('--notes', help='更新说明')
        
        # 列出任务
        task_subparsers.add_parser('list', help='列出所有任务')
        
        # 任务详情
        show_parser = task_subparsers.add_parser('show', help='显示任务详情')
        show_parser.add_argument('task_id', help='任务ID')
    
    def _add_session_commands(self, subparsers):
        """添加编程会话命令"""
        session_parser = subparsers.add_parser('session', help='编程会话管理')
        session_subparsers = session_parser.add_subparsers(dest='session_action', help='会话操作')
        
        # 开始会话
        start_parser = session_subparsers.add_parser('start', help='开始编程会话')
        start_parser.add_argument('task_id', help='任务ID')
        
        # 结束会话
        end_parser = session_subparsers.add_parser('end', help='结束编程会话')
        end_parser.add_argument('--notes', help='会话备注')
        
        # 会话状态
        session_subparsers.add_parser('status', help='查看当前会话状态')
    
    def _add_git_commands(self, subparsers):
        """添加Git操作命令"""
        # 智能提交
        commit_parser = subparsers.add_parser('commit', help='智能提交')
        commit_parser.add_argument('--message', '-m', help='自定义提交信息')
        commit_parser.add_argument('--smart', action='store_true', help='使用智能生成的提交信息')
        commit_parser.add_argument('--files', nargs='*', help='指定要提交的文件')
        commit_parser.add_argument('--push', action='store_true', help='提交后自动推送')
        
        # Pull Request
        pr_parser = subparsers.add_parser('pr', help='创建Pull Request')
        pr_parser.add_argument('--target', default='main', help='目标分支')
        pr_parser.add_argument('--title', help='自定义PR标题')
        pr_parser.add_argument('--description', help='自定义PR描述')
        pr_parser.add_argument('--task', help='关联的任务ID')
        
        # 合并分支
        merge_parser = subparsers.add_parser('merge', help='合并分支')
        merge_parser.add_argument('source', help='源分支')
        merge_parser.add_argument('target', help='目标分支')
        merge_parser.add_argument('--strategy', choices=['fast-forward', 'no-ff', 'squash', 'rebase'], 
                                default='no-ff', help='合并策略')
        
        # 分支管理
        branch_parser = subparsers.add_parser('branch', help='分支管理')
        branch_subparsers = branch_parser.add_subparsers(dest='branch_action', help='分支操作')
        
        branch_subparsers.add_parser('list', help='列出所有分支')
        
        cleanup_parser = branch_subparsers.add_parser('cleanup', help='清理已合并分支')
        cleanup_parser.add_argument('--dry-run', action='store_true', help='只显示会删除的分支，不实际删除')
        cleanup_parser.add_argument('--auto', action='store_true', help='自动清理安全的分支')
    
    def _add_hooks_commands(self, subparsers):
        """添加Hooks管理命令"""
        hooks_parser = subparsers.add_parser('hooks', help='Git Hooks管理')
        hooks_subparsers = hooks_parser.add_subparsers(dest='hooks_action', help='Hooks操作')
        
        # 安装hooks
        install_parser = hooks_subparsers.add_parser('install', help='安装Git Hooks')
        install_parser.add_argument('--all', action='store_true', help='安装所有hooks')
        install_parser.add_argument('--types', nargs='*', 
                                  choices=['pre-commit', 'commit-msg', 'pre-push', 'post-checkout'],
                                  help='指定hook类型')
        
        # 卸载hooks
        uninstall_parser = hooks_subparsers.add_parser('uninstall', help='卸载Git Hooks')
        uninstall_parser.add_argument('--all', action='store_true', help='卸载所有hooks')
        uninstall_parser.add_argument('--types', nargs='*',
                                    choices=['pre-commit', 'commit-msg', 'pre-push', 'post-checkout'],
                                    help='指定hook类型')
        
        # hooks状态
        hooks_subparsers.add_parser('status', help='显示hooks状态')
        
        # 测试hooks
        test_parser = hooks_subparsers.add_parser('test', help='测试hooks')
        test_parser.add_argument('hook_type', nargs='?', default='pre-commit',
                               choices=['pre-commit', 'commit-msg', 'pre-push', 'post-checkout'],
                               help='Hook类型')
    
    def _add_analytics_commands(self, subparsers):
        """添加分析和仪表板命令"""
        # 仪表板
        dashboard_parser = subparsers.add_parser('dashboard', help='显示个人仪表板')
        dashboard_parser.add_argument('--json', action='store_true', help='输出JSON格式')
        
        # 生产力分析
        productivity_parser = subparsers.add_parser('productivity', help='生产力分析')
        productivity_parser.add_argument('--days', type=int, default=7, help='分析天数')
        
        # 项目健康度
        health_parser = subparsers.add_parser('health', help='项目健康度检查')
        health_parser.add_argument('--full', action='store_true', help='显示详细信息')
        
        # 报告
        report_parser = subparsers.add_parser('report', help='生成报告')
        report_parser.add_argument('--type', choices=['performance', 'productivity', 'health'], 
                                 default='performance', help='报告类型')
        report_parser.add_argument('--output', help='输出文件名')
    
    def _add_utility_commands(self, subparsers):
        """添加工具命令"""
        # 清理
        cleanup_parser = subparsers.add_parser('cleanup', help='清理和优化')
        cleanup_parser.add_argument('--branches', action='store_true', help='清理已合并分支')
        cleanup_parser.add_argument('--cache', action='store_true', help='清理缓存')
        cleanup_parser.add_argument('--all', action='store_true', help='全面清理')
        cleanup_parser.add_argument('--dry-run', action='store_true', help='模拟运行')
        
        # 配置
        config_parser = subparsers.add_parser('config', help='配置管理')
        config_subparsers = config_parser.add_subparsers(dest='config_action', help='配置操作')
        
        config_subparsers.add_parser('show', help='显示当前配置')
        
        set_parser = config_subparsers.add_parser('set', help='设置配置项')
        set_parser.add_argument('key', help='配置键')
        set_parser.add_argument('value', help='配置值')
        
        # 初始化
        init_parser = subparsers.add_parser('init', help='初始化Perfect21 Git工作流')
        init_parser.add_argument('--force', action='store_true', help='强制初始化')
    
    async def run(self, args):
        """运行命令"""
        try:
            if args.command == 'task':
                return await self._handle_task_command(args)
            elif args.command == 'session':
                return await self._handle_session_command(args)
            elif args.command == 'commit':
                return await self._handle_commit_command(args)
            elif args.command == 'pr':
                return await self._handle_pr_command(args)
            elif args.command == 'merge':
                return await self._handle_merge_command(args)
            elif args.command == 'branch':
                return await self._handle_branch_command(args)
            elif args.command == 'hooks':
                return await self._handle_hooks_command(args)
            elif args.command == 'dashboard':
                return await self._handle_dashboard_command(args)
            elif args.command == 'productivity':
                return await self._handle_productivity_command(args)
            elif args.command == 'health':
                return await self._handle_health_command(args)
            elif args.command == 'report':
                return await self._handle_report_command(args)
            elif args.command == 'cleanup':
                return await self._handle_cleanup_command(args)
            elif args.command == 'config':
                return await self._handle_config_command(args)
            elif args.command == 'init':
                return await self._handle_init_command(args)
            else:
                return {'success': False, 'error': f'未知命令: {args.command}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # 命令处理方法
    async def _handle_task_command(self, args) -> Dict[str, Any]:
        """处理任务命令"""
        if args.task_action == 'create':
            # 转换枚举类型
            priority_map = {
                'urgent': TaskPriority.URGENT,
                'high': TaskPriority.HIGH, 
                'medium': TaskPriority.MEDIUM,
                'low': TaskPriority.LOW
            }
            
            type_map = {
                'feature': WorkflowType.FEATURE_DEVELOPMENT,
                'bugfix': WorkflowType.BUG_FIX,
                'hotfix': WorkflowType.HOTFIX,
                'maintenance': WorkflowType.MAINTENANCE
            }
            
            return await self.advanced_manager.create_task(
                title=args.title,
                description=args.description,
                priority=priority_map[args.priority],
                workflow_type=type_map[args.type],
                estimated_hours=args.hours,
                tags=args.tags
            )
        
        elif args.task_action == 'update':
            stage_map = {
                'planning': WorkflowStage.PLANNING,
                'development': WorkflowStage.DEVELOPMENT,
                'testing': WorkflowStage.TESTING,
                'review': WorkflowStage.REVIEW,
                'deployment': WorkflowStage.DEPLOYMENT,
                'completed': WorkflowStage.COMPLETED
            }
            
            return await self.advanced_manager.update_task_progress(
                task_id=args.task_id,
                progress=args.progress,
                stage=stage_map.get(args.stage) if args.stage else None,
                notes=args.notes or ""
            )
        
        elif args.task_action == 'list':
            return {
                'success': True,
                'tasks': {task_id: task.__dict__ for task_id, task in self.advanced_manager.tasks.items()}
            }
        
        elif args.task_action == 'show':
            if args.task_id in self.advanced_manager.tasks:
                return {
                    'success': True,
                    'task': self.advanced_manager.tasks[args.task_id].__dict__
                }
            else:
                return {
                    'success': False,
                    'error': f'任务 {args.task_id} 不存在'
                }
        
        return {'success': False, 'error': f'未知任务操作: {args.task_action}'}
    
    async def _handle_session_command(self, args) -> Dict[str, Any]:
        """处理会话命令"""
        if args.session_action == 'start':
            return await self.advanced_manager.start_coding_session(args.task_id)
        elif args.session_action == 'end':
            return await self.advanced_manager.end_coding_session(args.notes or "")
        elif args.session_action == 'status':
            session_file = Path(self.project_root) / ".perfect21" / "workflow" / "current_session.json"
            if session_file.exists():
                with open(session_file) as f:
                    session_data = json.load(f)
                return {
                    'success': True,
                    'active_session': True,
                    'session': session_data
                }
            else:
                return {
                    'success': True,
                    'active_session': False,
                    'message': '没有活跃的编程会话'
                }
        
        return {'success': False, 'error': f'未知会话操作: {args.session_action}'}
    
    async def _handle_commit_command(self, args) -> Dict[str, Any]:
        """处理提交命令"""
        message = args.message if not args.smart else None
        result = await self.git_workflow.commit_with_smart_message(
            files=args.files,
            custom_message=message
        )
        
        if result['success'] and args.push:
            # 推送到远程
            current_branch = await self.git_workflow._get_current_branch()
            push_result = await self.git_workflow._run_git_command(['git', 'push', 'origin', current_branch])
            result['push_result'] = {
                'success': push_result.returncode == 0,
                'output': push_result.stdout.decode() if push_result.returncode == 0 else push_result.stderr.decode()
            }
        
        return result
    
    async def _handle_pr_command(self, args) -> Dict[str, Any]:
        """处理PR命令"""
        if args.task:
            return await self.advanced_manager.create_pull_request_for_task(
                task_id=args.task,
                target_branch=args.target
            )
        else:
            return await self.git_workflow.create_pull_request(
                target_branch=args.target,
                title=args.title,
                description=args.description
            )
    
    async def _handle_merge_command(self, args) -> Dict[str, Any]:
        """处理合并命令"""
        from features.git.git_integration import MergeStrategy
        
        strategy_map = {
            'fast-forward': MergeStrategy.FAST_FORWARD,
            'no-ff': MergeStrategy.NO_FF,
            'squash': MergeStrategy.SQUASH,
            'rebase': MergeStrategy.REBASE
        }
        
        return await self.git_workflow.merge_branch(
            source_branch=args.source,
            target_branch=args.target,
            strategy=strategy_map[args.strategy]
        )
    
    async def _handle_branch_command(self, args) -> Dict[str, Any]:
        """处理分支命令"""
        if args.branch_action == 'list':
            # 简单的分支列表
            result = await self.git_workflow._run_git_command(['git', 'branch', '-a'])
            return {
                'success': result.returncode == 0,
                'branches': result.stdout.decode().split('\n') if result.returncode == 0 else [],
                'error': result.stderr.decode() if result.returncode != 0 else None
            }
        
        elif args.branch_action == 'cleanup':
            if args.auto:
                return await self.advanced_manager.branch_manager.auto_cleanup_branches(dry_run=args.dry_run)
            else:
                return await self.advanced_manager.branch_manager.suggest_branch_cleanup()
        
        return {'success': False, 'error': f'未知分支操作: {args.branch_action}'}
    
    async def _handle_hooks_command(self, args) -> Dict[str, Any]:
        """处理Hooks命令"""
        if args.hooks_action == 'install':
            if args.all:
                hook_types = list(HookType)
            elif args.types:
                hook_types = [HookType(t) for t in args.types]
            else:
                hook_types = [HookType.PRE_COMMIT, HookType.PRE_PUSH]
            
            return await self.hooks_manager.install_hooks(hook_types)
        
        elif args.hooks_action == 'uninstall':
            if args.all:
                hook_types = list(HookType)
            elif args.types:
                hook_types = [HookType(t) for t in args.types]
            else:
                hook_types = [HookType.PRE_COMMIT, HookType.PRE_PUSH]
            
            return await self.hooks_manager.uninstall_hooks(hook_types)
        
        elif args.hooks_action == 'status':
            return await self.hooks_manager.get_hook_status()
        
        elif args.hooks_action == 'test':
            hook_type = HookType(args.hook_type)
            return await self.hooks_manager.test_hook(hook_type)
        
        return {'success': False, 'error': f'未知hooks操作: {args.hooks_action}'}
    
    async def _handle_dashboard_command(self, args) -> Dict[str, Any]:
        """处理仪表板命令"""
        dashboard_data = await self.advanced_manager.get_dashboard_data()
        
        if args.json:
            return dashboard_data
        else:
            # 格式化输出仪表板
            return {
                'success': True,
                'formatted_output': self._format_dashboard(dashboard_data)
            }
    
    async def _handle_productivity_command(self, args) -> Dict[str, Any]:
        """处理生产力命令"""
        return await self.advanced_manager.productivity_analyzer.get_productivity_insights(args.days)
    
    async def _handle_health_command(self, args) -> Dict[str, Any]:
        """处理健康检查命令"""
        health_data = await self.git_workflow.get_project_health()
        
        if args.full:
            return health_data
        else:
            # 返回简化版本
            return {
                'success': True,
                'health_score': health_data.get('health_score', 0),
                'recommendations': health_data.get('recommendations', []),
                'timestamp': health_data.get('timestamp')
            }
    
    async def _handle_report_command(self, args) -> Dict[str, Any]:
        """处理报告命令"""
        if args.type == 'performance':
            filename = await self.hooks_manager.save_performance_report(args.output)
            return {
                'success': True,
                'report_file': filename,
                'message': f'性能报告已保存到: {filename}'
            }
        elif args.type == 'productivity':
            insights = await self.advanced_manager.productivity_analyzer.get_productivity_insights(30)
            if args.output:
                async with aiofiles.open(args.output, 'w') as f:
                    await f.write(json.dumps(insights, indent=2, default=str))
                return {
                    'success': True,
                    'report_file': args.output,
                    'message': f'生产力报告已保存到: {args.output}'
                }
            else:
                return insights
        else:
            return {'success': False, 'error': f'未知报告类型: {args.type}'}
    
    async def _handle_cleanup_command(self, args) -> Dict[str, Any]:
        """处理清理命令"""
        results = []
        
        if args.branches or args.all:
            branch_result = await self.git_workflow.cleanup_branches(dry_run=args.dry_run)
            results.append({
                'type': 'branches',
                'result': branch_result
            })
        
        if args.cache or args.all:
            # 清理缓存（这里可以添加实际缓存清理逻辑）
            results.append({
                'type': 'cache',
                'result': {
                    'success': True,
                    'message': '缓存清理功能暂未实现'
                }
            })
        
        return {
            'success': True,
            'cleanup_results': results,
            'dry_run': args.dry_run
        }
    
    async def _handle_config_command(self, args) -> Dict[str, Any]:
        """处理配置命令"""
        config_file = Path(self.project_root) / ".perfect21" / "config.json"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        if args.config_action == 'show':
            if config_file.exists():
                async with aiofiles.open(config_file, 'r') as f:
                    config = json.loads(await f.read())
                return {
                    'success': True,
                    'config': config
                }
            else:
                return {
                    'success': True,
                    'config': {},
                    'message': '配置文件不存在'
                }
        
        elif args.config_action == 'set':
            # 加载现有配置
            config = {}
            if config_file.exists():
                async with aiofiles.open(config_file, 'r') as f:
                    config = json.loads(await f.read())
            
            # 更新配置
            config[args.key] = args.value
            
            # 保存配置
            async with aiofiles.open(config_file, 'w') as f:
                await f.write(json.dumps(config, indent=2))
            
            return {
                'success': True,
                'message': f'配置 {args.key} 已设置为 {args.value}'
            }
        
        return {'success': False, 'error': f'未知配置操作: {args.config_action}'}
    
    async def _handle_init_command(self, args) -> Dict[str, Any]:
        """处理初始化命令"""
        # 创建目录结构
        perfect21_dir = Path(self.project_root) / ".perfect21"
        subdirs = ['workflow', 'productivity', 'git', 'reports']
        
        for subdir in subdirs:
            (perfect21_dir / subdir).mkdir(parents=True, exist_ok=True)
        
        # 安装基本的hooks
        hook_result = await self.hooks_manager.install_hooks([HookType.PRE_COMMIT, HookType.PRE_PUSH])
        
        # 创建默认配置
        default_config = {
            'version': '1.0.0',
            'initialized_at': datetime.now().isoformat(),
            'features': {
                'smart_commits': True,
                'productivity_tracking': True,
                'auto_branch_cleanup': True,
                'hooks_enabled': True
            },
            'preferences': {
                'default_branch': 'main',
                'merge_strategy': 'no-ff',
                'auto_push': False
            }
        }
        
        config_file = perfect21_dir / "config.json"
        if not config_file.exists() or args.force:
            async with aiofiles.open(config_file, 'w') as f:
                await f.write(json.dumps(default_config, indent=2))
        
        return {
            'success': True,
            'message': 'Perfect21 Git工作流初始化完成',
            'directories_created': subdirs,
            'hooks_installed': hook_result,
            'config_file': str(config_file)
        }
    
    def _format_dashboard(self, data: Dict[str, Any]) -> str:
        """格式化仪表板输出"""
        lines = []
        lines.append("📊 Perfect21 个人开发仪表板")
        lines.append("=" * 50)
        
        # 任务指标
        task_metrics = data.get('task_metrics', {})
        if hasattr(task_metrics, 'total_tasks'):
            lines.append(f"📝 任务指标:")
            lines.append(f"  总任务: {task_metrics.total_tasks}")
            lines.append(f"  已完成: {task_metrics.completed_tasks}")
            lines.append(f"  活跃任务: {task_metrics.active_tasks}")
            lines.append(f"  生产力分数: {task_metrics.productivity_score:.1f}")
            lines.append("")
        
        # 生产力洞察
        productivity = data.get('productivity_insights', {})
        if 'total_sessions' in productivity:
            lines.append(f"⚡ 生产力洞察:")
            lines.append(f"  编程会话: {productivity['total_sessions']}")
            lines.append(f"  总时长: {productivity.get('total_hours', 0)}h")
            lines.append(f"  平均分数: {productivity.get('average_productivity_score', 0):.1f}")
            lines.append("")
        
        # 项目健康度
        health = data.get('project_health', {})
        if 'health_score' in health:
            lines.append(f"🏅 项目健康度: {health['health_score']:.1f}/100")
            lines.append("")
        
        # 建议
        recommendations = data.get('recommendations', [])
        if recommendations:
            lines.append("💡 个性化建议:")
            for i, rec in enumerate(recommendations[:5], 1):
                lines.append(f"  {i}. {rec}")
            lines.append("")
        
        # 快速操作
        quick_actions = data.get('quick_actions', [])
        if quick_actions:
            lines.append("⚡ 快速操作:")
            for action in quick_actions[:5]:
                lines.append(f"  {action.get('icon', '•')} {action.get('label', action['name'])}")
        
        return "\n".join(lines)


def main():
    """主函数"""
    cli = GitCLI()
    parser = cli.create_parser()
    
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    args = parser.parse_args()
    
    # 运行异步命令
    try:
        result = asyncio.run(cli.run(args))
        
        if result['success']:
            if 'formatted_output' in result:
                print(result['formatted_output'])
            elif 'message' in result:
                print(f"✅ {result['message']}")
            else:
                print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
        else:
            print(f"❌ 错误: {result.get('error', '未知错误')}")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n操作已取消")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 意外错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()