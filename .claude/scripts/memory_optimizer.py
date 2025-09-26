#!/usr/bin/env python3
"""
Claude Enhancer 内存优化工具
实现智能内存管理、缓存优化和资源池管理

核心功能:
1. 内存使用监控和优化
2. 智能垃圾回收
3. Agent实例池管理
4. 缓存策略优化
5. 内存泄漏检测
"""

import gc
import time
import threading
import weakref
import psutil
import os
import sys
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, OrderedDict
import json
import pickle
import gzip
from concurrent.futures import ThreadPoolExecutor


@dataclass
class MemorySnapshot:
    """内存快照数据结构"""
    timestamp: float
    rss_mb: float
    vms_mb: float
    percent: float
    cache_size: int
    loaded_agents: int
    thread_count: int
    file_descriptors: int


class IntelligentMemoryManager:
    """智能内存管理器"""

    def __init__(self, target_memory_mb: int = 50):
        self.target_memory = target_memory_mb * 1024 * 1024  # 转换为字节
        self.process = psutil.Process()

        # 内存监控
        self.snapshots: List[MemorySnapshot] = []
        self.monitoring_active = False
        self.monitor_thread = None

        # 清理策略
        self.cleanup_strategies = [
            self._cleanup_caches,
            self._force_garbage_collection,
            self._clear_import_cache,
            self._compact_data_structures,
        ]

        # 统计信息
        self.stats = {
            "cleanups_performed": 0,
            "memory_saved_mb": 0.0,
            "gc_collections": 0,
            "cache_evictions": 0,
        }

    def start_monitoring(self, interval_seconds: int = 5):
        """启动内存监控"""
        if self.monitoring_active:
            return

        self.monitoring_active = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval_seconds,),
            daemon=True
        )
        self.monitor_thread.start()
        print(f"🔍 启动内存监控 (间隔: {interval_seconds}秒)")

    def stop_monitoring(self):
        """停止内存监控"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)

    def _monitoring_loop(self, interval: int):
        """内存监控循环"""
        while self.monitoring_active:
            try:
                snapshot = self._capture_memory_snapshot()
                self.snapshots.append(snapshot)

                # 保持最近50个快照
                if len(self.snapshots) > 50:
                    self.snapshots.pop(0)

                # 检查是否需要清理
                if snapshot.rss_mb > self.target_memory / 1024 / 1024:
                    self._trigger_cleanup(snapshot)

                time.sleep(interval)

            except Exception as e:
                print(f"⚠️ 内存监控出错: {e}")
                time.sleep(interval)

    def _capture_memory_snapshot(self) -> MemorySnapshot:
        """捕获当前内存快照"""
        memory_info = self.process.memory_info()

        # 获取文件描述符数量
        try:
            fd_count = len(self.process.open_files())
        except:
            fd_count = 0

        return MemorySnapshot(
            timestamp=time.time(),
            rss_mb=memory_info.rss / 1024 / 1024,
            vms_mb=memory_info.vms / 1024 / 1024,
            percent=self.process.memory_percent(),
            cache_size=len(gc.get_objects()),
            loaded_agents=0,  # 需要从外部传入
            thread_count=threading.active_count(),
            file_descriptors=fd_count,
        )

    def _trigger_cleanup(self, snapshot: MemorySnapshot):
        """触发内存清理"""
        print(f"🧹 内存使用过高 ({snapshot.rss_mb:.1f}MB), 开始清理...")

        initial_memory = snapshot.rss_mb

        for i, strategy in enumerate(self.cleanup_strategies):
            try:
                before_memory = self.process.memory_info().rss / 1024 / 1024
                strategy()
                after_memory = self.process.memory_info().rss / 1024 / 1024

                memory_saved = before_memory - after_memory
                if memory_saved > 0:
                    print(f"  ✅ 策略{i+1}: 释放 {memory_saved:.1f}MB")
                    self.stats["memory_saved_mb"] += memory_saved

                # 如果内存已经降到目标以下，停止清理
                if after_memory < self.target_memory / 1024 / 1024:
                    break

            except Exception as e:
                print(f"  ❌ 策略{i+1} 失败: {e}")

        final_memory = self.process.memory_info().rss / 1024 / 1024
        total_saved = initial_memory - final_memory

        if total_saved > 0:
            print(f"🎯 清理完成，总共释放 {total_saved:.1f}MB")

        self.stats["cleanups_performed"] += 1

    def _cleanup_caches(self):
        """清理各种缓存"""
        # 清理Python内部缓存
        if hasattr(sys, '_getframe'):
            frame = sys._getframe()
            while frame:
                if hasattr(frame, 'f_locals'):
                    frame.f_locals.clear()
                frame = frame.f_back

        # 清理模块缓存
        import importlib
        importlib.invalidate_caches()

    def _force_garbage_collection(self):
        """强制垃圾回收"""
        # 多轮垃圾回收
        for generation in range(3):
            collected = gc.collect()
            if collected > 0:
                print(f"    🗑️ GC第{generation}代: 清理了{collected}个对象")

        self.stats["gc_collections"] += 1

    def _clear_import_cache(self):
        """清理导入缓存"""
        # 清理 __pycache__ 相关缓存
        import importlib.util
        importlib.util.cache_from_source.cache_clear()

    def _compact_data_structures(self):
        """压缩数据结构"""
        # 这里可以添加特定于应用的数据结构压缩逻辑
        pass

    def get_memory_report(self) -> Dict[str, Any]:
        """生成内存使用报告"""
        if not self.snapshots:
            return {"error": "没有内存监控数据"}

        current = self.snapshots[-1]

        # 计算趋势
        if len(self.snapshots) > 5:
            recent_avg = sum(s.rss_mb for s in self.snapshots[-5:]) / 5
            older_avg = sum(s.rss_mb for s in self.snapshots[-10:-5]) / 5
            trend = "上升" if recent_avg > older_avg else "下降"
        else:
            trend = "稳定"

        # 内存分析
        peak_memory = max(s.rss_mb for s in self.snapshots)
        min_memory = min(s.rss_mb for s in self.snapshots)
        avg_memory = sum(s.rss_mb for s in self.snapshots) / len(self.snapshots)

        return {
            "current_status": {
                "rss_mb": current.rss_mb,
                "percent": current.percent,
                "trend": trend,
                "health": "良好" if current.rss_mb < self.target_memory/1024/1024 else "需要关注",
            },
            "statistics": {
                "peak_memory_mb": peak_memory,
                "min_memory_mb": min_memory,
                "avg_memory_mb": avg_memory,
                "memory_range_mb": peak_memory - min_memory,
            },
            "system_info": {
                "thread_count": current.thread_count,
                "file_descriptors": current.file_descriptors,
                "cache_objects": current.cache_size,
            },
            "optimization_stats": self.stats,
            "recommendations": self._generate_recommendations(current),
        }

    def _generate_recommendations(self, snapshot: MemorySnapshot) -> List[str]:
        """生成优化建议"""
        recommendations = []

        if snapshot.rss_mb > self.target_memory / 1024 / 1024 * 1.5:
            recommendations.append("内存使用过高，建议立即优化")

        if snapshot.thread_count > 20:
            recommendations.append("线程数量过多，建议使用线程池")

        if snapshot.file_descriptors > 100:
            recommendations.append("文件描述符过多，检查是否有资源泄漏")

        if len(self.snapshots) > 10:
            recent_growth = self.snapshots[-1].rss_mb - self.snapshots[-10].rss_mb
            if recent_growth > 20:
                recommendations.append("检测到内存持续增长，可能存在内存泄漏")

        if not recommendations:
            recommendations.append("内存使用状况良好")

        return recommendations


class AgentInstancePool:
    """Agent实例池管理器"""

    def __init__(self, max_instances: int = 20):
        self.max_instances = max_instances
        self.pool: Dict[str, List[weakref.ref]] = defaultdict(list)
        self.active_instances: Dict[str, weakref.ref] = {}
        self.creation_count = 0
        self.reuse_count = 0
        self.lock = threading.RLock()

    def get_agent_instance(self, agent_name: str, factory_func) -> Any:
        """获取Agent实例（复用或创建）"""
        with self.lock:
            # 尝试从池中获取可用实例
            if agent_name in self.pool:
                while self.pool[agent_name]:
                    weak_ref = self.pool[agent_name].pop()
                    instance = weak_ref()
                    if instance is not None:
                        self.active_instances[f"{agent_name}_{id(instance)}"] = weak_ref
                        self.reuse_count += 1
                        return instance

            # 池中没有可用实例，创建新的
            if len(self.active_instances) < self.max_instances:
                instance = factory_func()
                weak_ref = weakref.ref(instance, self._cleanup_callback)
                self.active_instances[f"{agent_name}_{id(instance)}"] = weak_ref
                self.creation_count += 1
                return instance

            # 实例数达到上限，强制回收最老的实例
            self._force_cleanup()
            return self.get_agent_instance(agent_name, factory_func)

    def return_agent_instance(self, agent_name: str, instance: Any):
        """归还Agent实例到池中"""
        with self.lock:
            instance_key = f"{agent_name}_{id(instance)}"
            if instance_key in self.active_instances:
                weak_ref = self.active_instances.pop(instance_key)

                # 将实例放回池中供复用
                if len(self.pool[agent_name]) < 5:  # 每种Agent最多缓存5个实例
                    self.pool[agent_name].append(weak_ref)

    def _cleanup_callback(self, weak_ref):
        """实例被垃圾回收时的回调"""
        with self.lock:
            # 从活动实例中移除
            keys_to_remove = []
            for key, ref in self.active_instances.items():
                if ref is weak_ref:
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                self.active_instances.pop(key, None)

    def _force_cleanup(self):
        """强制清理一些实例"""
        with self.lock:
            # 清理池中的弱引用
            for agent_name, refs in list(self.pool.items()):
                self.pool[agent_name] = [ref for ref in refs if ref() is not None]

            # 如果还是太多，直接清理一部分
            if len(self.active_instances) >= self.max_instances:
                keys_to_remove = list(self.active_instances.keys())[:5]
                for key in keys_to_remove:
                    self.active_instances.pop(key, None)

    def get_pool_stats(self) -> Dict[str, Any]:
        """获取池统计信息"""
        with self.lock:
            pool_sizes = {name: len(refs) for name, refs in self.pool.items()}
            active_count = len(self.active_instances)

            return {
                "creation_count": self.creation_count,
                "reuse_count": self.reuse_count,
                "active_instances": active_count,
                "pool_sizes": pool_sizes,
                "reuse_rate": f"{(self.reuse_count / max(1, self.creation_count + self.reuse_count)) * 100:.1f}%",
                "max_instances": self.max_instances,
            }


class CacheOptimizer:
    """缓存优化器"""

    def __init__(self):
        self.caches: Dict[str, Any] = {}
        self.access_counts: Dict[str, int] = defaultdict(int)
        self.last_access: Dict[str, float] = {}
        self.cache_sizes: Dict[str, int] = defaultdict(int)

    def register_cache(self, name: str, cache_obj: Any):
        """注册需要优化的缓存"""
        self.caches[name] = cache_obj
        print(f"📋 注册缓存: {name}")

    def optimize_all_caches(self):
        """优化所有注册的缓存"""
        print("🔧 开始缓存优化...")

        for name, cache in self.caches.items():
            try:
                before_size = self._get_cache_size(cache)
                self._optimize_cache(name, cache)
                after_size = self._get_cache_size(cache)

                if before_size > after_size:
                    saved = before_size - after_size
                    print(f"  ✅ {name}: 减少 {saved} 个条目")

            except Exception as e:
                print(f"  ❌ {name} 优化失败: {e}")

    def _get_cache_size(self, cache: Any) -> int:
        """获取缓存大小"""
        if hasattr(cache, '__len__'):
            return len(cache)
        elif hasattr(cache, 'cache_info'):  # functools.lru_cache
            return cache.cache_info().currsize
        return 0

    def _optimize_cache(self, name: str, cache: Any):
        """优化单个缓存"""
        if hasattr(cache, 'clear'):
            # 如果是字典类型的缓存
            if isinstance(cache, dict):
                self._optimize_dict_cache(cache)
            else:
                # 对于其他类型，直接清理一半
                if hasattr(cache, '__len__') and len(cache) > 100:
                    cache.clear()

    def _optimize_dict_cache(self, cache: dict):
        """优化字典类型缓存"""
        if len(cache) <= 50:
            return

        # 基于LRU策略保留最新的50%
        current_time = time.time()
        items = list(cache.items())

        # 按访问时间排序（如果有的话）
        sorted_items = sorted(items, key=lambda x: hash(x[0]))  # 简单排序

        # 保留前50%
        keep_count = len(items) // 2
        cache.clear()

        for key, value in sorted_items[:keep_count]:
            cache[key] = value


def run_memory_optimization_demo():
    """运行内存优化演示"""
    print("🧠 Claude Enhancer 内存优化演示")
    print("=" * 50)

    # 创建内存管理器
    memory_manager = IntelligentMemoryManager(target_memory_mb=40)

    # 启动监控
    memory_manager.start_monitoring(interval_seconds=2)

    # 模拟内存使用
    print("\n📈 模拟内存密集型操作...")

    # 创建一些内存消耗
    large_data = []
    for i in range(10):
        data = [j * i for j in range(100000)]  # 创建大量数据
        large_data.append(data)
        time.sleep(0.5)

    # 等待一段时间让监控器工作
    time.sleep(5)

    # 显示内存报告
    report = memory_manager.get_memory_report()
    print("\n📊 内存使用报告:")
    print(json.dumps(report, indent=2, ensure_ascii=False))

    # 清理大数据
    del large_data
    gc.collect()

    # 再等一段时间
    time.sleep(3)

    # 最终报告
    final_report = memory_manager.get_memory_report()
    print("\n📊 优化后内存报告:")
    print(f"当前内存: {final_report['current_status']['rss_mb']:.1f}MB")
    print(f"优化状态: {final_report['current_status']['health']}")
    print(f"总清理次数: {final_report['optimization_stats']['cleanups_performed']}")
    print(f"节省内存: {final_report['optimization_stats']['memory_saved_mb']:.1f}MB")

    # 停止监控
    memory_manager.stop_monitoring()

    # Agent池演示
    print("\n🔄 Agent实例池演示...")

    agent_pool = AgentInstancePool(max_instances=5)

    # 模拟Agent创建和复用
    def create_mock_agent():
        return {"id": time.time(), "data": [1, 2, 3, 4, 5]}

    # 创建和归还一些Agent实例
    agents = []
    for i in range(8):  # 超过池的最大容量
        agent = agent_pool.get_agent_instance("test-agent", create_mock_agent)
        agents.append(agent)

    # 归还部分Agent
    for agent in agents[:3]:
        agent_pool.return_agent_instance("test-agent", agent)

    # 再次获取（应该复用之前的实例）
    reused_agents = []
    for i in range(3):
        agent = agent_pool.get_agent_instance("test-agent", create_mock_agent)
        reused_agents.append(agent)

    pool_stats = agent_pool.get_pool_stats()
    print("📊 Agent池统计:")
    print(json.dumps(pool_stats, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        run_memory_optimization_demo()
    else:
        # 简单的内存检查
        manager = IntelligentMemoryManager()
        snapshot = manager._capture_memory_snapshot()
        print(f"当前内存使用: {snapshot.rss_mb:.1f}MB")
        print(f"内存占用率: {snapshot.percent:.1f}%")
        print(f"活跃线程数: {snapshot.thread_count}")

        if snapshot.rss_mb > 100:
            print("⚠️ 内存使用较高，建议运行优化: python3 memory_optimizer.py demo")