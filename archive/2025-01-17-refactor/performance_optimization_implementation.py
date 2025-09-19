#!/usr/bin/env python3
"""
Perfect21 性能优化实现
基于性能分析结果，实现具体的性能优化方案
"""

import os
import sys
import time
import json
import asyncio
import threading
import functools
import weakref
from typing import Dict, List, Any, Optional, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import OrderedDict, defaultdict
from pathlib import Path
import logging
import pickle
import hashlib

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__)))

from modules.logger import log_info, log_error, log_warning

logger = logging.getLogger(__name__)

T = TypeVar('T')

# ============================== 缓存优化 ==============================

class LRUCache(Generic[T]):
    """高性能LRU缓存实现"""

    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.access_times: Dict[str, float] = {}
        self.hit_count = 0
        self.miss_count = 0
        self._lock = threading.RLock()

    def _generate_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()

    def _is_expired(self, key: str) -> bool:
        """检查是否过期"""
        if key not in self.access_times:
            return True
        return time.time() - self.access_times[key] > self.ttl

    def get(self, key: str) -> Optional[T]:
        """获取缓存值"""
        with self._lock:
            if key in self.cache and not self._is_expired(key):
                # 移动到末尾（最近使用）
                value = self.cache.pop(key)
                self.cache[key] = value
                self.access_times[key] = time.time()
                self.hit_count += 1
                return value['data']

            self.miss_count += 1
            return None

    def put(self, key: str, value: T) -> None:
        """存储缓存值"""
        with self._lock:
            if key in self.cache:
                self.cache.pop(key)
            elif len(self.cache) >= self.max_size:
                # 移除最老的项
                oldest_key = next(iter(self.cache))
                self.cache.pop(oldest_key)
                self.access_times.pop(oldest_key, None)

            self.cache[key] = {'data': value, 'timestamp': time.time()}
            self.access_times[key] = time.time()

    def clear(self) -> None:
        """清空缓存"""
        with self._lock:
            self.cache.clear()
            self.access_times.clear()

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0

        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': f"{hit_rate:.1f}%",
            'utilization': f"{len(self.cache) / self.max_size * 100:.1f}%"
        }

def cached(max_size: int = 1000, ttl: int = 3600):
    """缓存装饰器"""
    def decorator(func: Callable) -> Callable:
        cache = LRUCache(max_size=max_size, ttl=ttl)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = cache._generate_key(*args, **kwargs)

            # 尝试从缓存获取
            result = cache.get(cache_key)
            if result is not None:
                return result

            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache.put(cache_key, result)
            return result

        # 添加缓存管理方法
        wrapper.cache = cache
        wrapper.clear_cache = cache.clear
        wrapper.cache_stats = cache.get_stats

        return wrapper

    return decorator

# ============================== 工作流缓存优化 ==============================

