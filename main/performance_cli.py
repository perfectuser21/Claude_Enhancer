#!/usr/bin/env python3
"""
Perfect21性能优化CLI
提供便捷的性能优化和监控命令
"""

import os
import sys
import asyncio
import argparse
import json
import time
from typing import Dict, Any

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.logger import log_info, log_error
from features.performance.performance_optimizer_feature import (
    performance_optimizer_feature,
    optimize_perfect21_performance,
    analyze_perfect21_performance,
    get_perfect21_performance_status
)

def print_performance_report(report: Dict[str, Any]) -> None:
    """格式化打印性能报告"""
    print("🚀 Perfect21性能报告")
    print("=" * 60)

    # 健康分数
    if 'analysis' in report and 'overall_health' in report['analysis']:
        health = report['analysis']['overall_health']
        status_icons = {
            'excellent': '🟢',
            'good': '🟡',
            'fair': '🟠',
            'poor': '🔴'
        }
        icon = status_icons.get(health['status'], '⚪')
        print(f"{icon} 系统健康分数: {health['score']:.1f}/100 ({health['status'].upper()})")
        print()

    # 核心指标
    print("📊 核心性能指标:")
    print("-" * 40)

    cache_stats = report.get('cache_stats', {})
    if cache_stats:
        hit_rate = cache_stats.get('hit_rate', '0%')
        cache_size = cache_stats.get('total_entries', 0)
        memory_usage = cache_stats.get('total_size_mb', 0)
        print(f"  📦 缓存命中率: {hit_rate}")
        print(f"  📦 缓存条目数: {cache_size}")
        print(f"  📦 缓存内存使用: {memory_usage:.2f}MB")

    memory_stats = report.get('memory_stats', {})
    if memory_stats:
        rss_mb = memory_stats.get('rss_mb', 0)
        percent = memory_stats.get('percent', 0)
        print(f"  💾 进程内存使用: {rss_mb:.2f}MB ({percent:.1f}%)")

    git_stats = report.get('git_optimization_stats', {})
    if git_stats:
        optimization_ratio = git_stats.get('optimization_ratio', '0%')
        pending = git_stats.get('pending_operations', 0)
        print(f"  🔧 Git优化率: {optimization_ratio}")
        print(f"  🔧 待处理Git操作: {pending}")

    # 瓶颈识别
    if 'analysis' in report and 'bottlenecks' in report['analysis']:
        bottlenecks = report['analysis']['bottlenecks']
        if bottlenecks:
            print("\n⚠️  识别的性能瓶颈:")
            print("-" * 40)
            for bottleneck in bottlenecks[:5]:  # 最多显示5个
                severity_icons = {'high': '🔴', 'medium': '🟠', 'low': '🟡'}
                icon = severity_icons.get(bottleneck['severity'], '⚪')
                print(f"  {icon} {bottleneck['description']}")

    # 优化建议
    if 'analysis' in report and 'recommendations' in report['analysis']:
        recommendations = report['analysis']['recommendations']
        if recommendations:
            print("\n💡 优化建议:")
            print("-" * 40)
            for i, rec in enumerate(recommendations[:3], 1):  # 最多显示3个
                priority_icons = {'high': '🔴', 'medium': '🟠', 'low': '🟡'}
                icon = priority_icons.get(rec['priority'], '⚪')
                print(f"  {i}. {icon} {rec['title']}")
                print(f"     {rec['description']}")
                print(f"     预期改善: {rec['expected_improvement']}")
                print()

    # 基准测试摘要
    if 'benchmark_summary' in report:
        benchmark = report['benchmark_summary']
        if benchmark:
            print("🏁 基准测试摘要:")
            print("-" * 40)
            for test_name, stats in benchmark.items():
                latest = stats.get('latest', 0)
                baseline = stats.get('baseline', 0)
                if baseline > 0:
                    ratio = (latest - baseline) / baseline
                    status = "🔴 回归" if ratio > 0.2 else "🟢 正常" if ratio < 0.1 else "🟡 注意"
                    print(f"  {test_name}: {latest:.3f}s {status}")

