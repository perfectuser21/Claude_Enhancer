"""
Performance Optimization: Configuration Management
性能配置管理器 - 统一的性能优化配置中心
"""

import os
import yaml
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
from datetime import timedelta
import asyncio
from enum import Enum

logger = logging.getLogger(__name__)


class CacheStrategy(Enum):
    """缓存策略"""

    LRU = "lru"
    LFU = "lfu"
    TTL = "ttl"
    WRITE_THROUGH = "write_through"
    WRITE_BACK = "write_back"


class LoadBalanceAlgorithm(Enum):
    """负载均衡算法"""

    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    IP_HASH = "ip_hash"
    HEALTH_BASED = "health_based"


@dataclass
class RedisConfig:
    """Redis配置"""

    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None
    db: int = 0
    pool_size: int = 50
    timeout: int = 5
    retry_on_timeout: bool = True
    compression_enabled: bool = True
    compression_threshold: int = 1024
    default_ttl: int = 300
    max_connections: int = 100


@dataclass
class DatabaseConfig:
    """数据库优化配置"""

    url: str = ""
    pool_size: int = 20
    max_overflow: int = 30
    pool_timeout: int = 30
    pool_recycle: int = 3600
    slow_query_threshold: float = 1.0
    enable_query_cache: bool = True
    query_cache_ttl: int = 300
    enable_prepared_statements: bool = True
    statement_cache_size: int = 100
    connection_timeout: float = 10.0
    query_timeout: float = 30.0


@dataclass
class AsyncProcessorConfig:
    """异步处理器配置"""

    max_workers: int = 10
    max_queue_size: int = 1000
    worker_timeout: float = 300.0
    health_check_interval: float = 30.0
    stats_report_interval: float = 60.0
    cleanup_interval: float = 3600.0
    task_retention_hours: int = 24

    # 邮件配置
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    email_from: str = "noreply@claude-enhancer.com"

    # 消息队列配置
    rabbitmq_url: str = "amqp://localhost"

    # API配置
    api_timeout: float = 30.0
    api_retries: int = 3


@dataclass
class LoadBalancerConfig:
    """负载均衡器配置"""

    algorithm: LoadBalanceAlgorithm = LoadBalanceAlgorithm.WEIGHTED_ROUND_ROBIN
    health_check_enabled: bool = True
    health_check_interval: int = 30
    session_affinity: bool = False
    session_timeout: int = 3600
    max_retries: int = 3
    retry_delay: float = 0.1
    circuit_breaker_enabled: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60
    connection_timeout: float = 10.0
    read_timeout: float = 30.0


@dataclass
class MetricsConfig:
    """指标收集配置"""

    collection_interval: float = 10.0
    retention_period_hours: int = 24
    max_metrics_per_type: int = 10000
    enable_system_metrics: bool = True
    enable_application_metrics: bool = True
    enable_business_metrics: bool = True
    alert_check_interval: float = 30.0
    export_interval: float = 60.0
    export_format: str = "prometheus"
    export_file: Optional[str] = "/tmp/metrics.txt"


@dataclass
class PerformanceThresholds:
    """性能阈值配置"""

    # 响应时间阈值 (毫秒)
    response_time_warning: float = 500.0
    response_time_critical: float = 1000.0

    # CPU使用率阈值 (%)
    cpu_usage_warning: float = 70.0
    cpu_usage_critical: float = 85.0

    # 内存使用率阈值 (%)
    memory_usage_warning: float = 75.0
    memory_usage_critical: float = 90.0

    # 磁盘使用率阈值 (%)
    disk_usage_warning: float = 80.0
    disk_usage_critical: float = 95.0

    # 网络延迟阈值 (毫秒)
    network_latency_warning: float = 100.0
    network_latency_critical: float = 500.0

    # 错误率阈值 (%)
    error_rate_warning: float = 1.0
    error_rate_critical: float = 5.0

    # 并发连接数阈值
    connection_count_warning: int = 1000
    connection_count_critical: int = 5000


