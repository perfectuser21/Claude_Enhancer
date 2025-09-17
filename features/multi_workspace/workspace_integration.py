#!/usr/bin/env python3
"""
Perfect21 工作空间集成器
======================

与Claude Code和其他Perfect21功能的集成接口
提供无缝的多工作空间开发体验
"""

import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

from .workspace_manager import WorkspaceManager, WorkspaceType, WorkspaceStatus

class WorkspaceIntegration:
    """工作空间集成器"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.workspace_manager = WorkspaceManager(project_root)

    def suggest_workspace_for_task(self, task_description: str) -> Dict[str, Any]:
        """为任务建议最佳工作空间"""

        # 基础推荐
        recommended_id = self.workspace_manager.recommend_workspace(task_description)

        # 分析任务复杂度
        task_analysis = self._analyze_task_complexity(task_description)

        # 获取当前工作空间状态
        current_workspaces = self.workspace_manager.list_workspaces()
        active_workspaces = [ws for ws in current_workspaces if ws['status'] == 'active']

        suggestions = {
            'recommended_workspace': recommended_id,
            'task_analysis': task_analysis,
            'create_new': self._should_create_new_workspace(task_analysis, active_workspaces),
            'available_workspaces': [
                {
                    'id': ws['id'],
                    'name': ws['name'],
                    'type': ws['type'],
                    'suitability_score': self._calculate_suitability(ws, task_analysis)
                }
                for ws in current_workspaces
                if ws['status'] in ['idle', 'paused']
            ],
            'parallel_suggestions': self._suggest_parallel_development(task_analysis, active_workspaces)
        }

        return suggestions

    def _analyze_task_complexity(self, task_description: str) -> Dict[str, Any]:
        """分析任务复杂度"""
        task_lower = task_description.lower()

        # 复杂度指标
        complexity_indicators = {
            'database_changes': any(word in task_lower for word in ['database', 'migration', 'schema', 'table']),
            'api_changes': any(word in task_lower for word in ['api', 'endpoint', 'route', 'service']),
            'ui_changes': any(word in task_lower for word in ['ui', 'frontend', 'component', 'page']),
            'authentication': any(word in task_lower for word in ['auth', 'login', 'permission', 'security']),
            'integration': any(word in task_lower for word in ['integration', 'external', 'third-party']),
            'testing': any(word in task_lower for word in ['test', 'testing', 'coverage']),
            'performance': any(word in task_lower for word in ['performance', 'optimization', 'speed']),
            'refactoring': any(word in task_lower for word in ['refactor', 'restructure', 'cleanup'])
        }

        # 估算工作量（小时）
        base_hours = 2
        if complexity_indicators['database_changes']: base_hours += 4
        if complexity_indicators['api_changes']: base_hours += 3
        if complexity_indicators['ui_changes']: base_hours += 2
        if complexity_indicators['authentication']: base_hours += 6
        if complexity_indicators['integration']: base_hours += 4
        if complexity_indicators['testing']: base_hours += 2
        if complexity_indicators['performance']: base_hours += 3
        if complexity_indicators['refactoring']: base_hours += 1

        # 风险评估
        risk_level = 'low'
        risk_count = sum(complexity_indicators.values())
        if risk_count >= 4:
            risk_level = 'high'
        elif risk_count >= 2:
            risk_level = 'medium'

        return {
            'complexity_score': risk_count,
            'estimated_hours': min(base_hours, 40),  # 最多40小时
            'risk_level': risk_level,
            'indicators': complexity_indicators,
            'recommended_type': self._determine_workspace_type(complexity_indicators)
        }

    def _determine_workspace_type(self, indicators: Dict[str, bool]) -> WorkspaceType:
        """基于指标确定工作空间类型"""
        if indicators.get('refactoring'):
            return WorkspaceType.REFACTOR
        elif indicators.get('performance') or indicators.get('integration'):
            return WorkspaceType.EXPERIMENT
        elif any(indicators.get(key) for key in ['database_changes', 'api_changes', 'ui_changes']):
            return WorkspaceType.FEATURE
        else:
            return WorkspaceType.BUGFIX

    def _should_create_new_workspace(self, task_analysis: Dict, active_workspaces: List) -> Dict[str, Any]:
        """判断是否应该创建新工作空间"""

        # 如果已有太多活跃工作空间
        if len(active_workspaces) >= 3:
            return {
                'recommended': False,
                'reason': 'Too many active workspaces, consider pausing some first'
            }

        # 高风险或复杂任务建议独立工作空间
        if task_analysis['risk_level'] == 'high' or task_analysis['complexity_score'] >= 3:
            return {
                'recommended': True,
                'reason': 'High complexity task benefits from isolated workspace',
                'suggested_name': self._suggest_workspace_name(task_analysis),
                'suggested_type': task_analysis['recommended_type'].value
            }

        return {
            'recommended': True,
            'reason': 'Clean workspace recommended for focused development',
            'suggested_name': self._suggest_workspace_name(task_analysis),
            'suggested_type': task_analysis['recommended_type'].value
        }

    def _suggest_workspace_name(self, task_analysis: Dict) -> str:
        """建议工作空间名称"""
        indicators = task_analysis['indicators']

        if indicators.get('authentication'):
            return "auth_system"
        elif indicators.get('database_changes'):
            return "database_update"
        elif indicators.get('api_changes'):
            return "api_enhancement"
        elif indicators.get('ui_changes'):
            return "ui_improvement"
        elif indicators.get('performance'):
            return "performance_opt"
        elif indicators.get('refactoring'):
            return "code_refactor"
        else:
            return f"feature_{datetime.now().strftime('%m%d')}"

    def _calculate_suitability(self, workspace: Dict, task_analysis: Dict) -> float:
        """计算工作空间对任务的适配度"""
        score = 0.0

        # 类型匹配
        if workspace['type'] == task_analysis['recommended_type'].value:
            score += 0.4

        # 状态匹配
        if workspace['status'] == 'idle':
            score += 0.3
        elif workspace['status'] == 'paused':
            score += 0.2

        # 优先级匹配
        if workspace.get('priority', 5) >= 7 and task_analysis['risk_level'] == 'high':
            score += 0.2

        # 最近使用时间
        last_accessed = workspace.get('last_accessed', '')
        if last_accessed:
            try:
                last_time = datetime.fromisoformat(last_accessed.replace('Z', '+00:00'))
                days_since = (datetime.now() - last_time).days
                if days_since < 3:
                    score += 0.1
            except:
                pass

        return min(score, 1.0)

    def _suggest_parallel_development(self, task_analysis: Dict, active_workspaces: List) -> Dict[str, Any]:
        """建议并行开发策略"""

        if not active_workspaces:
            return {'feasible': True, 'conflicts': [], 'recommendations': []}

        # 分析潜在冲突
        conflicts = []
        recommendations = []

        # 检查文件冲突风险
        for workspace in active_workspaces:
            workspace_id = workspace['id']
            conflict_info = self.workspace_manager.detect_conflicts(workspace_id)

            if conflict_info.get('potential_conflicts'):
                conflicts.append({
                    'workspace': workspace_id,
                    'risk_level': 'medium',
                    'description': 'Potential file conflicts detected'
                })

        # 基于任务类型给出建议
        indicators = task_analysis['indicators']

        if indicators.get('database_changes'):
            recommendations.append(
                "Database changes detected - consider coordinating schema migrations"
            )

        if indicators.get('api_changes'):
            recommendations.append(
                "API changes detected - ensure backward compatibility"
            )

        return {
            'feasible': len(conflicts) <= 1,
            'conflicts': conflicts,
            'recommendations': recommendations,
            'max_parallel_recommended': 2 if task_analysis['risk_level'] == 'low' else 1
        }

    def generate_claude_code_instructions(self, task_description: str, workspace_id: Optional[str] = None) -> str:
        """为Claude Code生成工作空间相关指令"""

        suggestions = self.suggest_workspace_for_task(task_description)

        if workspace_id:
            # 使用指定工作空间
            workspace_info = next(
                (ws for ws in self.workspace_manager.list_workspaces() if ws['id'] == workspace_id),
                None
            )
            if not workspace_info:
                return f"Error: Workspace {workspace_id} not found"

            instructions = f"""
