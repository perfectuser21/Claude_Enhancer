#!/usr/bin/env python3
"""
Phase验证器 - 确保正确的multi-agent并行执行模式
"""

import json
import os
from pathlib import Path
from datetime import datetime


class PhaseValidator:
    """验证每个Phase的执行是否符合规范"""

    # Phase最低agent数量要求
    MIN_AGENTS = {
        "P1": 4,  # 需求分析
        "P2": 6,  # 架构设计
        "P3": 8,  # 编码实现
        "P4": 6,  # 测试验证
        "P5": 4,  # 代码审查
        "P6": 2,  # 发布部署
    }

    def __init__(self):
        self.phase_dir = Path(".phase")
        self.tickets_dir = Path(".tickets")
        self.limits_dir = Path(".limits")

    def get_current_phase(self):
        """获取当前Phase"""
        phase_file = self.phase_dir / "current"
        if phase_file.exists():
            return phase_file.read_text().strip()
        return "P1"

    def create_prompt_with_restrictions(self, agent_type, task, ticket_id=None):
        """创建包含限制的prompt"""
        phase = self.get_current_phase()

        base_prompt = f"""
你是一个{agent_type}，负责在{phase}阶段完成以下任务：

任务描述：{task}
"""

        if ticket_id:
            base_prompt += f"\n工单编号：{ticket_id}"

        # 关键限制
        restrictions = """

🚨 重要限制：
1. 你不能调用其他agents（不能使用Task工具）
2. 你必须直接完成所有任务
3. 你不能要求其他agents协助
4. 如果任务太大，专注于最核心的部分
"""

        if phase == "P3" and ticket_id:
            restrictions += f"""
5. 提交信息必须包含：[P3][{agent_type}][{ticket_id}]
6. 提交信息必须列出Changed:清单
"""

        return base_prompt + restrictions


def main():
    """示例用法"""
    validator = PhaseValidator()
    phase = validator.get_current_phase()
    print(f"当前Phase: {phase}")
    print(f"最少需要{validator.MIN_AGENTS[phase]}个agents并行")


if __name__ == "__main__":
    main()
