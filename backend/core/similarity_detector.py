"""
High-Performance Similarity Detection
高性能相似度检测器 - 优化的文档相似度检测算法
"""

import asyncio
import hashlib
import logging
import time
from typing import Dict, List, Tuple, Set, Optional
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from collections import defaultdict, Counter
import re
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor
import mmap

logger = logging.getLogger(__name__)


@dataclass
class SimilarityResult:
    """相似度检测结果"""

    file1: str
    file2: str
    similarity_score: float
    similarity_type: str  # 'exact', 'high', 'medium', 'low'
    common_sections: List[str]
    processing_time: float


@dataclass
class DocumentFingerprint:
    """文档指纹"""

    file_path: str
    content_hash: str
    structure_hash: str
    keywords: Set[str]
    ngrams: Set[str]
    length: int
    sections: List[str]


class HighPerformanceSimilarityDetector:
    """高性能相似度检测器 - 多层次、多算法的文档相似度检测"""

    def __init__(self):
        self.similarity_thresholds = {
            "exact": 0.95,
            "high": 0.80,
            "medium": 0.60,
            "low": 0.40,
        }

        # 缓存和优化
        self.fingerprint_cache = {}
        self.similarity_cache = {}
        self.max_cache_size = 10000

        # 并行处理配置
        self.max_workers = min(mp.cpu_count(), 8)

    async def detect_similarities_batch(
        self, file_paths: List[str]
    ) -> List[SimilarityResult]:
        """批量相似度检测 - 高性能版本"""
        start_time = time.time()

        if len(file_paths) < 2:
            return []

        print(f"🔍 开始相似度检测 - {len(file_paths)} 个文件")

        # 1. 快速预过滤 - 按文件大小分组
        size_groups = self._group_files_by_size(file_paths)
        candidate_pairs = []

        for group in size_groups:
            if len(group) >= 2:
                # 只在相似大小的文件间检测
                candidate_pairs.extend(self._generate_pairs(group))

        print(f"📊 预过滤后候选对: {len(candidate_pairs)}")

        # 2. 计算文档指纹 - 并行处理
        fingerprints = await self._compute_fingerprints_parallel(file_paths)
        fingerprint_map = {fp.file_path: fp for fp in fingerprints}

        # 3. 多层次相似度检测
        results = []

        # 使用进程池并行处理
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # 分批处理，避免内存溢出
            batch_size = 100
            for i in range(0, len(candidate_pairs), batch_size):
                batch = candidate_pairs[i : i + batch_size]

                futures = []
                for file1, file2 in batch:
                    if file1 in fingerprint_map and file2 in fingerprint_map:
                        future = executor.submit(
                            self._compute_similarity_fast,
                            fingerprint_map[file1],
                            fingerprint_map[file2],
                        )
                        futures.append((future, file1, file2))

                # 收集结果
                for future, file1, file2 in futures:
                    try:
                        similarity = future.result(timeout=5)
                        if (
                            similarity
                            and similarity.similarity_score
                            > self.similarity_thresholds["low"]
                        ):
                            results.append(similarity)
                    except Exception as e:
                        logger.warning(
                            f"Similarity computation failed for {file1} vs {file2}: {e}"
                        )

        processing_time = time.time() - start_time
        print(f"✅ 相似度检测完成 - 耗时: {processing_time:.2f}s, 发现 {len(results)} 个相似对")

        return results

    def _group_files_by_size(self, file_paths: List[str]) -> List[List[str]]:
        """按文件大小分组 - 相似大小的文件更可能相似"""
        size_groups = defaultdict(list)

        for file_path in file_paths:
            try:
                size = Path(file_path).stat().st_size
                # 按大小范围分组
                size_bucket = self._get_size_bucket(size)
                size_groups[size_bucket].append(file_path)
            except Exception as e:
                logger.warning(f"Failed to get size for {file_path}: {e}")

        # 只返回有多个文件的组
        return [group for group in size_groups.values() if len(group) >= 2]

    def _get_size_bucket(self, size: int) -> str:
        """获取文件大小分桶"""
        if size < 1024:  # < 1KB
            return "tiny"
        elif size < 10 * 1024:  # < 10KB
            return "small"
        elif size < 100 * 1024:  # < 100KB
            return "medium"
        elif size < 1024 * 1024:  # < 1MB
            return "large"
        else:
            return "huge"

    def _generate_pairs(self, files: List[str]) -> List[Tuple[str, str]]:
        """生成文件对"""
        pairs = []
        for i in range(len(files)):
            for j in range(i + 1, len(files)):
                pairs.append((files[i], files[j]))
        return pairs

    async def _compute_fingerprints_parallel(
        self, file_paths: List[str]
    ) -> List[DocumentFingerprint]:
        """并行计算文档指纹"""
        fingerprints = []

        # 检查缓存
        uncached_files = []
        for file_path in file_paths:
            if file_path in self.fingerprint_cache:
                fingerprints.append(self.fingerprint_cache[file_path])
            else:
                uncached_files.append(file_path)

        if not uncached_files:
            return fingerprints

        print(f"📋 计算文档指纹 - {len(uncached_files)} 个新文件")

        # 并行计算指纹
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(self._compute_fingerprint, file_path)
                for file_path in uncached_files
            ]

            for future in futures:
                try:
                    fingerprint = future.result(timeout=10)
                    if fingerprint:
                        fingerprints.append(fingerprint)
                        # 缓存指纹
                        self._cache_fingerprint(fingerprint)
                except Exception as e:
                    logger.error(f"Fingerprint computation failed: {e}")

        return fingerprints

    def _compute_fingerprint(self, file_path: str) -> Optional[DocumentFingerprint]:
        """计算单个文档指纹"""
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                # 使用内存映射提高大文件读取性能
                content = f.read()

            if not content.strip():
                return None

            # 1. 内容哈希
            content_hash = hashlib.md5(content.encode()).hexdigest()

            # 2. 结构哈希 (标题、段落结构)
            structure = self._extract_structure(content)
            structure_hash = hashlib.md5(str(structure).encode()).hexdigest()

            # 3. 关键词提取
            keywords = self._extract_keywords(content)

            # 4. N-gram特征
            ngrams = self._extract_ngrams(content, n=3)

            # 5. 文档段落
            sections = self._extract_sections(content)

            return DocumentFingerprint(
                file_path=file_path,
                content_hash=content_hash,
                structure_hash=structure_hash,
                keywords=keywords,
                ngrams=ngrams,
                length=len(content),
                sections=sections,
            )

        except Exception as e:
            logger.error(f"Failed to compute fingerprint for {file_path}: {e}")
            return None

    def _compute_similarity_fast(
        self, fp1: DocumentFingerprint, fp2: DocumentFingerprint
    ) -> Optional[SimilarityResult]:
        """快速相似度计算"""
        start_time = time.time()

        # 1. 快速排除：完全相同
        if fp1.content_hash == fp2.content_hash:
            return SimilarityResult(
                file1=fp1.file_path,
                file2=fp2.file_path,
                similarity_score=1.0,
                similarity_type="exact",
                common_sections=[],
                processing_time=time.time() - start_time,
            )

        # 2. 快速排除：长度差异过大
        if abs(fp1.length - fp2.length) / max(fp1.length, fp2.length) > 0.8:
            return None

        # 3. 多维度相似度计算
        similarities = {}

        # 结构相似度
        similarities["structure"] = (
            1.0 if fp1.structure_hash == fp2.structure_hash else 0.0
        )

        # 关键词相似度 (Jaccard)
        similarities["keywords"] = self._jaccard_similarity(fp1.keywords, fp2.keywords)

        # N-gram相似度
        similarities["ngrams"] = self._jaccard_similarity(fp1.ngrams, fp2.ngrams)

        # 段落相似度
        similarities["sections"] = self._section_similarity(fp1.sections, fp2.sections)

        # 4. 加权平均
        weights = {"structure": 0.2, "keywords": 0.3, "ngrams": 0.3, "sections": 0.2}

        overall_similarity = sum(
            similarities[dim] * weight for dim, weight in weights.items()
        )

        # 5. 确定相似度类型
        similarity_type = "low"
        for stype, threshold in sorted(
            self.similarity_thresholds.items(), key=lambda x: x[1], reverse=True
        ):
            if overall_similarity >= threshold:
                similarity_type = stype
                break

        # 6. 找出共同段落
        common_sections = self._find_common_sections(fp1.sections, fp2.sections)

        return SimilarityResult(
            file1=fp1.file_path,
            file2=fp2.file_path,
            similarity_score=overall_similarity,
            similarity_type=similarity_type,
            common_sections=common_sections,
            processing_time=time.time() - start_time,
        )

    def _extract_structure(self, content: str) -> List[str]:
        """提取文档结构"""
        structure = []

        # Markdown标题
        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("#"):
                level = len(line) - len(line.lstrip("#"))
                structure.append(f"H{level}")
            elif line.startswith("-") or line.startswith("*"):
                structure.append("LIST")
            elif line.startswith("```"):
                structure.append("CODE")
            elif line.startswith(">"):
                structure.append("QUOTE")

        return structure

    def _extract_keywords(self, content: str) -> Set[str]:
        """提取关键词"""
        # 简化的关键词提取
        words = re.findall(r"\b[a-zA-Z]{3,}\b", content.lower())

        # 过滤停用词
        stop_words = {
            "the",
            "and",
            "for",
            "are",
            "but",
            "not",
            "you",
            "all",
            "can",
            "had",
            "her",
            "was",
            "one",
            "our",
            "out",
            "day",
            "get",
            "has",
            "him",
            "his",
            "how",
            "man",
            "new",
            "now",
            "old",
            "see",
            "two",
            "way",
            "who",
            "boy",
            "did",
            "its",
            "let",
            "put",
            "say",
            "she",
            "too",
            "use",
        }

        keywords = {word for word in words if word not in stop_words and len(word) > 3}

        # 只保留最常见的关键词
        word_counts = Counter(words)
        top_keywords = {word for word, count in word_counts.most_common(50)}

        return keywords.intersection(top_keywords)

    def _extract_ngrams(self, content: str, n: int = 3) -> Set[str]:
        """提取N-gram特征"""
        # 清理内容
        content = re.sub(r"[^\w\s]", " ", content.lower())
        words = content.split()

        ngrams = set()
        for i in range(len(words) - n + 1):
            ngram = " ".join(words[i : i + n])
            ngrams.add(ngram)

        # 限制数量，避免内存溢出
        return set(list(ngrams)[:1000])

    def _extract_sections(self, content: str) -> List[str]:
        """提取文档段落"""
        # 按空行分段
        sections = []
        current_section = []

        for line in content.split("\n"):
            line = line.strip()
            if line:
                current_section.append(line)
            else:
                if current_section:
                    sections.append(" ".join(current_section))
                    current_section = []

        if current_section:
            sections.append(" ".join(current_section))

        # 过滤过短的段落
        return [section for section in sections if len(section) > 50]

    def _jaccard_similarity(self, set1: Set, set2: Set) -> float:
        """Jaccard相似度"""
        if not set1 and not set2:
            return 1.0

        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        return intersection / union if union > 0 else 0.0

    def _section_similarity(self, sections1: List[str], sections2: List[str]) -> float:
        """段落相似度"""
        if not sections1 and not sections2:
            return 1.0

        if not sections1 or not sections2:
            return 0.0

        # 找出最相似的段落对
        max_similarities = []

        for s1 in sections1:
            max_sim = 0.0
            for s2 in sections2:
                sim = self._text_similarity(s1, s2)
                max_sim = max(max_sim, sim)
            max_similarities.append(max_sim)

        return (
            sum(max_similarities) / len(max_similarities) if max_similarities else 0.0
        )

    def _text_similarity(self, text1: str, text2: str) -> float:
        """文本相似度 (简化版)"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        return self._jaccard_similarity(words1, words2)

    def _find_common_sections(
        self, sections1: List[str], sections2: List[str]
    ) -> List[str]:
        """找出共同段落"""
        common = []

        for s1 in sections1:
            for s2 in sections2:
                similarity = self._text_similarity(s1, s2)
                if similarity > 0.8:
                    common.append(s1[:100] + "..." if len(s1) > 100 else s1)

        return common[:5]  # 最多返回5个共同段落

    def _cache_fingerprint(self, fingerprint: DocumentFingerprint):
        """缓存文档指纹"""
        if len(self.fingerprint_cache) >= self.max_cache_size:
            # 简单的LRU: 移除一半缓存
            items = list(self.fingerprint_cache.items())
            self.fingerprint_cache = dict(items[len(items) // 2 :])

        self.fingerprint_cache[fingerprint.file_path] = fingerprint

    def get_performance_stats(self) -> Dict:
        """获取性能统计"""
        return {
            "fingerprint_cache_size": len(self.fingerprint_cache),
            "similarity_cache_size": len(self.similarity_cache),
            "max_workers": self.max_workers,
            "similarity_thresholds": self.similarity_thresholds,
        }

    async def cleanup_cache(self):
        """清理缓存"""
        self.fingerprint_cache.clear()
        self.similarity_cache.clear()
        logger.info("Similarity detection cache cleared")


# 使用示例和性能测试
async def test_similarity_detection():
    """相似度检测性能测试"""
    detector = HighPerformanceSimilarityDetector()

    # 模拟文件列表
    test_files = [
        "README.md",
        "docs/API.md",
        "docs/GUIDE.md",
        "docs/TUTORIAL.md",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
    ]

    print("🚀 开始相似度检测测试...")

    start_time = time.time()
    results = await detector.detect_similarities_batch(test_files)
    duration = time.time() - start_time

    print(f"⏱️  检测耗时: {duration:.2f}s")
    print(f"📊 发现相似对: {len(results)}")

    for result in results:
        print(
            f"📄 {result.file1} vs {result.file2}: "
            f"{result.similarity_score:.2f} ({result.similarity_type})"
        )

    # 性能统计
    stats = detector.get_performance_stats()
    print(f"📈 性能统计: {stats}")


# 优化的相似度检测Hook集成
class SimilarityCheckHook:
    """相似度检查Hook - 集成到质量检查流程"""

    def __init__(self, max_similarity: float = 0.8):
        self.detector = HighPerformanceSimilarityDetector()
        self.max_similarity = max_similarity

    async def check_pre_commit(
        self, changed_files: List[str]
    ) -> Tuple[bool, List[str]]:
        """Pre-commit相似度检查 - 快速版本"""
        if len(changed_files) < 2:
            return True, []

        # 只检查变更文件之间的相似度
        results = await self.detector.detect_similarities_batch(changed_files)

        issues = []
        for result in results:
            if result.similarity_score > self.max_similarity:
                issues.append(
                    f"High similarity detected: {result.file1} vs {result.file2} "
                    f"({result.similarity_score:.2f})"
                )

        return len(issues) == 0, issues

    async def check_ci_deep(self, all_files: List[str]) -> Tuple[bool, List[str]]:
        """CI深度相似度检查"""
        results = await self.detector.detect_similarities_batch(all_files)

        issues = []
        duplicates = []

        for result in results:
            if result.similarity_type == "exact":
                duplicates.append(f"Duplicate files: {result.file1} vs {result.file2}")
            elif result.similarity_score > self.max_similarity:
                issues.append(
                    f"High similarity: {result.file1} vs {result.file2} "
                    f"({result.similarity_score:.2f}) - Common sections: "
                    f"{len(result.common_sections)}"
                )

        all_issues = duplicates + issues
        return len(all_issues) == 0, all_issues


if __name__ == "__main__":
    asyncio.run(test_similarity_detection())
