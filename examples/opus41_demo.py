#!/usr/bin/env python3
"""
Perfect21 Opus41 智能并行优化器演示
展示如何使用Opus41Optimizer进行智能任务分解和优化执行
"""

import os
import sys
import time
import json
from datetime import datetime

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

def demo_basic_optimization():
    """演示基础优化功能"""
    print("🚀 Opus41 基础优化演示")
    print("=" * 60)

    optimizer = get_opus41_optimizer()

    # 示例任务
    task = "实现一个高性能的电商平台，包含用户认证、商品管理、订单处理、支付集成和实时通知功能"

    print(f"📋 任务: {task}")
    print(f"🎯 开始智能优化...")

    # 生成优化计划
    plan = optimizer.optimize_execution(
        task_description=task,
        target_quality=QualityThreshold.EXCELLENT,
        optimization_level=OptimizationLevel.OPUS41
    )

    # 显示优化结果
    print(f"\n✅ 优化完成!")
    optimizer.display_execution_plan(plan)

    # 生成Task调用指令
    task_calls = optimizer.generate_task_calls(plan)

    print(f"\n🎯 **执行指令**: 请在单个消息中调用以下{len(task_calls)}个Task工具：")
    print("=" * 80)

    for i, call in enumerate(task_calls[:5], 1):  # 只显示前5个作为示例
        params = call["parameters"]
        print(f"\n**Task {i}: @{params['subagent_type']}**")
        print(f"Layer: {call['layer_name']}")
        print(f"Sync Points: {call['sync_points']}")

    if len(task_calls) > 5:
        print(f"\n... (还有 {len(task_calls) - 5} 个Task调用)")

    return plan

def demo_agent_selection():
    """演示智能Agent选择"""
    print("\n🤖 智能Agent选择演示")
    print("=" * 60)

    optimizer = get_opus41_optimizer()

    test_cases = [
        ("创建React前端应用", QualityLevel.PREMIUM),
        ("开发REST API后端", QualityLevel.BALANCED),
        ("构建AI推荐系统", QualityLevel.ULTIMATE),
        ("部署Kubernetes集群", QualityLevel.FAST)
    ]

    for task, quality_level in test_cases:
        print(f"\n📋 任务: {task}")
        print(f"🎯 质量级别: {quality_level.name}")

        selected_agents = optimizer.select_optimal_agents(task, quality_level)

        print(f"✅ 选择了 {len(selected_agents)} 个agents:")
        for i, agent in enumerate(selected_agents, 1):
            print(f"  {i:2d}. @{agent}")

        print(f"💡 建议: 在单个消息中并行调用这些agents")

def demo_quality_levels():
    """演示不同质量级别的差异"""
    print("\n🌟 质量级别对比演示")
    print("=" * 60)

    optimizer = get_opus41_optimizer()
    task = "开发一个微服务架构的博客系统"

    quality_levels = [
        QualityThreshold.MINIMUM,
        QualityThreshold.GOOD,
        QualityThreshold.EXCELLENT,
        QualityThreshold.PERFECT
    ]

    results = []

    for quality in quality_levels:
        print(f"\n🎯 质量级别: {quality.name} ({quality.value:.1%})")

        plan = optimizer.optimize_execution(
            task_description=task,
            target_quality=quality,
            optimization_level=OptimizationLevel.OPUS41
        )

        result = {
            "quality_level": quality.name,
            "target_value": quality.value,
            "total_agents": plan.resource_requirements['total_agents'],
            "concurrent_agents": plan.resource_requirements['concurrent_agents'],
            "estimated_time": plan.estimated_total_time,
            "success_probability": plan.success_probability,
            "layers": len(plan.execution_layers),
            "refinement_rounds": len(plan.refinement_rounds)
        }

        results.append(result)

        print(f"  📊 总Agent数: {result['total_agents']}")
        print(f"  ⚡ 最大并发: {result['concurrent_agents']}")
        print(f"  ⏱️ 预估时间: {result['estimated_time']}分钟")
        print(f"  🎯 成功概率: {result['success_probability']:.1%}")
        print(f"  📈 改进轮次: {result['refinement_rounds']}")

    # 对比分析
    print(f"\n📊 质量级别对比:")
    print(f"{'级别':<12} {'Agents':<8} {'并发':<6} {'时间':<8} {'成功率':<8} {'改进轮次':<8}")
    print("-" * 60)

    for result in results:
        print(f"{result['quality_level']:<12} "
              f"{result['total_agents']:<8} "
              f"{result['concurrent_agents']:<6} "
              f"{result['estimated_time']:<8} "
              f"{result['success_probability']:.1%}    "
              f"{result['refinement_rounds']:<8}")