**Perfect21 工作空间指令**

任务: {task_description}
工作空间: {workspace_info['name']} ({workspace_id})
端口: {workspace_info['dev_port']}
分支: {workspace_info['branch']}

1. 确认当前在正确的工作空间分支上
2. 任务复杂度: {suggestions['task_analysis']['complexity_score']}/8
3. 预估工时: {suggestions['task_analysis']['estimated_hours']}小时
4. 风险级别: {suggestions['task_analysis']['risk_level']}

**开发建议:**
- 使用端口 {workspace_info['dev_port']} 进行开发服务器
- 定期同步基分支以避免冲突
- 完成后使用Perfect21合并工具进行安全合并
"""
        else:
            # 生成工作空间选择建议
            if suggestions['recommended_workspace']:
                instructions = f"""
**Perfect21 工作空间建议**

任务: {task_description}

建议使用现有工作空间: {suggestions['recommended_workspace']}

切换命令:
```bash
python3 main/cli.py workspace switch {suggestions['recommended_workspace']}
```
"""
            elif suggestions['create_new']['recommended']:
                instructions = f"""
**Perfect21 工作空间建议**

任务: {task_description}

建议创建新工作空间:
- 名称: {suggestions['create_new']['suggested_name']}
- 类型: {suggestions['create_new']['suggested_type']}
- 原因: {suggestions['create_new']['reason']}

