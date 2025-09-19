#!/usr/bin/env python3
"""
Perfect21 反馈循环引擎
===================

解决工作流执行中的关键问题：
1. 测试失败时不应继续提交，而是返回修复
2. 同一个agent负责修复自己编写的代码
3. 智能重试机制和状态管理
4. 与现有质量门和同步点系统集成
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

logger = logging.getLogger("FeedbackLoopEngine")


class FeedbackAction(Enum):
    """反馈动作类型"""
    RETRY = "retry"
    ESCALATE = "escalate"
    ABORT = "abort"
    CONTINUE = "continue"
    ROLLBACK = "rollback"


class ValidationStage(Enum):
    """验证阶段"""
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    INTEGRATION = "integration"
    DEPLOYMENT = "deployment"
    QUALITY_GATE = "quality_gate"


class FeedbackSeverity(Enum):
    """反馈严重性"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FeedbackContext:
    """反馈上下文"""
    workflow_id: str
    stage: ValidationStage
    agent_name: str
    task_id: str
    original_prompt: str
    validation_result: Dict[str, Any]
    failure_reason: str
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetryStrategy:
    """重试策略"""
    max_attempts: int = 3
    backoff_factor: float = 1.5
    timeout_multiplier: float = 1.2
    escalation_threshold: int = 2
    abort_conditions: List[str] = field(default_factory=list)
    custom_fixes: Dict[str, str] = field(default_factory=dict)


@dataclass
class FeedbackDecision:
    """反馈决策"""
    action: FeedbackAction
    target_agent: str
    enhanced_prompt: str
    retry_strategy: RetryStrategy
    validation_requirements: Dict[str, Any]
    success_criteria: Dict[str, Any]
    reasoning: str
    confidence: float
    estimated_fix_time: int  # 估计修复时间（秒）


