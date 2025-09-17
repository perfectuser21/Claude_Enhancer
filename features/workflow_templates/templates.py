#!/usr/bin/env python3
"""
Perfect21 工作流模板系统
提供预定义的多Agent工作流模板
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("WorkflowTemplates")

class TemplateCategory(Enum):
    """模板分类"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    ANALYSIS = "analysis"
    REVIEW = "review"
    RESEARCH = "research"

class ExecutionPattern(Enum):
    """执行模式"""
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    HYBRID = "hybrid"
    CONDITIONAL = "conditional"

@dataclass
class AgentStep:
    """Agent执行步骤"""
    agent: str
    task: str
    prompt_template: str
    dependencies: List[str] = None
    timeout: int = 300
    critical: bool = False

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

@dataclass
class WorkflowTemplate:
    """工作流模板"""
    name: str
    description: str
    category: TemplateCategory
    pattern: ExecutionPattern
    steps: List[AgentStep]
    variables: Dict[str, Any] = None
    estimated_time: int = 0
    complexity: str = "medium"

    def __post_init__(self):
        if self.variables is None:
            self.variables = {}

class WorkflowTemplateManager:
    """工作流模板管理器"""

    def __init__(self):
        self.templates: Dict[str, WorkflowTemplate] = {}
        self._load_builtin_templates()
        logger.info("工作流模板管理器初始化完成")

    def _load_builtin_templates(self):
        """加载内置模板"""
        templates = [
            # 全栈开发模板
            self._create_fullstack_template(),
            self._create_api_development_template(),
            self._create_frontend_template(),

            # 测试模板
            self._create_comprehensive_testing_template(),
            self._create_security_audit_template(),

            # 部署模板
            self._create_deployment_pipeline_template(),
            self._create_container_deployment_template(),

            # 代码审查模板
            self._create_code_review_template(),
            self._create_performance_review_template(),

            # 分析模板
            self._create_architecture_analysis_template(),
            self._create_codebase_analysis_template(),

            # 研究模板
            self._create_technology_research_template(),
        ]

        for template in templates:
            self.templates[template.name] = template

        logger.info(f"加载了 {len(templates)} 个内置模板")

    def _create_fullstack_template(self) -> WorkflowTemplate:
        """创建全栈开发模板"""
        return WorkflowTemplate(
            name="fullstack_development",
            description="完整的全栈应用开发工作流，包括后端、前端、测试和部署",
            category=TemplateCategory.DEVELOPMENT,
            pattern=ExecutionPattern.HYBRID,
            steps=[
                # 阶段1：并行设计
                AgentStep(
                    agent="product-strategist",
                    task="需求分析和功能规划",
                    prompt_template="""
分析项目需求：{project_description}

请提供：
1. 功能模块分解
2. 用户故事定义
3. 技术栈建议
4. 开发里程碑规划

输出格式：JSON
""",
                    critical=True
                ),
                AgentStep(
                    agent="ux-designer",
                    task="用户界面设计",
                    prompt_template="""
基于项目需求设计用户界面：{project_description}

请提供：
1. 用户流程图
2. 页面线框图设计
3. 组件库规划
4. 响应式设计方案

输出格式：设计文档 + 代码示例
""",
                    dependencies=["product-strategist"]
                ),

                # 阶段2：并行开发
                AgentStep(
                    agent="backend-architect",
                    task="后端架构和API设计",
                    prompt_template="""
设计后端架构：{project_description}

技术需求：{tech_stack}

请实现：
1. API端点设计
2. 数据库模型设计
3. 身份验证系统
4. 业务逻辑实现

使用最佳实践和安全标准。
""",
                    dependencies=["product-strategist"],
                    critical=True
                ),
                AgentStep(
                    agent="frontend-specialist",
                    task="前端应用开发",
                    prompt_template="""
开发前端应用：{project_description}

设计规范：参考UX设计师的输出
API规范：参考后端架构师的API设计

请实现：
1. 组件开发
2. 路由配置
3. 状态管理
4. API集成

使用现代前端最佳实践。
""",
                    dependencies=["ux-designer", "backend-architect"]
                ),

                # 阶段3：质量保证
                AgentStep(
                    agent="test-engineer",
                    task="全面测试实施",
                    prompt_template="""
为全栈应用创建测试套件：

后端测试：
- API端点测试
- 数据库集成测试
- 业务逻辑单元测试

前端测试：
- 组件测试
- 端到端测试
- 用户交互测试

请提供完整的测试用例和自动化脚本。
""",
                    dependencies=["backend-architect", "frontend-specialist"],
                    critical=True
                ),
                AgentStep(
                    agent="security-auditor",
                    task="安全审计",
                    prompt_template="""
对全栈应用进行安全审计：

检查范围：
1. 身份验证和授权
2. 数据输入验证
3. SQL注入和XSS防护
4. API安全性
5. 数据加密

提供详细的安全报告和修复建议。
""",
                    dependencies=["backend-architect", "frontend-specialist"]
                ),

                # 阶段4：部署
                AgentStep(
                    agent="devops-engineer",
                    task="部署和运维配置",
                    prompt_template="""
设置全栈应用的部署管道：

部署需求：{deployment_env}

请配置：
1. CI/CD管道
2. 容器化配置
3. 环境变量管理
4. 监控和日志
5. 备份策略

提供生产就绪的部署方案。
""",
                    dependencies=["test-engineer", "security-auditor"]
                ),
            ],
            variables={
                "project_description": "项目描述",
                "tech_stack": "技术栈选择",
                "deployment_env": "部署环境"
            },
            estimated_time=480,  # 8小时
            complexity="high"
        )

    def _create_api_development_template(self) -> WorkflowTemplate:
        """创建API开发模板"""
        return WorkflowTemplate(
            name="api_development",
            description="RESTful API开发工作流，包括设计、实现、测试和文档",
            category=TemplateCategory.DEVELOPMENT,
            pattern=ExecutionPattern.SEQUENTIAL,
            steps=[
                AgentStep(
                    agent="api-designer",
                    task="API规范设计",
                    prompt_template="""
设计RESTful API：{api_description}

请提供：
1. OpenAPI规范文档
2. 端点设计和路由
3. 请求/响应模型
4. 错误处理规范
5. 版本控制策略

遵循REST最佳实践。
""",
                    critical=True
                ),
                AgentStep(
                    agent="backend-architect",
                    task="API实现",
                    prompt_template="""
实现API服务：{api_description}

基于API设计规范，请实现：
1. 路由处理器
2. 数据模型和验证
3. 业务逻辑层
4. 数据库集成
5. 中间件配置

使用 {framework} 框架。
""",
                    dependencies=["api-designer"],
                    critical=True
                ),
                AgentStep(
                    agent="test-engineer",
                    task="API测试",
                    prompt_template="""
为API创建完整测试套件：

测试范围：
1. 单元测试（业务逻辑）
2. 集成测试（数据库）
3. API端点测试
4. 性能测试
5. 负载测试

提供自动化测试脚本和持续集成配置。
""",
                    dependencies=["backend-architect"],
                    critical=True
                ),
                AgentStep(
                    agent="technical-writer",
                    task="API文档编写",
                    prompt_template="""
编写API文档：

内容包括：
1. API概述和使用指南
2. 身份验证说明
3. 端点详细文档
4. 代码示例（多语言）
5. 错误代码说明
6. 更新日志

创建开发者友好的文档。
""",
                    dependencies=["api-designer", "backend-architect"]
                ),
            ],
            variables={
                "api_description": "API功能描述",
                "framework": "后端框架"
            },
            estimated_time=240,  # 4小时
            complexity="medium"
        )

    def _create_frontend_template(self) -> WorkflowTemplate:
        """创建前端开发模板"""
        return WorkflowTemplate(
            name="frontend_development",
            description="现代前端应用开发工作流",
            category=TemplateCategory.DEVELOPMENT,
            pattern=ExecutionPattern.SEQUENTIAL,
            steps=[
                AgentStep(
                    agent="ux-designer",
                    task="用户体验设计",
                    prompt_template="""
设计前端应用UX：{app_description}

请提供：
1. 用户流程图
2. 线框图设计
3. 交互原型
4. 设计系统规范
5. 响应式布局方案
""",
                    critical=True
                ),
                AgentStep(
                    agent="frontend-specialist",
                    task="前端应用开发",
                    prompt_template="""
开发前端应用：{app_description}

基于UX设计，使用 {frontend_framework} 实现：
1. 组件库开发
2. 路由系统配置
3. 状态管理实现
4. API数据获取
5. 样式和动画
6. 性能优化

遵循现代前端最佳实践。
""",
                    dependencies=["ux-designer"],
                    critical=True
                ),
                AgentStep(
                    agent="e2e-test-specialist",
                    task="端到端测试",
                    prompt_template="""
为前端应用创建E2E测试：

测试范围：
1. 用户流程测试
2. 跨浏览器兼容性
3. 响应式设计测试
4. 性能测试
5. 可访问性测试

使用现代E2E测试工具。
""",
                    dependencies=["frontend-specialist"]
                ),
            ],
            variables={
                "app_description": "应用描述",
                "frontend_framework": "前端框架"
            },
            estimated_time=180,  # 3小时
            complexity="medium"
        )

    def _create_comprehensive_testing_template(self) -> WorkflowTemplate:
        """创建综合测试模板"""
        return WorkflowTemplate(
            name="comprehensive_testing",
            description="全面的代码质量和测试工作流",
            category=TemplateCategory.TESTING,
            pattern=ExecutionPattern.PARALLEL,
            steps=[
                AgentStep(
                    agent="test-engineer",
                    task="测试策略制定",
                    prompt_template="""
为项目制定测试策略：{project_description}

包含：
1. 测试金字塔规划
2. 单元测试策略
3. 集成测试方案
4. 系统测试计划
5. 测试数据管理
6. 测试环境配置
""",
                    critical=True
                ),
                AgentStep(
                    agent="performance-tester",
                    task="性能测试",
                    prompt_template="""
执行性能测试：{project_description}

测试内容：
1. 负载测试
2. 压力测试
3. 容量测试
4. 稳定性测试
5. 性能瓶颈分析
6. 优化建议

提供详细的性能报告。
""",
                    dependencies=["test-engineer"]
                ),
                AgentStep(
                    agent="security-auditor",
                    task="安全测试",
                    prompt_template="""
执行安全测试：{project_description}

测试范围：
1. 漏洞扫描
2. 渗透测试
3. 代码安全审计
4. 依赖安全检查
5. 配置安全评估

提供安全报告和修复建议。
""",
                    dependencies=["test-engineer"]
                ),
                AgentStep(
                    agent="accessibility-auditor",
                    task="可访问性测试",
                    prompt_template="""
执行可访问性审计：{project_description}

检查项目：
1. WCAG指南合规性
2. 键盘导航
3. 屏幕阅读器支持
4. 颜色对比度
5. 语义化HTML

提供可访问性改进建议。
""",
                    dependencies=["test-engineer"]
                ),
            ],
            variables={
                "project_description": "项目描述"
            },
            estimated_time=360,  # 6小时
            complexity="high"
        )

    def _create_security_audit_template(self) -> WorkflowTemplate:
        """创建安全审计模板"""
        return WorkflowTemplate(
            name="security_audit",
            description="全面的安全审计和加固工作流",
            category=TemplateCategory.REVIEW,
            pattern=ExecutionPattern.SEQUENTIAL,
            steps=[
                AgentStep(
                    agent="security-auditor",
                    task="安全评估",
                    prompt_template="""
执行安全评估：{target_description}

评估范围：
1. 代码安全审计
2. 架构安全分析
3. 依赖安全检查
4. 配置安全评估
5. 数据保护合规性

提供详细的安全评估报告。
""",
                    critical=True
                ),
                AgentStep(
                    agent="backend-architect",
                    task="安全加固实施",
                    prompt_template="""
基于安全评估报告实施加固措施：

加固内容：
1. 修复发现的安全漏洞
2. 加强身份验证和授权
3. 实现安全日志记录
4. 配置安全头部
5. 数据加密实施

确保所有修复都经过测试验证。
""",
                    dependencies=["security-auditor"],
                    critical=True
                ),
                AgentStep(
                    agent="test-engineer",
                    task="安全测试验证",
                    prompt_template="""
验证安全加固效果：

验证内容：
1. 漏洞修复验证
2. 安全功能测试
3. 回归测试执行
4. 渗透测试复查
5. 合规性验证

提供安全验证报告。
""",
                    dependencies=["backend-architect"],
                    critical=True
                ),
            ],
            variables={
                "target_description": "审计目标描述"
            },
            estimated_time=300,  # 5小时
            complexity="high"
        )

    def _create_deployment_pipeline_template(self) -> WorkflowTemplate:
        """创建部署管道模板"""
        return WorkflowTemplate(
            name="deployment_pipeline",
            description="CI/CD部署管道设置工作流",
            category=TemplateCategory.DEPLOYMENT,
            pattern=ExecutionPattern.SEQUENTIAL,
            steps=[
                AgentStep(
                    agent="devops-engineer",
                    task="CI/CD管道设计",
                    prompt_template="""
设计部署管道：{project_description}

设计内容：
1. 源码管理策略
2. 构建流程定义
3. 测试自动化集成
4. 部署策略规划
5. 环境管理方案
6. 回滚机制设计

目标平台：{target_platform}
""",
                    critical=True
                ),
                AgentStep(
                    agent="cloud-architect",
                    task="云基础设施配置",
                    prompt_template="""
配置云基础设施：{project_description}

配置内容：
1. 计算资源规划
2. 网络安全配置
3. 存储方案设计
4. 负载均衡配置
5. 监控和告警设置
6. 成本优化建议

云平台：{cloud_provider}
""",
                    dependencies=["devops-engineer"]
                ),
                AgentStep(
                    agent="monitoring-specialist",
                    task="监控系统配置",
                    prompt_template="""
配置监控系统：{project_description}

监控范围：
1. 应用性能监控
2. 基础设施监控
3. 日志聚合分析
4. 告警规则设置
5. 仪表板创建
6. SLA定义

提供完整的监控方案。
""",
                    dependencies=["cloud-architect"]
                ),
            ],
            variables={
                "project_description": "项目描述",
                "target_platform": "目标平台",
                "cloud_provider": "云服务提供商"
            },
            estimated_time=240,  # 4小时
            complexity="medium"
        )

    def _create_container_deployment_template(self) -> WorkflowTemplate:
        """创建容器部署模板"""
        return WorkflowTemplate(
            name="container_deployment",
            description="Kubernetes容器化部署工作流",
            category=TemplateCategory.DEPLOYMENT,
            pattern=ExecutionPattern.SEQUENTIAL,
            steps=[
                AgentStep(
                    agent="devops-engineer",
                    task="容器化配置",
                    prompt_template="""
容器化应用：{app_description}

配置内容：
1. Dockerfile编写
2. 镜像优化
3. 多阶段构建
4. 安全最佳实践
5. 健康检查配置

确保镜像精简和安全。
""",
                    critical=True
                ),
                AgentStep(
                    agent="kubernetes-expert",
                    task="Kubernetes部署配置",
                    prompt_template="""
配置Kubernetes部署：{app_description}

配置文件：
1. Deployment配置
2. Service配置
3. Ingress规则
4. ConfigMap和Secret
5. 资源限制设置
6. 健康检查配置

遵循K8s最佳实践。
""",
                    dependencies=["devops-engineer"],
                    critical=True
                ),
                AgentStep(
                    agent="monitoring-specialist",
                    task="容器监控配置",
                    prompt_template="""
配置容器监控：{app_description}

监控方案：
1. Prometheus配置
2. Grafana仪表板
3. 容器日志收集
4. 告警规则设置
5. 服务发现配置

提供完整的监控解决方案。
""",
                    dependencies=["kubernetes-expert"]
                ),
            ],
            variables={
                "app_description": "应用描述"
            },
            estimated_time=180,  # 3小时
            complexity="medium"
        )

    def _create_code_review_template(self) -> WorkflowTemplate:
        """创建代码审查模板"""
        return WorkflowTemplate(
            name="code_review",
            description="全面的代码审查工作流",
            category=TemplateCategory.REVIEW,
            pattern=ExecutionPattern.PARALLEL,
            steps=[
                AgentStep(
                    agent="code-reviewer",
                    task="代码质量审查",
                    prompt_template="""
执行代码审查：{code_description}

审查重点：
1. 代码结构和组织
2. 设计模式应用
3. 命名规范
4. 代码可读性
5. 重复代码检查
6. 最佳实践应用

提供详细的改进建议。
""",
                    critical=True
                ),
                AgentStep(
                    agent="security-auditor",
                    task="安全代码审查",
                    prompt_template="""
执行安全代码审查：{code_description}

安全检查：
1. 输入验证
2. SQL注入防护
3. XSS防护
4. 身份验证缺陷
5. 敏感数据处理
6. 加密使用

提供安全修复建议。
""",
                    critical=True
                ),
                AgentStep(
                    agent="performance-engineer",
                    task="性能代码审查",
                    prompt_template="""
执行性能代码审查：{code_description}

性能检查：
1. 算法复杂度分析
2. 内存使用优化
3. 数据库查询优化
4. 缓存策略检查
5. 并发处理审查
6. 资源释放检查

提供性能优化建议。
""",
                ),
            ],
            variables={
                "code_description": "代码描述"
            },
            estimated_time=120,  # 2小时
            complexity="medium"
        )

    def _create_performance_review_template(self) -> WorkflowTemplate:
        """创建性能审查模板"""
        return WorkflowTemplate(
            name="performance_review",
            description="应用性能分析和优化工作流",
            category=TemplateCategory.REVIEW,
            pattern=ExecutionPattern.SEQUENTIAL,
            steps=[
                AgentStep(
                    agent="performance-engineer",
                    task="性能分析",
                    prompt_template="""
执行性能分析：{app_description}

分析内容：
1. 应用性能基准测试
2. 瓶颈识别和分析
3. 资源使用分析
4. 响应时间分析
5. 吞吐量测试
6. 可扩展性评估

提供详细的性能报告。
""",
                    critical=True
                ),
                AgentStep(
                    agent="backend-architect",
                    task="性能优化实施",
                    prompt_template="""
基于性能分析实施优化：

优化措施：
1. 代码层面优化
2. 数据库查询优化
3. 缓存策略实现
4. 算法优化
5. 资源使用优化
6. 并发处理改进

确保优化后进行测试验证。
""",
                    dependencies=["performance-engineer"],
                    critical=True
                ),
                AgentStep(
                    agent="performance-tester",
                    task="优化效果验证",
                    prompt_template="""
验证性能优化效果：

验证内容：
1. 优化前后对比测试
2. 基准性能验证
3. 回归测试执行
4. 负载测试验证
5. 稳定性测试
6. 用户体验影响评估

提供优化效果报告。
""",
                    dependencies=["backend-architect"]
                ),
            ],
            variables={
                "app_description": "应用描述"
            },
            estimated_time=240,  # 4小时
            complexity="medium"
        )

    def _create_architecture_analysis_template(self) -> WorkflowTemplate:
        """创建架构分析模板"""
        return WorkflowTemplate(
            name="architecture_analysis",
            description="软件架构分析和改进建议工作流",
            category=TemplateCategory.ANALYSIS,
            pattern=ExecutionPattern.SEQUENTIAL,
            steps=[
                AgentStep(
                    agent="backend-architect",
                    task="架构评估",
                    prompt_template="""
评估软件架构：{system_description}

评估维度：
1. 架构模式分析
2. 模块化程度评估
3. 可维护性分析
4. 可扩展性评估
5. 性能架构分析
6. 技术债务识别

提供详细的架构评估报告。
""",
                    critical=True
                ),
                AgentStep(
                    agent="cloud-architect",
                    task="云架构优化建议",
                    prompt_template="""
提供云架构优化建议：{system_description}

建议内容：
1. 微服务架构建议
2. 容器化策略
3. 服务网格应用
4. 云原生最佳实践
5. 成本优化建议
6. 可靠性改进方案

基于当前架构评估提供改进路径。
""",
                    dependencies=["backend-architect"]
                ),
                AgentStep(
                    agent="technical-writer",
                    task="架构文档编写",
                    prompt_template="""
编写架构文档：

文档内容：
1. 当前架构概述
2. 架构决策记录
3. 组件交互图
4. 部署架构图
5. 改进建议总结
6. 迁移路线图

创建清晰易懂的架构文档。
""",
                    dependencies=["backend-architect", "cloud-architect"]
                ),
            ],
            variables={
                "system_description": "系统描述"
            },
            estimated_time=200,  # 3.3小时
            complexity="high"
        )

    def _create_codebase_analysis_template(self) -> WorkflowTemplate:
        """创建代码库分析模板"""
        return WorkflowTemplate(
            name="codebase_analysis",
            description="代码库全面分析工作流",
            category=TemplateCategory.ANALYSIS,
            pattern=ExecutionPattern.PARALLEL,
            steps=[
                AgentStep(
                    agent="code-reviewer",
                    task="代码质量分析",
                    prompt_template="""
分析代码库质量：{codebase_description}

分析内容：
1. 代码复杂度分析
2. 代码重复度检查
3. 代码覆盖率分析
4. 代码规范检查
5. 技术债务评估
6. 维护性指标分析

提供代码质量报告。
""",
                    critical=True
                ),
                AgentStep(
                    agent="security-auditor",
                    task="安全漏洞扫描",
                    prompt_template="""
扫描代码库安全漏洞：{codebase_description}

扫描内容：
1. 静态安全分析
2. 依赖漏洞检查
3. 敏感信息泄露检查
4. 安全配置检查
5. 加密实践审计
6. 权限控制审查

提供安全分析报告。
""",
                    critical=True
                ),
                AgentStep(
                    agent="performance-engineer",
                    task="性能问题分析",
                    prompt_template="""
分析代码库性能问题：{codebase_description}

分析范围：
1. 性能热点识别
2. 内存使用分析
3. 算法复杂度检查
4. 数据库查询分析
5. 资源泄露检查
6. 并发问题分析

提供性能分析报告。
""",
                ),
                AgentStep(
                    agent="technical-writer",
                    task="分析报告整合",
                    prompt_template="""
整合代码库分析结果：

整合内容：
1. 综合质量评估
2. 关键问题汇总
3. 优先级排序
4. 改进建议
5. 行动计划
6. 风险评估

创建执行友好的分析报告。
""",
                    dependencies=["code-reviewer", "security-auditor", "performance-engineer"]
                ),
            ],
            variables={
                "codebase_description": "代码库描述"
            },
            estimated_time=180,  # 3小时
            complexity="medium"
        )

    def _create_technology_research_template(self) -> WorkflowTemplate:
        """创建技术研究模板"""
        return WorkflowTemplate(
            name="technology_research",
            description="新技术调研和评估工作流",
            category=TemplateCategory.RESEARCH,
            pattern=ExecutionPattern.PARALLEL,
            steps=[
                AgentStep(
                    agent="backend-architect",
                    task="技术可行性分析",
                    prompt_template="""
分析技术可行性：{technology_description}

研究内容：
1. 技术成熟度评估
2. 性能特征分析
3. 集成复杂度评估
4. 学习曲线分析
5. 维护成本评估
6. 社区支持状况

提供技术可行性报告。
""",
                    critical=True
                ),
                AgentStep(
                    agent="project-manager",
                    task="业务影响评估",
                    prompt_template="""
评估业务影响：{technology_description}

评估内容：
1. 业务价值分析
2. ROI预估
3. 风险评估
4. 时间计划评估
5. 资源需求分析
6. 竞争优势分析

提供业务影响评估报告。
""",
                    critical=True
                ),
                AgentStep(
                    agent="security-auditor",
                    task="安全风险评估",
                    prompt_template="""
评估安全风险：{technology_description}

风险评估：
1. 安全漏洞历史
2. 安全配置复杂度
3. 合规性影响
4. 数据保护能力
5. 访问控制机制
6. 安全更新机制

提供安全风险评估报告。
""",
                ),
                AgentStep(
                    agent="technical-writer",
                    task="技术调研报告",
                    prompt_template="""
编写技术调研报告：

报告结构：
1. 技术概述
2. 可行性分析总结
3. 业务价值评估
4. 风险分析
5. 实施建议
6. 决策建议

基于各专家的分析结果编写综合报告。
""",
                    dependencies=["backend-architect", "project-manager", "security-auditor"]
                ),
            ],
            variables={
                "technology_description": "技术描述"
            },
            estimated_time=240,  # 4小时
            complexity="medium"
        )

    def get_template(self, name: str) -> Optional[WorkflowTemplate]:
        """获取指定名称的模板"""
        return self.templates.get(name)

    def list_templates(self, category: TemplateCategory = None) -> List[WorkflowTemplate]:
        """列出所有模板或指定分类的模板"""
        if category is None:
            return list(self.templates.values())

        return [template for template in self.templates.values()
                if template.category == category]

    def get_templates_by_pattern(self, pattern: ExecutionPattern) -> List[WorkflowTemplate]:
        """根据执行模式获取模板"""
        return [template for template in self.templates.values()
                if template.pattern == pattern]

    def search_templates(self, keyword: str) -> List[WorkflowTemplate]:
        """搜索模板"""
        keyword = keyword.lower()
        results = []

        for template in self.templates.values():
            if (keyword in template.name.lower() or
                keyword in template.description.lower() or
                any(keyword in step.task.lower() for step in template.steps)):
                results.append(template)

        return results

    def create_custom_template(self, template: WorkflowTemplate) -> bool:
        """创建自定义模板"""
        try:
            # 验证模板
            if self._validate_template(template):
                self.templates[template.name] = template
                logger.info(f"创建自定义模板: {template.name}")
                return True
            else:
                logger.error(f"模板验证失败: {template.name}")
                return False
        except Exception as e:
            logger.error(f"创建模板失败: {e}")
            return False

    def _validate_template(self, template: WorkflowTemplate) -> bool:
        """验证模板的有效性"""
        # 检查必需字段
        if not template.name or not template.description:
            return False

        if not template.steps:
            return False

        # 检查步骤依赖关系
        step_names = {step.agent for step in template.steps}
        for step in template.steps:
            for dep in step.dependencies:
                if dep not in step_names:
                    logger.error(f"依赖步骤不存在: {dep}")
                    return False

        return True

    def export_template(self, name: str, format: str = "json") -> Optional[str]:
        """导出模板为指定格式"""
        template = self.get_template(name)
        if not template:
            return None

        try:
            if format.lower() == "json":
                import json
                return json.dumps(self._template_to_dict(template),
                                indent=2, ensure_ascii=False)
            elif format.lower() == "yaml":
                import yaml
                return yaml.dump(self._template_to_dict(template),
                               default_flow_style=False, allow_unicode=True)
            else:
                logger.error(f"不支持的导出格式: {format}")
                return None
        except Exception as e:
            logger.error(f"导出模板失败: {e}")
            return None

    def _template_to_dict(self, template: WorkflowTemplate) -> Dict[str, Any]:
        """将模板转换为字典"""
        return {
            "name": template.name,
            "description": template.description,
            "category": template.category.value,
            "pattern": template.pattern.value,
            "estimated_time": template.estimated_time,
            "complexity": template.complexity,
            "variables": template.variables,
            "steps": [
                {
                    "agent": step.agent,
                    "task": step.task,
                    "prompt_template": step.prompt_template,
                    "dependencies": step.dependencies,
                    "timeout": step.timeout,
                    "critical": step.critical
                }
                for step in template.steps
            ]
        }

    def get_statistics(self) -> Dict[str, Any]:
        """获取模板统计信息"""
        stats = {
            "total_templates": len(self.templates),
            "by_category": {},
            "by_pattern": {},
            "by_complexity": {},
            "average_steps": 0,
            "average_time": 0
        }

        if not self.templates:
            return stats

        # 统计分类
        for template in self.templates.values():
            category = template.category.value
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1

            pattern = template.pattern.value
            stats["by_pattern"][pattern] = stats["by_pattern"].get(pattern, 0) + 1

            complexity = template.complexity
            stats["by_complexity"][complexity] = stats["by_complexity"].get(complexity, 0) + 1

        # 计算平均值
        total_steps = sum(len(t.steps) for t in self.templates.values())
        total_time = sum(t.estimated_time for t in self.templates.values())

        stats["average_steps"] = total_steps / len(self.templates)
        stats["average_time"] = total_time / len(self.templates)

        return stats

# 全局模板管理器实例
_template_manager = None

def get_template_manager() -> WorkflowTemplateManager:
    """获取全局模板管理器实例"""
    global _template_manager
    if _template_manager is None:
        _template_manager = WorkflowTemplateManager()
    return _template_manager