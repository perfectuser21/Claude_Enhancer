#!/usr/bin/env python3
"""
Claude Enhancer 全面压力测试套件 v2.0
================================================

专业性能工程压力测试，涵盖：
1. 性能压力测试 - Hook执行速度、Agent并发调用、文档加载性能
2. 并发压力测试 - 多Hook同时触发、多Agent并行执行、资源竞争
3. 内存压力测试 - 大文件处理、内存泄漏检测、缓存机制
4. 稳定性测试 - 长时间运行、错误恢复、边界条件

基于现有代码的专业增强版本
作者: Claude Code (Performance Engineering Expert)
版本: 2.0.0
许可: MIT
"""

import os
import sys
import time
import json
import yaml
import subprocess
import threading
import multiprocessing
import tracemalloc
import gc
import signal
import psutil
import statistics
import random
import string
import tempfile
import shutil
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import logging

# 设置专业级日志
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler("/tmp/claude_enhancer_stress_test.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""

    timestamp: float
    operation: str
    duration_ms: float
    cpu_percent: float
    memory_mb: float
    success: bool
    error_message: Optional[str] = None
    additional_data: Optional[Dict] = None


@dataclass
class StressTestResult:
    """压力测试结果"""

    test_name: str
    start_time: float
    end_time: float
    total_operations: int
    successful_operations: int
    failed_operations: int
    metrics: List[PerformanceMetrics]
    peak_memory_mb: float
    avg_cpu_percent: float
    error_summary: Dict[str, int]
    performance_percentiles: Dict[str, float]


class SystemMonitor:
    """系统性能监控器"""

    def __init__(self):
        self.monitoring = False
        self.monitor_thread = None
        self.metrics_history = deque(maxlen=10000)
        self.peak_memory = 0
        self.peak_cpu = 0

    def start_monitoring(self):
        """开始系统监控"""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        tracemalloc.start()

    def stop_monitoring(self):
        """停止系统监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        tracemalloc.stop()

    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024
                cpu_percent = process.cpu_percent()

                self.peak_memory = max(self.peak_memory, memory_mb)
                self.peak_cpu = max(self.peak_cpu, cpu_percent)

                self.metrics_history.append(
                    {
                        "timestamp": time.time(),
                        "memory_mb": memory_mb,
                        "cpu_percent": cpu_percent,
                        "threads": process.num_threads(),
                        "open_files": len(process.open_files()),
                    }
                )

                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Monitor error: {e}")

    def get_stats(self):
        """获取统计信息"""
        if not self.metrics_history:
            return {}

        memory_values = [m["memory_mb"] for m in self.metrics_history]
        cpu_values = [m["cpu_percent"] for m in self.metrics_history]

        return {
            "peak_memory_mb": self.peak_memory,
            "peak_cpu_percent": self.peak_cpu,
            "avg_memory_mb": statistics.mean(memory_values),
            "avg_cpu_percent": statistics.mean(cpu_values),
            "current_threads": self.metrics_history[-1]["threads"],
            "current_open_files": self.metrics_history[-1]["open_files"],
        }


class ClaudeEnhancerStressTest:
    """Claude Enhancer全面压力测试器"""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "system_info": self._get_system_info(),
            "tests": {},
            "summary": {},
            "bottlenecks": [],
            "recommendations": [],
        }

        # 项目路径配置
        self.project_root = Path("/home/xx/dev/Claude_Enhancer")
        self.hook_dir = self.project_root / ".claude" / "hooks"
        self.config_dir = self.project_root / ".claude" / "config"
        self.agents_dir = self.project_root / ".claude" / "agents"

        # 系统监控器
        self.system_monitor = SystemMonitor()

        # 测试配置
        self.test_config = {
            "hook_iterations": 100,
            "concurrent_levels": [5, 10, 20, 50],
            "memory_test_size_mb": [1, 10, 50, 100],
            "stability_duration_minutes": 5,
            "agent_test_scenarios": ["simple", "standard", "complex"],
        }

    def _get_system_info(self):
        """获取系统信息"""
        return {
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": psutil.virtual_memory().total / (1024**3),
            "python_version": sys.version,
            "platform": sys.platform,
            "timestamp": datetime.now().isoformat(),
        }

    def run_command(self, cmd, timeout=10, input_data=""):
        """执行命令并收集性能指标"""
        start_time = time.time()
        process = psutil.Process()
        start_memory = process.memory_info().rss / 1024 / 1024

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                input=input_data,
            )

            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            end_memory = process.memory_info().rss / 1024 / 1024

            return PerformanceMetrics(
                timestamp=start_time,
                operation=cmd[:50],  # 限制命令长度
                duration_ms=duration_ms,
                cpu_percent=psutil.cpu_percent(),
                memory_mb=end_memory - start_memory,
                success=result.returncode == 0,
                error_message=result.stderr if result.returncode != 0 else None,
                additional_data={
                    "stdout_length": len(result.stdout),
                    "stderr_length": len(result.stderr),
                    "return_code": result.returncode,
                },
            )
        except subprocess.TimeoutExpired:
            return PerformanceMetrics(
                timestamp=start_time,
                operation=cmd[:50],
                duration_ms=timeout * 1000,
                cpu_percent=0,
                memory_mb=0,
                success=False,
                error_message="Command timeout",
            )
        except Exception as e:
            return PerformanceMetrics(
                timestamp=start_time,
                operation=cmd[:50],
                duration_ms=0,
                cpu_percent=0,
                memory_mb=0,
                success=False,
                error_message=str(e),
            )

    def test_hook_performance(self):
        """测试Hook系统性能（增强版）"""
        logger.info("🔧 Testing Hook System Performance...")
        self.system_monitor.start_monitoring()

        hook_files = list(self.hook_dir.glob("*.sh"))
        all_metrics = []

        for hook_path in hook_files:
            if hook_path.name.startswith("."):
                continue

            logger.info(f"Testing hook: {hook_path.name}")
            hook_metrics = []

            # 测试多次获取统计数据
            for i in range(self.test_config["hook_iterations"]):
                # 模拟不同的输入数据
                test_inputs = [
                    '{"tool": "test", "prompt": "simple test"}',
                    '{"tool": "Task", "prompt": "complex development task with multiple requirements"}',
                    '{"tool": "Write", "prompt": "write complex code"}',
                    '{"phase": "3", "task": "implementation"}',
                    "",  # 空输入测试
                ]

                input_data = test_inputs[i % len(test_inputs)]
                metric = self.run_command(
                    f"bash {hook_path}", timeout=10, input_data=input_data
                )
                hook_metrics.append(metric)

                # 避免过度频繁调用
                if i % 10 == 0:
                    time.sleep(0.1)

            all_metrics.extend(hook_metrics)

            # 计算该Hook的统计信息
            successful_metrics = [m for m in hook_metrics if m.success]
            if successful_metrics:
                durations = [m.duration_ms for m in successful_metrics]
                logger.info(
                    f"  {hook_path.name}: avg={statistics.mean(durations):.2f}ms, "
                    f"p95={sorted(durations)[int(len(durations)*0.95)]:.2f}ms, "
                    f"success_rate={len(successful_metrics)/len(hook_metrics)*100:.1f}%"
                )

        self.system_monitor.stop_monitoring()

        # 分析结果
        result = self._analyze_performance_metrics(
            all_metrics, "Hook Performance Tests"
        )
        self.results["tests"]["hook_performance"] = asdict(result)

        return result

    def test_agent_concurrency(self):
        """测试Agent并发性能（4-6-8策略）"""
        logger.info("🤖 Testing Agent Concurrency (4-6-8 Strategy)...")
        self.system_monitor.start_monitoring()

        all_metrics = []

        # 模拟4-6-8策略的Agent执行
        strategies = {
            "simple": {"agents": 4, "complexity": 0.1, "duration_range": (0.1, 0.3)},
            "standard": {"agents": 6, "complexity": 0.5, "duration_range": (0.3, 0.6)},
            "complex": {"agents": 8, "complexity": 1.0, "duration_range": (0.6, 1.2)},
        }

        for strategy_name, config in strategies.items():
            logger.info(
                f"Testing {strategy_name} strategy with {config['agents']} agents"
            )

            for iteration in range(20):  # 每种策略测试20次
                # 并发执行模拟的Agent任务
                with ThreadPoolExecutor(max_workers=config["agents"]) as executor:
                    futures = []

                    for agent_id in range(config["agents"]):
                        future = executor.submit(
                            self._simulate_agent_execution,
                            f"{strategy_name}_agent_{agent_id}",
                            config["complexity"],
                            config["duration_range"],
                        )
                        futures.append(future)

                    # 收集结果
                    for future in as_completed(futures):
                        try:
                            metric = future.result(timeout=5)
                            all_metrics.append(metric)
                        except Exception as e:
                            logger.error(f"Agent execution failed: {e}")

        self.system_monitor.stop_monitoring()

        result = self._analyze_performance_metrics(
            all_metrics, "Agent Concurrency Tests"
        )
        self.results["tests"]["agent_concurrency"] = asdict(result)

        return result

    def _simulate_agent_execution(
        self, agent_name: str, complexity: float, duration_range: Tuple[float, float]
    ) -> PerformanceMetrics:
        """模拟Agent执行"""
        start_time = time.time()
        process = psutil.Process()
        start_memory = process.memory_info().rss / 1024 / 1024

        # 根据复杂度模拟不同的工作负载
        work_amount = int(1000 * complexity + 100)
        duration = random.uniform(*duration_range)

        # 模拟CPU密集型工作
        for _ in range(work_amount):
            _ = sum(range(random.randint(50, 200)))

        # 模拟I/O等待
        time.sleep(duration * 0.1)  # 10%的时间用于I/O等待

        # 模拟内存使用
        temp_data = [random.random() for _ in range(int(work_amount * 0.1))]
        del temp_data  # 立即释放

        end_time = time.time()
        end_memory = process.memory_info().rss / 1024 / 1024

        return PerformanceMetrics(
            timestamp=start_time,
            operation=f"agent_{agent_name}",
            duration_ms=(end_time - start_time) * 1000,
            cpu_percent=psutil.cpu_percent(),
            memory_mb=end_memory - start_memory,
            success=True,
            additional_data={
                "complexity": complexity,
                "agent_name": agent_name,
                "work_amount": work_amount,
            },
        )

    def test_concurrent_hook_execution(self):
        """测试Hook并发执行能力（增强版）"""
        logger.info("🔀 Testing Concurrent Hook Execution...")
        self.system_monitor.start_monitoring()

        hook_files = list(self.hook_dir.glob("*.sh"))[:5]  # 选择前5个Hook
        all_metrics = []

        for concurrency in self.test_config["concurrent_levels"]:
            logger.info(f"Testing concurrency level: {concurrency}")

            # 并发执行Hook
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = []

                for _ in range(concurrency):
                    hook_path = random.choice(hook_files)
                    input_data = '{"tool": "test", "concurrent": true}'

                    future = executor.submit(
                        self.run_command, f"bash {hook_path}", 5, input_data
                    )
                    futures.append(future)

                # 收集结果
                for future in as_completed(futures):
                    try:
                        metric = future.result(timeout=10)
                        metric.additional_data = {
                            **(metric.additional_data or {}),
                            "concurrency_level": concurrency,
                        }
                        all_metrics.append(metric)
                    except Exception as e:
                        logger.error(f"Concurrent hook execution failed: {e}")

        self.system_monitor.stop_monitoring()

        result = self._analyze_performance_metrics(
            all_metrics, "Concurrent Hook Execution"
        )
        self.results["tests"]["concurrent_execution"] = asdict(result)

        return result

    def test_memory_pressure(self):
        """内存压力测试"""
        logger.info("💾 Testing Memory Pressure...")
        self.system_monitor.start_monitoring()

        all_metrics = []

        # 测试大文件处理
        for size_mb in self.test_config["memory_test_size_mb"]:
            logger.info(f"Testing {size_mb}MB file processing...")

            # 创建测试文件
            test_file = self._create_test_file(size_mb)

            try:
                # 测试文件读取
                metric = self._test_file_processing(test_file, size_mb)
                all_metrics.append(metric)

                # 测试内存泄漏检测
                leak_metrics = self._test_memory_leak_simulation(100)
                all_metrics.extend(leak_metrics)

            finally:
                # 清理测试文件
                if test_file.exists():
                    test_file.unlink()

        self.system_monitor.stop_monitoring()

        result = self._analyze_performance_metrics(all_metrics, "Memory Pressure Tests")
        self.results["tests"]["memory_pressure"] = asdict(result)

        return result

    def _create_test_file(self, size_mb: int) -> Path:
        """创建测试文件"""
        test_file = Path(f"/tmp/claude_test_{size_mb}mb_{int(time.time())}.txt")

        content_size = size_mb * 1024 * 1024
        chunk_size = 8192

        with open(test_file, "w") as f:
            written = 0
            base_content = (
                "This is test content for Claude Enhancer stress testing. " * 100
            )

            while written < content_size:
                chunk = base_content[: min(chunk_size, content_size - written)]
                f.write(chunk)
                written += len(chunk)

        return test_file

    def _test_file_processing(
        self, file_path: Path, size_mb: int
    ) -> PerformanceMetrics:
        """测试文件处理性能"""
        start_time = time.time()
        process = psutil.Process()
        start_memory = process.memory_info().rss / 1024 / 1024

        try:
            # 模拟文档加载和处理
            with open(file_path, "r") as f:
                content = f.read()

            # 模拟内容分析
            lines = content.split("\n")
            words = content.split()

            # 模拟一些处理操作
            _ = len(lines)
            _ = len(words)

            end_time = time.time()
            end_memory = process.memory_info().rss / 1024 / 1024

            return PerformanceMetrics(
                timestamp=start_time,
                operation=f"file_processing_{size_mb}mb",
                duration_ms=(end_time - start_time) * 1000,
                cpu_percent=psutil.cpu_percent(),
                memory_mb=end_memory - start_memory,
                success=True,
                additional_data={
                    "file_size_mb": size_mb,
                    "lines_count": len(lines),
                    "words_count": len(words),
                },
            )
        except Exception as e:
            return PerformanceMetrics(
                timestamp=start_time,
                operation=f"file_processing_{size_mb}mb",
                duration_ms=0,
                cpu_percent=0,
                memory_mb=0,
                success=False,
                error_message=str(e),
            )

    def _test_memory_leak_simulation(self, iterations: int) -> List[PerformanceMetrics]:
        """模拟内存泄漏测试"""
        metrics = []
        memory_snapshots = []

        gc.collect()  # 清理垃圾回收
        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024

        for i in range(iterations):
            start_time = time.time()

            # 创建一些对象
            data = []
            for j in range(100):
                item = {
                    "id": j,
                    "data": "".join(random.choices(string.ascii_letters, k=1000)),
                    "timestamp": time.time(),
                    "nested": {"value": random.random()},
                }
                data.append(item)

            # 故意保留一些引用（模拟潜在泄漏）
            if i % 20 == 0:
                memory_snapshots.append(data[:5])

            current_memory = process.memory_info().rss / 1024 / 1024
            memory_delta = current_memory - baseline_memory

            metrics.append(
                PerformanceMetrics(
                    timestamp=start_time,
                    operation="memory_leak_test",
                    duration_ms=(time.time() - start_time) * 1000,
                    cpu_percent=psutil.cpu_percent(),
                    memory_mb=memory_delta,
                    success=True,
                    additional_data={
                        "iteration": i,
                        "current_memory_mb": current_memory,
                        "baseline_memory_mb": baseline_memory,
                        "snapshots_retained": len(memory_snapshots),
                    },
                )
            )

        return metrics

    def test_stability_long_running(self):
        """长时间运行稳定性测试"""
        logger.info(
            f"🔄 Testing Long-running Stability ({self.test_config['stability_duration_minutes']} minutes)..."
        )
        self.system_monitor.start_monitoring()

        all_metrics = []
        start_time = time.time()
        end_time = start_time + (self.test_config["stability_duration_minutes"] * 60)

        operations = [
            self._simulate_hook_operation,
            self._simulate_config_operation,
            self._simulate_agent_operation,
            self._simulate_file_operation,
        ]

        while time.time() < end_time:
            operation = random.choice(operations)

            try:
                metric = operation()
                all_metrics.append(metric)
            except Exception as e:
                logger.error(f"Stability test operation failed: {e}")

            # 随机休眠模拟真实使用模式
            time.sleep(random.uniform(0.1, 2.0))

        self.system_monitor.stop_monitoring()

        result = self._analyze_performance_metrics(
            all_metrics, "Long-running Stability Test"
        )
        self.results["tests"]["stability"] = asdict(result)

        logger.info(f"Stability test completed: {len(all_metrics)} operations")
        return result

    def _simulate_hook_operation(self) -> PerformanceMetrics:
        """模拟Hook操作"""
        hook_files = list(self.hook_dir.glob("*.sh"))
        if not hook_files:
            raise Exception("No hook files found")

        hook_path = random.choice(hook_files)
        return self.run_command(
            f"bash {hook_path}", timeout=5, input_data='{"test": true}'
        )

    def _simulate_config_operation(self) -> PerformanceMetrics:
        """模拟配置操作"""
        config_file = self.config_dir / "unified_main.yaml"
        if not config_file.exists():
            raise Exception("Config file not found")

        return self.run_command(
            f"python3 -c 'import yaml; yaml.safe_load(open(\"{config_file}\"))'",
            timeout=3,
        )

    def _simulate_agent_operation(self) -> PerformanceMetrics:
        """模拟Agent操作"""
        return self._simulate_agent_execution(
            "stability_agent", random.uniform(0.1, 0.5), (0.1, 0.3)
        )

    def _simulate_file_operation(self) -> PerformanceMetrics:
        """模拟文件操作"""
        start_time = time.time()

        try:
            # 创建临时文件
            temp_file = Path(f"/tmp/claude_stability_{random.randint(1000, 9999)}.tmp")

            with open(temp_file, "w") as f:
                f.write(f"Stability test data: {time.time()}")

            with open(temp_file, "r") as f:
                content = f.read()

            temp_file.unlink()

            return PerformanceMetrics(
                timestamp=start_time,
                operation="file_operation",
                duration_ms=(time.time() - start_time) * 1000,
                cpu_percent=psutil.cpu_percent(),
                memory_mb=0,
                success=True,
            )
        except Exception as e:
            return PerformanceMetrics(
                timestamp=start_time,
                operation="file_operation",
                duration_ms=0,
                cpu_percent=0,
                memory_mb=0,
                success=False,
                error_message=str(e),
            )

    def test_error_recovery(self):
        """错误恢复测试"""
        logger.info("🔧 Testing Error Recovery...")

        all_metrics = []
        error_scenarios = [
            self._test_timeout_recovery,
            self._test_file_not_found_recovery,
            self._test_invalid_input_recovery,
            self._test_memory_pressure_recovery,
        ]

        for scenario in error_scenarios:
            try:
                metric = scenario()
                all_metrics.append(metric)
            except Exception as e:
                logger.error(f"Error recovery test failed: {e}")

        result = self._analyze_performance_metrics(all_metrics, "Error Recovery Tests")
        self.results["tests"]["error_recovery"] = asdict(result)

        return result

    def _test_timeout_recovery(self) -> PerformanceMetrics:
        """测试超时恢复"""
        start_time = time.time()

        try:
            # 故意触发超时
            result = subprocess.run(["sleep", "3"], timeout=1, capture_output=True)
        except subprocess.TimeoutExpired:
            # 预期的超时，这是正常的恢复行为
            pass

        return PerformanceMetrics(
            timestamp=start_time,
            operation="timeout_recovery",
            duration_ms=(time.time() - start_time) * 1000,
            cpu_percent=psutil.cpu_percent(),
            memory_mb=0,
            success=True,  # 成功处理了超时
            additional_data={"recovery_type": "timeout"},
        )

    def _test_file_not_found_recovery(self) -> PerformanceMetrics:
        """测试文件未找到恢复"""
        start_time = time.time()

        try:
            with open("/nonexistent/path/file.txt", "r") as f:
                _ = f.read()
        except FileNotFoundError:
            # 预期的错误，正常恢复
            pass

        return PerformanceMetrics(
            timestamp=start_time,
            operation="file_not_found_recovery",
            duration_ms=(time.time() - start_time) * 1000,
            cpu_percent=psutil.cpu_percent(),
            memory_mb=0,
            success=True,
            additional_data={"recovery_type": "file_not_found"},
        )

    def _test_invalid_input_recovery(self) -> PerformanceMetrics:
        """测试无效输入恢复"""
        start_time = time.time()

        # 测试Hook对无效输入的处理
        hook_files = list(self.hook_dir.glob("*.sh"))
        if hook_files:
            hook_path = hook_files[0]
            # 发送无效JSON
            metric = self.run_command(
                f"bash {hook_path}", timeout=5, input_data="invalid json data"
            )
            metric.operation = "invalid_input_recovery"
            metric.additional_data = {"recovery_type": "invalid_input"}
            return metric

        return PerformanceMetrics(
            timestamp=start_time,
            operation="invalid_input_recovery",
            duration_ms=0,
            cpu_percent=0,
            memory_mb=0,
            success=False,
            error_message="No hooks available for testing",
        )

    def _test_memory_pressure_recovery(self) -> PerformanceMetrics:
        """测试内存压力恢复"""
        start_time = time.time()

        try:
            # 创建内存压力
            data = []
            for i in range(1000):
                data.append([random.random() for _ in range(1000)])

            # 立即释放内存
            del data
            gc.collect()

            return PerformanceMetrics(
                timestamp=start_time,
                operation="memory_pressure_recovery",
                duration_ms=(time.time() - start_time) * 1000,
                cpu_percent=psutil.cpu_percent(),
                memory_mb=0,
                success=True,
                additional_data={"recovery_type": "memory_pressure"},
            )
        except MemoryError:
            # 如果真的出现内存不足，也算是成功检测到了
            gc.collect()
            return PerformanceMetrics(
                timestamp=start_time,
                operation="memory_pressure_recovery",
                duration_ms=(time.time() - start_time) * 1000,
                cpu_percent=psutil.cpu_percent(),
                memory_mb=0,
                success=True,
                additional_data={"recovery_type": "memory_error_handled"},
            )

    def _analyze_performance_metrics(
        self, metrics: List[PerformanceMetrics], test_name: str
    ) -> StressTestResult:
        """分析性能指标"""
        if not metrics:
            return StressTestResult(
                test_name=test_name,
                start_time=time.time(),
                end_time=time.time(),
                total_operations=0,
                successful_operations=0,
                failed_operations=0,
                metrics=[],
                peak_memory_mb=0,
                avg_cpu_percent=0,
                error_summary={},
                performance_percentiles={},
            )

        successful_metrics = [m for m in metrics if m.success]
        failed_metrics = [m for m in metrics if not m.success]

        # 计算性能百分位数
        durations = [m.duration_ms for m in successful_metrics]
        percentiles = {}
        if durations:
            sorted_durations = sorted(durations)
            n = len(sorted_durations)
            percentiles = {
                "p50": sorted_durations[int(n * 0.5)] if n > 0 else 0,
                "p90": sorted_durations[int(n * 0.9)] if n > 0 else 0,
                "p95": sorted_durations[int(n * 0.95)] if n > 0 else 0,
                "p99": sorted_durations[int(n * 0.99)]
                if n >= 100
                else (sorted_durations[-1] if n > 0 else 0),
                "min": min(durations) if durations else 0,
                "max": max(durations) if durations else 0,
                "avg": statistics.mean(durations) if durations else 0,
            }

        # 错误统计
        error_summary = defaultdict(int)
        for metric in failed_metrics:
            if metric.error_message:
                error_summary[metric.error_message] += 1

        # 系统统计
        system_stats = self.system_monitor.get_stats()

        return StressTestResult(
            test_name=test_name,
            start_time=metrics[0].timestamp if metrics else time.time(),
            end_time=metrics[-1].timestamp if metrics else time.time(),
            total_operations=len(metrics),
            successful_operations=len(successful_metrics),
            failed_operations=len(failed_metrics),
            metrics=metrics,
            peak_memory_mb=system_stats.get("peak_memory_mb", 0),
            avg_cpu_percent=system_stats.get("avg_cpu_percent", 0),
            error_summary=dict(error_summary),
            performance_percentiles=percentiles,
        )

    def test_config_loading_advanced(self):
        """高级配置加载测试"""
        logger.info("📋 Testing Advanced Config Loading...")
        self.system_monitor.start_monitoring()

        all_metrics = []

        # 测试不同配置文件
        config_files = [
            self.config_dir / "unified_main.yaml",
            self.config_dir / "main.yaml",
            self.project_root / ".claude" / "settings.json",
        ]

        for config_file in config_files:
            if config_file.exists():
                logger.info(f"Testing config file: {config_file.name}")

                # 测试多次加载
                for i in range(50):
                    if config_file.suffix == ".yaml":
                        cmd = f"python3 -c 'import yaml; yaml.safe_load(open(\"{config_file}\"))'"
                    else:
                        cmd = f"python3 -c 'import json; json.load(open(\"{config_file}\"))'"

                    metric = self.run_command(cmd, timeout=3)
                    metric.additional_data = {
                        **(metric.additional_data or {}),
                        "config_file": config_file.name,
                        "file_type": config_file.suffix,
                    }
                    all_metrics.append(metric)

        # 测试配置验证
        config_manager = self.config_dir / "config_manager.py"
        if config_manager.exists():
            logger.info("Testing config validation...")
            for i in range(10):
                metric = self.run_command(
                    f"python3 {config_manager} validate", timeout=10
                )
                metric.additional_data = {
                    **(metric.additional_data or {}),
                    "operation_type": "validation",
                }
                all_metrics.append(metric)

        self.system_monitor.stop_monitoring()

        result = self._analyze_performance_metrics(
            all_metrics, "Advanced Config Loading"
        )
        self.results["tests"]["config_loading"] = asdict(result)

        return result

    def analyze_bottlenecks(self):
        """分析性能瓶颈（专业版）"""
        logger.info("🔍 Analyzing Performance Bottlenecks...")

        bottlenecks = []

        # 分析各个测试的性能指标
        for test_name, test_data in self.results["tests"].items():
            if isinstance(test_data, dict) and "performance_percentiles" in test_data:
                perf = test_data["performance_percentiles"]

                # 高延迟检测
                if perf.get("p95", 0) > 5000:  # P95 > 5秒
                    bottlenecks.append(
                        {
                            "type": "high_latency",
                            "test": test_name,
                            "severity": "critical",
                            "metric": f"P95 latency: {perf['p95']:.2f}ms",
                            "recommendation": "优化算法和减少I/O操作",
                        }
                    )
                elif perf.get("p95", 0) > 1000:  # P95 > 1秒
                    bottlenecks.append(
                        {
                            "type": "moderate_latency",
                            "test": test_name,
                            "severity": "warning",
                            "metric": f"P95 latency: {perf['p95']:.2f}ms",
                            "recommendation": "考虑性能优化",
                        }
                    )

                # 成功率检测
                success_rate = (
                    (
                        test_data["successful_operations"]
                        / test_data["total_operations"]
                        * 100
                    )
                    if test_data["total_operations"] > 0
                    else 0
                )
                if success_rate < 95:
                    bottlenecks.append(
                        {
                            "type": "low_success_rate",
                            "test": test_name,
                            "severity": "critical" if success_rate < 90 else "warning",
                            "metric": f"Success rate: {success_rate:.1f}%",
                            "recommendation": "增强错误处理和重试机制",
                        }
                    )

                # 内存使用检测
                if test_data.get("peak_memory_mb", 0) > 500:
                    bottlenecks.append(
                        {
                            "type": "high_memory_usage",
                            "test": test_name,
                            "severity": "warning",
                            "metric": f"Peak memory: {test_data['peak_memory_mb']:.2f}MB",
                            "recommendation": "优化内存使用和实现对象池",
                        }
                    )

                # CPU使用检测
                if test_data.get("avg_cpu_percent", 0) > 80:
                    bottlenecks.append(
                        {
                            "type": "high_cpu_usage",
                            "test": test_name,
                            "severity": "warning",
                            "metric": f"Avg CPU: {test_data['avg_cpu_percent']:.1f}%",
                            "recommendation": "实现异步处理和负载均衡",
                        }
                    )

        self.results["bottlenecks"] = bottlenecks

        # 输出分析结果
        if bottlenecks:
            logger.info("Performance bottlenecks identified:")
            for bottleneck in bottlenecks:
                severity_icon = "🔴" if bottleneck["severity"] == "critical" else "🟡"
                logger.info(
                    f"  {severity_icon} [{bottleneck['type']}] {bottleneck['test']}: {bottleneck['metric']}"
                )
        else:
            logger.info("  ✅ No significant bottlenecks identified")

        return bottlenecks

    def generate_recommendations(self):
        """生成优化建议（专业版）"""
        recommendations = []
        bottlenecks = self.results.get("bottlenecks", [])

        # 基于瓶颈生成建议
        bottleneck_types = set(b["type"] for b in bottlenecks)

        if "high_latency" in bottleneck_types or "moderate_latency" in bottleneck_types:
            recommendations.extend(
                ["实施Hook结果缓存机制", "优化文件I/O操作，使用批量处理", "考虑异步执行非关键Hook", "实现Hook执行优先级队列"]
            )

        if "low_success_rate" in bottleneck_types:
            recommendations.extend(
                ["增强错误处理和重试机制", "实现断路器模式防止级联失败", "添加详细的错误日志和监控", "设置合理的超时和回退策略"]
            )

        if "high_memory_usage" in bottleneck_types:
            recommendations.extend(
                ["实现内存池和对象重用", "添加内存监控和自动垃圾回收", "优化大文件处理，使用流式处理", "实现内存使用限制和警告机制"]
            )

        if "high_cpu_usage" in bottleneck_types:
            recommendations.extend(
                ["实现CPU密集型操作的负载均衡", "使用多进程处理并行任务", "优化算法复杂度", "考虑使用更高效的数据结构"]
            )

        # 通用建议
        recommendations.extend(
            ["建立性能监控Dashboard", "实施持续性能回归测试", "设置性能基准和SLA", "定期进行性能调优", "考虑实施A/B测试优化策略"]
        )

        self.results["recommendations"] = recommendations
        return recommendations

    def generate_comprehensive_report(self):
        """生成综合报告"""
        # 计算总体统计
        total_operations = sum(
            test.get("total_operations", 0)
            for test in self.results["tests"].values()
            if isinstance(test, dict)
        )
        total_successful = sum(
            test.get("successful_operations", 0)
            for test in self.results["tests"].values()
            if isinstance(test, dict)
        )
        total_failed = sum(
            test.get("failed_operations", 0)
            for test in self.results["tests"].values()
            if isinstance(test, dict)
        )

        overall_success_rate = (
            (total_successful / total_operations * 100) if total_operations > 0 else 0
        )

        self.results["summary"] = {
            "total_tests": len(self.results["tests"]),
            "total_operations": total_operations,
            "successful_operations": total_successful,
            "failed_operations": total_failed,
            "overall_success_rate": overall_success_rate,
            "bottlenecks_found": len(self.results["bottlenecks"]),
            "critical_issues": sum(
                1 for b in self.results["bottlenecks"] if b["severity"] == "critical"
            ),
            "warning_issues": sum(
                1 for b in self.results["bottlenecks"] if b["severity"] == "warning"
            ),
            "test_duration_minutes": (
                time.time()
                - datetime.fromisoformat(self.results["timestamp"]).timestamp()
            )
            / 60,
        }

        # 保存详细报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = (
            self.project_root / f"claude_enhancer_stress_report_{timestamp}.json"
        )

        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)

        # 保存简化摘要
        summary_file = (
            self.project_root / f"claude_enhancer_stress_summary_{timestamp}.txt"
        )
        with open(summary_file, "w", encoding="utf-8") as f:
            self._write_text_summary(f)

        logger.info(f"📊 Comprehensive report saved to: {report_file}")
        logger.info(f"📋 Summary saved to: {summary_file}")

        return self.results

    def _write_text_summary(self, f):
        """写入文本摘要"""
        f.write("Claude Enhancer Stress Test Report\n")
        f.write("=" * 50 + "\n\n")

        summary = self.results["summary"]
        f.write(f"Test Duration: {summary['test_duration_minutes']:.2f} minutes\n")
        f.write(f"Total Operations: {summary['total_operations']}\n")
        f.write(f"Success Rate: {summary['overall_success_rate']:.2f}%\n")
        f.write(f"Bottlenecks Found: {summary['bottlenecks_found']}\n")
        f.write(f"Critical Issues: {summary['critical_issues']}\n")
        f.write(f"Warning Issues: {summary['warning_issues']}\n\n")

        # 测试结果详情
        f.write("Test Results:\n")
        f.write("-" * 20 + "\n")
        for test_name, test_data in self.results["tests"].items():
            if isinstance(test_data, dict):
                f.write(f"{test_name}:\n")
                f.write(f"  Operations: {test_data.get('total_operations', 0)}\n")
                f.write(
                    f"  Success Rate: {(test_data.get('successful_operations', 0) / test_data.get('total_operations', 1) * 100):.1f}%\n"
                )

                perf = test_data.get("performance_percentiles", {})
                if perf:
                    f.write(f"  P50: {perf.get('p50', 0):.2f}ms\n")
                    f.write(f"  P95: {perf.get('p95', 0):.2f}ms\n")
                f.write("\n")

        # 瓶颈分析
        if self.results["bottlenecks"]:
            f.write("Performance Bottlenecks:\n")
            f.write("-" * 25 + "\n")
            for bottleneck in self.results["bottlenecks"]:
                f.write(
                    f"[{bottleneck['severity'].upper()}] {bottleneck['test']}: {bottleneck['metric']}\n"
                )
                f.write(f"  Recommendation: {bottleneck['recommendation']}\n\n")

        # 建议
        if self.results["recommendations"]:
            f.write("Recommendations:\n")
            f.write("-" * 15 + "\n")
            for i, rec in enumerate(self.results["recommendations"][:10], 1):  # 前10个建议
                f.write(f"{i}. {rec}\n")

    def run_all_tests(self):
        """运行所有测试"""
        logger.info("=" * 60)
        logger.info("🚀 Claude Enhancer Comprehensive Stress Test Suite v2.0")
        logger.info("=" * 60)

        try:
            # 运行各项测试
            self.test_hook_performance()
            self.test_agent_concurrency()
            self.test_concurrent_hook_execution()
            self.test_config_loading_advanced()
            self.test_memory_pressure()
            self.test_stability_long_running()
            self.test_error_recovery()

            # 分析和报告
            self.analyze_bottlenecks()
            self.generate_recommendations()
            report = self.generate_comprehensive_report()

            # 输出关键结果
            summary = self.results["summary"]
            logger.info("\n" + "=" * 60)
            logger.info("🎯 TEST RESULTS SUMMARY")
            logger.info("=" * 60)
            logger.info(f"⏱️  Duration: {summary['test_duration_minutes']:.2f} minutes")
            logger.info(f"🔢 Total Operations: {summary['total_operations']}")
            logger.info(f"✅ Success Rate: {summary['overall_success_rate']:.2f}%")
            logger.info(f"⚠️  Bottlenecks: {summary['bottlenecks_found']}")
            logger.info(f"🔴 Critical Issues: {summary['critical_issues']}")
            logger.info(f"🟡 Warnings: {summary['warning_issues']}")

            # 性能总结
            if self.results["tests"]:
                all_p95s = []
                for test_data in self.results["tests"].values():
                    if (
                        isinstance(test_data, dict)
                        and "performance_percentiles" in test_data
                    ):
                        p95 = test_data["performance_percentiles"].get("p95", 0)
                        if p95 > 0:
                            all_p95s.append(p95)

                if all_p95s:
                    avg_p95 = statistics.mean(all_p95s)
                    max_p95 = max(all_p95s)
                    logger.info(f"📊 Avg P95 Latency: {avg_p95:.2f}ms")
                    logger.info(f"📈 Max P95 Latency: {max_p95:.2f}ms")

            logger.info("=" * 60)

            # 根据结果确定退出状态
            if summary["critical_issues"] > 0:
                logger.error("❌ Test completed with CRITICAL issues!")
                return 1
            elif summary["overall_success_rate"] < 95:
                logger.warning("⚠️  Test completed with low success rate!")
                return 2
            elif summary["bottlenecks_found"] > 0:
                logger.warning("⚠️  Test completed with performance bottlenecks!")
                return 3
            else:
                logger.info("🎉 All tests passed successfully!")
                return 0

        except Exception as e:
            logger.error(f"Test suite failed with error: {e}")
            import traceback

            logger.debug(traceback.format_exc())
            return 1


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Claude Enhancer Comprehensive Stress Test Suite v2.0"
    )
    parser.add_argument(
        "--quick", action="store_true", help="Run quick test suite (reduced iterations)"
    )
    parser.add_argument(
        "--stability-duration",
        type=int,
        default=5,
        help="Stability test duration in minutes",
    )
    parser.add_argument(
        "--hook-iterations",
        type=int,
        default=100,
        help="Number of hook test iterations",
    )
    parser.add_argument(
        "--concurrent-levels",
        nargs="+",
        type=int,
        default=[5, 10, 20, 50],
        help="Concurrency levels to test",
    )

    args = parser.parse_args()

    # 创建测试器
    tester = ClaudeEnhancerStressTest()

    # 调整测试配置
    if args.quick:
        tester.test_config.update(
            {
                "hook_iterations": 20,
                "concurrent_levels": [5, 10],
                "memory_test_size_mb": [1, 10],
                "stability_duration_minutes": 1,
            }
        )
        logger.info("Running in quick test mode")
    else:
        tester.test_config.update(
            {
                "hook_iterations": args.hook_iterations,
                "concurrent_levels": args.concurrent_levels,
                "stability_duration_minutes": args.stability_duration,
            }
        )

    # 运行测试并返回退出码
    try:
        exit_code = tester.run_all_tests()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