class FeedbackLoopEngine:
    """反馈循环引擎"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.feedback_history: Dict[str, List[FeedbackContext]] = {}
        self.active_feedback_loops: Dict[str, FeedbackContext] = {}
        self.retry_strategies: Dict[str, RetryStrategy] = {}

        # 状态持久化文件
        self.state_file = self.project_root / ".perfect21" / "feedback_state.json"
        self.state_file.parent.mkdir(exist_ok=True)

        # 加载历史状态
        self._load_state()

        # 初始化默认重试策略
        self._init_default_strategies()

    def _init_default_strategies(self):
        """初始化默认重试策略"""
        # 代码实现阶段的重试策略
        self.retry_strategies["implementation"] = RetryStrategy(
            max_attempts=3,
            backoff_factor=1.0,  # 立即重试
            timeout_multiplier=1.5,
            escalation_threshold=2,
            abort_conditions=["syntax_error_repeated", "invalid_imports"],
            custom_fixes={
                "import_error": "请检查导入路径和模块是否存在",
                "syntax_error": "请仔细检查代码语法，特别是括号、引号匹配",
                "type_error": "请检查变量类型和函数签名"
            }
        )

        # 测试阶段的重试策略
        self.retry_strategies["testing"] = RetryStrategy(
            max_attempts=4,  # 测试允许更多重试
            backoff_factor=1.2,
            timeout_multiplier=1.3,
            escalation_threshold=3,
            abort_conditions=["test_framework_error", "dependency_missing"],
            custom_fixes={
                "assertion_error": "请根据测试失败信息修正实现逻辑",
                "test_timeout": "请优化代码性能或调整测试超时时间",
                "missing_test_case": "请补充缺失的测试用例"
            }
        )

        # 质量门阶段的重试策略
        self.retry_strategies["quality_gate"] = RetryStrategy(
            max_attempts=2,  # 质量门重试次数较少
            backoff_factor=2.0,
            timeout_multiplier=1.1,
            escalation_threshold=1,
            abort_conditions=["security_vulnerability", "performance_regression"],
            custom_fixes={
                "code_quality": "请按照代码规范修正质量问题",
                "coverage_low": "请增加测试覆盖率到要求的阈值",
                "security_issue": "请修复安全漏洞，这是强制要求"
            }
        )

    def analyze_failure(self, context: FeedbackContext) -> FeedbackDecision:
        """
        分析失败原因并决定反馈策略

        这是反馈循环的核心决策点
        """
        logger.info(f"分析失败: {context.task_id} - {context.failure_reason}")

        # 获取适用的重试策略
        strategy = self.retry_strategies.get(
            context.stage.value,
            self.retry_strategies["implementation"]
        )

        # 分析失败严重性
        severity = self._assess_failure_severity(context)

        # 判断是否应该中止
        if self._should_abort(context, strategy):
            return FeedbackDecision(
                action=FeedbackAction.ABORT,
                target_agent=context.agent_name,
                enhanced_prompt="",
                retry_strategy=strategy,
                validation_requirements={},
                success_criteria={},
                reasoning=f"达到中止条件: {context.failure_reason}",
                confidence=0.9,
                estimated_fix_time=0
            )

        # 判断是否需要升级处理
        if context.retry_count >= strategy.escalation_threshold:
            return self._create_escalation_decision(context, strategy, severity)

        # 创建重试决策
        return self._create_retry_decision(context, strategy, severity)

    def _assess_failure_severity(self, context: FeedbackContext) -> FeedbackSeverity:
        """评估失败严重性"""
        failure_reason = context.failure_reason.lower()
        validation_result = context.validation_result

        # 检查关键词确定严重性
        critical_keywords = ["security", "vulnerability", "data_loss", "corruption"]
        high_keywords = ["crash", "exception", "error", "failure", "timeout"]
        medium_keywords = ["warning", "deprecated", "slow", "performance"]

        if any(keyword in failure_reason for keyword in critical_keywords):
            return FeedbackSeverity.CRITICAL
        elif any(keyword in failure_reason for keyword in high_keywords):
            return FeedbackSeverity.HIGH
        elif any(keyword in failure_reason for keyword in medium_keywords):
            return FeedbackSeverity.MEDIUM
        else:
            return FeedbackSeverity.LOW

    def _should_abort(self, context: FeedbackContext, strategy: RetryStrategy) -> bool:
        """判断是否应该中止重试"""
        # 超过最大重试次数
        if context.retry_count >= strategy.max_attempts:
            return True

        # 命中中止条件
        for condition in strategy.abort_conditions:
            if condition in context.failure_reason.lower():
                return True

        # 时间窗口检查（超过1小时的反复失败）
        elapsed = datetime.now() - context.created_at
        if elapsed > timedelta(hours=1):
            return True

        return False

    def _create_retry_decision(self, context: FeedbackContext,
                             strategy: RetryStrategy,
                             severity: FeedbackSeverity) -> FeedbackDecision:
        """创建重试决策"""

        # 增强提示词，包含失败信息和修复指导
        enhanced_prompt = self._create_enhanced_prompt(context, strategy)

        # 定义成功标准
        success_criteria = self._define_success_criteria(context)

        # 计算置信度（基于重试次数递减）
        confidence = max(0.3, 0.9 - (context.retry_count * 0.2))

        # 估计修复时间
        base_time = 300  # 5分钟基础时间
        time_multiplier = 1 + (context.retry_count * 0.5)
        estimated_time = int(base_time * time_multiplier)

        return FeedbackDecision(
            action=FeedbackAction.RETRY,
            target_agent=context.agent_name,  # 同一个agent修复
            enhanced_prompt=enhanced_prompt,
            retry_strategy=strategy,
            validation_requirements=self._create_validation_requirements(context),
            success_criteria=success_criteria,
            reasoning=f"第{context.retry_count + 1}次重试，失败原因: {context.failure_reason}",
            confidence=confidence,
            estimated_fix_time=estimated_time
        )

    def _create_escalation_decision(self, context: FeedbackContext,
                                  strategy: RetryStrategy,
                                  severity: FeedbackSeverity) -> FeedbackDecision:
        """创建升级决策"""

        # 选择升级目标agent
        escalation_agent = self._select_escalation_agent(context)

        # 创建升级提示词
        escalation_prompt = self._create_escalation_prompt(context, escalation_agent)

        return FeedbackDecision(
            action=FeedbackAction.ESCALATE,
            target_agent=escalation_agent,
            enhanced_prompt=escalation_prompt,
            retry_strategy=strategy,
            validation_requirements=self._create_validation_requirements(context),
            success_criteria=self._define_success_criteria(context),
            reasoning=f"升级处理，原agent: {context.agent_name}, 失败{context.retry_count}次",
            confidence=0.7,
            estimated_fix_time=600  # 升级需要更多时间
        )

    def _create_enhanced_prompt(self, context: FeedbackContext,
                              strategy: RetryStrategy) -> str:
        """创建增强的提示词"""

        # 基础提示词
        base_prompt = context.original_prompt

        # 失败分析
        failure_analysis = f"""
