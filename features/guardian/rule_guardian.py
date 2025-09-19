#!/usr/bin/env python3
"""
Perfect21 规则守护者 - Rule Guardian
实时监督Claude Code遵守Perfect21规则的内置机制
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)


class ViolationType(Enum):
    """违规类型"""
    TOO_FEW_AGENTS = "too_few_agents"          # Agent数量不足
    WRONG_AGENT_COMBO = "wrong_combo"          # Agent组合错误
    NO_PARALLEL = "no_parallel"                # 未并行执行
    MISSING_QUALITY_CHECK = "missing_check"    # 缺少质量检查
    SKIP_FEEDBACK = "skip_feedback"            # 跳过反馈循环
    WRONG_COMMIT_FORMAT = "wrong_commit"       # 提交格式错误


@dataclass
class RuleViolation:
    """规则违规记录"""
    violation_type: ViolationType
    rule_name: str
    expected: Any
    actual: Any
    severity: str  # critical, high, medium, low
    suggestion: str


@dataclass
class GuardianCheckpoint:
    """守护检查点"""
    stage: str  # 阶段名称
    must_check: List[str]  # 必须检查的规则
    auto_fix: bool  # 是否自动修复
    block_on_violation: bool  # 违规时是否阻止继续


class RuleGuardian:
    """
    规则守护者 - Perfect21的实时监督机制

    这不是一个独立的执行系统，而是Claude Code的自我约束工具
    在每个关键决策点，Claude Code应该调用这个守护者检查是否符合规则
    """

    def __init__(self):
        self.rules = self._load_rules()
        self.checkpoints = self._initialize_checkpoints()
        self.violation_history = []
        self.current_context = {}

        logger.info("🛡️ Perfect21规则守护者已激活")

    def _load_rules(self) -> Dict:
        """加载Perfect21规则"""
        # 默认规则（总是使用，确保稳定）
        default_rules = {
            "agent_rules": {
                "min_agents": 3,
                "max_agents": 8,
                "prefer_parallel": True
            },
            "workflow_rules": {
                "require_feedback_loop": True,
                "require_quality_gates": True
            },
            "git_rules": {
                "commit_format": ["feat:", "fix:", "docs:", "test:", "refactor:", "perf:", "chore:"],
                "require_tests": True
            }
        }

        # 尝试加载自定义规则
        rules_path = Path(__file__).parent.parent.parent / "rules" / "perfect21_rules.yaml"
        if rules_path.exists():
            try:
                with open(rules_path, 'r') as f:
                    custom_rules = yaml.safe_load(f)
                    # 合并规则（自定义规则覆盖默认）
                    if custom_rules:
                        for key in default_rules:
                            if key in custom_rules:
                                default_rules[key].update(custom_rules[key])
            except Exception as e:
                logger.warning(f"加载自定义规则失败，使用默认规则: {e}")

        return default_rules

    def _initialize_checkpoints(self) -> Dict[str, GuardianCheckpoint]:
        """初始化检查点"""
        return {
            "task_analysis": GuardianCheckpoint(
                stage="任务分析",
                must_check=["task_complexity", "agent_requirements"],
                auto_fix=False,
                block_on_violation=False
            ),
            "agent_selection": GuardianCheckpoint(
                stage="Agent选择",
                must_check=["min_agents", "agent_combination", "parallel_execution"],
                auto_fix=True,
                block_on_violation=True
            ),
            "before_execution": GuardianCheckpoint(
                stage="执行前",
                must_check=["execution_mode", "quality_requirements"],
                auto_fix=False,
                block_on_violation=True
            ),
            "after_test": GuardianCheckpoint(
                stage="测试后",
                must_check=["test_results", "feedback_loop"],
                auto_fix=False,
                block_on_violation=True
            ),
            "before_commit": GuardianCheckpoint(
                stage="提交前",
                must_check=["commit_format", "tests_passed", "quality_gates"],
                auto_fix=True,
                block_on_violation=True
            )
        }

    def check_rule(self, checkpoint_name: str, context: Dict[str, Any]) -> Tuple[bool, List[RuleViolation]]:
        """
        检查规则遵守情况

        这个方法应该被Claude Code在关键决策点调用

        Args:
            checkpoint_name: 检查点名称
            context: 当前上下文（如选择的agents、任务类型等）

        Returns:
            (是否通过, 违规列表)
        """

        if checkpoint_name not in self.checkpoints:
            logger.warning(f"未知的检查点: {checkpoint_name}")
            return True, []

        checkpoint = self.checkpoints[checkpoint_name]
        violations = []

        logger.info(f"🔍 规则守护者检查: {checkpoint.stage}")

        # 根据检查点执行不同的规则检查
        if checkpoint_name == "agent_selection":
            violations.extend(self._check_agent_selection(context))
        elif checkpoint_name == "before_execution":
            violations.extend(self._check_execution_mode(context))
        elif checkpoint_name == "after_test":
            violations.extend(self._check_test_feedback(context))
        elif checkpoint_name == "before_commit":
            violations.extend(self._check_commit_rules(context))

        # 记录违规
        if violations:
            self.violation_history.extend(violations)
            self._report_violations(violations)

            # 如果配置了自动修复
            if checkpoint.auto_fix:
                self._suggest_fixes(violations)

            # 如果配置了阻止
            if checkpoint.block_on_violation:
                critical_violations = [v for v in violations if v.severity == "critical"]
                if critical_violations:
                    logger.error("❌ 发现关键违规，必须修正后才能继续！")
                    return False, violations

        passed = len(violations) == 0
        if passed:
            logger.info(f"✅ 通过{checkpoint.stage}规则检查")

        return passed, violations

    def _check_agent_selection(self, context: Dict[str, Any]) -> List[RuleViolation]:
        """检查Agent选择规则"""
        violations = []

        agents = context.get("selected_agents", [])
        task_type = context.get("task_type", "")

        # 检查Agent数量
        min_agents = self.rules["agent_rules"]["min_agents"]
        if len(agents) < min_agents:
            violations.append(RuleViolation(
                violation_type=ViolationType.TOO_FEW_AGENTS,
                rule_name="最少Agent数量",
                expected=f"至少{min_agents}个",
                actual=f"{len(agents)}个",
                severity="critical",
                suggestion=f"Perfect21规则要求至少使用{min_agents}个Agent并行执行"
            ))

        # 检查是否并行
        execution_mode = context.get("execution_mode", "")
        if execution_mode != "parallel" and len(agents) > 1:
            violations.append(RuleViolation(
                violation_type=ViolationType.NO_PARALLEL,
                rule_name="并行执行",
                expected="parallel",
                actual=execution_mode,
                severity="high",
                suggestion="多个Agent必须并行执行，使用单个function_calls批量调用"
            ))

        return violations

    def _check_execution_mode(self, context: Dict[str, Any]) -> List[RuleViolation]:
        """检查执行模式"""
        violations = []

        # 检查是否有质量要求
        if not context.get("quality_requirements"):
            violations.append(RuleViolation(
                violation_type=ViolationType.MISSING_QUALITY_CHECK,
                rule_name="质量要求",
                expected="定义质量标准",
                actual="未定义",
                severity="medium",
                suggestion="需要定义代码质量、测试覆盖率等要求"
            ))

        return violations

    def _check_test_feedback(self, context: Dict[str, Any]) -> List[RuleViolation]:
        """检查测试和反馈规则"""
        violations = []

        test_failed = context.get("test_failed", False)
        feedback_triggered = context.get("feedback_triggered", False)

        # 如果测试失败但没有触发反馈循环
        if test_failed and not feedback_triggered:
            violations.append(RuleViolation(
                violation_type=ViolationType.SKIP_FEEDBACK,
                rule_name="反馈循环",
                expected="测试失败应触发反馈",
                actual="直接继续",
                severity="critical",
                suggestion="测试失败时必须回到实现层，让同一个Agent修复"
            ))

        return violations

    def _check_commit_rules(self, context: Dict[str, Any]) -> List[RuleViolation]:
        """检查提交规则"""
        violations = []

        commit_msg = context.get("commit_message", "")
        valid_prefixes = self.rules["git_rules"]["commit_format"]

        # 检查提交消息格式
        if commit_msg and not any(commit_msg.startswith(prefix) for prefix in valid_prefixes):
            violations.append(RuleViolation(
                violation_type=ViolationType.WRONG_COMMIT_FORMAT,
                rule_name="提交格式",
                expected=f"以{valid_prefixes}之一开头",
                actual=commit_msg[:20],
                severity="medium",
                suggestion=f"使用标准格式: {', '.join(valid_prefixes)}"
            ))

        return violations

    def _report_violations(self, violations: List[RuleViolation]):
        """报告违规情况"""
        print("\n" + "="*60)
        print("⚠️ Perfect21规则守护者发现违规:")
        print("="*60)

        for v in violations:
            severity_icon = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🔵"
            }.get(v.severity, "⚪")

            print(f"\n{severity_icon} [{v.severity.upper()}] {v.rule_name}")
            print(f"   期望: {v.expected}")
            print(f"   实际: {v.actual}")
            print(f"   建议: {v.suggestion}")

        print("\n" + "="*60)

    def _suggest_fixes(self, violations: List[RuleViolation]):
        """建议修复方案"""
        print("\n💡 自动修复建议:")

        for v in violations:
            if v.violation_type == ViolationType.TOO_FEW_AGENTS:
                print(f"- 添加更多相关Agent以达到最少要求")
            elif v.violation_type == ViolationType.NO_PARALLEL:
                print(f"- 使用单个function_calls包含所有Agent调用")
            elif v.violation_type == ViolationType.WRONG_COMMIT_FORMAT:
                print(f"- 修改提交消息格式为标准格式")

    def get_current_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        total_checks = len(self.violation_history)
        critical_count = len([v for v in self.violation_history if v.severity == "critical"])

        return {
            "total_checks": total_checks,
            "violations": len(self.violation_history),
            "critical_violations": critical_count,
            "last_checkpoint": self.current_context.get("last_checkpoint", "none"),
            "health_score": max(0, 100 - critical_count * 20 - len(self.violation_history) * 5)
        }

    def reset(self):
        """重置守护者状态"""
        self.violation_history = []
        self.current_context = {}
        logger.info("规则守护者已重置")


# 全局实例
_guardian = None

def get_rule_guardian() -> RuleGuardian:
    """获取规则守护者实例"""
    global _guardian
    if _guardian is None:
        _guardian = RuleGuardian()
    return _guardian


def demonstrate_rule_guardian():
    """演示规则守护者"""
    print("="*80)
    print("🛡️ Perfect21 规则守护者演示")
    print("="*80)

    guardian = get_rule_guardian()

    # 场景1: Agent选择违规
    print("\n场景1: Agent选择不足")
    context = {
        "selected_agents": ["backend-architect", "test-engineer"],  # 只有2个
        "task_type": "authentication",
        "execution_mode": "sequential"  # 还不是并行
    }

    passed, violations = guardian.check_rule("agent_selection", context)
    print(f"检查结果: {'通过' if passed else '未通过'}")

    # 场景2: 测试失败但没有反馈
    print("\n场景2: 测试失败处理")
    context = {
        "test_failed": True,
        "feedback_triggered": False
    }

    passed, violations = guardian.check_rule("after_test", context)
    print(f"检查结果: {'通过' if passed else '未通过'}")

    # 获取状态
    status = guardian.get_current_status()
    print("\n守护者状态:")
    print(f"  健康分数: {status['health_score']}/100")
    print(f"  总违规数: {status['violations']}")
    print(f"  关键违规: {status['critical_violations']}")

    print("\n" + "="*80)
    print("演示完成！规则守护者会实时监督Perfect21规则的遵守。")
    print("="*80)


if __name__ == "__main__":
    demonstrate_rule_guardian()