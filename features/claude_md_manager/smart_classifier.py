#!/usr/bin/env python3
"""
Smart Classifier - 智能内容分类器

基于语义理解和模板匹配的智能内容分类系统，
能够准确识别文档中的固定、动态、易变内容。
"""

import os
import re
import json
import hashlib
from typing import Dict, List, Tuple, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from difflib import SequenceMatcher

@dataclass
class ContentSegment:
    """内容片段"""
    id: str
    content: str
    type: str  # 'fixed', 'dynamic', 'volatile'
    confidence: float
    start_line: int
    end_line: int
    fingerprint: str
    last_seen: str
    change_frequency: int
    semantic_tags: List[str]

@dataclass
class ClassificationRule:
    """分类规则"""
    name: str
    pattern: str
    content_type: str
    confidence: float
    semantic_indicators: List[str]
    anti_patterns: List[str] = None

class SmartClassifier:
    """智能内容分类器"""

    def __init__(self, project_root: str = None):
        # 智能检测项目根目录
        if project_root is None:
            current_file = os.path.abspath(__file__)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))

        self.project_root = project_root
        self.memory_file = os.path.join(project_root, 'features', 'claude_md_manager', 'classification_memory.json')

        # 加载分类记忆
        self.memory = self._load_memory()

        # 定义分类规则
        self.rules = self._define_classification_rules()

    def _define_classification_rules(self) -> List[ClassificationRule]:
        """定义分类规则"""
        return [
            # 固定内容规则
            ClassificationRule(
                name="project_identity",
                pattern=r"项目身份|核心原则|智能编排器",
                content_type="fixed",
                confidence=0.95,
                semantic_indicators=["项目", "定义", "本质", "原则"]
            ),
            ClassificationRule(
                name="core_concepts",
                pattern=r"项目本质|核心理念|不变.*理念",
                content_type="fixed",
                confidence=0.9,
                semantic_indicators=["本质", "理念", "不变", "永远", "核心"]
            ),
            ClassificationRule(
                name="basic_usage",
                pattern=r"基本使用|python3 main/cli\.py",
                content_type="fixed",
                confidence=0.85,
                semantic_indicators=["使用", "命令", "python3", "cli.py"]
            ),
            ClassificationRule(
                name="architecture",
                pattern=r"架构|目录结构|Perfect21/",
                content_type="fixed",
                confidence=0.8,
                semantic_indicators=["架构", "结构", "目录", "代码", "模块"]
            ),
            ClassificationRule(
                name="extension_rules",
                pattern=r"扩展规则|新功能.*features",
                content_type="fixed",
                confidence=0.85,
                semantic_indicators=["扩展", "规则", "features", "新功能"]
            ),

            # 动态内容规则
            ClassificationRule(
                name="version_info",
                pattern=r"当前版本.*v\d+\.\d+\.\d+|最后更新.*\d{4}-\d{2}-\d{2}",
                content_type="dynamic",
                confidence=0.95,
                semantic_indicators=["版本", "更新", "日期", "时间"],
                anti_patterns=[r"版本控制", r"版本管理"]
            ),
            ClassificationRule(
                name="module_status",
                pattern=r"模块状态|✅\s*正常|❌\s*异常",
                content_type="dynamic",
                confidence=0.9,
                semantic_indicators=["状态", "模块", "正常", "异常", "运行"]
            ),
            ClassificationRule(
                name="current_status",
                pattern=r"当前状态|系统状态|生产就绪",
                content_type="dynamic",
                confidence=0.85,
                semantic_indicators=["当前", "状态", "系统", "生产"]
            ),

            # 易变内容规则
            ClassificationRule(
                name="temp_info",
                pattern=r"TODO|FIXME|临时|测试中",
                content_type="volatile",
                confidence=0.9,
                semantic_indicators=["TODO", "临时", "测试", "修复", "待办"]
            ),
            ClassificationRule(
                name="recent_updates",
                pattern=r"近期.*更新|最新.*变更|刚刚.*",
                content_type="volatile",
                confidence=0.85,
                semantic_indicators=["近期", "最新", "刚刚", "新增", "变更"]
            ),
            ClassificationRule(
                name="doc_meta",
                pattern=r"文档说明|请勿.*修改|可随时更新",
                content_type="volatile",
                confidence=0.8,
                semantic_indicators=["文档", "说明", "修改", "更新"]
            )
        ]

    def classify_content(self, content: str) -> List[ContentSegment]:
        """分类内容"""
        segments = []
        lines = content.split('\n')

        # 按章节分割
        sections = self._split_into_sections(lines)

        for section in sections:
            segment = self._classify_section(section)
            if segment:
                segments.append(segment)

        # 更新分类记忆
        self._update_memory(segments)

        return segments

    def _split_into_sections(self, lines: List[str]) -> List[Dict]:
        """按章节分割内容"""
        sections = []
        current_section = None

        for i, line in enumerate(lines):
            # 标题行
            if line.startswith('#') and not line.startswith('<!--'):
                if current_section:
                    sections.append(current_section)

                # 确定标题级别
                level = 0
                for char in line:
                    if char == '#':
                        level += 1
                    else:
                        break

                current_section = {
                    'title': line.lstrip('#').strip(),
                    'level': level,
                    'start_line': i,
                    'content_lines': [line],
                    'raw_content': line
                }

            # HTML注释标记
            elif '<!-- =====' in line:
                if current_section:
                    sections.append(current_section)

                current_section = {
                    'title': 'separator_comment',
                    'level': 0,
                    'start_line': i,
                    'content_lines': [line],
                    'raw_content': line,
                    'is_separator': True
                }
                sections.append(current_section)
                current_section = None

            # 普通内容行
            else:
                if current_section:
                    current_section['content_lines'].append(line)
                    current_section['raw_content'] += '\n' + line

        if current_section:
            sections.append(current_section)

        return sections

    def _classify_section(self, section: Dict) -> Optional[ContentSegment]:
        """分类单个章节"""
        if section.get('is_separator'):
            # 分隔符注释
            if '固定核心' in section['raw_content']:
                return self._create_segment(section, 'fixed', 1.0, ['separator', 'fixed_marker'])
            elif '动态状态' in section['raw_content']:
                return self._create_segment(section, 'dynamic', 1.0, ['separator', 'dynamic_marker'])
            return None

        content = section['raw_content']
        title = section['title']

        # 规则匹配
        best_match = None
        best_confidence = 0

        for rule in self.rules:
            confidence = self._evaluate_rule(rule, content, title)
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = rule

        # 历史记忆匹配
        memory_result = self._check_memory_match(content)
        if memory_result and memory_result['confidence'] > best_confidence:
            best_confidence = memory_result['confidence']
            content_type = memory_result['type']
            semantic_tags = memory_result.get('tags', [])
        else:
            content_type = best_match.content_type if best_match else 'unknown'
            semantic_tags = best_match.semantic_indicators if best_match else []

        # 语义分析增强
        semantic_boost = self._semantic_analysis(content, title)
        final_confidence = min(best_confidence + semantic_boost, 1.0)

        return self._create_segment(section, content_type, final_confidence, semantic_tags)

    def _evaluate_rule(self, rule: ClassificationRule, content: str, title: str) -> float:
        """评估规则匹配度"""
        confidence = 0

        # 模式匹配
        if re.search(rule.pattern, content, re.IGNORECASE):
            confidence += rule.confidence * 0.6

        if re.search(rule.pattern, title, re.IGNORECASE):
            confidence += rule.confidence * 0.4

        # 反模式检查
        if rule.anti_patterns:
            for anti_pattern in rule.anti_patterns:
                if re.search(anti_pattern, content, re.IGNORECASE):
                    confidence *= 0.5  # 大幅降低置信度

        # 语义指标检查
        semantic_matches = 0
        for indicator in rule.semantic_indicators:
            if indicator.lower() in content.lower():
                semantic_matches += 1

        if semantic_matches > 0:
            semantic_ratio = semantic_matches / len(rule.semantic_indicators)
            confidence += semantic_ratio * 0.3

        return min(confidence, 1.0)

    def _semantic_analysis(self, content: str, title: str) -> float:
        """语义分析增强"""
        boost = 0
        content_lower = content.lower()
        title_lower = title.lower()

        # 固定内容指标
        fixed_indicators = [
            '不变', '永远', '始终', '核心', '本质', '原则',
            '定义', '架构', '设计', '规则', '基本'
        ]

        # 动态内容指标
        dynamic_indicators = [
            '当前', '最新', '状态', '版本', '更新', '运行',
            '正常', '异常', '✅', '❌', '数据'
        ]

        # 易变内容指标
        volatile_indicators = [
            '临时', '待定', 'todo', '计划', '即将', '测试',
            '调试', '开发中', '修复', '改进'
        ]

        # 计算各类型指标密度
        fixed_count = sum(1 for ind in fixed_indicators if ind in content_lower or ind in title_lower)
        dynamic_count = sum(1 for ind in dynamic_indicators if ind in content_lower or ind in title_lower)
        volatile_count = sum(1 for ind in volatile_indicators if ind in content_lower or ind in title_lower)

        total_indicators = fixed_count + dynamic_count + volatile_count
        if total_indicators > 0:
            # 根据指标分布给出语义增强
            if fixed_count > dynamic_count and fixed_count > volatile_count:
                boost = 0.1  # 偏向固定
            elif dynamic_count > volatile_count:
                boost = 0.05  # 偏向动态
            else:
                boost = 0.02  # 偏向易变

        return boost

    def _create_segment(self, section: Dict, content_type: str, confidence: float, semantic_tags: List[str]) -> ContentSegment:
        """创建内容片段"""
        content = section['raw_content']
        fingerprint = hashlib.md5(content.encode()).hexdigest()

        return ContentSegment(
            id=f"{content_type}_{section['start_line']}_{fingerprint[:8]}",
            content=content,
            type=content_type,
            confidence=confidence,
            start_line=section['start_line'],
            end_line=section['start_line'] + len(section['content_lines']) - 1,
            fingerprint=fingerprint,
            last_seen=datetime.now().isoformat(),
            change_frequency=self._get_change_frequency(fingerprint),
            semantic_tags=semantic_tags
        )

    def _get_change_frequency(self, fingerprint: str) -> int:
        """获取内容变更频率"""
        if fingerprint in self.memory:
            return self.memory[fingerprint].get('change_count', 0)
        return 0

    def _check_memory_match(self, content: str) -> Optional[Dict]:
        """检查记忆匹配"""
        fingerprint = hashlib.md5(content.encode()).hexdigest()

        if fingerprint in self.memory:
            memory_item = self.memory[fingerprint]
            # 时效性检查
            last_seen = datetime.fromisoformat(memory_item['last_seen'])
            days_old = (datetime.now() - last_seen).days

            if days_old < 30:  # 30天内的记忆有效
                return {
                    'type': memory_item['type'],
                    'confidence': memory_item['confidence'] * (1 - days_old * 0.01),  # 时间衰减
                    'tags': memory_item.get('tags', [])
                }

        # 相似度匹配
        for stored_fingerprint, stored_data in self.memory.items():
            if stored_data.get('content'):
                similarity = self._calculate_similarity(content, stored_data['content'])
                if similarity > 0.8:  # 80%相似度
                    return {
                        'type': stored_data['type'],
                        'confidence': stored_data['confidence'] * similarity * 0.8,
                        'tags': stored_data.get('tags', [])
                    }

        return None

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def _update_memory(self, segments: List[ContentSegment]):
        """更新分类记忆"""
        for segment in segments:
            if segment.fingerprint in self.memory:
                # 更新现有记忆
                self.memory[segment.fingerprint]['last_seen'] = segment.last_seen
                self.memory[segment.fingerprint]['change_count'] += 1
                # 置信度学习调整
                old_confidence = self.memory[segment.fingerprint]['confidence']
                self.memory[segment.fingerprint]['confidence'] = (old_confidence + segment.confidence) / 2
            else:
                # 创建新记忆
                self.memory[segment.fingerprint] = {
                    'type': segment.type,
                    'confidence': segment.confidence,
                    'first_seen': segment.last_seen,
                    'last_seen': segment.last_seen,
                    'change_count': 1,
                    'content': segment.content[:200],  # 存储前200字符用于相似度匹配
                    'tags': segment.semantic_tags
                }

        self._save_memory()

    def _load_memory(self) -> Dict:
        """加载分类记忆"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save_memory(self):
        """保存分类记忆"""
        # 清理过期记忆（超过6个月）
        cutoff_date = datetime.now() - timedelta(days=180)
        cleaned_memory = {}

        for fingerprint, data in self.memory.items():
            try:
                last_seen = datetime.fromisoformat(data['last_seen'])
                if last_seen > cutoff_date:
                    cleaned_memory[fingerprint] = data
            except:
                pass  # 跳过无效数据

        self.memory = cleaned_memory

        # 保存到文件
        os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.memory, f, indent=2, ensure_ascii=False)

    def get_classification_report(self, segments: List[ContentSegment]) -> Dict:
        """生成分类报告"""
        report = {
            'total_segments': len(segments),
            'by_type': {'fixed': 0, 'dynamic': 0, 'volatile': 0, 'unknown': 0},
            'confidence_distribution': {'high': 0, 'medium': 0, 'low': 0},
            'segments_detail': []
        }

        for segment in segments:
            # 按类型统计
            report['by_type'][segment.type] += 1

            # 按置信度统计
            if segment.confidence >= 0.8:
                report['confidence_distribution']['high'] += 1
            elif segment.confidence >= 0.5:
                report['confidence_distribution']['medium'] += 1
            else:
                report['confidence_distribution']['low'] += 1

            # 详细信息
            report['segments_detail'].append({
                'id': segment.id,
                'type': segment.type,
                'confidence': round(segment.confidence, 3),
                'lines': f"{segment.start_line}-{segment.end_line}",
                'content_preview': segment.content[:100] + "..." if len(segment.content) > 100 else segment.content,
                'tags': segment.semantic_tags
            })

        return report

if __name__ == "__main__":
    # 测试智能分类器
    classifier = SmartClassifier()

    # 测试内容
    test_content = """# Perfect21 项目核心文档

> 🎯 **项目身份**: Perfect21 - 智能编排器

## 🎯 项目本质

Perfect21 = **智能编排器** + claude-code-unified-agents

### 🔑 不变的核心理念
- **不重复造轮子**: 永远优先使用官方Agent

## 📊 当前状态

### 🚀 版本信息
- **当前版本**: v2.3.0 (生产就绪)
- **最后更新**: 2025-09-16

### 🔧 模块状态
- **capability_discovery**: ✅ 正常"""

    segments = classifier.classify_content(test_content)
    report = classifier.get_classification_report(segments)

    print("=== 分类结果 ===")
    print(f"总段落数: {report['total_segments']}")
    print(f"固定: {report['by_type']['fixed']}, 动态: {report['by_type']['dynamic']}, 易变: {report['by_type']['volatile']}")
    print(f"高置信度: {report['confidence_distribution']['high']}")

    print("\n=== 详细分类 ===")
    for detail in report['segments_detail']:
        print(f"[{detail['type'].upper()}] {detail['confidence']:.2f} - {detail['content_preview'][:50]}...")