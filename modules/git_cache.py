#!/usr/bin/env python3
"""
Git操作缓存管理器 - 线程安全版本
通过缓存和批量操作减少subprocess调用
实现了完整的线程安全机制：
- 双重检查锁定(Double-Checked Locking)
- 细粒度锁定(Fine-grained Locking)
- 原子性缓存操作
- 错误恢复机制
- 缓存失效策略
"""

import subprocess
import time
import json
import threading
import weakref
from typing import Dict, Any, Optional, List
from functools import lru_cache
import hashlib
import logging
from collections import defaultdict
from contextlib import contextmanager

logger = logging.getLogger("GitCache")

# 线程安全的常量
DEFAULT_CACHE_TIMEOUT = 30
DEFAULT_MAX_CACHE_SIZE = 1000
DEFAULT_COMMAND_TIMEOUT = 10
MAX_ERROR_COUNT = 3
CACHE_CLEANUP_THRESHOLD = 100


class GitCache:
    """Git操作缓存管理器 - 线程安全版本"""

    def __init__(self, cache_timeout: int = 30, project_root: str = None):
        """
        初始化Git缓存

        Args:
            cache_timeout: 缓存超时时间（秒）
            project_root: 项目根目录
        """
        self.cache_timeout = cache_timeout
        self.project_root = project_root or '.'

        # 线程安全的缓存存储
        self._cache: Dict[str, tuple] = {}  # key -> (result, timestamp)
        self._cache_lock = threading.RLock()  # 可重入锁，支持同一线程多次获取

        # 线程安全的统计信息
        self._stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'subprocess_calls': 0,
            'lock_waits': 0,
            'cache_invalidations': 0
        }
        self._stats_lock = threading.Lock()  # 统计信息专用锁

        # 缓存键锁管理器 - 细粒度锁定
        self._key_locks: Dict[str, threading.RLock] = {}
        self._key_locks_lock = threading.Lock()  # 管理键锁的锁

        # 缓存失效策略
        self._invalidation_callbacks = []
        self._max_cache_size = 1000  # 最大缓存条目数

        # 错误恢复机制
        self._error_count = defaultdict(int)
        self._error_lock = threading.Lock()

    def _is_cache_valid(self, key: str) -> bool:
        """检查缓存是否有效（线程安全）"""
        with self._cache_lock:
            if key not in self._cache:
                return False
            try:
                _, timestamp = self._cache[key]
                return (time.time() - timestamp) < self.cache_timeout
            except (ValueError, TypeError) as e:
                logger.warning(f"缓存数据格式错误，键: {key}, 错误: {e}")
                # 移除损坏的缓存条目
                self._cache.pop(key, None)
                return False

    def _get_cache_key(self, cmd: List[str], cwd: str = None) -> str:
        """生成缓存键"""
        cmd_str = ':'.join(cmd)
        cwd_str = cwd or self.project_root
        key_str = f"{cmd_str}:{cwd_str}"
        return hashlib.md5(key_str.encode()).hexdigest()

    def get_cached_git_result(self, cmd: List[str], cwd: str = None) -> Optional[subprocess.CompletedProcess]:
        """获取缓存的Git命令结果（线程安全，双重检查锁定）"""
        cache_key = self._get_cache_key(cmd, cwd)

        # 第一次检查（无锁快速路径）
        if self._is_cache_valid(cache_key):
            with self._cache_lock:
                # 第二次检查（已获得锁）
                if cache_key in self._cache:
                    try:
                        result, _ = self._cache[cache_key]
                        self._increment_stat('cache_hits')
                        logger.debug(f"缓存命中: {' '.join(cmd)}")
                        return result
                    except (ValueError, TypeError) as e:
                        logger.warning(f"缓存数据损坏，重新执行: {e}")
                        self._cache.pop(cache_key, None)

        # 使用细粒度锁，避免全局锁定
        with self._get_key_lock(cache_key):
            # 再次检查，可能其他线程已经更新了缓存
            if self._is_cache_valid(cache_key):
                with self._cache_lock:
                    if cache_key in self._cache:
                        try:
                            result, _ = self._cache[cache_key]
                            self._increment_stat('cache_hits')
                            logger.debug(f"缓存命中(二次检查): {' '.join(cmd)}")
                            return result
                        except (ValueError, TypeError):
                            self._cache.pop(cache_key, None)

            # 执行命令并缓存
            return self._execute_and_cache_command(cmd, cwd, cache_key)

    def _execute_and_cache_command(self, cmd: List[str], cwd: str, cache_key: str) -> Optional[subprocess.CompletedProcess]:
        """执行命令并缓存结果（已获得键锁）"""
        self._increment_stat('cache_misses')
        self._increment_stat('subprocess_calls')

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=cwd or self.project_root,
                timeout=10
            )

            # 原子性地更新缓存
            with self._cache_lock:
                # 检查缓存大小限制
                if len(self._cache) >= self._max_cache_size:
                    self._evict_old_entries()

                self._cache[cache_key] = (result, time.time())

            # 重置错误计数
            with self._error_lock:
                self._error_count[cache_key] = 0

            logger.debug(f"执行并缓存: {' '.join(cmd)}")
            return result

        except subprocess.TimeoutExpired:
            self._handle_command_error(cache_key, "timeout")
            logger.error(f"命令超时: {' '.join(cmd)}")
            return None
        except Exception as e:
            self._handle_command_error(cache_key, str(e))
            logger.error(f"命令执行失败: {' '.join(cmd)} - {e}")
            return None

    def _handle_command_error(self, cache_key: str, error: str):
        """处理命令执行错误"""
        with self._error_lock:
            self._error_count[cache_key] += 1
            if self._error_count[cache_key] >= 3:
                # 连续失败3次，移除缓存条目
                with self._cache_lock:
                    self._cache.pop(cache_key, None)
                logger.warning(f"命令连续失败，移除缓存: {cache_key}")

    @contextmanager
    def _get_key_lock(self, key: str):
        """获取键专用锁（上下文管理器）"""
        # 获取或创建键锁
        with self._key_locks_lock:
            if key not in self._key_locks:
                self._key_locks[key] = threading.RLock()
            key_lock = self._key_locks[key]

        self._increment_stat('lock_waits')
        try:
            with key_lock:
                yield
        finally:
            # 清理不再使用的锁（可选优化）
            self._cleanup_unused_locks()

    def _cleanup_unused_locks(self):
        """清理不再使用的键锁"""
        if len(self._key_locks) > 100:  # 只在锁数量较多时清理
            with self._key_locks_lock:
                # 保留最近使用的锁
                recent_keys = set()
                with self._cache_lock:
                    current_time = time.time()
                    for key, (_, timestamp) in self._cache.items():
                        if (current_time - timestamp) < self.cache_timeout * 2:
                            recent_keys.add(key)

                # 移除不再需要的锁
                keys_to_remove = set(self._key_locks.keys()) - recent_keys
                for key in list(keys_to_remove)[:50]:  # 每次最多清理50个
                    self._key_locks.pop(key, None)

    def _increment_stat(self, stat_name: str):
        """线程安全地增加统计计数"""
        with self._stats_lock:
            self._stats[stat_name] += 1

    def _evict_old_entries(self):
        """驱逐旧的缓存条目（已获得缓存锁）"""
        if len(self._cache) < self._max_cache_size:
            return

        # 按时间戳排序，移除最旧的25%条目
        sorted_items = sorted(self._cache.items(), key=lambda x: x[1][1])
        evict_count = len(sorted_items) // 4

        for key, _ in sorted_items[:evict_count]:
            self._cache.pop(key, None)

        self._increment_stat('cache_invalidations')
        logger.debug(f"驱逐了 {evict_count} 个旧缓存条目")

    def batch_git_status(self, cwd: str = None) -> Dict[str, Any]:
        """
        批量获取Git状态信息 - 减少subprocess调用（线程安全）

        使用一个命令获取所有需要的信息，而不是多次调用
        """
        try:
            # 使用porcelain格式获取所有信息
            status_cmd = [
                "git", "status",
                "--porcelain=v1",  # 机器可读格式
                "--branch",        # 包含分支信息
                "--ahead-behind"   # 包含ahead/behind信息
            ]

            result = self.get_cached_git_result(status_cmd, cwd)
            if not result or result.returncode != 0:
                return self._get_fallback_status()

            # 原子性地解析结果
            try:
                lines = result.stdout.strip().split('\n')

                # 解析结果
                branch_line = lines[0] if lines else ""
                status_lines = lines[1:] if len(lines) > 1 else []

                # 解析分支信息
                current_branch = 'unknown'
                ahead, behind = 0, 0

                if branch_line.startswith('## '):
                    branch_info = branch_line[3:]
                    if '...' in branch_info:
                        # 格式: ## branch...origin/branch [ahead X, behind Y]
                        parts = branch_info.split('...')
                        current_branch = parts[0]

                        # 解析ahead/behind
                        if '[' in branch_info:
                            tracking_info = branch_info.split('[')[1].rstrip(']')
                            if 'ahead' in tracking_info:
                                try:
                                    ahead = int(tracking_info.split('ahead ')[1].split(',')[0].split(']')[0])
                                except (ValueError, IndexError):
                                    ahead = 0
                            if 'behind' in tracking_info:
                                try:
                                    behind = int(tracking_info.split('behind ')[1].split(',')[0].split(']')[0])
                                except (ValueError, IndexError):
                                    behind = 0
                    else:
                        current_branch = branch_info.split()[0] if branch_info else 'unknown'

                # 统计文件状态
                staged_files = []
                modified_files = []
                untracked_files = []

                for line in status_lines:
                    if not line:
                        continue

                    status = line[:2] if len(line) >= 2 else '  '
                    filename = line[3:] if len(line) > 3 else ''

                    if not filename:
                        continue

                    # 第一个字符表示暂存区状态
                    if status[0] in 'MADRC':
                        staged_files.append(filename)

                    # 第二个字符表示工作区状态
                    if status[1] == 'M':
                        modified_files.append(filename)

                    # 未跟踪文件
                    if status == '??':
                        untracked_files.append(filename)

                return {
                    'current_branch': current_branch,
                    'is_clean': len(status_lines) == 0,
                    'has_staged_changes': len(staged_files) > 0,
                    'has_unstaged_changes': len(modified_files) > 0,
                    'staged_files': staged_files,
                    'modified_files': modified_files,
                    'untracked_files': untracked_files,
                    'ahead_count': ahead,
                    'behind_count': behind,
                    'total_files': len(staged_files) + len(modified_files) + len(untracked_files),
                    'thread_safe': True
                }

            except Exception as parse_error:
                logger.error(f"解析Git状态输出失败: {parse_error}")
                return self._get_fallback_status()

        except Exception as e:
            logger.error(f"批量获取Git状态失败: {e}")
            return self._get_fallback_status()

    def _get_fallback_status(self) -> Dict[str, Any]:
        """降级状态信息"""
        return {
            'current_branch': 'unknown',
            'is_clean': False,
            'has_staged_changes': False,
            'has_unstaged_changes': False,
            'staged_files': [],
            'modified_files': [],
            'untracked_files': [],
            'ahead_count': 0,
            'behind_count': 0,
            'total_files': 0,
            'error': 'Failed to get git status'
        }

    def clear_cache(self):
        """清空缓存（线程安全）"""
        with self._cache_lock:
            self._cache.clear()

        # 清理键锁
        with self._key_locks_lock:
            self._key_locks.clear()

        # 清理错误计数
        with self._error_lock:
            self._error_count.clear()

        # 执行失效回调
        for callback in self._invalidation_callbacks:
            try:
                callback()
            except Exception as e:
                logger.warning(f"缓存失效回调执行失败: {e}")

        self._increment_stat('cache_invalidations')
        logger.info("Git缓存已清空")

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息（线程安全）"""
        with self._stats_lock:
            stats_copy = self._stats.copy()

        with self._cache_lock:
            cache_size = len(self._cache)

        with self._key_locks_lock:
            key_locks_count = len(self._key_locks)

        total_requests = stats_copy['cache_hits'] + stats_copy['cache_misses']
        hit_rate = (stats_copy['cache_hits'] / total_requests * 100) if total_requests > 0 else 0

        return {
            'cache_hits': stats_copy['cache_hits'],
            'cache_misses': stats_copy['cache_misses'],
            'subprocess_calls': stats_copy['subprocess_calls'],
            'lock_waits': stats_copy['lock_waits'],
            'cache_invalidations': stats_copy['cache_invalidations'],
            'hit_rate': f"{hit_rate:.1f}%",
            'cache_size': cache_size,
            'max_cache_size': self._max_cache_size,
            'key_locks_count': key_locks_count,
            'thread_safety_enabled': True
        }

    def batch_get_file_diff(self, files: List[str]) -> Dict[str, str]:
        """批量获取文件差异（线程安全）"""
        if not files:
            return {}

        diffs = {}

        try:
            # 使用单个命令获取所有文件的diff
            diff_cmd = ["git", "diff", "--"] + files
            result = self.get_cached_git_result(diff_cmd, self.project_root)

            if result and result.returncode == 0:
                # 原子性地解析diff输出
                try:
                    current_file = None
                    current_diff = []

                    for line in result.stdout.split('\n'):
                        if line.startswith('diff --git'):
                            # 保存前一个文件的diff
                            if current_file:
                                diffs[current_file] = '\n'.join(current_diff)

                            # 开始新文件
                            parts = line.split()
                            if len(parts) >= 4:
                                current_file = parts[2][2:] if parts[2].startswith('a/') else parts[2]
                                current_diff = [line]
                        elif current_file:
                            current_diff.append(line)

                    # 保存最后一个文件
                    if current_file:
                        diffs[current_file] = '\n'.join(current_diff)

                except Exception as parse_error:
                    logger.error(f"解析diff输出失败: {parse_error}")
                    return {}

        except Exception as e:
            logger.error(f"批量获取文件差异失败: {e}")

        return diffs

    def add_invalidation_callback(self, callback):
        """添加缓存失效回调"""
        if callback not in self._invalidation_callbacks:
            self._invalidation_callbacks.append(callback)

    def remove_invalidation_callback(self, callback):
        """移除缓存失效回调"""
        try:
            self._invalidation_callbacks.remove(callback)
        except ValueError:
            pass

    def force_refresh_cache(self):
        """强制刷新缓存（清理所有缓存条目）"""
        with self._cache_lock:
            old_size = len(self._cache)
            self._cache.clear()

        with self._error_lock:
            self._error_count.clear()

        self._increment_stat('cache_invalidations')
        logger.info(f"强制刷新缓存，清理了 {old_size} 个条目")

    def is_healthy(self) -> bool:
        """检查缓存是否健康"""
        with self._stats_lock:
            total_requests = self._stats['cache_hits'] + self._stats['cache_misses']
            if total_requests == 0:
                return True

            hit_rate = self._stats['cache_hits'] / total_requests
            error_ratio = len(self._error_count) / max(total_requests, 1)

            # 健康标准：命中率 > 60%，错误率 < 10%
            return hit_rate > 0.6 and error_ratio < 0.1

    def get_cache_health_report(self) -> Dict[str, Any]:
        """获取缓存健康报告"""
        stats = self.get_stats()

        with self._cache_lock:
            cache_size = len(self._cache)

        with self._error_lock:
            error_count = len(self._error_count)
            total_errors = sum(self._error_count.values())

        total_requests = stats['cache_hits'] + stats['cache_misses']
        hit_rate = float(stats['hit_rate'].rstrip('%')) if total_requests > 0 else 0

        health_score = 100
        issues = []

        # 命中率检查
        if hit_rate < 60:
            health_score -= 30
            issues.append(f"低命中率: {hit_rate:.1f}%")

        # 错误率检查
        error_ratio = total_errors / max(total_requests, 1) * 100
        if error_ratio > 10:
            health_score -= 25
            issues.append(f"高错误率: {error_ratio:.1f}%")

        # 缓存大小检查
        if cache_size > self._max_cache_size * 0.9:
            health_score -= 15
            issues.append(f"缓存迅速填满: {cache_size}/{self._max_cache_size}")

        # 锁竞争检查
        lock_ratio = stats['lock_waits'] / max(total_requests, 1)
        if lock_ratio > 0.5:
            health_score -= 20
            issues.append(f"高锁竞争: {lock_ratio:.1f}")

        health_score = max(0, health_score)

        return {
            'health_score': health_score,
            'status': 'healthy' if health_score >= 80 else 'warning' if health_score >= 60 else 'critical',
            'issues': issues,
            'metrics': {
                'hit_rate': hit_rate,
                'error_ratio': error_ratio,
                'cache_utilization': cache_size / self._max_cache_size * 100,
                'lock_contention': lock_ratio,
                'total_errors': total_errors,
                'unique_error_keys': error_count
            },
            'recommendations': self._get_health_recommendations(health_score, issues)
        }

    def _get_health_recommendations(self, health_score: int, issues: List[str]) -> List[str]:
        """获取健康改进建议"""
        recommendations = []

        if health_score < 60:
            recommendations.append("考虑增加缓存超时时间")
            recommendations.append("检查Git操作是否过于频繁")

        if "低命中率" in ' '.join(issues):
            recommendations.append("优化缓存键生成策略")
            recommendations.append("考虑预热常用缓存")

        if "高错误率" in ' '.join(issues):
            recommendations.append("检查Git仓库状态和网络连接")
            recommendations.append("实现更健壮的错误处理")

        if "高锁竞争" in ' '.join(issues):
            recommendations.append("优化并发访问模式")
            recommendations.append("考虑使用更细粒度的锁")

        return recommendations


# 线程安全的全局Git缓存管理
class GitCacheManager:
    """线程安全的Git缓存管理器"""

    _instance: Optional['GitCacheManager'] = None
    _instance_lock = threading.Lock()

    def __init__(self):
        self._caches: Dict[str, GitCache] = {}
        self._cache_locks: Dict[str, threading.RLock] = {}
        self._caches_lock = threading.RLock()
        # 使用弱引用避免循环引用
        self._cache_refs: Dict[str, weakref.ReferenceType] = {}

    @classmethod
    def get_instance(cls) -> 'GitCacheManager':
        """获取单例实例（双重检查锁定）"""
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def get_cache(self, project_root: str = None, cache_timeout: int = 30) -> GitCache:
        """获取Git缓存实例（线程安全）"""
        project_root = project_root or '.'
        cache_key = f"{project_root}:{cache_timeout}"

        # 第一次检查（无锁快速路径）
        with self._caches_lock:
            if cache_key in self._caches:
                cache = self._caches[cache_key]
                if cache is not None:  # 检查缓存是否仍然有效
                    return cache

        # 获取或创建缓存（双重检查锁定）
        cache_lock = self._get_or_create_cache_lock(cache_key)
        with cache_lock:
            # 第二次检查
            with self._caches_lock:
                if cache_key in self._caches and self._caches[cache_key] is not None:
                    return self._caches[cache_key]

                # 创建新缓存
                cache = GitCache(cache_timeout=cache_timeout, project_root=project_root)
                self._caches[cache_key] = cache

                # 设置弱引用用于清理
                self._cache_refs[cache_key] = weakref.ref(
                    cache,
                    lambda ref: self._cleanup_cache(cache_key)
                )

                logger.debug(f"创建新的Git缓存实例: {cache_key}")
                return cache

    def _get_or_create_cache_lock(self, cache_key: str) -> threading.RLock:
        """获取或创建缓存专用锁"""
        with self._caches_lock:
            if cache_key not in self._cache_locks:
                self._cache_locks[cache_key] = threading.RLock()
            return self._cache_locks[cache_key]

    def _cleanup_cache(self, cache_key: str):
        """清理无效的缓存引用"""
        try:
            with self._caches_lock:
                self._caches.pop(cache_key, None)
                self._cache_locks.pop(cache_key, None)
                self._cache_refs.pop(cache_key, None)
        except Exception as e:
            logger.warning(f"清理缓存引用失败: {e}")

    def reset_all_caches(self):
        """重置所有缓存"""
        with self._caches_lock:
            for cache in self._caches.values():
                if cache is not None:
                    try:
                        cache.clear_cache()
                    except Exception as e:
                        logger.warning(f"清理缓存失败: {e}")

            self._caches.clear()
            self._cache_locks.clear()
            self._cache_refs.clear()

        logger.info("所有Git缓存已重置")

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取所有缓存的统计信息"""
        with self._caches_lock:
            stats = {}
            for key, cache in self._caches.items():
                if cache is not None:
                    try:
                        stats[key] = cache.get_stats()
                    except Exception as e:
                        stats[key] = {'error': str(e)}
            return stats

    def register_invalidation_callback(self, callback):
        """注册缓存失效回调"""
        with self._caches_lock:
            for cache in self._caches.values():
                if cache is not None:
                    cache._invalidation_callbacks.append(callback)


# 便捷函数
def get_git_cache(project_root: str = None, cache_timeout: int = 30) -> GitCache:
    """获取Git缓存实例（线程安全）"""
    manager = GitCacheManager.get_instance()
    return manager.get_cache(project_root, cache_timeout)


def reset_git_cache():
    """重置Git缓存（线程安全）"""
    manager = GitCacheManager.get_instance()
    manager.reset_all_caches()


def get_cache_stats() -> Dict[str, Dict[str, Any]]:
    """获取所有缓存统计信息"""
    manager = GitCacheManager.get_instance()
    return manager.get_all_stats()


def register_cache_invalidation_callback(callback):
    """注册缓存失效回调"""
    manager = GitCacheManager.get_instance()
    manager.register_invalidation_callback(callback)


def get_cache_health_report(project_root: str = None) -> Dict[str, Any]:
    """获取缓存健康报告"""
    cache = get_git_cache(project_root)
    return cache.get_cache_health_report()


def force_refresh_cache(project_root: str = None):
    """强制刷新缓存"""
    cache = get_git_cache(project_root)
    cache.force_refresh_cache()


def is_cache_healthy(project_root: str = None) -> bool:
    """检查缓存是否健康"""
    cache = get_git_cache(project_root)
    return cache.is_healthy()