#!/usr/bin/env python3
"""
Git缓存层 - 性能优化的Git操作（线程安全版本）
减少subprocess调用，提供智能缓存和批量操作
包含双重检查锁定、Circuit Breaker和Fallback机制
"""

import asyncio
import time
import logging
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger("GitCache")


class CircuitState(Enum):
    """Circuit Breaker状态"""
    CLOSED = "closed"      # 正常状态
    OPEN = "open"          # 熔断状态
    HALF_OPEN = "half_open"  # 半开状态


@dataclass
class CircuitBreakerConfig:
    """Circuit Breaker配置"""
    failure_threshold: int = 5         # 失败阈值
    success_threshold: int = 3         # 恢复阈值
    timeout: int = 60                  # 熔断时间(秒)
    reset_timeout: int = 300           # 重置时间(秒)


@dataclass
class GitStatus:
    """Git状态数据结构"""
    current_branch: str
    staged_files: List[str]
    modified_files: List[str]
    untracked_files: List[str]
    has_staged_changes: bool
    has_uncommitted_changes: bool
    latest_commit: Optional[Dict[str, str]] = None
    remote_status: Optional[Dict[str, Any]] = None
    is_fallback: bool = False          # 是否为fallback数据
    cache_timestamp: float = field(default_factory=time.time)


class CircuitBreaker:
    """Circuit Breaker实现"""

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.lock = threading.RLock()

    def call(self, func: Callable, *args, **kwargs):
        """执行函数调用"""
        with self.lock:
            if self.state == CircuitState.OPEN:
                if time.time() - self.last_failure_time > self.config.timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                    logger.info("Circuit Breaker转换为半开状态")
                else:
                    raise Exception("Circuit Breaker处于开启状态，拒绝调用")

            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except Exception as e:
                self._on_failure()
                raise e

    def _on_success(self):
        """成功回调"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                logger.info("Circuit Breaker恢复到关闭状态")
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0

    def _on_failure(self):
        """失败回调"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit Breaker开启，失败次数: {self.failure_count}")


