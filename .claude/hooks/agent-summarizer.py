#!/usr/bin/env python3
"""
Agent Output Summarizer - 汇总多个subagent的输出，防止上下文溢出
"""

import sys
import json
import re
from typing import List, Dict, Any

class AgentSummarizer:
    """汇总和压缩多个Agent的输出"""

    def __init__(self):
        self.max_output_per_agent = 500  # 每个Agent最多保留500行
        self.max_total_output = 2000     # 总输出最多2000行

    def summarize_agent_outputs(self, agents_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        汇总多个Agent的输出

        输入格式:
        [
            {
                "agent": "backend-architect",
                "output": "详细的架构设计...",
                "status": "completed"
            },
            ...
        ]
        """
        summary = {
            "agent_count": len(agents_data),
            "status": "summarized",
            "key_results": {},
            "compressed_outputs": {},
            "action_items": [],
            "warnings": []
        }

        total_lines = 0

        for agent_data in agents_data:
            agent_name = agent_data.get("agent", "unknown")
            output = agent_data.get("output", "")

            # 提取关键信息
            key_info = self._extract_key_information(output)
            summary["key_results"][agent_name] = key_info

            # 压缩输出
            compressed = self._compress_output(output, self.max_output_per_agent)
            summary["compressed_outputs"][agent_name] = compressed

            # 提取行动项
            actions = self._extract_action_items(output)
            summary["action_items"].extend(actions)

            # 检查警告
            warnings = self._extract_warnings(output)
            summary["warnings"].extend(warnings)

            total_lines += len(compressed.split('\n'))

        # 如果总输出还是太大，进一步压缩
        if total_lines > self.max_total_output:
            summary = self._aggressive_compression(summary)

        return summary

    def _extract_key_information(self, text: str) -> Dict[str, Any]:
        """提取关键信息"""
        key_info = {
            "main_points": [],
            "decisions": [],
            "dependencies": []
        }

        # 提取要点（查找列表项）
        bullets = re.findall(r'[•\-\*]\s+(.+)', text)
        key_info["main_points"] = bullets[:5]  # 最多5个要点

        # 提取决策（查找决策关键词）
        decision_patterns = [
            r'决定[：:]\s*(.+)',
            r'选择[：:]\s*(.+)',
            r'采用[：:]\s*(.+)',
            r'Decision[：:]\s*(.+)',
        ]
        for pattern in decision_patterns:
            decisions = re.findall(pattern, text, re.IGNORECASE)
            key_info["decisions"].extend(decisions[:2])

        # 提取依赖
        dep_patterns = [
            r'依赖[：:]\s*(.+)',
            r'需要[：:]\s*(.+)',
            r'Depends on[：:]\s*(.+)',
        ]
        for pattern in dep_patterns:
            deps = re.findall(pattern, text, re.IGNORECASE)
            key_info["dependencies"].extend(deps[:3])

        return key_info

    def _compress_output(self, text: str, max_lines: int) -> str:
        """压缩输出文本"""
        lines = text.split('\n')

        if len(lines) <= max_lines:
            return text

        # 保留开头和结尾
        head_lines = lines[:max_lines//3]
        tail_lines = lines[-(max_lines//3):]

        # 中间部分提取重要行
        middle_lines = []
        important_keywords = [
            'error', 'warning', 'critical', 'important',
            '错误', '警告', '重要', '关键',
            'TODO', 'FIXME', 'NOTE'
        ]

        for line in lines[max_lines//3:-(max_lines//3)]:
            if any(keyword in line.lower() for keyword in important_keywords):
                middle_lines.append(line)
                if len(middle_lines) >= max_lines//3:
                    break

        compressed = head_lines + ['... [中间内容已压缩] ...'] + middle_lines + tail_lines
        return '\n'.join(compressed)

    def _extract_action_items(self, text: str) -> List[str]:
        """提取行动项"""
        action_patterns = [
            r'TODO[：:]\s*(.+)',
            r'Action[：:]\s*(.+)',
            r'Next step[：:]\s*(.+)',
            r'下一步[：:]\s*(.+)',
        ]

        actions = []
        for pattern in action_patterns:
            found = re.findall(pattern, text, re.IGNORECASE)
            actions.extend(found[:3])

        return actions

    def _extract_warnings(self, text: str) -> List[str]:
        """提取警告信息"""
        warning_patterns = [
            r'WARNING[：:]\s*(.+)',
            r'CAUTION[：:]\s*(.+)',
            r'⚠️\s*(.+)',
            r'警告[：:]\s*(.+)',
        ]

        warnings = []
        for pattern in warning_patterns:
            found = re.findall(pattern, text, re.IGNORECASE)
            warnings.extend(found[:3])

        return warnings

    def _aggressive_compression(self, summary: Dict[str, Any]) -> Dict[str, Any]:
        """激进压缩模式"""
        # 只保留最关键的信息
        compressed_summary = {
            "agent_count": summary["agent_count"],
            "status": "heavily_compressed",
            "critical_only": {}
        }

        for agent, info in summary["key_results"].items():
            # 每个Agent只保留1个要点
            if info["main_points"]:
                compressed_summary["critical_only"][agent] = info["main_points"][0]

        # 只保留前3个行动项
        compressed_summary["next_actions"] = summary["action_items"][:3]

        # 只保留第一个警告
        if summary["warnings"]:
            compressed_summary["main_warning"] = summary["warnings"][0]

        return compressed_summary


def main():
    """主函数 - 处理Hook调用"""
    if len(sys.argv) < 2:
        print("Usage: agent-summarizer.py <agent_outputs.json>")
        sys.exit(1)

    try:
        # 读取Agent输出
        with open(sys.argv[1], 'r') as f:
            agent_outputs = json.load(f)

        # 创建汇总器
        summarizer = AgentSummarizer()

        # 生成汇总
        summary = summarizer.summarize_agent_outputs(agent_outputs)

        # 输出汇总结果
        print(json.dumps(summary, ensure_ascii=False, indent=2))

    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()