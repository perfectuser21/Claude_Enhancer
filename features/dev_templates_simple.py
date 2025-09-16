#!/usr/bin/env python3
"""
Perfect21 简化开发模板系统
预定义常见开发场景的多Agent协作模板
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class SimpleTemplate:
    """简化开发模板"""
    name: str
    description: str
    category: str
    complexity: int
    agents: List[str]
    execution_mode: str  # "串行", "并行", "协调者"

class SimpleDevTemplates:
    """简化开发模板库"""

    @staticmethod
    def get_all_templates() -> Dict[str, SimpleTemplate]:
        """获取所有开发模板"""
        return {
            "api_development": SimpleTemplate(
                name="API开发",
                description="REST API完整开发流程",
                category="后端开发",
                complexity=6,
                agents=["@orchestrator", "@api-designer", "@python-pro", "@test-engineer", "@security-auditor"],
                execution_mode="协调者"
            ),

            "frontend_feature": SimpleTemplate(
                name="前端功能开发",
                description="React/Vue前端功能开发",
                category="前端开发",
                complexity=5,
                agents=["@react-pro", "@typescript-pro", "@test-engineer", "@accessibility-auditor"],
                execution_mode="并行"
            ),

            "bug_fix": SimpleTemplate(
                name="Bug修复",
                description="系统化问题修复流程",
                category="问题修复",
                complexity=4,
                agents=["@error-detective", "@code-reviewer", "@python-pro", "@test-engineer"],
                execution_mode="串行"
            ),

            "microservice": SimpleTemplate(
                name="微服务开发",
                description="完整微服务开发部署",
                category="系统架构",
                complexity=8,
                agents=["@orchestrator", "@backend-architect", "@golang-pro", "@kubernetes-expert", "@monitoring-specialist"],
                execution_mode="协调者"
            ),

            "performance_optimization": SimpleTemplate(
                name="性能优化",
                description="系统性能优化",
                category="性能优化",
                complexity=7,
                agents=["@performance-engineer", "@database-specialist", "@backend-architect"],
                execution_mode="并行"
            ),

            "security_audit": SimpleTemplate(
                name="安全审计",
                description="全面安全检查和加固",
                category="安全",
                complexity=6,
                agents=["@security-auditor", "@code-reviewer", "@devops-engineer"],
                execution_mode="串行"
            ),

            "data_pipeline": SimpleTemplate(
                name="数据工程",
                description="数据管道和ETL开发",
                category="数据工程",
                complexity=7,
                agents=["@data-engineer", "@database-specialist", "@performance-engineer", "@monitoring-specialist"],
                execution_mode="并行"
            ),

            "ml_development": SimpleTemplate(
                name="机器学习开发",
                description="端到端ML项目开发",
                category="AI/ML",
                complexity=8,
                agents=["@orchestrator", "@data-scientist", "@ai-engineer", "@data-engineer"],
                execution_mode="协调者"
            ),

            "mobile_app": SimpleTemplate(
                name="移动应用开发",
                description="跨平台移动应用开发",
                category="移动开发",
                complexity=7,
                agents=["@mobile-developer", "@react-pro", "@test-engineer", "@ux-designer"],
                execution_mode="并行"
            ),

            "devops_setup": SimpleTemplate(
                name="DevOps设置",
                description="CI/CD和基础设施配置",
                category="DevOps",
                complexity=6,
                agents=["@devops-engineer", "@kubernetes-expert", "@monitoring-specialist", "@security-auditor"],
                execution_mode="串行"
            )
        }

    @staticmethod
    def get_template(name: str) -> Optional[SimpleTemplate]:
        """获取指定模板"""
        templates = SimpleDevTemplates.get_all_templates()
        return templates.get(name)

    @staticmethod
    def list_by_category() -> Dict[str, List[str]]:
        """按类别列出模板"""
        templates = SimpleDevTemplates.get_all_templates()
        categories = {}

        for name, template in templates.items():
            category = template.category
            if category not in categories:
                categories[category] = []
            categories[category].append(name)

        return categories

    @staticmethod
    def recommend(description: str) -> List[str]:
        """推荐模板"""
        description_lower = description.lower()

        keywords = {
            "api_development": ["api", "接口", "rest", "后端"],
            "frontend_feature": ["前端", "react", "vue", "组件", "ui"],
            "bug_fix": ["bug", "修复", "问题", "错误"],
            "microservice": ["微服务", "service", "架构"],
            "performance_optimization": ["性能", "优化", "慢", "瓶颈"],
            "security_audit": ["安全", "security", "审计"],
            "data_pipeline": ["数据", "etl", "管道"],
            "ml_development": ["机器学习", "ai", "模型"],
            "mobile_app": ["移动", "app", "手机"],
            "devops_setup": ["部署", "ci", "cd", "devops"]
        }

        recommendations = []
        for template_name, template_keywords in keywords.items():
            if any(keyword in description_lower for keyword in template_keywords):
                recommendations.append(template_name)

        return recommendations[:3]

# 为了兼容性，设置别名
DevTemplates = SimpleDevTemplates

if __name__ == "__main__":
    templates = SimpleDevTemplates()

    print("🚀 Perfect21 简化开发模板库")
    print("=" * 50)

    categories = templates.list_by_category()
    for category, template_names in categories.items():
        print(f"\n📁 {category}:")
        for name in template_names:
            template = templates.get_template(name)
            print(f"  • {template.name} (复杂度: {template.complexity}/10, {template.execution_mode})")
            print(f"    {template.description}")
            print(f"    Agent: {', '.join(template.agents)}")
            print()