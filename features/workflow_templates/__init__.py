"""
Perfect21 工作流模板系统
提供预定义的多Agent协作工作流模板
"""

from .templates import (
    WorkflowTemplateManager,
    WorkflowTemplate,
    AgentStep,
    TemplateCategory,
    ExecutionPattern,
    get_template_manager
)

from .capability import CAPABILITY

__all__ = [
    'WorkflowTemplateManager',
    'WorkflowTemplate',
    'AgentStep',
    'TemplateCategory',
    'ExecutionPattern',
    'get_template_manager',
    'CAPABILITY'
]

def create_template_manager() -> WorkflowTemplateManager:
    """
    创建工作流模板管理器实例

    Returns:
        WorkflowTemplateManager: 模板管理器实例
    """
    return WorkflowTemplateManager()

def list_available_templates(category: TemplateCategory = None) -> list:
    """
    列出可用的工作流模板

    Args:
        category: 可选的模板分类过滤

    Returns:
        list: 模板列表
    """
    manager = get_template_manager()
    return manager.list_templates(category)

def get_template_by_name(name: str) -> WorkflowTemplate:
    """
    根据名称获取工作流模板

    Args:
        name: 模板名称

    Returns:
        WorkflowTemplate: 工作流模板对象
    """
    manager = get_template_manager()
    return manager.get_template(name)

def search_templates_by_keyword(keyword: str) -> list:
    """
    根据关键词搜索模板

    Args:
        keyword: 搜索关键词

    Returns:
        list: 匹配的模板列表
    """
    manager = get_template_manager()
    return manager.search_templates(keyword)

def get_development_templates() -> list:
    """
    获取所有开发类模板

    Returns:
        list: 开发类模板列表
    """
    manager = get_template_manager()
    return manager.list_templates(TemplateCategory.DEVELOPMENT)

def get_testing_templates() -> list:
    """
    获取所有测试类模板

    Returns:
        list: 测试类模板列表
    """
    manager = get_template_manager()
    return manager.list_templates(TemplateCategory.TESTING)

def get_deployment_templates() -> list:
    """
    获取所有部署类模板

    Returns:
        list: 部署类模板列表
    """
    manager = get_template_manager()
    return manager.list_templates(TemplateCategory.DEPLOYMENT)

def get_parallel_templates() -> list:
    """
    获取并行执行模式的模板

    Returns:
        list: 并行执行模板列表
    """
    manager = get_template_manager()
    return manager.get_templates_by_pattern(ExecutionPattern.PARALLEL)

def get_sequential_templates() -> list:
    """
    获取顺序执行模式的模板

    Returns:
        list: 顺序执行模板列表
    """
    manager = get_template_manager()
    return manager.get_templates_by_pattern(ExecutionPattern.SEQUENTIAL)

def export_template_as_json(template_name: str) -> str:
    """
    导出模板为JSON格式

    Args:
        template_name: 模板名称

    Returns:
        str: JSON格式的模板字符串
    """
    manager = get_template_manager()
    return manager.export_template(template_name, "json")

def export_template_as_yaml(template_name: str) -> str:
    """
    导出模板为YAML格式

    Args:
        template_name: 模板名称

    Returns:
        str: YAML格式的模板字符串
    """
    manager = get_template_manager()
    return manager.export_template(template_name, "yaml")

def get_template_statistics() -> dict:
    """
    获取模板系统统计信息

    Returns:
        dict: 统计信息字典
    """
    manager = get_template_manager()
    return manager.get_statistics()

# 预设常用模板快捷访问函数
def get_fullstack_template() -> WorkflowTemplate:
    """获取全栈开发模板"""
    return get_template_by_name("fullstack_development")

def get_api_template() -> WorkflowTemplate:
    """获取API开发模板"""
    return get_template_by_name("api_development")

def get_security_audit_template() -> WorkflowTemplate:
    """获取安全审计模板"""
    return get_template_by_name("security_audit")

def get_code_review_template() -> WorkflowTemplate:
    """获取代码审查模板"""
    return get_template_by_name("code_review")

def get_deployment_pipeline_template() -> WorkflowTemplate:
    """获取部署管道模板"""
    return get_template_by_name("deployment_pipeline")

# 模板系统初始化函数
def initialize_template_system():
    """
    初始化工作流模板系统

    这个函数确保模板管理器被正确初始化并加载所有内置模板
    """
    manager = get_template_manager()
    stats = manager.get_statistics()

    print(f"Perfect21工作流模板系统已初始化:")
    print(f"- 总模板数: {stats['total_templates']}")
    print(f"- 分类统计: {stats['by_category']}")
    print(f"- 执行模式: {stats['by_pattern']}")
    print(f"- 平均步骤数: {stats['average_steps']:.1f}")
    print(f"- 平均预估时间: {stats['average_time']:.0f}分钟")

    return manager