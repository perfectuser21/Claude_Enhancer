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

class ContentAnalyzer:
    """内容分析器"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or os.getcwd()

        # 内容区块类型定义
        self.block_types = {
            'static': ['项目概述', '核心理念', '设计原则', '文件管理规则'],
            'dynamic': ['系统架构', '使用方法', '版本更新', '技术指标'],
            'meta': ['最后更新', '版本', '系统状态']
        }

        # 快速记忆模式
        self.memory_patterns = {
            'command': r'#.*(?:命令|command|cmd).*',
            'preference': r'#.*(?:偏好|preference|setting).*',
            'note': r'#.*(?:注意|note|memo).*',
            'rule': r'#.*(?:规则|rule|guideline).*'
        }

    def analyze_claude_md(self, file_path: str = None) -> Dict[str, Any]:
        """分析CLAUDE.md文件"""
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

            analysis = {
                'success': True,
                'file_path': file_path,
                'file_size': len(content),
                'line_count': len(content.split('\n')),
                'analysis_timestamp': datetime.now().isoformat(),
                'structure': self._analyze_structure(content),
                'content_blocks': self._identify_content_blocks(content),
                'dynamic_content': self._identify_dynamic_content(content),
                'quick_memories': self._extract_quick_memories(content),
                'metadata': self._extract_metadata(content),
                'quality_score': self._calculate_quality_score(content)
            }

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

        # 完整性评分 (0-25)
        required_sections = ['项目概述', '系统架构', '使用方法', '技术实现']
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

        # 结构性评分 (0-25)
        structure = self._analyze_structure(content)
        if structure['total_headers'] >= 5:
            score_details['structure'] = 25
        elif structure['total_headers'] >= 3:
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