#!/usr/bin/env python3
"""
并行 SubAgent 显示效果实现示例
实现类似 Claude Code 的彩色进度显示
"""

import asyncio
import random
from datetime import datetime
from typing import List, Dict, Any
import sys
from enum import Enum


# ANSI 颜色码
class Colors:
    RESET = "\033[0m"

    # 前景色
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # 亮色版本
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # 背景色
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

    # 样式
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    REVERSE = "\033[7m"
    HIDDEN = "\033[8m"
    STRIKETHROUGH = "\033[9m"


class AgentStatus(Enum):
    """Agent 执行状态"""

    PENDING = "pending"
    STARTING = "starting"
    RUNNING = "running"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    WARNING = "warning"


class AgentDisplay:
    """Agent 显示管理器"""

    STATUS_ICONS = {
        AgentStatus.PENDING: "⏳",
        AgentStatus.STARTING: "🚀",
        AgentStatus.RUNNING: "🔄",
        AgentStatus.PROCESSING: "⚙️",
        AgentStatus.COMPLETED: "✅",
        AgentStatus.ERROR: "❌",
        AgentStatus.WARNING: "⚠️",
    }

    STATUS_COLORS = {
        AgentStatus.PENDING: Colors.BRIGHT_BLACK,
        AgentStatus.STARTING: Colors.BRIGHT_YELLOW,
        AgentStatus.RUNNING: Colors.BRIGHT_CYAN,
        AgentStatus.PROCESSING: Colors.BRIGHT_BLUE,
        AgentStatus.COMPLETED: Colors.BRIGHT_GREEN,
        AgentStatus.ERROR: Colors.BRIGHT_RED,
        AgentStatus.WARNING: Colors.YELLOW,
    }

    def __init__(self):
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.display_lock = asyncio.Lock()
        self.line_count = 0

    def add_agent(self, name: str, description: str):
        """添加一个 Agent"""
        self.agents[name] = {
            "status": AgentStatus.PENDING,
            "description": description,
            "progress": 0,
            "message": "Waiting to start...",
            "start_time": None,
            "end_time": None,
            "subtasks": [],
        }

    def clear_lines(self, count: int):
        """清除指定行数的终端内容"""
        for _ in range(count):
            sys.stdout.write("\033[F")  # 光标上移一行
            sys.stdout.write("\033[K")  # 清除当前行

    async def update_display(self):
        """更新终端显示"""
        async with self.display_lock:
            # 清除之前的显示
            if self.line_count > 0:
                self.clear_lines(self.line_count)

            # 显示标题
            lines = []
            lines.append(
                f"\n{Colors.BOLD}{Colors.BRIGHT_WHITE}🤖 Parallel Agent Execution{Colors.RESET}"
            )
            lines.append(
                f"{Colors.DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.RESET}"
            )

            # 显示每个 Agent 的状态
            for name, agent in self.agents.items():
                status = agent["status"]
                icon = self.STATUS_ICONS[status]
                color = self.STATUS_COLORS[status]

                # 基础信息行
                status_line = f"{icon} {color}{Colors.BOLD}{name}{Colors.RESET}"

                # 添加进度条（如果正在运行）
                if status in [AgentStatus.RUNNING, AgentStatus.PROCESSING]:
                    progress = agent["progress"]
                    bar_length = 20
                    filled = int(bar_length * progress / 100)
                    bar = "█" * filled + "░" * (bar_length - filled)

                    # 计算运行时间
                    if agent["start_time"]:
                        elapsed = (datetime.now() - agent["start_time"]).seconds
                        time_str = f" [{elapsed}s]"
                    else:
                        time_str = ""

                    status_line += f" {Colors.DIM}[{color}{bar}{Colors.DIM}] {progress}%{time_str}{Colors.RESET}"

                # 添加消息
                message = agent["message"]
                if len(message) > 50:
                    message = message[:47] + "..."
                status_line += f" {Colors.DIM}- {message}{Colors.RESET}"

                # 如果完成，显示耗时
                if (
                    status == AgentStatus.COMPLETED
                    and agent["start_time"]
                    and agent["end_time"]
                ):
                    duration = (agent["end_time"] - agent["start_time"]).seconds
                    status_line += f" {Colors.BRIGHT_GREEN}({duration}s){Colors.RESET}"

                lines.append(status_line)

                # 显示子任务（如果有）
                for subtask in agent.get("subtasks", [])[-3:]:  # 只显示最近3个子任务
                    lines.append(f"    {Colors.DIM}└─ {subtask}{Colors.RESET}")

            # 显示统计信息
            completed = sum(
                1 for a in self.agents.values() if a["status"] == AgentStatus.COMPLETED
            )
            total = len(self.agents)
            running = sum(
                1
                for a in self.agents.values()
                if a["status"] in [AgentStatus.RUNNING, AgentStatus.PROCESSING]
            )

            lines.append(
                f"{Colors.DIM}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{Colors.RESET}"
            )
            lines.append(
                f"📊 Progress: {Colors.BRIGHT_GREEN}{completed}{Colors.RESET}/{total} completed, "
                f"{Colors.BRIGHT_CYAN}{running}{Colors.RESET} running"
            )

            # 输出所有行
            for line in lines:
                print(line)

            self.line_count = len(lines)
            sys.stdout.flush()

    async def update_agent(
        self,
        name: str,
        status: AgentStatus = None,
        progress: int = None,
        message: str = None,
        subtask: str = None,
    ):
        """更新 Agent 状态"""
        if name not in self.agents:
            return

        agent = self.agents[name]

        if status:
            agent["status"] = status
            if status == AgentStatus.STARTING:
                agent["start_time"] = datetime.now()
            elif status == AgentStatus.COMPLETED:
                agent["end_time"] = datetime.now()
                agent["progress"] = 100

        if progress is not None:
            agent["progress"] = min(100, max(0, progress))

        if message:
            agent["message"] = message

        if subtask:
            agent["subtasks"].append(subtask)
            if len(agent["subtasks"]) > 10:  # 保持子任务列表不要太长
                agent["subtasks"].pop(0)

        await self.update_display()


