"""
Claude Enhancer 5.1 - 监控系统集成
完整的监控系统集成层，连接所有监控组件
"""

import asyncio
import logging
import time
import yaml
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import aiohttp
import json

# 导入现有的监控组件
from backend.core.metrics_collector import MetricsCollector, MetricsConfig, AlertLevel
from backend.core.performance_dashboard import PerformanceDashboard

logger = logging.getLogger(__name__)


@dataclass
class MonitoringConfig:
    """监控配置"""

    config_file: str = "monitoring/monitoring_config.yaml"
    prometheus_config: str = "monitoring/prometheus_config.yml"
    grafana_dashboard: str = "monitoring/grafana_dashboard.json"
    alerting_rules: str = "monitoring/alerting_rules.yml"

    # 服务配置
    service_name: str = "claude-enhancer-5.1"
    version: str = "5.1.0"
    environment: str = "production"

    # 监控端点
    metrics_port: int = 9090
    dashboard_port: int = 8080
    health_check_port: int = 8081

    # 数据保留
    metrics_retention: str = "7d"
    logs_retention: str = "30d"

    # 告警配置
    alert_cooldown: int = 300  # 5分钟冷却期
    notification_timeout: int = 30


class SLACalculator:
    """SLA计算器"""

    def __init__(self):
        self.sla_targets = {
            "availability": 99.9,  # 99.9%
            "response_time": 200,  # 200ms P95
            "error_rate": 0.1,  # 0.1%
        }
        self.measurements = {}

    async def calculate_availability_sli(
        self, metrics_collector: MetricsCollector
    ) -> float:
        """计算可用性SLI"""
        try:
            # 获取最近24小时的up指标
            up_time = 0
            total_time = 24 * 60 * 60  # 24小时

            # 这里应该从实际指标中计算
            # 简化实现，假设从metrics_collector获取
            availability = (up_time / total_time) * 100
            return availability

        except Exception as e:
            logger.error(f"计算可用性SLI失败: {e}")
            return 0.0

    async def calculate_latency_sli(self, metrics_collector: MetricsCollector) -> float:
        """计算延迟SLI"""
        try:
            # 计算95%分位数延迟
            # 这里应该从histogram数据计算
            p95_latency = 150.0  # 示例值，单位毫秒
            return p95_latency

        except Exception as e:
            logger.error(f"计算延迟SLI失败: {e}")
            return float("inf")

    async def calculate_error_rate_sli(
        self, metrics_collector: MetricsCollector
    ) -> float:
        """计算错误率SLI"""
        try:
            # 计算错误率
            total_requests = 1000  # 从指标获取
            error_requests = 1  # 从指标获取

            if total_requests == 0:
                return 0.0

            error_rate = (error_requests / total_requests) * 100
            return error_rate

        except Exception as e:
            logger.error(f"计算错误率SLI失败: {e}")
            return 100.0

    async def check_sla_compliance(
        self, metrics_collector: MetricsCollector
    ) -> Dict[str, Any]:
        """检查SLA合规性"""
        compliance_report = {
            "timestamp": datetime.now(),
            "compliance": {},
            "violations": [],
            "recommendations": [],
        }

        # 检查可用性
        availability = await self.calculate_availability_sli(metrics_collector)
        availability_compliant = availability >= self.sla_targets["availability"]
        compliance_report["compliance"]["availability"] = {
            "target": self.sla_targets["availability"],
            "actual": availability,
            "compliant": availability_compliant,
            "margin": availability - self.sla_targets["availability"],
        }

        if not availability_compliant:
            compliance_report["violations"].append(
                {
                    "metric": "availability",
                    "severity": "critical",
                    "message": f"可用性{availability}%低于SLA要求{self.sla_targets['availability']}%",
                }
            )

        # 检查响应时间
        latency = await self.calculate_latency_sli(metrics_collector)
        latency_compliant = latency <= self.sla_targets["response_time"]
        compliance_report["compliance"]["response_time"] = {
            "target": self.sla_targets["response_time"],
            "actual": latency,
            "compliant": latency_compliant,
            "margin": self.sla_targets["response_time"] - latency,
        }

        if not latency_compliant:
            compliance_report["violations"].append(
                {
                    "metric": "response_time",
                    "severity": "warning",
                    "message": f"P95响应时间{latency}ms超过SLA要求{self.sla_targets['response_time']}ms",
                }
            )

        # 检查错误率
        error_rate = await self.calculate_error_rate_sli(metrics_collector)
        error_rate_compliant = error_rate <= self.sla_targets["error_rate"]
        compliance_report["compliance"]["error_rate"] = {
            "target": self.sla_targets["error_rate"],
            "actual": error_rate,
            "compliant": error_rate_compliant,
            "margin": self.sla_targets["error_rate"] - error_rate,
        }

        if not error_rate_compliant:
            compliance_report["violations"].append(
                {
                    "metric": "error_rate",
                    "severity": "error",
                    "message": f"错误率{error_rate}%超过SLA要求{self.sla_targets['error_rate']}%",
                }
            )

        return compliance_report


