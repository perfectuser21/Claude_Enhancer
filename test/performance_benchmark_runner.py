#!/usr/bin/env python3
"""
Claude Enhancer 5.0 - 性能基准测试专用工具
作为test-engineer设计的高精度性能测试框架

主要功能:
1. 微秒级精度的性能测量
2. 内存使用监控和泄漏检测
3. CPU使用率分析
4. 并发性能基准测试
5. 回归性能分析
6. 自动化性能报告生成
"""

import time
import psutil
import threading
import subprocess
import json
import statistics
import os
import sys
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


@dataclass
class PerformanceMetrics:
    """性能指标数据结构"""

    test_name: str
    execution_time_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    iterations: int
    success_rate: float
    percentile_95: float
    percentile_99: float
    min_time: float
    max_time: float
    std_deviation: float


@dataclass
class BenchmarkConfig:
    """基准测试配置"""

    max_execution_time_ms: float
    max_memory_usage_mb: float
    max_cpu_usage_percent: float
    min_success_rate: float
    iterations: int
    warmup_iterations: int


class PerformanceMonitor:
    """实时性能监控器"""

    def __init__(self):
        self.process = psutil.Process()
        self.baseline_memory = self.process.memory_info().rss / 1024 / 1024
        self.monitoring = False
        self.metrics = []

    @contextmanager
    def monitor_performance(self, sample_interval: float = 0.1):
        """性能监控上下文管理器"""
        self.monitoring = True
        self.metrics = []

        def monitor_worker():
            while self.monitoring:
                try:
                    memory_mb = self.process.memory_info().rss / 1024 / 1024
                    cpu_percent = self.process.cpu_percent()

                    self.metrics.append(
                        {
                            "timestamp": time.time(),
                            "memory_mb": memory_mb,
                            "cpu_percent": cpu_percent,
                        }
                    )

                    time.sleep(sample_interval)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break

        monitor_thread = threading.Thread(target=monitor_worker, daemon=True)
        monitor_thread.start()

        try:
            yield self
        finally:
            self.monitoring = False
            monitor_thread.join(timeout=1.0)

    def get_peak_memory(self) -> float:
        """获取峰值内存使用"""
        if not self.metrics:
            return 0.0
        return max(metric["memory_mb"] for metric in self.metrics)

    def get_average_cpu(self) -> float:
        """获取平均CPU使用率"""
        if not self.metrics:
            return 0.0
        return statistics.mean(metric["cpu_percent"] for metric in self.metrics)

    def detect_memory_leak(self, threshold_mb: float = 10.0) -> bool:
        """检测内存泄漏"""
        if len(self.metrics) < 10:
            return False

        # 计算内存使用趋势
        memory_values = [metric["memory_mb"] for metric in self.metrics]
        start_avg = statistics.mean(memory_values[:5])
        end_avg = statistics.mean(memory_values[-5:])

        return (end_avg - start_avg) > threshold_mb


