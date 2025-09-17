#!/usr/bin/env python3
"""
Perfect21 统一文档管理器
整合ClaudeMdManager, LifecycleManager, TemplateManager, ADRManager功能
提供统一的文档内容管理、生命周期跟踪、模板应用和架构决策记录服务

设计原则:
- 单一入口: 所有文档相关操作通过统一接口
- 功能内聚: 相关功能集中管理，避免分散
- 接口简化: 提供简洁的高级API，隐藏实现复杂性
- 向后兼容: 保持原有Manager的接口兼容性
"""

import os
import re
import json
import hashlib
import shutil
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# 配置日志
logger = logging.getLogger("Perfect21.DocumentManager")

# ================== 数据结构定义 ==================

class ContentType(Enum):
    """内容类型"""
    FIXED = "fixed"          # 固定内容
    DYNAMIC = "dynamic"      # 动态内容
    VOLATILE = "volatile"    # 易变内容

class LifecycleStage(Enum):
    """生命周期阶段"""
    ACTIVE = "active"        # 活跃
    AGING = "aging"          # 老化
    STALE = "stale"          # 陈旧
    OBSOLETE = "obsolete"    # 过期

class DocumentHealthGrade(Enum):
    """文档健康等级"""
    A = "excellent"      # 优秀
    B = "good"          # 良好
    C = "fair"          # 一般
    D = "poor"          # 较差
    F = "critical"      # 严重

@dataclass
class ContentMetadata:
    """内容元数据"""
    content_hash: str
    content_type: ContentType
    lifecycle_stage: LifecycleStage
    last_modified: datetime
    modification_count: int
    importance_score: float
    auto_cleanup: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'content_hash': self.content_hash,
            'content_type': self.content_type.value,
            'lifecycle_stage': self.lifecycle_stage.value,
            'last_modified': self.last_modified.isoformat(),
            'modification_count': self.modification_count,
            'importance_score': self.importance_score,
            'auto_cleanup': self.auto_cleanup
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContentMetadata':
        """从字典创建"""
        return cls(
            content_hash=data['content_hash'],
            content_type=ContentType(data['content_type']),
            lifecycle_stage=LifecycleStage(data['lifecycle_stage']),
            last_modified=datetime.fromisoformat(data['last_modified']),
            modification_count=data['modification_count'],
            importance_score=data['importance_score'],
            auto_cleanup=data.get('auto_cleanup', True)
        )

@dataclass
class DocumentHealth:
    """文档健康度评估"""
    total_lines: int
    fixed_ratio: float
    dynamic_ratio: float
    volatile_ratio: float
    staleness_score: float
    redundancy_score: float
    health_grade: DocumentHealthGrade
    recommendations: List[str]

@dataclass
class ArchitectureDecision:
    """架构决策记录"""
    id: str
    title: str
    status: str  # proposed, accepted, deprecated, superseded
    date: datetime
    context: str
    decision: str
    consequences: str
    alternatives: List[str]
    tags: List[str]

# ================== 核心组件类 ==================

