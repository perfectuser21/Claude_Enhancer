#!/usr/bin/env python3
"""
执行监督系统演示
展示Perfect21的"管家"如何确保并行执行不退化
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from features.phase_executor import PhaseExecutor
from features.phase_executor.phase_executor import ExecutionPhase

def demonstrate_supervisor_system():
    """演示执行监督系统"""
    print("=" * 80)
    print("🎯 Perfect21 执行监督系统演示")
    print("展示'管家'如何确保Claude Code保持并行执行")
    print("=" * 80)

    # 创建带监督的PhaseExecutor
    executor = PhaseExecutor()

    print("\n" + "=" * 80)
    print("场景1：正常的并行执行")
    print("=" * 80)

    # 生成分析阶段指令（会自动显示监督提醒）
    result = executor.generate_phase_instructions(
        ExecutionPhase.ANALYSIS,
        {'requirement': '实现用户认证系统'}
    )

    print("\n监督系统已经提醒Claude Code要并行执行！")
    print("✅ 包含执行检查清单")
    print("✅ 包含智能提示")
    print("✅ 包含具体建议")

    # 模拟Claude Code执行结果
    print("\n" + "-" * 80)
    print("模拟Claude Code执行...")
    print("-" * 80)

    # 好的执行（并行）
    good_execution = {
        'agent_count': 3,
        'is_parallel': True,
        'sync_point_executed': True,
        'summary_generated': True,
        'todos_generated': True,
        'success': True,
        'total_operations': 10,
        'parallel_operations': 8
    }

    print("\n📊 记录执行结果...")
    executor.record_phase_result(ExecutionPhase.ANALYSIS, good_execution)
    print("✅ 质量验证通过！")
    print("✅ 执行模式：并行")
    print("✅ 监督系统满意！")

    print("\n" + "=" * 80)
    print("场景2：检测到退化的执行")
    print("=" * 80)

    # 生成设计阶段指令
    print("\n进入设计阶段...")
    result = executor.generate_phase_instructions(
        ExecutionPhase.DESIGN,
        {'last_phase': {'was_parallel': True}}
    )

    # 模拟差的执行（退化为串行）
    bad_execution = {
        'agent_count': 1,  # 只有1个agent！
        'is_parallel': False,  # 串行了！
        'sync_point_executed': False,
        'summary_generated': False,
        'success': False,
        'total_operations': 10,
        'parallel_operations': 0  # 全是串行！
    }

    print("\n📊 记录执行结果...")
    executor.record_phase_result(ExecutionPhase.DESIGN, bad_execution)

    print("\n🚨 监督系统检测到问题：")
    print("❌ 从并行退化为串行！")
    print("❌ Agent数量不足！")
    print("❌ 未执行同步点！")
    print("❌ 质量门失败！")

    print("\n" + "=" * 80)
    print("监督系统报告")
    print("=" * 80)

    # 获取执行报告
    supervisor_report = executor.supervisor.get_execution_report()
    print(f"\n📊 执行统计：")
    print(f"  总阶段数：{supervisor_report['statistics']['total_phases']}")
    print(f"  并行阶段：{supervisor_report['statistics']['parallel_phases']}")
    print(f"  串行阶段：{supervisor_report['statistics']['sequential_phases']}")
    print(f"  退化阶段：{supervisor_report['statistics']['degraded_phases']}")
    print(f"  并行率：{supervisor_report['parallel_rate']:.1f}%")

    # 获取守护者报告
    guardian_report = executor.guardian.get_guardian_report()
    print(f"\n🛡️ 质量守护报告：")
    print(f"  总检查项：{guardian_report['total_checks']}")
    print(f"  完成检查：{guardian_report['completed_checks']}")
    print(f"  通过检查：{guardian_report['passed_checks']}")
    print(f"  违规次数：{guardian_report['total_violations']}")

    # 获取性能摘要
    monitor_summary = executor.monitor.get_performance_summary()
    print(f"\n⚡ 性能监控摘要：")
    print(f"  监控阶段：{monitor_summary['total_phases']}")
    if 'average_metrics' in monitor_summary:
        for metric, values in monitor_summary['average_metrics'].items():
            if isinstance(values, dict):
                print(f"  {metric}: 平均={values.get('mean', 0):.2f}")

    print("\n" + "=" * 80)
    print("监督系统效果总结")
    print("=" * 80)
    print("""
✅ 主动提醒：在每个阶段开始前提醒并行要求
✅ 执行检查：验证执行计划是否符合要求
✅ 质量门控：不满足质量要求则阻止继续
✅ 退化检测：发现并行退化为串行立即警告
✅ 智能学习：从执行历史中学习模式
✅ 实时监控：跟踪执行过程收集性能数据

有了这个"管家"系统，Claude Code不会再忘记并行执行了！
    """)

    print("=" * 80)
    print("🎉 演示完成！")
    print("=" * 80)

if __name__ == '__main__':
    demonstrate_supervisor_system()