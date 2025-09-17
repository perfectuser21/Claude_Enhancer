#!/usr/bin/env python3
"""
Lifecycle Manager - 内容生命周期管理器

管理CLAUDE.md文档内容的完整生命周期，包括：
- 内容过期检测
- 自动清理机制
- 版本历史管理
- 内容优化建议
"""

import os
import json
import shutil
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class ContentLifecycle:
    """内容生命周期状态"""
    content_id: str
    content_type: str  # 'fixed', 'dynamic', 'volatile'
    status: str  # 'active', 'aging', 'stale', 'obsolete'
    created_at: str
    last_updated: str
    last_accessed: str
    update_count: int
    importance_score: float
    auto_cleanup: bool = True

@dataclass
class CleanupAction:
    """清理动作"""
    action_type: str  # 'delete', 'archive', 'merge', 'update'
    target_content: str
    reason: str
    confidence: float
    suggested_replacement: Optional[str] = None

@dataclass
class DocumentSnapshot:
    """文档快照"""
    timestamp: str
    version: str
    content_hash: str
    file_size: int
    change_summary: str
    segment_count: int

class LifecycleManager:
    """内容生命周期管理器"""

    def __init__(self, project_root: str = None):
        # 智能检测项目根目录
        if project_root is None:
            current_file = os.path.abspath(__file__)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))

        self.project_root = project_root
        self.claude_md_path = os.path.join(project_root, 'CLAUDE.md')

        # 生命周期数据目录
        self.lifecycle_dir = os.path.join(project_root, 'features', 'claude_md_manager', 'lifecycle_data')
        self.history_dir = os.path.join(self.lifecycle_dir, 'history')
        self.snapshots_dir = os.path.join(self.lifecycle_dir, 'snapshots')

        # 确保目录存在
        for directory in [self.lifecycle_dir, self.history_dir, self.snapshots_dir]:
            os.makedirs(directory, exist_ok=True)

        # 生命周期配置
        self.lifecycle_config = {
            'fixed': {
                'max_age_days': None,  # 固定内容不过期
                'warning_threshold': 90,  # 90天未更新警告
                'auto_cleanup': False
            },
            'dynamic': {
                'max_age_days': 30,  # 30天过期
                'warning_threshold': 7,   # 7天未更新警告
                'auto_cleanup': True
            },
            'volatile': {
                'max_age_days': 7,   # 7天过期
                'warning_threshold': 3,   # 3天未更新警告
                'auto_cleanup': True
            }
        }

        # 加载生命周期数据
        self.lifecycle_data = self._load_lifecycle_data()

    def _load_lifecycle_data(self) -> Dict[str, ContentLifecycle]:
        """加载生命周期数据"""
        data_file = os.path.join(self.lifecycle_dir, 'lifecycle_data.json')

        if os.path.exists(data_file):
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                    return {k: ContentLifecycle(**v) for k, v in raw_data.items()}
            except Exception as e:
                print(f"加载生命周期数据失败: {e}")

        return {}

    def _save_lifecycle_data(self):
        """保存生命周期数据"""
        data_file = os.path.join(self.lifecycle_dir, 'lifecycle_data.json')

        raw_data = {k: asdict(v) for k, v in self.lifecycle_data.items()}

        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(raw_data, f, indent=2, ensure_ascii=False)

    def register_content(self, content_id: str, content_type: str, importance_score: float = 0.5) -> ContentLifecycle:
        """注册新内容"""
        now = datetime.now().isoformat()

        lifecycle = ContentLifecycle(
            content_id=content_id,
            content_type=content_type,
            status='active',
            created_at=now,
            last_updated=now,
            last_accessed=now,
            update_count=1,
            importance_score=importance_score,
            auto_cleanup=self.lifecycle_config[content_type]['auto_cleanup']
        )

        self.lifecycle_data[content_id] = lifecycle
        self._save_lifecycle_data()

        return lifecycle

    def update_content_access(self, content_id: str):
        """更新内容访问时间"""
        if content_id in self.lifecycle_data:
            self.lifecycle_data[content_id].last_accessed = datetime.now().isoformat()
            self._save_lifecycle_data()

    def update_content_modified(self, content_id: str):
        """更新内容修改时间"""
        if content_id in self.lifecycle_data:
            lifecycle = self.lifecycle_data[content_id]
            lifecycle.last_updated = datetime.now().isoformat()
            lifecycle.last_accessed = datetime.now().isoformat()
            lifecycle.update_count += 1
            lifecycle.status = 'active'  # 重置为活跃状态
            self._save_lifecycle_data()

    def evaluate_content_status(self) -> Dict[str, List[ContentLifecycle]]:
        """评估所有内容的生命周期状态"""
        now = datetime.now()
        status_groups = {
            'active': [],
            'aging': [],
            'stale': [],
            'obsolete': []
        }

        for content_id, lifecycle in self.lifecycle_data.items():
            last_updated = datetime.fromisoformat(lifecycle.last_updated)
            days_since_update = (now - last_updated).days

            config = self.lifecycle_config[lifecycle.content_type]

            # 根据内容类型和时间判断状态
            if lifecycle.content_type == 'fixed':
                # 固定内容特殊处理
                if days_since_update > config['warning_threshold']:
                    lifecycle.status = 'aging'
                else:
                    lifecycle.status = 'active'
            else:
                # 动态和易变内容
                if config['max_age_days'] and days_since_update > config['max_age_days']:
                    lifecycle.status = 'obsolete'
                elif days_since_update > config['warning_threshold']:
                    lifecycle.status = 'stale'
                elif days_since_update > config['warning_threshold'] // 2:
                    lifecycle.status = 'aging'
                else:
                    lifecycle.status = 'active'

            status_groups[lifecycle.status].append(lifecycle)

        self._save_lifecycle_data()
        return status_groups

    def suggest_cleanup_actions(self) -> List[CleanupAction]:
        """建议清理动作"""
        status_groups = self.evaluate_content_status()
        actions = []

        # 处理过期内容
        for lifecycle in status_groups['obsolete']:
            if lifecycle.auto_cleanup and lifecycle.importance_score < 0.7:
                actions.append(CleanupAction(
                    action_type='delete',
                    target_content=lifecycle.content_id,
                    reason=f"{lifecycle.content_type}内容已过期{self._get_days_since_update(lifecycle)}天",
                    confidence=0.9
                ))

        # 处理陈旧内容
        for lifecycle in status_groups['stale']:
            if lifecycle.content_type == 'volatile':
                actions.append(CleanupAction(
                    action_type='archive',
                    target_content=lifecycle.content_id,
                    reason=f"易变内容{self._get_days_since_update(lifecycle)}天未更新，建议归档",
                    confidence=0.7
                ))
            elif lifecycle.content_type == 'dynamic':
                actions.append(CleanupAction(
                    action_type='update',
                    target_content=lifecycle.content_id,
                    reason=f"动态内容{self._get_days_since_update(lifecycle)}天未更新，建议刷新",
                    confidence=0.8
                ))

        # 处理老化内容
        for lifecycle in status_groups['aging']:
            if lifecycle.content_type == 'dynamic' and lifecycle.update_count < 3:
                actions.append(CleanupAction(
                    action_type='update',
                    target_content=lifecycle.content_id,
                    reason=f"动态内容更新频率低，建议检查数据源",
                    confidence=0.6
                ))

        return actions

    def _get_days_since_update(self, lifecycle: ContentLifecycle) -> int:
        """获取距离上次更新的天数"""
        last_updated = datetime.fromisoformat(lifecycle.last_updated)
        return (datetime.now() - last_updated).days

    def create_document_snapshot(self, content: str, version: str, change_summary: str) -> DocumentSnapshot:
        """创建文档快照"""
        import hashlib

        timestamp = datetime.now().isoformat()
        content_hash = hashlib.md5(content.encode()).hexdigest()
        file_size = len(content.encode('utf-8'))

        # 计算段落数
        segment_count = len([line for line in content.split('\n') if line.startswith('#')])

        snapshot = DocumentSnapshot(
            timestamp=timestamp,
            version=version,
            content_hash=content_hash,
            file_size=file_size,
            change_summary=change_summary,
            segment_count=segment_count
        )

        # 保存快照文件
        snapshot_filename = f"snapshot_{timestamp.replace(':', '-').replace('.', '_')}.md"
        snapshot_path = os.path.join(self.snapshots_dir, snapshot_filename)

        with open(snapshot_path, 'w', encoding='utf-8') as f:
            f.write(f"<!-- 快照元数据\n")
            f.write(f"时间: {timestamp}\n")
            f.write(f"版本: {version}\n")
            f.write(f"哈希: {content_hash}\n")
            f.write(f"大小: {file_size} bytes\n")
            f.write(f"变更: {change_summary}\n")
            f.write(f"段落数: {segment_count}\n")
            f.write(f"-->\n\n")
            f.write(content)

        # 保存快照索引
        self._save_snapshot_index(snapshot)

        return snapshot

    def _save_snapshot_index(self, snapshot: DocumentSnapshot):
        """保存快照索引"""
        index_file = os.path.join(self.snapshots_dir, 'index.json')

        # 加载现有索引
        index = []
        if os.path.exists(index_file):
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    index = json.load(f)
            except:
                pass

        # 添加新快照
        index.append(asdict(snapshot))

        # 只保留最近50个快照的索引
        index = index[-50:]

        # 保存索引
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

    def get_snapshot_history(self, limit: int = 10) -> List[DocumentSnapshot]:
        """获取快照历史"""
        index_file = os.path.join(self.snapshots_dir, 'index.json')

        if not os.path.exists(index_file):
            return []

        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                index_data = json.load(f)

            snapshots = [DocumentSnapshot(**data) for data in index_data[-limit:]]
            return list(reversed(snapshots))  # 最新的在前

        except Exception as e:
            print(f"读取快照历史失败: {e}")
            return []

    def cleanup_old_snapshots(self, keep_days: int = 30):
        """清理旧快照"""
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        cleaned_count = 0

        # 清理快照文件
        for filename in os.listdir(self.snapshots_dir):
            if filename.startswith('snapshot_') and filename.endswith('.md'):
                filepath = os.path.join(self.snapshots_dir, filename)
                try:
                    # 从文件名提取时间
                    timestamp_str = filename[9:-3].replace('-', ':').replace('_', '.')
                    # 简化时间解析
                    file_time = datetime.strptime(timestamp_str[:19], '%Y-%m-%dT%H:%M:%S')

                    if file_time < cutoff_date:
                        os.remove(filepath)
                        cleaned_count += 1
                except:
                    pass  # 跳过无法解析的文件

        # 重建索引
        self._rebuild_snapshot_index()

        return cleaned_count

    def _rebuild_snapshot_index(self):
        """重建快照索引"""
        snapshots = []

        for filename in sorted(os.listdir(self.snapshots_dir)):
            if filename.startswith('snapshot_') and filename.endswith('.md'):
                filepath = os.path.join(self.snapshots_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # 解析元数据
                    if content.startswith('<!-- 快照元数据'):
                        meta_end = content.find('-->')
                        meta_content = content[4:meta_end]

                        # 提取元数据字段
                        meta_dict = {}
                        for line in meta_content.split('\n'):
                            if ':' in line:
                                key, value = line.split(':', 1)
                                meta_dict[key.strip()] = value.strip()

                        snapshot = DocumentSnapshot(
                            timestamp=meta_dict.get('时间', ''),
                            version=meta_dict.get('版本', ''),
                            content_hash=meta_dict.get('哈希', ''),
                            file_size=int(meta_dict.get('大小', '0').split()[0]),
                            change_summary=meta_dict.get('变更', ''),
                            segment_count=int(meta_dict.get('段落数', '0'))
                        )

                        snapshots.append(snapshot)

                except Exception as e:
                    print(f"处理快照文件 {filename} 失败: {e}")

        # 保存重建的索引
        index_file = os.path.join(self.snapshots_dir, 'index.json')
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump([asdict(s) for s in snapshots], f, indent=2, ensure_ascii=False)

    def generate_lifecycle_report(self) -> Dict[str, Any]:
        """生成生命周期报告"""
        status_groups = self.evaluate_content_status()
        cleanup_actions = self.suggest_cleanup_actions()

        report = {
            'timestamp': datetime.now().isoformat(),
            'total_content_items': len(self.lifecycle_data),
            'status_summary': {
                status: len(items) for status, items in status_groups.items()
            },
            'cleanup_suggestions': len(cleanup_actions),
            'content_by_type': {},
            'aging_items': [],
            'cleanup_actions': []
        }

        # 按类型统计
        for lifecycle in self.lifecycle_data.values():
            content_type = lifecycle.content_type
            if content_type not in report['content_by_type']:
                report['content_by_type'][content_type] = {
                    'total': 0,
                    'active': 0,
                    'aging': 0,
                    'stale': 0,
                    'obsolete': 0
                }

            report['content_by_type'][content_type]['total'] += 1
            report['content_by_type'][content_type][lifecycle.status] += 1

        # 老化项目详情
        for lifecycle in status_groups['aging'] + status_groups['stale']:
            report['aging_items'].append({
                'content_id': lifecycle.content_id,
                'type': lifecycle.content_type,
                'status': lifecycle.status,
                'days_since_update': self._get_days_since_update(lifecycle),
                'update_count': lifecycle.update_count,
                'importance': lifecycle.importance_score
            })

        # 清理动作详情
        for action in cleanup_actions:
            report['cleanup_actions'].append({
                'action': action.action_type,
                'target': action.target_content,
                'reason': action.reason,
                'confidence': action.confidence
            })

        return report

if __name__ == "__main__":
    # 测试生命周期管理器
    manager = LifecycleManager()

    # 注册测试内容
    manager.register_content('test_dynamic_content', 'dynamic', 0.8)
    manager.register_content('test_volatile_content', 'volatile', 0.3)

    # 评估状态
    status_groups = manager.evaluate_content_status()
    print("=== 生命周期状态 ===")
    for status, items in status_groups.items():
        print(f"{status}: {len(items)} 项")

    # 生成报告
    report = manager.generate_lifecycle_report()
    print(f"\n=== 生命周期报告 ===")
    print(f"总内容项: {report['total_content_items']}")
    print(f"清理建议: {report['cleanup_suggestions']} 项")

    # 创建测试快照
    test_content = "# 测试文档\n\n这是一个测试快照。"
    snapshot = manager.create_document_snapshot(test_content, "v1.0.0", "创建测试快照")
    print(f"\n快照已创建: {snapshot.timestamp}")

    print(f"\n生命周期数据目录: {manager.lifecycle_dir}")