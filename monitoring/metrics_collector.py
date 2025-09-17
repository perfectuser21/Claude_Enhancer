#!/usr/bin/env python3
"""
Metrics Collector - Perfect21 Prometheus Metrics
完整的度量指标收集器，支持自定义业务指标
"""

import time
import psutil
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from prometheus_client import (
    Counter, Histogram, Gauge, Summary, Info,
    CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST,
    start_http_server
)
from prometheus_client.core import REGISTRY
import json
import os

class Perfect21MetricsCollector:
    """Perfect21指标收集器"""

    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or REGISTRY
        self._setup_metrics()
        self._start_time = time.time()
        self._lock = threading.Lock()

    def _setup_metrics(self):
        """设置所有指标"""

        # ============ 系统级指标 ============
        self.system_cpu_usage = Gauge(
            'perfect21_system_cpu_usage_percent',
            'CPU usage percentage',
            registry=self.registry
        )

        self.system_memory_usage = Gauge(
            'perfect21_system_memory_usage_bytes',
            'Memory usage in bytes',
            ['type'],  # available, used, total
            registry=self.registry
        )

        self.system_disk_usage = Gauge(
            'perfect21_system_disk_usage_bytes',
            'Disk usage in bytes',
            ['path', 'type'],  # total, used, free
            registry=self.registry
        )

        # ============ API指标 ============
        self.api_requests_total = Counter(
            'perfect21_api_requests_total',
            'Total number of API requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )

        self.api_request_duration = Histogram(
            'perfect21_api_request_duration_seconds',
            'API request duration in seconds',
            ['method', 'endpoint'],
            buckets=[0.001, 0.01, 0.1, 0.5, 1, 2, 5, 10, 30],
            registry=self.registry
        )

        self.api_active_connections = Gauge(
            'perfect21_api_active_connections',
            'Number of active API connections',
            registry=self.registry
        )

        # ============ Agent执行指标 ============
        self.agent_executions_total = Counter(
            'perfect21_agent_executions_total',
            'Total number of agent executions',
            ['agent_name', 'status'],  # success, error, timeout
            registry=self.registry
        )

        self.agent_execution_duration = Histogram(
            'perfect21_agent_execution_duration_seconds',
            'Agent execution duration in seconds',
            ['agent_name'],
            buckets=[0.1, 0.5, 1, 5, 10, 30, 60, 300],
            registry=self.registry
        )

        self.parallel_executions_total = Counter(
            'perfect21_parallel_executions_total',
            'Total number of parallel executions',
            ['workflow_type', 'status'],
            registry=self.registry
        )

        self.parallel_execution_duration = Histogram(
            'perfect21_parallel_execution_duration_seconds',
            'Parallel execution duration in seconds',
            ['workflow_type'],
            buckets=[1, 5, 10, 30, 60, 300, 600],
            registry=self.registry
        )

        # ============ Git工作流指标 ============
        self.git_operations_total = Counter(
            'perfect21_git_operations_total',
            'Total number of git operations',
            ['operation', 'status'],  # commit, push, pull, etc.
            registry=self.registry
        )

        self.git_operation_duration = Histogram(
            'perfect21_git_operation_duration_seconds',
            'Git operation duration in seconds',
            ['operation'],
            buckets=[0.1, 0.5, 1, 5, 10, 30],
            registry=self.registry
        )

        self.git_hooks_executions = Counter(
            'perfect21_git_hooks_executions_total',
            'Total number of git hook executions',
            ['hook_type', 'status'],
            registry=self.registry
        )

        # ============ 质量指标 ============
        self.quality_checks_total = Counter(
            'perfect21_quality_checks_total',
            'Total number of quality checks',
            ['check_type', 'status'],
            registry=self.registry
        )

        self.sync_point_validations = Counter(
            'perfect21_sync_point_validations_total',
            'Total number of sync point validations',
            ['sync_point_type', 'status'],
            registry=self.registry
        )

        self.code_coverage_percentage = Gauge(
            'perfect21_code_coverage_percentage',
            'Code coverage percentage',
            ['project'],
            registry=self.registry
        )

        # ============ 缓存指标 ============
        self.cache_operations_total = Counter(
            'perfect21_cache_operations_total',
            'Total number of cache operations',
            ['operation', 'status'],  # hit, miss, set, delete
            registry=self.registry
        )

        self.cache_size_bytes = Gauge(
            'perfect21_cache_size_bytes',
            'Cache size in bytes',
            ['cache_type'],
            registry=self.registry
        )

        # ============ 错误处理指标 ============
        self.errors_total = Counter(
            'perfect21_errors_total',
            'Total number of errors',
            ['error_type', 'severity', 'component'],
            registry=self.registry
        )

        self.error_recovery_attempts = Counter(
            'perfect21_error_recovery_attempts_total',
            'Total number of error recovery attempts',
            ['error_type', 'status'],
            registry=self.registry
        )

        # ============ 性能指标 ============
        self.application_uptime_seconds = Gauge(
            'perfect21_application_uptime_seconds',
            'Application uptime in seconds',
            registry=self.registry
        )

        self.workflow_throughput = Summary(
            'perfect21_workflow_throughput',
            'Workflow throughput (workflows per second)',
            registry=self.registry
        )

        # ============ 业务指标 ============
        self.active_users = Gauge(
            'perfect21_active_users',
            'Number of active users',
            registry=self.registry
        )

        self.workspace_count = Gauge(
            'perfect21_workspace_count',
            'Number of active workspaces',
            registry=self.registry
        )

        # ============ 信息指标 ============
        self.build_info = Info(
            'perfect21_build_info',
            'Perfect21 build information',
            registry=self.registry
        )

        # 设置构建信息
        self.build_info.info({
            'version': '3.0.0',
            'build_date': datetime.now().isoformat(),
            'python_version': f"{psutil.python_version()}",
            'git_commit': self._get_git_commit()
        })

    def _get_git_commit(self) -> str:
        """获取Git提交哈希"""
        try:
            import subprocess
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip()[:8] if result.returncode == 0 else 'unknown'
        except:
            return 'unknown'

    def update_system_metrics(self):
        """更新系统指标"""
        with self._lock:
            try:
                # CPU使用率
                cpu_percent = psutil.cpu_percent(interval=1)
                self.system_cpu_usage.set(cpu_percent)

                # 内存使用
                memory = psutil.virtual_memory()
                self.system_memory_usage.labels(type='total').set(memory.total)
                self.system_memory_usage.labels(type='used').set(memory.used)
                self.system_memory_usage.labels(type='available').set(memory.available)

                # 磁盘使用
                disk_usage = psutil.disk_usage('/')
                self.system_disk_usage.labels(path='/', type='total').set(disk_usage.total)
                self.system_disk_usage.labels(path='/', type='used').set(disk_usage.used)
                self.system_disk_usage.labels(path='/', type='free').set(disk_usage.free)

                # 应用运行时间
                uptime = time.time() - self._start_time
                self.application_uptime_seconds.set(uptime)

            except Exception as e:
                print(f"Error updating system metrics: {e}")

    def record_api_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """记录API请求指标"""
        self.api_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=str(status_code)
        ).inc()

        self.api_request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)

    def record_agent_execution(self, agent_name: str, status: str, duration: float):
        """记录Agent执行指标"""
        self.agent_executions_total.labels(
            agent_name=agent_name,
            status=status
        ).inc()

        self.agent_execution_duration.labels(
            agent_name=agent_name
        ).observe(duration)

    def record_parallel_execution(self, workflow_type: str, status: str, duration: float):
        """记录并行执行指标"""
        self.parallel_executions_total.labels(
            workflow_type=workflow_type,
            status=status
        ).inc()

        self.parallel_execution_duration.labels(
            workflow_type=workflow_type
        ).observe(duration)

    def record_git_operation(self, operation: str, status: str, duration: float):
        """记录Git操作指标"""
        self.git_operations_total.labels(
            operation=operation,
            status=status
        ).inc()

        self.git_operation_duration.labels(
            operation=operation
        ).observe(duration)

    def record_git_hook_execution(self, hook_type: str, status: str):
        """记录Git Hook执行"""
        self.git_hooks_executions.labels(
            hook_type=hook_type,
            status=status
        ).inc()

    def record_quality_check(self, check_type: str, status: str):
        """记录质量检查"""
        self.quality_checks_total.labels(
            check_type=check_type,
            status=status
        ).inc()

    def record_sync_point_validation(self, sync_point_type: str, status: str):
        """记录同步点验证"""
        self.sync_point_validations.labels(
            sync_point_type=sync_point_type,
            status=status
        ).inc()

    def update_code_coverage(self, project: str, percentage: float):
        """更新代码覆盖率"""
        self.code_coverage_percentage.labels(project=project).set(percentage)

    def record_cache_operation(self, operation: str, status: str):
        """记录缓存操作"""
        self.cache_operations_total.labels(
            operation=operation,
            status=status
        ).inc()

    def update_cache_size(self, cache_type: str, size_bytes: int):
        """更新缓存大小"""
        self.cache_size_bytes.labels(cache_type=cache_type).set(size_bytes)

    def record_error(self, error_type: str, severity: str, component: str):
        """记录错误"""
        self.errors_total.labels(
            error_type=error_type,
            severity=severity,
            component=component
        ).inc()

    def record_error_recovery(self, error_type: str, status: str):
        """记录错误恢复尝试"""
        self.error_recovery_attempts.labels(
            error_type=error_type,
            status=status
        ).inc()

    def update_active_users(self, count: int):
        """更新活跃用户数"""
        self.active_users.set(count)

    def update_workspace_count(self, count: int):
        """更新工作空间数量"""
        self.workspace_count.set(count)

    def record_workflow_throughput(self, throughput: float):
        """记录工作流吞吐量"""
        self.workflow_throughput.observe(throughput)

    def get_metrics(self) -> str:
        """获取Prometheus格式的指标"""
        return generate_latest(self.registry)

    def start_metrics_server(self, port: int = 8080):
        """启动指标HTTP服务器"""
        try:
            start_http_server(port, registry=self.registry)
            print(f"Metrics server started on port {port}")
        except Exception as e:
            print(f"Failed to start metrics server: {e}")

