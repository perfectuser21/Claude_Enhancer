#!/usr/bin/env python3
"""
Claude Enhancer 并发压力测试
"""

import subprocess
import concurrent.futures
import time
import threading
import statistics
from pathlib import Path
import json
import random


class ConcurrentStressTest:
    def __init__(self):
        self.project_root = Path("/home/xx/dev/Perfect21")
        self.claude_dir = self.project_root / ".claude"
        self.hooks_dir = self.claude_dir / "hooks"
        self.lock = threading.Lock()
        self.results = {}

    def test_concurrent_hooks(self, workers=10, iterations=50):
        """测试Hook并发执行"""
        print(f"🔀 测试并发Hook执行: {workers} workers, {iterations} iterations")

        hooks = [
            f
            for f in self.hooks_dir.glob("*.sh")
            if f.is_file() and not f.name.startswith(".")
        ][:5]

        results = {"total": 0, "success": 0, "failed": 0, "times": []}

        def run_hook(hook):
            start = time.time()
            try:
                subprocess.run(
                    ["bash", str(hook)],
                    capture_output=True,
                    timeout=1,
                    cwd=str(self.project_root),
                )
                elapsed = time.time() - start
                with self.lock:
                    results["total"] += 1
                    results["success"] += 1
                    results["times"].append(elapsed)
                return True
            except:
                with self.lock:
                    results["total"] += 1
                    results["failed"] += 1
                return False

        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = []
            for _ in range(iterations):
                hook = random.choice(hooks)
                futures.append(executor.submit(run_hook, hook))

            concurrent.futures.wait(futures, timeout=30)

        total_time = time.time() - start_time

        if results["times"]:
            results["avg_time"] = statistics.mean(results["times"])
            results["p95_time"] = (
                statistics.quantiles(results["times"], n=20)[18]
                if len(results["times"]) > 20
                else max(results["times"])
            )

        results["success_rate"] = (
            results["success"] / results["total"] * 100 if results["total"] > 0 else 0
        )
        results["throughput"] = results["total"] / total_time

        print(
            f"  ✅ 成功率: {results['success_rate']:.1f}%, 吞吐量: {results['throughput']:.1f} ops/sec"
        )

        return results

    def run_test(self):
        print("=" * 60)
        print("🚀 Claude Enhancer 并发压力测试")
        print("=" * 60)

        # 测试不同并发级别
        for workers in [5, 10, 20]:
            self.results[f"{workers}_workers"] = self.test_concurrent_hooks(
                workers=workers, iterations=30
            )

        # 保存结果
        with open(self.project_root / "concurrent_test_report.json", "w") as f:
            json.dump(self.results, f, indent=2)

        print("\n📊 测试完成，结果已保存")

        # 分析结果
        print("\n💡 性能分析:")
        for config, data in self.results.items():
            if data.get("success_rate", 0) < 90:
                print(f"  ⚠️ {config}: 成功率低 ({data['success_rate']:.1f}%)")
            if data.get("p95_time", 0) > 0.5:
                print(f"  ⚠️ {config}: P95延迟高 ({data['p95_time']:.3f}s)")


if __name__ == "__main__":
    tester = ConcurrentStressTest()
    tester.run_test()