def demo_real_time_monitoring():
    """演示实时监控功能"""
    print("\n📊 实时监控演示")
    print("=" * 60)

    visualizer = get_opus41_visualizer()

    # 启动监控
    visualizer.start_real_time_monitoring({
        "task": "演示任务",
        "start_time": datetime.now().isoformat()
    })

    print("🚀 启动实时监控...")

    # 模拟执行过程
    simulation_steps = [
        {"desc": "初始化", "quality": 0.3, "success": 0.5, "time": 10, "agents": 2},
        {"desc": "第1层执行", "quality": 0.5, "success": 0.7, "time": 30, "agents": 5},
        {"desc": "第2层执行", "quality": 0.65, "success": 0.8, "time": 60, "agents": 8},
        {"desc": "第3层执行", "quality": 0.75, "success": 0.85, "time": 120, "agents": 12},
        {"desc": "质量保证", "quality": 0.85, "success": 0.9, "time": 150, "agents": 6},
        {"desc": "第1轮改进", "quality": 0.9, "success": 0.92, "time": 180, "agents": 4},
        {"desc": "第2轮改进", "quality": 0.94, "success": 0.95, "time": 200, "agents": 3},
        {"desc": "最终验证", "quality": 0.96, "success": 0.98, "time": 220, "agents": 2}
    ]

    try:
        for i, step in enumerate(simulation_steps):
            print(f"\n📈 步骤 {i+1}: {step['desc']}")

            # 更新指标
            visualizer.update_metrics(
                quality_score=step['quality'],
                success_rate=step['success'],
                execution_time=step['time'],
                active_agents=step['agents'],
                layer_progress={
                    1: min(1.0, i * 0.2),
                    2: max(0.0, min(1.0, (i-2) * 0.25)),
                    3: max(0.0, min(1.0, (i-4) * 0.25)),
                    4: max(0.0, min(1.0, (i-6) * 0.5))
                },
                agent_status={
                    "backend-architect": "completed" if i > 2 else "running" if i > 0 else "pending",
                    "frontend-specialist": "completed" if i > 3 else "running" if i > 1 else "pending",
                    "test-engineer": "completed" if i > 4 else "running" if i > 3 else "pending",
                    "security-auditor": "completed" if i > 5 else "running" if i > 4 else "pending"
                },
                refinement_progress=max(0.0, min(1.0, (i-5) * 0.33))
            )

            # 显示进度
            print(visualizer.create_progress_visualization())

            time.sleep(1)  # 模拟执行时间

    except KeyboardInterrupt:
        print("\n⏸️ 演示被用户中断")

    finally:
        # 停止监控
        visualizer.stop_monitoring()

        # 生成报告
        report = visualizer.generate_performance_report()
        print(f"\n📊 性能报告:")
        print(f"  平均质量分数: {report['quality_metrics']['avg_quality_score']:.1%}")
        print(f"  质量改进: {report['quality_metrics']['quality_improvement']:.1%}")
        print(f"  平均成功率: {report['performance_metrics']['avg_success_rate']:.1%}")

        # 生成HTML Dashboard
        dashboard_file = visualizer.generate_html_dashboard("opus41_demo_dashboard.html")
        print(f"📄 Dashboard已生成: {dashboard_file}")

def demo_performance_comparison():
    """演示性能对比"""
    print("\n⚔️ 性能对比演示")
    print("=" * 60)

    optimizer = get_opus41_optimizer()

    # 测试不同优化级别
    optimization_levels = [
        OptimizationLevel.BASIC,
        OptimizationLevel.ADAPTIVE,
        OptimizationLevel.INTELLIGENT,
        OptimizationLevel.OPUS41
    ]

    task = "构建一个分布式日志分析系统"
    results = []

    for level in optimization_levels:
        print(f"\n🎯 测试优化级别: {level.name}")

        start_time = time.time()

        plan = optimizer.optimize_execution(
            task_description=task,
            target_quality=QualityThreshold.EXCELLENT,
            optimization_level=level
        )

        optimization_time = time.time() - start_time

        result = {
            "level": level.name,
            "optimization_time": optimization_time,
            "total_agents": plan.resource_requirements['total_agents'],
            "estimated_time": plan.estimated_total_time,
            "success_probability": plan.success_probability,
            "layers": len(plan.execution_layers),
            "refinements": len(plan.refinement_rounds)
        }

        results.append(result)

        print(f"  ⏱️ 优化耗时: {optimization_time:.3f}秒")
        print(f"  🤖 Agent数: {result['total_agents']}")
        print(f"  📊 成功概率: {result['success_probability']:.1%}")

    # 对比表格
    print(f"\n📊 优化级别性能对比:")
    print(f"{'级别':<12} {'优化耗时':<10} {'Agent数':<8} {'预估时间':<10} {'成功率':<8} {'改进轮次':<8}")
    print("-" * 70)

    for result in results:
        print(f"{result['level']:<12} "
              f"{result['optimization_time']:.3f}s     "
              f"{result['total_agents']:<8} "
              f"{result['estimated_time']:<10} "
              f"{result['success_probability']:.1%}    "
              f"{result['refinements']:<8}")

