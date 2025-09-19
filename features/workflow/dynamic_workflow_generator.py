#!/usr/bin/env python3
"""
Dynamic Workflow Generator - 性能优化版本
实现LRU缓存、预编译正则表达式、优化agent选择算法
"""

import re
import time
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from functools import lru_cache, wraps
from dataclasses import dataclass, field
from collections import defaultdict, OrderedDict
from datetime import datetime, timedelta
import hashlib

# 性能监控装饰器
def performance_monitor(func):
    """性能监控装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            execution_time = time.perf_counter() - start_time

            # 记录性能指标
            DynamicWorkflowGenerator._performance_metrics[func.__name__] = {
                'execution_time': execution_time,
                'last_called': datetime.now(),
                'call_count': DynamicWorkflowGenerator._performance_metrics.get(func.__name__, {}).get('call_count', 0) + 1
            }

            return result
        except Exception as e:
            execution_time = time.perf_counter() - start_time
            DynamicWorkflowGenerator._performance_metrics[func.__name__] = {
                'execution_time': execution_time,
                'last_called': datetime.now(),
                'error': str(e),
                'call_count': DynamicWorkflowGenerator._performance_metrics.get(func.__name__, {}).get('call_count', 0) + 1
            }
            raise
    return wrapper

@dataclass
class AgentCapability:
    """Agent能力定义"""
    name: str
    domain: str
    skills: List[str]
    complexity_score: float
    performance_score: float = 100.0
    availability_score: float = 100.0
    last_used: Optional[datetime] = None
    usage_count: int = 0

@dataclass
class TaskRequirement:
    """任务需求定义"""
    description: str
    domain: str
    complexity: float
    required_skills: List[str]
    priority: int = 1
    estimated_duration: int = 300

@dataclass
class WorkflowTemplate:
    """工作流模板"""
    name: str
    description: str
    stages: List[Dict[str, Any]]
    complexity_threshold: float
    applicability_score: float = 0.0

class LRUCache:
    """高性能LRU缓存实现"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache: OrderedDict = OrderedDict()
        self.hit_count = 0
        self.miss_count = 0

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key in self.cache:
            # 移动到末尾（最近使用）
            value = self.cache.pop(key)
            self.cache[key] = value
            self.hit_count += 1
            return value
        else:
            self.miss_count += 1
            return None

    def put(self, key: str, value: Any) -> None:
        """设置缓存值"""
        if key in self.cache:
            # 更新现有值
            self.cache.pop(key)
        elif len(self.cache) >= self.max_size:
            # 删除最旧的项
            self.cache.popitem(last=False)

        self.cache[key] = value

    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
        self.hit_count = 0
        self.miss_count = 0

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0

        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': f"{hit_rate:.2f}%",
            'utilization': f"{len(self.cache) / self.max_size * 100:.2f}%"
        }

class PrecompiledRegexManager:
    """预编译正则表达式管理器"""

    def __init__(self):
        # 预编译常用正则表达式
        self.patterns = {
            'agent_name': re.compile(r'@([a-zA-Z0-9\-_]+)', re.IGNORECASE),
            'task_complexity': re.compile(r'\b(?:simple|complex|medium|high|low)\b', re.IGNORECASE),
            'domain_keywords': re.compile(r'\b(?:api|database|frontend|backend|design|test|deploy|security|performance)\b', re.IGNORECASE),
            'priority_keywords': re.compile(r'\b(?:urgent|high|medium|low|critical|normal)\b', re.IGNORECASE),
            'skill_keywords': re.compile(r'\b(?:python|javascript|react|vue|node|docker|kubernetes|aws|database|sql|nosql|redis|mongodb)\b', re.IGNORECASE),
            'time_estimates': re.compile(r'(\d+)\s*(?:minutes?|mins?|hours?|hrs?|days?)', re.IGNORECASE),
            'dependency_pattern': re.compile(r'(?:depends?\s+on|requires?|needs?|after)\s+([a-zA-Z0-9\-_\s,]+)', re.IGNORECASE),
            'parallel_keywords': re.compile(r'\b(?:parallel|concurrent|simultaneously|together)\b', re.IGNORECASE),
            'sequential_keywords': re.compile(r'\b(?:sequential|step-by-step|ordered|after|then|next)\b', re.IGNORECASE),
        }

        # 性能统计
        self.usage_stats = defaultdict(int)

    def search(self, pattern_name: str, text: str) -> List[re.Match]:
        """搜索匹配项"""
        if pattern_name not in self.patterns:
            raise ValueError(f"Unknown pattern: {pattern_name}")

        self.usage_stats[pattern_name] += 1
        return list(self.patterns[pattern_name].finditer(text))

    def findall(self, pattern_name: str, text: str) -> List[str]:
        """查找所有匹配项"""
        if pattern_name not in self.patterns:
            raise ValueError(f"Unknown pattern: {pattern_name}")

        self.usage_stats[pattern_name] += 1
        return self.patterns[pattern_name].findall(text)

    def get_stats(self) -> Dict[str, int]:
        """获取使用统计"""
        return dict(self.usage_stats)

