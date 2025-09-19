#!/usr/bin/env python3
"""
反馈循环集成层
==============

集成反馈循环系统到Perfect21的主要接口中，包括：
1. CLI集成
2. API集成
3. 与现有orchestrator的集成
4. 自动重试和修复流程
"""

import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pathlib import Path

from .enhanced_orchestrator import get_enhanced_orchestrator, EnhancedOrchestrator
from .feedback_loop_engine import get_feedback_engine, FeedbackLoopEngine, FeedbackAction
from .orchestrator import get_orchestrator_integration

logger = logging.getLogger("FeedbackIntegration")


class FeedbackIntegration:
    """反馈循环集成管理器"""

    def __init__(self, project_root: str = "/home/xx/dev/Perfect21"):
        self.project_root = project_root
        self.enhanced_orchestrator = get_enhanced_orchestrator(project_root)
        self.feedback_engine = get_feedback_engine(project_root)
        self.legacy_orchestrator = get_orchestrator_integration()

    def execute_enhanced_workflow(self, task_description: str,
                                 agent_assignments: Optional[List[Dict[str, str]]] = None,
                                 workflow_type: str = "full") -> Dict[str, Any]:
        """
        执行增强的工作流，包含完整的反馈循环支持

        Args:
            task_description: 任务描述
            agent_assignments: Agent分配列表
            workflow_type: 工作流类型 ("full", "implementation_only", "testing_only")

        Returns:
            包含完整反馈循环信息的执行结果
        """

        logger.info(f"开始执行增强工作流: {task_description[:50]}...")

        # 如果没有提供agent分配，使用智能分析
        if not agent_assignments:
            agent_assignments = self._analyze_and_assign_agents(task_description)

        # 构建工作流请求
        workflow_request = {
            "task_description": task_description,
            "agent_assignments": agent_assignments,
            "type": workflow_type,
            "enable_feedback_loops": True,
            "timestamp": datetime.now().isoformat()
        }

        try:
            # 执行增强工作流
            result = self.enhanced_orchestrator.execute_enhanced_workflow(workflow_request)

            # 添加集成信息
            result["integration_info"] = {
                "feedback_loops_enabled": True,
                "retry_support": True,
                "auto_escalation": True,
                "quality_gates_integrated": True
            }

            # 如果需要重试，生成便于用户的指令
            if result.get("requires_manual_intervention"):
                result["user_instructions"] = self._generate_user_instructions(result)

            return result

        except Exception as e:
            logger.error(f"增强工作流执行失败: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "integration_info": {
                    "feedback_loops_enabled": True,
                    "error_handled": True
                }
            }

    def execute_with_auto_retry(self, task_description: str,
                               agent_assignments: Optional[List[Dict[str, str]]] = None,
                               max_auto_retries: int = 2) -> Dict[str, Any]:
        """
        执行带自动重试的工作流

        当遇到可自动修复的问题时，自动执行重试循环
        """

        logger.info(f"开始执行自动重试工作流: {task_description[:50]}...")

        retry_count = 0
        workflow_history = []

        while retry_count <= max_auto_retries:
            # 执行工作流
            result = self.execute_enhanced_workflow(
                task_description, agent_assignments, "full"
            )

            workflow_history.append({
                "attempt": retry_count + 1,
                "result": result,
                "timestamp": datetime.now().isoformat()
            })

            # 如果成功，返回结果
            if result.get("status") == "completed":
                return {
                    "final_status": "completed",
                    "result": result,
                    "auto_retry_history": workflow_history,
                    "total_attempts": retry_count + 1
                }

            # 检查是否可以自动重试
            if not self._can_auto_retry(result):
                break

            # 执行自动重试
            retry_instructions = result.get("retry_instructions", [])
            if retry_instructions:
                logger.info(f"执行自动重试 (第{retry_count + 1}次)")

                # 这里需要实际执行重试指令
                # 目前返回重试信息，实际使用时需要真正执行
                retry_result = self._execute_auto_retry_instructions(retry_instructions)

                if not retry_result.get("success"):
                    break

            retry_count += 1

        # 如果达到最大重试次数或无法自动重试
        return {
            "final_status": "requires_manual_intervention",
            "last_result": workflow_history[-1]["result"] if workflow_history else None,
            "auto_retry_history": workflow_history,
            "total_attempts": retry_count,
            "manual_instructions": self._generate_manual_intervention_guide(workflow_history)
        }

    def handle_validation_failure(self, workflow_id: str, stage: str,
                                 validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理验证失败的反馈

        这是外部系统（如测试框架、质量门）调用的接口
        """

        logger.info(f"处理验证失败: {workflow_id} - {stage}")

        try:
            # 获取工作流状态
            workflow_status = self.enhanced_orchestrator.get_workflow_status(workflow_id)
            if not workflow_status:
                return {
                    "success": False,
                    "error": f"工作流 {workflow_id} 不存在"
                }

            # 查找对应的反馈循环
            feedback_loops = workflow_status.get("feedback_loops", {}).get("active_loops", {})

            relevant_loops = [
                loop_id for loop_id, loop_info in feedback_loops.items()
                if loop_info.get("stage") == stage
            ]

            if not relevant_loops:
                return {
                    "success": False,
                    "error": f"未找到阶段 {stage} 的活跃反馈循环"
                }

            # 处理每个相关的反馈循环
            decisions = []
            for loop_id in relevant_loops:
                decision = self.feedback_engine.process_validation_failure(
                    feedback_id=loop_id,
                    validation_result=validation_result,
                    failure_reason=validation_result.get("error", "验证失败")
                )
                decisions.append(decision)

            # 生成响应指令
            response_instructions = []
            for decision in decisions:
                if decision.action == FeedbackAction.RETRY:
                    instruction = self.feedback_engine.get_retry_instruction(decision)
                    response_instructions.append(instruction)
                elif decision.action == FeedbackAction.ESCALATE:
                    instruction = self.feedback_engine.get_escalation_instruction(decision)
                    response_instructions.append(instruction)

            return {
                "success": True,
                "decisions": [
                    {
                        "action": decision.action.value,
                        "target_agent": decision.target_agent,
                        "reasoning": decision.reasoning,
                        "confidence": decision.confidence
                    }
                    for decision in decisions
                ],
                "instructions": response_instructions,
                "requires_execution": len(response_instructions) > 0
            }

        except Exception as e:
            logger.error(f"处理验证失败时出错: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_feedback_status(self, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """获取反馈循环状态"""

        if workflow_id:
            return self.feedback_engine.get_workflow_feedback_status(workflow_id)
        else:
            # 返回全局状态
            return {
                "active_workflows": len(self.enhanced_orchestrator.active_workflows),
                "feedback_engine_status": "running",
                "recent_activity": "获取最近活动需要实现"
            }

    def cleanup_completed_workflows(self, max_age_hours: int = 24) -> Dict[str, Any]:
        """清理已完成的工作流"""

        # 清理过期的反馈循环
        cleaned_loops = self.feedback_engine.cleanup_expired_loops(max_age_hours)

        # 清理已完成的工作流（需要在enhanced_orchestrator中实现）
        # cleaned_workflows = self.enhanced_orchestrator.cleanup_completed_workflows(max_age_hours)

        return {
            "cleaned_feedback_loops": cleaned_loops,
            "cleaned_workflows": 0,  # 待实现
            "cleanup_time": datetime.now().isoformat()
        }

    def _analyze_and_assign_agents(self, task_description: str) -> List[Dict[str, str]]:
        """智能分析任务并分配agents"""

        # 使用legacy orchestrator的分析功能
        analysis = self.legacy_orchestrator.analyze_task_for_agents(task_description)

        # 转换为增强工作流格式
        agent_assignments = []

        recommended_agents = analysis.get("recommended_agents", [])
        execution_mode = analysis.get("execution_mode", "parallel")

        # 根据任务类型添加不同阶段的agents
        # 实现阶段
        implementation_agents = [
            agent for agent in recommended_agents
            if agent in ["backend-architect", "frontend-specialist", "fullstack-engineer", "python-pro"]
        ]

        if not implementation_agents:
            implementation_agents = ["backend-architect"]

        for agent in implementation_agents:
            agent_assignments.append({
                "agent": agent,
                "stage": "implementation",
                "task": f"实现核心功能 - {agent}专业领域",
                "prompt": f"{task_description}\n\n请专注于{agent}的专业领域进行实现。"
            })

        # 测试阶段
        test_agents = [
            agent for agent in recommended_agents
            if agent in ["test-engineer", "e2e-test-specialist", "performance-tester"]
        ]

        if not test_agents:
            test_agents = ["test-engineer"]

        for agent in test_agents:
            agent_assignments.append({
                "agent": agent,
                "stage": "testing",
                "task": f"编写和执行测试 - {agent}专业领域",
                "prompt": f"为以下功能编写测试:\n{task_description}\n\n请专注于{agent}的专业测试领域。"
            })

        return agent_assignments

    def _can_auto_retry(self, workflow_result: Dict[str, Any]) -> bool:
        """判断是否可以自动重试"""

        # 检查是否有可自动执行的重试指令
        retry_instructions = workflow_result.get("retry_instructions", [])

        # 简化判断：如果有重试指令且失败原因不是严重错误
        if not retry_instructions:
            return False

        # 检查失败原因是否允许自动重试
        failed_stages = workflow_result.get("failed_stages", [])

        # 某些失败类型不适合自动重试
        non_retryable_errors = [
            "security_vulnerability",
            "data_corruption",
            "permission_denied",
            "resource_exhausted"
        ]

        # 检查错误信息
        for stage in failed_stages:
            stage_info = workflow_result.get("stages", {}).get(stage, {})
            validation_result = stage_info.get("validation_result", {})

            for error_type in non_retryable_errors:
                if error_type in str(validation_result).lower():
                    return False

        return True

    def _execute_auto_retry_instructions(self, retry_instructions: List[str]) -> Dict[str, Any]:
        """执行自动重试指令"""

        logger.info(f"执行 {len(retry_instructions)} 个重试指令")

        # 这里是自动重试的核心逻辑
        # 实际实现需要解析指令并真正执行Task调用

        executed_instructions = []
        for instruction in retry_instructions:
            try:
                # 解析指令中的agent和prompt
                agent_info = self._parse_retry_instruction(instruction)

                if agent_info:
                    # 这里应该调用真正的Task执行
                    # 目前只是记录，实际使用时需要真正执行
                    executed_instructions.append({
                        "agent": agent_info["agent"],
                        "status": "simulated_success",  # 实际应该是真实执行结果
                        "instruction": instruction
                    })
                else:
                    executed_instructions.append({
                        "status": "parse_failed",
                        "instruction": instruction
                    })

            except Exception as e:
                executed_instructions.append({
                    "status": "execution_failed",
                    "error": str(e),
                    "instruction": instruction
                })

        # 判断总体执行结果
        success_count = len([r for r in executed_instructions if r.get("status") == "simulated_success"])
        success_rate = success_count / len(executed_instructions) if executed_instructions else 0

        return {
            "success": success_rate > 0.5,  # 超过一半成功就认为可以继续
            "executed_count": len(executed_instructions),
            "success_count": success_count,
            "success_rate": success_rate,
            "details": executed_instructions
        }

    def _parse_retry_instruction(self, instruction: str) -> Optional[Dict[str, str]]:
        """解析重试指令"""

        try:
            # 简化的指令解析
            # 实际应该解析XML格式的function_calls

            if "subagent_type" in instruction and "prompt" in instruction:
                # 提取agent名称
                agent_start = instruction.find('subagent_type">') + len('subagent_type">')
                agent_end = instruction.find('<', agent_start)
                agent = instruction[agent_start:agent_end].strip()

                # 提取prompt
                prompt_start = instruction.find('prompt">') + len('prompt">')
                prompt_end = instruction.find('</parameter>', prompt_start)
                prompt = instruction[prompt_start:prompt_end].strip()

                return {
                    "agent": agent,
                    "prompt": prompt
                }

        except Exception as e:
            logger.warning(f"解析重试指令失败: {e}")

        return None

    def _generate_user_instructions(self, workflow_result: Dict[str, Any]) -> Dict[str, Any]:
        """生成用户友好的操作指令"""

        retry_instructions = workflow_result.get("retry_instructions", [])
        failed_stages = workflow_result.get("failed_stages", [])

        user_instructions = {
            "summary": f"工作流部分失败，需要手动执行 {len(retry_instructions)} 个修复指令",
            "failed_stages": failed_stages,
            "action_required": "manual_execution",
            "steps": []
        }

        for i, instruction in enumerate(retry_instructions, 1):
            # 解析指令获取关键信息
            agent_info = self._parse_retry_instruction(instruction)

            step = {
                "step": i,
                "description": f"执行修复指令 #{i}",
                "instruction": instruction
            }

            if agent_info:
                step["agent"] = agent_info["agent"]
                step["summary"] = f"使用 {agent_info['agent']} 进行修复"

            user_instructions["steps"].append(step)

        # 添加执行后的验证要求
        user_instructions["post_execution"] = {
            "verification_required": True,
            "message": "执行完所有修复指令后，请重新运行工作流验证修复效果"
        }

        return user_instructions

    def _generate_manual_intervention_guide(self, workflow_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成手动干预指南"""

        if not workflow_history:
            return {"message": "无历史记录"}

        last_attempt = workflow_history[-1]
        total_attempts = len(workflow_history)

        guide = {
            "situation": f"自动重试 {total_attempts} 次后仍未成功",
            "last_failure": last_attempt.get("result", {}).get("failed_stages", []),
            "recommendations": [],
            "escalation_options": []
        }

        # 分析失败模式
        all_failures = []
        for attempt in workflow_history:
            failed_stages = attempt.get("result", {}).get("failed_stages", [])
            all_failures.extend(failed_stages)

        # 统计最常见的失败
        failure_counts = {}
        for failure in all_failures:
            failure_counts[failure] = failure_counts.get(failure, 0) + 1

        most_common_failure = max(failure_counts.items(), key=lambda x: x[1]) if failure_counts else None

        if most_common_failure:
            stage, count = most_common_failure
            if count > 1:
                guide["recommendations"].append(f"重点关注 {stage} 阶段，该阶段在 {count}/{total_attempts} 次尝试中失败")

        # 提供升级建议
        guide["escalation_options"] = [
            "人工审查代码质量和架构设计",
            "调整任务需求或简化实现方案",
            "寻求高级专家的技术支持",
            "分解任务为更小的可管理单元"
        ]

        return guide

    def create_cli_command_handler(self) -> Dict[str, callable]:
        """创建CLI命令处理器"""

        return {
            "execute-enhanced": self._cli_execute_enhanced,
            "execute-auto-retry": self._cli_execute_auto_retry,
            "feedback-status": self._cli_feedback_status,
            "cleanup": self._cli_cleanup
        }

    def _cli_execute_enhanced(self, args) -> Dict[str, Any]:
        """CLI: 执行增强工作流"""

        task_description = args.get("task", "")
        workflow_type = args.get("type", "full")

        if not task_description:
            return {"error": "需要提供任务描述"}

        return self.execute_enhanced_workflow(task_description, None, workflow_type)

    def _cli_execute_auto_retry(self, args) -> Dict[str, Any]:
        """CLI: 执行自动重试工作流"""

        task_description = args.get("task", "")
        max_retries = int(args.get("max_retries", 2))

        if not task_description:
            return {"error": "需要提供任务描述"}

        return self.execute_with_auto_retry(task_description, None, max_retries)

    def _cli_feedback_status(self, args) -> Dict[str, Any]:
        """CLI: 获取反馈状态"""

        workflow_id = args.get("workflow_id")
        return self.get_feedback_status(workflow_id)

    def _cli_cleanup(self, args) -> Dict[str, Any]:
        """CLI: 清理工作流"""

        max_age = int(args.get("max_age_hours", 24))
        return self.cleanup_completed_workflows(max_age)


# 全局实例
_feedback_integration = None

def get_feedback_integration(project_root: str = "/home/xx/dev/Perfect21") -> FeedbackIntegration:
    """获取全局反馈集成实例"""
    global _feedback_integration
    if _feedback_integration is None:
        _feedback_integration = FeedbackIntegration(project_root)
    return _feedback_integration