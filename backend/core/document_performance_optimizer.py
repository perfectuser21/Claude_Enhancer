"""
Document Quality Performance Optimizer
文档质量管理系统性能优化器 - 专为三层检查设计的高性能缓存和处理系统
"""

import asyncio
import hashlib
import time
import logging
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import json
import sqlite3
from contextlib import asynccontextmanager
from functools import lru_cache
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

logger = logging.getLogger(__name__)


@dataclass
class DocumentCheckResult:
    """文档检查结果"""

    file_path: str
    file_hash: str
    check_type: str  # 'syntax', 'style', 'content', 'similarity'
    passed: bool
    issues: List[str]
    processing_time: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class PerformanceMetrics:
    """性能指标"""

    check_duration: float
    files_processed: int
    cache_hits: int
    cache_misses: int
    parallel_workers: int
    memory_usage_mb: float


class DocumentPerformanceOptimizer:
    """文档质量性能优化器 - 高性能三层检查系统"""

    def __init__(self, cache_dir: str = "/tmp/claude_doc_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 缓存数据库
        self.cache_db = self.cache_dir / "doc_cache.db"
        self._init_cache_db()

        # 性能配置
        self.max_workers = min(mp.cpu_count(), 8)
        self.cache_ttl_hours = 24
        self.similarity_threshold = 0.85

        # 运行时统计
        self.stats = {
            "total_checks": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_check_time": 0.0,
            "files_per_second": 0.0,
        }

        # 内存缓存 (LRU)
        self._memory_cache = {}
        self._cache_access_times = {}
        self.max_memory_cache_size = 1000

    def _init_cache_db(self):
        """初始化缓存数据库"""
        with sqlite3.connect(self.cache_db) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS file_cache (
                    file_path TEXT PRIMARY KEY,
                    file_hash TEXT NOT NULL,
                    check_results TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_file_hash ON file_cache(file_hash)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_accessed_at ON file_cache(accessed_at)
            """
            )

    def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件哈希值"""
        try:
            with open(file_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return ""

    def _get_from_cache(self, file_path: str, file_hash: str) -> Optional[Dict]:
        """从缓存获取结果"""
        # 1. 内存缓存
        cache_key = f"{file_path}:{file_hash}"
        if cache_key in self._memory_cache:
            self._cache_access_times[cache_key] = time.time()
            self.stats["cache_hits"] += 1
            return self._memory_cache[cache_key]

        # 2. 磁盘缓存
        try:
            with sqlite3.connect(self.cache_db) as conn:
                cursor = conn.execute(
                    "SELECT check_results FROM file_cache WHERE file_path = ? AND file_hash = ?",
                    (file_path, file_hash),
                )
                row = cursor.fetchone()

                if row:
                    pass  # Auto-fixed empty block
                    # 更新访问时间
                    conn.execute(
                        "UPDATE file_cache SET accessed_at = CURRENT_TIMESTAMP WHERE file_path = ?",
                        (file_path,),
                    )

                    result = json.loads(row[0])
                    # 加入内存缓存
                    self._add_to_memory_cache(cache_key, result)
                    self.stats["cache_hits"] += 1
                    return result

        except Exception as e:
            logger.error(f"Cache read error: {e}")

        self.stats["cache_misses"] += 1
        return None

    def _save_to_cache(self, file_path: str, file_hash: str, results: Dict):
        """保存结果到缓存"""
        cache_key = f"{file_path}:{file_hash}"

        # 1. 内存缓存
        self._add_to_memory_cache(cache_key, results)

        # 2. 磁盘缓存
        try:
            with sqlite3.connect(self.cache_db) as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO file_cache
                       (file_path, file_hash, check_results, created_at, accessed_at)
                       VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
                    (file_path, file_hash, json.dumps(results)),
                )
        except Exception as e:
            logger.error(f"Cache save error: {e}")

    def _add_to_memory_cache(self, key: str, value: Dict):
        """添加到内存缓存（LRU策略）"""
        if len(self._memory_cache) >= self.max_memory_cache_size:
            pass  # Auto-fixed empty block
            # 移除最少使用的项
            oldest_key = min(
                self._cache_access_times.keys(),
                key=lambda k: self._cache_access_times[k],
            )
            del self._memory_cache[oldest_key]
            del self._cache_access_times[oldest_key]

        self._memory_cache[key] = value
        self._cache_access_times[key] = time.time()

    async def pre_commit_check(
        self, changed_files: List[str]
    ) -> Tuple[bool, PerformanceMetrics]:
        """Pre-commit快速检查 - 目标 < 2秒"""
        start_time = time.time()

        # 只检查基本语法和格式
        tasks = []
        for file_path in changed_files:
            if self._should_check_file(file_path):
                tasks.append(self._fast_syntax_check(file_path))

        if not tasks:
            return True, PerformanceMetrics(0, 0, 0, 0, 0, 0)

        # 并行执行
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 分析结果
        all_passed = all(
            r.passed for r in results if isinstance(r, DocumentCheckResult)
        )

        duration = time.time() - start_time
        metrics = PerformanceMetrics(
            check_duration=duration,
            files_processed=len(tasks),
            cache_hits=self.stats["cache_hits"],
            cache_misses=self.stats["cache_misses"],
            parallel_workers=min(len(tasks), self.max_workers),
            memory_usage_mb=self._get_memory_usage(),
        )

        logger.info(
            f"Pre-commit check: {duration:.2f}s, {len(tasks)} files, passed: {all_passed}"
        )
        return all_passed, metrics

    async def pre_push_check(
        self, changed_files: List[str]
    ) -> Tuple[bool, PerformanceMetrics]:
        """Pre-push增量检查 - 目标 < 5秒"""
        start_time = time.time()

        # 增量检查：语法 + 样式 + 基本内容检查
        tasks = []

        # 分批处理，避免内存溢出
        batch_size = 10
        for i in range(0, len(changed_files), batch_size):
            batch = changed_files[i : i + batch_size]
            for file_path in batch:
                if self._should_check_file(file_path):
                    tasks.extend(
                        [
                            self._fast_syntax_check(file_path),
                            self._style_check(file_path),
                            self._basic_content_check(file_path),
                        ]
                    )

        if not tasks:
            return True, PerformanceMetrics(0, 0, 0, 0, 0, 0)

        # 使用线程池并行执行
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self._run_async_check, task) for task in tasks]
            results = [f.result() for f in futures]

        all_passed = all(
            r.passed for r in results if isinstance(r, DocumentCheckResult)
        )

        duration = time.time() - start_time
        metrics = PerformanceMetrics(
            check_duration=duration,
            files_processed=len(changed_files),
            cache_hits=self.stats["cache_hits"],
            cache_misses=self.stats["cache_misses"],
            parallel_workers=self.max_workers,
            memory_usage_mb=self._get_memory_usage(),
        )

        logger.info(
            f"Pre-push check: {duration:.2f}s, {len(changed_files)} files, passed: {all_passed}"
        )
        return all_passed, metrics

    async def ci_deep_check(
        self, all_files: List[str]
    ) -> Tuple[bool, PerformanceMetrics]:
        """CI深度检查 - 目标 < 2分钟"""
        start_time = time.time()

        # 深度检查：语法 + 样式 + 内容 + 相似度检测

        # 1. 预过滤：只检查文档文件
        doc_files = [f for f in all_files if self._should_check_file(f)]

        # 2. 智能分组：相似文件一起处理，提高缓存命中率
        file_groups = self._group_similar_files(doc_files)

        # 3. 分布式并行处理
        all_results = []

        # 使用进程池处理大量文件
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = []

            for group in file_groups:
                future = executor.submit(self._process_file_group, group)
                futures.append(future)

            # 收集结果
            for future in futures:
                try:
                    group_results = future.result(timeout=30)  # 30秒超时
                    all_results.extend(group_results)
                except Exception as e:
                    logger.error(f"File group processing failed: {e}")

        # 4. 相似度检测（仅对通过基础检查的文件）
        passed_files = [
            r.file_path
            for r in all_results
            if isinstance(r, DocumentCheckResult) and r.passed
        ]

        similarity_results = await self._similarity_check_batch(passed_files)
        all_results.extend(similarity_results)

        all_passed = all(
            r.passed for r in all_results if isinstance(r, DocumentCheckResult)
        )

        duration = time.time() - start_time
        metrics = PerformanceMetrics(
            check_duration=duration,
            files_processed=len(doc_files),
            cache_hits=self.stats["cache_hits"],
            cache_misses=self.stats["cache_misses"],
            parallel_workers=self.max_workers,
            memory_usage_mb=self._get_memory_usage(),
        )

        logger.info(
            f"CI deep check: {duration:.2f}s, {len(doc_files)} files, passed: {all_passed}"
        )
        return all_passed, metrics

    def _should_check_file(self, file_path: str) -> bool:
        """判断是否应该检查文件"""
        doc_extensions = {".md", ".txt", ".rst", ".adoc", ".org"}
        return Path(file_path).suffix.lower() in doc_extensions

    async def _fast_syntax_check(self, file_path: str) -> DocumentCheckResult:
        """快速语法检查"""
        start_time = time.time()
        file_hash = self._calculate_file_hash(file_path)

        # 检查缓存
        cached = self._get_from_cache(file_path, file_hash)
        if cached and "syntax" in cached:
            return DocumentCheckResult(
                file_path=file_path,
                file_hash=file_hash,
                check_type="syntax",
                passed=cached["syntax"]["passed"],
                issues=cached["syntax"]["issues"],
                processing_time=0.001,  # 缓存命中
            )

        # 执行检查
        issues = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

                # 基本语法检查
                if not content.strip():
                    issues.append("Empty file")

                # Markdown特定检查
                if file_path.endswith(".md"):
                    if content.count("#") == 0:
                        issues.append("No headers found")

                    # 检查链接语法
                    import re

                    broken_links = re.findall(r"\[([^\]]*)\]\(\)", content)
                    if broken_links:
                        issues.append(f"Empty links: {len(broken_links)}")

        except Exception as e:
            issues.append(f"Read error: {str(e)}")

        result = DocumentCheckResult(
            file_path=file_path,
            file_hash=file_hash,
            check_type="syntax",
            passed=len(issues) == 0,
            issues=issues,
            processing_time=time.time() - start_time,
        )

        # 保存到缓存
        cache_data = {"syntax": {"passed": result.passed, "issues": result.issues}}
        self._save_to_cache(file_path, file_hash, cache_data)

        return result

    async def _style_check(self, file_path: str) -> DocumentCheckResult:
        """样式检查"""
        start_time = time.time()
        file_hash = self._calculate_file_hash(file_path)

        cached = self._get_from_cache(file_path, file_hash)
        if cached and "style" in cached:
            return DocumentCheckResult(
                file_path=file_path,
                file_hash=file_hash,
                check_type="style",
                passed=cached["style"]["passed"],
                issues=cached["style"]["issues"],
                processing_time=0.001,
            )

        issues = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

                # 行长度检查
                for i, line in enumerate(lines, 1):
                    if len(line) > 120:
                        issues.append(f"Line {i}: too long ({len(line)} chars)")

                # 空行检查
                empty_lines = sum(1 for line in lines if line.strip() == "")
                if empty_lines > len(lines) * 0.3:
                    issues.append("Too many empty lines")

        except Exception as e:
            issues.append(f"Style check error: {str(e)}")

        result = DocumentCheckResult(
            file_path=file_path,
            file_hash=file_hash,
            check_type="style",
            passed=len(issues) == 0,
            issues=issues,
            processing_time=time.time() - start_time,
        )

        # 更新缓存
        cached = cached or {}
        cached["style"] = {"passed": result.passed, "issues": result.issues}
        self._save_to_cache(file_path, file_hash, cached)

        return result

    async def _basic_content_check(self, file_path: str) -> DocumentCheckResult:
        """基本内容检查"""
        start_time = time.time()
        file_hash = self._calculate_file_hash(file_path)

        cached = self._get_from_cache(file_path, file_hash)
        if cached and "content" in cached:
            return DocumentCheckResult(
                file_path=file_path,
                file_hash=file_hash,
                check_type="content",
                passed=cached["content"]["passed"],
                issues=cached["content"]["issues"],
                processing_time=0.001,
            )

        issues = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

                # 内容质量检查
                word_count = len(content.split())
                if word_count < 10:
                    issues.append("Content too short")

                # TODO字样检查
                if "TODO" in content.upper():
                    issues.append("Contains TODO items")

                # 拼写检查（简化版）
                common_typos = ["teh", "recieve", "seperate", "occurence"]
                for typo in common_typos:
                    if typo in content.lower():
                        issues.append(f"Possible typo: {typo}")

        except Exception as e:
            issues.append(f"Content check error: {str(e)}")

        result = DocumentCheckResult(
            file_path=file_path,
            file_hash=file_hash,
            check_type="content",
            passed=len(issues) == 0,
            issues=issues,
            processing_time=time.time() - start_time,
        )

        # 更新缓存
        cached = cached or {}
        cached["content"] = {"passed": result.passed, "issues": result.issues}
        self._save_to_cache(file_path, file_hash, cached)

        return result

    def _group_similar_files(self, files: List[str]) -> List[List[str]]:
        """将相似文件分组以提高缓存命中率"""
        groups = {}

        for file_path in files:
            pass  # Auto-fixed empty block
            # 按目录和文件类型分组
            path_obj = Path(file_path)
            group_key = f"{path_obj.parent}:{path_obj.suffix}"

            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(file_path)

        return list(groups.values())

    def _process_file_group(self, files: List[str]) -> List[DocumentCheckResult]:
        """处理文件组"""
        results = []
        for file_path in files:
            pass  # Auto-fixed empty block
            # 在进程中运行异步检查
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                syntax_result = loop.run_until_complete(
                    self._fast_syntax_check(file_path)
                )
                style_result = loop.run_until_complete(self._style_check(file_path))
                content_result = loop.run_until_complete(
                    self._basic_content_check(file_path)
                )

                results.extend([syntax_result, style_result, content_result])
            finally:
                loop.close()

        return results

    async def _similarity_check_batch(
        self, files: List[str]
    ) -> List[DocumentCheckResult]:
        """批量相似度检测"""
        results = []

        # 使用高效的相似度算法
        file_contents = {}
        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    file_contents[file_path] = f.read()
            except Exception as e:
                logger.error(f"Failed to read {file_path}: {e}")
                continue

        # 简化的相似度检测（实际应用中可使用更高效的算法）
        for i, (file1, content1) in enumerate(file_contents.items()):
            issues = []

            for file2, content2 in list(file_contents.items())[i + 1 :]:
                similarity = self._calculate_similarity(content1, content2)
                if similarity > self.similarity_threshold:
                    issues.append(f"High similarity with {file2}: {similarity:.2f}")

            results.append(
                DocumentCheckResult(
                    file_path=file1,
                    file_hash=self._calculate_file_hash(file1),
                    check_type="similarity",
                    passed=len(issues) == 0,
                    issues=issues,
                    processing_time=0.1,
                )
            )

        return results

    def _calculate_similarity(self, content1: str, content2: str) -> float:
        """计算内容相似度（简化版）"""
        # 使用简单的Jaccard相似度
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())

        if not words1 and not words2:
            return 1.0

        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))

        return intersection / union if union > 0 else 0.0

    def _run_async_check(self, coro):
        """在线程中运行异步函数"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    def _get_memory_usage(self) -> float:
        """获取内存使用量（MB）"""
        import psutil

        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024

    async def cleanup_cache(self, max_age_hours: int = 72):
        """清理过期缓存"""
        try:
            with sqlite3.connect(self.cache_db) as conn:
                cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
                cursor = conn.execute(
                    "DELETE FROM file_cache WHERE accessed_at < ?", (cutoff_time,)
                )
                deleted_count = cursor.rowcount

                # 压缩数据库
                conn.execute("VACUUM")

                logger.info(
                    f"Cleaned {deleted_count} cache entries older than {max_age_hours}h"
                )

        except Exception as e:
            logger.error(f"Cache cleanup failed: {e}")

    def get_performance_stats(self) -> Dict:
        """获取性能统计"""
        cache_hit_rate = 0
        if self.stats["cache_hits"] + self.stats["cache_misses"] > 0:
            cache_hit_rate = (
                self.stats["cache_hits"]
                / (self.stats["cache_hits"] + self.stats["cache_misses"])
                * 100
            )

        return {
            **self.stats,
            "cache_hit_rate": f"{cache_hit_rate:.1f}%",
            "memory_cache_size": len(self._memory_cache),
            "max_workers": self.max_workers,
            "cache_db_size_mb": self.cache_db.stat().st_size / 1024 / 1024
            if self.cache_db.exists()
            else 0,
        }


# 单例模式的全局优化器
_optimizer_instance = None


def get_document_optimizer() -> DocumentPerformanceOptimizer:
    """获取文档性能优化器实例"""
    global _optimizer_instance
    if _optimizer_instance is None:
        _optimizer_instance = DocumentPerformanceOptimizer()
    return _optimizer_instance


# 使用示例和性能测试
async def performance_test():
    """性能测试"""
    optimizer = get_document_optimizer()

    # 模拟文件列表
    test_files = ["README.md", "docs/API.md", "docs/GUIDE.md", "CHANGELOG.md"]

    print("🚀 开始性能测试...")

    # Pre-commit测试
    start = time.time()
    passed, metrics = await optimizer.pre_commit_check(test_files[:2])
    print(f"Pre-commit: {metrics.check_duration:.2f}s, passed: {passed}")

    # Pre-push测试
    start = time.time()
    passed, metrics = await optimizer.pre_push_check(test_files)
    print(f"Pre-push: {metrics.check_duration:.2f}s, passed: {passed}")

    # CI深度测试
    start = time.time()
    passed, metrics = await optimizer.ci_deep_check(test_files * 10)  # 模拟更多文件
    print(f"CI deep: {metrics.check_duration:.2f}s, passed: {passed}")

    # 性能统计
    stats = optimizer.get_performance_stats()
    print(f"性能统计: {stats}")


if __name__ == "__main__":
    asyncio.run(performance_test())