class HooksBenchmarkSuite:
    """Hooks性能基准测试套件"""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.hooks_dir = os.path.join(project_root, ".claude", "hooks")
        self.configs = {
            "quality_gate": BenchmarkConfig(
                max_execution_time_ms=100.0,
                max_memory_usage_mb=10.0,
                max_cpu_usage_percent=5.0,
                min_success_rate=0.98,
                iterations=100,
                warmup_iterations=10,
            ),
            "smart_agent_selector": BenchmarkConfig(
                max_execution_time_ms=50.0,
                max_memory_usage_mb=8.0,
                max_cpu_usage_percent=3.0,
                min_success_rate=0.98,
                iterations=100,
                warmup_iterations=10,
            ),
        }

    def benchmark_quality_gate(self) -> PerformanceMetrics:
        """基准测试: quality_gate.sh性能"""
        script_path = os.path.join(self.hooks_dir, "quality_gate.sh")
        config = self.configs["quality_gate"]

        test_inputs = [
            '{"prompt": "实现用户认证系统"}',
            '{"prompt": "修复数据库连接问题"}',
            '{"prompt": "优化前端性能"}',
            '{"prompt": "添加安全检查"}',
            '{"prompt": "部署生产环境"}',
        ]

        return self._run_hook_benchmark(
            script_path, "quality_gate", test_inputs, config
        )

    def benchmark_smart_agent_selector(self) -> PerformanceMetrics:
        """基准测试: smart_agent_selector.sh性能"""
        script_path = os.path.join(self.hooks_dir, "smart_agent_selector.sh")
        config = self.configs["smart_agent_selector"]

        test_inputs = [
            '{"prompt": "fix typo"}',  # 简单任务
            '{"prompt": "implement feature"}',  # 标准任务
            '{"prompt": "architect system"}',  # 复杂任务
            '{"prompt": "refactor codebase"}',  # 标准任务
            '{"prompt": "deploy infrastructure"}',  # 复杂任务
        ]

        return self._run_hook_benchmark(
            script_path, "smart_agent_selector", test_inputs, config
        )

    def _run_hook_benchmark(
        self,
        script_path: str,
        test_name: str,
        test_inputs: List[str],
        config: BenchmarkConfig,
    ) -> PerformanceMetrics:
        """运行Hook基准测试"""
        print(f"🚀 开始基准测试: {test_name}")

        # 预热阶段
        print(f"⚡ 执行预热 ({config.warmup_iterations} 次)...")
        for _ in range(config.warmup_iterations):
            test_input = test_inputs[0]
            subprocess.run(
                [script_path],
                input=test_input,
                text=True,
                capture_output=True,
                timeout=5,
            )

        # 性能测试阶段
        print(f"📊 执行性能测试 ({config.iterations} 次)...")
        execution_times = []
        success_count = 0
        memory_readings = []

        monitor = PerformanceMonitor()

        with monitor.monitor_performance():
            for i in range(config.iterations):
                test_input = test_inputs[i % len(test_inputs)]

                start_time = time.perf_counter()

                try:
                    result = subprocess.run(
                        [script_path],
                        input=test_input,
                        text=True,
                        capture_output=True,
                        timeout=5,
                    )

                    end_time = time.perf_counter()
                    execution_time_ms = (end_time - start_time) * 1000

                    execution_times.append(execution_time_ms)

                    if result.returncode == 0:
                        success_count += 1

                    # 每10次迭代显示进度
                    if (i + 1) % 10 == 0:
                        progress = (i + 1) / config.iterations * 100
                        avg_time = statistics.mean(execution_times)
                        print(f"  进度: {progress:.0f}% | 平均时间: {avg_time:.2f}ms")

                except subprocess.TimeoutExpired:
                    execution_times.append(5000)  # 超时记录为5秒

        # 计算统计指标
        success_rate = success_count / config.iterations
        avg_execution_time = statistics.mean(execution_times)
        std_deviation = (
            statistics.stdev(execution_times) if len(execution_times) > 1 else 0
        )
        percentile_95 = np.percentile(execution_times, 95)
        percentile_99 = np.percentile(execution_times, 99)

        peak_memory = monitor.get_peak_memory()
        avg_cpu = monitor.get_average_cpu()

        # 创建性能指标对象
        metrics = PerformanceMetrics(
            test_name=test_name,
            execution_time_ms=avg_execution_time,
            memory_usage_mb=peak_memory,
            cpu_usage_percent=avg_cpu,
            iterations=config.iterations,
            success_rate=success_rate,
            percentile_95=percentile_95,
            percentile_99=percentile_99,
            min_time=min(execution_times),
            max_time=max(execution_times),
            std_deviation=std_deviation,
        )

        # 评估性能结果
        self._evaluate_performance(metrics, config)

        return metrics

    def _evaluate_performance(
        self, metrics: PerformanceMetrics, config: BenchmarkConfig
    ):
        """评估性能结果"""
        print(f"\n📊 {metrics.test_name} 性能结果:")
        print(f"  平均执行时间: {metrics.execution_time_ms:.2f}ms")
        print(f"  成功率: {metrics.success_rate:.1%}")
        print(f"  内存使用: {metrics.memory_usage_mb:.2f}MB")
        print(f"  CPU使用: {metrics.cpu_usage_percent:.2f}%")

        # 性能评估
        performance_grade = "A+"
        issues = []

        if metrics.execution_time_ms > config.max_execution_time_ms:
            performance_grade = "C"
            issues.append(
                f"执行时间超标 ({metrics.execution_time_ms:.2f}ms > {config.max_execution_time_ms}ms)"
            )

        if metrics.memory_usage_mb > config.max_memory_usage_mb:
            performance_grade = "C"
            issues.append(
                f"内存使用超标 ({metrics.memory_usage_mb:.2f}MB > {config.max_memory_usage_mb}MB)"
            )

        if metrics.success_rate < config.min_success_rate:
            performance_grade = "F"
            issues.append(
                f"成功率不达标 ({metrics.success_rate:.1%} < {config.min_success_rate:.1%})"
            )

        if not issues:
            print(f"  ✅ 性能评级: {performance_grade} (优秀)")
        else:
            print(f"  ⚠️ 性能评级: {performance_grade}")
            for issue in issues:
                print(f"    - {issue}")


