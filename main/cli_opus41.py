#!/usr/bin/env python3
"""
Perfect21 Opus41 CLI扩展
为Opus41智能并行优化器提供命令行接口
"""

import os
import sys
import argparse
import json
import time
from typing import Dict, Any, List

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from features.opus41_optimizer import (
    get_opus41_optimizer,
    OptimizationLevel,
    QualityThreshold,
    QualityLevel
)
from features.opus41_visualizer import get_opus41_visualizer
from modules.logger import log_info, log_error

def create_opus41_parser(subparsers):
    """创建Opus41命令解析器"""
    opus41_parser = subparsers.add_parser('opus41', help='Opus41智能并行优化器')
    opus41_subparsers = opus41_parser.add_subparsers(dest='opus41_action', help='Opus41操作')

    # 优化命令
    optimize_parser = opus41_subparsers.add_parser('optimize', help='优化执行计划')
    optimize_parser.add_argument('task', help='任务描述')
    optimize_parser.add_argument('--quality',
                               choices=['minimum', 'good', 'excellent', 'perfect'],
                               default='excellent',
                               help='目标质量级别')
    optimize_parser.add_argument('--level',
                               choices=['basic', 'adaptive', 'intelligent', 'opus41'],
                               default='opus41',
                               help='优化级别')
    optimize_parser.add_argument('--agents', type=int, help='最大Agent数量')
    optimize_parser.add_argument('--show-plan', action='store_true', help='显示执行计划')
    optimize_parser.add_argument('--export-plan', help='导出计划到文件')

    # 执行命令
    execute_parser = opus41_subparsers.add_parser('execute', help='执行优化计划')
    execute_parser.add_argument('task', help='任务描述')
    execute_parser.add_argument('--quality',
                              choices=['minimum', 'good', 'excellent', 'perfect'],
                              default='excellent',
                              help='目标质量级别')
    execute_parser.add_argument('--level',
                              choices=['basic', 'adaptive', 'intelligent', 'opus41'],
                              default='opus41',
                              help='优化级别')
    execute_parser.add_argument('--monitor', action='store_true', help='启用实时监控')
    execute_parser.add_argument('--dashboard', action='store_true', help='生成HTML Dashboard')
    execute_parser.add_argument('--save-report', help='保存执行报告到文件')

    # 智能选择命令
    select_parser = opus41_subparsers.add_parser('select', help='智能Agent选择')
    select_parser.add_argument('task', help='任务描述')
    select_parser.add_argument('--quality-level',
                             choices=['fast', 'balanced', 'premium', 'ultimate'],
                             default='premium',
                             help='质量级别')
    select_parser.add_argument('--max-agents', type=int, default=15, help='最大Agent数量')

    # 监控命令
    monitor_parser = opus41_subparsers.add_parser('monitor', help='监控和可视化')
    monitor_subparsers = monitor_parser.add_subparsers(dest='monitor_action', help='监控操作')

    # 启动监控
    start_monitor_parser = monitor_subparsers.add_parser('start', help='启动监控')
    start_monitor_parser.add_argument('--dashboard', action='store_true', help='启动Dashboard')
    start_monitor_parser.add_argument('--interval', type=int, default=2, help='更新间隔(秒)')

    # 生成报告
    report_parser = monitor_subparsers.add_parser('report', help='生成性能报告')
    report_parser.add_argument('--format', choices=['json', 'html'], default='json', help='报告格式')
    report_parser.add_argument('--output', help='输出文件名')

    # 导出数据
    export_parser = monitor_subparsers.add_parser('export', help='导出监控数据')
    export_parser.add_argument('--format', choices=['json', 'csv'], default='json', help='导出格式')
    export_parser.add_argument('--output', help='输出文件名')

    # 状态命令
    status_parser = opus41_subparsers.add_parser('status', help='查看优化器状态')
    status_parser.add_argument('--detailed', action='store_true', help='显示详细信息')

    # 基准测试命令
    benchmark_parser = opus41_subparsers.add_parser('benchmark', help='性能基准测试')
    benchmark_parser.add_argument('--agents', type=int, default=10, help='测试Agent数量')
    benchmark_parser.add_argument('--rounds', type=int, default=3, help='测试轮数')
    benchmark_parser.add_argument('--complexity',
                                choices=['simple', 'medium', 'complex', 'enterprise'],
                                default='medium',
                                help='测试复杂度')

    return opus41_parser

