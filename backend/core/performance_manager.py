"""
Performance Optimization: Unified Performance Manager
统一性能管理器 - 整合所有性能优化组件的中央控制系统
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

# 导入性能组件
from .cache import CacheManager, CacheConfig
from .database_optimizer import DatabaseOptimizer, DatabaseConfig
from .async_processor import AsyncProcessor, AsyncProcessorConfig
from .load_balancer import LoadBalancer, LoadBalancerConfig, Server
from .metrics_collector import MetricsCollector, MetricsConfig
from .performance_config import PerformanceConfigManager, PerformanceConfig
from .performance_dashboard import PerformanceDashboard

logger = logging.getLogger(__name__)


@dataclass
class PerformanceReport:
    """性能报告"""

    timestamp: datetime
    overall_score: float  # 0-100
    response_time_p95: float
    cache_hit_rate: float
    database_performance: float
    system_health: str
    bottlenecks: List[str]
    recommendations: List[str]
    metrics_summary: Dict[str, Any]


class PerformanceManager:
    """统一性能管理器 - 企业级性能优化系统的中央控制器"""

    def __init__(
        self, service_name: str = "claude-enhancer", config_file: Optional[str] = None
    ):
        self.service_name = service_name
        self.config_manager = PerformanceConfigManager(config_file)
        self.config: Optional[PerformanceConfig] = None

        # 性能组件
        self.cache_manager: Optional[CacheManager] = None
        self.database_optimizer: Optional[DatabaseOptimizer] = None
        self.async_processor: Optional[AsyncProcessor] = None
        self.load_balancer: Optional[LoadBalancer] = None
        self.metrics_collector: Optional[MetricsCollector] = None
        self.dashboard: Optional[PerformanceDashboard] = None

        # 状态管理
        self.initialized = False
        self.running = False
        self.start_time = time.time()

        # 性能统计
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time": 0.0,
            "cache_hit_count": 0,
            "cache_miss_count": 0,
            "db_query_count": 0,
            "async_task_count": 0,
        }

    async def initialize(self) -> bool:
        """初始化性能管理器"""
        try:
            logger.info(f"🚀 正在初始化性能管理器 - 服务: {self.service_name}")

            # 1. 加载配置
            self.config = await self.config_manager.initialize()
            logger.info(f"✅ 配置加载完成 - 环境: {self.config.environment}")

            # 2. 初始化指标收集器（优先初始化，其他组件需要它）
            if self.config.optimization.enable_detailed_monitoring:
                await self._initialize_metrics_collector()

            # 3. 初始化缓存管理器
            if self.config.optimization.enable_l2_cache:
                await self._initialize_cache_manager()

            # 4. 初始化数据库优化器
            if self.config.optimization.enable_query_optimization:
                await self._initialize_database_optimizer()

            # 5. 初始化异步处理器
            if self.config.optimization.enable_async_processing:
                await self._initialize_async_processor()

            # 6. 初始化负载均衡器
            if self.config.optimization.enable_load_balancing:
                await self._initialize_load_balancer()

            # 7. 初始化监控仪表板
            await self._initialize_dashboard()

            # 8. 启动后台任务
            asyncio.create_task(self._performance_monitoring_loop())
            asyncio.create_task(self._health_check_loop())
            asyncio.create_task(self._optimization_loop())

            self.initialized = True
            self.running = True

            logger.info("✅ 性能管理器初始化完成")
            return True

        except Exception as e:
            logger.error(f"❌ 性能管理器初始化失败: {e}")
            await self.shutdown()
            return False

    async def _initialize_metrics_collector(self):
        """初始化指标收集器"""
        try:
            metrics_config = MetricsConfig(
                collection_interval=self.config.metrics.collection_interval,
                retention_period_hours=self.config.metrics.retention_period_hours,
                enable_system_metrics=self.config.metrics.enable_system_metrics,
                enable_application_metrics=self.config.metrics.enable_application_metrics,
                export_file=self.config.metrics.export_file,
            )

            self.metrics_collector = MetricsCollector(self.service_name, metrics_config)
            await self.metrics_collector.initialize()

            # 添加性能阈值告警
            self._setup_performance_alerts()

            logger.info("✅ 指标收集器初始化完成")

        except Exception as e:
            logger.error(f"❌ 指标收集器初始化失败: {e}")
            raise

    async def _initialize_cache_manager(self):
        """初始化缓存管理器"""
        try:
            cache_config = CacheConfig(
                host=self.config.redis.host,
                port=self.config.redis.port,
                password=self.config.redis.password,
                db=self.config.redis.db,
                pool_size=self.config.redis.pool_size,
                timeout=self.config.redis.timeout,
                compression_enabled=self.config.redis.compression_enabled,
                default_ttl=self.config.redis.default_ttl,
            )

            self.cache_manager = CacheManager(cache_config)
            await self.cache_manager.initialize()

            logger.info("✅ 缓存管理器初始化完成")

        except Exception as e:
            logger.error(f"❌ 缓存管理器初始化失败: {e}")
            raise

    async def _initialize_database_optimizer(self):
        """初始化数据库优化器"""
        try:
            db_config = DatabaseConfig(
                url=self.config.database.url,
                pool_size=self.config.database.pool_size,
                max_overflow=self.config.database.max_overflow,
                slow_query_threshold=self.config.database.slow_query_threshold,
                enable_query_cache=self.config.database.enable_query_cache,
                query_cache_ttl=self.config.database.query_cache_ttl,
            )

            self.database_optimizer = DatabaseOptimizer(db_config)
            await self.database_optimizer.initialize()

            logger.info("✅ 数据库优化器初始化完成")

        except Exception as e:
            logger.error(f"❌ 数据库优化器初始化失败: {e}")
            raise

    async def _initialize_async_processor(self):
        """初始化异步处理器"""
        try:
            async_config = AsyncProcessorConfig(
                max_workers=self.config.async_processor.max_workers,
                max_queue_size=self.config.async_processor.max_queue_size,
                smtp_host=self.config.async_processor.smtp_host,
                smtp_port=self.config.async_processor.smtp_port,
                rabbitmq_url=self.config.async_processor.rabbitmq_url,
            )

            self.async_processor = AsyncProcessor(async_config)
            await self.async_processor.initialize()

            logger.info("✅ 异步处理器初始化完成")

        except Exception as e:
            logger.error(f"❌ 异步处理器初始化失败: {e}")
            raise

    async def _initialize_load_balancer(self):
        """初始化负载均衡器"""
        try:
            lb_config = LoadBalancerConfig(
                algorithm=self.config.load_balancer.algorithm,
                health_check_enabled=self.config.load_balancer.health_check_enabled,
                health_check_interval=self.config.load_balancer.health_check_interval,
                circuit_breaker_enabled=self.config.load_balancer.circuit_breaker_enabled,
            )

            self.load_balancer = LoadBalancer(lb_config)
            await self.load_balancer.initialize()

            logger.info("✅ 负载均衡器初始化完成")

        except Exception as e:
            logger.error(f"❌ 负载均衡器初始化失败: {e}")
            raise

    async def _initialize_dashboard(self):
        """初始化监控仪表板"""
        try:
            self.dashboard = PerformanceDashboard(self.service_name)

            # 注册性能组件到仪表板
            if self.cache_manager:
                self.dashboard.register_component("cache_manager", self.cache_manager)
            if self.database_optimizer:
                self.dashboard.register_component(
                    "database_optimizer", self.database_optimizer
                )
            if self.async_processor:
                self.dashboard.register_component(
                    "async_processor", self.async_processor
                )
            if self.load_balancer:
                self.dashboard.register_component("load_balancer", self.load_balancer)
            if self.metrics_collector:
                self.dashboard.register_component(
                    "metrics_collector", self.metrics_collector
                )

            await self.dashboard.initialize()

            logger.info("✅ 监控仪表板初始化完成")

        except Exception as e:
            logger.error(f"❌ 监控仪表板初始化失败: {e}")
            raise

    def _setup_performance_alerts(self):
        """设置性能告警"""
        if not self.metrics_collector:
            return

        # 响应时间告警
        self.metrics_collector.add_alert_rule(
            "response_time_warning",
            "lb_avg_response_time",
            self.config.thresholds.response_time_warning,
            message="响应时间过高",
        )

        # CPU使用率告警
        self.metrics_collector.add_alert_rule(
            "cpu_usage_critical",
            "cpu_usage",
            self.config.thresholds.cpu_usage_critical,
            message="CPU使用率达到临界值",
        )

        # 内存使用率告警
        self.metrics_collector.add_alert_rule(
            "memory_usage_critical",
            "memory_usage",
            self.config.thresholds.memory_usage_critical,
            message="内存使用率达到临界值",
        )

        # 错误率告警
        self.metrics_collector.add_alert_rule(
            "error_rate_warning",
            "db_error_rate",
            self.config.thresholds.error_rate_warning,
            message="错误率过高",
        )

    @asynccontextmanager
    async def performance_context(self, operation_name: str):
        """性能监控上下文管理器"""
        start_time = time.time()

        # 记录开始
        if self.metrics_collector:
            self.metrics_collector.increment_counter(
                f"{operation_name}_requests_total",
                labels={"service": self.service_name},
            )

        try:
            yield

            # 记录成功
            duration = time.time() - start_time
            self.stats["successful_requests"] += 1
            self._update_avg_response_time(duration)

            if self.metrics_collector:
                self.metrics_collector.record_timer(
                    f"{operation_name}_duration",
                    duration,
                    labels={"service": self.service_name, "status": "success"},
                )

        except Exception as e:
            pass  # Auto-fixed empty block
            # 记录失败
            duration = time.time() - start_time
            self.stats["failed_requests"] += 1

            if self.metrics_collector:
                self.metrics_collector.record_timer(
                    f"{operation_name}_duration",
                    duration,
                    labels={"service": self.service_name, "status": "error"},
                )
                self.metrics_collector.increment_counter(
                    f"{operation_name}_errors_total",
                    labels={
                        "service": self.service_name,
                        "error_type": type(e).__name__,
                    },
                )

            raise

        finally:
            self.stats["total_requests"] += 1

    def _update_avg_response_time(self, duration: float):
        """更新平均响应时间"""
        if self.stats["successful_requests"] == 1:
            self.stats["avg_response_time"] = duration
        else:
            pass  # Auto-fixed empty block
            # 指数移动平均
            alpha = 0.1
            self.stats["avg_response_time"] = (
                alpha * duration + (1 - alpha) * self.stats["avg_response_time"]
            )

    async def _performance_monitoring_loop(self):
        """性能监控循环"""
        while self.running:
            try:
                pass  # Auto-fixed empty block
                # 收集性能指标
                await self._collect_performance_metrics()

                # 生成性能报告
                if self.stats["total_requests"] % 1000 == 0:  # 每1000个请求生成一次报告
                    report = await self.generate_performance_report()
                    logger.info(f"📊 性能报告 - 评分: {report.overall_score:.1f}/100")

            except Exception as e:
                logger.error(f"❌ 性能监控失败: {e}")

            await asyncio.sleep(30)  # 每30秒执行一次

    async def _collect_performance_metrics(self):
        """收集性能指标"""
        if not self.metrics_collector:
            return

        # 收集基础统计
        self.metrics_collector.set_gauge("total_requests", self.stats["total_requests"])
        self.metrics_collector.set_gauge(
            "successful_requests", self.stats["successful_requests"]
        )
        self.metrics_collector.set_gauge(
            "failed_requests", self.stats["failed_requests"]
        )
        self.metrics_collector.set_gauge(
            "avg_response_time", self.stats["avg_response_time"] * 1000
        )  # 转换为毫秒

        # 计算成功率
        if self.stats["total_requests"] > 0:
            success_rate = (
                self.stats["successful_requests"] / self.stats["total_requests"]
            ) * 100
            self.metrics_collector.set_gauge("success_rate", success_rate)

        # 服务运行时间
        uptime = time.time() - self.start_time
        self.metrics_collector.set_gauge("service_uptime", uptime)

    async def _health_check_loop(self):
        """健康检查循环"""
        while self.running:
            try:
                pass  # Auto-fixed empty block
                # 检查各组件健康状态
                health_status = await self.get_health_status()

                if self.metrics_collector:
                    for component, status in health_status.items():
                        self.metrics_collector.set_gauge(
                            f"{component}_health",
                            1.0 if status else 0.0,
                            labels={"service": self.service_name},
                        )

            except Exception as e:
                logger.error(f"❌ 健康检查失败: {e}")

            await asyncio.sleep(60)  # 每分钟检查一次

    async def _optimization_loop(self):
        """优化循环"""
        while self.running:
            try:
                pass  # Auto-fixed empty block
                # 自动优化建议
                await self._auto_optimization()

            except Exception as e:
                logger.error(f"❌ 自动优化失败: {e}")

            await asyncio.sleep(300)  # 每5分钟执行一次

    async def _auto_optimization(self):
        """自动优化"""
        # 这里可以实现自动优化逻辑
        # 例如：根据负载调整连接池大小、缓存策略等
        pass

    async def get_health_status(self) -> Dict[str, bool]:
        """获取健康状态"""
        health_status = {}

        try:
            if self.cache_manager:
                health_status["cache"] = await self.cache_manager.health_check()

            if self.database_optimizer:
                health_status["database"] = await self.database_optimizer.health_check()

            if self.async_processor:
                health_status[
                    "async_processor"
                ] = await self.async_processor.health_check()

            if self.load_balancer:
                health_status["load_balancer"] = await self.load_balancer.health_check()

            if self.metrics_collector:
                health_status["metrics"] = await self.metrics_collector.health_check()

            if self.dashboard:
                health_status["dashboard"] = await self.dashboard.health_check()

        except Exception as e:
            logger.error(f"❌ 健康状态检查失败: {e}")

        return health_status

    async def generate_performance_report(self) -> PerformanceReport:
        """生成性能报告"""
        try:
            pass  # Auto-fixed empty block
            # 计算整体评分
            overall_score = await self._calculate_performance_score()

            # 获取关键指标
            response_time_p95 = self.stats["avg_response_time"] * 1.2  # 估算P95
            cache_hit_rate = 0.0
            if self.cache_manager:
                cache_stats = await self.cache_manager.get_stats()
                cache_hit_rate = cache_stats.get("hit_rate", 0)

            # 数据库性能
            database_performance = 100.0
            if self.database_optimizer:
                db_stats = await self.database_optimizer.get_database_stats()
                if db_stats["avg_query_time"] > 0:
                    database_performance = max(
                        0, 100 - (db_stats["avg_query_time"] * 1000 / 10)
                    )

            # 系统健康状态
            health_status = await self.get_health_status()
            healthy_components = sum(1 for status in health_status.values() if status)
            total_components = len(health_status)

            if total_components == 0:
                system_health = "unknown"
            elif healthy_components == total_components:
                system_health = "healthy"
            elif healthy_components >= total_components * 0.8:
                system_health = "degraded"
            else:
                system_health = "unhealthy"

            # 识别瓶颈
            bottlenecks = await self._identify_bottlenecks()

            # 生成建议
            recommendations = await self._generate_recommendations(bottlenecks)

            return PerformanceReport(
                timestamp=datetime.now(),
                overall_score=overall_score,
                response_time_p95=response_time_p95,
                cache_hit_rate=cache_hit_rate,
                database_performance=database_performance,
                system_health=system_health,
                bottlenecks=bottlenecks,
                recommendations=recommendations,
                metrics_summary=self.stats.copy(),
            )

        except Exception as e:
            logger.error(f"❌ 性能报告生成失败: {e}")
            # 返回默认报告
            return PerformanceReport(
                timestamp=datetime.now(),
                overall_score=0.0,
                response_time_p95=0.0,
                cache_hit_rate=0.0,
                database_performance=0.0,
                system_health="unknown",
                bottlenecks=["无法生成报告"],
                recommendations=["检查系统状态"],
                metrics_summary={},
            )

    async def _calculate_performance_score(self) -> float:
        """计算性能评分"""
        score = 100.0

        # 响应时间评分（30%）
        avg_response_time_ms = self.stats["avg_response_time"] * 1000
        if avg_response_time_ms > 1000:
            score -= 30
        elif avg_response_time_ms > 500:
            score -= 20
        elif avg_response_time_ms > 200:
            score -= 10

        # 成功率评分（25%）
        if self.stats["total_requests"] > 0:
            success_rate = (
                self.stats["successful_requests"] / self.stats["total_requests"]
            )
            if success_rate < 0.95:
                score -= (1 - success_rate) * 25

        # 缓存命中率评分（20%）
        if self.cache_manager:
            cache_stats = await self.cache_manager.get_stats()
            hit_rate = cache_stats.get("hit_rate", 0) / 100
            if hit_rate < 0.8:
                score -= (0.8 - hit_rate) * 20

        # 系统健康评分（25%）
        health_status = await self.get_health_status()
        if health_status:
            healthy_ratio = sum(1 for status in health_status.values() if status) / len(
                health_status
            )
            score -= (1 - healthy_ratio) * 25

        return max(0.0, min(100.0, score))

    async def _identify_bottlenecks(self) -> List[str]:
        """识别性能瓶颈"""
        bottlenecks = []

        # 响应时间瓶颈
        if self.stats["avg_response_time"] > 1.0:
            bottlenecks.append("响应时间过长")

        # 缓存命中率瓶颈
        if self.cache_manager:
            cache_stats = await self.cache_manager.get_stats()
            if cache_stats.get("hit_rate", 0) < 80:
                bottlenecks.append("缓存命中率低")

        # 数据库性能瓶颈
        if self.database_optimizer:
            db_stats = await self.database_optimizer.get_database_stats()
            if db_stats.get("slow_query_count", 0) > 0:
                bottlenecks.append("存在慢查询")

        # 异步队列瓶颈
        if self.async_processor:
            queue_status = await self.async_processor.get_queue_status()
            if queue_status.get("queue_size", 0) > 100:
                bottlenecks.append("异步队列堆积")

        return bottlenecks

    async def _generate_recommendations(self, bottlenecks: List[str]) -> List[str]:
        """生成优化建议"""
        recommendations = []

        for bottleneck in bottlenecks:
            if "响应时间" in bottleneck:
                recommendations.append("考虑增加缓存层或优化数据库查询")
            elif "缓存命中率" in bottleneck:
                recommendations.append("调整缓存策略或增加缓存容量")
            elif "慢查询" in bottleneck:
                recommendations.append("优化数据库索引或重构查询语句")
            elif "队列堆积" in bottleneck:
                recommendations.append("增加异步处理工作进程数量")

        if not recommendations:
            recommendations.append("系统运行良好，继续保持")

        return recommendations

    async def shutdown(self):
        """关闭性能管理器"""
        logger.info("🛑 正在关闭性能管理器...")

        self.running = False

        # 按依赖顺序关闭组件
        components = [
            ("仪表板", self.dashboard),
            ("指标收集器", self.metrics_collector),
            ("负载均衡器", self.load_balancer),
            ("异步处理器", self.async_processor),
            ("数据库优化器", self.database_optimizer),
            ("缓存管理器", self.cache_manager),
            ("配置管理器", self.config_manager),
        ]

        for name, component in components:
            if component:
                try:
                    await component.shutdown()
                    logger.info(f"✅ {name}已关闭")
                except Exception as e:
                    logger.error(f"❌ {name}关闭失败: {e}")

        logger.info("✅ 性能管理器已完全关闭")


# 全局性能管理器实例
_performance_manager: Optional[PerformanceManager] = None


async def get_performance_manager(
    service_name: str = "claude-enhancer", config_file: Optional[str] = None
) -> PerformanceManager:
    """获取性能管理器实例（单例模式）"""
    global _performance_manager

    if _performance_manager is None:
        _performance_manager = PerformanceManager(service_name, config_file)
        await _performance_manager.initialize()

    return _performance_manager


async def shutdown_performance_manager():
    """关闭全局性能管理器"""
    global _performance_manager

    if _performance_manager:
        await _performance_manager.shutdown()
        _performance_manager = None