def demo_export_and_reporting():
    """演示导出和报告功能"""
    print("\n📄 导出和报告演示")
    print("=" * 60)

    optimizer = get_opus41_optimizer()
    visualizer = get_opus41_visualizer()

    # 生成示例计划
    task = "开发企业级CRM系统"
    plan = optimizer.optimize_execution(
        task_description=task,
        target_quality=QualityThreshold.PERFECT,
        optimization_level=OptimizationLevel.OPUS41
    )

    # 1. 导出执行计划
    plan_data = {
        "task": plan.task_description,
        "optimization_level": plan.optimization_level.value,
        "target_quality": plan.target_quality.value,
        "total_agents": plan.resource_requirements['total_agents'],
        "estimated_time": plan.estimated_total_time,
        "success_probability": plan.success_probability,
        "execution_layers": [
            {
                "layer_id": layer.layer_id,
                "layer_name": layer.layer_name,
                "agents": layer.agents,
                "estimated_time": layer.estimated_time
            }
            for layer in plan.execution_layers
        ]
    }

    plan_file = f"opus41_plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(plan_file, 'w', encoding='utf-8') as f:
        json.dump(plan_data, f, indent=2, ensure_ascii=False)

    print(f"📋 执行计划已导出: {plan_file}")

    # 2. 生成Task调用脚本
    task_calls = optimizer.generate_task_calls(plan)

    script_content = f"""#!/usr/bin/env python3
\"\"\"
Opus41自动生成的任务执行脚本
任务: {task}
生成时间: {datetime.now().isoformat()}
\"\"\"

# 这是一个示例脚本，展示如何在代码中调用Task工具
# 在实际使用中，您需要在Claude Code中手动调用这些Task工具

task_calls = [
"""

    for i, call in enumerate(task_calls):
        script_content += f"""    # Task {i+1}: @{call['parameters']['subagent_type']}
    {{
        "tool_name": "Task",
        "parameters": {{
            "subagent_type": "{call['parameters']['subagent_type']}",
            "description": "{call['parameters']['description']}",
            "prompt": \"\"\"
{call['parameters']['prompt'][:200]}...
\"\"\"
        }}
    }},
"""

    script_content += """
]

print(f"准备调用 {len(task_calls)} 个Task工具")
print("请在Claude Code中手动执行这些调用")
"""

    script_file = f"opus41_execution_script_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
    with open(script_file, 'w', encoding='utf-8') as f:
        f.write(script_content)

    print(f"🐍 执行脚本已生成: {script_file}")

    # 3. 生成HTML Dashboard
    dashboard_file = visualizer.generate_html_dashboard("opus41_demo_final_dashboard.html")
    print(f"📊 HTML Dashboard已生成: {dashboard_file}")

    # 4. 导出优化器状态
    status = optimizer.get_optimization_status()
    status_file = f"opus41_status_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(status_file, 'w', encoding='utf-8') as f:
        json.dump(status, f, indent=2, ensure_ascii=False, default=str)

    print(f"⚙️ 系统状态已导出: {status_file}")

def main():
    """主演示程序"""
    print("🚀 Perfect21 Opus41 智能并行优化器 - 完整演示")
    print("=" * 80)
    print("这是一个交互式演示，展示Opus41的各项功能")
    print("=" * 80)

    demos = [
        ("1", "基础优化功能", demo_basic_optimization),
        ("2", "智能Agent选择", demo_agent_selection),
        ("3", "质量级别对比", demo_quality_levels),
        ("4", "实时监控", demo_real_time_monitoring),
        ("5", "性能对比", demo_performance_comparison),
        ("6", "导出和报告", demo_export_and_reporting),
        ("a", "运行所有演示", None)
    ]

    while True:
        print(f"\n📋 可用演示:")
        for code, name, _ in demos:
            print(f"  {code}. {name}")
        print(f"  q. 退出")

        choice = input(f"\n请选择演示 (1-6, a, q): ").strip().lower()

        if choice == 'q':
            print("👋 感谢使用Opus41演示!")
            break
        elif choice == 'a':
            print("🚀 运行所有演示...")
            for code, name, func in demos[:-1]:  # 排除"运行所有"选项
                if func:
                    print(f"\n" + "="*80)
                    func()
            print(f"\n✅ 所有演示完成!")
        else:
            demo_func = None
            for code, name, func in demos:
                if code == choice and func:
                    demo_func = func
                    break

            if demo_func:
                try:
                    demo_func()
                except KeyboardInterrupt:
                    print(f"\n⏸️ 演示被用户中断")
                except Exception as e:
                    print(f"\n❌ 演示出错: {e}")
            else:
                print(f"❌ 无效选择: {choice}")

if __name__ == '__main__':
    main()