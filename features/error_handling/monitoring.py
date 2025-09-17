#!/usr/bin/env python3
"""
Perfect21 错误监控系统
提供错误度量、监控和报告功能
"""

import json
import threading
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
import logging

from .exceptions import Perfect21Exception, ErrorCode, ErrorSeverity


@dataclass
class ErrorMetric:
    """错误度量"""
    timestamp: datetime
    error_code: str
    error_name: str
    severity: str
    message: str
    details: Dict[str, Any]
    context: Dict[str, Any]
    resolved: bool = False
    resolution_time: Optional[datetime] = None


class ErrorAggregator:
    """错误聚合器"""

    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.errors: deque = deque(maxlen=window_size)
        self._lock = threading.Lock()

    def add_error(self, metric: ErrorMetric):
        """添加错误"""
        with self._lock:
            self.errors.append(metric)

    def get_errors_by_timerange(
        self,
        start_time: datetime,
        end_time: Optional[datetime] = None
    ) -> List[ErrorMetric]:
        """按时间范围获取错误"""
        end_time = end_time or datetime.now()

        with self._lock:
            return [
                error for error in self.errors
                if start_time <= error.timestamp <= end_time
            ]

    def get_errors_by_severity(self, severity: ErrorSeverity) -> List[ErrorMetric]:
        """按严重程度获取错误"""
        with self._lock:
            return [
                error for error in self.errors
                if error.severity == severity.value
            ]

    def get_errors_by_code(self, error_code: ErrorCode) -> List[ErrorMetric]:
        """按错误码获取错误"""
        with self._lock:
            return [
                error for error in self.errors
                if error.error_code == error_code.name
            ]

    def get_error_counts(self) -> Dict[str, int]:
        """获取错误计数"""
        counts = defaultdict(int)
        with self._lock:
            for error in self.errors:
                counts[error.error_code] += 1
        return dict(counts)

    def get_error_trends(self, window_minutes: int = 60) -> Dict[str, List[int]]:
        """获取错误趋势"""
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=window_minutes)

        # 按分钟分组
        minute_buckets = defaultdict(lambda: defaultdict(int))

        with self._lock:
            for error in self.errors:
                if start_time <= error.timestamp <= end_time:
                    minute_key = error.timestamp.replace(second=0, microsecond=0)
                    minute_buckets[minute_key][error.error_code] += 1

        # 生成趋势数据
        trends = defaultdict(list)
        current_time = start_time.replace(second=0, microsecond=0)

        while current_time <= end_time:
            bucket = minute_buckets.get(current_time, {})
            for error_code in set().union(*[bucket.keys() for bucket in minute_buckets.values()]):
                trends[error_code].append(bucket.get(error_code, 0))
            current_time += timedelta(minutes=1)

        return dict(trends)