## 🔴 前次执行失败分析

**失败原因**: {context.failure_reason}
**重试次数**: {context.retry_count + 1}/{strategy.max_attempts}
**验证结果**: {json.dumps(context.validation_result, indent=2, ensure_ascii=False)}

## 🔧 修复指导

**阶段**: {context.stage.value}
**重点关注**:
"""

        # 添加针对性修复建议
        stage_guidance = {
            ValidationStage.IMPLEMENTATION: [
                "请仔细检查代码语法和逻辑错误",
                "确保所有导入的模块和依赖都正确",
                "验证函数签名和返回值类型",
                "注意变量作用域和命名规范"
            ],
            ValidationStage.TESTING: [
                "分析测试失败的具体原因",
                "检查测试用例的期望值是否正确",
                "确保测试环境和数据准备充分",
                "验证测试覆盖了所有关键路径"
            ],
            ValidationStage.QUALITY_GATE: [
                "按照质量标准修正代码规范问题",
                "优化性能瓶颈和资源使用",
                "修复安全漏洞和风险点",
                "确保文档和注释完整"
            ]
        }

        guidance_list = stage_guidance.get(context.stage, stage_guidance[ValidationStage.IMPLEMENTATION])
        for guidance in guidance_list:
            failure_analysis += f"\n- {guidance}"

        # 添加自定义修复建议
        if strategy.custom_fixes:
            failure_analysis += "\n\n**具体修复建议**:\n"
            for error_type, fix_suggestion in strategy.custom_fixes.items():
                if error_type.lower() in context.failure_reason.lower():
                    failure_analysis += f"- {fix_suggestion}\n"

        # 添加验证要求
        failure_analysis += f"""

## ✅ 验证要求

请确保修复后的代码能够通过以下验证:
1. **基本功能**: 核心功能正常工作
2. **错误处理**: 妥善处理异常情况
3. **性能要求**: 满足性能指标
4. **安全标准**: 符合安全规范
5. **测试覆盖**: 有充分的测试验证

## 🎯 成功标准

{self._format_success_criteria(context)}

---

## 📝 原始任务

{base_prompt}
"""

        return failure_analysis

    def _create_escalation_prompt(self, context: FeedbackContext,
                                escalation_agent: str) -> str:
        """创建升级提示词"""

        escalation_prompt = f"""
## 🚨 任务升级处理

**原始负责Agent**: {context.agent_name}
**升级原因**: 经过{context.retry_count}次重试仍未解决
**当前处理Agent**: {escalation_agent}

## 🔍 问题详情

**失败阶段**: {context.stage.value}
**核心问题**: {context.failure_reason}
**验证结果**:
{json.dumps(context.validation_result, indent=2, ensure_ascii=False)}

## 🎯 升级处理要求

作为升级处理的专家，请你:

1. **深度分析**: 从不同角度分析问题根因
2. **架构审查**: 检查是否有架构或设计问题
3. **全面修复**: 不仅修复表面问题，还要确保健壮性
4. **知识传递**: 在代码中添加注释说明修复思路

## 📋 原始任务

{context.original_prompt}

## 🔧 专家级修复指导

