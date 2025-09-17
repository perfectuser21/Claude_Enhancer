#!/usr/bin/env python3
"""
Git缓存快速验证测试
验证关键修复点
"""

import asyncio
import threading
import time
from pathlib import Path
from infrastructure.git.git_cache import get_git_cache, get_cache_manager, CircuitState

async def test_double_checked_locking():
    """测试双重检查锁定"""
    print("🔒 测试双重检查锁定...")

    cache = get_git_cache(cache_ttl=2)  # 短TTL

    # 并发获取状态
    async def worker(worker_id):
        try:
            status = await cache.get_git_status()
            return f"Worker{worker_id}: {status.current_branch} (fallback: {status.is_fallback})"
        except Exception as e:
            return f"Worker{worker_id}: Error - {e}"

    # 启动5个并发任务
    tasks = [worker(i) for i in range(5)]
    results = await asyncio.gather(*tasks)

    for result in results:
        print(f"  {result}")

    cache_info = cache.get_cache_info()
    print(f"  缓存命中: {cache_info['performance_metrics']['cache_hits']}")
    print(f"  缓存失效: {cache_info['performance_metrics']['cache_misses']}")
    print("  ✅ 双重检查锁定测试完成")

def test_thread_safety():
    """测试线程安全"""
    print("🧵 测试线程安全...")

    manager = get_cache_manager()
    cache_instances = []

    def get_cache_instance(thread_id):
        cache = manager.get_cache(str(Path.cwd()), cache_ttl=30)
        cache_instances.append(id(cache))
        print(f"  线程{thread_id}: 获取缓存实例 {id(cache)}")

    # 创建多个线程同时获取缓存实例
    threads = []
    for i in range(5):
        thread = threading.Thread(target=get_cache_instance, args=(i,))
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    # 检查是否都是同一个实例
    unique_instances = set(cache_instances)
    print(f"  唯一实例数: {len(unique_instances)} (期望: 1)")
    print(f"  单例模式: {'✅' if len(unique_instances) == 1 else '❌'}")

async def test_circuit_breaker():
    """测试Circuit Breaker"""
    print("⚡ 测试Circuit Breaker...")

    from infrastructure.git.git_cache import GitCache

    # 使用无效路径触发失败
    cache = GitCache("/nonexistent/path", cache_ttl=1)
    cache.circuit_breaker.config.failure_threshold = 2

    # 触发失败
    for i in range(3):
        try:
            await cache.get_git_status()
        except Exception:
            print(f"  请求{i+1}: 预期失败")

    # 检查状态
    cb_state = cache.circuit_breaker.state
    print(f"  Circuit Breaker状态: {cb_state.value}")

    if cb_state == CircuitState.OPEN:
        print("  ✅ Circuit Breaker正确开启")
    else:
        print(f"  ⚠️ Circuit Breaker状态: {cb_state.value}")

async def test_fallback():
    """测试Fallback机制"""
    print("🔄 测试Fallback机制...")

    cache = get_git_cache()

    # 先获取正常数据建立fallback
    try:
        normal_status = await cache.get_git_status()
        print(f"  正常状态: {normal_status.current_branch}")

        # 人为触发错误
        original_path = cache.project_root
        cache.project_root = Path("/invalid")

        fallback_status = await cache.get_git_status()
        print(f"  Fallback状态: {fallback_status.current_branch} (是fallback: {fallback_status.is_fallback})")

        # 恢复
        cache.project_root = original_path

        if fallback_status.is_fallback:
            print("  ✅ Fallback机制正常工作")
        else:
            print("  ❌ Fallback机制未触发")

    except Exception as e:
        print(f"  ⚠️ Fallback测试异常: {e}")

async def main():
    """主测试函数"""
    print("🚀 Git缓存快速验证测试")
    print("="*40)

    try:
        await test_double_checked_locking()
        print()

        test_thread_safety()
        print()

        await test_circuit_breaker()
        print()

        await test_fallback()
        print()

        print("✅ 快速验证测试完成")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())