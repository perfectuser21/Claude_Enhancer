#!/usr/bin/env python3
"""
Perfect21 Monitoring System
完整的监控、追踪、健康检查、告警和审计系统
"""

from .metrics_collector import (
    Perfect21MetricsCollector,
    MetricsMiddleware,
    MetricsUpdater,
    metrics_collector,
    metrics_updater,
    record_api_request,
    record_agent_execution,
    record_git_operation,
    record_error,
    get_metrics,
    start_metrics_collection
)

from .trace_exporter import (
    Perfect21Tracer,
    Perfect21TracingMiddleware,
    Perfect21AgentTracer,
    tracer,
    agent_tracer,
    start_span,
    get_current_span,
    trace_agent_execution,
    trace_parallel_execution,
    trace_git_operation,
    trace_quality_check,
    configure_tracing,
    get_trace_summary
)

from .health_checker import (
    Perfect21HealthChecker,
    HealthCheck,
    HealthStatus,
    HealthCheckResult,
    SystemHealthCheck,
    DatabaseHealthCheck,
    GitHealthCheck,
    ServiceHealthCheck,
    Perfect21ComponentHealthCheck,
    health_checker,
    health_scheduler,
    run_health_checks,
    run_health_check,
    get_health_status,
    get_health_summary,
    add_service_health_check,
    start_health_monitoring
)

from .dashboard_config import (
    GrafanaDashboardGenerator,
    CustomDashboardConfig,
    generate_all_dashboards,
    save_dashboard_configs,
    create_monitoring_config
)

from .alert_manager import (
    AlertManager,
    Alert,
    AlertRule,
    AlertSeverity,
    AlertStatus,
    NotificationChannel,
    SlackNotificationChannel,
    EmailNotificationChannel,
    WebhookNotificationChannel,
    alert_manager,
    configure_slack_notifications,
    configure_email_notifications,
    configure_webhook_notifications,
    start_alerting,
    fire_custom_alert,
    get_alert_status,
    create_default_alert_rules
)

from .audit_logger import (
    Perfect21AuditLogger,
    AuditEvent,
    AuditEventType,
    AuditLevel,
    AuditFilter,
    AuditStorage,
    FileAuditStorage,
    audit_logger,
    log_user_login,
    log_api_request,
    log_agent_execution,
    log_security_violation,
    start_audit_logging,
    get_audit_summary,
    query_audit_events
)

__version__ = "1.0.0"

# 监控系统状态
_monitoring_started = False

def start_monitoring_system(config: dict = None):
    """启动完整的监控系统"""
    global _monitoring_started

    if _monitoring_started:
        return

    config = config or {}

    # 启动指标收集
    metrics_config = config.get('metrics', {})
    start_metrics_collection(
        port=metrics_config.get('port', 8080),
        update_interval=metrics_config.get('update_interval', 30)
    )

    # 配置分布式追踪
    tracing_config = config.get('tracing', {})
    configure_tracing(
        service_name=tracing_config.get('service_name', 'perfect21'),
        jaeger_host=tracing_config.get('jaeger_host'),
        file_output=tracing_config.get('file_output', 'logs/traces.jsonl')
    )

    # 启动健康检查
    health_config = config.get('health', {})
    start_health_monitoring(
        interval=health_config.get('interval', 60)
    )

    # 启动告警系统
    alerting_config = config.get('alerting', {})
    start_alerting(
        slack_webhook=alerting_config.get('slack_webhook'),
        email_config=alerting_config.get('email')
    )

    # 启动审计日志
    start_audit_logging()

    # 生成仪表板配置
    dashboard_config = config.get('dashboards', {})
    if dashboard_config.get('generate', True):
        save_dashboard_configs(
            output_dir=dashboard_config.get('output_dir', 'monitoring/dashboards')
        )

    _monitoring_started = True
    print("🚀 Perfect21 Monitoring System started successfully!")
    print("📊 Metrics: http://localhost:8080/metrics")
    print("🏥 Health: Available via health_checker")
    print("📈 Dashboards: monitoring/dashboards/")
    print("📝 Audit logs: logs/audit/")

def stop_monitoring_system():
    """停止监控系统"""
    global _monitoring_started

    if not _monitoring_started:
        return

    # 停止各个组件
    metrics_updater.stop()
    health_scheduler.stop()
    alert_manager.stop()
    audit_logger.stop()

    _monitoring_started = False
    print("🛑 Perfect21 Monitoring System stopped")

def get_monitoring_status():
    """获取监控系统状态"""
    return {
        'started': _monitoring_started,
        'metrics': {
            'collector_active': metrics_updater._running if hasattr(metrics_updater, '_running') else False,
            'last_update': getattr(metrics_updater, '_last_update', None)
        },
        'health': {
            'scheduler_active': health_scheduler._running if hasattr(health_scheduler, '_running') else False,
            'last_check': get_health_summary()
        },
        'alerting': {
            'manager_active': alert_manager.running,
            'active_alerts': len(alert_manager.active_alerts),
            'total_rules': len(alert_manager.rules),
            'total_channels': len(alert_manager.channels)
        },
        'audit': {
            'logger_active': audit_logger.running,
            'session_id': audit_logger._session_id
        },
        'tracing': {
            'service_name': tracer.service_name,
            'active_spans': len(tracer.spans),
            'finished_spans': len(tracer.finished_spans)
        }
    }

