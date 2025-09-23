#!/usr/bin/env python3
"""
Claude Enhancer 基准测试套件
建立性能基准线，进行持续性能监控
"""

import time
import json
import statistics
import psutil
import subprocess
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, asdict

# 可选依赖，如果不存在不影响核心功能
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    import pandas as pd

    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False


@dataclass
class BenchmarkResult:
    """基准测试结果"""

    test_name: str
    category: str
    execution_time: float
    memory_usage_mb: float
    cpu_percent: float
    success: bool
    timestamp: str
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class SystemBenchmarks:
    """系统基准测试"""

    def __init__(self):
        self.results: List[BenchmarkResult] = []

    def run_cpu_benchmark(self, duration: float = 1.0) -> BenchmarkResult:
        """CPU密集型基准测试"""
        start_time = time.perf_counter()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024

        # CPU密集型计算
        total = 0
        for i in range(1000000):
            total += i * i

        end_time = time.perf_counter()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        cpu_percent = psutil.cpu_percent(interval=0.1)

        return BenchmarkResult(
            test_name="cpu_intensive_calculation",
            category="system",
            execution_time=end_time - start_time,
            memory_usage_mb=end_memory - start_memory,
            cpu_percent=cpu_percent,
            success=True,
            timestamp=datetime.now().isoformat(),
            metadata={"iterations": 1000000, "calculation": "sum_of_squares"},
        )

    def run_memory_benchmark(self) -> BenchmarkResult:
        """内存分配基准测试"""
        start_time = time.perf_counter()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024

        # 内存密集型操作
        large_list = [i for i in range(1000000)]
        matrix = [[j for j in range(100)] for i in range(1000)]

        end_time = time.perf_counter()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        cpu_percent = psutil.cpu_percent(interval=0.1)

        # 清理内存
        del large_list, matrix

        return BenchmarkResult(
            test_name="memory_allocation",
            category="system",
            execution_time=end_time - start_time,
            memory_usage_mb=end_memory - start_memory,
            cpu_percent=cpu_percent,
            success=True,
            timestamp=datetime.now().isoformat(),
            metadata={"list_size": 1000000, "matrix_size": "1000x100"},
        )

    def run_disk_io_benchmark(self) -> BenchmarkResult:
        """磁盘I/O基准测试"""
        start_time = time.perf_counter()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024

        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "benchmark_file.txt"

            # 写入测试
            test_data = "x" * 1024 * 100  # 100KB数据
            for i in range(100):  # 写入10MB
                with open(test_file, "a") as f:
                    f.write(test_data)

            # 读取测试
            total_read = 0
            with open(test_file, "r") as f:
                while True:
                    chunk = f.read(1024)
                    if not chunk:
                        break
                    total_read += len(chunk)

        end_time = time.perf_counter()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        cpu_percent = psutil.cpu_percent(interval=0.1)

        return BenchmarkResult(
            test_name="disk_io_operations",
            category="system",
            execution_time=end_time - start_time,
            memory_usage_mb=end_memory - start_memory,
            cpu_percent=cpu_percent,
            success=True,
            timestamp=datetime.now().isoformat(),
            metadata={"data_size_mb": 10, "total_read_bytes": total_read},
        )


