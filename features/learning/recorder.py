"""
Decision Recorder - Mock Implementation for Testing
决策记录器 - 记录架构决策和经验
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class DecisionRecorder:
    """决策记录器"""

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = Path(storage_path or ".perfect21/decisions.json")
        self.storage_path.parent.mkdir(exist_ok=True)
        self.decisions: List[Dict[str, Any]] = []
        self._load_decisions()

    def record_decision(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        """记录决策"""
        try:
            decision_id = f"decision_{int(time.time())}"

            decision_record = {
                'decision_id': decision_id,
                'title': decision.get('title', 'Untitled Decision'),
                'context': decision.get('context', ''),
                'options': decision.get('options', []),
                'decision': decision.get('decision', ''),
                'rationale': decision.get('rationale', ''),
                'consequences': decision.get('consequences', []),
                'stakeholders': decision.get('stakeholders', []),
                'status': decision.get('status', 'active'),
                'tags': decision.get('tags', []),
                'timestamp': datetime.now().isoformat(),
                'metadata': {
                    'author': decision.get('author', 'system'),
                    'version': '1.0',
                    'review_date': decision.get('review_date'),
                    'related_decisions': decision.get('related_decisions', [])
                }
            }

            self.decisions.append(decision_record)
            self._save_decisions()

            return {
                'success': True,
                'decision_id': decision_id,
                'message': f'Decision "{decision_record["title"]}" recorded successfully'
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to record decision: {str(e)}'
            }

    def get_decisions(self, status: Optional[str] = None, tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """获取决策列表"""
        filtered_decisions = self.decisions

        if status:
            filtered_decisions = [d for d in filtered_decisions if d.get('status') == status]

        if tags:
            filtered_decisions = [
                d for d in filtered_decisions
                if any(tag in d.get('tags', []) for tag in tags)
            ]

        return filtered_decisions

    def get_decision(self, decision_id: str) -> Optional[Dict[str, Any]]:
        """获取特定决策"""
        for decision in self.decisions:
            if decision.get('decision_id') == decision_id:
                return decision
        return None

    def search_decisions(self, query: str) -> List[Dict[str, Any]]:
        """搜索决策"""
        query_lower = query.lower()
        results = []

        for decision in self.decisions:
            # 在标题、上下文、决策内容中搜索
            searchable_text = ' '.join([
                decision.get('title', ''),
                decision.get('context', ''),
                decision.get('decision', ''),
                decision.get('rationale', ''),
                ' '.join(decision.get('tags', []))
            ]).lower()

            if query_lower in searchable_text:
                results.append(decision)

        return results

    def update_decision(self, decision_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """更新决策"""
        try:
            for i, decision in enumerate(self.decisions):
                if decision.get('decision_id') == decision_id:
                    # 更新字段
                    for key, value in updates.items():
                        if key != 'decision_id':  # 不允许更改ID
                            decision[key] = value

                    # 更新版本和时间戳
                    decision['metadata']['version'] = self._increment_version(
                        decision['metadata'].get('version', '1.0')
                    )
                    decision['metadata']['last_modified'] = datetime.now().isoformat()

                    self._save_decisions()

                    return {
                        'success': True,
                        'decision_id': decision_id,
                        'message': 'Decision updated successfully'
                    }

            return {
                'success': False,
                'error': f'Decision {decision_id} not found'
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to update decision: {str(e)}'
            }

    def delete_decision(self, decision_id: str) -> Dict[str, Any]:
        """删除决策"""
        try:
            for i, decision in enumerate(self.decisions):
                if decision.get('decision_id') == decision_id:
                    del self.decisions[i]
                    self._save_decisions()

                    return {
                        'success': True,
                        'decision_id': decision_id,
                        'message': 'Decision deleted successfully'
                    }

            return {
                'success': False,
                'error': f'Decision {decision_id} not found'
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to delete decision: {str(e)}'
            }

    def get_decision_statistics(self) -> Dict[str, Any]:
        """获取决策统计"""
        total_decisions = len(self.decisions)
        active_decisions = len([d for d in self.decisions if d.get('status') == 'active'])
        superseded_decisions = len([d for d in self.decisions if d.get('status') == 'superseded'])

        # 统计标签
        tag_counts = {}
        for decision in self.decisions:
            for tag in decision.get('tags', []):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # 统计时间分布
        current_year = datetime.now().year
        decisions_this_year = len([
            d for d in self.decisions
            if datetime.fromisoformat(d['timestamp']).year == current_year
        ])

        return {
            'total_decisions': total_decisions,
            'active_decisions': active_decisions,
            'superseded_decisions': superseded_decisions,
            'decisions_this_year': decisions_this_year,
            'top_tags': sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10],
            'average_decisions_per_month': decisions_this_year / 12 if decisions_this_year > 0 else 0
        }

    def export_decisions(self, format: str = 'json', file_path: Optional[str] = None) -> Dict[str, Any]:
        """导出决策"""
        try:
            if format.lower() == 'json':
                export_data = {
                    'metadata': {
                        'export_timestamp': datetime.now().isoformat(),
                        'total_decisions': len(self.decisions),
                        'format_version': '1.0'
                    },
                    'decisions': self.decisions
                }

                if file_path:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(export_data, f, indent=2, ensure_ascii=False)
                    return {'success': True, 'file_path': file_path}
                else:
                    return {'success': True, 'data': export_data}

            elif format.lower() == 'adr':
                # 导出为ADR (Architecture Decision Record) 格式
                adr_content = self._export_as_adr()
                if file_path:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(adr_content)
                    return {'success': True, 'file_path': file_path}
                else:
                    return {'success': True, 'content': adr_content}

            else:
                return {'success': False, 'error': f'Unsupported format: {format}'}

        except Exception as e:
            return {
                'success': False,
                'error': f'Export failed: {str(e)}'
            }

    def _load_decisions(self) -> None:
        """加载决策数据"""
        try:
            if self.storage_path.exists():
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.decisions = data.get('decisions', [])
        except Exception:
            self.decisions = []

    def _save_decisions(self) -> None:
        """保存决策数据"""
        try:
            data = {
                'metadata': {
                    'last_updated': datetime.now().isoformat(),
                    'total_decisions': len(self.decisions),
                    'format_version': '1.0'
                },
                'decisions': self.decisions
            }

            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            # 静默失败，避免影响主功能
            pass

    def _increment_version(self, current_version: str) -> str:
        """递增版本号"""
        try:
            parts = current_version.split('.')
            if len(parts) >= 2:
                major, minor = int(parts[0]), int(parts[1])
                return f"{major}.{minor + 1}"
            else:
                return "1.1"
        except:
            return "1.1"

    def _export_as_adr(self) -> str:
        """导出为ADR格式"""
        adr_content = "# Architecture Decision Records\n\n"

        for decision in self.decisions:
            adr_content += f"## {decision.get('title', 'Untitled Decision')}\n\n"
            adr_content += f"**Status:** {decision.get('status', 'unknown')}\n\n"
            adr_content += f"**Date:** {decision.get('timestamp', 'unknown')}\n\n"

            if decision.get('context'):
                adr_content += f"### Context\n\n{decision['context']}\n\n"

            if decision.get('options'):
                adr_content += "### Options Considered\n\n"
                for i, option in enumerate(decision['options'], 1):
                    adr_content += f"{i}. {option}\n"
                adr_content += "\n"

            if decision.get('decision'):
                adr_content += f"### Decision\n\n{decision['decision']}\n\n"

            if decision.get('rationale'):
                adr_content += f"### Rationale\n\n{decision['rationale']}\n\n"

            if decision.get('consequences'):
                adr_content += "### Consequences\n\n"
                for consequence in decision['consequences']:
                    adr_content += f"- {consequence}\n"
                adr_content += "\n"

            if decision.get('tags'):
                adr_content += f"**Tags:** {', '.join(decision['tags'])}\n\n"

            adr_content += "---\n\n"

        return adr_content