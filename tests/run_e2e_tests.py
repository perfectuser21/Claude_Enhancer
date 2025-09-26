#!/usr/bin/env python3
"""
Claude Enhancer 5.1 端到端测试执行器
支持不同测试模式和配置选项
"""

import os
import sys
import argparse
import json
from pathlib import Path
from e2e_test_framework import E2ETestFramework

def main():
    parser = argparse.ArgumentParser(
        description="Claude Enhancer 5.1 端到端测试执行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
测试模式说明:
  full         - 完整测试套件（默认）
  workflow     - 仅工作流测试（Phase 0-7）
  agents       - 仅Agent协作测试
  git          - 仅Git集成测试
  hooks        - 仅Hook触发测试
  recovery     - 仅错误恢复测试
  scenarios    - 仅用户场景测试
  performance  - 仅性能压力测试
  concurrent   - 仅并发执行测试

示例:
  python run_e2e_tests.py                    # 运行完整测试
  python run_e2e_tests.py --mode workflow    # 仅测试工作流
  python run_e2e_tests.py --mode agents --verbose    # 详细模式测试Agent
  python run_e2e_tests.py --quick            # 快速测试模式
  python run_e2e_tests.py --stress           # 压力测试模式
        """
    )

    parser.add_argument(
        "--mode", "-m",
        choices=["full", "workflow", "agents", "git", "hooks", "recovery", "scenarios", "performance", "concurrent"],
        default="full",
        help="测试模式（默认: full）"
    )

    parser.add_argument(
        "--project-path", "-p",
        default="/home/xx/dev/Claude Enhancer 5.0",
        help="项目路径（默认: /home/xx/dev/Claude Enhancer 5.0）"
    )

    parser.add_argument(
        "--output", "-o",
        help="输出报告文件路径"
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出模式"
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="快速测试模式（跳过耗时测试）"
    )

    parser.add_argument(
        "--stress",
        action="store_true",
        help="压力测试模式（增加测试强度）"
    )

    parser.add_argument(
        "--parallel",
        type=int,
        default=4,
        help="并发测试线程数（默认: 4）"
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=30,
        help="单个测试超时时间（秒，默认: 30）"
    )

    parser.add_argument(
        "--config",
        help="自定义配置文件路径"
    )

    args = parser.parse_args()

    # 创建测试框架实例
    framework = E2ETestFramework(args.project_path)

    # 应用配置
    if args.config and Path(args.config).exists():
        with open(args.config, 'r', encoding='utf-8') as f:
            custom_config = json.load(f)
            framework.test_config.update(custom_config)

    # 更新配置
    framework.test_config.update({
        "timeout": args.timeout,
        "parallel_tests": args.parallel,
        "verbose": args.verbose,
        "quick_mode": args.quick,
        "stress_mode": args.stress
    })

    print("🚀 启动Claude Enhancer 5.1端到端测试")
    print("="*60)
    print(f"测试模式: {args.mode}")
    print(f"项目路径: {args.project_path}")
    print(f"并发数: {args.parallel}")
    print(f"超时: {args.timeout}秒")
    if args.quick:
        print("🏃 快速模式: 启用")
    if args.stress:
        print("💪 压力模式: 启用")
    print("="*60)

    # 执行测试
    if args.mode == "full":
        report = framework.run_all_tests()
    elif args.mode == "workflow":
        framework.test_results = framework.test_complete_workflow()
        report = framework.generate_test_report(sum(r.duration for r in framework.test_results))
    elif args.mode == "agents":
        framework.test_results = framework.test_agent_collaboration()
        report = framework.generate_test_report(sum(r.duration for r in framework.test_results))
    elif args.mode == "git":
        framework.test_results = framework.test_git_integration()
        report = framework.generate_test_report(sum(r.duration for r in framework.test_results))
    elif args.mode == "hooks":
        framework.test_results = framework.test_hook_triggering()
        report = framework.generate_test_report(sum(r.duration for r in framework.test_results))
    elif args.mode == "recovery":
        framework.test_results = framework.test_error_recovery()
        report = framework.generate_test_report(sum(r.duration for r in framework.test_results))
    elif args.mode == "scenarios":
        framework.test_results = framework.test_user_scenarios()
        report = framework.generate_test_report(sum(r.duration for r in framework.test_results))
    elif args.mode == "performance":
        framework.test_results = framework.test_performance_stress()
        report = framework.generate_test_report(sum(r.duration for r in framework.test_results))
    elif args.mode == "concurrent":
        framework.test_results = framework.test_concurrent_execution()
        report = framework.generate_test_report(sum(r.duration for r in framework.test_results))

    # 输出结果
    print_report(report, args.verbose)

    # 保存报告
    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = __import__('datetime').datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(f"/tmp/claude/e2e_test_report_{args.mode}_{timestamp}.json")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n📝 测试报告已保存: {output_path}")

    # 返回适当的退出码
    if report['summary']['success_rate'] >= 80:
        print("✅ 测试通过！")
        return 0
    else:
        print("❌ 测试失败！")
        return 1

def print_report(report, verbose=False):
    """打印测试报告"""
    summary = report['summary']

    print("\n" + "="*80)
    print("🎯 测试结果摘要")
    print("="*80)

    # 基本统计
    print(f"📊 总测试数: {summary['total_tests']}")
    print(f"✅ 通过: {summary['passed']}")
    print(f"❌ 失败: {summary['failed']}")
    print(f"💥 错误: {summary['errors']}")
    print(f"⏭️  跳过: {summary['skipped']}")
    print(f"📈 成功率: {summary['success_rate']:.1f}%")
    print(f"⏱️  总耗时: {summary['total_duration']:.2f}秒")
    print(f"⏱️  平均耗时: {summary['avg_test_duration']:.3f}秒")

    # 成功率指示器
    success_rate = summary['success_rate']
    if success_rate >= 95:
        status = "🟢 优秀"
    elif success_rate >= 80:
        status = "🟡 良好"
    elif success_rate >= 60:
        status = "🟠 一般"
    else:
        status = "🔴 需要改进"

    print(f"🎯 整体评价: {status}")

    # 各阶段情况
    if report.get('phase_breakdown'):
        print(f"\n📋 各阶段测试情况:")
        for phase, stats in report['phase_breakdown'].items():
            phase_success_rate = (stats['passed'] / stats['total']) * 100 if stats['total'] > 0 else 0
            print(f"   📌 {phase}: {stats['passed']}/{stats['total']} ({phase_success_rate:.1f}%)")

    # 失败的测试
    if report.get('failed_tests'):
        print(f"\n❌ 失败的测试 ({len(report['failed_tests'])}):")
        for i, test in enumerate(report['failed_tests'][:10], 1):  # 只显示前10个
            print(f"   {i}. {test['name']} ({test.get('phase', 'N/A')})")
            if verbose:
                print(f"      原因: {test.get('message', 'N/A')}")
                print(f"      耗时: {test.get('duration', 0):.3f}秒")

        if len(report['failed_tests']) > 10:
            print(f"   ... 还有 {len(report['failed_tests']) - 10} 个失败测试")

    # 性能指标
    if report.get('performance_metrics'):
        print(f"\n🔧 性能指标:")
        for metric, value in report['performance_metrics'].items():
            if value > 0:
                print(f"   📊 {metric.replace('_', ' ').title()}: {value}")

    # 改进建议
    if report.get('recommendations'):
        print(f"\n💡 改进建议:")
        for i, rec in enumerate(report['recommendations'][:5], 1):
            print(f"   {i}. {rec}")

    # 详细结果（仅在verbose模式下显示）
    if verbose and report.get('detailed_results'):
        print(f"\n📋 详细测试结果:")
        for result in report['detailed_results'][:20]:  # 只显示前20个
            status_icon = {"PASS": "✅", "FAIL": "❌", "ERROR": "💥", "SKIP": "⏭️"}.get(result['status'], "❓")
            print(f"   {status_icon} {result['name']} ({result.get('duration', 0):.3f}s)")
            if result['status'] in ['FAIL', 'ERROR'] and result.get('message'):
                print(f"      💬 {result['message']}")

    print("="*80)

if __name__ == "__main__":
    sys.exit(main())