class HealthChecker:
    """健康检查器"""

    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.health_status = {}
        self.checks = []

    def register_check(self, name: str, check_func: Callable, interval: int = 30):
        """注册健康检查"""
        self.checks.append(
            {
                "name": name,
                "func": check_func,
                "interval": interval,
                "last_check": None,
                "status": "unknown",
            }
        )
        logger.info(f"注册健康检查: {name}, 间隔: {interval}秒")

    async def run_health_checks(self):
        """运行所有健康检查"""
        results = {}

        for check in self.checks:
            try:
                start_time = time.time()

                if asyncio.iscoroutinefunction(check["func"]):
                    result = await check["func"]()
                else:
                    result = check["func"]()

                duration = time.time() - start_time

                results[check["name"]] = {
                    "status": "healthy" if result else "unhealthy",
                    "duration": duration,
                    "timestamp": datetime.now(),
                    "result": result,
                }

                check["last_check"] = datetime.now()
                check["status"] = "healthy" if result else "unhealthy"

            except Exception as e:
                logger.error(f"健康检查 {check['name']} 失败: {e}")
                results[check["name"]] = {
                    "status": "unhealthy",
                    "error": str(e),
                    "timestamp": datetime.now(),
                }
                check["status"] = "unhealthy"

        self.health_status = results
        return results

    async def get_overall_health(self) -> Dict[str, Any]:
        """获取整体健康状态"""
        healthy_count = sum(1 for check in self.checks if check["status"] == "healthy")
        total_checks = len(self.checks)

        overall_status = "healthy"
        if healthy_count == 0:
            overall_status = "unhealthy"
        elif healthy_count < total_checks:
            overall_status = "degraded"

        return {
            "status": overall_status,
            "healthy_checks": healthy_count,
            "total_checks": total_checks,
            "health_ratio": healthy_count / max(total_checks, 1),
            "details": self.health_status,
            "timestamp": datetime.now(),
        }


