#!/usr/bin/env python3
"""
Claude Enhancer 性能基准测试套件
测试系统的性能指标和基准
"""

import pytest
import json
import tempfile
import os
import sys
import time
import threading
import psutil
import memory_profiler
from unittest.mock import patch
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / ".claude/hooks"))

try:
    from phase_manager import PhaseManager, ExecutionPhase, get_phase_manager
except ImportError as e:
    pytest.skip(f"Cannot import phase_manager: {e}", allow_module_level=True)


class PerformanceMetrics:
    """性能指标收集器"""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.memory_start = None
        self.memory_peak = None
        self.cpu_usage = []

    def start_monitoring(self):
        """开始性能监控"""
        self.start_time = time.time()
        self.memory_start = psutil.virtual_memory().used / 1024 / 1024  # MB

    def end_monitoring(self):
        """结束性能监控"""
        self.end_time = time.time()
        self.memory_peak = psutil.virtual_memory().used / 1024 / 1024  # MB

    @property
    def execution_time(self):
        """获取执行时间"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

    @property
    def memory_usage(self):
        """获取内存使用量"""
        if self.memory_start and self.memory_peak:
            return self.memory_peak - self.memory_start
        return None


class TestHookPerformance:
    """Hook性能测试"""

    def setup_method(self):
        """测试设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.metrics = PerformanceMetrics()

    def teardown_method(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_agent_validator_performance(self):
        """测试Agent验证器性能"""
        import subprocess

        validator_script = project_root / ".claude/hooks/agent_validator.sh"
        if not validator_script.exists():
            pytest.skip("Agent validator script not found")

        # 准备测试输入
        test_inputs = [
            self._create_small_task_input(),
            self._create_medium_task_input(),
            self._create_large_task_input()
        ]

        performance_results = []

        for i, test_input in enumerate(test_inputs):
            self.metrics.start_monitoring()

            # 运行验证器
            result = subprocess.run(
                [str(validator_script)],
                input=test_input,
                text=True,
                capture_output=True,
                timeout=10
            )

            self.metrics.end_monitoring()

            performance_results.append({
                "input_size": len(test_input),
                "execution_time": self.metrics.execution_time,
                "memory_usage": self.metrics.memory_usage,
                "success": result.returncode == 0
            })

            # 性能断言
            assert self.metrics.execution_time < 0.5, f"Validator too slow for input {i}: {self.metrics.execution_time}s"
            assert result.returncode == 0, f"Validator failed for input {i}"

        # 验证性能随输入大小的缩放
        small_time = performance_results[0]["execution_time"]
        large_time = performance_results[2]["execution_time"]

        # 大输入的执行时间不应该超过小输入的10倍
        assert large_time < small_time * 10, f"Performance doesn't scale well: {small_time}s -> {large_time}s"

    def test_agent_validator_concurrent_performance(self):
        """测试Agent验证器并发性能"""
        import subprocess
        import concurrent.futures

        validator_script = project_root / ".claude/hooks/agent_validator.sh"
        if not validator_script.exists():
            pytest.skip("Agent validator script not found")

        test_input = self._create_medium_task_input()

        def run_validation():
            start_time = time.time()
            result = subprocess.run(
                [str(validator_script)],
                input=test_input,
                text=True,
                capture_output=True,
                timeout=10
            )
            end_time = time.time()
            return {
                "success": result.returncode == 0,
                "time": end_time - start_time
            }

        # 并发执行验证
        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(run_validation) for _ in range(20)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        end_time = time.time()
        total_time = end_time - start_time

        # 验证结果
        successful_runs = sum(1 for r in results if r["success"])
        assert successful_runs == 20, f"Expected 20 successful runs, got {successful_runs}"

        # 平均执行时间
        avg_time = sum(r["time"] for r in results) / len(results)
        assert avg_time < 1.0, f"Average validation time too slow: {avg_time}s"

        # 总时间应该远小于顺序执行时间
        sequential_time_estimate = avg_time * 20
        assert total_time < sequential_time_estimate * 0.7, "Concurrent execution not efficient enough"

    def test_phase_manager_memory_usage(self):
        """测试阶段管理器内存使用"""
        state_file = os.path.join(self.temp_dir, "memory_test.json")

        with patch.object(PhaseManager, 'state_file', state_file):
            # 监控内存使用
            initial_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB

            manager = get_phase_manager()
            manager.reset_phases()

            # 执行大量操作
            for cycle in range(100):
                for phase in ExecutionPhase:
                    manager.advance_to_next_phase()

                    # 创建大量上下文数据
                    large_result = {
                        "cycle": cycle,
                        "phase": phase.value,
                        "data": [f"item_{i}" for i in range(1000)],
                        "metadata": {f"key_{i}": f"value_{i}" for i in range(500)}
                    }
                    manager.save_phase_results(phase, large_result)

                # 重置以避免无限增长
                if cycle % 20 == 19:
                    manager.reset_phases()

            final_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            # 内存增长应该在合理范围内
            assert memory_increase < 100, f"Memory usage increased too much: {memory_increase}MB"

    def _create_small_task_input(self):
        """创建小型任务输入"""
        return json.dumps({
            "function_calls": [
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "backend-architect",
                        "prompt": "简单任务"
                    }
                },
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "test-engineer",
                        "prompt": "测试"
                    }
                },
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": "technical-writer",
                        "prompt": "文档"
                    }
                }
            ]
        })

    def _create_medium_task_input(self):
        """创建中型任务输入"""
        return json.dumps({
            "function_calls": [
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": f"agent-{i}",
                        "prompt": f"Task {i} with medium complexity description that includes multiple requirements and specifications"
                    }
                } for i in range(10)
            ]
        })

    def _create_large_task_input(self):
        """创建大型任务输入"""
        return json.dumps({
            "function_calls": [
                {
                    "invoke": "Task",
                    "parameters": {
                        "subagent_type": f"agent-{i}",
                        "prompt": f"Task {i} with very detailed and complex description " * 10
                    }
                } for i in range(50)
            ]
        })


