"""
Performance Optimization: Monitoring Dashboard
性能监控仪表板 - 实时性能监控与可视化系统
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import aiofiles
from contextlib import asynccontextmanager
import psutil
import weakref

logger = logging.getLogger(__name__)


@dataclass
class DashboardMetric:
    """仪表板指标"""

    name: str
    value: float
    unit: str = ""
    category: str = "general"
    trend: float = 0.0  # 变化趋势 (正数上升，负数下降)
    status: str = "normal"  # normal, warning, critical
    timestamp: datetime = field(default_factory=datetime.now)
    history: List[Tuple[datetime, float]] = field(default_factory=list)


@dataclass
class SystemStatus:
    """系统状态"""

    overall_health: str = "healthy"  # healthy, degraded, unhealthy
    uptime: float = 0.0
    total_requests: int = 0
    error_rate: float = 0.0
    avg_response_time: float = 0.0
    active_connections: int = 0
    cache_hit_rate: float = 0.0
    queue_size: int = 0


class WebSocketManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """建立WebSocket连接"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"🔌 WebSocket连接建立，当前连接数: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"🔌 WebSocket连接断开，当前连接数: {len(self.active_connections)}")

    async def send_to_all(self, data: dict):
        """向所有客户端发送数据"""
        if not self.active_connections:
            return

        message = json.dumps(data, default=str)
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.warning(f"⚠️ WebSocket发送失败: {e}")
                disconnected.append(connection)

        # 清理断开的连接
        for connection in disconnected:
            self.disconnect(connection)