请以{escalation_agent}的专业视角，提供高质量的解决方案。
重点关注代码质量、可维护性和健壮性。
"""

        return escalation_prompt

    def _select_escalation_agent(self, context: FeedbackContext) -> str:
        """选择升级处理的agent"""

        # 基于当前阶段和失败类型选择最合适的专家
        escalation_map = {
            ValidationStage.IMPLEMENTATION: {
                "syntax_error": "python-pro",
                "import_error": "backend-architect",
                "logic_error": "fullstack-engineer",
                "type_error": "typescript-pro",
                "default": "code-reviewer"
            },
            ValidationStage.TESTING: {
                "test_failure": "test-engineer",
                "coverage": "e2e-test-specialist",
                "performance": "performance-tester",
                "default": "test-engineer"
            },
            ValidationStage.QUALITY_GATE: {
                "security": "security-auditor",
                "performance": "performance-engineer",
                "architecture": "backend-architect",
                "default": "code-reviewer"
            }
        }

        stage_map = escalation_map.get(context.stage, escalation_map[ValidationStage.IMPLEMENTATION])

        # 查找匹配的错误类型
        for error_type, agent in stage_map.items():
            if error_type != "default" and error_type in context.failure_reason.lower():
                return agent

        # 返回默认agent
        return stage_map["default"]

    def _define_success_criteria(self, context: FeedbackContext) -> Dict[str, Any]:
        """定义成功标准"""

        base_criteria = {
            "execution_success": True,
            "no_critical_errors": True,
            "validation_passed": True
        }

        # 根据阶段添加特定标准
        stage_criteria = {
            ValidationStage.IMPLEMENTATION: {
                "syntax_valid": True,
                "imports_resolved": True,
                "no_runtime_errors": True
            },
            ValidationStage.TESTING: {
                "all_tests_pass": True,
                "coverage_threshold": ">= 80%",
                "no_test_timeouts": True
            },
            ValidationStage.QUALITY_GATE: {
                "quality_score": ">= 8.0",
                "security_issues": "== 0",
                "performance_regression": False
            }
        }

        specific_criteria = stage_criteria.get(context.stage, {})
        base_criteria.update(specific_criteria)

        return base_criteria

    def _create_validation_requirements(self, context: FeedbackContext) -> Dict[str, Any]:
        """创建验证要求"""

        return {
            "stage": context.stage.value,
            "retry_count": context.retry_count + 1,
            "previous_failures": [context.failure_reason],
            "success_criteria": self._define_success_criteria(context),
            "timeout": 300 * (1.2 ** context.retry_count),  # 递增超时
            "validation_type": "enhanced",
            "failure_sensitive": True
        }

    def _format_success_criteria(self, context: FeedbackContext) -> str:
        """格式化成功标准显示"""
        criteria = self._define_success_criteria(context)
        formatted = []

        for criterion, requirement in criteria.items():
            formatted.append(f"- {criterion}: {requirement}")

        return "\n".join(formatted)

    def register_feedback_loop(self, workflow_id: str, stage: ValidationStage,
                             agent_name: str, task_id: str,
                             original_prompt: str) -> str:
        """注册反馈循环"""

        feedback_id = f"{workflow_id}_{stage.value}_{task_id}"

        context = FeedbackContext(
            workflow_id=workflow_id,
            stage=stage,
            agent_name=agent_name,
            task_id=task_id,
            original_prompt=original_prompt,
            validation_result={},
            failure_reason=""
        )

        self.active_feedback_loops[feedback_id] = context

        # 初始化历史记录
        if workflow_id not in self.feedback_history:
            self.feedback_history[workflow_id] = []

        logger.info(f"注册反馈循环: {feedback_id}")
        return feedback_id

    def process_validation_failure(self, feedback_id: str,
                                 validation_result: Dict[str, Any],
                                 failure_reason: str) -> FeedbackDecision:
        """处理验证失败"""

        if feedback_id not in self.active_feedback_loops:
            raise ValueError(f"反馈循环不存在: {feedback_id}")

        context = self.active_feedback_loops[feedback_id]
        context.validation_result = validation_result
        context.failure_reason = failure_reason
        context.retry_count += 1
        context.updated_at = datetime.now()

        # 添加到历史记录
        self.feedback_history[context.workflow_id].append(context)

        # 分析并生成决策
        decision = self.analyze_failure(context)

        # 保存状态
        self._save_state()

        logger.info(f"处理验证失败: {feedback_id} -> {decision.action.value}")
        return decision

    def process_validation_success(self, feedback_id: str,
                                 validation_result: Dict[str, Any]) -> bool:
        """处理验证成功"""

        if feedback_id not in self.active_feedback_loops:
            return False

        context = self.active_feedback_loops[feedback_id]
        context.validation_result = validation_result
        context.updated_at = datetime.now()

        # 移除活跃循环
        del self.active_feedback_loops[feedback_id]

        # 保存到历史
        self.feedback_history[context.workflow_id].append(context)

        logger.info(f"验证成功，关闭反馈循环: {feedback_id}")
        self._save_state()
        return True

    def get_retry_instruction(self, decision: FeedbackDecision) -> str:
        """获取重试指令"""

        if decision.action != FeedbackAction.RETRY:
            return ""

        instruction = f"""
