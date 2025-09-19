"""
ADR存储管理器 - 标准化决策记录持久化
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class ADRStorage:
    def __init__(self, base_path: str = None):
        if base_path is None:
            base_path = os.environ.get('PERFECT21_ROOT', '/home/xx/dev/Perfect21')

        self.base_path = Path(base_path)
        self.adr_path = self.base_path / 'knowledge' / 'decisions' / 'adr'
        self.sessions_path = self.base_path / 'knowledge' / 'decisions' / 'sessions'
        self.index_path = self.base_path / 'knowledge' / 'decisions' / 'index'

        # 确保目录存在
        for path in [self.adr_path, self.sessions_path, self.index_path]:
            path.mkdir(parents=True, exist_ok=True)

    def save_decision(self, decision_data: Dict) -> str:
        """保存单个决策记录"""
        timestamp = datetime.now()
        decision_id = f"ADR-{timestamp.strftime('%Y%m%d-%H%M%S')}"

        # 标准ADR格式
        adr_content = {
            'id': decision_id,
            'title': decision_data.get('title', '未命名决策'),
            'date': timestamp.isoformat(),
            'status': decision_data.get('status', 'proposed'),
            'context': decision_data.get('context', ''),
            'decision': decision_data.get('decision', ''),
            'consequences': decision_data.get('consequences', ''),
            'agents_involved': decision_data.get('agents_involved', []),
            'metadata': {
                'project': 'Perfect21',
                'session_id': decision_data.get('session_id'),
                'complexity': decision_data.get('complexity', 'medium')
            }
        }

        # 保存ADR文件
        adr_file = self.adr_path / f"{decision_id}.json"
        with open(adr_file, 'w', encoding='utf-8') as f:
            json.dump(adr_content, f, indent=2, ensure_ascii=False)

        # 更新索引
        self._update_index(decision_id, adr_content)

        return decision_id

    def _update_index(self, decision_id: str, content: Dict):
        """更新决策索引"""
        index_file = self.index_path / 'decisions_index.json'

        # 读取现有索引
        index = {}
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)

        # 添加新记录
        index[decision_id] = {
            'title': content['title'],
            'date': content['date'],
            'status': content['status'],
            'file_path': f"adr/{decision_id}.json"
        }

        # 保存索引
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

    def get_recent_decisions(self, limit: int = 10) -> List[Dict]:
        """获取最近的决策记录"""
        index_file = self.index_path / 'decisions_index.json'
        if not index_file.exists():
            return []

        with open(index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)

        # 按时间排序，返回最近的记录
        sorted_decisions = sorted(
            index.items(),
            key=lambda x: x[1]['date'],
            reverse=True
        )

        return sorted_decisions[:limit]

# 全局实例
adr_storage = ADRStorage()