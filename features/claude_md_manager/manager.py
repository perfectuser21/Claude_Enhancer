#!/usr/bin/env python3
"""
CLAUDE.md 智能管理器

核心功能：
1. 自动判断内容固定性 vs 动态性
2. 动态内容生命周期管理
3. 文档健康度监控和自动清理
4. 版本化管理文档状态
"""

import os
import re
import json
import hashlib
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from pathlib import Path

@dataclass
class ContentMetadata:
    """内容元数据"""
    content_hash: str
    last_modified: str
    modification_count: int
    content_type: str  # 'fixed', 'dynamic', 'volatile'
    importance_score: float
    lifecycle_stage: str  # 'active', 'aging', 'stale', 'obsolete'

@dataclass
class DocumentHealth:
    """文档健康度评估"""
    total_lines: int
    fixed_ratio: float
    dynamic_ratio: float
    volatile_ratio: float
    staleness_score: float
    redundancy_score: float
    health_grade: str  # A, B, C, D, F

class ClaudeMdManager:
    """CLAUDE.md 智能管理器"""

    def __init__(self, claude_md_path: str = None):
        self.claude_md_path = claude_md_path or "/home/xx/dev/Perfect21/CLAUDE.md"
        self.metadata_path = self.claude_md_path.replace('.md', '_metadata.json')
        self.history_path = self.claude_md_path.replace('.md', '_history.json')
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict[str, ContentMetadata]:
        """加载内容元数据"""
        if os.path.exists(self.metadata_path):
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {k: ContentMetadata(**v) for k, v in data.items()}
        return {}

    def _save_metadata(self):
        """保存内容元数据"""
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            data = {k: asdict(v) for k, v in self.metadata.items()}
            json.dump(data, f, indent=2, ensure_ascii=False)

    def analyze_content_stability(self, content_lines: List[str]) -> Dict[str, str]:
        """分析内容稳定性，自动分类固定/动态内容"""

        # 固定内容标识符
        fixed_indicators = [
            r'## 🎯 项目本质',
            r'### 🔑 不变的核心理念',
            r'## 🚀 基本使用',
            r'## 🏗️.*架构',
            r'## 📁 扩展规则',
            r'core.*不可修改',
            r'不重复造轮子',
            r'智能编排器',
        ]

        # 动态内容标识符
        dynamic_indicators = [
            r'## 📊 当前状态',
            r'### 🚀 版本信息',
            r'### 🔧.*状态',
            r'当前版本.*v\d+\.\d+\.\d+',
            r'最后更新.*\d{4}-\d{2}-\d{2}',
            r'✅.*正常',
            r'🔍.*开发重点',
        ]

        # 易变内容标识符 (经常变化的临时信息)
        volatile_indicators = [
            r'### 📋.*更新',
            r'近期.*',
            r'当前.*重点',
            r'TODO',
            r'正在.*',
            r'计划.*',
        ]

        classification = {}

        for i, line in enumerate(content_lines):
            line_key = f"line_{i}"

            # 检查固定内容
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in fixed_indicators):
                classification[line_key] = 'fixed'
            # 检查易变内容
            elif any(re.search(pattern, line, re.IGNORECASE) for pattern in volatile_indicators):
                classification[line_key] = 'volatile'
            # 检查动态内容
            elif any(re.search(pattern, line, re.IGNORECASE) for pattern in dynamic_indicators):
                classification[line_key] = 'dynamic'
            # 基于HTML注释判断
            elif '<!-- =====' in line and '固定核心' in line:
                classification[line_key] = 'fixed'
            elif '<!-- =====' in line and '动态状态' in line:
                classification[line_key] = 'dynamic'
            else:
                # 继承上下文类型
                prev_type = 'fixed'  # 默认为固定
                for j in range(max(0, i-5), i):
                    prev_key = f"line_{j}"
                    if prev_key in classification:
                        prev_type = classification[prev_key]
                        break
                classification[line_key] = prev_type

        return classification

    def assess_content_lifecycle(self, content_hash: str) -> str:
        """评估内容生命周期阶段"""
        if content_hash not in self.metadata:
            return 'active'

        meta = self.metadata[content_hash]
        last_modified = datetime.fromisoformat(meta.last_modified)
        days_since_modified = (datetime.now() - last_modified).days

        # 基于修改频率和时间判断生命周期
        if days_since_modified <= 7:
            return 'active'
        elif days_since_modified <= 30:
            return 'aging'
        elif days_since_modified <= 90:
            return 'stale'
        else:
            return 'obsolete'

    def calculate_document_health(self) -> DocumentHealth:
        """计算文档健康度"""
        if not os.path.exists(self.claude_md_path):
            return DocumentHealth(0, 0, 0, 0, 0, 0, 'F')

        with open(self.claude_md_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        total_lines = len(lines)
        classification = self.analyze_content_stability(lines)

        # 计算各类型内容比例
        fixed_count = sum(1 for t in classification.values() if t == 'fixed')
        dynamic_count = sum(1 for t in classification.values() if t == 'dynamic')
        volatile_count = sum(1 for t in classification.values() if t == 'volatile')

        fixed_ratio = fixed_count / total_lines if total_lines > 0 else 0
        dynamic_ratio = dynamic_count / total_lines if total_lines > 0 else 0
        volatile_ratio = volatile_count / total_lines if total_lines > 0 else 0

        # 计算陈旧度分数 (动态内容过期程度)
        staleness_score = 0
        if self.metadata:
            stale_count = sum(1 for meta in self.metadata.values()
                            if meta.lifecycle_stage in ['stale', 'obsolete'])
            staleness_score = stale_count / len(self.metadata)

        # 计算冗余度分数 (内容长度 vs 信息密度)
        redundancy_score = min(1.0, total_lines / 100)  # 超过100行认为开始冗余

        # 综合健康度评级
        health_score = (
            fixed_ratio * 0.3 +           # 固定内容比例 (30%)
            (1 - volatile_ratio) * 0.2 +  # 易变内容少 (20%)
            (1 - staleness_score) * 0.3 + # 内容新鲜度 (30%)
            (1 - redundancy_score) * 0.2  # 简洁度 (20%)
        )

        if health_score >= 0.9:
            health_grade = 'A'
        elif health_score >= 0.8:
            health_grade = 'B'
        elif health_score >= 0.7:
            health_grade = 'C'
        elif health_score >= 0.6:
            health_grade = 'D'
        else:
            health_grade = 'F'

        return DocumentHealth(
            total_lines=total_lines,
            fixed_ratio=fixed_ratio,
            dynamic_ratio=dynamic_ratio,
            volatile_ratio=volatile_ratio,
            staleness_score=staleness_score,
            redundancy_score=redundancy_score,
            health_grade=health_grade
        )

    def auto_cleanup_stale_content(self) -> List[str]:
        """自动清理陈旧内容"""
        cleanup_actions = []

        if not os.path.exists(self.claude_md_path):
            return cleanup_actions

        with open(self.claude_md_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        new_lines = []
        removed_sections = []

        for i, line in enumerate(lines):
            line_hash = hashlib.md5(line.encode()).hexdigest()

            # 检查是否为陈旧的动态内容
            if line_hash in self.metadata:
                meta = self.metadata[line_hash]
                if meta.lifecycle_stage == 'obsolete' and meta.content_type in ['dynamic', 'volatile']:
                    removed_sections.append(f"行 {i+1}: {line.strip()}")
                    cleanup_actions.append(f"删除过期内容: {line.strip()[:50]}...")
                    continue

            # 检查重复的版本信息
            if re.search(r'v\d+\.\d+\.\d+', line) and any(re.search(r'v\d+\.\d+\.\d+', prev) for prev in new_lines[-3:]):
                cleanup_actions.append(f"删除重复版本信息: {line.strip()}")
                continue

            new_lines.append(line)

        # 如果有清理动作，写回文件
        if cleanup_actions:
            with open(self.claude_md_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)

            # 记录清理历史
            self._record_cleanup_history(cleanup_actions)

        return cleanup_actions

    def _record_cleanup_history(self, actions: List[str]):
        """记录清理历史"""
        history = []
        if os.path.exists(self.history_path):
            with open(self.history_path, 'r', encoding='utf-8') as f:
                history = json.load(f)

        history.append({
            'timestamp': datetime.now().isoformat(),
            'actions': actions,
            'type': 'auto_cleanup'
        })

        # 只保留最近30次清理记录
        history = history[-30:]

        with open(self.history_path, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

    def generate_health_report(self) -> str:
        """生成文档健康度报告"""
        health = self.calculate_document_health()

        report = f"""
# CLAUDE.md 健康度报告

## 📊 整体评级: {health.health_grade}

### 📈 内容分布
- 固定内容: {health.fixed_ratio:.1%} ({health.fixed_ratio * health.total_lines:.0f} 行)
- 动态内容: {health.dynamic_ratio:.1%} ({health.dynamic_ratio * health.total_lines:.0f} 行)
- 易变内容: {health.volatile_ratio:.1%} ({health.volatile_ratio * health.total_lines:.0f} 行)

### 🔍 质量指标
- 总行数: {health.total_lines}
- 陈旧度: {health.staleness_score:.1%}
- 冗余度: {health.redundancy_score:.1%}

### 💡 建议
"""

        if health.health_grade in ['D', 'F']:
            report += "- ⚠️  文档需要紧急整理\n"
            report += "- 🧹 运行自动清理: `claude_md_manager.auto_cleanup_stale_content()`\n"

        if health.volatile_ratio > 0.3:
            report += "- 📝 易变内容过多，考虑移至单独的状态文件\n"

        if health.redundancy_score > 0.8:
            report += "- ✂️  文档过长，建议精简重复内容\n"

        return report.strip()

def main():
    """CLI入口"""
    import sys

    manager = ClaudeMdManager()

    if len(sys.argv) < 2:
        print("用法: python manager.py [health|cleanup|report]")
        return

    command = sys.argv[1]

    if command == 'health':
        health = manager.calculate_document_health()
        print(f"文档健康度: {health.health_grade}")
        print(f"总行数: {health.total_lines}")
        print(f"固定内容: {health.fixed_ratio:.1%}")
        print(f"动态内容: {health.dynamic_ratio:.1%}")

    elif command == 'cleanup':
        actions = manager.auto_cleanup_stale_content()
        if actions:
            print(f"已清理 {len(actions)} 项陈旧内容:")
            for action in actions:
                print(f"  - {action}")
        else:
            print("无需清理")

    elif command == 'report':
        print(manager.generate_health_report())

    else:
        print(f"未知命令: {command}")

if __name__ == '__main__':
    main()