def print_optimization_result(result: Dict[str, Any]) -> None:
    """格式化打印优化结果"""
    print("⚡ Perfect21性能优化结果")
    print("=" * 50)

    optimization_time = result.get('optimization_time', 0)
    print(f"🕐 优化耗时: {optimization_time:.3f}秒")
    print()

    # 内存优化结果
    if 'memory' in result:
        memory_result = result['memory']
        improvement = memory_result.get('improvement_mb', 0)
        if improvement > 0:
            print(f"💾 内存优化: 释放 {improvement:.2f}MB 内存")

    # 缓存优化结果
    if 'cache' in result:
        cache_result = result['cache']
        hit_rate = cache_result.get('hit_rate', '0%')
        print(f"📦 缓存优化: 命中率 {hit_rate}")

    # Git优化结果
    if 'git' in result:
        git_result = result['git']
        optimization_ratio = git_result.get('optimization_ratio', '0%')
        print(f"🔧 Git优化: 批量化率 {optimization_ratio}")

    # 基准测试结果
    if 'benchmark' in result:
        benchmark_result = result['benchmark']
        if 'regressions' in benchmark_result and benchmark_result['regressions']:
            print(f"⚠️  检测到 {len(benchmark_result['regressions'])} 个性能回归")
        else:
            print("🟢 基准测试通过，无性能回归")

    print("\n✅ 优化完成！")

async def cmd_optimize(args: argparse.Namespace) -> None:
    """执行性能优化"""
    optimization_types = []

    if args.memory:
        optimization_types.append('memory')
    if args.cache:
        optimization_types.append('cache')
    if args.git:
        optimization_types.append('git')
    if args.benchmark:
        optimization_types.append('benchmark')

    # 如果没有指定类型，默认执行所有优化
    if not optimization_types:
        optimization_types = ['memory', 'cache', 'git', 'benchmark']

    print(f"🚀 开始执行性能优化: {', '.join(optimization_types)}")
    print("请稍候...")

    try:
        result = await optimize_perfect21_performance(optimization_types)
        print_optimization_result(result)

        if args.report:
            print("\n" + "=" * 50)
            report = await analyze_perfect21_performance()
            print_performance_report(report)

    except Exception as e:
        log_error(f"性能优化失败: {e}")
        print(f"❌ 优化失败: {e}")

async def cmd_analyze(args: argparse.Namespace) -> None:
    """执行性能分析"""
    print("🔍 正在分析系统性能...")

    try:
        report = await analyze_perfect21_performance()

        if args.json:
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print_performance_report(report)

        if args.save:
            filename = args.save or f"performance_report_{int(time.time())}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"\n📁 报告已保存至: {filename}")

    except Exception as e:
        log_error(f"性能分析失败: {e}")
        print(f"❌ 分析失败: {e}")

def cmd_status(args: argparse.Namespace) -> None:
    """显示性能状态"""
    try:
        status = get_perfect21_performance_status()

        print("📊 Perfect21性能状态")
        print("=" * 40)

        print(f"📦 功能: {status['name']} v{status['version']}")
        print(f"🤖 自动优化: {'启用' if status['auto_optimization'] else '禁用'}")
        print()

        quick_stats = status.get('quick_stats', {})
        if 'cache_stats' in quick_stats:
            cache_stats = quick_stats['cache_stats']
            hit_rate = cache_stats.get('hit_rate', '0%')
            entries = cache_stats.get('total_entries', 0)
            print(f"📦 缓存命中率: {hit_rate} ({entries} 条目)")

        if 'memory_rss_mb' in quick_stats:
            memory = quick_stats['memory_rss_mb']
            print(f"💾 内存使用: {memory:.2f}MB")

        if 'resource_pools' in quick_stats:
            pools = quick_stats['resource_pools']
            print(f"🔧 资源池数: {pools}")

        if 'optimization_history' in quick_stats:
            history = quick_stats['optimization_history']
            print(f"📈 优化历史: {history} 次")

        if args.detailed:
            print("\n详细配置:")
            print("-" * 20)
            config = status.get('config', {})
            for key, value in config.items():
                print(f"  {key}: {value}")

    except Exception as e:
        log_error(f"获取状态失败: {e}")
        print(f"❌ 获取状态失败: {e}")

