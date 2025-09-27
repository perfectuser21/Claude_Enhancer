#!/usr/bin/env python3
"""
系统健康检查工具 - 一键生成彩色健康报告
"""

import os
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple, List


# ANSI颜色码
class Colors:
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def run_command(cmd: str, check=False) -> Tuple[bool, str]:
    """运行命令并返回成功状态和输出"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0, result.stdout.strip()
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        return False, str(e)


def check_file_exists(path: str) -> bool:
    """检查文件是否存在"""
    return Path(path).exists()


def check_executable(path: str) -> bool:
    """检查文件是否可执行"""
    return Path(path).is_file() and os.access(path, os.X_OK)


class SystemHealthChecker:
    def __init__(self):
        self.checks = []
        self.total_score = 0
        self.max_score = 0

    def add_check(
        self, name: str, status: str, score: int, max_score: int, note: str = ""
    ):
        """添加检查项"""
        self.checks.append(
            {
                "name": name,
                "status": status,
                "score": score,
                "max_score": max_score,
                "note": note,
            }
        )
        self.total_score += score
        self.max_score += max_score

    def check_phase_system(self):
        """检查Phase轨道系统"""
        print(f"{Colors.BLUE}检查Phase系统...{Colors.RESET}")

        # 检查当前phase
        if check_file_exists(".phase/current"):
            with open(".phase/current", "r") as f:
                current = f.read().strip()
            if current in ["P1", "P2", "P3", "P4", "P5", "P6"]:
                self.add_check("Phase轨道", "OK", 10, 10, f"当前{current}")
            else:
                self.add_check("Phase轨道", "Degraded", 5, 10, f"异常值:{current}")
        else:
            self.add_check("Phase轨道", "Missing", 0, 10, "文件缺失")

        # 检查Gates
        gates = []
        for i in range(1, 7):
            if check_file_exists(f".gates/0{i}.ok"):
                gates.append(f"0{i}")

        if len(gates) == 6:
            self.add_check("Gates", "OK", 10, 10, "全部通过")
        elif len(gates) > 0:
            self.add_check("Gates", "Degraded", 5, 10, f"通过{len(gates)}/6")
        else:
            self.add_check("Gates", "Missing", 0, 10, "无Gate")

    def check_tickets_limits(self):
        """检查并行控制系统"""
        print(f"{Colors.BLUE}检查并行控制...{Colors.RESET}")

        # 获取当前phase
        current_phase = "P1"
        if check_file_exists(".phase/current"):
            with open(".phase/current", "r") as f:
                current_phase = f.read().strip()

        # 检查limits
        limit = 5  # 默认值
        if check_file_exists(f".limits/{current_phase}/max"):
            with open(f".limits/{current_phase}/max", "r") as f:
                limit = int(f.read().strip())

        # 统计活动tickets
        active = 0
        if os.path.exists(".tickets"):
            active = len([f for f in os.listdir(".tickets") if f.endswith(".todo")])

        if active <= limit:
            self.add_check("并行控制", "OK", 10, 10, f"{active}/{limit}")
        else:
            self.add_check("并行控制", "Degraded", 5, 10, f"超限{active}/{limit}")

    def check_artifacts(self):
        """检查Phase产物"""
        print(f"{Colors.BLUE}检查Phase产物...{Colors.RESET}")

        artifacts = {
            "docs/PLAN.md": "P1产物",
            "docs/DESIGN.md": "P2产物",
            "docs/TEST-REPORT.md": "P4产物",
            "docs/REVIEW.md": "P5产物",
            "docs/README.md": "P6产物",
            "docs/CHANGELOG.md": "P6产物",
        }

        for path, name in artifacts.items():
            if check_file_exists(path):
                self.add_check(name, "OK", 5, 5, "存在")
            else:
                self.add_check(name, "Missing", 0, 5, "缺失")

    def check_git_hooks(self):
        """检查Git Hooks"""
        print(f"{Colors.BLUE}检查Git Hooks...{Colors.RESET}")

        hooks = ["pre-commit", "commit-msg", "pre-push", "post-merge"]
        present = []

        for hook in hooks:
            if check_executable(f".git/hooks/{hook}"):
                present.append(hook)

        if len(present) == 4:
            self.add_check("Git Hooks", "OK", 15, 15, "4个全部存在")
        elif len(present) > 0:
            self.add_check("Git Hooks", "Degraded", 10, 15, f"{len(present)}/4存在")
        else:
            self.add_check("Git Hooks", "Missing", 0, 15, "全部缺失")

    def check_claude_hooks(self):
        """检查Claude Hooks"""
        print(f"{Colors.BLUE}检查Claude Hooks...{Colors.RESET}")

        if os.path.exists(".claude/hooks"):
            total = len(os.listdir(".claude/hooks"))

            # 检查核心hooks
            core_hooks = [
                "workflow_enforcer.sh",
                "branch_helper.sh",
                "smart_agent_selector.sh",
                "quality_gate.sh",
                "performance_monitor.sh",
            ]

            missing = []
            for hook in core_hooks:
                if not check_file_exists(f".claude/hooks/{hook}"):
                    missing.append(hook)

            if total >= 50 and len(missing) == 0:
                self.add_check("Claude Hooks", "OK", 10, 10, f"{total}个hooks完整")
            elif total > 0:
                self.add_check(
                    "Claude Hooks",
                    "Degraded",
                    7,
                    10,
                    f"{total}个hooks,缺{len(missing)}个核心",
                )
            else:
                self.add_check("Claude Hooks", "Missing", 0, 10, "目录不存在")
        else:
            self.add_check("Claude Hooks", "Missing", 0, 10, "目录不存在")

    def check_executor(self):
        """检查执行器系统"""
        print(f"{Colors.BLUE}检查执行器系统...{Colors.RESET}")

        checks = {
            "Python executor": check_file_exists(".workflow/executor/executor.py"),
            "Shell executor": check_file_exists(".workflow/executor.sh"),
            "inotify-tools": run_command("command -v inotifywait")[0],
        }

        score = sum([5 if v else 0 for v in checks.values()])

        if all(checks.values()):
            self.add_check("执行器", "OK", 15, 15, "完全就绪")
        elif any(checks.values()):
            missing = [k for k, v in checks.items() if not v]
            self.add_check("执行器", "Degraded", score, 15, f"缺失:{','.join(missing)}")
        else:
            self.add_check("执行器", "Missing", 0, 15, "全部缺失")

    def check_performance(self):
        """检查性能"""
        print(f"{Colors.BLUE}检查性能...{Colors.RESET}")

        start = time.time()
        run_command("git diff --name-only")
        elapsed = int((time.time() - start) * 1000)

        if elapsed < 100:
            self.add_check("性能", "OK", 10, 10, f"{elapsed}ms优秀")
        elif elapsed < 250:
            self.add_check("性能", "OK", 8, 10, f"{elapsed}ms良好")
        else:
            self.add_check("性能", "Degraded", 5, 10, f"{elapsed}ms偏慢")

    def generate_report(self):
        """生成报告"""
        print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}系统健康检查报告{Colors.RESET}")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")

        # 状态表格
        print(f"{'模块':<20} {'状态':<15} {'得分':<10} {'备注':<30}")
        print("-" * 75)

        for check in self.checks:
            # 选择颜色
            if check["status"] == "OK":
                color = Colors.GREEN
                symbol = "✅"
            elif check["status"] == "Degraded":
                color = Colors.YELLOW
                symbol = "⚠️"
            else:
                color = Colors.RED
                symbol = "❌"

            print(
                f"{check['name']:<20} {color}{symbol} {check['status']:<12}{Colors.RESET} "
                f"{check['score']}/{check['max_score']:<8} {check['note']:<30}"
            )

        # 总分
        percentage = (
            int(self.total_score * 100 / self.max_score) if self.max_score > 0 else 0
        )

        print(f"\n{'='*60}")

        # 根据分数选择颜色
        if percentage >= 90:
            score_color = Colors.GREEN
            status = "优秀"
        elif percentage >= 70:
            score_color = Colors.YELLOW
            status = "良好"
        else:
            score_color = Colors.RED
            status = "需要修复"

        print(
            f"{Colors.BOLD}总体健康度: {score_color}{percentage}%{Colors.RESET} ({self.total_score}/{self.max_score}分)"
        )
        print(f"系统状态: {score_color}{status}{Colors.RESET}")

        # 问题汇总
        degraded = [c for c in self.checks if c["status"] == "Degraded"]
        missing = [c for c in self.checks if c["status"] == "Missing"]

        if degraded or missing:
            print(f"\n{Colors.YELLOW}需要关注的问题:{Colors.RESET}")
            for item in degraded:
                print(f"  ⚠️  {item['name']}: {item['note']}")
            for item in missing:
                print(f"  ❌ {item['name']}: {item['note']}")

        # 修复建议
        if percentage < 100:
            print(f"\n{Colors.BLUE}修复建议:{Colors.RESET}")
            if not run_command("command -v inotifywait")[0]:
                print(f"  1. 安装inotify-tools: sudo apt-get install inotify-tools")
            if missing:
                print(f"  2. 修复缺失组件: {', '.join([m['name'] for m in missing])}")
            if degraded:
                print(f"  3. 优化降级组件: {', '.join([d['name'] for d in degraded])}")

        print(f"\n{'='*60}")

        # 保存到文件
        self.save_to_file(percentage)

    def save_to_file(self, percentage):
        """保存报告到文件"""
        report_content = f"""# 系统健康检查报告
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
健康度: {percentage}%

## 检查结果

| 模块 | 状态 | 得分 | 备注 |
|------|------|------|------|
"""
        for check in self.checks:
            status_icon = (
                "✅"
                if check["status"] == "OK"
                else "⚠️"
                if check["status"] == "Degraded"
                else "❌"
            )
            report_content += f"| {check['name']} | {status_icon} {check['status']} | {check['score']}/{check['max_score']} | {check['note']} |\n"

        report_content += f"\n## 总体评分: {percentage}/100\n"

        with open("SYSTEM_HEALTH_CHECK.md", "w") as f:
            f.write(report_content)

        print(f"{Colors.GREEN}报告已保存到 SYSTEM_HEALTH_CHECK.md{Colors.RESET}")


def main():
    checker = SystemHealthChecker()

    # 运行所有检查
    checker.check_phase_system()
    checker.check_tickets_limits()
    checker.check_artifacts()
    checker.check_git_hooks()
    checker.check_claude_hooks()
    checker.check_executor()
    checker.check_performance()

    # 生成报告
    checker.generate_report()


if __name__ == "__main__":
    main()
