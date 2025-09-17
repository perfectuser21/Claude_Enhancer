#!/usr/bin/env python3
"""
Perfect21 执行监控系统
实时监控多Agent工作流执行，提供可视化界面
"""

import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import threading
from collections import defaultdict, deque
import queue

logger = logging.getLogger("ExecutionMonitor")

class MonitorEventType(Enum):
    """监控事件类型"""
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_PROGRESS = "task_progress"
    AGENT_STATUS_CHANGE = "agent_status_change"
    RESOURCE_UPDATE = "resource_update"
    ERROR_OCCURRED = "error_occurred"

@dataclass
class MonitorEvent:
    """监控事件"""
    event_type: MonitorEventType
    timestamp: datetime
    workflow_id: str
    task_id: Optional[str] = None
    agent_name: Optional[str] = None
    message: str = ""
    data: Dict[str, Any] = None
    duration: float = 0.0

    def __post_init__(self):
        if self.data is None:
            self.data = {}

@dataclass
class TaskMetrics:
    """任务执行指标"""
    task_id: str
    agent_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: float = 0.0
    status: str = "running"
    progress: int = 0  # 0-100
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    error_message: Optional[str] = None

@dataclass
class WorkflowMetrics:
    """工作流执行指标"""
    workflow_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_duration: float = 0.0
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    running_tasks: int = 0
    success_rate: float = 0.0
    average_task_duration: float = 0.0
    parallel_efficiency: float = 0.0  # 并行效率
    tasks: Dict[str, TaskMetrics] = None

    def __post_init__(self):
        if self.tasks is None:
            self.tasks = {}