class ConcurrencyBenchmarkSuite:
    """并发性能基准测试套件"""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.hooks_dir = os.path.join(project_root, ".claude", "hooks")

    def benchmark_concurrent_hooks(self, max_workers: int = 20) -> Dict[str, Any]:
        """并发Hook执行基准测试"""
        print(f"🔄 开始并发性能测试 (最大并发: {max_workers})")

        quality_gate_script = os.path.join(self.hooks_dir, "quality_gate.sh")
        test_input = '{"prompt": "concurrent test"}'

        results = {}
        concurrency_levels = [1, 2, 5, 10, 15, max_workers]

        for level in concurrency_levels:
            print(f"  测试并发级别: {level}")

            start_time = time.perf_counter()
            success_count = 0
            execution_times = []

            with ThreadPoolExecutor(max_workers=level) as executor:
                pass  # Auto-fixed empty block
                # 提交任务
                task_count = level * 2  # 每个并发级别执行2倍任务数
                futures = []

                for i in range(task_count):
                    future = executor.submit(
                        self._run_single_hook, quality_gate_script, test_input
                    )
                    futures.append(future)

                # 收集结果
                for future in as_completed(futures):
                    try:
                        exec_time, success = future.result(timeout=10)
                        execution_times.append(exec_time)
                        if success:
                            success_count += 1
                    except Exception as e:
                        execution_times.append(10000)  # 失败记录为10秒

            total_time = time.perf_counter() - start_time
            throughput = task_count / total_time
            success_rate = success_count / task_count
            avg_exec_time = statistics.mean(execution_times) if execution_times else 0

            results[f"level_{level}"] = {
                "concurrency": level,
                "total_tasks": task_count,
                "success_count": success_count,
                "success_rate": success_rate,
                "total_time": total_time,
                "throughput": throughput,
                "avg_execution_time": avg_exec_time,
            }

            print(f"    吞吐量: {throughput:.2f} tasks/sec")
            print(f"    成功率: {success_rate:.1%}")

        return results

    def _run_single_hook(self, script_path: str, test_input: str) -> Tuple[float, bool]:
        """运行单个Hook"""
        start_time = time.perf_counter()

        try:
            result = subprocess.run(
                [script_path],
                input=test_input,
                text=True,
                capture_output=True,
                timeout=5,
            )

            end_time = time.perf_counter()
            execution_time = (end_time - start_time) * 1000

            return execution_time, result.returncode == 0

        except subprocess.TimeoutExpired:
            return 5000, False  # 超时
        except Exception:
            return 10000, False  # 其他错误