class TestWorkflowPerformance:
    """工作流性能测试"""

    def setup_method(self):
        """测试设置"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_five_phase_execution_performance(self):
        """测试5阶段执行性能"""
        state_file = os.path.join(self.temp_dir, "workflow_perf.json")

        with patch.object(PhaseManager, 'state_file', state_file):
            manager = get_phase_manager()

            # 测试单个工作流性能
            start_time = time.time()

            manager.reset_phases()
            for phase in ExecutionPhase:
                phase_start = time.time()

                current_phase = manager.advance_to_next_phase()
                assert current_phase == phase

                # 模拟阶段工作
                result = {
                    "phase": phase.value,
                    "timestamp": time.time(),
                    "data": [f"result_{i}" for i in range(100)]
                }
                manager.save_phase_results(phase, result)

                phase_end = time.time()
                phase_time = phase_end - phase_start

                # 每个阶段应该在合理时间内完成
                assert phase_time < 0.1, f"Phase {phase.value} too slow: {phase_time}s"

            end_time = time.time()
            total_time = end_time - start_time

            # 完整工作流应该快速完成
            assert total_time < 0.5, f"Workflow too slow: {total_time}s"

    def test_concurrent_workflow_performance(self):
        """测试并发工作流性能"""
        import concurrent.futures

        def run_workflow(workflow_id):
            state_file = os.path.join(self.temp_dir, f"concurrent_{workflow_id}.json")

            with patch.object(PhaseManager, 'state_file', state_file):
                manager = get_phase_manager()
                manager.reset_phases()

                start_time = time.time()

                for phase in ExecutionPhase:
                    manager.advance_to_next_phase()
                    result = {
                        "workflow_id": workflow_id,
                        "phase": phase.value,
                        "timestamp": time.time()
                    }
                    manager.save_phase_results(phase, result)

                end_time = time.time()
                return end_time - start_time

        # 并发执行多个工作流
        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(run_workflow, i) for i in range(20)]
            execution_times = [future.result() for future in concurrent.futures.as_completed(futures)]

        end_time = time.time()
        total_concurrent_time = end_time - start_time

        # 验证性能
        avg_workflow_time = sum(execution_times) / len(execution_times)
        assert avg_workflow_time < 1.0, f"Average workflow time too slow: {avg_workflow_time}s"

        # 并发执行应该比顺序执行快
        estimated_sequential_time = avg_workflow_time * 20
        assert total_concurrent_time < estimated_sequential_time * 0.6, "Concurrent execution not efficient"

    def test_state_persistence_performance(self):
        """测试状态持久化性能"""
        state_file = os.path.join(self.temp_dir, "persistence_perf.json")

        with patch.object(PhaseManager, 'state_file', state_file):
            manager = get_phase_manager()

            # 测试大量状态保存和加载
            save_times = []
            load_times = []

            for i in range(100):
                # 创建复杂状态
                manager.reset_phases()
                for phase in ExecutionPhase:
                    manager.advance_to_next_phase()
                    large_result = {
                        "iteration": i,
                        "phase": phase.value,
                        "large_data": [f"data_{j}" for j in range(1000)]
                    }
                    manager.save_phase_results(phase, large_result)

                # 测试保存性能
                save_start = time.time()
                manager.save_state()
                save_end = time.time()
                save_times.append(save_end - save_start)

                # 测试加载性能
                load_start = time.time()
                manager.load_state()
                load_end = time.time()
                load_times.append(load_end - load_start)

            # 验证性能
            avg_save_time = sum(save_times) / len(save_times)
            avg_load_time = sum(load_times) / len(load_times)

            assert avg_save_time < 0.05, f"State save too slow: {avg_save_time}s"
            assert avg_load_time < 0.05, f"State load too slow: {avg_load_time}s"

    def test_context_retrieval_performance(self):
        """测试上下文检索性能"""
        state_file = os.path.join(self.temp_dir, "context_perf.json")

        with patch.object(PhaseManager, 'state_file', state_file):
            manager = get_phase_manager()
            manager.reset_phases()

            # 创建大量上下文数据
            for phase in ExecutionPhase:
                manager.advance_to_next_phase()
                large_context = {
                    "phase": phase.value,
                    "large_dataset": {f"key_{i}": f"value_{i}" * 100 for i in range(10000)}
                }
                manager.save_phase_results(phase, large_context)

            # 测试上下文检索性能
            retrieval_times = []

            for _ in range(100):
                start_time = time.time()
                context = manager.get_context_for_phase(ExecutionPhase.DEPLOYMENT)
                end_time = time.time()

                retrieval_times.append(end_time - start_time)

                # 验证上下文完整性
                assert len(context) == 4  # 前4个阶段的上下文

            avg_retrieval_time = sum(retrieval_times) / len(retrieval_times)
            assert avg_retrieval_time < 0.01, f"Context retrieval too slow: {avg_retrieval_time}s"


class TestMemoryPerformance:
    """内存性能测试"""

    def setup_method(self):
        """测试设置"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @memory_profiler.profile
    def test_memory_efficiency(self):
        """测试内存效率"""
        state_file = os.path.join(self.temp_dir, "memory_efficiency.json")

        with patch.object(PhaseManager, 'state_file', state_file):
            manager = get_phase_manager()

            # 执行大量操作并监控内存
            for cycle in range(50):
                manager.reset_phases()

                for phase in ExecutionPhase:
                    manager.advance_to_next_phase()

                    # 创建大型结果对象
                    result = {
                        "cycle": cycle,
                        "phase": phase.value,
                        "large_data": [i for i in range(10000)],
                        "metadata": {f"key_{i}": f"value_{i}" for i in range(1000)}
                    }
                    manager.save_phase_results(phase, result)

                # 定期清理以测试内存释放
                if cycle % 10 == 9:
                    manager.reset_phases()

    def test_memory_leak_detection(self):
        """测试内存泄漏检测"""
        import gc

        state_file = os.path.join(self.temp_dir, "leak_test.json")

        with patch.object(PhaseManager, 'state_file', state_file):
            # 记录初始内存
            gc.collect()
            initial_memory = psutil.Process().memory_info().rss / 1024 / 1024

            # 执行大量操作
            for i in range(100):
                manager = get_phase_manager()
                manager.reset_phases()

                for phase in ExecutionPhase:
                    manager.advance_to_next_phase()
                    result = {"iteration": i, "phase": phase.value}
                    manager.save_phase_results(phase, result)

                # 强制垃圾回收
                del manager
                gc.collect()

            # 检查最终内存
            final_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_increase = final_memory - initial_memory

            # 内存增长应该在合理范围内（考虑到Python的内存管理）
            assert memory_increase < 50, f"Potential memory leak detected: {memory_increase}MB increase"