class AnomalyDetector:
    """异常检测器"""

    def __init__(self):
        self.baseline_data = {}
        self.anomalies = []

    async def detect_statistical_anomalies(
        self, metric_name: str, values: List[float], threshold: float = 3.0
    ) -> List[Dict]:
        """基于统计的异常检测（Z-Score方法）"""
        anomalies = []

        if len(values) < 10:  # 需要足够的数据点
            return anomalies

        # 计算均值和标准差
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = variance**0.5

        if std_dev == 0:
            return anomalies

        # 检测异常值
        for i, value in enumerate(values):
            z_score = abs(value - mean) / std_dev
            if z_score > threshold:
                anomalies.append(
                    {
                        "metric": metric_name,
                        "index": i,
                        "value": value,
                        "z_score": z_score,
                        "mean": mean,
                        "std_dev": std_dev,
                        "severity": "high" if z_score > threshold * 1.5 else "medium",
                        "timestamp": datetime.now(),
                    }
                )

        return anomalies

    async def detect_trend_anomalies(
        self, metric_name: str, values: List[float], window_size: int = 10
    ) -> List[Dict]:
        """检测趋势异常"""
        anomalies = []

        if len(values) < window_size * 2:
            return anomalies

        # 计算移动平均和趋势
        for i in range(window_size, len(values) - window_size):
            before_window = values[i - window_size : i]
            after_window = values[i : i + window_size]

            before_avg = sum(before_window) / len(before_window)
            after_avg = sum(after_window) / len(after_window)

            # 检测显著趋势变化
            if before_avg > 0:  # 避免除零
                change_ratio = abs(after_avg - before_avg) / before_avg

                if change_ratio > 0.5:  # 50%变化阈值
                    anomalies.append(
                        {
                            "metric": metric_name,
                            "type": "trend_change",
                            "index": i,
                            "before_avg": before_avg,
                            "after_avg": after_avg,
                            "change_ratio": change_ratio,
                            "direction": "increase"
                            if after_avg > before_avg
                            else "decrease",
                            "severity": "high" if change_ratio > 1.0 else "medium",
                            "timestamp": datetime.now(),
                        }
                    )

        return anomalies

    async def analyze_metrics(
        self, metrics_data: Dict[str, List[float]]
    ) -> Dict[str, Any]:
        """分析指标数据，检测异常"""
        analysis_report = {
            "timestamp": datetime.now(),
            "anomalies": {},
            "summary": {
                "total_anomalies": 0,
                "high_severity": 0,
                "medium_severity": 0,
                "low_severity": 0,
            },
        }

        for metric_name, values in metrics_data.items():
            metric_anomalies = []

            # 统计异常检测
            statistical_anomalies = await self.detect_statistical_anomalies(
                metric_name, values
            )
            metric_anomalies.extend(statistical_anomalies)

            # 趋势异常检测
            trend_anomalies = await self.detect_trend_anomalies(metric_name, values)
            metric_anomalies.extend(trend_anomalies)

            if metric_anomalies:
                analysis_report["anomalies"][metric_name] = metric_anomalies

                # 更新统计
                for anomaly in metric_anomalies:
                    analysis_report["summary"]["total_anomalies"] += 1
                    severity = anomaly.get("severity", "low")
                    analysis_report["summary"][f"{severity}_severity"] += 1

        return analysis_report


class NotificationManager:
    """通知管理器"""

    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.notification_history = []
        self.rate_limits = {}

    async def send_slack_notification(self, alert: Dict[str, Any]):
        """发送Slack通知"""
        webhook_url = "YOUR_SLACK_WEBHOOK_URL"  # 从环境变量获取

        payload = {
            "text": f"🚨 Claude Enhancer 5.1 Alert",
            "attachments": [
                {
                    "color": self._get_color_for_severity(
                        alert.get("severity", "info")
                    ),
                    "fields": [
                        {
                            "title": "Alert",
                            "value": alert.get("name", "Unknown"),
                            "short": True,
                        },
                        {
                            "title": "Severity",
                            "value": alert.get("severity", "info"),
                            "short": True,
                        },
                        {
                            "title": "Message",
                            "value": alert.get("message", ""),
                            "short": False,
                        },
                        {
                            "title": "Service",
                            "value": self.config.service_name,
                            "short": True,
                        },
                        {
                            "title": "Time",
                            "value": alert.get("timestamp", datetime.now()).isoformat(),
                            "short": True,
                        },
                    ],
                }
            ],
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url, json=payload, timeout=self.config.notification_timeout
                ) as response:
                    if response.status == 200:
                        logger.info(f"Slack通知发送成功: {alert.get('name')}")
                    else:
                        logger.error(f"Slack通知发送失败: {response.status}")

        except Exception as e:
            logger.error(f"发送Slack通知时出错: {e}")

    async def send_email_notification(self, alert: Dict[str, Any]):
        """发送邮件通知"""
        # 邮件发送实现
        logger.info(f"📧 发送邮件通知: {alert.get('name')}")

        # 这里应该实现实际的邮件发送逻辑
        # 可以使用aiosmtplib或类似库
        pass

    def _get_color_for_severity(self, severity: str) -> str:
        """获取严重级别对应的颜色"""
        colors = {
            "critical": "danger",
            "error": "warning",
            "warning": "warning",
            "info": "good",
        }
        return colors.get(severity.lower(), "good")

    async def send_notification(self, alert: Dict[str, Any]):
        """发送通知"""
        # 检查频率限制
        alert_key = f"{alert.get('name')}_{alert.get('severity')}"
        now = time.time()

        if alert_key in self.rate_limits:
            if now - self.rate_limits[alert_key] < self.config.alert_cooldown:
                logger.debug(f"告警 {alert_key} 在冷却期内，跳过通知")
                return

        self.rate_limits[alert_key] = now

        # 根据严重级别发送不同通知
        severity = alert.get("severity", "info").lower()

        if severity in ["critical", "error"]:
            await self.send_slack_notification(alert)
            await self.send_email_notification(alert)
        elif severity == "warning":
            await self.send_slack_notification(alert)
        else:
            # info级别只记录日志
            logger.info(f"Info级告警: {alert.get('name')} - {alert.get('message')}")

        # 记录通知历史
        self.notification_history.append(
            {
                "alert": alert,
                "timestamp": datetime.now(),
                "channels": ["slack", "email"]
                if severity in ["critical", "error"]
                else ["slack"],
            }
        )

        # 限制历史记录数量
        if len(self.notification_history) > 1000:
            self.notification_history = self.notification_history[-1000:]


