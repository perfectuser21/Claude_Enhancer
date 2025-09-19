#!/usr/bin/env python3
"""
Perfect21性能优化快速入门
演示如何使用Perfect21的性能优化功能
"""

import os
import sys
import asyncio
import time
from typing import Dict, Any

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# 导入性能优化功能
from modules.enhanced_performance_optimizer import (
    enhanced_performance_optimizer,
    optimize_agent_execution,
    batch_git_operations,
    optimize_memory,
    start_performance_optimization,
    get_performance_report,
    run_benchmark,
    optimized_execution
)
from features.performance.performance_optimizer_feature import (
    performance_optimizer_feature,
    optimize_perfect21_performance,
    analyze_perfect21_performance
)

class PerformanceQuickStart:
    """性能优化快速入门演示"""

    def __init__(self):
        print("🚀 Perfect21性能优化快速入门")
        print("=" * 50)

    async def demo_basic_optimization(self):
        """演示基本优化功能"""
        print("\n📊 1. 基本性能优化演示")
        print("-" * 30)

        # 启动自动优化
        print("🤖 启动自动性能优化...")
        start_performance_optimization()
        print("✅ 自动优化已启动（后台运行）")

        # 演示优化执行上下文
        print("\n🎯 使用优化执行上下文:")
        async with optimized_execution() as optimizer:
            print("  📦 缓存系统已加载")
            print("  💾 内存优化器已就绪")
            print("  🔧 资源池管理器已激活")

            # 模拟一些工作
            await asyncio.sleep(0.1)
            print("  ⚡ 模拟工作完成")

        print("✅ 优化上下文演示完成")

    async def demo_agent_optimization(self):
        """演示Agent执行优化"""
        print("\n🤖 2. Agent执行优化演示")
        print("-" * 30)

        # 演示Agent缓存效果
        agent_type = "demo-agent"
        params = {"task": "example_task", "priority": "high"}

        print(f"🔄 执行Agent: {agent_type}")

        # 第一次执行（缓存未命中）
        start_time = time.perf_counter()
        result1 = await optimize_agent_execution(agent_type, params)
        first_time = time.perf_counter() - start_time
        print(f"  ⏱️  首次执行时间: {first_time * 1000:.2f}ms")

        # 第二次执行（缓存命中）
        start_time = time.perf_counter()
        result2 = await optimize_agent_execution(agent_type, params)
        second_time = time.perf_counter() - start_time
        print(f"  ⚡ 缓存命中时间: {second_time * 1000:.2f}ms")

        # 计算改善
        if first_time > 0:
            improvement = ((first_time - second_time) / first_time) * 100
            print(f"  📈 性能提升: {improvement:.1f}%")

        print("✅ Agent优化演示完成")

    async def demo_git_optimization(self):
        """演示Git操作优化"""
        print("\n🔧 3. Git操作批量优化演示")
        print("-" * 30)

        # 演示批量Git操作
        git_operations = [
            ("status", []),
            ("status", ["--short"]),
            ("branch", []),
            ("branch", ["-r"]),
            ("log", ["--oneline", "-5"]),
            ("diff", ["--stat"])
        ]

        print("📝 队列Git操作...")
        operation_ids = batch_git_operations(git_operations)
        print(f"  📋 已队列 {len(operation_ids)} 个操作")
        print(f"  🆔 操作ID: {operation_ids[:3]}...")

        # 等待批量处理
        print("⏳ 等待批量处理完成...")
        await asyncio.sleep(3)

        # 获取Git缓存统计
        from modules.enhanced_git_cache import get_git_cache_stats
        stats = get_git_cache_stats()
        print(f"📊 Git缓存统计:")
        print(f"  📦 缓存条目: {stats['total_entries']}")
        print(f"  🎯 命中率: {stats['hit_rate']}")

        print("✅ Git优化演示完成")

    async def demo_memory_optimization(self):
        """演示内存优化"""
        print("\n💾 4. 内存优化演示")
        print("-" * 30)

        # 获取优化前内存状态
        import psutil
        process = psutil.Process()
        before_memory = process.memory_info().rss / 1024 / 1024

        print(f"📊 优化前内存: {before_memory:.2f}MB")

        # 创建一些内存压力（模拟）
        temp_data = []
        for i in range(1000):
            temp_data.append([f"test_data_{j}" for j in range(100)])

        pressure_memory = process.memory_info().rss / 1024 / 1024
        print(f"🔴 内存压力测试: {pressure_memory:.2f}MB")

        # 执行内存优化
        print("🧹 执行内存优化...")
        optimization_result = await optimize_memory()

        after_memory = process.memory_info().rss / 1024 / 1024
        print(f"💚 优化后内存: {after_memory:.2f}MB")

        # 清理测试数据
        del temp_data
        final_memory = process.memory_info().rss / 1024 / 1024

        if 'improvement_mb' in optimization_result:
            print(f"📈 内存释放: {optimization_result['improvement_mb']:.2f}MB")

        print("✅ 内存优化演示完成")

    async def demo_performance_analysis(self):
        """演示性能分析"""
        print("\n📈 5. 性能分析演示")
        print("-" * 30)

        print("🔍 执行系统性能分析...")
        analysis_result = await analyze_perfect21_performance()

        # 显示关键指标
        if 'analysis' in analysis_result and 'overall_health' in analysis_result['analysis']:
            health = analysis_result['analysis']['overall_health']
            print(f"🏥 系统健康分数: {health['score']:.1f}/100 ({health['status']})")

        # 显示缓存统计
        if 'cache_stats' in analysis_result:
            cache_stats = analysis_result['cache_stats']
            print(f"📦 缓存命中率: {cache_stats.get('hit_rate', '0%')}")
            print(f"📦 缓存条目数: {cache_stats.get('total_entries', 0)}")

        # 显示瓶颈
        if 'analysis' in analysis_result and 'bottlenecks' in analysis_result['analysis']:
            bottlenecks = analysis_result['analysis']['bottlenecks']
            if bottlenecks:
                print("⚠️  发现的瓶颈:")
                for bottleneck in bottlenecks[:3]:
                    print(f"  • {bottleneck['description']}")
            else:
                print("🟢 未发现明显瓶颈")

        # 显示建议
        if 'analysis' in analysis_result and 'recommendations' in analysis_result['analysis']:
            recommendations = analysis_result['analysis']['recommendations']
            if recommendations:
                print("💡 优化建议:")
                for rec in recommendations[:2]:
                    print(f"  • {rec['title']}: {rec['expected_improvement']}")

        print("✅ 性能分析演示完成")

    async def demo_benchmark_testing(self):
        """演示基准测试"""
        print("\n🏁 6. 基准测试演示")
        print("-" * 30)

        print("🏃 运行性能基准测试...")
        benchmark_result = run_benchmark()

        if 'results' in benchmark_result:
            print("📊 基准测试结果:")
            for test_name, execution_time in benchmark_result['results'].items():
                print(f"  {test_name}: {execution_time:.3f}秒")

        # 检查回归
        if 'regressions' in benchmark_result:
            regressions = benchmark_result['regressions']
            if regressions:
                print(f"⚠️  检测到 {len(regressions)} 个性能回归")
            else:
                print("🟢 无性能回归")

        print("✅ 基准测试演示完成")

    async def demo_comprehensive_optimization(self):
        """演示全面系统优化"""
        print("\n⚡ 7. 全面系统优化演示")
        print("-" * 30)

        print("🚀 执行全面系统优化...")
        optimization_result = await optimize_perfect21_performance(['memory', 'cache', 'git'])

        print(f"⏱️  优化耗时: {optimization_result.get('optimization_time', 0):.3f}秒")

        # 显示各项优化结果
        if 'memory' in optimization_result:
            memory_result = optimization_result['memory']
            if 'improvement_mb' in memory_result:
                print(f"💾 内存优化: 释放 {memory_result['improvement_mb']:.2f}MB")

        if 'cache' in optimization_result:
            cache_result = optimization_result['cache']
            print(f"📦 缓存优化: 命中率 {cache_result.get('hit_rate', '0%')}")

        if 'git' in optimization_result:
            git_result = optimization_result['git']
            print(f"🔧 Git优化: 批量化率 {git_result.get('optimization_ratio', '0%')}")

        print("✅ 全面优化演示完成")

    async def show_performance_dashboard(self):
        """显示性能面板"""
        print("\n📱 8. 性能监控面板")
        print("-" * 30)

        # 获取全面性能报告
        report = get_performance_report()

        print("📊 实时性能指标:")

        # 内存使用
        if 'memory_stats' in report:
            memory = report['memory_stats']
            print(f"  💾 内存使用: {memory.get('rss_mb', 0):.2f}MB ({memory.get('percent', 0):.1f}%)")

        # 缓存效率
        if 'cache_stats' in report:
            cache = report['cache_stats']
            print(f"  📦 缓存效率: {cache.get('hit_rate', '0%')} ({cache.get('total_entries', 0)} 条目)")

        # 优化历史
        if 'optimization_history' in report:
            history = report['optimization_history']
            print(f"  📈 优化历史: {len(history)} 次优化")

        # 性能指标趋势
        if 'performance_metrics' in report:
            metrics = report['performance_metrics']
            for metric_name, metric_data in metrics.items():
                if metric_data.get('count', 0) > 0:
                    latest = metric_data.get('latest', 0)
                    avg = metric_data.get('average', 0)
                    print(f"  📏 {metric_name}: 当前 {latest:.2f} (平均 {avg:.2f})")

        print("✅ 性能面板显示完成")

    async def run_full_demo(self):
        """运行完整演示"""
        try:
            # 初始化性能优化器
            await performance_optimizer_feature.initialize()

            # 逐步演示各项功能
            await self.demo_basic_optimization()
            await self.demo_agent_optimization()
            await self.demo_git_optimization()
            await self.demo_memory_optimization()
            await self.demo_performance_analysis()
            await self.demo_benchmark_testing()
            await self.demo_comprehensive_optimization()
            await self.show_performance_dashboard()

            print("\n" + "=" * 50)
            print("🎉 Perfect21性能优化演示完成！")
            print("=" * 50)

            print("\n📚 快速使用指南:")
            print("1. 导入模块: from modules.enhanced_performance_optimizer import *")
            print("2. 启动自动优化: start_performance_optimization()")
            print("3. 优化Agent执行: await optimize_agent_execution(agent_type, params)")
            print("4. 批量Git操作: batch_git_operations(operations)")
            print("5. 内存优化: await optimize_memory()")
            print("6. 性能分析: await analyze_perfect21_performance()")
            print("7. 基准测试: run_benchmark()")

            print("\n💡 建议下一步:")
            print("• 运行 python3 tests/performance_validation.py 验证性能")
            print("• 使用 python3 main/performance_cli.py --help 查看CLI命令")
            print("• 查看 modules/enhanced_performance_optimizer.py 了解更多API")

            return True

        except Exception as e:
            print(f"\n❌ 演示过程中发生错误: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            # 停止自动优化
            enhanced_performance_optimizer.stop_auto_optimization()
            print("\n🛑 自动优化已停止")

async def main():
    """主函数"""
    print("Perfect21性能优化快速入门")
    print("本演示将展示Perfect21的各项性能优化功能")

    input("\n按回车键开始演示...")

    demo = PerformanceQuickStart()
    success = await demo.run_full_demo()

    if success:
        print("\n🎯 演示成功完成！")
        print("你现在可以在自己的项目中使用这些性能优化功能了。")
    else:
        print("\n⚠️ 演示过程中遇到问题，请检查错误信息。")

if __name__ == "__main__":
    import platform

    print(f"🖥️  运行环境:")
    print(f"  Python版本: {platform.python_version()}")
    print(f"  操作系统: {platform.system()} {platform.release()}")
    print(f"  处理器: {platform.processor()}")

    # 运行演示
    asyncio.run(main())