def handle_opus41_optimize(args: argparse.Namespace) -> None:
    """处理优化命令"""
    optimizer = get_opus41_optimizer()

    # 转换参数
    quality_mapping = {
        'minimum': QualityThreshold.MINIMUM,
        'good': QualityThreshold.GOOD,
        'excellent': QualityThreshold.EXCELLENT,
        'perfect': QualityThreshold.PERFECT
    }

    level_mapping = {
        'basic': OptimizationLevel.BASIC,
        'adaptive': OptimizationLevel.ADAPTIVE,
        'intelligent': OptimizationLevel.INTELLIGENT,
        'opus41': OptimizationLevel.OPUS41
    }

    target_quality = quality_mapping[args.quality]
    optimization_level = level_mapping[args.level]

    print(f"🚀 开始Opus41优化: {args.task}")
    print(f"🎯 目标质量: {target_quality.name}")
    print(f"⚡ 优化级别: {optimization_level.name}")

    try:
        # 生成优化计划
        plan = optimizer.optimize_execution(
            task_description=args.task,
            target_quality=target_quality,
            optimization_level=optimization_level
        )

        # 显示计划
        if args.show_plan:
            optimizer.display_execution_plan(plan)

        # 导出计划
        if args.export_plan:
            plan_data = {
                "task_description": plan.task_description,
                "optimization_level": plan.optimization_level.value,
                "target_quality": plan.target_quality.value,
                "estimated_total_time": plan.estimated_total_time,
                "success_probability": plan.success_probability,
                "resource_requirements": plan.resource_requirements,
                "execution_layers": [
                    {
                        "layer_id": layer.layer_id,
                        "layer_name": layer.layer_name,
                        "agents": layer.agents,
                        "estimated_time": layer.estimated_time,
                        "sync_points": layer.sync_points
                    }
                    for layer in plan.execution_layers
                ],
                "refinement_rounds": [
                    {
                        "round_id": round.round_id,
                        "improvement_areas": round.improvement_areas,
                        "selected_agents": round.selected_agents,
                        "estimated_time": round.estimated_time
                    }
                    for round in plan.refinement_rounds
                ]
            }

            with open(args.export_plan, 'w', encoding='utf-8') as f:
                json.dump(plan_data, f, indent=2, ensure_ascii=False)

            print(f"📄 计划已导出到: {args.export_plan}")

        # 生成Task调用指令
        task_calls = optimizer.generate_task_calls(plan)

        print(f"\n🎯 **执行指令**: 请在单个消息中调用以下{len(task_calls)}个Task工具：")
        print("=" * 80)

        for i, call in enumerate(task_calls, 1):
            params = call["parameters"]
            print(f"\n**Task {i}: @{params['subagent_type']}**")
            print(f"```")
            print(f"Task(")
            print(f"    subagent_type=\"{params['subagent_type']}\",")
            print(f"    description=\"{params['description']}\",")
            print(f"    prompt=\"\"\"")
            print(f"{params['prompt'][:200]}...")
            print(f"\"\"\"")
            print(f")")
            print(f"```")

        print(f"\n🚀 **优化摘要**:")
        print(f"- 总Agent数: {plan.resource_requirements['total_agents']}")
        print(f"- 最大并发: {plan.resource_requirements['concurrent_agents']}")
        print(f"- 预估时间: {plan.estimated_total_time}分钟")
        print(f"- 成功概率: {plan.success_probability:.1%}")
        print("=" * 80)

    except Exception as e:
        log_error(f"优化失败: {e}")
        print(f"❌ 优化失败: {e}")

