#!/usr/bin/env python3
"""
Perfect21 Intelligent Agent Selection System
智能分析任务需求并选择最优Agent组合，避免过度使用不必要的Agent
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)

class TaskComplexity(Enum):
    """任务复杂度等级"""
    SIMPLE = "simple"       # 1-2个agents
    MODERATE = "moderate"   # 3-4个agents
    COMPLEX = "complex"     # 5-7个agents
    CRITICAL = "critical"   # 8+个agents

class ExecutionMode(Enum):
    """执行模式"""
    PARALLEL = "parallel"
    SEQUENTIAL = "sequential"
    HYBRID = "hybrid"

@dataclass
class TaskAnalysis:
    """任务分析结果"""
    task_type: str
    complexity: TaskComplexity
    execution_mode: ExecutionMode
    required_agents: List[str]
    optional_agents: List[str]
    dependencies: Dict[str, List[str]]
    estimated_time: int  # minutes
    confidence: float   # 0.0-1.0
    reasoning: str

@dataclass
class AgentCapability:
    """Agent能力描述"""
    name: str
    domains: List[str]
    skills: List[str]
    dependencies: List[str]  # 依赖的其他agents
    conflicts: List[str]     # 冲突的agents
    cost: float             # 执行成本权重
    success_rate: float     # 历史成功率

class IntelligentAgentSelector:
    """智能Agent选择器"""

    def __init__(self, rules_path: str = None):
        self.rules_path = rules_path or "/home/xx/dev/Perfect21/rules/perfect21_rules.yaml"
        self.agent_capabilities = self._load_agent_capabilities()
        self.task_patterns = self._load_task_patterns()
        self.success_patterns = self._load_success_patterns()

        # 执行历史和学习数据
        self.execution_history: List[Dict] = []
        self.performance_metrics: Dict[str, float] = {}

        logger.info("智能Agent选择器初始化完成")

    def _load_agent_capabilities(self) -> Dict[str, AgentCapability]:
        """加载Agent能力映射"""
        capabilities = {
            # Backend Development
            "backend-architect": AgentCapability(
                name="backend-architect",
                domains=["architecture", "backend", "system-design"],
                skills=["API-design", "database-design", "scalability", "security"],
                dependencies=[],
                conflicts=["frontend-specialist"],
                cost=0.8,
                success_rate=0.92
            ),
            "python-pro": AgentCapability(
                name="python-pro",
                domains=["backend", "scripting", "automation"],
                skills=["python", "fastapi", "django", "data-processing"],
                dependencies=["backend-architect"],
                conflicts=[],
                cost=0.6,
                success_rate=0.88
            ),
            "database-specialist": AgentCapability(
                name="database-specialist",
                domains=["data", "storage", "performance"],
                skills=["sql", "nosql", "optimization", "migration"],
                dependencies=["backend-architect"],
                conflicts=[],
                cost=0.7,
                success_rate=0.90
            ),

            # Frontend Development
            "frontend-specialist": AgentCapability(
                name="frontend-specialist",
                domains=["ui", "frontend", "user-experience"],
                skills=["react", "vue", "css", "javascript"],
                dependencies=[],
                conflicts=["backend-architect"],
                cost=0.6,
                success_rate=0.85
            ),
            "react-pro": AgentCapability(
                name="react-pro",
                domains=["frontend", "components", "state-management"],
                skills=["react", "jsx", "hooks", "redux"],
                dependencies=["frontend-specialist"],
                conflicts=[],
                cost=0.5,
                success_rate=0.87
            ),

            # Quality Assurance
            "test-engineer": AgentCapability(
                name="test-engineer",
                domains=["testing", "quality", "automation"],
                skills=["unit-testing", "integration-testing", "e2e", "automation"],
                dependencies=[],
                conflicts=[],
                cost=0.4,
                success_rate=0.93
            ),
            "security-auditor": AgentCapability(
                name="security-auditor",
                domains=["security", "audit", "compliance"],
                skills=["vulnerability-scan", "penetration-test", "compliance"],
                dependencies=[],
                conflicts=[],
                cost=0.6,
                success_rate=0.91
            ),
            "code-reviewer": AgentCapability(
                name="code-reviewer",
                domains=["quality", "standards", "best-practices"],
                skills=["code-review", "standards", "refactoring"],
                dependencies=[],
                conflicts=[],
                cost=0.3,
                success_rate=0.89
            ),

            # Infrastructure
            "devops-engineer": AgentCapability(
                name="devops-engineer",
                domains=["deployment", "ci-cd", "monitoring"],
                skills=["docker", "kubernetes", "ci-cd", "monitoring"],
                dependencies=["backend-architect", "test-engineer"],
                conflicts=[],
                cost=0.8,
                success_rate=0.86
            ),
            "cloud-architect": AgentCapability(
                name="cloud-architect",
                domains=["cloud", "scalability", "infrastructure"],
                skills=["aws", "azure", "gcp", "terraform"],
                dependencies=["devops-engineer"],
                conflicts=[],
                cost=0.9,
                success_rate=0.88
            ),

            # Specialized
            "api-designer": AgentCapability(
                name="api-designer",
                domains=["api", "interface", "integration"],
                skills=["rest", "graphql", "openapi", "documentation"],
                dependencies=["backend-architect"],
                conflicts=[],
                cost=0.5,
                success_rate=0.90
            ),
            "performance-engineer": AgentCapability(
                name="performance-engineer",
                domains=["performance", "optimization", "scaling"],
                skills=["profiling", "optimization", "caching", "load-testing"],
                dependencies=["backend-architect"],
                conflicts=[],
                cost=0.7,
                success_rate=0.89
            ),
            "technical-writer": AgentCapability(
                name="technical-writer",
                domains=["documentation", "communication"],
                skills=["documentation", "api-docs", "user-guides"],
                dependencies=[],
                conflicts=[],
                cost=0.3,
                success_rate=0.94
            ),
            "project-manager": AgentCapability(
                name="project-manager",
                domains=["coordination", "planning", "communication"],
                skills=["planning", "coordination", "risk-management"],
                dependencies=[],
                conflicts=[],
                cost=0.4,
                success_rate=0.82
            )
        }

        return capabilities

    def _load_task_patterns(self) -> Dict[str, Dict]:
        """从规则文件加载任务模式"""
        try:
            with open(self.rules_path, 'r', encoding='utf-8') as f:
                rules = yaml.safe_load(f)
                return rules.get('agent_patterns', {})
        except Exception as e:
            logger.warning(f"无法加载规则文件: {e}")
            return {}

    def _load_success_patterns(self) -> Dict[str, List[str]]:
        """加载历史成功模式"""
        # 基于历史数据的成功Agent组合
        return {
            "authentication_success": [
                "backend-architect", "security-auditor", "test-engineer", "api-designer"
            ],
            "api_development_success": [
                "api-designer", "backend-architect", "test-engineer", "technical-writer"
            ],
            "fullstack_success": [
                "fullstack-engineer", "database-specialist", "test-engineer", "devops-engineer"
            ],
            "performance_success": [
                "performance-engineer", "backend-architect", "monitoring-specialist"
            ]
        }

    def analyze_task(self, task_description: str, context: Dict[str, Any] = None) -> TaskAnalysis:
        """
        分析任务并返回详细分析结果

        Args:
            task_description: 任务描述
            context: 额外上下文信息

        Returns:
            TaskAnalysis: 详细分析结果
        """
        context = context or {}

        # 1. 识别任务类型
        task_type = self._identify_task_type(task_description)

        # 2. 评估复杂度
        complexity = self._assess_complexity(task_description, context)

        # 3. 确定执行模式
        execution_mode = self._determine_execution_mode(task_type, complexity)

        # 4. 选择Agent组合
        required_agents, optional_agents = self._select_agents(
            task_type, complexity, task_description
        )

        # 5. 分析依赖关系
        dependencies = self._analyze_dependencies(required_agents + optional_agents)

        # 6. 估算时间
        estimated_time = self._estimate_time(required_agents, complexity)

        # 7. 计算置信度
        confidence = self._calculate_confidence(task_type, required_agents)

        # 8. 生成推理说明
        reasoning = self._generate_reasoning(
            task_type, complexity, required_agents, execution_mode
        )

        return TaskAnalysis(
            task_type=task_type,
            complexity=complexity,
            execution_mode=execution_mode,
            required_agents=required_agents,
            optional_agents=optional_agents,
            dependencies=dependencies,
            estimated_time=estimated_time,
            confidence=confidence,
            reasoning=reasoning
        )

    def _identify_task_type(self, task_description: str) -> str:
        """识别任务类型"""
        task_lower = task_description.lower()

        # 检查规则文件中的模式
        for task_type, pattern_config in self.task_patterns.items():
            keywords = pattern_config.get('keywords', [])
            if any(keyword.lower() in task_lower for keyword in keywords):
                return task_type

        # 使用正则表达式进行更精确匹配
        patterns = {
            'authentication': r'(登录|认证|auth|jwt|oauth|session|用户|权限)',
            'api_development': r'(api|接口|rest|graphql|endpoint)',
            'database_design': r'(数据库|database|schema|sql|mongodb|redis)',
            'frontend_development': r'(前端|frontend|react|vue|ui|组件|页面)',
            'fullstack_development': r'(全栈|fullstack|完整功能|前后端)',
            'performance_optimization': r'(性能|优化|performance|速度|缓存)',
            'testing': r'(测试|test|qa|质量保证)',
            'deployment': r'(部署|deploy|ci/cd|docker|kubernetes)',
            'security': r'(安全|security|漏洞|审计)',
            'documentation': r'(文档|document|说明|guide)'
        }

        for task_type, pattern in patterns.items():
            if re.search(pattern, task_lower):
                return task_type

        return 'general_development'

    def _assess_complexity(self, task_description: str, context: Dict) -> TaskComplexity:
        """评估任务复杂度"""
        complexity_score = 0

        # 基于关键词评估
        complexity_keywords = {
            'simple': ['简单', '快速', '基础', 'simple', 'basic', 'quick'],
            'moderate': ['中等', '标准', 'standard', 'moderate', '常规'],
            'complex': ['复杂', '完整', '系统', 'complex', 'system', 'full'],
            'critical': ['关键', '核心', '重要', 'critical', 'core', 'enterprise']
        }

        task_lower = task_description.lower()

        for level, keywords in complexity_keywords.items():
            if any(keyword in task_lower for keyword in keywords):
                if level == 'simple':
                    complexity_score = 1
                elif level == 'moderate':
                    complexity_score = 2
                elif level == 'complex':
                    complexity_score = 3
                elif level == 'critical':
                    complexity_score = 4
                break

        # 基于任务长度和技术栈数量调整
        if len(task_description) > 200:
            complexity_score += 1

        tech_stack_count = len(re.findall(r'\b(react|vue|python|java|docker|kubernetes|aws|api|database)\b', task_lower))
        complexity_score += tech_stack_count // 3

        # 基于上下文信息调整
        if context.get('deadline', '').lower() in ['urgent', 'asap', '紧急']:
            complexity_score += 1

        if context.get('team_size', 1) > 5:
            complexity_score += 1

        # 映射到枚举
        if complexity_score <= 1:
            return TaskComplexity.SIMPLE
        elif complexity_score <= 2:
            return TaskComplexity.MODERATE
        elif complexity_score <= 3:
            return TaskComplexity.COMPLEX
        else:
            return TaskComplexity.CRITICAL

    def _determine_execution_mode(self, task_type: str, complexity: TaskComplexity) -> ExecutionMode:
        """确定执行模式"""
        # 检查规则文件中的配置
        if task_type in self.task_patterns:
            configured_mode = self.task_patterns[task_type].get('execution_mode', 'parallel')
            if configured_mode == 'sequential':
                return ExecutionMode.SEQUENTIAL
            elif configured_mode == 'hybrid':
                return ExecutionMode.HYBRID

        # 基于复杂度决定
        if complexity in [TaskComplexity.SIMPLE, TaskComplexity.MODERATE]:
            return ExecutionMode.PARALLEL
        elif complexity == TaskComplexity.COMPLEX:
            return ExecutionMode.HYBRID
        else:
            return ExecutionMode.PARALLEL  # 关键任务需要快速响应

    def _select_agents(self, task_type: str, complexity: TaskComplexity,
                      task_description: str) -> Tuple[List[str], List[str]]:
        """选择Agent组合"""
        required_agents = []
        optional_agents = []

        # 从规则文件获取必需agents
        if task_type in self.task_patterns:
            required_agents = self.task_patterns[task_type].get('required_agents', [])

        # 基于复杂度调整agent数量
        if complexity == TaskComplexity.SIMPLE:
            # 简单任务：保持最少agents（2-3个）
            required_agents = required_agents[:3]
        elif complexity == TaskComplexity.MODERATE:
            # 中等任务：3-4个agents
            if len(required_agents) < 3:
                optional_agents = self._suggest_additional_agents(task_type, required_agents)
                required_agents.extend(optional_agents[:4-len(required_agents)])
                optional_agents = []
        elif complexity == TaskComplexity.COMPLEX:
            # 复杂任务：5-7个agents
            if len(required_agents) < 5:
                additional = self._suggest_additional_agents(task_type, required_agents)
                required_agents.extend(additional[:7-len(required_agents)])
        else:
            # 关键任务：8+个agents
            additional = self._suggest_additional_agents(task_type, required_agents)
            required_agents.extend(additional[:10-len(required_agents)])

        # 移除重复
        required_agents = list(dict.fromkeys(required_agents))

        # 验证Agent组合有效性
        required_agents = self._validate_agent_combination(required_agents)

        return required_agents, optional_agents

    def _suggest_additional_agents(self, task_type: str, existing_agents: List[str]) -> List[str]:
        """建议额外的agents"""
        suggestions = []

        # 基于任务类型的推荐逻辑
        recommendations = {
            'authentication': ['technical-writer', 'performance-engineer', 'project-manager'],
            'api_development': ['security-auditor', 'performance-engineer', 'database-specialist'],
            'database_design': ['test-engineer', 'security-auditor'],
            'frontend_development': ['backend-architect', 'performance-engineer'],
            'fullstack_development': ['security-auditor', 'technical-writer', 'project-manager'],
            'performance_optimization': ['test-engineer', 'devops-engineer'],
            'general_development': ['test-engineer', 'code-reviewer', 'project-manager']
        }

        task_recommendations = recommendations.get(task_type, recommendations['general_development'])

        for agent in task_recommendations:
            if agent not in existing_agents:
                suggestions.append(agent)

        return suggestions

    def _validate_agent_combination(self, agents: List[str]) -> List[str]:
        """验证并优化Agent组合"""
        valid_agents = []

        for agent in agents:
            if agent in self.agent_capabilities:
                # 检查冲突
                capability = self.agent_capabilities[agent]
                has_conflict = False

                for existing_agent in valid_agents:
                    if existing_agent in capability.conflicts:
                        has_conflict = True
                        # 选择成功率更高的agent
                        if (existing_agent in self.agent_capabilities and
                            self.agent_capabilities[existing_agent].success_rate > capability.success_rate):
                            continue
                        else:
                            valid_agents.remove(existing_agent)
                            break

                if not has_conflict or existing_agent not in valid_agents:
                    valid_agents.append(agent)

        return valid_agents

    def _analyze_dependencies(self, agents: List[str]) -> Dict[str, List[str]]:
        """分析Agent依赖关系"""
        dependencies = {}

        for agent in agents:
            if agent in self.agent_capabilities:
                agent_deps = self.agent_capabilities[agent].dependencies
                # 只保留实际包含在当前agents列表中的依赖
                actual_deps = [dep for dep in agent_deps if dep in agents]
                if actual_deps:
                    dependencies[agent] = actual_deps

        return dependencies

    def _estimate_time(self, agents: List[str], complexity: TaskComplexity) -> int:
        """估算执行时间（分钟）"""
        base_time = {
            TaskComplexity.SIMPLE: 30,
            TaskComplexity.MODERATE: 60,
            TaskComplexity.COMPLEX: 120,
            TaskComplexity.CRITICAL: 240
        }

        # 基础时间
        estimated = base_time[complexity]

        # 根据agent数量调整（更多agents不一定更快，需要协调开销）
        agent_count = len(agents)
        if agent_count <= 3:
            multiplier = 1.0
        elif agent_count <= 5:
            multiplier = 1.2  # 协调开销
        else:
            multiplier = 1.5  # 更大协调开销

        estimated = int(estimated * multiplier)

        return estimated

    def _calculate_confidence(self, task_type: str, agents: List[str]) -> float:
        """计算选择的置信度"""
        confidence = 0.5  # 基础置信度

        # 如果任务类型匹配规则，提高置信度
        if task_type in self.task_patterns:
            confidence += 0.2

        # 如果使用了成功模式，提高置信度
        for pattern_name, successful_agents in self.success_patterns.items():
            if set(agents).intersection(set(successful_agents)):
                overlap_ratio = len(set(agents).intersection(set(successful_agents))) / len(successful_agents)
                confidence += overlap_ratio * 0.3
                break

        # 基于历史成功率调整
        if agents:
            avg_success_rate = sum(
                self.agent_capabilities.get(agent, AgentCapability("", [], [], [], [], 0, 0.5)).success_rate
                for agent in agents
            ) / len(agents)
            confidence = confidence * 0.7 + avg_success_rate * 0.3

        return min(confidence, 1.0)

    def _generate_reasoning(self, task_type: str, complexity: TaskComplexity,
                          agents: List[str], execution_mode: ExecutionMode) -> str:
        """生成选择推理说明"""
        reasoning_parts = []

        reasoning_parts.append(f"**任务类型**: {task_type}")
        reasoning_parts.append(f"**复杂度等级**: {complexity.value}")
        reasoning_parts.append(f"**执行模式**: {execution_mode.value}")

        reasoning_parts.append(f"**选择了{len(agents)}个Agents**:")
        for agent in agents:
            if agent in self.agent_capabilities:
                capability = self.agent_capabilities[agent]
                reasoning_parts.append(
                    f"  - {agent}: {', '.join(capability.skills)} (成功率: {capability.success_rate:.1%})"
                )

        # 添加选择原因
        if task_type in self.task_patterns:
            reasoning_parts.append(f"**符合{task_type}模式规则**")

        if complexity == TaskComplexity.SIMPLE:
            reasoning_parts.append("**简单任务，使用最少Agents避免过度工程**")
        elif complexity == TaskComplexity.COMPLEX:
            reasoning_parts.append("**复杂任务，需要多领域专家协作**")

        return "\n".join(reasoning_parts)

    def get_optimal_agents(self, task_description: str,
                          context: Dict[str, Any] = None,
                          max_agents: int = 10) -> Dict[str, Any]:
        """
        获取最优Agent组合（主要接口）

        Args:
            task_description: 任务描述
            context: 额外上下文
            max_agents: 最大agent数量

        Returns:
            Dict: 优化后的agent选择结果
        """
        try:
            # 分析任务
            analysis = self.analyze_task(task_description, context)

            # 限制agent数量
            if len(analysis.required_agents) > max_agents:
                analysis.required_agents = analysis.required_agents[:max_agents]

            # 生成执行指令
            execution_instruction = self._generate_execution_instruction(analysis)

            result = {
                'success': True,
                'task_analysis': analysis,
                'selected_agents': analysis.required_agents,
                'optional_agents': analysis.optional_agents,
                'execution_mode': analysis.execution_mode.value,
                'estimated_time': analysis.estimated_time,
                'confidence': analysis.confidence,
                'reasoning': analysis.reasoning,
                'dependencies': analysis.dependencies,
                'execution_instruction': execution_instruction
            }

            # 记录到历史
            self._record_selection(task_description, result)

            return result

        except Exception as e:
            logger.error(f"Agent选择失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Agent选择过程发生错误'
            }

    def _generate_execution_instruction(self, analysis: TaskAnalysis) -> str:
        """生成Claude Code执行指令"""
        agents = analysis.required_agents

        if analysis.execution_mode == ExecutionMode.PARALLEL:
            # 并行执行指令
            instruction = "<function_calls>\n"
            for agent in agents:
                instruction += f"""<invoke name="Task">
