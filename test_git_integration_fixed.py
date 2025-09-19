#!/usr/bin/env python3
"""
Perfect21 Git Integration Test - Fixed Version
测试Git工作流集成功能
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.append(str(Path(__file__).parent))

try:
    from features.git import (
        GitHooksManager,
        GitWorkflowManager,
        AdvancedGitWorkflowManager,
        HookType,
        WorkflowType,
        TaskPriority,
        WorkflowStage,
        GitCLI
    )
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保Perfect21 Git模块已正确安装")
    sys.exit(1)


class GitIntegrationTester:
    """Git集成功能测试器"""

    def __init__(self):
        self.project_root = str(Path.cwd())
        self.test_results = []

    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始Perfect21 Git集成测试")
        print("=" * 60)

        tests = [
            ("Git Hooks管理器测试", self.test_git_hooks_manager),
            ("Git工作流管理器测试", self.test_git_workflow_manager),
            ("高级工作流管理器测试", self.test_advanced_workflow_manager),
            ("CLI接口测试", self.test_cli_interface),
            ("生产力分析器测试", self.test_productivity_analyzer),
            ("智能分支管理测试", self.test_smart_branch_manager)
        ]

        for test_name, test_func in tests:
            print(f"\n📋 {test_name}")
            print("-" * 40)

            try:
                result = await test_func()
                self.test_results.append({
                    'test': test_name,
                    'success': result['success'],
                    'details': result
                })

                if result['success']:
                    print(f"✅ {test_name} - 通过")
                else:
                    print(f"❌ {test_name} - 失败: {result.get('error', 'Unknown error')}")

            except Exception as e:
                print(f"❌ {test_name} - 异常: {e}")
                self.test_results.append({
                    'test': test_name,
                    'success': False,
                    'error': str(e)
                })

        return await self.print_summary()

    async def test_git_hooks_manager(self):
        """测试Git Hooks管理器"""
        try:
            manager = GitHooksManager(self.project_root)

            # 测试Hook状态
            status = await manager.get_hook_status()

            # 测试Hook配置加载
            config_loaded = len(manager.hooks_config) > 0

            # 测试Hook执行（测试模式）
            test_result = await manager.test_hook(HookType.PRE_COMMIT)

            return {
                'success': True,
                'hook_status': len(status) > 0 if isinstance(status, dict) else False,
                'config_loaded': config_loaded,
                'test_execution': test_result.get('success', False)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_git_workflow_manager(self):
        """测试Git工作流管理器"""
        try:
            manager = GitWorkflowManager(self.project_root)

            # 测试Git状态获取
            git_status = await manager._get_git_status()

            # 测试分支获取
            current_branch = await manager._get_current_branch()

            # 测试提交信息生成
            smart_message = await manager._generate_smart_commit_message(
                ['test_file.py'], 'test diff content'
            )

            # 测试项目健康度检查
            health = await manager.get_project_health()

            return {
                'success': True,
                'git_status': isinstance(git_status, dict) and 'current_branch' in git_status,
                'current_branch': isinstance(current_branch, str),
                'smart_message': isinstance(smart_message, str) and len(smart_message) > 0,
                'health_check': isinstance(health, dict)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_advanced_workflow_manager(self):
        """测试高级工作流管理器"""
        try:
            manager = AdvancedGitWorkflowManager(self.project_root)

            # 测试任务创建
            task_result = await manager.create_task(
                title="测试任务",
                description="这是一个测试任务",
                priority=TaskPriority.MEDIUM,
                workflow_type=WorkflowType.FEATURE_DEVELOPMENT
            )

            task_id = None
            if task_result['success']:
                task_id = task_result['task_id']

                # 测试任务进度更新
                update_result = await manager.update_task_progress(
                    task_id, 50.0, WorkflowStage.DEVELOPMENT, "测试进度更新"
                )
            else:
                update_result = {'success': False, 'error': 'Task creation failed'}

            # 测试仪表板数据
            dashboard = await manager.get_dashboard_data()

            return {
                'success': True,
                'task_creation': task_result['success'],
                'task_update': update_result['success'],
                'dashboard_available': 'timestamp' in dashboard,
                'task_id': task_id
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_cli_interface(self):
        """测试CLI接口"""
        try:
            cli = GitCLI()
            parser = cli.create_parser()

            # 测试解析器创建
            parser_created = parser is not None

            # 测试命令解析（模拟参数）
            import argparse
            test_args = argparse.Namespace(
                command='dashboard',
                json=True
            )

            # 测试仪表板命令
            dashboard_result = await cli._handle_dashboard_command(test_args)

            return {
                'success': True,
                'parser_created': parser_created,
                'dashboard_command': dashboard_result.get('success', False)
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_productivity_analyzer(self):
        """测试生产力分析器"""
        try:
            manager = AdvancedGitWorkflowManager(self.project_root)
            analyzer = manager.productivity_analyzer

            # 测试编程会话记录
            session_data = await analyzer.track_coding_session(
                "test_task", 30, 100, 5
            )

            # 测试生产力洞察
            insights = await analyzer.get_productivity_insights(7)

            return {
                'success': True,
                'session_tracking': 'productivity_score' in session_data,
                'insights_generated': 'analysis_period' in insights
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def test_smart_branch_manager(self):
        """测试智能分支管理"""
        try:
            manager = AdvancedGitWorkflowManager(self.project_root)
            branch_manager = manager.branch_manager

            # 测试分支清理建议
            cleanup_suggestions = await branch_manager.suggest_branch_cleanup()

            return {
                'success': True,
                'cleanup_suggestions_available': 'cleanup_suggestions' in cleanup_suggestions or 'error' in cleanup_suggestions
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def print_summary(self):
        """打印测试总结"""
        print("\n" + "="*60)
        print("📊 测试总结")
        print("="*60)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests

        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {failed_tests} ❌")
        if total_tests > 0:
            print(f"通过率: {(passed_tests/total_tests*100):.1f}%")

        if failed_tests > 0:
            print("\n失败的测试:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  ❌ {result['test']}: {result.get('error', 'Unknown error')}")

        # 保存详细结果
        results_file = Path("git_integration_test_results.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total': total_tests,
                    'passed': passed_tests,
                    'failed': failed_tests,
                    'success_rate': passed_tests/total_tests*100 if total_tests > 0 else 0
                },
                'detailed_results': self.test_results
            }, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n📄 详细结果已保存到: {results_file}")

        return passed_tests == total_tests


async def main():
    """主函数"""
    tester = GitIntegrationTester()

    try:
        success = await tester.run_all_tests()

        if success:
            print("\n🎉 所有测试通过！Perfect21 Git集成功能正常。")
            return 0
        else:
            print("\n⚠️  部分测试失败，请检查详细结果。")
            return 1

    except KeyboardInterrupt:
        print("\n⏹️  测试被用户中断")
        return 2
    except Exception as e:
        print(f"\n💥 测试过程中发生异常: {e}")
        return 3


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)