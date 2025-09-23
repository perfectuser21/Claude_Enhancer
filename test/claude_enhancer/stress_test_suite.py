#!/usr/bin/env python3
"""
Claude Enhancer 压力测试套件
高强度、高准确性的压力测试，确保系统在极限条件下的稳定性
"""

import time
import threading
import concurrent.futures
import subprocess
import psutil
import tempfile
import shutil
import json
import random
import signal
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, asdict
import queue
import multiprocessing


@dataclass
class StressTestResult:
    """压力测试结果"""

    test_name: str
    test_type: str
    duration: float
    total_operations: int
    successful_operations: int
    failed_operations: int
    operations_per_second: float
    peak_memory_mb: float
    peak_cpu_percent: float
    error_rate: float
    timestamp: str
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class SystemResourceMonitor:
    """系统资源实时监控"""

    def __init__(self, interval: float = 0.1):
        self.interval = interval
        self.monitoring = False
        self.metrics = {
            "cpu_percent": [],
            "memory_percent": [],
            "memory_mb": [],
            "disk_io_read": [],
            "disk_io_write": [],
            "network_io_sent": [],
            "network_io_recv": [],
            "process_count": [],
            "load_average": [],
        }
        self.monitor_thread = None

    def start_monitoring(self):
        """开始资源监控"""
        self.monitoring = True
        self.metrics = {key: [] for key in self.metrics.keys()}

        def monitor():
            prev_disk_io = psutil.disk_io_counters()
            prev_net_io = psutil.net_io_counters()

            while self.monitoring:
                try:
                    # CPU使用率
                    cpu_percent = psutil.cpu_percent(interval=None)
                    self.metrics["cpu_percent"].append(cpu_percent)

                    # 内存使用
                    memory = psutil.virtual_memory()
                    self.metrics["memory_percent"].append(memory.percent)
                    self.metrics["memory_mb"].append(memory.used / 1024 / 1024)

                    # 磁盘IO
                    current_disk_io = psutil.disk_io_counters()
                    if current_disk_io and prev_disk_io:
                        read_rate = (
                            current_disk_io.read_bytes - prev_disk_io.read_bytes
                        ) / self.interval
                        write_rate = (
                            current_disk_io.write_bytes - prev_disk_io.write_bytes
                        ) / self.interval
                        self.metrics["disk_io_read"].append(read_rate)
                        self.metrics["disk_io_write"].append(write_rate)
                        prev_disk_io = current_disk_io

                    # 网络IO
                    current_net_io = psutil.net_io_counters()
                    if current_net_io and prev_net_io:
                        sent_rate = (
                            current_net_io.bytes_sent - prev_net_io.bytes_sent
                        ) / self.interval
                        recv_rate = (
                            current_net_io.bytes_recv - prev_net_io.bytes_recv
                        ) / self.interval
                        self.metrics["network_io_sent"].append(sent_rate)
                        self.metrics["network_io_recv"].append(recv_rate)
                        prev_net_io = current_net_io

                    # 进程数量
                    process_count = len(psutil.pids())
                    self.metrics["process_count"].append(process_count)

                    # 系统负载
                    if hasattr(os, "getloadavg"):
                        load_avg = os.getloadavg()[0]
                        self.metrics["load_average"].append(load_avg)

                    time.sleep(self.interval)

                except Exception:
                    pass

        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self) -> Dict[str, float]:
        """停止监控并返回统计数据"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)

        stats = {}
        for key, values in self.metrics.items():
            if values:
                stats[f"{key}_avg"] = sum(values) / len(values)
                stats[f"{key}_max"] = max(values)
                stats[f"{key}_min"] = min(values)
                stats[f"{key}_samples"] = len(values)

        return stats


class HookStressTest:
    """Hook系统压力测试"""

    def __init__(self, claude_dir: str = "/home/xx/dev/Perfect21/.claude"):
        self.claude_dir = Path(claude_dir)
        self.hooks_dir = self.claude_dir / "hooks"

    def rapid_fire_hook_test(
        self, duration: float = 30.0, concurrent_hooks: int = 5
    ) -> StressTestResult:
        """快速连续Hook执行压力测试"""
        if not self.hooks_dir.exists():
            return self._create_error_result(
                "rapid_fire_hooks", "hooks directory not found"
            )

        # 找到可用的Hook文件
        available_hooks = [
            h
            for h in self.hooks_dir.glob("*.sh")
            if h.name
            in ["performance_monitor.sh", "error_handler.sh", "quality_gate.sh"]
        ]

        if not available_hooks:
            return self._create_error_result(
                "rapid_fire_hooks", "no suitable hooks found"
            )

        monitor = SystemResourceMonitor()
        monitor.start_monitoring()

        start_time = time.perf_counter()
        end_time = start_time + duration

        total_operations = 0
        successful_operations = 0
        failed_operations = 0

        def execute_hook_burst():
            nonlocal total_operations, successful_operations, failed_operations

            while time.perf_counter() < end_time:
                # 随机选择一个Hook
                hook = random.choice(available_hooks)

                try:
                    result = subprocess.run(
                        ["bash", str(hook), "--test"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        env={
                            "CLAUDE_TEST_MODE": "1",
                            "STRESS_TEST_MODE": "1",
                            "RAPID_FIRE_TEST": "1",
                        },
                    )

                    total_operations += 1
                    if result.returncode == 0:
                        successful_operations += 1
                    else:
                        failed_operations += 1

                except Exception:
                    total_operations += 1
                    failed_operations += 1

                # 短暂延迟，避免过度占用资源
                time.sleep(0.01)

        # 启动并发线程
        threads = []
        for _ in range(concurrent_hooks):
            thread = threading.Thread(target=execute_hook_burst)
            thread.start()
            threads.append(thread)

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        actual_duration = time.perf_counter() - start_time
        system_stats = monitor.stop_monitoring()

        operations_per_second = (
            total_operations / actual_duration if actual_duration > 0 else 0
        )
        error_rate = failed_operations / total_operations if total_operations > 0 else 0

        return StressTestResult(
            test_name="rapid_fire_hooks",
            test_type="concurrency",
            duration=actual_duration,
            total_operations=total_operations,
            successful_operations=successful_operations,
            failed_operations=failed_operations,
            operations_per_second=operations_per_second,
            peak_memory_mb=system_stats.get("memory_mb_max", 0),
            peak_cpu_percent=system_stats.get("cpu_percent_max", 0),
            error_rate=error_rate,
            timestamp=datetime.now().isoformat(),
            metadata={
                "concurrent_threads": concurrent_hooks,
                "available_hooks": len(available_hooks),
                "system_stats": system_stats,
            },
        )

    def hook_timeout_stress_test(self, iterations: int = 50) -> StressTestResult:
        """Hook超时压力测试"""
        if not self.hooks_dir.exists():
            return self._create_error_result(
                "hook_timeout_stress", "hooks directory not found"
            )

        monitor = SystemResourceMonitor()
        monitor.start_monitoring()

        start_time = time.perf_counter()

        total_operations = 0
        successful_operations = 0
        failed_operations = 0

        # 创建一个模拟慢速Hook
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".sh", delete=False
        ) as temp_hook:
            temp_hook.write(
                """#!/bin/bash
