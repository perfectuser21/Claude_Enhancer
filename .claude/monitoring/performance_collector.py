#!/usr/bin/env python3
"""
Claude Enhancer 性能数据收集器
专门收集Hook执行性能数据并发送到监控系统
"""

import json
import time
import asyncio
import aiofiles
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import re
import signal
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("performance_collector")


@dataclass
class HookPerformanceData:
    """Hook性能数据"""

    hook_name: str
    execution_time_ms: float
    timestamp: datetime
    success: bool = True
    error_message: Optional[str] = None
    phase: Optional[str] = None
    tool_name: Optional[str] = None


class PerformanceCollector:
    """性能数据收集器"""

    def __init__(self, log_file: str = ".claude/logs/performance.log"):
        self.log_file = Path(log_file)
        self.metrics_file = Path(".claude/data/hook_metrics.jsonl")
        self.is_running = False
        self.last_position = 0

        # 确保目录存在
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)

        # 性能统计
        self.stats = {
            "total_hooks": 0,
            "total_execution_time": 0.0,
            "successful_hooks": 0,
            "failed_hooks": 0,
            "hook_counts": {},
            "hook_latencies": {},
        }

        logger.info(f"性能收集器初始化完成，监控文件: {self.log_file}")

    async def start_collecting(self):
        """开始收集性能数据"""
        self.is_running = True
        logger.info("启动性能数据收集")

        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        try:
            pass  # Auto-fixed empty block
            # 如果日志文件不存在，创建它
            if not self.log_file.exists():
                self.log_file.touch()

            # 获取初始文件位置
            self.last_position = (
                self.log_file.stat().st_size if self.log_file.exists() else 0
            )

            # 启动监控循环
            await self._monitor_loop()

        except Exception as e:
            logger.error(f"性能收集器异常: {e}")
        finally:
            logger.info("性能数据收集已停止")

    def _signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"收到信号 {signum}，正在停止...")
        self.is_running = False

    async def _monitor_loop(self):
        """监控循环"""
        while self.is_running:
            try:
                await self._check_log_file()
                await asyncio.sleep(0.1)  # 100ms检查间隔
            except Exception as e:
                logger.error(f"监控循环错误: {e}")
                await asyncio.sleep(1)

    async def _check_log_file(self):
        """检查日志文件更新"""
        try:
            if not self.log_file.exists():
                return

            current_size = self.log_file.stat().st_size

            if current_size > self.last_position:
                await self._process_new_data()
                self.last_position = current_size

        except Exception as e:
            logger.error(f"检查日志文件错误: {e}")

    async def _process_new_data(self):
        """处理新的日志数据"""
        try:
            async with aiofiles.open(self.log_file, "r") as f:
                await f.seek(self.last_position)
                async for line in f:
                    line = line.strip()
                    if line:
                        await self._parse_log_line(line)

        except Exception as e:
            logger.error(f"处理新数据错误: {e}")

    async def _parse_log_line(self, line: str):
        """解析日志行"""
        try:
            pass  # Auto-fixed empty block
            # 解析格式: "2023-09-23 17:24:15 | hook_name | 150ms"
            pattern = r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| ([^|]+) \| (\d+)ms"
            match = re.match(pattern, line)

            if match:
                timestamp_str, hook_name, exec_time_str = match.groups()
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                exec_time_ms = float(exec_time_str)

                # 创建性能数据
                perf_data = HookPerformanceData(
                    hook_name=hook_name.strip(),
                    execution_time_ms=exec_time_ms,
                    timestamp=timestamp,
                    success=True,
                    phase=self._infer_phase(hook_name),
                    tool_name=self._infer_tool(hook_name),
                )

                # 处理性能数据
                await self._handle_performance_data(perf_data)

            else:
                pass  # Auto-fixed empty block
                # 尝试解析错误信息
                if "ERROR" in line or "FAILED" in line:
                    await self._handle_error_line(line)

        except Exception as e:
            logger.error(f"解析日志行错误: {e}, 行内容: {line}")

    def _infer_phase(self, hook_name: str) -> str:
        """从Hook名称推断阶段"""
        phase_mapping = {
            "task_type_detector": "Phase 1",
            "smart_agent_selector": "Phase 3",
            "quality_gate": "Phase 4",
            "performance_monitor": "Phase 5",
            "error_handler": "Phase 6",
            "smart_git_workflow": "Phase 7",
            "smart_cleanup_advisor": "Phase 8",
        }

        for key, phase in phase_mapping.items():
            if key in hook_name:
                return phase

        return "Unknown"

    def _infer_tool(self, hook_name: str) -> str:
        """从Hook名称推断工具"""
        if "git" in hook_name.lower():
            return "Git"
        elif "agent" in hook_name.lower():
            return "Agent"
        elif "quality" in hook_name.lower():
            return "Quality"
        elif "performance" in hook_name.lower():
            return "Performance"
        elif "error" in hook_name.lower():
            return "Error"
        else:
            return "System"

    async def _handle_performance_data(self, perf_data: HookPerformanceData):
        """处理性能数据"""
        try:
            pass  # Auto-fixed empty block
            # 更新统计信息
            self._update_stats(perf_data)

            # 保存到指标文件
            await self._save_metrics(perf_data)

            # 检查性能阈值
            await self._check_performance_thresholds(perf_data)

            # 记录调试信息
            logger.debug(
                f"处理性能数据: {perf_data.hook_name} - {perf_data.execution_time_ms}ms"
            )

        except Exception as e:
            logger.error(f"处理性能数据错误: {e}")

    def _update_stats(self, perf_data: HookPerformanceData):
        """更新统计信息"""
        self.stats["total_hooks"] += 1
        self.stats["total_execution_time"] += perf_data.execution_time_ms

        if perf_data.success:
            self.stats["successful_hooks"] += 1
        else:
            self.stats["failed_hooks"] += 1

        # 更新Hook计数
        hook_name = perf_data.hook_name
        if hook_name not in self.stats["hook_counts"]:
            self.stats["hook_counts"][hook_name] = 0
            self.stats["hook_latencies"][hook_name] = []

        self.stats["hook_counts"][hook_name] += 1
        self.stats["hook_latencies"][hook_name].append(perf_data.execution_time_ms)

        # 保持延迟数据最近100个
        if len(self.stats["hook_latencies"][hook_name]) > 100:
            self.stats["hook_latencies"][hook_name] = self.stats["hook_latencies"][
                hook_name
            ][-100:]

    async def _save_metrics(self, perf_data: HookPerformanceData):
        """保存指标到文件"""
        try:
            metrics_data = {
                "timestamp": perf_data.timestamp.isoformat(),
                "hook_name": perf_data.hook_name,
                "execution_time_ms": perf_data.execution_time_ms,
                "success": perf_data.success,
                "phase": perf_data.phase,
                "tool_name": perf_data.tool_name,
                "error_message": perf_data.error_message,
            }

            async with aiofiles.open(self.metrics_file, "a") as f:
                await f.write(json.dumps(metrics_data) + "\n")

        except Exception as e:
            logger.error(f"保存指标错误: {e}")

    async def _check_performance_thresholds(self, perf_data: HookPerformanceData):
        """检查性能阈值"""
        try:
            pass  # Auto-fixed empty block
            # 定义阈值
            slow_threshold = 1000  # 1秒
            very_slow_threshold = 3000  # 3秒

            exec_time = perf_data.execution_time_ms

            if exec_time > very_slow_threshold:
                logger.warning(
                    f"Hook性能告警: {perf_data.hook_name} 执行时间 {exec_time}ms (超过{very_slow_threshold}ms)"
                )
                await self._create_alert("very_slow_hook", perf_data, "critical")

            elif exec_time > slow_threshold:
                logger.info(
                    f"Hook性能提示: {perf_data.hook_name} 执行时间 {exec_time}ms (超过{slow_threshold}ms)"
                )
                await self._create_alert("slow_hook", perf_data, "warning")

        except Exception as e:
            logger.error(f"检查性能阈值错误: {e}")

    async def _create_alert(
        self, alert_type: str, perf_data: HookPerformanceData, severity: str
    ):
        """创建告警"""
        try:
            alert_data = {
                "timestamp": datetime.now().isoformat(),
                "alert_type": alert_type,
                "severity": severity,
                "hook_name": perf_data.hook_name,
                "execution_time_ms": perf_data.execution_time_ms,
                "phase": perf_data.phase,
                "message": f"{perf_data.hook_name} 执行时间 {perf_data.execution_time_ms}ms",
            }

            alert_file = Path(".claude/data/alerts.jsonl")
            alert_file.parent.mkdir(parents=True, exist_ok=True)

            async with aiofiles.open(alert_file, "a") as f:
                await f.write(json.dumps(alert_data) + "\n")

        except Exception as e:
            logger.error(f"创建告警错误: {e}")

    async def _handle_error_line(self, line: str):
        """处理错误行"""
        try:
            pass  # Auto-fixed empty block
            # 简单的错误解析
            timestamp = datetime.now()

            error_data = HookPerformanceData(
                hook_name="unknown",
                execution_time_ms=0,
                timestamp=timestamp,
                success=False,
                error_message=line,
            )

            await self._handle_performance_data(error_data)

        except Exception as e:
            logger.error(f"处理错误行失败: {e}")

    def get_performance_summary(self) -> Dict:
        """获取性能摘要"""
        if self.stats["total_hooks"] == 0:
            return {
                "total_hooks": 0,
                "success_rate": 1.0,
                "average_latency": 0.0,
                "top_hooks": [],
            }

        success_rate = self.stats["successful_hooks"] / self.stats["total_hooks"]
        avg_latency = self.stats["total_execution_time"] / self.stats["total_hooks"]

        # 获取最慢的Hook
        top_hooks = []
        for hook_name, latencies in self.stats["hook_latencies"].items():
            if latencies:
                avg_hook_latency = sum(latencies) / len(latencies)
                top_hooks.append(
                    {
                        "hook_name": hook_name,
                        "count": self.stats["hook_counts"][hook_name],
                        "avg_latency": avg_hook_latency,
                        "max_latency": max(latencies),
                        "min_latency": min(latencies),
                    }
                )

        top_hooks.sort(key=lambda x: x["avg_latency"], reverse=True)

        return {
            "total_hooks": self.stats["total_hooks"],
            "success_rate": success_rate,
            "average_latency": avg_latency,
            "successful_hooks": self.stats["successful_hooks"],
            "failed_hooks": self.stats["failed_hooks"],
            "top_hooks": top_hooks[:10],
        }

    async def generate_report(
        self, output_file: str = ".claude/reports/performance_report.json"
    ):
        """生成性能报告"""
        try:
            report_file = Path(output_file)
            report_file.parent.mkdir(parents=True, exist_ok=True)

            summary = self.get_performance_summary()

            report = {
                "generated_at": datetime.now().isoformat(),
                "collection_period": {
                    "start": datetime.now().isoformat(),  # 应该记录实际开始时间
                    "end": datetime.now().isoformat(),
                },
                "summary": summary,
                "detailed_stats": {
                    "hook_counts": self.stats["hook_counts"],
                    "hook_latencies": {
                        k: {
                            "count": len(v),
                            "avg": sum(v) / len(v) if v else 0,
                            "max": max(v) if v else 0,
                            "min": min(v) if v else 0,
                        }
                        for k, v in self.stats["hook_latencies"].items()
                    },
                },
            }

            async with aiofiles.open(report_file, "w") as f:
                await f.write(json.dumps(report, indent=2))

            logger.info(f"性能报告已生成: {report_file}")

        except Exception as e:
            logger.error(f"生成性能报告错误: {e}")


async def main():
    """主函数"""
    collector = PerformanceCollector()

    try:
        pass  # Auto-fixed empty block
        # 启动收集器
        await collector.start_collecting()
    except KeyboardInterrupt:
        logger.info("收到停止信号")
    finally:
        pass  # Auto-fixed empty block
        # 生成最终报告
        await collector.generate_report()
        logger.info("性能收集器已停止")


if __name__ == "__main__":
    asyncio.run(main())