class ContentAnalyzer:
    """内容分析器 (原ClaudeMdManager核心功能)"""

    def __init__(self):
        self.fixed_indicators = [
            r'## 🎯 项目本质',
            r'### 🔑 不变的核心理念',
            r'## 🚀 基本使用',
            r'## 🏗️.*架构',
            r'core.*不可修改',
            r'不重复造轮子',
        ]

        self.dynamic_indicators = [
            r'## 📊 当前状态',
            r'### 🚀 版本信息',
            r'### 🔧.*状态',
            r'当前版本.*v\d+\.\d+\.\d+',
            r'最后更新.*\d{4}-\d{2}-\d{2}',
            r'✅.*正常',
        ]

        self.volatile_indicators = [
            r'### 📋.*更新',
            r'近期.*',
            r'当前.*重点',
            r'TODO',
            r'正在.*',
            r'计划.*',
        ]

    def analyze_content_stability(self, content_lines: List[str]) -> Dict[str, ContentType]:
        """分析内容稳定性，自动分类固定/动态内容"""
        classification = {}

        for i, line in enumerate(content_lines):
            line_key = f"line_{i}"

            # 检查固定内容
            if any(re.search(pattern, line, re.IGNORECASE) for pattern in self.fixed_indicators):
                classification[line_key] = ContentType.FIXED
            # 检查易变内容
            elif any(re.search(pattern, line, re.IGNORECASE) for pattern in self.volatile_indicators):
                classification[line_key] = ContentType.VOLATILE
            # 检查动态内容
            elif any(re.search(pattern, line, re.IGNORECASE) for pattern in self.dynamic_indicators):
                classification[line_key] = ContentType.DYNAMIC
            # 基于HTML注释判断
            elif '<!-- =====' in line and '固定核心' in line:
                classification[line_key] = ContentType.FIXED
            elif '<!-- =====' in line and '动态状态' in line:
                classification[line_key] = ContentType.DYNAMIC
            else:
                # 继承上下文类型
                prev_type = ContentType.FIXED  # 默认为固定
                for j in range(max(0, i-5), i):
                    prev_key = f"line_{j}"
                    if prev_key in classification:
                        prev_type = classification[prev_key]
                        break
                classification[line_key] = prev_type

        return classification

    def calculate_document_health(self, file_path: str) -> DocumentHealth:
        """计算文档健康度"""
        if not os.path.exists(file_path):
            return DocumentHealth(0, 0, 0, 0, 1.0, 1.0, DocumentHealthGrade.F, ["文档不存在"])

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            total_lines = len(lines)
            classification = self.analyze_content_stability(lines)

            # 计算各类型内容比例
            fixed_count = sum(1 for t in classification.values() if t == ContentType.FIXED)
            dynamic_count = sum(1 for t in classification.values() if t == ContentType.DYNAMIC)
            volatile_count = sum(1 for t in classification.values() if t == ContentType.VOLATILE)

            fixed_ratio = fixed_count / total_lines if total_lines > 0 else 0
            dynamic_ratio = dynamic_count / total_lines if total_lines > 0 else 0
            volatile_ratio = volatile_count / total_lines if total_lines > 0 else 0

            # 计算陈旧度分数 (简化处理)
            staleness_score = 0.1 if volatile_ratio > 0.3 else 0

            # 计算冗余度分数
            redundancy_score = min(1.0, total_lines / 100)

            # 综合健康度评级
            health_score = (
                fixed_ratio * 0.3 +           # 固定内容比例 (30%)
                (1 - volatile_ratio) * 0.2 +  # 易变内容少 (20%)
                (1 - staleness_score) * 0.3 + # 内容新鲜度 (30%)
                (1 - redundancy_score) * 0.2  # 简洁度 (20%)
            )

            # 确定健康等级
            if health_score >= 0.9:
                health_grade = DocumentHealthGrade.A
            elif health_score >= 0.8:
                health_grade = DocumentHealthGrade.B
            elif health_score >= 0.7:
                health_grade = DocumentHealthGrade.C
            elif health_score >= 0.6:
                health_grade = DocumentHealthGrade.D
            else:
                health_grade = DocumentHealthGrade.F

            # 生成建议
            recommendations = []
            if health_grade in [DocumentHealthGrade.D, DocumentHealthGrade.F]:
                recommendations.append("文档需要紧急整理")
            if volatile_ratio > 0.3:
                recommendations.append("易变内容过多，考虑移至单独的状态文件")
            if redundancy_score > 0.8:
                recommendations.append("文档过长，建议精简重复内容")

            return DocumentHealth(
                total_lines=total_lines,
                fixed_ratio=fixed_ratio,
                dynamic_ratio=dynamic_ratio,
                volatile_ratio=volatile_ratio,
                staleness_score=staleness_score,
                redundancy_score=redundancy_score,
                health_grade=health_grade,
                recommendations=recommendations
            )

        except Exception as e:
            logger.error(f"计算文档健康度失败: {e}")
            return DocumentHealth(0, 0, 0, 0, 1.0, 1.0, DocumentHealthGrade.F, [f"分析失败: {str(e)}"])