class PerformanceDashboard:
    """性能监控仪表板"""

    def __init__(self, service_name: str = "claude-enhancer"):
        self.service_name = service_name
        self.metrics: Dict[str, DashboardMetric] = {}
        self.system_status = SystemStatus()
        self.websocket_manager = WebSocketManager()
        self.app = FastAPI(title=f"{service_name} Performance Dashboard")

        # 数据收集器引用
        self.cache_manager = None
        self.database_optimizer = None
        self.async_processor = None
        self.load_balancer = None
        self.metrics_collector = None

        # 运行状态
        self.running = False
        self.start_time = time.time()

        # 配置路由
        self._setup_routes()

    def _setup_routes(self):
        """配置API路由"""

        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard():
            """主仪表板页面"""
            return await self._render_dashboard_html()

        @self.app.get("/api/status")
        async def get_status():
            """获取系统状态"""
            return JSONResponse(
                content={
                    "status": self.system_status.__dict__,
                    "timestamp": datetime.now().isoformat(),
                }
            )

        @self.app.get("/api/metrics")
        async def get_metrics():
            """获取所有指标"""
            metrics_data = {}
            for name, metric in self.metrics.items():
                metrics_data[name] = {
                    "name": metric.name,
                    "value": metric.value,
                    "unit": metric.unit,
                    "category": metric.category,
                    "trend": metric.trend,
                    "status": metric.status,
                    "timestamp": metric.timestamp.isoformat(),
                    "history": [
                        (t.isoformat(), v) for t, v in metric.history[-50:]
                    ],  # 最近50个数据点
                }
            return JSONResponse(content=metrics_data)

        @self.app.get("/api/metrics/{category}")
        async def get_metrics_by_category(category: str):
            """按分类获取指标"""
            category_metrics = {
                name: {
                    "name": metric.name,
                    "value": metric.value,
                    "unit": metric.unit,
                    "trend": metric.trend,
                    "status": metric.status,
                    "timestamp": metric.timestamp.isoformat(),
                }
                for name, metric in self.metrics.items()
                if metric.category == category
            }
            return JSONResponse(content=category_metrics)

        @self.app.get("/api/alerts")
        async def get_alerts():
            """获取告警信息"""
            alerts = []
            for metric in self.metrics.values():
                if metric.status in ["warning", "critical"]:
                    alerts.append(
                        {
                            "name": metric.name,
                            "value": metric.value,
                            "status": metric.status,
                            "category": metric.category,
                            "timestamp": metric.timestamp.isoformat(),
                        }
                    )
            return JSONResponse(content=alerts)

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket端点"""
            await self.websocket_manager.connect(websocket)
            try:
                while True:
                    # 保持连接活跃
                    await websocket.receive_text()
            except WebSocketDisconnect:
                self.websocket_manager.disconnect(websocket)

        @self.app.get("/api/export/{format}")
        async def export_metrics(format: str):
            """导出指标数据"""
            if format == "json":
                return await get_metrics()
            elif format == "csv":
                return await self._export_csv()
            elif format == "prometheus":
                return await self._export_prometheus()
            else:
                return JSONResponse(
                    content={"error": "Unsupported format"}, status_code=400
                )

    async def initialize(self):
        """初始化仪表板"""
        try:
            self.running = True

            # 启动数据收集任务
            asyncio.create_task(self._collect_metrics_loop())
            asyncio.create_task(self._update_system_status_loop())
            asyncio.create_task(self._broadcast_updates_loop())
            asyncio.create_task(self._cleanup_old_data_loop())

            logger.info(f"✅ 性能监控仪表板初始化成功 - 服务: {self.service_name}")

        except Exception as e:
            logger.error(f"❌ 性能监控仪表板初始化失败: {e}")
            raise

    def register_component(self, component_name: str, component):
        """注册性能组件"""
        setattr(self, component_name, component)
        logger.info(f"📊 注册性能组件: {component_name}")

    async def _collect_metrics_loop(self):
        """指标收集循环"""
        while self.running:
            try:
                await self._collect_system_metrics()
                await self._collect_component_metrics()
                await self._calculate_trends()

            except Exception as e:
                logger.error(f"❌ 指标收集失败: {e}")

            await asyncio.sleep(5)  # 每5秒收集一次

    async def _collect_system_metrics(self):
        """收集系统指标"""
        try:
            # CPU指标
            cpu_percent = psutil.cpu_percent(interval=None)
            self._update_metric(
                "cpu_usage",
                cpu_percent,
                "percent",
                "system",
                self._get_status_by_threshold(cpu_percent, 70, 85),
            )

            # 内存指标
            memory = psutil.virtual_memory()
            self._update_metric(
                "memory_usage",
                memory.percent,
                "percent",
                "system",
                self._get_status_by_threshold(memory.percent, 75, 90),
            )
            self._update_metric(
                "memory_available",
                memory.available / 1024 / 1024 / 1024,
                "GB",
                "system",
            )

            # 磁盘指标
            disk = psutil.disk_usage("/")
            disk_percent = disk.used / disk.total * 100
            self._update_metric(
                "disk_usage",
                disk_percent,
                "percent",
                "system",
                self._get_status_by_threshold(disk_percent, 80, 95),
            )

            # 网络指标
            network = psutil.net_io_counters()
            self._update_metric(
                "network_bytes_sent", network.bytes_sent / 1024 / 1024, "MB", "network"
            )
            self._update_metric(
                "network_bytes_recv", network.bytes_recv / 1024 / 1024, "MB", "network"
            )

            # 进程指标
            process = psutil.Process()
            process_memory = process.memory_info()
            self._update_metric(
                "process_memory", process_memory.rss / 1024 / 1024, "MB", "process"
            )
            self._update_metric(
                "process_cpu", process.cpu_percent(), "percent", "process"
            )

        except Exception as e:
            logger.error(f"❌ 系统指标收集失败: {e}")

    async def _collect_component_metrics(self):
        """收集组件指标"""
        try:
            # 缓存管理器指标
            if self.cache_manager:
                stats = await self.cache_manager.get_stats()
                self._update_metric(
                    "cache_hit_rate",
                    stats.get("hit_rate", 0),
                    "percent",
                    "cache",
                    self._get_status_by_threshold(
                        stats.get("hit_rate", 0), 80, 95, reverse=True
                    ),
                )
                self._update_metric(
                    "cache_size", stats.get("local_cache_size", 0), "items", "cache"
                )

            # 数据库优化器指标
            if self.database_optimizer:
                stats = await self.database_optimizer.get_database_stats()
                self._update_metric(
                    "db_avg_query_time",
                    stats.get("avg_query_time", 0) * 1000,
                    "ms",
                    "database",
                    self._get_status_by_threshold(
                        stats.get("avg_query_time", 0) * 1000, 100, 500
                    ),
                )
                self._update_metric(
                    "db_slow_queries",
                    stats.get("slow_query_count", 0),
                    "count",
                    "database",
                )
                self._update_metric(
                    "db_error_rate",
                    stats.get("error_rate", 0),
                    "percent",
                    "database",
                    self._get_status_by_threshold(stats.get("error_rate", 0), 1, 5),
                )

            # 异步处理器指标
            if self.async_processor:
                status = await self.async_processor.get_queue_status()
                self._update_metric(
                    "queue_size",
                    status.get("queue_size", 0),
                    "items",
                    "async",
                    self._get_status_by_threshold(
                        status.get("queue_size", 0), 500, 800
                    ),
                )
                self._update_metric(
                    "active_workers", status.get("active_workers", 0), "count", "async"
                )

                stats = status.get("stats", {})
                self._update_metric(
                    "completed_tasks", stats.get("completed_tasks", 0), "count", "async"
                )
                self._update_metric(
                    "failed_tasks", stats.get("failed_tasks", 0), "count", "async"
                )

            # 负载均衡器指标
            if self.load_balancer:
                stats = await self.load_balancer.get_server_stats()
                global_stats = stats.get("global_stats", {})
                self._update_metric(
                    "lb_total_requests",
                    global_stats.get("total_requests", 0),
                    "count",
                    "loadbalancer",
                )
                self._update_metric(
                    "lb_success_rate",
                    (
                        global_stats.get("successful_requests", 0)
                        / max(global_stats.get("total_requests", 1), 1)
                    )
                    * 100,
                    "percent",
                    "loadbalancer",
                )
                self._update_metric(
                    "lb_avg_response_time",
                    global_stats.get("avg_response_time", 0) * 1000,
                    "ms",
                    "loadbalancer",
                )

        except Exception as e:
            logger.error(f"❌ 组件指标收集失败: {e}")

    def _update_metric(
        self,
        name: str,
        value: float,
        unit: str = "",
        category: str = "general",
        status: str = "normal",
    ):
        """更新指标"""
        now = datetime.now()

        if name not in self.metrics:
            self.metrics[name] = DashboardMetric(
                name=name,
                value=value,
                unit=unit,
                category=category,
                status=status,
                timestamp=now,
            )
        else:
            metric = self.metrics[name]
            metric.value = value
            metric.status = status
            metric.timestamp = now

            # 添加历史数据
            metric.history.append((now, value))

            # 限制历史数据数量
            if len(metric.history) > 1000:
                metric.history = metric.history[-1000:]

    async def _calculate_trends(self):
        """计算指标趋势"""
        for metric in self.metrics.values():
            if len(metric.history) >= 2:
                # 计算最近的变化趋势
                recent_values = [v for _, v in metric.history[-10:]]  # 最近10个值
                if len(recent_values) >= 2:
                    trend = (recent_values[-1] - recent_values[0]) / len(recent_values)
                    metric.trend = trend

    async def _update_system_status_loop(self):
        """更新系统状态循环"""
        while self.running:
            try:
                await self._update_system_status()
            except Exception as e:
                logger.error(f"❌ 系统状态更新失败: {e}")

            await asyncio.sleep(10)  # 每10秒更新一次

    async def _update_system_status(self):
        """更新系统状态"""
        # 计算整体健康状态
        critical_count = sum(1 for m in self.metrics.values() if m.status == "critical")
        warning_count = sum(1 for m in self.metrics.values() if m.status == "warning")

        if critical_count > 0:
            self.system_status.overall_health = "unhealthy"
        elif warning_count > 3:
            self.system_status.overall_health = "degraded"
        else:
            self.system_status.overall_health = "healthy"

        # 更新基本状态
        self.system_status.uptime = time.time() - self.start_time

        # 从指标中提取关键状态
        if "lb_total_requests" in self.metrics:
            self.system_status.total_requests = int(
                self.metrics["lb_total_requests"].value
            )

        if "db_error_rate" in self.metrics:
            self.system_status.error_rate = self.metrics["db_error_rate"].value

        if "lb_avg_response_time" in self.metrics:
            self.system_status.avg_response_time = self.metrics[
                "lb_avg_response_time"
            ].value

        if "cache_hit_rate" in self.metrics:
            self.system_status.cache_hit_rate = self.metrics["cache_hit_rate"].value

        if "queue_size" in self.metrics:
            self.system_status.queue_size = int(self.metrics["queue_size"].value)

    async def _broadcast_updates_loop(self):
        """广播更新循环"""
        while self.running:
            try:
                # 准备数据
                update_data = {
                    "type": "metrics_update",
                    "timestamp": datetime.now().isoformat(),
                    "system_status": self.system_status.__dict__,
                    "metrics": {
                        name: {
                            "value": metric.value,
                            "unit": metric.unit,
                            "status": metric.status,
                            "trend": metric.trend,
                        }
                        for name, metric in self.metrics.items()
                    },
                }

                # 广播给所有WebSocket客户端
                await self.websocket_manager.send_to_all(update_data)

            except Exception as e:
                logger.error(f"❌ 广播更新失败: {e}")

            await asyncio.sleep(2)  # 每2秒广播一次

    async def _cleanup_old_data_loop(self):
        """清理旧数据循环"""
        while self.running:
            try:
                cutoff_time = datetime.now() - timedelta(hours=2)  # 保留2小时数据

                for metric in self.metrics.values():
                    # 清理历史数据
                    metric.history = [
                        (timestamp, value)
                        for timestamp, value in metric.history
                        if timestamp > cutoff_time
                    ]

            except Exception as e:
                logger.error(f"❌ 数据清理失败: {e}")

            await asyncio.sleep(300)  # 每5分钟清理一次

    def _get_status_by_threshold(
        self,
        value: float,
        warning_threshold: float,
        critical_threshold: float,
        reverse: bool = False,
    ) -> str:
        """根据阈值确定状态"""
        if reverse:
            # 对于缓存命中率等指标，值越高越好
            if value < critical_threshold:
                return "critical"
            elif value < warning_threshold:
                return "warning"
            else:
                return "normal"
        else:
            # 对于CPU、内存等指标，值越低越好
            if value > critical_threshold:
                return "critical"
            elif value > warning_threshold:
                return "warning"
            else:
                return "normal"

    async def _render_dashboard_html(self) -> str:
        """渲染仪表板HTML"""
        html_content = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Claude Enhancer Performance Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; }
        .dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; padding: 20px; }
        .card { background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .card h3 { color: #333; margin-bottom: 15px; border-bottom: 2px solid #e0e0e0; padding-bottom: 5px; }
        .metric { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .metric-name { color: #666; }
        .metric-value { font-weight: bold; }
        .status-normal { color: #4CAF50; }
        .status-warning { color: #FF9800; }
        .status-critical { color: #F44336; }
        .header { background: #2196F3; color: white; padding: 20px; text-align: center; }
        .status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
        .healthy { background-color: #4CAF50; }
        .degraded { background-color: #FF9800; }
        .unhealthy { background-color: #F44336; }
        .trend-up::after { content: " ↗"; color: #4CAF50; }
        .trend-down::after { content: " ↘"; color: #F44336; }
        .refresh-indicator { position: fixed; top: 20px; right: 20px; background: rgba(0,0,0,0.7); color: white; padding: 10px; border-radius: 4px; display: none; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 Claude Enhancer Performance Dashboard</h1>
        <div id="systemStatus">
            <span class="status-indicator healthy"></span>
            <span>System Status: <strong id="overallHealth">Healthy</strong></span>
            <span style="margin-left: 20px;">Uptime: <strong id="uptime">0s</strong></span>
        </div>
    </div>

    <div class="refresh-indicator" id="refreshIndicator">
        📡 Real-time updates active
    </div>

    <div class="dashboard" id="dashboard">
        <!-- 动态生成的指标卡片 -->
    </div>

    <script>
        class Dashboard {
            constructor() {
                this.ws = null;
                this.metrics = {};
                this.categories = new Set();
                this.connectWebSocket();
                this.fetchInitialData();
            }

            connectWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws`;

                this.ws = new WebSocket(wsUrl);

                this.ws.onopen = () => {
                    console.log('WebSocket connected');
                    document.getElementById('refreshIndicator').style.display = 'block';
                    setTimeout(() => {
                        document.getElementById('refreshIndicator').style.display = 'none';
                    }, 3000);
                };

                this.ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    if (data.type === 'metrics_update') {
                        this.updateMetrics(data.metrics);
                        this.updateSystemStatus(data.system_status);
                    }
                };

                this.ws.onclose = () => {
                    console.log('WebSocket disconnected, attempting to reconnect...');
                    setTimeout(() => this.connectWebSocket(), 5000);
                };
            }

            async fetchInitialData() {
                try {
                    const response = await fetch('/api/metrics');
                    const metrics = await response.json();
                    this.updateMetrics(metrics);
                    this.renderDashboard();
                } catch (error) {
                    console.error('Failed to fetch initial data:', error);
                }
            }

            updateMetrics(metrics) {
                this.metrics = metrics;
                this.categories.clear();
                Object.values(metrics).forEach(metric => {
                    this.categories.add(metric.category || 'general');
                });
                this.renderDashboard();
            }

            updateSystemStatus(status) {
                const healthIndicator = document.querySelector('.status-indicator');
                const healthText = document.getElementById('overallHealth');
                const uptimeText = document.getElementById('uptime');

                if (healthIndicator && healthText) {
                    healthIndicator.className = `status-indicator ${status.overall_health}`;
                    healthText.textContent = status.overall_health.charAt(0).toUpperCase() + status.overall_health.slice(1);
                }

                if (uptimeText) {
                    const uptime = Math.floor(status.uptime);
                    const hours = Math.floor(uptime / 3600);
                    const minutes = Math.floor((uptime % 3600) / 60);
                    const seconds = uptime % 60;
                    uptimeText.textContent = `${hours}h ${minutes}m ${seconds}s`;
                }
            }

            renderDashboard() {
                const dashboard = document.getElementById('dashboard');
                dashboard.innerHTML = '';

                // 按分类组织指标
                this.categories.forEach(category => {
                    const categoryMetrics = Object.values(this.metrics).filter(m =>
                        (m.category || 'general') === category
                    );

                    if (categoryMetrics.length === 0) return;

                    const card = document.createElement('div');
                    card.className = 'card';

                    const title = category.charAt(0).toUpperCase() + category.slice(1);
                    card.innerHTML = `
                        <h3>${title}</h3>
                        ${categoryMetrics.map(metric => this.renderMetric(metric)).join('')}
                    `;

                    dashboard.appendChild(card);
                });
            }

            renderMetric(metric) {
                const trendClass = metric.trend > 0 ? 'trend-up' : metric.trend < 0 ? 'trend-down' : '';
                const statusClass = `status-${metric.status}`;
                const value = typeof metric.value === 'number' ?
                    (metric.value % 1 === 0 ? metric.value : metric.value.toFixed(2)) : metric.value;

                return `
                    <div class="metric">
                        <span class="metric-name">${metric.name.replace(/_/g, ' ').toUpperCase()}</span>
                        <span class="metric-value ${statusClass} ${trendClass}">
                            ${value} ${metric.unit}
                        </span>
                    </div>
                `;
            }
        }

        // 初始化仪表板
        document.addEventListener('DOMContentLoaded', () => {
            new Dashboard();
        });
    </script>
</body>
</html>
        """
        return html_content

    async def _export_csv(self) -> str:
        """导出CSV格式"""
        lines = ["timestamp,metric_name,value,unit,category,status"]

        for name, metric in self.metrics.items():
            line = f"{metric.timestamp.isoformat()},{name},{metric.value},{metric.unit},{metric.category},{metric.status}"
            lines.append(line)

        return "\\n".join(lines)

    async def _export_prometheus(self) -> str:
        """导出Prometheus格式"""
        lines = []

        for name, metric in self.metrics.items():
            # 标准化指标名称
            metric_name = name.replace("-", "_").replace(" ", "_").lower()

            # 添加标签
            labels = f'service="{self.service_name}",category="{metric.category}"'

            lines.append(f"# TYPE {metric_name} gauge")
            lines.append(f"{metric_name}{{{labels}}} {metric.value}")

        return "\\n".join(lines)

    async def health_check(self) -> bool:
        """健康检查"""
        return self.running and len(self.metrics) > 0

    async def shutdown(self):
        """关闭仪表板"""
        logger.info("🛑 正在关闭性能监控仪表板...")
        self.running = False

        # 通知所有WebSocket客户端
        await self.websocket_manager.send_to_all(
            {"type": "shutdown", "message": "Dashboard is shutting down"}
        )

        logger.info("✅ 性能监控仪表板已关闭")


# 使用示例
async def create_dashboard(service_name: str = "claude-enhancer") -> PerformanceDashboard:
    """创建仪表板实例"""
    dashboard = PerformanceDashboard(service_name)
    await dashboard.initialize()
    return dashboard
