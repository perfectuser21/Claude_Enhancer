#!/usr/bin/env python3
"""
Perfect21优化验证测试运行器
自动化执行完整的性能验证测试套件并生成详细报告
"""

import os
import sys
import time
import json
import argparse
import subprocess
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

class OptimizationTestRunner:
    """优化测试运行器"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or "tests/performance_benchmark_config.yaml"
        self.config = self._load_config()
        self.results = {}
        self.start_time = None
        self.end_time = None

    def _load_config(self) -> Dict[str, Any]:
        """加载测试配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Warning: Config file {self.config_path} not found, using defaults")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'performance_thresholds': {
                'workflow_generation_ms': 500,
                'min_parallel_agents': 3,
                'parallel_efficiency_threshold': 0.8,
                'max_memory_usage_mb': 100,
                'max_cpu_usage_percent': 80
            }
        }

    def run_all_tests(self, test_filter: Optional[str] = None) -> Dict[str, Any]:
        """运行所有优化验证测试"""
        print("🚀 Starting Perfect21 Optimization Validation Tests")
        print("=" * 60)

        self.start_time = time.time()

        test_suites = [
            ('parallel_execution', 'TestParallelExecution'),
            ('performance_benchmarks', 'TestPerformanceBenchmarks'),
            ('agent_selection', 'TestAgentSelectionAccuracy'),
            ('resource_monitoring', 'TestResourceMonitoring'),
            ('integration_scenarios', 'TestIntegrationScenarios')
        ]

        for suite_name, test_class in test_suites:
            if test_filter and test_filter not in suite_name:
                continue

            print(f"\n📋 Running {suite_name} tests...")
            try:
                result = self._run_test_suite(test_class)
                self.results[suite_name] = result
                self._print_suite_summary(suite_name, result)
            except Exception as e:
                print(f"❌ Error running {suite_name}: {str(e)}")
                self.results[suite_name] = {
                    'status': 'error',
                    'error': str(e),
                    'tests_run': 0,
                    'tests_passed': 0,
                    'tests_failed': 1
                }

        self.end_time = time.time()

        # 生成综合报告
        self._generate_comprehensive_report()

        return self.results

    def _run_test_suite(self, test_class: str) -> Dict[str, Any]:
        """运行单个测试套件"""
        cmd = [
            sys.executable, "-m", "pytest",
            f"tests/test_perfect21_optimization_validation.py::{test_class}",
            "-v",
            "--tb=short"
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5分钟超时
                cwd=Path(__file__).parent.parent
            )

            # 解析pytest的标准输出
            return self._parse_stdout_results(result)

        except subprocess.TimeoutExpired:
            return {
                'status': 'timeout',
                'tests_run': 0,
                'tests_passed': 0,
                'tests_failed': 1,
                'duration': 300
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'tests_run': 0,
                'tests_passed': 0,
                'tests_failed': 1
            }

    def _parse_pytest_results(self, json_file: str, result: subprocess.CompletedProcess) -> Dict[str, Any]:
        """解析pytest结果"""
        try:
            if os.path.exists(json_file):
                with open(json_file, 'r') as f:
                    json_data = json.load(f)

                return {
                    'status': 'passed' if result.returncode == 0 else 'failed',
                    'tests_run': json_data.get('summary', {}).get('total', 0),
                    'tests_passed': json_data.get('summary', {}).get('passed', 0),
                    'tests_failed': json_data.get('summary', {}).get('failed', 0),
                    'tests_skipped': json_data.get('summary', {}).get('skipped', 0),
                    'duration': json_data.get('duration', 0),
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
            else:
                # 如果没有JSON文件，从标准输出解析
                return self._parse_stdout_results(result)

        except Exception as e:
            return {
                'status': 'error',
                'error': f"Failed to parse results: {str(e)}",
                'tests_run': 0,
                'tests_passed': 0,
                'tests_failed': 1,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        finally:
            # 清理临时文件
            if os.path.exists(json_file):
                os.remove(json_file)

    def _parse_stdout_results(self, result: subprocess.CompletedProcess) -> Dict[str, Any]:
        """从标准输出解析测试结果"""
        stdout = result.stdout

        # 简单的正则表达式解析
        import re

        # 查找测试结果摘要
        summary_pattern = r'(\d+) passed.*?in ([\d.]+)s'
        match = re.search(summary_pattern, stdout)

        if match:
            passed = int(match.group(1))
            duration = float(match.group(2))

            return {
                'status': 'passed' if result.returncode == 0 else 'failed',
                'tests_run': passed,
                'tests_passed': passed if result.returncode == 0 else 0,
                'tests_failed': 0 if result.returncode == 0 else passed,
                'duration': duration,
                'stdout': stdout,
                'stderr': result.stderr
            }

        return {
            'status': 'unknown',
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 1,
            'stdout': stdout,
            'stderr': result.stderr
        }

    def _print_suite_summary(self, suite_name: str, result: Dict[str, Any]):
        """打印测试套件摘要"""
        status = result.get('status', 'unknown')
        passed = result.get('tests_passed', 0)
        failed = result.get('tests_failed', 0)
        duration = result.get('duration', 0)

        status_emoji = {
            'passed': '✅',
            'failed': '❌',
            'error': '💥',
            'timeout': '⏰',
            'unknown': '❓'
        }.get(status, '❓')

        print(f"{status_emoji} {suite_name}: {passed} passed, {failed} failed ({duration:.2f}s)")

        # 显示错误信息
        if result.get('error'):
            print(f"   Error: {result['error']}")

        # 显示关键输出
        if result.get('stdout') and '✅' in result.get('stdout', ''):
            for line in result['stdout'].split('\n'):
                if '✅' in line:
                    print(f"   {line.strip()}")

    def _generate_comprehensive_report(self):
        """生成综合测试报告"""
        report_data = {
            'test_run_info': {
                'timestamp': datetime.now().isoformat(),
                'duration': self.end_time - self.start_time if self.end_time and self.start_time else 0,
                'python_version': sys.version,
                'config_file': self.config_path
            },
            'summary': self._calculate_summary(),
            'detailed_results': self.results,
            'performance_analysis': self._analyze_performance(),
            'recommendations': self._generate_recommendations()
        }

        # 保存JSON报告
        json_report_path = f"tests/optimization_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_report_path, 'w') as f:
            json.dump(report_data, f, indent=2)

        # 生成Markdown报告
        markdown_report = self._generate_markdown_report(report_data)
        md_report_path = json_report_path.replace('.json', '.md')
        with open(md_report_path, 'w') as f:
            f.write(markdown_report)

        print(f"\n📊 Reports generated:")
        print(f"   - JSON: {json_report_path}")
        print(f"   - Markdown: {md_report_path}")

        # 打印总结
        self._print_final_summary(report_data)

    def _calculate_summary(self) -> Dict[str, Any]:
        """计算测试摘要"""
        total_tests = sum(r.get('tests_run', 0) for r in self.results.values())
        total_passed = sum(r.get('tests_passed', 0) for r in self.results.values())
        total_failed = sum(r.get('tests_failed', 0) for r in self.results.values())
        total_duration = sum(r.get('duration', 0) for r in self.results.values())

        return {
            'total_test_suites': len(self.results),
            'total_tests': total_tests,
            'total_passed': total_passed,
            'total_failed': total_failed,
            'total_skipped': sum(r.get('tests_skipped', 0) for r in self.results.values()),
            'success_rate': (total_passed / total_tests * 100) if total_tests > 0 else 0,
            'total_duration': total_duration,
            'overall_status': 'PASSED' if total_failed == 0 else 'FAILED'
        }

    def _analyze_performance(self) -> Dict[str, Any]:
        """分析性能测试结果"""
        analysis = {
            'parallel_execution': 'Not tested',
            'performance_benchmarks': 'Not tested',
            'resource_efficiency': 'Not tested',
            'agent_selection_accuracy': 'Not tested'
        }

        # 分析并行执行结果
        if 'parallel_execution' in self.results:
            pe_result = self.results['parallel_execution']
            if pe_result.get('status') == 'passed':
                analysis['parallel_execution'] = 'PASSED - Parallel execution capabilities verified'
            else:
                analysis['parallel_execution'] = f"FAILED - {pe_result.get('error', 'Unknown error')}"

        # 分析性能基准结果
        if 'performance_benchmarks' in self.results:
            pb_result = self.results['performance_benchmarks']
            if pb_result.get('status') == 'passed':
                analysis['performance_benchmarks'] = 'PASSED - Performance thresholds met'
            else:
                analysis['performance_benchmarks'] = f"FAILED - Performance issues detected"

        # 分析资源监控结果
        if 'resource_monitoring' in self.results:
            rm_result = self.results['resource_monitoring']
            if rm_result.get('status') == 'passed':
                analysis['resource_efficiency'] = 'PASSED - Resource usage within limits'
            else:
                analysis['resource_efficiency'] = f"FAILED - Resource usage exceeded limits"

        # 分析agent选择准确性
        if 'agent_selection' in self.results:
            as_result = self.results['agent_selection']
            if as_result.get('status') == 'passed':
                analysis['agent_selection_accuracy'] = 'PASSED - Agent selection accuracy acceptable'
            else:
                analysis['agent_selection_accuracy'] = f"FAILED - Agent selection needs improvement"

        return analysis

    def _generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []

        # 基于测试结果生成建议
        for suite_name, result in self.results.items():
            if result.get('status') != 'passed':
                if suite_name == 'parallel_execution':
                    recommendations.append("优化并行执行机制，检查线程池配置和任务调度算法")
                elif suite_name == 'performance_benchmarks':
                    recommendations.append("优化性能瓶颈，考虑缓存策略和算法优化")
                elif suite_name == 'resource_monitoring':
                    recommendations.append("优化资源使用，检查内存泄漏和CPU密集型操作")
                elif suite_name == 'agent_selection':
                    recommendations.append("改进agent选择算法，优化关键词匹配和上下文分析")

        if not recommendations:
            recommendations.append("所有测试通过，系统性能表现良好")

        return recommendations

    def _generate_markdown_report(self, report_data: Dict[str, Any]) -> str:
        """生成Markdown格式报告"""
        md = f"""# Perfect21 优化验证测试报告

## 测试摘要

- **测试时间**: {report_data['test_run_info']['timestamp']}
- **总执行时间**: {report_data['test_run_info']['duration']:.2f}秒
- **测试套件数**: {report_data['summary']['total_test_suites']}
- **总测试数**: {report_data['summary']['total_tests']}
- **通过数**: {report_data['summary']['total_passed']}
- **失败数**: {report_data['summary']['total_failed']}
- **成功率**: {report_data['summary']['success_rate']:.2f}%
- **整体状态**: {report_data['summary']['overall_status']}

## 详细结果

"""

        # 添加每个测试套件的详细结果
        for suite_name, result in report_data['detailed_results'].items():
            status_emoji = '✅' if result.get('status') == 'passed' else '❌'
            md += f"### {status_emoji} {suite_name.replace('_', ' ').title()}\n\n"
            md += f"- **状态**: {result.get('status', 'unknown')}\n"
            md += f"- **测试数**: {result.get('tests_run', 0)}\n"
            md += f"- **通过数**: {result.get('tests_passed', 0)}\n"
            md += f"- **失败数**: {result.get('tests_failed', 0)}\n"
            md += f"- **执行时间**: {result.get('duration', 0):.2f}秒\n\n"

            if result.get('error'):
                md += f"**错误信息**: {result['error']}\n\n"

        # 添加性能分析
        md += "## 性能分析\n\n"
        for metric, status in report_data['performance_analysis'].items():
            status_emoji = '✅' if 'PASSED' in status else '❌' if 'FAILED' in status else '⏸️'
            md += f"- {status_emoji} **{metric.replace('_', ' ').title()}**: {status}\n"

        # 添加改进建议
        md += "\n## 改进建议\n\n"
        for i, recommendation in enumerate(report_data['recommendations'], 1):
            md += f"{i}. {recommendation}\n"

        md += f"\n---\n*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"

        return md

    def _print_final_summary(self, report_data: Dict[str, Any]):
        """打印最终摘要"""
        print("\n" + "="*60)
        print("📋 PERFECT21 OPTIMIZATION VALIDATION SUMMARY")
        print("="*60)

        summary = report_data['summary']
        status_emoji = '✅' if summary['overall_status'] == 'PASSED' else '❌'

        print(f"{status_emoji} Overall Status: {summary['overall_status']}")
        print(f"📊 Tests: {summary['total_passed']}/{summary['total_tests']} passed ({summary['success_rate']:.1f}%)")
        print(f"⏱️  Duration: {summary['total_duration']:.2f}s")

        print("\n🎯 Key Performance Indicators:")
        for metric, status in report_data['performance_analysis'].items():
            status_emoji = '✅' if 'PASSED' in status else '❌' if 'FAILED' in status else '⏸️'
            metric_name = metric.replace('_', ' ').title()
            print(f"   {status_emoji} {metric_name}")

        if report_data['recommendations']:
            print("\n💡 Recommendations:")
            for rec in report_data['recommendations'][:3]:  # 显示前3个建议
                print(f"   • {rec}")

        print("\n" + "="*60)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Run Perfect21 optimization validation tests')
    parser.add_argument('--config', '-c', help='Configuration file path')
    parser.add_argument('--filter', '-f', help='Filter tests by name')
    parser.add_argument('--quiet', '-q', action='store_true', help='Reduce output verbosity')

    args = parser.parse_args()

    runner = OptimizationTestRunner(config_path=args.config)

    try:
        results = runner.run_all_tests(test_filter=args.filter)

        # 返回适当的退出码
        overall_status = runner._calculate_summary()['overall_status']
        sys.exit(0 if overall_status == 'PASSED' else 1)

    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()