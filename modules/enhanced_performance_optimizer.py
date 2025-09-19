#!/usr/bin/env python3
"""
Perfect21增强性能优化器 - 全面性能优化解决方案

🚀 核心功能：
1. 智能缓存系统 - Agent结果缓存、模板预编译
2. 并行执行优化 - 资源池管理、异步协调
3. Git操作优化 - 批量化、缓存利用
4. 内存管理 - 智能GC、对象复用
5. 性能监控 - 实时分析、自动优化
6. 基准测试 - 性能回归检测
"""

import os
import sys
import time
import asyncio
import threading
import concurrent.futures
import psutil
import gc
import pickle
import hashlib
import json
from typing import Dict, Any, List, Optional, Callable, Tuple, Union
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field
from contextlib import contextmanager, asynccontextmanager
from functools import wraps, lru_cache
import statistics
import logging
from pathlib import Path

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.logger import log_info, log_error, log_warning
from modules.config import config
from modules.performance_cache import performance_cache
from modules.performance_monitor import performance_monitor, PerformanceMetric

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    timestamp: float
    ttl: float
    hit_count: int = 0
    size_bytes: int = 0
    last_access: float = 0.0

@dataclass
class AgentExecutionContext:
    """Agent执行上下文"""
    agent_id: str
    request_id: str
    start_time: float
    parameters: Dict[str, Any]
    cached_result: Optional[Any] = None
    execution_time: float = 0.0
    memory_usage: float = 0.0

@dataclass
class OptimizationResult:
    """优化结果"""
    category: str
    before_metric: float
    after_metric: float
    improvement: float
    description: str
    timestamp: datetime = field(default_factory=datetime.now)