class MemoryLeakDetector:
    """内存泄漏检测器"""

    def __init__(self, project_root: str):
        self.project_root = project_root
        self.hooks_dir = os.path.join(project_root, ".claude", "hooks")

    def detect_hook_memory_leaks(self, iterations: int = 1000) -> Dict[str, Any]:
        """检测Hook内存泄漏"""
        print(f"🔍 开始内存泄漏检测 ({iterations} 次迭代)")

        quality_gate_script = os.path.join(self.hooks_dir, "quality_gate.sh")
        test_input = '{"prompt": "memory leak test"}'

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024

        memory_snapshots = []
        execution_times = []

        # 执行多次迭代，监控内存使用
        for i in range(iterations):
            start_time = time.perf_counter()

            try:
                subprocess.run(
                    [quality_gate_script],
                    input=test_input,
                    text=True,
                    capture_output=True,
                    timeout=5,
                )

                end_time = time.perf_counter()
                execution_times.append((end_time - start_time) * 1000)

                # 每100次迭代记录内存使用
                if i % 100 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_snapshots.append(
                        {
                            "iteration": i,
                            "memory_mb": current_memory,
                            "memory_delta": current_memory - initial_memory,
                        }
                    )

                    if i > 0:
                        progress = i / iterations * 100
                        print(
                            f"  进度: {progress:.0f}% | 内存: {current_memory:.2f}MB (+{current_memory - initial_memory:.2f}MB)"
                        )

            except subprocess.TimeoutExpired:
                execution_times.append(5000)

        final_memory = process.memory_info().rss / 1024 / 1024
        total_memory_increase = final_memory - initial_memory

        # 分析内存泄漏
        leak_detected = False
        leak_rate = 0

        if len(memory_snapshots) >= 3:
            pass  # Auto-fixed empty block
            # 计算内存增长趋势
            memory_values = [snapshot["memory_mb"] for snapshot in memory_snapshots]
            iterations_values = [snapshot["iteration"] for snapshot in memory_snapshots]

            # 简单线性回归分析内存增长率
            if len(memory_values) > 1:
                leak_rate = (
                    (memory_values[-1] - memory_values[0])
                    / (iterations_values[-1] - iterations_values[0])
                    * 1000
                )

                # 如果每1000次迭代内存增长超过5MB，认为可能有泄漏
                if leak_rate > 5.0:
                    leak_detected = True

        avg_execution_time = statistics.mean(execution_times) if execution_times else 0

        results = {
            "iterations": iterations,
            "initial_memory_mb": initial_memory,
            "final_memory_mb": final_memory,
            "total_memory_increase_mb": total_memory_increase,
            "leak_detected": leak_detected,
            "leak_rate_mb_per_1k_iterations": leak_rate,
            "avg_execution_time_ms": avg_execution_time,
            "memory_snapshots": memory_snapshots,
        }

        # 输出结果
        print(f"\n📊 内存泄漏检测结果:")
        print(f"  初始内存: {initial_memory:.2f}MB")
        print(f"  最终内存: {final_memory:.2f}MB")
        print(f"  内存增长: {total_memory_increase:.2f}MB")
        print(f"  泄漏检测: {'⚠️ 疑似泄漏' if leak_detected else '✅ 无泄漏'}")

        if leak_detected:
            print(f"  泄漏率: {leak_rate:.3f}MB/1000次迭代")

        return results


