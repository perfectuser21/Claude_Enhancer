"""
capability_discovery功能描述文件
动态发现和集成Perfect21新功能的元功能
"""

CAPABILITY = {
    "name": "capability_discovery",
    "version": "1.0.0",
    "description": "动态发现和集成Perfect21新功能的元功能模块",
    "category": "meta",
    "priority": "critical",
    "is_core": True,  # 标记为核心功能，优先加载

    "agents_can_use": [
        "orchestrator",
        "project-manager",
        "backend-architect",
        "devops-engineer"
    ],

    "functions": {
        "scan_features": "自动扫描features目录发现新功能模块",
        "load_capability": "动态加载单个功能模块",
        "register_to_agents": "向claude-code-unified-agents注册功能",
        "hot_reload": "运行时热加载新增功能",
        "validate_capability": "验证功能模块的完整性",
        "get_capability_catalog": "获取所有可用功能的目录"
    },

    "integration_points": [
        "system_startup",     # 系统启动时
        "feature_added",      # 新功能添加时
        "runtime_update",     # 运行时更新
        "before_task_routing" # 任务路由前
    ],

    "dependencies": [
        "os",
        "sys",
        "importlib",
        "pathlib",
        "typing",
        "logging"
    ],

    "file_patterns": [
        "**/*capability.py",  # 功能描述文件
        "**/capability.yaml", # YAML格式描述
        "**/feature.json"     # JSON格式描述
    ],

    "auto_discovery": {
        "enabled": True,
        "scan_interval": 30,  # 秒
        "watch_directories": ["features/"],
        "exclude_patterns": ["__pycache__", "*.pyc", ".git"]
    },

    "registration": {
        "auto_register": True,
        "registration_timeout": 10,
        "retry_count": 3,
        "fallback_enabled": True
    }
}