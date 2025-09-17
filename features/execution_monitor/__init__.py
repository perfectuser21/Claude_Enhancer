"""
Perfect21 执行监控和可视化系统
实时监控多Agent工作流执行，解决黑箱问题
"""

from .monitor import (
    ExecutionMonitor,
    MonitorEvent,
    MonitorEventType,
    TaskMetrics,
    WorkflowMetrics,
    get_execution_monitor
)

from .visualizer import (
    ConsoleVisualizer,
    WebVisualizer,
    VisualizationManager,
    get_visualization_manager
)

from .capability import CAPABILITY

__all__ = [
    'ExecutionMonitor',
    'MonitorEvent',
    'MonitorEventType',
    'TaskMetrics',
    'WorkflowMetrics',
    'get_execution_monitor',
    'ConsoleVisualizer',
    'WebVisualizer',
    'VisualizationManager',
    'get_visualization_manager',
    'CAPABILITY'
]

def create_monitoring_system(auto_start: bool = True, enable_console: bool = False):
    """
    创建完整的监控系统

    Args:
        auto_start: 是否自动启动监控
        enable_console: 是否启用控制台显示

    Returns:
        tuple: (monitor, visualizer) 监控器和可视化管理器
    """
    # 创建监控器
    monitor = get_execution_monitor()

    # 创建可视化管理器
    visualizer = get_visualization_manager(monitor)

    # 自动启动
    if auto_start:
        monitor.start_monitoring()

    # 启用控制台显示
    if enable_console:
        visualizer.start_console_display()

    return monitor, visualizer

def start_workflow_monitoring(workflow_id: str, total_tasks: int = 0):
    """
    开始监控工作流执行

    Args:
        workflow_id: 工作流ID
        total_tasks: 总任务数
    """
    monitor = get_execution_monitor()
    monitor.emit_event(
        MonitorEventType.WORKFLOW_STARTED,
        workflow_id=workflow_id,
        message=f"工作流 {workflow_id} 开始执行",
        data={"total_tasks": total_tasks}
    )

def complete_workflow_monitoring(workflow_id: str, duration: float, success: bool = True):
    """
    完成工作流监控

    Args:
        workflow_id: 工作流ID
        duration: 执行时长
        success: 是否成功
    """
    monitor = get_execution_monitor()
    event_type = MonitorEventType.WORKFLOW_COMPLETED if success else MonitorEventType.WORKFLOW_FAILED
    monitor.emit_event(
        event_type,
        workflow_id=workflow_id,
        message=f"工作流 {workflow_id} {'成功完成' if success else '执行失败'}",
        duration=duration
    )

def start_task_monitoring(workflow_id: str, task_id: str, agent_name: str, task_description: str):
    """
    开始监控任务执行

    Args:
        workflow_id: 工作流ID
        task_id: 任务ID
        agent_name: Agent名称
        task_description: 任务描述
    """
    monitor = get_execution_monitor()
    monitor.emit_event(
        MonitorEventType.TASK_STARTED,
        workflow_id=workflow_id,
        task_id=task_id,
        agent_name=agent_name,
        message=f"Agent {agent_name} 开始执行任务: {task_description}"
    )

def complete_task_monitoring(workflow_id: str, task_id: str, agent_name: str,
                           duration: float, success: bool = True, error_message: str = None):
    """
    完成任务监控

    Args:
        workflow_id: 工作流ID
        task_id: 任务ID
        agent_name: Agent名称
        duration: 执行时长
        success: 是否成功
        error_message: 错误信息
    """
    monitor = get_execution_monitor()
    event_type = MonitorEventType.TASK_COMPLETED if success else MonitorEventType.TASK_FAILED
    message = f"Agent {agent_name} {'成功完成' if success else '执行失败'}任务 {task_id}"
    if not success and error_message:
        message += f": {error_message}"

    monitor.emit_event(
        event_type,
        workflow_id=workflow_id,
        task_id=task_id,
        agent_name=agent_name,
        message=message,
        duration=duration
    )

def update_agent_status(agent_name: str, status: str, additional_data: dict = None):
    """
    更新Agent状态

    Args:
        agent_name: Agent名称
        status: 新状态 (busy, idle, error, running, stopped)
        additional_data: 额外数据
    """
    monitor = get_execution_monitor()
    data = {"status": status}
    if additional_data:
        data.update(additional_data)

    monitor.emit_event(
        MonitorEventType.AGENT_STATUS_CHANGE,
        workflow_id="system",
        agent_name=agent_name,
        message=f"Agent {agent_name} 状态变更为: {status}",
        data=data
    )

def update_resource_usage(resource_type: str, usage: float):
    """
    更新资源使用情况

    Args:
        resource_type: 资源类型 (cpu, memory, disk, network)
        usage: 使用率 (0.0-100.0)
    """
    monitor = get_execution_monitor()
    monitor.emit_event(
        MonitorEventType.RESOURCE_UPDATE,
        workflow_id="system",
        message=f"{resource_type.upper()}使用率: {usage:.1f}%",
        data={"resource_type": resource_type, "value": usage}
    )