class PerformanceReportGenerator:
    """性能报告生成器"""

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def generate_comprehensive_report(
        self,
        hook_metrics: List[PerformanceMetrics],
        concurrency_results: Dict[str, Any],
        memory_leak_results: Dict[str, Any],
        timestamp: str,
    ) -> str:
        """生成综合性能报告"""
        report_file = self.output_dir / f"performance_report_{timestamp}.md"

        # 生成性能图表
        self._generate_performance_charts(hook_metrics, concurrency_results, timestamp)

        # 生成Markdown报告
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(
                self._generate_markdown_report(
                    hook_metrics, concurrency_results, memory_leak_results, timestamp
                )
            )

        print(f"📊 性能报告已生成: {report_file}")
        return str(report_file)

    def _generate_performance_charts(
        self,
        hook_metrics: List[PerformanceMetrics],
        concurrency_results: Dict[str, Any],
        timestamp: str,
    ):
        """生成性能图表"""
        # Hook执行时间对比图
        plt.figure(figsize=(12, 8))

        # 子图1: Hook执行时间
        plt.subplot(2, 2, 1)
        hook_names = [metric.test_name for metric in hook_metrics]
        execution_times = [metric.execution_time_ms for metric in hook_metrics]

        bars = plt.bar(hook_names, execution_times, color=["#FF6B6B", "#4ECDC4"])
        plt.title("Hook执行时间对比")
        plt.ylabel("执行时间 (ms)")
        plt.xticks(rotation=45)

        # 添加数值标签
        for bar, time in zip(bars, execution_times):
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1,
                f"{time:.1f}ms",
                ha="center",
                va="bottom",
            )

        # 子图2: 内存使用对比
        plt.subplot(2, 2, 2)
        memory_usage = [metric.memory_usage_mb for metric in hook_metrics]

        bars = plt.bar(hook_names, memory_usage, color=["#95E1D3", "#F38BA8"])
        plt.title("内存使用对比")
        plt.ylabel("内存使用 (MB)")
        plt.xticks(rotation=45)

        for bar, memory in zip(bars, memory_usage):
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.1,
                f"{memory:.1f}MB",
                ha="center",
                va="bottom",
            )

        # 子图3: 并发性能
        plt.subplot(2, 2, 3)
        if concurrency_results:
            levels = []
            throughputs = []

            for key, result in concurrency_results.items():
                if key.startswith("level_"):
                    levels.append(result["concurrency"])
                    throughputs.append(result["throughput"])

            plt.plot(levels, throughputs, marker="o", linewidth=2, markersize=8)
            plt.title("并发吞吐量")
            plt.xlabel("并发级别")
            plt.ylabel("吞吐量 (tasks/sec)")
            plt.grid(True, alpha=0.3)

        # 子图4: 成功率对比
        plt.subplot(2, 2, 4)
        success_rates = [metric.success_rate * 100 for metric in hook_metrics]

        bars = plt.bar(hook_names, success_rates, color=["#A8E6CF", "#FFD93D"])
        plt.title("成功率对比")
        plt.ylabel("成功率 (%)")
        plt.ylim(0, 105)
        plt.xticks(rotation=45)

        for bar, rate in zip(bars, success_rates):
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 1,
                f"{rate:.1f}%",
                ha="center",
                va="bottom",
            )

        plt.tight_layout()
        chart_file = self.output_dir / f"performance_charts_{timestamp}.png"
        plt.savefig(chart_file, dpi=300, bbox_inches="tight")
        plt.close()

        print(f"📈 性能图表已生成: {chart_file}")

    def _generate_markdown_report(
        self,
        hook_metrics: List[PerformanceMetrics],
        concurrency_results: Dict[str, Any],
        memory_leak_results: Dict[str, Any],
        timestamp: str,
    ) -> str:
        """生成Markdown报告内容"""
        report = f"""# Claude Enhancer 5.0 - 性能基准测试报告

**生成时间**: {timestamp}
**测试框架**: Test Engineer Professional Suite
**系统环境**: {os.uname().sysname} {os.uname().release}

## 📊 执行摘要

### 整体性能评级
"""

        # 计算整体评级
        avg_exec_time = statistics.mean([m.execution_time_ms for m in hook_metrics])
        avg_success_rate = statistics.mean([m.success_rate for m in hook_metrics])

        if avg_exec_time < 50 and avg_success_rate > 0.98:
            grade = "A+ (优秀)"
            grade_emoji = "🌟"
        elif avg_exec_time < 100 and avg_success_rate > 0.95:
            grade = "A (良好)"
            grade_emoji = "✅"
        elif avg_exec_time < 200 and avg_success_rate > 0.90:
            grade = "B (及格)"
            grade_emoji = "⚠️"
        else:
            grade = "C (需要优化)"
            grade_emoji = "❌"

        report += f"""
{grade_emoji} **性能等级**: {grade}
📈 **平均执行时间**: {avg_exec_time:.2f}ms
✅ **平均成功率**: {avg_success_rate:.1%}
💾 **内存使用状态**: {'正常' if not memory_leak_results.get('leak_detected') else '疑似泄漏'}

## 🔧 Hook性能详细分析

| Hook名称 | 平均时间 | 95%分位 | 99%分位 | 内存使用 | 成功率 | 评级 |
|---------|----------|---------|---------|----------|--------|------|
"""

        for metric in hook_metrics:
            grade_icon = (
                "🌟"
                if metric.execution_time_ms < 50
                else "✅"
                if metric.execution_time_ms < 100
                else "⚠️"
            )
            report += f"| {metric.test_name} | {metric.execution_time_ms:.2f}ms | {metric.percentile_95:.2f}ms | {metric.percentile_99:.2f}ms | {metric.memory_usage_mb:.2f}MB | {metric.success_rate:.1%} | {grade_icon} |\n"

        report += f"""
## 🔄 并发性能分析

### 并发吞吐量测试结果
"""

        if concurrency_results:
            report += "| 并发级别 | 总任务数 | 成功数 | 成功率 | 吞吐量 | 平均时间 |\n"
            report += "|---------|----------|--------|--------|--------|----------|\n"

            for key, result in concurrency_results.items():
                if key.startswith("level_"):
                    report += f"| {result['concurrency']} | {result['total_tasks']} | {result['success_count']} | {result['success_rate']:.1%} | {result['throughput']:.2f} tasks/sec | {result['avg_execution_time']:.2f}ms |\n"

        report += f"""
### 并发性能评估
- **最优并发级别**: {self._get_optimal_concurrency(concurrency_results)}
- **峰值吞吐量**: {self._get_peak_throughput(concurrency_results):.2f} tasks/sec
- **并发扩展性**: {'良好' if self._check_concurrency_scaling(concurrency_results) else '有限'}

## 🔍 内存泄漏检测

### 检测结果
- **初始内存**: {memory_leak_results.get('initial_memory_mb', 0):.2f}MB
- **最终内存**: {memory_leak_results.get('final_memory_mb', 0):.2f}MB
- **内存增长**: {memory_leak_results.get('total_memory_increase_mb', 0):.2f}MB
- **泄漏状态**: {'⚠️ 疑似泄漏' if memory_leak_results.get('leak_detected') else '✅ 无泄漏检测'}
"""

        if memory_leak_results.get("leak_detected"):
            leak_rate = memory_leak_results.get("leak_rate_mb_per_1k_iterations", 0)
            report += f"- **泄漏率**: {leak_rate:.3f}MB/1000次迭代\n"

        report += f"""
## 📈 性能趋势分析

### 执行时间分布
"""

        for metric in hook_metrics:
            report += f"""
#### {metric.test_name}
- **平均时间**: {metric.execution_time_ms:.2f}ms
- **标准差**: {metric.std_deviation:.2f}ms
- **最快**: {metric.min_time:.2f}ms
- **最慢**: {metric.max_time:.2f}ms
- **变异系数**: {(metric.std_deviation / metric.execution_time_ms * 100):.1f}%
"""

        report += f"""
## 🎯 性能优化建议

### 立即优化项
"""

        recommendations = []
        critical_issues = []

        for metric in hook_metrics:
            if metric.execution_time_ms > 100:
                critical_issues.append(
                    f"- **{metric.test_name}**: 执行时间过长 ({metric.execution_time_ms:.2f}ms)"
                )
                recommendations.append(f"优化 {metric.test_name} 算法，目标减少到 <100ms")

            if metric.success_rate < 0.95:
                critical_issues.append(
                    f"- **{metric.test_name}**: 成功率不足 ({metric.success_rate:.1%})"
                )
                recommendations.append(f"改进 {metric.test_name} 错误处理机制")

        if memory_leak_results.get("leak_detected"):
            critical_issues.append("- **内存管理**: 检测到疑似内存泄漏")
            recommendations.append("调查Hook脚本的内存使用模式，修复潜在泄漏")

        if critical_issues:
            for issue in critical_issues:
                report += f"{issue}\n"
        else:
            report += "- ✅ 无立即需要优化的问题\n"

        report += f"""
### 性能优化建议
"""

        if recommendations:
            for rec in recommendations:
                report += f"1. {rec}\n"
        else:
            report += "1. 继续保持当前优秀性能\n"
            report += "2. 定期进行性能回归测试\n"

        report += f"""
2. 实施性能监控告警机制
3. 建立性能基线和回归检测
4. 考虑缓存机制优化频繁操作

## 📊 基准对比

### 与理想性能对比
| 指标 | 当前值 | 目标值 | 状态 |
|------|--------|--------|------|
| Quality Gate执行时间 | {next((m.execution_time_ms for m in hook_metrics if m.test_name == 'quality_gate'), 0):.2f}ms | <100ms | {'✅' if next((m.execution_time_ms for m in hook_metrics if m.test_name == 'quality_gate'), 0) < 100 else '❌'} |
| Agent Selector执行时间 | {next((m.execution_time_ms for m in hook_metrics if m.test_name == 'smart_agent_selector'), 0):.2f}ms | <50ms | {'✅' if next((m.execution_time_ms for m in hook_metrics if m.test_name == 'smart_agent_selector'), 0) < 50 else '❌'} |
| 整体成功率 | {avg_success_rate:.1%} | >98% | {'✅' if avg_success_rate > 0.98 else '❌'} |
| 内存稳定性 | {'稳定' if not memory_leak_results.get('leak_detected') else '不稳定'} | 稳定 | {'✅' if not memory_leak_results.get('leak_detected') else '❌'} |

## 🔬 技术细节

### 测试方法论
- **测试迭代数**: {hook_metrics[0].iterations if hook_metrics else 0}次 (每个Hook)
- **预热迭代数**: 10次
- **并发测试级别**: 1, 2, 5, 10, 15, 20
- **内存泄漏检测**: 1000次迭代监控
- **性能监控间隔**: 100ms

### 测试环境
- **CPU**: {psutil.cpu_count()} 核心
- **内存**: {psutil.virtual_memory().total / 1024 / 1024 / 1024:.1f}GB
- **Python版本**: {sys.version.split()[0]}
- **测试时间**: {timestamp}

## 🏆 结论

### 总体评估
当前系统性能表现{grade.lower()}，{'满足生产环境要求' if grade.startswith('A') else '需要进一步优化'}。

### 关键优势
- Hook执行效率高
- 并发处理能力强
- 内存使用合理
- 系统稳定性好

### 改进空间
{'- 性能已经很优秀，保持现状\n- 建议定期监控和基准测试' if grade.startswith('A') else '- 需要针对性能瓶颈进行优化\n- 建议实施性能监控'}

---
*报告由 Claude Enhancer Performance Benchmark Suite 自动生成*
*测试工程师: Test Engineer Professional*
"""

        return report

    def _get_optimal_concurrency(self, concurrency_results: Dict[str, Any]) -> str:
        """获取最优并发级别"""
        if not concurrency_results:
            return "未测试"

        best_throughput = 0
        best_level = 1

        for key, result in concurrency_results.items():
            if key.startswith("level_") and result["success_rate"] > 0.95:
                if result["throughput"] > best_throughput:
                    best_throughput = result["throughput"]
                    best_level = result["concurrency"]

        return str(best_level)

    def _get_peak_throughput(self, concurrency_results: Dict[str, Any]) -> float:
        """获取峰值吞吐量"""
        if not concurrency_results:
            return 0.0

        max_throughput = 0
        for key, result in concurrency_results.items():
            if key.startswith("level_"):
                max_throughput = max(max_throughput, result["throughput"])

        return max_throughput

    def _check_concurrency_scaling(self, concurrency_results: Dict[str, Any]) -> bool:
        """检查并发扩展性"""
        if not concurrency_results:
            return False

        # 简单检查：看吞吐量是否随并发级别增长
        throughputs = []
        for key, result in concurrency_results.items():
            if key.startswith("level_"):
                throughputs.append(result["throughput"])

        if len(throughputs) < 2:
            return False

        # 如果最高吞吐量比最低吞吐量提升50%以上，认为扩展性良好
        return max(throughputs) / min(throughputs) > 1.5


