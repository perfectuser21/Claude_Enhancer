#!/usr/bin/env python3
"""
Git缓存线程安全测试
测试双重检查锁定、Circuit Breaker和Fallback机制
"""

import asyncio
import threading
import time
import random
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from infrastructure.git.git_cache import get_git_cache, get_cache_manager, CircuitState

class GitCacheThreadSafetyTest:
    """Git缓存线程安全测试"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or str(Path.cwd())
        self.test_results = {
            'total_requests': 0,
            'successful_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'fallback_uses': 0,
            'circuit_breaker_trips': 0,
            'errors': [],
            'response_times': []
        }
        self.lock = threading.Lock()

    async def test_concurrent_access(self, num_threads: int = 10, requests_per_thread: int = 5):
        """测试并发访问"""
        print(f"🧪 开始并发访问测试: {num_threads} 线程, 每线程 {requests_per_thread} 请求")

        cache = get_git_cache(self.project_root, cache_ttl=5)  # 短TTL测试缓存

        async def worker(thread_id: int):
            """工作线程"""
            for i in range(requests_per_thread):
                start_time = time.time()
                try:
                    # 随机决定是否强制刷新
                    force_refresh = random.random() < 0.2
                    git_status = await cache.get_git_status(force_refresh=force_refresh)

                    response_time = time.time() - start_time

                    with self.lock:
                        self.test_results['total_requests'] += 1
                        self.test_results['successful_requests'] += 1
                        self.test_results['response_times'].append(response_time)

                        if git_status.is_fallback:
                            self.test_results['fallback_uses'] += 1

                    print(f"  线程{thread_id}-请求{i}: {'✅' if not git_status.is_fallback else '⚠️'} {response_time:.3f}s")

                    # 随机延迟
                    await asyncio.sleep(random.uniform(0.1, 0.5))

                except Exception as e:
                    with self.lock:
                        self.test_results['total_requests'] += 1
                        self.test_results['errors'].append(str(e))
                    print(f"  线程{thread_id}-请求{i}: ❌ 错误: {e}")

        # 创建并发任务
        tasks = [worker(i) for i in range(num_threads)]
        await asyncio.gather(*tasks)

        # 获取缓存信息
        cache_info = cache.get_cache_info()
        self.test_results.update({
            'cache_hits': cache_info['performance_metrics']['cache_hits'],
            'cache_misses': cache_info['performance_metrics']['cache_misses'],
            'circuit_breaker_trips': cache_info['performance_metrics']['circuit_breaker_trips']
        })

    def test_double_checked_locking(self):
        """测试双重检查锁定"""
        print("🔒 测试双重检查锁定模式")

        cache = get_git_cache(self.project_root, cache_ttl=10)
        results = []

        def sync_worker(thread_id: int):
            """同步工作线程"""
            try:
                # 使用asyncio.run在线程中运行async函数
                git_status = asyncio.run(cache.get_git_status())
                results.append({
                    'thread_id': thread_id,
                    'success': True,
                    'branch': git_status.current_branch,
                    'is_fallback': git_status.is_fallback
                })
            except Exception as e:
                results.append({
                    'thread_id': thread_id,
                    'success': False,
                    'error': str(e)
                })

        # 同时启动多个线程
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(sync_worker, i) for i in range(5)]
            for future in futures:
                future.result()  # 等待完成

        # 验证结果
        successful_results = [r for r in results if r['success']]
        print(f"  成功请求: {len(successful_results)}/{len(results)}")

        # 检查数据一致性
        branches = set(r['branch'] for r in successful_results if not r['is_fallback'])
        print(f"  数据一致性: {'✅' if len(branches) <= 1 else '❌'} (分支数: {len(branches)})")

    async def test_circuit_breaker(self):
        """测试Circuit Breaker机制"""
        print("⚡ 测试Circuit Breaker机制")

        # 创建一个新的缓存实例用于测试
        from infrastructure.git.git_cache import GitCache, CircuitBreakerConfig

        # 配置更激进的Circuit Breaker
        cache = GitCache("/invalid/path", cache_ttl=1)
        cache.circuit_breaker.config.failure_threshold = 3
        cache.circuit_breaker.config.timeout = 5

        print("  触发Circuit Breaker...")

        # 触发失败以开启Circuit Breaker
        for i in range(5):
            try:
                await cache.get_git_status()
            except Exception as e:
                print(f"    请求{i+1}: 失败 - {type(e).__name__}")

        # 检查Circuit Breaker状态
        cache_info = cache.get_cache_info()
        cb_state = cache_info['circuit_breaker_state']
        print(f"  Circuit Breaker状态: {cb_state}")

        if cb_state == CircuitState.OPEN.value:
            print("  ✅ Circuit Breaker正确开启")

            # 测试快速失败
            try:
                await cache.get_git_status()
                print("  ❌ Circuit Breaker未阻止请求")
            except Exception as e:
                print(f"  ✅ Circuit Breaker正确阻止请求: {type(e).__name__}")
        else:
            print(f"  ⚠️ Circuit Breaker状态异常: {cb_state}")

    async def test_fallback_mechanism(self):
        """测试Fallback机制"""
        print("🔄 测试Fallback机制")

        # 先获取正常数据
        cache = get_git_cache(self.project_root)
        try:
            normal_status = await cache.get_git_status()
            print(f"  正常数据获取成功: {normal_status.current_branch}")

            # 人为破坏缓存以触发fallback
            cache.project_root = Path("/invalid/path")

            # 尝试获取状态，应该返回fallback
            fallback_status = await cache.get_git_status()

            if fallback_status.is_fallback:
                print("  ✅ Fallback机制正常工作")
                print(f"    Fallback数据: {fallback_status.current_branch}")
            else:
                print("  ❌ Fallback机制未触发")

        except Exception as e:
            print(f"  ⚠️ Fallback测试异常: {e}")

    def test_cache_manager_thread_safety(self):
        """测试缓存管理器线程安全"""
        print("🏗️ 测试缓存管理器线程安全")

        manager = get_cache_manager()
        cache_instances = []

        def get_cache_worker(thread_id: int):
            """获取缓存实例的工作线程"""
            cache = manager.get_cache(self.project_root, cache_ttl=30)
            cache_instances.append((thread_id, id(cache)))

        # 多线程获取缓存实例
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(get_cache_worker, i) for i in range(10)]
            for future in futures:
                future.result()

        # 检查是否返回同一个实例
        cache_ids = set(cache_id for _, cache_id in cache_instances)
        print(f"  缓存实例数: {len(cache_ids)} (期望: 1)")
        print(f"  单例模式: {'✅' if len(cache_ids) == 1 else '❌'}")

    async def performance_test(self):
        """性能测试"""
        print("📊 性能测试")

        cache = get_git_cache(self.project_root, cache_ttl=30)

        # 预热缓存
        await cache.get_git_status()

        # 测试缓存命中性能
        start_time = time.time()
        for _ in range(100):
            await cache.get_git_status()
        cache_hit_time = time.time() - start_time

        # 测试缓存失效性能
        cache.invalidate_cache()
        start_time = time.time()
        for _ in range(10):
            await cache.get_git_status(force_refresh=True)
        cache_miss_time = time.time() - start_time

        print(f"  缓存命中 (100次): {cache_hit_time:.3f}s (平均: {cache_hit_time/100*1000:.1f}ms)")
        print(f"  缓存失效 (10次): {cache_miss_time:.3f}s (平均: {cache_miss_time/10*1000:.1f}ms)")

        # 获取性能指标
        cache_info = cache.get_cache_info()
        metrics = cache_info['performance_metrics']
        print(f"  总请求数: {metrics['total_requests']}")
        print(f"  缓存命中率: {metrics['cache_hits']/(metrics['cache_hits']+metrics['cache_misses'])*100:.1f}%")
        print(f"  平均响应时间: {metrics['avg_response_time']*1000:.1f}ms")

    def print_test_summary(self):
        """打印测试摘要"""
        print("\n" + "="*50)
        print("📋 测试摘要")
        print("="*50)

        if self.test_results['total_requests'] > 0:
            success_rate = self.test_results['successful_requests'] / self.test_results['total_requests'] * 100
            print(f"总请求数: {self.test_results['total_requests']}")
            print(f"成功率: {success_rate:.1f}%")

            if self.test_results['response_times']:
                avg_time = sum(self.test_results['response_times']) / len(self.test_results['response_times'])
                max_time = max(self.test_results['response_times'])
                min_time = min(self.test_results['response_times'])
                print(f"响应时间: 平均{avg_time*1000:.1f}ms, 最大{max_time*1000:.1f}ms, 最小{min_time*1000:.1f}ms")

            print(f"缓存命中: {self.test_results['cache_hits']}")
            print(f"缓存失效: {self.test_results['cache_misses']}")
            print(f"Fallback使用: {self.test_results['fallback_uses']}")
            print(f"熔断触发: {self.test_results['circuit_breaker_trips']}")

            if self.test_results['errors']:
                print(f"错误数: {len(self.test_results['errors'])}")
                for error in self.test_results['errors'][:3]:  # 显示前3个错误
                    print(f"  - {error}")

async def main():
    """主测试函数"""
    print("🚀 Git缓存线程安全测试开始")
    print("="*50)

    tester = GitCacheThreadSafetyTest()

    try:
        # 1. 并发访问测试
        await tester.test_concurrent_access(num_threads=8, requests_per_thread=3)
        print()

        # 2. 双重检查锁定测试
        tester.test_double_checked_locking()
        print()

        # 3. Circuit Breaker测试
        await tester.test_circuit_breaker()
        print()

        # 4. Fallback机制测试
        await tester.test_fallback_mechanism()
        print()

        # 5. 缓存管理器线程安全测试
        tester.test_cache_manager_thread_safety()
        print()

        # 6. 性能测试
        await tester.performance_test()

        # 打印测试摘要
        tester.print_test_summary()

        print("\n✅ 所有测试完成")

    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())