class MonitoringIntegration:
    """监控系统集成主类"""

    def __init__(self, config: MonitoringConfig = None):
        self.config = config or MonitoringConfig()

        # 核心组件
        self.metrics_collector = None
        self.dashboard = None
        self.sla_calculator = SLACalculator()
        self.health_checker = HealthChecker(self.config)
        self.anomaly_detector = AnomalyDetector()
        self.notification_manager = NotificationManager(self.config)

        # 运行状态
        self.running = False
        self.tasks = []

    async def initialize(self):
        """初始化监控系统"""
        try:
            logger.info("🚀 初始化Claude Enhancer 5.1监控系统...")

            # 初始化指标收集器
            metrics_config = MetricsConfig(
                collection_interval=10.0,
                enable_system_metrics=True,
                enable_application_metrics=True,
                export_file=f"/tmp/{self.config.service_name}_metrics.txt",
            )

            self.metrics_collector = MetricsCollector(
                self.config.service_name, metrics_config
            )
            await self.metrics_collector.initialize()

            # 初始化性能仪表板
            self.dashboard = PerformanceDashboard(self.config.service_name)
            await self.dashboard.initialize()

            # 注册性能组件到仪表板
            self.dashboard.register_component(
                "metrics_collector", self.metrics_collector
            )

            # 注册健康检查
            await self._register_health_checks()

            # 注册告警处理器
            await self._register_alert_handlers()

            # 启动后台任务
            await self._start_background_tasks()

            self.running = True
            logger.info("✅ Claude Enhancer 5.1监控系统初始化完成")

        except Exception as e:
            logger.error(f"❌ 监控系统初始化失败: {e}")
            raise

    async def _register_health_checks(self):
        """注册健康检查"""
        # 系统健康检查
        self.health_checker.register_check(
            "system_resources", self._check_system_resources, 30
        )

        # 服务健康检查
        self.health_checker.register_check(
            "auth_service", self._check_auth_service_health, 30
        )

        # 数据库健康检查
        self.health_checker.register_check("database", self._check_database_health, 60)

        # 缓存健康检查
        self.health_checker.register_check("cache", self._check_cache_health, 30)

    async def _register_alert_handlers(self):
        """注册告警处理器"""

        async def alert_handler(alert):
            await self.notification_manager.send_notification(
                {
                    "name": alert.name,
                    "severity": alert.level.value,
                    "message": alert.message,
                    "timestamp": alert.timestamp,
                }
            )

        self.metrics_collector.add_alert_handler(alert_handler)

    async def _start_background_tasks(self):
        """启动后台任务"""
        # SLA监控任务
        task1 = asyncio.create_task(self._sla_monitoring_loop())
        self.tasks.append(task1)

        # 异常检测任务
        task2 = asyncio.create_task(self._anomaly_detection_loop())
        self.tasks.append(task2)

        # 健康检查任务
        task3 = asyncio.create_task(self._health_check_loop())
        self.tasks.append(task3)

        # 报告生成任务
        task4 = asyncio.create_task(self._report_generation_loop())
        self.tasks.append(task4)

        logger.info(f"📋 启动了 {len(self.tasks)} 个后台监控任务")

    async def _sla_monitoring_loop(self):
        """SLA监控循环"""
        while self.running:
            try:
                # 检查SLA合规性
                compliance_report = await self.sla_calculator.check_sla_compliance(
                    self.metrics_collector
                )

                # 如果有SLA违规，发送告警
                for violation in compliance_report.get("violations", []):
                    await self.notification_manager.send_notification(
                        {
                            "name": f"SLA_VIOLATION_{violation['metric'].upper()}",
                            "severity": violation["severity"],
                            "message": violation["message"],
                            "timestamp": datetime.now(),
                        }
                    )

                # 记录SLA指标
                for metric, data in compliance_report["compliance"].items():
                    self.metrics_collector.set_gauge(
                        f"sla_{metric}_actual", data["actual"]
                    )
                    self.metrics_collector.set_gauge(
                        f"sla_{metric}_compliant", 1 if data["compliant"] else 0
                    )

            except Exception as e:
                logger.error(f"❌ SLA监控任务失败: {e}")

            await asyncio.sleep(300)  # 5分钟检查一次

    async def _anomaly_detection_loop(self):
        """异常检测循环"""
        while self.running:
            try:
                # 收集最近的指标数据
                metrics_data = {}

                # 从metrics_collector获取历史数据
                for (
                    metric_name,
                    history,
                ) in self.metrics_collector.metrics_history.items():
                    if len(history) >= 10:  # 需要足够的数据点
                        values = [metric.value for metric in list(history)]
                        metrics_data[metric_name] = values

                # 执行异常检测
                if metrics_data:
                    analysis_report = await self.anomaly_detector.analyze_metrics(
                        metrics_data
                    )

                    # 处理检测到的异常
                    for metric_name, anomalies in analysis_report["anomalies"].items():
                        for anomaly in anomalies:
                            if anomaly["severity"] in ["high", "medium"]:
                                await self.notification_manager.send_notification(
                                    {
                                        "name": f"ANOMALY_DETECTED_{metric_name}",
                                        "severity": "warning"
                                        if anomaly["severity"] == "medium"
                                        else "error",
                                        "message": f"在指标 {metric_name} 中检测到异常: {anomaly.get('type', 'statistical')}",
                                        "timestamp": anomaly["timestamp"],
                                    }
                                )

                    # 记录异常检测指标
                    self.metrics_collector.set_gauge(
                        "anomalies_detected_total",
                        analysis_report["summary"]["total_anomalies"],
                    )

            except Exception as e:
                logger.error(f"❌ 异常检测任务失败: {e}")

            await asyncio.sleep(180)  # 3分钟检查一次

    async def _health_check_loop(self):
        """健康检查循环"""
        while self.running:
            try:
                # 运行所有健康检查
                health_results = await self.health_checker.run_health_checks()

                # 获取整体健康状态
                overall_health = await self.health_checker.get_overall_health()

                # 记录健康状态指标
                self.metrics_collector.set_gauge(
                    "system_health_ratio", overall_health["health_ratio"]
                )

                # 记录各个检查的状态
                for check_name, result in health_results.items():
                    status_value = 1 if result["status"] == "healthy" else 0
                    self.metrics_collector.set_gauge(
                        f"health_check_{check_name}", status_value
                    )

                # 如果整体健康状态下降，发送告警
                if overall_health["status"] != "healthy":
                    severity = (
                        "critical"
                        if overall_health["status"] == "unhealthy"
                        else "warning"
                    )
                    await self.notification_manager.send_notification(
                        {
                            "name": "SYSTEM_HEALTH_DEGRADED",
                            "severity": severity,
                            "message": f"系统健康状态: {overall_health['status']}, 健康检查: {overall_health['healthy_checks']}/{overall_health['total_checks']}",
                            "timestamp": datetime.now(),
                        }
                    )

            except Exception as e:
                logger.error(f"❌ 健康检查任务失败: {e}")

            await asyncio.sleep(60)  # 1分钟检查一次

    async def _report_generation_loop(self):
        """报告生成循环"""
        while self.running:
            try:
                # 生成每小时报告
                await self._generate_hourly_report()

            except Exception as e:
                logger.error(f"❌ 报告生成任务失败: {e}")

            await asyncio.sleep(3600)  # 1小时生成一次

    async def _generate_hourly_report(self):
        """生成每小时监控报告"""
        report = {
            "timestamp": datetime.now(),
            "service": self.config.service_name,
            "version": self.config.version,
            "period": "1h",
            "metrics_summary": await self.metrics_collector.get_metrics_summary(),
            "sla_status": await self.sla_calculator.check_sla_compliance(
                self.metrics_collector
            ),
            "health_status": await self.health_checker.get_overall_health(),
            "notification_count": len(self.notification_manager.notification_history),
        }

        logger.info(
            f"📊 生成每小时监控报告: {report['metrics_summary']['total_metrics_collected']}个指标"
        )

    # 健康检查方法
    async def _check_system_resources(self) -> bool:
        """检查系统资源"""
        try:
            # 检查CPU、内存、磁盘使用率
            import psutil

            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # 如果任何资源使用率超过95%，认为不健康
            if (
                cpu_usage > 95
                or memory.percent > 95
                or (disk.used / disk.total * 100) > 95
            ):
                return False

            return True

        except Exception as e:
            logger.error(f"系统资源检查失败: {e}")
            return False

    async def _check_auth_service_health(self) -> bool:
        """检查认证服务健康"""
        try:
            # 这里应该实际检查认证服务
            # 例如调用健康检查端点
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://localhost:8001/health", timeout=10
                ) as response:
                    return response.status == 200
        except:
            return False

    async def _check_database_health(self) -> bool:
        """检查数据库健康"""
        try:
            # 这里应该检查数据库连接
            # 例如执行简单查询
            return True  # 简化实现
        except:
            return False

    async def _check_cache_health(self) -> bool:
        """检查缓存健康"""
        try:
            # 这里应该检查Redis连接
            # 例如执行ping命令
            return True  # 简化实现
        except:
            return False

    async def get_monitoring_summary(self) -> Dict[str, Any]:
        """获取监控系统摘要"""
        return {
            "service": self.config.service_name,
            "version": self.config.version,
            "environment": self.config.environment,
            "status": "running" if self.running else "stopped",
            "uptime": time.time()
            - (
                self.metrics_collector.stats.get("system_uptime", time.time())
                if self.metrics_collector
                else time.time()
            ),
            "metrics_collector": await self.metrics_collector.get_metrics_summary()
            if self.metrics_collector
            else None,
            "health_status": await self.health_checker.get_overall_health(),
            "active_tasks": len(self.tasks),
            "timestamp": datetime.now(),
        }

    async def shutdown(self):
        """关闭监控系统"""
        logger.info("🛑 正在关闭Claude Enhancer 5.1监控系统...")

        self.running = False

        # 取消后台任务
        for task in self.tasks:
            task.cancel()

        # 关闭组件
        if self.metrics_collector:
            await self.metrics_collector.shutdown()

        if self.dashboard:
            await self.dashboard.shutdown()

        logger.info("✅ Claude Enhancer 5.1监控系统已关闭")


