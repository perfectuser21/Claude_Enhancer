#!/usr/bin/env python3
"""
Perfect21 Git Hook CLI Integration
提供便捷的命令行接口来管理和使用Git Hook集成功能
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent.parent))

from features.git.workflow_hooks_integration import WorkflowHooksIntegration, HookCheckpoint
from features.git.enhanced_hooks import EnhancedHooksManager
from features.git.artifact_management import ArtifactManager, ArtifactType, ArtifactStatus
from modules.logger import setup_logger

logger = setup_logger("Perfect21.GitHooksCLI")


class GitHooksCLI:
    """Git Hooks CLI管理器"""

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root or os.getcwd())
        self.workflow_integration = WorkflowHooksIntegration(str(self.project_root))
        self.enhanced_hooks = EnhancedHooksManager(str(self.project_root))
        self.artifact_manager = ArtifactManager(str(self.project_root))

    async def install_hooks(self, hook_types: Optional[List[str]] = None,
                           force: bool = False) -> Dict[str, Any]:
        """安装Git hooks"""
        print("🔧 安装Perfect21 Git Hooks...")

        if hook_types is None:
            hook_types = ['pre-commit', 'commit-msg', 'pre-push', 'post-checkout', 'post-merge']

        git_hooks_dir = self.project_root / ".git" / "hooks"
        if not git_hooks_dir.exists():
            return {
                'success': False,
                'error': '当前目录不是Git仓库或.git/hooks目录不存在'
            }

        installed = []
        failed = []

        for hook_name in hook_types:
            try:
                hook_file = git_hooks_dir / hook_name

                # 检查是否已存在
                if hook_file.exists() and not force:
                    print(f"⚠️ {hook_name} 已存在，使用 --force 覆盖")
                    continue

                # 生成hook脚本
                hook_content = self._generate_hook_script(hook_name)

                # 写入文件
                with open(hook_file, 'w') as f:
                    f.write(hook_content)

                # 设置执行权限
                os.chmod(hook_file, 0o755)

                installed.append(hook_name)
                print(f"✅ {hook_name} 安装成功")

            except Exception as e:
                failed.append({
                    'hook': hook_name,
                    'error': str(e)
                })
                print(f"❌ {hook_name} 安装失败: {e}")

        result = {
            'success': len(failed) == 0,
            'installed': installed,
            'failed': failed,
            'message': f'安装完成: {len(installed)}个成功, {len(failed)}个失败'
        }

        print(f"\n📊 安装结果: {result['message']}")
        return result

    def _generate_hook_script(self, hook_name: str) -> str:
        """生成hook脚本"""
        return f'''#!/usr/bin/env python3
"""
Perfect21 Git Hook - {hook_name}
自动生成的增强Hook脚本
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from features.git.enhanced_hooks import execute_enhanced_hook

    async def main():
        # 准备上下文
        context = {{}}

        # 根据hook类型设置不同的上下文
        if "{hook_name}" == "commit-msg" and len(sys.argv) > 1:
            context["commit_msg_file"] = sys.argv[1]
        elif "{hook_name}" == "pre-push" and len(sys.argv) > 2:
            context["remote"] = sys.argv[1]
            context["url"] = sys.argv[2]
        elif "{hook_name}" == "post-checkout" and len(sys.argv) > 3:
            context["old_ref"] = sys.argv[1]
            context["new_ref"] = sys.argv[2]
            context["branch_flag"] = sys.argv[3]

        # 执行增强Hook
        result = await execute_enhanced_hook("{hook_name}", context, str(project_root))

        # 处理结果
        if result.get("success", True):
            if result.get("details", {}).get("skipped", False):
                print(f"⚠️ {{result.get('message', 'Hook skipped')}}")
            else:
                print(f"✅ {{result.get('message', 'Hook completed successfully')}}")
            sys.exit(0)
        else:
            print(f"❌ {{result.get('message', 'Hook failed')}}")
            if result.get("should_abort", False):
                sys.exit(1)
            else:
                sys.exit(0)

    if __name__ == "__main__":
        asyncio.run(main())

except ImportError as e:
    print(f"Warning: Perfect21 not available, skipping {hook_name} hook: {{e}}")
    sys.exit(0)
