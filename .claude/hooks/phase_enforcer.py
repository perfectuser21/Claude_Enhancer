#!/usr/bin/env python3
"""
Phase Enforcer - 强制Claude Code按5阶段执行
通过Hook拦截和重定向来确保正确的执行流程
"""

import json
import sys
from typing import Dict, List, Optional, Tuple

from phase_manager import ExecutionPhase, get_phase_manager


class PhaseEnforcer:
    """阶段执行强制器"""

    def __init__(self):
        self.manager = get_phase_manager()
        self.intercepted = False

    def intercept_tool_use(self, tool_name: str, params: dict) -> Optional[dict]:
        """拦截工具使用并强制进入阶段执行"""

        # 避免重复拦截
        if self.intercepted:
            return None

        # 检测是否应该开始5阶段
        if self.manager.should_start_phases(tool_name, params):
            self.intercepted = True
            return self.force_phase_execution(params.get("prompt", ""))

        # 如果已在阶段中，验证执行
        if self.manager.current_phase:
            return self.validate_current_execution(tool_name, params)

        return None

    def force_phase_execution(self, user_request: str) -> dict:
        """强制进入5阶段执行"""
        # 开始第一阶段
        self.manager.current_phase = ExecutionPhase.ANALYSIS

        # 生成执行指令
        instructions = self.manager.generate_phase_instructions(
            ExecutionPhase.ANALYSIS, {"user_request": user_request}
        )

        # 生成XML格式的agent调用
        xml_calls = self.generate_agent_calls_xml(instructions)

        return {
            "action": "redirect",
            "message": f"""
🎯 **Claude Enhancer 5阶段执行模式已启动**

📋 **任务**: {user_request}
📊 **当前阶段**: {instructions['phase_name']} (1/5)
👥 **需要并行执行 {len(instructions['agents_to_call'])} 个Agents**

请执行以下agent调用（必须在一个消息中）：

```xml
{xml_calls}
```

⚠️ **重要**: 所有agents必须在同一个function_calls块中并行执行！
""",
            "phase": instructions["phase"],
            "agents_required": [a["agent"] for a in instructions["agents_to_call"]],
        }

    def validate_current_execution(
        self, tool_name: str, params: dict
    ) -> Optional[dict]:
        """验证当前执行是否符合阶段要求"""
        if tool_name != "Task":
            return None

        agent_type = params.get("subagent_type", "")

        # 收集本次执行的agents
        if not hasattr(self, "current_execution_agents"):
            self.current_execution_agents = []

        self.current_execution_agents.append(agent_type)

        # 验证是否满足阶段要求
        config = self.manager.get_current_phase_config()
        if len(self.current_execution_agents) >= config["min_agents"]:
            is_valid, errors = self.manager.validate_agent_execution(
                self.current_execution_agents
            )

            if not is_valid:
                return {
                    "action": "warn",
                    "message": f"⚠️ 阶段执行不符合要求:\n" + "\n".join(errors),
                }

        return None

    def generate_agent_calls_xml(self, instructions: dict) -> str:
        """生成XML格式的agent调用代码"""
        xml = "<function_calls>\n"

        for agent_info in instructions["agents_to_call"]:
            xml += f"""  <invoke name="Task">
    <parameter name="subagent_type">{agent_info['agent']}</parameter>
    <parameter name="prompt">{agent_info['prompt']}</parameter>
  </invoke>
"""

        xml += "</function_calls>"
        return xml

    def handle_phase_completion(self, results: dict) -> Optional[dict]:
        """处理阶段完成"""
        if not self.manager.current_phase:
            return None

        # 保存阶段结果
        self.manager.save_phase_results(self.manager.current_phase, results)

        # 进入下一阶段
        next_phase = self.manager.advance_to_next_phase()

        if next_phase:
            # 获取上下文
            context = self.manager.get_context_for_phase(next_phase)

            # 生成下阶段指令
            instructions = self.manager.generate_phase_instructions(next_phase, context)
            xml_calls = self.generate_agent_calls_xml(instructions)

            # 重置执行跟踪
            self.current_execution_agents = []

            return {
                "action": "continue",
                "message": f"""
✅ **{self.manager.phase_config[self.manager.current_phase]['name']}阶段完成**

📊 **下一阶段**: {instructions['phase_name']} ({self.get_phase_number(next_phase)}/5)
👥 **需要并行执行 {len(instructions['agents_to_call'])} 个Agents**

请执行以下agent调用：

```xml
{xml_calls}
```
""",
                "phase": instructions["phase"],
                "agents_required": [a["agent"] for a in instructions["agents_to_call"]],
            }
        else:
            # 所有阶段完成
            summary = self.manager.generate_phase_summary()
            self.manager.reset_phases()
            self.intercepted = False

            return {
                "action": "complete",
                "message": f"""
🎉 **所有5个阶段已完成！**

{summary}

✨ 任务执行成功！
""",
            }

    def get_phase_number(self, phase: ExecutionPhase) -> int:
        """获取阶段编号"""
        phase_order = [
            ExecutionPhase.ANALYSIS,
            ExecutionPhase.DESIGN,
            ExecutionPhase.IMPLEMENTATION,
            ExecutionPhase.TESTING,
            ExecutionPhase.DEPLOYMENT,
        ]
        return phase_order.index(phase) + 1

    def check_parallel_execution(self, execution_log: str) -> Tuple[bool, str]:
        """检查是否真正并行执行"""
        # 检查是否所有agents在同一个function_calls块
        import re

        # 统计function_calls块数量
        function_calls_count = execution_log.count("<function_calls>")

        # 统计Task调用数量
        task_invokes = re.findall(r'<invoke name="Task">', execution_log)

        if function_calls_count > 1:
            return False, f"发现{function_calls_count}个分离的function_calls块，应该只有1个"

        if function_calls_count == 0:
            return False, "未找到function_calls块"

        if len(task_invokes) < 3:
            return False, f"只找到{len(task_invokes)}个Task调用，最少需要3个"

        # 检查是否在同一块内
        fc_start = execution_log.find("<function_calls>")
        fc_end = execution_log.find("</function_calls>")

        if fc_start != -1 and fc_end != -1:
            block_content = execution_log[fc_start:fc_end]
            block_task_count = block_content.count('<invoke name="Task">')

            if block_task_count != len(task_invokes):
                return (
                    False,
                    f"有{len(task_invokes) - block_task_count}个Task调用在function_calls块外",
                )

        return True, "✅ 所有agents在同一function_calls块中并行执行"