class HookSystemBenchmarks:
    """Hook系统基准测试"""

    def __init__(self, claude_dir: str = "/home/xx/dev/Perfect21/.claude"):
        self.claude_dir = Path(claude_dir)
        self.results: List[BenchmarkResult] = []

    def run_hook_execution_benchmark(self) -> List[BenchmarkResult]:
        """Hook执行性能基准测试"""
        results = []
        hooks_dir = self.claude_dir / "hooks"

        if not hooks_dir.exists():
            return results

        # 测试现有的Hook脚本
        hook_files = [
            "smart_agent_selector.sh",
            "quality_gate.sh",
            "performance_monitor.sh",
            "error_handler.sh",
            "task_type_detector.sh",
        ]

        for hook_name in hook_files:
            hook_path = hooks_dir / hook_name
            if hook_path.exists():
                result = self._benchmark_single_hook(hook_path)
                if result:
                    results.append(result)

        return results

    def _benchmark_single_hook(self, hook_path: Path) -> Optional[BenchmarkResult]:
        """对单个Hook进行基准测试"""
        try:
            start_time = time.perf_counter()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024

            # 运行Hook（测试模式）
            result = subprocess.run(
                ["bash", str(hook_path), "--test"],
                capture_output=True,
                text=True,
                timeout=10,
                env={"CLAUDE_TEST_MODE": "1", "HOOK_BENCHMARK": "1"},
            )

            end_time = time.perf_counter()
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024
            cpu_percent = psutil.cpu_percent(interval=0.1)

            return BenchmarkResult(
                test_name=f"hook_{hook_path.name}",
                category="hook_system",
                execution_time=end_time - start_time,
                memory_usage_mb=end_memory - start_memory,
                cpu_percent=cpu_percent,
                success=result.returncode == 0,
                timestamp=datetime.now().isoformat(),
                metadata={
                    "return_code": result.returncode,
                    "stdout_length": len(result.stdout),
                    "stderr_length": len(result.stderr),
                },
            )

        except Exception as e:
            return BenchmarkResult(
                test_name=f"hook_{hook_path.name}",
                category="hook_system",
                execution_time=0.0,
                memory_usage_mb=0.0,
                cpu_percent=0.0,
                success=False,
                timestamp=datetime.now().isoformat(),
                metadata={"error": str(e)},
            )

    def run_hook_concurrency_benchmark(self) -> BenchmarkResult:
        """Hook并发执行基准测试"""
        import threading
        import concurrent.futures

        hooks_dir = self.claude_dir / "hooks"
        if not hooks_dir.exists():
            return BenchmarkResult(
                test_name="hook_concurrency",
                category="hook_system",
                execution_time=0.0,
                memory_usage_mb=0.0,
                cpu_percent=0.0,
                success=False,
                timestamp=datetime.now().isoformat(),
                metadata={"error": "hooks directory not found"},
            )

        start_time = time.perf_counter()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024

        # 选择几个轻量级的Hook进行并发测试
        test_hooks = []
        for hook_file in hooks_dir.glob("*.sh"):
            if hook_file.name in ["performance_monitor.sh", "error_handler.sh"]:
                test_hooks.append(hook_file)

        if not test_hooks:
            return BenchmarkResult(
                test_name="hook_concurrency",
                category="hook_system",
                execution_time=0.0,
                memory_usage_mb=0.0,
                cpu_percent=0.0,
                success=False,
                timestamp=datetime.now().isoformat(),
                metadata={"error": "no suitable hooks found"},
            )

        # 并发执行Hook
        success_count = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for hook in test_hooks:
                future = executor.submit(self._run_hook_concurrent, hook)
                futures.append(future)

            for future in concurrent.futures.as_completed(futures):
                if future.result():
                    success_count += 1

        end_time = time.perf_counter()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
        cpu_percent = psutil.cpu_percent(interval=0.1)

        return BenchmarkResult(
            test_name="hook_concurrency",
            category="hook_system",
            execution_time=end_time - start_time,
            memory_usage_mb=end_memory - start_memory,
            cpu_percent=cpu_percent,
            success=success_count > 0,
            timestamp=datetime.now().isoformat(),
            metadata={
                "total_hooks": len(test_hooks),
                "successful_hooks": success_count,
                "success_rate": success_count / len(test_hooks) if test_hooks else 0,
            },
        )

    def _run_hook_concurrent(self, hook_path: Path) -> bool:
        """并发运行单个Hook"""
        try:
            result = subprocess.run(
                ["bash", str(hook_path), "--test"],
                capture_output=True,
                text=True,
                timeout=5,
                env={"CLAUDE_TEST_MODE": "1", "HOOK_CONCURRENT_TEST": "1"},
            )
            return result.returncode == 0
        except Exception:
            return False


