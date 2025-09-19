#!/usr/bin/env python3
"""
反馈循环系统演示
===============

演示Perfect21反馈循环系统如何解决以下关键问题：
1. 测试失败时自动回退到实现层修复
2. 同一个agent负责修复自己的代码
3. 智能重试机制和升级策略
4. 与质量门的集成
"""

import json
import logging
import asyncio
from typing import Dict, List, Any
from datetime import datetime

from .feedback_integration import get_feedback_integration
from .feedback_loop_engine import ValidationStage, FeedbackAction
from .enhanced_orchestrator import WorkflowStage

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("FeedbackDemo")


class FeedbackLoopDemo:
    """反馈循环演示类"""

    def __init__(self):
        self.integration = get_feedback_integration()

    def demo_basic_feedback_loop(self):
        """演示基础反馈循环"""

        print("=" * 60)
        print("🎯 Perfect21 反馈循环系统演示")
        print("=" * 60)

        # 场景1：实现阶段失败的反馈循环
        print("\n📋 场景1: 实现阶段失败的反馈循环")
        print("-" * 40)

        task_description = "实现用户登录功能，包括密码验证和JWT token生成"

        # 模拟实现阶段失败
        self._demo_implementation_failure()

        # 场景2：测试失败导致的实现修复
        print("\n📋 场景2: 测试失败导致的实现修复")
        print("-" * 40)

        self._demo_testing_failure_feedback()

        # 场景3：质量门失败的反馈
        print("\n📋 场景3: 质量门失败的反馈")
        print("-" * 40)

        self._demo_quality_gate_feedback()

        # 场景4：自动重试和升级机制
        print("\n📋 场景4: 自动重试和升级机制")
        print("-" * 40)

        self._demo_auto_retry_and_escalation()

    def _demo_implementation_failure(self):
        """演示实现阶段失败"""

        print("🔧 模拟：backend-architect 实现用户登录功能...")

        # 模拟实现失败的验证结果
        validation_result = {
            "success": False,
            "errors": [
                {
                    "type": "import_error",
                    "message": "无法导入 'jwt' 模块",
                    "details": "ModuleNotFoundError: No module named 'PyJWT'"
                },
                {
                    "type": "syntax_error",
                    "message": "函数定义语法错误",
                    "details": "SyntaxError: invalid syntax at line 45"
                }
            ]
        }

        print(f"❌ 实现验证失败: {json.dumps(validation_result, indent=2, ensure_ascii=False)}")

        # 注册反馈循环
        feedback_engine = self.integration.feedback_engine
        feedback_id = feedback_engine.register_feedback_loop(
            workflow_id="demo_workflow_001",
            stage=ValidationStage.IMPLEMENTATION,
            agent_name="backend-architect",
            task_id="login_implementation",
            original_prompt="实现用户登录功能，包括密码验证和JWT token生成"
        )

        print(f"📝 注册反馈循环: {feedback_id}")

        # 处理验证失败
        decision = feedback_engine.process_validation_failure(
            feedback_id=feedback_id,
            validation_result=validation_result,
            failure_reason="导入错误和语法错误"
        )

        print(f"🧠 反馈决策: {decision.action.value}")
        print(f"   目标Agent: {decision.target_agent}")
        print(f"   置信度: {decision.confidence:.2f}")
        print(f"   修复预估时间: {decision.estimated_fix_time}秒")

        # 生成重试指令
        if decision.action == FeedbackAction.RETRY:
            retry_instruction = feedback_engine.get_retry_instruction(decision)
            print(f"🔄 重试指令已生成:")
            print(retry_instruction[:300] + "..." if len(retry_instruction) > 300 else retry_instruction)

    def _demo_testing_failure_feedback(self):
        """演示测试失败导致的实现修复"""

        print("🧪 模拟：test-engineer 执行登录功能测试...")

        # 模拟测试失败的情况
        test_validation_result = {
            "success": False,
            "test_failures": [
                {
                    "test_name": "test_login_with_valid_credentials",
                    "type": "assertion_error",
                    "message": "期望返回JWT token，但得到了None",
                    "details": {
                        "expected": "JWT token string",
                        "actual": None,
                        "assertion": "assert result.token is not None"
                    }
                },
                {
                    "test_name": "test_login_with_invalid_password",
                    "type": "behavior_mismatch",
                    "message": "期望抛出AuthenticationError，但函数正常返回",
                    "details": {
                        "expected": "AuthenticationError exception",
                        "actual": "Normal return with empty result"
                    }
                }
            ]
        }

        print(f"❌ 测试验证失败: {json.dumps(test_validation_result, indent=2, ensure_ascii=False)}")

        # 注册测试阶段反馈循环
        feedback_engine = self.integration.feedback_engine
        test_feedback_id = feedback_engine.register_feedback_loop(
            workflow_id="demo_workflow_001",
            stage=ValidationStage.TESTING,
            agent_name="test-engineer",
            task_id="login_testing",
            original_prompt="为用户登录功能编写和执行测试"
        )

        # 分析测试失败类型
        for failure in test_validation_result["test_failures"]:
            failure_type = failure["type"]
            failure_message = failure["message"]

            print(f"\n🔍 分析测试失败: {failure['test_name']}")
            print(f"   失败类型: {failure_type}")

            # 判断是实现问题还是测试问题
            is_impl_issue = self._is_implementation_issue(failure_type, failure_message)

            if is_impl_issue:
                print("   🎯 判断: 这是实现问题，需要回退到实现层修复")

                # 创建实现修复指令
                impl_fix_instruction = self._create_implementation_fix_instruction(
                    "backend-architect", failure
                )

                print("   🔧 生成实现修复指令:")
                print(f"   目标Agent: backend-architect (原实现负责人)")
                print(f"   修复任务: 根据测试失败修正实现逻辑")

            else:
                print("   🎯 判断: 这是测试问题，由test-engineer修复")

                # 处理测试层面的问题
                decision = feedback_engine.process_validation_failure(
                    feedback_id=test_feedback_id,
                    validation_result=test_validation_result,
                    failure_reason=failure_message
                )

                print(f"   🔄 测试修复决策: {decision.action.value}")

    def _demo_quality_gate_feedback(self):
        """演示质量门失败的反馈"""

        print("🚦 模拟：执行质量门检查...")

        # 模拟质量门失败结果
        quality_gate_result = {
            "overall": {
                "status": "failed",
                "score": 65.0,
                "message": "质量门检查失败"
            },
            "code_quality": {
                "status": "failed",
                "score": 60.0,
                "violations": [
                    {"type": "complexity", "message": "函数复杂度过高: login_user() 复杂度为15"},
                    {"type": "duplication", "message": "代码重复: 密码验证逻辑在3个地方重复"},
                    {"type": "naming", "message": "变量命名不规范: usr, pwd, tkn"}
                ],
                "suggestions": [
                    "分解复杂函数为更小的函数",
                    "提取公共逻辑到独立模块",
                    "使用有意义的变量名"
                ]
            },
            "security": {
                "status": "failed",
                "score": 40.0,
                "violations": [
                    {"type": "hardcoded_secret", "message": "硬编码的JWT密钥"},
                    {"type": "weak_hash", "message": "使用了弱哈希算法MD5"}
                ],
                "suggestions": [
                    "使用环境变量存储敏感信息",
                    "升级到安全的哈希算法如bcrypt"
                ]
            }
        }

        print(f"❌ 质量门检查失败: 总分 {quality_gate_result['overall']['score']}/100")

        # 为每个失败的质量门生成修复指令
        for gate_name, gate_result in quality_gate_result.items():
            if gate_name == "overall":
                continue

            if gate_result["status"] == "failed":
                print(f"\n🔧 处理 {gate_name} 质量门失败:")

                # 确定负责修复的agent
                responsible_agent = self._get_responsible_agent_for_quality_gate(gate_name)
                print(f"   负责Agent: {responsible_agent}")

                # 生成修复指令
                fix_instruction = self._create_quality_gate_fix_instruction(
                    gate_name, gate_result, responsible_agent
                )

                print(f"   修复任务: {gate_result['violations'][0]['message'] if gate_result['violations'] else '质量改进'}")

    def _demo_auto_retry_and_escalation(self):
        """演示自动重试和升级机制"""

        print("🔄 模拟：自动重试和升级机制...")

        # 场景：backend-architect 连续3次实现失败
        feedback_engine = self.integration.feedback_engine

        failure_scenarios = [
            {"attempt": 1, "reason": "语法错误", "severity": "medium"},
            {"attempt": 2, "reason": "逻辑错误", "severity": "medium"},
            {"attempt": 3, "reason": "架构设计问题", "severity": "high"}
        ]

        feedback_id = feedback_engine.register_feedback_loop(
            workflow_id="demo_workflow_escalation",
            stage=ValidationStage.IMPLEMENTATION,
            agent_name="backend-architect",
            task_id="complex_feature",
            original_prompt="实现复杂的用户权限管理系统"
        )

        for scenario in failure_scenarios:
            print(f"\n📍 第 {scenario['attempt']} 次尝试失败:")
            print(f"   失败原因: {scenario['reason']}")

            validation_result = {
                "success": False,
                "errors": [{"message": scenario["reason"]}]
            }

            decision = feedback_engine.process_validation_failure(
                feedback_id=feedback_id,
                validation_result=validation_result,
                failure_reason=scenario["reason"]
            )

            print(f"   🧠 决策: {decision.action.value}")
            print(f"   目标Agent: {decision.target_agent}")
            print(f"   置信度: {decision.confidence:.2f}")

            if decision.action == FeedbackAction.ESCALATE:
                print(f"   🚨 升级原因: {decision.reasoning}")
                escalation_instruction = feedback_engine.get_escalation_instruction(decision)
                print("   📋 升级指令已生成，交由专家处理")
                break
            elif decision.action == FeedbackAction.ABORT:
                print("   🛑 达到中止条件，停止重试")
                break

    def demo_complete_workflow_with_feedback(self):
        """演示完整的工作流与反馈循环"""

        print("\n" + "=" * 60)
        print("🚀 完整工作流与反馈循环演示")
        print("=" * 60)

        task_description = "实现一个RESTful API用户管理系统，包括注册、登录、权限管理"

        print(f"📋 任务: {task_description}")

        # 执行增强工作流
        print("\n🔧 执行增强工作流...")

        try:
            result = self.integration.execute_enhanced_workflow(
                task_description=task_description,
                workflow_type="full"
            )

            print(f"📊 工作流结果:")
            print(f"   状态: {result.get('status')}")
            print(f"   执行时间: {result.get('execution_time', 0):.2f}秒")

            # 显示阶段执行情况
            stages = result.get("stages", {})
            for stage_name, stage_info in stages.items():
                print(f"   {stage_name}: {stage_info.get('status')} (重试{stage_info.get('retry_count', 0)}次)")

            # 显示反馈循环摘要
            feedback_summary = result.get("feedback_summary", {})
            if feedback_summary:
                print(f"\n📈 反馈循环摘要:")
                print(f"   总反馈循环: {feedback_summary.get('total_feedback_loops', 0)}")
                print(f"   活跃循环: {feedback_summary.get('active_loops', 0)}")
                print(f"   总重试次数: {feedback_summary.get('total_retries', 0)}")
                print(f"   成功率: {feedback_summary.get('success_rate', 0):.2%}")

            # 如果需要手动干预
            if result.get("requires_manual_intervention"):
                print(f"\n⚠️  需要手动干预:")
                retry_instructions = result.get("retry_instructions", [])
                print(f"   待执行指令: {len(retry_instructions)}个")

                # 显示用户友好的指令
                user_instructions = result.get("user_instructions", {})
                if user_instructions:
                    print(f"   下一步: {user_instructions.get('summary', '见详细指令')}")

        except Exception as e:
            print(f"❌ 工作流执行失败: {e}")

    def demo_auto_retry_workflow(self):
        """演示自动重试工作流"""

        print("\n" + "=" * 60)
        print("🔄 自动重试工作流演示")
        print("=" * 60)

        task_description = "实现一个简单的计算器API"

        print(f"📋 任务: {task_description}")
        print("🤖 启用自动重试机制 (最大2次重试)...")

        try:
            result = self.integration.execute_with_auto_retry(
                task_description=task_description,
                max_auto_retries=2
            )

            print(f"\n📊 自动重试结果:")
            print(f"   最终状态: {result.get('final_status')}")
            print(f"   总尝试次数: {result.get('total_attempts', 0)}")

            # 显示重试历史
            history = result.get("auto_retry_history", [])
            for i, attempt in enumerate(history, 1):
                attempt_result = attempt.get("result", {})
                print(f"   尝试 {i}: {attempt_result.get('status')} - {attempt.get('timestamp')}")

            # 如果需要手动干预
            if result.get("final_status") == "requires_manual_intervention":
                manual_guide = result.get("manual_instructions", {})
                print(f"\n🔧 手动干预指南:")
                print(f"   情况: {manual_guide.get('situation', '需要人工处理')}")

                recommendations = manual_guide.get("recommendations", [])
                for rec in recommendations:
                    print(f"   • {rec}")

        except Exception as e:
            print(f"❌ 自动重试失败: {e}")

    def _is_implementation_issue(self, failure_type: str, failure_message: str) -> bool:
        """判断是否为实现问题"""
        implementation_indicators = [
            "assertion_error", "logic_error", "return_value_error",
            "behavior_mismatch", "expected_vs_actual"
        ]

        return any(indicator in failure_type.lower() for indicator in implementation_indicators) or \
               ("expected" in failure_message.lower() and "actual" in failure_message.lower())

    def _create_implementation_fix_instruction(self, agent: str, failure_info: Dict[str, Any]) -> str:
        """创建实现修复指令"""

        return f"""
## 🔧 实现修复指令

**目标Agent**: {agent}
**修复原因**: 测试失败反馈

**测试失败详情**:
- 测试名称: {failure_info.get('test_name')}
- 失败类型: {failure_info.get('type')}
- 失败消息: {failure_info.get('message')}

**修复要求**:
请根据测试失败信息，修正你之前的实现代码，确保能够通过测试。
"""

    def _get_responsible_agent_for_quality_gate(self, gate_name: str) -> str:
        """获取负责质量门的agent"""
        gate_agent_map = {
            "code_quality": "code-reviewer",
            "security": "security-auditor",
            "performance": "performance-engineer",
            "architecture": "backend-architect"
        }
        return gate_agent_map.get(gate_name, "code-reviewer")

    def _create_quality_gate_fix_instruction(self, gate_name: str, gate_result: Dict[str, Any],
                                           responsible_agent: str) -> str:
        """创建质量门修复指令"""

        violations = gate_result.get("violations", [])
        suggestions = gate_result.get("suggestions", [])

        instruction = f"""
## 🚦 质量门修复指令 - {gate_name}

**负责Agent**: {responsible_agent}
**当前分数**: {gate_result.get('score', 0)}/100

**违规项目**:
"""
        for violation in violations[:3]:
            instruction += f"- {violation.get('message', str(violation))}\n"

        instruction += "\n**修复建议**:\n"
        for suggestion in suggestions[:2]:
            instruction += f"- {suggestion}\n"

        return instruction


def run_feedback_demo():
    """运行完整的反馈循环演示"""

    print("🎯 Perfect21 反馈循环系统 - 完整演示")
    print("解决测试失败时的智能反馈和自动修复问题")
    print()

    demo = FeedbackLoopDemo()

    try:
        # 基础反馈循环演示
        demo.demo_basic_feedback_loop()

        # 完整工作流演示
        demo.demo_complete_workflow_with_feedback()

        # 自动重试演示
        demo.demo_auto_retry_workflow()

        print("\n" + "=" * 60)
        print("✅ 反馈循环系统演示完成")
        print("=" * 60)

        print("\n🎯 系统核心优势:")
        print("1. ✅ 测试失败时自动回退到实现层修复")
        print("2. ✅ 同一个agent负责修复自己的代码")
        print("3. ✅ 智能重试机制，避免无限循环")
        print("4. ✅ 自动升级到专家agent处理复杂问题")
        print("5. ✅ 与质量门完全集成")
        print("6. ✅ 提供清晰的人工干预指导")

    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_feedback_demo()