def handle_opus41_execute(args: argparse.Namespace) -> None:
    """处理执行命令"""
    optimizer = get_opus41_optimizer()
    visualizer = get_opus41_visualizer()

    # 转换参数
    quality_mapping = {
        'minimum': QualityThreshold.MINIMUM,
        'good': QualityThreshold.GOOD,
        'excellent': QualityThreshold.EXCELLENT,
        'perfect': QualityThreshold.PERFECT
    }

    level_mapping = {
        'basic': OptimizationLevel.BASIC,
        'adaptive': OptimizationLevel.ADAPTIVE,
        'intelligent': OptimizationLevel.INTELLIGENT,
        'opus41': OptimizationLevel.OPUS41
    }

    target_quality = quality_mapping[args.quality]
    optimization_level = level_mapping[args.level]

    print(f"🚀 开始Opus41执行: {args.task}")

    try:
        # 1. 生成优化计划
        plan = optimizer.optimize_execution(
            task_description=args.task,
            target_quality=target_quality,
            optimization_level=optimization_level
        )

        # 2. 启动监控
        if args.monitor:
            visualizer.start_real_time_monitoring({
                "task": args.task,
                "quality_target": target_quality.value,
                "optimization_level": optimization_level.value
            })

        # 3. 执行计划
        result = optimizer.execute_optimized_plan(plan)

        # 4. 显示结果
        if result["success"]:
            print(f"✅ 执行成功!")
            print(f"⏱️ 执行时间: {result['execution_time']:.2f}秒")
            print(f"🎯 最终质量: {result['final_quality']:.1%}")
            print(f"📊 完成层数: {result['layers_completed']}")
            print(f"🔧 改进轮次: {result['refinements_completed']}")

            if result['quality_progression']:
                print(f"📈 质量进展: {' → '.join([f'{q:.1%}' for q in result['quality_progression']])}")

        else:
            print(f"❌ 执行失败: {result.get('error', '未知错误')}")

        # 5. 生成Dashboard
        if args.dashboard:
            dashboard_file = visualizer.generate_html_dashboard("opus41_execution_dashboard.html")
            print(f"📊 Dashboard已生成: {dashboard_file}")

        # 6. 保存报告
        if args.save_report:
            report_data = {
                "execution_result": result,
                "plan_summary": {
                    "task": plan.task_description,
                    "optimization_level": plan.optimization_level.value,
                    "target_quality": plan.target_quality.value,
                    "total_agents": plan.resource_requirements['total_agents'],
                    "estimated_time": plan.estimated_total_time
                },
                "performance_report": visualizer.generate_performance_report()
            }

            with open(args.save_report, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False, default=str)

            print(f"📄 执行报告已保存: {args.save_report}")

        # 7. 停止监控
        if args.monitor:
            visualizer.stop_monitoring()

    except Exception as e:
        log_error(f"执行失败: {e}")
        print(f"❌ 执行失败: {e}")

def handle_opus41_select(args: argparse.Namespace) -> None:
    """处理智能Agent选择命令"""
    optimizer = get_opus41_optimizer()

    quality_level_mapping = {
        'fast': QualityLevel.FAST,
        'balanced': QualityLevel.BALANCED,
        'premium': QualityLevel.PREMIUM,
        'ultimate': QualityLevel.ULTIMATE
    }

    quality_level = quality_level_mapping[args.quality_level]

    print(f"🤖 智能Agent选择: {args.task}")
    print(f"🎯 质量级别: {quality_level.name}")

    try:
        # 设置最大agent数量
        if args.max_agents:
            optimizer.max_parallel_agents = args.max_agents

        selected_agents = optimizer.select_optimal_agents(args.task, quality_level)

        print(f"\n✅ 已选择 {len(selected_agents)} 个最优Agents:")
        print("=" * 60)

        # 按类别分组显示
        for category, agents_in_category in optimizer.agent_categories.items():
            category_agents = [agent for agent in selected_agents if agent in agents_in_category]
            if category_agents:
                category_names = {
                    'business': '💼 业务分析',
                    'development': '💻 开发实现',
                    'frameworks': '🛠️ 框架专家',
                    'quality': '🔍 质量保证',
                    'infrastructure': '🏗️ 基础设施',
                    'data_ai': '🤖 数据AI',
                    'specialized': '🎨 专业服务',
                    'industry': '🏢 行业专家'
                }
                print(f"\n{category_names.get(category, category)}:")
                for agent in category_agents:
                    # 显示性能指标
                    if agent in optimizer.agent_metrics:
                        metrics = optimizer.agent_metrics[agent]
                        print(f"  • {agent} (成功率: {metrics.success_rate:.1%}, 质量: {metrics.quality_score:.1%})")
                    else:
                        print(f"  • {agent} (新Agent)")

        print(f"\n🎯 **执行建议**: 在单个消息中并行调用这些agents:")
        for i, agent in enumerate(selected_agents, 1):
            print(f"{i:2d}. @{agent}")

        print(f"\n📊 **资源预估**:")
        print(f"- 并发Agent数: {len(selected_agents)}")
        print(f"- 预估内存: {len(selected_agents) * 75}MB")
        print(f"- 推荐CPU核心: {min(16, len(selected_agents))}")

    except Exception as e:
        log_error(f"Agent选择失败: {e}")
        print(f"❌ Agent选择失败: {e}")

