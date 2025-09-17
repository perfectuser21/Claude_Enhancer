#!/usr/bin/env python3
"""
异步并行执行器 - 性能优化版本
使用异步操作、连接池、批量处理提升Perfect21性能
"""

import asyncio
import logging
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import aiofiles
import weakref
from functools import wraps

from .smart_decomposer import TaskAnalysis, AgentTask
from .parallel_manager import ParallelManager, ExecutionResult, ParallelExecutionSummary

logger = logging.getLogger("AsyncParallelExecutor")


class ExecutionMode(Enum):
    """执行模式"""
    SEQUENTIAL = "sequential"      # 顺序执行
    PARALLEL = "parallel"          # 并行执行
    PIPELINE = "pipeline"          # 流水线执行
    ADAPTIVE = "adaptive"          # 自适应执行


@dataclass
class AsyncExecutionConfig:
    """异步执行配置"""
    max_concurrent_tasks: int = 8
    task_timeout: int = 300  # 5分钟
    batch_size: int = 4
    retry_count: int = 3
    circuit_breaker_threshold: int = 5
    connection_pool_size: int = 10
    prefetch_enabled: bool = True
    resource_monitoring: bool = True


@dataclass
class ResourceMetrics:
    """资源指标"""
    cpu_usage: float
    memory_usage: float
    active_tasks: int
    queue_size: int
    response_time: float
    error_rate: float
    timestamp: datetime