class MockAgent:
    """模拟 Agent 执行"""

    def __init__(self, name: str, display: AgentDisplay):
        self.name = name
        self.display = display

    async def run(self):
        """模拟 Agent 执行过程"""
        # 启动
        await self.display.update_agent(
            self.name, AgentStatus.STARTING, message="Initializing agent..."
        )
        await asyncio.sleep(random.uniform(0.5, 1.5))

        # 运行
        await self.display.update_agent(
            self.name, AgentStatus.RUNNING, message="Analyzing requirements..."
        )

        # 模拟多个步骤
        steps = [
            ("Loading configuration", 20),
            ("Connecting to services", 40),
            ("Processing data", 60),
            ("Generating output", 80),
            ("Finalizing results", 100),
        ]

        for step_name, progress in steps:
            await self.display.update_agent(
                self.name, AgentStatus.PROCESSING, progress=progress, message=step_name
            )

            # 随机添加子任务
            if random.random() > 0.5:
                subtask = f"Processing: {step_name.lower()}"
                await self.display.update_agent(self.name, subtask=subtask)

            await asyncio.sleep(random.uniform(0.5, 2.0))

        # 完成
        await self.display.update_agent(
            self.name, AgentStatus.COMPLETED, message="Task completed successfully"
        )


async def demo_parallel_execution():
    """演示并行执行效果"""

    # 创建显示管理器
    display = AgentDisplay()

    # 定义要运行的 Agents
    agents_config = [
        ("backend-architect", "Designing system architecture"),
        ("security-auditor", "Performing security audit"),
        ("test-engineer", "Creating test strategy"),
        ("api-designer", "Designing API endpoints"),
        ("database-specialist", "Optimizing database schema"),
        ("performance-engineer", "Analyzing performance metrics"),
    ]

    # 添加所有 Agents
    for name, description in agents_config:
        display.add_agent(name, description)

    # 初始显示
    await display.update_display()

    # 创建并运行所有 Agents
    agents = [MockAgent(name, display) for name, _ in agents_config]
    tasks = [agent.run() for agent in agents]

    # 并行执行
    await asyncio.gather(*tasks)

    # 最终状态
    print(
        f"\n{Colors.BOLD}{Colors.BRIGHT_GREEN}✨ All agents completed successfully!{Colors.RESET}\n"
    )


