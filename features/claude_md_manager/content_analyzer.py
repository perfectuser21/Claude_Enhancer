#!/usr/bin/env python3
"""
Content Analyzer - 内容分析器
智能分析CLAUDE.md内容，识别静态和动态区块，支持Claude Code的#快速记忆功能
"""

import os
import re
import json
from typing import Dict, Any, List, Tuple, Set
from datetime import datetime

# 导入新组件
try:
    from .template_engine import TemplateEngine
    from .smart_classifier import SmartClassifier, ContentSegment
    from .lifecycle_manager import LifecycleManager
except ImportError:
    # 向后兼容
    TemplateEngine = None
    SmartClassifier = None
    ContentSegment = None
    LifecycleManager = None

class ContentAnalyzer:
    """内容分析器"""

    def __init__(self, project_root: str = None):
        # 智能检测项目根目录
        if project_root is None:
            # 从当前文件位置推断项目根目录
            current_file = os.path.abspath(__file__)
            # features/claude_md_manager/content_analyzer.py -> 向上2级
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
        self.project_root = project_root

        # 初始化新组件（如果可用）
        self.template_engine = TemplateEngine(project_root) if TemplateEngine else None
        self.smart_classifier = SmartClassifier(project_root) if SmartClassifier else None
        self.lifecycle_manager = LifecycleManager(project_root) if LifecycleManager else None

        # 启用智能分析
        self.use_smart_analysis = all([self.template_engine, self.smart_classifier, self.lifecycle_manager])

        # 内容区块类型定义
        self.block_types = {
            'static': ['项目本质', '核心理念', '设计原则', '基本使用', '简化架构', '扩展规则'],
            'dynamic': ['当前状态', '版本信息', '模块状态', '系统状态', '技术指标'],
            'meta': ['最后更新', '版本', '文档说明']
        }

        # 快速记忆模式
        self.memory_patterns = {
            'command': r'#.*(?:命令|command|cmd).*',
            'preference': r'#.*(?:偏好|preference|setting).*',
            'note': r'#.*(?:注意|note|memo).*',
            'rule': r'#.*(?:规则|rule|guideline).*'
        }

    def analyze_claude_md(self, file_path: str = None) -> Dict[str, Any]:
        """分析CLAUDE.md文件（增强版）"""
        if file_path is None:
            file_path = os.path.join(self.project_root, 'CLAUDE.md')

        try:
            if not os.path.exists(file_path):
                return {
                    'success': False,
                    'error': '文件不存在',
                    'file_path': file_path
                }

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 基础分析
            analysis = {
                'success': True,
                'file_path': file_path,
                'file_size': len(content),
                'line_count': len(content.split('\n')),
                'analysis_timestamp': datetime.now().isoformat(),
                'analysis_mode': 'smart' if self.use_smart_analysis else 'legacy',
                'structure': self._analyze_structure(content),
                'content_blocks': self._identify_content_blocks(content),
                'dynamic_content': self._identify_dynamic_content(content),
                'quick_memories': self._extract_quick_memories(content),
                'metadata': self._extract_metadata(content),
                'quality_score': self._calculate_quality_score(content)
            }

            # 智能分析增强
            if self.use_smart_analysis:
                analysis.update(self._smart_analysis_enhancement(content))

            return analysis

        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path
            }

    def _analyze_structure(self, content: str) -> Dict[str, Any]:
        """分析文档结构"""
        lines = content.split('\n')
        structure = {
            'headers': [],
            'sections': {},
            'header_hierarchy': []
        }

        current_section = None
        section_content = []

        for i, line in enumerate(lines):
            if line.startswith('#'):
                # 处理上一个section
                if current_section:
                    structure['sections'][current_section] = {
                        'content': '\n'.join(section_content),
                        'line_count': len(section_content),
                        'start_line': i - len(section_content)
                    }

                # 新section
                header_level = len(line) - len(line.lstrip('#'))
                header_text = line.lstrip('# ').strip()

                header_info = {
                    'level': header_level,
                    'text': header_text,
                    'line_number': i + 1
                }

                structure['headers'].append(header_info)
                structure['header_hierarchy'].append(header_level)

                current_section = header_text
                section_content = []
            else:
                if current_section:
                    section_content.append(line)

        # 处理最后一个section
        if current_section:
            structure['sections'][current_section] = {
                'content': '\n'.join(section_content),
                'line_count': len(section_content),
                'start_line': len(lines) - len(section_content)
            }

        # 统计信息
        structure['total_headers'] = len(structure['headers'])
        structure['max_depth'] = max(structure['header_hierarchy']) if structure['header_hierarchy'] else 0
        structure['total_sections'] = len(structure['sections'])

        return structure

    def _identify_content_blocks(self, content: str) -> Dict[str, List[str]]:
        """识别内容区块类型"""
        blocks = {
            'static': [],
            'dynamic': [],
            'meta': [],
            'unknown': []
        }

        structure = self._analyze_structure(content)

        for section_name, section_info in structure['sections'].items():
            block_type = self._classify_section(section_name, section_info['content'])
            blocks[block_type].append(section_name)

        return blocks

    def _classify_section(self, section_name: str, section_content: str) -> str:
        """分类section类型"""
        section_lower = section_name.lower()

        # 检查静态内容
        for static_keyword in self.block_types['static']:
            if static_keyword in section_name or static_keyword.lower() in section_lower:
                return 'static'

        # 检查动态内容
        for dynamic_keyword in self.block_types['dynamic']:
            if dynamic_keyword in section_name or dynamic_keyword.lower() in section_lower:
                return 'dynamic'

        # 检查元数据
        for meta_keyword in self.block_types['meta']:
            if meta_keyword in section_name or meta_keyword.lower() in section_lower:
                return 'meta'

        # 通过内容特征判断
        if self._has_dynamic_indicators(section_content):
            return 'dynamic'

        return 'unknown'

    def _has_dynamic_indicators(self, content: str) -> bool:
        """检查是否有动态内容指标"""
        dynamic_indicators = [
            r'版本.*\d+\.\d+\.\d+',
            r'\d{4}-\d{2}-\d{2}',  # 日期
            r'最后更新',
            r'系统状态',
            r'功能模块.*\d+',
            r'Agent.*\d+'
        ]

        for pattern in dynamic_indicators:
            if re.search(pattern, content):
                return True

        return False

    def _identify_dynamic_content(self, content: str) -> List[Dict[str, Any]]:
        """识别具体的动态内容位置"""
        dynamic_elements = []

        # 版本信息
        version_matches = re.finditer(r'(\*?版本:.*Perfect21\s+v?[\d\.]+)', content)
        for match in version_matches:
            dynamic_elements.append({
                'type': 'version_info',
                'content': match.group(1),
                'start': match.start(),
                'end': match.end(),
                'updatable': True
            })

        # 时间戳
        time_matches = re.finditer(r'(\*?最后更新:.*\d{4}-\d{2}-\d{2})', content)
        for match in time_matches:
            dynamic_elements.append({
                'type': 'timestamp',
                'content': match.group(1),
                'start': match.start(),
                'end': match.end(),
                'updatable': True
            })

        # 统计数字
        stats_matches = re.finditer(r'(\*?.*:?\s*\d+\s*个)', content)
        for match in stats_matches:
            dynamic_elements.append({
                'type': 'statistics',
                'content': match.group(1),
                'start': match.start(),
                'end': match.end(),
                'updatable': True
            })

        return dynamic_elements

    def _extract_quick_memories(self, content: str) -> List[Dict[str, Any]]:
        """提取快速记忆（#指令）"""
        memories = []

        # 查找以#开头的行（Claude Code快速记忆格式）
        lines = content.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith('#') and not line.startswith('##'):  # 排除markdown标题
                memory_type = self._classify_memory(line)
                memories.append({
                    'line_number': i + 1,
                    'content': line,
                    'type': memory_type,
                    'timestamp': datetime.now().isoformat()
                })

        return memories

    def _classify_memory(self, memory_line: str) -> str:
        """分类快速记忆类型"""
        line_lower = memory_line.lower()

        for memory_type, pattern in self.memory_patterns.items():
            if re.search(pattern, line_lower):
                return memory_type

        return 'general'

    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """提取元数据"""
        metadata = {}

        # 项目信息
        project_info = re.search(r'\*\*项目名称\*\*:\s*(.+)', content)
        if project_info:
            metadata['project_name'] = project_info.group(1).strip()

        project_type = re.search(r'\*\*项目类型\*\*:\s*(.+)', content)
        if project_type:
            metadata['project_type'] = project_type.group(1).strip()

        # 技术栈
        tech_stack = re.search(r'\*\*技术栈\*\*:\s*(.+)', content)
        if tech_stack:
            metadata['tech_stack'] = tech_stack.group(1).strip()

        # 版本信息
        version = re.search(r'版本:\s*Perfect21\s+v?([\d\.]+)', content)
        if version:
            metadata['version'] = version.group(1)

        # 最后更新时间
        last_update = re.search(r'最后更新:\s*(\d{4}-\d{2}-\d{2})', content)
        if last_update:
            metadata['last_updated'] = last_update.group(1)

        return metadata

    def _calculate_quality_score(self, content: str) -> Dict[str, Any]:
        """计算文档质量评分"""
        score_details = {
            'completeness': 0,  # 完整性
            'freshness': 0,     # 时效性
            'structure': 0,     # 结构性
            'consistency': 0    # 一致性
        }

        # 完整性评分 (0-25) - 适应精简文档结构
        required_sections = ['项目本质', '基本使用', '当前状态']
        found_sections = 0
        for section in required_sections:
            if section in content:
                found_sections += 1
        score_details['completeness'] = (found_sections / len(required_sections)) * 25

        # 时效性评分 (0-25)
        metadata = self._extract_metadata(content)
        if 'last_updated' in metadata:
            try:
                last_update = datetime.strptime(metadata['last_updated'], '%Y-%m-%d')
                days_old = (datetime.now() - last_update).days
                if days_old <= 7:
                    score_details['freshness'] = 25
                elif days_old <= 30:
                    score_details['freshness'] = 15
                elif days_old <= 90:
                    score_details['freshness'] = 10
                else:
                    score_details['freshness'] = 5
            except:
                score_details['freshness'] = 10
        else:
            score_details['freshness'] = 0

        # 结构性评分 (0-25) - 精简文档友好
        structure = self._analyze_structure(content)
        line_count = len(content.split('\n'))

        # 精简文档：行数适中 + 结构清晰 = 高分
        if 50 <= line_count <= 100 and structure['total_headers'] >= 4:
            score_details['structure'] = 25
        elif 30 <= line_count <= 150 and structure['total_headers'] >= 3:
            score_details['structure'] = 20
        elif structure['total_headers'] >= 2:
            score_details['structure'] = 15
        else:
            score_details['structure'] = 10

        # 一致性评分 (0-25)
        dynamic_content = self._identify_dynamic_content(content)
        if len(dynamic_content) > 0:
            score_details['consistency'] = 20
        else:
            score_details['consistency'] = 10

        total_score = sum(score_details.values())

        return {
            'total_score': total_score,
            'max_score': 100,
            'percentage': total_score,
            'grade': self._get_grade(total_score),
            'details': score_details
        }

    def _get_grade(self, score: float) -> str:
        """获取质量等级"""
        if score >= 90:
            return 'A+'
        elif score >= 80:
            return 'A'
        elif score >= 70:
            return 'B'
        elif score >= 60:
            return 'C'
        else:
            return 'D'

    def suggest_improvements(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """建议改进措施"""
        suggestions = []

        quality = analysis.get('quality_score', {})
        details = quality.get('details', {})

        # 完整性建议
        if details.get('completeness', 0) < 20:
            suggestions.append({
                'type': 'completeness',
                'priority': 'high',
                'message': '文档缺少必要的核心章节',
                'action': '添加项目概述、系统架构、使用方法等核心章节'
            })

        # 时效性建议
        if details.get('freshness', 0) < 15:
            suggestions.append({
                'type': 'freshness',
                'priority': 'medium',
                'message': '文档更新不够及时',
                'action': '使用CLAUDE.md自动更新功能定期同步内容'
            })

        # 结构性建议
        if details.get('structure', 0) < 15:
            suggestions.append({
                'type': 'structure',
                'priority': 'medium',
                'message': '文档结构层次不够清晰',
                'action': '增加更多的章节标题，改善文档结构'
            })

        # 一致性建议
        if details.get('consistency', 0) < 15:
            suggestions.append({
                'type': 'consistency',
                'priority': 'high',
                'message': '缺少动态内容标记',
                'action': '启用自动更新功能，添加版本和时间戳信息'
            })

        return suggestions

    def _smart_analysis_enhancement(self, content: str) -> Dict[str, Any]:
        """智能分析增强"""
        enhancement = {}

        # 智能分类分析
        if self.smart_classifier:
            segments = self.smart_classifier.classify_content(content)
            classification_report = self.smart_classifier.get_classification_report(segments)

            enhancement['smart_classification'] = {
                'segments': [
                    {
                        'id': seg.id,
                        'type': seg.type,
                        'confidence': seg.confidence,
                        'content_preview': seg.content[:100] + "..." if len(seg.content) > 100 else seg.content,
                        'semantic_tags': seg.semantic_tags
                    }
                    for seg in segments
                ],
                'classification_report': classification_report
            }

        # 生命周期分析
        if self.lifecycle_manager:
            lifecycle_report = self.lifecycle_manager.generate_lifecycle_report()
            enhancement['lifecycle_analysis'] = lifecycle_report

            # 清理建议
            cleanup_actions = self.lifecycle_manager.suggest_cleanup_actions()
            enhancement['cleanup_suggestions'] = [
                {
                    'action': action.action_type,
                    'target': action.target_content,
                    'reason': action.reason,
                    'confidence': action.confidence
                }
                for action in cleanup_actions
            ]

        # 模板一致性检查
        if self.template_engine:
            template_analysis = self.template_engine.analyze_current_document()
            enhancement['template_compliance'] = {
                'has_fixed_marker': template_analysis.get('has_fixed_marker', False),
                'has_dynamic_marker': template_analysis.get('has_dynamic_marker', False),
                'detected_blocks': len(template_analysis.get('detected_blocks', [])),
                'size_bytes': template_analysis.get('size_bytes', 0)
            }

        # 综合健康度评估
        enhancement['comprehensive_health'] = self._calculate_comprehensive_health(content, enhancement)

        return enhancement

    def _calculate_comprehensive_health(self, content: str, enhancement: Dict[str, Any]) -> Dict[str, Any]:
        """计算综合健康度"""
        health_factors = {}
        total_score = 0
        max_score = 0

        # 基础质量分数 (40%)
        basic_quality = self._calculate_quality_score(content)
        basic_score = basic_quality['total_score']
        health_factors['basic_quality'] = basic_score
        total_score += basic_score * 0.4
        max_score += 100 * 0.4

        # 智能分类准确性 (25%)
        if 'smart_classification' in enhancement:
            classification = enhancement['smart_classification']['classification_report']
            high_confidence = classification['confidence_distribution'].get('high', 0)
            total_segments = classification['total_segments']
            if total_segments > 0:
                classification_score = (high_confidence / total_segments) * 100
            else:
                classification_score = 0
            health_factors['classification_accuracy'] = classification_score
            total_score += classification_score * 0.25
            max_score += 100 * 0.25

        # 生命周期健康度 (20%)
        if 'lifecycle_analysis' in enhancement:
            lifecycle = enhancement['lifecycle_analysis']
            status_summary = lifecycle['status_summary']
            total_items = lifecycle['total_content_items']
            if total_items > 0:
                active_ratio = status_summary.get('active', 0) / total_items
                lifecycle_score = active_ratio * 100
            else:
                lifecycle_score = 100  # 无内容项时认为健康
            health_factors['lifecycle_health'] = lifecycle_score
            total_score += lifecycle_score * 0.2
            max_score += 100 * 0.2

        # 模板一致性 (15%)
        if 'template_compliance' in enhancement:
            compliance = enhancement['template_compliance']
            compliance_score = 0
            if compliance.get('has_fixed_marker'):
                compliance_score += 50
            if compliance.get('has_dynamic_marker'):
                compliance_score += 50
            health_factors['template_compliance'] = compliance_score
            total_score += compliance_score * 0.15
            max_score += 100 * 0.15

        # 计算最终分数
        if max_score > 0:
            final_score = (total_score / max_score) * 100
        else:
            final_score = basic_quality['total_score']

        # 等级评定
        if final_score >= 90:
            grade = 'A+'
        elif final_score >= 85:
            grade = 'A'
        elif final_score >= 80:
            grade = 'B+'
        elif final_score >= 75:
            grade = 'B'
        elif final_score >= 70:
            grade = 'C+'
        elif final_score >= 65:
            grade = 'C'
        elif final_score >= 60:
            grade = 'D'
        else:
            grade = 'F'

        return {
            'final_score': round(final_score, 1),
            'grade': grade,
            'factors': health_factors,
            'recommendations': self._generate_health_recommendations(health_factors, final_score)
        }

    def _generate_health_recommendations(self, factors: Dict[str, float], final_score: float) -> List[str]:
        """生成健康度改进建议"""
        recommendations = []

        # 基于各项因子给出建议
        if factors.get('basic_quality', 0) < 70:
            recommendations.append("基础文档质量较低，建议检查完整性和结构")

        if factors.get('classification_accuracy', 0) < 80:
            recommendations.append("内容分类准确性不高，建议优化内容标记")

        if factors.get('lifecycle_health', 0) < 80:
            recommendations.append("存在过期内容，建议执行生命周期清理")

        if factors.get('template_compliance', 0) < 80:
            recommendations.append("模板一致性不佳，建议使用标准分隔标记")

        # 基于总分给出总体建议
        if final_score >= 90:
            recommendations.append("文档健康度优秀，继续保持")
        elif final_score >= 80:
            recommendations.append("文档健康度良好，可进行细节优化")
        elif final_score >= 70:
            recommendations.append("文档健康度一般，建议重点改进薄弱环节")
        else:
            recommendations.append("文档健康度较差，建议全面重构")

        return recommendations

if __name__ == "__main__":
    # 测试脚本
    analyzer = ContentAnalyzer()
    analysis = analyzer.analyze_claude_md()
    print(json.dumps(analysis, ensure_ascii=False, indent=2))

    if analysis['success']:
        suggestions = analyzer.suggest_improvements(analysis)
        print("\n=== 改进建议 ===")
        for suggestion in suggestions:
            print(f"[{suggestion['priority'].upper()}] {suggestion['message']}")
            print(f"   建议行动: {suggestion['action']}")
            print()