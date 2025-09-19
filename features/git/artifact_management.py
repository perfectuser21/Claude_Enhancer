#!/usr/bin/env python3
"""
Perfect21 Artifact Management System
管理工作流产物，支持Git hooks集成和质量追踪
"""

import asyncio
import json
import logging
import os
import shutil
import time
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
import hashlib
import gzip

logger = logging.getLogger("Perfect21.ArtifactManagement")


class ArtifactType(Enum):
    """产物类型"""
    TASK_ANALYSIS = "task_analysis"
    AGENT_SELECTION = "agent_selection"
    EXECUTION_RESULTS = "execution_results"
    QUALITY_REPORT = "quality_report"
    TEST_RESULTS = "test_results"
    SECURITY_SCAN = "security_scan"
    PERFORMANCE_METRICS = "performance_metrics"
    DEPLOYMENT_CONFIG = "deployment_config"
    MONITORING_CONFIG = "monitoring_config"
    DOCUMENTATION = "documentation"


class ArtifactStatus(Enum):
    """产物状态"""
    DRAFT = "draft"                  # 草稿
    VALIDATED = "validated"          # 已验证
    APPROVED = "approved"            # 已批准
    DEPLOYED = "deployed"            # 已部署
    ARCHIVED = "archived"            # 已归档
    DEPRECATED = "deprecated"        # 已废弃


class QualityLevel(Enum):
    """质量等级"""
    EXCELLENT = "excellent"  # 优秀 (90-100分)
    GOOD = "good"           # 良好 (80-89分)
    ACCEPTABLE = "acceptable"  # 可接受 (70-79分)
    POOR = "poor"           # 较差 (60-69分)
    FAILED = "failed"       # 失败 (<60分)


@dataclass
class ArtifactMetadata:
    """产物元数据"""
    id: str
    type: ArtifactType
    name: str
    version: str
    status: ArtifactStatus
    quality_level: QualityLevel
    created_at: datetime
    updated_at: datetime
    created_by: str = "perfect21"
    size_bytes: int = 0
    checksum: str = ""
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    quality_score: float = 0.0
    validation_results: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityMetrics:
    """质量指标"""
    completeness: float = 0.0      # 完整性 (0-100)
    accuracy: float = 0.0          # 准确性 (0-100)
    consistency: float = 0.0       # 一致性 (0-100)
    timeliness: float = 0.0        # 及时性 (0-100)
    overall_score: float = 0.0     # 总分 (0-100)
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ArtifactRepository:
    """产物仓库配置"""
    base_path: Path
    max_storage_mb: int = 1024
    retention_days: int = 30
    compression_enabled: bool = True
    versioning_enabled: bool = True
    auto_cleanup_enabled: bool = True


