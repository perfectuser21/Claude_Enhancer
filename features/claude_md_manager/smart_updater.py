#!/usr/bin/env python3
"""
Smart Updater - 智能动态更新器

基于模板引擎和智能分类的新一代文档更新器，
支持增量更新、内容去重、生命周期管理。
"""

import os
import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass

# 导入新组件
from .template_engine import TemplateEngine, DocumentTemplate, ContentBlock
from .smart_classifier import SmartClassifier, ContentSegment
from .lifecycle_manager import LifecycleManager, CleanupAction

@dataclass
class UpdateResult:
    """更新结果"""
    success: bool
    message: str
    changes_made: List[str]
    content_updated: Dict[str, Any]
    warnings: List[str]
    errors: List[str]

@dataclass
class ContentDiff:
    """内容差异"""
    block_id: str
    old_content: str
    new_content: str
    change_type: str  # 'add', 'update', 'delete', 'move'
    confidence: float

class SmartUpdater:
    """智能动态更新器"""

    def __init__(self, project_root: str = None):
        # 智能检测项目根目录
        if project_root is None:
            current_file = os.path.abspath(__file__)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))

        self.project_root = project_root
        self.claude_md_path = os.path.join(project_root, 'CLAUDE.md')

        # 初始化组件
        self.template_engine = TemplateEngine(project_root)
        self.classifier = SmartClassifier(project_root)
        self.lifecycle_manager = LifecycleManager(project_root)

        # 更新策略配置
        self.update_strategies = {
            'fixed': 'preserve',      # 固定内容：保持不变
            'dynamic': 'replace',     # 动态内容：替换更新
            'volatile': 'merge'       # 易变内容：智能合并
        }

    def smart_sync_document(self, force_update: bool = False) -> UpdateResult:
        """智能同步文档"""
        try:
            # 1. 收集当前数据
            current_data = self._collect_current_data()

            # 2. 分析现有文档
            existing_analysis = self._analyze_existing_document()

            # 3. 生成新内容
            new_content = self.template_engine.generate_document(current_data)

            # 4. 对比差异
            diffs = self._calculate_content_diffs(existing_analysis, new_content)

            # 5. 应用更新策略
            final_content, changes = self._apply_update_strategies(diffs, force_update)

            # 6. 生命周期管理
            self._update_lifecycle_tracking(changes)

            # 7. 写入文件
            if final_content:
                self._write_document_safely(final_content)

                # 8. 创建快照
                version = current_data.get('current_version', 'unknown')
                change_summary = ', '.join(changes) if changes else '自动同步'
                self.lifecycle_manager.create_document_snapshot(final_content, version, change_summary)

            return UpdateResult(
                success=True,
                message=f"文档同步成功，应用了 {len(changes)} 项更改",
                changes_made=changes,
                content_updated=current_data,
                warnings=[],
                errors=[]
            )

        except Exception as e:
            return UpdateResult(
                success=False,
                message=f"文档同步失败: {str(e)}",
                changes_made=[],
                content_updated={},
                warnings=[],
                errors=[str(e)]
            )

    def _collect_current_data(self) -> Dict[str, Any]:
        """收集当前系统数据"""
        data = {}

        # 版本信息
        try:
            from features.version_manager.version_manager import VersionManager
            vm = VersionManager()
            data['current_version'] = vm.get_current_version()
        except:
            data['current_version'] = 'v2.3.0'

        # 系统状态
        data['system_status'] = self._get_system_health()

        # 模块信息
        data['modules_info'] = self._get_modules_status()

        # Git信息
        data['git_info'] = self._get_git_status()

        # 统计信息
        data['project_stats'] = self._get_project_statistics()

        # 时间戳
        data['last_update'] = datetime.now().strftime('%Y-%m-%d')
        data['timestamp'] = datetime.now().isoformat()

        return data

    def _get_system_health(self) -> str:
        """获取系统健康状态"""
        try:
            # 检查核心模块
            features_dir = os.path.join(self.project_root, 'features')
            if not os.path.exists(features_dir):
                return "配置异常"

            module_count = len([d for d in os.listdir(features_dir)
                              if os.path.isdir(os.path.join(features_dir, d)) and not d.startswith('.')])

            if module_count >= 3:
                return "生产就绪"
            elif module_count >= 2:
                return "开发中"
            else:
                return "基础配置"

        except:
            return "状态未知"

    def _get_modules_status(self) -> List[Dict[str, str]]:
        """获取模块状态"""
        modules = []
        features_dir = os.path.join(self.project_root, 'features')

        if os.path.exists(features_dir):
            for module_name in sorted(os.listdir(features_dir)):
                module_path = os.path.join(features_dir, module_name)
                if os.path.isdir(module_path) and not module_name.startswith('.'):
                    # 检查模块状态
                    status = "⚠️ 基础"
                    if os.path.exists(os.path.join(module_path, 'capability.py')):
                        status = "✅ 正常"
                    elif os.path.exists(os.path.join(module_path, '__init__.py')):
                        status = "🔄 开发中"

                    modules.append({
                        'name': module_name,
                        'status': status
                    })

        return modules

    def _get_git_status(self) -> Dict[str, Any]:
        """获取Git状态信息"""
        import subprocess
        git_info = {}

        try:
            # 当前分支
            result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                                  capture_output=True, text=True, cwd=self.project_root)
            if result.returncode == 0:
                git_info['current_branch'] = result.stdout.strip()

            # 提交数量
            result = subprocess.run(['git', 'rev-list', '--count', 'HEAD'],
                                  capture_output=True, text=True, cwd=self.project_root)
            if result.returncode == 0:
                git_info['total_commits'] = int(result.stdout.strip())

            # Git hooks覆盖率
            hooks_dir = os.path.join(self.project_root, '.git', 'hooks')
            if os.path.exists(hooks_dir):
                total_hooks = 13  # 标准Git钩子数量
                active_hooks = len([f for f in os.listdir(hooks_dir)
                                  if not f.endswith('.sample') and os.path.isfile(os.path.join(hooks_dir, f))])
                git_info['hooks_coverage'] = f"{active_hooks}/{total_hooks}"

        except Exception as e:
            git_info['error'] = str(e)

        return git_info

    def _get_project_statistics(self) -> Dict[str, Any]:
        """获取项目统计信息"""
        stats = {
            'total_files': 0,
            'python_files': 0,
            'features_count': 0,
            'code_lines': 0
        }

        try:
            for root, dirs, files in os.walk(self.project_root):
                # 跳过隐藏目录和不需要的目录
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv', 'node_modules']]

                for file in files:
                    if not file.startswith('.'):
                        stats['total_files'] += 1

                        if file.endswith('.py'):
                            stats['python_files'] += 1

            # 功能模块数量
            features_dir = os.path.join(self.project_root, 'features')
            if os.path.exists(features_dir):
                stats['features_count'] = len([d for d in os.listdir(features_dir)
                                             if os.path.isdir(os.path.join(features_dir, d)) and not d.startswith('.')])

        except Exception as e:
            stats['error'] = str(e)

        return stats

    def _analyze_existing_document(self) -> Dict[str, Any]:
        """分析现有文档"""
        if not os.path.exists(self.claude_md_path):
            return {'exists': False, 'segments': []}

        with open(self.claude_md_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 使用智能分类器分析
        segments = self.classifier.classify_content(content)

        return {
            'exists': True,
            'content': content,
            'segments': segments,
            'analysis': self.classifier.get_classification_report(segments)
        }

    def _calculate_content_diffs(self, existing_analysis: Dict, new_content: str) -> List[ContentDiff]:
        """计算内容差异"""
        diffs = []

        if not existing_analysis.get('exists'):
            # 新文档
            diffs.append(ContentDiff(
                block_id='full_document',
                old_content='',
                new_content=new_content,
                change_type='add',
                confidence=1.0
            ))
            return diffs

        # 分析新内容
        new_segments = self.classifier.classify_content(new_content)
        existing_segments = existing_analysis.get('segments', [])

        # 创建段落映射
        existing_map = {seg.fingerprint: seg for seg in existing_segments}
        new_map = {seg.fingerprint: seg for seg in new_segments}

        # 查找变化
        for new_seg in new_segments:
            if new_seg.fingerprint in existing_map:
                # 内容未变化
                continue
            else:
                # 查找相似的现有段落
                similar_seg = self._find_similar_segment(new_seg, existing_segments)
                if similar_seg:
                    # 内容更新
                    diffs.append(ContentDiff(
                        block_id=new_seg.id,
                        old_content=similar_seg.content,
                        new_content=new_seg.content,
                        change_type='update',
                        confidence=new_seg.confidence
                    ))
                else:
                    # 新增内容
                    diffs.append(ContentDiff(
                        block_id=new_seg.id,
                        old_content='',
                        new_content=new_seg.content,
                        change_type='add',
                        confidence=new_seg.confidence
                    ))

        # 查找删除的内容
        for existing_seg in existing_segments:
            if existing_seg.fingerprint not in new_map:
                # 可能被删除
                if not self._find_similar_segment(existing_seg, new_segments):
                    diffs.append(ContentDiff(
                        block_id=existing_seg.id,
                        old_content=existing_seg.content,
                        new_content='',
                        change_type='delete',
                        confidence=existing_seg.confidence
                    ))

        return diffs

    def _find_similar_segment(self, target_segment: ContentSegment, segments: List[ContentSegment]) -> Optional[ContentSegment]:
        """查找相似的段落"""
        from difflib import SequenceMatcher

        best_similarity = 0
        best_segment = None

        for seg in segments:
            if seg.type == target_segment.type:  # 同类型才比较
                similarity = SequenceMatcher(None, target_segment.content, seg.content).ratio()
                if similarity > best_similarity and similarity > 0.6:  # 60%以上相似度
                    best_similarity = similarity
                    best_segment = seg

        return best_segment

    def _apply_update_strategies(self, diffs: List[ContentDiff], force_update: bool) -> Tuple[Optional[str], List[str]]:
        """应用更新策略"""
        if not diffs:
            return None, []

        changes = []

        # 如果是全新文档，直接使用
        if len(diffs) == 1 and diffs[0].change_type == 'add' and diffs[0].block_id == 'full_document':
            changes.append("创建新文档")
            return diffs[0].new_content, changes

        # 读取现有内容
        if os.path.exists(self.claude_md_path):
            with open(self.claude_md_path, 'r', encoding='utf-8') as f:
                current_content = f.read()
        else:
            current_content = ""

        updated_content = current_content

        # 按更新策略处理差异
        for diff in diffs:
            strategy = self._determine_update_strategy(diff)

            if strategy == 'preserve':
                # 保持不变
                continue

            elif strategy == 'replace':
                # 替换更新
                if diff.change_type == 'update':
                    updated_content = updated_content.replace(diff.old_content, diff.new_content)
                    changes.append(f"更新{diff.block_id}")

                elif diff.change_type == 'add':
                    # 在适当位置添加新内容
                    updated_content = self._insert_new_content(updated_content, diff.new_content)
                    changes.append(f"添加{diff.block_id}")

            elif strategy == 'merge':
                # 智能合并
                merged_content = self._merge_content(diff.old_content, diff.new_content)
                updated_content = updated_content.replace(diff.old_content, merged_content)
                changes.append(f"合并{diff.block_id}")

            elif strategy == 'delete':
                # 删除内容
                if diff.old_content in updated_content:
                    updated_content = updated_content.replace(diff.old_content, '')
                    changes.append(f"删除{diff.block_id}")

        # 清理内容
        updated_content = self._cleanup_content(updated_content)

        return updated_content if changes else None, changes

    def _determine_update_strategy(self, diff: ContentDiff) -> str:
        """确定更新策略"""
        # 根据内容类型和变化类型决定策略
        if '固定核心' in diff.old_content or '固定核心' in diff.new_content:
            return 'preserve'  # 固定内容区域标记，保持不变

        # 基于内容特征判断
        content = diff.old_content + diff.new_content

        if any(keyword in content.lower() for keyword in ['项目本质', '核心理念', '基本使用']):
            return 'preserve'  # 核心内容保持不变

        elif any(keyword in content.lower() for keyword in ['当前版本', '最后更新', '状态']):
            return 'replace'  # 状态信息直接替换

        elif any(keyword in content.lower() for keyword in ['todo', '临时', '测试']):
            return 'merge'  # 临时信息智能合并

        else:
            return 'replace'  # 默认替换策略

    def _insert_new_content(self, current_content: str, new_content: str) -> str:
        """在适当位置插入新内容"""
        # 查找动态内容区域
        dynamic_marker = '<!-- ================== 动态状态部分'
        if dynamic_marker in current_content:
            insertion_point = current_content.find(dynamic_marker)
            # 在动态区域后插入
            end_marker = current_content.find('\n', insertion_point + len(dynamic_marker))
            if end_marker != -1:
                return (current_content[:end_marker + 1] +
                       '\n' + new_content + '\n' +
                       current_content[end_marker + 1:])

        # 默认追加到末尾
        return current_content + '\n\n' + new_content

    def _merge_content(self, old_content: str, new_content: str) -> str:
        """智能合并内容"""
        # 简化合并策略：保留旧内容，追加新信息
        if old_content and new_content:
            return old_content + '\n' + new_content
        return new_content or old_content

    def _cleanup_content(self, content: str) -> str:
        """清理内容"""
        # 移除多余的空行
        lines = content.split('\n')
        cleaned_lines = []
        prev_empty = False

        for line in lines:
            is_empty = not line.strip()
            if not (is_empty and prev_empty):  # 避免连续空行
                cleaned_lines.append(line)
            prev_empty = is_empty

        return '\n'.join(cleaned_lines)

    def _update_lifecycle_tracking(self, changes: List[str]):
        """更新生命周期跟踪"""
        for change in changes:
            # 为变更的内容更新生命周期
            content_id = f"change_{hashlib.md5(change.encode()).hexdigest()[:8]}"
            if change.startswith('更新'):
                self.lifecycle_manager.update_content_modified(content_id)
            elif change.startswith('添加'):
                self.lifecycle_manager.register_content(content_id, 'dynamic', 0.7)

    def _write_document_safely(self, content: str):
        """安全写入文档"""
        # 创建备份
        if os.path.exists(self.claude_md_path):
            backup_path = f"{self.claude_md_path}.backup"
            import shutil
            shutil.copy2(self.claude_md_path, backup_path)

        # 写入新内容
        with open(self.claude_md_path, 'w', encoding='utf-8') as f:
            f.write(content)

    def get_update_suggestions(self) -> List[str]:
        """获取更新建议"""
        suggestions = []

        # 生命周期建议
        cleanup_actions = self.lifecycle_manager.suggest_cleanup_actions()
        for action in cleanup_actions:
            suggestions.append(f"建议{action.action_type}: {action.reason}")

        # 文档健康度建议
        if os.path.exists(self.claude_md_path):
            with open(self.claude_md_path, 'r', encoding='utf-8') as f:
                content = f.read()

            line_count = len(content.split('\n'))
            if line_count > 100:
                suggestions.append("文档过长，建议精简内容")

            if '最后更新' in content:
                # 检查更新时间
                import re
                date_match = re.search(r'最后更新.*(\d{4}-\d{2}-\d{2})', content)
                if date_match:
                    last_date = datetime.strptime(date_match.group(1), '%Y-%m-%d')
                    days_old = (datetime.now() - last_date).days
                    if days_old > 7:
                        suggestions.append(f"文档{days_old}天未更新，建议同步最新状态")

        return suggestions

if __name__ == "__main__":
    # 测试智能更新器
    updater = SmartUpdater()

    print("=== 智能更新器测试 ===")

    # 获取更新建议
    suggestions = updater.get_update_suggestions()
    print(f"更新建议: {len(suggestions)} 条")
    for suggestion in suggestions:
        print(f"  - {suggestion}")

    # 执行智能同步
    result = updater.smart_sync_document()
    print(f"\n同步结果: {result.success}")
    print(f"消息: {result.message}")
    print(f"变更: {len(result.changes_made)} 项")
    for change in result.changes_made:
        print(f"  - {change}")