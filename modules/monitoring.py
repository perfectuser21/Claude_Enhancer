#!/usr/bin/env python3
"""
Perfect21 Monitoring and Observability System
监控和可观测性系统
"""

import logging
import time
import threading
import json
import psutil
import os
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from collections import deque, defaultdict
from enum import Enum
import weakref

logger = logging.getLogger("Perfect21.Monitoring")

class MetricType(Enum):
    """指标类型"""
    COUNTER = "counter"         # 计数器
    GAUGE = "gauge"            # 仪表盘
    HISTOGRAM = "histogram"     # 直方图
    TIMER = "timer"            # 计时器

@dataclass
class Metric:
    """指标数据"""
    name: str
    type: MetricType
    value: float
    timestamp: float
    labels: Dict[str, str]
    description: str = ""

@dataclass
class PerformanceTrace:
    """性能跟踪"""
    operation: str
    module: str
    start_time: float
    end_time: float
    duration: float
    success: bool
    error_message: Optional[str] = None
    context: Dict[str, Any] = None

class MetricsCollector:
    """指标收集器"""

    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        self.metrics: deque = deque(maxlen=max_metrics)
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.RLock()

    def increment_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] = None):
        """增加计数器"""
        with self._lock:
            key = self._make_key(name, labels)
            self.counters[key] += value
            self._add_metric(name, MetricType.COUNTER, self.counters[key], labels)

    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """设置仪表盘值"""
        with self._lock:
            key = self._make_key(name, labels)
            self.gauges[key] = value
            self._add_metric(name, MetricType.GAUGE, value, labels)

    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """记录直方图值"""
        with self._lock:
            key = self._make_key(name, labels)
            self.histograms[key].append(value)
            # 保持直方图不超过1000个值
            if len(self.histograms[key]) > 1000:
                self.histograms[key].pop(0)
            self._add_metric(name, MetricType.HISTOGRAM, value, labels)

    def _make_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """生成指标键"""
        if not labels:
            return name
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}[{label_str}]"

    def _add_metric(self, name: str, metric_type: MetricType, value: float, labels: Dict[str, str] = None):
        """添加指标"""
        metric = Metric(
            name=name,
            type=metric_type,
            value=value,
            timestamp=time.time(),
            labels=labels or {}
        )
        self.metrics.append(metric)

    def get_metrics(self, name_filter: str = None) -> List[Metric]:
        """获取指标"""
        with self._lock:
            if name_filter:
                return [m for m in self.metrics if name_filter in m.name]
            return list(self.metrics)

    def get_histogram_stats(self, name: str, labels: Dict[str, str] = None) -> Dict[str, float]:
        """获取直方图统计"""
        key = self._make_key(name, labels)
        values = self.histograms.get(key, [])

        if not values:
            return {}

        sorted_values = sorted(values)
        length = len(sorted_values)

        return {
            'count': length,
            'min': min(sorted_values),
            'max': max(sorted_values),
            'avg': sum(sorted_values) / length,
            'p50': sorted_values[length // 2],
            'p90': sorted_values[int(length * 0.9)],
            'p95': sorted_values[int(length * 0.95)],
            'p99': sorted_values[int(length * 0.99)]
        }

class PerformanceTracker:
    """性能跟踪器"""

    def __init__(self, max_traces: int = 1000):
        self.max_traces = max_traces
        self.traces: deque = deque(maxlen=max_traces)
        self._lock = threading.RLock()

    def start_trace(self, operation: str, module: str, context: Dict[str, Any] = None) -> str:
        """开始性能跟踪"""
        trace_id = f"{module}.{operation}.{int(time.time() * 1000000)}"
        # 这里可以使用更复杂的跟踪机制
        return trace_id

    def end_trace(self, trace_id: str, success: bool = True, error_message: str = None):
        """结束性能跟踪"""
        # 实际实现中需要从跟踪ID获取开始时间
        pass

    def record_trace(self, operation: str, module: str, start_time: float, end_time: float,
                    success: bool = True, error_message: str = None, context: Dict[str, Any] = None):
        """记录性能跟踪"""
        trace = PerformanceTrace(
            operation=operation,
            module=module,
            start_time=start_time,
            end_time=end_time,
            duration=end_time - start_time,
            success=success,
            error_message=error_message,
            context=context or {}
        )

        with self._lock:
            self.traces.append(trace)

    def get_traces(self, module: str = None, operation: str = None) -> List[PerformanceTrace]:
        """获取性能跟踪"""
        with self._lock:
            traces = list(self.traces)

            if module:
                traces = [t for t in traces if t.module == module]

            if operation:
                traces = [t for t in traces if t.operation == operation]

            return traces

    def get_performance_stats(self, module: str = None) -> Dict[str, Any]:
        """获取性能统计"""
        traces = self.get_traces(module)

        if not traces:
            return {}

        successful_traces = [t for t in traces if t.success]
        failed_traces = [t for t in traces if not t.success]

        durations = [t.duration for t in traces]
        successful_durations = [t.duration for t in successful_traces]

        stats = {
            'total_requests': len(traces),
            'successful_requests': len(successful_traces),
            'failed_requests': len(failed_traces),
            'success_rate': len(successful_traces) / len(traces) if traces else 0,
            'error_rate': len(failed_traces) / len(traces) if traces else 0
        }

        if durations:
            sorted_durations = sorted(durations)
            length = len(sorted_durations)

            stats.update({
                'avg_duration': sum(durations) / length,
                'min_duration': min(durations),
                'max_duration': max(durations),
                'p50_duration': sorted_durations[length // 2],
                'p90_duration': sorted_durations[int(length * 0.9)],
                'p95_duration': sorted_durations[int(length * 0.95)]
            })

        return stats

class SystemMonitor:
    """系统监控器"""

    def __init__(self):
        self.process = psutil.Process()
        self.start_time = time.time()

    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        try:
            # CPU使用率
            cpu_percent = self.process.cpu_percent()

            # 内存使用
            memory_info = self.process.memory_info()
            memory_percent = self.process.memory_percent()

            # 磁盘IO
            io_counters = self.process.io_counters() if hasattr(self.process, 'io_counters') else None

            # 线程数
            num_threads = self.process.num_threads()

            # 文件描述符
            num_fds = self.process.num_fds() if hasattr(self.process, 'num_fds') else 0

            return {
                'cpu_percent': cpu_percent,
                'memory_rss': memory_info.rss,
                'memory_vms': memory_info.vms,
                'memory_percent': memory_percent,
                'num_threads': num_threads,
                'num_fds': num_fds,
                'uptime': time.time() - self.start_time,
                'io_read_bytes': io_counters.read_bytes if io_counters else 0,
                'io_write_bytes': io_counters.write_bytes if io_counters else 0
            }
        except Exception as e:
            logger.error(f"获取系统指标失败: {e}")
            return {}

class MonitoringSystem:
    """监控系统主类"""

    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.performance_tracker = PerformanceTracker()
        self.system_monitor = SystemMonitor()
        self.agent_metrics: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self._monitoring_thread = None
        self._monitoring_active = False

    def start_monitoring(self, collection_interval: int = 30):
        """启动监控"""
        if self._monitoring_active:
            return

        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(collection_interval,),
            daemon=True
        )
        self._monitoring_thread.start()
        logger.info("监控系统已启动")

    def stop_monitoring(self):
        """停止监控"""
        self._monitoring_active = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
        logger.info("监控系统已停止")

    def _monitoring_loop(self, collection_interval: int):
        """监控循环"""
        while self._monitoring_active:
            try:
                self._collect_system_metrics()
                time.sleep(collection_interval)
            except Exception as e:
                logger.error(f"监控收集异常: {e}")

    def _collect_system_metrics(self):
        """收集系统指标"""
        system_metrics = self.system_monitor.get_system_metrics()

        for metric_name, value in system_metrics.items():
            self.metrics_collector.set_gauge(f"system.{metric_name}", value)

    def record_agent_execution(self, agent_name: str, operation: str,
                             duration: float, success: bool, context: Dict[str, Any] = None):
        """记录Agent执行"""
        # 更新指标
        labels = {'agent': agent_name, 'operation': operation}
        self.metrics_collector.increment_counter('agent.executions.total', labels=labels)

        if success:
            self.metrics_collector.increment_counter('agent.executions.success', labels=labels)
        else:
            self.metrics_collector.increment_counter('agent.executions.failure', labels=labels)

        self.metrics_collector.record_histogram('agent.execution.duration', duration, labels=labels)

        # 记录性能跟踪
        self.performance_tracker.record_trace(
            operation=operation,
            module=f"agent.{agent_name}",
            start_time=time.time() - duration,
            end_time=time.time(),
            success=success,
            context=context
        )

        # 更新Agent指标
        agent_key = f"{agent_name}.{operation}"
        if agent_key not in self.agent_metrics[agent_name]:
            self.agent_metrics[agent_name][agent_key] = {
                'total_executions': 0,
                'successful_executions': 0,
                'total_duration': 0.0,
                'avg_duration': 0.0
            }

        metrics = self.agent_metrics[agent_name][agent_key]
        metrics['total_executions'] += 1
        metrics['total_duration'] += duration
        metrics['avg_duration'] = metrics['total_duration'] / metrics['total_executions']

        if success:
            metrics['successful_executions'] += 1

    def get_dashboard_data(self) -> Dict[str, Any]:
        """获取仪表板数据"""
        # 系统指标
        system_metrics = self.system_monitor.get_system_metrics()

        # Agent统计
        total_agent_executions = sum(
            sum(ops.get('total_executions', 0) for ops in agent_ops.values())
            for agent_ops in self.agent_metrics.values()
        )

        successful_executions = sum(
            sum(ops.get('successful_executions', 0) for ops in agent_ops.values())
            for agent_ops in self.agent_metrics.values()
        )

        # 性能统计
        overall_perf = self.performance_tracker.get_performance_stats()

        return {
            'system': system_metrics,
            'agents': {
                'total_executions': total_agent_executions,
                'success_rate': successful_executions / total_agent_executions if total_agent_executions > 0 else 0,
                'agent_details': dict(self.agent_metrics)
            },
            'performance': overall_perf,
            'monitoring_status': {
                'active': self._monitoring_active,
                'uptime': time.time() - self.system_monitor.start_time
            }
        }

    def export_metrics(self, format: str = 'json') -> str:
        """导出指标"""
        data = self.get_dashboard_data()

        if format == 'json':
            return json.dumps(data, indent=2, default=str)
        elif format == 'prometheus':
            # 简单的Prometheus格式导出
            lines = []
            for metric in self.metrics_collector.get_metrics():
                labels_str = ",".join(f'{k}="{v}"' for k, v in metric.labels.items())
                labels_part = f"{{{labels_str}}}" if labels_str else ""
                lines.append(f"{metric.name}{labels_part} {metric.value}")
            return "\n".join(lines)
        else:
            raise ValueError(f"不支持的导出格式: {format}")

# 全局监控系统
monitoring_system = MonitoringSystem()

def setup_perfect21_monitoring():
    """设置Perfect21监控"""
    # 启动监控
    monitoring_system.start_monitoring()

    # 设置基础指标
    monitoring_system.metrics_collector.set_gauge('perfect21.version', 2.3)
    monitoring_system.metrics_collector.increment_counter('perfect21.startup')

    logger.info("Perfect21监控系统设置完成")

def time_execution(func):
    """执行时间装饰器"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            success = True
            return result
        except Exception as e:
            success = False
            raise
        finally:
            end_time = time.time()
            duration = end_time - start_time

            # 记录性能指标
            module_name = func.__module__ if hasattr(func, '__module__') else 'unknown'
            operation_name = func.__name__

            monitoring_system.performance_tracker.record_trace(
                operation=operation_name,
                module=module_name,
                start_time=start_time,
                end_time=end_time,
                success=success
            )

            monitoring_system.metrics_collector.record_histogram(
                'function.execution.duration',
                duration,
                labels={'module': module_name, 'function': operation_name}
            )

    return wrapper

if __name__ == "__main__":
    # 测试监控系统
    setup_perfect21_monitoring()
    time.sleep(2)
    dashboard = monitoring_system.get_dashboard_data()
    print("监控仪表板数据:", json.dumps(dashboard, indent=2, default=str))