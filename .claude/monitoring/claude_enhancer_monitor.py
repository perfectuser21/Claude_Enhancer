#!/usr/bin/env python3
"""
Claude Enhancer 实时监控系统
监控Hook执行、性能指标、系统资源和错误率
提供实时Dashboard和自动告警功能
"""

import asyncio
import json
import time
import psutil
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from prometheus_client import Counter, Histogram, Gauge, Summary, start_http_server
import aiohttp
from aiohttp import web
import websockets
import numpy as np
from collections import defaultdict, deque

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(".claude/logs/monitor.log"), logging.StreamHandler()],
)
logger = logging.getLogger("claude_enhancer_monitor")


@dataclass
class HookMetrics:
    """Hook执行指标"""

    hook_name: str
    execution_time: float
    success: bool
    timestamp: datetime
    phase: str
    tool_name: str
    error_message: Optional[str] = None
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None


@dataclass
class SystemMetrics:
    """系统资源指标"""

    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    disk_usage: float
    network_io: Dict[str, int]
    process_count: int
    load_average: List[float]


@dataclass
class PerformanceMetrics:
    """性能指标统计"""

    p50_latency: float
    p95_latency: float
    p99_latency: float
    error_rate: float
    success_rate: float
    throughput: float
    trend: str  # 'improving', 'degrading', 'stable'


class PrometheusMetrics:
    """Prometheus指标收集器"""

    def __init__(self):
        # Hook执行指标
        self.hook_executions = Counter(
            "claude_enhancer_hook_executions_total",
            "Total hook executions",
            ["hook_name", "phase", "status"],
        )

        self.hook_duration = Histogram(
            "claude_enhancer_hook_duration_seconds",
            "Hook execution duration",
            ["hook_name", "phase"],
            buckets=[0.001, 0.01, 0.1, 0.5, 1, 2, 5, 10],
        )

        self.hook_errors = Counter(
            "claude_enhancer_hook_errors_total",
            "Total hook errors",
            ["hook_name", "error_type"],
        )

        # 系统资源指标
        self.cpu_usage = Gauge(
            "claude_enhancer_cpu_usage_percent", "CPU usage percentage"
        )

        self.memory_usage = Gauge(
            "claude_enhancer_memory_usage_percent", "Memory usage percentage"
        )

        self.disk_usage = Gauge(
            "claude_enhancer_disk_usage_percent", "Disk usage percentage"
        )

        # 性能指标
        self.latency_summary = Summary(
            "claude_enhancer_latency_seconds", "Request latency summary"
        )

        self.active_hooks = Gauge(
            "claude_enhancer_active_hooks", "Number of currently executing hooks"
        )

        self.queue_size = Gauge(
            "claude_enhancer_queue_size", "Size of the hook execution queue"
        )