class WorkflowTemplateCache:
    """工作流模板缓存"""

    def __init__(self, cache_dir: str = ".perfect21/workflow_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.memory_cache = LRUCache(max_size=100, ttl=1800)  # 30分钟
        self.template_signatures: Dict[str, str] = {}

        # 加载已有的模板签名
        self._load_template_signatures()

    def _load_template_signatures(self):
        """加载模板签名"""
        signatures_file = self.cache_dir / "signatures.json"
        if signatures_file.exists():
            try:
                with open(signatures_file, 'r') as f:
                    self.template_signatures = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load template signatures: {e}")

    def _save_template_signatures(self):
        """保存模板签名"""
        signatures_file = self.cache_dir / "signatures.json"
        try:
            with open(signatures_file, 'w') as f:
                json.dump(self.template_signatures, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save template signatures: {e}")

    def _generate_signature(self, workflow_config: Dict[str, Any]) -> str:
        """生成工作流签名"""
        config_str = json.dumps(workflow_config, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()

    def get_workflow_template(self, workflow_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """获取缓存的工作流模板"""
        signature = self._generate_signature(workflow_config)

        # 先从内存缓存获取
        cached_template = self.memory_cache.get(signature)
        if cached_template:
            return cached_template

        # 从磁盘缓存获取
        cache_file = self.cache_dir / f"{signature}.pickle"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    template = pickle.load(f)

                # 加载到内存缓存
                self.memory_cache.put(signature, template)
                return template

            except Exception as e:
                logger.error(f"Failed to load cached workflow template: {e}")

        return None

    def cache_workflow_template(self, workflow_config: Dict[str, Any],
                              processed_template: Dict[str, Any]):
        """缓存工作流模板"""
        signature = self._generate_signature(workflow_config)

        # 存储到内存缓存
        self.memory_cache.put(signature, processed_template)

        # 存储到磁盘缓存
        cache_file = self.cache_dir / f"{signature}.pickle"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(processed_template, f)

            # 更新签名记录
            self.template_signatures[signature] = {
                'created_at': datetime.now().isoformat(),
                'workflow_name': workflow_config.get('name', 'Unknown')
            }
            self._save_template_signatures()

        except Exception as e:
            logger.error(f"Failed to cache workflow template: {e}")

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        memory_stats = self.memory_cache.get_stats()

        disk_cache_size = 0
        disk_file_count = 0
        for cache_file in self.cache_dir.glob("*.pickle"):
            disk_cache_size += cache_file.stat().st_size
            disk_file_count += 1

        return {
            'memory_cache': memory_stats,
            'disk_cache': {
                'file_count': disk_file_count,
                'total_size_mb': disk_cache_size / 1024 / 1024,
                'templates_cached': len(self.template_signatures)
            }
        }

# ============================== 并行处理优化 ==============================

class SmartThreadPool:
    """智能线程池"""

    def __init__(self, min_workers: int = 2, max_workers: int = 8,
                 scale_threshold: float = 0.8):
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.scale_threshold = scale_threshold

        self.current_workers = min_workers
        self.task_queue = asyncio.Queue()
        self.workers: List[asyncio.Task] = []
        self.active_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0

        self._lock = asyncio.Lock()
        self._shutdown = False
        self._monitoring_task: Optional[asyncio.Task] = None

    async def start(self):
        """启动线程池"""
        # 创建初始工作线程
        for i in range(self.min_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)

        # 启动监控任务
        self._monitoring_task = asyncio.create_task(self._monitor_load())

        log_info(f"SmartThreadPool started with {self.min_workers} workers")

    async def submit(self, func: Callable, *args, **kwargs) -> Any:
        """提交任务"""
        future = asyncio.Future()
        task_item = {
            'func': func,
            'args': args,
            'kwargs': kwargs,
            'future': future,
            'submitted_at': time.time()
        }

        await self.task_queue.put(task_item)
        self.active_tasks += 1

        return await future

    async def _worker(self, worker_name: str):
        """工作线程"""
        while not self._shutdown:
            try:
                # 获取任务（带超时）
                task_item = await asyncio.wait_for(
                    self.task_queue.get(),
                    timeout=1.0
                )

                func = task_item['func']
                args = task_item['args']
                kwargs = task_item['kwargs']
                future = task_item['future']

                try:
                    # 执行任务
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)

                    future.set_result(result)
                    self.completed_tasks += 1

                except Exception as e:
                    future.set_exception(e)
                    self.failed_tasks += 1

                finally:
                    self.active_tasks -= 1
                    self.task_queue.task_done()

            except asyncio.TimeoutError:
                # 超时，继续循环
                continue
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")

    async def _monitor_load(self):
        """监控负载并动态调整工作线程数"""
        while not self._shutdown:
            try:
                await asyncio.sleep(5)  # 每5秒检查一次

                queue_size = self.task_queue.qsize()
                worker_count = len(self.workers)

                # 计算负载
                load_ratio = queue_size / worker_count if worker_count > 0 else 0

                async with self._lock:
                    if load_ratio > self.scale_threshold and worker_count < self.max_workers:
                        # 增加工作线程
                        new_worker_id = len(self.workers)
                        worker = asyncio.create_task(self._worker(f"worker-{new_worker_id}"))
                        self.workers.append(worker)
                        log_info(f"Scaled up to {len(self.workers)} workers (load: {load_ratio:.2f})")

                    elif load_ratio < 0.2 and worker_count > self.min_workers:
                        # 减少工作线程
                        if self.workers:
                            worker = self.workers.pop()
                            worker.cancel()
                            log_info(f"Scaled down to {len(self.workers)} workers (load: {load_ratio:.2f})")

            except Exception as e:
                logger.error(f"Load monitoring error: {e}")

    async def shutdown(self):
        """关闭线程池"""
        self._shutdown = True

        # 等待所有任务完成
        await self.task_queue.join()

        # 取消所有工作线程
        for worker in self.workers:
            worker.cancel()

        # 取消监控任务
        if self._monitoring_task:
            self._monitoring_task.cancel()

        log_info("SmartThreadPool shutdown completed")

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'current_workers': len(self.workers),
            'min_workers': self.min_workers,
            'max_workers': self.max_workers,
            'active_tasks': self.active_tasks,
            'completed_tasks': self.completed_tasks,
            'failed_tasks': self.failed_tasks,
            'queue_size': self.task_queue.qsize(),
            'success_rate': (
                self.completed_tasks / (self.completed_tasks + self.failed_tasks) * 100
                if (self.completed_tasks + self.failed_tasks) > 0 else 100
            )
        }

# ============================== 内存优化 ==============================

class MemoryManager:
    """内存管理器"""

    def __init__(self, max_memory_mb: int = 512, cleanup_threshold: float = 0.8):
        self.max_memory_mb = max_memory_mb
        self.cleanup_threshold = cleanup_threshold

        self.object_pools: Dict[str, List[Any]] = defaultdict(list)
        self.weak_references: weakref.WeakValueDictionary = weakref.WeakValueDictionary()

        self._cleanup_interval = 60  # 60秒
        self._cleanup_task: Optional[asyncio.Task] = None
        self._memory_stats = {
            'allocations': 0,
            'deallocations': 0,
            'pool_hits': 0,
            'pool_misses': 0
        }

    def start_monitoring(self):
        """开始内存监控"""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        log_info("Memory manager started")

    async def _cleanup_loop(self):
        """清理循环"""
        import psutil

        while True:
            try:
                await asyncio.sleep(self._cleanup_interval)

                # 检查内存使用
                process = psutil.Process()
                memory_mb = process.memory_info().rss / 1024 / 1024

                if memory_mb > self.max_memory_mb * self.cleanup_threshold:
                    await self._perform_cleanup()
                    log_info(f"Memory cleanup performed, usage: {memory_mb:.1f}MB")

            except Exception as e:
                logger.error(f"Memory cleanup error: {e}")

    async def _perform_cleanup(self):
        """执行内存清理"""
        import gc

        # 清理对象池
        for pool_name, pool in self.object_pools.items():
            if len(pool) > 10:  # 保留最多10个对象
                pool[:] = pool[-10:]

        # 强制垃圾回收
        collected = gc.collect()
        log_info(f"Garbage collection freed {collected} objects")

        # 清理弱引用
        expired_refs = []
        for key, ref in self.weak_references.items():
            if ref is None:
                expired_refs.append(key)

        for key in expired_refs:
            del self.weak_references[key]

    def get_object(self, object_type: str, factory: Callable = None):
        """从对象池获取对象"""
        pool = self.object_pools[object_type]

        if pool:
            obj = pool.pop()
            self._memory_stats['pool_hits'] += 1
            return obj

        # 池中没有对象，创建新的
        if factory:
            obj = factory()
            self._memory_stats['pool_misses'] += 1
            self._memory_stats['allocations'] += 1
            return obj

        return None

    def return_object(self, object_type: str, obj: Any):
        """归还对象到池中"""
        pool = self.object_pools[object_type]

        # 重置对象状态（如果有reset方法）
        if hasattr(obj, 'reset'):
            obj.reset()

        pool.append(obj)
        self._memory_stats['deallocations'] += 1

    def register_weak_reference(self, key: str, obj: Any):
        """注册弱引用"""
        self.weak_references[key] = obj

    def get_stats(self) -> Dict[str, Any]:
        """获取内存统计"""
        import psutil

        process = psutil.Process()
        memory_info = process.memory_info()

        return {
            'current_memory_mb': memory_info.rss / 1024 / 1024,
            'max_memory_mb': self.max_memory_mb,
            'pool_stats': {
                pool_name: len(pool)
                for pool_name, pool in self.object_pools.items()
            },
            'allocation_stats': self._memory_stats,
            'weak_references': len(self.weak_references)
        }

# ============================== I/O优化 ==============================

class AsyncFileManager:
    """异步文件管理器"""

    def __init__(self, max_concurrent_ops: int = 20):
        self.max_concurrent_ops = max_concurrent_ops
        self.semaphore = asyncio.Semaphore(max_concurrent_ops)
        self.operation_stats = {
            'reads': 0,
            'writes': 0,
            'errors': 0,
            'total_bytes': 0
        }

    async def read_file(self, file_path: Path, encoding: str = 'utf-8') -> str:
        """异步读取文件"""
        async with self.semaphore:
            try:
                # 在线程池中执行I/O操作
                loop = asyncio.get_event_loop()

                def _read_sync():
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                        self.operation_stats['total_bytes'] += len(content.encode())
                        return content

                content = await loop.run_in_executor(None, _read_sync)
                self.operation_stats['reads'] += 1
                return content

            except Exception as e:
                self.operation_stats['errors'] += 1
                raise e

    async def write_file(self, file_path: Path, content: str,
                        encoding: str = 'utf-8', create_dirs: bool = True) -> None:
        """异步写入文件"""
        async with self.semaphore:
            try:
                # 在线程池中执行I/O操作
                loop = asyncio.get_event_loop()

                def _write_sync():
                    if create_dirs:
                        file_path.parent.mkdir(parents=True, exist_ok=True)

                    with open(file_path, 'w', encoding=encoding) as f:
                        f.write(content)
                        self.operation_stats['total_bytes'] += len(content.encode())

                await loop.run_in_executor(None, _write_sync)
                self.operation_stats['writes'] += 1

            except Exception as e:
                self.operation_stats['errors'] += 1
                raise e

    async def batch_read(self, file_paths: List[Path]) -> Dict[Path, str]:
        """批量读取文件"""
        tasks = [self.read_file(path) for path in file_paths]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            path: result for path, result in zip(file_paths, results)
            if not isinstance(result, Exception)
        }

    async def batch_write(self, file_data: Dict[Path, str]) -> None:
        """批量写入文件"""
        tasks = [
            self.write_file(path, content)
            for path, content in file_data.items()
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    def get_stats(self) -> Dict[str, Any]:
        """获取I/O统计"""
        total_ops = self.operation_stats['reads'] + self.operation_stats['writes']
        error_rate = (
            self.operation_stats['errors'] / total_ops * 100
            if total_ops > 0 else 0
        )

        return {
            'operations': self.operation_stats,
            'error_rate': f"{error_rate:.2f}%",
            'avg_bytes_per_op': (
                self.operation_stats['total_bytes'] / total_ops
                if total_ops > 0 else 0
            )
        }

# ============================== 正则表达式优化 ==============================

class RegexOptimizer:
    """正则表达式优化器"""

    def __init__(self, cache_size: int = 1000):
        self.compiled_patterns = LRUCache(max_size=cache_size, ttl=7200)  # 2小时
        self.pattern_stats = defaultdict(lambda: {'uses': 0, 'total_time': 0.0})

    def compile_pattern(self, pattern: str, flags: int = 0):
        """编译并缓存正则表达式"""
        import re

        cache_key = f"{pattern}:{flags}"

        # 从缓存获取
        compiled = self.compiled_patterns.get(cache_key)
        if compiled:
            return compiled

        # 编译并缓存
        start_time = time.perf_counter()
        compiled = re.compile(pattern, flags)
        compile_time = time.perf_counter() - start_time

        self.compiled_patterns.put(cache_key, compiled)

        # 更新统计
        stats = self.pattern_stats[pattern]
        stats['uses'] += 1
        stats['total_time'] += compile_time

        return compiled

    def find_all_optimized(self, pattern: str, text: str, flags: int = 0) -> List[str]:
        """优化的findall操作"""
        compiled_pattern = self.compile_pattern(pattern, flags)

        start_time = time.perf_counter()
        matches = compiled_pattern.findall(text)
        search_time = time.perf_counter() - start_time

        # 更新统计
        stats = self.pattern_stats[pattern]
        stats['total_time'] += search_time

        return matches

    def get_pattern_stats(self) -> Dict[str, Any]:
        """获取模式统计"""
        return {
            'cache_stats': self.compiled_patterns.get_stats(),
            'pattern_usage': dict(self.pattern_stats),
            'top_patterns': sorted(
                self.pattern_stats.items(),
                key=lambda x: x[1]['uses'],
                reverse=True
            )[:10]
        }

# ============================== 性能优化管理器 ==============================

class PerformanceOptimizationManager:
    """性能优化管理器"""

    def __init__(self):
        self.workflow_cache = WorkflowTemplateCache()
        self.thread_pool = SmartThreadPool()
        self.memory_manager = MemoryManager()
        self.file_manager = AsyncFileManager()
        self.regex_optimizer = RegexOptimizer()

        self.optimization_stats = {
            'workflow_cache_hits': 0,
            'workflow_cache_misses': 0,
            'parallel_tasks_executed': 0,
            'memory_cleanups': 0,
            'file_operations': 0,
            'regex_optimizations': 0
        }

        self._initialized = False

    async def initialize(self):
        """初始化性能优化"""
        if self._initialized:
            return

        try:
            # 启动线程池
            await self.thread_pool.start()

            # 启动内存管理
            self.memory_manager.start_monitoring()

            self._initialized = True
            log_info("Performance optimization manager initialized")

        except Exception as e:
            log_error(f"Failed to initialize performance optimization: {e}")
            raise

    async def shutdown(self):
        """关闭性能优化"""
        if not self._initialized:
            return

        try:
            await self.thread_pool.shutdown()
            self._initialized = False
            log_info("Performance optimization manager shutdown")

        except Exception as e:
            log_error(f"Failed to shutdown performance optimization: {e}")

    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """获取综合性能统计"""
        return {
            'workflow_cache': self.workflow_cache.get_cache_stats(),
            'thread_pool': self.thread_pool.get_stats(),
            'memory_manager': self.memory_manager.get_stats(),
            'file_manager': self.file_manager.get_stats(),
            'regex_optimizer': self.regex_optimizer.get_pattern_stats(),
            'optimization_stats': self.optimization_stats
        }

    def generate_optimization_report(self) -> Dict[str, Any]:
        """生成优化报告"""
        stats = self.get_comprehensive_stats()

        # 计算改进指标
        improvements = {}

        # 工作流缓存改进
        workflow_cache_stats = stats['workflow_cache']['memory_cache']
        if 'hit_rate' in workflow_cache_stats:
            hit_rate = float(workflow_cache_stats['hit_rate'].rstrip('%'))
            improvements['workflow_loading'] = f"{hit_rate:.1f}% cache hit rate"

        # 线程池效率
        thread_stats = stats['thread_pool']
        if 'success_rate' in thread_stats:
            improvements['parallel_execution'] = f"{thread_stats['success_rate']:.1f}% success rate"

        # 内存使用优化
        memory_stats = stats['memory_manager']
        pool_efficiency = sum(memory_stats['pool_stats'].values())
        if pool_efficiency > 0:
            improvements['memory_usage'] = f"{pool_efficiency} objects pooled"

        return {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'optimized',
            'active_optimizations': len([k for k, v in improvements.items() if v]),
            'improvements': improvements,
            'detailed_stats': stats,
            'recommendations': self._generate_further_optimizations(stats)
        }

    def _generate_further_optimizations(self, stats: Dict[str, Any]) -> List[str]:
        """生成进一步的优化建议"""
        recommendations = []

        # 分析缓存命中率
        workflow_hit_rate = float(
            stats['workflow_cache']['memory_cache'].get('hit_rate', '0%').rstrip('%')
        )
        if workflow_hit_rate < 80:
            recommendations.append("增加工作流缓存大小以提高命中率")

        # 分析线程池使用
        thread_stats = stats['thread_pool']
        if thread_stats['current_workers'] == thread_stats['max_workers']:
            recommendations.append("考虑增加最大工作线程数")

        # 分析内存使用
        memory_stats = stats['memory_manager']
        if memory_stats['current_memory_mb'] > memory_stats['max_memory_mb'] * 0.9:
            recommendations.append("增加内存限制或优化内存使用")

        # 分析I/O操作
        io_stats = stats['file_manager']
        error_rate = float(io_stats.get('error_rate', '0%').rstrip('%'))
        if error_rate > 1:
            recommendations.append("检查文件操作错误原因并优化")

        return recommendations

# ============================== 全局实例 ==============================

# 创建全局性能优化管理器实例
performance_manager = PerformanceOptimizationManager()

# 便捷函数
async def initialize_performance_optimizations():
    """初始化性能优化"""
    await performance_manager.initialize()

async def shutdown_performance_optimizations():
    """关闭性能优化"""
    await performance_manager.shutdown()

def get_performance_stats():
    """获取性能统计"""
    return performance_manager.get_comprehensive_stats()

def get_optimization_report():
    """获取优化报告"""
    return performance_manager.generate_optimization_report()

# 导出优化后的装饰器和工具
__all__ = [
    'cached',
    'LRUCache',
    'WorkflowTemplateCache',
    'SmartThreadPool',
    'MemoryManager',
    'AsyncFileManager',
    'RegexOptimizer',
    'PerformanceOptimizationManager',
    'performance_manager',
    'initialize_performance_optimizations',
    'shutdown_performance_optimizations',
    'get_performance_stats',
    'get_optimization_report'
]

if __name__ == "__main__":
    import asyncio

    async def demo():
        """演示性能优化功能"""
        print("🚀 Perfect21 性能优化演示")
        print("=" * 40)

        # 初始化性能优化
        await initialize_performance_optimizations()

        # 演示缓存功能
        @cached(max_size=100, ttl=60)
        def expensive_calculation(n):
            return sum(i * i for i in range(n))

        # 测试缓存
        start_time = time.perf_counter()
        result1 = expensive_calculation(10000)
        first_call_time = time.perf_counter() - start_time

        start_time = time.perf_counter()
        result2 = expensive_calculation(10000)  # 应该从缓存获取
        second_call_time = time.perf_counter() - start_time

        print(f"首次调用: {first_call_time:.4f}s")
        print(f"缓存调用: {second_call_time:.4f}s")
        print(f"加速比: {first_call_time / second_call_time:.1f}x")

        # 获取性能统计
        stats = get_performance_stats()
        print(f"\n📊 性能统计:")
        print(f"  线程池: {stats['thread_pool']['current_workers']} 工作线程")
        print(f"  内存使用: {stats['memory_manager']['current_memory_mb']:.1f}MB")

        # 生成优化报告
        report = get_optimization_report()
        print(f"\n📈 优化报告:")
        print(f"  状态: {report['overall_status']}")
        print(f"  活跃优化: {report['active_optimizations']} 项")

        # 关闭性能优化
        await shutdown_performance_optimizations()

        print("\n✅ 演示完成")

    asyncio.run(demo())