def report_error(workflow_id: str, task_id: str = None, agent_name: str = None,
                error_message: str = "", error_data: dict = None):
    """
    报告错误事件

    Args:
        workflow_id: 工作流ID
        task_id: 任务ID
        agent_name: Agent名称
        error_message: 错误消息
        error_data: 错误数据
    """
    monitor = get_execution_monitor()
    monitor.emit_event(
        MonitorEventType.ERROR_OCCURRED,
        workflow_id=workflow_id,
        task_id=task_id,
        agent_name=agent_name,
        message=error_message,
        data=error_data or {}
    )

def get_monitoring_dashboard_data():
    """
    获取监控仪表板数据

    Returns:
        dict: 包含所有监控数据的字典
    """
    monitor = get_execution_monitor()
    return {
        "statistics": monitor.get_statistics(),
        "active_workflows": monitor.get_active_workflows(),
        "agent_status": monitor.get_agent_status(),
        "resource_usage": monitor.get_resource_usage(),
        "recent_events": monitor.get_recent_events(limit=20)
    }

def generate_workflow_analysis_report(workflow_id: str, format: str = "json"):
    """
    生成工作流分析报告

    Args:
        workflow_id: 工作流ID
        format: 报告格式 (json, yaml, html)

    Returns:
        str: 报告内容
    """
    monitor = get_execution_monitor()
    return monitor.export_workflow_report(workflow_id, format)

def start_real_time_dashboard():
    """启动实时监控仪表板"""
    visualizer = get_visualization_manager()
    visualizer.start_console_display()
    print("🚀 Perfect21 实时监控仪表板已启动")
    print("💡 按 Ctrl+C 停止监控")

def stop_real_time_dashboard():
    """停止实时监控仪表板"""
    visualizer = get_visualization_manager()
    visualizer.stop_console_display()
    print("⏹️ Perfect21 实时监控仪表板已停止")

def generate_static_dashboard(filename: str = None) -> str:
    """
    生成静态HTML仪表板

    Args:
        filename: 输出文件名

    Returns:
        str: 生成的文件路径
    """
    visualizer = get_visualization_manager()
    return visualizer.generate_html_report(filename)

def show_workflow_summary(workflow_id: str):
    """显示工作流执行摘要"""
    visualizer = get_visualization_manager()
    visualizer.display_workflow_summary(workflow_id)

# 监控系统初始化函数
def initialize_monitoring_system(auto_start: bool = True, enable_console: bool = False):
    """
    初始化监控系统

    Args:
        auto_start: 是否自动启动监控
        enable_console: 是否启用控制台显示

    Returns:
        dict: 初始化状态
    """
    try:
        monitor, visualizer = create_monitoring_system(auto_start, enable_console)

        stats = monitor.get_statistics()

        result = {
            "status": "success",
            "monitoring_active": stats["monitoring_status"] == "active",
            "console_display": enable_console,
            "features": {
                "real_time_monitoring": True,
                "workflow_tracking": True,
                "agent_status_monitoring": True,
                "resource_usage_tracking": True,
                "event_logging": True,
                "performance_analysis": True,
                "bottleneck_detection": True,
                "html_report_generation": True
            }
        }

        print("✅ Perfect21执行监控系统已初始化")
        print(f"   - 监控状态: {'🟢 活跃' if result['monitoring_active'] else '🔴 未启动'}")
        print(f"   - 控制台显示: {'🟢 启用' if enable_console else '🔴 禁用'}")
        print("   - 支持功能:")
        for feature, enabled in result["features"].items():
            print(f"     • {feature}: {'✅' if enabled else '❌'}")

        return result

    except Exception as e:
        print(f"❌ 监控系统初始化失败: {e}")
        return {"status": "failed", "error": str(e)}

# 便捷监控装饰器
def monitor_workflow(workflow_id: str = None):
    """
    工作流监控装饰器

    Args:
        workflow_id: 工作流ID，如果为None则自动生成
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            from datetime import datetime

            # 生成工作流ID
            wf_id = workflow_id or f"workflow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # 开始监控
            start_workflow_monitoring(wf_id)
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                complete_workflow_monitoring(wf_id, duration, success=True)
                return result
            except Exception as e:
                duration = time.time() - start_time
                complete_workflow_monitoring(wf_id, duration, success=False)
                report_error(wf_id, error_message=str(e))
                raise

        return wrapper
    return decorator

def monitor_task(task_id: str = None, agent_name: str = "unknown"):
    """
    任务监控装饰器

    Args:
        task_id: 任务ID，如果为None则自动生成
        agent_name: Agent名称
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            from datetime import datetime

            # 生成任务ID
            t_id = task_id or f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            wf_id = getattr(wrapper, '_workflow_id', 'default_workflow')

            # 开始监控
            start_task_monitoring(wf_id, t_id, agent_name, func.__name__)
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                complete_task_monitoring(wf_id, t_id, agent_name, duration, success=True)
                return result
            except Exception as e:
                duration = time.time() - start_time
                complete_task_monitoring(wf_id, t_id, agent_name, duration,
                                       success=False, error_message=str(e))
                raise

        return wrapper
    return decorator