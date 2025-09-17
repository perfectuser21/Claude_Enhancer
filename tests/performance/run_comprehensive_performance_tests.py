#!/usr/bin/env python3
"""
Perfect21 综合性能测试执行器
协调运行所有性能测试并生成统一报告
"""

import os
import sys
import json
import time
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from perfect21_performance_test_suite import Perfect21PerformanceTestSuite
from database_performance_test import DatabasePerformanceTester

class ComprehensivePerformanceTestRunner:
    """综合性能测试执行器"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # 创建结果目录
        self.results_dir = Path("tests/performance/results")
        self.results_dir.mkdir(exist_ok=True)

        # 测试组件
        self.system_tester = Perfect21PerformanceTestSuite()
        self.db_tester = DatabasePerformanceTester()

        # 测试结果存储
        self.test_results = {}
        self.test_start_time = None

    def run_all_performance_tests(self) -> Dict[str, Any]:
        """运行所有性能测试"""
        print("🎯 启动Perfect21综合性能测试套件")
        print("=" * 80)

        self.test_start_time = datetime.now()

        try:
            # 1. 系统性能测试
            print("\n🚀 第一部分：系统性能测试")
            print("-" * 50)
            self.test_results['system_performance'] = self._run_system_performance_tests()

            # 2. 数据库性能测试
            print("\n🗄️  第二部分：数据库性能测试")
            print("-" * 50)
            self.test_results['database_performance'] = self._run_database_performance_tests()

            # 3. API负载测试 (K6)
            print("\n📡 第三部分：API负载测试")
            print("-" * 50)
            self.test_results['api_load_tests'] = self._run_k6_load_tests()

            # 4. 集成性能测试
            print("\n🔗 第四部分：集成性能测试")
            print("-" * 50)
            self.test_results['integration_performance'] = self._run_integration_performance_tests()

            # 5. 生成综合报告
            print("\n📊 第五部分：生成综合报告")
            print("-" * 50)
            comprehensive_report = self._generate_comprehensive_report()

            print("\n✅ 所有性能测试完成！")
            self._print_test_summary(comprehensive_report)

            return comprehensive_report

        except Exception as e:
            self.logger.error(f"性能测试执行失败: {e}")
            raise

    def _run_system_performance_tests(self) -> Dict[str, Any]:
        """运行系统性能测试"""
        try:
            print("执行工作流编排器和并行管理器性能测试...")
            system_results = self.system_tester.run_comprehensive_performance_test()

            print("✅ 系统性能测试完成")
            return {
                'status': 'completed',
                'results': system_results,
                'test_duration': (datetime.now() - self.test_start_time).total_seconds()
            }

        except Exception as e:
            self.logger.error(f"系统性能测试失败: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'test_duration': (datetime.now() - self.test_start_time).total_seconds()
            }

    def _run_database_performance_tests(self) -> Dict[str, Any]:
        """运行数据库性能测试"""
        try:
            print("执行数据库查询、插入、更新和并发性能测试...")
            db_results = self.db_tester.run_comprehensive_database_tests()

            print("✅ 数据库性能测试完成")
            return {
                'status': 'completed',
                'results': db_results,
                'test_duration': (datetime.now() - self.test_start_time).total_seconds()
            }

        except Exception as e:
            self.logger.error(f"数据库性能测试失败: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'test_duration': (datetime.now() - self.test_start_time).total_seconds()
            }

    def _run_k6_load_tests(self) -> Dict[str, Any]:
        """运行K6负载测试"""
        try:
            # 检查K6是否安装
            k6_available = self._check_k6_installation()
            if not k6_available:
                return {
                    'status': 'skipped',
                    'reason': 'K6 not installed',
                    'message': 'K6负载测试被跳过，请安装K6以执行API负载测试'
                }

            print("执行K6 API负载测试...")

            # 检查API服务是否运行
            api_available = self._check_api_service()
            if not api_available:
                return {
                    'status': 'skipped',
                    'reason': 'API service not available',
                    'message': 'API服务未运行，跳过负载测试'
                }

            # 运行K6测试
            k6_script_path = Path(__file__).parent / "k6_load_test.js"
            k6_results = self._execute_k6_test(str(k6_script_path))

            print("✅ K6负载测试完成")
            return {
                'status': 'completed',
                'results': k6_results,
                'test_duration': (datetime.now() - self.test_start_time).total_seconds()
            }

        except Exception as e:
            self.logger.error(f"K6负载测试失败: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'test_duration': (datetime.now() - self.test_start_time).total_seconds()
            }

    def _run_integration_performance_tests(self) -> Dict[str, Any]:
        """运行集成性能测试"""
        try:
            print("执行端到端集成性能测试...")

            integration_results = {
                'workflow_to_database_integration': self._test_workflow_database_integration(),
                'api_to_workflow_integration': self._test_api_workflow_integration(),
                'end_to_end_workflow': self._test_end_to_end_workflow_performance()
            }

            print("✅ 集成性能测试完成")
            return {
                'status': 'completed',
                'results': integration_results,
                'test_duration': (datetime.now() - self.test_start_time).total_seconds()
            }

        except Exception as e:
            self.logger.error(f"集成性能测试失败: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'test_duration': (datetime.now() - self.test_start_time).total_seconds()
            }

    def _test_workflow_database_integration(self) -> Dict[str, Any]:
        """测试工作流与数据库集成性能"""
        print("  测试工作流状态持久化性能...")

        start_time = time.time()
        test_workflows = 100
        successful_operations = 0

        try:
            for i in range(test_workflows):
                # 创建工作流
                workflow_config = self._create_integration_test_workflow(f"integration_test_{i}")

                # 测试完整的创建、执行、状态更新流程
                load_result = self.system_tester.orchestrator.load_workflow(workflow_config)
                if load_result['success']:
                    # 模拟执行和状态更新
                    self.system_tester.orchestrator._save_execution_state()
                    successful_operations += 1

                if i % 20 == 0:
                    print(f"    已测试 {i} 个工作流...")

            duration = time.time() - start_time
            throughput = successful_operations / duration

            return {
                'total_workflows': test_workflows,
                'successful_operations': successful_operations,
                'test_duration': duration,
                'throughput': throughput,
                'success_rate': successful_operations / test_workflows
            }

        except Exception as e:
            return {'error': str(e)}

    def _test_api_workflow_integration(self) -> Dict[str, Any]:
        """测试API与工作流集成性能"""
        print("  测试API调用到工作流执行的完整链路...")

        # 模拟API请求处理性能
        start_time = time.time()
        api_requests = 50
        successful_requests = 0

        try:
            for i in range(api_requests):
                # 模拟API请求处理
                request_start = time.time()

                # 创建工作流（模拟API调用）
                workflow_config = self._create_integration_test_workflow(f"api_integration_{i}")
                load_result = self.system_tester.orchestrator.load_workflow(workflow_config)

                if load_result['success']:
                    # 模拟阶段执行
                    stages = list(workflow_config['stages'])
                    if stages:
                        stage_result = self.system_tester.orchestrator.execute_stage(stages[0]['name'])
                        if stage_result['success']:
                            successful_requests += 1

                if i % 10 == 0:
                    print(f"    已处理 {i} 个API请求...")

            duration = time.time() - start_time
            throughput = successful_requests / duration

            return {
                'total_requests': api_requests,
                'successful_requests': successful_requests,
                'test_duration': duration,
                'throughput': throughput,
                'avg_response_time': duration / api_requests
            }

        except Exception as e:
            return {'error': str(e)}

    def _test_end_to_end_workflow_performance(self) -> Dict[str, Any]:
        """测试端到端工作流性能"""
        print("  测试完整工作流生命周期性能...")

        start_time = time.time()
        workflows = 20
        completed_workflows = 0

        workflow_metrics = []

        try:
            for i in range(workflows):
                workflow_start = time.time()

                # 创建复杂工作流
                workflow_config = self._create_complex_integration_workflow(f"e2e_test_{i}")

                # 执行完整生命周期
                load_result = self.system_tester.orchestrator.load_workflow(workflow_config)
                if load_result['success']:
                    # 执行所有阶段
                    stages = list(workflow_config['stages'])
                    stage_execution_times = []

                    for stage_config in stages:
                        stage_start = time.time()
                        stage_result = self.system_tester.orchestrator.execute_stage(stage_config['name'])
                        stage_duration = time.time() - stage_start
                        stage_execution_times.append(stage_duration)

                        if not stage_result['success']:
                            break

                    workflow_duration = time.time() - workflow_start
                    workflow_metrics.append({
                        'workflow_id': f"e2e_test_{i}",
                        'total_duration': workflow_duration,
                        'stage_count': len(stages),
                        'stage_execution_times': stage_execution_times,
                        'avg_stage_time': sum(stage_execution_times) / len(stage_execution_times) if stage_execution_times else 0
                    })

                    completed_workflows += 1

                if i % 5 == 0:
                    print(f"    已完成 {i} 个端到端工作流...")

            total_duration = time.time() - start_time

            # 计算统计指标
            if workflow_metrics:
                avg_workflow_duration = sum(w['total_duration'] for w in workflow_metrics) / len(workflow_metrics)
                max_workflow_duration = max(w['total_duration'] for w in workflow_metrics)
                min_workflow_duration = min(w['total_duration'] for w in workflow_metrics)
            else:
                avg_workflow_duration = max_workflow_duration = min_workflow_duration = 0

            return {
                'total_workflows': workflows,
                'completed_workflows': completed_workflows,
                'test_duration': total_duration,
                'success_rate': completed_workflows / workflows,
                'avg_workflow_duration': avg_workflow_duration,
                'max_workflow_duration': max_workflow_duration,
                'min_workflow_duration': min_workflow_duration,
                'workflow_metrics': workflow_metrics
            }

        except Exception as e:
            return {'error': str(e)}

    def _check_k6_installation(self) -> bool:
        """检查K6是否安装"""
        try:
            result = subprocess.run(['k6', 'version'], capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def _check_api_service(self) -> bool:
        """检查API服务是否可用"""
        try:
            import requests
            response = requests.get('http://localhost:8000/health', timeout=5)
            return response.status_code == 200
        except:
            return False

    def _execute_k6_test(self, script_path: str) -> Dict[str, Any]:
        """执行K6测试"""
        try:
            # 运行K6负载测试
            cmd = [
                'k6', 'run',
                '--out', f'json={self.results_dir}/k6_results.json',
                '--env', 'BASE_URL=http://localhost:8000',
                '--env', 'TEST_TYPE=load',
                script_path
            ]

            print(f"执行K6命令: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800  # 30分钟超时
            )

            if result.returncode == 0:
                # 解析K6结果
                k6_output = result.stdout
                return {
                    'status': 'success',
                    'output': k6_output,
                    'stderr': result.stderr,
                    'results_file': f'{self.results_dir}/k6_results.json'
                }
            else:
                return {
                    'status': 'failed',
                    'error': result.stderr,
                    'output': result.stdout
                }

        except subprocess.TimeoutExpired:
            return {
                'status': 'timeout',
                'error': 'K6 test timed out after 30 minutes'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    def _create_integration_test_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """创建集成测试工作流配置"""
        return {
            'name': f'Integration Test Workflow {workflow_id}',
            'global_context': {'integration_test': True, 'workflow_id': workflow_id},
            'stages': [
                {
                    'name': 'setup',
                    'description': '初始化阶段',
                    'execution_mode': 'sequential'
                },
                {
                    'name': 'execution',
                    'description': '执行阶段',
                    'execution_mode': 'parallel',
                    'depends_on': ['setup']
                }
            ]
        }

    def _create_complex_integration_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """创建复杂的集成测试工作流配置"""
        return {
            'name': f'Complex Integration Workflow {workflow_id}',
            'global_context': {
                'integration_test': True,
                'complexity': 'high',
                'workflow_id': workflow_id
            },
            'stages': [
                {
                    'name': 'requirements',
                    'description': '需求分析',
                    'execution_mode': 'parallel'
                },
                {
                    'name': 'design',
                    'description': '设计阶段',
                    'execution_mode': 'sequential',
                    'depends_on': ['requirements'],
                    'sync_point': {
                        'type': 'validation',
                        'validation_criteria': {'tasks_completed': '> 0'}
                    }
                },
                {
                    'name': 'implementation',
                    'description': '实现阶段',
                    'execution_mode': 'parallel',
                    'depends_on': ['design']
                },
                {
                    'name': 'testing',
                    'description': '测试阶段',
                    'execution_mode': 'sequential',
                    'depends_on': ['implementation'],
                    'quality_gate': {
                        'checklist': 'unit_tests,integration_tests',
                        'must_pass': True
                    }
                }
            ]
        }

    def _generate_comprehensive_report(self) -> Dict[str, Any]:
        """生成综合性能测试报告"""
        test_end_time = datetime.now()
        total_test_duration = (test_end_time - self.test_start_time).total_seconds()

        report = {
            'test_metadata': {
                'test_start_time': self.test_start_time.isoformat(),
                'test_end_time': test_end_time.isoformat(),
                'total_test_duration': total_test_duration,
                'test_environment': self._get_test_environment_info()
            },
            'test_results': self.test_results,
            'performance_summary': self._calculate_overall_performance_summary(),
            'bottleneck_analysis': self._analyze_performance_bottlenecks(),
            'recommendations': self._generate_comprehensive_recommendations(),
            'executive_summary': self._generate_executive_summary()
        }

        # 保存综合报告
        self._save_comprehensive_report(report)

        return report

    def _get_test_environment_info(self) -> Dict[str, Any]:
        """获取测试环境信息"""
        import platform
        import psutil

        return {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'memory_total_gb': psutil.virtual_memory().total / 1024 / 1024 / 1024,
            'disk_space_gb': psutil.disk_usage('/').total / 1024 / 1024 / 1024
        }

    def _calculate_overall_performance_summary(self) -> Dict[str, Any]:
        """计算整体性能摘要"""
        summary = {}

        # 系统性能摘要
        if 'system_performance' in self.test_results and self.test_results['system_performance']['status'] == 'completed':
            system_results = self.test_results['system_performance']['results']
            if 'performance_scores' in system_results:
                summary['system_performance_score'] = system_results['performance_scores'].get('overall', 0)

        # 数据库性能摘要
        if 'database_performance' in self.test_results and self.test_results['database_performance']['status'] == 'completed':
            db_results = self.test_results['database_performance']['results']
            if 'performance_summary' in db_results and 'overall' in db_results['performance_summary']:
                summary['database_performance_score'] = db_results['performance_summary']['overall'].get('performance_score', 0)

        # API性能摘要
        if 'api_load_tests' in self.test_results and self.test_results['api_load_tests']['status'] == 'completed':
            summary['api_load_test_status'] = 'completed'
        else:
            summary['api_load_test_status'] = 'failed_or_skipped'

        # 集成性能摘要
        if 'integration_performance' in self.test_results and self.test_results['integration_performance']['status'] == 'completed':
            integration_results = self.test_results['integration_performance']['results']
            e2e_results = integration_results.get('end_to_end_workflow', {})
            summary['integration_success_rate'] = e2e_results.get('success_rate', 0)

        # 计算总体评分
        scores = []
        if 'system_performance_score' in summary:
            scores.append(summary['system_performance_score'])
        if 'database_performance_score' in summary:
            scores.append(summary['database_performance_score'])
        if summary.get('integration_success_rate', 0) > 0:
            scores.append(summary['integration_success_rate'] * 100)

        if scores:
            summary['overall_performance_score'] = sum(scores) / len(scores)
        else:
            summary['overall_performance_score'] = 0

        return summary

    def _analyze_performance_bottlenecks(self) -> List[Dict[str, Any]]:
        """分析性能瓶颈"""
        bottlenecks = []

        # 分析系统性能瓶颈
        if 'system_performance' in self.test_results:
            system_results = self.test_results['system_performance']
            if system_results['status'] == 'completed':
                # 检查负载测试结果
                load_tests = system_results['results'].get('load_tests', {})
                if 'results' in load_tests:
                    for result in load_tests['results']:
                        if hasattr(result, 'bottlenecks') and result.bottlenecks:
                            bottlenecks.extend([
                                {
                                    'category': 'system_load',
                                    'severity': 'medium',
                                    'description': bottleneck,
                                    'affected_component': 'workflow_orchestrator'
                                }
                                for bottleneck in result.bottlenecks
                            ])

        # 分析数据库性能瓶颈
        if 'database_performance' in self.test_results:
            db_results = self.test_results['database_performance']
            if db_results['status'] == 'completed':
                perf_summary = db_results['results'].get('performance_summary', {})
                if 'overall' in perf_summary:
                    overall = perf_summary['overall']
                    if overall.get('avg_response_time', 0) > 0.1:
                        bottlenecks.append({
                            'category': 'database_performance',
                            'severity': 'high' if overall['avg_response_time'] > 0.5 else 'medium',
                            'description': f"数据库平均响应时间过高: {overall['avg_response_time']:.3f}s",
                            'affected_component': 'database'
                        })

        return bottlenecks

    def _generate_comprehensive_recommendations(self) -> List[str]:
        """生成综合优化建议"""
        recommendations = []

        # 基于性能摘要生成建议
        summary = self._calculate_overall_performance_summary()

        if summary.get('overall_performance_score', 0) < 70:
            recommendations.append("整体性能需要改进，建议优先处理关键性能瓶颈")

        if summary.get('system_performance_score', 0) < 60:
            recommendations.append("工作流编排器性能较低，考虑优化任务调度和资源管理")

        if summary.get('database_performance_score', 0) < 60:
            recommendations.append("数据库性能需要优化，建议检查索引策略和查询优化")

        if summary.get('integration_success_rate', 0) < 0.9:
            recommendations.append("集成测试成功率较低，需要改进错误处理和重试机制")

        # 通用建议
        recommendations.extend([
            "建议实施持续性能监控，及时发现性能回归",
            "考虑实现性能预算，确保新功能不影响整体性能",
            "定期进行性能基准测试，跟踪性能趋势",
            "优化关键路径上的组件，提高用户体验"
        ])

        return recommendations

    def _generate_executive_summary(self) -> Dict[str, Any]:
        """生成执行摘要"""
        summary = self._calculate_overall_performance_summary()
        bottlenecks = self._analyze_performance_bottlenecks()

        # 确定整体状态
        overall_score = summary.get('overall_performance_score', 0)
        if overall_score >= 80:
            status = 'excellent'
            status_description = '性能表现优秀'
        elif overall_score >= 60:
            status = 'good'
            status_description = '性能表现良好'
        elif overall_score >= 40:
            status = 'fair'
            status_description = '性能表现一般，需要改进'
        else:
            status = 'poor'
            status_description = '性能表现较差，需要立即优化'

        return {
            'overall_status': status,
            'status_description': status_description,
            'performance_score': overall_score,
            'total_bottlenecks': len(bottlenecks),
            'critical_bottlenecks': len([b for b in bottlenecks if b.get('severity') == 'high']),
            'key_metrics': {
                'system_performance': summary.get('system_performance_score', 0),
                'database_performance': summary.get('database_performance_score', 0),
                'integration_success_rate': summary.get('integration_success_rate', 0)
            },
            'priority_actions': self._get_priority_actions(bottlenecks)
        }

    def _get_priority_actions(self, bottlenecks: List[Dict]) -> List[str]:
        """获取优先行动项"""
        actions = []

        high_severity = [b for b in bottlenecks if b.get('severity') == 'high']
        if high_severity:
            actions.append(f"立即处理 {len(high_severity)} 个高严重性性能问题")

        medium_severity = [b for b in bottlenecks if b.get('severity') == 'medium']
        if medium_severity:
            actions.append(f"计划处理 {len(medium_severity)} 个中等严重性性能问题")

        if not bottlenecks:
            actions.append("继续监控性能指标，保持当前性能水平")

        return actions

    def _save_comprehensive_report(self, report: Dict[str, Any]):
        """保存综合性能报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSON详细报告
        json_filename = self.results_dir / f"comprehensive_performance_report_{timestamp}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        # HTML报告
        html_filename = self.results_dir / f"performance_dashboard_{timestamp}.html"
        self._generate_html_report(report, html_filename)

        # 文本摘要
        txt_filename = self.results_dir / f"performance_executive_summary_{timestamp}.txt"
        self._generate_text_summary(report, txt_filename)

        print(f"\n📄 综合性能测试报告已生成:")
        print(f"  • JSON详细报告: {json_filename}")
        print(f"  • HTML可视化报告: {html_filename}")
        print(f"  • 执行摘要: {txt_filename}")

    def _generate_html_report(self, report: Dict[str, Any], filename: Path):
        """生成HTML可视化报告"""
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Perfect21 性能测试报告</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 3px solid #007acc;
        }}
        .score-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin: 20px 0;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .metric-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #007acc;
        }}
        .status-excellent {{ color: #28a745; }}
        .status-good {{ color: #17a2b8; }}
        .status-fair {{ color: #ffc107; }}
        .status-poor {{ color: #dc3545; }}
        .bottleneck {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
        }}
        .recommendations {{
            background: #e7f3ff;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 Perfect21 性能测试报告</h1>
            <p>测试时间: {report['test_metadata']['test_start_time']} - {report['test_metadata']['test_end_time']}</p>
            <p>总测试时长: {report['test_metadata']['total_test_duration']:.1f} 秒</p>
        </div>

        <div class="score-card">
            <h2>整体性能评分</h2>
            <h1 class="status-{report['executive_summary']['overall_status']}">{report['executive_summary']['performance_score']:.1f}/100</h1>
            <p>{report['executive_summary']['status_description']}</p>
        </div>

        <div class="metrics-grid">
            <div class="metric-card">
                <h3>🚀 系统性能</h3>
                <p><strong>{report['performance_summary'].get('system_performance_score', 'N/A')}</strong>/100</p>
                <p>工作流编排器和并行管理器性能</p>
            </div>
            <div class="metric-card">
                <h3>🗄️ 数据库性能</h3>
                <p><strong>{report['performance_summary'].get('database_performance_score', 'N/A')}</strong>/100</p>
                <p>数据查询、插入、更新性能</p>
            </div>
            <div class="metric-card">
                <h3>🔗 集成测试</h3>
                <p><strong>{report['performance_summary'].get('integration_success_rate', 0)*100:.1f}%</strong></p>
                <p>端到端集成测试成功率</p>
            </div>
            <div class="metric-card">
                <h3>📡 API负载测试</h3>
                <p><strong>{report['performance_summary'].get('api_load_test_status', 'N/A')}</strong></p>
                <p>API负载测试执行状态</p>
            </div>
        </div>

        <h2>🔍 性能瓶颈分析</h2>
        <div>
            总计发现 <strong>{report['executive_summary']['total_bottlenecks']}</strong> 个性能问题，
            其中 <strong>{report['executive_summary']['critical_bottlenecks']}</strong> 个为高严重性。
        </div>
        {self._format_bottlenecks_html(report.get('bottleneck_analysis', []))}

        <div class="recommendations">
            <h2>💡 优化建议</h2>
            <h3>优先行动项:</h3>
            <ul>
                {"".join(f"<li>{action}</li>" for action in report['executive_summary']['priority_actions'])}
            </ul>
            <h3>详细建议:</h3>
            <ul>
                {"".join(f"<li>{rec}</li>" for rec in report['recommendations'])}
            </ul>
        </div>
    </div>
</body>
</html>
        """

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)

    def _format_bottlenecks_html(self, bottlenecks: List[Dict]) -> str:
        """格式化瓶颈信息为HTML"""
        if not bottlenecks:
            return "<p>✅ 未发现明显的性能瓶颈</p>"

        html = ""
        for bottleneck in bottlenecks:
            severity_class = f"status-{bottleneck.get('severity', 'fair')}"
            html += f"""
            <div class="bottleneck">
                <strong class="{severity_class}">[{bottleneck.get('severity', 'unknown').upper()}]</strong>
                {bottleneck.get('description', 'No description')}
                <small>(组件: {bottleneck.get('affected_component', 'unknown')})</small>
            </div>
            """
        return html

    def _generate_text_summary(self, report: Dict[str, Any], filename: Path):
        """生成文本摘要报告"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("Perfect21 性能测试执行摘要\n")
            f.write("=" * 50 + "\n\n")

            # 执行摘要
            exec_summary = report['executive_summary']
            f.write(f"整体状态: {exec_summary['status_description']}\n")
            f.write(f"性能评分: {exec_summary['performance_score']:.1f}/100\n")
            f.write(f"测试时长: {report['test_metadata']['total_test_duration']:.1f}秒\n\n")

            # 关键指标
            f.write("关键性能指标:\n")
            f.write("-" * 30 + "\n")
            key_metrics = exec_summary['key_metrics']
            f.write(f"系统性能评分: {key_metrics['system_performance']:.1f}/100\n")
            f.write(f"数据库性能评分: {key_metrics['database_performance']:.1f}/100\n")
            f.write(f"集成测试成功率: {key_metrics['integration_success_rate']*100:.1f}%\n\n")

            # 优先行动项
            f.write("优先行动项:\n")
            f.write("-" * 30 + "\n")
            for action in exec_summary['priority_actions']:
                f.write(f"• {action}\n")

    def _print_test_summary(self, report: Dict[str, Any]):
        """打印测试摘要"""
        exec_summary = report['executive_summary']

        print(f"\n📊 性能测试摘要")
        print("=" * 50)
        print(f"整体性能评分: {exec_summary['performance_score']:.1f}/100")
        print(f"状态: {exec_summary['status_description']}")
        print(f"总测试时长: {report['test_metadata']['total_test_duration']:.1f}秒")

        print(f"\n🔍 发现问题:")
        print(f"• 总计性能问题: {exec_summary['total_bottlenecks']}个")
        print(f"• 高严重性问题: {exec_summary['critical_bottlenecks']}个")

        print(f"\n💡 下一步行动:")
        for action in exec_summary['priority_actions']:
            print(f"• {action}")

def main():
    """主函数：运行综合性能测试"""
    runner = ComprehensivePerformanceTestRunner()

    try:
        # 运行所有性能测试
        comprehensive_report = runner.run_all_performance_tests()

        return comprehensive_report

    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
        return None
    except Exception as e:
        print(f"\n❌ 性能测试失败: {e}")
        raise

if __name__ == "__main__":
    main()