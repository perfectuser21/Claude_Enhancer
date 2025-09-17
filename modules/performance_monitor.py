#!/usr/bin/env python3
"""
Perfect21性能监控器
实时监控系统性能，自动优化和告警
"""

import os
import sys
import time
import psutil
import threading
import asyncio
import json
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque, defaultdict
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.logger import log_info, log_error
from modules.config import config

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """性能指标"""
    name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PerformanceAlert:
    """性能告警"""
    metric_name: str
    alert_type: str  # warning, critical
    current_value: float
    threshold: float
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False

class PerformanceCollector:
    """性能数据收集器"""

    def __init__(self):
        self.process = psutil.Process()
        self.start_time = time.time()
        self.boot_time = psutil.boot_time()

    def collect_system_metrics(self) -> Dict[str, PerformanceMetric]:
        """收集系统级性能指标"""
        metrics = {}

        try:
            # CPU指标
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics['cpu_usage'] = PerformanceMetric(
                'cpu_usage', cpu_percent, '%',
                threshold_warning=70.0, threshold_critical=90.0
            )

            cpu_count = psutil.cpu_count()
            metrics['cpu_count'] = PerformanceMetric('cpu_count', cpu_count, 'cores')

            # 内存指标
            memory = psutil.virtual_memory()
            metrics['memory_usage'] = PerformanceMetric(
                'memory_usage', memory.percent, '%',
                threshold_warning=80.0, threshold_critical=95.0
            )
            metrics['memory_available'] = PerformanceMetric(
                'memory_available', memory.available / 1024 / 1024, 'MB'
            )
            metrics['memory_total'] = PerformanceMetric(
                'memory_total', memory.total / 1024 / 1024, 'MB'
            )

            # 磁盘指标
            disk = psutil.disk_usage('/')
            metrics['disk_usage'] = PerformanceMetric(
                'disk_usage', disk.percent, '%',
                threshold_warning=80.0, threshold_critical=95.0
            )
            metrics['disk_free'] = PerformanceMetric(
                'disk_free', disk.free / 1024 / 1024 / 1024, 'GB'
            )

            # 网络指标
            network = psutil.net_io_counters()
            metrics['network_bytes_sent'] = PerformanceMetric(
                'network_bytes_sent', network.bytes_sent, 'bytes'
            )
            metrics['network_bytes_recv'] = PerformanceMetric(
                'network_bytes_recv', network.bytes_recv, 'bytes'
            )

            # 系统负载
            if hasattr(os, 'getloadavg'):
                load_avg = os.getloadavg()
                metrics['load_avg_1min'] = PerformanceMetric(
                    'load_avg_1min', load_avg[0], 'load',
                    threshold_warning=float(cpu_count), threshold_critical=float(cpu_count * 2)
                )

        except Exception as e:
            logger.error(f"收集系统指标失败: {e}")

        return metrics

    def collect_process_metrics(self) -> Dict[str, PerformanceMetric]:
        """收集进程级性能指标"""
        metrics = {}

        try:
            # CPU使用率
            cpu_percent = self.process.cpu_percent()
            metrics['process_cpu_usage'] = PerformanceMetric(
                'process_cpu_usage', cpu_percent, '%',
                threshold_warning=50.0, threshold_critical=80.0
            )

            # 内存使用
            memory_info = self.process.memory_info()
            metrics['process_memory_rss'] = PerformanceMetric(
                'process_memory_rss', memory_info.rss / 1024 / 1024, 'MB',
                threshold_warning=512.0, threshold_critical=1024.0
            )
            metrics['process_memory_vms'] = PerformanceMetric(
                'process_memory_vms', memory_info.vms / 1024 / 1024, 'MB'
            )

            # 内存百分比
            memory_percent = self.process.memory_percent()
            metrics['process_memory_percent'] = PerformanceMetric(
                'process_memory_percent', memory_percent, '%',
                threshold_warning=10.0, threshold_critical=20.0
            )

            # 文件描述符
            num_fds = self.process.num_fds() if hasattr(self.process, 'num_fds') else 0
            metrics['process_file_descriptors'] = PerformanceMetric(
                'process_file_descriptors', num_fds, 'count',
                threshold_warning=500, threshold_critical=800
            )

            # 线程数
            num_threads = self.process.num_threads()
            metrics['process_threads'] = PerformanceMetric(
                'process_threads', num_threads, 'count',
                threshold_warning=50, threshold_critical=100
            )

            # 运行时间
            runtime = time.time() - self.start_time
            metrics['process_runtime'] = PerformanceMetric(
                'process_runtime', runtime, 'seconds'
            )

            # IO统计
            io_counters = self.process.io_counters()
            metrics['process_io_read_bytes'] = PerformanceMetric(
                'process_io_read_bytes', io_counters.read_bytes, 'bytes'
            )
            metrics['process_io_write_bytes'] = PerformanceMetric(
                'process_io_write_bytes', io_counters.write_bytes, 'bytes'
            )

        except Exception as e:
            logger.error(f"收集进程指标失败: {e}")

        return metrics

    def collect_custom_metrics(self) -> Dict[str, PerformanceMetric]:
        """收集自定义性能指标"""
        metrics = {}

        try:
            # Perfect21特定指标
            from modules.performance_cache import performance_cache
            cache_stats = performance_cache.get_performance_stats()

            if 'cache_hit_rate' in cache_stats:
                hit_rate = float(cache_stats['cache_hit_rate'].rstrip('%'))
                metrics['cache_hit_rate'] = PerformanceMetric(
                    'cache_hit_rate', hit_rate, '%',
                    threshold_warning=70.0  # 低于70%发出警告
                )

            if 'memory_usage_mb' in cache_stats:
                metrics['cache_memory_usage'] = PerformanceMetric(
                    'cache_memory_usage', cache_stats['memory_usage_mb'], 'MB',
                    threshold_warning=100.0, threshold_critical=200.0
                )

            # Git缓存指标
            from modules.git_cache import get_cache_stats
            git_stats = get_cache_stats()

            for cache_key, stats in git_stats.items():
                if 'hit_rate' in stats:
                    hit_rate = float(stats['hit_rate'].rstrip('%'))
                    metrics[f'git_cache_hit_rate_{cache_key}'] = PerformanceMetric(
                        f'git_cache_hit_rate_{cache_key}', hit_rate, '%'
                    )

            # 连接池指标
            try:
                from modules.connection_pool import connection_pool_manager
                pool_stats = connection_pool_manager.get_all_stats()

                for pool_name, stats in pool_stats.items():
                    if 'current_size' in stats and 'max_size' in stats:
                        utilization = (stats['current_size'] / stats['max_size']) * 100
                        metrics[f'pool_utilization_{pool_name}'] = PerformanceMetric(
                            f'pool_utilization_{pool_name}', utilization, '%',
                            threshold_warning=80.0, threshold_critical=95.0
                        )
            except ImportError:
                pass

        except Exception as e:
            logger.error(f"收集自定义指标失败: {e}")

        return metrics