@dataclass
class OptimizationSettings:
    """优化设置"""

    # 缓存设置
    enable_l1_cache: bool = True
    enable_l2_cache: bool = True
    cache_strategy: CacheStrategy = CacheStrategy.LRU

    # 连接池设置
    enable_connection_pooling: bool = True
    connection_pool_preconnect: bool = True

    # 查询优化
    enable_query_optimization: bool = True
    enable_batch_operations: bool = True

    # 压缩设置
    enable_response_compression: bool = True
    compression_min_size: int = 1024

    # 异步处理
    enable_async_processing: bool = True
    async_queue_prioritization: bool = True

    # 负载均衡
    enable_load_balancing: bool = True
    enable_health_checks: bool = True

    # 监控设置
    enable_detailed_monitoring: bool = True
    enable_real_time_alerts: bool = True


@dataclass
class PerformanceConfig:
    """性能优化总配置"""

    # 组件配置
    redis: RedisConfig = field(default_factory=RedisConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    async_processor: AsyncProcessorConfig = field(default_factory=AsyncProcessorConfig)
    load_balancer: LoadBalancerConfig = field(default_factory=LoadBalancerConfig)
    metrics: MetricsConfig = field(default_factory=MetricsConfig)

    # 性能配置
    thresholds: PerformanceThresholds = field(default_factory=PerformanceThresholds)
    optimization: OptimizationSettings = field(default_factory=OptimizationSettings)

    # 全局设置
    service_name: str = "claude-enhancer"
    environment: str = "production"  # development, staging, production
    debug_mode: bool = False
    log_level: str = "INFO"

    # 配置文件路径
    config_file: Optional[str] = None
    config_refresh_interval: int = 300  # 5分钟


class PerformanceConfigManager:
    """性能配置管理器"""

    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or os.getenv(
            "PERFORMANCE_CONFIG_FILE", "performance.yaml"
        )
        self.config = PerformanceConfig()
        self._file_watcher_task = None
        self._last_modified = None

    async def initialize(self) -> PerformanceConfig:
        """初始化配置管理器"""
        try:
            pass  # Auto-fixed empty block
            # 加载配置文件
            await self.load_config()

            # 启动配置文件监控
            if self.config.config_refresh_interval > 0:
                self._file_watcher_task = asyncio.create_task(self._watch_config_file())

            logger.info(f"✅ 性能配置管理器初始化成功 - 环境: {self.config.environment}")
            return self.config

        except Exception as e:
            logger.error(f"❌ 性能配置管理器初始化失败: {e}")
            raise

    async def load_config(self):
        """加载配置文件"""
        config_path = Path(self.config_file)

        if not config_path.exists():
            logger.warning(f"⚠️ 配置文件不存在，使用默认配置: {self.config_file}")
            await self._create_default_config_file()
            return

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                if config_path.suffix.lower() in [".yaml", ".yml"]:
                    config_data = yaml.safe_load(f)
                else:
                    config_data = json.load(f)

            # 合并配置
            self._merge_config(config_data)

            # 验证配置
            self._validate_config()

            # 更新修改时间
            self._last_modified = config_path.stat().st_mtime

            logger.info(f"📋 配置文件加载成功: {self.config_file}")

        except Exception as e:
            logger.error(f"❌ 配置文件加载失败: {e}")
            raise

    def _merge_config(self, config_data: Dict[str, Any]):
        """合并配置数据"""
        # Redis配置
        if "redis" in config_data:
            redis_data = config_data["redis"]
            for key, value in redis_data.items():
                if hasattr(self.config.redis, key):
                    setattr(self.config.redis, key, value)

        # 数据库配置
        if "database" in config_data:
            db_data = config_data["database"]
            for key, value in db_data.items():
                if hasattr(self.config.database, key):
                    setattr(self.config.database, key, value)

        # 异步处理器配置
        if "async_processor" in config_data:
            async_data = config_data["async_processor"]
            for key, value in async_data.items():
                if hasattr(self.config.async_processor, key):
                    setattr(self.config.async_processor, key, value)

        # 负载均衡器配置
        if "load_balancer" in config_data:
            lb_data = config_data["load_balancer"]
            for key, value in lb_data.items():
                if hasattr(self.config.load_balancer, key):
                    if key == "algorithm" and isinstance(value, str):
                        setattr(
                            self.config.load_balancer, key, LoadBalanceAlgorithm(value)
                        )
                    else:
                        setattr(self.config.load_balancer, key, value)

        # 指标配置
        if "metrics" in config_data:
            metrics_data = config_data["metrics"]
            for key, value in metrics_data.items():
                if hasattr(self.config.metrics, key):
                    setattr(self.config.metrics, key, value)

        # 阈值配置
        if "thresholds" in config_data:
            threshold_data = config_data["thresholds"]
            for key, value in threshold_data.items():
                if hasattr(self.config.thresholds, key):
                    setattr(self.config.thresholds, key, value)

        # 优化设置
        if "optimization" in config_data:
            opt_data = config_data["optimization"]
            for key, value in opt_data.items():
                if hasattr(self.config.optimization, key):
                    if key == "cache_strategy" and isinstance(value, str):
                        setattr(self.config.optimization, key, CacheStrategy(value))
                    else:
                        setattr(self.config.optimization, key, value)

        # 全局设置
        global_keys = [
            "service_name",
            "environment",
            "debug_mode",
            "log_level",
            "config_refresh_interval",
        ]
        for key in global_keys:
            if key in config_data:
                setattr(self.config, key, config_data[key])

    def _validate_config(self):
        """验证配置合法性"""
        errors = []

        # 验证Redis配置
        if self.config.redis.port <= 0 or self.config.redis.port > 65535:
            errors.append("Redis端口必须在1-65535范围内")

        if self.config.redis.pool_size <= 0:
            errors.append("Redis连接池大小必须大于0")

        # 验证数据库配置
        if not self.config.database.url:
            errors.append("数据库URL不能为空")

        if self.config.database.pool_size <= 0:
            errors.append("数据库连接池大小必须大于0")

        # 验证异步处理器配置
        if self.config.async_processor.max_workers <= 0:
            errors.append("异步处理器工作进程数必须大于0")

        # 验证阈值配置
        if (
            self.config.thresholds.response_time_warning
            >= self.config.thresholds.response_time_critical
        ):
            errors.append("响应时间警告阈值必须小于严重阈值")

        if (
            self.config.thresholds.cpu_usage_warning
            >= self.config.thresholds.cpu_usage_critical
        ):
            errors.append("CPU使用率警告阈值必须小于严重阈值")

        if errors:
            raise ValueError(f"配置验证失败:\n" + "\n".join(f"- {error}" for error in errors))

    async def _create_default_config_file(self):
        """创建默认配置文件"""
        default_config = {
            "service_name": "claude-enhancer",
            "environment": "production",
            "debug_mode": False,
            "log_level": "INFO",
            "config_refresh_interval": 300,
            "redis": {
                "host": "localhost",
                "port": 6379,
                "db": 0,
                "pool_size": 50,
                "timeout": 5,
                "compression_enabled": True,
                "default_ttl": 300,
            },
            "database": {
                "pool_size": 20,
                "max_overflow": 30,
                "pool_timeout": 30,
                "slow_query_threshold": 1.0,
                "enable_query_cache": True,
                "query_cache_ttl": 300,
            },
            "async_processor": {
                "max_workers": 10,
                "max_queue_size": 1000,
                "worker_timeout": 300.0,
                "smtp_host": "localhost",
                "smtp_port": 587,
                "api_timeout": 30.0,
            },
            "load_balancer": {
                "algorithm": "weighted_round_robin",
                "health_check_enabled": True,
                "health_check_interval": 30,
                "circuit_breaker_enabled": True,
                "connection_timeout": 10.0,
            },
            "metrics": {
                "collection_interval": 10.0,
                "retention_period_hours": 24,
                "enable_system_metrics": True,
                "export_format": "prometheus",
            },
            "thresholds": {
                "response_time_warning": 500.0,
                "response_time_critical": 1000.0,
                "cpu_usage_warning": 70.0,
                "cpu_usage_critical": 85.0,
                "memory_usage_warning": 75.0,
                "memory_usage_critical": 90.0,
                "error_rate_warning": 1.0,
                "error_rate_critical": 5.0,
            },
            "optimization": {
                "enable_l1_cache": True,
                "enable_l2_cache": True,
                "cache_strategy": "lru",
                "enable_connection_pooling": True,
                "enable_query_optimization": True,
                "enable_response_compression": True,
                "enable_async_processing": True,
                "enable_load_balancing": True,
                "enable_detailed_monitoring": True,
            },
        }

        try:
            config_path = Path(self.config_file)
            config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(config_path, "w", encoding="utf-8") as f:
                if config_path.suffix.lower() in [".yaml", ".yml"]:
                    yaml.dump(default_config, f, default_flow_style=False, indent=2)
                else:
                    json.dump(default_config, f, indent=2)

            logger.info(f"📁 创建默认配置文件: {self.config_file}")

        except Exception as e:
            logger.error(f"❌ 创建默认配置文件失败: {e}")

    async def _watch_config_file(self):
        """监控配置文件变化"""
        while True:
            try:
                await asyncio.sleep(self.config.config_refresh_interval)

                config_path = Path(self.config_file)
                if not config_path.exists():
                    continue

                current_modified = config_path.stat().st_mtime
                if (
                    self._last_modified is None
                    or current_modified > self._last_modified
                ):
                    logger.info("🔄 检测到配置文件变化，重新加载...")
                    await self.load_config()
                    logger.info("✅ 配置文件重新加载完成")

            except Exception as e:
                logger.error(f"❌ 配置文件监控失败: {e}")

    def get_config(self) -> PerformanceConfig:
        """获取当前配置"""
        return self.config

    async def update_config(self, updates: Dict[str, Any]):
        """更新配置"""
        try:
            pass  # Auto-fixed empty block
            # 备份当前配置
            backup_config = self.config

            # 应用更新
            self._merge_config(updates)

            # 验证配置
            self._validate_config()

            # 保存到文件
            await self._save_config_to_file()

            logger.info("✅ 配置更新成功")

        except Exception as e:
            pass  # Auto-fixed empty block
            # 恢复备份配置
            self.config = backup_config
            logger.error(f"❌ 配置更新失败，已恢复: {e}")
            raise

    async def _save_config_to_file(self):
        """保存配置到文件"""
        config_data = {
            "service_name": self.config.service_name,
            "environment": self.config.environment,
            "debug_mode": self.config.debug_mode,
            "log_level": self.config.log_level,
            "config_refresh_interval": self.config.config_refresh_interval,
            "redis": {
                "host": self.config.redis.host,
                "port": self.config.redis.port,
                "db": self.config.redis.db,
                "pool_size": self.config.redis.pool_size,
                "timeout": self.config.redis.timeout,
                "compression_enabled": self.config.redis.compression_enabled,
                "default_ttl": self.config.redis.default_ttl,
            },
            "database": {
                "pool_size": self.config.database.pool_size,
                "max_overflow": self.config.database.max_overflow,
                "pool_timeout": self.config.database.pool_timeout,
                "slow_query_threshold": self.config.database.slow_query_threshold,
                "enable_query_cache": self.config.database.enable_query_cache,
                "query_cache_ttl": self.config.database.query_cache_ttl,
            },
            "thresholds": {
                "response_time_warning": self.config.thresholds.response_time_warning,
                "response_time_critical": self.config.thresholds.response_time_critical,
                "cpu_usage_warning": self.config.thresholds.cpu_usage_warning,
                "cpu_usage_critical": self.config.thresholds.cpu_usage_critical,
                "memory_usage_warning": self.config.thresholds.memory_usage_warning,
                "memory_usage_critical": self.config.thresholds.memory_usage_critical,
                "error_rate_warning": self.config.thresholds.error_rate_warning,
                "error_rate_critical": self.config.thresholds.error_rate_critical,
            },
            "optimization": {
                "enable_l1_cache": self.config.optimization.enable_l1_cache,
                "enable_l2_cache": self.config.optimization.enable_l2_cache,
                "cache_strategy": self.config.optimization.cache_strategy.value,
                "enable_connection_pooling": self.config.optimization.enable_connection_pooling,
                "enable_query_optimization": self.config.optimization.enable_query_optimization,
                "enable_response_compression": self.config.optimization.enable_response_compression,
                "enable_async_processing": self.config.optimization.enable_async_processing,
                "enable_load_balancing": self.config.optimization.enable_load_balancing,
                "enable_detailed_monitoring": self.config.optimization.enable_detailed_monitoring,
            },
        }

        config_path = Path(self.config_file)
        with open(config_path, "w", encoding="utf-8") as f:
            if config_path.suffix.lower() in [".yaml", ".yml"]:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            else:
                json.dump(config_data, f, indent=2)

    def get_environment_specific_config(self) -> Dict[str, Any]:
        """获取环境特定配置"""
        env_config = {
            "development": {
                "debug_mode": True,
                "log_level": "DEBUG",
                "redis": {"pool_size": 10},
                "database": {"pool_size": 5},
                "metrics": {"collection_interval": 5.0},
            },
            "staging": {
                "debug_mode": False,
                "log_level": "INFO",
                "redis": {"pool_size": 20},
                "database": {"pool_size": 10},
                "metrics": {"collection_interval": 10.0},
            },
            "production": {
                "debug_mode": False,
                "log_level": "WARNING",
                "redis": {"pool_size": 50},
                "database": {"pool_size": 20},
                "metrics": {"collection_interval": 10.0},
            },
        }

        return env_config.get(self.config.environment, {})

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            config_path = Path(self.config_file)
            return config_path.exists() and self.config is not None
        except:
            return False

    async def shutdown(self):
        """关闭配置管理器"""
        if self._file_watcher_task:
            self._file_watcher_task.cancel()
            try:
                await self._file_watcher_task
            except asyncio.CancelledError:
                pass

        logger.info("✅ 性能配置管理器已关闭")


# 全局配置管理器实例
_config_manager: Optional[PerformanceConfigManager] = None


async def get_performance_config(
    config_file: Optional[str] = None,
) -> PerformanceConfig:
    """获取性能配置（单例模式）"""
    global _config_manager

    if _config_manager is None:
        _config_manager = PerformanceConfigManager(config_file)
        await _config_manager.initialize()

    return _config_manager.get_config()


def get_config_manager() -> Optional[PerformanceConfigManager]:
    """获取配置管理器实例"""
    return _config_manager


# 环境变量支持
def load_config_from_env() -> Dict[str, Any]:
    """从环境变量加载配置"""
    env_config = {}

    # Redis配置
    if os.getenv("REDIS_HOST"):
        env_config.setdefault("redis", {})["host"] = os.getenv("REDIS_HOST")
    if os.getenv("REDIS_PORT"):
        env_config.setdefault("redis", {})["port"] = int(os.getenv("REDIS_PORT"))
    if os.getenv("REDIS_PASSWORD"):
        env_config.setdefault("redis", {})["password"] = os.getenv("REDIS_PASSWORD")

    # 数据库配置
    if os.getenv("DATABASE_URL"):
        env_config.setdefault("database", {})["url"] = os.getenv("DATABASE_URL")

    # 服务配置
    if os.getenv("SERVICE_NAME"):
        env_config["service_name"] = os.getenv("SERVICE_NAME")
    if os.getenv("ENVIRONMENT"):
        env_config["environment"] = os.getenv("ENVIRONMENT")
    if os.getenv("DEBUG_MODE"):
        env_config["debug_mode"] = os.getenv("DEBUG_MODE").lower() == "true"

    return env_config