class MetricsDatabase:
    """指标数据库管理"""

    def __init__(self, db_path: str = ".claude/data/metrics.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _init_database(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS hook_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hook_name TEXT NOT NULL,
                    execution_time REAL NOT NULL,
                    success BOOLEAN NOT NULL,
                    timestamp DATETIME NOT NULL,
                    phase TEXT,
                    tool_name TEXT,
                    error_message TEXT,
                    memory_usage REAL,
                    cpu_usage REAL
                );

                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    cpu_percent REAL NOT NULL,
                    memory_percent REAL NOT NULL,
                    disk_usage REAL NOT NULL,
                    network_io TEXT,
                    process_count INTEGER,
                    load_average TEXT
                );

                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at DATETIME
                );

                CREATE INDEX IF NOT EXISTS idx_hook_metrics_timestamp
                ON hook_metrics(timestamp);

                CREATE INDEX IF NOT EXISTS idx_system_metrics_timestamp
                ON system_metrics(timestamp);

                CREATE INDEX IF NOT EXISTS idx_hook_metrics_name_timestamp
                ON hook_metrics(hook_name, timestamp);
            """
            )

    def insert_hook_metrics(self, metrics: HookMetrics):
        """插入Hook指标"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO hook_metrics
                (hook_name, execution_time, success, timestamp, phase,
                 tool_name, error_message, memory_usage, cpu_usage)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    metrics.hook_name,
                    metrics.execution_time,
                    metrics.success,
                    metrics.timestamp,
                    metrics.phase,
                    metrics.tool_name,
                    metrics.error_message,
                    metrics.memory_usage,
                    metrics.cpu_usage,
                ),
            )

    def insert_system_metrics(self, metrics: SystemMetrics):
        """插入系统指标"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO system_metrics
                (timestamp, cpu_percent, memory_percent, disk_usage,
                 network_io, process_count, load_average)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    metrics.timestamp,
                    metrics.cpu_percent,
                    metrics.memory_percent,
                    metrics.disk_usage,
                    json.dumps(metrics.network_io),
                    metrics.process_count,
                    json.dumps(metrics.load_average),
                ),
            )

    def get_hook_metrics(self, hours: int = 24) -> List[HookMetrics]:
        """获取Hook指标"""
        since = datetime.now() - timedelta(hours=hours)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT hook_name, execution_time, success, timestamp, phase,
                       tool_name, error_message, memory_usage, cpu_usage
                FROM hook_metrics
                WHERE timestamp >= ?
                ORDER BY timestamp DESC
            """,
                (since,),
            )

            return [
                HookMetrics(
                    hook_name=row[0],
                    execution_time=row[1],
                    success=bool(row[2]),
                    timestamp=datetime.fromisoformat(row[3]),
                    phase=row[4],
                    tool_name=row[5],
                    error_message=row[6],
                    memory_usage=row[7],
                    cpu_usage=row[8],
                )
                for row in cursor.fetchall()
            ]

    def get_performance_summary(self, hours: int = 1) -> PerformanceMetrics:
        """获取性能摘要"""
        since = datetime.now() - timedelta(hours=hours)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT execution_time, success
                FROM hook_metrics
                WHERE timestamp >= ?
            """,
                (since,),
            )

            data = cursor.fetchall()
            if not data:
                return PerformanceMetrics(
                    p50_latency=0,
                    p95_latency=0,
                    p99_latency=0,
                    error_rate=0,
                    success_rate=1,
                    throughput=0,
                    trend="stable",
                )

            latencies = [row[0] for row in data]
            successes = [row[1] for row in data]

            p50 = np.percentile(latencies, 50)
            p95 = np.percentile(latencies, 95)
            p99 = np.percentile(latencies, 99)

            success_rate = sum(successes) / len(successes)
            error_rate = 1 - success_rate
            throughput = len(data) / hours  # per hour

            # 简单趋势分析
            trend = self._calculate_trend(latencies)

            return PerformanceMetrics(
                p50_latency=p50,
                p95_latency=p95,
                p99_latency=p99,
                error_rate=error_rate,
                success_rate=success_rate,
                throughput=throughput,
                trend=trend,
            )

    def _calculate_trend(self, latencies: List[float]) -> str:
        """计算性能趋势"""
        if len(latencies) < 10:
            return "stable"

        # 比较前半部分和后半部分的平均延迟
        mid = len(latencies) // 2
        first_half = np.mean(latencies[:mid])
        second_half = np.mean(latencies[mid:])

        if second_half > first_half * 1.1:
            return "degrading"
        elif second_half < first_half * 0.9:
            return "improving"
        else:
            return "stable"


class AlertManager:
    """告警管理器"""

    def __init__(self, db: MetricsDatabase):
        self.db = db
        self.alert_rules = {
            "high_error_rate": {"threshold": 0.05, "severity": "warning"},
            "very_high_error_rate": {"threshold": 0.2, "severity": "critical"},
            "high_latency": {"threshold": 5.0, "severity": "warning"},
            "very_high_latency": {"threshold": 10.0, "severity": "critical"},
            "high_cpu": {"threshold": 80.0, "severity": "warning"},
            "high_memory": {"threshold": 85.0, "severity": "warning"},
            "hook_failure": {"threshold": 3, "severity": "critical"},  # 连续失败次数
        }
        self.active_alerts = set()

    def check_alerts(self, performance: PerformanceMetrics, system: SystemMetrics):
        """检查告警条件"""
        alerts = []

        # 错误率告警
        if (
            performance.error_rate
            > self.alert_rules["very_high_error_rate"]["threshold"]
        ):
            alert = self._create_alert(
                "very_high_error_rate",
                f"Critical: Error rate is {performance.error_rate:.2%}",
                "critical",
            )
            alerts.append(alert)
        elif performance.error_rate > self.alert_rules["high_error_rate"]["threshold"]:
            alert = self._create_alert(
                "high_error_rate",
                f"Warning: Error rate is {performance.error_rate:.2%}",
                "warning",
            )
            alerts.append(alert)

        # 延迟告警
        if performance.p95_latency > self.alert_rules["very_high_latency"]["threshold"]:
            alert = self._create_alert(
                "very_high_latency",
                f"Critical: P95 latency is {performance.p95_latency:.2f}s",
                "critical",
            )
            alerts.append(alert)
        elif performance.p95_latency > self.alert_rules["high_latency"]["threshold"]:
            alert = self._create_alert(
                "high_latency",
                f"Warning: P95 latency is {performance.p95_latency:.2f}s",
                "warning",
            )
            alerts.append(alert)

        # 系统资源告警
        if system.cpu_percent > self.alert_rules["high_cpu"]["threshold"]:
            alert = self._create_alert(
                "high_cpu",
                f"Warning: CPU usage is {system.cpu_percent:.1f}%",
                "warning",
            )
            alerts.append(alert)

        if system.memory_percent > self.alert_rules["high_memory"]["threshold"]:
            alert = self._create_alert(
                "high_memory",
                f"Warning: Memory usage is {system.memory_percent:.1f}%",
                "warning",
            )
            alerts.append(alert)

        # 性能趋势告警
        if performance.trend == "degrading":
            alert = self._create_alert(
                "performance_degrading",
                "Warning: Performance is degrading over time",
                "warning",
            )
            alerts.append(alert)

        return alerts

    def _create_alert(self, alert_type: str, message: str, severity: str) -> Dict:
        """创建告警"""
        alert_id = f"{alert_type}_{int(time.time())}"

        if alert_id not in self.active_alerts:
            self.active_alerts.add(alert_id)

            # 存储到数据库
            with sqlite3.connect(self.db.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO alerts (timestamp, alert_type, severity, message)
                    VALUES (?, ?, ?, ?)
                """,
                    (datetime.now(), alert_type, severity, message),
                )

            return {
                "id": alert_id,
                "type": alert_type,
                "severity": severity,
                "message": message,
                "timestamp": datetime.now().isoformat(),
            }

        return None


