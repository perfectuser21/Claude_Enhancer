#!/usr/bin/env python3
"""
DocGate Agent - 文档质量分析专家
专门负责文档质量分析、自动生成摘要、相似度检测和改进建议

核心功能：
1. 文档质量分析 - 评估文档的完整性、可读性、结构
2. 自动生成摘要 - 提取关键信息生成简洁摘要
3. 相似度检测 - 检测重复内容和相似文档
4. 改进建议 - 提供具体的优化建议

作为独立Agent，不调用其他Agent，避免嵌套调用问题
"""

import os
import re
import json
import hashlib
import difflib
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter, defaultdict
from dataclasses import dataclass
import math


@dataclass
class DocumentMetrics:
    """文档指标"""
    word_count: int
    sentence_count: int
    paragraph_count: int
    heading_count: int
    link_count: int
    image_count: int
    code_block_count: int
    table_count: int
    readability_score: float
    structure_score: float
    completeness_score: float
    quality_score: float


@dataclass
class SimilarityResult:
    """相似度检测结果"""
    document_a: str
    document_b: str
    similarity_ratio: float
    common_lines: List[str]
    similarity_type: str  # 'identical', 'high', 'medium', 'low'


@dataclass
class QualityIssue:
    """质量问题"""
    type: str
    severity: str  # 'critical', 'major', 'minor'
    location: str
    description: str
    suggestion: str