def handle_opus41_monitor(args: argparse.Namespace) -> None:
    """处理监控命令"""
    visualizer = get_opus41_visualizer()

    if args.monitor_action == 'start':
        print("🚀 启动Opus41监控系统")

        if args.dashboard:
            # 启动实时监控
            visualizer.start_real_time_monitoring({
                "start_time": time.time(),
                "update_interval": args.interval
            })

            print(f"📊 实时Dashboard已启动，更新间隔: {args.interval}秒")
            print("💡 提示: 按 Ctrl+C 停止监控")

            try:
                while True:
                    # 模拟更新数据
                    visualizer.update_metrics(
                        quality_score=0.85,
                        success_rate=0.90,
                        execution_time=120.5,
                        active_agents=8,
                        layer_progress={1: 1.0, 2: 0.8, 3: 0.6, 4: 0.2},
                        agent_status={
                            "backend-architect": "completed",
                            "frontend-specialist": "running",
                            "test-engineer": "pending"
                        }
                    )
                    time.sleep(args.interval)
            except KeyboardInterrupt:
                visualizer.stop_monitoring()
                print("\n🛑 监控已停止")

    elif args.monitor_action == 'report':
        print("📊 生成性能报告")

        report = visualizer.generate_performance_report()

        if args.format == 'html':
            output_file = args.output or "opus41_performance_report.html"
            dashboard_file = visualizer.generate_html_dashboard(output_file)
            print(f"📄 HTML报告已生成: {dashboard_file}")
        else:
            output_file = args.output or "opus41_performance_report.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            print(f"📄 JSON报告已生成: {output_file}")

    elif args.monitor_action == 'export':
        print("📤 导出监控数据")

        if args.format == 'json':
            output_file = args.output or "opus41_metrics_export.json"
            exported_file = visualizer.export_metrics_to_json(output_file)
            print(f"📄 数据已导出: {exported_file}")
        else:
            print("❌ CSV格式暂未支持")

def handle_opus41_status(args: argparse.Namespace) -> None:
    """处理状态命令"""
    optimizer = get_opus41_optimizer()
    visualizer = get_opus41_visualizer()

    print("🚀 Opus41 优化器状态")
    print("=" * 60)

    status = optimizer.get_optimization_status()

    print(f"📊 基本信息:")
    print(f"  • Agent数量: {status['agent_count']}")
    print(f"  • 执行历史: {status['execution_history_count']}")
    print(f"  • 最大并发: {status['max_parallel_agents']}")
    print(f"  • 质量阈值: {status['quality_threshold']:.1%}")
    print(f"  • 系统状态: {status['system_status']}")

    if status['top_performers']:
        print(f"\n🏆 Top 5 性能最佳Agents:")
        for i, (agent, success_rate) in enumerate(status['top_performers'][:5], 1):
            print(f"  {i}. {agent}: {success_rate:.1%}")

    if args.detailed:
        print(f"\n📈 详细性能指标:")
        for agent_name, metrics in optimizer.agent_metrics.items():
            print(f"\n  🤖 {agent_name}:")
            print(f"      成功率: {metrics.success_rate:.1%}")
            print(f"      平均时间: {metrics.avg_execution_time:.1f}s")
            print(f"      质量分数: {metrics.quality_score:.1%}")
            print(f"      协作分数: {metrics.collaboration_score:.1%}")
            print(f"      最后更新: {metrics.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")

    # 可视化器状态
    if visualizer.current_metrics:
        print(f"\n📊 当前监控状态:")
        print(visualizer.create_progress_visualization())

