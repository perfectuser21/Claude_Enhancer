#!/usr/bin/env python3
"""
异步Git操作缓存管理器 - 性能优化版本
通过异步操作、连接池和批量处理大幅提升性能
"""

import asyncio
import subprocess
import time
import json
import logging
from typing import Dict, Any, Optional, List, Union, Tuple
from functools import lru_cache
import hashlib
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from dataclasses import dataclass
from enum import Enum
import aiofiles
import weakref

logger = logging.getLogger("AsyncGitCache")


class CacheStrategy(Enum):
    """缓存策略"""
    AGGRESSIVE = "aggressive"  # 积极缓存，适合开发环境
    BALANCED = "balanced"     # 平衡缓存，默认选项
    CONSERVATIVE = "conservative"  # 保守缓存，适合生产环境


@dataclass
class GitCommand:
    """Git命令封装"""
    cmd: List[str]
    cwd: Optional[str] = None
    timeout: int = 10
    cache_key: Optional[str] = None
    priority: int = 5  # 1-10，数字越小优先级越高


@dataclass
class BatchResult:
    """批量操作结果"""
    commands: List[GitCommand]
    results: List[subprocess.CompletedProcess]
    execution_time: float
    cache_hits: int
    cache_misses: int


class ConnectionPool:
    """Git操作连接池"""

    def __init__(self, max_workers: int = 4, max_process_workers: int = 2):
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="git-thread")
        self.process_pool = ProcessPoolExecutor(max_workers=max_process_workers)
        self._closed = False

    async def submit_thread(self, func, *args, **kwargs):
        """提交线程池任务"""
        if self._closed:
            raise RuntimeError("Connection pool is closed")
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.thread_pool, func, *args, **kwargs)

    async def submit_process(self, func, *args, **kwargs):
        """提交进程池任务"""
        if self._closed:
            raise RuntimeError("Connection pool is closed")
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.process_pool, func, *args, **kwargs)

    def close(self):
        """关闭连接池"""
        self._closed = True
        self.thread_pool.shutdown(wait=False)
        self.process_pool.shutdown(wait=False)

    def __del__(self):
        if not self._closed:
            self.close()


