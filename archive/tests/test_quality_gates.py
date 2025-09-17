#!/usr/bin/env python3
"""
Perfect21 质量门测试
==================

测试自动化质量门系统
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path

from features.quality_gates.quality_gate_engine import QualityGateEngine, QualityGateConfig
from features.quality_gates.ci_integration import CIIntegration


async def test_individual_gates():
    """测试各个质量门"""
    print("🔍 测试各个质量门...")

    config = QualityGateConfig()
    config.min_line_coverage = 70.0  # 降低要求用于测试
    config.max_complexity = 20      # 适度放宽

    engine = QualityGateEngine('.', config)

    # 测试代码质量门
    print("\n1. 测试代码质量门...")
    from features.quality_gates.code_quality_gate import CodeQualityGate
    code_gate = CodeQualityGate('.', config)
    code_result = await code_gate.check('test')
    print(f"   状态: {code_result.status.value}")
    print(f"   分数: {code_result.score:.1f}")
    print(f"   消息: {code_result.message}")

    # 测试安全门
    print("\n2. 测试安全门...")
    from features.quality_gates.security_gate import SecurityGate
    security_gate = SecurityGate('.', config)
    security_result = await security_gate.check('test')
    print(f"   状态: {security_result.status.value}")
    print(f"   分数: {security_result.score:.1f}")
    print(f"   消息: {security_result.message}")

    # 测试覆盖率门
    print("\n3. 测试覆盖率门...")
    from features.quality_gates.coverage_gate import CoverageGate
    coverage_gate = CoverageGate('.', config)
    coverage_result = await coverage_gate.check('test')
    print(f"   状态: {coverage_result.status.value}")
    print(f"   分数: {coverage_result.score:.1f}")
    print(f"   消息: {coverage_result.message}")

    # 测试性能门
    print("\n4. 测试性能门...")
    from features.quality_gates.performance_gate import PerformanceGate
    performance_gate = PerformanceGate('.', config)
    performance_result = await performance_gate.check('test')
    print(f"   状态: {performance_result.status.value}")
    print(f"   分数: {performance_result.score:.1f}")
    print(f"   消息: {performance_result.message}")

    # 测试架构门
    print("\n5. 测试架构门...")
    from features.quality_gates.architecture_gate import ArchitectureGate
    architecture_gate = ArchitectureGate('.', config)
    architecture_result = await architecture_gate.check('test')
    print(f"   状态: {architecture_result.status.value}")
    print(f"   分数: {architecture_result.score:.1f}")
    print(f"   消息: {architecture_result.message}")

    return {
        'code_quality': code_result,
        'security': security_result,
        'coverage': coverage_result,
        'performance': performance_result,
        'architecture': architecture_result
    }


async def test_quality_gate_engine():
    """测试质量门引擎"""
    print("\n🎯 测试质量门引擎...")

    config = QualityGateConfig()
    config.min_line_coverage = 70.0
    config.max_complexity = 20
    config.parallel_execution = True
    config.fail_fast = False

    engine = QualityGateEngine('.', config)

    # 测试快速检查
    print("\n1. 测试快速检查...")
    start_time = time.time()
    quick_results = await engine.run_quick_check()
    quick_time = time.time() - start_time

    print(f"   状态: {quick_results['status']}")
    print(f"   分数: {quick_results['score']:.1f}")
    print(f"   耗时: {quick_time:.2f}秒")
    print(f"   消息: {quick_results['message']}")

    # 测试完整检查
    print("\n2. 测试完整检查...")
    start_time = time.time()
    full_results = await engine.run_all_gates('test')
    full_time = time.time() - start_time

    overall = full_results.get('overall')
    print(f"   状态: {overall.status.value if overall else 'unknown'}")
    print(f"   分数: {overall.score:.1f if overall else 0}")
    print(f"   耗时: {full_time:.2f}秒")
    print(f"   执行的质量门: {len(full_results) - 1}")  # 减去overall

    # 生成报告
    print("\n3. 生成质量报告...")
    report = engine.generate_report(full_results)
    print(report)

    # 测试质量趋势
    print("\n4. 测试质量趋势...")
    trends = engine.get_quality_trends(days=7)
    print(f"   总执行次数: {trends.get('total_executions', 0)}")
    print(f"   常见违规: {list(trends.get('common_violations', {}).keys())[:3]}")

    return full_results


async def test_ci_integration():
    """测试CI/CD集成"""
    print("\n🚀 测试CI/CD集成...")

    ci = CIIntegration('.')

    # 测试Git hooks设置
    print("\n1. 测试Git hooks设置...")
    hooks_result = await ci.setup_pre_commit_hooks()
    print(f"   状态: {hooks_result['status']}")
    print(f"   消息: {hooks_result['message']}")
    if hooks_result['status'] == 'success':
        print(f"   安装的hooks: {hooks_result['hooks_installed']}")

    # 测试GitHub Actions生成
    print("\n2. 测试GitHub Actions工作流生成...")
    github_result = await ci.generate_github_actions_workflow()
    print(f"   状态: {github_result['status']}")
    print(f"   消息: {github_result['message']}")

    # 测试GitLab CI生成
    print("\n3. 测试GitLab CI配置生成...")
    gitlab_result = await ci.generate_gitlab_ci_config()
    print(f"   状态: {gitlab_result['status']}")
    print(f"   消息: {gitlab_result['message']}")

    # 测试持续监控设置
    print("\n4. 测试持续监控设置...")
    monitoring_result = await ci.setup_continuous_monitoring()
    print(f"   状态: {monitoring_result['status']}")
    print(f"   消息: {monitoring_result['message']}")

    # 测试质量仪表板
    print("\n5. 测试质量仪表板...")
    dashboard_result = await ci.create_quality_dashboard()
    print(f"   状态: {dashboard_result['status']}")
    print(f"   消息: {dashboard_result['message']}")

    return {
        'hooks': hooks_result,
        'github': github_result,
        'gitlab': gitlab_result,
        'monitoring': monitoring_result,
        'dashboard': dashboard_result
    }


async def test_quality_scenarios():
    """测试不同质量场景"""
    print("\n📋 测试不同质量场景...")

    config = QualityGateConfig()
    engine = QualityGateEngine('.', config)

    scenarios = [
        ('commit', '提交场景'),
        ('merge', '合并场景'),
        ('release', '发布场景'),
        ('performance_test', '性能测试场景')
    ]

    results = {}

    for context, description in scenarios:
        print(f"\n测试 {description} ({context})...")
        start_time = time.time()

        try:
            scenario_results = await engine.run_all_gates(context)
            execution_time = time.time() - start_time

            overall = scenario_results.get('overall')
            if overall:
                print(f"   状态: {overall.status.value}")
                print(f"   分数: {overall.score:.1f}")
                print(f"   耗时: {execution_time:.2f}秒")
                print(f"   违规数: {len(overall.violations)}")

                results[context] = {
                    'status': overall.status.value,
                    'score': overall.score,
                    'execution_time': execution_time,
                    'violations': len(overall.violations)
                }
            else:
                results[context] = {'error': 'No overall result'}

        except Exception as e:
            print(f"   错误: {str(e)}")
            results[context] = {'error': str(e)}

    return results


async def test_configuration_options():
    """测试配置选项"""
    print("\n⚙️  测试配置选项...")

    # 测试严格配置
    print("\n1. 测试严格配置...")
    strict_config = QualityGateConfig()
    strict_config.min_line_coverage = 95.0
    strict_config.max_complexity = 5
    strict_config.max_security_issues = 0
    strict_config.fail_fast = True

    strict_engine = QualityGateEngine('.', strict_config)
    strict_results = await strict_engine.run_quick_check()
    print(f"   严格模式状态: {strict_results['status']}")
    print(f"   严格模式分数: {strict_results['score']:.1f}")

    # 测试宽松配置
    print("\n2. 测试宽松配置...")
    lenient_config = QualityGateConfig()
    lenient_config.min_line_coverage = 50.0
    lenient_config.max_complexity = 50
    lenient_config.max_security_issues = 10
    lenient_config.fail_fast = False

    lenient_engine = QualityGateEngine('.', lenient_config)
    lenient_results = await lenient_engine.run_quick_check()
    print(f"   宽松模式状态: {lenient_results['status']}")
    print(f"   宽松模式分数: {lenient_results['score']:.1f}")

    return {
        'strict': strict_results,
        'lenient': lenient_results
    }


async def generate_test_report(results):
    """生成测试报告"""
    print("\n📊 生成测试报告...")

    report = {
        'timestamp': datetime.now().isoformat(),
        'test_results': results,
        'summary': {
            'total_tests': 5,
            'passed_tests': 0,
            'failed_tests': 0
        }
    }

    # 统计测试结果
    for test_name, test_result in results.items():
        if isinstance(test_result, dict) and not test_result.get('error'):
            report['summary']['passed_tests'] += 1
        else:
            report['summary']['failed_tests'] += 1

    # 保存报告
    report_file = Path('.perfect21/quality_gates_test_report.json')
    report_file.parent.mkdir(exist_ok=True)

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"✅ 测试报告已保存: {report_file}")

    # 生成HTML报告
    html_report = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Perfect21 质量门测试报告</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: #2196F3; color: white; padding: 20px; border-radius: 8px; }}
        .summary {{ background: #f5f5f5; padding: 15px; margin: 20px 0; border-radius: 5px; }}
        .test-result {{ background: white; border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
        .passed {{ border-left: 4px solid #4caf50; }}
        .failed {{ border-left: 4px solid #f44336; }}
        .code {{ background: #f8f8f8; padding: 10px; font-family: monospace; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 Perfect21 质量门测试报告</h1>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="summary">
        <h2>📋 测试摘要</h2>
        <p>总测试数: {report['summary']['total_tests']}</p>
        <p>通过: {report['summary']['passed_tests']}</p>
        <p>失败: {report['summary']['failed_tests']}</p>
        <p>成功率: {(report['summary']['passed_tests'] / report['summary']['total_tests'] * 100):.1f}%</p>
    </div>
    """

    for test_name, test_result in results.items():
        status_class = 'passed' if not test_result.get('error') else 'failed'
        html_report += f"""
    <div class="test-result {status_class}">
        <h3>{test_name}</h3>
        <div class="code">{json.dumps(test_result, indent=2, ensure_ascii=False)}</div>
    </div>
        """

    html_report += """
</body>
</html>
    """

    html_file = Path('.perfect21/quality_gates_test_report.html')
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_report)

    print(f"🌐 HTML报告已保存: {html_file}")
    print(f"   在浏览器中打开: file://{html_file.absolute()}")

    return report


async def main():
    """主测试函数"""
    print("🚀 开始Perfect21质量门测试")
    print("=" * 60)

    results = {}

    try:
        # 1. 测试各个质量门
        results['individual_gates'] = await test_individual_gates()

        # 2. 测试质量门引擎
        results['gate_engine'] = await test_quality_gate_engine()

        # 3. 测试CI/CD集成
        results['ci_integration'] = await test_ci_integration()

        # 4. 测试不同场景
        results['scenarios'] = await test_quality_scenarios()

        # 5. 测试配置选项
        results['configurations'] = await test_configuration_options()

        # 生成测试报告
        report = await generate_test_report(results)

        print("\n" + "=" * 60)
        print("🎉 测试完成!")
        print(f"📊 通过: {report['summary']['passed_tests']}/{report['summary']['total_tests']}")

        if report['summary']['failed_tests'] > 0:
            print("⚠️  请检查失败的测试并修复问题")
            return 1
        else:
            print("✅ 所有测试通过!")
            return 0

    except Exception as e:
        print(f"\n❌ 测试执行失败: {str(e)}")
        return 1


if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)