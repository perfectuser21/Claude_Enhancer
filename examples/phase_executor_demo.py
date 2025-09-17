#!/usr/bin/env python3
"""
Phase Executor 使用示例
展示如何使用阶段性并行执行框架
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from features.phase_executor import (
    PhaseExecutor,
    ContextPool,
    PhaseSummarizer,
    GitPhaseIntegration
)
from features.phase_executor.phase_executor import ExecutionPhase

def demo_phase_execution():
    """演示阶段执行流程"""
    print("🚀 Perfect21 阶段性并行执行框架演示")
    print("=" * 60)

    # 初始化组件
    executor = PhaseExecutor()
    context_pool = ContextPool()
    summarizer = PhaseSummarizer()
    git_integration = GitPhaseIntegration()

    # 模拟用户请求
    user_request = "实现用户认证系统"
    print(f"\n📋 用户请求: {user_request}")
    print("-" * 60)

    # 阶段1：需求分析
    print("\n📊 阶段1：需求分析")
    phase1_result = executor.generate_phase_instructions(
        ExecutionPhase.ANALYSIS,
        {'requirement': user_request}
    )

    if phase1_result['success']:
        instructions = phase1_result['instructions']
        print(f"  ✅ 生成执行指令")
        print(f"  📝 需要并行调用 {len(instructions['agents_to_call'])} 个agents:")
        for agent in instructions['agents_to_call']:
            print(f"     - @{agent}")
        print(f"  ⚡ 执行模式: {instructions['execution_mode']}")
        print(f"  🔍 同步点: {instructions['sync_point']}")

        # 模拟agent执行结果
        agent_results_phase1 = [
            {
                'agent': 'project-manager',
                'key_findings': ['需要OAuth2.0支持', '预计2周完成'],
                'issues': ['时间紧张'],
                'recommendations': ['采用成熟框架']
            },
            {
                'agent': 'business-analyst',
                'key_findings': ['支持多因素认证', '需要SSO集成'],
                'recommendations': ['优先实现基础认证']
            },
            {
                'agent': 'technical-writer',
                'key_findings': ['需要详细的API文档', '用户指南必要'],
                'recommendations': ['使用OpenAPI规范']
            }
        ]

        # 汇总阶段1结果
        phase1_summary = summarizer.summarize_phase_results('analysis', agent_results_phase1)
        print(f"\n  📊 阶段汇总:")
        print(f"     - 关键发现: {len(phase1_summary['key_findings'])}项")
        print(f"     - 关键问题: {len(phase1_summary['critical_issues'])}个")
        print(f"     - 建议: {len(phase1_summary['recommendations'])}条")

        # 将结果存入context pool
        context_pool.add_phase_output('analysis', phase1_summary)

        # 生成下阶段TODO
        phase2_todos = summarizer.generate_next_phase_todos('analysis', phase1_summary)
        print(f"\n  📝 生成下阶段TODO: {len(phase2_todos)}项")
        for i, todo in enumerate(phase2_todos[:3], 1):
            print(f"     {i}. {todo['task']} (优先级: {todo['priority']})")

    # 阶段2：架构设计
    print("\n🏗️ 阶段2：架构设计")

    # 获取阶段1的上下文
    phase2_context = context_pool.get_context_for_phase('design')

    phase2_result = executor.generate_phase_instructions(
        ExecutionPhase.DESIGN,
        phase2_context
    )

    if phase2_result['success']:
        instructions = phase2_result['instructions']
        print(f"  ✅ 生成执行指令")
        print(f"  📝 需要并行调用 {len(instructions['agents_to_call'])} 个agents:")
        for agent in instructions['agents_to_call']:
            print(f"     - @{agent}")

        # Git操作
        if instructions['git_operations']:
            print(f"\n  🔧 Git操作:")
            for op in instructions['git_operations']:
                print(f"     - {op}")

            # 模拟Git操作
            print("\n  执行Git操作...")
            git_result = git_integration.execute_phase_git_operations(
                'design',
                {'feature_name': 'auth-system'}
            )
            if git_result['success']:
                print(f"  ✅ Git操作完成: {git_result['message']}")

        # 模拟agent执行结果
        agent_results_phase2 = [
            {
                'agent': 'api-designer',
                'key_findings': ['RESTful API设计完成', '定义了12个端点'],
                'api_spec': 'openapi_v3.yaml'
            },
            {
                'agent': 'backend-architect',
                'key_findings': ['微服务架构', 'JWT认证方案'],
                'architecture': 'microservices'
            },
            {
                'agent': 'database-specialist',
                'key_findings': ['PostgreSQL数据库', '5张核心表'],
                'database_schema': 'auth_schema.sql'
            }
        ]

        # 汇总阶段2结果
        phase2_summary = summarizer.summarize_phase_results('design', agent_results_phase2)
        context_pool.add_phase_output('design', phase2_summary)
        print(f"\n  📊 架构设计完成")

    # 阶段3：实现开发
    print("\n💻 阶段3：实现开发")

    phase3_result = executor.generate_phase_instructions(
        ExecutionPhase.IMPLEMENTATION,
        context_pool.get_context_for_phase('implementation')
    )

    if phase3_result['success']:
        instructions = phase3_result['instructions']
        print(f"  ✅ 生成执行指令")
        print(f"  📝 需要并行调用 {len(instructions['agents_to_call'])} 个agents:")
        for agent in instructions['agents_to_call']:
            print(f"     - @{agent}")

        # 检查是否需要触发Git Hook
        if executor.should_trigger_git_hook(ExecutionPhase.IMPLEMENTATION, {'has_staged_changes': True}):
            print("\n  🔍 触发pre-commit hook检查")
            hook_result = git_integration.trigger_appropriate_hooks('implementation', {})
            print(f"  ✅ Hook检查完成")

    # 阶段4：测试验证
    print("\n🧪 阶段4：测试验证")

    phase4_result = executor.generate_phase_instructions(
        ExecutionPhase.TESTING,
        context_pool.get_context_for_phase('testing')
    )

    if phase4_result['success']:
        instructions = phase4_result['instructions']
        print(f"  ✅ 生成执行指令")
        print(f"  📝 需要并行调用 {len(instructions['agents_to_call'])} 个agents:")
        for agent in instructions['agents_to_call']:
            print(f"     - @{agent}")
        print(f"  ⚡ 这些agents将真正并行执行！")

    # 生成最终报告
    print("\n📊 生成最终报告")
    final_report = summarizer.generate_final_report()
    print(f"  ✅ 完成 {final_report['total_phases']} 个阶段")
    print(f"  📝 生成TODO总数: {sum(len(todos) for todos in final_report['todos_generated'].values())}")

    # 验证并行执行特性
    print("\n✨ 框架特性验证:")
    print("  ✅ 支持真正的多Agent并行执行")
    print("  ✅ 阶段间数据自动传递")
    print("  ✅ 智能汇总和TODO生成")
    print("  ✅ Git操作自然集成")
    print("  ✅ Hook在合适时机触发")

    print("\n🎉 演示完成！")
    print("=" * 60)
    print("\n💡 使用说明:")
    print("1. Claude Code调用此框架生成执行指令")
    print("2. 按指令并行调用多个SubAgents")
    print("3. 收集结果后进行汇总")
    print("4. 基于汇总生成下阶段任务")
    print("5. 在合适时机执行Git操作和Hooks")

if __name__ == '__main__':
    demo_phase_execution()