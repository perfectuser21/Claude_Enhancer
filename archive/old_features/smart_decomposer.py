#!/usr/bin/env python3
"""
Perfect21 智能任务分解器
分析复杂任务并自动决定需要哪些agents进行并行协作
绕过orchestrator限制，在主Claude Code层面实现智能分解
"""

import logging
import re
import json
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("SmartDecomposer")

class TaskComplexity(Enum):
    """任务复杂度"""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    ENTERPRISE = "enterprise"

@dataclass
class AgentTask:
    """Agent任务定义"""
    agent_name: str
    task_description: str
    detailed_prompt: str
    priority: int = 1
    estimated_time: int = 60  # 分钟
    dependencies: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

@dataclass
class TaskAnalysis:
    """任务分析结果"""
    original_task: str
    complexity: TaskComplexity
    project_type: str
    required_agents: List[str]
    agent_tasks: List[AgentTask]
    execution_mode: str = "parallel"
    estimated_total_time: int = 0

class SmartDecomposer:
    """智能任务分解器"""

    def __init__(self):
        # 可用的专业agents
        self.available_agents = {
            # 开发类
            "backend-architect": "后端架构设计、API开发、微服务、数据库设计",
            "frontend-specialist": "前端开发、React、Vue、Angular、UI/UX实现",
            "fullstack-engineer": "全栈开发、端到端应用、系统集成",
            "mobile-developer": "移动应用、iOS、Android、React Native、Flutter",
            "api-designer": "API设计、OpenAPI规范、接口文档、RESTful设计",

            # 数据库和数据
            "database-specialist": "数据库设计、SQL、NoSQL、数据建模、性能优化",
            "data-engineer": "数据管道、ETL、数据仓库、大数据处理",
            "data-scientist": "数据分析、机器学习、统计分析、数据可视化",

            # 质量和测试
            "test-engineer": "自动化测试、单元测试、集成测试、测试策略",
            "code-reviewer": "代码审查、质量控制、最佳实践、重构建议",
            "security-auditor": "安全审计、漏洞评估、合规检查、渗透测试",
            "performance-engineer": "性能优化、负载测试、性能调优、监控",

            # 基础设施和运维
            "devops-engineer": "CI/CD、容器化、自动化部署、基础设施",
            "cloud-architect": "云架构、AWS/GCP/Azure、微服务、可扩展性",
            "kubernetes-expert": "K8s集群、容器编排、云原生、服务网格",
            "monitoring-specialist": "监控系统、日志分析、告警、可观测性",

            # 业务和产品
            "business-analyst": "业务需求、流程分析、用户故事、需求规格",
            "product-strategist": "产品策略、市场分析、功能规划、路线图",
            "project-manager": "项目管理、里程碑规划、风险管理、团队协调",
            "ux-designer": "用户体验、界面设计、交互设计、用户研究",

            # 专业领域
            "ai-engineer": "AI/ML系统、深度学习、模型部署、AI集成",
            "blockchain-developer": "区块链、智能合约、Web3、DeFi应用",
            "fintech-specialist": "金融科技、支付系统、合规、风控",
            "healthcare-dev": "医疗健康、HIPAA合规、医疗设备集成、健康数据",
            "ecommerce-expert": "电商平台、支付集成、库存管理、订单处理",
            "game-developer": "游戏开发、游戏引擎、游戏机制、多人在线"
        }

        # 项目类型模式
        self.project_patterns = {
            "电商|商城|购物|支付|订单": {
                "type": "ecommerce",
                "complexity": TaskComplexity.COMPLEX,
                "core_agents": ["backend-architect", "frontend-specialist", "database-specialist", "security-auditor"]
            },
            "API|接口|服务端|后端": {
                "type": "backend_api",
                "complexity": TaskComplexity.MEDIUM,
                "core_agents": ["backend-architect", "api-designer", "test-engineer"]
            },
            "前端|界面|UI|React|Vue": {
                "type": "frontend",
                "complexity": TaskComplexity.MEDIUM,
                "core_agents": ["frontend-specialist", "ux-designer", "test-engineer"]
            },
            "全栈|完整应用|端到端": {
                "type": "fullstack",
                "complexity": TaskComplexity.COMPLEX,
                "core_agents": ["fullstack-engineer", "database-specialist", "devops-engineer"]
            },
            "移动应用|APP|安卓|iOS": {
                "type": "mobile",
                "complexity": TaskComplexity.COMPLEX,
                "core_agents": ["mobile-developer", "backend-architect", "api-designer"]
            },
            "AI|机器学习|深度学习|模型": {
                "type": "ai_ml",
                "complexity": TaskComplexity.COMPLEX,
                "core_agents": ["ai-engineer", "data-scientist", "data-engineer"]
            },
            "区块链|Web3|智能合约|DeFi": {
                "type": "blockchain",
                "complexity": TaskComplexity.COMPLEX,
                "core_agents": ["blockchain-developer", "security-auditor", "frontend-specialist"]
            },
            "金融|支付|银行|fintech": {
                "type": "fintech",
                "complexity": TaskComplexity.ENTERPRISE,
                "core_agents": ["fintech-specialist", "security-auditor", "backend-architect"]
            },
            "游戏|游戏开发|Unity|Unreal": {
                "type": "game",
                "complexity": TaskComplexity.COMPLEX,
                "core_agents": ["game-developer", "backend-architect", "performance-engineer"]
            },
            "医疗|健康|HIPAA|医院": {
                "type": "healthcare",
                "complexity": TaskComplexity.ENTERPRISE,
                "core_agents": ["healthcare-dev", "security-auditor", "database-specialist"]
            },
            "部署|运维|Docker|Kubernetes|AWS": {
                "type": "devops",
                "complexity": TaskComplexity.MEDIUM,
                "core_agents": ["devops-engineer", "cloud-architect", "monitoring-specialist"]
            },
            "测试|质量|QA|自动化测试": {
                "type": "testing",
                "complexity": TaskComplexity.MEDIUM,
                "core_agents": ["test-engineer", "code-reviewer", "performance-engineer"]
            },
            "安全|渗透测试|漏洞|合规": {
                "type": "security",
                "complexity": TaskComplexity.COMPLEX,
                "core_agents": ["security-auditor", "backend-architect", "test-engineer"]
            }
        }

        logger.info("智能任务分解器初始化完成")

    def decompose_task(self, task_description: str) -> TaskAnalysis:
        """
        智能分解任务

        Args:
            task_description: 任务描述

        Returns:
            TaskAnalysis: 分解后的任务分析结果
        """
        logger.info(f"开始分解任务: {task_description}")

        # 1. 分析项目类型和复杂度
        project_type, complexity = self._analyze_project_type(task_description)

        # 2. 识别所需agents
        required_agents = self._identify_required_agents(task_description, project_type)

        # 3. 生成具体的agent任务
        agent_tasks = self._generate_agent_tasks(task_description, project_type, required_agents)

        # 4. 确定执行模式
        execution_mode = self._determine_execution_mode(complexity, len(agent_tasks))

        # 5. 估算总时间
        estimated_time = sum(task.estimated_time for task in agent_tasks)

        analysis = TaskAnalysis(
            original_task=task_description,
            complexity=complexity,
            project_type=project_type,
            required_agents=required_agents,
            agent_tasks=agent_tasks,
            execution_mode=execution_mode,
            estimated_total_time=estimated_time
        )

        logger.info(f"任务分解完成: {project_type}项目, {complexity.value}复杂度, {len(agent_tasks)}个agents")
        return analysis

    def _analyze_project_type(self, task_description: str) -> Tuple[str, TaskComplexity]:
        """分析项目类型和复杂度"""
        task_lower = task_description.lower()

        for pattern, info in self.project_patterns.items():
            if re.search(pattern, task_lower):
                return info["type"], info["complexity"]

        # 默认分析
        if len(task_description) > 200:
            return "complex_custom", TaskComplexity.COMPLEX
        elif len(task_description) > 100:
            return "medium_custom", TaskComplexity.MEDIUM
        else:
            return "simple_custom", TaskComplexity.SIMPLE

    def _identify_required_agents(self, task_description: str, project_type: str) -> List[str]:
        """识别所需的agents"""
        task_lower = task_description.lower()
        required_agents = set()

        # 1. 根据项目类型获取核心agents
        for pattern, info in self.project_patterns.items():
            if info["type"] == project_type:
                required_agents.update(info["core_agents"])
                break

        # 2. 根据关键词补充agents
        keyword_mapping = {
            "数据库|mysql|mongodb|redis": ["database-specialist"],
            "测试|test|qa|质量": ["test-engineer"],
            "安全|security|漏洞|合规": ["security-auditor"],
            "部署|deploy|docker|kubernetes": ["devops-engineer"],
            "性能|performance|优化|负载": ["performance-engineer"],
            "监控|monitoring|日志|告警": ["monitoring-specialist"],
            "需求|业务|分析|用户故事": ["business-analyst"],
            "设计|UI|UX|用户体验": ["ux-designer"],
            "项目|管理|planning|协调": ["project-manager"],
            "云|AWS|GCP|Azure|cloud": ["cloud-architect"],
            "数据|大数据|ETL|数据仓库": ["data-engineer"],
            "AI|机器学习|ML|模型|算法": ["ai-engineer"],
            "支付|金融|银行|fintech": ["fintech-specialist"]
        }

        for keywords, agents in keyword_mapping.items():
            if re.search(keywords, task_lower):
                required_agents.update(agents)

        # 3. 确保最少有合理的agent组合
        if len(required_agents) == 0:
            required_agents.add("fullstack-engineer")

        # 4. 根据复杂度调整
        if "backend" in task_lower and "frontend" in task_lower:
            required_agents.add("fullstack-engineer")

        return list(required_agents)

    def _generate_agent_tasks(self, task_description: str, project_type: str,
                            required_agents: List[str]) -> List[AgentTask]:
        """生成具体的agent任务"""
        agent_tasks = []

        task_templates = {
            "backend-architect": self._generate_backend_task,
            "frontend-specialist": self._generate_frontend_task,
            "fullstack-engineer": self._generate_fullstack_task,
            "database-specialist": self._generate_database_task,
            "test-engineer": self._generate_testing_task,
            "security-auditor": self._generate_security_task,
            "devops-engineer": self._generate_devops_task,
            "api-designer": self._generate_api_task,
            "ux-designer": self._generate_ux_task,
            "business-analyst": self._generate_business_task,
            "project-manager": self._generate_pm_task,
            "cloud-architect": self._generate_cloud_task,
            "performance-engineer": self._generate_performance_task,
            "ai-engineer": self._generate_ai_task,
            "mobile-developer": self._generate_mobile_task,
            "blockchain-developer": self._generate_blockchain_task,
            "fintech-specialist": self._generate_fintech_task,
            "ecommerce-expert": self._generate_ecommerce_task,
            "healthcare-dev": self._generate_healthcare_task
        }

        for agent in required_agents:
            if agent in task_templates:
                task = task_templates[agent](task_description, project_type)
                if task:
                    agent_tasks.append(task)

        # 按优先级排序
        agent_tasks.sort(key=lambda x: x.priority)

        return agent_tasks

    def _generate_backend_task(self, task_description: str, project_type: str) -> AgentTask:
        """生成后端架构师任务"""
        prompt = f"""
请设计和实现后端架构：{task_description}

任务要求：
1. **系统架构设计**：
   - 设计整体架构（单体/微服务）
   - API接口规划和设计
   - 数据流和业务流程设计
   - 技术栈选择和说明

2. **核心功能实现**：
   - 用户认证和授权系统
   - 核心业务逻辑实现
   - 数据库集成和操作
   - API端点实现

3. **性能和安全**：
   - API性能优化
   - 安全最佳实践
   - 错误处理和日志
   - 缓存策略设计

4. **文档和规范**：
   - API文档生成
   - 代码规范和结构
   - 部署配置文件
   - 环境配置说明

请提供完整的后端解决方案，包括具体代码实现。
"""
        return AgentTask(
            agent_name="backend-architect",
            task_description="设计和实现后端架构",
            detailed_prompt=prompt,
            priority=1,
            estimated_time=120
        )

    def _generate_frontend_task(self, task_description: str, project_type: str) -> AgentTask:
        """生成前端专家任务"""
        prompt = f"""
请开发前端应用：{task_description}

任务要求：
1. **界面设计和开发**：
   - 现代化响应式界面设计
   - 主要页面和组件开发
   - 用户交互和体验优化
   - 移动端适配

2. **技术实现**：
   - 选择合适的前端框架（React/Vue/Angular）
   - 状态管理方案
   - 路由配置
   - API数据获取和处理

3. **功能特性**：
   - 表单验证和处理
   - 数据可视化（如需要）
   - 实时更新和通知
   - 搜索和过滤功能

4. **质量保证**：
   - 代码组织和规范
   - 性能优化
   - 浏览器兼容性
   - 错误处理

请提供完整的前端解决方案和实现代码。
"""
        return AgentTask(
            agent_name="frontend-specialist",
            task_description="开发前端用户界面",
            detailed_prompt=prompt,
            priority=2,
            estimated_time=90
        )

    def _generate_database_task(self, task_description: str, project_type: str) -> AgentTask:
        """生成数据库专家任务"""
        prompt = f"""
请设计和配置数据库系统：{task_description}

任务要求：
1. **数据库设计**：
   - 分析数据需求和关系
   - 设计数据库模型和表结构
   - 定义主键、外键和索引
   - 数据规范化和优化

2. **技术选择**：
   - 选择合适的数据库类型（SQL/NoSQL）
   - 缓存策略设计（Redis等）
   - 数据分片和集群方案
   - 备份和恢复策略

3. **性能优化**：
   - 查询优化和索引设计
   - 数据库配置优化
   - 连接池配置
   - 监控和告警设置

4. **安全和合规**：
   - 数据加密和安全
   - 用户权限管理
   - 审计日志设计
   - 合规性要求满足

请提供完整的数据库解决方案，包括建表SQL和配置。
"""
        return AgentTask(
            agent_name="database-specialist",
            task_description="设计和优化数据库系统",
            detailed_prompt=prompt,
            priority=1,
            estimated_time=75
        )

    def _generate_security_task(self, task_description: str, project_type: str) -> AgentTask:
        """生成安全审计任务"""
        prompt = f"""
请执行安全审计和加固：{task_description}

任务要求：
1. **安全评估**：
   - 系统安全架构分析
   - 潜在安全风险识别
   - 威胁建模和风险评估
   - 合规性要求检查

2. **安全实施**：
   - 身份认证和授权机制
   - 数据加密（传输和存储）
   - API安全防护
   - 输入验证和过滤

3. **安全测试**：
   - 漏洞扫描和检测
   - 渗透测试模拟
   - 安全配置审查
   - 依赖安全检查

4. **安全文档**：
   - 安全配置文档
   - 安全最佳实践指南
   - 事件响应计划
   - 安全培训材料

请提供完整的安全解决方案和实施建议。
"""
        return AgentTask(
            agent_name="security-auditor",
            task_description="安全审计和加固",
            detailed_prompt=prompt,
            priority=3,
            estimated_time=90
        )

    # 为其他agents生成类似的任务模板...
    def _generate_testing_task(self, task_description: str, project_type: str) -> AgentTask:
        """生成测试工程师任务"""
        prompt = f"""
请为项目创建全面的测试策略：{task_description}

任务要求：
1. 测试策略制定和测试用例设计
2. 自动化测试框架搭建
3. 单元测试、集成测试、E2E测试
4. 性能测试和负载测试
5. 测试数据管理和测试环境配置

请提供完整的测试解决方案。
"""
        return AgentTask("test-engineer", "创建测试策略和自动化测试", prompt, 4, 60)

    def _generate_devops_task(self, task_description: str, project_type: str) -> AgentTask:
        """生成DevOps任务"""
        prompt = f"""
请配置CI/CD和部署环境：{task_description}

任务要求：
1. CI/CD管道设计和实现
2. 容器化配置（Docker）
3. 自动化部署脚本
4. 监控和日志系统配置
5. 环境管理和配置

请提供完整的DevOps解决方案。
"""
        return AgentTask("devops-engineer", "配置CI/CD和部署", prompt, 5, 75)

    # 简化实现其他agent任务生成器...
    def _generate_fullstack_task(self, task_description: str, project_type: str) -> AgentTask:
        prompt = f"实现全栈应用：{task_description}\n包括前端、后端、数据库集成和部署配置。"
        return AgentTask("fullstack-engineer", "全栈应用开发", prompt, 2, 150)

    def _generate_api_task(self, task_description: str, project_type: str) -> AgentTask:
        prompt = f"设计API接口：{task_description}\n包括OpenAPI规范、接口文档和最佳实践。"
        return AgentTask("api-designer", "API接口设计", prompt, 1, 45)

    def _generate_ux_task(self, task_description: str, project_type: str) -> AgentTask:
        prompt = f"设计用户体验：{task_description}\n包括用户研究、交互设计和界面原型。"
        return AgentTask("ux-designer", "用户体验设计", prompt, 1, 60)

    def _generate_business_task(self, task_description: str, project_type: str) -> AgentTask:
        prompt = f"分析业务需求：{task_description}\n包括需求分析、用户故事和业务流程设计。"
        return AgentTask("business-analyst", "业务需求分析", prompt, 1, 45)

    def _generate_pm_task(self, task_description: str, project_type: str) -> AgentTask:
        prompt = f"制定项目管理计划：{task_description}\n包括里程碑规划、风险管理和团队协调。"
        return AgentTask("project-manager", "项目管理和规划", prompt, 1, 30)

    def _generate_cloud_task(self, task_description: str, project_type: str) -> AgentTask:
        prompt = f"设计云架构：{task_description}\n包括AWS/GCP/Azure架构设计和成本优化。"
        return AgentTask("cloud-architect", "云架构设计", prompt, 3, 60)

    def _generate_performance_task(self, task_description: str, project_type: str) -> AgentTask:
        prompt = f"性能优化：{task_description}\n包括性能测试、瓶颈分析和优化建议。"
        return AgentTask("performance-engineer", "性能优化分析", prompt, 4, 60)

    def _generate_ai_task(self, task_description: str, project_type: str) -> AgentTask:
        prompt = f"AI/ML系统开发：{task_description}\n包括模型选择、训练和部署集成。"
        return AgentTask("ai-engineer", "AI/ML系统开发", prompt, 2, 120)

    def _generate_mobile_task(self, task_description: str, project_type: str) -> AgentTask:
        prompt = f"移动应用开发：{task_description}\n包括iOS/Android原生或跨平台应用开发。"
        return AgentTask("mobile-developer", "移动应用开发", prompt, 2, 120)

    def _generate_blockchain_task(self, task_description: str, project_type: str) -> AgentTask:
        prompt = f"区块链应用开发：{task_description}\n包括智能合约、Web3集成和DeFi功能。"
        return AgentTask("blockchain-developer", "区块链应用开发", prompt, 2, 100)

    def _generate_fintech_task(self, task_description: str, project_type: str) -> AgentTask:
        prompt = f"金融科技解决方案：{task_description}\n包括支付集成、风控和合规要求。"
        return AgentTask("fintech-specialist", "金融科技解决方案", prompt, 2, 90)

    def _generate_ecommerce_task(self, task_description: str, project_type: str) -> AgentTask:
        prompt = f"电商平台开发：{task_description}\n包括商品管理、支付集成和订单处理。"
        return AgentTask("ecommerce-expert", "电商平台开发", prompt, 2, 100)

    def _generate_healthcare_task(self, task_description: str, project_type: str) -> AgentTask:
        prompt = f"医疗健康系统：{task_description}\n包括HIPAA合规、医疗数据处理和集成。"
        return AgentTask("healthcare-dev", "医疗健康系统", prompt, 2, 110)

    def _determine_execution_mode(self, complexity: TaskComplexity, agent_count: int) -> str:
        """确定执行模式"""
        if agent_count >= 5 or complexity in [TaskComplexity.COMPLEX, TaskComplexity.ENTERPRISE]:
            return "parallel"
        elif agent_count >= 3:
            return "hybrid"
        else:
            return "sequential"

    def get_execution_summary(self, analysis: TaskAnalysis) -> str:
        """获取执行摘要"""
        summary = f"""
📊 任务分解摘要：{analysis.original_task}

🎯 项目类型: {analysis.project_type}
📈 复杂度: {analysis.complexity.value}
⚡ 执行模式: {analysis.execution_mode}
👥 所需agents: {len(analysis.required_agents)}个
⏰ 预估时间: {analysis.estimated_total_time}分钟

🤖 Agent分工：
"""
        for i, task in enumerate(analysis.agent_tasks, 1):
            summary += f"{i}. {task.agent_name}: {task.task_description}\n"

        return summary

# 全局分解器实例
_smart_decomposer = None

def get_smart_decomposer() -> SmartDecomposer:
    """获取智能任务分解器实例"""
    global _smart_decomposer
    if _smart_decomposer is None:
        _smart_decomposer = SmartDecomposer()
    return _smart_decomposer