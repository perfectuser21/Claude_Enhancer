#!/usr/bin/env python3
"""
Perfect21 并行性能测试
测试并行执行器的性能、扩展性和资源利用率
"""

import os
import sys
import pytest
import time
import threading
import concurrent.futures
import psutil
import statistics
from unittest.mock import Mock, patch
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from features.opus41_optimizer import Opus41Optimizer, QualityLevel
from features.parallel_executor import ParallelExecutor
from features.smart_decomposer import TaskAnalysis, AgentTask, TaskComplexity

class TestParallelPerformance:
    """并行性能测试类"""

    @pytest.fixture
    def optimizer(self):
        """性能测试用优化器"""
        return Opus41Optimizer()

    @pytest.fixture
    def executor(self):
        """性能测试用执行器"""
        return ParallelExecutor()

    @pytest.fixture
    def performance_tasks(self):
        """性能测试任务集"""
        return [
            ("开发简单REST API", QualityLevel.FAST, 5),
            ("构建微服务架构", QualityLevel.BALANCED, 10),
            ("开发企业级平台", QualityLevel.PREMIUM, 15),
            ("构建分布式系统", QualityLevel.ULTIMATE, 20)
        ]

    def test_agent_selection_performance(self, optimizer, performance_tasks):
        """测试Agent选择性能"""
        selection_times = []

        for task_desc, quality_level, expected_agents in performance_tasks:
            start_time = time.time()

            agents = optimizer.select_optimal_agents(task_desc, quality_level)

            end_time = time.time()
            selection_time = end_time - start_time
            selection_times.append(selection_time)

            # 验证选择结果
            assert len(agents) >= expected_agents * 0.8  # 允许20%误差
            assert selection_time < 1.0  # 选择应该在1秒内完成

        # 分析性能趋势
        avg_time = statistics.mean(selection_times)
        max_time = max(selection_times)

        print(f"\nAgent选择性能统计:")
        print(f"平均时间: {avg_time:.3f}秒")
        print(f"最大时间: {max_time:.3f}秒")
        print(f"所有选择: {[f'{t:.3f}s' for t in selection_times]}")

        assert avg_time < 0.5  # 平均时间应该在0.5秒内
        assert max_time < 1.0   # 最大时间应该在1秒内

    def test_execution_plan_creation_performance(self, optimizer, performance_tasks):
        """测试执行计划创建性能"""
        planning_times = []

        for task_desc, quality_level, _ in performance_tasks:
            # 选择agents
            agents = optimizer.select_optimal_agents(task_desc, quality_level)

            # 测量计划创建时间
            start_time = time.time()

            execution_plan = optimizer.create_parallel_execution_plan(agents, task_desc)

            end_time = time.time()
            planning_time = end_time - start_time
            planning_times.append(planning_time)

            # 验证计划质量
            assert 'execution_layers' in execution_plan
            assert len(execution_plan['execution_layers']) >= 1
            assert planning_time < 2.0  # 计划创建应该在2秒内完成

        # 性能分析
        avg_time = statistics.mean(planning_times)
        max_time = max(planning_times)

        print(f"\n执行计划创建性能统计:")
        print(f"平均时间: {avg_time:.3f}秒")
        print(f"最大时间: {max_time:.3f}秒")

        assert avg_time < 1.0  # 平均时间应该在1秒内
        assert max_time < 2.0  # 最大时间应该在2秒内

    def test_concurrent_agent_selection(self, optimizer):
        """测试并发Agent选择性能"""
        tasks = [
            f"开发系统模块{i}" for i in range(10)
        ]

        # 并发执行测试
        def select_agents_for_task(task):
            start_time = time.time()
            agents = optimizer.select_optimal_agents(task, QualityLevel.PREMIUM)
            end_time = time.time()
            return {
                'task': task,
                'agents_count': len(agents),
                'execution_time': end_time - start_time
            }

        # 串行执行基准
        start_time = time.time()
        sequential_results = [select_agents_for_task(task) for task in tasks]
        sequential_time = time.time() - start_time

        # 并行执行测试
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            concurrent_results = list(executor.map(select_agents_for_task, tasks))
        concurrent_time = time.time() - start_time

        # 性能比较
        print(f"\n并发性能对比:")
        print(f"串行执行时间: {sequential_time:.3f}秒")
        print(f"并行执行时间: {concurrent_time:.3f}秒")
        print(f"性能提升: {sequential_time/concurrent_time:.2f}x")

        # 验证结果一致性
        assert len(sequential_results) == len(concurrent_results) == len(tasks)

        # 并行执行应该更快（考虑到线程开销，至少有一些提升）
        assert concurrent_time < sequential_time * 1.2  # 允许20%的线程开销

    def test_memory_usage_scaling(self, optimizer):
        """测试内存使用扩展性"""
        import gc

        def measure_memory_usage():
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB

        # 基准内存使用
        gc.collect()
        baseline_memory = measure_memory_usage()

        memory_measurements = []
        agent_counts = []

        # 测试不同规模的Agent选择
        for agent_count in [5, 10, 15, 20]:
            gc.collect()  # 清理垃圾回收

            # 创建大量agents的任务
            task = f"开发包含{agent_count}个组件的大型系统"

            if agent_count <= 5:
                quality_level = QualityLevel.FAST
            elif agent_count <= 10:
                quality_level = QualityLevel.BALANCED
            elif agent_count <= 15:
                quality_level = QualityLevel.PREMIUM
            else:
                quality_level = QualityLevel.ULTIMATE

            agents = optimizer.select_optimal_agents(task, quality_level)
            execution_plan = optimizer.create_parallel_execution_plan(agents, task)

            current_memory = measure_memory_usage()
            memory_increase = current_memory - baseline_memory

            memory_measurements.append(memory_increase)
            agent_counts.append(len(agents))

            print(f"Agents: {len(agents)}, 内存增加: {memory_increase:.2f}MB")

        # 验证内存使用合理
        max_memory_increase = max(memory_measurements)
        assert max_memory_increase < 100  # 不应该超过100MB

        # 验证内存增长是可控的
        if len(memory_measurements) > 1:
            memory_growth_rate = memory_measurements[-1] / memory_measurements[0]
            agent_growth_rate = agent_counts[-1] / agent_counts[0]

            # 内存增长应该小于或接近agent数量增长
            assert memory_growth_rate < agent_growth_rate * 2

    def test_task_processing_throughput(self, executor, optimizer):
        """测试任务处理吞吐量"""
        from features.smart_decomposer import TaskAnalysis, AgentTask, TaskComplexity

        # 创建不同数量的任务进行吞吐量测试
        task_counts = [1, 5, 10, 20]
        throughput_results = []

        for task_count in task_counts:
            tasks_data = []

            # 准备任务数据
            for i in range(task_count):
                task_desc = f"处理任务{i}"
                agents = optimizer.select_optimal_agents(task_desc, QualityLevel.BALANCED)

                agent_tasks = []
                for j, agent in enumerate(agents[:5]):  # 限制每个任务5个agents
                    agent_tasks.append(
                        AgentTask(
                            agent_name=agent,
                            task_description=f"Agent {agent} 处理任务 {i}",
                            detailed_prompt=f"执行任务{i}的具体工作",
                            estimated_time=20,
                            priority=1,
                            dependencies=[]
                        )
                    )

                task_analysis = TaskAnalysis(
                    original_task=task_desc,
                    project_type="batch_processing",
                    complexity=TaskComplexity.MEDIUM,
                    execution_mode="parallel",
                    estimated_total_time=60,
                    agent_tasks=agent_tasks
                )

                tasks_data.append((task_desc, task_analysis))

            # 测量处理时间
            start_time = time.time()

            for task_desc, task_analysis in tasks_data:
                result = executor.execute_parallel_task(task_desc, task_analysis)
                assert result['ready_for_execution'] is True

            end_time = time.time()
            processing_time = end_time - start_time
            throughput = task_count / processing_time

            throughput_results.append({
                'task_count': task_count,
                'processing_time': processing_time,
                'throughput': throughput
            })

            print(f"任务数: {task_count}, 处理时间: {processing_time:.3f}s, 吞吐量: {throughput:.2f} tasks/s")

        # 验证吞吐量合理性
        for result in throughput_results:
            assert result['throughput'] > 1  # 至少每秒处理1个任务

        # 验证扩展性（更多任务时吞吐量不应该显著下降）
        if len(throughput_results) > 1:
            first_throughput = throughput_results[0]['throughput']
            last_throughput = throughput_results[-1]['throughput']

            # 吞吐量下降不应该超过50%
            assert last_throughput > first_throughput * 0.5

    def test_cpu_utilization_efficiency(self, optimizer):
        """测试CPU利用率效率"""
        import multiprocessing

        cpu_count = multiprocessing.cpu_count()
        print(f"\n系统CPU核心数: {cpu_count}")

        def cpu_intensive_task():
            """CPU密集型任务模拟"""
            task = "开发高性能计算系统"
            agents = optimizer.select_optimal_agents(task, QualityLevel.ULTIMATE)
            plan = optimizer.create_parallel_execution_plan(agents, task)
            return len(agents), len(plan['execution_layers'])

        # 单线程基准测试
        start_time = time.time()
        single_result = cpu_intensive_task()
        single_thread_time = time.time() - start_time

        # 多线程测试
        thread_counts = [2, 4, min(8, cpu_count)]
        for thread_count in thread_counts:
            start_time = time.time()

            with concurrent.futures.ThreadPoolExecutor(max_workers=thread_count) as executor:
                futures = [executor.submit(cpu_intensive_task) for _ in range(thread_count)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]

            multi_thread_time = time.time() - start_time

            # 计算效率
            theoretical_improvement = thread_count
            actual_improvement = (single_thread_time * thread_count) / multi_thread_time
            efficiency = actual_improvement / theoretical_improvement

            print(f"线程数: {thread_count}")
            print(f"单线程时间: {single_thread_time:.3f}s")
            print(f"多线程时间: {multi_thread_time:.3f}s")
            print(f"理论提升: {theoretical_improvement:.2f}x")
            print(f"实际提升: {actual_improvement:.2f}x")
            print(f"效率: {efficiency:.2f}")

            # 验证合理的效率（考虑到GIL和其他开销）
            assert efficiency > 0.3  # 至少30%的效率

    def test_load_balancing_performance(self, optimizer):
        """测试负载均衡性能"""
        # 创建不同复杂度的任务
        mixed_tasks = [
            ("简单任务1", QualityLevel.FAST),
            ("复杂任务1", QualityLevel.ULTIMATE),
            ("简单任务2", QualityLevel.FAST),
            ("中等任务1", QualityLevel.BALANCED),
            ("复杂任务2", QualityLevel.ULTIMATE),
            ("中等任务2", QualityLevel.PREMIUM),
        ]

        execution_times = []
        agent_counts = []

        # 测量每个任务的处理时间
        for task_desc, quality_level in mixed_tasks:
            start_time = time.time()

            agents = optimizer.select_optimal_agents(task_desc, quality_level)
            execution_plan = optimizer.create_parallel_execution_plan(agents, task_desc)

            end_time = time.time()
            execution_time = end_time - start_time

            execution_times.append(execution_time)
            agent_counts.append(len(agents))

            print(f"任务: {task_desc[:15]}, 质量: {quality_level.value}, "
                  f"Agents: {len(agents)}, 时间: {execution_time:.3f}s")

        # 分析负载均衡
        time_variance = statistics.variance(execution_times) if len(execution_times) > 1 else 0
        time_std = statistics.stdev(execution_times) if len(execution_times) > 1 else 0

        print(f"\n负载均衡分析:")
        print(f"执行时间方差: {time_variance:.6f}")
        print(f"执行时间标准差: {time_std:.3f}")

        # 验证时间分布合理（标准差不应该太大）
        avg_time = statistics.mean(execution_times)
        assert time_std < avg_time  # 标准差应该小于平均时间

    def test_stress_testing(self, optimizer, executor):
        """压力测试"""
        print("\n开始压力测试...")

        # 大量并发任务
        stress_task_count = 50
        concurrent_workers = 10

        def stress_test_task(task_id):
            try:
                task_desc = f"压力测试任务{task_id}"
                agents = optimizer.select_optimal_agents(task_desc, QualityLevel.BALANCED)

                # 创建简化的任务分析
                from features.smart_decomposer import TaskAnalysis, AgentTask, TaskComplexity

                agent_tasks = [
                    AgentTask(
                        agent_name=agents[0] if agents else "test-agent",
                        task_description=f"压力测试任务{task_id}",
                        detailed_prompt="执行压力测试",
                        estimated_time=10,
                        priority=1,
                        dependencies=[]
                    )
                ]

                task_analysis = TaskAnalysis(
                    original_task=task_desc,
                    project_type="stress_test",
                    complexity=TaskComplexity.SIMPLE,
                    execution_mode="parallel",
                    estimated_total_time=30,
                    agent_tasks=agent_tasks
                )

                result = executor.execute_parallel_task(task_desc, task_analysis)
                return {'task_id': task_id, 'success': result['ready_for_execution']}

            except Exception as e:
                return {'task_id': task_id, 'error': str(e)}

        # 执行压力测试
        start_time = time.time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_workers) as executor_pool:
            futures = [
                executor_pool.submit(stress_test_task, task_id)
                for task_id in range(stress_task_count)
            ]

            results = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result(timeout=30)  # 30秒超时
                    results.append(result)
                except concurrent.futures.TimeoutError:
                    results.append({'error': 'timeout'})
                except Exception as e:
                    results.append({'error': str(e)})

        end_time = time.time()
        total_time = end_time - start_time

        # 分析压力测试结果
        successful_tasks = [r for r in results if r.get('success')]
        failed_tasks = [r for r in results if 'error' in r]

        success_rate = len(successful_tasks) / len(results)
        throughput = len(results) / total_time

        print(f"压力测试结果:")
        print(f"总任务数: {len(results)}")
        print(f"成功任务: {len(successful_tasks)}")
        print(f"失败任务: {len(failed_tasks)}")
        print(f"成功率: {success_rate:.2%}")
        print(f"总时间: {total_time:.2f}秒")
        print(f"吞吐量: {throughput:.2f} tasks/秒")

        # 验证压力测试结果
        assert success_rate > 0.8  # 至少80%成功率
        assert throughput > 1.0    # 至少每秒处理1个任务

    def test_memory_leak_detection(self, optimizer):
        """内存泄漏检测测试"""
        import gc

        def measure_memory():
            gc.collect()
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB

        # 基准内存
        initial_memory = measure_memory()
        print(f"\n初始内存: {initial_memory:.2f}MB")

        memory_readings = [initial_memory]

        # 执行多次操作检测内存泄漏
        for iteration in range(10):
            # 执行一系列操作
            for i in range(10):
                task = f"内存测试任务{iteration}_{i}"
                agents = optimizer.select_optimal_agents(task, QualityLevel.BALANCED)
                plan = optimizer.create_parallel_execution_plan(agents, task)

            # 强制垃圾回收
            gc.collect()
            current_memory = measure_memory()
            memory_readings.append(current_memory)

            print(f"迭代 {iteration}: {current_memory:.2f}MB "
                  f"(增长: {current_memory - initial_memory:.2f}MB)")

        # 分析内存趋势
        final_memory = memory_readings[-1]
        memory_growth = final_memory - initial_memory

        # 计算内存增长趋势
        if len(memory_readings) > 5:
            recent_avg = statistics.mean(memory_readings[-5:])
            early_avg = statistics.mean(memory_readings[:5])
            growth_trend = recent_avg - early_avg

            print(f"内存增长趋势: {growth_trend:.2f}MB")

            # 验证没有严重的内存泄漏
            assert growth_trend < 50  # 增长不应超过50MB
            assert memory_growth < 100  # 总增长不应超过100MB

    @pytest.mark.slow
    def test_long_running_stability(self, optimizer):
        """长时间运行稳定性测试"""
        print("\n开始长时间稳定性测试...")

        start_time = time.time()
        test_duration = 60  # 测试60秒
        iteration_count = 0
        error_count = 0

        while time.time() - start_time < test_duration:
            try:
                task = f"稳定性测试任务{iteration_count}"
                quality_level = [QualityLevel.FAST, QualityLevel.BALANCED, QualityLevel.PREMIUM][iteration_count % 3]

                agents = optimizer.select_optimal_agents(task, quality_level)
                plan = optimizer.create_parallel_execution_plan(agents, task)

                # 验证结果合理性
                assert len(agents) > 0
                assert 'execution_layers' in plan

                iteration_count += 1

                # 每100次迭代报告一次进度
                if iteration_count % 100 == 0:
                    elapsed = time.time() - start_time
                    rate = iteration_count / elapsed
                    print(f"已完成 {iteration_count} 次迭代，速率: {rate:.2f} iter/s")

            except Exception as e:
                error_count += 1
                print(f"错误 {error_count}: {e}")

            # 短暂休息避免过度占用CPU
            time.sleep(0.01)

        total_time = time.time() - start_time
        success_rate = (iteration_count - error_count) / iteration_count if iteration_count > 0 else 0
        average_rate = iteration_count / total_time

        print(f"\n稳定性测试结果:")
        print(f"运行时间: {total_time:.2f}秒")
        print(f"总迭代数: {iteration_count}")
        print(f"错误数: {error_count}")
        print(f"成功率: {success_rate:.2%}")
        print(f"平均速率: {average_rate:.2f} iter/s")

        # 验证稳定性
        assert success_rate > 0.95  # 至少95%成功率
        assert average_rate > 5     # 至少每秒5次迭代

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "not slow"])