class LifecycleTracker:
    """生命周期跟踪器 (原LifecycleManager核心功能)"""

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.metadata_file = self.data_dir / "content_metadata.json"
        self.snapshots_dir = self.data_dir / "snapshots"
        self.snapshots_dir.mkdir(exist_ok=True)

        self.metadata: Dict[str, ContentMetadata] = self._load_metadata()

    def _load_metadata(self) -> Dict[str, ContentMetadata]:
        """加载内容元数据"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {k: ContentMetadata.from_dict(v) for k, v in data.items()}
            except Exception as e:
                logger.error(f"加载元数据失败: {e}")
        return {}

    def _save_metadata(self):
        """保存内容元数据"""
        try:
            data = {k: v.to_dict() for k, v in self.metadata.items()}
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存元数据失败: {e}")

    def track_content_change(self, content_id: str, content_type: ContentType,
                           importance_score: float = 0.5):
        """跟踪内容变更"""
        now = datetime.now()

        if content_id in self.metadata:
            # 更新现有内容
            metadata = self.metadata[content_id]
            metadata.last_modified = now
            metadata.modification_count += 1
            metadata.lifecycle_stage = LifecycleStage.ACTIVE
        else:
            # 创建新内容记录
            content_hash = hashlib.md5(content_id.encode()).hexdigest()[:16]
            metadata = ContentMetadata(
                content_hash=content_hash,
                content_type=content_type,
                lifecycle_stage=LifecycleStage.ACTIVE,
                last_modified=now,
                modification_count=1,
                importance_score=importance_score
            )
            self.metadata[content_id] = metadata

        self._save_metadata()
        return metadata

    def evaluate_lifecycle_status(self) -> Dict[LifecycleStage, List[str]]:
        """评估所有内容的生命周期状态"""
        now = datetime.now()
        status_groups = {stage: [] for stage in LifecycleStage}

        for content_id, metadata in self.metadata.items():
            days_since_update = (now - metadata.last_modified).days

            # 根据内容类型和时间判断状态
            if metadata.content_type == ContentType.FIXED:
                # 固定内容特殊处理
                if days_since_update > 90:
                    metadata.lifecycle_stage = LifecycleStage.AGING
                else:
                    metadata.lifecycle_stage = LifecycleStage.ACTIVE
            elif metadata.content_type == ContentType.VOLATILE:
                # 易变内容
                if days_since_update > 7:
                    metadata.lifecycle_stage = LifecycleStage.OBSOLETE
                elif days_since_update > 3:
                    metadata.lifecycle_stage = LifecycleStage.STALE
                else:
                    metadata.lifecycle_stage = LifecycleStage.ACTIVE
            else:  # DYNAMIC
                # 动态内容
                if days_since_update > 30:
                    metadata.lifecycle_stage = LifecycleStage.OBSOLETE
                elif days_since_update > 7:
                    metadata.lifecycle_stage = LifecycleStage.STALE
                elif days_since_update > 3:
                    metadata.lifecycle_stage = LifecycleStage.AGING
                else:
                    metadata.lifecycle_stage = LifecycleStage.ACTIVE

            status_groups[metadata.lifecycle_stage].append(content_id)

        self._save_metadata()
        return status_groups

    def create_snapshot(self, content: str, version: str, change_summary: str) -> str:
        """创建内容快照"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        snapshot_filename = f"snapshot_{timestamp}.md"
        snapshot_path = self.snapshots_dir / snapshot_filename

        try:
            with open(snapshot_path, 'w', encoding='utf-8') as f:
                f.write(f"<!-- 快照元数据\n")
                f.write(f"时间: {timestamp}\n")
                f.write(f"版本: {version}\n")
                f.write(f"变更: {change_summary}\n")
                f.write(f"-->\n\n")
                f.write(content)

            logger.info(f"创建快照: {snapshot_filename}")
            return snapshot_filename

        except Exception as e:
            logger.error(f"创建快照失败: {e}")
            return ""

class TemplateEngine:
    """模板引擎 (原TemplateManager核心功能)"""

    def __init__(self, templates_dir: str):
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self._init_default_templates()

    def _init_default_templates(self):
        """初始化默认模板"""
        default_templates = {
            "claude_md_base.md": """# {{project_name}} 项目核心文档

> 🎯 **项目身份**: {{project_name}} - {{project_description}}
> 🔑 **核心原则**: {{core_principles}}

## 🎯 项目本质

{{project_essence}}

## 🚀 基本使用

{{usage_guide}}

## 📊 当前状态

### 🚀 版本信息
- **当前版本**: {{current_version}}
- **最后更新**: {{last_update}}

### 🔧 模块状态
{{module_status}}
""",
            "adr_template.md": """# ADR-{{adr_id}}: {{title}}

## 状态
{{status}}

## 日期
{{date}}

## 上下文
{{context}}

## 决策
{{decision}}

## 后果
{{consequences}}

## 备选方案
{{alternatives}}
""",
            "feature_doc.md": """# {{feature_name}} 功能文档

## 功能概述
{{feature_overview}}

## 技术实现
{{implementation}}

## API接口
{{api_specification}}

## 测试方案
{{test_plan}}
"""
        }

        for template_name, content in default_templates.items():
            template_path = self.templates_dir / template_name
            if not template_path.exists():
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(content)

    def apply_template(self, template_name: str, variables: Dict[str, str]) -> str:
        """应用模板"""
        template_path = self.templates_dir / template_name

        if not template_path.exists():
            raise FileNotFoundError(f"模板文件不存在: {template_name}")

        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()

            # 简单的变量替换
            result = template_content
            for key, value in variables.items():
                placeholder = f"{{{{{key}}}}}"
                result = result.replace(placeholder, str(value))

            return result

        except Exception as e:
            logger.error(f"应用模板失败: {e}")
            raise

    def list_templates(self) -> List[str]:
        """列出可用模板"""
        return [f.name for f in self.templates_dir.glob("*.md")]

