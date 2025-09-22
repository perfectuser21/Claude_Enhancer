"""
Perfect21 Performance Optimization Core Module
性能优化核心模块 - 统一导出所有性能优化组件
"""

from .cache import CacheManager, CacheConfig, cache_result
from .database_optimizer import DatabaseOptimizer, DatabaseConfig, optimized_query
from .async_processor import (
    AsyncProcessor,
    AsyncProcessorConfig,
    TaskPriority,
    async_task,
)
from .load_balancer import LoadBalancer, LoadBalancerConfig, Server, LoadBalanceStrategy
from .metrics_collector import MetricsCollector, MetricsConfig, MetricType, Alert
from .performance_config import (
    PerformanceConfigManager,
    PerformanceConfig,
    get_performance_config,
    load_config_from_env,
)
from .performance_dashboard import PerformanceDashboard
from .performance_manager import (
    PerformanceManager,
    get_performance_manager,
    shutdown_performance_manager,
)

__all__ = [
    # 缓存组件
    "CacheManager",
    "CacheConfig",
    "cache_result",
    # 数据库优化组件
    "DatabaseOptimizer",
    "DatabaseConfig",
    "optimized_query",
    # 异步处理组件
    "AsyncProcessor",
    "AsyncProcessorConfig",
    "TaskPriority",
    "async_task",
    # 负载均衡组件
    "LoadBalancer",
    "LoadBalancerConfig",
    "Server",
    "LoadBalanceStrategy",
    # 指标收集组件
    "MetricsCollector",
    "MetricsConfig",
    "MetricType",
    "Alert",
    # 配置管理组件
    "PerformanceConfigManager",
    "PerformanceConfig",
    "get_performance_config",
    "load_config_from_env",
    # 监控仪表板组件
    "PerformanceDashboard",
    # 统一管理器
    "PerformanceManager",
    "get_performance_manager",
    "shutdown_performance_manager",
]

# 版本信息
__version__ = "1.0.0"
__author__ = "Perfect21 Performance Team"
__description__ = "Enterprise-grade performance optimization system for Perfect21"

# 默认配置
DEFAULT_CONFIG = {
    "service_name": "perfect21",
    "environment": "production",
    "debug_mode": False,
    "performance_config_file": "performance.yaml",
}


def get_version():
    """获取版本信息"""
    return __version__


def get_components_info():
    """获取组件信息"""
    return {
        "cache": {
            "description": "Redis-based caching with L1/L2 strategy",
            "features": [
                "Multi-level caching",
                "Compression",
                "TTL management",
                "Hit rate tracking",
            ],
        },
        "database": {
            "description": "Database query optimization and connection pooling",
            "features": [
                "Query caching",
                "Slow query detection",
                "Connection pooling",
                "Performance analysis",
            ],
        },
        "async_processor": {
            "description": "Background task processing with queue management",
            "features": [
                "Priority queues",
                "Worker scaling",
                "Email/SMS/Webhook tasks",
                "Retry mechanisms",
            ],
        },
        "load_balancer": {
            "description": "Intelligent load balancing with health checks",
            "features": [
                "Multiple algorithms",
                "Health monitoring",
                "Circuit breakers",
                "Session affinity",
            ],
        },
        "metrics": {
            "description": "Comprehensive metrics collection and alerting",
            "features": [
                "System metrics",
                "Custom metrics",
                "Real-time alerts",
                "Prometheus export",
            ],
        },
        "dashboard": {
            "description": "Real-time performance monitoring dashboard",
            "features": [
                "WebSocket updates",
                "Visual metrics",
                "Alert notifications",
                "Export capabilities",
            ],
        },
    }


def validate_environment():
    """验证运行环境"""
    import sys
    import platform

    requirements = {"python_version": (3, 8), "platform": ["linux", "darwin", "win32"]}

    # 检查Python版本
    if sys.version_info < requirements["python_version"]:
        raise RuntimeError(
            f"Python {requirements['python_version'][0]}.{requirements['python_version'][1]}+ required, "
            f"found {sys.version_info.major}.{sys.version_info.minor}"
        )

    # 检查平台
    if sys.platform not in requirements["platform"]:
        raise RuntimeError(f"Unsupported platform: {sys.platform}")

    return True


