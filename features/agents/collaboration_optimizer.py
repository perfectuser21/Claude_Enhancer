#!/usr/bin/env python3
"""
Perfect21 Agent协作优化器
实现智能的Agent组合推荐、冲突检测和协作效率优化
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime, timedelta
import networkx as nx
from itertools import combinations

logger = logging.getLogger(__name__)

@dataclass
class CollaborationRecord:
    """协作记录"""
    agent1: str
    agent2: str
    task_type: str
    success: bool
    duration: float
    quality_score: float
    created_at: datetime
    feedback: str = ""

@dataclass
class AgentWorkload:
    """Agent工作负载"""
    agent_name: str
    current_tasks: int
    max_capacity: int
    efficiency_score: float
    last_task_completion: Optional[datetime]
    stress_level: float = 0.0

class CollaborationNetwork:
    """Agent协作网络分析"""

    def __init__(self):
        self.graph = nx.Graph()
        self.collaboration_history: List[CollaborationRecord] = []
        self.success_patterns: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))

    def add_collaboration_record(self, record: CollaborationRecord):
        """添加协作记录"""
        self.collaboration_history.append(record)

        # 更新协作网络
        if not self.graph.has_edge(record.agent1, record.agent2):
            self.graph.add_edge(record.agent1, record.agent2, weight=0, success_count=0, total_count=0)

        edge_data = self.graph[record.agent1][record.agent2]
        edge_data['total_count'] += 1

        if record.success:
            edge_data['success_count'] += 1
            edge_data['weight'] = edge_data['success_count'] / edge_data['total_count']

        # 更新成功模式
        pattern_key = f"{record.task_type}_{min(record.agent1, record.agent2)}_{max(record.agent1, record.agent2)}"
        if record.success:
            self.success_patterns[record.task_type][pattern_key] += record.quality_score

    def get_collaboration_strength(self, agent1: str, agent2: str) -> float:
        """获取两个Agent的协作强度"""
        if self.graph.has_edge(agent1, agent2):
            return self.graph[agent1][agent2].get('weight', 0)
        return 0.5  # 默认中等协作强度

    def find_optimal_team(self, agents: List[str], team_size: int = 3) -> List[str]:
        """找到最优团队组合"""
        if len(agents) <= team_size:
            return agents

        best_team = []
        best_score = 0

        # 尝试所有可能的组合
        for team in combinations(agents, team_size):
            score = self._calculate_team_synergy(list(team))
            if score > best_score:
                best_score = score
                best_team = list(team)

        return best_team if best_team else agents[:team_size]

    def _calculate_team_synergy(self, team: List[str]) -> float:
        """计算团队协同效应"""
        if len(team) < 2:
            return 0

        total_synergy = 0
        pair_count = 0

        for i in range(len(team)):
            for j in range(i + 1, len(team)):
                synergy = self.get_collaboration_strength(team[i], team[j])
                total_synergy += synergy
                pair_count += 1

        return total_synergy / pair_count if pair_count > 0 else 0

class ConflictDetector:
    """Agent冲突检测器"""

    def __init__(self):
        # 定义已知的冲突模式
        self.conflict_patterns = {
            'skill_overlap': {
                'description': '技能重叠过多，可能造成资源浪费',
                'severity': 'medium',
                'resolution': '保留最专业的Agent，其他Agent分配不同任务'
            },
            'workload_imbalance': {
                'description': '工作负载不平衡',
                'severity': 'high',
                'resolution': '重新分配任务或增加支援Agent'
            },
            'communication_mismatch': {
                'description': '沟通方式不匹配',
                'severity': 'low',
                'resolution': '建立清晰的沟通协议'
            },
            'priority_conflict': {
                'description': '优先级冲突',
                'severity': 'high',
                'resolution': '明确任务优先级和时间线'
            }
        }

        # Agent兼容性矩阵
        self.compatibility_matrix = {
            'backend-architect': {
                'compatible': ['api-designer', 'database-specialist', 'security-auditor'],
                'neutral': ['frontend-specialist', 'test-engineer'],
                'conflicting': []
            },
            'frontend-specialist': {
                'compatible': ['ux-designer', 'accessibility-auditor'],
                'neutral': ['backend-architect', 'test-engineer'],
                'conflicting': []
            },
            'devops-engineer': {
                'compatible': ['backend-architect', 'monitoring-specialist'],
                'neutral': ['frontend-specialist'],
                'conflicting': ['database-specialist']  # 可能在部署策略上有分歧
            }
        }

    def detect_conflicts(self, agent_team: List[str], workloads: Dict[str, AgentWorkload] = None) -> List[Dict[str, Any]]:
        """检测Agent团队中的潜在冲突"""
        conflicts = []

        # 检查技能重叠
        skill_conflicts = self._detect_skill_overlap(agent_team)
        conflicts.extend(skill_conflicts)

        # 检查兼容性冲突
        compatibility_conflicts = self._detect_compatibility_issues(agent_team)
        conflicts.extend(compatibility_conflicts)

        # 检查工作负载冲突
        if workloads:
            workload_conflicts = self._detect_workload_conflicts(agent_team, workloads)
            conflicts.extend(workload_conflicts)

        return conflicts

    def _detect_skill_overlap(self, agent_team: List[str]) -> List[Dict[str, Any]]:
        """检测技能重叠"""
        conflicts = []

        # 这里需要访问Agent的技能信息
        # 暂时使用简化逻辑
        similar_agents = [
            ('backend-architect', 'fullstack-engineer'),
            ('frontend-specialist', 'react-pro'),
            ('test-engineer', 'qa-specialist')
        ]

        for agent1, agent2 in similar_agents:
            if agent1 in agent_team and agent2 in agent_team:
                conflicts.append({
                    'type': 'skill_overlap',
                    'agents': [agent1, agent2],
                    'severity': 'medium',
                    'description': f'{agent1} 和 {agent2} 技能重叠较多',
                    'recommendation': f'考虑保留更专业的 {agent1}，让 {agent2} 处理其他任务'
                })

        return conflicts

    def _detect_compatibility_issues(self, agent_team: List[str]) -> List[Dict[str, Any]]:
        """检测兼容性问题"""
        conflicts = []

        for agent in agent_team:
            if agent in self.compatibility_matrix:
                conflicting_agents = self.compatibility_matrix[agent]['conflicting']
                for conflict_agent in conflicting_agents:
                    if conflict_agent in agent_team:
                        conflicts.append({
                            'type': 'compatibility_conflict',
                            'agents': [agent, conflict_agent],
                            'severity': 'high',
                            'description': f'{agent} 和 {conflict_agent} 在工作方式上可能存在冲突',
                            'recommendation': '需要明确分工界限或引入协调机制'
                        })

        return conflicts

    def _detect_workload_conflicts(self, agent_team: List[str], workloads: Dict[str, AgentWorkload]) -> List[Dict[str, Any]]:
        """检测工作负载冲突"""
        conflicts = []

        for agent in agent_team:
            if agent in workloads:
                workload = workloads[agent]

                # 检查工作负载过高
                if workload.current_tasks > workload.max_capacity * 0.9:
                    conflicts.append({
                        'type': 'workload_overload',
                        'agents': [agent],
                        'severity': 'high',
                        'description': f'{agent} 当前工作负载过高 ({workload.current_tasks}/{workload.max_capacity})',
                        'recommendation': '考虑减少任务分配或提供支援'
                    })

                # 检查压力水平
                if workload.stress_level > 0.8:
                    conflicts.append({
                        'type': 'high_stress',
                        'agents': [agent],
                        'severity': 'medium',
                        'description': f'{agent} 压力水平过高 ({workload.stress_level:.1%})',
                        'recommendation': '建议安排休息时间或降低任务复杂度'
                    })

        return conflicts

class CollaborationOptimizer:
    """协作优化器主类"""

    def __init__(self):
        self.network = CollaborationNetwork()
        self.conflict_detector = ConflictDetector()
        self.workload_tracker: Dict[str, AgentWorkload] = {}

        # 优化策略配置
        self.optimization_config = {
            'max_team_size': 5,
            'min_team_size': 3,
            'preferred_team_size': 4,
            'synergy_threshold': 0.7,
            'conflict_tolerance': 0.3
        }

    def optimize_agent_collaboration(self,
                                   candidate_agents: List[str],
                                   task_type: str = 'general',
                                   constraints: Dict[str, Any] = None) -> Dict[str, Any]:
        """优化Agent协作"""
        constraints = constraints or {}

        # 1. 检测和解决冲突
        conflicts = self.conflict_detector.detect_conflicts(candidate_agents, self.workload_tracker)

        # 2. 找到最优团队
        optimal_team = self.network.find_optimal_team(
            candidate_agents,
            constraints.get('team_size', self.optimization_config['preferred_team_size'])
        )

        # 3. 计算团队指标
        team_synergy = self.network._calculate_team_synergy(optimal_team)

        # 4. 生成优化建议
        recommendations = self._generate_recommendations(optimal_team, conflicts, task_type)

        return {
            'optimized_team': optimal_team,
            'team_synergy_score': team_synergy,
            'detected_conflicts': conflicts,
            'recommendations': recommendations,
            'optimization_metadata': {
                'original_team_size': len(candidate_agents),
                'optimized_team_size': len(optimal_team),
                'conflict_count': len(conflicts),
                'optimization_timestamp': datetime.now().isoformat()
            }
        }

    def _generate_recommendations(self,
                                team: List[str],
                                conflicts: List[Dict[str, Any]],
                                task_type: str) -> List[Dict[str, Any]]:
        """生成协作优化建议"""
        recommendations = []

        # 基于冲突的建议
        for conflict in conflicts:
            if conflict['severity'] == 'high':
                recommendations.append({
                    'type': 'conflict_resolution',
                    'priority': 'high',
                    'description': conflict['description'],
                    'action': conflict.get('recommendation', '需要人工介入解决'),
                    'affected_agents': conflict['agents']
                })

        # 基于协作历史的建议
        historical_recommendations = self._get_historical_recommendations(team, task_type)
        recommendations.extend(historical_recommendations)

        # 基于工作负载的建议
        workload_recommendations = self._get_workload_recommendations(team)
        recommendations.extend(workload_recommendations)

        return recommendations

    def _get_historical_recommendations(self, team: List[str], task_type: str) -> List[Dict[str, Any]]:
        """基于历史协作数据的建议"""
        recommendations = []

        # 查找成功的协作模式
        if task_type in self.network.success_patterns:
            patterns = self.network.success_patterns[task_type]

            for pattern_key, success_score in patterns.items():
                if success_score > 8.0:  # 高成功分数
                    recommendations.append({
                        'type': 'success_pattern',
                        'priority': 'medium',
                        'description': f'发现{task_type}任务的高成功率协作模式',
                        'action': f'建议保持当前团队配置，历史成功率{success_score:.1f}/10',
                        'success_score': success_score
                    })

        return recommendations

    def _get_workload_recommendations(self, team: List[str]) -> List[Dict[str, Any]]:
        """基于工作负载的建议"""
        recommendations = []

        high_load_agents = []
        low_load_agents = []

        for agent in team:
            if agent in self.workload_tracker:
                workload = self.workload_tracker[agent]
                load_ratio = workload.current_tasks / workload.max_capacity

                if load_ratio > 0.8:
                    high_load_agents.append(agent)
                elif load_ratio < 0.3:
                    low_load_agents.append(agent)

        if high_load_agents and low_load_agents:
            recommendations.append({
                'type': 'load_balancing',
                'priority': 'medium',
                'description': '团队内工作负载不平衡',
                'action': f'建议将部分任务从{high_load_agents}转移给{low_load_agents}',
                'affected_agents': high_load_agents + low_load_agents
            })

        return recommendations

    def update_workload(self, agent_name: str, workload_data: Dict[str, Any]):
        """更新Agent工作负载"""
        if agent_name not in self.workload_tracker:
            self.workload_tracker[agent_name] = AgentWorkload(
                agent_name=agent_name,
                current_tasks=0,
                max_capacity=10,
                efficiency_score=100.0,
                last_task_completion=None
            )

        workload = self.workload_tracker[agent_name]

        if 'current_tasks' in workload_data:
            workload.current_tasks = workload_data['current_tasks']
        if 'efficiency_score' in workload_data:
            workload.efficiency_score = workload_data['efficiency_score']
        if 'stress_level' in workload_data:
            workload.stress_level = workload_data['stress_level']

    def add_collaboration_feedback(self,
                                 agent1: str,
                                 agent2: str,
                                 task_type: str,
                                 success: bool,
                                 duration: float,
                                 quality_score: float,
                                 feedback: str = ""):
        """添加协作反馈"""
        record = CollaborationRecord(
            agent1=agent1,
            agent2=agent2,
            task_type=task_type,
            success=success,
            duration=duration,
            quality_score=quality_score,
            created_at=datetime.now(),
            feedback=feedback
        )

        self.network.add_collaboration_record(record)

    def get_collaboration_insights(self) -> Dict[str, Any]:
        """获取协作洞察"""
        total_collaborations = len(self.network.collaboration_history)
        successful_collaborations = sum(1 for r in self.network.collaboration_history if r.success)

        # 最佳协作对
        best_pairs = []
        for agent1, agent2, data in self.network.graph.edges(data=True):
            if data.get('total_count', 0) >= 3:  # 至少协作3次
                success_rate = data.get('weight', 0)
                best_pairs.append({
                    'agents': [agent1, agent2],
                    'success_rate': success_rate,
                    'total_collaborations': data.get('total_count', 0)
                })

        best_pairs.sort(key=lambda x: x['success_rate'], reverse=True)

        # 工作负载摘要
        workload_summary = {}
        for agent, workload in self.workload_tracker.items():
            workload_summary[agent] = {
                'load_ratio': workload.current_tasks / workload.max_capacity,
                'efficiency': workload.efficiency_score,
                'stress_level': workload.stress_level
            }

        return {
            'total_collaborations': total_collaborations,
            'success_rate': (successful_collaborations / total_collaborations * 100) if total_collaborations > 0 else 0,
            'best_collaboration_pairs': best_pairs[:5],
            'network_size': self.network.graph.number_of_nodes(),
            'network_density': nx.density(self.network.graph),
            'workload_summary': workload_summary,
            'insights_generated_at': datetime.now().isoformat()
        }

    def export_collaboration_data(self, filepath: str):
        """导出协作数据"""
        data = {
            'collaboration_history': [
                {
                    'agent1': r.agent1,
                    'agent2': r.agent2,
                    'task_type': r.task_type,
                    'success': r.success,
                    'duration': r.duration,
                    'quality_score': r.quality_score,
                    'created_at': r.created_at.isoformat(),
                    'feedback': r.feedback
                }
                for r in self.network.collaboration_history
            ],
            'workload_data': {
                agent: {
                    'current_tasks': w.current_tasks,
                    'max_capacity': w.max_capacity,
                    'efficiency_score': w.efficiency_score,
                    'stress_level': w.stress_level,
                    'last_task_completion': w.last_task_completion.isoformat() if w.last_task_completion else None
                }
                for agent, w in self.workload_tracker.items()
            },
            'export_timestamp': datetime.now().isoformat()
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

# 全局实例
collaboration_optimizer = CollaborationOptimizer()

# 便捷函数
def optimize_team_collaboration(candidate_agents: List[str],
                              task_type: str = 'general',
                              constraints: Dict[str, Any] = None) -> Dict[str, Any]:
    """优化团队协作的便捷函数"""
    return collaboration_optimizer.optimize_agent_collaboration(candidate_agents, task_type, constraints)

def add_collaboration_feedback(agent1: str, agent2: str, task_type: str,
                             success: bool, duration: float, quality_score: float):
    """添加协作反馈的便捷函数"""
    collaboration_optimizer.add_collaboration_feedback(agent1, agent2, task_type, success, duration, quality_score)

def get_collaboration_insights() -> Dict[str, Any]:
    """获取协作洞察的便捷函数"""
    return collaboration_optimizer.get_collaboration_insights()