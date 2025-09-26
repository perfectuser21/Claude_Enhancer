#!/usr/bin/env python3
"""
性能优化效果验证脚本
"""

import time
import statistics
import sys
from pathlib import Path


def benchmark_lazy_engine():
    """测试LazyWorkflowEngine性能"""
    sys.path.insert(0, str(Path(".claude/core")))

    try:
        from lazy_engine import LazyWorkflowEngine

        times = []
        for _ in range(20):
            start = time.time()
            engine = LazyWorkflowEngine()
            end = time.time()
            times.append(end - start)

        return {
            "component": "LazyWorkflowEngine",
            "avg_time": statistics.mean(times),
            "min_time": min(times),
            "max_time": max(times),
            "target": 0.005,  # 5ms目标
            "passed": statistics.mean(times) < 0.005,
        }
    except Exception as e:
        return {"component": "LazyWorkflowEngine", "error": str(e), "passed": False}


def benchmark_lazy_orchestrator():
    """测试LazyAgentOrchestrator性能"""
    sys.path.insert(0, str(Path(".claude/core")))

    try:
        from lazy_orchestrator import LazyAgentOrchestrator

        times = []
        selection_times = []

        for _ in range(15):
            start = time.time()
            orchestrator = LazyAgentOrchestrator()
            init_time = time.time() - start
            times.append(init_time)

            # 测试Agent选择速度
            start = time.time()
            result = orchestrator.select_agents_fast("implement user authentication")
            selection_time = time.time() - start
            selection_times.append(selection_time * 1000)  # 转换为毫秒

        return {
            "component": "LazyAgentOrchestrator",
            "init_avg_time": statistics.mean(times),
            "selection_avg_time": statistics.mean(selection_times),
            "init_target": 0.001,  # 1ms目标
            "selection_target": 1.0,  # 1ms目标
            "init_passed": statistics.mean(times) < 0.001,
            "selection_passed": statistics.mean(selection_times) < 1.0,
        }
    except Exception as e:
        return {"component": "LazyAgentOrchestrator", "error": str(e), "passed": False}


def main():
    print("🧪 性能优化效果验证")
    print("=" * 50)

    # 测试LazyWorkflowEngine
    engine_result = benchmark_lazy_engine()
    print(f"📊 {engine_result['component']}:")
    if "error" not in engine_result:
        print(f"   平均启动时间: {engine_result['avg_time']:.4f}s")
        print(f"   目标时间: {engine_result['target']}s")
        status = "✅ 通过" if engine_result["passed"] else "❌ 未达标"
        print(f"   状态: {status}")
    else:
        print(f"   ❌ 错误: {engine_result['error']}")
    print()

    # 测试LazyAgentOrchestrator
    orchestrator_result = benchmark_lazy_orchestrator()
    print(f"📊 {orchestrator_result['component']}:")
    if "error" not in orchestrator_result:
        print(f"   平均初始化时间: {orchestrator_result['init_avg_time']:.4f}s")
        print(f"   平均选择时间: {orchestrator_result['selection_avg_time']:.2f}ms")
        init_status = "✅ 通过" if orchestrator_result["init_passed"] else "❌ 未达标"
        selection_status = (
            "✅ 通过" if orchestrator_result["selection_passed"] else "❌ 未达标"
        )
        print(f"   初始化状态: {init_status}")
        print(f"   选择速度状态: {selection_status}")
    else:
        print(f"   ❌ 错误: {orchestrator_result['error']}")
    print()

    # 总体评估
    all_passed = (
        engine_result.get("passed", False)
        and orchestrator_result.get("init_passed", False)
        and orchestrator_result.get("selection_passed", False)
    )

    if all_passed:
        print("🎉 所有性能测试通过！优化成功！")
    else:
        print("⚠️  部分性能测试未达标，需要进一步优化")

    return all_passed


if __name__ == "__main__":
    main()