class ExecutionMonitor:
    """执行监控器"""

    def __init__(self, max_events: int = 10000, auto_cleanup: bool = True):
        """
        初始化执行监控器

        Args:
            max_events: 最大事件数量
            auto_cleanup: 是否自动清理旧事件
        """
        self.max_events = max_events
        self.auto_cleanup = auto_cleanup

        # 事件存储
        self.events: deque = deque(maxlen=max_events)
        self.workflows: Dict[str, WorkflowMetrics] = {}
        self.active_workflows: Dict[str, WorkflowMetrics] = {}

        # 监控状态
        self.is_monitoring = False
        self.event_queue = queue.Queue()
        self.subscribers: List[Callable] = []

        # 统计数据
        self.total_workflows_executed = 0
        self.total_tasks_executed = 0
        self.total_execution_time = 0.0

        # 实时状态
        self.current_agent_status: Dict[str, str] = {}
        self.resource_usage: Dict[str, float] = {
            "cpu": 0.0,
            "memory": 0.0,
            "disk": 0.0,
            "network": 0.0
        }

        logger.info("执行监控器初始化完成")

    def start_monitoring(self):
        """开始监控"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self._start_event_processor()
            logger.info("执行监控已启动")

    def stop_monitoring(self):
        """停止监控"""
        if self.is_monitoring:
            self.is_monitoring = False
            logger.info("执行监控已停止")

    def _start_event_processor(self):
        """启动事件处理器"""
        def process_events():
            while self.is_monitoring:
                try:
                    event = self.event_queue.get(timeout=1.0)
                    self._process_event(event)
                    self._notify_subscribers(event)
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"处理监控事件时发生错误: {e}")

        thread = threading.Thread(target=process_events, daemon=True)
        thread.start()

    def emit_event(self, event_type: MonitorEventType, workflow_id: str,
                   task_id: str = None, agent_name: str = None,
                   message: str = "", data: Dict[str, Any] = None,
                   duration: float = 0.0):
        """
        发出监控事件

        Args:
            event_type: 事件类型
            workflow_id: 工作流ID
            task_id: 任务ID（可选）
            agent_name: Agent名称（可选）
            message: 事件消息
            data: 附加数据
            duration: 执行时长
        """
        event = MonitorEvent(
            event_type=event_type,
            timestamp=datetime.now(),
            workflow_id=workflow_id,
            task_id=task_id,
            agent_name=agent_name,
            message=message,
            data=data or {},
            duration=duration
        )

        self.event_queue.put(event)

    def _process_event(self, event: MonitorEvent):
        """处理单个事件"""
        # 添加到事件历史
        self.events.append(event)

        # 更新工作流指标
        if event.event_type == MonitorEventType.WORKFLOW_STARTED:
            self._handle_workflow_started(event)
        elif event.event_type == MonitorEventType.WORKFLOW_COMPLETED:
            self._handle_workflow_completed(event)
        elif event.event_type == MonitorEventType.WORKFLOW_FAILED:
            self._handle_workflow_failed(event)
        elif event.event_type == MonitorEventType.TASK_STARTED:
            self._handle_task_started(event)
        elif event.event_type == MonitorEventType.TASK_COMPLETED:
            self._handle_task_completed(event)
        elif event.event_type == MonitorEventType.TASK_FAILED:
            self._handle_task_failed(event)
        elif event.event_type == MonitorEventType.AGENT_STATUS_CHANGE:
            self._handle_agent_status_change(event)
        elif event.event_type == MonitorEventType.RESOURCE_UPDATE:
            self._handle_resource_update(event)

    def _handle_workflow_started(self, event: MonitorEvent):
        """处理工作流开始事件"""
        workflow_metrics = WorkflowMetrics(
            workflow_id=event.workflow_id,
            start_time=event.timestamp,
            total_tasks=event.data.get('total_tasks', 0)
        )

        self.workflows[event.workflow_id] = workflow_metrics
        self.active_workflows[event.workflow_id] = workflow_metrics
        self.total_workflows_executed += 1

        logger.info(f"工作流开始监控: {event.workflow_id}")

    def _handle_workflow_completed(self, event: MonitorEvent):
        """处理工作流完成事件"""
        if event.workflow_id in self.active_workflows:
            workflow = self.active_workflows[event.workflow_id]
            workflow.end_time = event.timestamp
            workflow.total_duration = event.duration

            # 计算成功率
            if workflow.total_tasks > 0:
                workflow.success_rate = workflow.completed_tasks / workflow.total_tasks

            # 计算平均任务时长
            if workflow.completed_tasks > 0:
                total_task_duration = sum(
                    task.duration for task in workflow.tasks.values()
                    if task.end_time is not None
                )
                workflow.average_task_duration = total_task_duration / workflow.completed_tasks

            # 计算并行效率
            workflow.parallel_efficiency = self._calculate_parallel_efficiency(workflow)

            # 移出活跃列表
            del self.active_workflows[event.workflow_id]
            self.total_execution_time += workflow.total_duration

            logger.info(f"工作流完成监控: {event.workflow_id}, 成功率: {workflow.success_rate:.2%}")

    def _handle_workflow_failed(self, event: MonitorEvent):
        """处理工作流失败事件"""
        if event.workflow_id in self.active_workflows:
            workflow = self.active_workflows[event.workflow_id]
            workflow.end_time = event.timestamp
            workflow.total_duration = event.duration

            # 移出活跃列表
            del self.active_workflows[event.workflow_id]

            logger.warning(f"工作流执行失败: {event.workflow_id}")

    def _handle_task_started(self, event: MonitorEvent):
        """处理任务开始事件"""
        if event.workflow_id in self.workflows and event.task_id:
            workflow = self.workflows[event.workflow_id]

            task_metrics = TaskMetrics(
                task_id=event.task_id,
                agent_name=event.agent_name or "",
                start_time=event.timestamp,
                status="running"
            )

            workflow.tasks[event.task_id] = task_metrics
            workflow.running_tasks += 1

            # 更新Agent状态
            if event.agent_name:
                self.current_agent_status[event.agent_name] = "busy"

            logger.info(f"任务开始: {event.task_id} ({event.agent_name})")

    def _handle_task_completed(self, event: MonitorEvent):
        """处理任务完成事件"""
        if event.workflow_id in self.workflows and event.task_id:
            workflow = self.workflows[event.workflow_id]

            if event.task_id in workflow.tasks:
                task = workflow.tasks[event.task_id]
                task.end_time = event.timestamp
                task.duration = event.duration
                task.status = "completed"

                workflow.completed_tasks += 1
                workflow.running_tasks -= 1
                self.total_tasks_executed += 1

                # 更新Agent状态
                if task.agent_name:
                    self.current_agent_status[task.agent_name] = "idle"

                logger.info(f"任务完成: {event.task_id} ({task.agent_name}), 耗时: {event.duration:.2f}秒")

    def _handle_task_failed(self, event: MonitorEvent):
        """处理任务失败事件"""
        if event.workflow_id in self.workflows and event.task_id:
            workflow = self.workflows[event.workflow_id]

            if event.task_id in workflow.tasks:
                task = workflow.tasks[event.task_id]
                task.end_time = event.timestamp
                task.duration = event.duration
                task.status = "failed"
                task.error_message = event.message

                workflow.failed_tasks += 1
                workflow.running_tasks -= 1

                # 更新Agent状态
                if task.agent_name:
                    self.current_agent_status[task.agent_name] = "error"

                logger.warning(f"任务失败: {event.task_id} ({task.agent_name}), 错误: {event.message}")

    def _handle_agent_status_change(self, event: MonitorEvent):
        """处理Agent状态变化事件"""
        if event.agent_name:
            old_status = self.current_agent_status.get(event.agent_name, "unknown")
            new_status = event.data.get("status", "unknown")
            self.current_agent_status[event.agent_name] = new_status

            logger.debug(f"Agent状态变化: {event.agent_name} {old_status} -> {new_status}")

    def _handle_resource_update(self, event: MonitorEvent):
        """处理资源更新事件"""
        if "resource_type" in event.data and "value" in event.data:
            resource_type = event.data["resource_type"]
            value = event.data["value"]
            self.resource_usage[resource_type] = value

    def _calculate_parallel_efficiency(self, workflow: WorkflowMetrics) -> float:
        """
        计算并行执行效率

        Args:
            workflow: 工作流指标

        Returns:
            float: 并行效率（0.0-1.0）
        """
        if not workflow.tasks or workflow.total_duration <= 0:
            return 0.0

        # 计算理论最小执行时间（所有任务顺序执行）
        sequential_time = sum(task.duration for task in workflow.tasks.values()
                            if task.end_time is not None)

        if sequential_time <= 0:
            return 0.0

        # 并行效率 = 顺序执行时间 / 实际执行时间
        efficiency = min(sequential_time / workflow.total_duration, 1.0)
        return efficiency

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """
        获取工作流状态

        Args:
            workflow_id: 工作流ID

        Returns:
            Optional[Dict]: 工作流状态信息
        """
        if workflow_id not in self.workflows:
            return None

        workflow = self.workflows[workflow_id]
        is_active = workflow_id in self.active_workflows

        return {
            "workflow_id": workflow_id,
            "status": "running" if is_active else "completed",
            "start_time": workflow.start_time.isoformat(),
            "end_time": workflow.end_time.isoformat() if workflow.end_time else None,
            "duration": workflow.total_duration,
            "progress": {
                "total": workflow.total_tasks,
                "completed": workflow.completed_tasks,
                "failed": workflow.failed_tasks,
                "running": workflow.running_tasks,
                "percentage": (workflow.completed_tasks / workflow.total_tasks * 100)
                            if workflow.total_tasks > 0 else 0
            },
            "metrics": {
                "success_rate": workflow.success_rate,
                "average_task_duration": workflow.average_task_duration,
                "parallel_efficiency": workflow.parallel_efficiency
            },
            "tasks": [
                {
                    "task_id": task.task_id,
                    "agent": task.agent_name,
                    "status": task.status,
                    "duration": task.duration,
                    "progress": task.progress,
                    "error": task.error_message
                }
                for task in workflow.tasks.values()
            ]
        }

    def get_active_workflows(self) -> List[Dict[str, Any]]:
        """获取所有活跃工作流状态"""
        return [self.get_workflow_status(wf_id) for wf_id in self.active_workflows.keys()]

    def get_agent_status(self) -> Dict[str, str]:
        """获取所有Agent的当前状态"""
        return self.current_agent_status.copy()

    def get_resource_usage(self) -> Dict[str, float]:
        """获取资源使用情况"""
        return self.resource_usage.copy()

    def get_recent_events(self, limit: int = 50, event_types: List[MonitorEventType] = None) -> List[Dict[str, Any]]:
        """
        获取最近的事件

        Args:
            limit: 事件数量限制
            event_types: 过滤的事件类型

        Returns:
            List[Dict]: 事件列表
        """
        events = list(self.events)

        # 过滤事件类型
        if event_types:
            events = [e for e in events if e.event_type in event_types]

        # 按时间倒序排列
        events.sort(key=lambda e: e.timestamp, reverse=True)

        # 限制数量
        events = events[:limit]

        return [
            {
                "event_type": event.event_type.value,
                "timestamp": event.timestamp.isoformat(),
                "workflow_id": event.workflow_id,
                "task_id": event.task_id,
                "agent_name": event.agent_name,
                "message": event.message,
                "duration": event.duration,
                "data": event.data
            }
            for event in events
        ]

    def get_statistics(self) -> Dict[str, Any]:
        """获取监控统计信息"""
        now = datetime.now()
        active_count = len(self.active_workflows)

        # 计算平均值
        avg_workflow_duration = (self.total_execution_time / self.total_workflows_executed
                               if self.total_workflows_executed > 0 else 0)

        # 最近1小时的活动
        recent_events = [e for e in self.events
                        if now - e.timestamp <= timedelta(hours=1)]

        return {
            "monitoring_status": "active" if self.is_monitoring else "inactive",
            "total_events": len(self.events),
            "active_workflows": active_count,
            "completed_workflows": self.total_workflows_executed - active_count,
            "total_tasks_executed": self.total_tasks_executed,
            "total_execution_time": self.total_execution_time,
            "average_workflow_duration": avg_workflow_duration,
            "recent_activity": {
                "events_last_hour": len(recent_events),
                "active_agents": len([a for a, s in self.current_agent_status.items()
                                    if s in ["busy", "running"]]),
                "resource_usage": self.resource_usage
            },
            "event_distribution": self._get_event_distribution()
        }

    def _get_event_distribution(self) -> Dict[str, int]:
        """获取事件类型分布统计"""
        distribution = defaultdict(int)
        for event in self.events:
            distribution[event.event_type.value] += 1
        return dict(distribution)

    def subscribe(self, callback: Callable[[MonitorEvent], None]):
        """
        订阅监控事件

        Args:
            callback: 事件回调函数
        """
        self.subscribers.append(callback)

    def _notify_subscribers(self, event: MonitorEvent):
        """通知所有订阅者"""
        for callback in self.subscribers:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"通知订阅者时发生错误: {e}")

    def export_workflow_report(self, workflow_id: str, format: str = "json") -> Optional[str]:
        """
        导出工作流执行报告

        Args:
            workflow_id: 工作流ID
            format: 导出格式（json/yaml）

        Returns:
            Optional[str]: 报告内容
        """
        status = self.get_workflow_status(workflow_id)
        if not status:
            return None

        # 添加详细分析
        workflow = self.workflows[workflow_id]
        enhanced_report = {
            **status,
            "analysis": {
                "bottlenecks": self._analyze_bottlenecks(workflow),
                "recommendations": self._generate_recommendations(workflow),
                "performance_summary": self._generate_performance_summary(workflow)
            }
        }

        try:
            if format.lower() == "json":
                return json.dumps(enhanced_report, indent=2, ensure_ascii=False, default=str)
            elif format.lower() == "yaml":
                import yaml
                return yaml.dump(enhanced_report, default_flow_style=False, allow_unicode=True)
            else:
                logger.error(f"不支持的导出格式: {format}")
                return None
        except Exception as e:
            logger.error(f"导出报告失败: {e}")
            return None

    def _analyze_bottlenecks(self, workflow: WorkflowMetrics) -> List[str]:
        """分析工作流瓶颈"""
        bottlenecks = []

        if not workflow.tasks:
            return bottlenecks

        # 找出耗时最长的任务
        max_duration = max((task.duration for task in workflow.tasks.values()
                          if task.end_time is not None), default=0)

        if max_duration > 0:
            slow_tasks = [
                task for task in workflow.tasks.values()
                if task.duration > max_duration * 0.8 and task.end_time is not None
            ]

            if slow_tasks:
                agents = [task.agent_name for task in slow_tasks]
                bottlenecks.append(f"慢任务瓶颈: {', '.join(agents)} (耗时>{max_duration*0.8:.1f}秒)")

        # 分析失败率高的Agent
        if workflow.failed_tasks > 0:
            failed_agents = [task.agent_name for task in workflow.tasks.values()
                           if task.status == "failed"]
            if failed_agents:
                bottlenecks.append(f"高失败率Agent: {', '.join(set(failed_agents))}")

        return bottlenecks

    def _generate_recommendations(self, workflow: WorkflowMetrics) -> List[str]:
        """生成优化建议"""
        recommendations = []

        # 并行效率建议
        if workflow.parallel_efficiency < 0.7:
            recommendations.append("并行效率偏低，建议检查任务依赖关系和资源分配")

        # 成功率建议
        if workflow.success_rate < 0.9:
            recommendations.append("任务成功率偏低，建议优化Agent配置和错误处理")

        # 执行时间建议
        if workflow.average_task_duration > 300:  # 5分钟
            recommendations.append("平均任务执行时间较长，建议优化任务拆分和并行度")

        return recommendations

    def _generate_performance_summary(self, workflow: WorkflowMetrics) -> Dict[str, Any]:
        """生成性能摘要"""
        return {
            "efficiency_grade": self._grade_efficiency(workflow.parallel_efficiency),
            "reliability_grade": self._grade_reliability(workflow.success_rate),
            "speed_grade": self._grade_speed(workflow.average_task_duration),
            "overall_score": self._calculate_overall_score(workflow)
        }

    def _grade_efficiency(self, efficiency: float) -> str:
        """评估效率等级"""
        if efficiency >= 0.9:
            return "A"
        elif efficiency >= 0.7:
            return "B"
        elif efficiency >= 0.5:
            return "C"
        else:
            return "D"

    def _grade_reliability(self, success_rate: float) -> str:
        """评估可靠性等级"""
        if success_rate >= 0.95:
            return "A"
        elif success_rate >= 0.85:
            return "B"
        elif success_rate >= 0.7:
            return "C"
        else:
            return "D"

    def _grade_speed(self, avg_duration: float) -> str:
        """评估速度等级"""
        if avg_duration <= 60:  # 1分钟
            return "A"
        elif avg_duration <= 180:  # 3分钟
            return "B"
        elif avg_duration <= 300:  # 5分钟
            return "C"
        else:
            return "D"

    def _calculate_overall_score(self, workflow: WorkflowMetrics) -> float:
        """计算综合评分"""
        efficiency_score = workflow.parallel_efficiency * 40
        reliability_score = workflow.success_rate * 40
        # 速度评分：任务时长越短分数越高
        speed_score = max(0, 20 - (workflow.average_task_duration / 60) * 2)

        return min(100, efficiency_score + reliability_score + speed_score)

# 全局监控器实例
_execution_monitor = None

def get_execution_monitor() -> ExecutionMonitor:
    """获取全局执行监控器实例"""
    global _execution_monitor
    if _execution_monitor is None:
        _execution_monitor = ExecutionMonitor()
        _execution_monitor.start_monitoring()
    return _execution_monitor