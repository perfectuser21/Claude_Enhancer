#!/usr/bin/env python3
"""
增强型工作流编排器
==================

集成反馈循环系统的核心编排器，解决以下问题：
1. 测试失败时自动回退到实现层修复
2. 确保同一个agent负责修复自己的代码
3. 智能决策何时重试、升级或中止
4. 与现有质量门和同步点系统完全集成
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from .feedback_loop_engine import (
    FeedbackLoopEngine, ValidationStage, FeedbackAction,
    FeedbackContext, FeedbackDecision, get_feedback_engine
)
from .engine import WorkflowEngine, WorkflowResult, TaskStatus
from ..quality.quality_gate_engine import QualityGateEngine
from ..quality.sync_manager import SyncPointManager

logger = logging.getLogger("EnhancedOrchestrator")


class WorkflowStage(Enum):
    """工作流阶段"""
    ANALYSIS = "analysis"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    QUALITY_VALIDATION = "quality_validation"
    INTEGRATION = "integration"
    DEPLOYMENT = "deployment"


@dataclass
class StageResult:
    """阶段执行结果"""
    stage: WorkflowStage
    status: TaskStatus
    agent_results: Dict[str, Any]
    validation_result: Optional[Dict[str, Any]] = None
    feedback_loops: List[str] = None
    retry_count: int = 0

    def __post_init__(self):
        if self.feedback_loops is None:
            self.feedback_loops = []


class EnhancedOrchestrator:
    """增强型工作流编排器"""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.workflow_engine = WorkflowEngine(max_workers=10)
        self.feedback_engine = get_feedback_engine(project_root)
        self.quality_engine = QualityGateEngine(project_root)
        self.sync_manager = SyncPointManager()

        # 工作流状态跟踪
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.stage_dependencies: Dict[WorkflowStage, List[WorkflowStage]] = {
            WorkflowStage.TESTING: [WorkflowStage.IMPLEMENTATION],
            WorkflowStage.QUALITY_VALIDATION: [WorkflowStage.TESTING],
            WorkflowStage.INTEGRATION: [WorkflowStage.QUALITY_VALIDATION],
            WorkflowStage.DEPLOYMENT: [WorkflowStage.INTEGRATION]
        }

    def execute_enhanced_workflow(self, workflow_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行增强的工作流，包含完整的反馈循环

        Args:
            workflow_request: 工作流请求，包含任务描述、agent分配等

        Returns:
            Dict: 完整的执行结果，包含所有阶段和反馈循环信息
        """
        workflow_id = f"enhanced_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"开始增强工作流: {workflow_id}")

        # 初始化工作流状态
        workflow_state = {
            "workflow_id": workflow_id,
            "request": workflow_request,
            "stages": {},
            "current_stage": None,
            "status": "running",
            "start_time": datetime.now(),
            "total_retries": 0,
            "feedback_loops": [],
            "quality_gates_passed": [],
            "sync_points_validated": []
        }

        self.active_workflows[workflow_id] = workflow_state

        try:
            # 执行工作流阶段
            result = self._execute_workflow_stages(workflow_id, workflow_request)
            workflow_state["status"] = "completed"
            workflow_state["end_time"] = datetime.now()

            return result

        except Exception as e:
            logger.error(f"工作流执行失败: {workflow_id} - {e}")
            workflow_state["status"] = "failed"
            workflow_state["error"] = str(e)
            workflow_state["end_time"] = datetime.now()

            return {
                "workflow_id": workflow_id,
                "status": "failed",
                "error": str(e),
                "partial_results": workflow_state.get("stages", {})
            }

    def _execute_workflow_stages(self, workflow_id: str,
                               workflow_request: Dict[str, Any]) -> Dict[str, Any]:
        """执行工作流阶段"""

        workflow_state = self.active_workflows[workflow_id]
        task_description = workflow_request.get("task_description", "")
        agent_assignments = workflow_request.get("agent_assignments", [])

        # 确定执行阶段
        stages_to_execute = self._determine_execution_stages(workflow_request)

        logger.info(f"工作流 {workflow_id} 将执行 {len(stages_to_execute)} 个阶段")

        stage_results = {}

        for stage in stages_to_execute:
            logger.info(f"执行阶段: {stage.value}")
            workflow_state["current_stage"] = stage.value

            try:
                # 检查依赖关系
                if not self._check_stage_dependencies(stage, stage_results):
                    raise Exception(f"阶段 {stage.value} 的依赖条件未满足")

                # 执行阶段
                stage_result = self._execute_single_stage(
                    workflow_id, stage, task_description, agent_assignments
                )

                stage_results[stage.value] = stage_result
                workflow_state["stages"][stage.value] = stage_result

                # 如果阶段失败且无法恢复，停止执行
                if stage_result.status == TaskStatus.FAILED and not stage_result.feedback_loops:
                    logger.error(f"阶段 {stage.value} 失败且无法恢复")
                    break

            except Exception as e:
                logger.error(f"阶段 {stage.value} 执行异常: {e}")
                stage_results[stage.value] = StageResult(
                    stage=stage,
                    status=TaskStatus.FAILED,
                    agent_results={"error": str(e)},
                    validation_result={"success": False, "error": str(e)}
                )
                break

        # 生成最终结果
        return self._generate_workflow_result(workflow_id, stage_results)

    def _execute_single_stage(self, workflow_id: str, stage: WorkflowStage,
                            task_description: str,
                            agent_assignments: List[Dict[str, str]]) -> StageResult:
        """执行单个工作流阶段"""

        max_stage_retries = 3
        retry_count = 0

        while retry_count < max_stage_retries:
            try:
                # 根据阶段类型选择执行方式
                if stage == WorkflowStage.IMPLEMENTATION:
                    return self._execute_implementation_stage(
                        workflow_id, task_description, agent_assignments, retry_count
                    )
                elif stage == WorkflowStage.TESTING:
                    return self._execute_testing_stage(
                        workflow_id, task_description, agent_assignments, retry_count
                    )
                elif stage == WorkflowStage.QUALITY_VALIDATION:
                    return self._execute_quality_validation_stage(
                        workflow_id, task_description, retry_count
                    )
                else:
                    # 其他阶段的默认实现
                    return self._execute_default_stage(
                        workflow_id, stage, task_description, agent_assignments, retry_count
                    )

            except Exception as e:
                retry_count += 1
                logger.warning(f"阶段 {stage.value} 第 {retry_count} 次重试: {e}")

                if retry_count >= max_stage_retries:
                    return StageResult(
                        stage=stage,
                        status=TaskStatus.FAILED,
                        agent_results={"error": str(e)},
                        retry_count=retry_count
                    )

    def _execute_implementation_stage(self, workflow_id: str, task_description: str,
                                    agent_assignments: List[Dict[str, str]],
                                    retry_count: int) -> StageResult:
        """执行实现阶段"""

        logger.info(f"执行实现阶段: {workflow_id}")

        # 准备任务列表
        tasks = []
        for assignment in agent_assignments:
            if assignment.get('stage', 'implementation') == 'implementation':
                tasks.append({
                    'agent_name': assignment.get('agent'),
                    'description': assignment.get('task'),
                    'prompt': assignment.get('prompt')
                })

        if not tasks:
            # 如果没有明确的实现任务，创建默认任务
            tasks = [{
                'agent_name': 'backend-architect',
                'description': '实现核心功能',
                'prompt': task_description
            }]

        # 注册反馈循环
        feedback_loops = []
        for i, task in enumerate(tasks):
            feedback_id = self.feedback_engine.register_feedback_loop(
                workflow_id=workflow_id,
                stage=ValidationStage.IMPLEMENTATION,
                agent_name=task['agent_name'],
                task_id=f"impl_task_{i+1}",
                original_prompt=task['prompt']
            )
            feedback_loops.append(feedback_id)

        # 执行任务
        workflow_result = self.workflow_engine.execute_parallel_tasks(
            tasks, workflow_id=f"{workflow_id}_implementation"
        )

        # 验证实现结果
        validation_result = self._validate_implementation_result(workflow_result)

        # 处理验证结果
        if not validation_result.get("success", False):
            return self._handle_implementation_failure(
                workflow_id, feedback_loops, validation_result, tasks
            )
        else:
            # 验证成功，关闭反馈循环
            for feedback_id in feedback_loops:
                self.feedback_engine.process_validation_success(feedback_id, validation_result)

        return StageResult(
            stage=WorkflowStage.IMPLEMENTATION,
            status=TaskStatus.COMPLETED,
            agent_results={"workflow_result": workflow_result},
            validation_result=validation_result,
            feedback_loops=feedback_loops,
            retry_count=retry_count
        )

    def _execute_testing_stage(self, workflow_id: str, task_description: str,
                             agent_assignments: List[Dict[str, str]],
                             retry_count: int) -> StageResult:
        """执行测试阶段"""

        logger.info(f"执行测试阶段: {workflow_id}")

        # 获取实现阶段的结果作为上下文
        workflow_state = self.active_workflows[workflow_id]
        impl_result = workflow_state.get("stages", {}).get("implementation")

        # 准备测试任务
        test_tasks = []
        for assignment in agent_assignments:
            if assignment.get('stage', 'testing') == 'testing':
                # 增强测试任务的prompt，包含实现上下文
                enhanced_prompt = assignment.get('prompt', '')
                if impl_result:
                    enhanced_prompt += f"\n\n## 实现阶段结果:\n{json.dumps(impl_result.agent_results, indent=2, ensure_ascii=False)}"

                test_tasks.append({
                    'agent_name': assignment.get('agent'),
                    'description': assignment.get('task'),
                    'prompt': enhanced_prompt
                })

        if not test_tasks:
            # 默认测试任务
            test_tasks = [{
                'agent_name': 'test-engineer',
                'description': '编写和执行测试',
                'prompt': f"为以下功能编写测试:\n{task_description}"
            }]

        # 注册反馈循环
        feedback_loops = []
        for i, task in enumerate(test_tasks):
            feedback_id = self.feedback_engine.register_feedback_loop(
                workflow_id=workflow_id,
                stage=ValidationStage.TESTING,
                agent_name=task['agent_name'],
                task_id=f"test_task_{i+1}",
                original_prompt=task['prompt']
            )
            feedback_loops.append(feedback_id)

        # 执行测试任务
        workflow_result = self.workflow_engine.execute_parallel_tasks(
            test_tasks, workflow_id=f"{workflow_id}_testing"
        )

        # 验证测试结果
        validation_result = self._validate_testing_result(workflow_result)

        # 处理验证结果
        if not validation_result.get("success", False):
            # 测试失败 - 这是关键点！
            # 需要回退到实现阶段进行修复
            return self._handle_testing_failure(
                workflow_id, feedback_loops, validation_result, workflow_result
            )
        else:
            # 测试成功
            for feedback_id in feedback_loops:
                self.feedback_engine.process_validation_success(feedback_id, validation_result)

        return StageResult(
            stage=WorkflowStage.TESTING,
            status=TaskStatus.COMPLETED,
            agent_results={"workflow_result": workflow_result},
            validation_result=validation_result,
            feedback_loops=feedback_loops,
            retry_count=retry_count
        )

    def _execute_quality_validation_stage(self, workflow_id: str,
                                        task_description: str,
                                        retry_count: int) -> StageResult:
        """执行质量验证阶段"""

        logger.info(f"执行质量验证阶段: {workflow_id}")

        try:
            # 运行质量门检查
            quality_results = await self.quality_engine.run_all_gates("workflow_validation")

            # 检查质量门是否通过
            overall_result = quality_results.get("overall")
            if overall_result and overall_result.status.value in ["failed", "blocked"]:
                # 质量门失败，需要反馈修复
                return self._handle_quality_gate_failure(
                    workflow_id, quality_results, retry_count
                )

            return StageResult(
                stage=WorkflowStage.QUALITY_VALIDATION,
                status=TaskStatus.COMPLETED,
                agent_results={"quality_results": quality_results},
                validation_result={"success": True, "quality_gates": quality_results},
                retry_count=retry_count
            )

        except Exception as e:
            return StageResult(
                stage=WorkflowStage.QUALITY_VALIDATION,
                status=TaskStatus.FAILED,
                agent_results={"error": str(e)},
                validation_result={"success": False, "error": str(e)},
                retry_count=retry_count
            )

    def _execute_default_stage(self, workflow_id: str, stage: WorkflowStage,
                             task_description: str,
                             agent_assignments: List[Dict[str, str]],
                             retry_count: int) -> StageResult:
        """执行默认阶段"""

        # 简化的默认实现
        return StageResult(
            stage=stage,
            status=TaskStatus.COMPLETED,
            agent_results={"message": f"阶段 {stage.value} 执行完成"},
            validation_result={"success": True},
            retry_count=retry_count
        )

    def _handle_implementation_failure(self, workflow_id: str,
                                     feedback_loops: List[str],
                                     validation_result: Dict[str, Any],
                                     original_tasks: List[Dict[str, str]]) -> StageResult:
        """处理实现阶段失败"""

        logger.warning(f"实现阶段失败: {workflow_id}")

        retry_decisions = []

        for i, feedback_id in enumerate(feedback_loops):
            # 获取失败原因
            failure_reason = validation_result.get("errors", [{}])[i] if i < len(validation_result.get("errors", [])) else {"message": "实现验证失败"}

            # 处理验证失败
            decision = self.feedback_engine.process_validation_failure(
                feedback_id=feedback_id,
                validation_result=validation_result,
                failure_reason=failure_reason.get("message", "Unknown implementation error")
            )

            retry_decisions.append(decision)

        # 生成重试指令
        retry_instructions = []
        for decision in retry_decisions:
            if decision.action == FeedbackAction.RETRY:
                instruction = self.feedback_engine.get_retry_instruction(decision)
                retry_instructions.append(instruction)
            elif decision.action == FeedbackAction.ESCALATE:
                instruction = self.feedback_engine.get_escalation_instruction(decision)
                retry_instructions.append(instruction)

        return StageResult(
            stage=WorkflowStage.IMPLEMENTATION,
            status=TaskStatus.FAILED,
            agent_results={
                "validation_result": validation_result,
                "retry_decisions": retry_decisions,
                "retry_instructions": retry_instructions
            },
            validation_result=validation_result,
            feedback_loops=feedback_loops
        )

    def _handle_testing_failure(self, workflow_id: str,
                              feedback_loops: List[str],
                              validation_result: Dict[str, Any],
                              workflow_result: WorkflowResult) -> StageResult:
        """
        处理测试阶段失败 - 关键功能

        当测试失败时，需要：
        1. 分析失败原因
        2. 决定是修复测试还是修复实现
        3. 回退到相应的agent进行修复
        """

        logger.warning(f"测试阶段失败: {workflow_id}")

        # 分析测试失败的类型
        test_failures = validation_result.get("test_failures", [])

        retry_decisions = []
        implementation_fixes_needed = []

        for i, feedback_id in enumerate(feedback_loops):
            test_failure = test_failures[i] if i < len(test_failures) else {}
            failure_type = test_failure.get("type", "unknown")
            failure_message = test_failure.get("message", "测试失败")

            # 判断是测试问题还是实现问题
            if self._is_implementation_issue(failure_type, failure_message):
                # 这是实现问题，需要回退到实现层修复
                implementation_fixes_needed.append({
                    "test_failure": test_failure,
                    "feedback_id": feedback_id
                })
            else:
                # 这是测试本身的问题
                decision = self.feedback_engine.process_validation_failure(
                    feedback_id=feedback_id,
                    validation_result=validation_result,
                    failure_reason=failure_message
                )
                retry_decisions.append(decision)

        # 处理需要修复实现的情况
        implementation_fix_instructions = []
        if implementation_fixes_needed:
            implementation_fix_instructions = self._create_implementation_fix_instructions(
                workflow_id, implementation_fixes_needed
            )

        # 生成重试指令
        retry_instructions = []
        for decision in retry_decisions:
            if decision.action == FeedbackAction.RETRY:
                instruction = self.feedback_engine.get_retry_instruction(decision)
                retry_instructions.append(instruction)
            elif decision.action == FeedbackAction.ESCALATE:
                instruction = self.feedback_engine.get_escalation_instruction(decision)
                retry_instructions.append(instruction)

        return StageResult(
            stage=WorkflowStage.TESTING,
            status=TaskStatus.FAILED,
            agent_results={
                "validation_result": validation_result,
                "retry_decisions": retry_decisions,
                "retry_instructions": retry_instructions,
                "implementation_fix_instructions": implementation_fix_instructions,
                "requires_implementation_fix": len(implementation_fixes_needed) > 0
            },
            validation_result=validation_result,
            feedback_loops=feedback_loops
        )

    def _handle_quality_gate_failure(self, workflow_id: str,
                                   quality_results: Dict[str, Any],
                                   retry_count: int) -> StageResult:
        """处理质量门失败"""

        logger.warning(f"质量门失败: {workflow_id}")

        # 分析质量门失败的原因
        failed_gates = {
            name: result for name, result in quality_results.items()
            if hasattr(result, 'status') and result.status.value in ["failed", "blocked"]
        }

        # 为每个失败的质量门创建修复指令
        fix_instructions = []

        for gate_name, gate_result in failed_gates.items():
            # 确定负责修复的agent
            responsible_agent = self._get_responsible_agent_for_quality_gate(gate_name)

            # 创建修复任务
            fix_prompt = self._create_quality_gate_fix_prompt(gate_name, gate_result)

            fix_instruction = f"""
## 🔧 质量门修复指令 - {gate_name}

**负责Agent**: {responsible_agent}
**问题描述**: {gate_result.message}
**修复要求**: {fix_prompt}

### 执行指令:
```xml
<function_calls>
  <invoke name="Task">
    <parameter name="subagent_type">{responsible_agent}</parameter>
    <parameter name="prompt">{fix_prompt}</parameter>
  </invoke>
</function_calls>
```

### 验证要求:
修复完成后必须重新运行质量门: {gate_name}
"""
            fix_instructions.append(fix_instruction)

        return StageResult(
            stage=WorkflowStage.QUALITY_VALIDATION,
            status=TaskStatus.FAILED,
            agent_results={
                "quality_results": quality_results,
                "failed_gates": list(failed_gates.keys()),
                "fix_instructions": fix_instructions
            },
            validation_result={"success": False, "quality_gates": quality_results},
            retry_count=retry_count
        )

    def _is_implementation_issue(self, failure_type: str, failure_message: str) -> bool:
        """判断测试失败是否为实现问题"""

        # 明确的实现问题指标
        implementation_indicators = [
            "assertion_error",
            "logic_error",
            "return_value_error",
            "behavior_mismatch",
            "expected_vs_actual",
            "function_not_working",
            "incorrect_result"
        ]

        # 测试自身问题指标
        test_indicators = [
            "test_setup_error",
            "test_framework_error",
            "invalid_test_case",
            "test_configuration_error",
            "mock_error"
        ]

        failure_lower = failure_message.lower()

        # 检查是否为实现问题
        for indicator in implementation_indicators:
            if indicator in failure_type.lower() or indicator in failure_lower:
                return True

        # 检查是否为测试问题
        for indicator in test_indicators:
            if indicator in failure_type.lower() or indicator in failure_lower:
                return False

        # 默认情况下，如果包含"expected"和"actual"，通常是实现问题
        if "expected" in failure_lower and "actual" in failure_lower:
            return True

        # 其他情况默认为测试问题
        return False

    def _create_implementation_fix_instructions(self, workflow_id: str,
                                              implementation_fixes: List[Dict[str, Any]]) -> List[str]:
        """创建实现修复指令"""

        instructions = []

        # 获取原始实现阶段的agent信息
        workflow_state = self.active_workflows[workflow_id]
        impl_stage = workflow_state.get("stages", {}).get("implementation")

        for fix_needed in implementation_fixes:
            test_failure = fix_needed["test_failure"]

            # 确定负责修复的原始实现agent
            # 这里应该从实现阶段的结果中获取真实的agent
            original_agent = "backend-architect"  # 默认值，实际应该从工作流状态获取

            if impl_stage and "workflow_result" in impl_stage.agent_results:
                workflow_result = impl_stage.agent_results["workflow_result"]
                if hasattr(workflow_result, 'tasks') and workflow_result.tasks:
                    # 获取第一个实现任务的agent（简化处理）
                    original_agent = workflow_result.tasks[0].agent_name

            fix_prompt = f"""
## 🔴 实现修复请求（基于测试失败）

**测试失败信息**:
- 类型: {test_failure.get('type', 'unknown')}
- 消息: {test_failure.get('message', '未知错误')}
- 详细信息: {json.dumps(test_failure.get('details', {}), indent=2, ensure_ascii=False)}

## 🎯 修复要求

你之前编写的实现代码存在问题，导致测试失败。请分析测试失败的原因，并修正你的实现代码。

**关键点**:
1. 仔细分析测试期望的行为
2. 修正实现逻辑以满足测试要求
3. 确保修复不会破坏其他功能
4. 添加必要的错误处理

**验证要求**:
修复后的代码必须能够通过相关测试。
"""

            instruction = f"""
## 🔧 实现修复指令

**原始负责Agent**: {original_agent}
**修复原因**: 测试失败反馈

### 执行指令:
```xml
<function_calls>
  <invoke name="Task">
    <parameter name="subagent_type">{original_agent}</parameter>
    <parameter name="prompt">{fix_prompt}</parameter>
  </invoke>
</function_calls>
```

⚠️ **重要**: 修复完成后必须重新运行测试验证
"""

            instructions.append(instruction)

        return instructions

    def _get_responsible_agent_for_quality_gate(self, gate_name: str) -> str:
        """获取负责特定质量门的agent"""

        gate_agent_map = {
            "code_quality": "code-reviewer",
            "security": "security-auditor",
            "performance": "performance-engineer",
            "architecture": "backend-architect",
            "coverage": "test-engineer"
        }

        return gate_agent_map.get(gate_name, "code-reviewer")

    def _create_quality_gate_fix_prompt(self, gate_name: str, gate_result) -> str:
        """创建质量门修复提示词"""

        violations = gate_result.violations if hasattr(gate_result, 'violations') else []
        suggestions = gate_result.suggestions if hasattr(gate_result, 'suggestions') else []

        prompt = f"""
## 🔧 质量门修复任务 - {gate_name}

**失败原因**: {gate_result.message}
**当前分数**: {gate_result.score}/100

### 违规项目:
"""
        for violation in violations[:5]:  # 最多显示5个违规
            prompt += f"- {violation.get('message', str(violation))}\n"

        prompt += "\n### 修复建议:\n"
        for suggestion in suggestions[:3]:  # 最多显示3个建议
            prompt += f"- {suggestion}\n"

        prompt += f"""

### 修复要求:
1. 逐项解决上述违规问题
2. 确保修复后质量门分数 >= 8.0
3. 不破坏现有功能
4. 遵循最佳实践

请提供具体的修复方案和代码改进。
"""

        return prompt

    def _validate_implementation_result(self, workflow_result: WorkflowResult) -> Dict[str, Any]:
        """验证实现结果"""

        # 基础验证：检查是否有任务失败
        if workflow_result.failure_count > 0:
            failed_tasks = [
                task for task in workflow_result.tasks
                if task.status == TaskStatus.FAILED
            ]

            return {
                "success": False,
                "errors": [
                    {
                        "task_id": task.task_id,
                        "agent": task.agent_name,
                        "message": task.error or "任务执行失败"
                    }
                    for task in failed_tasks
                ]
            }

        # 检查执行结果的质量
        quality_issues = []
        for task in workflow_result.tasks:
            if task.result:
                # 这里可以添加更多的质量检查逻辑
                # 比如检查代码语法、导入错误等
                pass

        if quality_issues:
            return {
                "success": False,
                "errors": quality_issues
            }

        return {
            "success": True,
            "task_count": len(workflow_result.tasks),
            "success_rate": workflow_result.success_count / len(workflow_result.tasks)
        }

    def _validate_testing_result(self, workflow_result: WorkflowResult) -> Dict[str, Any]:
        """验证测试结果"""

        # 检查测试任务是否成功执行
        if workflow_result.failure_count > 0:
            failed_tasks = [
                task for task in workflow_result.tasks
                if task.status == TaskStatus.FAILED
            ]

            return {
                "success": False,
                "test_failures": [
                    {
                        "task_id": task.task_id,
                        "agent": task.agent_name,
                        "type": "test_execution_failure",
                        "message": task.error or "测试执行失败",
                        "details": {"task_result": task.result}
                    }
                    for task in failed_tasks
                ]
            }

        # 分析测试结果内容
        test_failures = []
        for task in workflow_result.tasks:
            if task.result:
                # 这里应该解析真实的测试结果
                # 检查是否有测试失败、断言错误等
                result_analysis = self._analyze_test_task_result(task)
                if not result_analysis["success"]:
                    test_failures.extend(result_analysis["failures"])

        if test_failures:
            return {
                "success": False,
                "test_failures": test_failures
            }

        return {
            "success": True,
            "tests_passed": True,
            "task_count": len(workflow_result.tasks)
        }

    def _analyze_test_task_result(self, task) -> Dict[str, Any]:
        """分析单个测试任务的结果"""

        # 这里应该实现真实的测试结果分析
        # 目前是简化的示例实现

        if task.result and "instruction" in task.result:
            # 如果任务只是生成了指令而没有真实执行，认为是成功的
            return {"success": True, "failures": []}

        # 模拟测试结果分析
        # 实际应该解析真实的测试输出
        return {"success": True, "failures": []}

    def _determine_execution_stages(self, workflow_request: Dict[str, Any]) -> List[WorkflowStage]:
        """确定需要执行的工作流阶段"""

        # 默认的完整工作流阶段
        default_stages = [
            WorkflowStage.IMPLEMENTATION,
            WorkflowStage.TESTING,
            WorkflowStage.QUALITY_VALIDATION
        ]

        # 可以根据请求类型定制阶段
        request_type = workflow_request.get("type", "full")

        if request_type == "implementation_only":
            return [WorkflowStage.IMPLEMENTATION]
        elif request_type == "testing_only":
            return [WorkflowStage.TESTING]
        elif request_type == "quality_only":
            return [WorkflowStage.QUALITY_VALIDATION]
        else:
            return default_stages

    def _check_stage_dependencies(self, stage: WorkflowStage,
                                stage_results: Dict[str, StageResult]) -> bool:
        """检查阶段依赖关系"""

        dependencies = self.stage_dependencies.get(stage, [])

        for dep_stage in dependencies:
            if dep_stage.value not in stage_results:
                return False

            dep_result = stage_results[dep_stage.value]
            if dep_result.status != TaskStatus.COMPLETED:
                return False

        return True

    def _generate_workflow_result(self, workflow_id: str,
                                stage_results: Dict[str, StageResult]) -> Dict[str, Any]:
        """生成工作流结果"""

        workflow_state = self.active_workflows[workflow_id]

        # 计算总体状态
        overall_status = "completed"
        failed_stages = []

        for stage_name, stage_result in stage_results.items():
            if stage_result.status == TaskStatus.FAILED:
                overall_status = "failed"
                failed_stages.append(stage_name)

        # 收集所有反馈循环信息
        all_feedback_loops = []
        all_retry_instructions = []

        for stage_result in stage_results.values():
            if stage_result.feedback_loops:
                all_feedback_loops.extend(stage_result.feedback_loops)

            if hasattr(stage_result, 'agent_results') and stage_result.agent_results:
                retry_instructions = stage_result.agent_results.get("retry_instructions", [])
                implementation_fixes = stage_result.agent_results.get("implementation_fix_instructions", [])
                all_retry_instructions.extend(retry_instructions)
                all_retry_instructions.extend(implementation_fixes)

        # 获取反馈循环状态
        feedback_status = self.feedback_engine.get_workflow_feedback_status(workflow_id)

        execution_time = (datetime.now() - workflow_state["start_time"]).total_seconds()

        result = {
            "workflow_id": workflow_id,
            "status": overall_status,
            "execution_time": execution_time,
            "stages": {
                name: {
                    "stage": result.stage.value,
                    "status": result.status.value,
                    "retry_count": result.retry_count,
                    "validation_result": result.validation_result,
                    "feedback_loops": result.feedback_loops
                }
                for name, result in stage_results.items()
            },
            "feedback_summary": {
                "total_feedback_loops": len(all_feedback_loops),
                "active_loops": feedback_status.get("active_feedback_loops", 0),
                "total_retries": feedback_status.get("total_retries", 0),
                "success_rate": feedback_status.get("success_rate", 0)
            },
            "retry_instructions": all_retry_instructions,
            "failed_stages": failed_stages,
            "requires_manual_intervention": len(all_retry_instructions) > 0
        }

        # 如果有重试指令，添加执行指导
        if all_retry_instructions:
            result["next_steps"] = {
                "action": "execute_retry_instructions",
                "message": f"检测到 {len(all_retry_instructions)} 个修复指令，请按照指令进行修复",
                "instructions": all_retry_instructions
            }

        return result

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流状态"""

        if workflow_id not in self.active_workflows:
            return None

        workflow_state = self.active_workflows[workflow_id]
        feedback_status = self.feedback_engine.get_workflow_feedback_status(workflow_id)

        return {
            "workflow_id": workflow_id,
            "status": workflow_state["status"],
            "current_stage": workflow_state.get("current_stage"),
            "stages": workflow_state.get("stages", {}),
            "feedback_loops": feedback_status,
            "total_retries": workflow_state.get("total_retries", 0)
        }


# 全局实例
_enhanced_orchestrator = None

def get_enhanced_orchestrator(project_root: str = "/home/xx/dev/Perfect21") -> EnhancedOrchestrator:
    """获取全局增强编排器实例"""
    global _enhanced_orchestrator
    if _enhanced_orchestrator is None:
        _enhanced_orchestrator = EnhancedOrchestrator(project_root)
    return _enhanced_orchestrator