class TestScalabilityPerformance:
    """可扩展性性能测试"""

    def setup_method(self):
        """测试设置"""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """清理测试环境"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_agent_count_scalability(self):
        """测试Agent数量可扩展性"""
        import subprocess

        validator_script = project_root / ".claude/hooks/agent_validator.sh"
        if not validator_script.exists():
            pytest.skip("Agent validator script not found")

        agent_counts = [5, 10, 20, 50, 100]
        execution_times = []

        for count in agent_counts:
            # 创建包含指定数量agents的输入
            task_input = json.dumps({
                "function_calls": [
                    {
                        "invoke": "Task",
                        "parameters": {
                            "subagent_type": f"agent-{i}",
                            "prompt": f"Task {i}"
                        }
                    } for i in range(count)
                ]
            })

            start_time = time.time()

            result = subprocess.run(
                [str(validator_script)],
                input=task_input,
                text=True,
                capture_output=True,
                timeout=30
            )

            end_time = time.time()
            execution_time = end_time - start_time

            execution_times.append(execution_time)

            # 验证结果
            assert result.returncode == 0, f"Validation failed for {count} agents"
            assert execution_time < 5.0, f"Validation too slow for {count} agents: {execution_time}s"

        # 验证可扩展性（执行时间不应该指数增长）
        time_ratio = execution_times[-1] / execution_times[0]  # 100 agents vs 5 agents
        count_ratio = agent_counts[-1] / agent_counts[0]  # 20x increase

        # 时间增长应该小于数量增长的平方
        assert time_ratio < count_ratio ** 2, f"Poor scalability: {time_ratio}x time for {count_ratio}x agents"

    def test_concurrent_users_scalability(self):
        """测试并发用户可扩展性"""
        import concurrent.futures

        user_counts = [1, 5, 10, 20]
        results = {}

        for user_count in user_counts:
            def simulate_user(user_id):
                state_file = os.path.join(self.temp_dir, f"user_{user_id}_scalability.json")

                with patch.object(PhaseManager, 'state_file', state_file):
                    manager = get_phase_manager()
                    manager.reset_phases()

                    start_time = time.time()

                    for phase in ExecutionPhase:
                        manager.advance_to_next_phase()
                        result = {"user_id": user_id, "phase": phase.value}
                        manager.save_phase_results(phase, result)

                    end_time = time.time()
                    return end_time - start_time

            # 并发执行用户模拟
            start_time = time.time()

            with concurrent.futures.ThreadPoolExecutor(max_workers=user_count) as executor:
                futures = [executor.submit(simulate_user, i) for i in range(user_count)]
                user_times = [future.result() for future in concurrent.futures.as_completed(futures)]

            end_time = time.time()
            total_time = end_time - start_time

            results[user_count] = {
                "total_time": total_time,
                "avg_user_time": sum(user_times) / len(user_times),
                "max_user_time": max(user_times)
            }

            # 验证性能
            assert results[user_count]["max_user_time"] < 2.0, f"User response too slow with {user_count} users"

        # 验证可扩展性
        single_user_time = results[1]["total_time"]
        multi_user_time = results[20]["total_time"]

        # 20个用户的总时间不应该超过单用户的10倍
        assert multi_user_time < single_user_time * 10, "Poor concurrent user scalability"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])