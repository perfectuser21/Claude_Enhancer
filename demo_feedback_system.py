#!/usr/bin/env python3
"""
Perfect21 反馈循环系统演示
========================

独立演示脚本，展示反馈循环系统如何解决核心问题
"""

import json
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def demo_feedback_loop_concepts():
    """演示反馈循环核心概念"""

    print("=" * 70)
    print("🎯 Perfect21 反馈循环系统 - 核心概念演示")
    print("=" * 70)

    print("\n📋 解决的核心问题:")
    print("1. ❌ 当前问题: 测试失败时工作流继续提交，而不是回退修复")
    print("2. ❌ 当前问题: 修复代码的不是原始编写者，导致上下文丢失")
    print("3. ❌ 当前问题: 缺乏智能重试和升级机制")

    print("\n✅ 反馈循环系统解决方案:")
    print("1. ✅ 智能检测失败类型，自动回退到正确的层级")
    print("2. ✅ 确保同一个agent负责修复自己编写的代码")
    print("3. ✅ 提供智能重试、升级和中止机制")

    # 模拟实际场景
    demo_scenario_1_implementation_failure()
    demo_scenario_2_testing_failure_feedback()
    demo_scenario_3_quality_gate_feedback()
    demo_scenario_4_auto_escalation()

def demo_scenario_1_implementation_failure():
    """场景1: 实现阶段失败的反馈循环"""

    print("\n" + "="*50)
    print("📋 场景1: 实现阶段失败的反馈循环")
    print("="*50)

    print("\n🔧 模拟: backend-architect 实现用户登录功能...")

    # 模拟实现失败
    implementation_errors = {
        "import_error": "无法导入 'jwt' 模块 - ModuleNotFoundError: No module named 'PyJWT'",
        "syntax_error": "函数定义语法错误 - SyntaxError: invalid syntax at line 45"
    }

    print("❌ 实现验证失败:")
    for error_type, error_msg in implementation_errors.items():
        print(f"   - {error_type}: {error_msg}")

    # 反馈循环决策过程
    print("\n🧠 反馈循环决策过程:")
    print("1. 📝 注册反馈循环: workflow_001_implementation_backend-architect")
    print("2. 🔍 分析失败原因: 导入错误 + 语法错误")
    print("3. 📊 评估严重性: MEDIUM (可修复)")
    print("4. 🎯 决策: RETRY")
    print("5. 👤 目标Agent: backend-architect (同一个agent)")
    print("6. 🔧 置信度: 0.8")

    # 生成的修复指令
    print("\n🔄 生成的修复指令:")
    retry_instruction = """
## 🔴 前次执行失败分析

**失败原因**: 导入错误和语法错误
**重试次数**: 1/3

## 🔧 修复指导

**重点关注**:
- 请仔细检查代码语法和逻辑错误
- 确保所有导入的模块和依赖都正确
- 添加缺失的依赖: pip install PyJWT

## ✅ 验证要求
修复后的代码必须能够通过基本的语法和导入验证。

### 执行指令:
<function_calls>
  <invoke name="Task">
    <parameter name="subagent_type">backend-architect</parameter>
    <parameter name="prompt">修复用户登录功能实现中的导入错误和语法错误...</parameter>
  </invoke>
</function_calls>
"""

    print(retry_instruction)

    print("✅ 结果: 同一个agent (backend-architect) 负责修复自己的代码")

def demo_scenario_2_testing_failure_feedback():
    """场景2: 测试失败导致的实现修复 - 关键功能"""

    print("\n" + "="*50)
    print("📋 场景2: 测试失败导致的实现修复")
    print("="*50)

    print("\n🧪 模拟: test-engineer 执行登录功能测试...")

    # 模拟测试失败
    test_failures = [
        {
            "test_name": "test_login_with_valid_credentials",
            "type": "assertion_error",
            "message": "期望返回JWT token，但得到了None",
            "expected": "JWT token string",
            "actual": None
        },
        {
            "test_name": "test_login_with_invalid_password",
            "type": "behavior_mismatch",
            "message": "期望抛出AuthenticationError，但函数正常返回"
        }
    ]

    print("❌ 测试失败详情:")
    for failure in test_failures:
        print(f"   - {failure['test_name']}: {failure['message']}")

    print("\n🎯 关键决策: 是实现问题还是测试问题?")

    for failure in test_failures:
        print(f"\n🔍 分析: {failure['test_name']}")
        print(f"   失败类型: {failure['type']}")

        # 智能判断逻辑
        is_impl_issue = failure['type'] in ['assertion_error', 'behavior_mismatch']

        if is_impl_issue:
            print("   🎯 判断: 这是实现问题 (expected vs actual)")
            print("   🔄 决策: 回退到实现层修复")
            print("   👤 目标: backend-architect (原实现负责人)")

            implementation_fix = f"""
## 🔧 实现修复指令 (基于测试失败)

**原始负责Agent**: backend-architect
**修复原因**: 测试失败反馈

**测试失败详情**:
- 测试: {failure['test_name']}
- 期望: {failure.get('expected', '见测试')}
- 实际: {failure.get('actual', '见错误信息')}

**修复要求**:
请分析测试期望的行为，修正你之前的实现代码以满足测试要求。

<function_calls>
  <invoke name="Task">
    <parameter name="subagent_type">backend-architect</parameter>
    <parameter name="prompt">根据测试失败修正登录功能实现...</parameter>
  </invoke>
</function_calls>
"""
            print("   📋 生成实现修复指令 ↑")

        else:
            print("   🎯 判断: 这是测试问题")
            print("   🔄 决策: 由test-engineer修复测试")

    print("\n✅ 核心优势: 测试失败时自动回退到实现层，由原作者修复")

