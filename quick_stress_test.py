#!/usr/bin/env python3
"""
Claude Enhancer 快速压力测试
============================

5分钟内完成的核心性能检查，适用于：
- 日常开发检查
- CI/CD管道集成
- 快速性能验证

使用方法:
  python3 quick_stress_test.py
  python3 quick_stress_test.py --minimal  # 1分钟极简测试
"""

import os
import sys
import time
import json
import subprocess
import statistics
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import psutil


class QuickStressTest:
    """快速压力测试器"""

    def __init__(self, minimal=False):
        self.minimal = minimal
        self.project_root = Path("/home/xx/dev/Claude_Enhancer")
        self.hook_dir = self.project_root / ".claude" / "hooks"

        # 测试配置
        if minimal:
            self.config = {
                "hook_samples": 5,
                "concurrent_levels": [5, 10],
                "memory_sizes": [1],  # MB
                "stability_seconds": 30,
            }
        else:
            self.config = {
                "hook_samples": 20,
                "concurrent_levels": [5, 10, 20],
                "memory_sizes": [1, 10],  # MB
                "stability_seconds": 60,
            }

    def run_command(self, cmd, timeout=5):
        """执行命令并测量性能"""
        start = time.time()
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout
            )
            duration = (time.time() - start) * 1000  # ms
            return {
                "success": result.returncode == 0,
                "duration_ms": duration,
                "error": result.stderr if result.returncode != 0 else None,
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "duration_ms": timeout * 1000, "error": "Timeout"}
        except Exception as e:
            return {"success": False, "duration_ms": 0, "error": str(e)}

    def test_core_hooks(self):
        """测试核心Hook性能"""
        print("🔧 Testing Core Hooks...")

        # 选择关键Hook进行测试
        core_hooks = [
            "smart_agent_selector.sh",
            "quality_gate.sh",
            "performance_monitor.sh",
            "error_handler.sh",
        ]

        results = {}

        for hook in core_hooks:
            hook_path = self.hook_dir / hook
            if not hook_path.exists():
                continue

            print(f"  Testing {hook}...")
            times = []

            for i in range(self.config["hook_samples"]):
                result = self.run_command(f"bash {hook_path}")
                if result["success"]:
                    times.append(result["duration_ms"])

            if times:
                results[hook] = {
                    "avg_ms": statistics.mean(times),
                    "max_ms": max(times),
                    "success_rate": len(times) / self.config["hook_samples"] * 100,
                }
                print(
                    f"    ✓ Avg: {results[hook]['avg_ms']:.1f}ms, "
                    f"Success: {results[hook]['success_rate']:.0f}%"
                )
            else:
                results[hook] = {"avg_ms": 0, "max_ms": 0, "success_rate": 0}
                print(f"    ✗ Failed")

        return results

    def test_concurrency(self):
        """测试并发性能"""
        print("🔀 Testing Concurrency...")

        hook_path = self.hook_dir / "performance_monitor.sh"
        if not hook_path.exists():
            print("  ⚠️  performance_monitor.sh not found")
            return {}

        results = {}

        for level in self.config["concurrent_levels"]:
            print(f"  Testing {level} concurrent requests...")

            start_time = time.time()
            success_count = 0

            with ThreadPoolExecutor(max_workers=level) as executor:
                futures = [
                    executor.submit(self.run_command, f"bash {hook_path}", 3)
                    for _ in range(level)
                ]

                for future in futures:
                    result = future.result()
                    if result["success"]:
                        success_count += 1

            total_time = time.time() - start_time
            throughput = level / total_time if total_time > 0 else 0
            success_rate = success_count / level * 100

            results[f"concurrent_{level}"] = {
                "throughput_rps": throughput,
                "success_rate": success_rate,
                "total_time_s": total_time,
            }

            print(
                f"    ✓ Throughput: {throughput:.1f} RPS, "
                f"Success: {success_rate:.0f}%"
            )

        return results

    def test_memory_usage(self):
        """测试内存使用"""
        print("💾 Testing Memory Usage...")

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 模拟内存压力
        data_blocks = []
        for size_mb in self.config["memory_sizes"]:
            print(f"  Creating {size_mb}MB data block...")

            # 创建指定大小的数据
            block_size = size_mb * 1024 * 1024
            data_block = "x" * block_size
            data_blocks.append(data_block)

            current_memory = process.memory_info().rss / 1024 / 1024
            memory_delta = current_memory - initial_memory

            print(f"    Memory delta: +{memory_delta:.1f}MB")

        # 清理并检查内存释放
        del data_blocks
        import gc

        gc.collect()

        final_memory = process.memory_info().rss / 1024 / 1024
        final_delta = final_memory - initial_memory

        result = {
            "initial_memory_mb": initial_memory,
            "final_memory_mb": final_memory,
            "memory_delta_mb": final_delta,
            "cleanup_effective": final_delta < 10,  # 10MB以内认为清理有效
        }

        print(f"  Final memory delta: {final_delta:.1f}MB")

        return result

    def test_config_loading(self):
        """测试配置加载性能"""
        print("📋 Testing Config Loading...")

        config_file = self.project_root / ".claude" / "config" / "unified_main.yaml"
        if not config_file.exists():
            config_file = self.project_root / ".claude" / "settings.json"

        if not config_file.exists():
            print("  ⚠️  No config file found")
            return {}

        times = []
        for i in range(10):
            if config_file.suffix == ".yaml":
                cmd = (
                    f"python3 -c 'import yaml; yaml.safe_load(open(\"{config_file}\"))'"
                )
            else:
                cmd = f"python3 -c 'import json; json.load(open(\"{config_file}\"))'"

            result = self.run_command(cmd, timeout=2)
            if result["success"]:
                times.append(result["duration_ms"])

        if times:
            result = {
                "avg_load_time_ms": statistics.mean(times),
                "max_load_time_ms": max(times),
                "success_rate": len(times) / 10 * 100,
            }
            print(f"  ✓ Avg load time: {result['avg_load_time_ms']:.1f}ms")
        else:
            result = {"avg_load_time_ms": 0, "max_load_time_ms": 0, "success_rate": 0}
            print("  ✗ Config loading failed")

        return result

    def test_stability(self):
        """快速稳定性测试"""
        print(f"🔄 Testing Stability ({self.config['stability_seconds']}s)...")

        hook_path = self.hook_dir / "error_handler.sh"
        if not hook_path.exists():
            print("  ⚠️  error_handler.sh not found")
            return {}

        start_time = time.time()
        end_time = start_time + self.config["stability_seconds"]

        operations = 0
        successes = 0

        while time.time() < end_time:
            result = self.run_command(f"bash {hook_path}", timeout=2)
            operations += 1
            if result["success"]:
                successes += 1

            time.sleep(0.5)  # 避免过度压力

        success_rate = successes / operations * 100 if operations > 0 else 0

        result = {
            "operations": operations,
            "success_rate": success_rate,
            "duration_s": self.config["stability_seconds"],
        }

        print(f"  ✓ {operations} operations, {success_rate:.0f}% success rate")

        return result

    def analyze_results(self, results):
        """分析测试结果"""
        print("\n🔍 Analyzing Results...")

        issues = []
        warnings = []

        # 分析Hook性能
        if "hooks" in results:
            for hook, data in results["hooks"].items():
                if data["success_rate"] < 90:
                    issues.append(
                        f"Hook {hook}: Low success rate ({data['success_rate']:.0f}%)"
                    )
                elif data["avg_ms"] > 100:
                    warnings.append(
                        f"Hook {hook}: High latency ({data['avg_ms']:.0f}ms)"
                    )

        # 分析并发性能
        if "concurrency" in results:
            for test, data in results["concurrency"].items():
                if data["success_rate"] < 90:
                    issues.append(
                        f"{test}: Low success rate ({data['success_rate']:.0f}%)"
                    )
                elif data["throughput_rps"] < 5:
                    warnings.append(
                        f"{test}: Low throughput ({data['throughput_rps']:.1f} RPS)"
                    )

        # 分析内存使用
        if "memory" in results:
            if not results["memory"]["cleanup_effective"]:
                warnings.append(
                    f"Memory cleanup ineffective (+{results['memory']['memory_delta_mb']:.1f}MB)"
                )

        # 分析配置加载
        if "config" in results:
            if results["config"]["success_rate"] < 90:
                issues.append(
                    f"Config loading: Low success rate ({results['config']['success_rate']:.0f}%)"
                )
            elif results["config"]["avg_load_time_ms"] > 200:
                warnings.append(
                    f"Config loading: High latency ({results['config']['avg_load_time_ms']:.0f}ms)"
                )

        # 分析稳定性
        if "stability" in results:
            if results["stability"]["success_rate"] < 95:
                issues.append(
                    f"Stability: Low success rate ({results['stability']['success_rate']:.0f}%)"
                )

        return issues, warnings

    def generate_summary(self, results, issues, warnings):
        """生成测试摘要"""
        print("\n" + "=" * 50)
        print("📊 QUICK STRESS TEST SUMMARY")
        print("=" * 50)

        # 总体状态
        total_issues = len(issues) + len(warnings)
        if len(issues) > 0:
            status = "❌ CRITICAL ISSUES FOUND"
            status_code = 1
        elif len(warnings) > 0:
            status = "⚠️  WARNINGS DETECTED"
            status_code = 2
        else:
            status = "✅ ALL TESTS PASSED"
            status_code = 0

        print(f"Status: {status}")
        print(f"Test Mode: {'Minimal' if self.minimal else 'Standard'}")
        print(f"Issues: {len(issues)} critical, {len(warnings)} warnings")

        # 关键指标
        print(f"\nKey Metrics:")
        if "hooks" in results:
            hook_avg = statistics.mean(
                [h["avg_ms"] for h in results["hooks"].values() if h["avg_ms"] > 0]
            )
            print(f"  Hook Avg Latency: {hook_avg:.1f}ms")

        if "concurrency" in results:
            max_throughput = max(
                [c["throughput_rps"] for c in results["concurrency"].values()]
            )
            print(f"  Max Throughput: {max_throughput:.1f} RPS")

        if "memory" in results:
            print(f"  Memory Delta: {results['memory']['memory_delta_mb']:.1f}MB")

        # 问题详情
        if issues:
            print(f"\n🔴 Critical Issues:")
            for issue in issues:
                print(f"  • {issue}")

        if warnings:
            print(f"\n🟡 Warnings:")
            for warning in warnings:
                print(f"  • {warning}")

        # 建议
        recommendations = []
        if any("Low success rate" in issue for issue in issues):
            recommendations.append("Improve error handling and retry mechanisms")
        if any("High latency" in warning for warning in warnings):
            recommendations.append("Optimize hook execution performance")
        if any("Low throughput" in warning for warning in warnings):
            recommendations.append("Enhance concurrency handling")
        if any("Memory" in warning for warning in warnings):
            recommendations.append("Implement better memory management")

        if recommendations:
            print(f"\n💡 Recommendations:")
            for rec in recommendations:
                print(f"  • {rec}")

        print("=" * 50)

        return status_code

    def run_all_tests(self):
        """运行所有快速测试"""
        print("🚀 Claude Enhancer Quick Stress Test")
        print(f"Mode: {'Minimal (1min)' if self.minimal else 'Standard (5min)'}")
        print("-" * 40)

        start_time = time.time()

        results = {
            "timestamp": datetime.now().isoformat(),
            "minimal_mode": self.minimal,
            "hooks": self.test_core_hooks(),
            "concurrency": self.test_concurrency(),
            "memory": self.test_memory_usage(),
            "config": self.test_config_loading(),
            "stability": self.test_stability(),
        }

        total_time = time.time() - start_time
        results["total_duration_s"] = total_time

        # 分析结果
        issues, warnings = self.analyze_results(results)

        # 保存结果
        report_file = (
            self.project_root
            / f"quick_stress_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(report_file, "w") as f:
            json.dump(results, f, indent=2)

        print(f"\n📋 Report saved: {report_file}")

        # 生成摘要并返回状态码
        status_code = self.generate_summary(results, issues, warnings)

        return status_code


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Claude Enhancer Quick Stress Test")
    parser.add_argument(
        "--minimal", action="store_true", help="Run minimal test suite (1 minute)"
    )

    args = parser.parse_args()

    try:
        tester = QuickStressTest(minimal=args.minimal)
        exit_code = tester.run_all_tests()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
