#!/usr/bin/env python3
"""
Memory Compression System for Claude Enhancer
防止memory-cache.json无限膨胀，保持<5KB (1200 tokens)

Architecture:
    Hot Storage (memory-cache.json) ← 最近30天的决策
    Cold Storage (.claude/memory-archive/) ← 历史归档
    Quick Index (decision-index.json) ← 快速查找

Strategy:
    - Critical decisions → 永久保留在hot storage
    - Warning (>90 days) → 压缩为摘要
    - Info (>30 days) → 归档到cold storage
    - 保持向后兼容性（旧系统仍可读取）
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Any
import hashlib

# ============================================================================
# Configuration
# ============================================================================

class CompressionConfig:
    """压缩配置（可从memory-cache.json动态读取）"""

    # 默认配置
    RETENTION_DAYS_INFO = 30      # info级别决策保留天数
    RETENTION_DAYS_WARNING = 90   # warning级别决策保留天数
    MAX_SIZE_KB = 5               # 目标大小上限（KB）
    MAX_SIZE_TOKENS = 1200        # 目标token上限（约4字节/token）

    # 路径配置
    PROJECT_ROOT = Path(__file__).parent.parent
    CLAUDE_DIR = PROJECT_ROOT / ".claude"
    MEMORY_CACHE = CLAUDE_DIR / "memory-cache.json"
    DECISION_INDEX = CLAUDE_DIR / "decision-index.json"
    ARCHIVE_DIR = CLAUDE_DIR / "memory-archive"

    # 压缩策略
    IMPORTANCE_LEVELS = ["critical", "warning", "info"]

    @classmethod
    def load_from_cache(cls, cache_data: Dict) -> None:
        """从memory-cache.json加载动态配置"""
        if "_auto_cleanup" in cache_data:
            config = cache_data["_auto_cleanup"]
            cls.RETENTION_DAYS_INFO = config.get("retention_days", cls.RETENTION_DAYS_INFO)
            cls.MAX_SIZE_KB = config.get("max_size_kb", cls.MAX_SIZE_KB)
            archive_path = config.get("archive_path", str(cls.ARCHIVE_DIR))
            cls.ARCHIVE_DIR = Path(archive_path) if not Path(archive_path).is_absolute() else Path(archive_path)


# ============================================================================
# Core Logic
# ============================================================================

class MemoryCompressor:
    """记忆压缩器 - 主控制器"""

    def __init__(self, config: CompressionConfig):
        self.config = config
        self.stats = {
            "decisions_archived": 0,
            "decisions_compressed": 0,
            "size_before_kb": 0.0,
            "size_after_kb": 0.0,
            "tokens_saved": 0
        }

    def run(self, dry_run: bool = False) -> Dict:
        """
        执行压缩流程

        Args:
            dry_run: True = 只分析不修改文件

        Returns:
            压缩统计信息
        """
        print("🚀 Memory Compression System Starting...")
        print(f"   Config: Retention={self.config.RETENTION_DAYS_INFO}days, Max={self.config.MAX_SIZE_KB}KB")
        print(f"   Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        print()

        # Step 1: Load data
        cache_data = self._load_memory_cache()
        if not cache_data:
            print("❌ Failed to load memory-cache.json")
            return self.stats

        self.stats["size_before_kb"] = self._calculate_size_kb(cache_data)
        print(f"📊 Current size: {self.stats['size_before_kb']:.2f} KB")

        # Step 2: Analyze and classify decisions
        decisions_to_archive, decisions_to_compress = self._classify_decisions(cache_data)

        print(f"\n📋 Analysis:")
        print(f"   - To archive: {len(decisions_to_archive)} decisions")
        print(f"   - To compress: {len(decisions_to_compress)} decisions")

        if not decisions_to_archive and not decisions_to_compress:
            print("\n✅ No compression needed. System is healthy!")
            return self.stats

        # Step 3: Execute compression (if not dry run)
        if not dry_run:
            new_cache = self._execute_compression(
                cache_data,
                decisions_to_archive,
                decisions_to_compress
            )

            # Step 4: Save results
            self._save_memory_cache(new_cache)
            self._update_decision_index(decisions_to_archive)

            self.stats["size_after_kb"] = self._calculate_size_kb(new_cache)
            self.stats["tokens_saved"] = int(
                (self.stats["size_before_kb"] - self.stats["size_after_kb"]) * 1024 / 4
            )

            print(f"\n✅ Compression completed!")
            print(f"   Size: {self.stats['size_before_kb']:.2f} KB → {self.stats['size_after_kb']:.2f} KB")
            print(f"   Saved: {self.stats['tokens_saved']} tokens")
        else:
            print("\n🔍 Dry run completed. No files modified.")

        return self.stats

    # ------------------------------------------------------------------------
    # Data Loading
    # ------------------------------------------------------------------------

    def _load_memory_cache(self) -> Dict:
        """加载memory-cache.json"""
        try:
            with open(self.config.MEMORY_CACHE, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 加载动态配置
            CompressionConfig.load_from_cache(data)
            return data
        except FileNotFoundError:
            print(f"⚠️  {self.config.MEMORY_CACHE} not found")
            return {}
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error: {e}")
            return {}

    # ------------------------------------------------------------------------
    # Classification Logic
    # ------------------------------------------------------------------------

    def _classify_decisions(self, cache_data: Dict) -> Tuple[List[Dict], List[Dict]]:
        """
        分类决策：哪些归档，哪些压缩

        Returns:
            (decisions_to_archive, decisions_to_compress)
        """
        decisions_to_archive = []
        decisions_to_compress = []

        recent_decisions = cache_data.get("recent_decisions", {})
        now = datetime.now()

        for key, decision in recent_decisions.items():
            # 提取元数据
            importance = self._get_importance(decision)
            age_days = self._calculate_age_days(decision.get("date", ""), now)

            # 决策规则
            should_archive, should_compress = self._apply_retention_rules(
                importance, age_days
            )

            if should_archive:
                decisions_to_archive.append({
                    "key": key,
                    "data": decision,
                    "importance": importance,
                    "age_days": age_days
                })
            elif should_compress:
                decisions_to_compress.append({
                    "key": key,
                    "data": decision,
                    "importance": importance,
                    "age_days": age_days
                })

        return decisions_to_archive, decisions_to_compress

    def _get_importance(self, decision: Dict) -> str:
        """
        推断决策重要性

        Priority:
            1. 显式标记: decision.get("importance")
            2. do_not_revert标记 → critical
            3. 影响文件数量 → warning/info
        """
        # 显式标记
        if "importance" in decision:
            return decision["importance"]

        # 隐式推断
        if decision.get("do_not_revert") or decision.get("do_not_delete"):
            return "critical"

        affected_count = len(decision.get("affected_files", [])) + \
                        len(decision.get("created_files", [])) + \
                        len(decision.get("deleted_files", []))

        if affected_count >= 5:
            return "warning"
        else:
            return "info"

    def _calculate_age_days(self, date_str: str, now: datetime) -> int:
        """计算决策年龄（天数）"""
        if not date_str:
            return 0

        try:
            decision_date = datetime.strptime(date_str, "%Y-%m-%d")
            return (now - decision_date).days
        except ValueError:
            # 兼容ISO格式
            try:
                decision_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return (now - decision_date.replace(tzinfo=None)).days
            except:
                return 0

    def _apply_retention_rules(self, importance: str, age_days: int) -> Tuple[bool, bool]:
        """
        应用保留规则

        Returns:
            (should_archive, should_compress)
        """
        # Critical永久保留
        if importance == "critical":
            return False, False

        # Warning: >90天归档
        if importance == "warning" and age_days > self.config.RETENTION_DAYS_WARNING:
            return True, False

        # Info: >30天归档
        if importance == "info" and age_days > self.config.RETENTION_DAYS_INFO:
            return True, False

        # 不满足归档条件，但可以压缩（未来扩展）
        return False, False

    # ------------------------------------------------------------------------
    # Compression Execution
    # ------------------------------------------------------------------------

    def _execute_compression(
        self,
        cache_data: Dict,
        decisions_to_archive: List[Dict],
        decisions_to_compress: List[Dict]
    ) -> Dict:
        """
        执行压缩操作

        Returns:
            压缩后的cache_data
        """
        new_cache = cache_data.copy()
        recent_decisions = new_cache.get("recent_decisions", {})

        # Archive decisions
        for item in decisions_to_archive:
            key = item["key"]
            decision = item["data"]

            # 移动到归档
            self._archive_decision(key, decision)

            # 从hot storage删除
            if key in recent_decisions:
                del recent_decisions[key]

            self.stats["decisions_archived"] += 1

        # Compress decisions (保留但精简内容)
        for item in decisions_to_compress:
            key = item["key"]
            decision = item["data"]

            # 生成摘要
            compressed = self._compress_decision(decision)
            recent_decisions[key] = compressed

            self.stats["decisions_compressed"] += 1

        # 更新metadata
        new_cache["_last_compressed"] = datetime.now().isoformat()
        new_cache["_compression_stats"] = {
            "archived": self.stats["decisions_archived"],
            "compressed": self.stats["decisions_compressed"]
        }

        return new_cache

    def _archive_decision(self, key: str, decision: Dict) -> None:
        """归档单个决策到cold storage"""
        # 确定归档文件（按月）
        date_str = decision.get("date", datetime.now().strftime("%Y-%m-%d"))
        year_month = date_str[:7]  # "2025-10"

        archive_file = self.config.ARCHIVE_DIR / f"{year_month}.json"

        # 加载现有归档（如果存在）
        if archive_file.exists():
            with open(archive_file, 'r', encoding='utf-8') as f:
                archive_data = json.load(f)
        else:
            archive_data = {
                "_month": year_month,
                "_archived_at": datetime.now().isoformat(),
                "decisions": {}
            }

        # 添加决策
        archive_data["decisions"][key] = decision

        # 保存
        self.config.ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        with open(archive_file, 'w', encoding='utf-8') as f:
            json.dump(archive_data, f, indent=2, ensure_ascii=False)

        print(f"   📦 Archived: {key} → {archive_file.name}")

    def _compress_decision(self, decision: Dict) -> Dict:
        """
        压缩单个决策为摘要

        Strategy:
            - 保留核心字段：date, decision, rationale
            - 删除详细字段：affected_files, created_files等
            - 添加compressed标记
        """
        compressed = {
            "date": decision.get("date"),
            "decision": decision.get("decision"),
            "rationale": decision.get("rationale"),
            "_compressed": True,
            "_original_size": len(json.dumps(decision))
        }

        # 保留关键标记
        if decision.get("do_not_revert"):
            compressed["do_not_revert"] = True
        if decision.get("do_not_delete"):
            compressed["do_not_delete"] = True

        return compressed

    # ------------------------------------------------------------------------
    # Index Management
    # ------------------------------------------------------------------------

    def _update_decision_index(self, archived_decisions: List[Dict]) -> None:
        """更新decision-index.json快速索引"""
        # 加载现有索引
        if self.config.DECISION_INDEX.exists():
            with open(self.config.DECISION_INDEX, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
        else:
            index_data = {
                "_description": "Index of archived decisions - Quick reference to historical decisions",
                "_purpose": "Allow AI to quickly find relevant past decisions without loading full archives",
                "_last_updated": datetime.now().isoformat(),
                "_version": "1.0",
                "archives": {},
                "_usage": {
                    "for_ai": "When you need context about old decisions, check this index first. If you need full details, load the specific archive file.",
                    "for_humans": "Quick overview of what happened each month. Full details are in the archive files.",
                    "update_frequency": "Updated automatically by memory-compressor.py"
                },
                "_size_tracking": {
                    "current_month": datetime.now().strftime("%Y-%m"),
                    "oldest_month": None,
                    "total_archives": 0,
                    "estimated_total_size_kb": 0.0
                }
            }

        # 更新索引
        archives = index_data.get("archives", {})

        for item in archived_decisions:
            date_str = item["data"].get("date", "")
            year_month = date_str[:7] if date_str else datetime.now().strftime("%Y-%m")
            decision_summary = item["data"].get("decision", "Unknown decision")

            if year_month not in archives:
                archives[year_month] = decision_summary
            else:
                # 合并摘要
                archives[year_month] += f", {decision_summary}"

        # 更新metadata
        index_data["_last_updated"] = datetime.now().isoformat()
        index_data["archives"] = archives

        # 更新size tracking
        archive_files = list(self.config.ARCHIVE_DIR.glob("*.json"))
        total_size_kb = sum(f.stat().st_size for f in archive_files) / 1024

        index_data["_size_tracking"].update({
            "total_archives": len(archive_files),
            "estimated_total_size_kb": round(total_size_kb, 2),
            "oldest_month": min(archives.keys()) if archives else None
        })

        # 保存索引
        with open(self.config.DECISION_INDEX, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)

        print(f"   📇 Updated decision-index.json")

    # ------------------------------------------------------------------------
    # File Operations
    # ------------------------------------------------------------------------

    def _save_memory_cache(self, cache_data: Dict) -> None:
        """保存压缩后的memory-cache.json"""
        # 创建备份
        backup_file = self.config.MEMORY_CACHE.with_suffix('.json.backup')
        if self.config.MEMORY_CACHE.exists():
            import shutil
            shutil.copy(self.config.MEMORY_CACHE, backup_file)

        # 保存新版本
        with open(self.config.MEMORY_CACHE, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2, ensure_ascii=False)

        print(f"   💾 Saved compressed memory-cache.json")
        print(f"   📦 Backup created: {backup_file.name}")

    def _calculate_size_kb(self, data: Dict) -> float:
        """计算JSON数据大小（KB）"""
        json_str = json.dumps(data, ensure_ascii=False)
        return len(json_str.encode('utf-8')) / 1024


# ============================================================================
# CLI Interface
# ============================================================================

def main():
    """主入口"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Memory Compression System - Prevent token inflation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (analyze only)
  python memory-compressor.py --dry-run

  # Execute compression
  python memory-compressor.py

  # Force compression (ignore size check)
  python memory-compressor.py --force

  # Show statistics only
  python memory-compressor.py --stats
        """
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Analyze only, don't modify files"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force compression even if size is under threshold"
    )

    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show current statistics only"
    )

    parser.add_argument(
        "--retention-days",
        type=int,
        help=f"Override retention days (default: {CompressionConfig.RETENTION_DAYS_INFO})"
    )

    args = parser.parse_args()

    # Override config
    if args.retention_days:
        CompressionConfig.RETENTION_DAYS_INFO = args.retention_days

    # Initialize compressor
    config = CompressionConfig()
    compressor = MemoryCompressor(config)

    # Stats mode
    if args.stats:
        show_statistics(config)
        return 0

    # Check if compression needed
    if not args.force and config.MEMORY_CACHE.exists():
        current_size_kb = config.MEMORY_CACHE.stat().st_size / 1024
        if current_size_kb < config.MAX_SIZE_KB:
            print(f"✅ Size is healthy ({current_size_kb:.2f} KB < {config.MAX_SIZE_KB} KB)")
            print("   No compression needed. Use --force to compress anyway.")
            return 0

    # Run compression
    stats = compressor.run(dry_run=args.dry_run)

    # Summary
    print("\n" + "="*60)
    print("📊 Compression Summary:")
    print("="*60)
    print(f"Decisions archived:  {stats['decisions_archived']}")
    print(f"Decisions compressed: {stats['decisions_compressed']}")
    if not args.dry_run:
        print(f"Size reduction:      {stats['size_before_kb']:.2f} KB → {stats['size_after_kb']:.2f} KB")
        print(f"Tokens saved:        ~{stats['tokens_saved']} tokens")
    print("="*60)

    return 0


def show_statistics(config: CompressionConfig) -> None:
    """显示当前统计信息"""
    print("📊 Memory System Statistics")
    print("="*60)

    # Memory cache
    if config.MEMORY_CACHE.exists():
        size_kb = config.MEMORY_CACHE.stat().st_size / 1024
        with open(config.MEMORY_CACHE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        decision_count = len(data.get("recent_decisions", {}))
        print(f"Memory Cache:")
        print(f"  Size: {size_kb:.2f} KB (~{int(size_kb * 1024 / 4)} tokens)")
        print(f"  Decisions: {decision_count}")
        print(f"  Status: {'✅ Healthy' if size_kb < config.MAX_SIZE_KB else '⚠️  Needs compression'}")
    else:
        print("Memory Cache: Not found")

    print()

    # Archives
    if config.ARCHIVE_DIR.exists():
        archives = list(config.ARCHIVE_DIR.glob("*.json"))
        total_size = sum(f.stat().st_size for f in archives)
        print(f"Archives:")
        print(f"  Count: {len(archives)} months")
        print(f"  Total size: {total_size / 1024:.2f} KB")
        print(f"  Location: {config.ARCHIVE_DIR}")
    else:
        print("Archives: None")

    print()

    # Index
    if config.DECISION_INDEX.exists():
        with open(config.DECISION_INDEX, 'r', encoding='utf-8') as f:
            index = json.load(f)

        print(f"Decision Index:")
        print(f"  Months indexed: {len(index.get('archives', {}))}")
        print(f"  Last updated: {index.get('_last_updated', 'Unknown')}")
    else:
        print("Decision Index: Not found")

    print("="*60)


# ============================================================================
# Auto-run via Git Hook
# ============================================================================

def auto_compress_on_commit():
    """
    Git hook集成 - 在每次commit后自动检查是否需要压缩

    Usage in .git/hooks/post-commit:
        python scripts/memory-compressor.py --auto
    """
    config = CompressionConfig()

    if not config.MEMORY_CACHE.exists():
        return

    # Check size
    size_kb = config.MEMORY_CACHE.stat().st_size / 1024

    if size_kb > config.MAX_SIZE_KB:
        print(f"\n⚠️  Memory cache is {size_kb:.2f} KB (threshold: {config.MAX_SIZE_KB} KB)")
        print("🤖 Auto-compressing...")

        compressor = MemoryCompressor(config)
        compressor.run(dry_run=False)


if __name__ == "__main__":
    sys.exit(main())
