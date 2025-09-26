#!/usr/bin/env python3
"""
Agent Output Summarizer - 智能收集和汇总多Agent并行执行结果
用于解决8个agents并行执行时输出过多导致的问题
"""

import json
import sys
import os
import time
from datetime import datetime
from pathlib import Path
import hashlib
import re
from typing import Dict, List, Any, Optional
from collections import defaultdict


class AgentOutputSummarizer:
    """Agent输出收集和汇总器"""

    def __init__(self):
        self.project_root = os.environ.get(
            "CLAUDE_PROJECT_DIR", "/home/xx/dev/Claude Enhancer 5.0"
        )
        self.cache_dir = Path(self.project_root) / ".claude" / "agent_outputs"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 输出限制
        self.MAX_OUTPUT_SIZE = 10 * 1024 * 1024  # 10MB per agent
        self.MAX_TOTAL_SIZE = 50 * 1024 * 1024  # 50MB total

        # 收集的数据
        self.agents_data = defaultdict(dict)
        self.execution_stats = {
            "start_time": None,
            "end_time": None,
            "total_agents": 0,
            "completed_agents": 0,
            "failed_agents": 0,
            "total_output_size": 0,
        }

    def process_agent_output(self, tool_data: Dict[str, Any]) -> None:
        """处理单个agent的输出"""
        try:
            # 提取agent信息
            agent_type = tool_data.get("subagent_type", "unknown")
            description = tool_data.get("description", "")
            output = tool_data.get("output", "")

            # 检查输出大小
            output_size = len(output.encode("utf-8"))
            if output_size > self.MAX_OUTPUT_SIZE:
                # 如果输出太大，创建摘要
                output = self._create_summary(output, agent_type)

            # 解析输出内容
            agent_info = {
                "type": agent_type,
                "description": description,
                "output_size": output_size,
                "status": "completed",
                "timestamp": datetime.now().isoformat(),
                "metrics": self._extract_metrics(output),
                "files_created": self._extract_files(output),
                "key_achievements": self._extract_achievements(output),
            }

            # 保存完整输出到文件（避免内存溢出）
            if output_size > 1024 * 1024:  # >1MB保存到文件
                output_file = self._save_output_to_file(agent_type, output)
                agent_info["output_file"] = str(output_file)
                agent_info["output_preview"] = output[:1000] + "..."
            else:
                agent_info["output"] = output

            self.agents_data[agent_type] = agent_info
            self.execution_stats["completed_agents"] += 1
            self.execution_stats["total_output_size"] += output_size

        except Exception as e:
            print(f"⚠️ Error processing agent output: {e}", file=sys.stderr)

    def _create_summary(self, output: str, agent_type: str) -> str:
        """创建输出摘要"""
        lines = output.split("\n")
        summary_lines = []

        # 保留重要行（标题、完成标记、错误等）
        important_patterns = [
            r"^#{1,3}\s+",  # Markdown headers
            r"^✅|^❌|^⚠️",  # Status markers
            r"complete|success|fail|error",  # Status words
            r"created|updated|deleted",  # Action words
            r"\d+\s+files?\s+",  # File counts
            r"\d+\s+lines?\s+",  # Line counts
        ]

        for line in lines[:100]:  # 只看前100行
            if any(re.search(p, line, re.IGNORECASE) for p in important_patterns):
                summary_lines.append(line)

        # 添加统计信息
        summary_lines.append(f"\n... [Output truncated - {len(lines)} total lines]")

        return "\n".join(summary_lines[:50])  # 最多50行摘要

    def _extract_metrics(self, output: str) -> Dict[str, Any]:
        """从输出中提取关键指标"""
        metrics = {
            "lines_of_code": 0,
            "files_created": 0,
            "files_modified": 0,
            "tests_added": 0,
            "performance_improvement": None,
        }

        # 提取代码行数
        loc_match = re.search(r"(\d+)\s+lines?\s+of\s+code", output, re.IGNORECASE)
        if loc_match:
            metrics["lines_of_code"] = int(loc_match.group(1))

        # 提取文件数量
        files_created = re.findall(r"created?\s+(\d+)\s+files?", output, re.IGNORECASE)
        if files_created:
            metrics["files_created"] = sum(int(x) for x in files_created)

        # 提取性能改进
        perf_match = re.search(
            r"(\d+)%\s+(?:improvement|faster|reduction)", output, re.IGNORECASE
        )
        if perf_match:
            metrics["performance_improvement"] = f"{perf_match.group(1)}%"

        return metrics

    def _extract_files(self, output: str) -> List[str]:
        """提取创建或修改的文件列表"""
        files = []

        # 匹配文件路径模式
        file_patterns = [
            r"(?:created?|updated?|modified?)\s+([/\w\-\.]+\.\w+)",
            r"([/\w\-\.]+\.\w+)\s+(?:created|updated|modified)",
            r"^\s*[-*]\s+([/\w\-\.]+\.\w+)",  # Markdown list
        ]

        for pattern in file_patterns:
            matches = re.findall(pattern, output, re.MULTILINE | re.IGNORECASE)
            files.extend(matches)

        # 去重并限制数量
        unique_files = list(set(files))[:20]
        return unique_files

    def _extract_achievements(self, output: str) -> List[str]:
        """提取主要成就"""
        achievements = []

        # 查找成就标记
        achievement_patterns = [
            r"✅\s+(.+?)(?:\n|$)",
            r"(?:completed?|achieved?|implemented?)\s+(.+?)(?:\n|$)",
            r"#{2,3}\s+(?:完成|Completed?|Done)\s*[:：]\s*(.+?)(?:\n|$)",
        ]

        for pattern in achievement_patterns:
            matches = re.findall(pattern, output, re.IGNORECASE)
            achievements.extend(matches)

        # 清理和去重
        achievements = [a.strip() for a in achievements if len(a.strip()) > 10]
        return list(set(achievements))[:10]

    def _save_output_to_file(self, agent_type: str, output: str) -> Path:
        """保存输出到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"agent_output_{agent_type}_{timestamp}.txt"
        filepath = self.cache_dir / filename

        filepath.write_text(output, encoding="utf-8")
        return filepath

    def generate_summary_report(self) -> str:
        """生成汇总报告"""
        if not self.agents_data:
            return "⚠️ No agent outputs collected"

        # 计算执行时间
        execution_time = "N/A"
        if self.execution_stats["start_time"] and self.execution_stats["end_time"]:
            duration = (
                self.execution_stats["end_time"] - self.execution_stats["start_time"]
            )
            execution_time = f"{duration:.1f}s"

        # 生成报告
        report = []
        report.append("# 📊 Agent执行汇总报告\n")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 执行概览
        report.append("## 执行概览\n")
        report.append(f"- **总Agents数**: {len(self.agents_data)}")
        report.append(f"- **成功完成**: {self.execution_stats['completed_agents']}")
        report.append(f"- **执行时间**: {execution_time}")
        report.append(
            f"- **总输出大小**: {self._format_size(self.execution_stats['total_output_size'])}"
        )

        # 计算并行效率
        if len(self.agents_data) > 1:
            parallel_efficiency = min(100, (len(self.agents_data) * 100) / 8)
            report.append(f"- **并行效率**: {parallel_efficiency:.0f}%")

        report.append("\n## Agent成果详情\n")

        # 按agent类型排序
        for idx, (agent_type, data) in enumerate(sorted(self.agents_data.items()), 1):
            report.append(f"### {idx}. **{agent_type}** ✅\n")
            report.append(f"- **任务**: {data.get('description', 'N/A')}")
            report.append(
                f"- **输出大小**: {self._format_size(data.get('output_size', 0))}"
            )

            # 显示指标
            metrics = data.get("metrics", {})
            if metrics.get("lines_of_code"):
                report.append(f"- **代码行数**: {metrics['lines_of_code']}")
            if metrics.get("files_created"):
                report.append(f"- **创建文件**: {metrics['files_created']}个")
            if metrics.get("performance_improvement"):
                report.append(f"- **性能提升**: {metrics['performance_improvement']}")

            # 显示主要成就
            achievements = data.get("key_achievements", [])
            if achievements:
                report.append("- **主要成就**:")
                for achievement in achievements[:3]:
                    report.append(f"  - {achievement}")

            # 显示关键文件
            files = data.get("files_created", [])
            if files:
                report.append("- **关键文件**:")
                for file in files[:5]:
                    report.append(f"  - `{file}`")

            report.append("")

        # 汇总统计
        report.append("## 📈 汇总统计\n")

        total_loc = sum(
            d.get("metrics", {}).get("lines_of_code", 0)
            for d in self.agents_data.values()
        )
        total_files = sum(
            d.get("metrics", {}).get("files_created", 0)
            for d in self.agents_data.values()
        )

        if total_loc > 0:
            report.append(f"- **总代码行数**: {total_loc:,}")
        if total_files > 0:
            report.append(f"- **总创建文件**: {total_files}")

        # 性能改进汇总
        perf_improvements = [
            d.get("metrics", {}).get("performance_improvement")
            for d in self.agents_data.values()
            if d.get("metrics", {}).get("performance_improvement")
        ]
        if perf_improvements:
            report.append(f"- **性能改进**: {', '.join(perf_improvements)}")

        # 建议
        report.append("\n## 💡 后续建议\n")

        if len(self.agents_data) >= 6:
            report.append("- ✅ 多Agent并行执行成功")
            report.append("- 🔍 建议运行测试验证所有变更")
            report.append("- 📊 检查性能基准确认优化效果")

        if total_files > 20:
            report.append("- ⚠️ 创建了大量文件，建议review关键变更")

        if self.execution_stats["total_output_size"] > 20 * 1024 * 1024:
            report.append("- ⚠️ 输出较大，部分内容已保存到文件")

        return "\n".join(report)

    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ["B", "KB", "MB", "GB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f}TB"

    def save_summary(self) -> Path:
        """保存汇总报告到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.cache_dir / f"summary_report_{timestamp}.md"

        report = self.generate_summary_report()
        report_file.write_text(report, encoding="utf-8")

        # 同时保存到固定位置方便查看
        latest_report = Path(self.project_root) / ".claude" / "LATEST_AGENT_SUMMARY.md"
        latest_report.write_text(report, encoding="utf-8")

        return report_file


def main():
    """主函数 - 作为hook被调用"""
    try:
        # 读取输入
        input_data = sys.stdin.read() if not sys.stdin.isatty() else "{}"

        # 解析工具数据
        try:
            tool_data = json.loads(input_data)
        except json.JSONDecodeError:
            # 如果不是JSON，尝试其他格式
            tool_data = {"output": input_data}

        # 只处理Task工具的输出
        if tool_data.get("tool") == "Task" or "subagent_type" in tool_data:
            summarizer = AgentOutputSummarizer()

            # 标记开始时间
            if not summarizer.execution_stats["start_time"]:
                summarizer.execution_stats["start_time"] = time.time()

            # 处理输出
            summarizer.process_agent_output(tool_data)

            # 更新结束时间
            summarizer.execution_stats["end_time"] = time.time()

            # 生成并保存报告
            report_file = summarizer.save_summary()

            # 输出简短提示（非阻塞）
            print(f"✅ Agent output collected and summarized → {report_file.name}")

    except Exception as e:
        # 静默失败，不影响主流程
        print(f"⚠️ Agent summarizer error: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