class AsyncGitCache:
    """异步Git操作缓存管理器"""

    def __init__(self,
                 cache_timeout: int = 30,
                 project_root: str = None,
                 cache_strategy: CacheStrategy = CacheStrategy.BALANCED,
                 max_cache_size: int = 1000,
                 max_workers: int = 4):
        """
        初始化异步Git缓存

        Args:
            cache_timeout: 缓存超时时间（秒）
            project_root: 项目根目录
            cache_strategy: 缓存策略
            max_cache_size: 最大缓存条目数
            max_workers: 最大工作线程数
        """
        self.cache_timeout = cache_timeout
        self.project_root = project_root or '.'
        self.cache_strategy = cache_strategy
        self.max_cache_size = max_cache_size

        # 缓存存储：{cache_key: (result, timestamp, access_count)}
        self._cache: Dict[str, Tuple[Any, float, int]] = {}
        self._cache_lock = asyncio.Lock()

        # 统计信息
        self._stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'subprocess_calls': 0,
            'async_calls': 0,
            'batch_operations': 0,
            'total_time_saved': 0.0
        }

        # 连接池
        self.connection_pool = ConnectionPool(max_workers=max_workers)

        # 批量操作队列
        self._batch_queue: List[GitCommand] = []
        self._batch_lock = asyncio.Lock()
        self._batch_event = asyncio.Event()

        # 启动批量处理任务
        self._batch_task = None
        self._start_batch_processor()

    def _start_batch_processor(self):
        """启动批量处理任务"""
        if self._batch_task is None or self._batch_task.done():
            self._batch_task = asyncio.create_task(self._batch_processor())

    async def _batch_processor(self):
        """批量处理器"""
        while True:
            try:
                await asyncio.sleep(0.1)  # 100ms批量间隔

                async with self._batch_lock:
                    if self._batch_queue:
                        commands_to_process = self._batch_queue.copy()
                        self._batch_queue.clear()

                        # 异步处理批量命令
                        asyncio.create_task(self._process_batch_commands(commands_to_process))

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"批量处理器错误: {e}")

    async def _process_batch_commands(self, commands: List[GitCommand]):
        """处理批量命令"""
        if not commands:
            return

        logger.debug(f"处理批量命令: {len(commands)}个")

        try:
            # 按优先级排序
            commands.sort(key=lambda x: x.priority)

            # 分组执行
            tasks = []
            for cmd in commands:
                task = asyncio.create_task(self._execute_single_command(cmd))
                tasks.append(task)

            # 等待所有命令完成
            await asyncio.gather(*tasks, return_exceptions=True)

            self._stats['batch_operations'] += 1

        except Exception as e:
            logger.error(f"批量命令执行失败: {e}")

    async def _execute_single_command(self, cmd: GitCommand) -> Optional[subprocess.CompletedProcess]:
        """执行单个Git命令"""
        cache_key = cmd.cache_key or self._get_cache_key(cmd.cmd, cmd.cwd)

        # 检查缓存
        cached_result = await self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result

        # 执行命令
        try:
            result = await self.connection_pool.submit_thread(
                self._run_subprocess, cmd.cmd, cmd.cwd, cmd.timeout
            )

            # 缓存结果
            if result and result.returncode == 0:
                await self._set_cache(cache_key, result)

            self._stats['subprocess_calls'] += 1
            return result

        except Exception as e:
            logger.error(f"命令执行失败: {' '.join(cmd.cmd)} - {e}")
            return None

    def _run_subprocess(self, cmd: List[str], cwd: Optional[str], timeout: int) -> subprocess.CompletedProcess:
        """运行subprocess命令（同步版本，在线程池中执行）"""
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd or self.project_root,
            timeout=timeout
        )

    def _get_cache_key(self, cmd: List[str], cwd: str = None) -> str:
        """生成缓存键"""
        cmd_str = ':'.join(cmd)
        cwd_str = cwd or self.project_root
        key_str = f"{cmd_str}:{cwd_str}"
        return hashlib.md5(key_str.encode()).hexdigest()

    async def _is_cache_valid(self, key: str) -> bool:
        """检查缓存是否有效"""
        async with self._cache_lock:
            if key not in self._cache:
                return False

            _, timestamp, _ = self._cache[key]

            # 根据缓存策略调整超时时间
            timeout = self.cache_timeout
            if self.cache_strategy == CacheStrategy.AGGRESSIVE:
                timeout *= 2
            elif self.cache_strategy == CacheStrategy.CONSERVATIVE:
                timeout //= 2

            return (time.time() - timestamp) < timeout

    async def _get_from_cache(self, key: str) -> Optional[Any]:
        """从缓存获取结果"""
        if await self._is_cache_valid(key):
            async with self._cache_lock:
                if key in self._cache:
                    result, timestamp, access_count = self._cache[key]
                    self._cache[key] = (result, timestamp, access_count + 1)
                    self._stats['cache_hits'] += 1
                    logger.debug(f"缓存命中: {key[:8]}...")
                    return result

        self._stats['cache_misses'] += 1
        return None

    async def _set_cache(self, key: str, result: Any):
        """设置缓存"""
        async with self._cache_lock:
            # 检查缓存大小限制
            if len(self._cache) >= self.max_cache_size:
                await self._evict_cache()

            self._cache[key] = (result, time.time(), 0)

    async def _evict_cache(self):
        """缓存淘汰策略（LRU）"""
        if not self._cache:
            return

        # 按访问次数和时间戳排序，移除最少使用的条目
        items = list(self._cache.items())
        items.sort(key=lambda x: (x[1][2], x[1][1]))  # 按访问次数和时间戳排序

        # 移除10%的条目
        remove_count = max(1, len(items) // 10)
        for i in range(remove_count):
            key, _ = items[i]
            del self._cache[key]

        logger.debug(f"缓存淘汰: 移除 {remove_count} 个条目")

    async def get_cached_git_result(self, cmd: List[str], cwd: str = None, priority: int = 5) -> Optional[subprocess.CompletedProcess]:
        """获取缓存的Git命令结果（异步版本）"""
        cache_key = self._get_cache_key(cmd, cwd)

        # 先检查缓存
        cached_result = await self._get_from_cache(cache_key)
        if cached_result is not None:
            return cached_result

        # 创建命令对象
        git_cmd = GitCommand(
            cmd=cmd,
            cwd=cwd,
            cache_key=cache_key,
            priority=priority
        )

        # 直接执行（高优先级）或加入批量队列
        if priority <= 2:
            return await self._execute_single_command(git_cmd)
        else:
            async with self._batch_lock:
                self._batch_queue.append(git_cmd)

            # 等待一小段时间看是否在批量处理中完成
            for _ in range(50):  # 最多等待5秒
                await asyncio.sleep(0.1)
                cached_result = await self._get_from_cache(cache_key)
                if cached_result is not None:
                    return cached_result

            # 如果批量处理没有完成，直接执行
            return await self._execute_single_command(git_cmd)

    async def batch_git_status(self, cwd: str = None) -> Dict[str, Any]:
        """
        批量获取Git状态信息（异步版本）
        """
        try:
            start_time = time.time()

            # 使用单个porcelain命令获取所有信息
            status_cmd = [
                "git", "status",
                "--porcelain=v1",
                "--branch",
                "--ahead-behind"
            ]

            result = await self.get_cached_git_result(status_cmd, cwd, priority=1)
            if not result or result.returncode != 0:
                return await self._get_fallback_status()

            lines = result.stdout.strip().split('\n')

            # 并行解析不同部分
            parse_tasks = [
                self._parse_branch_info(lines[0] if lines else ""),
                self._parse_file_status(lines[1:] if len(lines) > 1 else [])
            ]

            branch_info, file_status = await asyncio.gather(*parse_tasks)

            # 合并结果
            status_info = {**branch_info, **file_status}

            execution_time = time.time() - start_time
            self._stats['total_time_saved'] += max(0, 0.5 - execution_time)  # 假设传统方式需要0.5秒
            self._stats['async_calls'] += 1

            return status_info

        except Exception as e:
            logger.error(f"异步批量获取Git状态失败: {e}")
            return await self._get_fallback_status()

    async def _parse_branch_info(self, branch_line: str) -> Dict[str, Any]:
        """解析分支信息"""
        current_branch = 'unknown'
        ahead, behind = 0, 0

        if branch_line.startswith('## '):
            branch_info = branch_line[3:]
            if '...' in branch_info:
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

        return {
            'current_branch': current_branch,
            'ahead_count': ahead,
            'behind_count': behind
        }

    async def _parse_file_status(self, status_lines: List[str]) -> Dict[str, Any]:
        """解析文件状态"""
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
            'is_clean': len(status_lines) == 0,
            'has_staged_changes': len(staged_files) > 0,
            'has_unstaged_changes': len(modified_files) > 0,
            'staged_files': staged_files,
            'modified_files': modified_files,
            'untracked_files': untracked_files,
            'total_files': len(staged_files) + len(modified_files) + len(untracked_files)
        }

    async def _get_fallback_status(self) -> Dict[str, Any]:
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

    async def batch_git_operations(self, commands: List[GitCommand]) -> BatchResult:
        """批量执行Git操作"""
        start_time = time.time()

        # 按优先级分组
        high_priority = [cmd for cmd in commands if cmd.priority <= 2]
        normal_priority = [cmd for cmd in commands if cmd.priority > 2]

        # 高优先级命令立即执行
        high_priority_tasks = [self._execute_single_command(cmd) for cmd in high_priority]

        # 普通优先级命令加入批量队列
        async with self._batch_lock:
            self._batch_queue.extend(normal_priority)

        # 等待高优先级命令完成
        high_priority_results = await asyncio.gather(*high_priority_tasks, return_exceptions=True)

        # 等待普通优先级命令完成
        normal_priority_results = []
        for cmd in normal_priority:
            for _ in range(100):  # 最多等待10秒
                await asyncio.sleep(0.1)
                cached_result = await self._get_from_cache(cmd.cache_key or self._get_cache_key(cmd.cmd, cmd.cwd))
                if cached_result is not None:
                    normal_priority_results.append(cached_result)
                    break
            else:
                # 超时，直接执行
                result = await self._execute_single_command(cmd)
                normal_priority_results.append(result)

        all_results = high_priority_results + normal_priority_results
        execution_time = time.time() - start_time

        cache_hits = sum(1 for r in all_results if r is not None)
        cache_misses = len(commands) - cache_hits

        return BatchResult(
            commands=commands,
            results=[r for r in all_results if r is not None],
            execution_time=execution_time,
            cache_hits=cache_hits,
            cache_misses=cache_misses
        )

    async def batch_get_file_diff(self, files: List[str]) -> Dict[str, str]:
        """批量获取文件差异（异步版本）"""
        if not files:
            return {}

        # 分批处理大量文件
        batch_size = 20
        all_diffs = {}

        for i in range(0, len(files), batch_size):
            batch_files = files[i:i + batch_size]
            diff_cmd = ["git", "diff", "--"] + batch_files

            result = await self.get_cached_git_result(diff_cmd, priority=3)

            if result and result.returncode == 0:
                batch_diffs = await self._parse_diff_output(result.stdout)
                all_diffs.update(batch_diffs)

        return all_diffs

    async def _parse_diff_output(self, diff_output: str) -> Dict[str, str]:
        """解析diff输出（异步版本）"""
        diffs = {}
        current_file = None
        current_diff = []

        for line in diff_output.split('\n'):
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

        return diffs

    async def prefetch_common_commands(self):
        """预获取常用命令结果"""
        common_commands = [
            GitCommand(["git", "status", "--porcelain"], priority=1),
            GitCommand(["git", "branch", "--show-current"], priority=2),
            GitCommand(["git", "rev-parse", "--abbrev-ref", "HEAD"], priority=2),
            GitCommand(["git", "diff", "--name-only"], priority=3),
            GitCommand(["git", "diff", "--cached", "--name-only"], priority=3),
        ]

        # 异步预获取
        tasks = [self._execute_single_command(cmd) for cmd in common_commands]
        await asyncio.gather(*tasks, return_exceptions=True)

        logger.info(f"预获取了 {len(common_commands)} 个常用Git命令")

    async def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        async with self._cache_lock:
            cache_size = len(self._cache)

        total_requests = self._stats['cache_hits'] + self._stats['cache_misses']
        hit_rate = (self._stats['cache_hits'] / total_requests * 100) if total_requests > 0 else 0

        return {
            'cache_hits': self._stats['cache_hits'],
            'cache_misses': self._stats['cache_misses'],
            'subprocess_calls': self._stats['subprocess_calls'],
            'async_calls': self._stats['async_calls'],
            'batch_operations': self._stats['batch_operations'],
            'hit_rate': f"{hit_rate:.1f}%",
            'cache_size': cache_size,
            'total_time_saved': f"{self._stats['total_time_saved']:.2f}s",
            'cache_strategy': self.cache_strategy.value,
            'connection_pool_active': not self.connection_pool._closed
        }

    async def clear_cache(self):
        """清空缓存"""
        async with self._cache_lock:
            self._cache.clear()
        logger.info("异步Git缓存已清空")

    async def warm_up_cache(self, project_root: str = None):
        """预热缓存"""
        logger.info("开始预热Git缓存...")

        # 预热常用命令
        await self.prefetch_common_commands()

        # 获取当前状态
        await self.batch_git_status(project_root)

        logger.info("Git缓存预热完成")

    def close(self):
        """关闭异步Git缓存"""
        if self._batch_task and not self._batch_task.done():
            self._batch_task.cancel()

        self.connection_pool.close()
        logger.info("异步Git缓存已关闭")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.warm_up_cache()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        self.close()


