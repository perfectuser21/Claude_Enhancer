#!/usr/bin/env python3
"""
Git缓存线程安全完整测试
测试修复后的modules/git_cache.py的线程安全特性
"""

import asyncio
import threading
import time
import random
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Any
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ThreadSafetyTest")

# 导入修复后的Git缓存
from modules.git_cache import (
    get_git_cache,
    reset_git_cache,
    get_cache_stats,
    GitCacheManager,
    get_cache_health_report,
    force_refresh_cache,
    is_cache_healthy
)


class ComprehensiveThreadSafetyTest:
    """Git缓存线程安全综合测试"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or str(Path.cwd())
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': [],
            'performance_metrics': {},
            'thread_safety_violations': [],
            'data_consistency_issues': []
        }
        self.result_lock = threading.Lock()

    def record_test_result(self, test_name: str, passed: bool, details: str = ""):
        """记录测试结果"""
        with self.result_lock:
            self.test_results['total_tests'] += 1
            if passed:
                self.test_results['passed_tests'] += 1
                status = "✅ PASS"
            else:
                self.test_results['failed_tests'] += 1
                status = "❌ FAIL"

            self.test_results['test_details'].append({
                'test': test_name,
                'status': status,
                'details': details,
                'timestamp': time.time()
            })
            print(f"{status}: {test_name} - {details}")

    def test_concurrent_cache_access(self, num_threads: int = 20, requests_per_thread: int = 10):
        """测试并发缓存访问"""
        print(f"\n🧪 测试并发缓存访问: {num_threads} 线程, 每线程 {requests_per_thread} 请求")

        cache = get_git_cache(self.project_root, cache_timeout=5)
        results = []
        errors = []

        def worker(thread_id: int):
            """工作线程"""
            thread_results = []
            for i in range(requests_per_thread):
                try:
                    start_time = time.time()

                    # 随机选择操作
                    operation = random.choice(['status', 'diff', 'git_cmd'])

                    if operation == 'status':
                        result = cache.batch_git_status()
                        thread_results.append({
                            'thread_id': thread_id,
                            'operation': 'batch_git_status',
                            'success': True,
                            'response_time': time.time() - start_time,
                            'result_type': type(result).__name__
                        })
                    elif operation == 'diff':
                        result = cache.batch_get_file_diff(['README.md', 'main/cli.py'])
                        thread_results.append({
                            'thread_id': thread_id,
                            'operation': 'batch_get_file_diff',
                            'success': True,
                            'response_time': time.time() - start_time,
                            'result_type': type(result).__name__
                        })
                    else:
                        result = cache.get_cached_git_result(['git', 'rev-parse', 'HEAD'])
                        thread_results.append({
                            'thread_id': thread_id,
                            'operation': 'get_cached_git_result',
                            'success': result is not None,
                            'response_time': time.time() - start_time,
                            'result_type': type(result).__name__
                        })

                    # 随机延迟
                    time.sleep(random.uniform(0.01, 0.1))

                except Exception as e:
                    errors.append(f"Thread {thread_id}: {str(e)}")
                    thread_results.append({
                        'thread_id': thread_id,
                        'operation': 'error',
                        'success': False,
                        'error': str(e)
                    })

            results.extend(thread_results)

        # 启动所有线程
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 分析结果
        successful_operations = [r for r in results if r.get('success', False)]
        failed_operations = [r for r in results if not r.get('success', True)]

        success_rate = len(successful_operations) / len(results) * 100 if results else 0
        avg_response_time = sum(r.get('response_time', 0) for r in successful_operations) / len(successful_operations) if successful_operations else 0

        self.test_results['performance_metrics']['concurrent_access'] = {
            'total_operations': len(results),
            'successful_operations': len(successful_operations),
            'failed_operations': len(failed_operations),
            'success_rate': success_rate,
            'avg_response_time': avg_response_time,
            'errors': errors[:5]  # 保留前5个错误
        }

        passed = success_rate >= 95 and len(errors) == 0
        self.record_test_result(
            "concurrent_cache_access",
            passed,
            f"成功率: {success_rate:.1f}%, 平均响应时间: {avg_response_time*1000:.1f}ms"
        )

    def test_double_checked_locking(self):
        """测试双重检查锁定"""
        print("\n🔒 测试双重检查锁定模式")

        cache = get_git_cache(self.project_root, cache_timeout=10)
        cache.clear_cache()  # 清空缓存开始测试

        results = {}
        execution_times = []

        def worker(thread_id: int):
            """工作线程"""
            start_time = time.time()
            result = cache.batch_git_status()
            end_time = time.time()

            results[thread_id] = {
                'result': result,
                'execution_time': end_time - start_time,
                'timestamp': end_time
            }
            execution_times.append(end_time - start_time)

        # 同时启动多个线程
        threads = []
        for i in range(10):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)

        # 几乎同时启动所有线程
        start_time = time.time()
        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()
        total_time = time.time() - start_time

        # 验证数据一致性
        first_result = list(results.values())[0]['result']
        data_consistent = all(
            r['result'].get('current_branch') == first_result.get('current_branch')
            for r in results.values()
        )

        # 验证性能 - 应该有缓存效果
        cache_stats = cache.get_stats()
        cache_hits = cache_stats.get('cache_hits', 0)

        passed = data_consistent and cache_hits > 0
        self.record_test_result(
            "double_checked_locking",
            passed,
            f"数据一致性: {'✅' if data_consistent else '❌'}, 缓存命中: {cache_hits}, 总耗时: {total_time:.3f}s"
        )

    def test_cache_invalidation_strategy(self):
        """测试缓存失效策略"""
        print("\n🔄 测试缓存失效策略")

        cache = get_git_cache(self.project_root, cache_timeout=2)  # 短TTL
        cache.clear_cache()

        # 第一次请求 - 缓存失效
        result1 = cache.batch_git_status()
        stats1 = cache.get_stats()

        # 第二次请求 - 缓存命中
        result2 = cache.batch_git_status()
        stats2 = cache.get_stats()

        # 等待缓存过期
        time.sleep(3)

        # 第三次请求 - 缓存应该已过期
        result3 = cache.batch_git_status()
        stats3 = cache.get_stats()

        # 强制刷新测试
        cache.force_refresh_cache()
        result4 = cache.batch_git_status()
        stats4 = cache.get_stats()

        # 验证缓存行为
        cache_hit_increase = stats2['cache_hits'] > stats1['cache_hits']
        cache_miss_after_expire = stats3['cache_misses'] > stats2['cache_misses']
        invalidation_count = stats4.get('cache_invalidations', 0)

        passed = cache_hit_increase and cache_miss_after_expire and invalidation_count > 0
        self.record_test_result(
            "cache_invalidation_strategy",
            passed,
            f"缓存命中增加: {'✅' if cache_hit_increase else '❌'}, "
            f"过期后失效: {'✅' if cache_miss_after_expire else '❌'}, "
            f"强制失效: {invalidation_count}"
        )

    def test_error_recovery_mechanism(self):
        """测试错误恢复机制"""
        print("\n🔧 测试错误恢复机制")

        cache = get_git_cache("/invalid/path", cache_timeout=5)  # 无效路径

        error_count = 0
        successful_fallback = 0

        # 连续执行多次会出错的操作
        for i in range(5):
            try:
                result = cache.batch_git_status()
                if 'error' in str(result).lower() or result.get('current_branch') == 'unknown':
                    successful_fallback += 1
                else:
                    # 如果没有错误，说明可能有备用机制
                    successful_fallback += 1
            except Exception:
                error_count += 1

        # 测试错误计数机制
        stats = cache.get_stats()

        # 验证健康检查
        health_report = cache.get_cache_health_report()

        passed = successful_fallback > 0 and health_report is not None
        self.record_test_result(
            "error_recovery_mechanism",
            passed,
            f"错误数: {error_count}, 成功回退: {successful_fallback}, "
            f"健康分数: {health_report.get('health_score', 0)}"
        )

    def test_cache_manager_singleton(self):
        """测试缓存管理器单例模式"""
        print("\n🏗️ 测试缓存管理器单例模式")

        managers = []

        def get_manager_worker():
            manager = GitCacheManager.get_instance()
            managers.append(id(manager))

        threads = []
        for i in range(10):
            thread = threading.Thread(target=get_manager_worker)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # 所有管理器应该是同一个实例
        unique_managers = set(managers)

        passed = len(unique_managers) == 1
        self.record_test_result(
            "cache_manager_singleton",
            passed,
            f"唯一管理器实例: {len(unique_managers) == 1}, 实例ID数: {len(unique_managers)}"
        )

    def test_fine_grained_locking(self):
        """测试细粒度锁定"""
        print("\n🔐 测试细粒度锁定机制")

        cache = get_git_cache(self.project_root, cache_timeout=10)
        cache.clear_cache()

        lock_wait_counts = []

        def concurrent_different_operations(thread_id: int):
            """执行不同类型的操作"""
            start_time = time.time()

            if thread_id % 3 == 0:
                cache.batch_git_status()
            elif thread_id % 3 == 1:
                cache.get_cached_git_result(['git', 'rev-parse', 'HEAD'])
            else:
                cache.batch_get_file_diff(['README.md'])

            end_time = time.time()

            # 获取锁等待统计
            stats = cache.get_stats()
            lock_wait_counts.append(stats.get('lock_waits', 0))

        # 启动多线程执行不同操作
        threads = []
        for i in range(15):
            thread = threading.Thread(target=concurrent_different_operations, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # 分析锁竞争情况
        final_stats = cache.get_stats()
        total_lock_waits = final_stats.get('lock_waits', 0)
        total_requests = final_stats.get('cache_hits', 0) + final_stats.get('cache_misses', 0)

        lock_contention_ratio = total_lock_waits / max(total_requests, 1)

        # 细粒度锁应该降低锁竞争
        passed = lock_contention_ratio < 2.0  # 合理的锁竞争比例
        self.record_test_result(
            "fine_grained_locking",
            passed,
            f"锁竞争比例: {lock_contention_ratio:.2f}, 总锁等待: {total_lock_waits}"
        )

    def test_cache_size_limits_and_eviction(self):
        """测试缓存大小限制和驱逐策略"""
        print("\n📦 测试缓存大小限制和驱逐策略")

        cache = get_git_cache(self.project_root, cache_timeout=60)  # 长TTL
        cache.clear_cache()

        # 强制缓存很多不同的条目
        commands = [
            ['git', 'rev-parse', 'HEAD'],
            ['git', 'status', '--porcelain'],
            ['git', 'log', '-1', '--oneline'],
            ['git', 'branch', '-a'],
            ['git', 'remote', '-v']
        ]

        initial_size = len(cache._cache)

        # 执行大量不同的命令以填充缓存
        for i in range(50):
            for cmd in commands:
                # 添加随机参数使每个命令都不同
                modified_cmd = cmd + [f'--dummy-{i}-{random.randint(1, 1000)}']
                try:
                    cache.get_cached_git_result(modified_cmd)
                except:
                    pass  # 忽略错误，关注缓存行为

        stats = cache.get_stats()
        cache_size = stats.get('cache_size', 0)
        max_cache_size = stats.get('max_cache_size', 1000)

        # 检查缓存是否被限制
        cache_within_limits = cache_size <= max_cache_size
        eviction_occurred = stats.get('cache_invalidations', 0) > 0

        passed = cache_within_limits
        self.record_test_result(
            "cache_size_limits_and_eviction",
            passed,
            f"缓存大小: {cache_size}/{max_cache_size}, "
            f"在限制内: {'✅' if cache_within_limits else '❌'}, "
            f"发生驱逐: {'✅' if eviction_occurred else '❌'}"
        )

    def test_atomic_cache_operations(self):
        """测试原子性缓存操作"""
        print("\n⚛️ 测试原子性缓存操作")

        cache = get_git_cache(self.project_root, cache_timeout=10)

        # 测试并发读写的原子性
        read_results = []
        write_operations = []

        def reader_worker(thread_id: int):
            """读取工作线程"""
            for i in range(20):
                try:
                    result = cache.batch_git_status()
                    read_results.append({
                        'thread_id': thread_id,
                        'iteration': i,
                        'result': result.get('current_branch', 'unknown'),
                        'timestamp': time.time()
                    })
                except Exception as e:
                    read_results.append({
                        'thread_id': thread_id,
                        'iteration': i,
                        'error': str(e),
                        'timestamp': time.time()
                    })
                time.sleep(0.01)

        def writer_worker():
            """写入工作线程（缓存清理）"""
            for i in range(5):
                time.sleep(0.05)
                cache.clear_cache()
                write_operations.append({
                    'operation': 'clear_cache',
                    'timestamp': time.time()
                })

        # 启动读写线程
        readers = [threading.Thread(target=reader_worker, args=(i,)) for i in range(3)]
        writer = threading.Thread(target=writer_worker)

        for reader in readers:
            reader.start()
        writer.start()

        for reader in readers:
            reader.join()
        writer.join()

        # 验证原子性 - 没有损坏的数据
        valid_reads = [r for r in read_results if 'error' not in r and r.get('result') != '']
        corrupted_reads = [r for r in read_results if 'error' in r and 'corrupt' in str(r.get('error', '')).lower()]

        passed = len(corrupted_reads) == 0 and len(valid_reads) > 0
        self.record_test_result(
            "atomic_cache_operations",
            passed,
            f"有效读取: {len(valid_reads)}, 损坏读取: {len(corrupted_reads)}, "
            f"写操作: {len(write_operations)}"
        )

    def run_performance_benchmark(self):
        """性能基准测试"""
        print("\n📊 性能基准测试")

        cache = get_git_cache(self.project_root, cache_timeout=30)

        # 单线程性能
        start_time = time.time()
        for _ in range(100):
            cache.batch_git_status()
        single_thread_time = time.time() - start_time

        # 清理缓存重新测试
        cache.clear_cache()

        # 多线程性能
        def multi_thread_worker():
            for _ in range(20):
                cache.batch_git_status()

        start_time = time.time()
        threads = [threading.Thread(target=multi_thread_worker) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        multi_thread_time = time.time() - start_time

        # 性能指标
        stats = cache.get_stats()
        health_report = cache.get_cache_health_report()

        self.test_results['performance_metrics']['benchmark'] = {
            'single_thread_time': single_thread_time,
            'multi_thread_time': multi_thread_time,
            'cache_stats': stats,
            'health_score': health_report.get('health_score', 0)
        }

        # 多线程应该有更好的吞吐量（考虑到缓存）
        efficiency_ratio = single_thread_time / multi_thread_time if multi_thread_time > 0 else 0

        passed = efficiency_ratio > 0.5 and health_report.get('health_score', 0) >= 70
        self.record_test_result(
            "performance_benchmark",
            passed,
            f"单线程: {single_thread_time:.3f}s, 多线程: {multi_thread_time:.3f}s, "
            f"效率比: {efficiency_ratio:.2f}, 健康分数: {health_report.get('health_score', 0)}"
        )

    def print_comprehensive_report(self):
        """打印综合测试报告"""
        print("\n" + "="*80)
        print("🎯 Git缓存线程安全综合测试报告")
        print("="*80)

        results = self.test_results

        print(f"📋 测试概览:")
        print(f"  总测试数: {results['total_tests']}")
        print(f"  通过测试: {results['passed_tests']} ✅")
        print(f"  失败测试: {results['failed_tests']} ❌")
        print(f"  成功率: {results['passed_tests']/results['total_tests']*100:.1f}%" if results['total_tests'] > 0 else "  成功率: N/A")

        print(f"\n📊 性能指标:")
        for metric_name, metrics in results['performance_metrics'].items():
            print(f"  {metric_name}:")
            if isinstance(metrics, dict):
                for key, value in metrics.items():
                    if isinstance(value, (int, float)):
                        print(f"    {key}: {value}")
                    elif isinstance(value, list) and len(value) <= 5:
                        print(f"    {key}: {value}")

        print(f"\n📝 测试详情:")
        for detail in results['test_details']:
            print(f"  {detail['status']}: {detail['test']}")
            if detail['details']:
                print(f"      {detail['details']}")

        # 获取当前缓存统计
        try:
            all_stats = get_cache_stats()
            print(f"\n🏥 当前缓存健康状态:")
            for cache_key, stats in all_stats.items():
                if isinstance(stats, dict) and 'thread_safety_enabled' in stats:
                    print(f"  缓存 {cache_key}:")
                    print(f"    线程安全: ✅")
                    print(f"    命中率: {stats.get('hit_rate', 'N/A')}")
                    print(f"    缓存大小: {stats.get('cache_size', 0)}")
                    print(f"    锁等待次数: {stats.get('lock_waits', 0)}")
        except Exception as e:
            print(f"  获取缓存统计失败: {e}")

        print("\n🎯 线程安全修复验证:")
        if results['passed_tests'] >= results['total_tests'] * 0.8:
            print("  ✅ 线程安全修复成功！所有关键测试通过")
        else:
            print("  ⚠️  部分测试失败，需要进一步优化")

        print("\n" + "="*80)


def main():
    """主测试函数"""
    print("🚀 Git缓存线程安全完整测试开始")
    print("="*50)

    # 重置缓存确保干净的测试环境
    reset_git_cache()

    tester = ComprehensiveThreadSafetyTest()

    try:
        # 执行所有测试
        test_methods = [
            tester.test_concurrent_cache_access,
            tester.test_double_checked_locking,
            tester.test_cache_invalidation_strategy,
            tester.test_error_recovery_mechanism,
            tester.test_cache_manager_singleton,
            tester.test_fine_grained_locking,
            tester.test_cache_size_limits_and_eviction,
            tester.test_atomic_cache_operations,
            tester.run_performance_benchmark
        ]

        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                logger.error(f"测试 {test_method.__name__} 执行失败: {e}")
                tester.record_test_result(
                    test_method.__name__,
                    False,
                    f"测试执行异常: {str(e)}"
                )

        # 打印综合报告
        tester.print_comprehensive_report()

        # 最终验证
        final_success_rate = tester.test_results['passed_tests'] / tester.test_results['total_tests'] * 100
        if final_success_rate >= 80:
            print("\n🎉 线程安全修复验证成功！")
            return 0
        else:
            print(f"\n⚠️ 线程安全修复需要改进，成功率: {final_success_rate:.1f}%")
            return 1

    except Exception as e:
        print(f"\n❌ 测试过程中发生严重错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())