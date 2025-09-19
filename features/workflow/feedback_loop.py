#!/usr/bin/env python3
"""
Perfect21 反馈循环机制
解决测试失败后直接提交的逻辑问题，实现智能回退和同Agent修复
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class RetryDecision(Enum):
    """重试决策类型"""
    RETRY_SAME_AGENT = "retry_same"      # 同Agent重试
    ESCALATE_EXPERT = "escalate"         # 升级到专家
    MANUAL_INTERVENTION = "manual"       # 需要人工
    ABORT = "abort"                      # 终止


@dataclass
class FeedbackContext:
    """反馈上下文"""
    layer_name: str
    agent_name: str
    original_input: Any
    execution_result: Any
    validation_errors: List[str]
    attempt_number: int
    max_retries: int
    execution_history: List[Dict]


@dataclass
class FixInstruction:
    """修复指令"""
    target_agent: str
    fix_prompt: str
    context_data: Dict
    priority: str
    estimated_time: int


class FeedbackLoopEngine:
    """
    反馈循环引擎
    负责处理验证失败时的智能回退和修复
    """

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.retry_history = []
        self.escalation_rules = self._load_escalation_rules()
        logger.info(f"反馈循环引擎初始化，最大重试次数: {max_retries}")

    def _load_escalation_rules(self) -> Dict:
        """加载升级规则"""
        return {
            "test_failure": {
                "retry_threshold": 2,
                "escalate_to": "senior-engineer",
                "conditions": ["critical_test_failure", "security_issue"]
            },
            "lint_failure": {
                "retry_threshold": 3,
                "escalate_to": "code-reviewer",
                "conditions": ["style_violation", "complexity_issue"]
            },
            "security_failure": {
                "retry_threshold": 1,
                "escalate_to": "security-auditor",
                "conditions": ["vulnerability", "exposure"]
            }
        }

    def handle_validation_failure(self, context: FeedbackContext) -> Tuple[RetryDecision, FixInstruction]:
        """
        处理验证失败

        Args:
            context: 反馈上下文

        Returns:
            (重试决策, 修复指令)
        """
        logger.info(f"处理验证失败: {context.layer_name}/{context.agent_name}, 尝试 {context.attempt_number}/{context.max_retries}")

        # 1. 分析失败类型
        failure_type = self._analyze_failure_type(context.validation_errors)

        # 2. 决定重试策略
        decision = self._make_retry_decision(context, failure_type)

        # 3. 生成修复指令
        fix_instruction = self._generate_fix_instruction(context, decision, failure_type)

        # 4. 记录历史
        self._record_retry_history(context, decision, fix_instruction)

        return decision, fix_instruction

    def _analyze_failure_type(self, errors: List[str]) -> str:
        """分析失败类型"""
        error_text = " ".join(errors).lower()

        if "test" in error_text or "assertion" in error_text:
            return "test_failure"
        elif "lint" in error_text or "style" in error_text:
            return "lint_failure"
        elif "security" in error_text or "vulnerability" in error_text:
            return "security_failure"
        elif "type" in error_text or "typing" in error_text:
            return "type_failure"
        else:
            return "general_failure"

    def _make_retry_decision(self, context: FeedbackContext, failure_type: str) -> RetryDecision:
        """
        做出重试决策

        基于：
        - 当前尝试次数
        - 失败类型
        - 升级规则
        """
        # 检查是否超过最大重试次数
        if context.attempt_number >= context.max_retries:
            logger.warning(f"超过最大重试次数 {context.max_retries}")
            return RetryDecision.MANUAL_INTERVENTION

        # 检查是否需要升级
        if failure_type in self.escalation_rules:
            rule = self.escalation_rules[failure_type]
            if context.attempt_number >= rule["retry_threshold"]:
                logger.info(f"触发升级规则: {failure_type} -> {rule['escalate_to']}")
                return RetryDecision.ESCALATE_EXPERT

        # 检查是否有改善
        if self._has_improvement(context):
            logger.info("检测到改善，继续同Agent重试")
            return RetryDecision.RETRY_SAME_AGENT

        # 检查是否陷入循环
        if self._is_stuck_in_loop(context):
            logger.warning("检测到循环，需要人工介入")
            return RetryDecision.MANUAL_INTERVENTION

        # 默认：同Agent重试
        return RetryDecision.RETRY_SAME_AGENT

    def _generate_fix_instruction(self, context: FeedbackContext,
                                 decision: RetryDecision,
                                 failure_type: str) -> FixInstruction:
        """生成修复指令"""

        if decision == RetryDecision.RETRY_SAME_AGENT:
            # 同Agent修复
            target_agent = context.agent_name
            fix_prompt = self._create_same_agent_fix_prompt(context, failure_type)

        elif decision == RetryDecision.ESCALATE_EXPERT:
            # 升级到专家
            target_agent = self._get_expert_agent(failure_type)
            fix_prompt = self._create_expert_fix_prompt(context, failure_type)

        elif decision == RetryDecision.MANUAL_INTERVENTION:
            # 人工介入
            target_agent = "human"
            fix_prompt = self._create_manual_intervention_prompt(context)

        else:  # ABORT
            target_agent = None
            fix_prompt = "Task aborted due to repeated failures"

        return FixInstruction(
            target_agent=target_agent,
            fix_prompt=fix_prompt,
            context_data={
                "original_input": context.original_input,
                "previous_result": context.execution_result,
                "errors": context.validation_errors,
                "attempt": context.attempt_number
            },
            priority="high" if decision == RetryDecision.ESCALATE_EXPERT else "normal",
            estimated_time=self._estimate_fix_time(failure_type)
        )

    def _create_same_agent_fix_prompt(self, context: FeedbackContext, failure_type: str) -> str:
        """创建同Agent修复提示"""
        prompt = f"""