class CircuitBreaker:
    """熔断器"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN

    def call(self, func: Callable):
        """包装函数调用"""
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if self.state == 'OPEN':
                if time.time() - self.last_failure_time > self.recovery_timeout:
                    self.state = 'HALF_OPEN'
                else:
                    raise Exception("Circuit breaker is OPEN")

            try:
                result = await func(*args, **kwargs)
                if self.state == 'HALF_OPEN':
                    self.state = 'CLOSED'
                    self.failure_count = 0
                return result
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()

                if self.failure_count >= self.failure_threshold:
                    self.state = 'OPEN'

                raise e

        return wrapper


class AsyncTaskQueue:
    """异步任务队列"""

    def __init__(self, max_size: int = 1000):
        self.queue = asyncio.Queue(maxsize=max_size)
        self.priority_queue = asyncio.PriorityQueue(maxsize=max_size)
        self.processing = set()
        self.completed = {}
        self.failed = {}

    async def put(self, task: AgentTask, priority: int = 5):
        """添加任务到队列"""
        await self.priority_queue.put((priority, time.time(), task))

    async def get(self) -> Tuple[int, float, AgentTask]:
        """获取任务"""
        return await self.priority_queue.get()

    def mark_processing(self, task_id: str):
        """标记任务为处理中"""
        self.processing.add(task_id)

    def mark_completed(self, task_id: str, result: Any):
        """标记任务完成"""
        self.processing.discard(task_id)
        self.completed[task_id] = result

    def mark_failed(self, task_id: str, error: Exception):
        """标记任务失败"""
        self.processing.discard(task_id)
        self.failed[task_id] = error

    @property
    def size(self) -> int:
        """队列大小"""
        return self.priority_queue.qsize()

    @property
    def stats(self) -> Dict[str, int]:
        """获取统计信息"""
        return {
            'queue_size': self.size,
            'processing': len(self.processing),
            'completed': len(self.completed),
            'failed': len(self.failed)
        }


class AsyncConnectionPool:
    """异步连接池"""

    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self.pool = asyncio.Queue(maxsize=max_connections)
        self.active_connections = 0
        self.total_connections = 0
        self._lock = asyncio.Lock()

        # 预创建连接
        asyncio.create_task(self._populate_pool())

    async def _populate_pool(self):
        """预填充连接池"""
        for _ in range(self.max_connections):
            connection = await self._create_connection()
            await self.pool.put(connection)

    async def _create_connection(self) -> Dict[str, Any]:
        """创建新连接"""
        self.total_connections += 1
        return {
            'id': self.total_connections,
            'created_at': datetime.now(),
            'executor': ThreadPoolExecutor(max_workers=2, thread_name_prefix=f"conn-{self.total_connections}"),
            'process_executor': ProcessPoolExecutor(max_workers=1)
        }

    async def acquire(self) -> Dict[str, Any]:
        """获取连接"""
        async with self._lock:
            self.active_connections += 1

        try:
            # 等待可用连接，最多等待10秒
            connection = await asyncio.wait_for(self.pool.get(), timeout=10.0)
            return connection
        except asyncio.TimeoutError:
            # 如果没有可用连接，创建新的临时连接
            logger.warning("连接池耗尽，创建临时连接")
            return await self._create_connection()

    async def release(self, connection: Dict[str, Any]):
        """释放连接"""
        async with self._lock:
            self.active_connections -= 1

        try:
            # 如果队列未满，放回连接池
            self.pool.put_nowait(connection)
        except asyncio.QueueFull:
            # 队列已满，关闭连接
            await self._close_connection(connection)

    async def _close_connection(self, connection: Dict[str, Any]):
        """关闭连接"""
        try:
            connection['executor'].shutdown(wait=False)
            connection['process_executor'].shutdown(wait=False)
        except Exception as e:
            logger.error(f"关闭连接失败: {e}")

    async def close_all(self):
        """关闭所有连接"""
        while not self.pool.empty():
            try:
                connection = self.pool.get_nowait()
                await self._close_connection(connection)
            except asyncio.QueueEmpty:
                break

    @property
    def stats(self) -> Dict[str, Any]:
        """获取连接池统计"""
        return {
            'max_connections': self.max_connections,
            'active_connections': self.active_connections,
            'available_connections': self.pool.qsize(),
            'total_created': self.total_connections
        }


class AsyncPerformanceMonitor:
    """异步性能监控器"""

    def __init__(self, monitoring_interval: float = 1.0):
        self.monitoring_interval = monitoring_interval
        self.metrics_history: List[ResourceMetrics] = []
        self.max_history_size = 1000
        self._monitoring_task = None
        self._stop_event = asyncio.Event()

    def start_monitoring(self):
        """开始监控"""
        if self._monitoring_task is None or self._monitoring_task.done():
            self._stop_event.clear()
            self._monitoring_task = asyncio.create_task(self._monitor_loop())

    async def _monitor_loop(self):
        """监控循环"""
        while not self._stop_event.is_set():
            try:
                metrics = await self._collect_metrics()
                self.metrics_history.append(metrics)

                # 限制历史记录大小
                if len(self.metrics_history) > self.max_history_size:
                    self.metrics_history = self.metrics_history[-self.max_history_size:]

                await asyncio.sleep(self.monitoring_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"性能监控错误: {e}")

    async def _collect_metrics(self) -> ResourceMetrics:
        """收集性能指标"""
        try:
            import psutil
            cpu_usage = psutil.cpu_percent(interval=None)
            memory_usage = psutil.virtual_memory().percent
        except ImportError:
            cpu_usage = 0.0
            memory_usage = 0.0

        return ResourceMetrics(
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            active_tasks=len(asyncio.all_tasks()),
            queue_size=0,  # 由调用者设置
            response_time=0.0,  # 由调用者设置
            error_rate=0.0,  # 由调用者设置
            timestamp=datetime.now()
        )

    def stop_monitoring(self):
        """停止监控"""
        self._stop_event.set()
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()

    def get_latest_metrics(self) -> Optional[ResourceMetrics]:
        """获取最新指标"""
        return self.metrics_history[-1] if self.metrics_history else None

    def get_average_metrics(self, window_size: int = 60) -> Optional[ResourceMetrics]:
        """获取平均指标"""
        if not self.metrics_history:
            return None

        recent_metrics = self.metrics_history[-window_size:]
        if not recent_metrics:
            return None

        avg_cpu = sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m.memory_usage for m in recent_metrics) / len(recent_metrics)
        avg_response_time = sum(m.response_time for m in recent_metrics) / len(recent_metrics)

        return ResourceMetrics(
            cpu_usage=avg_cpu,
            memory_usage=avg_memory,
            active_tasks=recent_metrics[-1].active_tasks,
            queue_size=recent_metrics[-1].queue_size,
            response_time=avg_response_time,
            error_rate=sum(m.error_rate for m in recent_metrics) / len(recent_metrics),
            timestamp=datetime.now()
        )


class AsyncParallelExecutor:
    """异步并行执行器"""

    def __init__(self, config: AsyncExecutionConfig = None):
        self.config = config or AsyncExecutionConfig()
        self.task_queue = AsyncTaskQueue()
        self.connection_pool = AsyncConnectionPool(self.config.connection_pool_size)
        self.performance_monitor = AsyncPerformanceMonitor()
        self.circuit_breaker = CircuitBreaker(self.config.circuit_breaker_threshold)

        # 执行统计
        self.execution_stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'total_execution_time': 0.0,
            'average_response_time': 0.0,
            'throughput': 0.0,
            'error_rate': 0.0
        }

        # 执行日志
        self.execution_log = []

        # 启动性能监控
        self.performance_monitor.start_monitoring()

    async def execute_parallel_task(self, task_description: str, analysis: TaskAnalysis) -> Dict[str, Any]:
        """
        异步执行并行任务

        Args:
            task_description: 任务描述
            analysis: 任务分析结果

        Returns:
            执行结果
        """
        logger.info(f"开始异步并行执行: {task_description}")
        start_time = time.time()

        try:
            # 显示执行计划
            await self._display_execution_plan_async(analysis)

            # 选择执行模式
            execution_mode = await self._determine_execution_mode(analysis)

            # 根据模式执行任务
            if execution_mode == ExecutionMode.PARALLEL:
                results = await self._execute_parallel_mode(analysis)
            elif execution_mode == ExecutionMode.PIPELINE:
                results = await self._execute_pipeline_mode(analysis)
            elif execution_mode == ExecutionMode.ADAPTIVE:
                results = await self._execute_adaptive_mode(analysis)
            else:
                results = await self._execute_sequential_mode(analysis)

            # 计算执行时间
            execution_time = time.time() - start_time

            # 更新统计
            await self._update_execution_stats(execution_time, results)

            # 创建执行记录
            execution_record = {
                "task_description": task_description,
                "timestamp": datetime.now().isoformat(),
                "execution_mode": execution_mode.value,
                "execution_time": execution_time,
                "results": results,
                "stats": self.execution_stats.copy()
            }

            self.execution_log.append(execution_record)

            return {
                "success": True,
                "execution_mode": execution_mode.value,
                "execution_time": execution_time,
                "results": results,
                "performance_metrics": await self._get_performance_summary()
            }

        except Exception as e:
            logger.error(f"异步并行执行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time,
                "performance_metrics": await self._get_performance_summary()
            }

    async def _display_execution_plan_async(self, analysis: TaskAnalysis):
        """异步显示执行计划"""
        plan_text = f"""