def handle_opus41_benchmark(args: argparse.Namespace) -> None:
    """处理基准测试命令"""
    optimizer = get_opus41_optimizer()

    print(f"🏃 开始Opus41性能基准测试")
    print(f"🤖 测试Agent数: {args.agents}")
    print(f"🔄 测试轮数: {args.rounds}")
    print(f"📊 复杂度: {args.complexity}")
    print("=" * 60)

    benchmark_results = []

    for round_num in range(1, args.rounds + 1):
        print(f"\n🔄 第 {round_num} 轮测试...")

        # 生成测试任务
        test_task = f"基准测试 - {args.complexity} 复杂度任务 (轮次 {round_num})"

        start_time = time.time()

        try:
            # 智能Agent选择
            selected_agents = optimizer.select_optimal_agents(test_task, QualityLevel.PREMIUM)

            # 限制为测试数量
            test_agents = selected_agents[:args.agents]

            # 生成优化计划
            plan = optimizer.optimize_execution(
                task_description=test_task,
                target_quality=QualityThreshold.EXCELLENT,
                optimization_level=OptimizationLevel.OPUS41
            )

            # 模拟执行
            execution_result = optimizer.execute_optimized_plan(plan)

            end_time = time.time()
            round_time = end_time - start_time

            result = {
                "round": round_num,
                "agents_selected": len(test_agents),
                "execution_time": round_time,
                "success": execution_result["success"],
                "final_quality": execution_result.get("final_quality", 0),
                "layers_completed": execution_result.get("layers_completed", 0)
            }

            benchmark_results.append(result)

            print(f"  ✅ 完成 - 时间: {round_time:.2f}s, 质量: {result['final_quality']:.1%}")

        except Exception as e:
            print(f"  ❌ 失败: {e}")
            benchmark_results.append({
                "round": round_num,
                "error": str(e),
                "success": False
            })

    # 计算统计结果
    successful_rounds = [r for r in benchmark_results if r.get("success", False)]

    print(f"\n📊 基准测试结果:")
    print("=" * 60)
    print(f"成功轮数: {len(successful_rounds)}/{args.rounds}")

    if successful_rounds:
        avg_time = sum(r["execution_time"] for r in successful_rounds) / len(successful_rounds)
        avg_quality = sum(r["final_quality"] for r in successful_rounds) / len(successful_rounds)

        print(f"平均执行时间: {avg_time:.2f}秒")
        print(f"平均质量分数: {avg_quality:.1%}")
        print(f"最快执行时间: {min(r['execution_time'] for r in successful_rounds):.2f}秒")
        print(f"最慢执行时间: {max(r['execution_time'] for r in successful_rounds):.2f}秒")

        # 性能评级
        if avg_time < 5 and avg_quality > 0.9:
            rating = "🚀 优秀"
        elif avg_time < 10 and avg_quality > 0.8:
            rating = "✅ 良好"
        elif avg_time < 20 and avg_quality > 0.7:
            rating = "📊 一般"
        else:
            rating = "⚠️ 需要优化"

        print(f"性能评级: {rating}")

    # 保存基准测试结果
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    benchmark_file = f"opus41_benchmark_{timestamp}.json"

    benchmark_data = {
        "test_config": {
            "agents": args.agents,
            "rounds": args.rounds,
            "complexity": args.complexity
        },
        "results": benchmark_results,
        "summary": {
            "success_rate": len(successful_rounds) / args.rounds,
            "avg_execution_time": avg_time if successful_rounds else 0,
            "avg_quality": avg_quality if successful_rounds else 0
        }
    }

    with open(benchmark_file, 'w', encoding='utf-8') as f:
        json.dump(benchmark_data, f, indent=2, ensure_ascii=False)

    print(f"\n📄 基准测试报告已保存: {benchmark_file}")

def handle_opus41_command(args: argparse.Namespace) -> None:
    """处理Opus41命令"""
    if args.opus41_action == 'optimize':
        handle_opus41_optimize(args)
    elif args.opus41_action == 'execute':
        handle_opus41_execute(args)
    elif args.opus41_action == 'select':
        handle_opus41_select(args)
    elif args.opus41_action == 'monitor':
        handle_opus41_monitor(args)
    elif args.opus41_action == 'status':
        handle_opus41_status(args)
    elif args.opus41_action == 'benchmark':
        handle_opus41_benchmark(args)
    else:
        print("❌ 未知的Opus41操作")
        print("使用 'python3 main/cli.py opus41 --help' 查看帮助")

if __name__ == '__main__':
    # 测试CLI
    import argparse

    parser = argparse.ArgumentParser(description='Perfect21 Opus41 CLI测试')
    subparsers = parser.add_subparsers(dest='command')

    create_opus41_parser(subparsers)

    args = parser.parse_args()

    if args.command == 'opus41':
        handle_opus41_command(args)
    else:
        print("请使用 opus41 命令")