class ClaudeEnhancerMonitor:
    """Claude Enhancer主监控器"""

    def __init__(self):
        self.prometheus_metrics = PrometheusMetrics()
        self.db = MetricsDatabase()
        self.alert_manager = AlertManager(self.db)
        self.is_running = False

        # 性能数据缓存
        self.hook_execution_times = defaultdict(lambda: deque(maxlen=1000))
        self.system_metrics_cache = deque(maxlen=300)  # 5分钟的数据(1秒间隔)

        # WebSocket连接管理
        self.websocket_clients = set()

        logger.info("Claude Enhancer监控系统初始化完成")

    async def start_monitoring(self):
        """启动监控"""
        self.is_running = True
        logger.info("启动Claude Enhancer监控系统")

        # 启动Prometheus metrics服务器
        start_http_server(9091)
        logger.info("Prometheus metrics服务器启动在端口9091")

        # 启动监控任务
        tasks = [
            asyncio.create_task(self._monitor_hooks()),
            asyncio.create_task(self._monitor_system()),
            asyncio.create_task(self._check_alerts()),
            asyncio.create_task(self._start_web_dashboard()),
            asyncio.create_task(self._cleanup_old_data()),
        ]

        await asyncio.gather(*tasks)

    async def _monitor_hooks(self):
        """监控Hook执行"""
        log_file = Path(".claude/logs/performance.log")

        if not log_file.exists():
            log_file.parent.mkdir(parents=True, exist_ok=True)
            log_file.touch()

        # 监控性能日志文件
        last_position = 0

        while self.is_running:
            try:
                if log_file.stat().st_size > last_position:
                    with open(log_file, "r") as f:
                        f.seek(last_position)
                        for line in f:
                            await self._process_hook_log(line.strip())
                        last_position = f.tell()

                await asyncio.sleep(0.1)  # 100ms检查间隔

            except Exception as e:
                logger.error(f"监控Hook执行时出错: {e}")
                await asyncio.sleep(1)

    async def _process_hook_log(self, log_line: str):
        """处理Hook日志行"""
        try:
            pass  # Auto-fixed empty block
            # 解析日志格式: "2023-09-23 17:24:15 | hook_name | 150ms"
            parts = log_line.split(" | ")
            if len(parts) >= 3:
                timestamp_str = parts[0]
                hook_name = parts[1]
                exec_time_str = parts[2].replace("ms", "")

                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                exec_time = float(exec_time_str) / 1000  # 转换为秒

                # 获取当前系统资源
                process = psutil.Process()
                memory_usage = process.memory_percent()
                cpu_usage = process.cpu_percent()

                # 创建指标
                metrics = HookMetrics(
                    hook_name=hook_name,
                    execution_time=exec_time,
                    success=True,  # 从日志推断
                    timestamp=timestamp,
                    phase="unknown",  # 从hook名称推断
                    tool_name="unknown",
                    memory_usage=memory_usage,
                    cpu_usage=cpu_usage,
                )

                # 存储指标
                self.db.insert_hook_metrics(metrics)

                # 更新Prometheus指标
                self.prometheus_metrics.hook_executions.labels(
                    hook_name=hook_name, phase=metrics.phase, status="success"
                ).inc()

                self.prometheus_metrics.hook_duration.labels(
                    hook_name=hook_name, phase=metrics.phase
                ).observe(exec_time)

                # 缓存数据用于实时分析
                self.hook_execution_times[hook_name].append(exec_time)

                # 通过WebSocket发送实时数据
                await self._broadcast_hook_metrics(metrics)

        except Exception as e:
            logger.error(f"处理Hook日志时出错: {e}")

    async def _monitor_system(self):
        """监控系统资源"""
        while self.is_running:
            try:
                pass  # Auto-fixed empty block
                # 收集系统指标
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage("/")
                network_io = dict(psutil.net_io_counters()._asdict())
                process_count = len(psutil.pids())
                load_avg = (
                    list(psutil.getloadavg())
                    if hasattr(psutil, "getloadavg")
                    else [0, 0, 0]
                )

                metrics = SystemMetrics(
                    timestamp=datetime.now(),
                    cpu_percent=cpu_percent,
                    memory_percent=memory.percent,
                    disk_usage=disk.percent,
                    network_io=network_io,
                    process_count=process_count,
                    load_average=load_avg,
                )

                # 存储指标
                self.db.insert_system_metrics(metrics)
                self.system_metrics_cache.append(metrics)

                # 更新Prometheus指标
                self.prometheus_metrics.cpu_usage.set(cpu_percent)
                self.prometheus_metrics.memory_usage.set(memory.percent)
                self.prometheus_metrics.disk_usage.set(disk.percent)

                # 通过WebSocket发送实时数据
                await self._broadcast_system_metrics(metrics)

                await asyncio.sleep(5)  # 5秒间隔

            except Exception as e:
                logger.error(f"监控系统资源时出错: {e}")
                await asyncio.sleep(5)

    async def _check_alerts(self):
        """检查告警条件"""
        while self.is_running:
            try:
                pass  # Auto-fixed empty block
                # 获取最新性能指标
                performance = self.db.get_performance_summary(hours=1)

                # 获取最新系统指标
                if self.system_metrics_cache:
                    system = self.system_metrics_cache[-1]

                    # 检查告警
                    alerts = self.alert_manager.check_alerts(performance, system)

                    # 处理新告警
                    for alert in alerts:
                        if alert:
                            logger.warning(f"触发告警: {alert['message']}")
                            await self._handle_alert(alert)

                await asyncio.sleep(30)  # 30秒检查间隔

            except Exception as e:
                logger.error(f"检查告警时出错: {e}")
                await asyncio.sleep(30)

    async def _handle_alert(self, alert: Dict):
        """处理告警"""
        # 发送WebSocket告警通知
        await self._broadcast_alert(alert)

        # 记录告警日志
        logger.warning(f"[{alert['severity'].upper()}] {alert['message']}")

        # 可以在这里添加其他告警处理逻辑，如发送邮件、Slack通知等

    async def _start_web_dashboard(self):
        """启动Web Dashboard"""
        app = web.Application()

        # 静态文件路由
        app.router.add_get("/", self._dashboard_index)
        app.router.add_get("/api/metrics", self._api_metrics)
        app.router.add_get("/api/alerts", self._api_alerts)
        app.router.add_get("/api/performance", self._api_performance)
        app.router.add_get("/ws", self._websocket_handler)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "localhost", 8091)
        await site.start()

        logger.info("Web Dashboard启动在 http://localhost:8091")

    async def _dashboard_index(self, request):
        """Dashboard首页"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Claude Enhancer 监控Dashboard</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .container { max-width: 1200px; margin: 0 auto; }
                .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
                .metric-card { border: 1px solid #ddd; padding: 15px; border-radius: 5px; }
                .metric-value { font-size: 2em; font-weight: bold; }
                .metric-label { color: #666; }
                .chart-container { width: 100%; height: 300px; margin: 20px 0; }
                .alert { padding: 10px; margin: 10px 0; border-radius: 5px; }
                .alert-warning { background-color: #fff3cd; border: 1px solid #ffeaa7; }
                .alert-critical { background-color: #f8d7da; border: 1px solid #f5c6cb; }
                .status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
                .status-green { background-color: #28a745; }
                .status-yellow { background-color: #ffc107; }
                .status-red { background-color: #dc3545; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 Claude Enhancer 监控Dashboard</h1>

                <div id="status-bar">
                    <span class="status-indicator status-green"></span>
                    <span>系统运行正常</span>
                </div>

                <div class="metrics-grid">
                    <div class="metric-card">
                        <div class="metric-label">Hook成功率</div>
                        <div class="metric-value" id="success-rate">--</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">P95延迟</div>
                        <div class="metric-value" id="p95-latency">--</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">CPU使用率</div>
                        <div class="metric-value" id="cpu-usage">--</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-label">内存使用率</div>
                        <div class="metric-value" id="memory-usage">--</div>
                    </div>
                </div>

                <div class="chart-container">
                    <canvas id="latency-chart"></canvas>
                </div>

                <div class="chart-container">
                    <canvas id="system-chart"></canvas>
                </div>

                <div id="alerts-container">
                    <h3>🚨 告警信息</h3>
                    <div id="alerts"></div>
                </div>
            </div>

            <script>
                // WebSocket连接
                const ws = new WebSocket('ws://localhost:8091/ws');

                // 图表初始化
                const latencyChart = new Chart(document.getElementById('latency-chart'), {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: [{
                            label: 'P95延迟(ms)',
                            data: [],
                            borderColor: 'rgb(75, 192, 192)',
                            tension: 0.1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                title: {
                                    display: true,
                                    text: '延迟 (ms)'
                                }
                            }
                        }
                    }
                });

                const systemChart = new Chart(document.getElementById('system-chart'), {
                    type: 'line',
                    data: {
                        labels: [],
                        datasets: [{
                            label: 'CPU %',
                            data: [],
                            borderColor: 'rgb(255, 99, 132)',
                            tension: 0.1
                        }, {
                            label: '内存 %',
                            data: [],
                            borderColor: 'rgb(54, 162, 235)',
                            tension: 0.1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            y: {
                                beginAtZero: true,
                                max: 100,
                                title: {
                                    display: true,
                                    text: '使用率 (%)'
                                }
                            }
                        }
                    }
                });

                // WebSocket消息处理
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);

                    if (data.type === 'performance') {
                        updatePerformanceMetrics(data.data);
                    } else if (data.type === 'system') {
                        updateSystemMetrics(data.data);
                    } else if (data.type === 'alert') {
                        addAlert(data.data);
                    }
                };

                function updatePerformanceMetrics(data) {
                    document.getElementById('success-rate').textContent =
                        (data.success_rate * 100).toFixed(1) + '%';
                    document.getElementById('p95-latency').textContent =
                        (data.p95_latency * 1000).toFixed(0) + 'ms';

                    // 更新延迟图表
                    const now = new Date().toLocaleTimeString();
                    latencyChart.data.labels.push(now);
                    latencyChart.data.datasets[0].data.push(data.p95_latency * 1000);

                    if (latencyChart.data.labels.length > 20) {
                        latencyChart.data.labels.shift();
                        latencyChart.data.datasets[0].data.shift();
                    }

                    latencyChart.update('none');
                }

                function updateSystemMetrics(data) {
                    document.getElementById('cpu-usage').textContent =
                        data.cpu_percent.toFixed(1) + '%';
                    document.getElementById('memory-usage').textContent =
                        data.memory_percent.toFixed(1) + '%';

                    // 更新系统图表
                    const now = new Date().toLocaleTimeString();
                    systemChart.data.labels.push(now);
                    systemChart.data.datasets[0].data.push(data.cpu_percent);
                    systemChart.data.datasets[1].data.push(data.memory_percent);

                    if (systemChart.data.labels.length > 20) {
                        systemChart.data.labels.shift();
                        systemChart.data.datasets[0].data.shift();
                        systemChart.data.datasets[1].data.shift();
                    }

                    systemChart.update('none');
                }

                function addAlert(alert) {
                    const alertsContainer = document.getElementById('alerts');
                    const alertDiv = document.createElement('div');
                    alertDiv.className = `alert alert-${alert.severity}`;
                    alertDiv.innerHTML = `
                        <strong>${alert.severity.toUpperCase()}:</strong>
                        ${alert.message}
                        <small>(${new Date(alert.timestamp).toLocaleString()})</small>
                    `;
                    alertsContainer.insertBefore(alertDiv, alertsContainer.firstChild);
                }

                // 定期获取数据
                setInterval(async function() {
                    try {
                        const response = await fetch('/api/performance');
                        const data = await response.json();
                        updatePerformanceMetrics(data);
                    } catch (e) {
                        console.error('获取性能数据失败:', e);
                    }
                }, 5000);

            </script>
        </body>
        </html>
        """
        return web.Response(text=html, content_type="text/html")

    async def _api_metrics(self, request):
        """API: 获取指标数据"""
        try:
            hook_metrics = self.db.get_hook_metrics(hours=1)
            performance = self.db.get_performance_summary(hours=1)

            return web.json_response(
                {
                    "hook_count": len(hook_metrics),
                    "performance": asdict(performance),
                    "timestamp": datetime.now().isoformat(),
                }
            )
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def _api_performance(self, request):
        """API: 获取性能数据"""
        try:
            performance = self.db.get_performance_summary(hours=1)
            return web.json_response(asdict(performance))
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def _api_alerts(self, request):
        """API: 获取告警数据"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT alert_type, severity, message, timestamp
                    FROM alerts
                    WHERE resolved = FALSE
                    ORDER BY timestamp DESC
                    LIMIT 50
                """
                )

                alerts = [
                    {
                        "type": row[0],
                        "severity": row[1],
                        "message": row[2],
                        "timestamp": row[3],
                    }
                    for row in cursor.fetchall()
                ]

                return web.json_response(alerts)
        except Exception as e:
            return web.json_response({"error": str(e)}, status=500)

    async def _websocket_handler(self, request):
        """WebSocket处理器"""
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        self.websocket_clients.add(ws)
        logger.info("新的WebSocket连接")

        try:
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    pass  # Auto-fixed empty block
                    # 处理客户端消息
                    pass
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket错误: {ws.exception()}")
        except Exception as e:
            logger.error(f"WebSocket处理错误: {e}")
        finally:
            self.websocket_clients.discard(ws)
            logger.info("WebSocket连接断开")

        return ws

    async def _broadcast_hook_metrics(self, metrics: HookMetrics):
        """广播Hook指标"""
        if self.websocket_clients:
            message = {"type": "hook", "data": asdict(metrics)}
            await self._broadcast_to_clients(message)

    async def _broadcast_system_metrics(self, metrics: SystemMetrics):
        """广播系统指标"""
        if self.websocket_clients:
            message = {"type": "system", "data": asdict(metrics)}
            await self._broadcast_to_clients(message)

    async def _broadcast_alert(self, alert: Dict):
        """广播告警"""
        if self.websocket_clients:
            message = {"type": "alert", "data": alert}
            await self._broadcast_to_clients(message)

    async def _broadcast_to_clients(self, message: Dict):
        """向所有WebSocket客户端广播消息"""
        if not self.websocket_clients:
            return

        disconnected = set()
        for ws in self.websocket_clients:
            try:
                await ws.send_str(json.dumps(message, default=str))
            except Exception as e:
                logger.error(f"发送WebSocket消息失败: {e}")
                disconnected.add(ws)

        # 清理断开的连接
        self.websocket_clients -= disconnected

    async def _cleanup_old_data(self):
        """清理旧数据"""
        while self.is_running:
            try:
                pass  # Auto-fixed empty block
                # 删除7天前的数据
                cutoff = datetime.now() - timedelta(days=7)

                with sqlite3.connect(self.db.db_path) as conn:
                    conn.execute(
                        "DELETE FROM hook_metrics WHERE timestamp < ?", (cutoff,)
                    )
                    conn.execute(
                        "DELETE FROM system_metrics WHERE timestamp < ?", (cutoff,)
                    )
                    conn.execute(
                        "DELETE FROM alerts WHERE timestamp < ? AND resolved = TRUE",
                        (cutoff,),
                    )

                logger.info("清理旧数据完成")

                # 每天清理一次
                await asyncio.sleep(24 * 3600)

            except Exception as e:
                logger.error(f"清理旧数据时出错: {e}")
                await asyncio.sleep(3600)  # 1小时后重试


async def main():
    """主函数"""
    monitor = ClaudeEnhancerMonitor()

    try:
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        logger.info("收到停止信号，正在关闭监控系统...")
        monitor.is_running = False
    except Exception as e:
        logger.error(f"监控系统异常: {e}")
    finally:
        logger.info("Claude Enhancer监控系统已停止")


if __name__ == "__main__":
    asyncio.run(main())
