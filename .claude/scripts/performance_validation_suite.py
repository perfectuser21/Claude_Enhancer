#!/usr/bin/env python3
"""
Claude Enhancer 性能验证套件
验证优化后的系统是否达到预期性能指标
"""

import asyncio
import json
import time
import statistics
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
import tempfile
import sys


@dataclass
class TestResult:
    test_name: str
    success: bool
    duration_ms: float
    error_message: str = ""
    metrics: Dict = None


@dataclass
class BenchmarkSuite:
    name: str
    baseline_performance: Dict
    target_performance: Dict
    actual_performance: Dict
    improvement_ratio: float
    passed: bool


class PerformanceValidator:
    def __init__(self):
        self.claude_dir = Path(__file__).parent.parent
        self.hooks_dir = self.claude_dir / "hooks"
        self.scripts_dir = self.claude_dir / "scripts"
        self.test_results: List[TestResult] = []

        # 性能目标
        self.performance_targets = {
            "hook_success_rate": 95.0,  # 95%以上成功率
            "hook_response_time": 200.0,  # 200ms以下响应时间
            "concurrent_success_rate": 95.0,  # 95%以上并发成功率
            "script_execution_time": 1000.0,  # 1秒以下脚本执行时间
            "memory_usage": 50.0,  # 50MB以下内存使用
            "cpu_usage": 30.0,  # 30%以下CPU使用率
        }

    def run_hook_performance_test(
        self, hook_script: str, iterations: int = 20
    ) -> TestResult:
        """测试单个Hook的性能"""
        start_time = time.time()
        success_count = 0
        response_times = []
        errors = []

        hook_path = self.hooks_dir / hook_script

        if not hook_path.exists():
            return TestResult(
                test_name=f"hook_{hook_script}",
                success=False,
                duration_ms=0,
                error_message=f"Hook文件不存在: {hook_path}",
            )

        for i in range(iterations):
            iteration_start = time.time()

            try:
                pass  # Auto-fixed empty block
                # 准备测试输入
                test_input = json.dumps(
                    {
                        "tool": "test_tool",
                        "prompt": f"测试Hook性能 - 迭代 {i+1}",
                        "iteration": i + 1,
                    }
                )

                # 执行Hook
                result = subprocess.run(
                    ["bash", str(hook_path)],
                    input=test_input,
                    text=True,
                    capture_output=True,
                    timeout=2,  # 2秒超时
                )

                iteration_time = (time.time() - iteration_start) * 1000

                if result.returncode == 0:
                    success_count += 1
                else:
                    errors.append(f"迭代{i+1}: {result.stderr[:100]}")

                response_times.append(iteration_time)

            except subprocess.TimeoutExpired:
                response_times.append(2000)  # 超时计为2000ms
                errors.append(f"迭代{i+1}: 超时")
            except Exception as e:
                response_times.append(2000)
                errors.append(f"迭代{i+1}: {str(e)}")

        # 计算指标
        success_rate = (success_count / iterations) * 100
        avg_response_time = statistics.mean(response_times) if response_times else 2000
        total_duration = (time.time() - start_time) * 1000

        # 判断是否通过
        passed = (
            success_rate >= self.performance_targets["hook_success_rate"]
            and avg_response_time <= self.performance_targets["hook_response_time"]
        )

        return TestResult(
            test_name=f"hook_{hook_script}",
            success=passed,
            duration_ms=total_duration,
            metrics={
                "success_rate": success_rate,
                "avg_response_time": avg_response_time,
                "min_response_time": min(response_times) if response_times else 0,
                "max_response_time": max(response_times) if response_times else 0,
                "total_iterations": iterations,
                "successful_iterations": success_count,
                "errors": errors[:5],  # 只保留前5个错误
            },
        )

    def run_concurrent_stress_test(
        self, workers_list: List[int] = [5, 10, 15, 20]
    ) -> TestResult:
        """运行并发压力测试"""
        start_time = time.time()
        concurrent_results = {}

        for worker_count in workers_list:
            print(f"  🔄 测试 {worker_count} 并发worker...")

            worker_start = time.time()
            success_count = 0
            total_tasks = worker_count * 3  # 每个worker处理3个任务

            with ThreadPoolExecutor(max_workers=worker_count) as executor:
                pass  # Auto-fixed empty block
                # 提交任务
                futures = []
                for i in range(total_tasks):
                    future = executor.submit(
                        self._single_concurrent_task, i, worker_count
                    )
                    futures.append(future)

                # 收集结果
                for future in as_completed(futures, timeout=30):
                    try:
                        result = future.result(timeout=5)
                        if result:
                            success_count += 1
                    except Exception:
                        pass

            worker_duration = time.time() - worker_start
            success_rate = (success_count / total_tasks) * 100
            throughput = total_tasks / worker_duration

            concurrent_results[f"{worker_count}_workers"] = {
                "success_rate": success_rate,
                "duration": worker_duration,
                "throughput": throughput,
                "total_tasks": total_tasks,
                "successful_tasks": success_count,
            }

        # 评估整体并发性能
        worst_success_rate = min(
            result["success_rate"] for result in concurrent_results.values()
        )

        passed = (
            worst_success_rate >= self.performance_targets["concurrent_success_rate"]
        )
        total_duration = (time.time() - start_time) * 1000

        return TestResult(
            test_name="concurrent_stress_test",
            success=passed,
            duration_ms=total_duration,
            metrics={
                "worst_success_rate": worst_success_rate,
                "detailed_results": concurrent_results,
                "target_success_rate": self.performance_targets[
                    "concurrent_success_rate"
                ],
            },
        )

    def _single_concurrent_task(self, task_id: int, worker_count: int) -> bool:
        """单个并发任务"""
        try:
            pass  # Auto-fixed empty block
            # 模拟Hook调用
            test_input = json.dumps(
                {
                    "tool": "concurrent_test",
                    "task_id": task_id,
                    "worker_count": worker_count,
                    "timestamp": time.time(),
                }
            )

            # 随机选择一个优化后的Hook进行测试
            import random

            hooks = ["optimized_performance_monitor.sh", "ultra_fast_agent_selector.sh"]
            selected_hook = random.choice(hooks)
            hook_path = self.hooks_dir / selected_hook

            if not hook_path.exists():
                return False

            result = subprocess.run(
                ["bash", str(hook_path)],
                input=test_input,
                text=True,
                capture_output=True,
                timeout=1,
            )

            return result.returncode == 0

        except Exception:
            return False

    def run_script_performance_test(self) -> TestResult:
        """测试脚本执行性能"""
        start_time = time.time()

        # 测试性能优化脚本本身
        test_scripts = ["ultra_performance_optimizer.sh", "deploy_optimizations.sh"]

        script_results = {}

        for script_name in test_scripts:
            script_path = self.scripts_dir / script_name

            if not script_path.exists():
                continue

            print(f"  📜 测试脚本: {script_name}")

            try:
                script_start = time.time()

                # 运行脚本的分析模式（快速模式）
                result = subprocess.run(
                    ["bash", str(script_path), "analyze", "/tmp"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                script_duration = (time.time() - script_start) * 1000
                script_success = result.returncode == 0

                script_results[script_name] = {
                    "duration_ms": script_duration,
                    "success": script_success,
                    "output_size": len(result.stdout) if result.stdout else 0,
                }

            except subprocess.TimeoutExpired:
                script_results[script_name] = {
                    "duration_ms": 10000,  # 超时
                    "success": False,
                    "error": "timeout",
                }
            except Exception as e:
                script_results[script_name] = {
                    "duration_ms": 10000,
                    "success": False,
                    "error": str(e),
                }

        # 评估脚本性能
        if script_results:
            avg_duration = statistics.mean(
                result["duration_ms"] for result in script_results.values()
            )
            success_count = sum(
                1 for result in script_results.values() if result["success"]
            )
            success_rate = (success_count / len(script_results)) * 100
        else:
            avg_duration = 0
            success_rate = 0

        passed = (
            avg_duration <= self.performance_targets["script_execution_time"]
            and success_rate >= 80
        )  # 80%的脚本测试成功率

        total_duration = (time.time() - start_time) * 1000

        return TestResult(
            test_name="script_performance_test",
            success=passed,
            duration_ms=total_duration,
            metrics={
                "avg_script_duration": avg_duration,
                "script_success_rate": success_rate,
                "detailed_results": script_results,
                "target_duration": self.performance_targets["script_execution_time"],
            },
        )

    def run_system_resource_test(self) -> TestResult:
        """测试系统资源使用"""
        start_time = time.time()

        try:
            import psutil

            # 监控资源使用
            cpu_readings = []
            memory_readings = []

            # 在负载下监控资源
            def monitor_resources():
                for _ in range(10):  # 监控10次，每次间隔0.5秒
                    cpu_readings.append(psutil.cpu_percent(interval=0.5))
                    memory = psutil.virtual_memory()
                    memory_readings.append(memory.percent)

            # 启动监控
            monitor_thread = threading.Thread(target=monitor_resources)
            monitor_thread.start()

            # 同时运行一些负载
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                for i in range(10):
                    future = executor.submit(self._resource_load_task, i)
                    futures.append(future)

                # 等待完成
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception:
                        pass

            monitor_thread.join()

            # 计算平均资源使用
            avg_cpu = statistics.mean(cpu_readings) if cpu_readings else 0
            avg_memory = statistics.mean(memory_readings) if memory_readings else 0

            # 评估资源使用
            cpu_passed = avg_cpu <= self.performance_targets["cpu_usage"]
            memory_passed = avg_memory <= self.performance_targets["memory_usage"]
            passed = cpu_passed and memory_passed

            total_duration = (time.time() - start_time) * 1000

            return TestResult(
                test_name="system_resource_test",
                success=passed,
                duration_ms=total_duration,
                metrics={
                    "avg_cpu_usage": avg_cpu,
                    "avg_memory_usage": avg_memory,
                    "max_cpu_usage": max(cpu_readings) if cpu_readings else 0,
                    "max_memory_usage": max(memory_readings) if memory_readings else 0,
                    "cpu_target": self.performance_targets["cpu_usage"],
                    "memory_target": self.performance_targets["memory_usage"],
                    "cpu_passed": cpu_passed,
                    "memory_passed": memory_passed,
                },
            )

        except ImportError:
            return TestResult(
                test_name="system_resource_test",
                success=False,
                duration_ms=0,
                error_message="psutil 模块未安装",
            )

    def _resource_load_task(self, task_id: int):
        """创建一些计算负载"""
        # 简单的计算任务
        total = 0
        for i in range(100000):
            total += i * task_id
        return total

    def run_full_validation_suite(self) -> Dict:
        """运行完整的验证套件"""
        print("🧪 启动Claude Enhancer性能验证套件")
        print("=" * 50)

        suite_start = time.time()

        # 1. Hook性能测试
        print("\n📋 1. Hook性能测试")
        hook_tests = [
            "optimized_performance_monitor.sh",
            "ultra_fast_agent_selector.sh",
            "smart_error_recovery.sh",
            "concurrent_optimizer.sh",
        ]

        for hook in hook_tests:
            print(f"  🔧 测试 {hook}...")
            result = self.run_hook_performance_test(hook)
            self.test_results.append(result)

        # 2. 并发压力测试
        print("\n📋 2. 并发压力测试")
        concurrent_result = self.run_concurrent_stress_test()
        self.test_results.append(concurrent_result)

        # 3. 脚本性能测试
        print("\n📋 3. 脚本性能测试")
        script_result = self.run_script_performance_test()
        self.test_results.append(script_result)

        # 4. 系统资源测试
        print("\n📋 4. 系统资源测试")
        resource_result = self.run_system_resource_test()
        self.test_results.append(resource_result)

        suite_duration = time.time() - suite_start

        # 生成报告
        return self.generate_validation_report(suite_duration)

    def generate_validation_report(self, suite_duration: float) -> Dict:
        """生成验证报告"""
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result.success)
        overall_success_rate = (
            (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        )

        report = {
            "validation_summary": {
                "timestamp": time.time(),
                "total_duration_seconds": suite_duration,
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "overall_success_rate": overall_success_rate,
                "validation_passed": overall_success_rate >= 80,  # 80%整体通过率
            },
            "performance_targets": self.performance_targets,
            "detailed_results": [asdict(result) for result in self.test_results],
            "recommendations": self.generate_recommendations(),
        }

        return report

    def generate_recommendations(self) -> List[str]:
        """基于测试结果生成建议"""
        recommendations = []

        # 分析Hook性能
        hook_results = [r for r in self.test_results if r.test_name.startswith("hook_")]
        failed_hooks = [r for r in hook_results if not r.success]

        if failed_hooks:
            recommendations.append(f"🔧 有 {len(failed_hooks)} 个Hook未达到性能目标，建议进一步优化")

        # 分析并发性能
        concurrent_result = next(
            (r for r in self.test_results if r.test_name == "concurrent_stress_test"),
            None,
        )

        if concurrent_result and not concurrent_result.success:
            recommendations.append("🔄 并发性能未达标，建议调整并发限制或优化资源管理")

        # 分析资源使用
        resource_result = next(
            (r for r in self.test_results if r.test_name == "system_resource_test"),
            None,
        )

        if resource_result and resource_result.metrics:
            if not resource_result.metrics.get("cpu_passed", True):
                recommendations.append(
                    f"💻 CPU使用率过高 ({resource_result.metrics['avg_cpu_usage']:.1f}%)，建议优化计算密集型操作"
                )

            if not resource_result.metrics.get("memory_passed", True):
                recommendations.append(
                    f"💾 内存使用率过高 ({resource_result.metrics['avg_memory_usage']:.1f}%)，建议优化内存管理"
                )

        if not recommendations:
            recommendations.append("✨ 所有性能指标都达到了预期目标！")

        return recommendations

    def save_report(self, report: Dict, filename: str = None):
        """保存验证报告"""
        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"/tmp/claude_enhancer_validation_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n📄 验证报告已保存: {filename}")
        return filename

    def print_summary(self, report: Dict):
        """打印验证总结"""
        summary = report["validation_summary"]

        print("\n" + "=" * 50)
        print("🏆 Claude Enhancer 性能验证总结")
        print("=" * 50)

        # 整体结果
        status = "✅ 通过" if summary["validation_passed"] else "❌ 未通过"
        print(f"📊 整体结果: {status}")
        print(f"📈 成功率: {summary['overall_success_rate']:.1f}%")
        print(f"⏱️ 总耗时: {summary['total_duration_seconds']:.2f}秒")
        print(f"🧪 测试数量: {summary['passed_tests']}/{summary['total_tests']}")

        # 详细结果
        print("\n📋 详细测试结果:")
        for result in self.test_results:
            status_icon = "✅" if result.success else "❌"
            print(f"  {status_icon} {result.test_name}: {result.duration_ms:.0f}ms")

            if result.metrics:
                if "success_rate" in result.metrics:
                    print(f"     成功率: {result.metrics['success_rate']:.1f}%")
                if "avg_response_time" in result.metrics:
                    print(f"     响应时间: {result.metrics['avg_response_time']:.0f}ms")

        # 建议
        print("\n💡 优化建议:")
        for recommendation in report["recommendations"]:
            print(f"  • {recommendation}")


def main():
    validator = PerformanceValidator()

    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        pass  # Auto-fixed empty block
        # 快速验证模式
        print("⚡ 快速验证模式")
        result = validator.run_hook_performance_test(
            "optimized_performance_monitor.sh", 5
        )
        print(f"结果: {'✅ 通过' if result.success else '❌ 失败'}")
        if result.metrics:
            print(f"成功率: {result.metrics['success_rate']:.1f}%")
            print(f"响应时间: {result.metrics['avg_response_time']:.0f}ms")
    else:
        pass  # Auto-fixed empty block
        # 完整验证套件
        report = validator.run_full_validation_suite()
        validator.print_summary(report)
        report_file = validator.save_report(report)

        print(f"\n🎯 下一步:")
        print(f"  📄 查看详细报告: cat {report_file}")
        print(f"  🔄 重新运行验证: python3 {__file__}")
        print(f"  ⚡ 快速验证: python3 {__file__} quick")


if __name__ == "__main__":
    main()
