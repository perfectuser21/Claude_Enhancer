#!/usr/bin/env python3
"""
Phase Summarizer - 阶段汇总器
汇总多个agent的执行结果，生成下一阶段的任务
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger("PhaseSummarizer")

class PhaseSummarizer:
    """
    阶段结果汇总和TODO生成

    功能：
    1. 汇总多个agent的执行结果
    2. 提取关键信息和共识
    3. 识别分歧和冲突
    4. 生成下一阶段的TODO
    """

    def __init__(self):
        self.summaries = {}
        self.todos_generated = {}
        logger.info("PhaseSummarizer初始化完成")

    def summarize_phase_results(self, phase_id: str, agent_results: List[Dict]) -> Dict[str, Any]:
        """
        汇总阶段执行结果

        Args:
            phase_id: 阶段标识
            agent_results: 各agent的执行结果列表

        Returns:
            汇总后的结果
        """
        summary = {
            'phase_id': phase_id,
            'timestamp': datetime.now().isoformat(),
            'total_agents': len(agent_results),
            'key_findings': [],
            'consensus_points': [],
            'divergence_points': [],
            'critical_issues': [],
            'recommendations': [],
            'aggregated_data': {}
        }

        # 提取各agent的关键信息
        for result in agent_results:
            agent_name = result.get('agent', 'unknown')

            # 提取关键发现
            if 'key_findings' in result:
                for finding in result['key_findings']:
                    summary['key_findings'].append({
                        'agent': agent_name,
                        'finding': finding
                    })

            # 提取关键问题
            if 'issues' in result:
                for issue in result['issues']:
                    summary['critical_issues'].append({
                        'agent': agent_name,
                        'issue': issue,
                        'severity': result.get('severity', 'medium')
                    })

            # 提取建议
            if 'recommendations' in result:
                summary['recommendations'].extend(result['recommendations'])

        # 分析共识和分歧
        consensus, divergence = self._analyze_agreement(agent_results)
        summary['consensus_points'] = consensus
        summary['divergence_points'] = divergence

        # 按重要性排序
        summary['critical_issues'].sort(key=lambda x: self._severity_score(x['severity']), reverse=True)

        # 保存汇总
        self.summaries[phase_id] = summary

        logger.info(f"完成{phase_id}阶段汇总，发现{len(summary['key_findings'])}个关键点")

        return summary

    def generate_next_phase_todos(self, current_phase: str, summary: Dict) -> List[Dict]:
        """
        基于汇总生成下一阶段TODO

        Args:
            current_phase: 当前阶段
            summary: 阶段汇总

        Returns:
            下一阶段的TODO列表
        """
        todos = []

        # 根据不同阶段生成相应的TODO
        if current_phase == 'analysis':
            todos = self._generate_design_todos(summary)
        elif current_phase == 'design':
            todos = self._generate_implementation_todos(summary)
        elif current_phase == 'implementation':
            todos = self._generate_testing_todos(summary)
        elif current_phase == 'testing':
            todos = self._generate_deployment_todos(summary)

        # 添加解决关键问题的TODO
        for issue in summary.get('critical_issues', []):
            if self._severity_score(issue['severity']) >= 3:
                todos.append({
                    'task': f"解决{issue['agent']}发现的问题: {issue['issue']}",
                    'priority': 'high',
                    'assigned_agent': self._get_resolver_agent(issue),
                    'type': 'fix'
                })

        # 保存生成的TODO
        self.todos_generated[current_phase] = todos

        logger.info(f"为{current_phase}生成了{len(todos)}个下阶段TODO")

        return todos

    def _generate_design_todos(self, summary: Dict) -> List[Dict]:
        """生成设计阶段的TODO"""
        todos = []

        # 基于需求分析结果生成设计任务
        for finding in summary.get('key_findings', []):
            if 'requirement' in finding.get('finding', '').lower():
                todos.append({
                    'task': f"设计满足需求的架构方案",
                    'priority': 'high',
                    'assigned_agent': 'backend-architect',
                    'type': 'design'
                })
                break

        # 标准设计任务
        todos.extend([
            {
                'task': '设计API接口规范',
                'priority': 'high',
                'assigned_agent': 'api-designer',
                'type': 'design'
            },
            {
                'task': '设计数据库架构',
                'priority': 'high',
                'assigned_agent': 'database-specialist',
                'type': 'design'
            },
            {
                'task': '设计系统架构图',
                'priority': 'medium',
                'assigned_agent': 'backend-architect',
                'type': 'design'
            }
        ])

        return todos

    def _generate_implementation_todos(self, summary: Dict) -> List[Dict]:
        """生成实现阶段的TODO"""
        todos = []

        # 基于设计结果生成实现任务
        if 'api_spec' in summary.get('aggregated_data', {}):
            todos.append({
                'task': '实现API接口',
                'priority': 'high',
                'assigned_agent': 'backend-architect',
                'type': 'implementation'
            })

        if 'database_schema' in summary.get('aggregated_data', {}):
            todos.append({
                'task': '实现数据库访问层',
                'priority': 'high',
                'assigned_agent': 'database-specialist',
                'type': 'implementation'
            })

        # 标准实现任务
        todos.extend([
            {
                'task': '实现业务逻辑',
                'priority': 'high',
                'assigned_agent': 'backend-architect',
                'type': 'implementation'
            },
            {
                'task': '实现前端界面',
                'priority': 'medium',
                'assigned_agent': 'frontend-specialist',
                'type': 'implementation'
            },
            {
                'task': '编写单元测试',
                'priority': 'high',
                'assigned_agent': 'test-engineer',
                'type': 'testing'
            }
        ])

        return todos

    def _generate_testing_todos(self, summary: Dict) -> List[Dict]:
        """生成测试阶段的TODO"""
        todos = [
            {
                'task': '执行功能测试',
                'priority': 'high',
                'assigned_agent': 'test-engineer',
                'type': 'testing'
            },
            {
                'task': '执行安全审计',
                'priority': 'high',
                'assigned_agent': 'security-auditor',
                'type': 'security'
            },
            {
                'task': '执行性能测试',
                'priority': 'medium',
                'assigned_agent': 'performance-engineer',
                'type': 'performance'
            },
            {
                'task': '生成测试报告',
                'priority': 'low',
                'assigned_agent': 'test-engineer',
                'type': 'documentation'
            }
        ]

        # 根据实现阶段的问题添加特定测试
        for issue in summary.get('critical_issues', []):
            if 'security' in issue['issue'].lower():
                todos.insert(0, {
                    'task': f"针对安全问题的专项测试: {issue['issue']}",
                    'priority': 'critical',
                    'assigned_agent': 'security-auditor',
                    'type': 'security'
                })

        return todos

    def _generate_deployment_todos(self, summary: Dict) -> List[Dict]:
        """生成部署阶段的TODO"""
        todos = [
            {
                'task': '准备部署环境',
                'priority': 'high',
                'assigned_agent': 'devops-engineer',
                'type': 'deployment'
            },
            {
                'task': '配置监控告警',
                'priority': 'high',
                'assigned_agent': 'monitoring-specialist',
                'type': 'monitoring'
            },
            {
                'task': '执行部署流程',
                'priority': 'high',
                'assigned_agent': 'deployment-manager',
                'type': 'deployment'
            },
            {
                'task': '验证部署结果',
                'priority': 'high',
                'assigned_agent': 'devops-engineer',
                'type': 'validation'
            }
        ]

        return todos

    def _analyze_agreement(self, agent_results: List[Dict]) -> tuple:
        """分析agent间的共识和分歧"""
        consensus = []
        divergence = []

        # 收集所有agent的观点
        opinions = {}
        for result in agent_results:
            agent_name = result.get('agent', 'unknown')
            for key, value in result.items():
                if key not in ['agent', 'timestamp', 'metadata']:
                    if key not in opinions:
                        opinions[key] = []
                    opinions[key].append({
                        'agent': agent_name,
                        'value': value
                    })

        # 分析共识和分歧
        for key, agent_opinions in opinions.items():
            unique_values = set(str(op['value']) for op in agent_opinions)

            if len(unique_values) == 1:
                # 所有agent意见一致
                consensus.append({
                    'topic': key,
                    'agreement': agent_opinions[0]['value'],
                    'agents': [op['agent'] for op in agent_opinions]
                })
            elif len(unique_values) > 1:
                # 存在分歧
                divergence.append({
                    'topic': key,
                    'opinions': agent_opinions,
                    'unique_values': list(unique_values)
                })

        return consensus, divergence

    def _severity_score(self, severity: str) -> int:
        """获取严重程度分数"""
        severity_map = {
            'critical': 5,
            'high': 4,
            'medium': 3,
            'low': 2,
            'info': 1
        }
        return severity_map.get(severity.lower(), 2)

    def _get_resolver_agent(self, issue: Dict) -> str:
        """根据问题类型获取解决问题的agent"""
        issue_text = issue.get('issue', '').lower()

        if 'security' in issue_text:
            return 'security-auditor'
        elif 'performance' in issue_text:
            return 'performance-engineer'
        elif 'test' in issue_text:
            return 'test-engineer'
        elif 'api' in issue_text:
            return 'api-designer'
        elif 'database' in issue_text:
            return 'database-specialist'
        else:
            return 'backend-architect'

    def get_phase_summary(self, phase_id: str) -> Optional[Dict]:
        """获取阶段汇总"""
        return self.summaries.get(phase_id)

    def get_generated_todos(self, phase_id: str) -> List[Dict]:
        """获取生成的TODO"""
        return self.todos_generated.get(phase_id, [])

    def generate_final_report(self) -> Dict[str, Any]:
        """生成最终报告"""
        report = {
            'total_phases': len(self.summaries),
            'phases': self.summaries,
            'todos_generated': self.todos_generated,
            'overall_findings': [],
            'overall_issues': [],
            'timestamp': datetime.now().isoformat()
        }

        # 汇总所有阶段的发现和问题
        for phase_id, summary in self.summaries.items():
            report['overall_findings'].extend(summary.get('key_findings', []))
            report['overall_issues'].extend(summary.get('critical_issues', []))

        return report