class PerformanceComparisonBenchmarks:
    """性能对比基准测试"""

    def __init__(self, claude_dir: str = "/home/xx/dev/Perfect21/.claude"):
        self.claude_dir = Path(claude_dir)
        self.results: List[BenchmarkResult] = []

    def compare_cleanup_scripts(self) -> List[BenchmarkResult]:
        """对比不同版本的清理脚本性能"""
        results = []
        scripts_dir = self.claude_dir / "scripts"

        cleanup_scripts = [
            "cleanup.sh",
            "performance_optimized_cleanup.sh",
            "ultra_optimized_cleanup.sh",
        ]

        for script_name in cleanup_scripts:
            script_path = scripts_dir / script_name
            if script_path.exists():
                result = self._benchmark_cleanup_script(script_path)
                if result:
                    results.append(result)

        return results

    def _benchmark_cleanup_script(self, script_path: Path) -> Optional[BenchmarkResult]:
        """对单个清理脚本进行基准测试"""
        try:
            # 创建临时测试环境
            with tempfile.TemporaryDirectory() as temp_dir:
                test_claude_dir = Path(temp_dir) / ".claude"
                test_claude_dir.mkdir(parents=True)

                # 创建一些测试文件用于清理
                for i in range(10):
                    (test_claude_dir / f"temp_file_{i}.tmp").write_text("test data")

                start_time = time.perf_counter()
                start_memory = psutil.Process().memory_info().rss / 1024 / 1024

                # 运行清理脚本
                result = subprocess.run(
                    ["bash", str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=temp_dir,
                    env={"CLAUDE_TEST_MODE": "1", "CLEANUP_BENCHMARK": "1"},
                )

                end_time = time.perf_counter()
                end_memory = psutil.Process().memory_info().rss / 1024 / 1024
                cpu_percent = psutil.cpu_percent(interval=0.1)

                return BenchmarkResult(
                    test_name=f"cleanup_{script_path.name}",
                    category="performance_comparison",
                    execution_time=end_time - start_time,
                    memory_usage_mb=end_memory - start_memory,
                    cpu_percent=cpu_percent,
                    success=result.returncode == 0,
                    timestamp=datetime.now().isoformat(),
                    metadata={
                        "script_name": script_path.name,
                        "return_code": result.returncode,
                        "stdout_length": len(result.stdout),
                    },
                )

        except Exception as e:
            return BenchmarkResult(
                test_name=f"cleanup_{script_path.name}",
                category="performance_comparison",
                execution_time=0.0,
                memory_usage_mb=0.0,
                cpu_percent=0.0,
                success=False,
                timestamp=datetime.now().isoformat(),
                metadata={"error": str(e)},
            )


class BenchmarkAnalyzer:
    """基准测试分析器"""

    def __init__(self):
        self.historical_data: List[Dict[str, Any]] = []

    def load_historical_data(self, data_file: Path) -> bool:
        """加载历史基准数据"""
        try:
            if data_file.exists():
                with open(data_file, "r") as f:
                    self.historical_data = json.load(f)
                return True
        except Exception:
            pass
        return False

    def save_benchmark_data(self, results: List[BenchmarkResult], data_file: Path):
        """保存基准测试数据"""
        benchmark_session = {
            "timestamp": datetime.now().isoformat(),
            "results": [asdict(result) for result in results],
            "system_info": {
                "cpu_count": psutil.cpu_count(),
                "memory_total_gb": psutil.virtual_memory().total / (1024**3),
                "python_version": __import__("sys").version,
            },
        }

        self.historical_data.append(benchmark_session)

        # 保存到文件
        data_file.parent.mkdir(parents=True, exist_ok=True)
        with open(data_file, "w") as f:
            json.dump(self.historical_data, f, indent=2)

    def analyze_performance_trends(self) -> Dict[str, Any]:
        """分析性能趋势"""
        if len(self.historical_data) < 2:
            return {"message": "需要至少2次基准测试数据来分析趋势"}

        analysis = {
            "total_sessions": len(self.historical_data),
            "date_range": {
                "start": self.historical_data[0]["timestamp"],
                "end": self.historical_data[-1]["timestamp"],
            },
            "trends": {},
            "performance_regression": [],
            "performance_improvement": [],
        }

        # 分析每个测试的趋势
        test_performance = {}
        for session in self.historical_data:
            for result in session["results"]:
                test_name = result["test_name"]
                if test_name not in test_performance:
                    test_performance[test_name] = []
                test_performance[test_name].append(
                    {
                        "timestamp": session["timestamp"],
                        "execution_time": result["execution_time"],
                        "memory_usage": result["memory_usage_mb"],
                        "success": result["success"],
                    }
                )

        # 计算趋势
        for test_name, history in test_performance.items():
            if len(history) >= 2:
                recent_times = [h["execution_time"] for h in history[-3:]]
                older_times = (
                    [h["execution_time"] for h in history[:-3]]
                    if len(history) > 3
                    else history[:-1]
                )

                if older_times:
                    recent_avg = statistics.mean(recent_times)
                    older_avg = statistics.mean(older_times)
                    change_percent = ((recent_avg - older_avg) / older_avg) * 100

                    analysis["trends"][test_name] = {
                        "recent_avg_time": recent_avg,
                        "historical_avg_time": older_avg,
                        "change_percent": change_percent,
                        "trend": "improving"
                        if change_percent < -5
                        else "degrading"
                        if change_percent > 5
                        else "stable",
                    }

                    # 检测性能回归或改进
                    if change_percent > 20:  # 20%以上的性能下降
                        analysis["performance_regression"].append(
                            {
                                "test_name": test_name,
                                "degradation_percent": change_percent,
                            }
                        )
                    elif change_percent < -20:  # 20%以上的性能提升
                        analysis["performance_improvement"].append(
                            {
                                "test_name": test_name,
                                "improvement_percent": abs(change_percent),
                            }
                        )

        return analysis

    def generate_performance_report(
        self, results: List[BenchmarkResult]
    ) -> Dict[str, Any]:
        """生成性能报告"""
        report = {
            "summary": {
                "total_tests": len(results),
                "successful_tests": sum(1 for r in results if r.success),
                "failed_tests": sum(1 for r in results if not r.success),
                "success_rate": 0.0,
            },
            "performance_metrics": {
                "execution_times": {},
                "memory_usage": {},
                "cpu_usage": {},
            },
            "category_analysis": {},
            "recommendations": [],
        }

        if results:
            report["summary"]["success_rate"] = report["summary"][
                "successful_tests"
            ] / len(results)

            # 成功的测试结果
            successful_results = [r for r in results if r.success]

            if successful_results:
                execution_times = [r.execution_time for r in successful_results]
                memory_usage = [r.memory_usage_mb for r in successful_results]
                cpu_usage = [
                    r.cpu_percent
                    for r in successful_results
                    if r.cpu_percent is not None
                ]

                report["performance_metrics"]["execution_times"] = {
                    "mean": statistics.mean(execution_times),
                    "median": statistics.median(execution_times),
                    "min": min(execution_times),
                    "max": max(execution_times),
                    "std_dev": statistics.stdev(execution_times)
                    if len(execution_times) > 1
                    else 0,
                }

                report["performance_metrics"]["memory_usage"] = {
                    "mean": statistics.mean(memory_usage),
                    "median": statistics.median(memory_usage),
                    "min": min(memory_usage),
                    "max": max(memory_usage),
                }

                if cpu_usage:
                    report["performance_metrics"]["cpu_usage"] = {
                        "mean": statistics.mean(cpu_usage),
                        "median": statistics.median(cpu_usage),
                        "min": min(cpu_usage),
                        "max": max(cpu_usage),
                    }

                # 按类别分析
                categories = {}
                for result in successful_results:
                    category = result.category
                    if category not in categories:
                        categories[category] = []
                    categories[category].append(result)

                for category, cat_results in categories.items():
                    cat_times = [r.execution_time for r in cat_results]
                    report["category_analysis"][category] = {
                        "test_count": len(cat_results),
                        "avg_time": statistics.mean(cat_times),
                        "total_time": sum(cat_times),
                    }

        # 生成建议
        self._generate_recommendations(report, results)

        return report

    def _generate_recommendations(
        self, report: Dict[str, Any], results: List[BenchmarkResult]
    ):
        """生成性能优化建议"""
        recommendations = []

        # 基于成功率的建议
        success_rate = report["summary"]["success_rate"]
        if success_rate < 0.9:
            recommendations.append(
                {
                    "category": "Reliability",
                    "priority": "HIGH",
                    "issue": f"基准测试成功率较低: {success_rate:.1%}",
                    "recommendation": "调查失败的测试用例，修复潜在的稳定性问题",
                }
            )

        # 基于执行时间的建议
        exec_metrics = report["performance_metrics"].get("execution_times", {})
        if exec_metrics:
            max_time = exec_metrics.get("max", 0)
            mean_time = exec_metrics.get("mean", 0)

            if max_time > 10.0:  # 超过10秒的测试
                recommendations.append(
                    {
                        "category": "Performance",
                        "priority": "MEDIUM",
                        "issue": f"发现执行时间过长的测试: {max_time:.2f}秒",
                        "recommendation": "优化慢速操作，考虑异步执行或缓存",
                    }
                )

            if mean_time > 2.0:  # 平均时间超过2秒
                recommendations.append(
                    {
                        "category": "Performance",
                        "priority": "MEDIUM",
                        "issue": f"平均执行时间较长: {mean_time:.2f}秒",
                        "recommendation": "整体性能优化，减少不必要的操作",
                    }
                )

        # 基于内存使用的建议
        memory_metrics = report["performance_metrics"].get("memory_usage", {})
        if memory_metrics:
            max_memory = memory_metrics.get("max", 0)
            if max_memory > 100:  # 超过100MB
                recommendations.append(
                    {
                        "category": "Memory",
                        "priority": "LOW",
                        "issue": f"内存使用量较高: {max_memory:.1f}MB",
                        "recommendation": "检查内存泄漏，优化内存使用",
                    }
                )

        report["recommendations"] = recommendations


class ComprehensiveBenchmarkSuite:
    """综合基准测试套件"""

    def __init__(self, claude_dir: str = "/home/xx/dev/Perfect21/.claude"):
        self.claude_dir = claude_dir
        self.system_bench = SystemBenchmarks()
        self.hook_bench = HookSystemBenchmarks(claude_dir)
        self.comparison_bench = PerformanceComparisonBenchmarks(claude_dir)
        self.analyzer = BenchmarkAnalyzer()

    def run_full_benchmark_suite(self) -> Dict[str, Any]:
        """运行完整的基准测试套件"""
        print("🏃 开始运行综合基准测试套件...")
        print("=" * 80)

        all_results = []

        # 1. 系统基准测试
        print("🖥️  运行系统基准测试...")
        all_results.append(self.system_bench.run_cpu_benchmark())
        all_results.append(self.system_bench.run_memory_benchmark())
        all_results.append(self.system_bench.run_disk_io_benchmark())

        # 2. Hook系统基准测试
        print("🔗 运行Hook系统基准测试...")
        hook_results = self.hook_bench.run_hook_execution_benchmark()
        all_results.extend(hook_results)

        concurrency_result = self.hook_bench.run_hook_concurrency_benchmark()
        all_results.append(concurrency_result)

        # 3. 性能对比基准测试
        print("⚖️  运行性能对比基准测试...")
        comparison_results = self.comparison_bench.compare_cleanup_scripts()
        all_results.extend(comparison_results)

        # 4. 生成报告
        print("📊 生成基准测试报告...")
        report = self.analyzer.generate_performance_report(all_results)

        # 5. 保存数据
        data_file = (
            Path(self.claude_dir).parent
            / "test"
            / "claude_enhancer"
            / "benchmark_data.json"
        )
        self.analyzer.save_benchmark_data(all_results, data_file)

        # 6. 加载历史数据并分析趋势
        self.analyzer.load_historical_data(data_file)
        trends = self.analyzer.analyze_performance_trends()

        # 合并报告
        final_report = {
            "timestamp": datetime.now().isoformat(),
            "benchmark_results": [asdict(result) for result in all_results],
            "performance_report": report,
            "trend_analysis": trends,
            "data_file": str(data_file),
        }

        print("✅ 基准测试套件执行完成!")
        return final_report

    def save_report(
        self, report: Dict[str, Any], filename: str = "benchmark_report.json"
    ) -> Path:
        """保存基准测试报告"""
        report_path = (
            Path(self.claude_dir).parent / "test" / "claude_enhancer" / filename
        )
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"📄 基准测试报告已保存到: {report_path}")
        return report_path


