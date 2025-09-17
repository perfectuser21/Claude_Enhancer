#!/usr/bin/env python3
"""
Alert Manager - Perfect21 Intelligent Alert System
智能告警系统，支持多渠道通知、告警聚合和智能降噪
"""

import time
import json
import asyncio
import hashlib
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import queue
import logging

class AlertSeverity(Enum):
    """告警严重程度"""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

class AlertStatus(Enum):
    """告警状态"""
    FIRING = "firing"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

@dataclass
class Alert:
    """告警对象"""
    name: str
    message: str
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.FIRING
    labels: Dict[str, str] = None
    annotations: Dict[str, str] = None
    starts_at: datetime = None
    ends_at: Optional[datetime] = None
    generator_url: str = ""
    fingerprint: str = ""

    def __post_init__(self):
        if self.labels is None:
            self.labels = {}
        if self.annotations is None:
            self.annotations = {}
        if self.starts_at is None:
            self.starts_at = datetime.now()
        if not self.fingerprint:
            self.fingerprint = self._generate_fingerprint()

    def _generate_fingerprint(self) -> str:
        """生成告警指纹"""
        content = f"{self.name}:{self.message}:{json.dumps(sorted(self.labels.items()))}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    @property
    def duration(self) -> timedelta:
        """获取告警持续时间"""
        end_time = self.ends_at or datetime.now()
        return end_time - self.starts_at

    def resolve(self):
        """解决告警"""
        self.status = AlertStatus.RESOLVED
        self.ends_at = datetime.now()

    def suppress(self):
        """抑制告警"""
        self.status = AlertStatus.SUPPRESSED

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result['severity'] = self.severity.value
        result['status'] = self.status.value
        result['starts_at'] = self.starts_at.isoformat()
        result['ends_at'] = self.ends_at.isoformat() if self.ends_at else None
        result['duration_seconds'] = self.duration.total_seconds()
        return result

class AlertRule:
    """告警规则"""

    def __init__(self,
                 name: str,
                 condition: str,
                 threshold: float,
                 duration: timedelta,
                 severity: AlertSeverity,
                 message: str,
                 labels: Dict[str, str] = None,
                 annotations: Dict[str, str] = None):
        self.name = name
        self.condition = condition
        self.threshold = threshold
        self.duration = duration
        self.severity = severity
        self.message = message
        self.labels = labels or {}
        self.annotations = annotations or {}
        self.last_check = None
        self.firing_since = None

    def evaluate(self, metrics: Dict[str, float]) -> Optional[Alert]:
        """评估告警规则"""
        try:
            # 简化的条件评估（实际应用中需要更复杂的表达式解析）
            metric_value = metrics.get(self.condition.split()[0], 0)

            # 检查阈值
            if self._check_condition(metric_value):
                if self.firing_since is None:
                    self.firing_since = datetime.now()

                # 检查持续时间
                if datetime.now() - self.firing_since >= self.duration:
                    return Alert(
                        name=self.name,
                        message=self.message.format(value=metric_value, threshold=self.threshold),
                        severity=self.severity,
                        labels=self.labels.copy(),
                        annotations=self.annotations.copy()
                    )
            else:
                self.firing_since = None

            return None

        except Exception as e:
            logging.error(f"Error evaluating alert rule {self.name}: {e}")
            return None

    def _check_condition(self, value: float) -> bool:
        """检查条件是否满足"""
        if ">" in self.condition:
            return value > self.threshold
        elif "<" in self.condition:
            return value < self.threshold
        elif "==" in self.condition:
            return abs(value - self.threshold) < 0.001
        return False

class NotificationChannel:
    """通知渠道基类"""

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.enabled = config.get('enabled', True)

    async def send(self, alert: Alert) -> bool:
        """发送通知"""
        if not self.enabled:
            return False
        return await self._send_notification(alert)

    async def _send_notification(self, alert: Alert) -> bool:
        """子类实现的具体发送逻辑"""
        raise NotImplementedError