async def demo_advanced_display():
    """演示更高级的显示效果"""

    print(
        f"\n{Colors.BOLD}{Colors.BRIGHT_MAGENTA}🎨 Advanced Display Features Demo{Colors.RESET}\n"
    )

    # 1. 渐变进度条
    print(f"{Colors.BOLD}1. Gradient Progress Bars:{Colors.RESET}")
    for i in range(0, 101, 10):
        bar_length = 30
        filled = int(bar_length * i / 100)

        # 使用不同颜色创建渐变效果
        if i < 33:
            color = Colors.BRIGHT_RED
        elif i < 66:
            color = Colors.BRIGHT_YELLOW
        else:
            color = Colors.BRIGHT_GREEN

        bar = "█" * filled + "░" * (bar_length - filled)
        print(f"  {color}{bar}{Colors.RESET} {i}%")

    print()

    # 2. 动画效果
    print(f"{Colors.BOLD}2. Animation Effects:{Colors.RESET}")
    spinners = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    for _ in range(2):
        for spinner in spinners:
            sys.stdout.write(
                f"\r  {Colors.BRIGHT_CYAN}{spinner} Processing...{Colors.RESET}"
            )
            sys.stdout.flush()
            await asyncio.sleep(0.1)
    print("\r  ✅ Complete!                ")

    print()

    # 3. 状态卡片
    print(f"{Colors.BOLD}3. Status Cards:{Colors.RESET}")
    print(
        f"""
  {Colors.BG_BLUE}{Colors.WHITE} Backend Service {Colors.RESET}
  ├─ Status: {Colors.BRIGHT_GREEN}● Active{Colors.RESET}
  ├─ Uptime: 2h 34m
  ├─ Memory: 256MB / 512MB
  └─ CPU: 23%

  {Colors.BG_MAGENTA}{Colors.WHITE} Database {Colors.RESET}
  ├─ Status: {Colors.BRIGHT_GREEN}● Connected{Colors.RESET}
  ├─ Queries: 1,234/s
  ├─ Connections: 45/100
  └─ Response: 12ms
    """
    )

    # 4. 实时图表（ASCII）
    print(f"{Colors.BOLD}4. ASCII Charts:{Colors.RESET}")
    print(
        f"""
  Performance Metrics (last 60s)
  100% ┤
   90% ┤    ╭─╮
   80% ┤   ╱  ╰╮
   70% ┤  ╱    ╰─╮
   60% ┤ ╱       ╰╮
   50% ┼─         ╰─╮
   40% ┤            ╰╮
   30% ┤             ╰─╮
   20% ┤               ╰╮
   10% ┤                ╰─
    0% └─────────────────────
        0s   20s   40s   60s
    """
    )


if __name__ == "__main__":
    print(
        f"\n{Colors.BOLD}{Colors.BRIGHT_WHITE}═══════════════════════════════════════════════{Colors.RESET}"
    )
    print(
        f"{Colors.BOLD}{Colors.BRIGHT_CYAN}   Claude Code Style Agent Display Demo{Colors.RESET}"
    )
    print(
        f"{Colors.BOLD}{Colors.BRIGHT_WHITE}═══════════════════════════════════════════════{Colors.RESET}"
    )

    # 运行演示
    asyncio.run(demo_parallel_execution())

    # 显示高级特性
    asyncio.run(demo_advanced_display())