# 模拟慢速Hook
sleep_time=${1:-0.5}
sleep $sleep_time
echo "Slow hook completed after ${sleep_time}s"
exit 0
"""
            )
            temp_hook_path = Path(temp_hook.name)
            os.chmod(temp_hook_path, 0o755)

        try:
            for i in range(iterations):
                # 随机延迟时间，测试超时处理
                sleep_time = random.uniform(0.1, 2.0)

                try:
                    result = subprocess.run(
                        ["bash", str(temp_hook_path), str(sleep_time)],
                        capture_output=True,
                        text=True,
                        timeout=1.0,  # 1秒超时
                        env={"TIMEOUT_STRESS_TEST": "1"},
                    )

                    total_operations += 1
                    if result.returncode == 0:
                        successful_operations += 1
                    else:
                        failed_operations += 1

                except subprocess.TimeoutExpired:
                    total_operations += 1
                    failed_operations += 1  # 超时被认为是失败

                except Exception:
                    total_operations += 1
                    failed_operations += 1

        finally:
            # 清理临时文件
            if temp_hook_path.exists():
                temp_hook_path.unlink()

        actual_duration = time.perf_counter() - start_time
        system_stats = monitor.stop_monitoring()

        operations_per_second = (
            total_operations / actual_duration if actual_duration > 0 else 0
        )
        error_rate = failed_operations / total_operations if total_operations > 0 else 0

        return StressTestResult(
            test_name="hook_timeout_stress",
            test_type="timeout_handling",
            duration=actual_duration,
            total_operations=total_operations,
            successful_operations=successful_operations,
            failed_operations=failed_operations,
            operations_per_second=operations_per_second,
            peak_memory_mb=system_stats.get("memory_mb_max", 0),
            peak_cpu_percent=system_stats.get("cpu_percent_max", 0),
            error_rate=error_rate,
            timestamp=datetime.now().isoformat(),
            metadata={
                "iterations": iterations,
                "timeout_threshold": 1.0,
                "system_stats": system_stats,
            },
        )

    def memory_pressure_test(self, duration: float = 60.0) -> StressTestResult:
        """内存压力测试"""
        monitor = SystemResourceMonitor()
        monitor.start_monitoring()

        start_time = time.perf_counter()
        end_time = start_time + duration

        total_operations = 0
        successful_operations = 0
        failed_operations = 0

        # 内存压力生成器
        memory_blocks = []

        def memory_pressure_worker():
            nonlocal total_operations, successful_operations, failed_operations

            while time.perf_counter() < end_time:
                try:
                    # 分配内存块（每次10MB）
                    block_size = 10 * 1024 * 1024  # 10MB
                    memory_block = bytearray(block_size)

                    # 写入一些数据以确保内存真正被使用
                    for i in range(0, block_size, 4096):
                        memory_block[i] = random.randint(0, 255)

                    memory_blocks.append(memory_block)
                    total_operations += 1
                    successful_operations += 1

                    # 当内存块过多时，释放一些
                    if len(memory_blocks) > 50:  # 限制在500MB左右
                        memory_blocks.pop(0)

                    time.sleep(0.1)

                except Exception:
                    total_operations += 1
                    failed_operations += 1
                    time.sleep(0.1)

        # 同时运行Hook测试
        def hook_under_pressure():
            if not self.hooks_dir.exists():
                return

            available_hooks = list(self.hooks_dir.glob("*.sh"))[:3]  # 限制Hook数量

            while time.perf_counter() < end_time:
                if available_hooks:
                    hook = random.choice(available_hooks)
                    try:
                        subprocess.run(
                            ["bash", str(hook), "--test"],
                            capture_output=True,
                            text=True,
                            timeout=2,
                            env={"MEMORY_PRESSURE_TEST": "1"},
                        )
                    except Exception:
                        pass

                time.sleep(1)

        # 启动内存压力和Hook测试
        memory_thread = threading.Thread(target=memory_pressure_worker)
        hook_thread = threading.Thread(target=hook_under_pressure)

        memory_thread.start()
        hook_thread.start()

        memory_thread.join()
        hook_thread.join()

        # 清理内存
        memory_blocks.clear()

        actual_duration = time.perf_counter() - start_time
        system_stats = monitor.stop_monitoring()

        operations_per_second = (
            total_operations / actual_duration if actual_duration > 0 else 0
        )
        error_rate = failed_operations / total_operations if total_operations > 0 else 0

        return StressTestResult(
            test_name="memory_pressure",
            test_type="resource_stress",
            duration=actual_duration,
            total_operations=total_operations,
            successful_operations=successful_operations,
            failed_operations=failed_operations,
            operations_per_second=operations_per_second,
            peak_memory_mb=system_stats.get("memory_mb_max", 0),
            peak_cpu_percent=system_stats.get("cpu_percent_max", 0),
            error_rate=error_rate,
            timestamp=datetime.now().isoformat(),
            metadata={
                "peak_memory_blocks": len(memory_blocks),
                "system_stats": system_stats,
            },
        )

    def _create_error_result(self, test_name: str, error_msg: str) -> StressTestResult:
        """创建错误结果"""
        return StressTestResult(
            test_name=test_name,
            test_type="error",
            duration=0.0,
            total_operations=0,
            successful_operations=0,
            failed_operations=1,
            operations_per_second=0.0,
            peak_memory_mb=0.0,
            peak_cpu_percent=0.0,
            error_rate=1.0,
            timestamp=datetime.now().isoformat(),
            metadata={"error": error_msg},
        )


class FileSystemStressTest:
    """文件系统压力测试"""

    def __init__(self, claude_dir: str = "/home/xx/dev/Perfect21/.claude"):
        self.claude_dir = Path(claude_dir)

    def rapid_file_operations_test(self, duration: float = 30.0) -> StressTestResult:
        """快速文件操作压力测试"""
        monitor = SystemResourceMonitor()
        monitor.start_monitoring()

        start_time = time.perf_counter()
        end_time = start_time + duration

        total_operations = 0
        successful_operations = 0
        failed_operations = 0

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            def file_operations_worker():
                nonlocal total_operations, successful_operations, failed_operations

                file_counter = 0
                while time.perf_counter() < end_time:
                    try:
                        # 创建文件
                        file_path = temp_path / f"test_file_{file_counter}.txt"
                        file_content = f"Test content {file_counter}" * random.randint(
                            10, 100
                        )

                        file_path.write_text(file_content)
                        total_operations += 1

                        # 读取文件
                        content = file_path.read_text()
                        total_operations += 1

                        # 修改文件
                        file_path.write_text(content + " modified")
                        total_operations += 1

                        # 删除文件
                        file_path.unlink()
                        total_operations += 1

                        successful_operations += 4
                        file_counter += 1

                        # 避免创建过多文件
                        if file_counter % 10 == 0:
                            time.sleep(0.01)

                    except Exception:
                        failed_operations += 1
                        total_operations += 1

            # 启动多个文件操作线程
            threads = []
            for _ in range(3):
                thread = threading.Thread(target=file_operations_worker)
                thread.start()
                threads.append(thread)

            for thread in threads:
                thread.join()

        actual_duration = time.perf_counter() - start_time
        system_stats = monitor.stop_monitoring()

        operations_per_second = (
            total_operations / actual_duration if actual_duration > 0 else 0
        )
        error_rate = failed_operations / total_operations if total_operations > 0 else 0

        return StressTestResult(
            test_name="rapid_file_operations",
            test_type="file_system_stress",
            duration=actual_duration,
            total_operations=total_operations,
            successful_operations=successful_operations,
            failed_operations=failed_operations,
            operations_per_second=operations_per_second,
            peak_memory_mb=system_stats.get("memory_mb_max", 0),
            peak_cpu_percent=system_stats.get("cpu_percent_max", 0),
            error_rate=error_rate,
            timestamp=datetime.now().isoformat(),
            metadata={"concurrent_threads": 3, "system_stats": system_stats},
        )


class ProcessStressTest:
    """进程压力测试"""

    def __init__(self, claude_dir: str = "/home/xx/dev/Perfect21/.claude"):
        self.claude_dir = Path(claude_dir)

    def process_spawn_stress_test(
        self, duration: float = 30.0, max_processes: int = 20
    ) -> StressTestResult:
        """进程生成压力测试"""
        monitor = SystemResourceMonitor()
        monitor.start_monitoring()

        start_time = time.perf_counter()
        end_time = start_time + duration

        total_operations = 0
        successful_operations = 0
        failed_operations = 0

        active_processes = []

        def process_manager():
            nonlocal total_operations, successful_operations, failed_operations

            while time.perf_counter() < end_time:
                try:
                    # 清理已完成的进程
                    active_processes[:] = [
                        p for p in active_processes if p.poll() is None
                    ]

                    # 如果进程数量未达到上限，创建新进程
                    if len(active_processes) < max_processes:
                        # 创建简单的测试进程
                        process = subprocess.Popen(
                            ["bash", "-c", "sleep 0.5; echo 'test process'"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                        )
                        active_processes.append(process)
                        total_operations += 1
                        successful_operations += 1

                    time.sleep(0.1)

                except Exception:
                    total_operations += 1
                    failed_operations += 1

        # 运行进程管理器
        process_thread = threading.Thread(target=process_manager)
        process_thread.start()
        process_thread.join()

        # 清理剩余进程
        for process in active_processes:
            try:
                process.terminate()
                process.wait(timeout=2)
            except Exception:
                try:
                    process.kill()
                    process.wait(timeout=1)
                except Exception:
                    pass

        actual_duration = time.perf_counter() - start_time
        system_stats = monitor.stop_monitoring()

        operations_per_second = (
            total_operations / actual_duration if actual_duration > 0 else 0
        )
        error_rate = failed_operations / total_operations if total_operations > 0 else 0

        return StressTestResult(
            test_name="process_spawn_stress",
            test_type="process_stress",
            duration=actual_duration,
            total_operations=total_operations,
            successful_operations=successful_operations,
            failed_operations=failed_operations,
            operations_per_second=operations_per_second,
            peak_memory_mb=system_stats.get("memory_mb_max", 0),
            peak_cpu_percent=system_stats.get("cpu_percent_max", 0),
            error_rate=error_rate,
            timestamp=datetime.now().isoformat(),
            metadata={
                "max_concurrent_processes": max_processes,
                "final_active_processes": len(active_processes),
                "system_stats": system_stats,
            },
        )


class ComprehensiveStressTestSuite:
    """综合压力测试套件"""

    def __init__(self, claude_dir: str = "/home/xx/dev/Perfect21/.claude"):
        self.claude_dir = claude_dir
        self.hook_stress = HookStressTest(claude_dir)
        self.fs_stress = FileSystemStressTest(claude_dir)
        self.process_stress = ProcessStressTest(claude_dir)

    def run_full_stress_test_suite(self, test_duration: float = 60.0) -> Dict[str, Any]:
        """运行完整的压力测试套件"""
        print("💪 开始运行综合压力测试套件...")
        print("=" * 80)

        results = []

        # 记录系统初始状态
        initial_stats = {
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": psutil.virtual_memory().total / (1024**3),
            "memory_available_gb": psutil.virtual_memory().available / (1024**3),
            "disk_free_gb": psutil.disk_usage("/").free / (1024**3),
            "load_average": os.getloadavg() if hasattr(os, "getloadavg") else None,
        }

        # 1. Hook系统压力测试
        print("🔗 运行Hook系统压力测试...")

        print("  - 快速连续Hook执行测试...")
        rapid_fire_result = self.hook_stress.rapid_fire_hook_test(
            duration=test_duration / 4
        )
        results.append(rapid_fire_result)

        print("  - Hook超时压力测试...")
        timeout_result = self.hook_stress.hook_timeout_stress_test(iterations=20)
        results.append(timeout_result)

        print("  - 内存压力下的Hook测试...")
        memory_pressure_result = self.hook_stress.memory_pressure_test(
            duration=test_duration / 3
        )
        results.append(memory_pressure_result)

        # 2. 文件系统压力测试
        print("📁 运行文件系统压力测试...")
        fs_result = self.fs_stress.rapid_file_operations_test(
            duration=test_duration / 4
        )
        results.append(fs_result)

        # 3. 进程压力测试
        print("⚙️  运行进程压力测试...")
        process_result = self.process_stress.process_spawn_stress_test(
            duration=test_duration / 4
        )
        results.append(process_result)

        # 4. 综合分析
        print("📊 分析压力测试结果...")
        analysis = self._analyze_stress_results(results, initial_stats)

        # 5. 生成最终报告
        final_report = {
            "timestamp": datetime.now().isoformat(),
            "test_duration": test_duration,
            "initial_system_stats": initial_stats,
            "stress_test_results": [asdict(result) for result in results],
            "analysis": analysis,
            "recommendations": self._generate_stress_recommendations(results, analysis),
        }

        print("✅ 压力测试套件执行完成!")
        return final_report

    def _analyze_stress_results(
        self, results: List[StressTestResult], initial_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """分析压力测试结果"""
        analysis = {
            "overall_summary": {},
            "performance_metrics": {},
            "stress_tolerance": {},
            "resource_usage": {},
            "stability_assessment": {},
        }

        successful_results = [r for r in results if r.successful_operations > 0]

        if successful_results:
            # 总体摘要
            total_ops = sum(r.total_operations for r in results)
            total_successful = sum(r.successful_operations for r in results)
            total_failed = sum(r.failed_operations for r in results)

            analysis["overall_summary"] = {
                "total_tests": len(results),
                "successful_tests": len(successful_results),
                "total_operations": total_ops,
                "total_successful_operations": total_successful,
                "total_failed_operations": total_failed,
                "overall_success_rate": total_successful / total_ops
                if total_ops > 0
                else 0,
                "average_error_rate": sum(r.error_rate for r in results) / len(results),
            }

            # 性能指标
            ops_per_sec = [r.operations_per_second for r in successful_results]
            durations = [r.duration for r in successful_results]

            analysis["performance_metrics"] = {
                "avg_operations_per_second": sum(ops_per_sec) / len(ops_per_sec)
                if ops_per_sec
                else 0,
                "max_operations_per_second": max(ops_per_sec) if ops_per_sec else 0,
                "min_operations_per_second": min(ops_per_sec) if ops_per_sec else 0,
                "avg_test_duration": sum(durations) / len(durations)
                if durations
                else 0,
                "total_test_time": sum(durations),
            }

            # 资源使用分析
            peak_memory = [r.peak_memory_mb for r in successful_results]
            peak_cpu = [r.peak_cpu_percent for r in successful_results]

            analysis["resource_usage"] = {
                "peak_memory_usage_mb": max(peak_memory) if peak_memory else 0,
                "avg_memory_usage_mb": sum(peak_memory) / len(peak_memory)
                if peak_memory
                else 0,
                "peak_cpu_usage_percent": max(peak_cpu) if peak_cpu else 0,
                "avg_cpu_usage_percent": sum(peak_cpu) / len(peak_cpu)
                if peak_cpu
                else 0,
                "memory_efficiency": (
                    initial_stats.get("memory_available_gb", 1) * 1024
                )
                / (max(peak_memory) if peak_memory else 1),
            }

            # 压力容忍度评估
            error_rates = [r.error_rate for r in results]
            high_stress_tests = [
                r for r in results if r.test_type in ["concurrency", "resource_stress"]
            ]

            analysis["stress_tolerance"] = {
                "max_error_rate": max(error_rates) if error_rates else 0,
                "high_stress_success_rate": sum(
                    r.successful_operations for r in high_stress_tests
                )
                / sum(r.total_operations for r in high_stress_tests)
                if high_stress_tests
                else 0,
                "stability_score": 1 - (sum(error_rates) / len(error_rates))
                if error_rates
                else 0,
            }

            # 稳定性评估
            timeout_tests = [r for r in results if r.test_type == "timeout_handling"]
            concurrency_tests = [r for r in results if r.test_type == "concurrency"]

            analysis["stability_assessment"] = {
                "timeout_handling_score": sum(
                    r.successful_operations for r in timeout_tests
                )
                / sum(r.total_operations for r in timeout_tests)
                if timeout_tests
                else 0,
                "concurrency_stability": sum(
                    r.successful_operations for r in concurrency_tests
                )
                / sum(r.total_operations for r in concurrency_tests)
                if concurrency_tests
                else 0,
                "overall_stability_grade": self._calculate_stability_grade(analysis),
            }

        return analysis

    def _calculate_stability_grade(self, analysis: Dict[str, Any]) -> str:
        """计算稳定性等级"""
        try:
            overall_success = analysis["overall_summary"]["overall_success_rate"]
            stability_score = analysis["stress_tolerance"]["stability_score"]

            combined_score = (overall_success + stability_score) / 2

            if combined_score >= 0.95:
                return "A+ (Excellent)"
            elif combined_score >= 0.90:
                return "A (Very Good)"
            elif combined_score >= 0.80:
                return "B (Good)"
            elif combined_score >= 0.70:
                return "C (Fair)"
            elif combined_score >= 0.60:
                return "D (Poor)"
            else:
                return "F (Critical Issues)"
        except Exception:
            return "Unknown"

    def _generate_stress_recommendations(
        self, results: List[StressTestResult], analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成压力测试建议"""
        recommendations = []

        try:
            overall_success_rate = analysis["overall_summary"]["overall_success_rate"]
            avg_error_rate = analysis["overall_summary"]["average_error_rate"]
            stability_score = analysis["stress_tolerance"]["stability_score"]

            # 基于成功率的建议
            if overall_success_rate < 0.8:
                recommendations.append(
                    {
                        "category": "System Stability",
                        "priority": "CRITICAL",
                        "issue": f"压力测试整体成功率过低: {overall_success_rate:.1%}",
                        "recommendation": "需要立即调查系统稳定性问题，检查资源配置和错误处理机制",
                        "action_items": ["检查系统资源限制", "优化错误处理逻辑", "增加重试机制", "考虑增加系统资源"],
                    }
                )

            # 基于错误率的建议
            if avg_error_rate > 0.1:
                recommendations.append(
                    {
                        "category": "Error Handling",
                        "priority": "HIGH",
                        "issue": f"平均错误率较高: {avg_error_rate:.1%}",
                        "recommendation": "改善错误处理和恢复机制",
                        "action_items": ["分析常见错误模式", "实施更好的错误恢复策略", "增加监控和告警"],
                    }
                )

            # 基于资源使用的建议
            resource_usage = analysis.get("resource_usage", {})
            peak_memory = resource_usage.get("peak_memory_usage_mb", 0)
            peak_cpu = resource_usage.get("peak_cpu_usage_percent", 0)

            if peak_memory > 1000:  # 超过1GB
                recommendations.append(
                    {
                        "category": "Memory Management",
                        "priority": "MEDIUM",
                        "issue": f"峰值内存使用过高: {peak_memory:.1f}MB",
                        "recommendation": "优化内存使用，实施内存管理策略",
                        "action_items": ["识别内存泄漏", "优化数据结构", "实施内存池", "增加内存监控"],
                    }
                )

            if peak_cpu > 90:
                recommendations.append(
                    {
                        "category": "CPU Performance",
                        "priority": "MEDIUM",
                        "issue": f"峰值CPU使用率过高: {peak_cpu:.1f}%",
                        "recommendation": "优化CPU密集型操作，考虑负载均衡",
                        "action_items": ["识别CPU瓶颈", "优化算法复杂度", "实施异步处理", "考虑多进程架构"],
                    }
                )

            # 基于稳定性的建议
            if stability_score < 0.8:
                recommendations.append(
                    {
                        "category": "System Reliability",
                        "priority": "HIGH",
                        "issue": f"系统稳定性分数较低: {stability_score:.2f}",
                        "recommendation": "全面提升系统可靠性和容错能力",
                        "action_items": ["实施熔断器模式", "增加健康检查", "改进超时处理", "增加系统韧性"],
                    }
                )

        except Exception as e:
            recommendations.append(
                {
                    "category": "Analysis Error",
                    "priority": "LOW",
                    "issue": f"分析过程中出现错误: {str(e)}",
                    "recommendation": "检查分析逻辑并修复错误",
                }
            )

        return recommendations

    def save_stress_test_report(
        self, report: Dict[str, Any], filename: str = "stress_test_report.json"
    ) -> Path:
        """保存压力测试报告"""
        report_path = (
            Path(self.claude_dir).parent / "test" / "claude_enhancer" / filename
        )
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"📄 压力测试报告已保存到: {report_path}")
        return report_path


