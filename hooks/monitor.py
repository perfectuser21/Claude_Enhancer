#!/usr/bin/env python3
"""
Perfect21 监控器 - 实时监控Claude Code的规则遵守情况
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
import time

sys.path.append(str(Path(__file__).parent.parent))
from hooks.perfect21_enforcer import Perfect21Enforcer

class Perfect21Monitor:
    """Perfect21监控器"""

    def __init__(self):
        self.console = Console()
        self.enforcer = Perfect21Enforcer()
        self.violations_log = self.enforcer.violations_log
        self.compliance_threshold = 80  # 合规率阈值

    def get_recent_violations(self, hours: int = 24) -> List[Dict]:
        """获取最近的违规记录"""
        if not self.violations_log.exists():
            return []

        violations = []
        cutoff_time = datetime.now() - timedelta(hours=hours)

        with open(self.violations_log, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    entry_time = datetime.fromisoformat(entry["timestamp"])
                    if entry_time > cutoff_time and not entry.get("passed", True):
                        violations.append(entry)
                except:
                    continue

        return violations[-10:]  # 返回最近10条违规

    def get_agent_usage_stats(self) -> Dict[str, int]:
        """获取Agent使用统计"""
        if not self.violations_log.exists():
            return {}

        agent_counts = {}

        with open(self.violations_log, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get("passed") and "agents" in entry:
                        for agent in entry["agents"]:
                            agent_counts[agent] = agent_counts.get(agent, 0) + 1
                except:
                    continue

        return dict(sorted(agent_counts.items(), key=lambda x: x[1], reverse=True)[:10])

    def create_dashboard(self) -> Layout:
        """创建监控仪表板"""
        layout = Layout()

        # 获取统计数据
        stats = self.enforcer.get_violation_stats()
        recent_violations = self.get_recent_violations()
        agent_stats = self.get_agent_usage_stats()

        # 创建布局
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )

        layout["main"].split_row(
            Layout(name="stats"),
            Layout(name="violations")
        )

        # Header
        header_text = Text("Perfect21 规则监控中心", style="bold cyan")
        layout["header"].update(Panel(header_text, title="监控器"))

        # Stats Panel
        stats_table = Table(title="遵守情况统计", show_header=True)
        stats_table.add_column("指标", style="cyan")
        stats_table.add_column("数值", style="green")

        compliance_color = "green" if stats["compliance_rate"] >= self.compliance_threshold else "red"
        stats_table.add_row("总执行次数", str(stats["total"]))
        stats_table.add_row("违规次数", str(stats["violations"]))
        stats_table.add_row("合规率", f"[{compliance_color}]{stats['compliance_rate']}%[/{compliance_color}]")

        # Agent使用TOP榜
        if agent_stats:
            stats_table.add_row("", "")
            stats_table.add_row("[bold]常用Agent TOP5[/bold]", "")
            for agent, count in list(agent_stats.items())[:5]:
                stats_table.add_row(f"  {agent}", str(count))

        layout["stats"].update(Panel(stats_table))

        # Violations Panel
        violations_table = Table(title="最近违规记录", show_header=True)
        violations_table.add_column("时间", style="yellow")
        violations_table.add_column("错误", style="red")

        if recent_violations:
            for violation in recent_violations:
                timestamp = datetime.fromisoformat(violation["timestamp"]).strftime("%H:%M:%S")
                error = violation.get("error", "未知错误")[:50] + "..."
                violations_table.add_row(timestamp, error)
        else:
            violations_table.add_row("无违规", "[green]系统运行正常[/green]")

        layout["violations"].update(Panel(violations_table))

        # Footer
        footer_text = f"刷新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        if stats["compliance_rate"] < self.compliance_threshold:
            footer_text += f" | [red]⚠️ 合规率低于{self.compliance_threshold}%[/red]"
        else:
            footer_text += " | [green]✅ 系统合规[/green]"

        layout["footer"].update(Panel(footer_text))

        return layout

    def run_live_monitor(self, refresh_rate: int = 5):
        """运行实时监控"""
        self.console.print("[cyan]Perfect21 实时监控启动中...[/cyan]")
        self.console.print(f"[yellow]刷新率: {refresh_rate}秒[/yellow]")
        self.console.print("[dim]按 Ctrl+C 退出[/dim]\n")

        try:
            with Live(self.create_dashboard(), refresh_per_second=1/refresh_rate) as live:
                while True:
                    time.sleep(refresh_rate)
                    live.update(self.create_dashboard())
        except KeyboardInterrupt:
            self.console.print("\n[yellow]监控停止[/yellow]")

    def generate_report(self) -> str:
        """生成合规报告"""
        stats = self.enforcer.get_violation_stats()
        violations = self.get_recent_violations(hours=7*24)  # 一周的数据
        agent_stats = self.get_agent_usage_stats()

        report = f"""
# Perfect21 合规报告
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 总体统计
- 总执行次数: {stats['total']}
- 违规次数: {stats['violations']}
- 合规率: {stats['compliance_rate']}%

## Agent使用排行
"""
        for i, (agent, count) in enumerate(agent_stats.items(), 1):
            report += f"{i}. {agent}: {count}次\n"

        if violations:
            report += "\n## 违规详情（最近一周）\n"
            for v in violations[:20]:
                report += f"- {v.get('timestamp', 'N/A')}: {v.get('error', 'N/A')[:100]}\n"

        # 建议
        report += "\n## 改进建议\n"
        if stats['compliance_rate'] < 90:
            report += "- ⚠️ 合规率偏低，建议强化规则学习\n"
        if stats['violations'] > 10:
            report += "- ⚠️ 违规次数较多，建议检查规则配置\n"

        return report

    def interactive_menu(self):
        """交互式菜单"""
        while True:
            self.console.print("\n[cyan]Perfect21 监控中心[/cyan]")
            self.console.print("1. 查看实时监控")
            self.console.print("2. 生成合规报告")
            self.console.print("3. 查看违规统计")
            self.console.print("4. 清除历史记录")
            self.console.print("0. 退出")

            choice = input("\n请选择: ")

            if choice == "1":
                self.run_live_monitor()
            elif choice == "2":
                report = self.generate_report()
                self.console.print(report)
                # 保存报告
                report_file = Path(f"perfect21_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
                report_file.write_text(report)
                self.console.print(f"[green]报告已保存到: {report_file}[/green]")
            elif choice == "3":
                stats = self.enforcer.get_violation_stats()
                self.console.print(Panel(f"""
总执行: {stats['total']}
违规数: {stats['violations']}
合规率: {stats['compliance_rate']}%
                """, title="违规统计"))
            elif choice == "4":
                if input("确认清除所有历史记录？(y/n): ").lower() == "y":
                    if self.violations_log.exists():
                        self.violations_log.unlink()
                        self.console.print("[green]历史记录已清除[/green]")
            elif choice == "0":
                break

def main():
    """主函数"""
    monitor = Perfect21Monitor()

    if len(sys.argv) > 1:
        if sys.argv[1] == "live":
            monitor.run_live_monitor()
        elif sys.argv[1] == "report":
            print(monitor.generate_report())
        elif sys.argv[1] == "stats":
            stats = monitor.enforcer.get_violation_stats()
            print(f"合规率: {stats['compliance_rate']}%")
    else:
        monitor.interactive_menu()

if __name__ == "__main__":
    main()