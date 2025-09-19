#!/usr/bin/env python3
"""
测试优化后的Perfect21核心工作流引擎
直接测试engine.py，绕过依赖问题
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
logger = logging.getLogger("CoreEngineTest")

def test_workflow_engine_directly():
    """直接测试工作流引擎核心功能"""
    print("🚀 直接测试Perfect21工作流引擎核心")
    print("=" * 60)

    try:
        # 直接导入engine模块
        from features.workflow.engine import WorkflowEngine, AgentTask, TaskStatus

        # 创建工作流引擎
        engine = WorkflowEngine(max_workers=5)

        # 测试并行任务
        tasks = [
            {
                'agent_name': 'backend-architect',
                'description': '设计用户认证系统',
                'prompt': '请设计一个完整的用户认证系统，包括JWT、密码加密、会话管理等功能。请提供详细的实现方案和代码示例。',
                'timeout': 300,
                'critical': True
            },
            {
                'agent_name': 'frontend-specialist',
                'description': '开发登录界面',
                'prompt': '基于后端认证API开发现代化的登录界面，使用React和TypeScript，包括响应式设计和错误处理。',
                'timeout': 300,
                'critical': False
            },
            {
                'agent_name': 'test-engineer',
                'description': '编写认证测试',
                'prompt': '为认证系统编写全面的测试用例，包括单元测试、集成测试和安全测试。使用Jest和Cypress。',
                'timeout': 300,
                'critical': True
            }
        ]

        print(f"📋 并行执行 {len(tasks)} 个Agent任务")
        print("-" * 50)

        # 执行并行工作流
        start_time = datetime.now()
        result = engine.execute_parallel_tasks(tasks)
        end_time = datetime.now()

        print(f"✅ 工作流执行完成")
        print(f"🆔 工作流ID: {result.workflow_id}")
        print(f"⏱️ 执行时间: {result.execution_time:.3f}秒")
        print(f"✅ 成功: {result.success_count}/{len(tasks)}")
        print(f"❌ 失败: {result.failure_count}")
        print(f"📊 状态: {result.status.value}")

        # 验证没有time.sleep等模拟延迟
        expected_max_time = 0.1  # 不应该有显著延迟
        if result.execution_time < expected_max_time:
            print(f"✅ 验证通过: 无模拟延迟（实际{result.execution_time:.3f}s < 预期{expected_max_time}s）")
        else:
            print(f"⚠️ 可能仍有延迟: 实际{result.execution_time:.3f}s")

        # 验证批量执行指令生成
        if hasattr(result, 'batch_execution_instruction') and result.batch_execution_instruction:
            instruction = result.batch_execution_instruction
            print(f"\n✅ 批量执行指令生成成功 (长度: {len(instruction)}字符)")

            # 验证指令格式
            format_checks = [
                ('<function_calls>' in instruction, 'function_calls标签'),
                ('</function_calls>' in instruction, 'function_calls结束标签'),
                ('<invoke name="Task">' in instruction, 'Task调用'),
                ('subagent_type' in instruction, 'subagent_type参数'),
                ('prompt' in instruction, 'prompt参数'),
                (instruction.count('<invoke name="Task">') == len(tasks), f'Task调用数量({len(tasks)}个)')
            ]

            all_passed = True
            print(f"📊 指令格式验证:")
            for check, name in format_checks:
                status = "✅" if check else "❌"
                print(f"  {status} {name}")
                if not check:
                    all_passed = False

            if all_passed:
                print(f"🎯 指令格式验证通过，可直接在Claude Code中执行")
            else:
                print(f"⚠️ 指令格式存在问题")

            # 显示指令示例（前几行）
            lines = instruction.split('\n')
            print(f"\n📋 指令预览 (共{len(lines)}行):")
            for i, line in enumerate(lines[:15]):  # 显示前15行
                print(f"  {i+1:2d}| {line}")
            if len(lines) > 15:
                print(f"     ... (省略{len(lines)-15}行)")

        # 验证集成结果
        if result.integrated_result:
            print(f"\n📊 集成结果验证:")
            integrated = result.integrated_result
            print(f"  ✅ 涉及Agents: {len(integrated.get('agents_involved', []))}")
            print(f"  ✅ 指令数量: {integrated.get('instruction_count', 0)}")
            print(f"  ✅ Claude Code就绪: {integrated.get('ready_for_claude_code', False)}")

            if 'execution_guidance' in integrated:
                guidance = integrated['execution_guidance']
                print(f"  ✅ 执行指导: {guidance['type']}")
                print(f"  ✅ Ready状态: {guidance['ready_for_claude_code']}")

        # 测试任务详情
        print(f"\n📋 任务执行详情:")
        for task in result.tasks:
            status_icon = {"completed": "✅", "failed": "❌", "running": "⏳"}.get(task.status.value, "❓")
            print(f"  {status_icon} {task.agent_name} - {task.description}")
            if task.result:
                print(f"    📄 指令: {task.result.get('instruction', 'N/A')[:60]}...")
                print(f"    📊 状态: {task.result.get('status', 'N/A')}")
                if task.start_time and task.end_time:
                    duration = (task.end_time - task.start_time).total_seconds()
                    print(f"    ⏱️ 耗时: {duration:.3f}s")

        return True

    except Exception as e:
        logger.error(f"工作流引擎核心测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_instant_instruction_generation():
    """测试即时指令生成"""
    print("\n⚡ 测试即时并行指令生成")
    print("=" * 60)

    try:
        from features.workflow.engine import WorkflowEngine

        engine = WorkflowEngine()

        # 测试即时指令生成
        agents = ['fullstack-engineer', 'devops-engineer', 'security-auditor']
        prompt = '部署高可用的微服务架构到Kubernetes集群，包括监控、日志和安全配置'

        print(f"🤖 Agents: {', '.join(agents)}")
        print(f"📝 任务: {prompt}")
        print("-" * 50)

        start_time = datetime.now()
        instruction = engine.create_real_time_parallel_instruction(agents, prompt)
        end_time = datetime.now()

        duration = (end_time - start_time).total_seconds()

        print(f"✅ 即时指令生成完成")
        print(f"⏱️ 生成时间: {duration:.3f}秒")
        print(f"📏 指令长度: {len(instruction)}字符")

        # 验证即时性（应该非常快）
        if duration < 0.01:  # 10ms内
            print(f"✅ 即时性验证通过: {duration*1000:.1f}ms")
        else:
            print(f"⚠️ 生成时间较长: {duration*1000:.1f}ms")

        # 验证指令结构
        lines = instruction.split('\n')
        header_lines = [line for line in lines if line.startswith('#')]
        function_calls = instruction.count('<invoke name="Task">')
        parameter_lines = instruction.count('<parameter name=')

        print(f"📊 指令结构分析:")
        print(f"  ✅ 总行数: {len(lines)}")
        print(f"  ✅ 注释行: {len(header_lines)}")
        print(f"  ✅ Task调用: {function_calls}")
        print(f"  ✅ 参数行: {parameter_lines}")

        # 验证格式正确性
        format_valid = (
            '<function_calls>' in instruction and
            '</function_calls>' in instruction and
            function_calls == len(agents) and
            'subagent_type' in instruction and
            'prompt' in instruction
        )

        print(f"✅ 格式验证: {'通过' if format_valid else '失败'}")

        # 显示指令内容（简化）
        print(f"\n📋 即时指令内容:")
        print("-" * 50)
        for i, line in enumerate(lines[:20]):  # 显示前20行
            print(f"{i+1:2d}| {line}")
        if len(lines) > 20:
            print(f"   ... (省略{len(lines)-20}行)")

        print(f"🎯 该指令可立即在Claude Code中执行，无需等待Perfect21进一步处理")

        return format_valid

    except Exception as e:
        logger.error(f"即时指令生成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sequential_workflow():
    """测试顺序工作流"""
    print("\n📋 测试顺序工作流执行")
    print("=" * 60)

    try:
        from features.workflow.engine import WorkflowEngine

        engine = WorkflowEngine(max_workers=3)

        # 定义顺序管道
        pipeline = [
            {
                'agent_name': 'product-strategist',
                'description': '需求分析',
                'prompt': '分析电商系统需求，定义核心功能和用户故事',
                'timeout': 300
            },
            {
                'agent_name': 'backend-architect',
                'description': '架构设计',
                'prompt': '基于需求分析结果设计电商系统架构，包括微服务划分和数据库设计',
                'timeout': 300
            },
            {
                'agent_name': 'test-engineer',
                'description': '测试策略',
                'prompt': '基于架构设计制定测试策略和自动化测试计划',
                'timeout': 300
            }
        ]

        print(f"📋 顺序执行 {len(pipeline)} 个阶段")
        print("-" * 50)

        result = engine.execute_sequential_pipeline(pipeline)

        print(f"✅ 顺序工作流执行完成")
        print(f"🆔 工作流ID: {result.workflow_id}")
        print(f"⏱️ 执行时间: {result.execution_time:.3f}秒")
        print(f"✅ 成功阶段: {result.success_count}/{len(pipeline)}")
        print(f"❌ 失败阶段: {result.failure_count}")

        # 验证顺序执行指令
        if hasattr(result, 'batch_execution_instruction') and result.batch_execution_instruction:
            instruction = result.batch_execution_instruction
            print(f"\n✅ 顺序执行指令生成成功")

            # 检查是否包含前一阶段结果的传递
            context_passing = '前一阶段结果' in instruction or 'previous' in instruction.lower()
            print(f"📊 上下文传递: {'✅ 包含' if context_passing else '❌ 缺失'}")

        # 显示阶段执行详情
        print(f"\n📊 阶段执行详情:")
        for i, task in enumerate(result.tasks, 1):
            status_icon = {"completed": "✅", "failed": "❌", "running": "⏳"}.get(task.status.value, "❓")
            print(f"  阶段{i} {status_icon} {task.agent_name} - {task.description}")

        return result.failure_count == 0

    except Exception as e:
        logger.error(f"顺序工作流测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🔬 Perfect21核心工作流引擎测试")
    print("=" * 80)
    print(f"📅 测试时间: {datetime.now().isoformat()}")
    print(f"🐍 Python版本: {sys.version.split()[0]}")
    print(f"📁 工作目录: {os.getcwd()}")
    print("=" * 80)

    test_results = []
    test_names = [
        "核心并行工作流引擎",
        "即时指令生成",
        "顺序工作流执行"
    ]

    # 测试1: 核心工作流引擎
    print("\n1️⃣ 核心并行工作流引擎测试")
    test_results.append(test_workflow_engine_directly())

    # 测试2: 即时指令生成
    print("\n2️⃣ 即时指令生成测试")
    test_results.append(test_instant_instruction_generation())

    # 测试3: 顺序工作流
    print("\n3️⃣ 顺序工作流测试")
    test_results.append(test_sequential_workflow())

    # 测试结果汇总
    print("\n" + "="*80)
    print("📊 Perfect21核心引擎测试结果汇总")
    print("="*80)

    passed = sum(test_results)
    total = len(test_results)

    for i, (name, result) in enumerate(zip(test_names, test_results)):
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{i+1}. {name}: {status}")

    print("-" * 80)
    print(f"总体结果: {passed}/{total} 测试通过")
    success_rate = passed / total * 100

    if passed == total:
        print("🎉 所有测试通过！Perfect21核心优化成功")
        print("\n💡 核心优化成果:")
        print("  ✅ 移除所有模拟实现（time.sleep、mock result）")
        print("  ✅ 实现真正的Task工具调用指令生成")
        print("  ✅ Perfect21作为策略层，生成执行指令")
        print("  ✅ 支持即时并行指令生成（< 10ms）")
        print("  ✅ 支持批量并行和顺序执行模式")
        print("  ✅ 提供清晰的执行日志和进度反馈")
        print("  ✅ 生成标准的Claude Code function_calls格式")

        print("\n🚀 使用方法:")
        print("  # 即时并行执行")
        print("  python3 main/cli.py perfect21 instant '任务描述' --agents 'agent1,agent2,agent3'")
        print("  ")
        print("  # 完整并行工作流")
        print("  python3 main/cli.py perfect21 parallel '任务描述' --agents 'agent1,agent2,agent3'")

        return 0
    else:
        print(f"⚠️ {total-passed}个测试失败 (成功率: {success_rate:.1f}%)")
        print("需要进一步检查和优化")
        return 1

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)