class GitCache:
    """Git操作缓存层（线程安全版本）"""

    def __init__(self, project_root: str, cache_ttl: int = 30):
        """
        初始化Git缓存

        Args:
            project_root: 项目根目录
            cache_ttl: 缓存生存时间(秒)，默认30秒
        """
        self.project_root = Path(project_root)
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, Any] = {}
        self._last_refresh = 0

        # 锁机制
        self._async_lock = asyncio.Lock()
        self._sync_lock = threading.RLock()

        # Circuit Breaker
        self.circuit_breaker = CircuitBreaker(CircuitBreakerConfig())

        # Fallback数据
        self._fallback_data: Optional[GitStatus] = None
        self._fallback_timestamp = 0

        # 性能监控
        self._performance_metrics = {
            'cache_hits': 0,
            'cache_misses': 0,
            'fallback_uses': 0,
            'circuit_breaker_trips': 0,
            'total_requests': 0,
            'avg_response_time': 0.0
        }

    async def get_git_status(self, force_refresh: bool = False) -> GitStatus:
        """
        获取Git状态信息（双重检查锁定模式）

        Args:
            force_refresh: 是否强制刷新缓存

        Returns:
            GitStatus对象
        """
        start_time = time.time()
        self._performance_metrics['total_requests'] += 1

        try:
            # 第一次检查（无锁）
            current_time = time.time()
            if not force_refresh and self._is_cache_valid_unlocked(current_time):
                self._performance_metrics['cache_hits'] += 1
                return self._get_cached_status()

            # 双重检查锁定
            async with self._async_lock:
                # 第二次检查（已获得锁）
                current_time = time.time()
                if not force_refresh and self._is_cache_valid_locked(current_time):
                    self._performance_metrics['cache_hits'] += 1
                    return self._get_cached_status()

                # 缓存失效，需要刷新
                self._performance_metrics['cache_misses'] += 1

                try:
                    # 使用Circuit Breaker保护
                    git_status = await self.circuit_breaker.call(
                        self._refresh_git_status_with_timeout
                    )

                    # 更新缓存和fallback
                    self._update_cache(git_status, current_time)
                    self._update_fallback(git_status)

                    return git_status

                except Exception as e:
                    logger.error(f"刷新Git状态失败，使用fallback: {e}")
                    self._performance_metrics['circuit_breaker_trips'] += 1
                    return self._get_fallback_status()

        finally:
            # 更新性能指标
            response_time = time.time() - start_time
            self._update_performance_metrics(response_time)

    def _is_cache_valid_unlocked(self, current_time: float) -> bool:
        """检查缓存是否有效（无锁版本）"""
        return (
            'git_status' in self._cache and
            (current_time - self._last_refresh) < self.cache_ttl and
            self._cache.get('git_status') is not None
        )

    def _is_cache_valid_locked(self, current_time: float) -> bool:
        """检查缓存是否有效（已获得锁）"""
        with self._sync_lock:
            return self._is_cache_valid_unlocked(current_time)

    def _get_cached_status(self) -> GitStatus:
        """安全获取缓存状态"""
        with self._sync_lock:
            cached_status = self._cache.get('git_status')
            if cached_status is None:
                raise ValueError("缓存状态为空")
            return cached_status

    def _update_cache(self, git_status: GitStatus, timestamp: float):
        """更新缓存"""
        with self._sync_lock:
            self._cache['git_status'] = git_status
            self._last_refresh = timestamp

    def _update_fallback(self, git_status: GitStatus):
        """更新fallback数据"""
        with self._sync_lock:
            if not git_status.is_fallback:  # 只有真实数据才更新fallback
                self._fallback_data = git_status
                self._fallback_timestamp = time.time()

    def _get_fallback_status(self) -> GitStatus:
        """获取fallback状态"""
        with self._sync_lock:
            self._performance_metrics['fallback_uses'] += 1

            if self._fallback_data is not None:
                # 返回fallback数据的副本，标记为fallback
                fallback_copy = GitStatus(
                    current_branch=self._fallback_data.current_branch,
                    staged_files=self._fallback_data.staged_files.copy(),
                    modified_files=self._fallback_data.modified_files.copy(),
                    untracked_files=self._fallback_data.untracked_files.copy(),
                    has_staged_changes=self._fallback_data.has_staged_changes,
                    has_uncommitted_changes=self._fallback_data.has_uncommitted_changes,
                    latest_commit=self._fallback_data.latest_commit.copy() if self._fallback_data.latest_commit else None,
                    is_fallback=True,
                    cache_timestamp=self._fallback_timestamp
                )
                logger.warning("使用fallback Git状态数据")
                return fallback_copy
            else:
                # 创建最小化的错误状态
                logger.error("无fallback数据，返回错误状态")
                return self._create_error_status("无可用数据，请稍后重试")

    async def _refresh_git_status_with_timeout(self) -> GitStatus:
        """带超时的Git状态刷新"""
        try:
            # 设置30秒超时
            return await asyncio.wait_for(
                self._refresh_git_status(),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            raise Exception("Git操作超时")

    async def _refresh_git_status(self) -> GitStatus:
        """批量刷新Git状态信息"""
        try:
            # 并行执行所有Git命令
            commands = {
                'branch': ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                'status': ['git', 'status', '--porcelain'],
                'staged': ['git', 'diff', '--cached', '--name-only'],
                'modified': ['git', 'diff', '--name-only'],
                'untracked': ['git', 'ls-files', '--others', '--exclude-standard'],
                'log': ['git', 'log', '-1', '--pretty=format:%H|%s|%an|%ad', '--date=iso']
            }

            results = await self._execute_commands_parallel(commands)

            # 解析结果
            return self._parse_git_results(results)

        except Exception as e:
            logger.error(f"刷新Git状态失败: {e}")
            raise e  # 让Circuit Breaker处理

    async def _execute_commands_parallel(self, commands: Dict[str, List[str]]) -> Dict[str, Dict[str, Any]]:
        """并行执行Git命令"""
        async def run_command(name: str, cmd: List[str]) -> tuple:
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    cwd=self.project_root,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=10.0  # 单个命令10秒超时
                )

                return name, {
                    'success': proc.returncode == 0,
                    'returncode': proc.returncode,
                    'stdout': stdout.decode('utf-8').strip(),
                    'stderr': stderr.decode('utf-8').strip()
                }
            except asyncio.TimeoutError:
                return name, {
                    'success': False,
                    'error': 'Command timeout',
                    'stdout': '',
                    'stderr': 'Command execution timeout'
                }
            except Exception as e:
                return name, {
                    'success': False,
                    'error': str(e),
                    'stdout': '',
                    'stderr': str(e)
                }

        # 并行执行所有命令
        tasks = [run_command(name, cmd) for name, cmd in commands.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        parsed_results = {}
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Git命令执行异常: {result}")
                continue
            name, data = result
            parsed_results[name] = data

        return parsed_results

    def _parse_git_results(self, results: Dict[str, Dict[str, Any]]) -> GitStatus:
        """解析Git命令结果"""
        try:
            # 当前分支
            branch_result = results.get('branch', {})
            current_branch = branch_result.get('stdout', 'unknown') if branch_result.get('success') else 'unknown'

            # 暂存文件
            staged_result = results.get('staged', {})
            staged_files = self._parse_file_list(staged_result.get('stdout', '')) if staged_result.get('success') else []

            # 修改文件
            modified_result = results.get('modified', {})
            modified_files = self._parse_file_list(modified_result.get('stdout', '')) if modified_result.get('success') else []

            # 未跟踪文件
            untracked_result = results.get('untracked', {})
            untracked_files = self._parse_file_list(untracked_result.get('stdout', '')) if untracked_result.get('success') else []

            # Git状态
            status_result = results.get('status', {})
            status_lines = status_result.get('stdout', '').split('\n') if status_result.get('success') else []
            status_lines = [line for line in status_lines if line.strip()]

            # 最新提交
            log_result = results.get('log', {})
            latest_commit = self._parse_commit_info(log_result.get('stdout', '')) if log_result.get('success') else None

            return GitStatus(
                current_branch=current_branch,
                staged_files=staged_files,
                modified_files=modified_files,
                untracked_files=untracked_files,
                has_staged_changes=len(staged_files) > 0,
                has_uncommitted_changes=len(modified_files) > 0 or len(staged_files) > 0,
                latest_commit=latest_commit,
                is_fallback=False
            )

        except Exception as e:
            logger.error(f"解析Git结果失败: {e}")
            raise e  # 让Circuit Breaker处理

    def _parse_file_list(self, output: str) -> List[str]:
        """解析文件列表输出"""
        if not output.strip():
            return []
        return [line.strip() for line in output.split('\n') if line.strip()]

    def _parse_commit_info(self, output: str) -> Optional[Dict[str, str]]:
        """解析提交信息"""
        if not output.strip():
            return None

        try:
            parts = output.split('|')
            if len(parts) >= 4:
                return {
                    'hash': parts[0],
                    'message': parts[1],
                    'author': parts[2],
                    'date': parts[3]
                }
        except Exception as e:
            logger.warning(f"解析提交信息失败: {e}")

        return None

    def _create_error_status(self, error_message: str) -> GitStatus:
        """创建错误状态"""
        return GitStatus(
            current_branch='unknown',
            staged_files=[],
            modified_files=[],
            untracked_files=[],
            has_staged_changes=False,
            has_uncommitted_changes=False,
            latest_commit={'error': error_message},
            is_fallback=True
        )

    def _update_performance_metrics(self, response_time: float):
        """更新性能指标"""
        with self._sync_lock:
            # 计算移动平均响应时间
            total_requests = self._performance_metrics['total_requests']
            current_avg = self._performance_metrics['avg_response_time']
            new_avg = ((current_avg * (total_requests - 1)) + response_time) / total_requests
            self._performance_metrics['avg_response_time'] = new_avg

    async def get_branch_info(self, branch_name: str = None) -> Dict[str, Any]:
        """获取分支信息"""
        try:
            if not branch_name:
                git_status = await self.get_git_status()
                branch_name = git_status.current_branch

            commands = {
                'commits_ahead': ['git', 'rev-list', '--count', f'origin/main..{branch_name}'],
                'commits_behind': ['git', 'rev-list', '--count', f'{branch_name}..origin/main'],
                'last_commit': ['git', 'log', '-1', '--pretty=format:%H|%s|%an|%ad', '--date=iso', branch_name]
            }

            results = await self._execute_commands_parallel(commands)

            return {
                'branch_name': branch_name,
                'commits_ahead': int(results.get('commits_ahead', {}).get('stdout', '0') or '0'),
                'commits_behind': int(results.get('commits_behind', {}).get('stdout', '0') or '0'),
                'last_commit': self._parse_commit_info(results.get('last_commit', {}).get('stdout', ''))
            }

        except Exception as e:
            logger.error(f"获取分支信息失败: {e}")
            return {'error': str(e)}

    async def get_file_changes_summary(self) -> Dict[str, Any]:
        """获取文件变更摘要"""
        try:
            git_status = await self.get_git_status()

            # 分析文件类型
            file_analysis = self._analyze_file_types(
                git_status.staged_files + git_status.modified_files
            )

            return {
                'total_files': len(git_status.staged_files) + len(git_status.modified_files),
                'staged_count': len(git_status.staged_files),
                'modified_count': len(git_status.modified_files),
                'untracked_count': len(git_status.untracked_files),
                'file_types': file_analysis,
                'has_critical_changes': file_analysis.get('has_critical_files', False),
                'is_fallback_data': git_status.is_fallback
            }

        except Exception as e:
            logger.error(f"获取文件变更摘要失败: {e}")
            return {'error': str(e)}

    def _analyze_file_types(self, files: List[str]) -> Dict[str, Any]:
        """分析文件类型"""
        analysis = {
            'has_python_files': False,
            'has_config_files': False,
            'has_test_files': False,
            'has_critical_files': False,
            'has_security_sensitive': False,
            'file_type_counts': {}
        }

        critical_patterns = [
            'main/', 'core/', 'infrastructure/', 'requirements.txt',
            'setup.py', 'Dockerfile', 'docker-compose.yml'
        ]

        security_patterns = [
            'auth', 'security', 'password', 'token', 'key', 'secret'
        ]

        for file in files:
            file_lower = file.lower()

            # Python文件
            if file.endswith('.py'):
                analysis['has_python_files'] = True
                analysis['file_type_counts']['python'] = analysis['file_type_counts'].get('python', 0) + 1

            # 配置文件
            if any(ext in file for ext in ['.yml', '.yaml', '.json', '.toml', '.ini']):
                analysis['has_config_files'] = True
                analysis['file_type_counts']['config'] = analysis['file_type_counts'].get('config', 0) + 1

            # 测试文件
            if 'test' in file_lower or file.startswith('test_'):
                analysis['has_test_files'] = True
                analysis['file_type_counts']['test'] = analysis['file_type_counts'].get('test', 0) + 1

            # 关键文件
            if any(pattern in file for pattern in critical_patterns):
                analysis['has_critical_files'] = True

            # 安全敏感文件
            if any(pattern in file_lower for pattern in security_patterns):
                analysis['has_security_sensitive'] = True

        return analysis

    def invalidate_cache(self) -> None:
        """使缓存失效"""
        with self._sync_lock:
            self._cache.clear()
            self._last_refresh = 0
            logger.debug("Git缓存已清空")

    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息"""
        with self._sync_lock:
            current_time = time.time()
            return {
                'cache_ttl': self.cache_ttl,
                'last_refresh': self._last_refresh,
                'time_since_refresh': current_time - self._last_refresh,
                'is_valid': self._is_cache_valid_unlocked(current_time),
                'cached_keys': list(self._cache.keys()),
                'circuit_breaker_state': self.circuit_breaker.state.value,
                'performance_metrics': self._performance_metrics.copy(),
                'has_fallback_data': self._fallback_data is not None,
                'fallback_age': current_time - self._fallback_timestamp if self._fallback_data else None
            }

    def reset_circuit_breaker(self) -> None:
        """重置Circuit Breaker"""
        with self._sync_lock:
            self.circuit_breaker.state = CircuitState.CLOSED
            self.circuit_breaker.failure_count = 0
            self.circuit_breaker.success_count = 0
            logger.info("Circuit Breaker已重置")


class GitCacheManager:
    """Git缓存管理器 - 线程安全单例模式"""

    _instance = None
    _lock = threading.Lock()
    _cache_instances = {}
    _cache_lock = threading.RLock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def get_cache(self, project_root: str, cache_ttl: int = 30) -> GitCache:
        """获取Git缓存实例（线程安全）"""
        cache_key = f"{project_root}:{cache_ttl}"

        # 双重检查锁定
        if cache_key not in self._cache_instances:
            with self._cache_lock:
                if cache_key not in self._cache_instances:
                    self._cache_instances[cache_key] = GitCache(project_root, cache_ttl)

        return self._cache_instances[cache_key]

    def clear_all_caches(self) -> None:
        """清空所有缓存"""
        with self._cache_lock:
            for cache in self._cache_instances.values():
                cache.invalidate_cache()
            logger.info("所有Git缓存已清空")

    def get_all_cache_info(self) -> Dict[str, Any]:
        """获取所有缓存信息"""
        with self._cache_lock:
            return {
                cache_key: cache.get_cache_info()
                for cache_key, cache in self._cache_instances.items()
            }

    def reset_all_circuit_breakers(self) -> None:
        """重置所有Circuit Breaker"""
        with self._cache_lock:
            for cache in self._cache_instances.values():
                cache.reset_circuit_breaker()
            logger.info("所有Circuit Breaker已重置")


# 便捷函数
def get_git_cache(project_root: str = None, cache_ttl: int = 30) -> GitCache:
    """获取Git缓存实例"""
    project_root = project_root or str(Path.cwd())
    manager = GitCacheManager()
    return manager.get_cache(project_root, cache_ttl)


def get_cache_manager() -> GitCacheManager:
    """获取缓存管理器实例"""
    return GitCacheManager()