<parameter name="subagent_type">{agent}</parameter>
<parameter name="prompt">{analysis.reasoning}</parameter>
</invoke>\n"""
            instruction += "</function_calls>"
        else:
            # 顺序执行指令
            instruction = "顺序执行以下Agents:\n"
            for i, agent in enumerate(agents, 1):
                instruction += f"{i}. {agent}\n"

        return instruction

    def _record_selection(self, task_description: str, result: Dict[str, Any]) -> None:
        """记录选择历史用于学习"""
        record = {
            'timestamp': logger.name,  # 临时使用logger名称
            'task_description': task_description,
            'selected_agents': result['selected_agents'],
            'confidence': result['confidence'],
            'execution_mode': result['execution_mode']
        }

        self.execution_history.append(record)

        # 限制历史记录大小
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-500:]

    def learn_from_execution(self, task_description: str, agents: List[str],
                           success: bool, execution_time: float) -> None:
        """从执行结果学习，更新成功模式"""
        if success:
            # 更新成功率
            for agent in agents:
                if agent in self.agent_capabilities:
                    current_rate = self.agent_capabilities[agent].success_rate
                    # 使用指数移动平均更新成功率
                    new_rate = current_rate * 0.9 + 0.1
                    self.agent_capabilities[agent].success_rate = min(new_rate, 1.0)

        # 记录性能指标
        agent_key = "-".join(sorted(agents))
        if agent_key not in self.performance_metrics:
            self.performance_metrics[agent_key] = execution_time
        else:
            # 使用移动平均
            self.performance_metrics[agent_key] = (
                self.performance_metrics[agent_key] * 0.8 + execution_time * 0.2
            )

    def get_selection_statistics(self) -> Dict[str, Any]:
        """获取选择统计信息"""
        total_selections = len(self.execution_history)

        if total_selections == 0:
            return {'total_selections': 0}

        # 最常用agents
        agent_usage = {}
        for record in self.execution_history:
            for agent in record['selected_agents']:
                agent_usage[agent] = agent_usage.get(agent, 0) + 1

        most_used = sorted(agent_usage.items(), key=lambda x: x[1], reverse=True)[:10]

        # 平均置信度
        avg_confidence = sum(r['confidence'] for r in self.execution_history) / total_selections

        # 执行模式分布
        mode_distribution = {}
        for record in self.execution_history:
            mode = record['execution_mode']
            mode_distribution[mode] = mode_distribution.get(mode, 0) + 1

        return {
            'total_selections': total_selections,
            'most_used_agents': most_used,
            'average_confidence': avg_confidence,
            'execution_mode_distribution': mode_distribution,
            'performance_metrics': dict(list(self.performance_metrics.items())[:10])
        }


# 全局实例
_intelligent_selector = None

def get_intelligent_selector() -> IntelligentAgentSelector:
    """获取全局智能选择器实例"""
    global _intelligent_selector
    if _intelligent_selector is None:
        _intelligent_selector = IntelligentAgentSelector()
    return _intelligent_selector