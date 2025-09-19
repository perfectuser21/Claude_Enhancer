#!/usr/bin/env python3
"""
Perfect21 规则定义 - 改进的工作流规范
定义反馈循环和Git Hook检查点规则，指导Claude Code处理测试失败场景
注意：这只是规则定义，实际执行由Claude Code完成
"""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json

# 导入优化组件
from features.agents.intelligent_selector import get_intelligent_selector
from features.storage.artifact_manager import get_artifact_manager
from features.workflow.feedback_loop import (
    get_feedback_engine,
    FeedbackContext,
    RetryDecision
)
from features.git.git_checkpoints import GitCheckpoints, HookAction

logger = logging.getLogger(__name__)


@dataclass
class LayerResult:
    """层执行结果"""
    layer_name: str
    agents: List[str]
    success: bool
    outputs: Dict[str, Any]
    errors: List[str]
    artifacts: List[str]
    retry_count: int
    git_check_passed: bool


class ImprovedOrchestrator:
    """
    改进的工作流规范定义器
    提供规则定义：
    1. 反馈循环规则 - 定义失败时应该回到原Agent修复
    2. Git Hook检查点规则 - 定义关键节点的质量验证标准
    3. 重试规则 - 定义如何避免无限循环
    注意：这些都是规则定义，执行由Claude Code完成
    """

    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers

        # 集成组件
        self.agent_selector = get_intelligent_selector()
        self.artifact_manager = get_artifact_manager()
        self.feedback_engine = get_feedback_engine(max_retries=3)
        self.git_checkpoints = GitCheckpoints()

        # 执行统计
        self.execution_stats = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "failed_workflows": 0,
            "total_retries": 0,
            "git_checks_failed": 0,
            "feedback_loops_triggered": 0
        }

        logger.info(f"改进Orchestrator初始化完成")

    def generate_workflow_guidance(self, task_description: str,
                                      context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        生成带反馈循环的工作流指导

        为Claude Code提供工作流执行指导，包括：
        - 应该选择哪些Agent
        - 如何处理失败情况
        - 质量检查点要求

        Args:
            task_description: 任务描述
            context: 额外上下文

        Returns:
            工作流执行指导
        """
        start_time = time.time()
        workflow_id = f"workflow_{int(time.time())}"

        try:
            logger.info(f"开始执行工作流: {workflow_id}")
            self.execution_stats["total_workflows"] += 1

            # 1. 智能Agent选择
            agent_selection = self.agent_selector.get_optimal_agents(task_description, context)
            if not agent_selection['success']:
                raise ValueError(f"Agent选择失败: {agent_selection.get('error')}")

            selected_agents = agent_selection['selected_agents']
            logger.info(f"选择了 {len(selected_agents)} 个Agents: {', '.join(selected_agents)}")

            # 2. 创建Artifact会话
            session_id = f"session_{workflow_id}"
            # artifact_manager需要适配

            # 3. 执行5层工作流
            layer_results = []

            # Layer 1: 分析
            analysis_result = self._execute_layer_with_feedback(
                "analysis",
                self._get_layer_agents("analysis", selected_agents),
                task_description,
                session_id
            )
            layer_results.append(analysis_result)

            # Layer 2: 设计
            design_result = self._execute_layer_with_feedback(
                "design",
                self._get_layer_agents("design", selected_agents),
                analysis_result.outputs,
                session_id
            )
            layer_results.append(design_result)

            # Layer 3: 实现（关键层，需要Git检查）
            implementation_result = self._execute_layer_with_feedback(
                "implementation",
                self._get_layer_agents("implementation", selected_agents),
                design_result.outputs,
                session_id
            )

            # 🔥 Git检查点1: pre-commit
            git_check_passed = self._run_git_checkpoint(
                "after_implementation",
                implementation_result,
                session_id
            )

            if not git_check_passed:
                logger.warning("Git pre-commit检查失败，触发修复")
                implementation_result = self._fix_with_feedback(
                    implementation_result,
                    ["pre-commit检查失败，代码格式或lint问题"],
                    session_id
                )

            layer_results.append(implementation_result)

            # Layer 4: 测试（测试失败要回到实现层）
            test_result = self._execute_layer_with_feedback(
                "testing",
                self._get_layer_agents("testing", selected_agents),
                implementation_result.outputs,
                session_id
            )

            # 如果测试失败，回到实现层修复
            if not test_result.success:
                logger.warning("测试失败，回到实现层修复")
                self.execution_stats["feedback_loops_triggered"] += 1

                # 构建修复指令
                fix_context = FeedbackContext(
                    layer_name="implementation",
                    agent_name=implementation_result.agents[0] if implementation_result.agents else "python-pro",
                    original_input=design_result.outputs,
                    execution_result=implementation_result.outputs,
                    validation_errors=test_result.errors,
                    attempt_number=1,
                    max_retries=3,
                    execution_history=[]
                )

                # 获取修复决策
                decision, fix_instruction = self.feedback_engine.handle_validation_failure(fix_context)

                if decision == RetryDecision.RETRY_SAME_AGENT:
                    # 同Agent修复
                    implementation_result = self._execute_layer_with_feedback(
                        "implementation",
                        [fix_instruction.target_agent],
                        fix_instruction.fix_prompt,
                        session_id
                    )

                    # 重新测试
                    test_result = self._execute_layer_with_feedback(
                        "testing",
                        self._get_layer_agents("testing", selected_agents),
                        implementation_result.outputs,
                        session_id
                    )

            # 🔥 Git检查点2: pre-push
            git_check_passed = self._run_git_checkpoint(
                "after_testing",
                test_result,
                session_id
            )

            if not git_check_passed:
                logger.error("Git pre-push检查失败，测试未通过或安全问题")
                self.execution_stats["git_checks_failed"] += 1
                # 这里应该阻止继续，而不是直接提交

            layer_results.append(test_result)

            # Layer 5: 交付（只有测试通过才能到这里）
            if test_result.success and git_check_passed:
                delivery_result = self._execute_layer_with_feedback(
                    "delivery",
                    self._get_layer_agents("delivery", selected_agents),
                    test_result.outputs,
                    session_id
                )
                layer_results.append(delivery_result)

                # 🔥 Git检查点3: post-merge
                self._run_git_checkpoint(
                    "before_deployment",
                    delivery_result,
                    session_id
                )

                self.execution_stats["successful_workflows"] += 1
            else:
                logger.error("工作流未通过验证，不能继续交付")
                self.execution_stats["failed_workflows"] += 1

            # 4. 生成最终结果
            execution_time = time.time() - start_time

            return {
                "success": test_result.success and git_check_passed,
                "workflow_id": workflow_id,
                "execution_time": execution_time,
                "layer_results": [self._serialize_layer_result(r) for r in layer_results],
                "total_retries": sum(r.retry_count for r in layer_results),
                "feedback_loops_triggered": self.execution_stats["feedback_loops_triggered"],
                "message": "工作流完成且通过所有验证" if test_result.success else "工作流失败或未通过验证"
            }

        except Exception as e:
            logger.error(f"工作流执行失败: {e}")
            self.execution_stats["failed_workflows"] += 1
            return {
                "success": False,
                "workflow_id": workflow_id,
                "execution_time": time.time() - start_time,
                "error": str(e)
            }

    def _execute_layer_with_feedback(self, layer_name: str,
                                    agents: List[str],
                                    input_data: Any,
                                    session_id: str,
                                    max_retries: int = 3) -> LayerResult:
        """
        执行层，带反馈循环

        Args:
            layer_name: 层名称
            agents: Agent列表
            input_data: 输入数据
            session_id: 会话ID
            max_retries: 最大重试次数

        Returns:
            LayerResult
        """
        retry_count = 0
        errors = []
        outputs = {}

        for attempt in range(max_retries):
            try:
                # 执行Agent
                outputs = self._execute_agents(agents, input_data)

                # 验证结果
                validation_errors = self._validate_layer_output(layer_name, outputs)

                if not validation_errors:
                    # 验证通过
                    return LayerResult(
                        layer_name=layer_name,
                        agents=agents,
                        success=True,
                        outputs=outputs,
                        errors=[],
                        artifacts=self._save_artifacts(session_id, layer_name, outputs),
                        retry_count=retry_count,
                        git_check_passed=True
                    )

                # 验证失败，准备重试
                errors = validation_errors
                retry_count += 1
                self.execution_stats["total_retries"] += 1

                if attempt < max_retries - 1:
                    logger.warning(f"层 {layer_name} 验证失败，尝试 {retry_count}/{max_retries}")
                    # 修改输入以包含错误信息
                    input_data = self._enhance_input_with_errors(input_data, errors)

            except Exception as e:
                logger.error(f"层 {layer_name} 执行失败: {e}")
                errors.append(str(e))
                retry_count += 1

        # 超过最大重试次数
        return LayerResult(
            layer_name=layer_name,
            agents=agents,
            success=False,
            outputs=outputs,
            errors=errors,
            artifacts=[],
            retry_count=retry_count,
            git_check_passed=False
        )

    def _fix_with_feedback(self, layer_result: LayerResult,
                          errors: List[str],
                          session_id: str) -> LayerResult:
        """使用反馈循环修复层结果"""

        fix_context = FeedbackContext(
            layer_name=layer_result.layer_name,
            agent_name=layer_result.agents[0] if layer_result.agents else "unknown",
            original_input=None,
            execution_result=layer_result.outputs,
            validation_errors=errors,
            attempt_number=layer_result.retry_count + 1,
            max_retries=3,
            execution_history=[]
        )

        decision, fix_instruction = self.feedback_engine.handle_validation_failure(fix_context)

        if decision in [RetryDecision.RETRY_SAME_AGENT, RetryDecision.ESCALATE_EXPERT]:
            # 重新执行
            return self._execute_layer_with_feedback(
                layer_result.layer_name,
                [fix_instruction.target_agent],
                fix_instruction.fix_prompt,
                session_id,
                max_retries=1  # 修复只尝试一次
            )

        return layer_result

    def _run_git_checkpoint(self, checkpoint_name: str,
                          layer_result: LayerResult,
                          session_id: str) -> bool:
        """运行Git检查点"""

        # 获取文件列表（模拟）
        files = self._get_layer_files(layer_result)

        passed, hook_results = self.git_checkpoints.run_checkpoint(
            checkpoint_name,
            files,
            {"layer_result": layer_result}
        )

        if not passed:
            logger.warning(f"Git检查点 {checkpoint_name} 失败")
            for result in hook_results:
                if not result.success:
                    logger.error(f"  {result.hook_type.value}: {', '.join(result.errors)}")

        return passed

    def _generate_agent_instructions(self, agents: List[str], input_data: Any) -> Dict[str, Any]:
        """生成Agent执行指导

        为Claude Code生成应该如何调用这些Agent的指导
        """
        instructions = {}
        for agent in agents:
            instructions[agent] = {
                "suggested_prompt": f"请作为{agent}处理: {str(input_data)[:100] if input_data else ''}",
                "execution_mode": "parallel",
                "quality_requirements": self._get_agent_quality_requirements(agent)
            }
        return instructions

    def _validate_layer_output(self, layer_name: str, outputs: Dict[str, Any]) -> List[str]:
        """验证层输出"""
        errors = []

        # 基于层的不同验证规则
        if layer_name == "implementation":
            # 检查是否有实际代码
            if not any("code" in str(v) or "实现" in str(v) for v in outputs.values()):
                errors.append("实现层未生成实际代码")

        elif layer_name == "testing":
            # 检查测试是否通过
            if any("failed" in str(v).lower() for v in outputs.values()):
                errors.append("测试未通过")

        return errors

    def _save_artifacts(self, session_id: str, layer_name: str,
                       outputs: Dict[str, Any]) -> List[str]:
        """保存Artifacts（模拟）"""
        artifacts = []
        for agent, output in outputs.items():
            artifact_id = f"{session_id}_{layer_name}_{agent}"
            artifacts.append(artifact_id)
        return artifacts

    def _get_layer_agents(self, layer_name: str, all_agents: List[str]) -> List[str]:
        """根据层获取相应的Agent"""
        layer_mapping = {
            "analysis": ["requirements-analyst", "product-strategist"],
            "design": ["backend-architect", "api-designer"],
            "implementation": ["python-pro", "frontend-specialist"],
            "testing": ["test-engineer", "security-auditor"],
            "delivery": ["devops-engineer", "technical-writer"]
        }

        # 从所有Agent中筛选该层的Agent
        layer_agents = []
        for agent in all_agents:
            for layer_agent in layer_mapping.get(layer_name, []):
                if layer_agent in agent:
                    layer_agents.append(agent)
                    break

        # 如果没有匹配的，返回第一个Agent
        if not layer_agents and all_agents:
            layer_agents = [all_agents[0]]

        return layer_agents

    def _get_layer_files(self, layer_result: LayerResult) -> List[str]:
        """获取层产生的文件（模拟）"""
        files = []
        if layer_result.layer_name == "implementation":
            files = ["src/implementation.py", "tests/test_implementation.py"]
        elif layer_result.layer_name == "testing":
            files = ["tests/test_results.py"]
        return files

    def _enhance_input_with_errors(self, input_data: Any,
                                  errors: List[str]) -> Any:
        """增强输入，包含错误信息"""
        if isinstance(input_data, str):
            return f"{input_data}\n\n请修复以下问题:\n" + "\n".join(errors)
        elif isinstance(input_data, dict):
            input_data["errors_to_fix"] = errors
            return input_data
        else:
            return {"original": input_data, "errors": errors}

    def _serialize_layer_result(self, result: LayerResult) -> Dict:
        """序列化层结果"""
        return {
            "layer": result.layer_name,
            "agents": result.agents,
            "success": result.success,
            "retry_count": result.retry_count,
            "git_check_passed": result.git_check_passed,
            "errors": result.errors
        }

    def get_statistics(self) -> Dict[str, Any]:
        """获取执行统计"""
        stats = self.execution_stats.copy()

        # 计算成功率
        total = stats["total_workflows"]
        if total > 0:
            stats["success_rate"] = stats["successful_workflows"] / total
            stats["average_retries"] = stats["total_retries"] / total
            stats["feedback_loop_rate"] = stats["feedback_loops_triggered"] / total
        else:
            stats["success_rate"] = 0
            stats["average_retries"] = 0
            stats["feedback_loop_rate"] = 0

        # 添加子系统统计
        stats["feedback_engine_stats"] = self.feedback_engine.get_retry_statistics()
        stats["git_checkpoint_stats"] = self.git_checkpoints.get_checkpoint_statistics()

        return stats


def demonstrate_improved_orchestrator():
    """演示改进的Orchestrator"""
    print("=" * 80)
    print("Perfect21 改进Orchestrator演示")
    print("=" * 80)

    orchestrator = ImprovedOrchestrator()

    # 测试任务
    task = "实现用户登录功能，包括密码验证和JWT生成"

    print(f"\n执行任务: {task}")
    print("-" * 40)

    result = orchestrator.execute_workflow_with_feedback(task)

    print(f"\n执行结果:")
    print(f"  成功: {result['success']}")
    print(f"  工作流ID: {result['workflow_id']}")
    print(f"  执行时间: {result['execution_time']:.2f}秒")
    print(f"  总重试次数: {result.get('total_retries', 0)}")
    print(f"  触发反馈循环: {result.get('feedback_loops_triggered', 0)}次")
    print(f"  消息: {result['message']}")

    if 'layer_results' in result:
        print("\n各层执行情况:")
        for layer in result['layer_results']:
            status = "✅" if layer['success'] else "❌"
            print(f"  {layer['layer']}: {status} (重试{layer['retry_count']}次)")

    # 显示统计
    print("\n执行统计:")
    stats = orchestrator.get_statistics()
    print(f"  总工作流: {stats['total_workflows']}")
    print(f"  成功率: {stats['success_rate']:.1%}")
    print(f"  平均重试: {stats['average_retries']:.1f}次")
    print(f"  反馈循环率: {stats['feedback_loop_rate']:.1%}")

    print("\n" + "=" * 80)
    print("演示完成！改进的Orchestrator解决了测试失败直接提交的问题。")
    print("=" * 80)


if __name__ == "__main__":
    demonstrate_improved_orchestrator()