class OptimizedAgentSelector:
    """优化的Agent选择器 - O(log n)复杂度"""

    def __init__(self):
        # 按域分组的agents
        self.agents_by_domain: Dict[str, List[AgentCapability]] = defaultdict(list)

        # 按技能分组的agents
        self.agents_by_skill: Dict[str, Set[str]] = defaultdict(set)

        # 综合评分索引
        self.score_index: List[Tuple[float, str]] = []

        # 缓存
        self.selection_cache = LRUCache(max_size=500)

        # 性能统计
        self.selection_stats = {
            'total_selections': 0,
            'cache_hits': 0,
            'fast_path_selections': 0,
            'fallback_selections': 0
        }

    def add_agent(self, agent: AgentCapability) -> None:
        """添加agent"""
        # 按域分组
        self.agents_by_domain[agent.domain].append(agent)

        # 按技能分组
        for skill in agent.skills:
            self.agents_by_skill[skill].add(agent.name)

        # 更新评分索引
        self._update_score_index()

    def _update_score_index(self) -> None:
        """更新评分索引"""
        self.score_index.clear()
        for domain_agents in self.agents_by_domain.values():
            for agent in domain_agents:
                composite_score = (
                    agent.performance_score * 0.4 +
                    agent.availability_score * 0.3 +
                    (100 - agent.usage_count * 2) * 0.3  # 负载均衡
                )
                self.score_index.append((composite_score, agent.name))

        # 按评分降序排序
        self.score_index.sort(reverse=True)

    @performance_monitor
    def select_agents(self, task_req: TaskRequirement, count: int = 1) -> List[str]:
        """选择最适合的agents - 优化算法复杂度"""
        self.selection_stats['total_selections'] += 1

        # 生成缓存键
        cache_key = self._generate_cache_key(task_req, count)

        # 检查缓存
        cached_result = self.selection_cache.get(cache_key)
        if cached_result:
            self.selection_stats['cache_hits'] += 1
            return cached_result

        # Fast path: 域匹配 + 技能匹配
        candidates = self._fast_candidate_selection(task_req)

        if len(candidates) >= count:
            self.selection_stats['fast_path_selections'] += 1
            result = self._select_top_candidates(candidates, count, task_req)
        else:
            # Fallback: 全局搜索
            self.selection_stats['fallback_selections'] += 1
            result = self._fallback_selection(task_req, count)

        # 缓存结果
        self.selection_cache.put(cache_key, result)

        # 更新agent使用统计
        self._update_usage_stats(result)

        return result

    def _generate_cache_key(self, task_req: TaskRequirement, count: int) -> str:
        """生成缓存键"""
        key_data = {
            'domain': task_req.domain,
            'skills': sorted(task_req.required_skills),
            'complexity': task_req.complexity,
            'count': count
        }
        return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()

    def _fast_candidate_selection(self, task_req: TaskRequirement) -> List[AgentCapability]:
        """快速候选选择 - O(log n)"""
        candidates = []

        # 1. 优先选择域匹配的agents
        if task_req.domain in self.agents_by_domain:
            domain_agents = self.agents_by_domain[task_req.domain]
            candidates.extend(domain_agents)

        # 2. 技能匹配过滤
        if task_req.required_skills:
            skill_matched_agents = set()
            for skill in task_req.required_skills:
                if skill in self.agents_by_skill:
                    skill_matched_agents.update(self.agents_by_skill[skill])

            # 只保留有技能匹配的candidates
            candidates = [
                agent for agent in candidates
                if agent.name in skill_matched_agents or not task_req.required_skills
            ]

        return candidates

    def _select_top_candidates(self, candidates: List[AgentCapability],
                             count: int, task_req: TaskRequirement) -> List[str]:
        """从候选中选择top agents"""
        # 计算适配分数
        scored_candidates = []
        for agent in candidates:
            score = self._calculate_agent_score(agent, task_req)
            scored_candidates.append((score, agent.name))

        # 排序并选择top N
        scored_candidates.sort(reverse=True)
        return [name for _, name in scored_candidates[:count]]

    def _fallback_selection(self, task_req: TaskRequirement, count: int) -> List[str]:
        """回退选择策略"""
        # 使用预排序的评分索引
        selected = []
        for score, agent_name in self.score_index:
            if len(selected) >= count:
                break

            # 基本适配检查
            agent = self._get_agent_by_name(agent_name)
            if agent and self._is_agent_suitable(agent, task_req):
                selected.append(agent_name)

        return selected

    def _calculate_agent_score(self, agent: AgentCapability, task_req: TaskRequirement) -> float:
        """计算agent适配分数"""
        score = 0.0

        # 域匹配 (40%)
        if agent.domain == task_req.domain:
            score += 40.0

        # 技能匹配 (30%)
        if task_req.required_skills:
            matched_skills = set(agent.skills) & set(task_req.required_skills)
            skill_match_rate = len(matched_skills) / len(task_req.required_skills)
            score += skill_match_rate * 30.0

        # 复杂度匹配 (20%)
        complexity_diff = abs(agent.complexity_score - task_req.complexity)
        complexity_score = max(0, 20 - complexity_diff * 2)
        score += complexity_score

        # 性能和可用性 (10%)
        score += (agent.performance_score + agent.availability_score) / 2 * 0.1

        # 负载均衡惩罚
        usage_penalty = min(agent.usage_count * 0.5, 10)
        score -= usage_penalty

        return score

    def _is_agent_suitable(self, agent: AgentCapability, task_req: TaskRequirement) -> bool:
        """检查agent是否适合任务"""
        # 基本适配检查
        if agent.complexity_score < task_req.complexity * 0.5:
            return False

        if agent.availability_score < 50:
            return False

        return True

    def _get_agent_by_name(self, name: str) -> Optional[AgentCapability]:
        """根据名称获取agent"""
        for domain_agents in self.agents_by_domain.values():
            for agent in domain_agents:
                if agent.name == name:
                    return agent
        return None

    def _update_usage_stats(self, selected_agents: List[str]) -> None:
        """更新使用统计"""
        for agent_name in selected_agents:
            agent = self._get_agent_by_name(agent_name)
            if agent:
                agent.usage_count += 1
                agent.last_used = datetime.now()

        # 定期重新索引
        if self.selection_stats['total_selections'] % 100 == 0:
            self._update_score_index()

    def get_stats(self) -> Dict[str, Any]:
        """获取选择器统计信息"""
        return {
            'selection_stats': self.selection_stats,
            'cache_stats': self.selection_cache.get_stats(),
            'total_agents': sum(len(agents) for agents in self.agents_by_domain.values()),
            'domains': list(self.agents_by_domain.keys()),
            'skills': list(self.agents_by_skill.keys())
        }