class SlackNotificationChannel(NotificationChannel):
    """Slack通知渠道"""

    async def _send_notification(self, alert: Alert) -> bool:
        try:
            import aiohttp

            webhook_url = self.config.get('webhook_url')
            if not webhook_url:
                logging.error("Slack webhook URL not configured")
                return False

            # 构建Slack消息
            color = {
                AlertSeverity.CRITICAL: "danger",
                AlertSeverity.WARNING: "warning",
                AlertSeverity.INFO: "good"
            }.get(alert.severity, "warning")

            payload = {
                "channel": self.config.get('channel', '#alerts'),
                "username": self.config.get('username', 'Perfect21 Monitor'),
                "icon_emoji": self.config.get('icon', ':warning:'),
                "attachments": [{
                    "color": color,
                    "title": f"🚨 {alert.name}",
                    "text": alert.message,
                    "fields": [
                        {"title": "Severity", "value": alert.severity.value, "short": True},
                        {"title": "Status", "value": alert.status.value, "short": True},
                        {"title": "Duration", "value": str(alert.duration), "short": True}
                    ],
                    "timestamp": int(alert.starts_at.timestamp()),
                    "footer": "Perfect21 Monitor"
                }]
            }

            # 添加标签和注解
            if alert.labels:
                labels_text = "\n".join([f"• {k}: {v}" for k, v in alert.labels.items()])
                payload["attachments"][0]["fields"].append({
                    "title": "Labels",
                    "value": labels_text,
                    "short": False
                })

            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    return response.status == 200

        except Exception as e:
            logging.error(f"Failed to send Slack notification: {e}")
            return False

class EmailNotificationChannel(NotificationChannel):
    """邮件通知渠道"""

    async def _send_notification(self, alert: Alert) -> bool:
        try:
            import aiosmtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            smtp_config = self.config.get('smtp', {})
            if not smtp_config:
                logging.error("SMTP configuration not found")
                return False

            # 构建邮件
            msg = MIMEMultipart()
            msg['From'] = smtp_config.get('from_email')
            msg['To'] = ', '.join(self.config.get('to_emails', []))
            msg['Subject'] = f"[Perfect21] {alert.severity.value.upper()}: {alert.name}"

            # HTML邮件内容
            html_content = f"""
            <html>
                <body>
                    <h2>Perfect21 Alert Notification</h2>
                    <table border="1" cellpadding="5" cellspacing="0">
                        <tr><th>Alert Name</th><td>{alert.name}</td></tr>
                        <tr><th>Message</th><td>{alert.message}</td></tr>
                        <tr><th>Severity</th><td>{alert.severity.value}</td></tr>
                        <tr><th>Status</th><td>{alert.status.value}</td></tr>
                        <tr><th>Start Time</th><td>{alert.starts_at}</td></tr>
                        <tr><th>Duration</th><td>{alert.duration}</td></tr>
                    </table>

                    {self._format_labels_html(alert.labels)}
                    {self._format_annotations_html(alert.annotations)}
                </body>
            </html>
            """

            msg.attach(MIMEText(html_content, 'html'))

            # 发送邮件
            await aiosmtplib.send(
                msg,
                hostname=smtp_config.get('host'),
                port=smtp_config.get('port', 587),
                username=smtp_config.get('username'),
                password=smtp_config.get('password'),
                use_tls=smtp_config.get('use_tls', True)
            )

            return True

        except Exception as e:
            logging.error(f"Failed to send email notification: {e}")
            return False

    def _format_labels_html(self, labels: Dict[str, str]) -> str:
        """格式化标签为HTML"""
        if not labels:
            return ""

        rows = "\n".join([f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in labels.items()])
        return f"""
        <h3>Labels</h3>
        <table border="1" cellpadding="3" cellspacing="0">
            {rows}
        </table>
        """

    def _format_annotations_html(self, annotations: Dict[str, str]) -> str:
        """格式化注解为HTML"""
        if not annotations:
            return ""

        rows = "\n".join([f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in annotations.items()])
        return f"""
        <h3>Annotations</h3>
        <table border="1" cellpadding="3" cellspacing="0">
            {rows}
        </table>
        """

class WebhookNotificationChannel(NotificationChannel):
    """Webhook通知渠道"""

    async def _send_notification(self, alert: Alert) -> bool:
        try:
            import aiohttp

            url = self.config.get('url')
            if not url:
                logging.error("Webhook URL not configured")
                return False

            payload = {
                "alert": alert.to_dict(),
                "timestamp": datetime.now().isoformat(),
                "source": "perfect21-monitor"
            }

            headers = self.config.get('headers', {})
            timeout = self.config.get('timeout', 10)

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=timeout) as response:
                    return 200 <= response.status < 300

        except Exception as e:
            logging.error(f"Failed to send webhook notification: {e}")
            return False

