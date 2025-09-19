"""
execution_monitor功能描述文件
Perfect21工作流状态监控系统
"""

CAPABILITY = {
    "name": "execution_monitor",
    "version": "1.0.0",
    "description": "Perfect21工作流状态监控系统，监控Claude Code执行多Agent工作流时的状态",
    "category": "monitoring",
    "priority": "high",
    "is_core": True,

    "agents_can_use": [
        "orchestrator",
        "project-manager",
        "devops-engineer",
        "monitoring-specialist",
        "performance-engineer"
    ],

    "functions": {
        "start_monitoring": "启动执行监控",
        "stop_monitoring": "停止执行监控",
        "emit_event": "发送监控事件",
        "get_workflow_status": "获取工作流执行状态",
        "get_active_workflows": "获取所有活跃工作流",
        "get_agent_status": "获取Agent状态信息",
        "get_recent_events": "获取最近的监控事件",
        "get_statistics": "获取监控统计信息",
        "export_workflow_report": "导出工作流执行报告",
        "start_console_display": "启动控制台实时显示",
        "generate_html_report": "生成HTML可视化报告"
    },

    "event_types": [
        "workflow_started",      # 工作流开始
        "workflow_completed",    # 工作流完成
        "workflow_failed",       # 工作流失败
        "task_started",         # 任务开始
        "task_completed",       # 任务完成
        "task_failed",          # 任务失败
        "task_progress",        # 任务进度更新
        "agent_status_change",  # Agent状态变化
        "resource_update",      # 资源使用更新
        "error_occurred"        # 错误发生
    ],

    "visualization_features": [
        "real_time_console_dashboard",  # 实时控制台仪表板
        "html_static_reports",          # HTML静态报告
        "workflow_progress_tracking",   # 工作流进度跟踪
        "agent_status_monitoring",      # Agent状态监控
        "resource_usage_display",       # 资源使用显示
        "event_timeline_view",          # 事件时间轴视图
        "performance_metrics",          # 性能指标
        "bottleneck_analysis",          # 瓶颈分析
        "success_rate_tracking",        # 成功率跟踪
        "parallel_efficiency_metrics"   # 并行效率指标
    ],

    "monitoring_metrics": {
        "workflow_level": [
            "total_duration",           # 总执行时间
            "success_rate",            # 成功率
            "parallel_efficiency",     # 并行效率
            "task_distribution",       # 任务分布
            "completion_timeline"      # 完成时间线
        ],
        "task_level": [
            "execution_time",          # 执行时间
            "agent_assignment",        # Agent分配
            "dependency_chain",        # 依赖链
            "resource_usage",          # 资源使用
            "error_details"           # 错误详情
        ],
        "agent_level": [
            "utilization_rate",       # 利用率
            "task_success_rate",      # 任务成功率
            "average_task_time",      # 平均任务时间
            "concurrent_capacity",    # 并发能力
            "error_frequency"         # 错误频率
        ],
        "system_level": [
            "total_throughput",       # 总吞吐量
            "resource_efficiency",   # 资源效率
            "system_load",           # 系统负载
            "concurrent_workflows",  # 并发工作流数
            "error_rate_trend"      # 错误率趋势
        ]
    },

    "integration_points": [
        "workflow_execution_start",    # 工作流执行开始时
        "task_delegation",             # 任务委托时
        "agent_status_change",         # Agent状态变化时
        "error_handling",              # 错误处理时
        "performance_analysis",        # 性能分析时
        "report_generation"            # 报告生成时
    ],

    "dependencies": [
        "typing",
        "dataclasses",
        "enum",
        "logging",
        "json",
        "threading",
        "collections",
        "queue",
        "datetime"
    ],

    "real_time_features": {
        "live_dashboard": True,
        "auto_refresh": True,
        "event_streaming": True,
        "alert_notifications": True,
        "progress_visualization": True,
        "resource_monitoring": True,
        "concurrent_workflow_tracking": True,
        "bottleneck_detection": True
    },

    "export_formats": [
        "json",              # JSON格式报告
        "yaml",              # YAML格式报告
        "html",              # HTML可视化报告
        "csv",               # CSV数据导出
        "console_display"    # 控制台实时显示
    ],

    "configuration": {
        "max_events": 10000,           # 最大事件数量
        "refresh_interval": 1.0,       # 刷新间隔(秒)
        "auto_cleanup": True,          # 自动清理旧数据
        "enable_console_display": True, # 启用控制台显示
        "enable_html_export": True,    # 启用HTML导出
        "performance_analysis": True,   # 启用性能分析
        "bottleneck_detection": True,  # 启用瓶颈检测
        "resource_monitoring": True    # 启用资源监控
    },

    "usage_examples": {
        "start_monitoring": "monitor = get_execution_monitor(); monitor.start_monitoring()",
        "emit_workflow_event": "monitor.emit_event(MonitorEventType.WORKFLOW_STARTED, 'wf_001', message='全栈开发工作流开始')",
        "get_workflow_status": "status = monitor.get_workflow_status('workflow_001')",
        "start_console_display": "visualizer = get_visualization_manager(); visualizer.start_console_display()",
        "generate_html_report": "report_file = visualizer.generate_html_report('dashboard.html')",
        "export_workflow_report": "report = monitor.export_workflow_report('wf_001', 'json')"
    }
}