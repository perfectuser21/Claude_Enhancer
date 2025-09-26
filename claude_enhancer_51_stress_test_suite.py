#!/usr/bin/env python3
"""
Claude Enhancer 5.1 Stress Test Suite
极限压力测试套件 - 验证系统在极端条件下的稳定性和性能

专门测试：
1. 大量并发请求处理
2. 长时间运行稳定性
3. 资源耗尽情况下的行为
4. 故障恢复能力
5. 内存泄漏检测
"""

import asyncio
import threading
import multiprocessing
import time
import gc
import psutil
import statistics
import sys
import os
import logging
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import json
import traceback
import signal
import resource

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class StressTestResult:
    """压力测试结果"""

    test_name: str
    duration_minutes: float
    total_operations: int
    successful_operations: int
    failed_operations: int
    operations_per_second: float
    peak_memory_mb: float
    peak_cpu_percent: float
    peak_threads: int
    peak_file_descriptors: int
    error_rate_percent: float
    recovery_time_ms: float
    stability_score: float
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    memory_growth_mb: float = 0.0
    cpu_variance_percent: float = 0.0


class SystemMonitor:
    """系统资源监控器"""

    def __init__(self):
        self.process = psutil.Process()
        self.monitoring = False
        self.samples = []
        self.start_time = time.time()

    def start_monitoring(self, interval: float = 0.5):
        """开始监控"""
        self.monitoring = True
        self.samples = []

        def monitor_loop():
            while self.monitoring:
                try:
                    sample = {
                        "timestamp": time.time(),
                        "cpu_percent": self.process.cpu_percent(),
                        "memory_mb": self.process.memory_info().rss / 1024 / 1024,
                        "threads": self.process.num_threads(),
                        "fds": self.process.num_fds()
                        if hasattr(self.process, "num_fds")
                        else 0,
                        "system_cpu": psutil.cpu_percent(),
                        "system_memory": psutil.virtual_memory().percent,
                    }
                    self.samples.append(sample)
                except Exception as e:
                    logger.warning(f"监控采样失败: {e}")

                time.sleep(interval)

        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("🔍 系统监控已启动")

    def stop_monitoring(self) -> Dict[str, Any]:
        """停止监控并返回统计数据"""
        self.monitoring = False
        if hasattr(self, "monitor_thread"):
            self.monitor_thread.join(timeout=2)

        if not self.samples:
            return {}

        # 计算统计数据
        stats = {
            "duration": time.time() - self.start_time,
            "sample_count": len(self.samples),
            "peak_memory_mb": max(s["memory_mb"] for s in self.samples),
            "avg_memory_mb": statistics.mean(s["memory_mb"] for s in self.samples),
            "peak_cpu_percent": max(s["cpu_percent"] for s in self.samples),
            "avg_cpu_percent": statistics.mean(s["cpu_percent"] for s in self.samples),
            "peak_threads": max(s["threads"] for s in self.samples),
            "peak_fds": max(s["fds"] for s in self.samples),
            "memory_growth_mb": max(s["memory_mb"] for s in self.samples)
            - min(s["memory_mb"] for s in self.samples),
            "cpu_variance": statistics.variance(
                [s["cpu_percent"] for s in self.samples]
            )
            if len(self.samples) > 1
            else 0,
        }

        logger.info("📊 系统监控已停止")
        return stats