class ErrorAnalyzer:
    """错误分析器"""

    def __init__(self, aggregator: ErrorAggregator):
        self.aggregator = aggregator

    def analyze_patterns(self, time_window: int = 3600) -> Dict[str, Any]:
        """分析错误模式"""
        end_time = datetime.now()
        start_time = end_time - timedelta(seconds=time_window)

        errors = self.aggregator.get_errors_by_timerange(start_time, end_time)

        if not errors:
            return {'pattern': 'no_errors', 'confidence': 1.0}

        # 分析错误频率
        frequency_analysis = self._analyze_frequency(errors)

        # 分析错误分布
        distribution_analysis = self._analyze_distribution(errors)

        # 分析错误相关性
        correlation_analysis = self._analyze_correlation(errors)

        # 检测异常模式
        anomaly_analysis = self._detect_anomalies(errors)

        return {
            'frequency': frequency_analysis,
            'distribution': distribution_analysis,
            'correlation': correlation_analysis,
            'anomalies': anomaly_analysis,
            'analysis_time': datetime.now().isoformat(),
            'analyzed_errors': len(errors)
        }

    def _analyze_frequency(self, errors: List[ErrorMetric]) -> Dict[str, Any]:
        """分析错误频率"""
        if not errors:
            return {'pattern': 'no_errors'}

        total_errors = len(errors)
        time_span = (errors[-1].timestamp - errors[0].timestamp).total_seconds()

        if time_span == 0:
            frequency = float('inf')
        else:
            frequency = total_errors / time_span  # 错误/秒

        # 分类频率模式
        if frequency > 10:
            pattern = 'error_storm'
            severity = 'critical'
        elif frequency > 1:
            pattern = 'high_frequency'
            severity = 'high'
        elif frequency > 0.1:
            pattern = 'moderate_frequency'
            severity = 'medium'
        else:
            pattern = 'low_frequency'
            severity = 'low'

        return {
            'pattern': pattern,
            'frequency': frequency,
            'severity': severity,
            'total_errors': total_errors,
            'time_span_seconds': time_span
        }

    def _analyze_distribution(self, errors: List[ErrorMetric]) -> Dict[str, Any]:
        """分析错误分布"""
        severity_counts = defaultdict(int)
        code_counts = defaultdict(int)

        for error in errors:
            severity_counts[error.severity] += 1
            code_counts[error.error_code] += 1

        # 计算分布
        total_errors = len(errors)
        severity_distribution = {
            severity: count / total_errors
            for severity, count in severity_counts.items()
        }

        code_distribution = {
            code: count / total_errors
            for code, count in code_counts.items()
        }

        # 找出主要错误类型
        dominant_severity = max(severity_counts.items(), key=lambda x: x[1])
        dominant_code = max(code_counts.items(), key=lambda x: x[1])

        return {
            'severity_distribution': severity_distribution,
            'code_distribution': code_distribution,
            'dominant_severity': {
                'type': dominant_severity[0],
                'percentage': dominant_severity[1] / total_errors
            },
            'dominant_code': {
                'type': dominant_code[0],
                'percentage': dominant_code[1] / total_errors
            }
        }

    def _analyze_correlation(self, errors: List[ErrorMetric]) -> Dict[str, Any]:
        """分析错误相关性"""
        # 检查错误之间的时间相关性
        time_correlations = []
        code_sequences = []

        for i in range(len(errors) - 1):
            current = errors[i]
            next_error = errors[i + 1]

            time_diff = (next_error.timestamp - current.timestamp).total_seconds()
            if time_diff < 60:  # 1分钟内的错误认为可能相关
                time_correlations.append({
                    'first_error': current.error_code,
                    'second_error': next_error.error_code,
                    'time_diff': time_diff
                })

            code_sequences.append((current.error_code, next_error.error_code))

        # 分析错误序列模式
        sequence_counts = defaultdict(int)
        for sequence in code_sequences:
            sequence_counts[sequence] += 1

        common_sequences = sorted(
            sequence_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return {
            'time_correlations': time_correlations,
            'common_sequences': [
                {'sequence': seq, 'count': count}
                for seq, count in common_sequences
            ]
        }

    def _detect_anomalies(self, errors: List[ErrorMetric]) -> Dict[str, Any]:
        """检测异常模式"""
        anomalies = []

        # 检测错误爆发
        if self._detect_error_burst(errors):
            anomalies.append({
                'type': 'error_burst',
                'description': 'Sudden increase in error rate detected',
                'severity': 'high'
            })

        # 检测新错误类型
        recent_codes = set(error.error_code for error in errors[-10:])
        historical_codes = set(error.error_code for error in errors[:-10])
        new_codes = recent_codes - historical_codes

        if new_codes:
            anomalies.append({
                'type': 'new_error_types',
                'description': f'New error types detected: {", ".join(new_codes)}',
                'severity': 'medium',
                'details': {'new_codes': list(new_codes)}
            })

        # 检测错误停止（之前频繁出现的错误突然停止）
        if self._detect_error_cessation(errors):
            anomalies.append({
                'type': 'error_cessation',
                'description': 'Previously frequent errors have stopped',
                'severity': 'low'
            })

        return {
            'anomalies': anomalies,
            'anomaly_count': len(anomalies)
        }

    def _detect_error_burst(self, errors: List[ErrorMetric]) -> bool:
        """检测错误爆发"""
        if len(errors) < 20:
            return False

        # 比较最近10个错误的时间间隔与历史平均值
        recent_errors = errors[-10:]
        historical_errors = errors[-20:-10]

        recent_intervals = []
        for i in range(len(recent_errors) - 1):
            interval = (recent_errors[i + 1].timestamp - recent_errors[i].timestamp).total_seconds()
            recent_intervals.append(interval)

        historical_intervals = []
        for i in range(len(historical_errors) - 1):
            interval = (historical_errors[i + 1].timestamp - historical_errors[i].timestamp).total_seconds()
            historical_intervals.append(interval)

        if not recent_intervals or not historical_intervals:
            return False

        recent_avg = sum(recent_intervals) / len(recent_intervals)
        historical_avg = sum(historical_intervals) / len(historical_intervals)

        # 如果最近的平均间隔比历史平均间隔小很多，认为是错误爆发
        return recent_avg < historical_avg * 0.3

    def _detect_error_cessation(self, errors: List[ErrorMetric]) -> bool:
        """检测错误停止"""
        if len(errors) < 20:
            return False

        # 检查最近是否有某种错误类型停止出现
        recent_time = datetime.now() - timedelta(minutes=30)
        recent_codes = set(
            error.error_code for error in errors
            if error.timestamp > recent_time
        )

        historical_time = recent_time - timedelta(hours=2)
        historical_codes = set(
            error.error_code for error in errors
            if historical_time <= error.timestamp <= recent_time
        )

        # 如果有错误类型在历史期间频繁出现但在最近期间没有出现
        missing_codes = historical_codes - recent_codes
        return len(missing_codes) > 0


class ErrorNotifier:
    """错误通知器"""

    def __init__(self):
        self.notification_handlers: List[Callable[[Dict[str, Any]], None]] = []
        self.logger = logging.getLogger('Perfect21.ErrorNotifier')

    def add_handler(self, handler: Callable[[Dict[str, Any]], None]):
        """添加通知处理器"""
        self.notification_handlers.append(handler)

    def notify(self, notification: Dict[str, Any]):
        """发送通知"""
        for handler in self.notification_handlers:
            try:
                handler(notification)
            except Exception as e:
                self.logger.error(f"Notification handler failed: {e}")

    def notify_error_threshold(
        self,
        error_count: int,
        threshold: int,
        time_window: int
    ):
        """错误阈值通知"""
        notification = {
            'type': 'error_threshold',
            'error_count': error_count,
            'threshold': threshold,
            'time_window_minutes': time_window,
            'timestamp': datetime.now().isoformat(),
            'severity': 'high' if error_count > threshold * 2 else 'medium'
        }
        self.notify(notification)

    def notify_anomaly(self, anomaly: Dict[str, Any]):
        """异常通知"""
        notification = {
            'type': 'anomaly_detected',
            'anomaly': anomaly,
            'timestamp': datetime.now().isoformat()
        }
        self.notify(notification)


class ErrorMonitor:
    """错误监控器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.aggregator = ErrorAggregator(
            window_size=self.config.get('window_size', 1000)
        )
        self.analyzer = ErrorAnalyzer(self.aggregator)
        self.notifier = ErrorNotifier()
        self.logger = logging.getLogger('Perfect21.ErrorMonitor')

        # 监控配置
        self.error_thresholds = self.config.get('error_thresholds', {
            ErrorSeverity.CRITICAL: {'count': 1, 'window_minutes': 5},
            ErrorSeverity.HIGH: {'count': 5, 'window_minutes': 15},
            ErrorSeverity.MEDIUM: {'count': 20, 'window_minutes': 60},
            ErrorSeverity.LOW: {'count': 100, 'window_minutes': 60}
        })

        # 统计信息
        self.stats = {
            'total_errors_recorded': 0,
            'errors_by_severity': defaultdict(int),
            'errors_by_code': defaultdict(int),
            'last_analysis_time': None,
            'anomalies_detected': 0
        }

    def record_error(
        self,
        exception: Perfect21Exception,
        context: Optional[Dict[str, Any]] = None
    ):
        """记录错误"""
        metric = ErrorMetric(
            timestamp=datetime.now(),
            error_code=exception.error_code.name,
            error_name=exception.error_code.name,
            severity=exception.severity.value,
            message=exception.message,
            details=exception.details,
            context=context or {}
        )

        self.aggregator.add_error(metric)

        # 更新统计信息
        self.stats['total_errors_recorded'] += 1
        self.stats['errors_by_severity'][exception.severity.value] += 1
        self.stats['errors_by_code'][exception.error_code.name] += 1

        # 检查阈值
        self._check_thresholds(exception.severity)

        self.logger.info(f"Error recorded: {exception.error_code.name}")

    def _check_thresholds(self, severity: ErrorSeverity):
        """检查错误阈值"""
        threshold_config = self.error_thresholds.get(severity)
        if not threshold_config:
            return

        window_minutes = threshold_config['window_minutes']
        threshold_count = threshold_config['count']

        # 获取时间窗口内的错误
        start_time = datetime.now() - timedelta(minutes=window_minutes)
        recent_errors = self.aggregator.get_errors_by_timerange(start_time)
        severity_errors = [e for e in recent_errors if e.severity == severity.value]

        if len(severity_errors) >= threshold_count:
            self.notifier.notify_error_threshold(
                len(severity_errors),
                threshold_count,
                window_minutes
            )

    def analyze_errors(self) -> Dict[str, Any]:
        """分析错误"""
        analysis = self.analyzer.analyze_patterns()
        self.stats['last_analysis_time'] = datetime.now()

        # 检查异常
        anomalies = analysis.get('anomalies', {}).get('anomalies', [])
        if anomalies:
            self.stats['anomalies_detected'] += len(anomalies)
            for anomaly in anomalies:
                self.notifier.notify_anomaly(anomaly)

        return analysis

    def get_recent_errors(
        self,
        severity: Optional[ErrorSeverity] = None,
        time_window: Optional[timedelta] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取最近的错误"""
        if time_window:
            start_time = datetime.now() - time_window
            errors = self.aggregator.get_errors_by_timerange(start_time)
        else:
            errors = list(self.aggregator.errors)

        if severity:
            errors = [e for e in errors if e.severity == severity.value]

        # 限制数量
        errors = errors[-limit:]

        return [asdict(error) for error in errors]

    def get_error_summary(self) -> Dict[str, Any]:
        """获取错误摘要"""
        now = datetime.now()

        # 最近1小时的错误
        hour_ago = now - timedelta(hours=1)
        recent_errors = self.aggregator.get_errors_by_timerange(hour_ago)

        # 按严重程度统计
        severity_counts = defaultdict(int)
        for error in recent_errors:
            severity_counts[error.severity] += 1

        # 错误趋势
        trends = self.aggregator.get_error_trends(60)

        return {
            'total_errors_last_hour': len(recent_errors),
            'severity_breakdown': dict(severity_counts),
            'error_trends': trends,
            'top_error_codes': dict(
                sorted(
                    self.stats['errors_by_code'].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
            ),
            'monitoring_stats': self.stats,
            'last_updated': now.isoformat()
        }

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return dict(self.stats)

    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'total_errors_recorded': 0,
            'errors_by_severity': defaultdict(int),
            'errors_by_code': defaultdict(int),
            'last_analysis_time': None,
            'anomalies_detected': 0
        }

    def export_errors(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        format: str = 'json'
    ) -> str:
        """导出错误数据"""
        if start_time is None:
            start_time = datetime.now() - timedelta(days=1)
        if end_time is None:
            end_time = datetime.now()

        errors = self.aggregator.get_errors_by_timerange(start_time, end_time)
        error_data = [asdict(error) for error in errors]

        if format == 'json':
            return json.dumps(error_data, default=str, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")


class ErrorMetrics:
    """错误度量系统"""

    def __init__(self, monitor: ErrorMonitor):
        self.monitor = monitor

    def get_error_rate(self, time_window: int = 3600) -> float:
        """获取错误率"""
        start_time = datetime.now() - timedelta(seconds=time_window)
        errors = self.monitor.aggregator.get_errors_by_timerange(start_time)
        return len(errors) / time_window  # 错误/秒

    def get_mttr(self) -> Optional[float]:
        """获取平均恢复时间 (Mean Time To Recovery)"""
        errors = list(self.monitor.aggregator.errors)
        resolved_errors = [e for e in errors if e.resolved and e.resolution_time]

        if not resolved_errors:
            return None

        total_resolution_time = sum(
            (e.resolution_time - e.timestamp).total_seconds()
            for e in resolved_errors
        )

        return total_resolution_time / len(resolved_errors)

    def get_error_distribution(self) -> Dict[str, float]:
        """获取错误分布"""
        errors = list(self.monitor.aggregator.errors)
        if not errors:
            return {}

        total_errors = len(errors)
        distribution = defaultdict(int)

        for error in errors:
            distribution[error.severity] += 1

        return {
            severity: count / total_errors
            for severity, count in distribution.items()
        }