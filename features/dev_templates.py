#!/usr/bin/env python3
"""
Perfect21 开发任务模板系统
预定义常见开发场景的多Agent协作模板
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json

@dataclass
class AgentStep:
    """Agent执行步骤"""
    agent: str
    action: str
    description: str
    parallel_group: Optional[int] = None  # 并行组，相同组号的步骤并行执行
    dependencies: List[str] = None  # 依赖的步骤
    context_inputs: List[str] = None  # 需要的上下文输入

@dataclass
class DevTemplate:
    """开发模板"""
    name: str
    description: str
    category: str
    complexity: int  # 1-10
    estimated_time: str  # 预估时间
    steps: List[AgentStep]
    required_context: List[str]  # 必需的上下文信息
    output_artifacts: List[str]  # 输出产物

class DevTemplates:
    """开发模板库"""

    @staticmethod
    def get_all_templates() -> Dict[str, DevTemplate]:
        """获取所有开发模板"""
        return {
            # ===== 功能开发模板 =====
            "rest_api_development": DevTemplate(
                name="REST API开发",
                description="从需求到部署的完整REST API开发流程",
                category="后端开发",
                complexity=6,
                estimated_time="2-4小时",
                steps=[
                    AgentStep("@requirements-analyst", "analyze", "分析API需求和用例"),
                    AgentStep("@api-designer", "design", "设计API接口规范", dependencies=["analyze"]),
                    AgentStep("@database-specialist", "schema", "设计数据库表结构", dependencies=["analyze"]),
                    AgentStep("@backend-architect", "architecture", "设计系统架构", dependencies=["design", "schema"]),
                    AgentStep("@python-pro", "implement", "实现API核心逻辑", parallel_group=1, dependencies=["architecture"]),
                    AgentStep("@test-engineer", "unit_tests", "编写单元测试", parallel_group=1, dependencies=["architecture"]),
                    AgentStep("@security-auditor", "security_review", "安全性审查", parallel_group=2, dependencies=["implement"]),
                    AgentStep("@code-reviewer", "code_review", "代码质量审查", parallel_group=2, dependencies=["implement"]),
                    AgentStep("@technical-writer", "documentation", "编写API文档", parallel_group=2, dependencies=["implement"]),
                    AgentStep("@devops-engineer", "deployment", "配置部署环境", dependencies=["security_review", "code_review"]),
                    AgentStep("@monitoring-specialist", "monitoring", "配置监控告警", dependencies=["deployment"])
                ],
                required_context=["业务需求", "技术栈", "目标环境"],
                output_artifacts=["API代码", "数据库脚本", "测试用例", "API文档", "部署配置"]
            ),

            "frontend_feature": DevTemplate(
                name="前端功能开发",
                description="React/Vue前端功能完整开发流程",
                category="前端开发",
                complexity=5,
                estimated_time="1-3小时",
                steps=[
                    AgentStep("@ux-designer", "design", "设计用户界面和交互", 1),
                    AgentStep("@requirements-analyst", "analyze", "分析功能需求", 1),
                    AgentStep("@frontend-specialist", "setup", "配置开发环境", 2, ["design", "analyze"]),
                    AgentStep("@react-pro", "component", "开发React组件", 3, ["setup"], parallel_group=1),
                    AgentStep("@typescript-pro", "types", "定义TypeScript类型", 3, ["setup"], parallel_group=1),
                    AgentStep("@test-engineer", "tests", "编写组件测试", 4, ["component"], parallel_group=2),
                    AgentStep("@accessibility-auditor", "a11y", "可访问性检查", 4, ["component"], parallel_group=2),
                    AgentStep("@code-reviewer", "review", "代码审查", 5, ["tests", "a11y"]),
                    AgentStep("@e2e-test-specialist", "e2e", "端到端测试", 6, ["review"])
                ],
                required_context=["设计稿", "API接口", "浏览器支持"],
                output_artifacts=["组件代码", "类型定义", "测试用例", "文档"]
            ),

            "microservice_development": DevTemplate(
                name="微服务开发",
                description="完整微服务的设计、开发、部署流程",
                category="系统架构",
                complexity=8,
                estimated_time="1-2天",
                steps=[
                    AgentStep("@business-analyst", "domain", "领域建模和边界定义", 1),
                    AgentStep("@backend-architect", "architecture", "微服务架构设计", 2, ["domain"]),
                    AgentStep("@api-designer", "contracts", "服务契约设计", 3, ["architecture"], parallel_group=1),
                    AgentStep("@database-specialist", "persistence", "数据持久化设计", 3, ["architecture"], parallel_group=1),
                    AgentStep("@golang-pro", "service", "Go微服务实现", 4, ["contracts", "persistence"]),
                    AgentStep("@test-engineer", "testing", "测试策略实施", 5, ["service"], parallel_group=1),
                    AgentStep("@security-auditor", "security", "安全性审计", 5, ["service"], parallel_group=1),
                    AgentStep("@kubernetes-expert", "containerization", "容器化配置", 6, ["testing"]),
                    AgentStep("@devops-engineer", "cicd", "CI/CD流水线", 7, ["containerization"], parallel_group=1),
                    AgentStep("@monitoring-specialist", "observability", "可观测性配置", 7, ["containerization"], parallel_group=1),
                    AgentStep("@orchestrator", "integration", "服务集成测试", 8, ["cicd", "observability"])
                ],
                required_context=["业务领域", "现有服务", "技术栈", "基础设施"],
                output_artifacts=["服务代码", "Docker镜像", "K8s配置", "API文档", "监控配置"]
            ),

            # ===== 问题修复模板 =====
            "bug_fix_workflow": DevTemplate(
                name="Bug修复流程",
                description="系统化的问题定位、修复、验证流程",
                category="问题修复",
                complexity=4,
                estimated_time="30分钟-2小时",
                steps=[
                    AgentStep("@error-detective", "investigate", "问题调查和根因分析", 1),
                    AgentStep("@code-reviewer", "locate", "定位问题代码", 2, ["investigate"]),
                    AgentStep("@python-pro", "fix", "实施代码修复", 3, ["locate"]),
                    AgentStep("@test-engineer", "verify", "编写回归测试", 4, ["fix"], parallel_group=1),
                    AgentStep("@security-auditor", "security_check", "安全影响评估", 4, ["fix"], parallel_group=1),
                    AgentStep("@performance-engineer", "performance_test", "性能影响测试", 5, ["verify", "security_check"])
                ],
                required_context=["错误报告", "复现步骤", "影响范围"],
                output_artifacts=["修复代码", "测试用例", "修复报告"]
            ),

            "performance_optimization": DevTemplate(
                name="性能优化",
                description="系统性能问题诊断和优化流程",
                category="性能优化",
                complexity=7,
                estimated_time="半天-1天",
                steps=[
                    AgentStep("@performance-engineer", "profiling", "性能分析和瓶颈识别", 1),
                    AgentStep("@database-specialist", "db_optimization", "数据库优化", 2, ["profiling"], parallel_group=1),
                    AgentStep("@backend-architect", "architecture_review", "架构优化评估", 2, ["profiling"], parallel_group=1),
                    AgentStep("@python-pro", "code_optimization", "代码级优化", 3, ["db_optimization"], parallel_group=1),
                    AgentStep("@devops-engineer", "infrastructure", "基础设施优化", 3, ["architecture_review"], parallel_group=1),
                    AgentStep("@performance-tester", "benchmark", "性能基准测试", 4, ["code_optimization", "infrastructure"]),
                    AgentStep("@monitoring-specialist", "metrics", "建立性能监控", 5, ["benchmark"])
                ],
                required_context=["性能指标", "系统架构", "负载特征"],
                output_artifacts=["优化代码", "配置调整", "性能报告", "监控配置"]
            ),

            # ===== 系统设计模板 =====
            "system_design": DevTemplate(
                name="系统架构设计",
                description="大型系统的完整架构设计流程",
                category="架构设计",
                complexity=9,
                estimated_time="2-5天",
                steps=[
                    AgentStep("@requirements-analyst", "requirements", "需求分析和非功能性需求", 1),
                    AgentStep("@business-analyst", "domain_modeling", "业务领域建模", 2, ["requirements"]),
                    AgentStep("@backend-architect", "high_level_design", "高层架构设计", 3, ["domain_modeling"]),
                    AgentStep("@database-specialist", "data_architecture", "数据架构设计", 4, ["high_level_design"], parallel_group=1),
                    AgentStep("@api-designer", "service_design", "服务和API设计", 4, ["high_level_design"], parallel_group=1),
                    AgentStep("@cloud-architect", "infrastructure", "基础设施架构", 4, ["high_level_design"], parallel_group=1),
                    AgentStep("@security-auditor", "security_architecture", "安全架构设计", 5, ["data_architecture", "service_design"]),
                    AgentStep("@performance-engineer", "capacity_planning", "容量规划", 6, ["infrastructure"], parallel_group=1),
                    AgentStep("@monitoring-specialist", "observability_design", "可观测性设计", 6, ["infrastructure"], parallel_group=1),
                    AgentStep("@orchestrator", "integration", "整体架构验证", 7, ["security_architecture", "capacity_planning", "observability_design"]),
                    AgentStep("@technical-writer", "documentation", "架构文档编写", 8, ["integration"])
                ],
                required_context=["业务需求", "技术约束", "质量要求", "预算限制"],
                output_artifacts=["架构图", "技术选型", "部署策略", "架构文档"]
            ),

            # ===== 数据和AI模板 =====
            "ml_pipeline": DevTemplate(
                name="机器学习流水线",
                description="端到端机器学习项目开发流程",
                category="AI/ML",
                complexity=8,
                estimated_time="1-3天",
                steps=[
                    AgentStep("@data-scientist", "problem_definition", "问题定义和指标设计", 1),
                    AgentStep("@data-engineer", "data_pipeline", "数据管道建设", 2, ["problem_definition"], parallel_group=1),
                    AgentStep("@ai-engineer", "feature_engineering", "特征工程", 2, ["problem_definition"], parallel_group=1),
                    AgentStep("@data-scientist", "model_development", "模型开发和训练", 3, ["data_pipeline", "feature_engineering"]),
                    AgentStep("@test-engineer", "model_testing", "模型测试和验证", 4, ["model_development"], parallel_group=1),
                    AgentStep("@performance-engineer", "optimization", "模型性能优化", 4, ["model_development"], parallel_group=1),
                    AgentStep("@ai-engineer", "deployment", "模型部署和服务", 5, ["model_testing", "optimization"]),
                    AgentStep("@monitoring-specialist", "monitoring", "模型监控系统", 6, ["deployment"])
                ],
                required_context=["业务问题", "数据源", "性能要求"],
                output_artifacts=["训练代码", "模型文件", "部署服务", "监控dashboard"]
            ),

            # ===== 移动开发模板 =====
            "mobile_app": DevTemplate(
                name="移动应用开发",
                description="跨平台移动应用开发流程",
                category="移动开发",
                complexity=7,
                estimated_time="1-2天",
                steps=[
                    AgentStep("@ux-designer", "mobile_design", "移动端UI/UX设计", 1),
                    AgentStep("@mobile-developer", "architecture", "移动应用架构设计", 2, ["mobile_design"]),
                    AgentStep("@react-pro", "cross_platform", "React Native开发", 3, ["architecture"], parallel_group=1),
                    AgentStep("@api-designer", "mobile_api", "移动端API适配", 3, ["architecture"], parallel_group=1),
                    AgentStep("@test-engineer", "mobile_testing", "移动端测试", 4, ["cross_platform"], parallel_group=1),
                    AgentStep("@performance-tester", "mobile_performance", "移动端性能测试", 4, ["cross_platform"], parallel_group=1),
                    AgentStep("@security-auditor", "mobile_security", "移动端安全审计", 5, ["mobile_testing"]),
                    AgentStep("@devops-engineer", "app_distribution", "应用分发配置", 6, ["mobile_security"])
                ],
                required_context=["目标平台", "设计规范", "性能要求"],
                output_artifacts=["应用代码", "测试用例", "部署包", "应用商店资源"]
            )
        }

    @staticmethod
    def get_template(name: str) -> Optional[DevTemplate]:
        """获取指定模板"""
        templates = DevTemplates.get_all_templates()
        return templates.get(name)

    @staticmethod
    def list_templates_by_category() -> Dict[str, List[str]]:
        """按类别列出模板"""
        templates = DevTemplates.get_all_templates()
        categories = {}

        for name, template in templates.items():
            category = template.category
            if category not in categories:
                categories[category] = []
            categories[category].append(name)

        return categories

    @staticmethod
    def recommend_template(description: str) -> List[str]:
        """根据描述推荐模板"""
        description_lower = description.lower()
        templates = DevTemplates.get_all_templates()

        recommendations = []

        # 关键词匹配
        template_keywords = {
            "rest_api_development": ["api", "接口", "rest", "后端"],
            "frontend_feature": ["前端", "react", "vue", "组件", "ui"],
            "microservice_development": ["微服务", "service", "架构"],
            "bug_fix_workflow": ["bug", "修复", "问题", "错误"],
            "performance_optimization": ["性能", "优化", "慢", "瓶颈"],
            "system_design": ["系统", "架构", "设计"],
            "ml_pipeline": ["机器学习", "ai", "模型", "算法"],
            "mobile_app": ["移动", "app", "手机", "ios", "android"]
        }

        for template_name, keywords in template_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                recommendations.append(template_name)

        return recommendations[:3]  # 返回前3个推荐

    @staticmethod
    def get_template_info(name: str) -> Dict[str, Any]:
        """获取模板详细信息"""
        template = DevTemplates.get_template(name)
        if not template:
            return {}

        return {
            "name": template.name,
            "description": template.description,
            "category": template.category,
            "complexity": template.complexity,
            "estimated_time": template.estimated_time,
            "steps_count": len(template.steps),
            "parallel_groups": len(set(step.parallel_group for step in template.steps if step.parallel_group)),
            "required_context": template.required_context,
            "output_artifacts": template.output_artifacts,
            "agents_involved": list(set(step.agent for step in template.steps))
        }

if __name__ == "__main__":
    # 测试模板系统
    templates = DevTemplates()

    print("🚀 Perfect21 开发模板库")
    print("=" * 50)

    # 按类别显示所有模板
    categories = templates.list_templates_by_category()
    for category, template_names in categories.items():
        print(f"\n📁 {category}:")
        for name in template_names:
            template = templates.get_template(name)
            print(f"  • {template.name} (复杂度: {template.complexity}/10, 时间: {template.estimated_time})")

    # 测试推荐系统
    print(f"\n🎯 推荐测试:")
    test_descriptions = [
        "实现用户登录API",
        "开发React前端页面",
        "修复支付系统bug",
        "设计微服务架构",
        "优化数据库性能"
    ]

    for desc in test_descriptions:
        recommendations = templates.recommend_template(desc)
        print(f"  '{desc}' → {recommendations}")

    # 显示模板详情
    print(f"\n📋 REST API开发模板详情:")
    info = templates.get_template_info("rest_api_development")
    print(json.dumps(info, indent=2, ensure_ascii=False))