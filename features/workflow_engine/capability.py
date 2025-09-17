"""
workflow_engine功能描述文件
Perfect21多Agent工作流执行引擎
"""

CAPABILITY = {
    "name": "workflow_engine",
    "version": "1.0.0",
    "description": "Perfect21多Agent工作流执行引擎，实现真正的并行协作",
    "category": "execution",
    "priority": "critical",
    "is_core": True,

    "agents_can_use": [
        "orchestrator",
        "project-manager",
        "backend-architect",
        "devops-engineer"
    ],

    "functions": {
        "execute_parallel_tasks": "并行执行多个agent任务",
        "execute_sequential_pipeline": "顺序执行任务管道",
        "handle_dependencies": "处理任务依赖关系",
        "monitor_execution": "监控多agent执行状态",
        "integrate_results": "整合多个agent的执行结果",
        "create_task_graph": "创建任务依赖图",
        "validate_workflow": "验证工作流的有效性",
        "get_execution_status": "获取当前执行状态"
    },

    "integration_points": [
        "orchestrator_call",      # orchestrator调用时
        "multi_agent_request",    # 多agent请求时
        "parallel_execution",     # 并行执行时
        "workflow_monitoring",    # 工作流监控时
        "result_integration"      # 结果整合时
    ],

    "dependencies": [
        "typing",
        "concurrent.futures",
        "logging",
        "datetime",
        "json"
    ],

    "workflow_patterns": [
        "parallel_execution",     # 并行执行模式
        "sequential_pipeline",    # 顺序管道模式
        "dependency_graph",       # 依赖图模式
        "conditional_routing",    # 条件路由模式
        "error_recovery"          # 错误恢复模式
    ],

    "execution_config": {
        "max_parallel_agents": 10,
        "timeout_per_task": 300,  # 5分钟
        "retry_count": 3,
        "enable_monitoring": True,
        "auto_integration": True
    }
}