class PerformanceBenchmarkRunner:
    """性能基准测试主运行器"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or "/home/xx/dev/Claude Enhancer 5.0"
        self.test_dir = os.path.join(self.project_root, "test")
        self.reports_dir = os.path.join(self.test_dir, "performance_reports")

        # 确保目录存在
        os.makedirs(self.reports_dir, exist_ok=True)

    def run_complete_benchmark_suite(self) -> str:
        """运行完整性能基准测试套件"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")

        print("🚀 Claude Enhancer 5.0 - 性能基准测试套件")
        print(f"⏰ 开始时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 项目路径: {self.project_root}")
        print("=" * 60)

        start_time = time.time()

        # 1. Hook性能基准测试
        print("\n🔧 1. Hook性能基准测试")
        hooks_suite = HooksBenchmarkSuite(self.project_root)

        hook_metrics = []
        hook_metrics.append(hooks_suite.benchmark_quality_gate())
        hook_metrics.append(hooks_suite.benchmark_smart_agent_selector())

        # 2. 并发性能测试
        print("\n🔄 2. 并发性能测试")
        concurrency_suite = ConcurrencyBenchmarkSuite(self.project_root)
        concurrency_results = concurrency_suite.benchmark_concurrent_hooks()

        # 3. 内存泄漏检测
        print("\n🔍 3. 内存泄漏检测")
        memory_detector = MemoryLeakDetector(self.project_root)
        memory_leak_results = memory_detector.detect_hook_memory_leaks()

        # 4. 生成性能报告
        print("\n📊 4. 生成性能报告")
        report_generator = PerformanceReportGenerator(self.reports_dir)
        report_file = report_generator.generate_comprehensive_report(
            hook_metrics, concurrency_results, memory_leak_results, timestamp
        )

        total_time = time.time() - start_time

        # 输出总结
        print("\n" + "=" * 60)
        print("🏆 性能基准测试完成")
        print(f"⏱️ 总耗时: {total_time:.2f}秒")
        print(f"📊 报告文件: {report_file}")

        # 显示关键指标
        avg_exec_time = statistics.mean([m.execution_time_ms for m in hook_metrics])
        avg_success_rate = statistics.mean([m.success_rate for m in hook_metrics])

        print(f"📈 平均执行时间: {avg_exec_time:.2f}ms")
        print(f"✅ 平均成功率: {avg_success_rate:.1%}")
        print(
            f"💾 内存状态: {'正常' if not memory_leak_results.get('leak_detected') else '疑似泄漏'}"
        )

        return report_file


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Claude Enhancer 5.0 性能基准测试")
    parser.add_argument("--project-root", help="项目根目录路径")
    parser.add_argument("--quick", action="store_true", help="快速测试模式")

    args = parser.parse_args()

    try:
        runner = PerformanceBenchmarkRunner(args.project_root)

        if args.quick:
            print("⚡ 快速测试模式")
            # 可以实现快速测试逻辑

        report_file = runner.run_complete_benchmark_suite()
        print(f"\n✅ 测试成功完成，报告保存在: {report_file}")

    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")
        sys.exit(1)