# 全局异步Git缓存实例
_async_git_cache: Optional[AsyncGitCache] = None


async def get_async_git_cache(project_root: str = None,
                             cache_strategy: CacheStrategy = CacheStrategy.BALANCED) -> AsyncGitCache:
    """获取异步Git缓存实例（单例模式）"""
    global _async_git_cache
    if _async_git_cache is None:
        _async_git_cache = AsyncGitCache(
            project_root=project_root,
            cache_strategy=cache_strategy
        )
        await _async_git_cache.warm_up_cache()
    return _async_git_cache


async def reset_async_git_cache():
    """重置异步Git缓存"""
    global _async_git_cache
    if _async_git_cache:
        await _async_git_cache.clear_cache()
        _async_git_cache.close()
    _async_git_cache = None


# 向后兼容的同步包装器
class SyncGitCacheWrapper:
    """同步Git缓存包装器，为现有代码提供兼容性"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root
        self._async_cache = None
        self._loop = None

    def _get_or_create_loop(self):
        """获取或创建事件循环"""
        try:
            self._loop = asyncio.get_event_loop()
        except RuntimeError:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        return self._loop

    async def _get_async_cache(self):
        """获取异步缓存实例"""
        if self._async_cache is None:
            self._async_cache = await get_async_git_cache(self.project_root)
        return self._async_cache

    def batch_git_status(self, cwd: str = None) -> Dict[str, Any]:
        """同步版本的批量Git状态获取"""
        loop = self._get_or_create_loop()

        async def _async_wrapper():
            cache = await self._get_async_cache()
            return await cache.batch_git_status(cwd)

        return loop.run_until_complete(_async_wrapper())

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        loop = self._get_or_create_loop()

        async def _async_wrapper():
            cache = await self._get_async_cache()
            return await cache.get_performance_stats()

        return loop.run_until_complete(_async_wrapper())


def get_git_cache(project_root: str = None) -> SyncGitCacheWrapper:
    """获取兼容的Git缓存实例"""
    return SyncGitCacheWrapper(project_root)