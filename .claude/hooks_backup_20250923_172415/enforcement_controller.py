#!/usr/bin/env python3
"""
Claude Enhancer强制执行控制器
确保遵循8-Phase工作流和4-6-8 Agent策略
"""

import json
import sys
import os
import re

# 添加核心模块路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.engine import WorkflowEngine, Phase, TaskType
from core.orchestrator import AgentOrchestrator


class EnforcementController:
    """强制执行控制器"""

    def __init__(self):
        self.engine = WorkflowEngine()
        self.orchestrator = AgentOrchestrator()
        self.blocked_count = 0
        self.max_retries = 3

    def check_task_execution(self, input_data: str) -> dict:
        """检查任务执行是否合规"""
        try:
            # 解析输入
            data = json.loads(input_data) if isinstance(input_data, str) else input_data

            # 提取任务信息
            task_description = self._extract_task_description(data)
            agents = self._extract_agents(data)

            # 检查结果
            violations = []

            # 1. 检查Phase顺序
            phase_check = self._check_phase_sequence(task_description)
            if not phase_check["valid"]:
                violations.append(f"Phase违规: {phase_check['error']}")

            # 2. 检查Agent数量
            agent_check = self.orchestrator.validate_agent_count(agents)
            if not agent_check["valid"]:
                violations.append(f"Agent违规: {agent_check['error']}")

            # 3. 检查并行执行
            parallel_check = self._check_parallel_execution(data)
            if not parallel_check:
                violations.append("执行方式违规: 必须并行执行所有Agent")

            # 生成结果
            if violations:
                return self._generate_block_response(violations, task_description)
            else:
                return self._generate_allow_response(agents)

        except Exception as e:
            return {"action": "allow", "warning": f"检查时出错: {str(e)}"}

    def _extract_task_description(self, data: dict) -> str:
        """提取任务描述"""
        # 尝试多个可能的字段
        for field in ["prompt", "description", "task", "message"]:
            if field in data:
                return str(data[field])
        return ""

    def _extract_agents(self, data: dict) -> list:
        """提取Agent列表"""
        agents = []

        # 如果是Task工具调用
        if "subagent_type" in data:
            agents.append(data["subagent_type"])

        # 如果是批量调用
        if "agents" in data:
            agents.extend(data["agents"])

        # 检查function_calls
        if "function_calls" in data:
            for call in data["function_calls"]:
                if call.get("name") == "Task":
                    params = call.get("parameters", {})
                    if "subagent_type" in params:
                        agents.append(params["subagent_type"])

        return agents

    def _check_phase_sequence(self, task_description: str) -> dict:
        """检查Phase顺序是否正确"""
        # 检测任务类型
        task_type = self.engine.detect_task_type(task_description)
        self.engine.task_type = task_type

        # 获取当前Phase状态
        status = self.engine.get_status()

        # 检查是否按顺序执行
        next_phases = status.get("next_phases", [])
        if next_phases and next_phases[0] != "Set task type first":
            current_phase_value = status.get("phase_value", 0)

            # 如果当前在Phase 3（实现），需要多个Agent
            if current_phase_value == 3:
                return {
                    "valid": True,
                    "phase": "PHASE_3_IMPLEMENT",
                    "requires_agents": True,
                }

        return {"valid": True}  # 暂时不强制Phase顺序

    def _check_parallel_execution(self, data: dict) -> bool:
        """检查是否并行执行"""
        # 简单检查：是否在同一批次调用
        if "function_calls" in data:
            task_count = 0
            for call in data["function_calls"]:
                if call.get("name") == "Task":
                    task_count += 1
            return task_count >= self.orchestrator.min_agents

        return True  # 默认通过

    def _generate_block_response(self, violations: list, task_description: str) -> dict:
        """生成阻止响应"""
        self.blocked_count += 1

        # 获取正确的执行建议
        suggestion = self.orchestrator.select_agents(task_description)

        response = {
            "action": "block",
            "violations": violations,
            "blocked_count": self.blocked_count,
            "max_retries": self.max_retries,
            "suggestion": {
                "message": "请按以下方式重新执行:",
                "required_agents": suggestion["selected_agents"],
                "agent_count": suggestion["agent_count"],
                "complexity": suggestion["complexity"],
                "execution_mode": "parallel",
                "example": self._generate_example_code(
                    suggestion["selected_agents"], task_description
                ),
            },
        }

        # 如果超过最大重试次数，强制通过但警告
        if self.blocked_count >= self.max_retries:
            response["action"] = "allow"
            response["warning"] = "已达到最大重试次数，强制通过但记录违规"

        return response

    def _generate_allow_response(self, agents: list) -> dict:
        """生成允许响应"""
        return {
            "action": "allow",
            "message": f"✅ 执行合规: {len(agents)}个Agent并行执行",
            "agents": agents,
        }

    def _generate_example_code(self, agents: list, task: str) -> str:
        """生成示例代码"""
        code = "<function_calls>\n"
        for agent in agents:
            code += f'  <invoke name="Task">\n'
            code += f'    <parameter name="subagent_type">{agent}</parameter>\n'
            code += f'    <parameter name="prompt">{task[:50]}...</parameter>\n'
            code += f"  </invoke>\n"
        code += "</function_calls>"
        return code


def main():
    """主函数"""
    controller = EnforcementController()

    # 从stdin读取输入
    input_data = sys.stdin.read()

    # 检查执行
    result = controller.check_task_execution(input_data)

    # 输出结果
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # 如果被阻止，返回非0退出码
    if result["action"] == "block":
        sys.exit(1)


if __name__ == "__main__":
    main()