class ADRRecorder:
    """架构决策记录器 (原ADRManager核心功能)"""

    def __init__(self, adr_dir: str):
        self.adr_dir = Path(adr_dir)
        self.adr_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.adr_dir / "index.json"
        self.decisions: List[ArchitectureDecision] = self._load_decisions()

    def _load_decisions(self) -> List[ArchitectureDecision]:
        """加载决策记录"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return [
                        ArchitectureDecision(
                            id=d['id'],
                            title=d['title'],
                            status=d['status'],
                            date=datetime.fromisoformat(d['date']),
                            context=d['context'],
                            decision=d['decision'],
                            consequences=d['consequences'],
                            alternatives=d.get('alternatives', []),
                            tags=d.get('tags', [])
                        ) for d in data
                    ]
            except Exception as e:
                logger.error(f"加载ADR失败: {e}")
        return []

    def _save_decisions(self):
        """保存决策记录"""
        try:
            data = [
                {
                    'id': d.id,
                    'title': d.title,
                    'status': d.status,
                    'date': d.date.isoformat(),
                    'context': d.context,
                    'decision': d.decision,
                    'consequences': d.consequences,
                    'alternatives': d.alternatives,
                    'tags': d.tags
                } for d in self.decisions
            ]

            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"保存ADR失败: {e}")

    def record_decision(self, title: str, context: str, decision: str,
                       consequences: str, alternatives: List[str] = None,
                       tags: List[str] = None) -> ArchitectureDecision:
        """记录架构决策"""
        # 生成ID
        adr_id = f"ADR-{len(self.decisions) + 1:03d}"

        adr = ArchitectureDecision(
            id=adr_id,
            title=title,
            status="proposed",
            date=datetime.now(),
            context=context,
            decision=decision,
            consequences=consequences,
            alternatives=alternatives or [],
            tags=tags or []
        )

        self.decisions.append(adr)
        self._save_decisions()

        # 创建ADR文档文件
        self._create_adr_file(adr)

        logger.info(f"记录架构决策: {adr_id} - {title}")
        return adr

    def _create_adr_file(self, adr: ArchitectureDecision):
        """创建ADR文档文件"""
        filename = f"{adr.id}-{adr.title.lower().replace(' ', '-')}.md"
        filepath = self.adr_dir / filename

        content = f"""# {adr.id}: {adr.title}

## 状态
{adr.status}

## 日期
{adr.date.strftime('%Y-%m-%d')}

## 上下文
{adr.context}

## 决策
{adr.decision}

## 后果
{adr.consequences}

## 备选方案
{chr(10).join([f"- {alt}" for alt in adr.alternatives])}