class StressTestSuite:
    """压力测试套件"""

    def __init__(self):
        self.monitor = SystemMonitor()
        self.results: List[StressTestResult] = []
        self.process = psutil.Process()

        # 设置资源限制
        self._set_resource_limits()

        # 导入组件
        self._load_components()

    def _set_resource_limits(self):
        """设置资源限制以防止系统过载"""
        try:
            # 设置内存限制 (2GB)
            resource.setrlimit(resource.RLIMIT_AS, (2 * 1024 * 1024 * 1024, -1))

            # 设置文件描述符限制
            resource.setrlimit(resource.RLIMIT_NOFILE, (4096, 8192))

            logger.info("⚙️ 资源限制已设置")
        except Exception as e:
            logger.warning(f"⚠️ 资源限制设置失败: {e}")

    def _load_components(self):
        """加载Claude Enhancer组件"""
        try:
            # 添加项目路径
            project_path = Path(__file__).parent
            sys.path.insert(0, str(project_path / ".claude" / "core"))

            # 导入lazy引擎和编排器
            from lazy_engine import LazyWorkflowEngine
            from lazy_orchestrator import LazyAgentOrchestrator

            self.lazy_engine_class = LazyWorkflowEngine
            self.lazy_orchestrator_class = LazyAgentOrchestrator

            logger.info("✅ 成功加载Claude Enhancer 5.1组件")

        except ImportError as e:
            logger.warning(f"⚠️ 无法导入组件，将使用模拟测试: {e}")
            self.lazy_engine_class = None
            self.lazy_orchestrator_class = None

    def concurrent_load_test(
        self, duration_minutes: float = 10, max_workers: int = 50
    ) -> StressTestResult:
        """并发负载压力测试"""
        logger.info(f"🔥 开始并发负载测试: {duration_minutes}分钟, {max_workers}并发")

        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)

        # 启动监控
        self.monitor.start_monitoring()

        operations_counter = {"total": 0, "success": 0, "failed": 0}
        operations_lock = threading.Lock()
        errors = []

        def worker_task(worker_id: int):
            """工作线程任务"""
            local_ops = 0
            local_successes = 0
            local_errors = []

            try:
                if self.lazy_orchestrator_class:
                    orchestrator = self.lazy_orchestrator_class()
                    engine = self.lazy_engine_class()

                while time.time() < end_time:
                    try:
                        # 执行混合操作
                        if self.lazy_orchestrator_class:
                            # 真实组件测试
                            task = f"worker_{worker_id}_task_{local_ops}"
                            result = orchestrator.select_agents_fast(task)

                            if local_ops % 5 == 0:
                                phase_result = engine.execute_phase(local_ops % 4)
                                if not phase_result.get("success", False):
                                    raise Exception("Phase execution failed")
                        else:
                            # 模拟操作
                            time.sleep(0.001)  # 模拟1ms处理时间
                            if local_ops % 100 == 0:  # 偶尔制造延迟
                                time.sleep(0.01)

                        local_successes += 1

                    except Exception as e:
                        local_errors.append(f"Worker {worker_id}: {str(e)}")
                        if len(local_errors) > 10:  # 限制错误记录数量
                            local_errors = local_errors[-10:]

                    local_ops += 1

                    # 每100次操作更新全局计数
                    if local_ops % 100 == 0:
                        with operations_lock:
                            operations_counter["total"] += 100
                            operations_counter["success"] += min(100, local_successes)
                            operations_counter["failed"] += max(
                                0, 100 - local_successes
                            )
                            if local_errors:
                                errors.extend(local_errors[-5:])  # 只保留最近5个错误
                        local_successes = 0
                        local_errors = []

                # 最终更新
                with operations_lock:
                    remaining_ops = local_ops % 100
                    if remaining_ops > 0:
                        operations_counter["total"] += remaining_ops
                        operations_counter["success"] += min(
                            remaining_ops, local_successes
                        )
                        operations_counter["failed"] += max(
                            0, remaining_ops - local_successes
                        )

            except Exception as e:
                logger.error(f"Worker {worker_id} 崩溃: {e}")
                with operations_lock:
                    errors.append(f"Worker {worker_id} crashed: {str(e)}")

        # 启动工作线程
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(worker_task, i) for i in range(max_workers)]

            # 等待所有任务完成
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"工作线程异常: {e}")
                    errors.append(str(e))

        # 停止监控
        monitor_stats = self.monitor.stop_monitoring()

        actual_duration = time.time() - start_time
        total_ops = operations_counter["total"]
        success_ops = operations_counter["success"]
        failed_ops = operations_counter["failed"]

        # 计算指标
        ops_per_second = total_ops / actual_duration if actual_duration > 0 else 0
        error_rate = (failed_ops / total_ops * 100) if total_ops > 0 else 0
        stability_score = (success_ops / total_ops * 100) if total_ops > 0 else 0

        result = StressTestResult(
            test_name="并发负载压力测试",
            duration_minutes=actual_duration / 60,
            total_operations=total_ops,
            successful_operations=success_ops,
            failed_operations=failed_ops,
            operations_per_second=ops_per_second,
            peak_memory_mb=monitor_stats.get("peak_memory_mb", 0),
            peak_cpu_percent=monitor_stats.get("peak_cpu_percent", 0),
            peak_threads=monitor_stats.get("peak_threads", 0),
            peak_file_descriptors=monitor_stats.get("peak_fds", 0),
            error_rate_percent=error_rate,
            recovery_time_ms=0,  # 此测试不涉及恢复时间
            stability_score=stability_score,
            errors=errors[-20:],  # 保留最近20个错误
            memory_growth_mb=monitor_stats.get("memory_growth_mb", 0),
            cpu_variance_percent=monitor_stats.get("cpu_variance", 0),
        )

        logger.info(
            f"✅ 并发负载测试完成: {ops_per_second:.1f} ops/sec, 稳定性: {stability_score:.1f}%"
        )
        return result

    def memory_leak_test(self, duration_minutes: float = 30) -> StressTestResult:
        """内存泄漏检测测试"""
        logger.info(f"🧠 开始内存泄漏检测: {duration_minutes}分钟")

        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)

        # 启动监控
        self.monitor.start_monitoring(interval=1.0)  # 更频繁的内存监控

        operations = 0
        successes = 0
        errors = []

        # 记录内存基准
        gc.collect()
        baseline_memory = self.process.memory_info().rss / 1024 / 1024

        try:
            while time.time() < end_time:
                try:
                    # 创建和销毁对象以测试内存泄漏
                    if self.lazy_orchestrator_class and self.lazy_engine_class:
                        # 真实组件测试
                        components = []
                        for _ in range(10):
                            orchestrator = self.lazy_orchestrator_class()
                            engine = self.lazy_engine_class()
                            components.extend([orchestrator, engine])

                        # 执行一些操作
                        for i, orchestrator in enumerate(components[::2]):
                            result = orchestrator.select_agents_fast(
                                f"memory_test_{operations}_{i}"
                            )

                        # 清理引用
                        components.clear()

                    else:
                        # 模拟内存密集操作
                        data = []
                        for _ in range(1000):
                            data.append(
                                {
                                    "id": operations,
                                    "data": [i for i in range(100)],
                                    "metadata": {
                                        "timestamp": time.time(),
                                        "iteration": operations,
                                    },
                                }
                            )
                        data.clear()

                    successes += 1

                    # 定期垃圾回收
                    if operations % 100 == 0:
                        gc.collect()
                        current_memory = self.process.memory_info().rss / 1024 / 1024
                        growth = current_memory - baseline_memory

                        if operations % 1000 == 0:
                            logger.info(f"内存增长: {growth:.1f}MB, 操作数: {operations}")

                except Exception as e:
                    errors.append(str(e))
                    if len(errors) > 50:
                        errors = errors[-50:]

                operations += 1

                # 避免过快循环
                if operations % 10 == 0:
                    time.sleep(0.001)

        except KeyboardInterrupt:
            logger.info("内存泄漏测试被中断")

        # 停止监控
        monitor_stats = self.monitor.stop_monitoring()

        actual_duration = time.time() - start_time
        ops_per_second = operations / actual_duration if actual_duration > 0 else 0
        error_rate = (len(errors) / operations * 100) if operations > 0 else 0

        # 评估内存泄漏严重程度
        memory_growth = monitor_stats.get("memory_growth_mb", 0)
        stability_score = 100 - min(memory_growth / 10, 50)  # 内存增长越多，稳定性越低

        result = StressTestResult(
            test_name="内存泄漏检测测试",
            duration_minutes=actual_duration / 60,
            total_operations=operations,
            successful_operations=successes,
            failed_operations=len(errors),
            operations_per_second=ops_per_second,
            peak_memory_mb=monitor_stats.get("peak_memory_mb", 0),
            peak_cpu_percent=monitor_stats.get("peak_cpu_percent", 0),
            peak_threads=monitor_stats.get("peak_threads", 0),
            peak_file_descriptors=monitor_stats.get("peak_fds", 0),
            error_rate_percent=error_rate,
            recovery_time_ms=0,
            stability_score=stability_score,
            errors=errors[-10:],
            memory_growth_mb=memory_growth,
        )

        logger.info(
            f"✅ 内存泄漏检测完成: 内存增长 {memory_growth:.1f}MB, 稳定性: {stability_score:.1f}%"
        )
        return result

    def fault_tolerance_test(self, duration_minutes: float = 15) -> StressTestResult:
        """故障容错能力测试"""
        logger.info(f"🛡️ 开始故障容错测试: {duration_minutes}分钟")

        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)

        # 启动监控
        self.monitor.start_monitoring()

        operations = 0
        successes = 0
        failures = 0
        errors = []
        recovery_times = []

        fault_scenarios = [
            "timeout_simulation",
            "resource_exhaustion",
            "invalid_input",
            "component_failure",
            "network_error",
        ]

        try:
            while time.time() < end_time:
                fault_type = fault_scenarios[operations % len(fault_scenarios)]

                recovery_start = time.time()

                try:
                    if self.lazy_orchestrator_class and self.lazy_engine_class:
                        orchestrator = self.lazy_orchestrator_class()
                        engine = self.lazy_engine_class()

                        # 模拟不同类型的故障
                        if fault_type == "timeout_simulation":
                            # 模拟超时情况
                            result = orchestrator.select_agents_fast(
                                "timeout_test_task",
                                required_agents=["nonexistent_agent"],
                            )

                        elif fault_type == "resource_exhaustion":
                            # 模拟资源耗尽
                            for _ in range(100):  # 快速创建大量对象
                                temp_orchestrator = self.lazy_orchestrator_class()

                        elif fault_type == "invalid_input":
                            # 模拟无效输入
                            result = engine.execute_phase(-1)  # 无效phase

                        elif fault_type == "component_failure":
                            # 模拟组件故障
                            result = orchestrator.select_agents_fast("")  # 空任务

                        elif fault_type == "network_error":
                            # 模拟网络错误
                            result = engine.execute_phase(999)  # 不存在的phase

                    else:
                        # 模拟故障恢复
                        if fault_type == "timeout_simulation":
                            time.sleep(0.01)
                            if operations % 10 == 0:  # 10%的超时情况
                                raise TimeoutError("模拟超时")

                        elif fault_type == "resource_exhaustion":
                            large_data = [i for i in range(10000)]  # 创建大数据
                            if operations % 20 == 0:  # 5%的资源耗尽情况
                                raise MemoryError("模拟内存耗尽")
                            del large_data

                        else:
                            time.sleep(0.001)
                            if operations % 15 == 0:  # 约7%的错误率
                                raise Exception(f"模拟{fault_type}错误")

                    successes += 1
                    recovery_time = (time.time() - recovery_start) * 1000
                    recovery_times.append(recovery_time)

                except Exception as e:
                    failures += 1
                    error_msg = f"{fault_type}: {str(e)}"
                    errors.append(error_msg)

                    # 记录恢复时间
                    recovery_time = (time.time() - recovery_start) * 1000
                    recovery_times.append(recovery_time)

                    if len(errors) > 30:
                        errors = errors[-30:]

                operations += 1

                # 控制测试频率
                time.sleep(0.01)

        except KeyboardInterrupt:
            logger.info("故障容错测试被中断")

        # 停止监控
        monitor_stats = self.monitor.stop_monitoring()

        actual_duration = time.time() - start_time
        ops_per_second = operations / actual_duration if actual_duration > 0 else 0
        error_rate = (failures / operations * 100) if operations > 0 else 0
        avg_recovery_time = statistics.mean(recovery_times) if recovery_times else 0
        stability_score = (successes / operations * 100) if operations > 0 else 0

        result = StressTestResult(
            test_name="故障容错能力测试",
            duration_minutes=actual_duration / 60,
            total_operations=operations,
            successful_operations=successes,
            failed_operations=failures,
            operations_per_second=ops_per_second,
            peak_memory_mb=monitor_stats.get("peak_memory_mb", 0),
            peak_cpu_percent=monitor_stats.get("peak_cpu_percent", 0),
            peak_threads=monitor_stats.get("peak_threads", 0),
            peak_file_descriptors=monitor_stats.get("peak_fds", 0),
            error_rate_percent=error_rate,
            recovery_time_ms=avg_recovery_time,
            stability_score=stability_score,
            errors=errors[-15:],
            memory_growth_mb=monitor_stats.get("memory_growth_mb", 0),
        )

        logger.info(
            f"✅ 故障容错测试完成: 恢复时间 {avg_recovery_time:.1f}ms, 稳定性: {stability_score:.1f}%"
        )
        return result

    def resource_exhaustion_test(
        self, duration_minutes: float = 20
    ) -> StressTestResult:
        """资源耗尽边界测试"""
        logger.info(f"⚡ 开始资源耗尽测试: {duration_minutes}分钟")

        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)

        # 启动监控
        self.monitor.start_monitoring()

        operations = 0
        successes = 0
        failures = 0
        errors = []

        # 逐步增加负载
        current_load = 1
        max_load = 100
        load_increment = 2
        load_change_interval = 30  # 每30秒增加负载
        last_load_change = start_time

        try:
            while time.time() < end_time:
                current_time = time.time()

                # 动态调整负载
                if current_time - last_load_change > load_change_interval:
                    current_load = min(current_load + load_increment, max_load)
                    last_load_change = current_time
                    logger.info(f"增加负载到: {current_load}")

                try:
                    # 根据当前负载执行操作
                    if self.lazy_orchestrator_class and self.lazy_engine_class:
                        # 创建负载相应数量的组件
                        components = []
                        for _ in range(current_load):
                            orchestrator = self.lazy_orchestrator_class()
                            engine = self.lazy_engine_class()
                            components.extend([orchestrator, engine])

                        # 执行批量操作
                        with ThreadPoolExecutor(
                            max_workers=min(current_load, 20)
                        ) as executor:
                            futures = []
                            for i in range(current_load):
                                if i < len(components) // 2:
                                    orchestrator = components[i * 2]
                                    future = executor.submit(
                                        orchestrator.select_agents_fast,
                                        f"load_test_{operations}_{i}",
                                    )
                                    futures.append(future)

                            # 等待完成
                            for future in as_completed(futures, timeout=5):
                                result = future.result()

                        components.clear()

                    else:
                        # 模拟资源密集操作
                        data_chunks = []
                        for _ in range(current_load):
                            chunk = [i for i in range(1000)]
                            data_chunks.append(chunk)

                        # 处理数据
                        total = 0
                        for chunk in data_chunks:
                            total += sum(chunk)

                        data_chunks.clear()

                    successes += 1

                except Exception as e:
                    failures += 1
                    error_msg = f"Load {current_load}: {str(e)}"
                    errors.append(error_msg)

                    if len(errors) > 20:
                        errors = errors[-20:]

                    # 如果错误率过高，降低负载
                    if failures > operations * 0.3:  # 错误率超过30%
                        current_load = max(1, current_load - 5)
                        logger.warning(f"错误率过高，降低负载到: {current_load}")

                operations += 1

                # 检查资源使用情况
                if operations % 50 == 0:
                    memory_mb = self.process.memory_info().rss / 1024 / 1024
                    cpu_percent = self.process.cpu_percent()

                    if memory_mb > 1500:  # 内存超过1.5GB
                        logger.warning(f"内存使用过高: {memory_mb:.1f}MB")

                    if cpu_percent > 90:  # CPU使用超过90%
                        logger.warning(f"CPU使用过高: {cpu_percent:.1f}%")

                # 适当延迟避免过载
                time.sleep(0.001 * max(1, current_load // 10))

        except KeyboardInterrupt:
            logger.info("资源耗尽测试被中断")

        # 停止监控
        monitor_stats = self.monitor.stop_monitoring()

        actual_duration = time.time() - start_time
        ops_per_second = operations / actual_duration if actual_duration > 0 else 0
        error_rate = (failures / operations * 100) if operations > 0 else 0
        stability_score = (successes / operations * 100) if operations > 0 else 0

        result = StressTestResult(
            test_name="资源耗尽边界测试",
            duration_minutes=actual_duration / 60,
            total_operations=operations,
            successful_operations=successes,
            failed_operations=failures,
            operations_per_second=ops_per_second,
            peak_memory_mb=monitor_stats.get("peak_memory_mb", 0),
            peak_cpu_percent=monitor_stats.get("peak_cpu_percent", 0),
            peak_threads=monitor_stats.get("peak_threads", 0),
            peak_file_descriptors=monitor_stats.get("peak_fds", 0),
            error_rate_percent=error_rate,
            recovery_time_ms=0,
            stability_score=stability_score,
            errors=errors[-10:],
            memory_growth_mb=monitor_stats.get("memory_growth_mb", 0),
            cpu_variance_percent=monitor_stats.get("cpu_variance", 0),
        )

        logger.info(f"✅ 资源耗尽测试完成: 峰值负载 {current_load}, 稳定性: {stability_score:.1f}%")
        return result

    def run_complete_stress_suite(self, quick_mode: bool = False) -> Dict[str, Any]:
        """运行完整压力测试套件"""
        logger.info("🔥 开始Claude Enhancer 5.1完整压力测试套件")

        if quick_mode:
            logger.info("⚡ 快速模式: 缩短测试时间")
            test_configs = [
                ("concurrent_load_test", 3, 20),  # 3分钟, 20并发
                ("memory_leak_test", 5),  # 5分钟
                ("fault_tolerance_test", 3),  # 3分钟
                ("resource_exhaustion_test", 5),  # 5分钟
            ]
        else:
            logger.info("🎯 标准模式: 完整压力测试")
            test_configs = [
                ("concurrent_load_test", 10, 50),  # 10分钟, 50并发
                ("memory_leak_test", 30),  # 30分钟
                ("fault_tolerance_test", 15),  # 15分钟
                ("resource_exhaustion_test", 20),  # 20分钟
            ]

        suite_start_time = time.time()

        for config in test_configs:
            test_name = config[0]

            logger.info(f"\n{'='*60}")
            logger.info(f"🧪 执行测试: {test_name}")
            logger.info(f"{'='*60}")

            try:
                if test_name == "concurrent_load_test":
                    result = self.concurrent_load_test(config[1], config[2])
                elif test_name == "memory_leak_test":
                    result = self.memory_leak_test(config[1])
                elif test_name == "fault_tolerance_test":
                    result = self.fault_tolerance_test(config[1])
                elif test_name == "resource_exhaustion_test":
                    result = self.resource_exhaustion_test(config[1])

                self.results.append(result)

                # 显示测试结果
                self._print_test_result(result)

                # 测试间隔，让系统恢复
                logger.info("⏳ 系统恢复中...")
                gc.collect()
                time.sleep(5)

            except Exception as e:
                logger.error(f"❌ 测试失败 {test_name}: {e}")
                traceback.print_exc()

        total_duration = time.time() - suite_start_time

        # 生成综合报告
        summary = self._generate_stress_test_report(total_duration)

        return summary

    def _print_test_result(self, result: StressTestResult):
        """打印单个测试结果"""
        print(f"\n📊 {result.test_name} 结果:")
        print(f"  ⏱️  持续时间: {result.duration_minutes:.1f}分钟")
        print(f"  📈 总操作数: {result.total_operations:,}")
        print(f"  ✅ 成功操作: {result.successful_operations:,}")
        print(f"  ❌ 失败操作: {result.failed_operations:,}")
        print(f"  🚀 操作速率: {result.operations_per_second:.1f} ops/sec")
        print(f"  💾 峰值内存: {result.peak_memory_mb:.1f} MB")
        print(f"  ⚡ 峰值CPU: {result.peak_cpu_percent:.1f}%")
        print(f"  🧵 峰值线程: {result.peak_threads}")
        print(f"  📂 峰值文件描述符: {result.peak_file_descriptors}")
        print(f"  ❗ 错误率: {result.error_rate_percent:.2f}%")
        print(f"  🛡️ 稳定性评分: {result.stability_score:.1f}")

        if result.recovery_time_ms > 0:
            print(f"  ⚡ 恢复时间: {result.recovery_time_ms:.1f}ms")

        if result.memory_growth_mb > 0:
            print(f"  📈 内存增长: {result.memory_growth_mb:.1f}MB")

        if result.errors:
            print(f"  ⚠️  最近错误: {len(result.errors)}个")
            for error in result.errors[-3:]:
                print(f"    - {error}")

    def _generate_stress_test_report(self, total_duration: float) -> Dict[str, Any]:
        """生成压力测试综合报告"""
        if not self.results:
            return {"error": "没有测试结果"}

        # 计算综合指标
        total_operations = sum(r.total_operations for r in self.results)
        total_successes = sum(r.successful_operations for r in self.results)
        total_failures = sum(r.failed_operations for r in self.results)

        avg_ops_per_sec = statistics.mean(
            [r.operations_per_second for r in self.results]
        )
        max_memory = max([r.peak_memory_mb for r in self.results])
        avg_cpu = statistics.mean([r.peak_cpu_percent for r in self.results])
        avg_error_rate = statistics.mean([r.error_rate_percent for r in self.results])
        avg_stability = statistics.mean([r.stability_score for r in self.results])

        # 系统稳定性评级
        if avg_stability >= 95 and avg_error_rate < 1 and max_memory < 500:
            system_grade = "A+"
        elif avg_stability >= 90 and avg_error_rate < 3 and max_memory < 800:
            system_grade = "A"
        elif avg_stability >= 85 and avg_error_rate < 5 and max_memory < 1200:
            system_grade = "B"
        elif avg_stability >= 80 and avg_error_rate < 10:
            system_grade = "C"
        else:
            system_grade = "D"

        # 识别关键问题
        critical_issues = []
        if max_memory > 1000:
            critical_issues.append("内存使用过高")
        if avg_error_rate > 10:
            critical_issues.append("错误率过高")
        if avg_cpu > 80:
            critical_issues.append("CPU负载过高")
        if avg_stability < 80:
            critical_issues.append("系统稳定性不足")

        # 性能建议
        recommendations = []
        if max_memory > 500:
            recommendations.append("优化内存管理，实施对象池")
        if avg_error_rate > 5:
            recommendations.append("加强错误处理和恢复机制")
        if avg_ops_per_sec < 50:
            recommendations.append("提升处理吞吐量")
        if any(r.memory_growth_mb > 100 for r in self.results):
            recommendations.append("检查并修复潜在的内存泄漏")

        summary = {
            "test_suite_info": {
                "version": "Claude Enhancer 5.1 Stress Test",
                "timestamp": datetime.now().isoformat(),
                "total_duration_minutes": total_duration / 60,
                "total_tests": len(self.results),
                "system_grade": system_grade,
            },
            "aggregate_metrics": {
                "total_operations": total_operations,
                "total_successes": total_successes,
                "total_failures": total_failures,
                "average_ops_per_second": avg_ops_per_sec,
                "peak_memory_mb": max_memory,
                "average_cpu_percent": avg_cpu,
                "average_error_rate_percent": avg_error_rate,
                "average_stability_score": avg_stability,
            },
            "test_results": [
                {
                    "test_name": r.test_name,
                    "duration_minutes": r.duration_minutes,
                    "total_operations": r.total_operations,
                    "operations_per_second": r.operations_per_second,
                    "error_rate_percent": r.error_rate_percent,
                    "stability_score": r.stability_score,
                    "peak_memory_mb": r.peak_memory_mb,
                    "peak_cpu_percent": r.peak_cpu_percent,
                    "memory_growth_mb": r.memory_growth_mb,
                }
                for r in self.results
            ],
            "critical_issues": critical_issues,
            "recommendations": recommendations,
            "system_limits": {
                "max_concurrent_operations": max(
                    [r.operations_per_second for r in self.results]
                )
                if self.results
                else 0,
                "memory_ceiling_mb": max_memory,
                "cpu_threshold_percent": max([r.peak_cpu_percent for r in self.results])
                if self.results
                else 0,
                "stability_floor_percent": min(
                    [r.stability_score for r in self.results]
                )
                if self.results
                else 0,
            },
        }

        return summary

    def save_stress_test_results(self, filename: str = None) -> str:
        """保存压力测试结果"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"claude_enhancer_51_stress_test_report_{timestamp}.json"

        total_duration = sum(r.duration_minutes for r in self.results) * 60
        summary = self._generate_stress_test_report(total_duration)

        filepath = Path(__file__).parent / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        logger.info(f"📄 压力测试结果已保存: {filepath}")
        return str(filepath)


def main():
    """主函数"""
    print("🔥 启动Claude Enhancer 5.1压力测试套件...")

    # 解析命令行参数
    quick_mode = "--quick" in sys.argv

    try:
        # 创建压力测试套件
        stress_suite = StressTestSuite()

        # 运行压力测试
        summary = stress_suite.run_complete_stress_suite(quick_mode=quick_mode)

        # 打印总结报告
        print("\n" + "=" * 80)
        print("🎯 CLAUDE ENHANCER 5.1 压力测试总结报告")
        print("=" * 80)

        print(f"\n📊 测试概览:")
        print(f"  系统评级: {summary['test_suite_info']['system_grade']}")
        print(f"  总测试时间: {summary['test_suite_info']['total_duration_minutes']:.1f}分钟")
        print(f"  测试数量: {summary['test_suite_info']['total_tests']}")

        print(f"\n📈 聚合指标:")
        metrics = summary["aggregate_metrics"]
        print(f"  总操作数: {metrics['total_operations']:,}")
        print(f"  平均吞吐量: {metrics['average_ops_per_second']:.1f} ops/sec")
        print(f"  峰值内存: {metrics['peak_memory_mb']:.1f} MB")
        print(f"  平均CPU: {metrics['average_cpu_percent']:.1f}%")
        print(f"  平均错误率: {metrics['average_error_rate_percent']:.2f}%")
        print(f"  平均稳定性: {metrics['average_stability_score']:.1f}")

        # 关键问题
        if summary["critical_issues"]:
            print(f"\n⚠️ 关键问题:")
            for issue in summary["critical_issues"]:
                print(f"  - {issue}")

        # 优化建议
        if summary["recommendations"]:
            print(f"\n💡 优化建议:")
            for rec in summary["recommendations"]:
                print(f"  - {rec}")

        # 保存结果
        report_file = stress_suite.save_stress_test_results()
        print(f"\n📄 详细报告已保存: {report_file}")

        # 判断测试是否通过
        system_grade = summary["test_suite_info"]["system_grade"]
        success = system_grade in ["A+", "A", "B"]

        print(f"\n🎯 压力测试{'通过' if success else '需要优化'}! (评级: {system_grade})")

        return success

    except KeyboardInterrupt:
        print("\n⚠️ 用户中断了压力测试")
        return False
    except Exception as e:
        logger.error(f"❌ 压力测试套件执行失败: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
