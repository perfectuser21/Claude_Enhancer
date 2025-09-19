#!/usr/bin/env python3
"""
Perfect21 动态工作流生成器
根据任务特征智能生成最优工作流
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

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
        # 扩展的Agent选择映射表
        self.agent_selector = {
            # === 开发实现类 ===
            r"API|接口|REST|GraphQL|endpoint|服务接口": ["api-designer", "backend-architect", "test-engineer"],
            r"界面|UI|前端|页面|React|Vue|Angular|组件|交互": ["ux-designer", "frontend-specialist", "accessibility-auditor"],
            r"数据库|存储|SQL|MongoDB|Redis|数据模型|Schema": ["database-specialist", "backend-architect", "performance-engineer"],
            r"全栈|完整应用|系统|端到端|整体架构": ["product-strategist", "backend-architect", "frontend-specialist", "api-designer"],
            r"微服务|分布式|SOA|服务架构": ["backend-architect", "api-designer", "devops-engineer", "monitoring-specialist"],
            r"移动端|APP|移动应用|iOS|Android": ["frontend-specialist", "ux-designer", "performance-engineer"],

            # === 认证授权类 ===
            r"登录|登陆|login|signin|注册|signup|用户系统": ["backend-architect", "security-auditor", "api-designer", "test-engineer"],
            r"JWT|token|令牌|会话|session|认证": ["backend-architect", "security-auditor", "api-designer"],
            r"密码|加密|哈希|bcrypt|crypto|安全认证": ["security-auditor", "backend-architect", "test-engineer"],
            r"权限|授权|RBAC|访问控制|鉴权": ["security-auditor", "backend-architect", "api-designer"],
            r"OAuth|SSO|单点登录|第三方登录": ["security-auditor", "backend-architect", "api-designer"],

            # === 数据处理类 ===
            r"CRUD|增删改查|数据操作|数据管理": ["backend-architect", "database-specialist", "api-designer", "test-engineer"],
            r"搜索|检索|全文搜索|ElasticSearch": ["backend-architect", "database-specialist", "performance-engineer"],
            r"缓存|Redis|内存|性能优化": ["backend-architect", "performance-engineer", "database-specialist"],
            r"消息队列|MQ|异步|事件驱动": ["backend-architect", "devops-engineer", "monitoring-specialist"],
            r"文件上传|存储|OSS|CDN": ["backend-architect", "cloud-architect", "security-auditor"],

            # === 质量保证类 ===
            r"测试|验证|检查|TDD|BDD|单元测试|集成测试": ["test-engineer", "backend-architect", "api-designer"],
            r"性能|优化|速度|快|慢|负载|压力测试": ["performance-engineer", "performance-tester", "backend-architect"],
            r"安全|漏洞|审计|扫描|渗透测试": ["security-auditor", "test-engineer", "backend-architect"],
            r"可访问性|无障碍|WCAG|用户体验": ["accessibility-auditor", "ux-designer", "frontend-specialist"],
            r"代码质量|重构|Clean Code|最佳实践": ["backend-architect", "test-engineer", "technical-writer"],

            # === 运维部署类 ===
            r"部署|发布|生产|上线|CI/CD|持续集成": ["devops-engineer", "deployment-manager", "monitoring-specialist"],
            r"容器|Docker|K8s|Kubernetes|编排": ["kubernetes-expert", "devops-engineer", "cloud-architect"],
            r"监控|日志|告警|指标|APM|观测性": ["monitoring-specialist", "devops-engineer", "performance-engineer"],
            r"云|AWS|Azure|GCP|云原生|Serverless": ["cloud-architect", "devops-engineer", "kubernetes-expert"],
            r"自动化|脚本|工具|流水线": ["devops-engineer", "backend-architect", "test-engineer"],

            # === 分析设计类 ===
            r"分析|评估|调研|研究|需求分析|业务分析": ["business-analyst", "product-strategist", "backend-architect"],
            r"架构|设计|规划|重构|技术选型": ["backend-architect", "api-designer", "product-strategist"],
            r"文档|说明|指南|README|技术文档": ["technical-writer", "api-designer", "product-strategist"],
            r"原型|Demo|POC|概念验证": ["product-strategist", "ux-designer", "backend-architect"],
            r"产品|需求|用户故事|业务逻辑": ["product-strategist", "business-analyst", "ux-designer"],

            # === 特定技术栈 ===
            r"Python|Django|Flask|FastAPI": ["backend-architect", "api-designer", "test-engineer"],
            r"Node\.js|Express|Nest\.js|JavaScript": ["backend-architect", "frontend-specialist", "api-designer"],
            r"Java|Spring|SpringBoot|Maven": ["backend-architect", "api-designer", "test-engineer"],
            r"Go|Golang|Gin|高性能": ["backend-architect", "performance-engineer", "api-designer"],
            r"Rust|系统编程|内存安全": ["backend-architect", "performance-engineer", "security-auditor"],

            # === 业务场景类 ===
            r"电商|商城|支付|订单|购物车": ["product-strategist", "backend-architect", "security-auditor", "api-designer"],
            r"社交|聊天|消息|通讯|即时通信": ["backend-architect", "frontend-specialist", "performance-engineer"],
            r"内容管理|CMS|博客|发布系统": ["backend-architect", "frontend-specialist", "ux-designer"],
            r"数据分析|报表|BI|统计|图表": ["backend-architect", "database-specialist", "frontend-specialist"],
            r"AI|机器学习|算法|智能推荐": ["backend-architect", "performance-engineer", "api-designer"],
        }

        # 预编译正则表达式以提高性能（添加安全验证）
        self.compiled_patterns = {}
        for pattern, agents in self.agent_selector.items():
            try:
                # 安全检查：防止ReDoS攻击
                if len(pattern) > 500:  # 限制正则表达式长度
                    logger.warning(f"正则表达式过长，跳过: {pattern[:50]}...")
                    continue

                # 检查危险的正则模式（嵌套量词）
                if re.search(r'(\*|\+|\?|\{[^}]+\}){2,}', pattern):
                    logger.warning(f"检测到潜在的ReDoS模式，跳过: {pattern}")
                    continue

                # 安全编译
                self.compiled_patterns[re.compile(pattern, re.I)] = agents
            except re.error as e:
                logger.warning(f"无效的正则表达式 '{pattern}': {e}")
                continue

        # 扩展的Agent分类
        self.agent_categories = {
            "design": ["product-strategist", "business-analyst", "ux-designer", "api-designer"],
            "implementation": ["backend-architect", "frontend-specialist", "database-specialist"],
            "quality": ["test-engineer", "security-auditor", "performance-engineer", "performance-tester", "accessibility-auditor"],
            "deployment": ["devops-engineer", "cloud-architect", "kubernetes-expert", "monitoring-specialist", "deployment-manager"],
            "documentation": ["technical-writer"]
        }

        # Agent能力标签（用于智能补充）
        self.agent_capabilities = {
            "backend-architect": ["后端", "架构", "API", "系统设计", "数据库"],
            "frontend-specialist": ["前端", "UI", "用户界面", "组件", "交互"],
            "api-designer": ["API", "接口", "服务", "协议", "文档"],
            "database-specialist": ["数据库", "存储", "数据模型", "查询优化"],
            "test-engineer": ["测试", "质量", "验证", "自动化", "TDD"],
            "security-auditor": ["安全", "认证", "授权", "加密", "审计"],
            "performance-engineer": ["性能", "优化", "监控", "调优", "缓存"],
            "devops-engineer": ["部署", "运维", "自动化", "CI/CD", "基础设施"],
            "ux-designer": ["用户体验", "交互设计", "原型", "界面"],
            "product-strategist": ["产品", "需求", "业务", "规划", "策略"],
            "business-analyst": ["业务分析", "需求", "流程", "调研"],
            "technical-writer": ["文档", "说明", "指南", "技术写作"],
            "cloud-architect": ["云计算", "架构", "分布式", "云服务"],
            "kubernetes-expert": ["容器", "编排", "K8s", "微服务"],
            "monitoring-specialist": ["监控", "日志", "告警", "观测"],
            "accessibility-auditor": ["可访问性", "无障碍", "用户体验"],
            "performance-tester": ["性能测试", "压力测试", "负载测试"],
            "deployment-manager": ["部署管理", "发布", "版本控制"]
        }

        # 最少agent数量配置（提高到3-5个）
        self.min_agents_config = {
            ComplexityLevel.SIMPLE: 3,  # 原来是2，现在至少3个
            ComplexityLevel.MEDIUM: 4,  # 原来是3，现在至少4个
            ComplexityLevel.COMPLEX: 5  # 原来是4，现在至少5个
        }

        # 成功模式记忆（基于经验积累的最佳组合）
        self.successful_patterns = {
            "用户认证": ["backend-architect", "security-auditor", "test-engineer", "api-designer"],
            "用户登录": ["backend-architect", "security-auditor", "test-engineer", "api-designer"],
            "API开发": ["api-designer", "backend-architect", "test-engineer", "technical-writer"],
            "UI组件": ["frontend-specialist", "ux-designer", "accessibility-auditor", "test-engineer"],
            "数据库设计": ["database-specialist", "backend-architect", "performance-engineer", "data-engineer"],
            "性能优化": ["performance-engineer", "backend-architect", "monitoring-specialist", "devops-engineer"],
            "部署流程": ["devops-engineer", "deployment-manager", "monitoring-specialist", "cloud-architect"],
            "全栈功能": ["fullstack-engineer", "database-specialist", "test-engineer", "devops-engineer"],
            "微服务": ["backend-architect", "devops-engineer", "api-designer", "monitoring-specialist"],
            "测试系统": ["test-engineer", "performance-tester", "security-auditor", "e2e-test-specialist"],
            "安全审计": ["security-auditor", "backend-architect", "test-engineer", "code-reviewer"]
        }

        # 推荐agent组合（核心agents）
        self.core_agent_combinations = {
            "开发": ["backend-architect", "test-engineer"],
            "前端": ["frontend-specialist", "ux-designer"],
            "API": ["api-designer", "backend-architect", "test-engineer"],
            "全栈": ["backend-architect", "frontend-specialist", "api-designer"],
            "安全": ["security-auditor", "backend-architect", "test-engineer"],
            "性能": ["performance-engineer", "backend-architect", "monitoring-specialist"],
            "部署": ["devops-engineer", "monitoring-specialist"],
            "测试": ["test-engineer", "performance-tester"]
        }

        logger.info(f"动态工作流生成器初始化完成: {len(self.compiled_patterns)}个模式, {len(self.agent_capabilities)}个agents")

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
        """提取关键词（增强版）"""
        important_words = []

        # 扩展的关键词模式库
        keyword_patterns = {
            "开发动作": r"开发|实现|创建|构建|编写|编码|制作|搭建",
            "优化动作": r"优化|改进|提升|加速|增强|升级|重构",
            "维护动作": r"修复|解决|处理|debug|调试|排查|修正",
            "质量动作": r"测试|验证|检查|审计|评估|审查|校验",
            "部署动作": r"部署|发布|上线|迁移|安装|配置|发布",
            "技术领域": r"API|接口|服务|系统|框架|平台|组件|模块",
            "架构层次": r"前端|后端|全栈|数据库|缓存|消息队列|微服务",
            "质量属性": r"安全|性能|质量|稳定|可靠|可用|扩展",
            "业务场景": r"电商|社交|内容|支付|用户|订单|消息|聊天",
            "技术栈": r"Python|Java|Node|React|Vue|Docker|K8s|Redis|MySQL|MongoDB"
        }

        # 使用预编译正则表达式提取关键词
        for category, pattern in keyword_patterns.items():
            try:
                matches = re.findall(pattern, text, re.I)
                if matches:
                    important_words.extend(matches)
                    logger.debug(f"关键词类别 '{category}': {matches}")
            except re.error as e:
                logger.warning(f"无效的关键词模式 '{pattern}': {e}")
                continue

        # 去重并返回
        unique_keywords = list(set(important_words))
        logger.debug(f"提取到 {len(unique_keywords)} 个关键词: {unique_keywords}")
        return unique_keywords

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
        """选择合适的agents（改进版 - 优先使用成功模式）"""
        selected = set()  # 使用set避免重复
        match_details = []  # 记录匹配详情用于调试

        # 1. 首先检查是否有成功模式匹配
        request_lower = request.lower()
        for pattern_key, agents_list in self.successful_patterns.items():
            if pattern_key in request_lower:
                selected.update(agents_list)
                logger.info(f"匹配成功模式: '{pattern_key}' -> {agents_list}")
                # 如果匹配到成功模式，可以直接返回（已经是最佳组合）
                if len(selected) >= self.min_agents_config[analysis.complexity]:
                    return list(selected)

        # 2. 如果成功模式不够，继续使用正则匹配补充
        for compiled_pattern, agents in self.compiled_patterns.items():
            matches = compiled_pattern.findall(request)
            if matches:
                selected.update(agents)
                match_details.append({
                    'pattern': compiled_pattern.pattern,
                    'matches': matches,
                    'agents': agents
                })
                logger.debug(f"模式匹配: '{compiled_pattern.pattern}' -> {matches} -> {agents}")

        # 转换为列表
        selected = list(selected)

        # 记录初始选择结果
        logger.info(f"初始选择: {len(selected)}个agents - {selected}")

        # 如果没有匹配到足够的agents，使用智能补充
        min_required = self.min_agents_config[analysis.complexity]
        if len(selected) < min_required:
            logger.info(f"agents数量不足({len(selected)} < {min_required})，启动智能补充")
            selected = self._smart_supplement_agents(request, analysis, selected)

        # 如果仍然没有选中任何agents，使用fallback策略
        if not selected:
            logger.warning("没有匹配到任何agents，使用fallback策略")
            selected = self._fallback_agent_selection(analysis)

        logger.info(f"最终选择: {len(selected)}个agents - {selected}")
        return selected

    def _smart_supplement_agents(self, request: str, analysis: TaskAnalysis, current_agents: List[str]) -> List[str]:
        """智能补充agents"""
        supplemented = current_agents.copy()
        min_required = self.min_agents_config[analysis.complexity]

        # 1. 根据领域添加核心agents
        domain_agents = self.core_agent_combinations.get(analysis.domain, [])
        for agent in domain_agents:
            if agent not in supplemented:
                supplemented.append(agent)
                logger.debug(f"领域补充: {analysis.domain} -> {agent}")
                if len(supplemented) >= min_required:
                    break

        # 2. 如果还不够，基于能力标签匹配
        if len(supplemented) < min_required:
            request_lower = request.lower()
            agent_scores = defaultdict(int)

            # 计算每个agent与请求的相似度
            for agent, capabilities in self.agent_capabilities.items():
                if agent in supplemented:
                    continue

                score = 0
                for capability in capabilities:
                    if capability.lower() in request_lower:
                        score += 1

                if score > 0:
                    agent_scores[agent] = score

            # 按分数排序并添加
            sorted_agents = sorted(agent_scores.items(), key=lambda x: x[1], reverse=True)
            for agent, score in sorted_agents:
                supplemented.append(agent)
                logger.debug(f"能力补充: {agent} (分数: {score})")
                if len(supplemented) >= min_required:
                    break

        # 3. 如果还不够，添加必需的质量保证agents
        if len(supplemented) < min_required:
            essential_agents = ["test-engineer", "backend-architect"]
            for agent in essential_agents:
                if agent not in supplemented:
                    supplemented.append(agent)
                    logger.debug(f"必需补充: {agent}")
                    if len(supplemented) >= min_required:
                        break

        logger.info(f"智能补充完成: {len(current_agents)} -> {len(supplemented)} agents")
        return supplemented

    def _fallback_agent_selection(self, analysis: TaskAnalysis) -> List[str]:
        """Fallback agent选择策略"""
        fallback_map = {
            "开发": ["backend-architect", "test-engineer", "api-designer"],
            "优化": ["performance-engineer", "backend-architect", "monitoring-specialist"],
            "测试": ["test-engineer", "performance-tester", "security-auditor"],
            "部署": ["devops-engineer", "monitoring-specialist", "deployment-manager"],
            "安全": ["security-auditor", "backend-architect", "test-engineer"],
            "维护": ["backend-architect", "test-engineer", "monitoring-specialist"]
        }

        agents = fallback_map.get(analysis.domain, ["backend-architect", "test-engineer"])

        # 确保满足最小数量要求
        min_required = self.min_agents_config[analysis.complexity]
        if len(agents) < min_required:
            # 添加通用agents
            additional = ["api-designer", "technical-writer", "product-strategist"]
            for agent in additional:
                if agent not in agents:
                    agents.append(agent)
                    if len(agents) >= min_required:
                        break

        logger.info(f"Fallback选择: {analysis.domain} -> {agents}")
        return agents

    def _optimize_agents(self, agents: List[str], analysis: TaskAnalysis) -> List[str]:
        """优化agent组合（增强版）"""
        optimized = agents.copy()

        # 根据复杂度设置最优agent数量范围
        optimal_ranges = {
            ComplexityLevel.SIMPLE: (2, 3),    # 2-3个agents
            ComplexityLevel.MEDIUM: (3, 5),   # 3-5个agents
            ComplexityLevel.COMPLEX: (4, 8)   # 4-8个agents
        }

        min_agents, max_agents = optimal_ranges[analysis.complexity]

        logger.debug(f"优化前: {len(optimized)}个agents - {optimized}")

        # 1. 确保满足最小数量
        if len(optimized) < min_agents:
            logger.info(f"agents数量不足({len(optimized)} < {min_agents})，在优化阶段进行补充")
            optimized = self._smart_supplement_agents("agent优化补充", analysis, optimized)

        # 2. 限制最大数量（避免过多的协调成本）
        if len(optimized) > max_agents:
            logger.info(f"agents数量过多({len(optimized)} > {max_agents})，进行智能裁剪")
            optimized = self._smart_trim_agents(optimized, analysis, max_agents)

        # 3. 确保必需的质量保证agents
        optimized = self._ensure_quality_agents(optimized, analysis)

        # 4. 检查并优化agent组合协调性
        optimized = self._optimize_agent_synergy(optimized, analysis)

        logger.info(f"优化后: {len(optimized)}个agents - {optimized}")
        return optimized

    def _smart_trim_agents(self, agents: List[str], analysis: TaskAnalysis, max_count: int) -> List[str]:
        """智能裁剪agents"""
        if len(agents) <= max_count:
            return agents

        # 按优先级对agents进行分类
        priority_levels = {
            # 最高优先级 - 核心开发agents
            1: ["backend-architect", "api-designer"],
            # 高优先级 - 质量保证agents
            2: ["test-engineer", "security-auditor"],
            # 中优先级 - 业务和设计agents
            3: ["product-strategist", "business-analyst", "ux-designer", "frontend-specialist"],
            # 较低优先级 - 专业agents
            4: ["database-specialist", "performance-engineer", "cloud-architect"],
            # 最低优先级 - 辅助agents
            5: ["technical-writer", "accessibility-auditor", "performance-tester"]
        }

        # 按优先级组织agents
        prioritized_agents = []
        for level in sorted(priority_levels.keys()):
            level_agents = [a for a in agents if a in priority_levels[level]]
            prioritized_agents.extend(level_agents)

        # 添加未分类的agents
        uncategorized = [a for a in agents if a not in prioritized_agents]
        prioritized_agents.extend(uncategorized)

        # 取前 max_count 个
        trimmed = prioritized_agents[:max_count]

        logger.debug(f"智能裁剪: {len(agents)} -> {len(trimmed)} agents")
        return trimmed

    def _ensure_quality_agents(self, agents: List[str], analysis: TaskAnalysis) -> List[str]:
        """确保必要的质量保证agents"""
        enhanced = agents.copy()

        # 根据复杂度确定必需的质量agents
        required_quality_agents = {
            ComplexityLevel.SIMPLE: [],  # 简单任务可以不强制要求
            ComplexityLevel.MEDIUM: ["test-engineer"],  # 中等任务需要测试
            ComplexityLevel.COMPLEX: ["test-engineer", "security-auditor"]  # 复杂任务需要测试+安全
        }

        required = required_quality_agents[analysis.complexity]

        for agent in required:
            if agent not in enhanced:
                enhanced.append(agent)
                logger.debug(f"添加必需质量agent: {agent}")

        return enhanced

    def _optimize_agent_synergy(self, agents: List[str], analysis: TaskAnalysis) -> List[str]:
        """优化agent组合的协调性"""
        # 定义agent协调关系（哪些agents在一起工作时效果更好）
        synergy_pairs = {
            ("backend-architect", "api-designer"): 2.0,      # 后端+API设计
            ("frontend-specialist", "ux-designer"): 1.8,     # 前端+UX设计
            ("test-engineer", "backend-architect"): 1.6,     # 测试+后端
            ("security-auditor", "backend-architect"): 1.5, # 安全+后端
            ("performance-engineer", "backend-architect"): 1.4, # 性能+后端
            ("devops-engineer", "monitoring-specialist"): 1.3, # 运维+监控
            ("product-strategist", "business-analyst"): 1.2, # 产品+业务分析
        }

        # 计算当前组合的协调分数
        synergy_score = 0
        for i, agent1 in enumerate(agents):
            for agent2 in agents[i+1:]:
                pair = tuple(sorted([agent1, agent2]))
                if pair in synergy_pairs:
                    synergy_score += synergy_pairs[pair]

        logger.debug(f"Agent组合协调分数: {synergy_score:.1f}")

        # 如果协调分数较低，尝试添加一个协调agent
        if synergy_score < 2.0 and len(agents) < self.min_agents_config[analysis.complexity] + 2:
            # 寻找最佳的协调添加
            best_addition = None
            best_score_increase = 0

            for candidate in self.agent_capabilities.keys():
                if candidate in agents:
                    continue

                score_increase = 0
                for existing in agents:
                    pair = tuple(sorted([candidate, existing]))
                    if pair in synergy_pairs:
                        score_increase += synergy_pairs[pair]

                if score_increase > best_score_increase:
                    best_score_increase = score_increase
                    best_addition = candidate

            if best_addition and best_score_increase > 1.0:
                agents.append(best_addition)
                logger.debug(f"添加协调agent: {best_addition} (增加分数: {best_score_increase:.1f})")

        return agents

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