class ArtifactManager:
    """产物管理器"""

    def __init__(self, project_root: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        self.project_root = Path(project_root or os.getcwd())

        # 配置仓库
        self.config = config or {}
        self.repository = ArtifactRepository(
            base_path=self.project_root / ".perfect21" / "artifacts",
            max_storage_mb=self.config.get('max_storage_mb', 1024),
            retention_days=self.config.get('retention_days', 30),
            compression_enabled=self.config.get('compression_enabled', True),
            versioning_enabled=self.config.get('versioning_enabled', True),
            auto_cleanup_enabled=self.config.get('auto_cleanup_enabled', True)
        )

        # 创建目录结构
        self._initialize_repository()

        # 产物索引
        self.index_file = self.repository.base_path / "index.json"
        self.artifacts_index = self._load_artifacts_index()

        # 质量检查器
        self.quality_checkers = self._register_quality_checkers()

    def _initialize_repository(self) -> None:
        """初始化产物仓库"""
        base_path = self.repository.base_path
        base_path.mkdir(parents=True, exist_ok=True)

        # 创建类型目录
        for artifact_type in ArtifactType:
            type_dir = base_path / artifact_type.value
            type_dir.mkdir(exist_ok=True)

        # 创建特殊目录
        (base_path / "temp").mkdir(exist_ok=True)
        (base_path / "archive").mkdir(exist_ok=True)
        (base_path / "backup").mkdir(exist_ok=True)

    def _load_artifacts_index(self) -> Dict[str, ArtifactMetadata]:
        """加载产物索引"""
        if not self.index_file.exists():
            return {}

        try:
            with open(self.index_file) as f:
                index_data = json.load(f)

            artifacts = {}
            for artifact_id, data in index_data.items():
                # 反序列化元数据
                metadata = ArtifactMetadata(
                    id=data['id'],
                    type=ArtifactType(data['type']),
                    name=data['name'],
                    version=data['version'],
                    status=ArtifactStatus(data['status']),
                    quality_level=QualityLevel(data['quality_level']),
                    created_at=datetime.fromisoformat(data['created_at']),
                    updated_at=datetime.fromisoformat(data['updated_at']),
                    created_by=data.get('created_by', 'perfect21'),
                    size_bytes=data.get('size_bytes', 0),
                    checksum=data.get('checksum', ''),
                    tags=data.get('tags', []),
                    dependencies=data.get('dependencies', []),
                    quality_score=data.get('quality_score', 0.0),
                    validation_results=data.get('validation_results', {})
                )
                artifacts[artifact_id] = metadata

            return artifacts

        except Exception as e:
            logger.error(f"加载产物索引失败: {e}")
            return {}

    def _save_artifacts_index(self) -> None:
        """保存产物索引"""
        try:
            index_data = {}
            for artifact_id, metadata in self.artifacts_index.items():
                index_data[artifact_id] = {
                    'id': metadata.id,
                    'type': metadata.type.value,
                    'name': metadata.name,
                    'version': metadata.version,
                    'status': metadata.status.value,
                    'quality_level': metadata.quality_level.value,
                    'created_at': metadata.created_at.isoformat(),
                    'updated_at': metadata.updated_at.isoformat(),
                    'created_by': metadata.created_by,
                    'size_bytes': metadata.size_bytes,
                    'checksum': metadata.checksum,
                    'tags': metadata.tags,
                    'dependencies': metadata.dependencies,
                    'quality_score': metadata.quality_score,
                    'validation_results': metadata.validation_results
                }

            with open(self.index_file, 'w') as f:
                json.dump(index_data, f, indent=2)

        except Exception as e:
            logger.error(f"保存产物索引失败: {e}")

    def _register_quality_checkers(self) -> Dict[ArtifactType, callable]:
        """注册质量检查器"""
        return {
            ArtifactType.TASK_ANALYSIS: self._check_task_analysis_quality,
            ArtifactType.AGENT_SELECTION: self._check_agent_selection_quality,
            ArtifactType.EXECUTION_RESULTS: self._check_execution_results_quality,
            ArtifactType.QUALITY_REPORT: self._check_quality_report_quality,
            ArtifactType.TEST_RESULTS: self._check_test_results_quality,
            ArtifactType.SECURITY_SCAN: self._check_security_scan_quality,
            ArtifactType.PERFORMANCE_METRICS: self._check_performance_metrics_quality,
            ArtifactType.DEPLOYMENT_CONFIG: self._check_deployment_config_quality,
            ArtifactType.MONITORING_CONFIG: self._check_monitoring_config_quality,
            ArtifactType.DOCUMENTATION: self._check_documentation_quality
        }

    async def store_artifact(self, artifact_type: ArtifactType, name: str,
                           content: Union[Dict[str, Any], str, bytes],
                           tags: Optional[List[str]] = None,
                           dependencies: Optional[List[str]] = None) -> str:
        """存储产物"""
        try:
            # 生成产物ID
            artifact_id = self._generate_artifact_id(artifact_type, name)

            # 准备内容
            if isinstance(content, dict):
                content_bytes = json.dumps(content, indent=2).encode('utf-8')
                file_extension = '.json'
            elif isinstance(content, str):
                content_bytes = content.encode('utf-8')
                file_extension = '.txt'
            else:
                content_bytes = content
                file_extension = '.bin'

            # 计算校验和
            checksum = hashlib.sha256(content_bytes).hexdigest()

            # 确定文件路径
            file_path = self._get_artifact_path(artifact_type, artifact_id, file_extension)

            # 写入文件
            if self.repository.compression_enabled and len(content_bytes) > 1024:
                # 压缩大文件
                with gzip.open(f"{file_path}.gz", 'wb') as f:
                    f.write(content_bytes)
                actual_path = f"{file_path}.gz"
            else:
                with open(file_path, 'wb') as f:
                    f.write(content_bytes)
                actual_path = file_path

            # 获取文件大小
            size_bytes = os.path.getsize(actual_path)

            # 质量检查
            quality_metrics = await self._check_artifact_quality(artifact_type, content)

            # 创建元数据
            metadata = ArtifactMetadata(
                id=artifact_id,
                type=artifact_type,
                name=name,
                version=self._generate_version(),
                status=ArtifactStatus.DRAFT,
                quality_level=self._determine_quality_level(quality_metrics.overall_score),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                size_bytes=size_bytes,
                checksum=checksum,
                tags=tags or [],
                dependencies=dependencies or [],
                quality_score=quality_metrics.overall_score,
                validation_results={
                    'completeness': quality_metrics.completeness,
                    'accuracy': quality_metrics.accuracy,
                    'consistency': quality_metrics.consistency,
                    'timeliness': quality_metrics.timeliness,
                    'issues': quality_metrics.issues,
                    'recommendations': quality_metrics.recommendations
                }
            )

            # 更新索引
            self.artifacts_index[artifact_id] = metadata
            self._save_artifacts_index()

            logger.info(f"产物已存储: {artifact_id} (质量: {metadata.quality_level.value})")
            return artifact_id

        except Exception as e:
            logger.error(f"存储产物失败: {e}")
            raise

    async def retrieve_artifact(self, artifact_id: str) -> Optional[Tuple[ArtifactMetadata, Any]]:
        """检索产物"""
        if artifact_id not in self.artifacts_index:
            return None

        try:
            metadata = self.artifacts_index[artifact_id]

            # 确定文件路径
            file_path = self._get_artifact_path(metadata.type, artifact_id)

            # 查找实际文件
            actual_file = None
            for ext in ['.json', '.txt', '.bin', '.json.gz', '.txt.gz', '.bin.gz']:
                potential_path = f"{file_path}{ext}"
                if os.path.exists(potential_path):
                    actual_file = potential_path
                    break

            if not actual_file:
                logger.error(f"产物文件未找到: {artifact_id}")
                return None

            # 读取内容
            if actual_file.endswith('.gz'):
                with gzip.open(actual_file, 'rb') as f:
                    content_bytes = f.read()
            else:
                with open(actual_file, 'rb') as f:
                    content_bytes = f.read()

            # 验证校验和
            actual_checksum = hashlib.sha256(content_bytes).hexdigest()
            if actual_checksum != metadata.checksum:
                logger.warning(f"产物校验和不匹配: {artifact_id}")

            # 解析内容
            if actual_file.endswith('.json') or actual_file.endswith('.json.gz'):
                content = json.loads(content_bytes.decode('utf-8'))
            elif actual_file.endswith('.txt') or actual_file.endswith('.txt.gz'):
                content = content_bytes.decode('utf-8')
            else:
                content = content_bytes

            return metadata, content

        except Exception as e:
            logger.error(f"检索产物失败 {artifact_id}: {e}")
            return None

    async def update_artifact_status(self, artifact_id: str, status: ArtifactStatus) -> bool:
        """更新产物状态"""
        if artifact_id not in self.artifacts_index:
            return False

        try:
            metadata = self.artifacts_index[artifact_id]
            metadata.status = status
            metadata.updated_at = datetime.now()

            self._save_artifacts_index()

            logger.info(f"产物状态已更新: {artifact_id} -> {status.value}")
            return True

        except Exception as e:
            logger.error(f"更新产物状态失败 {artifact_id}: {e}")
            return False

    async def validate_artifact(self, artifact_id: str) -> Dict[str, Any]:
        """验证产物"""
        result = await self.retrieve_artifact(artifact_id)
        if not result:
            return {
                'success': False,
                'error': f'产物不存在: {artifact_id}'
            }

        metadata, content = result

        try:
            # 重新进行质量检查
            quality_metrics = await self._check_artifact_quality(metadata.type, content)

            # 更新质量信息
            metadata.quality_score = quality_metrics.overall_score
            metadata.quality_level = self._determine_quality_level(quality_metrics.overall_score)
            metadata.validation_results.update({
                'completeness': quality_metrics.completeness,
                'accuracy': quality_metrics.accuracy,
                'consistency': quality_metrics.consistency,
                'timeliness': quality_metrics.timeliness,
                'issues': quality_metrics.issues,
                'recommendations': quality_metrics.recommendations,
                'last_validated': datetime.now().isoformat()
            })

            # 如果质量足够，更新状态
            if quality_metrics.overall_score >= 70:
                metadata.status = ArtifactStatus.VALIDATED

            metadata.updated_at = datetime.now()
            self._save_artifacts_index()

            return {
                'success': True,
                'quality_score': quality_metrics.overall_score,
                'quality_level': metadata.quality_level.value,
                'issues': quality_metrics.issues,
                'recommendations': quality_metrics.recommendations,
                'validated': quality_metrics.overall_score >= 70
            }

        except Exception as e:
            logger.error(f"验证产物失败 {artifact_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def get_artifacts_by_type(self, artifact_type: ArtifactType,
                                   status: Optional[ArtifactStatus] = None) -> List[ArtifactMetadata]:
        """按类型获取产物"""
        artifacts = []

        for metadata in self.artifacts_index.values():
            if metadata.type == artifact_type:
                if status is None or metadata.status == status:
                    artifacts.append(metadata)

        # 按创建时间降序排序
        artifacts.sort(key=lambda x: x.created_at, reverse=True)

        return artifacts

    async def get_artifacts_for_hook(self, hook_name: str) -> Dict[str, List[ArtifactMetadata]]:
        """获取特定Hook需要的产物"""
        hook_artifact_mapping = {
            'pre-commit': [ArtifactType.TASK_ANALYSIS, ArtifactType.AGENT_SELECTION],
            'commit-msg': [ArtifactType.EXECUTION_RESULTS],
            'pre-push': [ArtifactType.QUALITY_REPORT, ArtifactType.TEST_RESULTS,
                        ArtifactType.SECURITY_SCAN, ArtifactType.PERFORMANCE_METRICS],
            'post-checkout': [ArtifactType.TASK_ANALYSIS],
            'post-merge': [ArtifactType.DEPLOYMENT_CONFIG, ArtifactType.MONITORING_CONFIG]
        }

        required_types = hook_artifact_mapping.get(hook_name, [])
        result = {}

        for artifact_type in required_types:
            artifacts = await self.get_artifacts_by_type(artifact_type, ArtifactStatus.VALIDATED)
            result[artifact_type.value] = artifacts

        return result

    async def cleanup_artifacts(self, dry_run: bool = True) -> Dict[str, Any]:
        """清理过期产物"""
        if not self.repository.auto_cleanup_enabled:
            return {'message': '自动清理已禁用'}

        try:
            cutoff_date = datetime.now() - timedelta(days=self.repository.retention_days)
            cleanup_stats = {
                'candidates': 0,
                'removed': 0,
                'space_freed_mb': 0,
                'errors': []
            }

            for artifact_id, metadata in list(self.artifacts_index.items()):
                # 检查是否过期
                if metadata.created_at < cutoff_date and metadata.status != ArtifactStatus.DEPLOYED:
                    cleanup_stats['candidates'] += 1

                    if not dry_run:
                        # 删除文件
                        try:
                            file_path = self._get_artifact_path(metadata.type, artifact_id)
                            for ext in ['.json', '.txt', '.bin', '.json.gz', '.txt.gz', '.bin.gz']:
                                potential_path = f"{file_path}{ext}"
                                if os.path.exists(potential_path):
                                    file_size = os.path.getsize(potential_path)
                                    os.remove(potential_path)
                                    cleanup_stats['space_freed_mb'] += file_size / (1024 * 1024)
                                    break

                            # 从索引中移除
                            del self.artifacts_index[artifact_id]
                            cleanup_stats['removed'] += 1

                        except Exception as e:
                            cleanup_stats['errors'].append(f"删除 {artifact_id} 失败: {e}")

            if not dry_run and cleanup_stats['removed'] > 0:
                self._save_artifacts_index()

            cleanup_stats['space_freed_mb'] = round(cleanup_stats['space_freed_mb'], 2)

            logger.info(f"清理完成: {cleanup_stats}")
            return cleanup_stats

        except Exception as e:
            logger.error(f"清理产物失败: {e}")
            return {'error': str(e)}

    async def get_repository_stats(self) -> Dict[str, Any]:
        """获取仓库统计信息"""
        try:
            stats = {
                'total_artifacts': len(self.artifacts_index),
                'by_type': {},
                'by_status': {},
                'by_quality_level': {},
                'total_size_mb': 0,
                'average_quality_score': 0,
                'oldest_artifact': None,
                'newest_artifact': None
            }

            if not self.artifacts_index:
                return stats

            total_quality_score = 0
            oldest_date = datetime.max
            newest_date = datetime.min

            for metadata in self.artifacts_index.values():
                # 按类型统计
                type_key = metadata.type.value
                stats['by_type'][type_key] = stats['by_type'].get(type_key, 0) + 1

                # 按状态统计
                status_key = metadata.status.value
                stats['by_status'][status_key] = stats['by_status'].get(status_key, 0) + 1

                # 按质量等级统计
                quality_key = metadata.quality_level.value
                stats['by_quality_level'][quality_key] = stats['by_quality_level'].get(quality_key, 0) + 1

                # 大小和质量
                stats['total_size_mb'] += metadata.size_bytes / (1024 * 1024)
                total_quality_score += metadata.quality_score

                # 时间范围
                if metadata.created_at < oldest_date:
                    oldest_date = metadata.created_at
                    stats['oldest_artifact'] = {
                        'id': metadata.id,
                        'name': metadata.name,
                        'created_at': metadata.created_at.isoformat()
                    }

                if metadata.created_at > newest_date:
                    newest_date = metadata.created_at
                    stats['newest_artifact'] = {
                        'id': metadata.id,
                        'name': metadata.name,
                        'created_at': metadata.created_at.isoformat()
                    }

            stats['total_size_mb'] = round(stats['total_size_mb'], 2)
            stats['average_quality_score'] = round(total_quality_score / len(self.artifacts_index), 2)

            return stats

        except Exception as e:
            logger.error(f"获取仓库统计失败: {e}")
            return {'error': str(e)}

    # 质量检查器实现
    async def _check_artifact_quality(self, artifact_type: ArtifactType, content: Any) -> QualityMetrics:
        """检查产物质量"""
        checker = self.quality_checkers.get(artifact_type)
        if checker:
            return await checker(content)
        else:
            return await self._check_generic_quality(content)

    async def _check_task_analysis_quality(self, content: Any) -> QualityMetrics:
        """检查任务分析质量"""
        metrics = QualityMetrics()

        if isinstance(content, dict):
            # 检查必需字段
            required_fields = ['task_description', 'requirements', 'constraints', 'success_criteria']
            present_fields = sum(1 for field in required_fields if field in content and content[field])
            metrics.completeness = (present_fields / len(required_fields)) * 100

            # 检查内容详细程度
            total_content_length = sum(len(str(content.get(field, ''))) for field in required_fields)
            metrics.accuracy = min(total_content_length / 500 * 100, 100)  # 期望至少500字符

            # 检查一致性（简化检查）
            metrics.consistency = 85 if 'task_description' in content else 60

            # 及时性（假设都是及时的）
            metrics.timeliness = 100

        metrics.overall_score = (
            metrics.completeness * 0.4 +
            metrics.accuracy * 0.3 +
            metrics.consistency * 0.2 +
            metrics.timeliness * 0.1
        )

        if metrics.completeness < 80:
            metrics.issues.append("任务分析不够完整")
        if metrics.accuracy < 70:
            metrics.issues.append("任务描述过于简略")

        return metrics

    async def _check_agent_selection_quality(self, content: Any) -> QualityMetrics:
        """检查Agent选择质量"""
        metrics = QualityMetrics()

        if isinstance(content, dict):
            selected_agents = content.get('selected_agents', [])
            execution_mode = content.get('execution_mode', '')

            # 完整性：是否有足够的Agent
            metrics.completeness = min(len(selected_agents) / 3 * 100, 100)

            # 准确性：是否选择了合适的Agent
            task_type = content.get('task_type', '')
            if task_type and self._validate_agent_selection(task_type, selected_agents):
                metrics.accuracy = 90
            else:
                metrics.accuracy = 70

            # 一致性：执行模式是否与Agent数量匹配
            if len(selected_agents) > 1 and execution_mode == 'parallel':
                metrics.consistency = 95
            elif len(selected_agents) == 1:
                metrics.consistency = 85
            else:
                metrics.consistency = 60

            # 及时性
            metrics.timeliness = 100

        metrics.overall_score = (
            metrics.completeness * 0.3 +
            metrics.accuracy * 0.4 +
            metrics.consistency * 0.2 +
            metrics.timeliness * 0.1
        )

        if len(selected_agents) < 3:
            metrics.issues.append("Agent数量不足")
        if execution_mode != 'parallel' and len(selected_agents) > 1:
            metrics.issues.append("多Agent未配置并行执行")

        return metrics

    async def _check_execution_results_quality(self, content: Any) -> QualityMetrics:
        """检查执行结果质量"""
        metrics = QualityMetrics()

        if isinstance(content, dict):
            agent_results = content.get('agent_results', [])

            # 完整性：所有Agent都有结果
            total_agents = len(agent_results)
            successful_agents = sum(1 for r in agent_results if r.get('success', False))

            metrics.completeness = (total_agents / max(total_agents, 1)) * 100 if total_agents > 0 else 0

            # 准确性：成功率
            metrics.accuracy = (successful_agents / max(total_agents, 1)) * 100 if total_agents > 0 else 0

            # 一致性：结果格式一致性
            expected_fields = ['agent', 'success', 'execution_time', 'result']
            consistent_results = sum(1 for r in agent_results
                                   if all(field in r for field in expected_fields))
            metrics.consistency = (consistent_results / max(total_agents, 1)) * 100 if total_agents > 0 else 0

            # 及时性：执行时间合理性
            avg_execution_time = sum(r.get('execution_time', 0) for r in agent_results) / max(total_agents, 1)
            metrics.timeliness = max(100 - avg_execution_time, 0)  # 执行时间越短越好

        metrics.overall_score = (
            metrics.completeness * 0.2 +
            metrics.accuracy * 0.4 +
            metrics.consistency * 0.2 +
            metrics.timeliness * 0.2
        )

        if metrics.accuracy < 80:
            metrics.issues.append("Agent执行成功率过低")
        if avg_execution_time > 60:
            metrics.issues.append("Agent执行时间过长")

        return metrics

    async def _check_generic_quality(self, content: Any) -> QualityMetrics:
        """通用质量检查"""
        metrics = QualityMetrics()

        if isinstance(content, dict):
            # 基于内容丰富程度评估
            field_count = len(content)
            metrics.completeness = min(field_count / 5 * 100, 100)  # 期望至少5个字段

            # 基于内容大小评估
            content_str = json.dumps(content)
            metrics.accuracy = min(len(content_str) / 200 * 100, 100)  # 期望至少200字符

            # 一致性和及时性给默认分
            metrics.consistency = 80
            metrics.timeliness = 90

        elif isinstance(content, str):
            metrics.completeness = min(len(content) / 100 * 100, 100)
            metrics.accuracy = 80
            metrics.consistency = 80
            metrics.timeliness = 90

        else:
            # 其他类型给基础分
            metrics.completeness = 60
            metrics.accuracy = 60
            metrics.consistency = 60
            metrics.timeliness = 60

        metrics.overall_score = (
            metrics.completeness * 0.3 +
            metrics.accuracy * 0.3 +
            metrics.consistency * 0.2 +
            metrics.timeliness * 0.2
        )

        return metrics

    # 质量检查器的其他实现（简化版）
    async def _check_quality_report_quality(self, content: Any) -> QualityMetrics:
        """检查质量报告质量"""
        return await self._check_generic_quality(content)

    async def _check_test_results_quality(self, content: Any) -> QualityMetrics:
        """检查测试结果质量"""
        return await self._check_generic_quality(content)

    async def _check_security_scan_quality(self, content: Any) -> QualityMetrics:
        """检查安全扫描质量"""
        return await self._check_generic_quality(content)

    async def _check_performance_metrics_quality(self, content: Any) -> QualityMetrics:
        """检查性能指标质量"""
        return await self._check_generic_quality(content)

    async def _check_deployment_config_quality(self, content: Any) -> QualityMetrics:
        """检查部署配置质量"""
        return await self._check_generic_quality(content)

    async def _check_monitoring_config_quality(self, content: Any) -> QualityMetrics:
        """检查监控配置质量"""
        return await self._check_generic_quality(content)

    async def _check_documentation_quality(self, content: Any) -> QualityMetrics:
        """检查文档质量"""
        return await self._check_generic_quality(content)

    # 工具方法
    def _generate_artifact_id(self, artifact_type: ArtifactType, name: str) -> str:
        """生成产物ID"""
        timestamp = int(time.time())
        name_hash = hashlib.md5(name.encode()).hexdigest()[:8]
        return f"{artifact_type.value}_{timestamp}_{name_hash}"

    def _generate_version(self) -> str:
        """生成版本号"""
        return datetime.now().strftime("%Y%m%d.%H%M%S")

    def _get_artifact_path(self, artifact_type: ArtifactType, artifact_id: str, extension: str = "") -> str:
        """获取产物文件路径"""
        type_dir = self.repository.base_path / artifact_type.value
        return str(type_dir / f"{artifact_id}{extension}")

    def _determine_quality_level(self, score: float) -> QualityLevel:
        """根据分数确定质量等级"""
        if score >= 90:
            return QualityLevel.EXCELLENT
        elif score >= 80:
            return QualityLevel.GOOD
        elif score >= 70:
            return QualityLevel.ACCEPTABLE
        elif score >= 60:
            return QualityLevel.POOR
        else:
            return QualityLevel.FAILED

    def _validate_agent_selection(self, task_type: str, selected_agents: List[str]) -> bool:
        """验证Agent选择是否合适"""
        # 简化的验证逻辑
        task_agent_mapping = {
            'authentication': ['backend-architect', 'security-auditor', 'test-engineer'],
            'api_development': ['api-designer', 'backend-architect', 'test-engineer'],
            'database': ['database-specialist', 'backend-architect', 'performance-engineer']
        }

        required_agents = task_agent_mapping.get(task_type, [])
        return any(agent in selected_agents for agent in required_agents)


# 便捷函数
async def store_workflow_artifact(artifact_type: str, name: str, content: Any,
                                 project_root: Optional[str] = None) -> str:
    """存储工作流产物的便捷函数"""
    manager = ArtifactManager(project_root)
    artifact_type_enum = ArtifactType(artifact_type)
    return await manager.store_artifact(artifact_type_enum, name, content)


async def get_artifacts_for_git_hook(hook_name: str, project_root: Optional[str] = None) -> Dict[str, Any]:
    """获取Git Hook所需产物的便捷函数"""
    manager = ArtifactManager(project_root)
    return await manager.get_artifacts_for_hook(hook_name)


if __name__ == "__main__":
    import sys

    async def main():
        if len(sys.argv) < 2:
            print("用法: python artifact_management.py <command> [args...]")
            print("命令: store, retrieve, validate, cleanup, stats")
            return

        command = sys.argv[1]
        manager = ArtifactManager()

        if command == "store":
            if len(sys.argv) < 5:
                print("用法: store <type> <name> <content_json>")
                return

            artifact_type = ArtifactType(sys.argv[2])
            name = sys.argv[3]
            content = json.loads(sys.argv[4])

            artifact_id = await manager.store_artifact(artifact_type, name, content)
            print(f"产物已存储: {artifact_id}")

        elif command == "retrieve":
            if len(sys.argv) < 3:
                print("用法: retrieve <artifact_id>")
                return

            artifact_id = sys.argv[2]
            result = await manager.retrieve_artifact(artifact_id)

            if result:
                metadata, content = result
                print(f"元数据: {json.dumps(metadata.__dict__, default=str, indent=2)}")
                print(f"内容: {json.dumps(content, indent=2, default=str)}")
            else:
                print("产物未找到")

        elif command == "validate":
            if len(sys.argv) < 3:
                print("用法: validate <artifact_id>")
                return

            artifact_id = sys.argv[2]
            result = await manager.validate_artifact(artifact_id)
            print(json.dumps(result, indent=2, default=str))

        elif command == "cleanup":
            dry_run = len(sys.argv) < 3 or sys.argv[2] != "--force"
            result = await manager.cleanup_artifacts(dry_run)
            print(json.dumps(result, indent=2, default=str))

        elif command == "stats":
            stats = await manager.get_repository_stats()
            print(json.dumps(stats, indent=2, default=str))

        else:
            print(f"未知命令: {command}")

    asyncio.run(main())