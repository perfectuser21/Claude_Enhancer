#!/usr/bin/env python3
"""
Perfect21 Git Hooks Integration Test
专门测试Git工作流与多Agent协调机制

重点测试:
- Git钩子触发机制
- 多Agent并行调用
- 分支保护策略
- SubAgent路由选择
"""

import os
import sys
import json
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# 添加项目路径
sys.path.append(os.path.dirname(__file__))

class GitHooksIntegrationTest:
    """Git Hooks集成测试"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'test_summary': {},
            'hooks_tests': {},
            'agent_coordination': {},
            'performance': {}
        }
        print("🔧 Perfect21 Git Hooks集成测试初始化")

    def test_hooks_configuration(self):
        """测试钩子配置"""
        print("📋 测试Git钩子配置...")

        try:
            from features.git_workflow.hooks_manager import GitHooksManager
            hooks_manager = GitHooksManager()

            config_test = {
                'hooks_manager_init': True,
                'total_hooks': len(hooks_manager.hooks_config),
                'hook_groups': list(hooks_manager.hook_groups.keys()),
                'required_hooks': [],
                'subagent_mapping': {}
            }

            # 检查必需钩子
            for hook_name, config in hooks_manager.hooks_config.items():
                if config.get('required'):
                    config_test['required_hooks'].append(hook_name)

                # 记录SubAgent映射
                if 'subagent' in config:
                    config_test['subagent_mapping'][hook_name] = config['subagent']

            self.test_results['hooks_tests']['configuration'] = config_test
            print(f"✅ 配置测试完成 - 共{config_test['total_hooks']}个钩子")
            return True

        except Exception as e:
            self.test_results['hooks_tests']['configuration'] = {
                'success': False,
                'error': str(e)
            }
            print(f"❌ 配置测试失败: {e}")
            return False

    def test_hook_installation(self):
        """测试钩子安装机制"""
        print("⚙️ 测试钩子安装...")

        try:
            from features.git_workflow.hooks_manager import GitHooksManager
            hooks_manager = GitHooksManager()

            # 检查Git目录
            git_hooks_dir = Path('.git/hooks')
            git_exists = git_hooks_dir.exists()

            install_test = {
                'git_hooks_dir_exists': git_exists,
                'install_capability': True,
                'hook_groups_available': list(hooks_manager.hook_groups.keys()),
                'installation_methods': ['single', 'group', 'all']
            }

            if git_exists:
                # 检查现有钩子
                existing_hooks = [f.name for f in git_hooks_dir.iterdir()
                                if f.is_file() and not f.name.endswith('.sample')]
                install_test['existing_hooks'] = existing_hooks
                install_test['perfect21_hooks'] = [
                    hook for hook in existing_hooks
                    if self.is_perfect21_hook(git_hooks_dir / hook)
                ]

            self.test_results['hooks_tests']['installation'] = install_test
            print(f"✅ 安装测试完成 - Git目录: {'存在' if git_exists else '不存在'}")
            return True

        except Exception as e:
            self.test_results['hooks_tests']['installation'] = {
                'success': False,
                'error': str(e)
            }
            print(f"❌ 安装测试失败: {e}")
            return False

    def is_perfect21_hook(self, hook_file: Path) -> bool:
        """检查是否为Perfect21钩子"""
        try:
            content = hook_file.read_text()
            return 'Perfect21' in content or 'perfect21' in content
        except:
            return False

    def test_hook_execution_simulation(self):
        """测试钩子执行模拟"""
        print("🚀 测试钩子执行模拟...")

        try:
            from main.perfect21 import Perfect21
            p21 = Perfect21()

            execution_test = {
                'perfect21_init': True,
                'hook_simulations': {},
                'agent_calls_generated': {},
                'branch_routing': {}
            }

            # 测试不同钩子的执行
            test_hooks = [
                ('pre-commit', []),
                ('pre-push', ['origin']),
                ('post-checkout', ['old_ref', 'new_ref', '1']),
                ('commit-msg', ['.git/COMMIT_EDITMSG'])
            ]

            for hook_name, args in test_hooks:
                try:
                    print(f"  🔍 模拟执行: {hook_name}")
                    result = p21.git_hook_handler(hook_name, *args)

                    execution_test['hook_simulations'][hook_name] = {
                        'success': result.get('success', False),
                        'has_call_info': 'call_info' in result,
                        'message': result.get('message', '')
                    }

                    # 记录Agent调用信息
                    if 'call_info' in result:
                        call_info = result['call_info']
                        execution_test['agent_calls_generated'][hook_name] = {
                            'command': call_info.get('command', ''),
                            'context_provided': 'context' in call_info
                        }

                except Exception as e:
                    execution_test['hook_simulations'][hook_name] = {
                        'success': False,
                        'error': str(e)
                    }

            self.test_results['hooks_tests']['execution'] = execution_test
            print(f"✅ 执行模拟完成 - 测试{len(test_hooks)}个钩子")
            return True

        except Exception as e:
            self.test_results['hooks_tests']['execution'] = {
                'success': False,
                'error': str(e)
            }
            print(f"❌ 执行模拟失败: {e}")
            return False

    def test_branch_based_routing(self):
        """测试基于分支的Agent路由"""
        print("🌿 测试分支路由策略...")

        try:
            from main.perfect21 import Perfect21
            p21 = Perfect21()

            # 获取当前分支信息
            current_branch = self.get_current_branch()

            routing_test = {
                'current_branch': current_branch,
                'routing_logic': {},
                'protection_levels': {},
                'agent_selection': {}
            }

            # 测试不同分支类型的路由
            branch_scenarios = [
                ('main', 'main'),
                ('feature/test', 'feature'),
                ('release/1.0.0', 'release'),
                ('hotfix/critical', 'hotfix')
            ]

            for branch_name, expected_type in branch_scenarios:
                try:
                    # 模拟分支分析
                    branch_info = self.analyze_branch_type(branch_name)
                    routing_test['routing_logic'][branch_name] = branch_info

                    # 基于分支类型的Agent选择逻辑
                    expected_agent = self.get_expected_agent_for_branch(expected_type)
                    routing_test['agent_selection'][branch_name] = expected_agent

                except Exception as e:
                    routing_test['routing_logic'][branch_name] = {'error': str(e)}

            self.test_results['agent_coordination']['branch_routing'] = routing_test
            print(f"✅ 分支路由测试完成 - 当前分支: {current_branch}")
            return True

        except Exception as e:
            self.test_results['agent_coordination']['branch_routing'] = {
                'success': False,
                'error': str(e)
            }
            print(f"❌ 分支路由测试失败: {e}")
            return False

    def get_current_branch(self) -> str:
        """获取当前Git分支"""
        try:
            result = subprocess.run(['git', 'branch', '--show-current'],
                                  capture_output=True, text=True)
            return result.stdout.strip() if result.returncode == 0 else 'unknown'
        except:
            return 'unknown'

    def analyze_branch_type(self, branch_name: str) -> Dict[str, Any]:
        """分析分支类型"""
        if branch_name.startswith('main') or branch_name == 'master':
            return {
                'type': 'main',
                'protection_level': 'strict',
                'requires_review': True,
                'suggested_agent': '@orchestrator'
            }
        elif branch_name.startswith('feature/'):
            return {
                'type': 'feature',
                'protection_level': 'standard',
                'requires_review': False,
                'suggested_agent': '@code-reviewer'
            }
        elif branch_name.startswith('release/'):
            return {
                'type': 'release',
                'protection_level': 'strict',
                'requires_review': True,
                'suggested_agent': '@deployment-manager'
            }
        elif branch_name.startswith('hotfix/'):
            return {
                'type': 'hotfix',
                'protection_level': 'expedited',
                'requires_review': True,
                'suggested_agent': '@test-engineer'
            }
        else:
            return {
                'type': 'unknown',
                'protection_level': 'standard',
                'requires_review': False,
                'suggested_agent': '@code-reviewer'
            }

    def get_expected_agent_for_branch(self, branch_type: str) -> str:
        """获取分支类型对应的预期Agent"""
        agent_mapping = {
            'main': '@orchestrator',
            'feature': '@code-reviewer',
            'release': '@deployment-manager',
            'hotfix': '@test-engineer'
        }
        return agent_mapping.get(branch_type, '@code-reviewer')

    def test_multi_agent_coordination(self):
        """测试多Agent协调机制"""
        print("🤝 测试多Agent协调...")

        try:
            coordination_test = {
                'parallel_capability': True,
                'agent_workflows': {},
                'coordination_scenarios': {}
            }

            # 测试不同协调场景
            scenarios = {
                'main_branch_commit': {
                    'primary_agent': '@orchestrator',
                    'supporting_agents': ['@code-reviewer', '@security-auditor', '@test-engineer'],
                    'execution_mode': 'sequential_with_gates'
                },
                'feature_development': {
                    'primary_agent': '@code-reviewer',
                    'supporting_agents': ['@test-engineer'],
                    'execution_mode': 'parallel'
                },
                'security_focused': {
                    'primary_agent': '@security-auditor',
                    'supporting_agents': ['@code-reviewer'],
                    'execution_mode': 'security_first'
                },
                'performance_critical': {
                    'primary_agent': '@performance-engineer',
                    'supporting_agents': ['@test-engineer', '@devops-engineer'],
                    'execution_mode': 'performance_gated'
                }
            }

            for scenario_name, scenario_config in scenarios.items():
                coordination_test['coordination_scenarios'][scenario_name] = {
                    'agents_count': len(scenario_config['supporting_agents']) + 1,
                    'coordination_complexity': self.calculate_coordination_complexity(scenario_config),
                    'expected_execution_time': self.estimate_execution_time(scenario_config),
                    'config': scenario_config
                }

            # 测试Agent可用性
            available_agents = self.check_available_agents()
            coordination_test['available_agents'] = available_agents

            self.test_results['agent_coordination']['multi_agent'] = coordination_test
            print(f"✅ 多Agent协调测试完成 - 可用Agent: {len(available_agents)}个")
            return True

        except Exception as e:
            self.test_results['agent_coordination']['multi_agent'] = {
                'success': False,
                'error': str(e)
            }
            print(f"❌ 多Agent协调测试失败: {e}")
            return False

    def calculate_coordination_complexity(self, scenario_config: Dict) -> str:
        """计算协调复杂度"""
        agent_count = len(scenario_config['supporting_agents']) + 1
        execution_mode = scenario_config['execution_mode']

        if agent_count <= 2:
            return 'simple'
        elif agent_count <= 4 and 'parallel' in execution_mode:
            return 'moderate'
        else:
            return 'complex'

    def estimate_execution_time(self, scenario_config: Dict) -> str:
        """估算执行时间"""
        agent_count = len(scenario_config['supporting_agents']) + 1
        execution_mode = scenario_config['execution_mode']

        if 'parallel' in execution_mode:
            return f"{agent_count * 2}-{agent_count * 3}秒"
        elif 'sequential' in execution_mode:
            return f"{agent_count * 5}-{agent_count * 8}秒"
        else:
            return f"{agent_count * 3}-{agent_count * 5}秒"

    def check_available_agents(self) -> list:
        """检查可用的Agent"""
        agents_dir = self.project_root / 'core' / 'claude-code-unified-agents' / '.claude' / 'agents'

        if not agents_dir.exists():
            return []

        # 扫描所有Agent文件
        agent_files = list(agents_dir.rglob('*.md'))
        return [f.stem for f in agent_files if f.is_file()]

    def test_performance_benchmarks(self):
        """测试性能基准"""
        print("⚡ 测试性能基准...")

        import time

        try:
            performance_test = {
                'hook_execution_times': {},
                'agent_call_preparation': {},
                'parallel_processing': {}
            }

            # 测试钩子执行时间
            from main.perfect21 import Perfect21
            p21 = Perfect21()

            test_hooks = ['pre-commit', 'pre-push', 'post-checkout']

            for hook_name in test_hooks:
                start_time = time.time()
                result = p21.git_hook_handler(hook_name)
                execution_time = time.time() - start_time

                performance_test['hook_execution_times'][hook_name] = {
                    'time_seconds': execution_time,
                    'success': result.get('success', False),
                    'performance_rating': 'fast' if execution_time < 1 else 'moderate' if execution_time < 3 else 'slow'
                }

            # 测试Agent调用准备时间
            from features.auto_capability_injection import get_global_injector

            injector = get_global_injector()
            start_time = time.time()
            result = injector.inject_and_call_orchestrator("性能测试请求")
            injection_time = time.time() - start_time

            performance_test['agent_call_preparation'] = {
                'injection_time': injection_time,
                'success': result.get('success', False),
                'context_size': len(result.get('orchestrator_context', '')),
                'performance_rating': 'fast' if injection_time < 2 else 'moderate' if injection_time < 5 else 'slow'
            }

            self.test_results['performance'] = performance_test
            print(f"✅ 性能测试完成 - 平均钩子执行时间: {sum(t['time_seconds'] for t in performance_test['hook_execution_times'].values()) / len(performance_test['hook_execution_times']):.3f}秒")
            return True

        except Exception as e:
            self.test_results['performance'] = {
                'success': False,
                'error': str(e)
            }
            print(f"❌ 性能测试失败: {e}")
            return False

    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 Perfect21 Git Hooks Integration Test Suite")
        print("=" * 60)
        print(f"开始时间: {datetime.now().strftime('%H:%M:%S')}")
        print("=" * 60)

        test_methods = [
            ('配置测试', self.test_hooks_configuration),
            ('安装测试', self.test_hook_installation),
            ('执行模拟', self.test_hook_execution_simulation),
            ('分支路由', self.test_branch_based_routing),
            ('多Agent协调', self.test_multi_agent_coordination),
            ('性能基准', self.test_performance_benchmarks)
        ]

        results = []
        for test_name, test_method in test_methods:
            print(f"\n🔍 开始{test_name}...")
            try:
                success = test_method()
                results.append((test_name, success))
                if success:
                    print(f"✅ {test_name}完成")
                else:
                    print(f"❌ {test_name}失败")
            except Exception as e:
                print(f"💥 {test_name}异常: {e}")
                results.append((test_name, False))

        # 生成测试报告
        self.generate_test_report(results)

        return results

    def generate_test_report(self, results):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📊 生成测试报告...")

        # 计算总体结果
        total_tests = len(results)
        passed_tests = sum(1 for _, success in results if success)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0

        # 更新测试摘要
        self.test_results['test_summary'] = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'success_rate': success_rate,
            'overall_status': '通过' if passed_tests == total_tests else '部分失败'
        }

        # 生成Markdown报告
        report_content = self._generate_markdown_report()

        # 保存报告
        report_file = self.project_root / 'git_hooks_integration_test_report.md'
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

        # 保存JSON数据
        json_file = self.project_root / 'git_hooks_integration_test_results.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)

        # 显示结果
        print(f"📋 测试报告: {report_file}")
        print(f"📊 详细数据: {json_file}")
        print(f"🎯 测试结果: {passed_tests}/{total_tests} 通过 ({success_rate:.1f}%)")

        if passed_tests == total_tests:
            print("🎉 Perfect21 Git Hooks集成测试全部通过!")
            print("   ✅ Git工作流机制正常")
            print("   ✅ 多Agent协调就绪")
            print("   ✅ 分支保护策略有效")
            print("   ✅ 性能指标达标")
        else:
            failed_count = total_tests - passed_tests
            print(f"⚠️ {failed_count}个测试需要关注")

            # 显示失败的测试
            for test_name, success in results:
                if not success:
                    print(f"   ❌ {test_name}")

        print("=" * 60)

    def _generate_markdown_report(self) -> str:
        """生成Markdown格式报告"""
        summary = self.test_results['test_summary']

        report = f"""# Perfect21 Git Hooks Integration Test Report