# Hook集成函数
def pre_tool_use_hook(tool_name: str, params: dict) -> Optional[dict]:
    """PreToolUse Hook - 在工具使用前拦截"""
    enforcer = PhaseEnforcer()
    result = enforcer.intercept_tool_use(tool_name, params)

    if result and result.get("action") == "redirect":
        # 输出重定向信息
    # print(result["message"])
        # 返回修改后的参数，强制执行
        return {"modified": True, "instructions": result}

    return None


def post_tool_use_hook(tool_name: str, result: any) -> Optional[dict]:
    """PostToolUse Hook - 在工具使用后处理"""
    if tool_name == "Task":
        enforcer = PhaseEnforcer()

        # 检查是否需要进入下一阶段
        if hasattr(enforcer, "current_execution_agents"):
            config = enforcer.manager.get_current_phase_config()
            if len(enforcer.current_execution_agents) >= config["min_agents"]:
                # 阶段完成，准备下一阶段
                next_phase_info = enforcer.handle_phase_completion(
                    {"agents_executed": enforcer.current_execution_agents}
                )
                if next_phase_info:
    # print(next_phase_info["message"])

    return None


if __name__ == "__main__":
    # 测试阶段强制器
    enforcer = PhaseEnforcer()

    # 模拟任务开始
    # print("测试阶段强制执行...")
    result = enforcer.intercept_tool_use("Task", {"prompt": "实现用户认证系统"})

    if result:
    # print(result["message"])
    # print(f"\n需要的agents: {result.get('agents_required')}")

    # 模拟阶段完成
    # print("\n模拟阶段完成...")
    completion = enforcer.handle_phase_completion({"test": "results"})
    if completion:
    # print(completion["message"])