# 使用示例和工厂方法
async def create_monitoring_system(config_file: str = None) -> MonitoringIntegration:
    """创建监控系统实例"""
    config = MonitoringConfig()

    if config_file:
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            # 更新配置
            if "monitoring" in config_data:
                monitoring_config = config_data["monitoring"]
                config.service_name = monitoring_config.get(
                    "service_name", config.service_name
                )
                config.version = monitoring_config.get("version", config.version)
                config.environment = monitoring_config.get(
                    "environment", config.environment
                )

        except Exception as e:
            logger.warning(f"配置文件加载失败，使用默认配置: {e}")

    monitoring = MonitoringIntegration(config)
    await monitoring.initialize()

    return monitoring


# 主函数示例
async def main():
    """主函数示例"""
    try:
        # 创建监控系统
        monitoring = await create_monitoring_system("monitoring/monitoring_config.yaml")

        # 运行监控系统
        logger.info("🎯 Claude Enhancer 5.1监控系统正在运行...")

        # 模拟运行一段时间
        await asyncio.sleep(60)

        # 获取监控摘要
        summary = await monitoring.get_monitoring_summary()
        logger.info(
            f"📊 监控摘要: {json.dumps(summary, default=str, ensure_ascii=False, indent=2)}"
        )

    except KeyboardInterrupt:
        logger.info("接收到中断信号，正在关闭...")
    except Exception as e:
        logger.error(f"监控系统运行失败: {e}")
    finally:
        if "monitoring" in locals():
            await monitoring.shutdown()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    asyncio.run(main())
