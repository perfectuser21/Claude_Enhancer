"""
capability_discovery功能描述文件
动态发现和集成Perfect21新功能的元功能
"""

CAPABILITY = {
    "name": "capability_discovery",
    "version": "2.3.0",
    "description": "动态发现Perfect21功能并为@orchestrator提供集成桥梁",
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
        "get_capability_catalog": "获取所有可用功能的目录",
        "get_perfect21_capabilities": "获取Perfect21能力信息供@orchestrator使用",
        "save_capabilities_manifest": "保存能力清单到临时文件",
        "get_capabilities_for_orchestrator": "生成@orchestrator专用的功能描述"
    },

    "integration_points": [
        "system_startup",     # 系统启动时
        "feature_added",      # 新功能添加时
        "runtime_update",     # 运行时更新
        "before_task_routing", # 任务路由前
        "before_orchestrator_call", # @orchestrator调用前
        "capability_update",     # 功能更新时
        "feature_discovery"      # 功能发现时
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

class CapabilityLoader:
    """能力加载器 - Mock实现"""

    def __init__(self):
        self.capabilities = {}

    def scan_capabilities(self, directory):
        """扫描能力目录"""
        import os
        import json
        capabilities = []

        if not os.path.exists(directory):
            return capabilities

        for file in os.listdir(directory):
            if file.endswith('.json'):
                try:
                    file_path = os.path.join(directory, file)
                    cap = self.load_capability(file_path)
                    if cap:
                        capabilities.append(cap)
                except:
                    pass

        return capabilities

    def load_capability(self, file_path):
        """加载能力文件"""
        import json
        import os

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Capability file not found: {file_path}")

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            return Capability(
                name=data.get('name'),
                version=data.get('version'),
                description=data.get('description'),
                entry_point=data.get('entry_point'),
                dependencies=data.get('dependencies', []),
                metadata=data.get('metadata', {})
            )
        except json.JSONDecodeError:
            raise Exception(f"Invalid JSON in capability file: {file_path}")

    def validate_capability(self, capability):
        """验证能力"""
        if not capability.name or not capability.version:
            return False
        return True

class Capability:
    """能力对象"""

    def __init__(self, name, version, description, entry_point, dependencies=None, metadata=None):
        self.name = name
        self.version = version
        self.description = description
        self.entry_point = entry_point
        self.dependencies = dependencies or []
        self.metadata = metadata or {}

    def execute(self):
        """执行能力"""
        # Mock执行
        return "success"