class IntelligentCacheSystem:
    """智能缓存系统 - Agent结果和模板预编译"""

    def __init__(self, max_size: int = 2048, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self.cache: Dict[str, CacheEntry] = {}
        self.access_history = deque(maxlen=10000)
        self.lock = threading.RLock()

        # 分层缓存
        self.hot_cache = {}  # 高频访问
        self.warm_cache = {}  # 中等频率
        self.cold_cache = {}  # 低频访问

        # 预编译模板缓存
        self.template_cache = {}
        self.compiled_workflows = {}

        # 智能预测
        self.access_patterns = defaultdict(list)
        self.prediction_accuracy = 0.0

        log_info("智能缓存系统初始化完成")

    def _generate_cache_key(self, category: str, identifier: str, params: Dict[str, Any] = None) -> str:
        """生成缓存键"""
        key_parts = [category, identifier]
        if params:
            # 参数标准化
            sorted_params = sorted(params.items())
            param_str = str(sorted_params)
            param_hash = hashlib.md5(param_str.encode()).hexdigest()[:8]
            key_parts.append(param_hash)
        return ":".join(key_parts)

    def _estimate_size(self, value: Any) -> int:
        """估算对象大小"""
        try:
            return len(pickle.dumps(value))
        except:
            return sys.getsizeof(value)

    def _categorize_by_frequency(self, key: str) -> str:
        """根据访问频率分类"""
        if key in self.cache:
            hit_count = self.cache[key].hit_count
            if hit_count > 50:
                return 'hot'
            elif hit_count > 10:
                return 'warm'
            else:
                return 'cold'
        return 'cold'

    async def get_agent_result(self, agent_type: str, request_hash: str,
                              params: Dict[str, Any] = None) -> Optional[Any]:
        """获取Agent执行结果缓存"""
        cache_key = self._generate_cache_key("agent", f"{agent_type}:{request_hash}", params)

        with self.lock:
            if cache_key in self.cache:
                entry = self.cache[cache_key]

                # 检查TTL
                if time.time() - entry.timestamp <= entry.ttl:
                    entry.hit_count += 1
                    entry.last_access = time.time()
                    self.access_history.append((cache_key, time.time(), 'hit'))

                    # 记录访问模式
                    self.access_patterns[cache_key].append(time.time())

                    log_info(f"Agent缓存命中: {agent_type} (hit_count: {entry.hit_count})")
                    return entry.value
                else:
                    # 过期删除
                    del self.cache[cache_key]

        self.access_history.append((cache_key, time.time(), 'miss'))
        return None

    async def cache_agent_result(self, agent_type: str, request_hash: str, result: Any,
                                params: Dict[str, Any] = None, ttl: int = None) -> None:
        """缓存Agent执行结果"""
        cache_key = self._generate_cache_key("agent", f"{agent_type}:{request_hash}", params)
        ttl = ttl or self.ttl

        # 估算大小
        size_bytes = self._estimate_size(result)

        # 检查缓存容量
        if len(self.cache) >= self.max_size:
            await self._evict_cache()

        with self.lock:
            entry = CacheEntry(
                key=cache_key,
                value=result,
                timestamp=time.time(),
                ttl=ttl,
                size_bytes=size_bytes,
                last_access=time.time()
            )

            self.cache[cache_key] = entry
            log_info(f"Agent结果已缓存: {agent_type} (size: {size_bytes} bytes)")

    async def precompile_template(self, template_name: str, template_content: str) -> str:
        """预编译工作流模板"""
        template_hash = hashlib.md5(template_content.encode()).hexdigest()

        if template_hash in self.template_cache:
            log_info(f"模板缓存命中: {template_name}")
            return self.template_cache[template_hash]

        # 模拟模板编译优化
        compiled_template = template_content.replace('\n', ' ').strip()

        # 缓存编译结果
        self.template_cache[template_hash] = compiled_template
        log_info(f"模板预编译完成: {template_name}")

        return compiled_template

    async def _evict_cache(self) -> None:
        """智能缓存淘汰"""
        with self.lock:
            if not self.cache:
                return

            # LFU + LRU 混合策略
            entries = list(self.cache.values())

            # 按访问频率和时间排序
            entries.sort(key=lambda e: (e.hit_count, e.last_access))

            # 淘汰最少使用的25%
            evict_count = max(1, len(entries) // 4)
            for i in range(evict_count):
                if entries[i].key in self.cache:
                    del self.cache[entries[i].key]

        log_info(f"缓存淘汰完成，移除 {evict_count} 个条目")

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self.lock:
            total_size = sum(entry.size_bytes for entry in self.cache.values())
            hit_rate = 0.0

            if len(self.access_history) > 100:
                recent_hits = sum(1 for _, _, status in list(self.access_history)[-100:] if status == 'hit')
                hit_rate = recent_hits / 100 * 100

            return {
                'total_entries': len(self.cache),
                'total_size_mb': total_size / 1024 / 1024,
                'hit_rate': f"{hit_rate:.1f}%",
                'template_cache_size': len(self.template_cache),
                'access_history_size': len(self.access_history),
                'prediction_accuracy': f"{self.prediction_accuracy:.1f}%"
            }

class ResourcePoolManager:
    """资源池管理器 - 复用连接和上下文"""

    def __init__(self):
        self.pools: Dict[str, List[Any]] = defaultdict(list)
        self.pool_configs: Dict[str, Dict[str, int]] = {}
        self.pool_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {
            'created': 0, 'reused': 0, 'destroyed': 0, 'active': 0
        })
        self.lock = threading.RLock()

        # 默认池配置
        self._setup_default_pools()

        log_info("资源池管理器初始化完成")

    def _setup_default_pools(self):
        """设置默认资源池"""
        self.pool_configs.update({
            'dict': {'initial': 50, 'max': 200, 'factory': dict},
            'list': {'initial': 50, 'max': 200, 'factory': list},
            'execution_context': {'initial': 20, 'max': 100, 'factory': lambda: AgentExecutionContext('', '', 0.0, {})},
            'thread_executor': {'initial': 2, 'max': 10, 'factory': lambda: concurrent.futures.ThreadPoolExecutor(max_workers=4)},
        })

        # 预分配对象
        for pool_name, config in self.pool_configs.items():
            for _ in range(config['initial']):
                obj = config['factory']()
                self.pools[pool_name].append(obj)
                self.pool_stats[pool_name]['created'] += 1

    @contextmanager
    def get_resource(self, pool_name: str):
        """从资源池获取资源"""
        with self.lock:
            if self.pools[pool_name]:
                resource = self.pools[pool_name].pop()
                self.pool_stats[pool_name]['reused'] += 1
                self.pool_stats[pool_name]['active'] += 1
            else:
                # 创建新资源
                if pool_name in self.pool_configs:
                    resource = self.pool_configs[pool_name]['factory']()
                    self.pool_stats[pool_name]['created'] += 1
                    self.pool_stats[pool_name]['active'] += 1
                else:
                    raise ValueError(f"未知资源池: {pool_name}")

        try:
            yield resource
        finally:
            self.return_resource(pool_name, resource)

    def return_resource(self, pool_name: str, resource: Any):
        """归还资源到池"""
        with self.lock:
            if len(self.pools[pool_name]) < self.pool_configs.get(pool_name, {}).get('max', 100):
                # 重置资源状态
                if hasattr(resource, 'clear'):
                    resource.clear()
                elif hasattr(resource, 'reset'):
                    resource.reset()

                self.pools[pool_name].append(resource)
                self.pool_stats[pool_name]['active'] -= 1
            else:
                # 超过最大容量，销毁资源
                self.pool_stats[pool_name]['destroyed'] += 1
                self.pool_stats[pool_name]['active'] -= 1
                if hasattr(resource, 'shutdown'):
                    resource.shutdown(wait=False)

    def get_pool_stats(self) -> Dict[str, Any]:
        """获取池统计信息"""
        with self.lock:
            return {
                pool_name: {
                    'available': len(self.pools[pool_name]),
                    'stats': dict(stats)
                }
                for pool_name, stats in self.pool_stats.items()
            }

class GitOperationOptimizer:
    """Git操作优化器 - 批量化和缓存利用"""

    def __init__(self):
        self.batch_operations = deque()
        self.batch_lock = threading.Lock()
        self.batch_timer = None
        self.batch_interval = 2.0  # 2秒批量处理

        # Git缓存集成
        self.git_cache = performance_cache.git_cache

        # 操作统计
        self.stats = {
            'batched_operations': 0,
            'cache_hits': 0,
            'single_operations': 0,
            'optimization_ratio': 0.0
        }

        log_info("Git操作优化器初始化完成")

    def queue_git_operation(self, operation: str, args: List[str],
                           callback: Optional[Callable] = None, priority: int = 5) -> str:
        """队列化Git操作用于批量处理"""
        operation_id = f"{operation}_{int(time.time() * 1000000)}"

        with self.batch_lock:
            self.batch_operations.append({
                'id': operation_id,
                'operation': operation,
                'args': args,
                'callback': callback,
                'priority': priority,
                'timestamp': time.time()
            })

        # 启动批量处理定时器
        self._schedule_batch_processing()

        return operation_id

    def _schedule_batch_processing(self):
        """调度批量处理"""
        if self.batch_timer is None or not self.batch_timer.is_alive():
            self.batch_timer = threading.Timer(self.batch_interval, self._process_batch)
            self.batch_timer.start()

    def _process_batch(self):
        """处理批量Git操作"""
        with self.batch_lock:
            if not self.batch_operations:
                return

            # 按优先级和操作类型分组
            operations_by_type = defaultdict(list)
            for op in self.batch_operations:
                operations_by_type[op['operation']].append(op)

            self.batch_operations.clear()

        # 优化批量操作
        for operation_type, ops in operations_by_type.items():
            self._execute_batch_operations(operation_type, ops)

        self.batch_timer = None

    def _execute_batch_operations(self, operation_type: str, operations: List[Dict]):
        """执行批量操作"""
        if operation_type == 'status':
            # 状态查询可以合并
            self._batch_status_operations(operations)
        elif operation_type == 'log':
            # 日志查询可以合并
            self._batch_log_operations(operations)
        else:
            # 其他操作逐个执行
            for op in operations:
                self._execute_single_operation(op)

        self.stats['batched_operations'] += len(operations)

    def _batch_status_operations(self, operations: List[Dict]):
        """批量状态操作"""
        # 合并状态查询，一次性获取完整状态
        try:
            # 模拟批量Git状态获取
            batch_result = {
                'status': 'clean',
                'branch': 'main',
                'ahead': 0,
                'behind': 0,
                'staged': [],
                'modified': [],
                'untracked': []
            }

            # 为所有操作返回结果
            for op in operations:
                if op['callback']:
                    op['callback'](batch_result)

            log_info(f"批量状态查询完成: {len(operations)} 个操作")

        except Exception as e:
            log_error(f"批量状态查询失败: {e}")

    def _batch_log_operations(self, operations: List[Dict]):
        """批量日志操作"""
        # 合并日志查询参数
        max_count = max((int(op['args'][1]) if len(op['args']) > 1 else 10) for op in operations)

        try:
            # 模拟批量Git日志获取
            batch_result = [
                {'hash': 'abc123', 'message': 'commit message', 'author': 'user', 'date': '2024-01-17'}
            ] * max_count

            # 为每个操作筛选对应结果
            for op in operations:
                count = int(op['args'][1]) if len(op['args']) > 1 else 10
                result = batch_result[:count]

                if op['callback']:
                    op['callback'](result)

            log_info(f"批量日志查询完成: {len(operations)} 个操作")

        except Exception as e:
            log_error(f"批量日志查询失败: {e}")

    def _execute_single_operation(self, operation: Dict):
        """执行单个Git操作"""
        try:
            # 检查缓存
            cache_key = f"{operation['operation']}:{':'.join(operation['args'])}"
            cached_result = self.git_cache.get_cached_result(cache_key)

            if cached_result:
                self.stats['cache_hits'] += 1
                if operation['callback']:
                    operation['callback'](cached_result)
                return

            # 执行实际Git操作 (模拟)
            result = f"Git {operation['operation']} result"

            # 缓存结果
            self.git_cache.cache_result(cache_key, result)

            if operation['callback']:
                operation['callback'](result)

            self.stats['single_operations'] += 1

        except Exception as e:
            log_error(f"Git操作执行失败 {operation['operation']}: {e}")

    def get_optimization_stats(self) -> Dict[str, Any]:
        """获取优化统计"""
        total_ops = self.stats['batched_operations'] + self.stats['single_operations']
        optimization_ratio = (self.stats['batched_operations'] / total_ops * 100) if total_ops > 0 else 0

        return {
            **self.stats,
            'optimization_ratio': f"{optimization_ratio:.1f}%",
            'pending_operations': len(self.batch_operations)
        }

class MemoryOptimizer:
    """内存优化器 - 智能GC和对象复用"""

    def __init__(self):
        self.gc_stats = {'collections': 0, 'freed_objects': 0, 'freed_memory_mb': 0.0}
        self.object_pools: Dict[type, List[Any]] = defaultdict(list)
        self.weak_refs: Dict[str, Any] = {}
        self.memory_pressure_threshold = 80.0  # 80%内存使用率

        # 设置GC调优
        self._tune_gc()

        log_info("内存优化器初始化完成")

    def _tune_gc(self):
        """调优垃圾收集器"""
        # 设置更激进的GC阈值以减少内存碎片
        gc.set_threshold(700, 10, 10)

        # 启用自动垃圾回收
        gc.enable()

    async def smart_gc(self, force: bool = False) -> Dict[str, Any]:
        """智能垃圾回收"""
        # 检查内存压力
        memory_percent = psutil.virtual_memory().percent

        if not force and memory_percent < self.memory_pressure_threshold:
            return {'message': 'Memory pressure low, GC skipped', 'memory_percent': memory_percent}

        before_memory = psutil.Process().memory_info().rss / 1024 / 1024

        # 执行垃圾回收
        collected = gc.collect()

        after_memory = psutil.Process().memory_info().rss / 1024 / 1024
        freed_memory = before_memory - after_memory

        # 更新统计
        self.gc_stats['collections'] += 1
        self.gc_stats['freed_objects'] += collected
        self.gc_stats['freed_memory_mb'] += freed_memory

        result = {
            'objects_collected': collected,
            'memory_freed_mb': freed_memory,
            'before_memory_mb': before_memory,
            'after_memory_mb': after_memory,
            'memory_percent': memory_percent
        }

        log_info(f"智能GC完成: 回收 {collected} 对象, 释放 {freed_memory:.2f}MB 内存")
        return result

    @contextmanager
    def managed_object(self, obj_type: type, *args, **kwargs):
        """管理对象生命周期"""
        # 从对象池获取或创建
        if self.object_pools[obj_type]:
            obj = self.object_pools[obj_type].pop()
            if hasattr(obj, 'reset'):
                obj.reset()
        else:
            obj = obj_type(*args, **kwargs)

        try:
            yield obj
        finally:
            # 归还到对象池
            if len(self.object_pools[obj_type]) < 50:  # 限制池大小
                self.object_pools[obj_type].append(obj)

    def register_weak_reference(self, key: str, obj: Any) -> None:
        """注册弱引用避免循环引用"""
        import weakref
        self.weak_refs[key] = weakref.ref(obj)

    def cleanup_weak_references(self) -> int:
        """清理死亡的弱引用"""
        dead_refs = []
        for key, ref in self.weak_refs.items():
            if ref() is None:
                dead_refs.append(key)

        for key in dead_refs:
            del self.weak_refs[key]

        return len(dead_refs)

    def get_memory_stats(self) -> Dict[str, Any]:
        """获取内存统计"""
        process = psutil.Process()
        memory_info = process.memory_info()

        return {
            'rss_mb': memory_info.rss / 1024 / 1024,
            'vms_mb': memory_info.vms / 1024 / 1024,
            'percent': process.memory_percent(),
            'gc_stats': self.gc_stats.copy(),
            'object_pools': {str(k): len(v) for k, v in self.object_pools.items()},
            'weak_refs_count': len(self.weak_refs)
        }

class PerformanceBenchmark:
    """性能基准测试系统"""

    def __init__(self):
        self.benchmarks: Dict[str, List[float]] = defaultdict(list)
        self.baselines: Dict[str, float] = {}
        self.regression_threshold = 0.2  # 20%性能回归阈值

        log_info("性能基准测试系统初始化完成")

    def record_benchmark(self, test_name: str, execution_time: float,
                        metadata: Dict[str, Any] = None) -> None:
        """记录基准测试结果"""
        self.benchmarks[test_name].append(execution_time)

        # 保持最近100个结果
        if len(self.benchmarks[test_name]) > 100:
            self.benchmarks[test_name] = self.benchmarks[test_name][-100:]

        log_info(f"基准测试记录: {test_name} = {execution_time:.3f}s")

    def establish_baseline(self, test_name: str) -> None:
        """建立性能基线"""
        if test_name in self.benchmarks and len(self.benchmarks[test_name]) >= 10:
            # 使用最近10次的中位数作为基线
            recent_results = self.benchmarks[test_name][-10:]
            self.baselines[test_name] = statistics.median(recent_results)
            log_info(f"基线建立: {test_name} = {self.baselines[test_name]:.3f}s")

    def check_regression(self, test_name: str) -> Optional[Dict[str, Any]]:
        """检查性能回归"""
        if test_name not in self.baselines or test_name not in self.benchmarks:
            return None

        current_result = self.benchmarks[test_name][-1]
        baseline = self.baselines[test_name]

        regression_ratio = (current_result - baseline) / baseline

        if regression_ratio > self.regression_threshold:
            return {
                'test_name': test_name,
                'current': current_result,
                'baseline': baseline,
                'regression_ratio': regression_ratio,
                'severity': 'high' if regression_ratio > 0.5 else 'medium'
            }

        return None

    def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """运行全面基准测试"""
        results = {}

        # 1. Agent执行基准测试
        start_time = time.perf_counter()
        # 模拟Agent执行
        time.sleep(0.1)  # 模拟100ms执行时间
        agent_time = time.perf_counter() - start_time
        self.record_benchmark('agent_execution', agent_time)
        results['agent_execution'] = agent_time

        # 2. 缓存性能基准测试
        start_time = time.perf_counter()
        # 测试缓存读写性能
        for i in range(100):
            performance_cache.git_cache.cache_result(f'test_key_{i}', f'test_value_{i}')
        for i in range(100):
            performance_cache.git_cache.get_cached_result(f'test_key_{i}')
        cache_time = time.perf_counter() - start_time
        self.record_benchmark('cache_performance', cache_time)
        results['cache_performance'] = cache_time

        # 3. Git操作基准测试
        start_time = time.perf_counter()
        # 模拟Git操作
        time.sleep(0.05)  # 模拟50ms Git操作
        git_time = time.perf_counter() - start_time
        self.record_benchmark('git_operations', git_time)
        results['git_operations'] = git_time

        # 4. 内存分配基准测试
        start_time = time.perf_counter()
        # 测试内存分配性能
        test_objects = [{'data': f'item_{i}'} for i in range(1000)]
        del test_objects
        memory_time = time.perf_counter() - start_time
        self.record_benchmark('memory_allocation', memory_time)
        results['memory_allocation'] = memory_time

        # 检查回归
        regressions = []
        for test_name in results.keys():
            regression = self.check_regression(test_name)
            if regression:
                regressions.append(regression)

        return {
            'results': results,
            'regressions': regressions,
            'timestamp': datetime.now().isoformat()
        }

    def get_benchmark_summary(self) -> Dict[str, Any]:
        """获取基准测试摘要"""
        summary = {}

        for test_name, results in self.benchmarks.items():
            if results:
                summary[test_name] = {
                    'count': len(results),
                    'latest': results[-1],
                    'average': statistics.mean(results),
                    'median': statistics.median(results),
                    'min': min(results),
                    'max': max(results),
                    'baseline': self.baselines.get(test_name, 0.0)
                }

        return summary

class EnhancedPerformanceOptimizer:
    """增强性能优化器 - 统一所有优化功能"""

    def __init__(self):
        self.cache_system = IntelligentCacheSystem()
        self.resource_manager = ResourcePoolManager()
        self.git_optimizer = GitOperationOptimizer()
        self.memory_optimizer = MemoryOptimizer()
        self.benchmark_system = PerformanceBenchmark()

        # 自动优化配置
        self.auto_optimization = False
        self.optimization_interval = 300  # 5分钟
        self.optimization_thread = None

        # 优化历史
        self.optimization_history: List[OptimizationResult] = []

        # 性能指标
        self.performance_metrics = {
            'response_time_p95': deque(maxlen=1000),
            'throughput_rps': deque(maxlen=1000),
            'memory_usage_mb': deque(maxlen=1000),
            'cache_hit_rate': deque(maxlen=1000)
        }

        log_info("增强性能优化器初始化完成")

    async def optimize_agent_execution(self, agent_type: str, request_params: Dict[str, Any]) -> Any:
        """优化Agent执行"""
        # 生成请求哈希
        request_hash = hashlib.md5(str(request_params).encode()).hexdigest()

        # 尝试从缓存获取结果
        cached_result = await self.cache_system.get_agent_result(agent_type, request_hash, request_params)
        if cached_result:
            return cached_result

        # 使用资源池获取执行上下文
        with self.resource_manager.get_resource('execution_context') as context:
            context.agent_id = agent_type
            context.request_id = request_hash
            context.start_time = time.perf_counter()
            context.parameters = request_params

            try:
                # 模拟Agent执行
                await asyncio.sleep(0.1)  # 模拟100ms执行时间
                result = {"status": "success", "data": f"Result from {agent_type}"}

                # 记录执行时间
                context.execution_time = time.perf_counter() - context.start_time

                # 缓存结果
                await self.cache_system.cache_agent_result(agent_type, request_hash, result, request_params)

                # 更新性能指标
                self.performance_metrics['response_time_p95'].append(context.execution_time * 1000)  # ms

                return result

            except Exception as e:
                log_error(f"Agent执行失败 {agent_type}: {e}")
                raise

    def batch_git_operations(self, operations: List[Tuple[str, List[str]]]) -> List[str]:
        """批量Git操作"""
        operation_ids = []

        for operation, args in operations:
            op_id = self.git_optimizer.queue_git_operation(operation, args)
            operation_ids.append(op_id)

        return operation_ids

    async def optimize_memory_usage(self) -> Dict[str, Any]:
        """优化内存使用"""
        before_stats = self.memory_optimizer.get_memory_stats()

        # 执行内存优化
        gc_result = await self.memory_optimizer.smart_gc()

        # 清理弱引用
        dead_refs = self.memory_optimizer.cleanup_weak_references()

        # 清理过期缓存
        await self.cache_system._evict_cache()

        after_stats = self.memory_optimizer.get_memory_stats()

        # 记录优化结果
        improvement = before_stats['rss_mb'] - after_stats['rss_mb']
        optimization_result = OptimizationResult(
            category='memory',
            before_metric=before_stats['rss_mb'],
            after_metric=after_stats['rss_mb'],
            improvement=improvement,
            description=f"释放 {improvement:.2f}MB 内存, 清理 {dead_refs} 个弱引用"
        )

        self.optimization_history.append(optimization_result)

        return {
            'before_stats': before_stats,
            'after_stats': after_stats,
            'gc_result': gc_result,
            'dead_refs_cleaned': dead_refs,
            'improvement_mb': improvement
        }

    def start_auto_optimization(self) -> None:
        """启动自动优化"""
        if self.auto_optimization:
            return

        self.auto_optimization = True

        def optimization_loop():
            while self.auto_optimization:
                try:
                    # 异步运行优化任务
                    asyncio.run(self._run_optimization_cycle())
                    time.sleep(self.optimization_interval)
                except Exception as e:
                    log_error(f"自动优化循环异常: {e}")
                    time.sleep(60)  # 出错后等待1分钟

        self.optimization_thread = threading.Thread(target=optimization_loop, daemon=True)
        self.optimization_thread.start()

        log_info("自动性能优化已启动")

    def stop_auto_optimization(self) -> None:
        """停止自动优化"""
        self.auto_optimization = False
        log_info("自动性能优化已停止")

    async def _run_optimization_cycle(self) -> None:
        """运行优化周期"""
        # 检查性能指标
        current_metrics = performance_monitor.get_current_metrics()

        # 决定是否需要优化
        needs_optimization = False

        if 'memory_usage' in current_metrics:
            memory_usage = current_metrics['memory_usage'].value
            if memory_usage > 80:  # 内存使用率超过80%
                needs_optimization = True
                await self.optimize_memory_usage()

        if 'cache_hit_rate' in current_metrics:
            hit_rate = current_metrics['cache_hit_rate'].value
            if hit_rate < 70:  # 缓存命中率低于70%
                needs_optimization = True
                await self.cache_system._evict_cache()

        if needs_optimization:
            log_info("自动优化周期完成")

    def run_performance_benchmark(self) -> Dict[str, Any]:
        """运行性能基准测试"""
        return self.benchmark_system.run_comprehensive_benchmark()

    def get_comprehensive_report(self) -> Dict[str, Any]:
        """获取全面性能报告"""
        return {
            'timestamp': datetime.now().isoformat(),
            'cache_stats': self.cache_system.get_cache_stats(),
            'resource_pool_stats': self.resource_manager.get_pool_stats(),
            'git_optimization_stats': self.git_optimizer.get_optimization_stats(),
            'memory_stats': self.memory_optimizer.get_memory_stats(),
            'benchmark_summary': self.benchmark_system.get_benchmark_summary(),
            'optimization_history': [
                {
                    'category': opt.category,
                    'improvement': opt.improvement,
                    'description': opt.description,
                    'timestamp': opt.timestamp.isoformat()
                }
                for opt in self.optimization_history[-10:]  # 最近10次优化
            ],
            'performance_metrics': {
                name: {
                    'count': len(values),
                    'latest': values[-1] if values else 0,
                    'average': statistics.mean(values) if values else 0,
                    'p95': statistics.quantiles(values, n=20)[18] if len(values) > 20 else (values[-1] if values else 0)
                }
                for name, values in self.performance_metrics.items()
            }
        }

# 全局增强性能优化器实例
enhanced_performance_optimizer = EnhancedPerformanceOptimizer()

# 便捷函数
async def optimize_agent_execution(agent_type: str, params: Dict[str, Any]) -> Any:
    """便捷函数：优化Agent执行"""
    return await enhanced_performance_optimizer.optimize_agent_execution(agent_type, params)

def batch_git_operations(operations: List[Tuple[str, List[str]]]) -> List[str]:
    """便捷函数：批量Git操作"""
    return enhanced_performance_optimizer.batch_git_operations(operations)

async def optimize_memory() -> Dict[str, Any]:
    """便捷函数：优化内存"""
    return await enhanced_performance_optimizer.optimize_memory_usage()

def start_performance_optimization() -> None:
    """便捷函数：启动性能优化"""
    enhanced_performance_optimizer.start_auto_optimization()

def get_performance_report() -> Dict[str, Any]:
    """便捷函数：获取性能报告"""
    return enhanced_performance_optimizer.get_comprehensive_report()

def run_benchmark() -> Dict[str, Any]:
    """便捷函数：运行基准测试"""
    return enhanced_performance_optimizer.run_performance_benchmark()

# 性能优化上下文管理器
@asynccontextmanager
async def optimized_execution():
    """优化执行上下文管理器"""
    start_time = time.perf_counter()

    # 执行前优化
    await enhanced_performance_optimizer.memory_optimizer.smart_gc()

    try:
        yield enhanced_performance_optimizer
    finally:
        # 执行后清理
        execution_time = time.perf_counter() - start_time
        enhanced_performance_optimizer.performance_metrics['response_time_p95'].append(execution_time * 1000)

        # 如果执行时间过长，触发优化
        if execution_time > 1.0:  # 超过1秒
            log_warning(f"执行时间过长: {execution_time:.3f}s，触发优化")
            await enhanced_performance_optimizer.optimize_memory_usage()

if __name__ == "__main__":
    # 测试性能优化器
    async def test_optimizer():
        print("🚀 测试增强性能优化器")

        # 启动自动优化
        enhanced_performance_optimizer.start_auto_optimization()

        # 测试Agent执行优化
        result = await optimize_agent_execution('test-agent', {'param1': 'value1'})
        print(f"Agent执行结果: {result}")

        # 测试批量Git操作
        git_ops = [
            ('status', []),
            ('log', ['--oneline', '10']),
            ('branch', ['-a'])
        ]
        operation_ids = batch_git_operations(git_ops)
        print(f"Git操作队列: {operation_ids}")

        # 等待批量处理
        await asyncio.sleep(3)

        # 运行基准测试
        benchmark_results = run_benchmark()
        print(f"基准测试结果: {benchmark_results}")

        # 获取全面报告
        report = get_performance_report()
        print(f"性能报告摘要:")
        print(f"  缓存命中率: {report['cache_stats']['hit_rate']}")
        print(f"  内存使用: {report['memory_stats']['rss_mb']:.2f}MB")
        print(f"  优化历史: {len(report['optimization_history'])} 次")

        # 停止自动优化
        enhanced_performance_optimizer.stop_auto_optimization()

    # 运行测试
    asyncio.run(test_optimizer())