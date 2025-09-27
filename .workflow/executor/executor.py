#!/usr/bin/env python3
"""
Claude Enhancer Python执行器
替代Shell脚本，提供高性能Gate验证和缓存机制
"""

import os
import sys
import json
import time
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import yaml

# 第三方库（需要pip install）
try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import track
    from pydantic import BaseModel
    import orjson
except ImportError:
    print("请先安装依赖: pip install rich pydantic orjson pyyaml")
    sys.exit(1)

console = Console()

# 路径配置
BASE_DIR = Path(__file__).parent.parent.parent
WORKFLOW_DIR = BASE_DIR / ".workflow"
CONFIG_FILE = WORKFLOW_DIR / "config.yml"
GATES_FILE = WORKFLOW_DIR / "gates.yml"
PHASE_FILE = BASE_DIR / ".phase" / "current"
GATES_DIR = BASE_DIR / ".gates"
TICKETS_DIR = BASE_DIR / ".tickets"
LIMITS_DIR = BASE_DIR / ".limits"
CACHE_DIR = WORKFLOW_DIR / "executor" / "cache"
METRICS_FILE = WORKFLOW_DIR / "metrics.jsonl"

# 确保目录存在
for dir_path in [GATES_DIR, TICKETS_DIR, LIMITS_DIR, CACHE_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


@dataclass
class ValidationResult:
    """验证结果"""

    phase: str
    passed: bool
    duration_ms: float
    cache_hit: bool
    failures: List[str]
    timestamp: str = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class CacheManager:
    """缓存管理器"""

    def __init__(self, cache_dir: Path = CACHE_DIR):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(
        self, phase: str, ticket: str = "", files: List[Path] = None
    ) -> str:
        """生成缓存键"""
        if files:
            # 计算文件内容的哈希
            hasher = hashlib.sha256()
            for file_path in sorted(files):
                if file_path.exists():
                    hasher.update(file_path.read_bytes())
            file_hash = hasher.hexdigest()[:16]
        else:
            file_hash = "no_files"

        return f"{phase}:{ticket}:{file_hash}"

    def get(
        self, phase: str, ticket: str = "", files: List[Path] = None
    ) -> Optional[ValidationResult]:
        """获取缓存"""
        cache_key = self._get_cache_key(phase, ticket, files)
        cache_file = self.cache_dir / f"kv-{cache_key}.json"

        if cache_file.exists():
            # 检查TTL（5分钟）
            if time.time() - cache_file.stat().st_mtime < 300:
                try:
                    data = orjson.loads(cache_file.read_bytes())
                    return ValidationResult(**data)
                except Exception:
                    pass
        return None

    def set(
        self,
        result: ValidationResult,
        phase: str,
        ticket: str = "",
        files: List[Path] = None,
    ):
        """设置缓存"""
        cache_key = self._get_cache_key(phase, ticket, files)
        cache_file = self.cache_dir / f"kv-{cache_key}.json"

        cache_file.write_bytes(orjson.dumps(asdict(result)))


class PhaseValidator:
    """阶段验证器"""

    def __init__(self):
        self.config = self._load_config()
        self.gates = self._load_gates()
        self.cache = CacheManager()

    def _load_config(self) -> dict:
        """加载配置"""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as f:
                return yaml.safe_load(f)
        return {}

    def _load_gates(self) -> dict:
        """加载Gates定义"""
        if GATES_FILE.exists():
            with open(GATES_FILE) as f:
                return yaml.safe_load(f)
        return {}

    def get_current_phase(self) -> str:
        """获取当前阶段"""
        if PHASE_FILE.exists():
            return PHASE_FILE.read_text().strip()
        return "P1"

    def validate_phase(
        self, phase: str = None, use_cache: bool = True
    ) -> ValidationResult:
        """验证阶段Gates"""
        start_time = time.perf_counter()

        if not phase:
            phase = self.get_current_phase()

        # 有效阶段检查
        valid_phases = ["P1", "P2", "P3", "P4", "P5", "P6"]
        if phase not in valid_phases:
            return ValidationResult(
                phase=phase,
                passed=False,
                duration_ms=(time.perf_counter() - start_time) * 1000,
                cache_hit=False,
                failures=[f"无效的阶段: {phase}"],
            )

        # 获取相关文件列表
        phase_files = self._get_phase_files(phase)

        # 尝试缓存
        if use_cache:
            cached = self.cache.get(phase, files=phase_files)
            if cached:
                cached.cache_hit = True
                cached.duration_ms = (time.perf_counter() - start_time) * 1000
                self._write_metrics(cached)
                return cached

        # 执行验证
        failures = []
        phase_gates = self.gates.get("phases", {}).get(phase, {}).get("gates", [])

        for gate in phase_gates:
            if not self._check_gate(phase, gate):
                failures.append(f"Gate失败: {gate.get('name', 'unknown')}")

        # 构建结果
        result = ValidationResult(
            phase=phase,
            passed=len(failures) == 0,
            duration_ms=(time.perf_counter() - start_time) * 1000,
            cache_hit=False,
            failures=failures,
        )

        # 写入缓存
        if use_cache and result.passed:
            self.cache.set(result, phase, files=phase_files)

        # 写入metrics
        self._write_metrics(result)

        return result

    def _get_phase_files(self, phase: str) -> List[Path]:
        """获取阶段相关文件"""
        files = []
        whitelist = self.config.get("path_whitelist", {}).get(phase, [])

        for pattern in whitelist:
            # 转换为Path并查找匹配文件
            for path in BASE_DIR.glob(pattern):
                if path.is_file():
                    files.append(path)

        return files

    def _check_gate(self, phase: str, gate: dict) -> bool:
        """检查单个Gate"""
        gate_type = gate.get("type", "")

        if gate_type == "file_exists":
            path = BASE_DIR / gate.get("path", "")
            return path.exists()

        elif gate_type == "file_contains":
            path = BASE_DIR / gate.get("path", "")
            pattern = gate.get("pattern", "")
            if path.exists():
                content = path.read_text()
                return pattern in content
            return False

        elif gate_type == "task_count":
            min_count = gate.get("min", 1)
            path = BASE_DIR / gate.get("path", "docs/PLAN.md")
            if path.exists():
                content = path.read_text()
                # 简单计数：数字开头的行
                tasks = len(
                    [
                        l
                        for l in content.split("\n")
                        if l.strip() and l.strip()[0].isdigit()
                    ]
                )
                return tasks >= min_count
            return False

        elif gate_type == "test_pass":
            # 运行测试命令
            cmd = gate.get("command", "")
            if cmd:
                try:
                    result = subprocess.run(
                        cmd, shell=True, capture_output=True, timeout=30
                    )
                    return result.returncode == 0
                except Exception:
                    return False

        return True

    def _write_metrics(self, result: ValidationResult):
        """写入性能指标"""
        metrics = {
            "timestamp": result.timestamp,
            "phase": result.phase,
            "validate_ms": result.duration_ms,
            "cache_hit": result.cache_hit,
            "passed": result.passed,
            "failures_count": len(result.failures),
        }

        with open(METRICS_FILE, "a") as f:
            f.write(orjson.dumps(metrics).decode() + "\n")

    def advance_phase(self) -> bool:
        """推进到下一阶段"""
        current = self.get_current_phase()

        # 验证当前阶段
        result = self.validate_phase(current)
        if not result.passed:
            console.print(f"[red]❌ 当前阶段 {current} 验证失败，无法推进[/red]")
            for failure in result.failures:
                console.print(f"  • {failure}")
            return False

        # 阶段映射
        phase_order = ["P1", "P2", "P3", "P4", "P5", "P6"]
        try:
            current_idx = phase_order.index(current)
            if current_idx < len(phase_order) - 1:
                next_phase = phase_order[current_idx + 1]

                # 写入新阶段
                PHASE_FILE.write_text(next_phase)

                # 创建Gate标记
                gate_file = GATES_DIR / f"{current_idx + 1:02d}.ok"
                gate_file.touch()

                console.print(f"[green]✅ 成功推进: {current} → {next_phase}[/green]")
                return True
            else:
                console.print(f"[yellow]已在最后阶段 {current}[/yellow]")
        except ValueError:
            console.print(f"[red]无效阶段 {current}[/red]")

        return False


class TicketManager:
    """工单管理器"""

    def __init__(self):
        self.config = (
            yaml.safe_load(CONFIG_FILE.read_text()) if CONFIG_FILE.exists() else {}
        )
        self.max_active = self.config.get("tickets", {}).get("max_active", 8)

    def get_active_tickets(self) -> List[str]:
        """获取活跃工单"""
        tickets = []
        if TICKETS_DIR.exists():
            for ticket_file in TICKETS_DIR.glob("*.todo"):
                tickets.append(ticket_file.stem)
        return tickets

    def can_create_ticket(self) -> bool:
        """检查是否可以创建新工单"""
        return len(self.get_active_tickets()) < self.max_active


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Claude Enhancer Python执行器")
    parser.add_argument(
        "command", choices=["validate", "advance", "status", "cache-stats"]
    )
    parser.add_argument("--phase", help="指定阶段")
    parser.add_argument("--no-cache", action="store_true", help="禁用缓存")

    args = parser.parse_args()

    validator = PhaseValidator()

    if args.command == "validate":
        result = validator.validate_phase(args.phase, use_cache=not args.no_cache)

        # 显示结果
        if result.passed:
            console.print(f"[green]✅ 阶段 {result.phase} 验证通过[/green]")
        else:
            console.print(f"[red]❌ 阶段 {result.phase} 验证失败[/red]")
            for failure in result.failures:
                console.print(f"  • {failure}")

        console.print(
            f"[dim]耗时: {result.duration_ms:.2f}ms, 缓存: {'命中' if result.cache_hit else '未命中'}[/dim]"
        )

        sys.exit(0 if result.passed else 1)

    elif args.command == "advance":
        success = validator.advance_phase()
        sys.exit(0 if success else 1)

    elif args.command == "status":
        current_phase = validator.get_current_phase()
        ticket_mgr = TicketManager()
        active_tickets = ticket_mgr.get_active_tickets()

        # 创建表格
        table = Table(title="Claude Enhancer 状态")
        table.add_column("项目", style="cyan")
        table.add_column("值", style="green")

        table.add_row("当前阶段", current_phase)
        table.add_row("活跃工单", str(len(active_tickets)))
        table.add_row("工单上限", str(ticket_mgr.max_active))

        # 添加Gates状态
        gates_count = len(list(GATES_DIR.glob("*.ok")))
        table.add_row("完成Gates", f"{gates_count}/6")

        console.print(table)

    elif args.command == "cache-stats":
        cache_files = list(CACHE_DIR.glob("kv-*.json"))
        total_size = sum(f.stat().st_size for f in cache_files) / 1024 / 1024

        console.print(f"[cyan]缓存统计:[/cyan]")
        console.print(f"  文件数: {len(cache_files)}")
        console.print(f"  总大小: {total_size:.2f} MB")

        # 最近的缓存命中率
        if METRICS_FILE.exists():
            recent_metrics = []
            with open(METRICS_FILE) as f:
                for line in f:
                    recent_metrics.append(json.loads(line))

            if recent_metrics:
                recent_100 = recent_metrics[-100:]
                hits = sum(1 for m in recent_100 if m.get("cache_hit"))
                console.print(f"  最近100次命中率: {hits}%")


if __name__ == "__main__":
    main()