你之前的实现有以下问题需要修复：

**错误类型**: {failure_type}
**具体错误**:
{chr(10).join(f"- {error}" for error in context.validation_errors)}

**你之前的实现**:
```
{json.dumps(context.execution_result, indent=2, ensure_ascii=False) if isinstance(context.execution_result, dict) else str(context.execution_result)[:1000]}
```

**原始需求**:
{context.original_input}

请修复这些问题，确保：
1. 解决所有报告的错误
2. 保持与原始需求的一致性
3. 不要引入新的问题
4. 提供清晰的修复说明

这是第 {context.attempt_number + 1} 次尝试，共有 {context.max_retries} 次机会。
"""
        return prompt

    def _create_expert_fix_prompt(self, context: FeedbackContext, failure_type: str) -> str:
        """创建专家修复提示"""
        prompt = f"""
作为专家，你需要解决一个复杂的问题。

**背景**: {context.agent_name} 尝试了 {context.attempt_number} 次但未能解决

**问题类型**: {failure_type}
**错误详情**:
{chr(10).join(f"- {error}" for error in context.validation_errors)}

**历史尝试**:
{self._format_attempt_history(context.execution_history)}

**原始需求**:
{context.original_input}

请提供专家级的解决方案，包括：
1. 根本原因分析
2. 完整的修复方案
3. 预防措施建议
4. 代码示例和最佳实践
"""
        return prompt

    def _create_manual_intervention_prompt(self, context: FeedbackContext) -> str:
        """创建人工介入提示"""
        return f"""
需要人工介入解决问题。

**情况摘要**:
- 层级: {context.layer_name}
- Agent: {context.agent_name}
- 尝试次数: {context.attempt_number}
- 错误类型: {self._analyze_failure_type(context.validation_errors)}

**错误列表**:
{chr(10).join(f"{i+1}. {error}" for i, error in enumerate(context.validation_errors))}

**建议操作**:
1. 检查需求是否明确
2. 验证Agent能力是否匹配
3. 考虑分解任务
4. 可能需要架构调整

