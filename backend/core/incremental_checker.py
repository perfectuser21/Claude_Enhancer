"""
Incremental Document Checker
增量文档检查器 - 智能差异检测和最小化检查范围
"""

import asyncio
import json
import logging
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class FileChange:
    """文件变更信息"""

    path: str
    change_type: str  # 'added', 'modified', 'deleted', 'renamed'
    old_path: Optional[str] = None  # for renamed files
    lines_changed: List[int] = None
    size_delta: int = 0


@dataclass
class IncrementalResult:
    """增量检查结果"""

    total_files: int
    skipped_files: int
    checked_files: int
    processing_time: float
    cache_hit_rate: float
    performance_gain: float  # 相比全量检查的性能提升


class IncrementalChecker:
    """增量文档检查器 - 智能识别变更范围，最小化检查工作量"""

    def __init__(self, repo_root: str):
        self.repo_root = Path(repo_root)
        self.state_file = self.repo_root / ".claude" / "incremental_state.json"
        self.last_check_state = self._load_state()

    def _load_state(self) -> Dict:
        """加载上次检查状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load incremental state: {e}")

        return {
            "last_commit": None,
            "file_hashes": {},
            "last_check_time": None,
            "branch": None,
        }

    def _save_state(self, state: Dict):
        """保存检查状态"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.state_file, "w") as f:
                json.dump(state, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save incremental state: {e}")

    def get_changed_files_since_last_check(self) -> List[FileChange]:
        """获取自上次检查以来的变更文件"""
        changes = []

        try:
            # 获取当前Git状态
            current_commit = self._get_current_commit()
            current_branch = self._get_current_branch()

            # 如果是首次检查或切换分支，返回所有文档文件
            if not self.last_check_state.get(
                "last_commit"
            ) or current_branch != self.last_check_state.get("branch"):
                logger.info("First check or branch change, checking all files")
                return self._get_all_doc_files()

            # Git diff获取变更
            last_commit = self.last_check_state["last_commit"]
            git_changes = self._git_diff_files(last_commit, current_commit)

            # 解析变更
            for change in git_changes:
                if self._is_document_file(change["path"]):
                    changes.append(
                        FileChange(
                            path=change["path"],
                            change_type=change["type"],
                            old_path=change.get("old_path"),
                            lines_changed=change.get("lines_changed", []),
                        )
                    )

            # 额外检查：文件内容哈希变更（捕获非Git管理的变更）
            hash_changes = self._detect_hash_changes()
            changes.extend(hash_changes)

        except Exception as e:
            logger.error(f"Failed to detect changes: {e}")
            # fallback: 检查所有文档文件
            return self._get_all_doc_files()

        logger.info(f"Detected {len(changes)} changed files")
        return changes

    def get_dependent_files(self, changed_files: List[str]) -> Set[str]:
        """获取依赖文件 - 变更可能影响的其他文件"""
        dependent_files = set()

        for file_path in changed_files:
            # 1. 检查引用关系
            references = self._find_file_references(file_path)
            dependent_files.update(references)

            # 2. 检查目录关联
            dir_related = self._find_directory_related_files(file_path)
            dependent_files.update(dir_related)

            # 3. 检查模板/配置文件影响
            template_affected = self._find_template_affected_files(file_path)
            dependent_files.update(template_affected)

        # 移除自身
        dependent_files.discard(file_path)

        logger.info(f"Found {len(dependent_files)} dependent files")
        return dependent_files

    def optimize_check_order(self, files_to_check: List[str]) -> List[str]:
        """优化检查顺序 - 快速失败，缓存友好"""
        file_info = []

        for file_path in files_to_check:
            info = {
                "path": file_path,
                "size": self._get_file_size(file_path),
                "complexity": self._estimate_complexity(file_path),
                "cache_probability": self._estimate_cache_hit_probability(file_path),
            }
            file_info.append(info)

        # 排序策略：
        # 1. 缓存命中率高的优先（快速完成）
        # 2. 小文件优先（快速反馈）
        # 3. 复杂度低的优先（快速完成）
        file_info.sort(
            key=lambda x: (
                -x["cache_probability"],  # 缓存命中率高的优先
                x["size"],  # 小文件优先
                x["complexity"],  # 低复杂度优先
            )
        )

        optimized_order = [info["path"] for info in file_info]
        logger.info(f"Optimized check order for {len(optimized_order)} files")
        return optimized_order

    def should_skip_check(self, file_path: str, check_type: str) -> bool:
        """判断是否应跳过检查"""
        # 1. 文件大小过滤
        file_size = self._get_file_size(file_path)
        if file_size > 1024 * 1024:  # 1MB
            logger.debug(f"Skipping large file: {file_path} ({file_size} bytes)")
            return True

        # 2. 文件类型过滤
        if not self._is_checkable_file(file_path, check_type):
            return True

        # 3. 时间戳检查（文件未修改）
        if not self._has_file_changed_recently(file_path):
            logger.debug(f"Skipping unchanged file: {file_path}")
            return True

        # 4. 临时文件过滤
        if self._is_temp_file(file_path):
            return True

        return False

    def create_incremental_context(self, changed_files: List[str]) -> Dict:
        """创建增量检查上下文 - 为检查器提供优化信息"""
        return {
            "changed_files": changed_files,
            "change_hotspots": self._identify_change_hotspots(changed_files),
            "risk_level": self._assess_change_risk(changed_files),
            "suggested_focus": self._suggest_check_focus(changed_files),
            "parallel_groups": self._create_parallel_groups(changed_files),
            "estimated_time": self._estimate_check_time(changed_files),
        }

    def _get_current_commit(self) -> str:
        """获取当前Git提交"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return ""

    def _get_current_branch(self) -> str:
        """获取当前Git分支"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return ""

    def _git_diff_files(self, from_commit: str, to_commit: str) -> List[Dict]:
        """Git diff获取文件变更"""
        changes = []

        try:
            # 获取变更文件列表
            result = subprocess.run(
                ["git", "diff", "--name-status", f"{from_commit}..{to_commit}"],
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                check=True,
            )

            for line in result.stdout.strip().split("\n"):
                if not line:
                    continue

                parts = line.split("\t")
                if len(parts) >= 2:
                    status = parts[0]
                    file_path = parts[1]

                    change_type = {
                        "A": "added",
                        "M": "modified",
                        "D": "deleted",
                        "R": "renamed",
                        "C": "copied",
                    }.get(status[0], "modified")

                    change = {"path": file_path, "type": change_type}

                    # 重命名文件的旧路径
                    if status.startswith("R") and len(parts) >= 3:
                        change["old_path"] = parts[2]

                    changes.append(change)

        except subprocess.CalledProcessError as e:
            logger.error(f"Git diff failed: {e}")

        return changes

    def _detect_hash_changes(self) -> List[FileChange]:
        """检测文件哈希变更"""
        changes = []
        current_hashes = {}

        # 计算当前文件哈希
        doc_files = self._get_all_doc_files()
        for file_change in doc_files:
            file_path = file_change.path
            if Path(file_path).exists():
                current_hash = self._calculate_file_hash(file_path)
                current_hashes[file_path] = current_hash

                # 与上次对比
                last_hash = self.last_check_state.get("file_hashes", {}).get(file_path)
                if last_hash and last_hash != current_hash:
                    changes.append(FileChange(path=file_path, change_type="modified"))

        return changes

    def _calculate_file_hash(self, file_path: str) -> str:
        """计算文件哈希"""
        try:
            with open(file_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return ""

    def _get_all_doc_files(self) -> List[FileChange]:
        """获取所有文档文件"""
        doc_files = []
        doc_extensions = {".md", ".txt", ".rst", ".adoc", ".org"}

        for ext in doc_extensions:
            for file_path in self.repo_root.rglob(f"*{ext}"):
                if self._is_checkable_file(str(file_path), "all"):
                    doc_files.append(
                        FileChange(
                            path=str(file_path.relative_to(self.repo_root)),
                            change_type="existing",
                        )
                    )

        return doc_files

    def _is_document_file(self, file_path: str) -> bool:
        """判断是否为文档文件"""
        doc_extensions = {".md", ".txt", ".rst", ".adoc", ".org"}
        return Path(file_path).suffix.lower() in doc_extensions

    def _is_checkable_file(self, file_path: str, check_type: str) -> bool:
        """判断文件是否可检查"""
        path_obj = Path(file_path)

        # 跳过隐藏文件和目录
        if any(part.startswith(".") for part in path_obj.parts):
            if not any(part in [".claude", ".github"] for part in path_obj.parts):
                return False

        # 跳过特定目录
        skip_dirs = {"node_modules", "__pycache__", ".git", "build", "dist"}
        if any(part in skip_dirs for part in path_obj.parts):
            return False

        # 检查文件扩展名
        return self._is_document_file(file_path)

    def _find_file_references(self, file_path: str) -> Set[str]:
        """查找文件引用关系"""
        references = set()

        try:
            # 搜索包含该文件路径的其他文件
            result = subprocess.run(
                ["grep", "-r", "-l", Path(file_path).name, str(self.repo_root)],
                capture_output=True,
                text=True,
            )

            for line in result.stdout.strip().split("\n"):
                if line and line != file_path and self._is_document_file(line):
                    relative_path = str(Path(line).relative_to(self.repo_root))
                    references.add(relative_path)

        except Exception as e:
            logger.debug(f"Failed to find references for {file_path}: {e}")

        return references

    def _find_directory_related_files(self, file_path: str) -> Set[str]:
        """查找目录相关文件"""
        related = set()
        file_dir = Path(file_path).parent

        # 同目录下的其他文档文件
        for sibling in file_dir.glob("*.md"):
            if sibling.name != Path(file_path).name:
                related.add(str(sibling.relative_to(self.repo_root)))

        # 检查是否有README文件需要更新
        readme_files = ["README.md", "readme.md", "README.txt"]
        for readme in readme_files:
            readme_path = file_dir / readme
            if readme_path.exists():
                related.add(str(readme_path.relative_to(self.repo_root)))

        return related

    def _find_template_affected_files(self, file_path: str) -> Set[str]:
        """查找模板影响的文件"""
        affected = set()

        # 如果是配置文件或模板文件
        template_indicators = ["template", "config", ".claude", "settings"]
        if any(indicator in file_path.lower() for indicator in template_indicators):
            # 可能影响整个项目的文档
            for doc_file in self._get_all_doc_files():
                affected.add(doc_file.path)

        return affected

    def _get_file_size(self, file_path: str) -> int:
        """获取文件大小"""
        try:
            return Path(file_path).stat().st_size
        except Exception:
            return 0

    def _estimate_complexity(self, file_path: str) -> int:
        """估算文件复杂度"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 简单的复杂度指标
            complexity = 0
            complexity += len(content.split("\n"))  # 行数
            complexity += content.count("[")  # 链接数量
            complexity += content.count("#")  # 标题数量
            complexity += content.count("```")  # 代码块数量

            return complexity

        except Exception:
            return 100  # 默认中等复杂度

    def _estimate_cache_hit_probability(self, file_path: str) -> float:
        """估算缓存命中概率"""
        # 基于文件修改时间和历史模式
        try:
            file_stat = Path(file_path).stat()
            hours_since_modified = (
                datetime.now().timestamp() - file_stat.st_mtime
            ) / 3600

            # 文件越旧，缓存命中率越高
            if hours_since_modified > 24:
                return 0.9
            elif hours_since_modified > 1:
                return 0.7
            else:
                return 0.3

        except Exception:
            return 0.5

    def _has_file_changed_recently(self, file_path: str, hours: int = 1) -> bool:
        """检查文件是否最近修改过"""
        try:
            file_stat = Path(file_path).stat()
            hours_since_modified = (
                datetime.now().timestamp() - file_stat.st_mtime
            ) / 3600
            return hours_since_modified < hours
        except Exception:
            return True  # 安全起见，认为已修改

    def _is_temp_file(self, file_path: str) -> bool:
        """判断是否为临时文件"""
        temp_patterns = [".tmp", ".temp", ".bak", ".swp", "~"]
        return any(pattern in file_path for pattern in temp_patterns)

    def _identify_change_hotspots(self, changed_files: List[str]) -> List[str]:
        """识别变更热点目录"""
        directories = {}
        for file_path in changed_files:
            dir_path = str(Path(file_path).parent)
            directories[dir_path] = directories.get(dir_path, 0) + 1

        # 返回变更文件最多的目录
        hotspots = sorted(directories.items(), key=lambda x: x[1], reverse=True)
        return [dir_path for dir_path, count in hotspots[:5]]

    def _assess_change_risk(self, changed_files: List[str]) -> str:
        """评估变更风险级别"""
        if len(changed_files) > 50:
            return "high"
        elif len(changed_files) > 10:
            return "medium"
        else:
            return "low"

    def _suggest_check_focus(self, changed_files: List[str]) -> List[str]:
        """建议检查重点"""
        focus_areas = []

        # 根据文件类型建议
        has_readme = any("readme" in f.lower() for f in changed_files)
        has_docs = any("doc" in f.lower() for f in changed_files)
        has_api = any("api" in f.lower() for f in changed_files)

        if has_readme:
            focus_areas.append("项目介绍和使用说明")
        if has_docs:
            focus_areas.append("技术文档完整性")
        if has_api:
            focus_areas.append("API文档准确性")

        return focus_areas

    def _create_parallel_groups(self, changed_files: List[str]) -> List[List[str]]:
        """创建并行处理组"""
        # 按目录分组，避免文件系统竞争
        groups = {}
        for file_path in changed_files:
            dir_path = str(Path(file_path).parent)
            if dir_path not in groups:
                groups[dir_path] = []
            groups[dir_path].append(file_path)

        return list(groups.values())

    def _estimate_check_time(self, changed_files: List[str]) -> float:
        """估算检查时间"""
        base_time_per_file = 0.5  # 秒
        total_size = sum(self._get_file_size(f) for f in changed_files)
        complexity_factor = min(total_size / (1024 * 100), 5)  # 最多5倍复杂度

        return len(changed_files) * base_time_per_file * complexity_factor

    async def update_state_after_check(self, checked_files: List[str]):
        """检查完成后更新状态"""
        new_state = {
            "last_commit": self._get_current_commit(),
            "last_check_time": datetime.now().isoformat(),
            "branch": self._get_current_branch(),
            "file_hashes": {},
        }

        # 更新文件哈希
        for file_path in checked_files:
            if Path(file_path).exists():
                new_state["file_hashes"][file_path] = self._calculate_file_hash(
                    file_path
                )

        # 保留未检查文件的哈希
        for file_path, file_hash in self.last_check_state.get(
            "file_hashes", {}
        ).items():
            if file_path not in new_state["file_hashes"]:
                new_state["file_hashes"][file_path] = file_hash

        self._save_state(new_state)
        self.last_check_state = new_state

        logger.info(f"Updated incremental state for {len(checked_files)} files")


# 使用示例
async def test_incremental_checker():
    """增量检查器测试"""
    checker = IncrementalChecker("/home/xx/dev/Claude Enhancer 5.0")

    print("🔍 检测文件变更...")
    changed_files = checker.get_changed_files_since_last_check()
    print(f"变更文件: {len(changed_files)}")

    if changed_files:
        file_paths = [change.path for change in changed_files]

        print("🔗 分析依赖关系...")
        dependent_files = checker.get_dependent_files(file_paths)
        print(f"依赖文件: {len(dependent_files)}")

        all_files = list(set(file_paths + list(dependent_files)))

        print("⚡ 优化检查顺序...")
        optimized_files = checker.optimize_check_order(all_files)

        print("📊 创建增量上下文...")
        context = checker.create_incremental_context(file_paths)
        print(f"检查上下文: {context}")

        # 模拟检查完成
        await checker.update_state_after_check(optimized_files)


if __name__ == "__main__":
    asyncio.run(test_incremental_checker())
