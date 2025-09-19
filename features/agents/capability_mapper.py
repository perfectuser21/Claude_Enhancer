#!/usr/bin/env python3
"""
Perfect21 Agent能力映射器
提供Agent能力评估、技能匹配和动态能力更新功能
"""

import json
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

@dataclass
class SkillLevel:
    """技能水平定义"""
    skill_name: str
    proficiency: float  # 0-10分
    experience_years: float
    certification_level: str = "none"  # none, basic, intermediate, advanced, expert
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class AgentCapabilityProfile:
    """Agent能力档案"""
    agent_name: str
    primary_domain: str
    secondary_domains: List[str]
    core_skills: Dict[str, SkillLevel]
    soft_skills: Dict[str, float]  # 沟通、领导等软技能评分
    performance_metrics: Dict[str, float]
    learning_velocity: float  # 学习新技能的速度
    adaptability_score: float  # 适应性评分
    collaboration_preferences: List[str]
    availability_pattern: Dict[str, float]  # 不同时间段的可用性
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class TaskSkillRequirement:
    """任务技能需求"""
    skill_name: str
    required_level: float  # 0-10分
    importance_weight: float  # 0-1权重
    is_mandatory: bool = True
    alternatives: List[str] = field(default_factory=list)

class SkillTaxonomy:
    """技能分类体系"""

    def __init__(self):
        self.skill_hierarchy = {
            "technical": {
                "programming": {
                    "languages": ["python", "javascript", "java", "go", "rust", "c++"],
                    "frameworks": ["react", "vue", "angular", "django", "flask", "spring"],
                    "tools": ["git", "docker", "kubernetes", "jenkins"]
                },
                "database": {
                    "relational": ["mysql", "postgresql", "oracle", "sql_server"],
                    "nosql": ["mongodb", "redis", "elasticsearch", "cassandra"],
                    "skills": ["query_optimization", "schema_design", "data_modeling"]
                },
                "cloud": {
                    "aws": ["ec2", "s3", "lambda", "rds", "dynamodb"],
                    "azure": ["vm", "blob", "functions", "cosmos_db"],
                    "gcp": ["compute_engine", "cloud_storage", "cloud_functions"]
                },
                "devops": {
                    "ci_cd": ["jenkins", "github_actions", "gitlab_ci", "azure_devops"],
                    "monitoring": ["prometheus", "grafana", "elk_stack", "datadog"],
                    "infrastructure": ["terraform", "ansible", "chef", "puppet"]
                }
            },
            "design": {
                "ui_ux": ["figma", "sketch", "adobe_xd", "prototyping"],
                "graphic": ["photoshop", "illustrator", "after_effects"],
                "web": ["responsive_design", "accessibility", "user_research"]
            },
            "business": {
                "analysis": ["requirements_gathering", "process_modeling", "stakeholder_management"],
                "project_management": ["agile", "scrum", "kanban", "risk_management"],
                "communication": ["presentation", "documentation", "negotiation"]
            },
            "security": {
                "application": ["secure_coding", "penetration_testing", "vulnerability_assessment"],
                "infrastructure": ["network_security", "identity_management", "compliance"],
                "governance": ["risk_assessment", "security_policies", "incident_response"]
            }
        }

        # 技能相似度映射
        self.skill_similarities = self._build_skill_similarity_matrix()

        # 中文技能映射
        self.chinese_skill_mapping = {
            "编程": ["programming", "python", "javascript"],
            "数据库": ["database", "sql", "mysql", "mongodb"],
            "前端": ["frontend", "react", "vue", "html", "css"],
            "后端": ["backend", "api", "server", "database"],
            "运维": ["devops", "docker", "kubernetes", "deployment"],
            "测试": ["testing", "qa", "automation", "selenium"],
            "安全": ["security", "audit", "vulnerability", "compliance"],
            "设计": ["design", "ui", "ux", "figma"],
            "分析": ["analysis", "requirements", "business"],
            "管理": ["management", "project", "team", "leadership"]
        }

    def _build_skill_similarity_matrix(self) -> Dict[str, Dict[str, float]]:
        """构建技能相似度矩阵"""
        similarities = defaultdict(lambda: defaultdict(float))

        # 定义相似技能组
        similar_groups = [
            ["python", "django", "flask"],
            ["javascript", "react", "vue", "angular"],
            ["mysql", "postgresql", "sql"],
            ["mongodb", "redis", "elasticsearch"],
            ["docker", "kubernetes", "containerization"],
            ["aws", "azure", "gcp", "cloud"],
            ["jenkins", "github_actions", "ci_cd"],
            ["figma", "sketch", "design"],
            ["testing", "qa", "quality_assurance"]
        ]

        for group in similar_groups:
            for i, skill1 in enumerate(group):
                for j, skill2 in enumerate(group):
                    if i != j:
                        similarities[skill1][skill2] = 0.8

        return similarities

    def find_similar_skills(self, skill: str, threshold: float = 0.6) -> List[Tuple[str, float]]:
        """查找相似技能"""
        similar = []

        if skill in self.skill_similarities:
            for similar_skill, score in self.skill_similarities[skill].items():
                if score >= threshold:
                    similar.append((similar_skill, score))

        return sorted(similar, key=lambda x: x[1], reverse=True)

    def get_skill_category(self, skill: str) -> Optional[str]:
        """获取技能所属类别"""
        def search_category(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key
                    if isinstance(value, list) and skill.lower() in [s.lower() for s in value]:
                        return new_path
                    result = search_category(value, new_path)
                    if result:
                        return result
            return None

        return search_category(self.skill_hierarchy)

class CapabilityMatcher:
    """能力匹配器"""

    def __init__(self):
        self.taxonomy = SkillTaxonomy()
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.agent_profiles: Dict[str, AgentCapabilityProfile] = {}

    def add_agent_profile(self, profile: AgentCapabilityProfile):
        """添加Agent能力档案"""
        self.agent_profiles[profile.agent_name] = profile
        logger.info(f"Added capability profile for agent: {profile.agent_name}")

    def calculate_skill_match_score(self,
                                  agent_skills: Dict[str, SkillLevel],
                                  task_requirements: List[TaskSkillRequirement]) -> float:
        """计算技能匹配分数"""
        if not task_requirements:
            return 1.0

        total_weighted_score = 0.0
        total_weight = 0.0

        for requirement in task_requirements:
            skill_name = requirement.skill_name.lower()
            required_level = requirement.required_level
            weight = requirement.importance_weight

            # 直接匹配
            match_score = 0.0
            if skill_name in agent_skills:
                agent_level = agent_skills[skill_name].proficiency
                match_score = min(agent_level / required_level, 1.0) if required_level > 0 else 1.0

            # 相似技能匹配
            if match_score == 0.0:
                similar_skills = self.taxonomy.find_similar_skills(skill_name)
                for similar_skill, similarity in similar_skills[:3]:  # 检查前3个相似技能
                    if similar_skill in agent_skills:
                        agent_level = agent_skills[similar_skill].proficiency
                        adjusted_score = min(agent_level / required_level, 1.0) * similarity
                        match_score = max(match_score, adjusted_score)

            # 替代技能匹配
            for alternative in requirement.alternatives:
                if alternative.lower() in agent_skills:
                    agent_level = agent_skills[alternative.lower()].proficiency
                    alt_score = min(agent_level / required_level, 1.0) * 0.8  # 替代技能打8折
                    match_score = max(match_score, alt_score)

            # 强制要求处理
            if requirement.is_mandatory and match_score < 0.5:
                return 0.0  # 不满足强制要求，直接返回0分

            total_weighted_score += match_score * weight
            total_weight += weight

        return total_weighted_score / total_weight if total_weight > 0 else 0.0

    def calculate_domain_alignment(self, agent_profile: AgentCapabilityProfile, task_domain: str) -> float:
        """计算领域对齐度"""
        alignment_score = 0.0

        # 主要领域完全匹配
        if agent_profile.primary_domain.lower() == task_domain.lower():
            alignment_score = 1.0
        # 次要领域匹配
        elif task_domain.lower() in [d.lower() for d in agent_profile.secondary_domains]:
            alignment_score = 0.7
        # 相关领域匹配
        else:
            related_domains = {
                "technical": ["backend", "frontend", "database", "api"],
                "business": ["analysis", "management", "strategy"],
                "design": ["ui", "ux", "graphic"],
                "security": ["audit", "compliance", "risk"],
                "infrastructure": ["devops", "cloud", "deployment"]
            }

            for domain_group, related in related_domains.items():
                if (agent_profile.primary_domain.lower() in related and
                    task_domain.lower() in related):
                    alignment_score = 0.5
                    break

        return alignment_score

    def find_best_agent_matches(self,
                              task_requirements: List[TaskSkillRequirement],
                              task_domain: str = "general",
                              count: int = 5,
                              filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """找到最佳Agent匹配"""
        matches = []

        for agent_name, profile in self.agent_profiles.items():
            # 应用过滤器
            if filters and not self._apply_filters(profile, filters):
                continue

            # 计算技能匹配分数
            skill_score = self.calculate_skill_match_score(profile.core_skills, task_requirements)

            # 计算领域对齐度
            domain_score = self.calculate_domain_alignment(profile, task_domain)

            # 综合评分
            composite_score = (
                skill_score * 0.6 +
                domain_score * 0.2 +
                profile.performance_metrics.get('success_rate', 80) / 100 * 0.1 +
                profile.adaptability_score / 10 * 0.1
            )

            matches.append({
                'agent_name': agent_name,
                'composite_score': composite_score,
                'skill_match_score': skill_score,
                'domain_alignment_score': domain_score,
                'performance_score': profile.performance_metrics.get('success_rate', 80) / 100,
                'adaptability_score': profile.adaptability_score / 10,
                'profile': profile
            })

        # 按综合评分排序
        matches.sort(key=lambda x: x['composite_score'], reverse=True)

        return matches[:count]

    def _apply_filters(self, profile: AgentCapabilityProfile, filters: Dict[str, Any]) -> bool:
        """应用过滤条件"""
        # 可用性过滤
        if 'availability_required' in filters:
            required_availability = filters['availability_required']
            current_hour = datetime.now().hour
            if profile.availability_pattern.get(str(current_hour), 1.0) < required_availability:
                return False

        # 最小性能要求过滤
        if 'min_performance' in filters:
            min_performance = filters['min_performance']
            if profile.performance_metrics.get('success_rate', 0) < min_performance:
                return False

        # 技能认证级别过滤
        if 'required_certifications' in filters:
            required_certs = filters['required_certifications']
            for skill_name, required_level in required_certs.items():
                if skill_name in profile.core_skills:
                    cert_levels = {"none": 0, "basic": 1, "intermediate": 2, "advanced": 3, "expert": 4}
                    skill_cert_level = cert_levels.get(profile.core_skills[skill_name].certification_level, 0)
                    if skill_cert_level < cert_levels.get(required_level, 0):
                        return False

        return True

    def generate_skill_gap_analysis(self,
                                  agent_name: str,
                                  task_requirements: List[TaskSkillRequirement]) -> Dict[str, Any]:
        """生成技能差距分析"""
        if agent_name not in self.agent_profiles:
            return {"error": f"Agent {agent_name} not found"}

        profile = self.agent_profiles[agent_name]
        gaps = []
        strengths = []

        for requirement in task_requirements:
            skill_name = requirement.skill_name.lower()
            required_level = requirement.required_level

            current_level = 0.0
            if skill_name in profile.core_skills:
                current_level = profile.core_skills[skill_name].proficiency

            gap = required_level - current_level

            if gap > 1.0:  # 显著差距
                gaps.append({
                    'skill': skill_name,
                    'current_level': current_level,
                    'required_level': required_level,
                    'gap': gap,
                    'priority': requirement.importance_weight,
                    'is_mandatory': requirement.is_mandatory
                })
            elif gap <= 0:  # 超出要求或满足要求
                strengths.append({
                    'skill': skill_name,
                    'current_level': current_level,
                    'required_level': required_level,
                    'surplus': abs(gap)
                })

        # 生成学习建议
        learning_recommendations = self._generate_learning_recommendations(profile, gaps)

        return {
            'agent_name': agent_name,
            'skill_gaps': sorted(gaps, key=lambda x: x['gap'], reverse=True),
            'skill_strengths': sorted(strengths, key=lambda x: x['surplus'], reverse=True),
            'learning_recommendations': learning_recommendations,
            'overall_readiness': self.calculate_skill_match_score(profile.core_skills, task_requirements),
            'analysis_date': datetime.now().isoformat()
        }

    def _generate_learning_recommendations(self,
                                         profile: AgentCapabilityProfile,
                                         gaps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成学习建议"""
        recommendations = []

        for gap in gaps[:5]:  # 只处理前5个最重要的差距
            skill_name = gap['skill']
            gap_size = gap['gap']

            # 估算学习时间
            learning_time = gap_size * 10 / profile.learning_velocity  # 天数

            # 查找学习路径
            similar_skills = self.taxonomy.find_similar_skills(skill_name)
            prerequisite_skills = [skill for skill, _ in similar_skills[:3]]

            recommendation = {
                'skill': skill_name,
                'priority': 'high' if gap['is_mandatory'] else 'medium',
                'estimated_learning_time_days': learning_time,
                'recommended_approach': self._get_learning_approach(skill_name, gap_size),
                'prerequisite_skills': prerequisite_skills,
                'resources': self._get_learning_resources(skill_name)
            }

            recommendations.append(recommendation)

        return recommendations

    def _get_learning_approach(self, skill_name: str, gap_size: float) -> str:
        """获取学习方法建议"""
        if gap_size > 5.0:
            return "intensive_course"
        elif gap_size > 3.0:
            return "structured_practice"
        else:
            return "targeted_improvement"

    def _get_learning_resources(self, skill_name: str) -> List[str]:
        """获取学习资源建议"""
        resource_mapping = {
            "python": ["Python官方文档", "Coursera Python课程", "LeetCode练习"],
            "javascript": ["MDN Web Docs", "JavaScript.info", "NodeSchool"],
            "react": ["React官方教程", "React Training", "Egghead.io"],
            "database": ["SQL教程", "数据库设计原理", "实战项目"],
            "docker": ["Docker官方文档", "Docker实战", "在线练习平台"],
        }

        return resource_mapping.get(skill_name, ["在线教程", "实践项目", "社区论坛"])

    def update_agent_performance(self, agent_name: str, performance_data: Dict[str, float]):
        """更新Agent性能数据"""
        if agent_name in self.agent_profiles:
            profile = self.agent_profiles[agent_name]
            profile.performance_metrics.update(performance_data)
            profile.last_updated = datetime.now()

            # 自动调整技能水平
            if 'task_success_rate' in performance_data:
                success_rate = performance_data['task_success_rate']
                if success_rate > 90:
                    # 成功率高，提升相关技能
                    for skill in profile.core_skills.values():
                        skill.proficiency = min(skill.proficiency + 0.1, 10.0)

            logger.info(f"Updated performance data for agent: {agent_name}")

# 全局实例
capability_mapper = CapabilityMatcher()

# 便捷函数
def find_best_agents(task_requirements: List[TaskSkillRequirement],
                    task_domain: str = "general",
                    count: int = 5) -> List[Dict[str, Any]]:
    """查找最佳Agent匹配的便捷函数"""
    return capability_mapper.find_best_agent_matches(task_requirements, task_domain, count)

def analyze_skill_gaps(agent_name: str, task_requirements: List[TaskSkillRequirement]) -> Dict[str, Any]:
    """分析技能差距的便捷函数"""
    return capability_mapper.generate_skill_gap_analysis(agent_name, task_requirements)