#!/usr/bin/env python3
"""
Perfect21性能优化验证测试
全面测试和验证性能优化效果
"""

import os
import sys
import asyncio
import time
import statistics
import psutil
import json
from typing import Dict, Any, List, Tuple
from datetime import datetime
import concurrent.futures
import threading

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.enhanced_performance_optimizer import (
    enhanced_performance_optimizer,
    optimize_agent_execution,
    batch_git_operations,
    optimize_memory,
    start_performance_optimization,
    get_performance_report,
    run_benchmark,
    optimized_execution
)
from modules.enhanced_git_cache import (
    enhanced_git_cache,
    git_batch_processor,
    queue_git_operation,
    get_git_cache_stats
)
from modules.performance_cache import performance_cache
from modules.logger import log_info, log_error

class PerformanceValidator:
    """性能优化验证器"""

    def __init__(self):
        self.test_results = {}
        self.baseline_metrics = {}
        self.optimized_metrics = {}

        log_info("性能验证器初始化完成")

    async def run_comprehensive_validation(self) -> Dict[str, Any]:
        """运行全面性能验证"""
        print("🚀 开始Perfect21性能优化验证")
        print("=" * 60)

        validation_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'summary': {},
            'recommendations': []
        }

        # 1. 基线性能测试
        print("📊 建立性能基线...")
        baseline_results = await self._establish_baseline()
        validation_results['tests']['baseline'] = baseline_results

        # 2. Agent执行优化测试
        print("🤖 测试Agent执行优化...")
        agent_results = await self._test_agent_optimization()
        validation_results['tests']['agent_optimization'] = agent_results

        # 3. 缓存系统测试
        print("📦 测试缓存系统...")
        cache_results = await self._test_cache_system()
        validation_results['tests']['cache_system'] = cache_results

        # 4. Git操作优化测试
        print("🔧 测试Git操作优化...")
        git_results = await self._test_git_optimization()
        validation_results['tests']['git_optimization'] = git_results

        # 5. 内存优化测试
        print("💾 测试内存优化...")
        memory_results = await self._test_memory_optimization()
        validation_results['tests']['memory_optimization'] = memory_results

        # 6. 并发性能测试
        print("⚡ 测试并发性能...")
        concurrency_results = await self._test_concurrency_performance()
        validation_results['tests']['concurrency'] = concurrency_results

        # 7. 资源池测试
        print("🔄 测试资源池...")
        pool_results = await self._test_resource_pool()
        validation_results['tests']['resource_pool'] = pool_results

        # 生成总结和建议
        validation_results['summary'] = self._generate_summary(validation_results['tests'])
        validation_results['recommendations'] = self._generate_recommendations(validation_results['tests'])

        print("\n✅ 性能验证完成!")
        return validation_results

    async def _establish_baseline(self) -> Dict[str, Any]:
        """建立性能基线"""
        baseline = {}

        # 系统资源基线
        process = psutil.Process()
        baseline['initial_memory_mb'] = process.memory_info().rss / 1024 / 1024
        baseline['initial_cpu_percent'] = process.cpu_percent()

        # 执行基线测试
        execution_times = []
        for i in range(10):
            start_time = time.perf_counter()
            await asyncio.sleep(0.01)  # 模拟10ms操作
            execution_time = time.perf_counter() - start_time
            execution_times.append(execution_time * 1000)  # 转换为毫秒

        baseline['avg_execution_time_ms'] = statistics.mean(execution_times)
        baseline['p95_execution_time_ms'] = statistics.quantiles(execution_times, n=20)[18]

        return baseline

    async def _test_agent_optimization(self) -> Dict[str, Any]:
        """测试Agent执行优化"""
        results = {}

        # 测试缓存命中
        agent_type = 'test-agent'
        params = {'test_param': 'test_value'}

        # 第一次执行 (缓存未命中)
        start_time = time.perf_counter()
        result1 = await optimize_agent_execution(agent_type, params)
        first_execution_time = time.perf_counter() - start_time

        # 第二次执行 (缓存命中)
        start_time = time.perf_counter()
        result2 = await optimize_agent_execution(agent_type, params)
        second_execution_time = time.perf_counter() - start_time

        # 计算缓存效果
        cache_improvement = ((first_execution_time - second_execution_time) / first_execution_time) * 100

        results['first_execution_time_ms'] = first_execution_time * 1000
        results['second_execution_time_ms'] = second_execution_time * 1000
        results['cache_improvement_percent'] = cache_improvement
        results['cache_working'] = second_execution_time < first_execution_time * 0.5  # 至少50%提升

        # 测试不同Agent类型
        agent_types = ['agent-1', 'agent-2', 'agent-3']
        concurrent_times = []

        async def test_agent(agent_type):
            start_time = time.perf_counter()
            await optimize_agent_execution(agent_type, {'id': agent_type})
            return time.perf_counter() - start_time

        # 并发执行
        start_time = time.perf_counter()
        concurrent_results = await asyncio.gather(*[test_agent(agent) for agent in agent_types])
        total_concurrent_time = time.perf_counter() - start_time

        # 顺序执行对比
        sequential_times = []
        for agent_type in agent_types:
            start_time = time.perf_counter()
            await optimize_agent_execution(agent_type, {'id': agent_type})
            sequential_times.append(time.perf_counter() - start_time)

        total_sequential_time = sum(sequential_times)

        results['concurrent_execution_time_ms'] = total_concurrent_time * 1000
        results['sequential_execution_time_ms'] = total_sequential_time * 1000
        results['concurrency_improvement_percent'] = ((total_sequential_time - total_concurrent_time) / total_sequential_time) * 100

        return results

    async def _test_cache_system(self) -> Dict[str, Any]:
        """测试缓存系统"""
        results = {}

        # 测试多层缓存
        cache_operations = []

        # 异步缓存测试
        async_test_data = {'test': 'async_data', 'timestamp': time.time()}
        await enhanced_performance_optimizer.cache_system.async_set('async_test_key', async_test_data)
        cached_data = await enhanced_performance_optimizer.cache_system.async_get('async_test_key')

        results['async_cache_working'] = cached_data == async_test_data

        # Git缓存测试
        git_cache_stats_before = get_git_cache_stats()

        # 模拟Git操作
        test_operations = [
            ('status', []),
            ('branch', []),
            ('log', ['--oneline', '-10']),
            ('status', []),  # 重复操作测试缓存
            ('log', ['--oneline', '-10'])  # 重复操作测试缓存
        ]

        git_execution_times = []
        for command, args in test_operations:
            start_time = time.perf_counter()
            # 这里模拟Git缓存调用
            cached_result = enhanced_git_cache.get_cached_result(command, args)
            if cached_result is None:
                # 模拟Git执行并缓存
                mock_result = f"Mock {command} result"
                enhanced_git_cache.cache_result(command, args, mock_result)
            execution_time = time.perf_counter() - start_time
            git_execution_times.append(execution_time * 1000)

        git_cache_stats_after = get_git_cache_stats()

        results['git_cache_hit_rate'] = git_cache_stats_after['hit_rate']
        results['git_cache_entries'] = git_cache_stats_after['total_entries']
        results['avg_git_operation_time_ms'] = statistics.mean(git_execution_times)

        # 通用缓存测试
        cache_hit_times = []
        cache_miss_times = []

        # 测试缓存未命中
        for i in range(5):
            start_time = time.perf_counter()
            with performance_cache.get_dict() as test_dict:
                test_dict[f'key_{i}'] = f'value_{i}'
                # 模拟处理
                sum(range(100))
            miss_time = time.perf_counter() - start_time
            cache_miss_times.append(miss_time * 1000)

        results['avg_cache_miss_time_ms'] = statistics.mean(cache_miss_times)

        # 内存池效率测试
        pool_stats = enhanced_performance_optimizer.resource_manager.get_pool_stats()
        results['resource_pool_stats'] = pool_stats

        return results

    async def _test_git_optimization(self) -> Dict[str, Any]:
        """测试Git操作优化"""
        results = {}

        # 测试批量Git操作
        batch_operations = [
            ('status', []),
            ('status', ['--short']),
            ('branch', []),
            ('branch', ['-r']),
            ('log', ['--oneline', '-5']),
            ('log', ['--oneline', '-10'])
        ]

        # 批量执行
        batch_start_time = time.perf_counter()
        operation_callbacks = []
        operation_results = []

        def create_callback(op_id):
            def callback(result):
                operation_results.append((op_id, result, time.perf_counter()))
            return callback

        # 队列所有操作
        for i, (command, args) in enumerate(batch_operations):
            callback = create_callback(i)
            operation_callbacks.append(callback)
            queue_git_operation(command, args, callback)

        # 等待批量处理完成
        await asyncio.sleep(3)  # 等待批量处理

        batch_total_time = time.perf_counter() - batch_start_time

        # 单独执行对比
        individual_start_time = time.perf_counter()
        for command, args in batch_operations:
            # 模拟单独Git执行
            start_time = time.perf_counter()
            cached_result = enhanced_git_cache.get_cached_result(command, args)
            if cached_result is None:
                # 模拟Git命令执行延迟
                await asyncio.sleep(0.05)  # 50ms模拟Git命令
                enhanced_git_cache.cache_result(command, args, f"Individual {command} result")
            individual_time = time.perf_counter() - start_time

        individual_total_time = time.perf_counter() - individual_start_time

        # 计算批量优化效果
        batch_improvement = ((individual_total_time - batch_total_time) / individual_total_time) * 100

        results['batch_execution_time_ms'] = batch_total_time * 1000
        results['individual_execution_time_ms'] = individual_total_time * 1000
        results['batch_improvement_percent'] = batch_improvement
        results['operations_processed'] = len(batch_operations)
        results['batch_optimization_working'] = batch_improvement > 20  # 至少20%提升

        # Git缓存统计
        git_stats = get_git_cache_stats()
        results['git_cache_final_stats'] = git_stats

        return results

    async def _test_memory_optimization(self) -> Dict[str, Any]:
        """测试内存优化"""
        results = {}

        # 内存使用基线
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024

        # 创建内存压力
        memory_hogs = []
        for i in range(100):
            # 创建大对象
            memory_hogs.append([f'data_{j}' for j in range(1000)])

        before_optimization_memory = process.memory_info().rss / 1024 / 1024

        # 执行内存优化
        optimization_result = await optimize_memory()

        after_optimization_memory = process.memory_info().rss / 1024 / 1024

        # 清理测试对象
        del memory_hogs

        final_memory = process.memory_info().rss / 1024 / 1024

        results['initial_memory_mb'] = initial_memory
        results['before_optimization_memory_mb'] = before_optimization_memory
        results['after_optimization_memory_mb'] = after_optimization_memory
        results['final_memory_mb'] = final_memory
        results['memory_freed_by_optimization_mb'] = before_optimization_memory - after_optimization_memory
        results['optimization_effectiveness'] = optimization_result
        results['memory_optimization_working'] = before_optimization_memory > after_optimization_memory

        return results

    async def _test_concurrency_performance(self) -> Dict[str, Any]:
        """测试并发性能"""
        results = {}

        # 并发Agent执行测试
        concurrent_tasks = 20

        async def concurrent_agent_task(task_id: int):
            start_time = time.perf_counter()
            result = await optimize_agent_execution(f'concurrent-agent-{task_id}', {'task_id': task_id})
            execution_time = time.perf_counter() - start_time
            return task_id, execution_time, result

        # 并发执行
        concurrent_start_time = time.perf_counter()
        concurrent_results = await asyncio.gather(*[
            concurrent_agent_task(i) for i in range(concurrent_tasks)
        ])
        concurrent_total_time = time.perf_counter() - concurrent_start_time

        # 顺序执行对比
        sequential_start_time = time.perf_counter()
        sequential_results = []
        for i in range(concurrent_tasks):
            task_result = await concurrent_agent_task(i)
            sequential_results.append(task_result)
        sequential_total_time = time.perf_counter() - sequential_start_time

        # 分析结果
        concurrent_individual_times = [result[1] * 1000 for result in concurrent_results]
        sequential_individual_times = [result[1] * 1000 for result in sequential_results]

        results['concurrent_tasks'] = concurrent_tasks
        results['concurrent_total_time_ms'] = concurrent_total_time * 1000
        results['sequential_total_time_ms'] = sequential_total_time * 1000
        results['concurrency_speedup'] = sequential_total_time / concurrent_total_time
        results['avg_concurrent_task_time_ms'] = statistics.mean(concurrent_individual_times)
        results['avg_sequential_task_time_ms'] = statistics.mean(sequential_individual_times)
        results['concurrency_efficiency'] = (concurrent_tasks / (concurrent_total_time / (sequential_total_time / concurrent_tasks))) * 100

        return results

    async def _test_resource_pool(self) -> Dict[str, Any]:
        """测试资源池"""
        results = {}

        # 资源池使用测试
        pool_usage_times = []
        direct_creation_times = []

        # 测试资源池使用
        for i in range(50):
            start_time = time.perf_counter()
            with enhanced_performance_optimizer.resource_manager.get_resource('dict') as test_dict:
                test_dict['test_key'] = f'test_value_{i}'
                # 模拟使用
                len(test_dict)
            pool_time = time.perf_counter() - start_time
            pool_usage_times.append(pool_time * 1000)

        # 测试直接创建
        for i in range(50):
            start_time = time.perf_counter()
            test_dict = {}
            test_dict['test_key'] = f'test_value_{i}'
            len(test_dict)
            del test_dict
            direct_time = time.perf_counter() - start_time
            direct_creation_times.append(direct_time * 1000)

        # 分析效果
        avg_pool_time = statistics.mean(pool_usage_times)
        avg_direct_time = statistics.mean(direct_creation_times)
        pool_efficiency = ((avg_direct_time - avg_pool_time) / avg_direct_time) * 100

        results['avg_pool_usage_time_ms'] = avg_pool_time
        results['avg_direct_creation_time_ms'] = avg_direct_time
        results['pool_efficiency_percent'] = pool_efficiency
        results['pool_working'] = avg_pool_time < avg_direct_time

        # 获取资源池统计
        pool_stats = enhanced_performance_optimizer.resource_manager.get_pool_stats()
        results['pool_stats'] = pool_stats

        return results

    def _generate_summary(self, tests: Dict[str, Any]) -> Dict[str, Any]:
        """生成测试总结"""
        summary = {
            'total_tests': len(tests),
            'passed_tests': 0,
            'failed_tests': 0,
            'performance_improvements': {},
            'issues_found': []
        }

        # 分析各项测试
        test_status = {}

        # Agent优化测试
        if 'agent_optimization' in tests:
            agent_test = tests['agent_optimization']
            agent_passed = (agent_test.get('cache_working', False) and
                          agent_test.get('cache_improvement_percent', 0) > 10)
            test_status['agent_optimization'] = agent_passed

            if agent_passed:
                summary['performance_improvements']['agent_cache'] = f"{agent_test.get('cache_improvement_percent', 0):.1f}%"
            else:
                summary['issues_found'].append("Agent缓存优化效果不明显")

        # 缓存系统测试
        if 'cache_system' in tests:
            cache_test = tests['cache_system']
            cache_passed = cache_test.get('async_cache_working', False)
            test_status['cache_system'] = cache_passed

            if not cache_passed:
                summary['issues_found'].append("异步缓存系统工作异常")

        # Git优化测试
        if 'git_optimization' in tests:
            git_test = tests['git_optimization']
            git_passed = (git_test.get('batch_optimization_working', False) and
                         git_test.get('batch_improvement_percent', 0) > 20)
            test_status['git_optimization'] = git_passed

            if git_passed:
                summary['performance_improvements']['git_batch'] = f"{git_test.get('batch_improvement_percent', 0):.1f}%"
            else:
                summary['issues_found'].append("Git批量优化效果不足")

        # 内存优化测试
        if 'memory_optimization' in tests:
            memory_test = tests['memory_optimization']
            memory_passed = memory_test.get('memory_optimization_working', False)
            test_status['memory_optimization'] = memory_passed

            if memory_passed:
                memory_freed = memory_test.get('memory_freed_by_optimization_mb', 0)
                summary['performance_improvements']['memory_freed'] = f"{memory_freed:.2f}MB"
            else:
                summary['issues_found'].append("内存优化效果不明显")

        # 并发性能测试
        if 'concurrency' in tests:
            concurrency_test = tests['concurrency']
            speedup = concurrency_test.get('concurrency_speedup', 1)
            concurrency_passed = speedup > 1.5  # 至少1.5倍加速
            test_status['concurrency'] = concurrency_passed

            if concurrency_passed:
                summary['performance_improvements']['concurrency_speedup'] = f"{speedup:.1f}x"
            else:
                summary['issues_found'].append("并发性能提升不足")

        # 资源池测试
        if 'resource_pool' in tests:
            pool_test = tests['resource_pool']
            pool_passed = pool_test.get('pool_working', False)
            test_status['resource_pool'] = pool_passed

            if pool_passed:
                pool_efficiency = pool_test.get('pool_efficiency_percent', 0)
                summary['performance_improvements']['resource_pool'] = f"{pool_efficiency:.1f}%"
            else:
                summary['issues_found'].append("资源池效率不佳")

        # 统计通过/失败测试
        summary['passed_tests'] = sum(1 for passed in test_status.values() if passed)
        summary['failed_tests'] = len(test_status) - summary['passed_tests']
        summary['test_status'] = test_status

        return summary

    def _generate_recommendations(self, tests: Dict[str, Any]) -> List[Dict[str, str]]:
        """生成优化建议"""
        recommendations = []

        # 基于测试结果生成建议
        if 'agent_optimization' in tests:
            agent_test = tests['agent_optimization']
            if agent_test.get('cache_improvement_percent', 0) < 20:
                recommendations.append({
                    'category': 'agent_cache',
                    'priority': 'medium',
                    'recommendation': '增加Agent缓存TTL或优化缓存键生成策略',
                    'expected_benefit': '提升Agent执行效率20-40%'
                })

        if 'git_optimization' in tests:
            git_test = tests['git_optimization']
            if git_test.get('batch_improvement_percent', 0) < 30:
                recommendations.append({
                    'category': 'git_batch',
                    'priority': 'high',
                    'recommendation': '调整Git批量处理间隔和批量大小',
                    'expected_benefit': '减少Git操作延迟30-50%'
                })

        if 'memory_optimization' in tests:
            memory_test = tests['memory_optimization']
            if memory_test.get('memory_freed_by_optimization_mb', 0) < 10:
                recommendations.append({
                    'category': 'memory',
                    'priority': 'medium',
                    'recommendation': '启用更积极的垃圾回收策略',
                    'expected_benefit': '降低内存使用10-20MB'
                })

        if 'concurrency' in tests:
            concurrency_test = tests['concurrency']
            if concurrency_test.get('concurrency_speedup', 1) < 2:
                recommendations.append({
                    'category': 'concurrency',
                    'priority': 'high',
                    'recommendation': '优化异步执行和线程池配置',
                    'expected_benefit': '提升并发性能2-3倍'
                })

        return recommendations

    def print_validation_report(self, results: Dict[str, Any]) -> None:
        """打印验证报告"""
        print("\n" + "=" * 60)
        print("🏁 Perfect21性能优化验证报告")
        print("=" * 60)

        summary = results.get('summary', {})

        # 总体状况
        total_tests = summary.get('total_tests', 0)
        passed_tests = summary.get('passed_tests', 0)
        failed_tests = summary.get('failed_tests', 0)

        success_rate = (passed_tests / max(1, total_tests)) * 100

        print(f"📊 测试结果: {passed_tests}/{total_tests} 通过 ({success_rate:.1f}%)")

        if success_rate >= 80:
            print("🟢 整体性能: 优秀")
        elif success_rate >= 60:
            print("🟡 整体性能: 良好")
        else:
            print("🔴 整体性能: 需要改进")

        # 性能提升
        improvements = summary.get('performance_improvements', {})
        if improvements:
            print("\n✨ 性能提升:")
            for category, improvement in improvements.items():
                print(f"  • {category}: {improvement}")

        # 问题和建议
        issues = summary.get('issues_found', [])
        if issues:
            print("\n⚠️ 发现的问题:")
            for issue in issues:
                print(f"  • {issue}")

        recommendations = results.get('recommendations', [])
        if recommendations:
            print("\n💡 优化建议:")
            for i, rec in enumerate(recommendations[:3], 1):
                priority_icon = {'high': '🔴', 'medium': '🟠', 'low': '🟡'}.get(rec['priority'], '⚪')
                print(f"  {i}. {priority_icon} {rec['recommendation']}")
                print(f"     预期收益: {rec['expected_benefit']}")

        print("\n" + "=" * 60)

async def main():
    """主函数"""
    validator = PerformanceValidator()

    try:
        # 运行全面验证
        results = await validator.run_comprehensive_validation()

        # 打印报告
        validator.print_validation_report(results)

        # 保存详细结果
        output_file = f"performance_validation_{int(time.time())}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n📁 详细报告已保存: {output_file}")

        return results

    except Exception as e:
        log_error(f"性能验证失败: {e}")
        print(f"❌ 验证失败: {e}")
        return None

if __name__ == "__main__":
    import platform

    print(f"🚀 Perfect21性能验证")
    print(f"Python版本: {platform.python_version()}")
    print(f"平台: {platform.platform()}")

    results = asyncio.run(main())

    if results:
        summary = results.get('summary', {})
        success_rate = (summary.get('passed_tests', 0) / max(1, summary.get('total_tests', 1))) * 100

        if success_rate >= 80:
            print("\n🎉 性能优化验证通过！Perfect21运行状态优秀。")
            exit(0)
        else:
            print("\n⚠️ 性能优化验证部分失败，建议查看详细报告。")
            exit(1)
    else:
        print("\n❌ 性能验证失败")
        exit(1)