class AlertManager:
    """告警管理器"""

    def __init__(self):
        self.rules: List[AlertRule] = []
        self.channels: List[NotificationChannel] = []
        self.active_alerts: Dict[str, Alert] = {}
        self.resolved_alerts: List[Alert] = []
        self.alert_queue = queue.Queue()
        self.running = False
        self._processor_thread = None
        self._evaluator_thread = None
        self.suppression_rules: List[Dict[str, Any]] = []

    def add_rule(self, rule: AlertRule):
        """添加告警规则"""
        self.rules.append(rule)

    def add_channel(self, channel: NotificationChannel):
        """添加通知渠道"""
        self.channels.append(channel)

    def add_suppression_rule(self, labels: Dict[str, str], duration: timedelta):
        """添加抑制规则"""
        self.suppression_rules.append({
            'labels': labels,
            'duration': duration,
            'created_at': datetime.now()
        })

    def start(self):
        """启动告警管理器"""
        if self.running:
            return

        self.running = True
        self._processor_thread = threading.Thread(target=self._process_alerts, daemon=True)
        self._evaluator_thread = threading.Thread(target=self._evaluate_rules, daemon=True)

        self._processor_thread.start()
        self._evaluator_thread.start()

        logging.info("Alert manager started")

    def stop(self):
        """停止告警管理器"""
        self.running = False
        if self._processor_thread:
            self._processor_thread.join(timeout=5)
        if self._evaluator_thread:
            self._evaluator_thread.join(timeout=5)
        logging.info("Alert manager stopped")

    def fire_alert(self, alert: Alert):
        """触发告警"""
        # 检查是否被抑制
        if self._is_suppressed(alert):
            alert.suppress()
            logging.info(f"Alert suppressed: {alert.name}")
            return

        # 检查是否已存在
        if alert.fingerprint in self.active_alerts:
            # 更新现有告警
            existing = self.active_alerts[alert.fingerprint]
            existing.message = alert.message
            existing.labels.update(alert.labels)
            existing.annotations.update(alert.annotations)
        else:
            # 新告警
            self.active_alerts[alert.fingerprint] = alert
            self.alert_queue.put(('fire', alert))

    def resolve_alert(self, fingerprint: str):
        """解决告警"""
        if fingerprint in self.active_alerts:
            alert = self.active_alerts.pop(fingerprint)
            alert.resolve()
            self.resolved_alerts.append(alert)
            self.alert_queue.put(('resolve', alert))

    def get_metrics(self, source: str = "prometheus") -> Dict[str, float]:
        """获取指标数据（模拟实现）"""
        # 在实际实现中，这里会从Prometheus或其他数据源获取指标
        return {
            'perfect21_system_cpu_usage_percent': 85.0,
            'perfect21_api_request_duration_seconds': 2.5,
            'perfect21_errors_total': 5.0,
            'perfect21_agent_execution_duration_seconds': 30.0
        }

    def _evaluate_rules(self):
        """评估告警规则"""
        while self.running:
            try:
                metrics = self.get_metrics()

                for rule in self.rules:
                    alert = rule.evaluate(metrics)
                    if alert:
                        self.fire_alert(alert)

                time.sleep(30)  # 每30秒评估一次

            except Exception as e:
                logging.error(f"Error in rule evaluation: {e}")
                time.sleep(30)

    def _process_alerts(self):
        """处理告警队列"""
        while self.running:
            try:
                action, alert = self.alert_queue.get(timeout=1)

                if action == 'fire':
                    asyncio.run(self._send_notifications(alert))
                elif action == 'resolve':
                    asyncio.run(self._send_resolution_notifications(alert))

            except queue.Empty:
                continue
            except Exception as e:
                logging.error(f"Error processing alert: {e}")

    async def _send_notifications(self, alert: Alert):
        """发送告警通知"""
        tasks = []
        for channel in self.channels:
            if self._should_notify_channel(channel, alert):
                tasks.append(channel.send(alert))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for r in results if r is True)
            logging.info(f"Sent alert '{alert.name}' to {success_count}/{len(tasks)} channels")

    async def _send_resolution_notifications(self, alert: Alert):
        """发送告警解决通知"""
        # 只发送关键告警的解决通知
        if alert.severity == AlertSeverity.CRITICAL:
            alert.message = f"RESOLVED: {alert.message}"
            await self._send_notifications(alert)

    def _should_notify_channel(self, channel: NotificationChannel, alert: Alert) -> bool:
        """判断是否应该通知某个渠道"""
        # 检查渠道配置的告警级别
        min_severity = channel.config.get('min_severity', 'info')
        severity_levels = {'info': 0, 'warning': 1, 'critical': 2}

        alert_level = severity_levels.get(alert.severity.value, 0)
        channel_level = severity_levels.get(min_severity, 0)

        return alert_level >= channel_level

    def _is_suppressed(self, alert: Alert) -> bool:
        """检查告警是否被抑制"""
        current_time = datetime.now()

        for rule in self.suppression_rules:
            # 检查抑制规则是否过期
            if current_time - rule['created_at'] > rule['duration']:
                continue

            # 检查标签是否匹配
            if self._labels_match(alert.labels, rule['labels']):
                return True

        return False

    def _labels_match(self, alert_labels: Dict[str, str], rule_labels: Dict[str, str]) -> bool:
        """检查标签是否匹配"""
        for key, value in rule_labels.items():
            if alert_labels.get(key) != value:
                return False
        return True

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """获取活跃告警"""
        return [alert.to_dict() for alert in self.active_alerts.values()]

    def get_alert_stats(self) -> Dict[str, Any]:
        """获取告警统计"""
        total_active = len(self.active_alerts)
        total_resolved = len(self.resolved_alerts)

        severity_counts = {}
        for alert in self.active_alerts.values():
            severity = alert.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

        return {
            'active_alerts': total_active,
            'resolved_alerts': total_resolved,
            'severity_breakdown': severity_counts,
            'total_rules': len(self.rules),
            'total_channels': len(self.channels)
        }

