#!/usr/bin/env python3
"""
Execution Monitor - 执行监控器
实时监控执行过程，收集性能数据
"""

import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

logger = logging.getLogger("ExecutionMonitor")

class MetricType:
    """指标类型"""
    PARALLEL_RATE = "parallel_rate"        # 并行率
    AGENT_COUNT = "agent_count"            # Agent数量
    EXECUTION_TIME = "execution_time"       # 执行时间
    SYNC_POINT_TIME = "sync_point_time"    # 同步点时间
    SUCCESS_RATE = "success_rate"          # 成功率
    QUALITY_SCORE = "quality_score"        # 质量分数

class ExecutionMonitor:
    """
    执行监控器 - 实时监控和数据收集

    主要功能：
    1. 实时监控执行状态
    2. 收集性能指标
    3. 检测异常模式
    4. 生成监控报告
    """

    def __init__(self):
        self.current_phase = None
        self.phase_start_time = None
        self.metrics = defaultdict(list)
        self.real_time_data = {}
        self.alerts = []
        self.phase_metrics = {}

        # 性能基准
        self.benchmarks = {
            'phase_duration': {
                'analysis': 180,        # 3分钟
                'design': 300,          # 5分钟
                'implementation': 600,   # 10分钟
                'testing': 300,         # 5分钟
                'deployment': 180       # 3分钟
            },
            'min_parallel_agents': 2,
            'max_sync_point_time': 30,  # 30秒
            'min_success_rate': 0.8     # 80%
        }

        # 实时监控状态
        self.monitoring_active = False
        self.monitored_operations = []

        logger.info("ExecutionMonitor初始化 - 监控系统已启动")

    def start_phase_monitoring(self, phase: str) -> None:
        """
        开始监控阶段执行

        Args:
            phase: 阶段名称
        """
        self.current_phase = phase
        self.phase_start_time = time.time()
        self.monitoring_active = True

        self.real_time_data[phase] = {
            'start_time': datetime.now().isoformat(),
            'agents': [],
            'operations': [],
            'sync_points': [],
            'status': 'RUNNING'
        }

        logger.info(f"开始监控{phase}阶段")

    def record_agent_call(self, agent_name: str, is_parallel: bool = True) -> None:
        """
        记录Agent调用

        Args:
            agent_name: Agent名称
            is_parallel: 是否并行调用
        """
        if not self.monitoring_active:
            return

        agent_record = {
            'name': agent_name,
            'timestamp': datetime.now().isoformat(),
            'is_parallel': is_parallel,
            'call_time': time.time() - self.phase_start_time
        }

        self.real_time_data[self.current_phase]['agents'].append(agent_record)
        self.monitored_operations.append(('agent_call', agent_record))

        # 检测串行调用警告
        if not is_parallel:
            self._raise_alert('SEQUENTIAL_CALL', f"检测到串行调用: {agent_name}")

        logger.debug(f"记录Agent调用: {agent_name} (并行: {is_parallel})")

    def record_operation(self, operation_type: str, details: Dict[str, Any]) -> None:
        """
        记录操作

        Args:
            operation_type: 操作类型
            details: 操作详情
        """
        if not self.monitoring_active:
            return

        operation_record = {
            'type': operation_type,
            'details': details,
            'timestamp': datetime.now().isoformat(),
            'elapsed_time': time.time() - self.phase_start_time
        }

        self.real_time_data[self.current_phase]['operations'].append(operation_record)
        self.monitored_operations.append((operation_type, operation_record))

        logger.debug(f"记录操作: {operation_type}")

    def record_sync_point(self, sync_point_name: str, duration: float = None) -> None:
        """
        记录同步点

        Args:
            sync_point_name: 同步点名称
            duration: 同步点执行时间
        """
        if not self.monitoring_active:
            return

        sync_record = {
            'name': sync_point_name,
            'timestamp': datetime.now().isoformat(),
            'duration': duration,
            'phase_elapsed': time.time() - self.phase_start_time
        }

        self.real_time_data[self.current_phase]['sync_points'].append(sync_record)

        # 检查同步点时间
        if duration and duration > self.benchmarks['max_sync_point_time']:
            self._raise_alert('SLOW_SYNC_POINT',
                            f"同步点{sync_point_name}执行缓慢: {duration:.1f}秒")

        logger.debug(f"记录同步点: {sync_point_name}")

    def end_phase_monitoring(self, phase: str, success: bool = True) -> Dict[str, Any]:
        """
        结束阶段监控

        Args:
            phase: 阶段名称
            success: 是否成功

        Returns:
            阶段监控报告
        """
        if not self.monitoring_active or phase != self.current_phase:
            return {}

        duration = time.time() - self.phase_start_time
        self.monitoring_active = False

        # 更新阶段数据
        phase_data = self.real_time_data[phase]
        phase_data['end_time'] = datetime.now().isoformat()
        phase_data['duration'] = duration
        phase_data['status'] = 'SUCCESS' if success else 'FAILED'
        phase_data['success'] = success

        # 计算指标
        metrics = self._calculate_phase_metrics(phase, phase_data)
        self.phase_metrics[phase] = metrics

        # 记录指标
        self._record_metrics(phase, metrics)

        # 检查性能
        self._check_performance(phase, metrics)

        # 生成报告
        report = self._generate_phase_report(phase, phase_data, metrics)

        logger.info(f"结束{phase}阶段监控，耗时: {duration:.1f}秒")

        return report

    def get_real_time_status(self) -> Dict[str, Any]:
        """
        获取实时状态

        Returns:
            实时状态信息
        """
        if not self.monitoring_active:
            return {'monitoring': False, 'message': '未在监控中'}

        elapsed_time = time.time() - self.phase_start_time
        phase_data = self.real_time_data.get(self.current_phase, {})

        status = {
            'monitoring': True,
            'current_phase': self.current_phase,
            'elapsed_time': elapsed_time,
            'agent_count': len(phase_data.get('agents', [])),
            'operation_count': len(phase_data.get('operations', [])),
            'sync_point_count': len(phase_data.get('sync_points', [])),
            'recent_operations': self.monitored_operations[-5:],  # 最近5个操作
            'active_alerts': [a for a in self.alerts if a['active']]
        }

        # 添加进度估计
        if self.current_phase in self.benchmarks['phase_duration']:
            expected_duration = self.benchmarks['phase_duration'][self.current_phase]
            progress = min((elapsed_time / expected_duration) * 100, 100)
            status['progress'] = progress
            status['expected_remaining'] = max(expected_duration - elapsed_time, 0)

        return status

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        获取性能摘要

        Returns:
            性能摘要信息
        """
        if not self.metrics:
            return {'message': '暂无性能数据'}

        summary = {
            'total_phases': len(self.phase_metrics),
            'average_metrics': {},
            'best_performance': None,
            'worst_performance': None,
            'alerts_summary': self._summarize_alerts()
        }

        # 计算平均指标
        for metric_type in MetricType.__dict__.values():
            if isinstance(metric_type, str) and metric_type in self.metrics:
                values = self.metrics[metric_type]
                if values:
                    summary['average_metrics'][metric_type] = {
                        'mean': statistics.mean(values),
                        'median': statistics.median(values),
                        'min': min(values),
                        'max': max(values)
                    }

        # 找出最佳和最差性能
        if self.phase_metrics:
            sorted_phases = sorted(self.phase_metrics.items(),
                                 key=lambda x: x[1].get('quality_score', 0))
            if sorted_phases:
                summary['worst_performance'] = sorted_phases[0]
                summary['best_performance'] = sorted_phases[-1]

        return summary

    def _calculate_phase_metrics(self, phase: str, phase_data: Dict[str, Any]) -> Dict[str, Any]:
        """计算阶段指标"""
        agents = phase_data.get('agents', [])
        parallel_agents = [a for a in agents if a.get('is_parallel')]

        metrics = {
            MetricType.AGENT_COUNT: len(agents),
            MetricType.PARALLEL_RATE: len(parallel_agents) / len(agents) if agents else 0,
            MetricType.EXECUTION_TIME: phase_data.get('duration', 0),
            MetricType.SUCCESS_RATE: 1.0 if phase_data.get('success') else 0.0
        }

        # 计算同步点时间
        sync_points = phase_data.get('sync_points', [])
        if sync_points:
            sync_times = [sp.get('duration', 0) for sp in sync_points if sp.get('duration')]
            if sync_times:
                metrics[MetricType.SYNC_POINT_TIME] = statistics.mean(sync_times)

        # 计算质量分数
        quality_score = self._calculate_quality_score(metrics)
        metrics[MetricType.QUALITY_SCORE] = quality_score

        return metrics

    def _calculate_quality_score(self, metrics: Dict[str, Any]) -> float:
        """计算质量分数"""
        score = 0
        max_score = 100

        # 并行率 (40分)
        parallel_rate = metrics.get(MetricType.PARALLEL_RATE, 0)
        score += parallel_rate * 40

        # 成功率 (30分)
        success_rate = metrics.get(MetricType.SUCCESS_RATE, 0)
        score += success_rate * 30

        # Agent数量 (20分)
        agent_count = metrics.get(MetricType.AGENT_COUNT, 0)
        if agent_count >= self.benchmarks['min_parallel_agents']:
            score += 20
        else:
            score += (agent_count / self.benchmarks['min_parallel_agents']) * 20

        # 执行时间 (10分)
        # 执行时间越短越好
        execution_time = metrics.get(MetricType.EXECUTION_TIME, float('inf'))
        if execution_time < 60:  # 1分钟内
            score += 10
        elif execution_time < 180:  # 3分钟内
            score += 5

        return min(score, max_score)

    def _record_metrics(self, phase: str, metrics: Dict[str, Any]) -> None:
        """记录指标"""
        for metric_type, value in metrics.items():
            self.metrics[metric_type].append(value)

        # 保持指标历史在合理范围
        max_history = 100
        for metric_type in self.metrics:
            if len(self.metrics[metric_type]) > max_history:
                self.metrics[metric_type] = self.metrics[metric_type][-max_history:]

    def _check_performance(self, phase: str, metrics: Dict[str, Any]) -> None:
        """检查性能"""
        # 检查执行时间
        if phase in self.benchmarks['phase_duration']:
            expected = self.benchmarks['phase_duration'][phase]
            actual = metrics.get(MetricType.EXECUTION_TIME, 0)
            if actual > expected * 1.5:
                self._raise_alert('SLOW_EXECUTION',
                                f"{phase}阶段执行缓慢: {actual:.1f}秒 (预期: {expected}秒)")

        # 检查并行率
        parallel_rate = metrics.get(MetricType.PARALLEL_RATE, 0)
        if parallel_rate < 0.5:
            self._raise_alert('LOW_PARALLEL_RATE',
                            f"{phase}阶段并行率低: {parallel_rate:.1%}")

        # 检查质量分数
        quality_score = metrics.get(MetricType.QUALITY_SCORE, 0)
        if quality_score < 60:
            self._raise_alert('LOW_QUALITY',
                            f"{phase}阶段质量分数低: {quality_score:.1f}/100")

    def _raise_alert(self, alert_type: str, message: str) -> None:
        """发出警报"""
        alert = {
            'type': alert_type,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'phase': self.current_phase,
            'active': True
        }

        self.alerts.append(alert)
        logger.warning(f"警报: {message}")

    def _generate_phase_report(self, phase: str, phase_data: Dict[str, Any],
                              metrics: Dict[str, Any]) -> Dict[str, Any]:
        """生成阶段报告"""
        report = {
            'phase': phase,
            'duration': phase_data.get('duration', 0),
            'status': phase_data.get('status'),
            'metrics': metrics,
            'agent_summary': {
                'total': len(phase_data.get('agents', [])),
                'parallel': sum(1 for a in phase_data.get('agents', []) if a.get('is_parallel'))
            },
            'sync_points': len(phase_data.get('sync_points', [])),
            'quality_score': metrics.get(MetricType.QUALITY_SCORE, 0),
            'alerts': [a for a in self.alerts if a.get('phase') == phase]
        }

        # 添加性能评级
        if report['quality_score'] >= 80:
            report['rating'] = '优秀'
        elif report['quality_score'] >= 60:
            report['rating'] = '良好'
        elif report['quality_score'] >= 40:
            report['rating'] = '及格'
        else:
            report['rating'] = '需改进'

        return report

    def _summarize_alerts(self) -> Dict[str, int]:
        """汇总警报"""
        alert_counts = defaultdict(int)
        for alert in self.alerts:
            alert_counts[alert['type']] += 1

        return dict(alert_counts)