class DocGateAgent:
    """DocGate Agent - 文档质量分析专家"""

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = project_root or os.environ.get(
            "CLAUDE_PROJECT_DIR", "/home/xx/dev/Claude Enhancer 5.0"
        )
        self.cache_dir = Path(self.project_root) / ".claude" / "docgate_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 质量标准配置
        self.quality_standards = {
            'min_word_count': 100,
            'max_word_count': 5000,
            'min_headings': 2,
            'max_sentence_length': 25,
            'min_paragraph_sentences': 2,
            'max_paragraph_sentences': 6,
            'similarity_threshold': 0.8,
            'readability_target': 70  # Flesch Reading Ease target
        }

        # 文档类型模式
        self.doc_patterns = {
            'readme': r'readme\.md$',
            'api_doc': r'api\.md$|swagger\.md$',
            'changelog': r'changelog\.md$|changes\.md$',
            'install': r'install\.md$|setup\.md$',
            'config': r'config\.md$|configuration\.md$',
            'guide': r'guide\.md$|tutorial\.md$',
            'reference': r'reference\.md$|ref\.md$'
        }

    def analyze_document_quality(self, file_path: str) -> Dict[str, Any]:
        """分析单个文档的质量"""
        try:
            if not os.path.exists(file_path):
                return {'error': f'File not found: {file_path}'}

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 计算基础指标
            metrics = self._calculate_metrics(content)

            # 检测质量问题
            issues = self._detect_quality_issues(content, file_path)

            # 生成改进建议
            suggestions = self._generate_suggestions(metrics, issues)

            # 分析文档类型
            doc_type = self._detect_document_type(file_path)

            # 计算总体质量评分
            overall_score = self._calculate_overall_score(metrics, issues)

            return {
                'file_path': file_path,
                'document_type': doc_type,
                'metrics': metrics.__dict__,
                'overall_score': overall_score,
                'quality_level': self._get_quality_level(overall_score),
                'issues': [issue.__dict__ for issue in issues],
                'suggestions': suggestions,
                'analysis_timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {'error': f'Analysis failed: {str(e)}'}

    def generate_document_summary(self, file_path: str, max_sentences: int = 3) -> Dict[str, Any]:
        """生成文档摘要"""
        try:
            if not os.path.exists(file_path):
                return {'error': f'File not found: {file_path}'}

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取关键信息
            title = self._extract_title(content)
            key_points = self._extract_key_points(content)
            summary_sentences = self._generate_summary_sentences(content, max_sentences)

            # 提取元数据
            metadata = self._extract_metadata(content)

            return {
                'file_path': file_path,
                'title': title,
                'summary': ' '.join(summary_sentences),
                'key_points': key_points,
                'metadata': metadata,
                'word_count': len(content.split()),
                'estimated_reading_time': self._estimate_reading_time(content),
                'summary_timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {'error': f'Summary generation failed: {str(e)}'}

    def detect_document_similarity(self, documents: List[str]) -> List[SimilarityResult]:
        """检测文档间的相似度"""
        results = []

        try:
            # 读取所有文档内容
            doc_contents = {}
            for doc_path in documents:
                if os.path.exists(doc_path):
                    with open(doc_path, 'r', encoding='utf-8') as f:
                        doc_contents[doc_path] = f.read()

            # 计算两两相似度
            doc_list = list(doc_contents.items())
            for i in range(len(doc_list)):
                for j in range(i + 1, len(doc_list)):
                    path_a, content_a = doc_list[i]
                    path_b, content_b = doc_list[j]

                    similarity = self._calculate_similarity(content_a, content_b)
                    # 创建新的SimilarityResult对象
                    result = SimilarityResult(
                        document_a=path_a,
                        document_b=path_b,
                        similarity_ratio=similarity.similarity_ratio,
                        common_lines=similarity.common_lines,
                        similarity_type=similarity.similarity_type
                    )
                    results.append(result)

            # 按相似度排序
            results.sort(key=lambda x: x.similarity_ratio, reverse=True)

            return results

        except Exception as e:
            return [SimilarityResult(
                document_a='', document_b='', similarity_ratio=0.0,
                common_lines=[], similarity_type=f'error: {str(e)}'
            )]

    def analyze_documentation_coverage(self, project_path: str) -> Dict[str, Any]:
        """分析项目文档覆盖度"""
        try:
            project_path = Path(project_path)

            # 查找所有代码文件和文档文件
            code_files = self._find_code_files(project_path)
            doc_files = self._find_documentation_files(project_path)

            # 分析文档覆盖度
            coverage_analysis = self._analyze_coverage(code_files, doc_files)

            # 检查缺失的文档
            missing_docs = self._find_missing_documentation(project_path)

            # 生成文档结构图
            doc_structure = self._analyze_doc_structure(doc_files)

            return {
                'project_path': str(project_path),
                'total_code_files': len(code_files),
                'total_doc_files': len(doc_files),
                'coverage_percentage': coverage_analysis['coverage_percentage'],
                'coverage_details': coverage_analysis,
                'missing_documentation': missing_docs,
                'documentation_structure': doc_structure,
                'recommendations': self._generate_coverage_recommendations(coverage_analysis, missing_docs),
                'analysis_timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {'error': f'Coverage analysis failed: {str(e)}'}

    def batch_analyze_documents(self, file_patterns: List[str]) -> Dict[str, Any]:
        """批量分析文档"""
        results = {
            'analyzed_files': [],
            'summary_statistics': {},
            'quality_distribution': {},
            'common_issues': [],
            'global_recommendations': []
        }

        try:
            # 查找匹配的文件
            all_files = []
            for pattern in file_patterns:
                files = self._find_files_by_pattern(pattern)
                all_files.extend(files)

            # 去重
            all_files = list(set(all_files))

            # 分析每个文件
            quality_scores = []
            all_issues = []

            for file_path in all_files:
                analysis = self.analyze_document_quality(file_path)
                if 'error' not in analysis:
                    results['analyzed_files'].append(analysis)
                    quality_scores.append(analysis['overall_score'])
                    all_issues.extend(analysis['issues'])

            # 计算统计信息
            if quality_scores:
                results['summary_statistics'] = {
                    'total_documents': len(quality_scores),
                    'average_quality': statistics.mean(quality_scores),
                    'median_quality': statistics.median(quality_scores),
                    'quality_std_dev': statistics.stdev(quality_scores) if len(quality_scores) > 1 else 0,
                    'highest_quality': max(quality_scores),
                    'lowest_quality': min(quality_scores)
                }

            # 分析质量分布
            results['quality_distribution'] = self._analyze_quality_distribution(quality_scores)

            # 分析常见问题
            results['common_issues'] = self._analyze_common_issues(all_issues)

            # 生成全局建议
            results['global_recommendations'] = self._generate_global_recommendations(
                results['summary_statistics'], results['common_issues']
            )

            return results

        except Exception as e:
            return {'error': f'Batch analysis failed: {str(e)}'}

    def _calculate_metrics(self, content: str) -> DocumentMetrics:
        """计算文档指标"""
        # 基础计数
        words = re.findall(r'\b\w+\b', content)
        sentences = re.split(r'[.!?]+', content)
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]

        # Markdown元素计数
        headings = re.findall(r'^#{1,6}\s+', content, re.MULTILINE)
        links = re.findall(r'\[([^\]]+)\]\([^)]+\)', content)
        images = re.findall(r'!\[([^\]]*)\]\([^)]+\)', content)
        code_blocks = re.findall(r'```[^`]*```', content, re.DOTALL)
        tables = re.findall(r'\|.*\|', content)

        # 计算各种分数
        readability_score = self._calculate_readability_score(content)
        structure_score = self._calculate_structure_score(content)
        completeness_score = self._calculate_completeness_score(content)

        # 综合质量分数
        quality_score = (readability_score + structure_score + completeness_score) / 3

        return DocumentMetrics(
            word_count=len(words),
            sentence_count=len([s for s in sentences if s.strip()]),
            paragraph_count=len(paragraphs),
            heading_count=len(headings),
            link_count=len(links),
            image_count=len(images),
            code_block_count=len(code_blocks),
            table_count=len(tables),
            readability_score=readability_score,
            structure_score=structure_score,
            completeness_score=completeness_score,
            quality_score=quality_score
        )

    def _calculate_readability_score(self, content: str) -> float:
        """计算可读性分数（简化版Flesch Reading Ease）"""
        words = re.findall(r'\b\w+\b', content)
        sentences = re.split(r'[.!?]+', content)
        sentences = [s for s in sentences if s.strip()]

        if not sentences or not words:
            return 0.0

        # 计算平均句长和平均音节数（简化）
        avg_sentence_length = len(words) / len(sentences)
        avg_syllables = sum(self._count_syllables(word) for word in words) / len(words)

        # 简化的Flesch公式
        score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables)

        # 归一化到0-100
        return max(0, min(100, score))

    def _count_syllables(self, word: str) -> int:
        """简单的音节计数（英文）"""
        word = word.lower()
        if not word:
            return 0

        vowels = 'aeiouy'
        syllable_count = 0
        prev_was_vowel = False

        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_was_vowel:
                syllable_count += 1
            prev_was_vowel = is_vowel

        # 如果以e结尾，减去1（英文规则）
        if word.endswith('e') and syllable_count > 1:
            syllable_count -= 1

        return max(1, syllable_count)

    def _calculate_structure_score(self, content: str) -> float:
        """计算结构分数"""
        score = 0.0
        max_score = 100.0

        # 检查是否有标题
        headings = re.findall(r'^#{1,6}\s+', content, re.MULTILINE)
        if headings:
            score += 20

            # 检查标题层次结构
            heading_levels = [len(h.split()[0]) for h in headings]
            if len(set(heading_levels)) > 1:  # 有不同层次的标题
                score += 15

        # 检查段落结构
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        if len(paragraphs) >= 3:
            score += 15

        # 检查是否有链接
        links = re.findall(r'\[([^\]]+)\]\([^)]+\)', content)
        if links:
            score += 10

        # 检查是否有代码示例
        code_blocks = re.findall(r'```[^`]*```', content, re.DOTALL)
        if code_blocks:
            score += 15

        # 检查是否有列表
        lists = re.findall(r'^[-*]\s+', content, re.MULTILINE)
        if lists:
            score += 10

        # 检查是否有表格
        tables = re.findall(r'\|.*\|', content)
        if tables:
            score += 15

        return min(max_score, score)

    def _calculate_completeness_score(self, content: str) -> float:
        """计算完整性分数"""
        score = 0.0
        max_score = 100.0

        # 检查文档长度
        word_count = len(re.findall(r'\b\w+\b', content))
        if word_count >= self.quality_standards['min_word_count']:
            score += 20

        # 检查是否有介绍部分
        intro_patterns = [r'^#{1,2}\s+(介绍|Introduction|Overview|简介)', r'^.*(?:是什么|what is|概述)']
        if any(re.search(pattern, content, re.MULTILINE | re.IGNORECASE) for pattern in intro_patterns):
            score += 15

        # 检查是否有使用说明
        usage_patterns = [r'^#{1,3}\s+(使用|Usage|How to|安装|Installation)']
        if any(re.search(pattern, content, re.MULTILINE | re.IGNORECASE) for pattern in usage_patterns):
            score += 15

        # 检查是否有示例
        example_patterns = [r'```', r'^#{1,3}\s+(示例|Example|例子)']
        if any(re.search(pattern, content, re.MULTILINE | re.IGNORECASE) for pattern in example_patterns):
            score += 20

        # 检查是否有联系信息或贡献指南
        contact_patterns = [r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', r'github\.com', r'贡献|contribute']
        if any(re.search(pattern, content, re.IGNORECASE) for pattern in contact_patterns):
            score += 10

        # 检查是否有更新日期
        date_patterns = [r'\d{4}-\d{2}-\d{2}', r'\d{4}/\d{2}/\d{2}', r'更新|updated|修订|revised']
        if any(re.search(pattern, content, re.IGNORECASE) for pattern in date_patterns):
            score += 10

        # 检查目录或大纲
        toc_patterns = [r'^#{1,2}\s+(目录|Table of Contents|TOC)', r'^\s*[-*]\s+\[.*\]\(#']
        if any(re.search(pattern, content, re.MULTILINE | re.IGNORECASE) for pattern in toc_patterns):
            score += 10

        return min(max_score, score)

    def _detect_quality_issues(self, content: str, file_path: str) -> List[QualityIssue]:
        """检测质量问题"""
        issues = []

        # 检查文档长度
        word_count = len(re.findall(r'\b\w+\b', content))
        if word_count < self.quality_standards['min_word_count']:
            issues.append(QualityIssue(
                type='length',
                severity='major',
                location='document',
                description=f'文档太短，只有{word_count}个单词',
                suggestion=f'建议至少{self.quality_standards["min_word_count"]}个单词'
            ))
        elif word_count > self.quality_standards['max_word_count']:
            issues.append(QualityIssue(
                type='length',
                severity='minor',
                location='document',
                description=f'文档过长，有{word_count}个单词',
                suggestion='考虑分割成多个文档或添加目录'
            ))

        # 检查标题结构
        headings = re.findall(r'^(#{1,6})\s+(.+)', content, re.MULTILINE)
        if len(headings) < self.quality_standards['min_headings']:
            issues.append(QualityIssue(
                type='structure',
                severity='major',
                location='document',
                description='缺少足够的标题结构',
                suggestion='添加至少2个标题来组织内容'
            ))

        # 检查过长的句子
        sentences = re.split(r'[.!?]+', content)
        for i, sentence in enumerate(sentences):
            words = re.findall(r'\b\w+\b', sentence)
            if len(words) > self.quality_standards['max_sentence_length']:
                issues.append(QualityIssue(
                    type='readability',
                    severity='minor',
                    location=f'sentence {i+1}',
                    description=f'句子过长（{len(words)}个单词）',
                    suggestion='考虑分解为多个较短的句子'
                ))

        # 检查断链
        links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
        for link_text, link_url in links:
            if link_url.startswith('http') and not self._check_url_accessible(link_url):
                issues.append(QualityIssue(
                    type='links',
                    severity='major',
                    location=f'link: {link_text}',
                    description=f'链接可能失效: {link_url}',
                    suggestion='检查并更新链接地址'
                ))

        # 检查重复内容
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        for i, para1 in enumerate(paragraphs):
            for j, para2 in enumerate(paragraphs[i+1:], i+1):
                similarity = difflib.SequenceMatcher(None, para1, para2).ratio()
                if similarity > 0.8:
                    issues.append(QualityIssue(
                        type='duplication',
                        severity='minor',
                        location=f'paragraphs {i+1} and {j+1}',
                        description='发现重复或高度相似的段落',
                        suggestion='合并或重写重复的内容'
                    ))

        return issues

    def _check_url_accessible(self, url: str) -> bool:
        """检查URL是否可访问（简化版）"""
        # 这里简化处理，实际应该发送HTTP请求
        # 由于我们不想添加网络依赖，这里只做基本检查
        return not any(indicator in url.lower() for indicator in ['example.com', 'localhost', '127.0.0.1'])

    def _generate_suggestions(self, metrics: DocumentMetrics, issues: List[QualityIssue]) -> List[str]:
        """生成改进建议"""
        suggestions = []

        # 基于指标的建议
        if metrics.readability_score < 50:
            suggestions.append('提高可读性：使用更简单的词汇和更短的句子')

        if metrics.structure_score < 60:
            suggestions.append('改进文档结构：添加更多标题、列表和代码示例')

        if metrics.completeness_score < 70:
            suggestions.append('完善文档内容：添加使用示例、安装说明或贡献指南')

        # 基于问题的建议
        issue_types = [issue.type for issue in issues]
        if 'length' in issue_types:
            suggestions.append('调整文档长度：确保内容充实但不冗长')

        if 'structure' in issue_types:
            suggestions.append('优化文档结构：使用适当的标题层次')

        if 'links' in issue_types:
            suggestions.append('检查所有链接：确保外部链接有效')

        if 'duplication' in issue_types:
            suggestions.append('消除重复内容：合并相似的段落')

        # 通用建议
        if not suggestions:
            suggestions.append('文档质量良好，继续保持！')

        return suggestions

    def _detect_document_type(self, file_path: str) -> str:
        """检测文档类型"""
        file_name = os.path.basename(file_path).lower()

        for doc_type, pattern in self.doc_patterns.items():
            if re.search(pattern, file_name, re.IGNORECASE):
                return doc_type

        return 'general'

    def _calculate_overall_score(self, metrics: DocumentMetrics, issues: List[QualityIssue]) -> float:
        """计算总体质量评分"""
        base_score = metrics.quality_score

        # 根据问题严重性扣分
        for issue in issues:
            if issue.severity == 'critical':
                base_score -= 15
            elif issue.severity == 'major':
                base_score -= 8
            elif issue.severity == 'minor':
                base_score -= 3

        return max(0, min(100, base_score))

    def _get_quality_level(self, score: float) -> str:
        """获取质量等级"""
        if score >= 90:
            return 'excellent'
        elif score >= 80:
            return 'good'
        elif score >= 70:
            return 'fair'
        elif score >= 60:
            return 'poor'
        else:
            return 'very_poor'

    def _extract_title(self, content: str) -> str:
        """提取文档标题"""
        # 查找第一个标题
        title_match = re.search(r'^#\s+(.+)', content, re.MULTILINE)
        if title_match:
            return title_match.group(1).strip()

        # 查找文件名形式的标题
        title_match = re.search(r'^(.+)\n=+\s*$', content, re.MULTILINE)
        if title_match:
            return title_match.group(1).strip()

        # 取第一行作为标题
        first_line = content.split('\n')[0].strip()
        if first_line and len(first_line) < 100:
            return first_line

        return 'Untitled Document'

    def _extract_key_points(self, content: str) -> List[str]:
        """提取关键要点"""
        key_points = []

        # 提取列表项
        list_items = re.findall(r'^[-*]\s+(.+)', content, re.MULTILINE)
        key_points.extend(list_items[:5])  # 最多5个

        # 提取二级标题
        headings = re.findall(r'^##\s+(.+)', content, re.MULTILINE)
        key_points.extend(headings[:3])  # 最多3个

        # 提取重点标记的内容
        bold_text = re.findall(r'\*\*([^*]+)\*\*', content)
        key_points.extend(bold_text[:3])

        return list(set(key_points))[:8]  # 去重，最多8个

    def _generate_summary_sentences(self, content: str, max_sentences: int) -> List[str]:
        """生成摘要句子"""
        sentences = re.split(r'[.!?]+', content)
        sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 20]

        if len(sentences) <= max_sentences:
            return sentences

        # 简单的摘要算法：选择最有代表性的句子
        # 1. 包含关键词的句子
        # 2. 位置靠前的句子
        # 3. 中等长度的句子

        scored_sentences = []
        for i, sentence in enumerate(sentences):
            score = 0

            # 位置权重（越靠前越重要）
            score += (len(sentences) - i) / len(sentences) * 30

            # 长度权重（中等长度最佳）
            word_count = len(sentence.split())
            if 10 <= word_count <= 20:
                score += 20
            elif 5 <= word_count <= 30:
                score += 10

            # 关键词权重
            keywords = ['是', 'is', '提供', 'provide', '支持', 'support', '功能', 'feature']
            for keyword in keywords:
                if keyword in sentence.lower():
                    score += 15

            scored_sentences.append((score, sentence))

        # 按分数排序并选择前N个
        scored_sentences.sort(reverse=True)
        return [sentence for _, sentence in scored_sentences[:max_sentences]]

    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """提取文档元数据"""
        metadata = {}

        # 查找YAML front matter
        yaml_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
        if yaml_match:
            # 简单解析YAML（不使用外部库）
            yaml_content = yaml_match.group(1)
            for line in yaml_content.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()

        # 查找常见的元数据模式
        patterns = {
            'author': r'(?:author|作者)[:：]\s*(.+)',
            'date': r'(?:date|日期|更新时间)[:：]\s*(\d{4}[-/]\d{2}[-/]\d{2})',
            'version': r'(?:version|版本)[:：]\s*([v\d.]+)',
            'tags': r'(?:tags|标签)[:：]\s*(.+)'
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                metadata[key] = match.group(1).strip()

        return metadata

    def _estimate_reading_time(self, content: str) -> str:
        """估算阅读时间"""
        words = re.findall(r'\b\w+\b', content)
        # 平均阅读速度：200字/分钟
        minutes = len(words) / 200

        if minutes < 1:
            return f"{int(minutes * 60)} seconds"
        elif minutes < 60:
            return f"{int(minutes)} minutes"
        else:
            hours = int(minutes // 60)
            remaining_minutes = int(minutes % 60)
            return f"{hours}h {remaining_minutes}m"

    def _calculate_similarity(self, content_a: str, content_b: str) -> SimilarityResult:
        """计算两个文档的相似度"""
        # 预处理文本
        lines_a = [line.strip() for line in content_a.split('\n') if line.strip()]
        lines_b = [line.strip() for line in content_b.split('\n') if line.strip()]

        # 计算序列相似度
        seq_matcher = difflib.SequenceMatcher(None, lines_a, lines_b)
        similarity_ratio = seq_matcher.ratio()

        # 找出相同的行
        common_lines = []
        for tag, i1, i2, j1, j2 in seq_matcher.get_opcodes():
            if tag == 'equal':
                common_lines.extend(lines_a[i1:i2])

        # 确定相似度类型
        if similarity_ratio >= 0.95:
            similarity_type = 'identical'
        elif similarity_ratio >= 0.8:
            similarity_type = 'high'
        elif similarity_ratio >= 0.5:
            similarity_type = 'medium'
        else:
            similarity_type = 'low'

        return SimilarityResult(
            document_a='',  # 将在调用时设置
            document_b='',  # 将在调用时设置
            similarity_ratio=similarity_ratio,
            common_lines=common_lines[:10],  # 最多显示10行
            similarity_type=similarity_type
        )

    def _find_code_files(self, project_path) -> List[str]:
        """查找代码文件"""
        code_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs', '.php', '.rb'}
        code_files = []

        # 确保project_path是Path对象
        if isinstance(project_path, str):
            project_path = Path(project_path)

        for file_path in project_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in code_extensions:
                code_files.append(str(file_path))

        return code_files

    def _find_documentation_files(self, project_path) -> List[str]:
        """查找文档文件"""
        doc_extensions = {'.md', '.rst', '.txt', '.adoc'}
        doc_files = []

        # 确保project_path是Path对象
        if isinstance(project_path, str):
            project_path = Path(project_path)

        for file_path in project_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in doc_extensions:
                doc_files.append(str(file_path))

        return doc_files

    def _analyze_coverage(self, code_files: List[str], doc_files: List[str]) -> Dict[str, Any]:
        """分析文档覆盖度"""
        # 简化的覆盖度分析
        total_files = len(code_files)
        documented_files = 0

        # 检查每个代码文件是否有对应的文档
        for code_file in code_files:
            code_path = Path(code_file)
            # 查找同目录下的README或同名的.md文件
            possible_docs = [
                code_path.parent / 'README.md',
                code_path.with_suffix('.md'),
                code_path.parent / f"{code_path.stem}.md"
            ]

            if any(str(doc_path) in doc_files for doc_path in possible_docs):
                documented_files += 1

        coverage_percentage = (documented_files / total_files * 100) if total_files > 0 else 0

        return {
            'coverage_percentage': coverage_percentage,
            'total_code_files': total_files,
            'documented_files': documented_files,
            'undocumented_files': total_files - documented_files
        }

    def _find_missing_documentation(self, project_path: Path) -> List[str]:
        """查找缺失的文档"""
        missing_docs = []

        # 检查标准文档文件
        standard_docs = ['README.md', 'CHANGELOG.md', 'CONTRIBUTING.md', 'LICENSE.md', 'API.md']
        for doc_name in standard_docs:
            doc_path = project_path / doc_name
            if not doc_path.exists():
                missing_docs.append(doc_name)

        return missing_docs

    def _analyze_doc_structure(self, doc_files: List[str]) -> Dict[str, Any]:
        """分析文档结构"""
        structure = {
            'total_files': len(doc_files),
            'by_type': defaultdict(int),
            'by_directory': defaultdict(int)
        }

        for doc_file in doc_files:
            file_path = Path(doc_file)

            # 按类型分类
            doc_type = self._detect_document_type(doc_file)
            structure['by_type'][doc_type] += 1

            # 按目录分类
            directory = str(file_path.parent)
            structure['by_directory'][directory] += 1

        return dict(structure)

    def _generate_coverage_recommendations(self, coverage_analysis: Dict[str, Any], missing_docs: List[str]) -> List[str]:
        """生成覆盖度建议"""
        recommendations = []

        coverage = coverage_analysis['coverage_percentage']

        if coverage < 30:
            recommendations.append('文档覆盖度严重不足，建议为主要模块添加文档')
        elif coverage < 60:
            recommendations.append('文档覆盖度偏低，建议增加API文档和使用指南')
        elif coverage < 80:
            recommendations.append('文档覆盖度良好，可以完善详细说明和示例')

        if missing_docs:
            recommendations.append(f'建议添加缺失的标准文档：{", ".join(missing_docs)}')

        if coverage_analysis['undocumented_files'] > 0:
            recommendations.append(f'有{coverage_analysis["undocumented_files"]}个代码文件缺少文档')

        return recommendations

    def _find_files_by_pattern(self, pattern: str) -> List[str]:
        """按模式查找文件"""
        project_path = Path(self.project_root)
        matching_files = []

        try:
            if '*' in pattern or '?' in pattern:
                # Glob模式
                matching_files = [str(p) for p in project_path.rglob(pattern) if p.is_file()]
            else:
                # 精确匹配或扩展名匹配
                if pattern.startswith('.'):
                    # 扩展名匹配
                    matching_files = [str(p) for p in project_path.rglob(f'*{pattern}') if p.is_file()]
                else:
                    # 文件名匹配
                    matching_files = [str(p) for p in project_path.rglob(f'*{pattern}*') if p.is_file()]
        except Exception:
            pass

        return matching_files

    def _analyze_quality_distribution(self, quality_scores: List[float]) -> Dict[str, int]:
        """分析质量分布"""
        distribution = {
            'excellent': 0,  # 90+
            'good': 0,       # 80-89
            'fair': 0,       # 70-79
            'poor': 0,       # 60-69
            'very_poor': 0   # <60
        }

        for score in quality_scores:
            if score >= 90:
                distribution['excellent'] += 1
            elif score >= 80:
                distribution['good'] += 1
            elif score >= 70:
                distribution['fair'] += 1
            elif score >= 60:
                distribution['poor'] += 1
            else:
                distribution['very_poor'] += 1

        return distribution

    def _analyze_common_issues(self, all_issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """分析常见问题"""
        issue_counter = Counter()
        severity_counter = Counter()

        for issue in all_issues:
            issue_type = issue['type']
            severity = issue['severity']

            issue_counter[issue_type] += 1
            severity_counter[severity] += 1

        return [
            {
                'type': 'most_common_issues',
                'data': dict(issue_counter.most_common(5))
            },
            {
                'type': 'severity_distribution',
                'data': dict(severity_counter)
            }
        ]

    def _generate_global_recommendations(self, statistics: Dict[str, Any], common_issues: List[Dict[str, Any]]) -> List[str]:
        """生成全局建议"""
        recommendations = []

        if not statistics:
            return ['无法生成建议，缺少统计数据']

        avg_quality = statistics.get('average_quality', 0)

        if avg_quality < 60:
            recommendations.append('整体文档质量较低，建议制定文档规范和改进计划')
        elif avg_quality < 80:
            recommendations.append('文档质量中等，建议重点改进低质量文档')
        else:
            recommendations.append('文档质量良好，继续保持并持续优化')

        # 基于常见问题的建议
        for issue_analysis in common_issues:
            if issue_analysis['type'] == 'most_common_issues':
                top_issues = list(issue_analysis['data'].keys())[:3]
                if top_issues:
                    recommendations.append(f'重点关注这些问题类型：{", ".join(top_issues)}')

        quality_std = statistics.get('quality_std_dev', 0)
        if quality_std > 20:
            recommendations.append('文档质量差异较大，建议统一标准和模板')

        return recommendations

    def generate_quality_report(self, output_file: Optional[str] = None) -> str:
        """生成质量报告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = output_file or str(self.cache_dir / f'docgate_quality_report_{timestamp}.md')

        # 分析项目中的所有文档
        doc_files = self._find_documentation_files(Path(self.project_root))
        batch_result = self.batch_analyze_documents(['*.md', '*.rst', '*.txt'])

        # 生成报告内容
        report_content = f"""# DocGate 文档质量分析报告

## 📊 生成信息
- **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **分析路径**: {self.project_root}
- **DocGate版本**: 1.0.0

## 📈 总体统计

"""

        if 'summary_statistics' in batch_result and batch_result['summary_statistics']:
            stats = batch_result['summary_statistics']
            report_content += f"""
- **文档总数**: {stats.get('total_documents', 0)}
- **平均质量**: {stats.get('average_quality', 0):.1f}/100
- **质量中位数**: {stats.get('median_quality', 0):.1f}/100
- **最高质量**: {stats.get('highest_quality', 0):.1f}/100
- **最低质量**: {stats.get('lowest_quality', 0):.1f}/100
- **质量标准差**: {stats.get('quality_std_dev', 0):.1f}

"""

        # 质量分布
        if 'quality_distribution' in batch_result:
            dist = batch_result['quality_distribution']
            report_content += """## 📊 质量分布

| 质量等级 | 文档数量 | 百分比 |
|----------|----------|--------|
"""
            total_docs = sum(dist.values()) if dist else 1
            for level, count in dist.items():
                percentage = count / total_docs * 100
                report_content += f"| {level} | {count} | {percentage:.1f}% |\n"

        # 常见问题
        if 'common_issues' in batch_result and batch_result['common_issues']:
            report_content += "\n## ⚠️ 常见问题\n\n"
            for issue_analysis in batch_result['common_issues']:
                if issue_analysis['type'] == 'most_common_issues':
                    report_content += "### 问题类型分布\n\n"
                    for issue_type, count in issue_analysis['data'].items():
                        report_content += f"- **{issue_type}**: {count}次\n"
                elif issue_analysis['type'] == 'severity_distribution':
                    report_content += "\n### 严重程度分布\n\n"
                    for severity, count in issue_analysis['data'].items():
                        report_content += f"- **{severity}**: {count}个问题\n"

        # 改进建议
        if 'global_recommendations' in batch_result and batch_result['global_recommendations']:
            report_content += "\n## 💡 改进建议\n\n"
            for i, recommendation in enumerate(batch_result['global_recommendations'], 1):
                report_content += f"{i}. {recommendation}\n"

        # 详细文档分析
        if 'analyzed_files' in batch_result and batch_result['analyzed_files']:
            report_content += "\n## 📋 详细文档分析\n\n"
            for doc in batch_result['analyzed_files'][:10]:  # 只显示前10个
                quality_level = doc.get('quality_level', 'unknown')
                overall_score = doc.get('overall_score', 0)
                file_path = doc.get('file_path', '').replace(self.project_root, '')

                report_content += f"### {file_path}\n\n"
                report_content += f"- **质量评分**: {overall_score:.1f}/100 ({quality_level})\n"
                report_content += f"- **文档类型**: {doc.get('document_type', 'unknown')}\n"

                metrics = doc.get('metrics', {})
                if metrics:
                    report_content += f"- **字数**: {metrics.get('word_count', 0)}\n"
                    report_content += f"- **可读性**: {metrics.get('readability_score', 0):.1f}/100\n"
                    report_content += f"- **结构性**: {metrics.get('structure_score', 0):.1f}/100\n"

                issues = doc.get('issues', [])
                if issues:
                    report_content += "- **主要问题**:\n"
                    for issue in issues[:3]:  # 只显示前3个问题
                        report_content += f"  - {issue.get('description', 'Unknown issue')}\n"

                report_content += "\n"

        # 写入文件
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)

        return report_file


def main():
    """主函数 - 演示DocGate Agent的功能"""
    docgate = DocGateAgent()

    print("🚀 DocGate Agent - 文档质量分析专家")
    print("=" * 50)

    # 演示功能
    sample_doc = "/home/xx/dev/Claude Enhancer 5.0/README.md"

    if os.path.exists(sample_doc):
        print(f"\n📖 分析文档: {sample_doc}")

        # 质量分析
        quality_result = docgate.analyze_document_quality(sample_doc)
        if 'error' not in quality_result:
            print(f"✅ 质量评分: {quality_result['overall_score']:.1f}/100")
            print(f"✅ 质量等级: {quality_result['quality_level']}")

        # 生成摘要
        summary_result = docgate.generate_document_summary(sample_doc)
        if 'error' not in summary_result:
            print(f"✅ 摘要: {summary_result['summary'][:100]}...")

    # 生成项目报告
    print(f"\n📊 生成项目质量报告...")
    report_file = docgate.generate_quality_report()
    print(f"✅ 报告已保存: {report_file}")

    print("\n🎉 DocGate Agent 演示完成!")


if __name__ == "__main__":
    main()