def create_default_alert_rules() -> List[AlertRule]:
    """创建默认告警规则"""
    return [
        AlertRule(
            name="HighCPUUsage",
            condition="perfect21_system_cpu_usage_percent > 90",
            threshold=90.0,
            duration=timedelta(minutes=5),
            severity=AlertSeverity.CRITICAL,
            message="High CPU usage: {value:.1f}% (threshold: {threshold}%)",
            labels={"component": "system"},
            annotations={"runbook": "https://wiki.perfect21.com/runbooks/high-cpu"}
        ),
        AlertRule(
            name="HighAPILatency",
            condition="perfect21_api_request_duration_seconds > 2",
            threshold=2.0,
            duration=timedelta(minutes=2),
            severity=AlertSeverity.WARNING,
            message="High API latency: {value:.2f}s (threshold: {threshold}s)",
            labels={"component": "api"}
        ),
        AlertRule(
            name="HighErrorRate",
            condition="perfect21_errors_total > 10",
            threshold=10.0,
            duration=timedelta(minutes=1),
            severity=AlertSeverity.CRITICAL,
            message="High error rate: {value} errors/min (threshold: {threshold})",
            labels={"component": "application"}
        ),
        AlertRule(
            name="LongRunningAgentExecution",
            condition="perfect21_agent_execution_duration_seconds > 300",
            threshold=300.0,
            duration=timedelta(minutes=1),
            severity=AlertSeverity.WARNING,
            message="Long running agent execution: {value:.0f}s (threshold: {threshold}s)",
            labels={"component": "agent"}
        )
    ]

# 全局告警管理器实例
alert_manager = AlertManager()

# 设置默认规则
for rule in create_default_alert_rules():
    alert_manager.add_rule(rule)

def configure_slack_notifications(webhook_url: str, channel: str = "#alerts"):
    """配置Slack通知"""
    slack_channel = SlackNotificationChannel("slack", {
        "webhook_url": webhook_url,
        "channel": channel,
        "username": "Perfect21 Monitor",
        "icon": ":robot_face:",
        "min_severity": "warning"
    })
    alert_manager.add_channel(slack_channel)

def configure_email_notifications(smtp_config: Dict[str, Any], to_emails: List[str]):
    """配置邮件通知"""
    email_channel = EmailNotificationChannel("email", {
        "smtp": smtp_config,
        "to_emails": to_emails,
        "min_severity": "critical"
    })
    alert_manager.add_channel(email_channel)

def configure_webhook_notifications(url: str, headers: Dict[str, str] = None):
    """配置Webhook通知"""
    webhook_channel = WebhookNotificationChannel("webhook", {
        "url": url,
        "headers": headers or {},
        "timeout": 10,
        "min_severity": "info"
    })
    alert_manager.add_channel(webhook_channel)

def start_alerting(slack_webhook: str = None, email_config: Dict[str, Any] = None):
    """启动告警系统"""
    if slack_webhook:
        configure_slack_notifications(slack_webhook)

    if email_config:
        configure_email_notifications(
            email_config.get('smtp', {}),
            email_config.get('to_emails', [])
        )

    alert_manager.start()
    logging.info("Alert system started")

def fire_custom_alert(name: str, message: str, severity: str = "warning", **kwargs):
    """触发自定义告警"""
    alert = Alert(
        name=name,
        message=message,
        severity=AlertSeverity(severity),
        labels=kwargs.get('labels', {}),
        annotations=kwargs.get('annotations', {})
    )
    alert_manager.fire_alert(alert)

def get_alert_status() -> Dict[str, Any]:
    """获取告警状态"""
    return alert_manager.get_alert_stats()