# 性能优化工具函数
def create_optimized_app(app_name: str = "perfect21", config_file: str = None):
    """创建性能优化的应用实例"""
    import asyncio

    async def _create_app():
        # 验证环境
        validate_environment()

        # 初始化性能管理器
        manager = await get_performance_manager(app_name, config_file)

        return manager

    return asyncio.run(_create_app())


def setup_performance_middleware(app, performance_manager: PerformanceManager):
    """设置性能监控中间件"""
    from fastapi import Request
    import time

    @app.middleware("http")
    async def performance_middleware(request: Request, call_next):
        # 使用性能上下文
        async with performance_manager.performance_context("http_request"):
            start_time = time.time()

            response = await call_next(request)

            # 记录请求指标
            if performance_manager.metrics_collector:
                duration = time.time() - start_time
                performance_manager.metrics_collector.record_timer(
                    "http_request_duration",
                    duration,
                    labels={
                        "method": request.method,
                        "endpoint": str(request.url.path),
                        "status": str(response.status_code),
                    },
                )

                performance_manager.metrics_collector.increment_counter(
                    "http_requests_total",
                    labels={
                        "method": request.method,
                        "endpoint": str(request.url.path),
                        "status": str(response.status_code),
                    },
                )

            return response

    return app


# 快速启动函数
async def quick_start(
    service_name: str = "perfect21",
    config_file: str = None,
    enable_dashboard: bool = True,
) -> PerformanceManager:
    """快速启动性能优化系统"""
    try:
        # 获取性能管理器
        manager = await get_performance_manager(service_name, config_file)

        # print(f"✅ Perfect21 Performance System started for {service_name}")
        # print(f"📊 Dashboard available at: http://localhost:8000/ (if enabled)")
        # print(f"📈 Metrics export: {manager.config.metrics.export_file}")
        # print(f"🎯 Performance score calculation: Active")

        return manager

    except Exception as e:
        # print(f"❌ Failed to start performance system: {e}")
        raise


# 性能测试工具
class PerformanceTester:
    """性能测试工具"""

    def __init__(self, performance_manager: PerformanceManager):
        self.manager = performance_manager

    async def benchmark_cache(self, iterations: int = 1000):
        """缓存性能基准测试"""
        if not self.manager.cache_manager:
            return {"error": "Cache manager not available"}

        import time

        # 写入测试
        start_time = time.time()
        for i in range(iterations):
            await self.manager.cache_manager.set("benchmark", f"key_{i}", f"value_{i}")
        write_time = time.time() - start_time

        # 读取测试
        start_time = time.time()
        for i in range(iterations):
            await self.manager.cache_manager.get("benchmark", f"key_{i}")
        read_time = time.time() - start_time

        return {
            "iterations": iterations,
            "write_ops_per_sec": iterations / write_time,
            "read_ops_per_sec": iterations / read_time,
            "write_avg_latency": (write_time / iterations) * 1000,  # ms
            "read_avg_latency": (read_time / iterations) * 1000,  # ms
        }

    async def benchmark_database(self, iterations: int = 100):
        """数据库性能基准测试"""
        if not self.manager.database_optimizer:
            return {"error": "Database optimizer not available"}

        import time

        start_time = time.time()
        for i in range(iterations):
            await self.manager.database_optimizer.execute_optimized(
                "SELECT 1 as test_query", fetch_type="val"
            )
        total_time = time.time() - start_time

        return {
            "iterations": iterations,
            "queries_per_sec": iterations / total_time,
            "avg_query_time": (total_time / iterations) * 1000,  # ms
        }


def create_performance_tester(
    performance_manager: PerformanceManager,
) -> PerformanceTester:
    """创建性能测试器"""
    return PerformanceTester(performance_manager)
