#!/usr/bin/env python3
"""
实时性能监控仪表板
监控Claude Enhancer系统性能并提供实时优化建议
"""

import asyncio
import json
import time
import psutil
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import subprocess


@dataclass
class PerformanceMetrics:
    timestamp: str
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_hooks: int
    avg_response_time: float
    success_rate: float
    concurrent_jobs: int
    error_count: int


@dataclass
class OptimizationSuggestion:
    type: str
    priority: str  # high, medium, low
    message: str
    action: str
    estimated_improvement: str


class PerformanceMonitor:
    def __init__(self):
        self.metrics_history: List[PerformanceMetrics] = []
        self.cache_dir = Path("/tmp/.claude_perf_cache")
        self.cache_dir.mkdir(exist_ok=True)

        self.log_files = {
            "performance": self.cache_dir / "performance.log",
            "errors": self.cache_dir / "errors.log",
            "metrics": self.cache_dir / "metrics.log",
        }

        # 性能阈值
        self.thresholds = {
            "cpu_high": 70.0,
            "memory_high": 80.0,
            "disk_high": 90.0,
            "response_slow": 1000.0,  # ms
            "success_rate_low": 90.0,
            "error_rate_high": 5.0,
        }

        self.optimization_suggestions: List[OptimizationSuggestion] = []
        self.is_monitoring = False

    def collect_system_metrics(self) -> Dict:
        """收集系统性能指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=0.1)

            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # 磁盘使用率
            disk = psutil.disk_usage("/")
            disk_percent = disk.percent

            # 进程信息
            processes = list(psutil.process_iter(["pid", "name", "cmdline"]))
            claude_processes = [
                p
                for p in processes
                if any(
                    "claude" in str(item).lower() for item in p.info["cmdline"] or []
                )
            ]

            return {
                "cpu_usage": cpu_percent,
                "memory_usage": memory_percent,
                "disk_usage": disk_percent,
                "active_processes": len(claude_processes),
                "total_processes": len(processes),
            }
        except Exception as e:
            print(f"❌ 收集系统指标时出错: {e}")
            return {}

    def parse_performance_logs(self) -> Dict:
        """解析性能日志文件"""
        metrics = {
            "avg_response_time": 0.0,
            "total_requests": 0,
            "error_count": 0,
            "success_count": 0,
        }

        try:
            # 解析性能日志
            if self.log_files["performance"].exists():
                with open(self.log_files["performance"], "r") as f:
                    lines = f.readlines()[-100:]  # 只看最近100条

                response_times = []
                for line in lines:
                    if "|" in line and "ms" in line:
                        parts = line.strip().split("|")
                        if len(parts) >= 3:
                            time_part = parts[2].replace("ms", "")
                            try:
                                response_times.append(float(time_part))
                            except ValueError:
                                continue

                if response_times:
                    metrics["avg_response_time"] = sum(response_times) / len(
                        response_times
                    )
                    metrics["total_requests"] = len(response_times)

            # 解析错误日志
            if self.log_files["errors"].exists():
                with open(self.log_files["errors"], "r") as f:
                    lines = f.readlines()[-50:]  # 最近50条错误

                for line in lines:
                    if "ERROR" in line:
                        metrics["error_count"] += 1
                    elif "SUCCESS" in line:
                        metrics["success_count"] += 1

        except Exception as e:
            print(f"❌ 解析日志时出错: {e}")

        return metrics

    def calculate_success_rate(self, success_count: int, error_count: int) -> float:
        """计算成功率"""
        total = success_count + error_count
        if total == 0:
            return 100.0
        return (success_count / total) * 100.0

    def analyze_performance(
        self, metrics: PerformanceMetrics
    ) -> List[OptimizationSuggestion]:
        """分析性能并生成优化建议"""
        suggestions = []

        # CPU使用率过高
        if metrics.cpu_usage > self.thresholds["cpu_high"]:
            suggestions.append(
                OptimizationSuggestion(
                    type="cpu_optimization",
                    priority="high",
                    message=f"CPU使用率过高 ({metrics.cpu_usage:.1f}%)",
                    action="减少并发数量或优化计算密集型操作",
                    estimated_improvement="减少20-30%的CPU使用率",
                )
            )

        # 内存使用率过高
        if metrics.memory_usage > self.thresholds["memory_high"]:
            suggestions.append(
                OptimizationSuggestion(
                    type="memory_optimization",
                    priority="high",
                    message=f"内存使用率过高 ({metrics.memory_usage:.1f}%)",
                    action="清理缓存文件或增加内存限制",
                    estimated_improvement="释放10-20%的内存空间",
                )
            )

        # 响应时间过慢
        if metrics.avg_response_time > self.thresholds["response_slow"]:
            suggestions.append(
                OptimizationSuggestion(
                    type="response_optimization",
                    priority="medium",
                    message=f"平均响应时间过慢 ({metrics.avg_response_time:.0f}ms)",
                    action="启用缓存机制或优化脚本算法",
                    estimated_improvement="提升50-70%的响应速度",
                )
            )

        # 成功率过低
        if metrics.success_rate < self.thresholds["success_rate_low"]:
            suggestions.append(
                OptimizationSuggestion(
                    type="reliability_optimization",
                    priority="high",
                    message=f"成功率过低 ({metrics.success_rate:.1f}%)",
                    action="启用错误重试机制或修复失败的Hook",
                    estimated_improvement="提升成功率到95%以上",
                )
            )

        # 并发任务过多
        if metrics.concurrent_jobs > 10:
            suggestions.append(
                OptimizationSuggestion(
                    type="concurrency_optimization",
                    priority="medium",
                    message=f"并发任务过多 ({metrics.concurrent_jobs}个)",
                    action="限制最大并发数或实施任务队列",
                    estimated_improvement="提升系统稳定性",
                )
            )

        return suggestions

    def collect_metrics(self) -> PerformanceMetrics:
        """收集完整的性能指标"""
        system_metrics = self.collect_system_metrics()
        log_metrics = self.parse_performance_logs()

        # 计算成功率
        success_rate = self.calculate_success_rate(
            log_metrics.get("success_count", 0), log_metrics.get("error_count", 0)
        )

        return PerformanceMetrics(
            timestamp=datetime.now().isoformat(),
            cpu_usage=system_metrics.get("cpu_usage", 0),
            memory_usage=system_metrics.get("memory_usage", 0),
            disk_usage=system_metrics.get("disk_usage", 0),
            active_hooks=system_metrics.get("active_processes", 0),
            avg_response_time=log_metrics.get("avg_response_time", 0),
            success_rate=success_rate,
            concurrent_jobs=log_metrics.get("total_requests", 0),
            error_count=log_metrics.get("error_count", 0),
        )

    def display_dashboard(
        self, metrics: PerformanceMetrics, suggestions: List[OptimizationSuggestion]
    ):
        """显示实时仪表板"""
        # 清屏
        print("\033[2J\033[H")

        print("🚀 Claude Enhancer 实时性能监控")
        print("=" * 60)
        print(f"📅 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # 系统指标
        print("📊 系统性能指标:")
        print(
            f"  🖥️  CPU使用率:     {metrics.cpu_usage:6.1f}% {'🔴' if metrics.cpu_usage > 70 else '🟢'}"
        )
        print(
            f"  💾 内存使用率:     {metrics.memory_usage:6.1f}% {'🔴' if metrics.memory_usage > 80 else '🟢'}"
        )
        print(
            f"  💿 磁盘使用率:     {metrics.disk_usage:6.1f}% {'🔴' if metrics.disk_usage > 90 else '🟢'}"
        )
        print(
            f"  ⚡ 平均响应时间:   {metrics.avg_response_time:6.0f}ms {'🔴' if metrics.avg_response_time > 1000 else '🟢'}"
        )
        print(
            f"  ✅ 成功率:         {metrics.success_rate:6.1f}% {'🔴' if metrics.success_rate < 90 else '🟢'}"
        )
        print(f"  🔄 活跃Hook:       {metrics.active_hooks:6d}个")
        print(f"  📝 并发任务:       {metrics.concurrent_jobs:6d}个")
        print(f"  ❌ 错误计数:       {metrics.error_count:6d}个")
        print()

        # 优化建议
        if suggestions:
            print("💡 优化建议:")
            for i, suggestion in enumerate(suggestions[:5], 1):
                priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[
                    suggestion.priority
                ]
                print(f"  {i}. {priority_icon} {suggestion.message}")
                print(f"     🔧 建议: {suggestion.action}")
                print(f"     📈 预期: {suggestion.estimated_improvement}")
                print()
        else:
            print("✨ 系统运行良好，无需优化建议")
            print()

        # 历史趋势
        if len(self.metrics_history) > 1:
            print("📈 性能趋势 (最近5分钟):")
            recent_metrics = self.metrics_history[-10:]

            cpu_trend = (
                "上升"
                if recent_metrics[-1].cpu_usage > recent_metrics[0].cpu_usage
                else "下降"
            )
            memory_trend = (
                "上升"
                if recent_metrics[-1].memory_usage > recent_metrics[0].memory_usage
                else "下降"
            )

            print(f"  📊 CPU趋势: {cpu_trend}")
            print(f"  📊 内存趋势: {memory_trend}")
            print(f"  📊 数据点: {len(recent_metrics)}个")

    def save_metrics(self, metrics: PerformanceMetrics):
        """保存指标到文件"""
        try:
            metrics_file = self.cache_dir / "realtime_metrics.jsonl"
            with open(metrics_file, "a") as f:
                f.write(json.dumps(asdict(metrics)) + "\n")
        except Exception as e:
            print(f"❌ 保存指标时出错: {e}")

    async def monitor_loop(self):
        """主监控循环"""
        print("🚀 启动实时性能监控...")
        self.is_monitoring = True

        while self.is_monitoring:
            try:
                # 收集指标
                metrics = self.collect_metrics()
                self.metrics_history.append(metrics)

                # 保持历史记录在合理范围内
                if len(self.metrics_history) > 100:
                    self.metrics_history = self.metrics_history[-50:]

                # 分析性能
                suggestions = self.analyze_performance(metrics)
                self.optimization_suggestions = suggestions

                # 显示仪表板
                self.display_dashboard(metrics, suggestions)

                # 保存指标
                self.save_metrics(metrics)

                # 等待下次更新
                await asyncio.sleep(3)

            except KeyboardInterrupt:
                print("\n🛑 监控已停止")
                self.is_monitoring = False
                break
            except Exception as e:
                print(f"❌ 监控循环出错: {e}")
                await asyncio.sleep(5)

    def export_report(self, hours: int = 1) -> str:
        """导出性能报告"""
        report_file = (
            self.cache_dir
            / f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        # 读取最近的指标
        metrics_file = self.cache_dir / "realtime_metrics.jsonl"
        recent_metrics = []

        if metrics_file.exists():
            cutoff_time = datetime.now() - timedelta(hours=hours)

            with open(metrics_file, "r") as f:
                for line in f:
                    try:
                        metric = json.loads(line)
                        metric_time = datetime.fromisoformat(metric["timestamp"])
                        if metric_time > cutoff_time:
                            recent_metrics.append(metric)
                    except Exception:
                        continue

        # 生成报告
        report = {
            "report_generated": datetime.now().isoformat(),
            "time_range_hours": hours,
            "total_metrics": len(recent_metrics),
            "summary": {
                "avg_cpu": sum(m["cpu_usage"] for m in recent_metrics)
                / len(recent_metrics)
                if recent_metrics
                else 0,
                "avg_memory": sum(m["memory_usage"] for m in recent_metrics)
                / len(recent_metrics)
                if recent_metrics
                else 0,
                "avg_response_time": sum(m["avg_response_time"] for m in recent_metrics)
                / len(recent_metrics)
                if recent_metrics
                else 0,
                "avg_success_rate": sum(m["success_rate"] for m in recent_metrics)
                / len(recent_metrics)
                if recent_metrics
                else 0,
                "total_errors": sum(m["error_count"] for m in recent_metrics),
            },
            "optimization_suggestions": [
                asdict(s) for s in self.optimization_suggestions
            ],
            "raw_metrics": recent_metrics,
        }

        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        print(f"📄 性能报告已导出: {report_file}")
        return str(report_file)


def main():
    import sys

    monitor = PerformanceMonitor()

    if len(sys.argv) > 1 and sys.argv[1] == "report":
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        monitor.export_report(hours)
    else:
        try:
            asyncio.run(monitor.monitor_loop())
        except KeyboardInterrupt:
            print("\n👋 监控已停止")


if __name__ == "__main__":
    main()