def demo_scenario_3_quality_gate_feedback():
    """场景3: 质量门失败的反馈"""

    print("\n" + "="*50)
    print("📋 场景3: 质量门失败的反馈")
    print("="*50)

    print("\n🚦 模拟: 执行质量门检查...")

    # 模拟质量门失败
    quality_failures = {
        "code_quality": {
            "score": 60,
            "violations": [
                "函数复杂度过高: login_user() 复杂度为15",
                "代码重复: 密码验证逻辑在3个地方重复"
            ],
            "responsible_agent": "code-reviewer"
        },
        "security": {
            "score": 40,
            "violations": [
                "硬编码的JWT密钥",
                "使用了弱哈希算法MD5"
            ],
            "responsible_agent": "security-auditor"
        }
    }

    print("❌ 质量门失败:")
    for gate_name, gate_info in quality_failures.items():
        print(f"   {gate_name}: {gate_info['score']}/100")
        for violation in gate_info['violations']:
            print(f"     - {violation}")

    print("\n🔧 反馈修复策略:")
    for gate_name, gate_info in quality_failures.items():
        print(f"\n{gate_name}:")
        print(f"   👤 负责Agent: {gate_info['responsible_agent']}")
        print(f"   🎯 修复任务: 解决{len(gate_info['violations'])}个违规项")

        fix_instruction = f"""
## 🚦 质量门修复指令 - {gate_name}

**负责Agent**: {gate_info['responsible_agent']}
**当前分数**: {gate_info['score']}/100

**修复要求**:
{chr(10).join(f'- {v}' for v in gate_info['violations'])}

<function_calls>
  <invoke name="Task">
    <parameter name="subagent_type">{gate_info['responsible_agent']}</parameter>
    <parameter name="prompt">修复{gate_name}质量门问题...</parameter>
  </invoke>
</function_calls>
"""
        print("   📋 生成专门修复指令")

    print("\n✅ 结果: 每个质量门失败都有专门的agent负责修复")

def demo_scenario_4_auto_escalation():
    """场景4: 自动重试和升级机制"""

    print("\n" + "="*50)
    print("📋 场景4: 自动重试和升级机制")
    print("="*50)

    print("\n🔄 模拟: backend-architect 连续失败和自动升级...")

    failure_scenarios = [
        {"attempt": 1, "reason": "语法错误", "severity": "MEDIUM", "action": "RETRY"},
        {"attempt": 2, "reason": "逻辑错误", "severity": "MEDIUM", "action": "RETRY"},
        {"attempt": 3, "reason": "架构设计问题", "severity": "HIGH", "action": "ESCALATE"}
    ]

    for scenario in failure_scenarios:
        print(f"\n📍 第 {scenario['attempt']} 次尝试:")
        print(f"   失败原因: {scenario['reason']}")
        print(f"   严重性: {scenario['severity']}")

        if scenario['action'] == 'RETRY':
            print(f"   🔄 决策: 重试 (backend-architect)")
            print(f"   📊 置信度: {0.9 - (scenario['attempt'] * 0.2):.1f}")
        elif scenario['action'] == 'ESCALATE':
            print(f"   🚨 决策: 升级到专家")
            print(f"   👤 升级到: fullstack-engineer (架构专家)")
            print(f"   📋 升级原因: 连续重试失败，需要架构级解决方案")

            escalation_instruction = """
## 🚨 任务升级处理

**原始负责Agent**: backend-architect
**升级原因**: 经过2次重试仍未解决
**当前处理Agent**: fullstack-engineer

## 🔧 专家级修复指导

作为升级处理的专家，请你:
1. **深度分析**: 从架构角度分析问题根因
2. **架构审查**: 检查是否有设计问题
3. **全面修复**: 不仅修复表面问题，还要确保健壮性
4. **知识传递**: 在代码中添加注释说明修复思路

<function_calls>
  <invoke name="Task">
    <parameter name="subagent_type">fullstack-engineer</parameter>
    <parameter name="prompt">专家级架构修复...</parameter>
  </invoke>
</function_calls>
"""
            print("   📋 生成升级处理指令")
            break

    print("\n✅ 防死循环机制:")
    print("   - ✅ 最大重试次数限制 (3次)")
    print("   - ✅ 自动升级到专家agent")
    print("   - ✅ 严重错误直接中止")
    print("   - ✅ 时间窗口超时保护")