# 便捷的一体化监控装饰器
def monitor_function(func_name: str = None, track_performance: bool = True, log_errors: bool = True):
    """监控函数执行的装饰器"""
    def decorator(func):
        import functools
        import time

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            name = func_name or f"{func.__module__}.{func.__name__}"

            # 开始追踪
            with tracer.span(f"function:{name}") as span:
                start_time = time.time()

                try:
                    result = func(*args, **kwargs)

                    # 记录成功指标
                    if track_performance:
                        duration = time.time() - start_time
                        metrics_collector.record_agent_execution(name, "success", duration)
                        span.set_tag("duration", duration)
                        span.set_tag("success", True)

                    return result

                except Exception as e:
                    # 记录错误
                    if log_errors:
                        record_error(type(e).__name__, component=name)
                        span.set_error(e)

                    if track_performance:
                        duration = time.time() - start_time
                        metrics_collector.record_agent_execution(name, "error", duration)

                    raise

        return wrapper
    return decorator

# 监控系统健康检查
class MonitoringSystemHealthCheck(HealthCheck):
    """监控系统自身的健康检查"""

    def __init__(self):
        super().__init__("monitoring_system")

    async def _perform_check(self) -> HealthCheckResult:
        status = get_monitoring_status()

        issues = []
        if not status['started']:
            issues.append("Monitoring system not started")
        if not status['metrics']['collector_active']:
            issues.append("Metrics collector not active")
        if not status['health']['scheduler_active']:
            issues.append("Health scheduler not active")
        if not status['alerting']['manager_active']:
            issues.append("Alert manager not active")
        if not status['audit']['logger_active']:
            issues.append("Audit logger not active")

        if issues:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.DEGRADED,
                message=f"Monitoring issues: {', '.join(issues)}",
                details=status
            )
        else:
            return HealthCheckResult(
                name=self.name,
                status=HealthStatus.HEALTHY,
                message="All monitoring components operational",
                details=status
            )

# 添加监控系统自身的健康检查
health_checker.add_check(MonitoringSystemHealthCheck())

__all__ = [
    # 指标收集
    'Perfect21MetricsCollector', 'MetricsMiddleware', 'MetricsUpdater',
    'metrics_collector', 'metrics_updater',
    'record_api_request', 'record_agent_execution', 'record_git_operation', 'record_error',
    'get_metrics', 'start_metrics_collection',

    # 分布式追踪
    'Perfect21Tracer', 'Perfect21TracingMiddleware', 'Perfect21AgentTracer',
    'tracer', 'agent_tracer',
    'start_span', 'get_current_span',
    'trace_agent_execution', 'trace_parallel_execution', 'trace_git_operation', 'trace_quality_check',
    'configure_tracing', 'get_trace_summary',

    # 健康检查
    'Perfect21HealthChecker', 'HealthCheck', 'HealthStatus', 'HealthCheckResult',
    'SystemHealthCheck', 'DatabaseHealthCheck', 'GitHealthCheck', 'ServiceHealthCheck',
    'Perfect21ComponentHealthCheck', 'health_checker', 'health_scheduler',
    'run_health_checks', 'run_health_check', 'get_health_status', 'get_health_summary',
    'add_service_health_check', 'start_health_monitoring',

    # 仪表板配置
    'GrafanaDashboardGenerator', 'CustomDashboardConfig',
    'generate_all_dashboards', 'save_dashboard_configs', 'create_monitoring_config',

    # 告警管理
    'AlertManager', 'Alert', 'AlertRule', 'AlertSeverity', 'AlertStatus',
    'NotificationChannel', 'SlackNotificationChannel', 'EmailNotificationChannel', 'WebhookNotificationChannel',
    'alert_manager', 'configure_slack_notifications', 'configure_email_notifications', 'configure_webhook_notifications',
    'start_alerting', 'fire_custom_alert', 'get_alert_status', 'create_default_alert_rules',

    # 审计日志
    'Perfect21AuditLogger', 'AuditEvent', 'AuditEventType', 'AuditLevel', 'AuditFilter',
    'AuditStorage', 'FileAuditStorage', 'audit_logger',
    'log_user_login', 'log_api_request', 'log_agent_execution', 'log_security_violation',
    'start_audit_logging', 'get_audit_summary', 'query_audit_events',

    # 系统管理
    'start_monitoring_system', 'stop_monitoring_system', 'get_monitoring_status',
    'monitor_function', 'MonitoringSystemHealthCheck'
]