## 标签
{', '.join(adr.tags)}
"""

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            logger.error(f"创建ADR文件失败: {e}")

    def get_decision(self, adr_id: str) -> Optional[ArchitectureDecision]:
        """获取指定决策"""
        for decision in self.decisions:
            if decision.id == adr_id:
                return decision
        return None

    def list_decisions(self, status: str = None, tags: List[str] = None) -> List[ArchitectureDecision]:
        """列出决策记录"""
        filtered_decisions = self.decisions

        if status:
            filtered_decisions = [d for d in filtered_decisions if d.status == status]

        if tags:
            filtered_decisions = [
                d for d in filtered_decisions
                if any(tag in d.tags for tag in tags)
            ]

        return sorted(filtered_decisions, key=lambda d: d.date, reverse=True)

# ================== 主要管理器类 ==================

class DocumentManager:
    """统一文档管理器

    整合ClaudeMdManager, LifecycleManager, TemplateManager, ADRManager功能
    提供统一的文档管理服务
    """

    def __init__(self, project_root: str = None):
        """初始化文档管理器"""
        self.project_root = Path(project_root or os.getcwd())

        # 创建数据目录结构
        self.data_dir = self.project_root / ".perfect21" / "documents"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # 初始化核心组件
        self.content_analyzer = ContentAnalyzer()
        self.lifecycle_tracker = LifecycleTracker(str(self.data_dir / "lifecycle"))
        self.template_engine = TemplateEngine(str(self.data_dir / "templates"))
        self.adr_recorder = ADRRecorder(str(self.data_dir / "adr"))

        logger.info(f"DocumentManager initialized at {self.project_root}")

    # =================== 内容分析接口 ===================

    def analyze_document_health(self, file_path: str = None) -> DocumentHealth:
        """分析文档健康度"""
        if not file_path:
            file_path = str(self.project_root / "CLAUDE.md")

        return self.content_analyzer.calculate_document_health(file_path)

    def analyze_content_stability(self, content: str) -> Dict[str, ContentType]:
        """分析内容稳定性"""
        lines = content.split('\n')
        return self.content_analyzer.analyze_content_stability(lines)

    # =================== 生命周期管理接口 ===================

    def track_content_change(self, content_id: str, content_type: ContentType,
                           importance_score: float = 0.5) -> ContentMetadata:
        """跟踪内容变更"""
        return self.lifecycle_tracker.track_content_change(
            content_id, content_type, importance_score
        )

    def get_lifecycle_status(self) -> Dict[LifecycleStage, List[str]]:
        """获取生命周期状态"""
        return self.lifecycle_tracker.evaluate_lifecycle_status()

    def create_content_snapshot(self, content: str, version: str,
                              change_summary: str) -> str:
        """创建内容快照"""
        return self.lifecycle_tracker.create_snapshot(content, version, change_summary)

    # =================== 模板管理接口 ===================

    def apply_template(self, template_name: str, variables: Dict[str, str]) -> str:
        """应用模板"""
        return self.template_engine.apply_template(template_name, variables)

    def list_available_templates(self) -> List[str]:
        """列出可用模板"""
        return self.template_engine.list_templates()

    def generate_document_from_template(self, template_name: str,
                                      variables: Dict[str, str],
                                      output_path: str = None) -> str:
        """从模板生成文档"""
        content = self.apply_template(template_name, variables)

        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"Generated document: {output_path}")

            # 跟踪新文档
            self.track_content_change(
                output_path,
                ContentType.DYNAMIC,
                importance_score=0.7
            )

        return content

    # =================== 架构决策记录接口 ===================

    def record_architecture_decision(self, title: str, context: str,
                                   decision: str, consequences: str,
                                   alternatives: List[str] = None,
                                   tags: List[str] = None) -> ArchitectureDecision:
        """记录架构决策"""
        adr = self.adr_recorder.record_decision(
            title, context, decision, consequences, alternatives, tags
        )

        # 跟踪ADR文档
        self.track_content_change(
            f"adr/{adr.id}",
            ContentType.FIXED,
            importance_score=0.9
        )

        return adr

    def get_architecture_decision(self, adr_id: str) -> Optional[ArchitectureDecision]:
        """获取架构决策"""
        return self.adr_recorder.get_decision(adr_id)

    def list_architecture_decisions(self, status: str = None,
                                  tags: List[str] = None) -> List[ArchitectureDecision]:
        """列出架构决策"""
        return self.adr_recorder.list_decisions(status, tags)

    # =================== 综合管理接口 ===================

    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """生成综合文档报告"""
        health = self.analyze_document_health()
        lifecycle_status = self.get_lifecycle_status()
        templates = self.list_available_templates()
        decisions = self.list_architecture_decisions()

        return {
            'timestamp': datetime.now().isoformat(),
            'document_health': {
                'grade': health.health_grade.value,
                'total_lines': health.total_lines,
                'content_distribution': {
                    'fixed': health.fixed_ratio,
                    'dynamic': health.dynamic_ratio,
                    'volatile': health.volatile_ratio
                },
                'recommendations': health.recommendations
            },
            'lifecycle_overview': {
                stage.value: len(content_list)
                for stage, content_list in lifecycle_status.items()
            },
            'template_system': {
                'available_templates': len(templates),
                'template_list': templates
            },
            'architecture_decisions': {
                'total_decisions': len(decisions),
                'recent_decisions': [
                    {
                        'id': d.id,
                        'title': d.title,
                        'status': d.status,
                        'date': d.date.isoformat()
                    } for d in decisions[:5]
                ]
            }
        }

    def auto_cleanup_stale_content(self) -> List[str]:
        """自动清理陈旧内容"""
        lifecycle_status = self.get_lifecycle_status()
        obsolete_content = lifecycle_status.get(LifecycleStage.OBSOLETE, [])

        cleanup_actions = []

        for content_id in obsolete_content:
            metadata = self.lifecycle_tracker.metadata.get(content_id)
            if metadata and metadata.auto_cleanup and metadata.importance_score < 0.5:
                cleanup_actions.append(f"标记清理: {content_id}")
                # 这里可以实际执行清理操作

        if cleanup_actions:
            logger.info(f"执行自动清理: {len(cleanup_actions)}项")

        return cleanup_actions

    def backup_all_documents(self, backup_dir: str = None) -> str:
        """备份所有文档"""
        if not backup_dir:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = str(self.data_dir / f"backup_{timestamp}")

        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)

        try:
            # 备份主要文档
            claude_md = self.project_root / "CLAUDE.md"
            if claude_md.exists():
                shutil.copy2(claude_md, backup_path / "CLAUDE.md")

            # 备份数据目录
            data_backup = backup_path / "data"
            if self.data_dir.exists():
                shutil.copytree(self.data_dir, data_backup, dirs_exist_ok=True)

            # 创建备份清单
            manifest = {
                'timestamp': datetime.now().isoformat(),
                'backed_up_files': [
                    str(f.relative_to(backup_path))
                    for f in backup_path.rglob('*') if f.is_file()
                ],
                'backup_source': str(self.project_root)
            }

            with open(backup_path / "manifest.json", 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)

            logger.info(f"文档备份完成: {backup_dir}")
            return backup_dir

        except Exception as e:
            logger.error(f"文档备份失败: {e}")
            raise

    def cleanup(self):
        """清理资源"""
        try:
            # 清理各组件
            if hasattr(self.lifecycle_tracker, 'cleanup'):
                self.lifecycle_tracker.cleanup()

            logger.info("DocumentManager清理完成")
        except Exception as e:
            logger.error(f"DocumentManager清理失败: {e}")

# ================== 向后兼容适配器 ==================

class ClaudeMdManager:
    """向后兼容适配器 - ClaudeMdManager"""

    def __init__(self, claude_md_path: str = None):
        self._manager = DocumentManager()
        self.claude_md_path = claude_md_path or "CLAUDE.md"

    def calculate_document_health(self) -> DocumentHealth:
        return self._manager.analyze_document_health(self.claude_md_path)

    def auto_cleanup_stale_content(self) -> List[str]:
        return self._manager.auto_cleanup_stale_content()

class LifecycleManager:
    """向后兼容适配器 - LifecycleManager"""

    def __init__(self, project_root: str = None):
        self._manager = DocumentManager(project_root)

    def evaluate_content_status(self) -> Dict[LifecycleStage, List[str]]:
        return self._manager.get_lifecycle_status()

    def create_document_snapshot(self, content: str, version: str, change_summary: str) -> str:
        return self._manager.create_content_snapshot(content, version, change_summary)

# ================== 使用示例 ==================

def main():
    """使用示例"""
    # 创建文档管理器
    doc_manager = DocumentManager()

    # 分析文档健康度
    health = doc_manager.analyze_document_health()
    print(f"文档健康等级: {health.health_grade.value}")
    print(f"建议: {health.recommendations}")

    # 应用模板创建新文档
    variables = {
        'project_name': 'Perfect21',
        'project_description': 'Claude Code智能工作流增强层',
        'core_principles': '质量优先 + 智能编排 + 持续学习',
        'current_version': 'v3.0.0'
    }

    content = doc_manager.apply_template('claude_md_base.md', variables)
    print(f"生成内容长度: {len(content)}")

    # 记录架构决策
    adr = doc_manager.record_architecture_decision(
        title="采用统一Manager架构",
        context="Perfect21项目存在20+个分散的Manager类，造成维护困难",
        decision="整合相关Manager类，减少重复功能，提供统一接口",
        consequences="减少代码重复，提高维护性，可能需要迁移现有代码",
        tags=["architecture", "refactoring"]
    )
    print(f"记录架构决策: {adr.id}")

    # 生成综合报告
    report = doc_manager.generate_comprehensive_report()
    print(f"综合报告生成完成，包含 {len(report)} 个部分")

if __name__ == "__main__":
    main()