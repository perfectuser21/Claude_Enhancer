#!/usr/bin/env python3
"""
Agent Output Collector - 自动收集和汇总Agent输出
在PostToolUse时触发，防止上下文溢出
"""

import sys
import os
import json
import re
from datetime import datetime
from pathlib import Path

class AgentOutputCollector:
    def __init__(self):
        self.output_dir = Path("/home/xx/dev/Perfect21/.perfect21/agent_outputs")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.summary_file = self.output_dir / "latest_summary.json"
        self.max_lines_per_agent = 300
        self.max_total_lines = 1500

    def collect_from_stdin(self):
        """从stdin读取Agent输出"""
        try:
            input_data = sys.stdin.read()

            # 检测是否是Task工具的输出
            if "Task" not in input_data or "subagent_type" not in input_data:
                # 不是Agent输出，直接返回
                print(input_data, end='')
                return

            # 提取Agent信息
            agent_info = self.extract_agent_info(input_data)
            if agent_info:
                # 收集并汇总
                self.collect_and_summarize(agent_info)

            # 返回处理后的输出
            processed = self.process_output(input_data)
            print(processed, end='')

        except Exception as e:
            # 出错时返回原始输入
            print(f"Error in collector: {e}", file=sys.stderr)
            if 'input_data' in locals():
                print(input_data, end='')

    def extract_agent_info(self, text):
        """提取Agent类型和输出"""
        agent_pattern = r'"subagent_type"\s*:\s*"([^"]+)"'
        agents = re.findall(agent_pattern, text)

        if not agents:
            return None

        return {
            "timestamp": datetime.now().isoformat(),
            "agents": agents,
            "agent_count": len(set(agents)),
            "raw_output": text[:5000]  # 只保存前5000字符
        }

    def collect_and_summarize(self, agent_info):
        """收集并汇总Agent输出"""
        # 加载现有汇总
        if self.summary_file.exists():
            with open(self.summary_file, 'r') as f:
                summary = json.load(f)
        else:
            summary = {
                "session_start": datetime.now().isoformat(),
                "total_agents_used": 0,
                "phases_completed": [],
                "compressed_outputs": {}
            }

        # 更新汇总
        summary["total_agents_used"] += agent_info["agent_count"]
        summary["last_update"] = agent_info["timestamp"]

        # 压缩存储每个Agent的输出
        for agent in agent_info["agents"]:
            if agent not in summary["compressed_outputs"]:
                summary["compressed_outputs"][agent] = []

            # 提取关键信息
            key_info = self.extract_key_points(agent_info["raw_output"])
            summary["compressed_outputs"][agent].append({
                "timestamp": agent_info["timestamp"],
                "key_points": key_info
            })

            # 限制每个Agent的历史记录
            if len(summary["compressed_outputs"][agent]) > 3:
                summary["compressed_outputs"][agent] = summary["compressed_outputs"][agent][-3:]

        # 检查是否需要触发压缩
        if summary["total_agents_used"] >= 5:
            summary = self.aggressive_compress(summary)

        # 保存汇总
        with open(self.summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        # 如果Agent太多，发出警告
        if agent_info["agent_count"] >= 5:
            print(f"\n⚠️  Context Usage: {agent_info['agent_count']} agents detected", file=sys.stderr)
            print(f"   Summary saved to reduce context usage", file=sys.stderr)

    def extract_key_points(self, text):
        """提取关键信息点"""
        key_points = []

        # 提取要点标记
        patterns = [
            r'(?:^|\n)[-•*]\s+(.+)',  # 列表项
            r'(?:^|\n)\d+\.\s+(.+)',   # 编号项
            r'TODO:\s*(.+)',           # TODO项
            r'IMPORTANT:\s*(.+)',      # 重要项
            r'Decision:\s*(.+)',       # 决策项
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            key_points.extend(matches[:2])  # 每种类型最多2个

        # 如果没找到要点，提取前3行非空行
        if not key_points:
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            key_points = lines[:3]

        return key_points[:5]  # 最多5个要点

    def aggressive_compress(self, summary):
        """激进压缩模式"""
        compressed = {
            "session_start": summary["session_start"],
            "total_agents_used": summary["total_agents_used"],
            "last_update": summary["last_update"],
            "critical_summary": {}
        }

        # 每个Agent只保留最新的1个要点
        for agent, outputs in summary["compressed_outputs"].items():
            if outputs:
                latest = outputs[-1]
                if latest["key_points"]:
                    compressed["critical_summary"][agent] = latest["key_points"][0]

        return compressed

    def process_output(self, output):
        """处理输出，添加汇总信息"""
        # 如果有汇总文件，添加提示
        if self.summary_file.exists():
            with open(self.summary_file, 'r') as f:
                summary = json.load(f)

            if summary.get("total_agents_used", 0) >= 3:
                hint = f"\n💡 Context optimized: {summary['total_agents_used']} agents summarized\n"
                return output + hint

        return output


def main():
    """主函数"""
    collector = AgentOutputCollector()
    collector.collect_from_stdin()


if __name__ == "__main__":
    main()