async def cmd_benchmark(args: argparse.Namespace) -> None:
    """运行基准测试"""
    print("🏁 运行性能基准测试...")

    try:
        from modules.enhanced_performance_optimizer import run_benchmark
        result = run_benchmark()

        if args.json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
            return

        print("\n📊 基准测试结果:")
        print("-" * 30)

        results = result.get('results', {})
        for test_name, time_taken in results.items():
            print(f"  {test_name}: {time_taken:.3f}秒")

        regressions = result.get('regressions', [])
        if regressions:
            print(f"\n⚠️  检测到 {len(regressions)} 个性能回归:")
            for regression in regressions:
                print(f"  🔴 {regression['test_name']}: "
                      f"{regression['current']:.3f}s (基线: {regression['baseline']:.3f}s, "
                      f"回归: {regression['regression_ratio']:.1%})")
        else:
            print("\n🟢 无性能回归检测")

        if args.save:
            filename = args.save or f"benchmark_result_{int(time.time())}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"\n📁 基准测试结果已保存至: {filename}")

    except Exception as e:
        log_error(f"基准测试失败: {e}")
        print(f"❌ 基准测试失败: {e}")

async def cmd_auto_optimize(args: argparse.Namespace) -> None:
    """自动优化控制"""
    from modules.enhanced_performance_optimizer import enhanced_performance_optimizer

    if args.action == 'start':
        enhanced_performance_optimizer.start_auto_optimization()
        print("🤖 自动性能优化已启动")
        print(f"⏰ 优化间隔: {enhanced_performance_optimizer.optimization_interval}秒")

    elif args.action == 'stop':
        enhanced_performance_optimizer.stop_auto_optimization()
        print("⏹️  自动性能优化已停止")

    elif args.action == 'status':
        status = enhanced_performance_optimizer.auto_optimization
        print(f"🤖 自动优化状态: {'运行中' if status else '已停止'}")

        if status:
            interval = enhanced_performance_optimizer.optimization_interval
            print(f"⏰ 优化间隔: {interval}秒")

def create_parser() -> argparse.ArgumentParser:
    """创建参数解析器"""
    parser = argparse.ArgumentParser(
        description="Perfect21性能优化CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  python3 performance_cli.py optimize --memory --cache
  python3 performance_cli.py analyze --report --save report.json
  python3 performance_cli.py status --detailed
  python3 performance_cli.py benchmark --save benchmark.json
  python3 performance_cli.py auto start
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # optimize命令
    optimize_parser = subparsers.add_parser('optimize', help='执行性能优化')
    optimize_parser.add_argument('--memory', action='store_true', help='优化内存使用')
    optimize_parser.add_argument('--cache', action='store_true', help='优化缓存策略')
    optimize_parser.add_argument('--git', action='store_true', help='优化Git操作')
    optimize_parser.add_argument('--benchmark', action='store_true', help='运行基准测试')
    optimize_parser.add_argument('--report', action='store_true', help='优化后显示分析报告')

    # analyze命令
    analyze_parser = subparsers.add_parser('analyze', help='分析系统性能')
    analyze_parser.add_argument('--json', action='store_true', help='输出JSON格式')
    analyze_parser.add_argument('--save', nargs='?', const=True, help='保存报告到文件')

    # status命令
    status_parser = subparsers.add_parser('status', help='显示性能状态')
    status_parser.add_argument('--detailed', action='store_true', help='显示详细配置')

    # benchmark命令
    benchmark_parser = subparsers.add_parser('benchmark', help='运行基准测试')
    benchmark_parser.add_argument('--json', action='store_true', help='输出JSON格式')
    benchmark_parser.add_argument('--save', nargs='?', const=True, help='保存结果到文件')

    # auto命令
    auto_parser = subparsers.add_parser('auto', help='自动优化控制')
    auto_parser.add_argument('action', choices=['start', 'stop', 'status'],
                           help='自动优化操作')

    return parser

async def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 初始化性能优化器
    if not await performance_optimizer_feature.initialize():
        print("❌ 性能优化器初始化失败")
        return

    try:
        if args.command == 'optimize':
            await cmd_optimize(args)
        elif args.command == 'analyze':
            await cmd_analyze(args)
        elif args.command == 'status':
            cmd_status(args)
        elif args.command == 'benchmark':
            await cmd_benchmark(args)
        elif args.command == 'auto':
            await cmd_auto_optimize(args)
        else:
            parser.print_help()

    except KeyboardInterrupt:
        print("\n❌ 操作被用户中断")
    except Exception as e:
        log_error(f"执行命令失败: {e}")
        print(f"❌ 执行失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())