class DynamicWorkflowGenerator:
    """动态工作流生成器 - 性能优化版本"""

    # 类级别的性能指标存储
    _performance_metrics: Dict[str, Dict[str, Any]] = {}

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # 高性能组件
        self.workflow_cache = LRUCache(max_size=1000)
        self.regex_manager = PrecompiledRegexManager()
        self.agent_selector = OptimizedAgentSelector()

        # 工作流模板缓存
        self.template_cache = LRUCache(max_size=200)

        # 任务分析缓存
        self.analysis_cache = LRUCache(max_size=500)

        # 内置agents
        self._initialize_builtin_agents()

        # 内置工作流模板
        self._initialize_workflow_templates()

        # 性能优化配置
        self.optimization_config = {
            'cache_ttl': 3600,  # 缓存TTL秒
            'max_analysis_depth': 5,
            'parallel_analysis_threshold': 3,
            'complexity_calculation_cache': True
        }

        self.logger.info("DynamicWorkflowGenerator initialized with performance optimizations")

    def _initialize_builtin_agents(self) -> None:
        """初始化内置agents"""
        builtin_agents = [
            AgentCapability("project-manager", "business", ["planning", "coordination", "requirements"], 8.0, 95.0, 100.0),
            AgentCapability("business-analyst", "business", ["analysis", "requirements", "documentation"], 7.0, 90.0, 100.0),
            AgentCapability("api-designer", "technical", ["api", "design", "documentation"], 7.5, 92.0, 100.0),
            AgentCapability("backend-architect", "technical", ["backend", "architecture", "database"], 9.0, 95.0, 100.0),
            AgentCapability("frontend-specialist", "technical", ["frontend", "ui", "javascript"], 8.0, 88.0, 100.0),
            AgentCapability("devops-engineer", "infrastructure", ["deployment", "docker", "kubernetes"], 8.5, 90.0, 100.0),
            AgentCapability("test-engineer", "quality", ["testing", "automation", "quality"], 7.0, 85.0, 100.0),
            AgentCapability("security-auditor", "security", ["security", "audit", "compliance"], 8.0, 92.0, 100.0),
            AgentCapability("performance-engineer", "technical", ["performance", "optimization", "monitoring"], 8.5, 88.0, 100.0),
            AgentCapability("code-reviewer", "quality", ["review", "standards", "quality"], 7.5, 90.0, 100.0)
        ]

        for agent in builtin_agents:
            self.agent_selector.add_agent(agent)

    def _initialize_workflow_templates(self) -> None:
        """初始化工作流模板"""
        self.workflow_templates = [
            WorkflowTemplate(
                "premium_quality_workflow",
                "质量优先的完整开发工作流",
                [
                    {
                        "name": "requirement_analysis",
                        "description": "深度需求分析",
                        "execution_mode": "parallel",
                        "agents": ["project-manager", "business-analyst", "technical-writer"],
                        "sync_point": {"type": "consensus_check", "validation_criteria": {"consensus_rate": "> 80"}}
                    },
                    {
                        "name": "architecture_design",
                        "description": "系统架构设计",
                        "execution_mode": "sequential",
                        "agents": ["api-designer", "backend-architect", "database-specialist"],
                        "quality_gate": {"checklist": "architecture_review,security_review,scalability_review"}
                    },
                    {
                        "name": "parallel_implementation",
                        "description": "并行开发实现",
                        "execution_mode": "parallel",
                        "agents": ["backend-architect", "frontend-specialist", "test-engineer"],
                        "sync_point": {"type": "integration_check", "validation_criteria": {"api_compatibility": "100"}}
                    },
                    {
                        "name": "quality_assurance",
                        "description": "质量保证",
                        "execution_mode": "parallel",
                        "agents": ["test-engineer", "security-auditor", "performance-engineer"],
                        "quality_gate": {"checklist": "test_coverage_90,security_scan_pass,performance_test_pass"}
                    },
                    {
                        "name": "deployment_prep",
                        "description": "部署准备",
                        "execution_mode": "sequential",
                        "agents": ["devops-engineer", "monitoring-specialist"],
                        "sync_point": {"type": "final_verification", "validation_criteria": {"deployment_ready": "true"}}
                    }
                ],
                9.0
            ),
            WorkflowTemplate(
                "rapid_development_workflow",
                "快速开发工作流",
                [
                    {
                        "name": "quick_analysis",
                        "description": "快速需求分析",
                        "execution_mode": "sequential",
                        "agents": ["business-analyst"],
                    },
                    {
                        "name": "rapid_implementation",
                        "description": "快速实现",
                        "execution_mode": "parallel",
                        "agents": ["backend-architect", "frontend-specialist"],
                    },
                    {
                        "name": "basic_testing",
                        "description": "基础测试",
                        "execution_mode": "sequential",
                        "agents": ["test-engineer"],
                    }
                ],
                5.0
            )
        ]

    @performance_monitor
    @lru_cache(maxsize=128)
    def analyze_task_complexity(self, task_description: str) -> float:
        """分析任务复杂度 - 缓存优化"""
        # 使用预编译正则表达式
        complexity_keywords = self.regex_manager.findall('task_complexity', task_description)
        domain_keywords = self.regex_manager.findall('domain_keywords', task_description)

        base_complexity = 5.0

        # 基于关键词调整复杂度
        complexity_modifiers = {
            'simple': -2.0, 'low': -1.5,
            'medium': 0.0,
            'complex': 2.0, 'high': 1.5, 'critical': 3.0
        }

        for keyword in complexity_keywords:
            base_complexity += complexity_modifiers.get(keyword.lower(), 0)

        # 基于涉及的技术域数量
        base_complexity += len(set(domain_keywords)) * 0.5

        # 基于描述长度
        if len(task_description) > 500:
            base_complexity += 1.0
        elif len(task_description) > 1000:
            base_complexity += 2.0

        return max(1.0, min(10.0, base_complexity))

    @performance_monitor
    def parse_task_requirements(self, task_description: str) -> TaskRequirement:
        """解析任务需求 - 性能优化版本"""
        # 生成缓存键
        cache_key = hashlib.md5(task_description.encode()).hexdigest()

        # 检查分析缓存
        cached_result = self.analysis_cache.get(cache_key)
        if cached_result:
            return cached_result

        # 使用预编译正则表达式提取信息
        domain_matches = self.regex_manager.findall('domain_keywords', task_description)
        skill_matches = self.regex_manager.findall('skill_keywords', task_description)
        priority_matches = self.regex_manager.findall('priority_keywords', task_description)
        time_matches = self.regex_manager.findall('time_estimates', task_description)

        # 确定主要域
        domain_counts = defaultdict(int)
        domain_mapping = {
            'api': 'technical', 'database': 'technical', 'backend': 'technical',
            'frontend': 'technical', 'design': 'technical',
            'test': 'quality', 'deploy': 'infrastructure',
            'security': 'security', 'performance': 'technical'
        }

        for match in domain_matches:
            domain = domain_mapping.get(match.lower(), 'general')
            domain_counts[domain] += 1

        primary_domain = max(domain_counts, key=domain_counts.get) if domain_counts else 'general'

        # 确定优先级
        priority_mapping = {'urgent': 5, 'critical': 5, 'high': 4, 'medium': 3, 'normal': 2, 'low': 1}
        priority = 3  # 默认medium
        for match in priority_matches:
            priority = max(priority, priority_mapping.get(match.lower(), 3))

        # 估算时间
        estimated_duration = 300  # 默认5分钟
        if time_matches:
            time_value = int(time_matches[0])
            if 'hour' in task_description.lower():
                estimated_duration = time_value * 3600
            elif 'day' in task_description.lower():
                estimated_duration = time_value * 24 * 3600
            else:
                estimated_duration = time_value * 60

        # 分析复杂度（使用缓存的方法）
        complexity = self.analyze_task_complexity(task_description)

        # 创建任务需求
        task_req = TaskRequirement(
            description=task_description,
            domain=primary_domain,
            complexity=complexity,
            required_skills=list(set(skill_matches)),
            priority=priority,
            estimated_duration=estimated_duration
        )

        # 缓存结果
        self.analysis_cache.put(cache_key, task_req)

        return task_req

    @performance_monitor
    def select_workflow_template(self, task_req: TaskRequirement) -> WorkflowTemplate:
        """选择工作流模板 - 优化版本"""
        cache_key = f"template_{task_req.domain}_{task_req.complexity}_{task_req.priority}"

        # 检查模板缓存
        cached_template = self.template_cache.get(cache_key)
        if cached_template:
            return cached_template

        # 计算模板适配分数
        best_template = None
        best_score = 0.0

        for template in self.workflow_templates:
            score = self._calculate_template_score(template, task_req)
            if score > best_score:
                best_score = score
                best_template = template

        # 使用默认模板如果没有找到合适的
        if not best_template:
            best_template = self.workflow_templates[0]  # premium_quality_workflow

        # 缓存结果
        self.template_cache.put(cache_key, best_template)

        return best_template

    def _calculate_template_score(self, template: WorkflowTemplate, task_req: TaskRequirement) -> float:
        """计算模板适配分数"""
        score = 0.0

        # 复杂度匹配
        complexity_diff = abs(template.complexity_threshold - task_req.complexity)
        complexity_score = max(0, 10 - complexity_diff)
        score += complexity_score * 0.6

        # 优先级匹配
        if task_req.priority >= 4 and 'premium' in template.name:
            score += 30
        elif task_req.priority <= 2 and 'rapid' in template.name:
            score += 25

        # 域匹配
        template_domains = set()
        for stage in template.stages:
            for agent in stage.get('agents', []):
                agent_obj = self.agent_selector._get_agent_by_name(agent)
                if agent_obj:
                    template_domains.add(agent_obj.domain)

        if task_req.domain in template_domains:
            score += 20

        return score

    @performance_monitor
    def generate_workflow(self, task_description: str,
                         workflow_type: str = "auto") -> Dict[str, Any]:
        """生成工作流 - 主入口方法"""
        # 生成工作流缓存键
        cache_key = hashlib.md5(f"{workflow_type}_{task_description}".encode()).hexdigest()

        # 检查工作流缓存
        cached_workflow = self.workflow_cache.get(cache_key)
        if cached_workflow:
            self.logger.info(f"Using cached workflow for: {task_description[:50]}...")
            return cached_workflow

        start_time = time.perf_counter()

        try:
            # 1. 解析任务需求
            task_req = self.parse_task_requirements(task_description)

            # 2. 选择工作流模板
            if workflow_type == "auto":
                template = self.select_workflow_template(task_req)
            else:
                template = self._get_template_by_name(workflow_type)

            # 3. 为每个阶段选择agents
            workflow_stages = []
            for stage_config in template.stages:
                stage = self._generate_stage(stage_config, task_req)
                workflow_stages.append(stage)

            # 4. 构建完整工作流
            workflow = {
                'name': f"{template.name}_{int(time.time())}",
                'description': f"为任务生成的工作流: {task_description[:100]}...",
                'task_requirements': {
                    'domain': task_req.domain,
                    'complexity': task_req.complexity,
                    'priority': task_req.priority,
                    'estimated_duration': task_req.estimated_duration
                },
                'template_used': template.name,
                'stages': workflow_stages,
                'global_context': {
                    'task_description': task_description,
                    'generation_time': datetime.now().isoformat(),
                    'complexity_score': task_req.complexity
                },
                'execution_metadata': {
                    'total_stages': len(workflow_stages),
                    'total_agents': len(set(agent for stage in workflow_stages for agent in stage.get('agents', []))),
                    'estimated_total_time': sum(stage.get('estimated_duration', 300) for stage in workflow_stages)
                }
            }

            # 缓存工作流
            self.workflow_cache.put(cache_key, workflow)

            generation_time = time.perf_counter() - start_time
            self.logger.info(f"Generated workflow in {generation_time:.3f}s for: {task_description[:50]}...")

            return workflow

        except Exception as e:
            self.logger.error(f"Failed to generate workflow: {e}")
            raise

    def _generate_stage(self, stage_config: Dict[str, Any], task_req: TaskRequirement) -> Dict[str, Any]:
        """生成工作流阶段"""
        # 选择agents
        suggested_agents = stage_config.get('agents', [])
        required_agent_count = len(suggested_agents) if suggested_agents else 1

        # 使用优化的agent选择器
        selected_agents = self.agent_selector.select_agents(task_req, required_agent_count)

        # 如果有建议的agents，优先使用
        if suggested_agents:
            # 验证建议的agents是否可用
            available_suggested = [
                agent for agent in suggested_agents
                if self.agent_selector._get_agent_by_name(agent)
            ]
            if available_suggested:
                selected_agents = available_suggested[:required_agent_count]

        stage = {
            'name': stage_config['name'],
            'description': stage_config['description'],
            'execution_mode': stage_config.get('execution_mode', 'parallel'),
            'agents': selected_agents,
            'estimated_duration': stage_config.get('estimated_duration', task_req.estimated_duration),
            'depends_on': stage_config.get('depends_on', []),
            'timeout': stage_config.get('timeout', 1800)
        }

        # 添加同步点
        if 'sync_point' in stage_config:
            stage['sync_point'] = stage_config['sync_point']

        # 添加质量门
        if 'quality_gate' in stage_config:
            stage['quality_gate'] = stage_config['quality_gate']

        # 添加思考模式
        if task_req.complexity >= 8.0:
            stage['thinking_mode'] = 'think_harder'
        elif task_req.complexity >= 6.0:
            stage['thinking_mode'] = 'think_hard'

        return stage

    def _get_template_by_name(self, template_name: str) -> WorkflowTemplate:
        """根据名称获取模板"""
        for template in self.workflow_templates:
            if template.name == template_name:
                return template

        # 返回默认模板
        return self.workflow_templates[0]

    def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        return {
            'method_metrics': self._performance_metrics,
            'cache_stats': {
                'workflow_cache': self.workflow_cache.get_stats(),
                'template_cache': self.template_cache.get_stats(),
                'analysis_cache': self.analysis_cache.get_stats()
            },
            'regex_stats': self.regex_manager.get_stats(),
            'agent_selector_stats': self.agent_selector.get_stats(),
            'optimization_config': self.optimization_config
        }

    def clear_caches(self) -> None:
        """清空所有缓存"""
        self.workflow_cache.clear()
        self.template_cache.clear()
        self.analysis_cache.clear()
        self.analyze_task_complexity.cache_clear()
        self.logger.info("All caches cleared")

    def optimize_performance(self) -> Dict[str, Any]:
        """性能优化建议"""
        metrics = self.get_performance_metrics()
        recommendations = []

        # 检查缓存命中率
        for cache_name, stats in metrics['cache_stats'].items():
            hit_rate = float(stats['hit_rate'].rstrip('%'))
            if hit_rate < 70:
                recommendations.append(f"{cache_name} 命中率较低 ({hit_rate:.1f}%), 考虑增加缓存大小")

        # 检查方法执行时间
        for method_name, method_stats in metrics['method_metrics'].items():
            if method_stats.get('execution_time', 0) > 0.1:  # 100ms
                recommendations.append(f"{method_name} 执行时间较长 ({method_stats['execution_time']:.3f}s)")

        return {
            'current_performance': metrics,
            'recommendations': recommendations,
            'optimization_status': 'good' if not recommendations else 'needs_improvement'
        }

# 全局实例
dynamic_workflow_generator = DynamicWorkflowGenerator()

# 便捷函数
def generate_workflow(task_description: str, workflow_type: str = "auto") -> Dict[str, Any]:
    """生成工作流的便捷函数"""
    return dynamic_workflow_generator.generate_workflow(task_description, workflow_type)

def get_workflow_performance_metrics() -> Dict[str, Any]:
    """获取工作流生成器性能指标"""
    return dynamic_workflow_generator.get_performance_metrics()

def optimize_workflow_performance() -> Dict[str, Any]:
    """优化工作流生成器性能"""
    return dynamic_workflow_generator.optimize_performance()