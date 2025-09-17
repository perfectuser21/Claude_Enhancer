#!/usr/bin/env python3
"""
Perfect21 动态工作流生成器
根据任务特征智能生成最优工作流
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("DynamicWorkflowGenerator")

class ComplexityLevel(Enum):
    """任务复杂度级别"""
    SIMPLE = "simple"      # 1-2个agents, <1小时
    MEDIUM = "medium"      # 2-4个agents, 1-3小时
    COMPLEX = "complex"    # 4-8个agents, 3+小时

class ExecutionMode(Enum):
    """执行模式"""
    SEQUENTIAL = "sequential"  # 顺序执行
    PARALLEL = "parallel"      # 并行执行
    HYBRID = "hybrid"         # 混合模式

@dataclass
class TaskAnalysis:
    """任务分析结果"""
    keywords: List[str]
    complexity: ComplexityLevel
    domain: str
    estimated_loc: int  # 预估代码行数
    module_count: int   # 涉及模块数

@dataclass
class WorkflowStage:
    """工作流阶段"""
    name: str
    agents: List[str]
    mode: ExecutionMode
    sync_point: bool = False
    quality_gate: Optional[Dict[str, Any]] = None

@dataclass
class DynamicWorkflow:
    """动态生成的工作流"""
    analysis: TaskAnalysis
    selected_agents: List[str]
    stages: List[WorkflowStage]
    execution_mode: ExecutionMode
    estimated_time: float  # 小时

class DynamicWorkflowGenerator:
    """动态工作流生成器"""

    def __init__(self):
        """初始化生成器"""
        # Agent选择映射表
        self.agent_selector = {
            # 开发类
            r"API|接口|REST|GraphQL": ["api-designer", "backend-architect"],
            r"界面|UI|前端|页面|React|Vue": ["ux-designer", "frontend-specialist"],
            r"数据库|存储|SQL|MongoDB": ["database-specialist", "backend-architect"],
            r"全栈|完整应用|系统": ["product-strategist", "backend-architect", "frontend-specialist"],

            # 认证相关 - 新增
            r"登录|登陆|login|signin|注册|signup": ["backend-architect", "security-auditor", "api-designer"],
            r"JWT|token|令牌|会话|session": ["backend-architect", "security-auditor"],
            r"密码|加密|哈希|bcrypt|crypto": ["security-auditor", "backend-architect"],

            # 质量类
            r"测试|验证|检查|TDD": ["test-engineer"],
            r"性能|优化|速度|快|慢": ["performance-engineer", "performance-tester"],
            r"安全|漏洞|审计|认证|授权|鉴权": ["security-auditor"],
            r"可访问性|无障碍|WCAG": ["accessibility-auditor"],

            # 运维类
            r"部署|发布|生产|上线": ["devops-engineer", "deployment-manager"],
            r"容器|Docker|K8s|Kubernetes": ["kubernetes-expert", "devops-engineer"],
            r"监控|日志|告警|指标": ["monitoring-specialist"],
            r"云|AWS|Azure|GCP": ["cloud-architect"],

            # 分析类
            r"分析|评估|调研|研究": ["business-analyst", "backend-architect"],
            r"架构|设计|规划|重构": ["backend-architect", "api-designer"],
            r"文档|说明|指南|README": ["technical-writer"],
        }

        # Agent分类
        self.agent_categories = {
            "design": ["product-strategist", "business-analyst", "ux-designer", "api-designer"],
            "implementation": ["backend-architect", "frontend-specialist", "database-specialist"],
            "quality": ["test-engineer", "security-auditor", "performance-engineer", "accessibility-auditor"],
            "deployment": ["devops-engineer", "cloud-architect", "kubernetes-expert", "monitoring-specialist"],
            "documentation": ["technical-writer"]
        }

        logger.info("动态工作流生成器初始化完成")

    def generate_workflow(self, user_request: str) -> DynamicWorkflow:
        """根据用户请求生成工作流"""
        # 1. 分析任务
        analysis = self._analyze_task(user_request)

        # 2. 选择agents
        selected_agents = self._select_agents(user_request, analysis)

        # 3. 优化agent组合
        selected_agents = self._optimize_agents(selected_agents, analysis)

        # 4. 确定执行模式
        execution_mode = self._determine_execution_mode(selected_agents, analysis)

        # 5. 生成阶段
        stages = self._generate_stages(selected_agents, analysis)

        # 6. 估算时间
        estimated_time = self._estimate_time(analysis, len(selected_agents))

        workflow = DynamicWorkflow(
            analysis=analysis,
            selected_agents=selected_agents,
            stages=stages,
            execution_mode=execution_mode,
            estimated_time=estimated_time
        )

        logger.info(f"生成工作流: {len(stages)}个阶段, {len(selected_agents)}个agents")
        return workflow

    def _analyze_task(self, request: str) -> TaskAnalysis:
        """分析任务特征"""
        # 提取关键词
        keywords = self._extract_keywords(request)

        # 评估复杂度
        complexity = self._estimate_complexity(request)

        # 识别领域
        domain = self._identify_domain(keywords)

        # 估算代码规模
        estimated_loc = self._estimate_code_size(request, complexity)

        # 估算模块数量
        module_count = self._estimate_modules(request, complexity)

        return TaskAnalysis(
            keywords=keywords,
            complexity=complexity,
            domain=domain,
            estimated_loc=estimated_loc,
            module_count=module_count
        )

    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取逻辑
        important_words = []

        # 检查常见关键词
        patterns = [
            r"开发|实现|创建|构建|编写",
            r"优化|改进|提升|加速",
            r"修复|解决|处理|debug",
            r"测试|验证|检查|审计",
            r"部署|发布|上线|迁移",
            r"API|接口|服务|系统",
            r"前端|后端|全栈|数据库",
            r"安全|性能|质量|稳定"
        ]

        for pattern in patterns:
            if re.search(pattern, text, re.I):
                matches = re.findall(pattern, text, re.I)
                important_words.extend(matches)

        return list(set(important_words))

    def _estimate_complexity(self, request: str) -> ComplexityLevel:
        """评估任务复杂度"""
        request_lower = request.lower()

        # 复杂度指标
        complexity_score = 0

        # 关键词权重
        if "简单" in request_lower or "快速" in request_lower:
            complexity_score -= 1
        if "复杂" in request_lower or "完整" in request_lower:
            complexity_score += 2
        if "系统" in request_lower or "架构" in request_lower:
            complexity_score += 2
        if "全栈" in request_lower:
            complexity_score += 3

        # 功能数量
        feature_count = len(re.findall(r"实现|添加|创建|开发", request_lower))
        complexity_score += feature_count

        # 技术栈多样性
        tech_keywords = ["前端", "后端", "数据库", "API", "部署", "测试"]
        tech_count = sum(1 for tech in tech_keywords if tech in request_lower)
        complexity_score += tech_count

        # 判定复杂度
        if complexity_score <= 2:
            return ComplexityLevel.SIMPLE
        elif complexity_score <= 5:
            return ComplexityLevel.MEDIUM
        else:
            return ComplexityLevel.COMPLEX

    def _identify_domain(self, keywords: List[str]) -> str:
        """识别任务领域"""
        domain_keywords = {
            "开发": ["开发", "实现", "创建", "编写", "构建"],
            "优化": ["优化", "改进", "提升", "加速", "性能"],
            "测试": ["测试", "验证", "检查", "审计"],
            "部署": ["部署", "发布", "上线", "迁移"],
            "安全": ["安全", "认证", "授权", "加密"],
            "维护": ["修复", "debug", "解决", "处理"]
        }

        # 统计各领域关键词出现次数
        domain_scores = {}
        for domain, domain_words in domain_keywords.items():
            score = sum(1 for keyword in keywords
                       for word in domain_words
                       if word.lower() in keyword.lower())
            if score > 0:
                domain_scores[domain] = score

        # 返回得分最高的领域
        if domain_scores:
            return max(domain_scores, key=domain_scores.get)
        return "通用"

    def _estimate_code_size(self, request: str, complexity: ComplexityLevel) -> int:
        """估算代码规模"""
        base_size = {
            ComplexityLevel.SIMPLE: 30,
            ComplexityLevel.MEDIUM: 100,
            ComplexityLevel.COMPLEX: 300
        }

        size = base_size[complexity]

        # 根据具体需求调整
        if "CRUD" in request or "增删改查" in request:
            size *= 1.5
        if "完整" in request or "全面" in request:
            size *= 2

        return int(size)

    def _estimate_modules(self, request: str, complexity: ComplexityLevel) -> int:
        """估算涉及模块数"""
        base_modules = {
            ComplexityLevel.SIMPLE: 1,
            ComplexityLevel.MEDIUM: 2,
            ComplexityLevel.COMPLEX: 4
        }

        modules = base_modules[complexity]

        # 检查是否涉及多个系统
        if "全栈" in request:
            modules += 2
        if "微服务" in request:
            modules += 3

        return modules

    def _select_agents(self, request: str, analysis: TaskAnalysis) -> List[str]:
        """选择合适的agents"""
        selected = []

        # 根据关键词匹配agents
        for pattern, agents in self.agent_selector.items():
            if re.search(pattern, request, re.I):
                selected.extend(agents)

        # 去重
        selected = list(set(selected))

        # 如果没有匹配到，根据领域选择默认agents
        if not selected:
            if analysis.domain == "开发":
                selected = ["backend-architect", "test-engineer"]
            elif analysis.domain == "优化":
                selected = ["performance-engineer"]
            elif analysis.domain == "测试":
                selected = ["test-engineer"]
            else:
                selected = ["backend-architect"]

        return selected

    def _optimize_agents(self, agents: List[str], analysis: TaskAnalysis) -> List[str]:
        """优化agent组合"""
        optimized = agents.copy()

        # 根据复杂度调整agent数量
        max_agents = {
            ComplexityLevel.SIMPLE: 2,
            ComplexityLevel.MEDIUM: 4,
            ComplexityLevel.COMPLEX: 8
        }

        # 限制最大数量
        if len(optimized) > max_agents[analysis.complexity]:
            # 优先保留核心agents
            priority_agents = ["backend-architect", "test-engineer", "security-auditor"]
            core = [a for a in optimized if a in priority_agents]
            others = [a for a in optimized if a not in priority_agents]
            optimized = core + others[:max_agents[analysis.complexity] - len(core)]

        # 确保有测试agent（质量保证）
        if analysis.complexity != ComplexityLevel.SIMPLE and "test-engineer" not in optimized:
            optimized.append("test-engineer")

        return optimized

    def _determine_execution_mode(self, agents: List[str], analysis: TaskAnalysis) -> ExecutionMode:
        """确定执行模式"""
        agent_count = len(agents)

        # 简单规则
        if agent_count <= 2:
            return ExecutionMode.SEQUENTIAL

        # 检查是否需要协调
        design_agents = [a for a in agents if a in self.agent_categories["design"]]
        impl_agents = [a for a in agents if a in self.agent_categories["implementation"]]

        if design_agents and impl_agents:
            return ExecutionMode.HYBRID  # 设计和实现需要分阶段

        # 默认并行
        return ExecutionMode.PARALLEL

    def _generate_stages(self, agents: List[str], analysis: TaskAnalysis) -> List[WorkflowStage]:
        """生成执行阶段"""
        stages = []

        # 按类别分组agents
        categorized = {
            "design": [],
            "implementation": [],
            "quality": [],
            "deployment": [],
            "documentation": []
        }

        for agent in agents:
            for category, category_agents in self.agent_categories.items():
                if agent in category_agents:
                    categorized[category].append(agent)
                    break

        # 生成阶段
        # 阶段1: 设计与分析
        if categorized["design"]:
            stages.append(WorkflowStage(
                name="设计与分析",
                agents=categorized["design"],
                mode=ExecutionMode.PARALLEL,
                sync_point=True
            ))

        # 阶段2: 开发实现
        if categorized["implementation"]:
            mode = ExecutionMode.SEQUENTIAL if len(categorized["implementation"]) > 2 else ExecutionMode.PARALLEL
            stages.append(WorkflowStage(
                name="开发实现",
                agents=categorized["implementation"],
                mode=mode,
                sync_point=True
            ))

        # 阶段3: 质量保证
        if categorized["quality"]:
            stages.append(WorkflowStage(
                name="质量保证",
                agents=categorized["quality"],
                mode=ExecutionMode.PARALLEL,
                quality_gate={
                    "测试通过率": ">95%",
                    "代码覆盖率": ">80%"
                }
            ))

        # 阶段4: 部署
        if categorized["deployment"]:
            stages.append(WorkflowStage(
                name="部署准备",
                agents=categorized["deployment"],
                mode=ExecutionMode.SEQUENTIAL
            ))

        # 阶段5: 文档
        if categorized["documentation"]:
            stages.append(WorkflowStage(
                name="文档编写",
                agents=categorized["documentation"],
                mode=ExecutionMode.SEQUENTIAL
            ))

        # 如果没有生成任何阶段，创建默认阶段
        if not stages and agents:
            stages.append(WorkflowStage(
                name="任务执行",
                agents=agents,
                mode=ExecutionMode.PARALLEL if len(agents) > 1 else ExecutionMode.SEQUENTIAL
            ))

        return stages

    def _estimate_time(self, analysis: TaskAnalysis, agent_count: int) -> float:
        """估算执行时间（小时）"""
        # 基础时间
        base_time = {
            ComplexityLevel.SIMPLE: 0.5,
            ComplexityLevel.MEDIUM: 2.0,
            ComplexityLevel.COMPLEX: 5.0
        }

        time = base_time[analysis.complexity]

        # 根据agent数量调整（并行可以减少时间）
        if agent_count > 3:
            time *= 0.8  # 并行执行节省20%时间

        # 根据模块数量调整
        time += analysis.module_count * 0.3

        return round(time, 1)

# 使用示例
if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(level=logging.INFO)

    # 创建生成器
    generator = DynamicWorkflowGenerator()

    # 测试不同类型的任务
    test_requests = [
        "开发一个用户认证系统，包括登录、注册、密码重置功能",
        "优化网站首页的加载速度",
        "部署应用到生产环境",
        "为API添加单元测试和集成测试"
    ]

    for request in test_requests:
        print(f"\n{'='*50}")
        print(f"任务: {request}")
        print('='*50)

        workflow = generator.generate_workflow(request)

        print(f"分析结果:")
        print(f"  - 复杂度: {workflow.analysis.complexity.value}")
        print(f"  - 领域: {workflow.analysis.domain}")
        print(f"  - 预估代码: {workflow.analysis.estimated_loc}行")

        print(f"\n选中Agents ({len(workflow.selected_agents)}个):")
        for agent in workflow.selected_agents:
            print(f"  - {agent}")

        print(f"\n执行阶段:")
        for i, stage in enumerate(workflow.stages, 1):
            print(f"  阶段{i}: {stage.name} [{stage.mode.value}]")
            for agent in stage.agents:
                print(f"    └─ @{agent}")
            if stage.sync_point:
                print(f"    🔴 同步点")
            if stage.quality_gate:
                print(f"    ✅ 质量门: {stage.quality_gate}")

        print(f"\n预计时间: {workflow.estimated_time}小时")