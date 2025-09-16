#!/usr/bin/env python3
"""
Perfect21 并行任务监控器
实时监控多Agent协作状态，提供串行/并行任务可视化
"""

import asyncio
import threading
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json

class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ExecutionMode(Enum):
    SERIAL = "串行"
    PARALLEL = "并行"
    MIXED = "混合"

@dataclass
class TaskInfo:
    task_id: str
    agent_name: str
    description: str
    status: TaskStatus
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    result: Optional[Any] = None
    error: Optional[str] = None

class ParallelMonitor:
    """并行任务监控器"""

    def __init__(self):
        self.tasks: Dict[str, TaskInfo] = {}
        self.active_tasks: Dict[str, TaskInfo] = {}
        self.execution_history: List[Dict[str, Any]] = []
        self.is_monitoring = False
        self._monitor_thread = None

    def detect_execution_mode(self) -> ExecutionMode:
        """检测当前执行模式"""
        running_tasks = [t for t in self.active_tasks.values()
                        if t.status == TaskStatus.RUNNING]

        if len(running_tasks) == 0:
            return ExecutionMode.SERIAL
        elif len(running_tasks) == 1:
            return ExecutionMode.SERIAL
        else:
            return ExecutionMode.PARALLEL

    def add_task(self, task_id: str, agent_name: str, description: str) -> None:
        """添加新任务"""
        task = TaskInfo(
            task_id=task_id,
            agent_name=agent_name,
            description=description,
            status=TaskStatus.PENDING
        )
        self.tasks[task_id] = task
        self.active_tasks[task_id] = task

    def start_task(self, task_id: str) -> None:
        """开始执行任务"""
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.RUNNING
            self.tasks[task_id].start_time = time.time()

    def complete_task(self, task_id: str, result: Any = None) -> None:
        """完成任务"""
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.COMPLETED
            self.tasks[task_id].end_time = time.time()
            self.tasks[task_id].result = result
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]

    def fail_task(self, task_id: str, error: str) -> None:
        """任务失败"""
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.FAILED
            self.tasks[task_id].end_time = time.time()
            self.tasks[task_id].error = error
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]

    def get_status_display(self) -> str:
        """获取状态显示字符串"""
        mode = self.detect_execution_mode()
        running_count = len([t for t in self.active_tasks.values()
                           if t.status == TaskStatus.RUNNING])

        status_lines = [
            f"🔍 Perfect21 任务执行监控",
            f"=" * 40,
            f"📊 执行模式: {mode.value}",
            f"🏃 运行中任务: {running_count}个",
            f"📋 总任务数: {len(self.tasks)}个",
            ""
        ]

        if self.active_tasks:
            status_lines.append("🚀 当前活跃任务:")
            for task in self.active_tasks.values():
                status_icon = {
                    TaskStatus.PENDING: "⏳",
                    TaskStatus.RUNNING: "🔄",
                    TaskStatus.COMPLETED: "✅",
                    TaskStatus.FAILED: "❌"
                }[task.status]

                duration = ""
                if task.start_time:
                    duration = f" ({time.time() - task.start_time:.1f}s)"

                status_lines.append(
                    f"  {status_icon} {task.agent_name}: {task.description[:50]}...{duration}"
                )

        # 显示最近完成的任务
        completed_tasks = [t for t in self.tasks.values()
                          if t.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]][-3:]

        if completed_tasks:
            status_lines.append("\n📈 最近完成:")
            for task in completed_tasks:
                status_icon = "✅" if task.status == TaskStatus.COMPLETED else "❌"
                duration = ""
                if task.start_time and task.end_time:
                    duration = f" ({task.end_time - task.start_time:.1f}s)"
                status_lines.append(
                    f"  {status_icon} {task.agent_name}: {task.description[:50]}...{duration}"
                )

        return "\n".join(status_lines)

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        completed_tasks = [t for t in self.tasks.values()
                          if t.status == TaskStatus.COMPLETED and t.start_time and t.end_time]

        if not completed_tasks:
            return {"total_tasks": 0, "avg_duration": 0, "success_rate": 0}

        durations = [t.end_time - t.start_time for t in completed_tasks]
        failed_count = len([t for t in self.tasks.values() if t.status == TaskStatus.FAILED])

        return {
            "total_tasks": len(self.tasks),
            "completed_tasks": len(completed_tasks),
            "failed_tasks": failed_count,
            "avg_duration": sum(durations) / len(durations) if durations else 0,
            "success_rate": len(completed_tasks) / len(self.tasks) if self.tasks else 0,
            "execution_mode": self.detect_execution_mode().value
        }

    def start_monitoring(self) -> None:
        """开始监控"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._monitor_thread.start()

    def stop_monitoring(self) -> None:
        """停止监控"""
        self.is_monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1)

    def _monitor_loop(self) -> None:
        """监控循环"""
        while self.is_monitoring:
            # 记录执行历史
            stats = self.get_performance_stats()
            stats['timestamp'] = time.time()
            self.execution_history.append(stats)

            # 保持历史记录在合理范围内
            if len(self.execution_history) > 100:
                self.execution_history = self.execution_history[-100:]

            time.sleep(0.5)  # 每0.5秒更新一次

# 全局监控器实例
_global_monitor = None

def get_global_monitor() -> ParallelMonitor:
    """获取全局监控器实例"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = ParallelMonitor()
        _global_monitor.start_monitoring()
    return _global_monitor

def monitor_task(task_id: str, agent_name: str, description: str):
    """监控任务装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            monitor = get_global_monitor()
            monitor.add_task(task_id, agent_name, description)
            monitor.start_task(task_id)

            try:
                result = func(*args, **kwargs)
                monitor.complete_task(task_id, result)
                return result
            except Exception as e:
                monitor.fail_task(task_id, str(e))
                raise
        return wrapper
    return decorator

if __name__ == "__main__":
    # 测试示例
    import uuid

    monitor = ParallelMonitor()
    monitor.start_monitoring()

    # 模拟任务
    task1_id = str(uuid.uuid4())
    task2_id = str(uuid.uuid4())

    monitor.add_task(task1_id, "@code-reviewer", "代码质量检查")
    monitor.add_task(task2_id, "@test-engineer", "运行测试套件")

    print("=== 串行执行演示 ===")
    monitor.start_task(task1_id)
    print(monitor.get_status_display())
    time.sleep(2)
    monitor.complete_task(task1_id)

    monitor.start_task(task2_id)
    print("\n" + monitor.get_status_display())
    time.sleep(1)
    monitor.complete_task(task2_id)

    print("\n=== 并行执行演示 ===")
    task3_id = str(uuid.uuid4())
    task4_id = str(uuid.uuid4())

    monitor.add_task(task3_id, "@security-auditor", "安全扫描")
    monitor.add_task(task4_id, "@performance-engineer", "性能分析")

    # 同时启动两个任务(并行)
    monitor.start_task(task3_id)
    monitor.start_task(task4_id)
    print(monitor.get_status_display())

    time.sleep(3)
    monitor.complete_task(task3_id)
    monitor.complete_task(task4_id)

    print("\n=== 最终统计 ===")
    print(json.dumps(monitor.get_performance_stats(), indent=2, ensure_ascii=False))

    monitor.stop_monitoring()