except Exception as e:
    print(f"Error in {hook_name} hook: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
'''

    async def uninstall_hooks(self, hook_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """卸载Git hooks"""
        print("🧹 卸载Perfect21 Git Hooks...")

        if hook_types is None:
            hook_types = ['pre-commit', 'commit-msg', 'pre-push', 'post-checkout', 'post-merge']

        git_hooks_dir = self.project_root / ".git" / "hooks"
        if not git_hooks_dir.exists():
            return {
                'success': False,
                'error': '当前目录不是Git仓库'
            }

        uninstalled = []
        not_found = []

        for hook_name in hook_types:
            hook_file = git_hooks_dir / hook_name

            if hook_file.exists():
                try:
                    hook_file.unlink()
                    uninstalled.append(hook_name)
                    print(f"✅ {hook_name} 卸载成功")
                except Exception as e:
                    print(f"❌ {hook_name} 卸载失败: {e}")
            else:
                not_found.append(hook_name)
                print(f"⚠️ {hook_name} 不存在")

        result = {
            'success': True,
            'uninstalled': uninstalled,
            'not_found': not_found,
            'message': f'卸载完成: {len(uninstalled)}个成功'
        }

        print(f"\n📊 卸载结果: {result['message']}")
        return result

    async def test_hook(self, hook_name: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """测试单个hook"""
        print(f"🧪 测试Hook: {hook_name}")

        try:
            result = await self.enhanced_hooks.execute_enhanced_hook(hook_name, context or {})

            if result['success']:
                print(f"✅ {hook_name} 测试通过")
                if 'details' in result:
                    self._print_test_details(result['details'])
            else:
                print(f"❌ {hook_name} 测试失败: {result['message']}")
                if 'details' in result:
                    self._print_test_details(result['details'])

            return result

        except Exception as e:
            error_result = {
                'success': False,
                'error': str(e),
                'hook_name': hook_name
            }
            print(f"❌ 测试异常: {e}")
            return error_result

    def _print_test_details(self, details: Dict[str, Any]) -> None:
        """打印测试详情"""
        if 'issues' in details and details['issues']:
            print("  发现的问题:")
            for issue in details['issues']:
                print(f"    • {issue}")

        if 'quality_score' in details:
            print(f"  质量评分: {details['quality_score']:.1f}")

        if 'execution_time' in details:
            print(f"  执行时间: {details['execution_time']:.2f}秒")

    async def show_status(self) -> Dict[str, Any]:
        """显示hooks状态"""
        print("📊 Perfect21 Git Hooks状态")
        print("=" * 50)

        git_hooks_dir = self.project_root / ".git" / "hooks"
        if not git_hooks_dir.exists():
            print("❌ 当前目录不是Git仓库")
            return {'success': False, 'error': '不是Git仓库'}

        hook_names = ['pre-commit', 'commit-msg', 'pre-push', 'post-checkout', 'post-merge']
        status = {}

        for hook_name in hook_names:
            hook_file = git_hooks_dir / hook_name
            hook_status = {
                'installed': hook_file.exists(),
                'executable': hook_file.exists() and os.access(hook_file, os.X_OK),
                'is_perfect21': False
            }

            if hook_file.exists():
                try:
                    with open(hook_file) as f:
                        content = f.read()
                        hook_status['is_perfect21'] = 'Perfect21' in content
                except Exception:
                    pass

            status[hook_name] = hook_status

            # 显示状态
            if hook_status['installed']:
                if hook_status['is_perfect21']:
                    icon = "✅"
                    desc = "Perfect21 Hook"
                else:
                    icon = "⚠️"
                    desc = "其他Hook"

                if not hook_status['executable']:
                    icon = "❌"
                    desc += " (不可执行)"
            else:
                icon = "❌"
                desc = "未安装"

            print(f"  {hook_name:15} {icon} {desc}")

        # 显示产物统计
        print("\n📁 产物仓库状态:")
        artifact_stats = await self.artifact_manager.get_repository_stats()
        print(f"  总产物数量: {artifact_stats['total_artifacts']}")
        print(f"  仓库大小: {artifact_stats['total_size_mb']:.1f} MB")
        print(f"  平均质量: {artifact_stats['average_quality_score']:.1f}")

        # 显示配置
        print("\n⚙️ 配置信息:")
        config = self.enhanced_hooks.hook_configs
        for hook_name, hook_config in config.items():
            print(f"  {hook_name}:")
            print(f"    优先级: {hook_config.priority.name}")
            print(f"    失败策略: {hook_config.failure_strategy.value}")
            print(f"    超时: {hook_config.timeout_seconds}s")

        return {
            'success': True,
            'hooks_status': status,
            'artifact_stats': artifact_stats
        }

    async def manage_artifacts(self, action: str, **kwargs) -> Dict[str, Any]:
        """管理产物"""
        if action == "list":
            artifact_type = kwargs.get('type')
            if artifact_type:
                try:
                    artifact_type_enum = ArtifactType(artifact_type)
                    artifacts = await self.artifact_manager.get_artifacts_by_type(artifact_type_enum)

                    print(f"📋 {artifact_type} 类型的产物:")
                    for artifact in artifacts:
                        print(f"  {artifact.id}")
                        print(f"    名称: {artifact.name}")
                        print(f"    状态: {artifact.status.value}")
                        print(f"    质量: {artifact.quality_level.value} ({artifact.quality_score:.1f})")
                        print(f"    创建时间: {artifact.created_at}")
                        print()

                    return {
                        'success': True,
                        'artifacts': [a.__dict__ for a in artifacts]
                    }
                except ValueError:
                    print(f"❌ 无效的产物类型: {artifact_type}")
                    return {'success': False, 'error': '无效的产物类型'}
            else:
                # 显示所有类型的统计
                stats = await self.artifact_manager.get_repository_stats()
                print("📊 产物仓库统计:")
                print(f"总数: {stats['total_artifacts']}")
                print("\n按类型分布:")
                for type_name, count in stats['by_type'].items():
                    print(f"  {type_name}: {count}")
                print("\n按状态分布:")
                for status_name, count in stats['by_status'].items():
                    print(f"  {status_name}: {count}")
                return {'success': True, 'stats': stats}

        elif action == "cleanup":
            dry_run = not kwargs.get('force', False)
            if dry_run:
                print("🧹 产物清理预览 (使用 --force 执行实际清理):")
            else:
                print("🧹 执行产物清理:")

            result = await self.artifact_manager.cleanup_artifacts(dry_run)

            if 'error' in result:
                print(f"❌ 清理失败: {result['error']}")
            else:
                print(f"📊 清理统计:")
                print(f"  候选产物: {result['candidates']}")
                print(f"  已删除: {result['removed']}")
                print(f"  释放空间: {result['space_freed_mb']} MB")
                if result['errors']:
                    print("  错误:")
                    for error in result['errors']:
                        print(f"    • {error}")

            return result

        elif action == "validate":
            artifact_id = kwargs.get('id')
            if not artifact_id:
                print("❌ 请提供产物ID")
                return {'success': False, 'error': '缺少产物ID'}

            print(f"🔍 验证产物: {artifact_id}")
            result = await self.artifact_manager.validate_artifact(artifact_id)

            if result['success']:
                print(f"✅ 验证通过")
                print(f"  质量评分: {result['quality_score']:.1f}")
                print(f"  质量等级: {result['quality_level']}")
                if result['issues']:
                    print("  发现的问题:")
                    for issue in result['issues']:
                        print(f"    • {issue}")
                if result['recommendations']:
                    print("  改进建议:")
                    for rec in result['recommendations']:
                        print(f"    • {rec}")
            else:
                print(f"❌ 验证失败: {result['error']}")

            return result

        else:
            print(f"❌ 未知的产物操作: {action}")
            return {'success': False, 'error': f'未知操作: {action}'}

    async def run_workflow_test(self, task_description: str) -> Dict[str, Any]:
        """运行完整的工作流测试"""
        print("🚀 运行Perfect21工作流测试")
        print(f"任务: {task_description}")
        print("=" * 50)

        # 模拟工作流的各个阶段
        stages = [
            ('task_analysis', '任务分析'),
            ('agent_selection', 'Agent选择'),
            ('execution', '并行执行'),
            ('quality_check', '质量检查'),
            ('deployment_prep', '部署准备')
        ]

        results = {}
        overall_success = True

        for stage_id, stage_name in stages:
            print(f"\n📋 阶段: {stage_name}")

            try:
                if stage_id == 'task_analysis':
                    result = await self._test_task_analysis(task_description)
                elif stage_id == 'agent_selection':
                    result = await self._test_agent_selection(task_description)
                elif stage_id == 'execution':
                    result = await self._test_execution()
                elif stage_id == 'quality_check':
                    result = await self._test_quality_checks()
                elif stage_id == 'deployment_prep':
                    result = await self._test_deployment_prep()

                results[stage_id] = result

                if result['success']:
                    print(f"✅ {stage_name} 完成")
                else:
                    print(f"❌ {stage_name} 失败: {result.get('message', '未知错误')}")
                    overall_success = False

            except Exception as e:
                print(f"❌ {stage_name} 异常: {e}")
                results[stage_id] = {'success': False, 'error': str(e)}
                overall_success = False

        # 汇总结果
        print(f"\n📊 工作流测试结果:")
        print(f"总体状态: {'✅ 成功' if overall_success else '❌ 失败'}")

        successful_stages = sum(1 for r in results.values() if r.get('success', False))
        print(f"成功阶段: {successful_stages}/{len(stages)}")

        return {
            'success': overall_success,
            'stages': results,
            'summary': {
                'total_stages': len(stages),
                'successful_stages': successful_stages,
                'success_rate': successful_stages / len(stages) * 100
            }
        }

    # 工作流测试阶段实现
    async def _test_task_analysis(self, task_description: str) -> Dict[str, Any]:
        """测试任务分析阶段"""
        # 创建任务分析产物
        task_analysis = {
            'task_description': task_description,
            'requirements': ['功能完整', '质量保证', '性能优化'],
            'constraints': ['时间限制', '资源限制'],
            'success_criteria': ['测试通过', '代码审查通过', '性能达标']
        }

        artifact_id = await self.artifact_manager.store_artifact(
            ArtifactType.TASK_ANALYSIS,
            f"task_analysis_{int(asyncio.get_event_loop().time())}",
            task_analysis
        )

        return {
            'success': True,
            'artifact_id': artifact_id,
            'message': '任务分析完成'
        }

    async def _test_agent_selection(self, task_description: str) -> Dict[str, Any]:
        """测试Agent选择阶段"""
        # 模拟Agent选择
        agent_selection = {
            'task_type': 'development',
            'selected_agents': ['backend-architect', 'test-engineer', 'security-auditor'],
            'execution_mode': 'parallel',
            'reasoning': 'Based on task requirements'
        }

        artifact_id = await self.artifact_manager.store_artifact(
            ArtifactType.AGENT_SELECTION,
            f"agent_selection_{int(asyncio.get_event_loop().time())}",
            agent_selection
        )

        return {
            'success': True,
            'artifact_id': artifact_id,
            'message': 'Agent选择完成'
        }

    async def _test_execution(self) -> Dict[str, Any]:
        """测试执行阶段"""
        # 模拟执行结果
        execution_results = {
            'execution_mode': 'parallel',
            'agent_results': [
                {
                    'agent': 'backend-architect',
                    'success': True,
                    'execution_time': 2.5,
                    'result': '架构设计完成'
                },
                {
                    'agent': 'test-engineer',
                    'success': True,
                    'execution_time': 1.8,
                    'result': '测试用例创建完成'
                },
                {
                    'agent': 'security-auditor',
                    'success': True,
                    'execution_time': 3.2,
                    'result': '安全审查完成'
                }
            ]
        }

        artifact_id = await self.artifact_manager.store_artifact(
            ArtifactType.EXECUTION_RESULTS,
            f"execution_results_{int(asyncio.get_event_loop().time())}",
            execution_results
        )

        return {
            'success': True,
            'artifact_id': artifact_id,
            'message': '并行执行完成'
        }

    async def _test_quality_checks(self) -> Dict[str, Any]:
        """测试质量检查阶段"""
        # 模拟质量报告
        quality_report = {
            'overall_score': 85,
            'code_quality': {
                'score': 88,
                'coverage': 85,
                'complexity': 7
            },
            'security': {
                'score': 90,
                'vulnerabilities': 0
            },
            'performance': {
                'score': 80,
                'response_time_p95': 180
            }
        }

        artifact_id = await self.artifact_manager.store_artifact(
            ArtifactType.QUALITY_REPORT,
            f"quality_report_{int(asyncio.get_event_loop().time())}",
            quality_report
        )

        return {
            'success': True,
            'artifact_id': artifact_id,
            'message': '质量检查完成'
        }

    async def _test_deployment_prep(self) -> Dict[str, Any]:
        """测试部署准备阶段"""
        # 模拟部署配置
        deployment_config = {
            'environment': 'staging',
            'containers': ['app', 'db', 'cache'],
            'monitoring': {
                'enabled': True,
                'metrics': ['cpu', 'memory', 'response_time']
            },
            'rollback_plan': {
                'available': True,
                'auto_rollback': True
            }
        }

        artifact_id = await self.artifact_manager.store_artifact(
            ArtifactType.DEPLOYMENT_CONFIG,
            f"deployment_config_{int(asyncio.get_event_loop().time())}",
            deployment_config
        )

        return {
            'success': True,
            'artifact_id': artifact_id,
            'message': '部署准备完成'
        }


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="Perfect21 Git Hooks CLI - 管理和使用Git Hook集成功能",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  %(prog)s install                     # 安装所有hooks
  %(prog)s install --hooks pre-commit  # 安装特定hook
  %(prog)s test pre-commit             # 测试hook
  %(prog)s status                      # 显示状态
  %(prog)s artifacts list              # 查看产物
  %(prog)s workflow-test "实现登录功能"  # 运行工作流测试
        """
    )

    parser.add_argument(
        '--project-root',
        help='项目根目录路径 (默认: 当前目录)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='显示详细输出'
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # install命令
    install_parser = subparsers.add_parser('install', help='安装Git hooks')
    install_parser.add_argument(
        '--hooks',
        nargs='+',
        choices=['pre-commit', 'commit-msg', 'pre-push', 'post-checkout', 'post-merge'],
        help='要安装的hook类型 (默认: 全部)'
    )
    install_parser.add_argument(
        '--force',
        action='store_true',
        help='强制覆盖已存在的hooks'
    )

    # uninstall命令
    uninstall_parser = subparsers.add_parser('uninstall', help='卸载Git hooks')
    uninstall_parser.add_argument(
        '--hooks',
        nargs='+',
        choices=['pre-commit', 'commit-msg', 'pre-push', 'post-checkout', 'post-merge'],
        help='要卸载的hook类型 (默认: 全部)'
    )

    # test命令
    test_parser = subparsers.add_parser('test', help='测试Git hook')
    test_parser.add_argument(
        'hook_name',
        choices=['pre-commit', 'commit-msg', 'pre-push', 'post-checkout', 'post-merge'],
        help='要测试的hook名称'
    )
    test_parser.add_argument(
        '--context',
        help='测试上下文 (JSON格式)'
    )

    # status命令
    subparsers.add_parser('status', help='显示hooks和产物状态')

    # artifacts命令
    artifacts_parser = subparsers.add_parser('artifacts', help='管理产物')
    artifacts_subparsers = artifacts_parser.add_subparsers(dest='artifacts_action')

    # artifacts list
    list_parser = artifacts_subparsers.add_parser('list', help='列出产物')
    list_parser.add_argument(
        '--type',
        choices=[t.value for t in ArtifactType],
        help='产物类型过滤'
    )

    # artifacts cleanup
    cleanup_parser = artifacts_subparsers.add_parser('cleanup', help='清理产物')
    cleanup_parser.add_argument(
        '--force',
        action='store_true',
        help='执行实际清理 (否则只是预览)'
    )

    # artifacts validate
    validate_parser = artifacts_subparsers.add_parser('validate', help='验证产物')
    validate_parser.add_argument(
        'id',
        help='产物ID'
    )

    # workflow-test命令
    workflow_test_parser = subparsers.add_parser('workflow-test', help='运行完整工作流测试')
    workflow_test_parser.add_argument(
        'task_description',
        help='任务描述'
    )

    return parser


async def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # 创建CLI管理器
    cli = GitHooksCLI(args.project_root)

    try:
        if args.command == 'install':
            result = await cli.install_hooks(args.hooks, args.force)

        elif args.command == 'uninstall':
            result = await cli.uninstall_hooks(args.hooks)

        elif args.command == 'test':
            context = {}
            if args.context:
                try:
                    context = json.loads(args.context)
                except json.JSONDecodeError as e:
                    print(f"❌ 解析context JSON失败: {e}")
                    return

            result = await cli.test_hook(args.hook_name, context)

        elif args.command == 'status':
            result = await cli.show_status()

        elif args.command == 'artifacts':
            if args.artifacts_action == 'list':
                result = await cli.manage_artifacts('list', type=getattr(args, 'type', None))
            elif args.artifacts_action == 'cleanup':
                result = await cli.manage_artifacts('cleanup', force=args.force)
            elif args.artifacts_action == 'validate':
                result = await cli.manage_artifacts('validate', id=args.id)
            else:
                print("❌ 请指定artifacts子命令: list, cleanup, validate")
                return

        elif args.command == 'workflow-test':
            result = await cli.run_workflow_test(args.task_description)

        else:
            print(f"❌ 未知命令: {args.command}")
            return

        # 设置退出码
        if result and not result.get('success', True):
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️ 操作被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 操作失败: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())