创建命令:
```bash
python3 main/cli.py workspace create "{suggestions['create_new']['suggested_name']}" "{task_description}" --type {suggestions['create_new']['suggested_type']}
```
"""
            else:
                instructions = f"""
**Perfect21 工作空间建议**

任务: {task_description}

{suggestions['create_new']['reason']}

可用工作空间:
"""
                for ws in suggestions['available_workspaces'][:3]:
                    instructions += f"- {ws['name']} ({ws['type']}) - 适配度: {ws['suitability_score']:.1f}\n"

        return instructions

    def get_workspace_development_context(self, workspace_id: str) -> Dict[str, Any]:
        """获取工作空间开发上下文"""

        workspaces = self.workspace_manager.list_workspaces()
        workspace = next((ws for ws in workspaces if ws['id'] == workspace_id), None)

        if not workspace:
            return {"error": "Workspace not found"}

        # 获取冲突信息
        conflicts = self.workspace_manager.detect_conflicts(workspace_id)

        # 获取统计信息
        stats = self.workspace_manager.get_workspace_stats()

        return {
            'workspace_info': workspace,
            'conflicts': conflicts,
            'development_ports': {
                'dev_server': workspace['dev_port'],
                'api_server': workspace.get('api_port')
            },
            'branch_status': {
                'ahead': workspace['commits_ahead'],
                'behind': workspace['commits_behind']
            },
            'parallel_context': {
                'active_workspaces': stats['active_count'],
                'total_workspaces': stats['total_workspaces']
            },
            'recommendations': self._get_development_recommendations(workspace, conflicts)
        }

    def _get_development_recommendations(self, workspace: Dict, conflicts: Dict) -> List[str]:
        """获取开发建议"""
        recommendations = []

        # 分支状态建议
        if workspace['commits_behind'] > 5:
            recommendations.append(f"考虑同步基分支，当前落后 {workspace['commits_behind']} 个提交")

        if workspace['commits_ahead'] > 20:
            recommendations.append("分支提交较多，考虑分阶段合并或拆分功能")

        # 冲突建议
        if conflicts.get('potential_conflicts'):
            recommendations.append("检测到潜在冲突，建议与相关工作空间协调开发")

        # 端口建议
        if workspace['dev_port'] > 3500:
            recommendations.append("使用高端口号，确保防火墙配置正确")

        return recommendations