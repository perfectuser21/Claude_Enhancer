#!/usr/bin/env python3
"""
Claude Enhancer Agent并行调用压力测试
模拟真实的Agent调用场景，测试系统在不同负载下的表现
"""

import os
import sys
import time
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
import random
from datetime import datetime


class AgentStressTest:
    def __init__(self):
        self.agents = [
            "backend-architect",
            "frontend-specialist",
            "database-specialist",
            "security-auditor",
            "test-engineer",
            "api-designer",
            "devops-engineer",
            "performance-engineer",
            "technical-writer",
            "code-reviewer",
            "ux-designer",
            "fullstack-engineer",
        ]
        self.task_scenarios = {
            "simple": {"agents": 4, "description": "简单任务 - 4个Agent", "timeout": 600},
            "standard": {"agents": 6, "description": "标准任务 - 6个Agent", "timeout": 1200},
            "complex": {"agents": 8, "description": "复杂任务 - 8个Agent", "timeout": 1800},
        }
        self.results = {}

    def simulate_agent_call(self, agent_name, task_complexity):
        """模拟Agent调用"""
        start_time = time.time()

        # 模拟不同复杂度的任务执行时间
        base_time = {"simple": 0.5, "standard": 1.0, "complex": 2.0}[task_complexity]
        execution_time = base_time + random.uniform(-0.2, 0.5)

        time.sleep(execution_time)

        return {
            "agent": agent_name,
            "complexity": task_complexity,
            "start_time": start_time,
            "execution_time": time.time() - start_time,
            "success": random.random() > 0.05,  # 95%成功率
        }

    def test_parallel_agents(self, complexity="standard", iterations=5):
        """测试Agent并行执行"""
        scenario = self.task_scenarios[complexity]
        print(f"\n🤖 测试场景: {scenario['description']}")
        print(f"   迭代次数: {iterations}")

        all_results = []

        for i in range(iterations):
            print(f"   迭代 {i+1}/{iterations}...", end="")

            # 随机选择agents
            selected_agents = random.sample(self.agents, scenario["agents"])

            # 并行执行
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=scenario["agents"]) as executor:
                futures = [
                    executor.submit(self.simulate_agent_call, agent, complexity)
                    for agent in selected_agents
                ]

                results = [f.result() for f in futures]

            total_time = time.time() - start_time
            success_count = sum(1 for r in results if r["success"])

            iteration_result = {
                "iteration": i + 1,
                "agents_used": selected_agents,
                "total_time": total_time,
                "success_rate": success_count / len(results),
                "avg_agent_time": sum(r["execution_time"] for r in results)
                / len(results),
            }

            all_results.append(iteration_result)
            print(
                f" 完成 (耗时: {total_time:.2f}s, 成功率: {iteration_result['success_rate']*100:.1f}%)"
            )

        # 统计分析
        avg_time = sum(r["total_time"] for r in all_results) / len(all_results)
        avg_success = sum(r["success_rate"] for r in all_results) / len(all_results)
        max_time = max(r["total_time"] for r in all_results)
        min_time = min(r["total_time"] for r in all_results)

        summary = {
            "scenario": scenario["description"],
            "iterations": iterations,
            "avg_execution_time": avg_time,
            "max_execution_time": max_time,
            "min_execution_time": min_time,
            "avg_success_rate": avg_success,
            "details": all_results,
        }

        print(f"\n   📊 统计:")
        print(f"      平均执行时间: {avg_time:.2f}s")
        print(f"      最快/最慢: {min_time:.2f}s / {max_time:.2f}s")
        print(f"      平均成功率: {avg_success*100:.1f}%")

        return summary

    def test_agent_combinations(self):
        """测试不同Agent组合的性能"""
        print("\n🔄 测试Agent组合性能...")

        # 定义常见的Agent组合
        combinations = {
            "认证系统": [
                "backend-architect",
                "security-auditor",
                "database-specialist",
                "api-designer",
                "test-engineer",
            ],
            "API开发": [
                "api-designer",
                "backend-architect",
                "test-engineer",
                "technical-writer",
            ],
            "前端开发": [
                "frontend-specialist",
                "ux-designer",
                "test-engineer",
                "accessibility-auditor",
            ],
            "全栈应用": [
                "fullstack-engineer",
                "backend-architect",
                "frontend-specialist",
                "database-specialist",
                "devops-engineer",
                "test-engineer",
            ],
        }

        results = {}
        for name, agents in combinations.items():
            print(f"\n   测试组合: {name} ({len(agents)} agents)")

            start_time = time.time()
            with ThreadPoolExecutor(max_workers=len(agents)) as executor:
                futures = [
                    executor.submit(self.simulate_agent_call, agent, "standard")
                    for agent in agents
                ]

                agent_results = [f.result() for f in futures]

            total_time = time.time() - start_time

            results[name] = {
                "agents": agents,
                "agent_count": len(agents),
                "total_time": total_time,
                "avg_time_per_agent": total_time / len(agents),
                "success_rate": sum(1 for r in agent_results if r["success"])
                / len(agent_results),
            }

            print(f"      总时间: {total_time:.2f}s")
            print(f"      每Agent平均: {results[name]['avg_time_per_agent']:.2f}s")
            print(f"      成功率: {results[name]['success_rate']*100:.1f}%")

        return results

    def test_error_recovery(self):
        """测试错误恢复能力"""
        print("\n⚠️ 测试错误恢复能力...")

        def agent_with_errors(agent_name, error_rate=0.3):
            """模拟可能出错的Agent"""
            if random.random() < error_rate:
                time.sleep(0.1)
                raise Exception(f"Agent {agent_name} failed")

            time.sleep(random.uniform(0.5, 1.5))
            return {"agent": agent_name, "success": True}

        selected_agents = random.sample(self.agents, 6)
        retry_count = {}
        max_retries = 3

        results = []
        for agent in selected_agents:
            retries = 0
            while retries < max_retries:
                try:
                    result = agent_with_errors(agent, error_rate=0.3)
                    results.append(result)
                    retry_count[agent] = retries
                    print(f"   ✓ {agent}: 成功 (重试 {retries} 次)")
                    break
                except Exception as e:
                    retries += 1
                    if retries >= max_retries:
                        print(f"   ✗ {agent}: 失败 (达到最大重试次数)")
                        retry_count[agent] = retries

        success_rate = len(results) / len(selected_agents)
        avg_retries = sum(retry_count.values()) / len(retry_count)

        return {
            "total_agents": len(selected_agents),
            "successful_agents": len(results),
            "success_rate": success_rate,
            "avg_retries": avg_retries,
            "retry_details": retry_count,
        }

    def test_load_patterns(self):
        """测试不同负载模式"""
        print("\n📈 测试负载模式...")

        patterns = {
            "steady": [6, 6, 6, 6, 6],  # 稳定负载
            "spike": [4, 4, 10, 4, 4],  # 峰值负载
            "gradual": [2, 4, 6, 8, 10],  # 渐进负载
            "random": [random.randint(2, 10) for _ in range(5)],  # 随机负载
        }

        results = {}
        for pattern_name, loads in patterns.items():
            print(f"\n   模式: {pattern_name}")
            print(f"   负载序列: {loads}")

            pattern_results = []
            for i, load in enumerate(loads):
                start = time.time()

                # 并行执行指定数量的agents
                selected = random.sample(self.agents, min(load, len(self.agents)))
                with ThreadPoolExecutor(max_workers=load) as executor:
                    futures = [
                        executor.submit(self.simulate_agent_call, agent, "simple")
                        for agent in selected
                    ]
                    [f.result() for f in futures]

                elapsed = time.time() - start
                pattern_results.append(
                    {
                        "step": i + 1,
                        "load": load,
                        "time": elapsed,
                        "throughput": load / elapsed,
                    }
                )

                print(
                    f"      步骤{i+1}: {load} agents, {elapsed:.2f}s, 吞吐量: {load/elapsed:.1f} req/s"
                )

            avg_time = sum(r["time"] for r in pattern_results) / len(pattern_results)
            avg_throughput = sum(r["throughput"] for r in pattern_results) / len(
                pattern_results
            )

            results[pattern_name] = {
                "pattern": loads,
                "avg_time": avg_time,
                "avg_throughput": avg_throughput,
                "details": pattern_results,
            }

        return results

    def generate_report(self):
        """生成测试报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "test_results": self.results,
            "recommendations": [],
        }

        # 生成建议
        if "parallel_simple" in self.results:
            if self.results["parallel_simple"]["avg_execution_time"] > 1.0:
                report["recommendations"].append("优化简单任务的Agent执行时间")

        if "combinations" in self.results:
            slow_combos = [
                k
                for k, v in self.results["combinations"].items()
                if v["total_time"] > 3.0
            ]
            if slow_combos:
                report["recommendations"].append(f"优化以下组合的性能: {', '.join(slow_combos)}")

        if "error_recovery" in self.results:
            if self.results["error_recovery"]["avg_retries"] > 1.0:
                report["recommendations"].append("改进错误处理机制，减少重试次数")

        # 保存报告
        with open(
            "/home/xx/dev/Claude_Enhancer/agent_stress_test_report.json", "w"
        ) as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return report

    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("🚀 Claude Enhancer Agent并行调用压力测试")
        print("=" * 60)

        # 测试不同复杂度的并行执行
        self.results["parallel_simple"] = self.test_parallel_agents("simple", 3)
        self.results["parallel_standard"] = self.test_parallel_agents("standard", 3)
        self.results["parallel_complex"] = self.test_parallel_agents("complex", 2)

        # 测试Agent组合
        self.results["combinations"] = self.test_agent_combinations()

        # 测试错误恢复
        self.results["error_recovery"] = self.test_error_recovery()

        # 测试负载模式
        self.results["load_patterns"] = self.test_load_patterns()

        # 生成报告
        report = self.generate_report()

        print("\n" + "=" * 60)
        print("✅ Agent压力测试完成!")
        print(f"📊 报告已保存到: agent_stress_test_report.json")

        if report["recommendations"]:
            print("\n💡 优化建议:")
            for rec in report["recommendations"]:
                print(f"   - {rec}")

        print("=" * 60)

        return report


if __name__ == "__main__":
    tester = AgentStressTest()
    tester.run_all_tests()