## 🔄 Perfect21 反馈循环重试指令

**目标Agent**: {decision.target_agent}
**修复任务**: 基于验证失败进行代码修复
**置信度**: {decision.confidence:.2f}
**预估时间**: {decision.estimated_fix_time}秒

### 执行指令:
```xml
<function_calls>
  <invoke name="Task">
    <parameter name="subagent_type">{decision.target_agent}</parameter>
    <parameter name="prompt">{decision.enhanced_prompt}</parameter>
  </invoke>
</function_calls>
```

### 验证要求:
{json.dumps(decision.validation_requirements, indent=2, ensure_ascii=False)}

### 成功标准:
{json.dumps(decision.success_criteria, indent=2, ensure_ascii=False)}

⚠️ **重要**: 执行完成后必须重新运行相同的验证流程
"""

        return instruction

    def get_escalation_instruction(self, decision: FeedbackDecision) -> str:
        """获取升级指令"""

        if decision.action != FeedbackAction.ESCALATE:
            return ""

        instruction = f"""
## 🚨 Perfect21 反馈循环升级指令

**升级到**: {decision.target_agent}
**升级原因**: {decision.reasoning}
**置信度**: {decision.confidence:.2f}
**预估时间**: {decision.estimated_fix_time}秒

### 执行指令:
```xml
<function_calls>
  <invoke name="Task">
    <parameter name="subagent_type">{decision.target_agent}</parameter>
    <parameter name="prompt">{decision.enhanced_prompt}</parameter>
  </invoke>
</function_calls>
```

### 专家级要求:
- 深度分析问题根因
- 提供架构级解决方案
- 确保代码健壮性和可维护性
- 添加详细的修复说明