🚀 Perfect21 异步并行执行计划
{"=" * 60}
📋 原始任务: {analysis.original_task}
🎯 项目类型: {analysis.project_type}
📊 复杂度等级: {analysis.complexity.value}
⚡ 执行模式: 异步并行优化
⏱️ 预估总时间: {analysis.estimated_total_time}分钟
🤖 涉及agents: {len(analysis.agent_tasks)}个
{"=" * 60}

👥 Agent执行清单:
"""

        for i, task in enumerate(analysis.agent_tasks, 1):
            priority_emoji = "🔥" if task.priority <= 2 else "📋"
            plan_text += f"""  {priority_emoji} {i}. @{task.agent_name}
      任务: {task.task_description}
      预估: {task.estimated_time}分钟
      优先级: P{task.priority}
"""
            if task.dependencies:
                deps = ", ".join([f"@{dep}" for dep in task.dependencies])
                plan_text += f"      依赖: {deps}\n"

        plan_text += f"""
⚡ **性能优化特性**:
- 异步并行执行，避免阻塞
- 智能任务队列和优先级调度
- 连接池复用，减少开销
- 熔断器保护，提高稳定性
- 实时性能监控和自适应调整
{"=" * 60}
"""

        # 异步写入日志（如果需要）
        logger.info(plan_text)
        print(plan_text)

    async def _determine_execution_mode(self, analysis: TaskAnalysis) -> ExecutionMode:
        """确定执行模式"""
        # 获取当前系统资源状态
        metrics = self.performance_monitor.get_latest_metrics()

        # 根据任务复杂度和系统资源决定执行模式
        if len(analysis.agent_tasks) <= 2:
            return ExecutionMode.SEQUENTIAL

        if metrics and metrics.cpu_usage > 80:
            # CPU使用率高，使用流水线模式
            return ExecutionMode.PIPELINE

        if len(analysis.agent_tasks) >= 6:
            # 大量任务，使用自适应模式
            return ExecutionMode.ADAPTIVE

        # 默认并行模式
        return ExecutionMode.PARALLEL

    async def _execute_parallel_mode(self, analysis: TaskAnalysis) -> List[Dict[str, Any]]:
        """并行执行模式"""
        logger.info(f"使用并行执行模式处理 {len(analysis.agent_tasks)} 个任务")

        # 创建信号量限制并发数
        semaphore = asyncio.Semaphore(self.config.max_concurrent_tasks)

        # 包装任务执行
        async def execute_with_semaphore(task: AgentTask):
            async with semaphore:
                return await self._execute_single_task(task)

        # 并行执行所有任务
        tasks = [execute_with_semaphore(task) for task in analysis.agent_tasks]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "task_id": analysis.agent_tasks[i].agent_name,
                    "success": False,
                    "error": str(result),
                    "execution_time": 0.0
                })
            else:
                processed_results.append(result)

        return processed_results

    async def _execute_pipeline_mode(self, analysis: TaskAnalysis) -> List[Dict[str, Any]]:
        """流水线执行模式"""
        logger.info(f"使用流水线执行模式处理 {len(analysis.agent_tasks)} 个任务")

        # 按依赖关系排序任务
        sorted_tasks = self._sort_tasks_by_dependencies(analysis.agent_tasks)

        # 分批执行
        results = []
        batch_size = self.config.batch_size

        for i in range(0, len(sorted_tasks), batch_size):
            batch = sorted_tasks[i:i + batch_size]
            logger.info(f"执行批次 {i//batch_size + 1}: {len(batch)} 个任务")

            # 并行执行批次内的任务
            batch_tasks = [self._execute_single_task(task) for task in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            # 处理批次结果
            for j, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    results.append({
                        "task_id": batch[j].agent_name,
                        "success": False,
                        "error": str(result),
                        "execution_time": 0.0
                    })
                else:
                    results.append(result)

            # 短暂休息，防止系统过载
            await asyncio.sleep(0.1)

        return results

    async def _execute_adaptive_mode(self, analysis: TaskAnalysis) -> List[Dict[str, Any]]:
        """自适应执行模式"""
        logger.info(f"使用自适应执行模式处理 {len(analysis.agent_tasks)} 个任务")

        # 将任务添加到队列
        for task in analysis.agent_tasks:
            await self.task_queue.put(task, task.priority)

        # 动态调整并发数
        results = []
        workers = []

        # 启动初始工作者
        initial_workers = min(self.config.max_concurrent_tasks, len(analysis.agent_tasks))
        for i in range(initial_workers):
            worker = asyncio.create_task(self._adaptive_worker(f"worker-{i}"))
            workers.append(worker)

        # 监控执行进度并动态调整
        while self.task_queue.size > 0 or any(not w.done() for w in workers):
            # 检查是否需要调整工作者数量
            metrics = self.performance_monitor.get_latest_metrics()
            if metrics:
                if metrics.cpu_usage < 50 and self.task_queue.size > len(workers):
                    # CPU使用率低且有待处理任务，增加工作者
                    if len(workers) < self.config.max_concurrent_tasks:
                        new_worker = asyncio.create_task(self._adaptive_worker(f"worker-{len(workers)}"))
                        workers.append(new_worker)
                        logger.info(f"增加工作者，当前工作者数: {len(workers)}")

                elif metrics.cpu_usage > 90:
                    # CPU使用率过高，减少工作者（通过完成任务自然减少）
                    pass

            await asyncio.sleep(1.0)

        # 等待所有工作者完成
        await asyncio.gather(*workers, return_exceptions=True)

        # 收集结果
        results.extend(list(self.task_queue.completed.values()))

        # 处理失败的任务
        for task_id, error in self.task_queue.failed.items():
            results.append({
                "task_id": task_id,
                "success": False,
                "error": str(error),
                "execution_time": 0.0
            })

        return results

    async def _adaptive_worker(self, worker_id: str):
        """自适应工作者"""
        logger.debug(f"启动自适应工作者: {worker_id}")

        while True:
            try:
                # 尝试获取任务，超时5秒
                priority, timestamp, task = await asyncio.wait_for(
                    self.task_queue.get(), timeout=5.0
                )

                task_id = task.agent_name
                self.task_queue.mark_processing(task_id)

                try:
                    # 执行任务
                    result = await self._execute_single_task(task)
                    self.task_queue.mark_completed(task_id, result)

                except Exception as e:
                    self.task_queue.mark_failed(task_id, e)
                    logger.error(f"工作者 {worker_id} 执行任务 {task_id} 失败: {e}")

            except asyncio.TimeoutError:
                # 没有更多任务，退出工作者
                logger.debug(f"工作者 {worker_id} 超时退出")
                break
            except Exception as e:
                logger.error(f"工作者 {worker_id} 异常: {e}")
                break

    async def _execute_sequential_mode(self, analysis: TaskAnalysis) -> List[Dict[str, Any]]:
        """顺序执行模式"""
        logger.info(f"使用顺序执行模式处理 {len(analysis.agent_tasks)} 个任务")

        results = []
        for task in analysis.agent_tasks:
            try:
                result = await self._execute_single_task(task)
                results.append(result)
            except Exception as e:
                results.append({
                    "task_id": task.agent_name,
                    "success": False,
                    "error": str(e),
                    "execution_time": 0.0
                })

        return results

    @CircuitBreaker(failure_threshold=5)
    async def _execute_single_task(self, task: AgentTask) -> Dict[str, Any]:
        """执行单个任务（带熔断器保护）"""
        start_time = time.time()
        task_id = task.agent_name

        try:
            # 获取连接
            connection = await self.connection_pool.acquire()

            try:
                # 模拟任务执行（实际应该调用相应的agent）
                logger.info(f"执行任务: {task_id} - {task.task_description}")

                # 这里应该是实际的agent调用逻辑
                # 为了演示，我们模拟一个异步操作
                await asyncio.sleep(min(task.estimated_time * 0.1, 2.0))  # 模拟执行时间

                execution_time = time.time() - start_time

                result = {
                    "task_id": task_id,
                    "agent_name": task.agent_name,
                    "task_description": task.task_description,
                    "success": True,
                    "execution_time": execution_time,
                    "result": f"模拟执行结果 for {task_id}",
                    "timestamp": datetime.now().isoformat()
                }

                logger.info(f"任务 {task_id} 执行完成，耗时 {execution_time:.2f}s")
                return result

            finally:
                # 释放连接
                await self.connection_pool.release(connection)

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"任务 {task_id} 执行失败: {e}")

            return {
                "task_id": task_id,
                "agent_name": task.agent_name,
                "task_description": task.task_description,
                "success": False,
                "execution_time": execution_time,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

    def _sort_tasks_by_dependencies(self, tasks: List[AgentTask]) -> List[AgentTask]:
        """按依赖关系排序任务"""
        # 简单的拓扑排序实现
        sorted_tasks = []
        remaining_tasks = tasks.copy()

        while remaining_tasks:
            # 找到没有依赖或依赖已满足的任务
            ready_tasks = []
            for task in remaining_tasks:
                if not task.dependencies:
                    ready_tasks.append(task)
                else:
                    completed_agents = {t.agent_name for t in sorted_tasks}
                    if set(task.dependencies).issubset(completed_agents):
                        ready_tasks.append(task)

            if not ready_tasks:
                # 如果没有就绪任务，可能存在循环依赖，添加剩余任务
                logger.warning("检测到可能的循环依赖，强制添加剩余任务")
                ready_tasks = remaining_tasks

            # 将就绪任务添加到结果并从剩余任务中移除
            for task in ready_tasks:
                sorted_tasks.append(task)
                remaining_tasks.remove(task)

        return sorted_tasks

    async def _update_execution_stats(self, execution_time: float, results: List[Dict[str, Any]]):
        """更新执行统计"""
        successful_tasks = sum(1 for r in results if r.get('success', False))
        failed_tasks = len(results) - successful_tasks

        self.execution_stats['total_tasks'] += len(results)
        self.execution_stats['completed_tasks'] += successful_tasks
        self.execution_stats['failed_tasks'] += failed_tasks
        self.execution_stats['total_execution_time'] += execution_time

        # 计算平均响应时间
        if self.execution_stats['total_tasks'] > 0:
            self.execution_stats['average_response_time'] = (
                self.execution_stats['total_execution_time'] / self.execution_stats['total_tasks']
            )

        # 计算吞吐量（任务/秒）
        if execution_time > 0:
            self.execution_stats['throughput'] = len(results) / execution_time

        # 计算错误率
        if self.execution_stats['total_tasks'] > 0:
            self.execution_stats['error_rate'] = (
                self.execution_stats['failed_tasks'] / self.execution_stats['total_tasks']
            )

    async def _get_performance_summary(self) -> Dict[str, Any]:
        """获取性能总结"""
        latest_metrics = self.performance_monitor.get_latest_metrics()
        avg_metrics = self.performance_monitor.get_average_metrics()

        return {
            "execution_stats": self.execution_stats.copy(),
            "current_metrics": asdict(latest_metrics) if latest_metrics else None,
            "average_metrics": asdict(avg_metrics) if avg_metrics else None,
            "connection_pool_stats": self.connection_pool.stats,
            "task_queue_stats": self.task_queue.stats,
            "circuit_breaker_state": self.circuit_breaker.state
        }

    async def get_real_time_status(self) -> Dict[str, Any]:
        """获取实时状态"""
        return {
            "timestamp": datetime.now().isoformat(),
            "active_tasks": len(asyncio.all_tasks()),
            "performance_summary": await self._get_performance_summary(),
            "last_execution": self.execution_log[-1] if self.execution_log else None
        }

    async def save_execution_report(self, filename: Optional[str] = None) -> str:
        """保存执行报告"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"async_execution_report_{timestamp}.json"

        report_data = {
            "report_type": "async_parallel_execution",
            "timestamp": datetime.now().isoformat(),
            "execution_stats": self.execution_stats,
            "performance_summary": await self._get_performance_summary(),
            "execution_log": self.execution_log[-10:],  # 最近10次执行
            "config": asdict(self.config)
        }

        async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(report_data, indent=2, ensure_ascii=False))

        logger.info(f"异步执行报告已保存到: {filename}")
        return filename

    async def optimize_performance(self):
        """性能优化建议"""
        avg_metrics = self.performance_monitor.get_average_metrics()
        if not avg_metrics:
            return

        optimizations = []

        if avg_metrics.cpu_usage > 80:
            optimizations.append("建议减少并发任务数量或使用流水线模式")

        if avg_metrics.memory_usage > 85:
            optimizations.append("建议减少缓存大小或增加内存")

        if self.execution_stats['error_rate'] > 0.1:
            optimizations.append("建议检查任务失败原因，可能需要调整超时设置")

        if avg_metrics.response_time > 30:
            optimizations.append("建议优化任务执行逻辑或增加连接池大小")

        return {
            "optimizations": optimizations,
            "current_config": asdict(self.config),
            "recommended_config": self._generate_optimized_config(avg_metrics)
        }

    def _generate_optimized_config(self, metrics: ResourceMetrics) -> AsyncExecutionConfig:
        """生成优化配置"""
        optimized_config = AsyncExecutionConfig()

        if metrics.cpu_usage > 80:
            optimized_config.max_concurrent_tasks = max(2, self.config.max_concurrent_tasks - 2)
            optimized_config.batch_size = max(2, self.config.batch_size - 1)

        if metrics.memory_usage > 85:
            optimized_config.connection_pool_size = max(5, self.config.connection_pool_size - 2)

        if self.execution_stats['error_rate'] > 0.1:
            optimized_config.task_timeout = min(600, self.config.task_timeout + 60)
            optimized_config.retry_count = min(5, self.config.retry_count + 1)

        return optimized_config

    async def close(self):
        """关闭异步执行器"""
        logger.info("关闭异步并行执行器...")

        # 停止性能监控
        self.performance_monitor.stop_monitoring()

        # 关闭连接池
        await self.connection_pool.close_all()

        # 取消批量处理任务
        if hasattr(self.task_queue, '_batch_task'):
            self.task_queue._batch_task.cancel()

        logger.info("异步并行执行器已关闭")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()


# 全局异步执行器实例
_async_parallel_executor: Optional[AsyncParallelExecutor] = None


async def get_async_parallel_executor(config: AsyncExecutionConfig = None) -> AsyncParallelExecutor:
    """获取异步并行执行器实例"""
    global _async_parallel_executor
    if _async_parallel_executor is None:
        _async_parallel_executor = AsyncParallelExecutor(config)
    return _async_parallel_executor


async def reset_async_parallel_executor():
    """重置异步并行执行器"""
    global _async_parallel_executor
    if _async_parallel_executor:
        await _async_parallel_executor.close()
    _async_parallel_executor = None