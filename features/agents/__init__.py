#!/usr/bin/env python3
"""
Perfect21 Agent管理模块
提供智能Agent选择、协作优化和任务匹配功能
"""

from .smart_agent_selector import (
    SmartAgentSelector,
    AgentProfile,
    TaskSemantics,
    ChineseSemanticAnalyzer,
    SuccessPatternLibrary,
    smart_agent_selector,
    select_agents,
    get_agent_recommendations,
    get_selector_stats
)

from .collaboration_optimizer import (
    CollaborationOptimizer,
    CollaborationNetwork,
    ConflictDetector,
    CollaborationRecord,
    AgentWorkload,
    collaboration_optimizer,
    optimize_team_collaboration,
    add_collaboration_feedback,
    get_collaboration_insights
)

from .capability_mapper import (
    CapabilityMatcher,
    SkillTaxonomy,
    AgentCapabilityProfile,
    TaskSkillRequirement,
    SkillLevel,
    capability_mapper,
    find_best_agents,
    analyze_skill_gaps
)

__all__ = [
    # 智能选择器
    'SmartAgentSelector',
    'AgentProfile',
    'TaskSemantics',
    'ChineseSemanticAnalyzer',
    'SuccessPatternLibrary',
    'smart_agent_selector',
    'select_agents',
    'get_agent_recommendations',
    'get_selector_stats',

    # 协作优化器
    'CollaborationOptimizer',
    'CollaborationNetwork',
    'ConflictDetector',
    'CollaborationRecord',
    'AgentWorkload',
    'collaboration_optimizer',
    'optimize_team_collaboration',
    'add_collaboration_feedback',
    'get_collaboration_insights',

    # 能力映射器
    'CapabilityMatcher',
    'SkillTaxonomy',
    'AgentCapabilityProfile',
    'TaskSkillRequirement',
    'SkillLevel',
    'capability_mapper',
    'find_best_agents',
    'analyze_skill_gaps'
]

# 版本信息
__version__ = "1.0.0"

# 模块描述
__description__ = """
Perfect21 Agent管理模块提供以下核心功能：

1. 智能Agent选择 (80%+准确率)
   - 中文语义分析和关键词匹配
   - 成功模式库匹配
   - 多维度评分算法

2. 协作优化
   - 冲突检测和解决
   - 团队协同效应计算
   - 工作负载平衡

3. 任务匹配
   - 技能匹配算法
   - 复杂度适配
   - 优先级调度
"""