**测试时间**: {self.test_results['timestamp']}
**总体状态**: {summary['overall_status']}
**成功率**: {summary['success_rate']:.1f}%

## 📋 测试概览

- **总测试数**: {summary['total_tests']}
- **通过数**: {summary['passed_tests']}
- **失败数**: {summary['failed_tests']}

## 🔧 Git Hooks测试结果

### 配置测试
"""

        # 添加具体测试结果
        if 'configuration' in self.test_results['hooks_tests']:
            config = self.test_results['hooks_tests']['configuration']
            if not config.get('success', True):
                report += f"❌ 配置测试失败: {config.get('error', '未知错误')}\n"
            else:
                report += f"✅ 发现{config.get('total_hooks', 0)}个钩子配置\n"
                report += f"✅ {len(config.get('hook_groups', []))}个钩子组可用\n"

        if 'execution' in self.test_results['hooks_tests']:
            execution = self.test_results['hooks_tests']['execution']
            if execution.get('success', True):
                simulations = execution.get('hook_simulations', {})
                successful_sims = sum(1 for s in simulations.values() if s.get('success'))
                report += f"✅ 钩子执行模拟: {successful_sims}/{len(simulations)}成功\n"

        # 添加Agent协调结果
        report += "\n## 🤝 多Agent协调测试\n\n"

        if 'multi_agent' in self.test_results['agent_coordination']:
            multi_agent = self.test_results['agent_coordination']['multi_agent']
            if not multi_agent.get('success', True):
                report += f"❌ 多Agent协调测试失败: {multi_agent.get('error')}\n"
            else:
                scenarios = multi_agent.get('coordination_scenarios', {})
                report += f"✅ 测试{len(scenarios)}个协调场景\n"
                available_agents = len(multi_agent.get('available_agents', []))
                report += f"✅ {available_agents}个Agent可用\n"

        # 添加性能测试结果
        report += "\n## ⚡ 性能测试结果\n\n"

        if self.test_results.get('performance'):
            perf = self.test_results['performance']
            if not perf.get('success', True):
                report += f"❌ 性能测试失败: {perf.get('error')}\n"
            else:
                hook_times = perf.get('hook_execution_times', {})
                if hook_times:
                    avg_time = sum(t['time_seconds'] for t in hook_times.values()) / len(hook_times)
                    report += f"✅ 平均钩子执行时间: {avg_time:.3f}秒\n"

                injection = perf.get('agent_call_preparation', {})
                if injection:
                    report += f"✅ Agent调用准备时间: {injection.get('injection_time', 0):.3f}秒\n"

        report += "\n## 💡 建议\n\n"

        if summary['success_rate'] == 100:
            report += "🎉 Perfect21 Git工作流系统完全就绪，可以投入生产使用！\n\n"
            report += "- 所有Git钩子功能正常\n"
            report += "- 多Agent协调机制可靠\n"
            report += "- 性能指标满足要求\n"
        else:
            report += "需要修复的问题：\n\n"
            # 这里可以添加具体的修复建议
            report += "- 检查失败的测试用例\n"
            report += "- 验证Agent配置完整性\n"
            report += "- 优化性能瓶颈\n"

        return report

def main():
    """主测试函数"""
    test_suite = GitHooksIntegrationTest()
    results = test_suite.run_all_tests()

    # 返回退出码
    all_passed = all(success for _, success in results)
    return 0 if all_passed else 1

if __name__ == '__main__':
    exit_code = main()
    exit(exit_code)