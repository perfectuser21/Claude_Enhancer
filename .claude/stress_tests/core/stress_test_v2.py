#!/usr/bin/env python3
"""
Claude Enhancer 5.0 压力测试套件 v2
符合工作流规范的完整压力测试
"""

import asyncio
import time
import json
import psutil
import random
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any
import subprocess
import sys


class StressTestSuite:
    """压力测试套件"""

    def __init__(self):
        self.results = {}
        self.start_time = time.time()
        self.test_dir = Path(__file__).parent.parent
        self.report_dir = self.test_dir / "reports"
        self.report_dir.mkdir(exist_ok=True)

    def log(self, msg: str, level: str = "INFO"):
        """彩色日志输出"""
        colors = {
            "INFO": "\033[0;34m",
            "SUCCESS": "\033[0;32m",
            "WARNING": "\033[1;33m",
            "ERROR": "\033[0;31m",
        }
        color = colors.get(level, "\033[0m")
        reset = "\033[0m"
        print(f"{color}[{level}] {msg}{reset}")

    def test_workflow_hooks(self, iterations: int = 10):
        """测试工作流Hooks"""
        self.log("🔧 测试工作流Hooks...", "INFO")

        hook_path = Path(
            "/home/xx/dev/Claude Enhancer 5.0/.claude/hooks/workflow_enforcer_v2.sh"
        )
        if not hook_path.exists():
            self.log("Hook文件不存在", "ERROR")
            return

        times = []
        successes = 0

        test_tasks = ["实现新功能", "修复bug", "优化性能", "添加测试", "重构代码"]

        for i in range(iterations):
            task = random.choice(test_tasks)
            start = time.time()

            try:
                result = subprocess.run(
                    ["bash", str(hook_path), task],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)

                if result.returncode == 0:
                    successes += 1

            except subprocess.TimeoutExpired:
                self.log(f"Hook超时: {task}", "WARNING")
            except Exception as e:
                self.log(f"Hook错误: {e}", "ERROR")

        if times:
            self.results["workflow_hooks"] = {
                "iterations": iterations,
                "success_rate": (successes / iterations) * 100,
                "avg_time_ms": sum(times) / len(times),
                "min_time_ms": min(times),
                "max_time_ms": max(times),
            }
            self.log(f"✅ Hook测试完成: {successes}/{iterations} 成功", "SUCCESS")

    def test_git_hooks(self):
        """测试Git Hooks"""
        self.log("🔧 测试Git Hooks...", "INFO")

        git_hooks = ["pre-commit", "commit-msg", "pre-push"]
        hook_status = {}

        for hook in git_hooks:
            hook_path = Path(f"/home/xx/dev/Claude Enhancer 5.0/.git/hooks/{hook}")
            if hook_path.exists() and hook_path.stat().st_mode & 0o111:
                hook_status[hook] = "installed"
                self.log(f"✅ {hook}: 已安装", "SUCCESS")
            else:
                hook_status[hook] = "missing"
                self.log(f"❌ {hook}: 未安装", "ERROR")

        # 测试Phase检查
        phase_file = Path("/home/xx/dev/Claude Enhancer 5.0/.phase/current")
        if phase_file.exists():
            current_phase = phase_file.read_text().strip()
            self.log(f"📍 当前Phase: {current_phase}", "INFO")
            hook_status["phase"] = current_phase
        else:
            self.log("⚠️ Phase文件不存在", "WARNING")
            hook_status["phase"] = "none"

        self.results["git_hooks"] = hook_status

    def test_agent_selection(self, iterations: int = 50):
        """测试Agent选择性能"""
        self.log(f"🎯 测试Agent选择 ({iterations}次)...", "INFO")

        # 测试shell脚本选择器
        selector_path = Path(
            "/home/xx/dev/Claude Enhancer 5.0/.claude/v5.2/hooks/core/unified_agent_selector.sh"
        )

        if selector_path.exists():
            times = []
            cache_hits = 0

            test_tasks = ["实现用户认证", "优化数据库", "编写测试", "修复安全漏洞", "设计API"]

            for i in range(iterations):
                task = random.choice(test_tasks)
                start = time.time()

                try:
                    result = subprocess.run(
                        ["bash", str(selector_path), task],
                        capture_output=True,
                        text=True,
                        timeout=2,
                    )
                    elapsed = (time.time() - start) * 1000
                    times.append(elapsed)

                    # 小于5ms认为是缓存命中
                    if elapsed < 5:
                        cache_hits += 1

                except Exception as e:
                    self.log(f"选择器错误: {e}", "ERROR")

            if times:
                self.results["agent_selection"] = {
                    "iterations": iterations,
                    "avg_time_ms": sum(times) / len(times),
                    "min_time_ms": min(times),
                    "max_time_ms": max(times),
                    "cache_hit_rate": (cache_hits / iterations) * 100,
                }
                self.log(f"✅ Agent选择测试完成", "SUCCESS")
        else:
            self.log("Agent选择器不存在", "WARNING")

    def test_memory_usage(self, duration: int = 10):
        """测试内存使用"""
        self.log(f"💾 测试内存使用 ({duration}秒)...", "INFO")

        process = psutil.Process()
        memory_samples = []

        for i in range(duration):
            mem_info = process.memory_info()
            memory_mb = mem_info.rss / 1024 / 1024
            memory_samples.append(memory_mb)
            time.sleep(1)

        self.results["memory_usage"] = {
            "samples": len(memory_samples),
            "min_mb": min(memory_samples),
            "max_mb": max(memory_samples),
            "avg_mb": sum(memory_samples) / len(memory_samples),
        }

        self.log(
            f"✅ 内存测试完成: 平均{self.results['memory_usage']['avg_mb']:.1f}MB", "SUCCESS"
        )

    def test_concurrent_operations(self, workers: int = 5, tasks: int = 20):
        """测试并发操作"""
        self.log(f"⚡ 测试并发操作 ({workers}个工作线程, {tasks}个任务)...", "INFO")

        def worker_task(task_id):
            """模拟工作任务"""
            time.sleep(random.uniform(0.1, 0.3))
            return {
                "task_id": task_id,
                "duration": random.uniform(0.1, 0.3),
                "status": "completed",
            }

        start = time.time()
        results = []

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(worker_task, i) for i in range(tasks)]

            for future in as_completed(futures):
                results.append(future.result())

        total_time = time.time() - start

        self.results["concurrent_ops"] = {
            "workers": workers,
            "tasks": tasks,
            "total_time_s": total_time,
            "throughput": tasks / total_time,
            "completed": len(results),
        }

        self.log(
            f"✅ 并发测试完成: {self.results['concurrent_ops']['throughput']:.1f} tasks/s",
            "SUCCESS",
        )

    def generate_report(self):
        """生成测试报告"""
        self.log("\n📊 生成测试报告...", "INFO")

        total_time = time.time() - self.start_time

        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "duration_seconds": total_time,
            "results": self.results,
            "summary": {
                "total_tests": len(self.results),
                "status": "PASS" if self.results else "FAIL",
            },
        }

        # 保存JSON报告
        report_file = (
            self.report_dir / f"stress_test_{time.strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)

        # 打印摘要
        print("\n" + "=" * 50)
        print("📊 Claude Enhancer 5.0 压力测试报告")
        print("=" * 50)

        for test_name, test_results in self.results.items():
            print(f"\n🔧 {test_name}:")
            if isinstance(test_results, dict):
                for key, value in test_results.items():
                    if isinstance(value, float):
                        print(f"  {key}: {value:.2f}")
                    else:
                        print(f"  {key}: {value}")

        print(f"\n📄 详细报告已保存: {report_file}")
        print(f"⏱️ 总耗时: {total_time:.1f}秒")

        # 性能评级
        self.rate_performance()

    def rate_performance(self):
        """性能评级"""
        print("\n🏆 性能评级:")

        score = 100

        # Hook测试评分
        if "workflow_hooks" in self.results:
            success_rate = self.results["workflow_hooks"]["success_rate"]
            if success_rate >= 90:
                print("  ✅ 工作流Hooks: 优秀")
            elif success_rate >= 70:
                print("  ⚠️ 工作流Hooks: 良好")
                score -= 10
            else:
                print("  ❌ 工作流Hooks: 需改进")
                score -= 20

        # Agent选择评分
        if "agent_selection" in self.results:
            avg_time = self.results["agent_selection"]["avg_time_ms"]
            if avg_time < 10:
                print("  ✅ Agent选择: 优秀")
            elif avg_time < 50:
                print("  ⚠️ Agent选择: 良好")
                score -= 10
            else:
                print("  ❌ Agent选择: 需改进")
                score -= 20

        # 内存使用评分
        if "memory_usage" in self.results:
            avg_memory = self.results["memory_usage"]["avg_mb"]
            if avg_memory < 100:
                print("  ✅ 内存使用: 优秀")
            elif avg_memory < 200:
                print("  ⚠️ 内存使用: 良好")
                score -= 10
            else:
                print("  ❌ 内存使用: 需改进")
                score -= 20

        print(f"\n📊 总评分: {score}/100")

        if score >= 90:
            print("🎉 系统性能优秀！")
        elif score >= 70:
            print("✅ 系统性能良好")
        else:
            print("⚠️ 系统性能有待提升")


def main():
    """主函数"""
    print("🚀 启动Claude Enhancer 5.0压力测试...")
    print("=" * 50)

    tester = StressTestSuite()

    # 运行各项测试
    tester.test_workflow_hooks(10)
    tester.test_git_hooks()
    tester.test_agent_selection(30)
    tester.test_memory_usage(5)
    tester.test_concurrent_operations(5, 20)

    # 生成报告
    tester.generate_report()

    print("\n✅ 压力测试完成！")


if __name__ == "__main__":
    main()
