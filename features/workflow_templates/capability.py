"""
workflow_templates功能描述文件
Perfect21工作流模板系统
"""

CAPABILITY = {
    "name": "workflow_templates",
    "version": "1.0.0",
    "description": "Perfect21工作流模板系统，提供预定义的多Agent协作模板",
    "category": "development",
    "priority": "high",
    "is_core": True,

    "agents_can_use": [
        "orchestrator",
        "project-manager",
        "backend-architect",
        "frontend-specialist",
        "devops-engineer",
        "product-strategist"
    ],

    "functions": {
        "get_template": "获取指定名称的工作流模板",
        "list_templates": "列出所有可用的工作流模板",
        "search_templates": "搜索匹配的工作流模板",
        "create_custom_template": "创建自定义工作流模板",
        "get_templates_by_category": "根据分类获取模板",
        "get_templates_by_pattern": "根据执行模式获取模板",
        "export_template": "导出模板为JSON/YAML格式",
        "validate_template": "验证模板有效性",
        "get_statistics": "获取模板系统统计信息"
    },

    "template_categories": [
        "development",    # 开发类模板
        "testing",       # 测试类模板
        "deployment",    # 部署类模板
        "analysis",      # 分析类模板
        "review",        # 审查类模板
        "research"       # 研究类模板
    ],

    "execution_patterns": [
        "parallel",      # 并行执行
        "sequential",    # 顺序执行
        "hybrid",        # 混合模式
        "conditional"    # 条件路由
    ],

    "builtin_templates": [
        "fullstack_development",        # 全栈开发
        "api_development",              # API开发
        "frontend_development",         # 前端开发
        "comprehensive_testing",        # 综合测试
        "security_audit",              # 安全审计
        "deployment_pipeline",         # 部署管道
        "container_deployment",        # 容器部署
        "code_review",                 # 代码审查
        "performance_review",          # 性能审查
        "architecture_analysis",       # 架构分析
        "codebase_analysis",           # 代码库分析
        "technology_research"          # 技术研究
    ],

    "integration_points": [
        "template_selection",      # 模板选择时
        "workflow_execution",      # 工作流执行时
        "custom_template_creation", # 自定义模板创建时
        "template_export_import",  # 模板导入导出时
        "template_validation"      # 模板验证时
    ],

    "dependencies": [
        "typing",
        "dataclasses",
        "enum",
        "logging",
        "json"
    ],

    "workflow_features": {
        "pre_built_templates": 12,
        "template_categories": 6,
        "execution_patterns": 4,
        "variable_substitution": True,
        "dependency_management": True,
        "time_estimation": True,
        "complexity_grading": True,
        "custom_template_support": True,
        "template_export_import": True,
        "template_validation": True
    },

    "usage_examples": {
        "get_fullstack_template": "template = get_template_manager().get_template('fullstack_development')",
        "list_dev_templates": "templates = get_template_manager().list_templates(TemplateCategory.DEVELOPMENT)",
        "search_api_templates": "templates = get_template_manager().search_templates('api')",
        "export_template": "json_str = get_template_manager().export_template('api_development', 'json')"
    }
}