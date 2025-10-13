#!/usr/bin/env python3
"""
Claude Enhancer智能清理模块
集成到工作流的自动文件管理系统
"""

import os
import re
import time
import shutil
from pathlib import Path
from typing import Dict, List, Set, Tuple
from datetime import datetime, timedelta

class SmartCleanup:
    """智能清理系统 - 融入Claude Enhancer工作流"""

    def __init__(self):
        self.project_root = Path.cwd()
        self.cleanup_log = self.project_root / ".cleanup_log"
        self.stats = {"files_checked": 0, "files_cleaned": 0, "space_saved": 0}

        # 保护目录（永不清理）
        self.protected_dirs = {
            ".git", ".claude", "node_modules", "core", "api",
            "migrations", ".workflow", "sre", "observability"
        }

        # Phase相关的清理规则
        self.phase_rules = {
            "P3": {  # 实现阶段后
                "patterns": ["test_*.tmp", "*_test_output.*", "*.pyc"],
                "aggressive": False
            },
            "P5": {  # 审查阶段后
                "patterns": ["*.bak", "*.backup", "*.log"],
                "aggressive": True
            },
            "P6": {  # 发布阶段前
                "patterns": ["*.tmp", "*.cache", "__pycache__"],
                "aggressive": True
            }
        }

        # 清理分级策略
        self.cleanup_levels = {
            1: {  # 安全级 - 无风险
                "name": "安全清理",
                "patterns": ["*.pyc", "*.pyo", "*~", ".DS_Store", "Thumbs.db"],
                "risk": "无风险"
            },
            2: {  # 临时文件 - 低风险
                "name": "临时文件",
                "patterns": ["*.tmp", "*.temp", "*.swp", "*.swo"],
                "risk": "低风险"
            },
            3: {  # 冗余文件 - 中风险
                "name": "冗余文件",
                "patterns": ["*_copy.*", "*(1).*", "*(2).*", "*_backup.*"],
                "risk": "中风险"
            },
            4: {  # 深度清理 - 高风险
                "name": "深度清理",
                "patterns": ["*_old.*", "*_deprecated.*", "*.orig"],
                "risk": "高风险"
            }
        }

    def get_current_phase(self) -> str:
        """获取当前工作流Phase"""
        phase_file = self.project_root / ".phase" / "current"
        if phase_file.exists():
            return phase_file.read_text().strip()
        return "P1"

    def should_cleanup(self) -> Tuple[bool, str]:
        """判断是否需要清理"""
        # 检查新文件数量
        recent_files = self._find_recent_files(hours=24)
        if len(recent_files) > 100:
            return True, f"最近24小时创建了{len(recent_files)}个文件"

        # 检查垃圾文件数量
        junk_count = self._count_junk_files()
        if junk_count > 50:
            return True, f"发现{junk_count}个垃圾文件"

        # 检查磁盘空间
        trash_size = self._calculate_trash_size()
        if trash_size > 100 * 1024 * 1024:  # 100MB
            return True, f"垃圾文件占用{self._human_size(trash_size)}"

        return False, "暂不需要清理"

    def cleanup_by_phase(self, phase: str = None) -> Dict:
        """根据Phase执行清理"""
        if phase is None:
            phase = self.get_current_phase()

        results = {
            "phase": phase,
            "cleaned_files": [],
            "space_saved": 0,
            "errors": []
        }

        if phase not in self.phase_rules:
            return results

        rule = self.phase_rules[phase]
        for pattern in rule["patterns"]:
            files = self._find_files_by_pattern(pattern)
            for file_path in files:
                if self._is_safe_to_delete(file_path):
                    size = file_path.stat().st_size
                    try:
                        file_path.unlink()
                        results["cleaned_files"].append(str(file_path))
                        results["space_saved"] += size
                    except Exception as e:
                        results["errors"].append(f"{file_path}: {e}")

        return results

    def cleanup_by_level(self, max_level: int = 2) -> Dict:
        """分级清理（1-4级）"""
        results = {
            "levels_cleaned": [],
            "total_files": 0,
            "total_space": 0,
            "details": {}
        }

        for level in range(1, min(max_level + 1, 5)):
            level_info = self.cleanup_levels[level]
            level_results = {
                "name": level_info["name"],
                "risk": level_info["risk"],
                "files": 0,
                "space": 0
            }

            for pattern in level_info["patterns"]:
                files = self._find_files_by_pattern(pattern)
                for file_path in files:
                    if self._is_safe_to_delete(file_path):
                        size = file_path.stat().st_size
                        try:
                            file_path.unlink()
                            level_results["files"] += 1
                            level_results["space"] += size
                        except:
                            pass

            if level_results["files"] > 0:
                results["levels_cleaned"].append(level)
                results["total_files"] += level_results["files"]
                results["total_space"] += level_results["space"]
                results["details"][level] = level_results

        return results

    def smart_cleanup(self, dry_run: bool = False) -> Dict:
        """智能清理主函数"""
        # 1. 检查是否需要清理
        need_cleanup, reason = self.should_cleanup()
        if not need_cleanup and not dry_run:
            return {"status": "skip", "reason": reason}

        # 2. 获取当前Phase
        current_phase = self.get_current_phase()

        # 3. 执行清理
        results = {
            "status": "success",
            "phase": current_phase,
            "reason": reason,
            "phase_cleanup": {},
            "level_cleanup": {},
            "duplicate_cleanup": {},
            "empty_dirs": 0
        }

        # Phase相关清理
        if current_phase in ["P3", "P5", "P6"]:
            results["phase_cleanup"] = self.cleanup_by_phase(current_phase)

        # 分级清理（根据Phase决定级别）
        max_level = 2 if current_phase in ["P1", "P2"] else 3
        results["level_cleanup"] = self.cleanup_by_level(max_level)

        # 清理重复文件
        results["duplicate_cleanup"] = self._cleanup_duplicates(dry_run)

        # 清理空目录
        results["empty_dirs"] = self._cleanup_empty_dirs(dry_run)

        # 记录日志
        self._log_cleanup(results)

        return results

    def _find_recent_files(self, hours: int = 24) -> List[Path]:
        """查找最近创建的文件"""
        recent_files = []
        cutoff_time = time.time() - (hours * 3600)

        for path in self.project_root.rglob("*"):
            if path.is_file() and not self._is_protected(path):
                if path.stat().st_mtime > cutoff_time:
                    recent_files.append(path)

        return recent_files

    def _count_junk_files(self) -> int:
        """统计垃圾文件数量"""
        count = 0
        for level_info in self.cleanup_levels.values():
            for pattern in level_info["patterns"]:
                count += len(self._find_files_by_pattern(pattern))
        return count

    def _calculate_trash_size(self) -> int:
        """计算垃圾文件总大小"""
        total_size = 0
        for level_info in self.cleanup_levels.values():
            for pattern in level_info["patterns"]:
                files = self._find_files_by_pattern(pattern)
                for file_path in files:
                    try:
                        total_size += file_path.stat().st_size
                    except:
                        pass
        return total_size

    def _find_files_by_pattern(self, pattern: str) -> List[Path]:
        """根据模式查找文件"""
        files = []
        try:
            for path in self.project_root.rglob(pattern):
                if path.is_file() and not self._is_protected(path):
                    files.append(path)
        except:
            pass
        return files

    def _is_protected(self, path: Path) -> bool:
        """检查路径是否受保护"""
        path_str = str(path)
        for protected in self.protected_dirs:
            if protected in path_str:
                return True
        return False

    def _is_safe_to_delete(self, path: Path) -> bool:
        """检查文件是否可以安全删除"""
        if self._is_protected(path):
            return False

        # 不删除最近1小时内修改的文件
        if (time.time() - path.stat().st_mtime) < 3600:
            return False

        # 不删除大于10MB的文件（需要人工确认）
        if path.stat().st_size > 10 * 1024 * 1024:
            return False

        return True

    def _cleanup_duplicates(self, dry_run: bool = False) -> Dict:
        """清理重复文件"""
        results = {"files": 0, "space": 0}

        # 查找同名文件
        file_map = {}
        for path in self.project_root.rglob("*"):
            if path.is_file() and not self._is_protected(path):
                name = path.name
                if name not in file_map:
                    file_map[name] = []
                file_map[name].append(path)

        # 清理重复的（保留最新的）
        for name, paths in file_map.items():
            if len(paths) > 1:
                paths.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                for path in paths[1:]:  # 删除除了最新的之外的所有文件
                    if not dry_run:
                        size = path.stat().st_size
                        try:
                            path.unlink()
                            results["files"] += 1
                            results["space"] += size
                        except:
                            pass

        return results

    def _cleanup_empty_dirs(self, dry_run: bool = False) -> int:
        """清理空目录"""
        count = 0
        for root, dirs, files in os.walk(self.project_root, topdown=False):
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                if not self._is_protected(dir_path):
                    try:
                        if not any(dir_path.iterdir()):
                            if not dry_run:
                                dir_path.rmdir()
                            count += 1
                    except:
                        pass
        return count

    def _human_size(self, bytes_size: int) -> str:
        """人性化显示文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f}{unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f}TB"

    def _log_cleanup(self, results: Dict):
        """记录清理日志"""
        with open(self.cleanup_log, 'a') as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"\n[{timestamp}] Phase: {results.get('phase', 'N/A')}\n")
            f.write(f"Reason: {results.get('reason', 'Manual')}\n")

            if results.get('level_cleanup'):
                total_files = results['level_cleanup'].get('total_files', 0)
                total_space = results['level_cleanup'].get('total_space', 0)
                f.write(f"Cleaned: {total_files} files, {self._human_size(total_space)}\n")


# CLI接口
if __name__ == "__main__":
    import sys
    import json

    cleaner = SmartCleanup()

    # 解析参数
    dry_run = "--dry-run" in sys.argv
    check_only = "--check" in sys.argv

    if check_only:
        pass  # Auto-fixed empty block
        # 只检查是否需要清理
        need, reason = cleaner.should_cleanup()
        print(json.dumps({"need_cleanup": need, "reason": reason}))
    else:
        pass  # Auto-fixed empty block
        # 执行清理
        results = cleaner.smart_cleanup(dry_run=dry_run)
        print(json.dumps(results, indent=2, default=str))