⚠️ **重要**: 升级处理完成后必须进行全面验证
"""

        return instruction

    def get_workflow_feedback_status(self, workflow_id: str) -> Dict[str, Any]:
        """获取工作流反馈状态"""

        active_loops = {fid: ctx for fid, ctx in self.active_feedback_loops.items()
                       if ctx.workflow_id == workflow_id}

        history = self.feedback_history.get(workflow_id, [])

        # 统计信息
        total_failures = len(history)
        total_retries = sum(ctx.retry_count for ctx in history)
        success_rate = 0

        if total_failures > 0:
            successful_fixes = len([ctx for ctx in history if ctx.validation_result.get('success', False)])
            success_rate = successful_fixes / total_failures

        return {
            "workflow_id": workflow_id,
            "active_feedback_loops": len(active_loops),
            "total_failures": total_failures,
            "total_retries": total_retries,
            "success_rate": success_rate,
            "active_loops": {fid: {
                "stage": ctx.stage.value,
                "agent": ctx.agent_name,
                "retry_count": ctx.retry_count,
                "failure_reason": ctx.failure_reason
            } for fid, ctx in active_loops.items()},
            "recent_history": [
                {
                    "stage": ctx.stage.value,
                    "agent": ctx.agent_name,
                    "retry_count": ctx.retry_count,
                    "failure_reason": ctx.failure_reason,
                    "timestamp": ctx.updated_at.isoformat()
                }
                for ctx in history[-5:]  # 最近5条
            ]
        }

    def cleanup_expired_loops(self, max_age_hours: int = 24):
        """清理过期的反馈循环"""

        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        expired_ids = []

        for feedback_id, context in self.active_feedback_loops.items():
            if context.created_at < cutoff_time:
                expired_ids.append(feedback_id)

        for feedback_id in expired_ids:
            logger.warning(f"清理过期反馈循环: {feedback_id}")
            del self.active_feedback_loops[feedback_id]

        if expired_ids:
            self._save_state()

        return len(expired_ids)

    def _save_state(self):
        """保存状态到文件"""
        try:
            state = {
                "active_feedback_loops": {
                    fid: {
                        "workflow_id": ctx.workflow_id,
                        "stage": ctx.stage.value,
                        "agent_name": ctx.agent_name,
                        "task_id": ctx.task_id,
                        "original_prompt": ctx.original_prompt,
                        "validation_result": ctx.validation_result,
                        "failure_reason": ctx.failure_reason,
                        "retry_count": ctx.retry_count,
                        "max_retries": ctx.max_retries,
                        "created_at": ctx.created_at.isoformat(),
                        "updated_at": ctx.updated_at.isoformat(),
                        "metadata": ctx.metadata
                    }
                    for fid, ctx in self.active_feedback_loops.items()
                },
                "feedback_history": {
                    wid: [
                        {
                            "workflow_id": ctx.workflow_id,
                            "stage": ctx.stage.value,
                            "agent_name": ctx.agent_name,
                            "task_id": ctx.task_id,
                            "original_prompt": ctx.original_prompt,
                            "validation_result": ctx.validation_result,
                            "failure_reason": ctx.failure_reason,
                            "retry_count": ctx.retry_count,
                            "max_retries": ctx.max_retries,
                            "created_at": ctx.created_at.isoformat(),
                            "updated_at": ctx.updated_at.isoformat(),
                            "metadata": ctx.metadata
                        }
                        for ctx in history
                    ]
                    for wid, history in self.feedback_history.items()
                }
            }

            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"保存反馈循环状态失败: {e}")

    def _load_state(self):
        """从文件加载状态"""
        try:
            if not self.state_file.exists():
                return

            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)

            # 恢复活跃循环
            for fid, ctx_data in state.get("active_feedback_loops", {}).items():
                context = FeedbackContext(
                    workflow_id=ctx_data["workflow_id"],
                    stage=ValidationStage(ctx_data["stage"]),
                    agent_name=ctx_data["agent_name"],
                    task_id=ctx_data["task_id"],
                    original_prompt=ctx_data["original_prompt"],
                    validation_result=ctx_data["validation_result"],
                    failure_reason=ctx_data["failure_reason"],
                    retry_count=ctx_data["retry_count"],
                    max_retries=ctx_data["max_retries"],
                    created_at=datetime.fromisoformat(ctx_data["created_at"]),
                    updated_at=datetime.fromisoformat(ctx_data["updated_at"]),
                    metadata=ctx_data["metadata"]
                )
                self.active_feedback_loops[fid] = context

            # 恢复历史记录
            for wid, history_data in state.get("feedback_history", {}).items():
                history = []
                for ctx_data in history_data:
                    context = FeedbackContext(
                        workflow_id=ctx_data["workflow_id"],
                        stage=ValidationStage(ctx_data["stage"]),
                        agent_name=ctx_data["agent_name"],
                        task_id=ctx_data["task_id"],
                        original_prompt=ctx_data["original_prompt"],
                        validation_result=ctx_data["validation_result"],
                        failure_reason=ctx_data["failure_reason"],
                        retry_count=ctx_data["retry_count"],
                        max_retries=ctx_data["max_retries"],
                        created_at=datetime.fromisoformat(ctx_data["created_at"]),
                        updated_at=datetime.fromisoformat(ctx_data["updated_at"]),
                        metadata=ctx_data["metadata"]
                    )
                    history.append(context)
                self.feedback_history[wid] = history

        except Exception as e:
            logger.error(f"加载反馈循环状态失败: {e}")


# 全局实例
_feedback_engine = None

def get_feedback_engine(project_root: str = "/home/xx/dev/Perfect21") -> FeedbackLoopEngine:
    """获取全局反馈循环引擎实例"""
    global _feedback_engine
    if _feedback_engine is None:
        _feedback_engine = FeedbackLoopEngine(project_root)
    return _feedback_engine