def main():
    """主函数"""
    try:
        suite = ComprehensiveStressTestSuite()

        # 运行压力测试（可以调整持续时间）
        test_duration = 120.0  # 2分钟的压力测试
        report = suite.run_full_stress_test_suite(test_duration)

        # 保存报告
        report_path = suite.save_stress_test_report(report)

        # 打印摘要
        print("\n" + "=" * 80)
        print("💪 压力测试摘要")
        print("=" * 80)

        summary = report.get("analysis", {}).get("overall_summary", {})
        if summary:
            print(f"总测试数量: {summary.get('total_tests', 0)}")
            print(f"成功测试: {summary.get('successful_tests', 0)}")
            print(f"总操作数: {summary.get('total_operations', 0)}")
            print(f"成功操作: {summary.get('total_successful_operations', 0)}")
            print(f"整体成功率: {summary.get('overall_success_rate', 0):.1%}")
            print(f"平均错误率: {summary.get('average_error_rate', 0):.1%}")

        # 性能指标
        perf_metrics = report.get("analysis", {}).get("performance_metrics", {})
        if perf_metrics:
            print(f"\n⚡ 性能指标:")
            print(f"平均操作/秒: {perf_metrics.get('avg_operations_per_second', 0):.1f}")
            print(f"最高操作/秒: {perf_metrics.get('max_operations_per_second', 0):.1f}")

        # 资源使用
        resource_usage = report.get("analysis", {}).get("resource_usage", {})
        if resource_usage:
            print(f"\n📊 资源使用:")
            print(f"峰值内存: {resource_usage.get('peak_memory_usage_mb', 0):.1f}MB")
            print(f"峰值CPU: {resource_usage.get('peak_cpu_usage_percent', 0):.1f}%")

        # 稳定性评估
        stability = report.get("analysis", {}).get("stability_assessment", {})
        if stability:
            print(f"\n🛡️  稳定性评估:")
            print(f"稳定性等级: {stability.get('overall_stability_grade', 'Unknown')}")

        # 建议
        recommendations = report.get("recommendations", [])
        if recommendations:
            print(f"\n💡 优化建议 ({len(recommendations)}条):")
            for rec in recommendations[:3]:  # 显示前3条最重要的建议
                print(f"  [{rec['priority']}] {rec['issue']}")

        print(f"\n📄 详细报告: {report_path}")
        return True

    except Exception as e:
        print(f"❌ 压力测试执行失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