class PerformanceMonitor:
    """性能监控器"""

    def __init__(self, collection_interval: int = 60):
        self.collection_interval = collection_interval
        self.collector = PerformanceCollector()

        # 数据存储
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.alerts: List[PerformanceAlert] = []
        self.alert_callbacks: List[Callable] = []

        # 监控状态
        self.monitoring = False
        self.monitor_thread = None
        self.async_monitor_task = None

        # 性能基线
        self.baselines: Dict[str, float] = {}
        self.baseline_window = 100  # 前100个数据点作为基线

        # 统计信息
        self.stats = {
            'total_collections': 0,
            'failed_collections': 0,
            'alerts_generated': 0,
            'last_collection': None
        }

        log_info("性能监控器初始化完成")

    def start_monitoring(self):
        """启动性能监控"""
        if self.monitoring:
            return

        self.monitoring = True

        # 启动同步监控线程
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

        log_info(f"性能监控已启动，采集间隔: {self.collection_interval}秒")

    async def start_async_monitoring(self):
        """启动异步性能监控"""
        if self.monitoring:
            return

        self.monitoring = True
        self.async_monitor_task = asyncio.create_task(self._async_monitor_loop())

        log_info(f"异步性能监控已启动，采集间隔: {self.collection_interval}秒")

    def stop_monitoring(self):
        """停止性能监控"""
        self.monitoring = False

        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)

        if self.async_monitor_task and not self.async_monitor_task.done():
            self.async_monitor_task.cancel()

        log_info("性能监控已停止")

    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                self._collect_and_process_metrics()
                time.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"监控循环异常: {e}")
                self.stats['failed_collections'] += 1

    async def _async_monitor_loop(self):
        """异步监控循环"""
        while self.monitoring:
            try:
                await self._async_collect_and_process_metrics()
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"异步监控循环异常: {e}")
                self.stats['failed_collections'] += 1

    def _collect_and_process_metrics(self):
        """收集和处理指标"""
        try:
            # 收集所有指标
            all_metrics = {}
            all_metrics.update(self.collector.collect_system_metrics())
            all_metrics.update(self.collector.collect_process_metrics())
            all_metrics.update(self.collector.collect_custom_metrics())

            # 处理指标
            self._process_metrics(all_metrics)

            self.stats['total_collections'] += 1
            self.stats['last_collection'] = datetime.now()

        except Exception as e:
            logger.error(f"收集处理指标失败: {e}")
            self.stats['failed_collections'] += 1

    async def _async_collect_and_process_metrics(self):
        """异步收集和处理指标"""
        try:
            # 收集所有指标（在线程池中执行避免阻塞）
            loop = asyncio.get_event_loop()

            system_metrics = await loop.run_in_executor(None, self.collector.collect_system_metrics)
            process_metrics = await loop.run_in_executor(None, self.collector.collect_process_metrics)
            custom_metrics = await loop.run_in_executor(None, self.collector.collect_custom_metrics)

            all_metrics = {}
            all_metrics.update(system_metrics)
            all_metrics.update(process_metrics)
            all_metrics.update(custom_metrics)

            # 处理指标
            await loop.run_in_executor(None, self._process_metrics, all_metrics)

            self.stats['total_collections'] += 1
            self.stats['last_collection'] = datetime.now()

        except Exception as e:
            logger.error(f"异步收集处理指标失败: {e}")
            self.stats['failed_collections'] += 1

    def _process_metrics(self, metrics: Dict[str, PerformanceMetric]):
        """处理指标数据"""
        for name, metric in metrics.items():
            # 存储历史数据
            self.metrics_history[name].append(metric)

            # 检查告警条件
            self._check_alert_conditions(metric)

            # 更新基线
            self._update_baseline(name, metric.value)

    def _check_alert_conditions(self, metric: PerformanceMetric):
        """检查告警条件"""
        alerts_to_create = []

        # 检查阈值告警
        if metric.threshold_critical and metric.value >= metric.threshold_critical:
            alerts_to_create.append(PerformanceAlert(
                metric_name=metric.name,
                alert_type='critical',
                current_value=metric.value,
                threshold=metric.threshold_critical,
                message=f"{metric.name} 达到临界值: {metric.value}{metric.unit} >= {metric.threshold_critical}{metric.unit}"
            ))
        elif metric.threshold_warning and metric.value >= metric.threshold_warning:
            alerts_to_create.append(PerformanceAlert(
                metric_name=metric.name,
                alert_type='warning',
                current_value=metric.value,
                threshold=metric.threshold_warning,
                message=f"{metric.name} 达到警告值: {metric.value}{metric.unit} >= {metric.threshold_warning}{metric.unit}"
            ))

        # 检查趋势告警
        trend_alert = self._check_trend_alert(metric)
        if trend_alert:
            alerts_to_create.append(trend_alert)

        # 添加告警并触发回调
        for alert in alerts_to_create:
            self.alerts.append(alert)
            self.stats['alerts_generated'] += 1

            # 触发告警回调
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    logger.error(f"告警回调执行失败: {e}")

    def _check_trend_alert(self, metric: PerformanceMetric) -> Optional[PerformanceAlert]:
        """检查趋势告警"""
        history = self.metrics_history[metric.name]
        if len(history) < 10:  # 至少需要10个数据点
            return None

        # 计算最近10个点的趋势
        recent_values = [m.value for m in list(history)[-10:]]
        trend_slope = self._calculate_trend_slope(recent_values)

        # 检查异常增长趋势
        baseline = self.baselines.get(metric.name, 0)
        if baseline > 0:
            growth_rate = trend_slope / baseline
            if growth_rate > 0.5:  # 增长率超过50%
                return PerformanceAlert(
                    metric_name=metric.name,
                    alert_type='warning',
                    current_value=metric.value,
                    threshold=baseline,
                    message=f"{metric.name} 异常增长趋势: 增长率 {growth_rate:.1%}"
                )

        return None

    def _calculate_trend_slope(self, values: List[float]) -> float:
        """计算趋势斜率"""
        if len(values) < 2:
            return 0.0

        n = len(values)
        x = list(range(n))
        y = values

        # 使用最小二乘法计算斜率
        x_mean = sum(x) / n
        y_mean = sum(y) / n

        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))

        return numerator / denominator if denominator != 0 else 0.0

    def _update_baseline(self, metric_name: str, value: float):
        """更新性能基线"""
        history = self.metrics_history[metric_name]
        if len(history) >= self.baseline_window:
            # 使用前N个数据点的平均值作为基线
            baseline_values = [m.value for m in list(history)[:self.baseline_window]]
            self.baselines[metric_name] = sum(baseline_values) / len(baseline_values)

    def add_alert_callback(self, callback: Callable[[PerformanceAlert], None]):
        """添加告警回调"""
        self.alert_callbacks.append(callback)

    def get_current_metrics(self) -> Dict[str, PerformanceMetric]:
        """获取当前指标"""
        current_metrics = {}
        for name, history in self.metrics_history.items():
            if history:
                current_metrics[name] = history[-1]
        return current_metrics

    def get_metric_history(self, metric_name: str, hours: int = 1) -> List[PerformanceMetric]:
        """获取指标历史数据"""
        if metric_name not in self.metrics_history:
            return []

        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            metric for metric in self.metrics_history[metric_name]
            if metric.timestamp >= cutoff_time
        ]

    def get_active_alerts(self) -> List[PerformanceAlert]:
        """获取活跃告警"""
        return [alert for alert in self.alerts if not alert.resolved]

    def resolve_alert(self, alert_id: str):
        """解决告警"""
        for alert in self.alerts:
            if str(id(alert)) == alert_id:
                alert.resolved = True
                break

    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        current_metrics = self.get_current_metrics()
        active_alerts = self.get_active_alerts()

        # 计算健康分数
        health_score = self._calculate_health_score(current_metrics, active_alerts)

        return {
            'health_score': health_score,
            'total_metrics': len(current_metrics),
            'active_alerts': len(active_alerts),
            'critical_alerts': len([a for a in active_alerts if a.alert_type == 'critical']),
            'warning_alerts': len([a for a in active_alerts if a.alert_type == 'warning']),
            'monitoring_status': 'active' if self.monitoring else 'stopped',
            'collection_stats': self.stats,
            'key_metrics': self._get_key_metrics_summary(current_metrics)
        }

    def _calculate_health_score(self, metrics: Dict[str, PerformanceMetric],
                               alerts: List[PerformanceAlert]) -> float:
        """计算系统健康分数"""
        base_score = 100.0

        # 根据告警扣分
        for alert in alerts:
            if alert.alert_type == 'critical':
                base_score -= 20
            elif alert.alert_type == 'warning':
                base_score -= 10

        # 根据关键指标扣分
        key_metrics = ['cpu_usage', 'memory_usage', 'disk_usage']
        for metric_name in key_metrics:
            if metric_name in metrics:
                metric = metrics[metric_name]
                if metric.threshold_critical and metric.value >= metric.threshold_critical:
                    base_score -= 15
                elif metric.threshold_warning and metric.value >= metric.threshold_warning:
                    base_score -= 5

        return max(0.0, min(100.0, base_score))

    def _get_key_metrics_summary(self, metrics: Dict[str, PerformanceMetric]) -> Dict[str, Any]:
        """获取关键指标摘要"""
        key_metrics = {}

        important_metrics = [
            'cpu_usage', 'memory_usage', 'disk_usage',
            'process_cpu_usage', 'process_memory_rss',
            'cache_hit_rate'
        ]

        for metric_name in important_metrics:
            if metric_name in metrics:
                metric = metrics[metric_name]
                key_metrics[metric_name] = {
                    'value': metric.value,
                    'unit': metric.unit,
                    'status': self._get_metric_status(metric)
                }

        return key_metrics

    def _get_metric_status(self, metric: PerformanceMetric) -> str:
        """获取指标状态"""
        if metric.threshold_critical and metric.value >= metric.threshold_critical:
            return 'critical'
        elif metric.threshold_warning and metric.value >= metric.threshold_warning:
            return 'warning'
        else:
            return 'normal'

    def export_metrics(self, format: str = 'json', time_range_hours: int = 1) -> str:
        """导出指标数据"""
        export_data = {}

        for metric_name, history in self.metrics_history.items():
            recent_data = self.get_metric_history(metric_name, time_range_hours)
            if recent_data:
                export_data[metric_name] = [
                    {
                        'timestamp': metric.timestamp.isoformat(),
                        'value': metric.value,
                        'unit': metric.unit
                    }
                    for metric in recent_data
                ]

        if format == 'json':
            return json.dumps(export_data, indent=2)
        else:
            raise ValueError(f"不支持的导出格式: {format}")

# 全局性能监控器实例
performance_monitor = PerformanceMonitor(
    collection_interval=config.get('performance.monitor_interval', 60)
)

# 便捷函数
def start_performance_monitoring():
    """启动性能监控"""
    performance_monitor.start_monitoring()

def stop_performance_monitoring():
    """停止性能监控"""
    performance_monitor.stop_monitoring()

def get_performance_summary():
    """获取性能摘要"""
    return performance_monitor.get_performance_summary()

def add_performance_alert_handler(handler: Callable):
    """添加性能告警处理器"""
    performance_monitor.add_alert_callback(handler)

# 默认告警处理器
def default_alert_handler(alert: PerformanceAlert):
    """默认告警处理器"""
    if alert.alert_type == 'critical':
        log_error(f"CRITICAL ALERT: {alert.message}")
    else:
        logger.warning(f"WARNING ALERT: {alert.message}")

# 注册默认告警处理器
add_performance_alert_handler(default_alert_handler)