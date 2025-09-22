"""
Performance Optimization: Metrics Collector
指标收集器 - 企业级性能监控与指标收集系统
"""

import asyncio
import time
import psutil
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from collections import defaultdict, deque
import aiofiles
import threading
from contextlib import asynccontextmanager
import weakref

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """指标类型"""
    COUNTER = "counter"          # 计数器（只增不减）
    GAUGE = "gauge"             # 仪表（可增可减的瞬时值）
    HISTOGRAM = "histogram"     # 直方图（分布统计）
    SUMMARY = "summary"         # 摘要（分位数统计）
    TIMER = "timer"            # 计时器（特殊的直方图）

class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class Metric:
    """指标数据结构"""
    name: str
    value: float
    metric_type: MetricType
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    unit: str = ""
    help_text: str = ""

@dataclass
class Alert:
    """告警数据结构"""
    id: str
    name: str
    level: AlertLevel
    message: str
    metric_name: str
    threshold: float
    current_value: float
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolved_at: Optional[datetime] = None

@dataclass
class MetricsConfig:
    """指标收集器配置"""
    collection_interval: float = 10.0  # 10秒
    retention_period: timedelta = timedelta(hours=24)  # 24小时
    max_metrics_per_type: int = 10000
    enable_system_metrics: bool = True
    enable_application_metrics: bool = True
    enable_business_metrics: bool = True
    alert_check_interval: float = 30.0  # 30秒
    export_interval: float = 60.0  # 1分钟
    export_format: str = "prometheus"  # prometheus, json
    export_file: Optional[str] = "/tmp/metrics.txt"