def demo_integration_benefits():
    """演示集成优势"""

    print("\n" + "="*70)
    print("🎯 Perfect21 反馈循环系统 - 核心优势总结")
    print("="*70)

    benefits = [
        {
            "title": "智能失败分析",
            "description": "自动识别失败是实现问题、测试问题还是质量问题",
            "example": "测试中的 'expected vs actual' → 回退到实现层修复"
        },
        {
            "title": "同Agent修复原则",
            "description": "确保同一个agent负责修复自己编写的代码",
            "example": "backend-architect 写的代码 → backend-architect 负责修复"
        },
        {
            "title": "精准回退机制",
            "description": "测试失败时精准回退到对应的实现agent",
            "example": "JWT验证测试失败 → 回退到backend-architect修复JWT实现"
        },
        {
            "title": "智能升级策略",
            "description": "重试失败时自动升级到专家agent",
            "example": "连续语法错误 → 升级到python-pro专家"
        },
        {
            "title": "防死循环保护",
            "description": "多重保护机制防止无限重试",
            "example": "最大3次重试 + 时间窗口 + 严重错误中止"
        },
        {
            "title": "完整状态跟踪",
            "description": "记录所有反馈循环的状态和历史",
            "example": "可查询任何工作流的重试历史和决策过程"
        }
    ]

    for i, benefit in enumerate(benefits, 1):
        print(f"\n{i}. ✅ {benefit['title']}")
        print(f"   📋 {benefit['description']}")
        print(f"   💡 示例: {benefit['example']}")

    print("\n📊 预期效果:")
    print("   - 🎯 70% 的问题可自动修复")
    print("   - 🚀 25% 的问题通过升级解决")
    print("   - 👤 仅5% 的问题需要人工干预")
    print("   - ⚡ 显著减少无效重试和时间浪费")

def demo_usage_examples():
    """演示使用方式"""

    print("\n" + "="*70)
    print("🚀 使用方式演示")
    print("="*70)

    print("\n1. 📝 基础增强工作流:")
    print("""
from features.workflow.feedback_integration import get_feedback_integration

integration = get_feedback_integration()

result = integration.execute_enhanced_workflow(
    task_description="实现用户登录功能",
    workflow_type="full"
)

if result.get("requires_manual_intervention"):
    # 执行修复指令
    for instruction in result.get("retry_instructions", []):
        print(f"需要执行: {instruction}")
""")

    print("\n2. 🔄 自动重试工作流:")
    print("""
result = integration.execute_with_auto_retry(
    task_description="实现API功能",
    max_auto_retries=2
)

if result.get("final_status") == "completed":
    print("自动修复成功!")
else:
    print("需要人工干预:", result.get("manual_instructions"))
""")

    print("\n3. 🖥️ CLI命令:")
    print("""
# 执行增强工作流
python main/cli.py execute-enhanced --task "实现用户系统"

# 自动重试工作流
python main/cli.py execute-auto-retry --task "实现API" --max_retries 3

# 查看反馈状态
python main/cli.py feedback-status --workflow_id workflow_123
""")

    print("\n4. 📊 状态监控:")
    print("""
# 获取工作流状态
status = integration.get_feedback_status("workflow_123")

print(f"活跃反馈循环: {status.get('active_feedback_loops')}")
print(f"总重试次数: {status.get('total_retries')}")
print(f"成功率: {status.get('success_rate'):.2%}")
""")

def main():
    """主演示函数"""

    try:
        # 核心概念演示
        demo_feedback_loop_concepts()

        # 集成优势演示
        demo_integration_benefits()

        # 使用方式演示
        demo_usage_examples()

        print("\n" + "="*70)
        print("✅ Perfect21 反馈循环系统演示完成")
        print("="*70)

        print("\n🎯 系统解决的核心问题:")
        print("1. ✅ 测试失败时自动回退到实现层修复 (不再继续提交)")
        print("2. ✅ 同一个agent负责修复自己的代码 (保持上下文)")
        print("3. ✅ 智能重试机制避免无限循环")
        print("4. ✅ 自动升级到专家agent处理复杂问题")
        print("5. ✅ 与现有质量门完全集成")
        print("6. ✅ 提供清晰的人工干预指导")

        print("\n💡 下一步:")
        print("   - 查看详细架构文档: FEEDBACK_LOOP_ARCHITECTURE.md")
        print("   - 集成到现有CLI: main/cli.py")
        print("   - 运行真实测试验证效果")

    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()