请人工评估并提供指导。
"""

    def _has_improvement(self, context: FeedbackContext) -> bool:
        """检查是否有改善"""
        if len(context.execution_history) < 2:
            return True  # 首次重试，假设会改善

        # 比较最近两次的错误数量
        prev_errors = len(context.execution_history[-2].get("errors", []))
        curr_errors = len(context.validation_errors)

        return curr_errors < prev_errors

    def _is_stuck_in_loop(self, context: FeedbackContext) -> bool:
        """检查是否陷入循环"""
        if len(context.execution_history) < 3:
            return False

        # 检查最近3次的错误是否相同
        recent_errors = [
            set(h.get("errors", []))
            for h in context.execution_history[-3:]
        ]

        return len(set(map(frozenset, recent_errors))) == 1

    def _get_expert_agent(self, failure_type: str) -> str:
        """获取专家Agent"""
        expert_mapping = {
            "test_failure": "test-engineer",
            "lint_failure": "code-reviewer",
            "security_failure": "security-auditor",
            "type_failure": "typescript-pro",
            "general_failure": "backend-architect"
        }
        return expert_mapping.get(failure_type, "backend-architect")

    def _estimate_fix_time(self, failure_type: str) -> int:
        """估算修复时间（分钟）"""
        time_estimates = {
            "test_failure": 15,
            "lint_failure": 5,
            "security_failure": 30,
            "type_failure": 10,
            "general_failure": 20
        }
        return time_estimates.get(failure_type, 15)

    def _format_attempt_history(self, history: List[Dict]) -> str:
        """格式化尝试历史"""
        if not history:
            return "无历史记录"

        formatted = []
        for i, attempt in enumerate(history, 1):
            formatted.append(f"尝试 {i}: {attempt.get('status', 'unknown')} - {len(attempt.get('errors', []))} 个错误")

        return "\n".join(formatted)

    def _record_retry_history(self, context: FeedbackContext,
                            decision: RetryDecision,
                            instruction: FixInstruction):
        """记录重试历史"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "layer": context.layer_name,
            "agent": context.agent_name,
            "attempt": context.attempt_number,
            "decision": decision.value,
            "target_agent": instruction.target_agent,
            "errors_count": len(context.validation_errors)
        }
        self.retry_history.append(record)

        # 限制历史记录大小
        if len(self.retry_history) > 1000:
            self.retry_history = self.retry_history[-500:]

    def get_retry_statistics(self) -> Dict[str, Any]:
        """获取重试统计"""
        if not self.retry_history:
            return {"total_retries": 0}

        decisions = {}
        for record in self.retry_history:
            decision = record["decision"]
            decisions[decision] = decisions.get(decision, 0) + 1

        return {
            "total_retries": len(self.retry_history),
            "decision_distribution": decisions,
            "average_attempts": sum(r["attempt"] for r in self.retry_history) / len(self.retry_history),
            "most_failed_agent": self._get_most_failed_agent()
        }

    def _get_most_failed_agent(self) -> str:
        """获取失败最多的Agent"""
        agent_failures = {}
        for record in self.retry_history:
            agent = record["agent"]
            agent_failures[agent] = agent_failures.get(agent, 0) + 1

        if agent_failures:
            return max(agent_failures, key=agent_failures.get)
        return "none"


# 全局实例
_feedback_engine = None

def get_feedback_engine(max_retries: int = 3) -> FeedbackLoopEngine:
    """获取全局反馈引擎实例"""
    global _feedback_engine
    if _feedback_engine is None:
        _feedback_engine = FeedbackLoopEngine(max_retries)
    return _feedback_engine


def demonstrate_feedback_loop():
    """演示反馈循环"""
    print("=" * 80)
    print("Perfect21 反馈循环机制演示")
    print("=" * 80)

    engine = get_feedback_engine()

    # 模拟测试失败场景
    context = FeedbackContext(
        layer_name="implementation",
        agent_name="python-pro",
        original_input="实现用户登录功能",
        execution_result={"code": "def login(): pass"},
        validation_errors=[
            "Test failed: login() missing password validation",
            "Test failed: No JWT token generation"
        ],
        attempt_number=1,
        max_retries=3,
        execution_history=[]
    )

    decision, instruction = engine.handle_validation_failure(context)

    print(f"\n决策: {decision.value}")
    print(f"目标Agent: {instruction.target_agent}")
    print(f"优先级: {instruction.priority}")
    print(f"预估时间: {instruction.estimated_time}分钟")
    print("\n修复指令预览:")
    print(instruction.fix_prompt[:500] + "...")

    # 显示统计
    stats = engine.get_retry_statistics()
    print("\n重试统计:")
    print(json.dumps(stats, indent=2, ensure_ascii=False))

    print("\n" + "=" * 80)
    print("演示完成！反馈循环可以智能处理验证失败。")
    print("=" * 80)


if __name__ == "__main__":
    demonstrate_feedback_loop()