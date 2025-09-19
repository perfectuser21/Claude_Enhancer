#!/usr/bin/env python3
"""
测试Perfect21规则引擎
验证规则匹配和执行指导生成
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rules.rule_engine import Perfect21RuleEngine


def test_rule_engine():
    """测试规则引擎的核心功能"""

    print("=" * 70)
    print("Perfect21 规则引擎测试")
    print("=" * 70)

    engine = Perfect21RuleEngine()

    # 测试场景
    test_cases = [
        {
            'description': "认证系统开发",
            'task': "实现用户登录系统，包括JWT认证和权限管理",
            'expected_type': 'authentication'
        },
        {
            'description': "API接口开发",
            'task': "开发RESTful API接口，实现用户的CRUD操作",
            'expected_type': 'api_development'
        },
        {
            'description': "数据库设计",
            'task': "设计用户表和订单表的数据库Schema",
            'expected_type': 'database_design'
        },
        {
            'description': "前端组件开发",
            'task': "开发React登录组件，要求响应式设计",
            'expected_type': 'frontend_development'
        },
        {
            'description': "性能优化",
            'task': "优化数据库查询性能，减少API响应时间",
            'expected_type': 'performance_optimization'
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"测试场景 {i}: {test_case['description']}")
        print(f"{'='*70}")
        print(f"任务描述: {test_case['task']}")

        # 分析任务
        guidance = engine.analyze_task(test_case['task'])

        # 验证结果
        print(f"\n📊 分析结果:")
        print(f"  识别类型: {guidance['task_type']}")
        print(f"  期望类型: {test_case['expected_type']}")
        print(f"  匹配结果: {'✅ 正确' if guidance['task_type'] == test_case['expected_type'] else '❌ 错误'}")

        # 显示执行指导
        exec_guidance = guidance['execution_guidance']
        print(f"\n🤖 执行指导:")
        print(f"  需要Agents: {', '.join(exec_guidance['agents_to_use'])}")
        print(f"  执行模式: {exec_guidance['execution_mode']}")
        print(f"  并行执行: {'是' if exec_guidance['parallel_execution'] else '否'}")

        # 显示质量要求
        if exec_guidance['quality_requirements']:
            print(f"\n📋 质量要求:")
            for req in exec_guidance['quality_requirements']:
                print(f"  - {req}")

        # 显示最佳实践
        if guidance['best_practices']:
            print(f"\n💡 最佳实践:")
            for practice in guidance['best_practices'][:3]:  # 只显示前3个
                print(f"  - {practice}")

        # 显示给Claude的指令
        print(f"\n📝 给Claude Code的执行指令预览:")
        instructions = guidance['instructions_for_claude'].split('\n')
        for line in instructions[:15]:  # 只显示前15行
            print(f"  {line}")
        if len(instructions) > 15:
            print(f"  ... (共{len(instructions)}行)")

    # 测试Git Hook指导
    print(f"\n{'='*70}")
    print("Git Hook测试")
    print(f"{'='*70}")

    hook_tests = [
        ('pre_commit', {'branch': 'main', 'files_changed': 10}),
        ('pre_push', {'branch': 'feature/login', 'remote': 'origin'}),
        ('post_merge', {'branch': 'develop', 'merged_from': 'feature/api'})
    ]

    for hook_name, context in hook_tests:
        print(f"\n🔗 Hook: {hook_name}")
        print(f"   上下文: {context}")

        hook_guidance = engine.get_hook_guidance(hook_name, context)

        if hook_guidance['should_trigger']:
            print(f"   触发: ✅ 是")
            print(f"   必需Agents: {', '.join(hook_guidance['required_agents'])}")
            if hook_guidance.get('optional_agents'):
                print(f"   可选Agents: {', '.join(hook_guidance['optional_agents'])}")
            if hook_guidance.get('strict_mode'):
                print(f"   严格模式: ⚠️ 启用（主分支）")
        else:
            print(f"   触发: ❌ 否")

    # 测试质量门检查
    print(f"\n{'='*70}")
    print("质量门检查测试")
    print(f"{'='*70}")

    test_metrics = {
        '代码覆盖率': 85,
        '圈复杂度': 8,
        'API响应时间': {'p95': 180, 'p99': 450},
        '页面加载时间': 2.5,
        '内存使用': 400
    }

    print(f"测试指标: {test_metrics}")

    quality_results = engine.check_quality_gates(test_metrics)

    print(f"\n质量检查结果:")
    print(f"  总体通过: {'✅ 是' if quality_results['passed'] else '❌ 否'}")

    if quality_results['checks']:
        print(f"  通过的检查:")
        for check in quality_results['checks']:
            print(f"    - {check}")

    if quality_results['failed_checks']:
        print(f"  失败的检查:")
        for check in quality_results['failed_checks']:
            print(f"    - ❌ {check}")

    print(f"\n{'='*70}")
    print("测试完成!")
    print(f"{'='*70}")


if __name__ == "__main__":
    test_rule_engine()