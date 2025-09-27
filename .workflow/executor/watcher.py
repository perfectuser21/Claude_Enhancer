#!/usr/bin/env python3
"""
Claude Enhancer 事件监听器
使用inotify监听文件变化，自动触发验证和phase推进
高性能，低延迟，替代polling方式
"""

import os
import sys
import time
import json
import hashlib
import subprocess
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from collections import deque, defaultdict

# 第三方库
try:
    import inotify.adapters
    import inotify.constants
    from rich.console import Console
    import yaml
    import orjson
except ImportError:
    print("请先安装依赖: pip install inotify rich pyyaml orjson")
    sys.exit(1)

console = Console()

# 路径配置
BASE_DIR = Path(__file__).parent.parent.parent
WORKFLOW_DIR = BASE_DIR / ".workflow"
CONFIG_FILE = WORKFLOW_DIR / "config.yml"
PHASE_FILE = BASE_DIR / ".phase" / "current"
TICKETS_DIR = BASE_DIR / ".tickets"
GATES_DIR = BASE_DIR / ".gates"
METRICS_FILE = WORKFLOW_DIR / "metrics.jsonl"
EVENT_LOG = WORKFLOW_DIR / "events.jsonl"

# 监听配置
WATCH_PATHS = {
    "docs": BASE_DIR / "docs",
    "src": BASE_DIR / "src",
    "tests": BASE_DIR / "tests",
    "tickets": TICKETS_DIR,
    "phase": PHASE_FILE.parent,
    "gates": GATES_DIR,
}

# 忽略的模式
IGNORE_PATTERNS = [
    "__pycache__",
    ".pyc",
    ".git",
    "node_modules",
    ".DS_Store",
    ".swp",
    ".tmp",
]


@dataclass
class FileEvent:
    """文件事件"""

    path: Path
    event_type: str  # CREATE, MODIFY, DELETE, MOVE
    timestamp: float
    phase: str

    def to_dict(self) -> dict:
        return {
            "path": str(self.path),
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "phase": self.phase,
        }


class EventDebouncer:
    """事件防抖器"""

    def __init__(self, window_ms: int = 100):
        self.window_ms = window_ms
        self.pending = {}
        self.lock = threading.Lock()

    def add(self, path: Path, event_type: str) -> bool:
        """添加事件，返回是否应该处理"""
        with self.lock:
            key = (str(path), event_type)
            now = time.time() * 1000

            if key in self.pending:
                last_time = self.pending[key]
                if now - last_time < self.window_ms:
                    # 在防抖窗口内，更新时间但不处理
                    self.pending[key] = now
                    return False

            self.pending[key] = now
            return True

    def cleanup(self):
        """清理过期的防抖记录"""
        with self.lock:
            now = time.time() * 1000
            expired = []
            for key, timestamp in self.pending.items():
                if now - timestamp > self.window_ms * 10:
                    expired.append(key)

            for key in expired:
                del self.pending[key]