class MetricsMiddleware:
    """指标收集中间件"""

    def __init__(self, collector: Perfect21MetricsCollector):
        self.collector = collector

    def __call__(self, request, call_next):
        """ASGI中间件"""
        import asyncio
        return asyncio.create_task(self._process_request(request, call_next))

    async def _process_request(self, request, call_next):
        """处理请求并收集指标"""
        start_time = time.time()

        # 增加活跃连接数
        self.collector.api_active_connections.inc()

        try:
            response = await call_next(request)

            # 记录请求指标
            duration = time.time() - start_time
            method = request.method
            endpoint = request.url.path
            status_code = response.status_code

            self.collector.record_api_request(
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                duration=duration
            )

            return response

        except Exception as e:
            # 记录错误
            self.collector.record_error(
                error_type=type(e).__name__,
                severity='error',
                component='api'
            )
            raise
        finally:
            # 减少活跃连接数
            self.collector.api_active_connections.dec()

class MetricsUpdater:
    """后台指标更新器"""

    def __init__(self, collector: Perfect21MetricsCollector, update_interval: int = 30):
        self.collector = collector
        self.update_interval = update_interval
        self._running = False
        self._thread = None

    def start(self):
        """启动后台更新"""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._update_loop, daemon=True)
        self._thread.start()
        print(f"Metrics updater started (interval: {self.update_interval}s)")

    def stop(self):
        """停止后台更新"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def _update_loop(self):
        """更新循环"""
        while self._running:
            try:
                self.collector.update_system_metrics()
                time.sleep(self.update_interval)
            except Exception as e:
                print(f"Error in metrics update loop: {e}")
                time.sleep(self.update_interval)

# 全局指标收集器实例
metrics_collector = Perfect21MetricsCollector()
metrics_updater = MetricsUpdater(metrics_collector)

# 便捷函数
def record_api_request(method: str, endpoint: str, status_code: int, duration: float):
    """记录API请求"""
    metrics_collector.record_api_request(method, endpoint, status_code, duration)

def record_agent_execution(agent_name: str, status: str, duration: float):
    """记录Agent执行"""
    metrics_collector.record_agent_execution(agent_name, status, duration)

def record_git_operation(operation: str, status: str, duration: float):
    """记录Git操作"""
    metrics_collector.record_git_operation(operation, status, duration)

def record_error(error_type: str, severity: str = 'error', component: str = 'unknown'):
    """记录错误"""
    metrics_collector.record_error(error_type, severity, component)

def get_metrics() -> str:
    """获取指标数据"""
    return metrics_collector.get_metrics()

def start_metrics_collection(port: int = 8080, update_interval: int = 30):
    """启动指标收集"""
    metrics_updater.start()
    metrics_collector.start_metrics_server(port)