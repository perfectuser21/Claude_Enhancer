#!/usr/bin/env python3
"""
Perfect21 执行器 - 自动执行动态工作流
这是Claude Code应该自动调用的核心执行器
"""

import json
import logging
from typing import List, Dict, Any
from datetime import datetime

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from features.auto_activator import perfect21_activator
from features.dynamic_workflow_generator import DynamicWorkflowGenerator
from features.decision_recorder.adr_storage import adr_storage

logger = logging.getLogger("Perfect21Executor")

class Perfect21Executor:
    """Perfect21自动执行器"""

    def __init__(self):
        self.generator = DynamicWorkflowGenerator()
        self.execution_log = []

    def should_use_perfect21(self, user_request: str) -> bool:
        """判断是否应该使用Perfect21"""
        return perfect21_activator.should_activate_perfect21(user_request)

    def execute_request(self, user_request: str) -> Dict[str, Any]:
        """执行用户请求的完整Perfect21工作流"""

        # 1. 检查是否应该激活Perfect21
        if not self.should_use_perfect21(user_request):
            return {
                "mode": "standard",
                "message": "使用标准Claude Code模式"
            }

        # 2. 生成动态工作流
        workflow = self.generator.generate_workflow(user_request)

        # 3. 准备执行计划
        execution_plan = self.create_execution_plan(workflow)

        # 4. 记录架构决策
        self.record_workflow_decision(user_request, workflow)

        return {
            "mode": "perfect21",
            "workflow": workflow,
            "execution_plan": execution_plan,
            "message": self.format_execution_message(workflow)
        }

    def create_execution_plan(self, workflow) -> List[Dict]:
        """创建详细的执行计划"""
        plan = []

        for stage_num, stage in enumerate(workflow.stages, 1):
            stage_plan = {
                "stage": stage_num,
                "name": stage.name,
                "mode": stage.mode.value,
                "agents": [],
                "sync_point": stage.sync_point,
                "quality_gate": stage.quality_gate
            }

            # 并行执行计划
            if stage.mode.value == "parallel":
                stage_plan["execution"] = "PARALLEL - 同时调用所有agents"
                stage_plan["agents"] = [
                    {"agent": agent, "parallel": True}
                    for agent in stage.agents
                ]
            else:
                stage_plan["execution"] = "SEQUENTIAL - 顺序调用agents"
                stage_plan["agents"] = [
                    {"agent": agent, "parallel": False}
                    for agent in stage.agents
                ]

            plan.append(stage_plan)

        return plan

    def format_execution_message(self, workflow) -> str:
        """格式化执行消息 - 强调并行批量执行"""
        msg = f"""
🚀 **Perfect21 动态工作流已生成**

📊 任务分析：
- 复杂度: {workflow.analysis.complexity.value}
- 领域: {workflow.analysis.domain}
- 预估规模: {workflow.analysis.estimated_loc}行代码
- 涉及模块: {workflow.analysis.module_count}个

🤖 选中Agents ({len(workflow.selected_agents)}个):
{chr(10).join(f'  - {agent}' for agent in workflow.selected_agents)}

📋 执行阶段 ({len(workflow.stages)}个):
"""
        for i, stage in enumerate(workflow.stages, 1):
            msg += f"\n**阶段{i}: {stage.name}** [{stage.mode.value.upper()}]\n"

            # 改进：为并行执行生成可复制的批量调用代码
            if stage.mode.value == "parallel" and len(stage.agents) > 1:
                msg += "\n  🔴 **并行批量执行指令**:\n"
                msg += "  ```python\n"
                msg += "  # 必须在一个消息中同时调用所有agents\n"
                for agent in stage.agents:
                    msg += f'  Task("{agent}", "根据需求完成任务")\n'
                msg += "  ```\n"
                msg += "  ⚠️ **不要分开调用！复制上面所有Task到一个function_calls中！**\n\n"
            elif stage.mode.value == "parallel":
                msg += "  🔀 并行执行:\n"
                for agent in stage.agents:
                    msg += f"    └─ @{agent}\n"
            else:
                msg += "  ➡️ 顺序执行:\n"
                for agent in stage.agents:
                    msg += f"    └─ @{agent}\n"

            if stage.sync_point:
                msg += "  🔴 同步点: 必须验证所有结果一致性后才能继续\n"

            if stage.quality_gate:
                msg += f"  ✅ 质量门: {stage.quality_gate}\n"

        msg += f"\n⏱️ 预计时间: {workflow.estimated_time}小时"
        msg += "\n\n💡 **执行提示**: 看到并行批量执行指令时，必须同时调用所有agents！"

        return msg

    def record_workflow_decision(self, request: str, workflow):
        """记录工作流决策"""
        decision = {
            "title": f"工作流决策: {request[:50]}",
            "context": f"用户请求: {request}",
            "decision": f"使用{len(workflow.selected_agents)}个agents的{workflow.execution_mode.value}工作流",
            "consequences": f"预计{workflow.estimated_time}小时完成，{len(workflow.stages)}个阶段",
            "agents_involved": workflow.selected_agents,
            "complexity": workflow.analysis.complexity.value
        }

        decision_id = adr_storage.save_decision(decision)
        logger.info(f"决策已记录: {decision_id}")
        return decision_id

# 全局执行器实例
perfect21_executor = Perfect21Executor()

def auto_execute(user_request: str) -> Dict[str, Any]:
    """
    Claude Code应该调用的自动执行函数

    使用方式：
    1. 接收用户请求
    2. 调用auto_execute(request)
    3. 根据返回的execution_plan执行agents
    """
    return perfect21_executor.execute_request(user_request)

# 执行示例
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # 测试请求
    test_request = "实现用户登录功能，包括JWT认证、密码加密、会话管理"

    result = auto_execute(test_request)

    if result["mode"] == "perfect21":
        print(result["message"])
        print("\n📝 执行计划:")
        for stage in result["execution_plan"]:
            print(f"\n阶段{stage['stage']}: {stage['name']}")
            print(f"  执行模式: {stage['execution']}")
            for agent_info in stage['agents']:
                parallel_mark = "🔀" if agent_info['parallel'] else "➡️"
                print(f"    {parallel_mark} {agent_info['agent']}")