class PhaseAwareWatcher:
    """阶段感知的文件监听器"""

    def __init__(self):
        self.config = self._load_config()
        self.debouncer = EventDebouncer(
            window_ms=self.config.get("watcher", {}).get("debounce_ms", 100)
        )
        self.current_phase = self._get_current_phase()
        self.event_queue = deque(maxlen=1000)
        self.running = False
        self.executor_path = WORKFLOW_DIR / "executor" / "executor.py"

        # 性能统计
        self.stats = {
            "events_total": 0,
            "events_processed": 0,
            "events_debounced": 0,
            "validations_triggered": 0,
            "phase_advances": 0,
        }

    def _load_config(self) -> dict:
        """加载配置"""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as f:
                return yaml.safe_load(f)
        return {}

    def _get_current_phase(self) -> str:
        """获取当前阶段"""
        if PHASE_FILE.exists():
            return PHASE_FILE.read_text().strip()
        return "P1"

    def _should_ignore(self, path: Path) -> bool:
        """检查是否应该忽略"""
        path_str = str(path)
        for pattern in IGNORE_PATTERNS:
            if pattern in path_str:
                return True
        return False

    def _get_phase_for_path(self, path: Path) -> Optional[str]:
        """根据文件路径判断所属阶段"""
        path_str = str(path.relative_to(BASE_DIR))

        # 根据路径白名单判断
        whitelist = self.config.get("path_whitelist", {})
        for phase, patterns in whitelist.items():
            for pattern in patterns:
                # 简化的匹配逻辑
                if pattern.replace("**", "").replace("*", "") in path_str:
                    return phase

        # 默认规则
        if "docs" in path_str:
            if "PLAN.md" in path_str:
                return "P1"
            elif "DESIGN.md" in path_str:
                return "P2"
            elif "REVIEW.md" in path_str:
                return "P6"
        elif "src" in path_str or "lib" in path_str:
            return "P3"
        elif "test" in path_str:
            return "P4"
        elif ".git" in path_str:
            return "P5"

        return None

    def _process_event(self, event: FileEvent):
        """处理文件事件"""
        self.stats["events_processed"] += 1

        # 写入事件日志
        with open(EVENT_LOG, "a") as f:
            f.write(orjson.dumps(event.to_dict()).decode() + "\n")

        # 判断是否需要触发验证
        if event.phase and event.phase == self.current_phase:
            self._trigger_validation(event.phase)

    def _trigger_validation(self, phase: str):
        """触发阶段验证"""
        self.stats["validations_triggered"] += 1

        try:
            # 调用Python执行器进行验证
            result = subprocess.run(
                [sys.executable, str(self.executor_path), "validate", "--phase", phase],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                console.print(f"[green]✅ Phase {phase} 验证通过[/green]")

                # 检查是否可以自动推进
                if self._should_auto_advance(phase):
                    self._try_advance_phase()
            else:
                console.print(f"[yellow]⚠️ Phase {phase} 验证未通过[/yellow]")

        except subprocess.TimeoutExpired:
            console.print(f"[red]❌ 验证超时[/red]")
        except Exception as e:
            console.print(f"[red]❌ 验证失败: {e}[/red]")

    def _should_auto_advance(self, phase: str) -> bool:
        """判断是否应该自动推进阶段"""
        # 根据配置判断
        auto_advance = self.config.get("workflow", {}).get("auto_advance", {})
        return auto_advance.get(phase, False)

    def _try_advance_phase(self):
        """尝试推进阶段"""
        self.stats["phase_advances"] += 1

        try:
            result = subprocess.run(
                [sys.executable, str(self.executor_path), "advance"],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                # 重新读取当前阶段
                self.current_phase = self._get_current_phase()
                console.print(f"[green]✅ 成功推进到 {self.current_phase}[/green]")

        except Exception as e:
            console.print(f"[red]❌ 推进失败: {e}[/red]")

    def _monitor_path(self, path: Path, label: str):
        """监听单个路径"""
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)

        i = inotify.adapters.InotifyTree(str(path))

        for event in i.event_gen(yield_nones=False):
            if not self.running:
                break

            (_, type_names, path_str, filename) = event

            if filename:
                full_path = Path(path_str) / filename
            else:
                full_path = Path(path_str)

            # 统计
            self.stats["events_total"] += 1

            # 忽略检查
            if self._should_ignore(full_path):
                continue

            # 防抖
            event_type = type_names[0] if type_names else "UNKNOWN"
            if not self.debouncer.add(full_path, event_type):
                self.stats["events_debounced"] += 1
                continue

            # 创建事件
            phase = self._get_phase_for_path(full_path)
            if phase:
                event = FileEvent(
                    path=full_path,
                    event_type=event_type,
                    timestamp=time.time(),
                    phase=phase,
                )

                self.event_queue.append(event)
                self._process_event(event)

    def start(self):
        """启动监听器"""
        self.running = True
        console.print("[cyan]🚀 Claude Enhancer 事件监听器启动[/cyan]")
        console.print(f"[dim]当前阶段: {self.current_phase}[/dim]")
        console.print(f"[dim]监听路径: {', '.join(WATCH_PATHS.keys())}[/dim]")

        # 启动监听线程
        threads = []
        for label, path in WATCH_PATHS.items():
            if path.exists():
                t = threading.Thread(
                    target=self._monitor_path, args=(path, label), daemon=True
                )
                t.start()
                threads.append(t)

        # 定期清理和报告
        try:
            while self.running:
                time.sleep(10)
                self.debouncer.cleanup()

                # 每分钟报告一次统计
                if (
                    self.stats["events_total"] % 100 == 0
                    and self.stats["events_total"] > 0
                ):
                    self._report_stats()

        except KeyboardInterrupt:
            console.print("\n[yellow]⚠️ 监听器停止[/yellow]")
            self.stop()

    def stop(self):
        """停止监听器"""
        self.running = False
        self._report_stats()

    def _report_stats(self):
        """报告统计信息"""
        console.print("\n[cyan]📊 监听器统计:[/cyan]")
        console.print(f"  总事件: {self.stats['events_total']}")
        console.print(f"  已处理: {self.stats['events_processed']}")
        console.print(f"  防抖过滤: {self.stats['events_debounced']}")
        console.print(f"  触发验证: {self.stats['validations_triggered']}")
        console.print(f"  阶段推进: {self.stats['phase_advances']}")

        # 写入metrics
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "component": "watcher",
            **self.stats,
        }

        with open(METRICS_FILE, "a") as f:
            f.write(orjson.dumps(metrics).decode() + "\n")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Claude Enhancer 事件监听器")
    parser.add_argument("--daemon", action="store_true", help="后台运行")
    parser.add_argument("--status", action="store_true", help="显示状态")

    args = parser.parse_args()

    if args.status:
        # 显示状态
        if EVENT_LOG.exists():
            # 读取最近的事件
            events = []
            with open(EVENT_LOG) as f:
                for line in f:
                    events.append(json.loads(line))

            if events:
                recent = events[-10:]
                console.print("[cyan]最近的文件事件:[/cyan]")
                for event in recent:
                    console.print(
                        f"  {event['timestamp']}: {event['event_type']} - {event['path']}"
                    )

        return

    # 启动监听器
    watcher = PhaseAwareWatcher()

    if args.daemon:
        # TODO: 实现守护进程模式
        console.print("[yellow]守护进程模式尚未实现[/yellow]")
    else:
        watcher.start()


if __name__ == "__main__":
    main()