def main():
    """主函数"""
    try:
        suite = ComprehensiveBenchmarkSuite()
        report = suite.run_full_benchmark_suite()
        report_path = suite.save_report(report)

        # 打印摘要
        print("\n" + "=" * 80)
        print("📈 基准测试摘要")
        print("=" * 80)

        perf_report = report.get("performance_report", {})
        summary = perf_report.get("summary", {})

        print(f"总测试数量: {summary.get('total_tests', 0)}")
        print(f"成功测试: {summary.get('successful_tests', 0)}")
        print(f"成功率: {summary.get('success_rate', 0):.1%}")

        exec_metrics = perf_report.get("performance_metrics", {}).get(
            "execution_times", {}
        )
        if exec_metrics:
            print(f"平均执行时间: {exec_metrics.get('mean', 0):.4f}s")
            print(f"最快测试: {exec_metrics.get('min', 0):.4f}s")
            print(f"最慢测试: {exec_metrics.get('max', 0):.4f}s")

        # 显示类别分析
        category_analysis = perf_report.get("category_analysis", {})
        if category_analysis:
            print("\n📊 按类别分析:")
            for category, stats in category_analysis.items():
                print(
                    f"  {category}: {stats['test_count']}个测试, 平均时间: {stats['avg_time']:.4f}s"
                )

        # 显示建议
        recommendations = perf_report.get("recommendations", [])
        if recommendations:
            print(f"\n💡 性能优化建议 ({len(recommendations)}条):")
            for rec in recommendations[:3]:  # 显示前3条
                print(f"  [{rec['priority']}] {rec['issue']}")

        print(f"\n📄 详细报告: {report_path}")
        return True

    except Exception as e:
        print(f"❌ 基准测试执行失败: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