class MetricsCollector:
    """指标收集器 - 企业级性能监控系统"""

    def __init__(self, service_name: str, config: MetricsConfig = None):
        self.service_name = service_name
        self.config = config or MetricsConfig()

        # 指标存储
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.timers: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

        # 历史数据存储
        self.metrics_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=int(self.config.retention_period.total_seconds() / self.config.collection_interval))
        )

        # 告警
        self.alerts: Dict[str, Alert] = {}
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        self.alert_handlers: List[Callable] = []

        # 统计信息
        self.stats = {
            'total_metrics_collected': 0,
            'active_alerts': 0,
            'system_uptime': time.time(),
            'last_collection_time': None,
            'collection_errors': 0
        }

        # 控制标志
        self.running = False
        self._lock = asyncio.Lock()

        # 系统资源监控
        self.process = psutil.Process()

    async def initialize(self):
        """初始化指标收集器"""
        try:
            self.running = True

            # 启动收集任务
            asyncio.create_task(self._collection_loop())
            asyncio.create_task(self._alert_check_loop())
            asyncio.create_task(self._export_loop())
            asyncio.create_task(self._cleanup_loop())

            # 注册系统指标
            if self.config.enable_system_metrics:
                await self._register_system_metrics()

            logger.info(f"✅ 指标收集器初始化成功 - 服务: {self.service_name}")

        except Exception as e:
            logger.error(f"❌ 指标收集器初始化失败: {e}")
            raise

    async def _register_system_metrics(self):
        """注册系统指标"""
        # CPU使用率
        self.add_alert_rule(
            "cpu_usage_high",
            metric_name="system_cpu_percent",
            threshold=80.0,
            level=AlertLevel.WARNING,
            message="CPU使用率过高"
        )

        # 内存使用率
        self.add_alert_rule(
            "memory_usage_high",
            metric_name="system_memory_percent",
            threshold=85.0,
            level=AlertLevel.ERROR,
            message="内存使用率过高"
        )

        # 磁盘使用率
        self.add_alert_rule(
            "disk_usage_high",
            metric_name="system_disk_percent",
            threshold=90.0,
            level=AlertLevel.CRITICAL,
            message="磁盘使用率过高"
        )

    def increment_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] = None):
        """递增计数器"""
        key = self._make_key(name, labels)
        self.counters[key] += value
        self._record_metric(name, self.counters[key], MetricType.COUNTER, labels)

    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None):
        """设置仪表值"""
        key = self._make_key(name, labels)
        self.gauges[key] = value
        self._record_metric(name, value, MetricType.GAUGE, labels)

    def observe_histogram(self, name: str, value: float, labels: Dict[str, str] = None):
        """观察直方图值"""
        key = self._make_key(name, labels)
        self.histograms[key].append(value)

        # 限制历史数据数量
        if len(self.histograms[key]) > 1000:
            self.histograms[key] = self.histograms[key][-1000:]

        self._record_metric(name, value, MetricType.HISTOGRAM, labels)

    def time_function(self, name: str, labels: Dict[str, str] = None):
        """函数执行时间装饰器"""
        def decorator(func):
            if asyncio.iscoroutinefunction(func):
                async def async_wrapper(*args, **kwargs):
                    start_time = time.time()
                    try:
                        result = await func(*args, **kwargs)
                        return result
                    finally:
                        duration = time.time() - start_time
                        self.record_timer(name, duration, labels)
                return async_wrapper
            else:
                def sync_wrapper(*args, **kwargs):
                    start_time = time.time()
                    try:
                        result = func(*args, **kwargs)
                        return result
                    finally:
                        duration = time.time() - start_time
                        self.record_timer(name, duration, labels)
                return sync_wrapper
        return decorator

    def record_timer(self, name: str, duration: float, labels: Dict[str, str] = None):
        """记录计时器"""
        key = self._make_key(name, labels)
        self.timers[key].append(duration)
        self._record_metric(name, duration, MetricType.TIMER, labels)

    @asynccontextmanager
    async def timer_context(self, name: str, labels: Dict[str, str] = None):
        """计时器上下文管理器"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.record_timer(name, duration, labels)

    def _make_key(self, name: str, labels: Dict[str, str] = None) -> str:
        """生成指标键"""
        if not labels:
            return name

        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def _record_metric(self, name: str, value: float, metric_type: MetricType,
                      labels: Dict[str, str] = None):
        """记录指标到历史数据"""
        key = self._make_key(name, labels)
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            labels=labels or {},
            timestamp=datetime.now()
        )

        self.metrics_history[key].append(metric)
        self.stats['total_metrics_collected'] += 1

    async def _collection_loop(self):
        """指标收集循环"""
        while self.running:
            try:
                await self._collect_system_metrics()
                await self._collect_application_metrics()

                self.stats['last_collection_time'] = datetime.now()

            except Exception as e:
                logger.error(f"❌ 指标收集失败: {e}")
                self.stats['collection_errors'] += 1

            await asyncio.sleep(self.config.collection_interval)

    async def _collect_system_metrics(self):
        """收集系统指标"""
        if not self.config.enable_system_metrics:
            return

        try:
            # CPU指标
            cpu_percent = psutil.cpu_percent(interval=None)
            self.set_gauge("system_cpu_percent", cpu_percent)

            cpu_count = psutil.cpu_count()
            self.set_gauge("system_cpu_count", cpu_count)

            # 内存指标
            memory = psutil.virtual_memory()
            self.set_gauge("system_memory_total", memory.total)
            self.set_gauge("system_memory_used", memory.used)
            self.set_gauge("system_memory_percent", memory.percent)
            self.set_gauge("system_memory_available", memory.available)

            # 磁盘指标
            disk = psutil.disk_usage('/')
            self.set_gauge("system_disk_total", disk.total)
            self.set_gauge("system_disk_used", disk.used)
            self.set_gauge("system_disk_percent", disk.used / disk.total * 100)

            # 网络指标
            network = psutil.net_io_counters()
            self.increment_counter("system_network_bytes_sent", network.bytes_sent)
            self.increment_counter("system_network_bytes_recv", network.bytes_recv)
            self.increment_counter("system_network_packets_sent", network.packets_sent)
            self.increment_counter("system_network_packets_recv", network.packets_recv)

            # 进程指标
            process_memory = self.process.memory_info()
            self.set_gauge("process_memory_rss", process_memory.rss)
            self.set_gauge("process_memory_vms", process_memory.vms)
            self.set_gauge("process_cpu_percent", self.process.cpu_percent())
            self.set_gauge("process_threads", self.process.num_threads())

            # 文件描述符
            try:
                self.set_gauge("process_open_fds", self.process.num_fds())
            except:
                pass  # Windows不支持

        except Exception as e:
            logger.error(f"❌ 系统指标收集失败: {e}")

    async def _collect_application_metrics(self):
        """收集应用指标"""
        if not self.config.enable_application_metrics:
            return

        try:
            # 服务运行时间
            uptime = time.time() - self.stats['system_uptime']
            self.set_gauge("service_uptime_seconds", uptime)

            # 指标统计
            self.set_gauge("metrics_total_collected", self.stats['total_metrics_collected'])
            self.set_gauge("metrics_collection_errors", self.stats['collection_errors'])
            self.set_gauge("alerts_active", len([a for a in self.alerts.values() if not a.resolved]))

            # 队列长度统计
            self.set_gauge("metrics_counters_count", len(self.counters))
            self.set_gauge("metrics_gauges_count", len(self.gauges))
            self.set_gauge("metrics_histograms_count", len(self.histograms))
            self.set_gauge("metrics_timers_count", len(self.timers))

        except Exception as e:
            logger.error(f"❌ 应用指标收集失败: {e}")

    def add_alert_rule(self, rule_id: str, metric_name: str, threshold: float,
                      level: AlertLevel = AlertLevel.WARNING,
                      message: str = "", operator: str = "gt"):
        """添加告警规则"""
        self.alert_rules[rule_id] = {
            'metric_name': metric_name,
            'threshold': threshold,
            'level': level,
            'message': message,
            'operator': operator  # gt, lt, eq, gte, lte
        }

        logger.info(f"📋 添加告警规则: {rule_id} - {metric_name} {operator} {threshold}")

    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """添加告警处理器"""
        self.alert_handlers.append(handler)

    async def _alert_check_loop(self):
        """告警检查循环"""
        while self.running:
            try:
                await self._check_alerts()
            except Exception as e:
                logger.error(f"❌ 告警检查失败: {e}")

            await asyncio.sleep(self.config.alert_check_interval)

    async def _check_alerts(self):
        """检查告警条件"""
        for rule_id, rule in self.alert_rules.items():
            metric_name = rule['metric_name']
            threshold = rule['threshold']
            operator = rule['operator']

            # 获取当前指标值
            current_value = None
            for key, value in self.gauges.items():
                if key.startswith(metric_name):
                    current_value = value
                    break

            if current_value is None:
                continue

            # 检查告警条件
            alert_triggered = False
            if operator == "gt" and current_value > threshold:
                alert_triggered = True
            elif operator == "lt" and current_value < threshold:
                alert_triggered = True
            elif operator == "eq" and current_value == threshold:
                alert_triggered = True
            elif operator == "gte" and current_value >= threshold:
                alert_triggered = True
            elif operator == "lte" and current_value <= threshold:
                alert_triggered = True

            # 处理告警
            if alert_triggered:
                if rule_id not in self.alerts or self.alerts[rule_id].resolved:
                    # 新告警
                    alert = Alert(
                        id=rule_id,
                        name=rule_id,
                        level=rule['level'],
                        message=rule['message'] or f"{metric_name} {operator} {threshold}",
                        metric_name=metric_name,
                        threshold=threshold,
                        current_value=current_value
                    )

                    self.alerts[rule_id] = alert
                    await self._trigger_alert(alert)

            else:
                # 告警恢复
                if rule_id in self.alerts and not self.alerts[rule_id].resolved:
                    self.alerts[rule_id].resolved = True
                    self.alerts[rule_id].resolved_at = datetime.now()
                    await self._resolve_alert(self.alerts[rule_id])

    async def _trigger_alert(self, alert: Alert):
        """触发告警"""
        logger.warning(f"🚨 告警触发: {alert.name} - {alert.message} (当前值: {alert.current_value})")

        # 调用告警处理器
        for handler in self.alert_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(alert)
                else:
                    handler(alert)
            except Exception as e:
                logger.error(f"❌ 告警处理器失败: {e}")

    async def _resolve_alert(self, alert: Alert):
        """解决告警"""
        logger.info(f"✅ 告警恢复: {alert.name}")

        # 可以在这里发送恢复通知

    async def _export_loop(self):
        """指标导出循环"""
        while self.running:
            try:
                await self._export_metrics()
            except Exception as e:
                logger.error(f"❌ 指标导出失败: {e}")

            await asyncio.sleep(self.config.export_interval)

    async def _export_metrics(self):
        """导出指标"""
        if not self.config.export_file:
            return

        try:
            if self.config.export_format == "prometheus":
                content = await self._generate_prometheus_format()
            else:
                content = await self._generate_json_format()

            async with aiofiles.open(self.config.export_file, 'w') as f:
                await f.write(content)

        except Exception as e:
            logger.error(f"❌ 导出指标到文件失败: {e}")

    async def _generate_prometheus_format(self) -> str:
        """生成Prometheus格式的指标"""
        lines = []

        # 计数器
        for key, value in self.counters.items():
            name, labels = self._parse_key(key)
            labels_str = self._format_prometheus_labels(labels)
            lines.append(f'# TYPE {name} counter')
            lines.append(f'{name}{labels_str} {value}')

        # 仪表
        for key, value in self.gauges.items():
            name, labels = self._parse_key(key)
            labels_str = self._format_prometheus_labels(labels)
            lines.append(f'# TYPE {name} gauge')
            lines.append(f'{name}{labels_str} {value}')

        # 直方图摘要
        for key, values in self.histograms.items():
            if not values:
                continue

            name, labels = self._parse_key(key)
            labels_str = self._format_prometheus_labels(labels)

            sorted_values = sorted(values)
            count = len(sorted_values)
            total = sum(sorted_values)

            lines.append(f'# TYPE {name} histogram')
            lines.append(f'{name}_count{labels_str} {count}')
            lines.append(f'{name}_sum{labels_str} {total}')

            # 分位数
            percentiles = [0.5, 0.95, 0.99]
            for p in percentiles:
                index = int(count * p)
                if index < count:
                    value = sorted_values[index]
                    labels_with_quantile = {**labels, 'quantile': str(p)}
                    labels_str = self._format_prometheus_labels(labels_with_quantile)
                    lines.append(f'{name}{labels_str} {value}')

        return '\n'.join(lines) + '\n'

    async def _generate_json_format(self) -> str:
        """生成JSON格式的指标"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'service': self.service_name,
            'counters': dict(self.counters),
            'gauges': dict(self.gauges),
            'histograms': {k: list(v) for k, v in self.histograms.items()},
            'timers': {k: list(v) for k, v in self.timers.items()},
            'stats': self.stats.copy(),
            'alerts': {k: {
                'id': v.id,
                'name': v.name,
                'level': v.level.value,
                'message': v.message,
                'resolved': v.resolved,
                'timestamp': v.timestamp.isoformat()
            } for k, v in self.alerts.items()}
        }

        return json.dumps(data, indent=2, default=str)

    def _parse_key(self, key: str) -> Tuple[str, Dict[str, str]]:
        """解析指标键"""
        if '{' not in key:
            return key, {}

        name, labels_str = key.split('{', 1)
        labels_str = labels_str.rstrip('}')

        labels = {}
        if labels_str:
            for label_pair in labels_str.split(','):
                k, v = label_pair.split('=', 1)
                labels[k] = v

        return name, labels

    def _format_prometheus_labels(self, labels: Dict[str, str]) -> str:
        """格式化Prometheus标签"""
        if not labels:
            return ''

        label_pairs = [f'{k}="{v}"' for k, v in sorted(labels.items())]
        return '{' + ','.join(label_pairs) + '}'

    async def _cleanup_loop(self):
        """清理循环"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # 每小时清理一次

                # 清理过期的历史数据
                cutoff_time = datetime.now() - self.config.retention_period

                for key, history in self.metrics_history.items():
                    # 移除过期数据
                    while history and history[0].timestamp < cutoff_time:
                        history.popleft()

                # 清理已解决的旧告警
                resolved_alerts = [
                    alert_id for alert_id, alert in self.alerts.items()
                    if alert.resolved and alert.resolved_at and
                    datetime.now() - alert.resolved_at > timedelta(hours=24)
                ]

                for alert_id in resolved_alerts:
                    del self.alerts[alert_id]

                if resolved_alerts:
                    logger.info(f"🧹 清理已解决告警: {len(resolved_alerts)}个")

            except Exception as e:
                logger.error(f"❌ 清理任务失败: {e}")

    async def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        return {
            'service': self.service_name,
            'stats': self.stats.copy(),
            'counters_count': len(self.counters),
            'gauges_count': len(self.gauges),
            'histograms_count': len(self.histograms),
            'timers_count': len(self.timers),
            'active_alerts': len([a for a in self.alerts.values() if not a.resolved]),
            'total_alerts': len(self.alerts),
            'uptime_seconds': time.time() - self.stats['system_uptime']
        }

    async def health_check(self) -> bool:
        """健康检查"""
        return self.running and self.stats['last_collection_time'] is not None

    async def shutdown(self):
        """关闭指标收集器"""
        logger.info("🛑 正在关闭指标收集器...")
        self.running = False

        # 最后一次导出
        try:
            await self._export_metrics()
        except Exception as e:
            logger.error(f"❌ 最终导出失败: {e}")

        logger.info("✅ 指标收集器已关闭")

# 告警处理器示例
async def email_alert_handler(alert: Alert):
    """邮件告警处理器"""
    logger.info(f"📧 发送告警邮件: {alert.name} - {alert.message}")
    # 这里实现邮件发送逻辑

def slack_alert_handler(alert: Alert):
    """Slack告警处理器"""
    logger.info(f"💬 发送Slack告警: {alert.name} - {alert.message}")
    # 这里实现Slack消息发送逻辑

# 使用示例
async def example_usage():
    """指标收集器使用示例"""
    config = MetricsConfig(
        collection_interval=5.0,
        enable_system_metrics=True,
        export_file="/tmp/perfect21_metrics.txt"
    )

    collector = MetricsCollector("perfect21-auth", config)

    # 添加告警处理器
    collector.add_alert_handler(email_alert_handler)
    collector.add_alert_handler(slack_alert_handler)

    await collector.initialize()

    # 使用指标
    collector.increment_counter("requests_total", labels={"method": "GET", "endpoint": "/api/users"})
    collector.set_gauge("active_connections", 45)
    collector.observe_histogram("request_duration", 0.234)

    # 使用计时器装饰器
    @collector.time_function("database_query_duration")
    async def query_database():
        await asyncio.sleep(0.1)  # 模拟数据库查询
        return "result"

    # 使用计时器上下文
    async with collector.timer_context("complex_operation"):
        await asyncio.sleep(0.5)  # 模拟复杂操作

    # 获取摘要
    summary = await collector.get_metrics_summary()
    print(f"Metrics Summary: {json.dumps(summary, indent=2)}")