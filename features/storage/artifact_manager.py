#!/usr/bin/env python3
"""
Perfect21 Artifact Management System
基于文件的Agent输出缓存和上下文管理系统
"""

import os
import json
import hashlib
import pickle
import gzip
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import threading
import time

logger = logging.getLogger(__name__)

@dataclass
class ArtifactMetadata:
    """Artifact元数据"""
    artifact_id: str
    agent_name: str
    task_description: str
    created_at: datetime
    updated_at: datetime
    size_bytes: int
    content_hash: str
    tags: List[str]
    dependencies: List[str]  # 依赖的其他artifacts
    usage_count: int
    last_accessed: datetime
    expires_at: Optional[datetime] = None

@dataclass
class ArtifactSummary:
    """Artifact摘要信息"""
    artifact_id: str
    agent_name: str
    summary_text: str
    key_points: List[str]
    metadata: Dict[str, Any]
    created_at: datetime

class ArtifactStorage:
    """Artifact存储后端"""

    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # 创建子目录
        self.content_dir = self.storage_path / "content"
        self.metadata_dir = self.storage_path / "metadata"
        self.summary_dir = self.storage_path / "summaries"
        self.index_dir = self.storage_path / "index"

        for dir_path in [self.content_dir, self.metadata_dir, self.summary_dir, self.index_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # 索引文件
        self.index_file = self.index_dir / "artifacts.json"
        self.agent_index_file = self.index_dir / "by_agent.json"
        self.tag_index_file = self.index_dir / "by_tag.json"

        # 加载索引
        self.artifact_index = self._load_index()
        self.agent_index = self._load_agent_index()
        self.tag_index = self._load_tag_index()

        # 线程锁
        self._lock = threading.RLock()

    def _load_index(self) -> Dict[str, ArtifactMetadata]:
        """加载主索引"""
        if not self.index_file.exists():
            return {}

        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    aid: ArtifactMetadata(**meta) for aid, meta in data.items()
                }
        except Exception as e:
            logger.warning(f"索引加载失败: {e}")
            return {}

    def _load_agent_index(self) -> Dict[str, List[str]]:
        """加载Agent索引"""
        if not self.agent_index_file.exists():
            return {}

        try:
            with open(self.agent_index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def _load_tag_index(self) -> Dict[str, List[str]]:
        """加载标签索引"""
        if not self.tag_index_file.exists():
            return {}

        try:
            with open(self.tag_index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_indexes(self):
        """保存所有索引"""
        with self._lock:
            try:
                # 保存主索引
                with open(self.index_file, 'w', encoding='utf-8') as f:
                    serializable_index = {
                        aid: asdict(meta) for aid, meta in self.artifact_index.items()
                    }
                    # 转换datetime为字符串
                    for meta in serializable_index.values():
                        for key in ['created_at', 'updated_at', 'last_accessed', 'expires_at']:
                            if meta[key] and isinstance(meta[key], datetime):
                                meta[key] = meta[key].isoformat()

                    json.dump(serializable_index, f, indent=2, ensure_ascii=False)

                # 保存Agent索引
                with open(self.agent_index_file, 'w', encoding='utf-8') as f:
                    json.dump(self.agent_index, f, indent=2)

                # 保存标签索引
                with open(self.tag_index_file, 'w', encoding='utf-8') as f:
                    json.dump(self.tag_index, f, indent=2)

            except Exception as e:
                logger.error(f"索引保存失败: {e}")

    def store_artifact(self, artifact_id: str, content: Any, metadata: ArtifactMetadata) -> bool:
        """存储artifact"""
        with self._lock:
            try:
                # 序列化内容
                content_data = self._serialize_content(content)

                # 计算哈希
                content_hash = hashlib.sha256(content_data).hexdigest()
                metadata.content_hash = content_hash
                metadata.size_bytes = len(content_data)
                metadata.updated_at = datetime.now()

                # 压缩并保存内容
                content_file = self.content_dir / f"{artifact_id}.gz"
                with gzip.open(content_file, 'wb') as f:
                    f.write(content_data)

                # 保存元数据
                metadata_file = self.metadata_dir / f"{artifact_id}.json"
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    meta_dict = asdict(metadata)
                    # 转换datetime
                    for key in ['created_at', 'updated_at', 'last_accessed', 'expires_at']:
                        if meta_dict[key] and isinstance(meta_dict[key], datetime):
                            meta_dict[key] = meta_dict[key].isoformat()
                    json.dump(meta_dict, f, indent=2, ensure_ascii=False)

                # 更新索引
                self.artifact_index[artifact_id] = metadata

                # 更新Agent索引
                agent = metadata.agent_name
                if agent not in self.agent_index:
                    self.agent_index[agent] = []
                if artifact_id not in self.agent_index[agent]:
                    self.agent_index[agent].append(artifact_id)

                # 更新标签索引
                for tag in metadata.tags:
                    if tag not in self.tag_index:
                        self.tag_index[tag] = []
                    if artifact_id not in self.tag_index[tag]:
                        self.tag_index[tag].append(artifact_id)

                self._save_indexes()
                return True

            except Exception as e:
                logger.error(f"存储artifact失败 {artifact_id}: {e}")
                return False

    def load_artifact(self, artifact_id: str) -> Optional[Any]:
        """加载artifact内容"""
        with self._lock:
            try:
                if artifact_id not in self.artifact_index:
                    return None

                # 更新访问时间和次数
                metadata = self.artifact_index[artifact_id]
                metadata.last_accessed = datetime.now()
                metadata.usage_count += 1

                # 加载内容
                content_file = self.content_dir / f"{artifact_id}.gz"
                if not content_file.exists():
                    return None

                with gzip.open(content_file, 'rb') as f:
                    content_data = f.read()

                content = self._deserialize_content(content_data)

                # 更新索引
                self._save_indexes()

                return content

            except Exception as e:
                logger.error(f"加载artifact失败 {artifact_id}: {e}")
                return None

    def _serialize_content(self, content: Any) -> bytes:
        """序列化内容"""
        if isinstance(content, (str, dict, list)):
            return json.dumps(content, ensure_ascii=False).encode('utf-8')
        else:
            return pickle.dumps(content)

    def _deserialize_content(self, data: bytes) -> Any:
        """反序列化内容"""
        try:
            # 尝试JSON反序列化
            return json.loads(data.decode('utf-8'))
        except (UnicodeDecodeError, json.JSONDecodeError):
            # 回退到pickle
            return pickle.loads(data)

    def get_metadata(self, artifact_id: str) -> Optional[ArtifactMetadata]:
        """获取artifact元数据"""
        return self.artifact_index.get(artifact_id)

    def delete_artifact(self, artifact_id: str) -> bool:
        """删除artifact"""
        with self._lock:
            try:
                if artifact_id not in self.artifact_index:
                    return True

                metadata = self.artifact_index[artifact_id]

                # 删除文件
                content_file = self.content_dir / f"{artifact_id}.gz"
                metadata_file = self.metadata_dir / f"{artifact_id}.json"
                summary_file = self.summary_dir / f"{artifact_id}.json"

                for file_path in [content_file, metadata_file, summary_file]:
                    if file_path.exists():
                        file_path.unlink()

                # 更新索引
                del self.artifact_index[artifact_id]

                # 从Agent索引中移除
                agent = metadata.agent_name
                if agent in self.agent_index and artifact_id in self.agent_index[agent]:
                    self.agent_index[agent].remove(artifact_id)
                    if not self.agent_index[agent]:
                        del self.agent_index[agent]

                # 从标签索引中移除
                for tag in metadata.tags:
                    if tag in self.tag_index and artifact_id in self.tag_index[tag]:
                        self.tag_index[tag].remove(artifact_id)
                        if not self.tag_index[tag]:
                            del self.tag_index[tag]

                self._save_indexes()
                return True

            except Exception as e:
                logger.error(f"删除artifact失败 {artifact_id}: {e}")
                return False

    def find_artifacts(self, agent_name: str = None, tags: List[str] = None,
                      since: datetime = None) -> List[str]:
        """查找artifacts"""
        results = set()

        if agent_name and agent_name in self.agent_index:
            results.update(self.agent_index[agent_name])

        if tags:
            tag_results = set()
            for tag in tags:
                if tag in self.tag_index:
                    if not tag_results:
                        tag_results.update(self.tag_index[tag])
                    else:
                        tag_results.intersection_update(self.tag_index[tag])

            if agent_name:
                results.intersection_update(tag_results)
            else:
                results.update(tag_results)

        if since:
            filtered_results = set()
            for artifact_id in results:
                metadata = self.artifact_index.get(artifact_id)
                if metadata and metadata.created_at >= since:
                    filtered_results.add(artifact_id)
            results = filtered_results

        if not agent_name and not tags:
            results = set(self.artifact_index.keys())
            if since:
                results = {
                    aid for aid in results
                    if self.artifact_index[aid].created_at >= since
                }

        return list(results)

    def cleanup_expired(self) -> int:
        """清理过期artifacts"""
        now = datetime.now()
        expired_count = 0

        with self._lock:
            expired_artifacts = []

            for artifact_id, metadata in self.artifact_index.items():
                if metadata.expires_at and metadata.expires_at < now:
                    expired_artifacts.append(artifact_id)

            for artifact_id in expired_artifacts:
                if self.delete_artifact(artifact_id):
                    expired_count += 1

        return expired_count

    def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        total_artifacts = len(self.artifact_index)
        total_size = sum(meta.size_bytes for meta in self.artifact_index.values())

        # 按Agent统计
        agent_stats = {}
        for agent, artifact_ids in self.agent_index.items():
            agent_stats[agent] = {
                'count': len(artifact_ids),
                'size': sum(
                    self.artifact_index[aid].size_bytes
                    for aid in artifact_ids if aid in self.artifact_index
                )
            }

        # 最近访问统计
        now = datetime.now()
        recent_access = sum(
            1 for meta in self.artifact_index.values()
            if (now - meta.last_accessed).days < 7
        )

        return {
            'total_artifacts': total_artifacts,
            'total_size_bytes': total_size,
            'total_size_mb': total_size / (1024 * 1024),
            'agent_statistics': agent_stats,
            'recently_accessed': recent_access,
            'storage_path': str(self.storage_path)
        }


class ArtifactSummarizer:
    """Artifact摘要生成器"""

    def __init__(self):
        self.summary_templates = {
            'code': self._summarize_code,
            'api_response': self._summarize_api_response,
            'documentation': self._summarize_documentation,
            'test_result': self._summarize_test_result,
            'analysis': self._summarize_analysis,
            'default': self._summarize_default
        }

    def generate_summary(self, content: Any, content_type: str = 'default') -> ArtifactSummary:
        """生成content摘要"""
        try:
            summarizer = self.summary_templates.get(content_type, self._summarize_default)
            return summarizer(content)
        except Exception as e:
            logger.error(f"摘要生成失败: {e}")
            return ArtifactSummary(
                artifact_id="",
                agent_name="unknown",
                summary_text="摘要生成失败",
                key_points=[],
                metadata={},
                created_at=datetime.now()
            )

    def _summarize_code(self, content: Any) -> ArtifactSummary:
        """代码类型摘要"""
        if isinstance(content, str):
            lines = content.split('\n')
            non_empty_lines = [line for line in lines if line.strip()]

            # 提取关键信息
            key_points = []

            # 函数和类定义
            for line in non_empty_lines:
                if line.strip().startswith(('def ', 'class ', 'async def ')):
                    key_points.append(line.strip())

            summary_text = f"代码文件，共{len(non_empty_lines)}行，包含{len(key_points)}个定义"

        else:
            summary_text = "代码内容（非字符串格式）"
            key_points = []

        return ArtifactSummary(
            artifact_id="",
            agent_name="code_analyzer",
            summary_text=summary_text,
            key_points=key_points[:10],  # 最多10个关键点
            metadata={'type': 'code', 'lines': len(non_empty_lines) if isinstance(content, str) else 0},
            created_at=datetime.now()
        )

    def _summarize_api_response(self, content: Any) -> ArtifactSummary:
        """API响应摘要"""
        if isinstance(content, dict):
            status = content.get('status', 'unknown')
            data_size = len(str(content))

            key_points = []
            for key in ['message', 'error', 'result', 'data']:
                if key in content:
                    key_points.append(f"{key}: {str(content[key])[:100]}")

            summary_text = f"API响应，状态: {status}，数据大小: {data_size}字符"

        else:
            summary_text = f"API响应数据: {str(content)[:200]}"
            key_points = []

        return ArtifactSummary(
            artifact_id="",
            agent_name="api_handler",
            summary_text=summary_text,
            key_points=key_points,
            metadata={'type': 'api_response'},
            created_at=datetime.now()
        )

    def _summarize_documentation(self, content: Any) -> ArtifactSummary:
        """文档摘要"""
        if isinstance(content, str):
            words = content.split()
            paragraphs = content.split('\n\n')

            # 提取标题（以#开始的行）
            key_points = []
            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('#'):
                    key_points.append(line)

            summary_text = f"文档，共{len(words)}个词，{len(paragraphs)}个段落"

        else:
            summary_text = "文档内容"
            key_points = []

        return ArtifactSummary(
            artifact_id="",
            agent_name="documentation_writer",
            summary_text=summary_text,
            key_points=key_points[:10],
            metadata={'type': 'documentation'},
            created_at=datetime.now()
        )

    def _summarize_test_result(self, content: Any) -> ArtifactSummary:
        """测试结果摘要"""
        if isinstance(content, dict):
            passed = content.get('passed', 0)
            failed = content.get('failed', 0)
            total = passed + failed

            key_points = []
            if 'failures' in content:
                for failure in content['failures'][:5]:  # 最多5个失败案例
                    key_points.append(f"失败: {failure}")

            summary_text = f"测试结果: {passed}/{total} 通过"

        else:
            summary_text = f"测试结果: {str(content)[:200]}"
            key_points = []

        return ArtifactSummary(
            artifact_id="",
            agent_name="test_runner",
            summary_text=summary_text,
            key_points=key_points,
            metadata={'type': 'test_result'},
            created_at=datetime.now()
        )

    def _summarize_analysis(self, content: Any) -> ArtifactSummary:
        """分析结果摘要"""
        if isinstance(content, dict):
            key_points = []
            for key, value in content.items():
                if isinstance(value, (str, int, float)):
                    key_points.append(f"{key}: {value}")
                elif isinstance(value, list) and value:
                    key_points.append(f"{key}: {len(value)}项")

            summary_text = f"分析报告，包含{len(content)}个维度"

        else:
            summary_text = f"分析内容: {str(content)[:200]}"
            key_points = []

        return ArtifactSummary(
            artifact_id="",
            agent_name="analyzer",
            summary_text=summary_text,
            key_points=key_points[:10],
            metadata={'type': 'analysis'},
            created_at=datetime.now()
        )

    def _summarize_default(self, content: Any) -> ArtifactSummary:
        """默认摘要"""
        content_str = str(content)
        content_type = type(content).__name__

        key_points = []
        if isinstance(content, dict):
            key_points = [f"{k}: {str(v)[:50]}" for k, v in list(content.items())[:5]]
        elif isinstance(content, list):
            key_points = [f"Item {i}: {str(item)[:50]}" for i, item in enumerate(content[:5])]

        summary_text = f"{content_type}类型内容，长度: {len(content_str)}"

        return ArtifactSummary(
            artifact_id="",
            agent_name="generic",
            summary_text=summary_text,
            key_points=key_points,
            metadata={'type': 'generic', 'python_type': content_type},
            created_at=datetime.now()
        )


class ArtifactManager:
    """Artifact管理器主类"""

    def __init__(self, storage_path: str = None):
        if storage_path is None:
            storage_path = "/home/xx/dev/Perfect21/.perfect21/artifacts"

        self.storage = ArtifactStorage(storage_path)
        self.summarizer = ArtifactSummarizer()

        # 启动清理任务
        self._cleanup_thread = threading.Thread(target=self._background_cleanup, daemon=True)
        self._cleanup_thread.start()

        logger.info(f"Artifact管理器初始化完成，存储路径: {storage_path}")

    def store_agent_output(self, agent_name: str, task_description: str, content: Any,
                          tags: List[str] = None, expires_in_hours: int = None) -> str:
        """
        存储Agent输出

        Args:
            agent_name: Agent名称
            task_description: 任务描述
            content: 输出内容
            tags: 标签列表
            expires_in_hours: 过期时间（小时）

        Returns:
            str: Artifact ID
        """
        try:
            now = datetime.now()
            artifact_id = self._generate_artifact_id(agent_name, task_description, now)

            # 设置过期时间
            expires_at = None
            if expires_in_hours:
                expires_at = now + timedelta(hours=expires_in_hours)

            # 创建元数据
            metadata = ArtifactMetadata(
                artifact_id=artifact_id,
                agent_name=agent_name,
                task_description=task_description,
                created_at=now,
                updated_at=now,
                size_bytes=0,  # 将在storage中设置
                content_hash="",  # 将在storage中设置
                tags=tags or [],
                dependencies=[],
                usage_count=0,
                last_accessed=now,
                expires_at=expires_at
            )

            # 存储artifact
            if self.storage.store_artifact(artifact_id, content, metadata):
                # 生成并存储摘要
                self._store_summary(artifact_id, content, agent_name)
                logger.info(f"Agent输出已存储: {artifact_id}")
                return artifact_id
            else:
                raise Exception("存储失败")

        except Exception as e:
            logger.error(f"存储Agent输出失败: {e}")
            raise

    def _generate_artifact_id(self, agent_name: str, task_description: str, timestamp: datetime) -> str:
        """生成Artifact ID"""
        # 使用agent名、任务描述和时间戳生成唯一ID
        content = f"{agent_name}_{task_description}_{timestamp.isoformat()}"
        hash_object = hashlib.md5(content.encode())
        return f"{agent_name}_{hash_object.hexdigest()[:12]}"

    def _store_summary(self, artifact_id: str, content: Any, agent_name: str):
        """存储artifact摘要"""
        try:
            # 推断内容类型
            content_type = self._infer_content_type(content, agent_name)

            # 生成摘要
            summary = self.summarizer.generate_summary(content, content_type)
            summary.artifact_id = artifact_id
            summary.agent_name = agent_name

            # 存储摘要
            summary_file = self.storage.summary_dir / f"{artifact_id}.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                summary_dict = asdict(summary)
                summary_dict['created_at'] = summary.created_at.isoformat()
                json.dump(summary_dict, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.warning(f"摘要存储失败 {artifact_id}: {e}")

    def _infer_content_type(self, content: Any, agent_name: str) -> str:
        """推断内容类型"""
        # 基于agent名称推断
        if 'test' in agent_name.lower():
            return 'test_result'
        elif 'api' in agent_name.lower() or 'backend' in agent_name.lower():
            return 'api_response'
        elif 'writer' in agent_name.lower() or 'documentation' in agent_name.lower():
            return 'documentation'

        # 基于内容推断
        if isinstance(content, str):
            if any(keyword in content.lower() for keyword in ['def ', 'class ', 'import ']):
                return 'code'
            elif content.startswith('#') or '##' in content:
                return 'documentation'
        elif isinstance(content, dict):
            if 'passed' in content or 'failed' in content or 'test' in str(content).lower():
                return 'test_result'
            elif 'status' in content or 'response' in content:
                return 'api_response'
            else:
                return 'analysis'

        return 'default'

    def get_agent_output(self, artifact_id: str, include_summary: bool = False) -> Optional[Dict[str, Any]]:
        """
        获取Agent输出

        Args:
            artifact_id: Artifact ID
            include_summary: 是否包含摘要

        Returns:
            Dict: 包含内容和元数据的字典
        """
        try:
            # 加载内容
            content = self.storage.load_artifact(artifact_id)
            if content is None:
                return None

            # 获取元数据
            metadata = self.storage.get_metadata(artifact_id)
            if metadata is None:
                return None

            result = {
                'artifact_id': artifact_id,
                'content': content,
                'metadata': asdict(metadata),
                'agent_name': metadata.agent_name,
                'task_description': metadata.task_description,
                'created_at': metadata.created_at.isoformat(),
                'size_bytes': metadata.size_bytes
            }

            # 包含摘要
            if include_summary:
                summary = self.get_artifact_summary(artifact_id)
                result['summary'] = summary

            return result

        except Exception as e:
            logger.error(f"获取Agent输出失败 {artifact_id}: {e}")
            return None

    def get_artifact_summary(self, artifact_id: str) -> Optional[Dict[str, Any]]:
        """获取artifact摘要"""
        try:
            summary_file = self.storage.summary_dir / f"{artifact_id}.json"
            if not summary_file.exists():
                return None

            with open(summary_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        except Exception as e:
            logger.error(f"获取摘要失败 {artifact_id}: {e}")
            return None

    def find_related_artifacts(self, agent_name: str = None, tags: List[str] = None,
                             since_hours: int = None) -> List[Dict[str, Any]]:
        """
        查找相关artifacts

        Args:
            agent_name: Agent名称
            tags: 标签列表
            since_hours: 最近多少小时内

        Returns:
            List: Artifact列表（包含摘要）
        """
        since = None
        if since_hours:
            since = datetime.now() - timedelta(hours=since_hours)

        artifact_ids = self.storage.find_artifacts(agent_name, tags, since)

        results = []
        for artifact_id in artifact_ids:
            metadata = self.storage.get_metadata(artifact_id)
            summary = self.get_artifact_summary(artifact_id)

            if metadata:
                result = {
                    'artifact_id': artifact_id,
                    'agent_name': metadata.agent_name,
                    'task_description': metadata.task_description,
                    'created_at': metadata.created_at.isoformat(),
                    'size_bytes': metadata.size_bytes,
                    'usage_count': metadata.usage_count,
                    'tags': metadata.tags
                }

                if summary:
                    result['summary'] = summary

                results.append(result)

        # 按创建时间倒序排序
        results.sort(key=lambda x: x['created_at'], reverse=True)
        return results

    def create_context_from_artifacts(self, artifact_ids: List[str],
                                    max_context_size: int = 8000) -> str:
        """
        从artifacts创建上下文字符串（用于传递给agents）

        Args:
            artifact_ids: Artifact ID列表
            max_context_size: 最大上下文大小（字符数）

        Returns:
            str: 格式化的上下文字符串
        """
        context_parts = []
        current_size = 0

        for artifact_id in artifact_ids:
            if current_size >= max_context_size:
                break

            summary = self.get_artifact_summary(artifact_id)
            if not summary:
                continue

            # 创建紧凑的上下文条目
            context_entry = f"""
## {summary['agent_name']} 输出摘要
**任务**: {summary.get('summary_text', '无描述')}
**要点**: {', '.join(summary.get('key_points', [])[:3])}
**ID**: {artifact_id}
"""

            entry_size = len(context_entry)
            if current_size + entry_size > max_context_size:
                # 如果添加这个条目会超出限制，就截断
                remaining_space = max_context_size - current_size
                if remaining_space > 100:  # 确保有足够空间
                    context_parts.append(context_entry[:remaining_space] + "...")
                break

            context_parts.append(context_entry)
            current_size += entry_size

        if not context_parts:
            return "无相关上下文信息。"

        return f"""# 相关上下文信息
以下是相关Agent的输出摘要，可用于理解当前任务的背景：

{''.join(context_parts)}

---
*注意：这是自动生成的上下文摘要。如需完整内容，请使用对应的artifact_id获取。*
"""

    def cleanup_artifacts(self, max_age_days: int = 30, max_count: int = 1000) -> Dict[str, int]:
        """
        清理旧的artifacts

        Args:
            max_age_days: 最大保留天数
            max_count: 最大保留数量

        Returns:
            Dict: 清理统计
        """
        stats = {'expired': 0, 'old': 0, 'excess': 0, 'total_cleaned': 0}

        try:
            # 1. 清理过期artifacts
            expired_count = self.storage.cleanup_expired()
            stats['expired'] = expired_count

            # 2. 清理超过最大年龄的artifacts
            cutoff_date = datetime.now() - timedelta(days=max_age_days)
            old_artifacts = []

            for artifact_id, metadata in self.storage.artifact_index.items():
                if metadata.created_at < cutoff_date:
                    old_artifacts.append(artifact_id)

            for artifact_id in old_artifacts:
                if self.storage.delete_artifact(artifact_id):
                    stats['old'] += 1

            # 3. 如果数量仍然超过限制，删除最老的artifacts
            remaining_artifacts = list(self.storage.artifact_index.items())
            if len(remaining_artifacts) > max_count:
                # 按创建时间排序，保留最新的
                remaining_artifacts.sort(key=lambda x: x[1].created_at, reverse=True)

                to_delete = remaining_artifacts[max_count:]
                for artifact_id, _ in to_delete:
                    if self.storage.delete_artifact(artifact_id):
                        stats['excess'] += 1

            stats['total_cleaned'] = stats['expired'] + stats['old'] + stats['excess']
            logger.info(f"Artifact清理完成: {stats}")

        except Exception as e:
            logger.error(f"Artifact清理失败: {e}")

        return stats

    def _background_cleanup(self):
        """后台清理任务"""
        while True:
            try:
                time.sleep(3600)  # 每小时执行一次
                self.storage.cleanup_expired()
            except Exception as e:
                logger.error(f"后台清理任务失败: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """获取管理器统计信息"""
        storage_stats = self.storage.get_storage_stats()

        # 添加摘要统计
        summary_count = len(list(self.storage.summary_dir.glob("*.json")))

        return {
            **storage_stats,
            'summary_count': summary_count,
            'manager_status': 'active'
        }


# 全局实例
_artifact_manager = None

def get_artifact_manager() -> ArtifactManager:
    """获取全局Artifact管理器实例"""
    global _artifact_manager
    if _artifact_manager is None:
        _artifact_manager = ArtifactManager()
    return _artifact_manager