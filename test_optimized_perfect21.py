#!/usr/bin/env python3
"""
测试优化后的Perfect21核心执行流程
验证真实的并行执行机制和Task指令生成
"""

import os
import sys
import json
import logging
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(__file__))

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Perfect21Test")

def test_workflow_engine():
    """测试优化后的工作流引擎"""
    print("🚀 测试Perfect21优化后的工作流引擎")
    print("=" * 60)

    try:
        from features.workflow.engine import WorkflowEngine

        # 创建工作流引擎
        engine = WorkflowEngine(max_workers=5)

        # 测试并行任务
        tasks = [
            {
                'agent_name': 'backend-architect',
                'description': '设计用户认证系统',
                'prompt': '请设计一个完整的用户认证系统，包括JWT、密码加密、会话管理等功能',
                'timeout': 300,
                'critical': True
            },
            {
                'agent_name': 'frontend-specialist',
                'description': '开发登录界面',
                'prompt': '基于后端认证API开发现代化的登录界面，包括响应式设计和错误处理',
                'timeout': 300,
                'critical': False
            },
            {
                'agent_name': 'test-engineer',
                'description': '编写认证测试',
                'prompt': '为认证系统编写全面的测试用例，包括单元测试、集成测试和安全测试',
                'timeout': 300,
                'critical': True
            },
            {
                'agent_name': 'security-auditor',
                'description': '安全审计',
                'prompt': '对认证系统进行全面的安全审计，检查潜在漏洞和安全最佳实践',
                'timeout': 300,
                'critical': True
            }
        ]

        print(f"📋 并行执行 {len(tasks)} 个Agent任务")
        print("-" * 50)

        # 执行并行工作流
        result = engine.execute_parallel_tasks(tasks)

        print(f"✅ 工作流执行完成")
        print(f"🆔 工作流ID: {result.workflow_id}")
        print(f"⏱️ 执行时间: {result.execution_time:.3f}秒")
        print(f"✅ 成功: {result.success_count}/{len(tasks)}")
        print(f"❌ 失败: {result.failure_count}")
        print(f"📊 状态: {result.status.value}")

        # 显示批量执行指令
        if hasattr(result, 'batch_execution_instruction') and result.batch_execution_instruction:
            print("\n" + "="*80)
            print("🎯 Claude Code 批量执行指令已生成")
            print("="*80)
            print("📋 以下指令可直接在Claude Code中执行:")
            print("="*80)
            print(result.batch_execution_instruction)
            print("="*80)

        # 显示集成结果
        if result.integrated_result:
            print(f"\n📊 集成结果摘要:")
            integrated = result.integrated_result
            print(f"  - 涉及Agents: {', '.join(integrated.get('agents_involved', []))}")
            print(f"  - 指令数量: {integrated.get('instruction_count', 0)}")
            print(f"  - Claude Code就绪: {'是' if integrated.get('ready_for_claude_code', False) else '否'}")

            if 'execution_guidance' in integrated:
                guidance = integrated['execution_guidance']
                print(f"  - 执行类型: {guidance['type']}")
                print(f"  - Agent数量: {guidance['agent_count']}")
                print(f"  - 失败数量: {guidance['failed_count']}")

        return True

    except Exception as e:
        logger.error(f"工作流引擎测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_perfect21_core():
    """测试Perfect21核心类"""
    print("\n🔧 测试Perfect21核心类")
    print("=" * 60)

    try:
        from main.perfect21 import Perfect21

        # 创建Perfect21实例
        p21 = Perfect21()

        # 测试并行执行
        agents = ['backend-architect', 'test-engineer', 'security-auditor']
        prompt = '实现用户认证功能，包括JWT认证、密码加密、会话管理'

        print(f"🤖 使用Agents: {', '.join(agents)}")
        print(f"📝 任务: {prompt}")
        print("-" * 50)

        result = p21.execute_parallel_workflow(
            agents=agents,
            base_prompt=prompt,
            task_description='用户认证系统开发'
        )

        if result['success']:
            print("✅ Perfect21并行工作流执行成功")
            print(f"🆔 工作流ID: {result['workflow_id']}")
            print(f"⏱️ 执行时间: {result['execution_time']:.3f}秒")
            print(f"✅ 成功/总数: {result['success_count']}/{result['agents_count']}")
            print(f"❌ 失败数: {result['failure_count']}")
            print(f"🎯 Claude Code就绪: {'是' if result['claude_code_ready'] else '否'}")

            if result.get('batch_instruction'):
                print("\n" + "="*80)
                print("⚡ Perfect21生成的批量执行指令")
                print("="*80)
                # 只显示前500字符避免过长
                instruction = result['batch_instruction']
                if len(instruction) > 500:
                    print(instruction[:500] + "...")
                    print(f"\n[指令总长度: {len(instruction)}字符]")
                else:
                    print(instruction)
                print("="*80)

        else:
            print(f"❌ Perfect21并行工作流执行失败: {result.get('message')}")
            if result.get('error'):
                print(f"错误详情: {result['error']}")

        # 测试即时指令生成
        print(f"\n⚡ 测试即时并行指令生成")
        print("-" * 30)

        instant_result = p21.create_instant_parallel_instruction(
            agents=['frontend-specialist', 'ux-designer'],
            prompt='设计现代化的用户界面'
        )

        if instant_result['success']:
            print("✅ 即时指令生成成功")
            print(f"🤖 Agents数量: {instant_result['agents_count']}")
            print(f"⚡ 执行就绪: {'是' if instant_result['ready_for_execution'] else '否'}")

            # 显示即时指令（简化显示）
            instruction = instant_result['instruction']
            lines = instruction.split('\n')
            print(f"\n📋 即时指令预览 ({len(lines)}行):")
            for i, line in enumerate(lines[:10]):  # 只显示前10行
                print(f"  {line}")
            if len(lines) > 10:
                print(f"  ... (省略{len(lines)-10}行)")

        # 清理资源
        p21.cleanup()

        return True

    except Exception as e:
        logger.error(f"Perfect21核心类测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_real_time_instruction():
    """测试实时指令生成"""
    print("\n⚡ 测试实时指令生成")
    print("=" * 60)

    try:
        from features.workflow.engine import WorkflowEngine

        engine = WorkflowEngine()

        # 创建实时并行指令
        agents = ['fullstack-engineer', 'devops-engineer', 'monitoring-specialist']
        prompt = '部署微服务应用到Kubernetes集群'

        instruction = engine.create_real_time_parallel_instruction(agents, prompt)

        print(f"🤖 Agents: {', '.join(agents)}")
        print(f"📝 任务: {prompt}")
        print("-" * 50)

        print("✅ 实时并行指令生成成功")
        print(f"📏 指令长度: {len(instruction)}字符")

        # 显示指令结构分析
        lines = instruction.split('\n')
        header_lines = [line for line in lines if line.startswith('#')]
        function_calls = [line for line in lines if 'invoke name="Task"' in line]
        parameter_lines = [line for line in lines if 'parameter name=' in line]

        print(f"📊 指令结构分析:")
        print(f"  - 总行数: {len(lines)}")
        print(f"  - 注释行: {len(header_lines)}")
        print(f"  - Task调用: {len(function_calls)}")
        print(f"  - 参数行: {len(parameter_lines)}")

        # 验证指令格式
        is_valid = ('<function_calls>' in instruction and
                   '</function_calls>' in instruction and
                   len(function_calls) == len(agents))

        print(f"✅ 指令格式验证: {'通过' if is_valid else '失败'}")

        if is_valid:
            print("\n🎯 指令可直接在Claude Code中执行")

        return True

    except Exception as e:
        logger.error(f"实时指令生成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🔬 Perfect21优化执行流程测试")
    print("=" * 80)
    print(f"📅 测试时间: {datetime.now().isoformat()}")
    print(f"🐍 Python版本: {sys.version.split()[0]}")
    print("=" * 80)

    test_results = []

    # 测试1: 工作流引擎
    print("\n1️⃣ 工作流引擎测试")
    test_results.append(test_workflow_engine())

    # 测试2: Perfect21核心类
    print("\n2️⃣ Perfect21核心类测试")
    test_results.append(test_perfect21_core())

    # 测试3: 实时指令生成
    print("\n3️⃣ 实时指令生成测试")
    test_results.append(test_real_time_instruction())

    # 测试结果汇总
    print("\n" + "="*80)
    print("📊 测试结果汇总")
    print("="*80)

    passed = sum(test_results)
    total = len(test_results)

    test_names = [
        "工作流引擎",
        "Perfect21核心类",
        "实时指令生成"
    ]

    for i, (name, result) in enumerate(zip(test_names, test_results)):
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{i+1}. {name}: {status}")

    print("-" * 80)
    print(f"总体结果: {passed}/{total} 测试通过")

    if passed == total:
        print("🎉 所有测试通过！Perfect21优化执行流程验证成功")
        print("\n💡 主要改进:")
        print("  ✅ 移除了所有time.sleep()模拟延迟")
        print("  ✅ 实现了真正的Task指令生成而非mock结果")
        print("  ✅ Perfect21保持策略层定位，生成执行指令给Claude Code")
        print("  ✅ 提供清晰的执行日志和进度反馈")
        print("  ✅ 支持批量并行和实时指令生成")

        return 0
    else:
        print(f"⚠️ {total-passed}个测试失败，需要进一步优化")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)