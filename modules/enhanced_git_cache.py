#!/usr/bin/env python3
"""
增强Git缓存优化器
专为Perfect21优化的Git操作缓存和批量处理系统
"""

import os
import sys
import time
import asyncio
import threading
import hashlib
import pickle
from typing import Dict, Any, List, Optional, Callable, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field
import subprocess
import json

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.logger import log_info, log_error, log_warning
from modules.config import config

@dataclass
class GitCacheEntry:
    """Git缓存条目"""
    command: str
    args: List[str]
    result: Any
    timestamp: float
    ttl: float = 30.0  # 30秒默认TTL
    hit_count: int = 0
    last_access: float = 0.0
    project_root: str = "."

@dataclass
class BatchOperation:
    """批量操作"""
    operation_id: str
    command: str
    args: List[str]
    callback: Optional[Callable] = None
    priority: int = 5
    timestamp: float = field(default_factory=time.time)
    project_root: str = "."

class EnhancedGitCache:
    """增强Git缓存系统"""

    def __init__(self):
        self.cache: Dict[str, GitCacheEntry] = {}
        self.lock = threading.RLock()

        # 缓存配置
        self.max_cache_size = config.get('performance.git_cache.max_size', 1000)
        self.default_ttl = config.get('performance.git_cache.default_ttl', 30)
        self.enable_compression = config.get('performance.git_cache.compression', True)

        # 统计信息
        self.stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'total_requests': 0
        }

        # 智能缓存策略
        self.high_frequency_commands = {'status', 'branch', 'log', 'diff'}
        self.long_cache_commands = {'log', 'blame', 'show'}
        self.short_cache_commands = {'status', 'diff', 'stash'}

        log_info("增强Git缓存系统初始化完成")

    def _generate_cache_key(self, command: str, args: List[str], project_root: str = ".") -> str:
        """生成缓存键"""
        # 标准化参数
        normalized_args = []
        for arg in args:
            # 路径标准化
            if os.path.exists(arg):
                normalized_args.append(os.path.abspath(arg))
            else:
                normalized_args.append(arg)

        key_parts = [project_root, command] + normalized_args
        key_str = "|".join(str(part) for part in key_parts)

        # 对长键进行哈希
        if len(key_str) > 100:
            return f"{command}:{hashlib.md5(key_str.encode()).hexdigest()}"
        return key_str

    def _determine_ttl(self, command: str, args: List[str]) -> float:
        """智能确定TTL"""
        # 根据命令类型设置不同的TTL
        if command in self.long_cache_commands:
            return 300  # 5分钟
        elif command in self.short_cache_commands:
            return 10   # 10秒
        elif command == 'log' and any('--since' in arg or '--until' in arg for arg in args):
            return 600  # 时间范围查询缓存更长时间
        else:
            return self.default_ttl

    def _should_cache(self, command: str, args: List[str]) -> bool:
        """判断是否应该缓存"""
        # 不缓存的命令
        no_cache_commands = {'add', 'commit', 'push', 'pull', 'merge', 'rebase', 'reset'}
        if command in no_cache_commands:
            return False

        # 不缓存包含变更操作的命令
        change_args = {'-f', '--force', '--delete', '--prune'}
        if any(arg in change_args for arg in args):
            return False

        return True

    def _compress_result(self, result: Any) -> bytes:
        """压缩结果"""
        if self.enable_compression:
            try:
                import gzip
                pickled = pickle.dumps(result)
                return gzip.compress(pickled)
            except:
                return pickle.dumps(result)
        return pickle.dumps(result)

    def _decompress_result(self, compressed_data: bytes) -> Any:
        """解压结果"""
        if self.enable_compression:
            try:
                import gzip
                pickled = gzip.decompress(compressed_data)
                return pickle.loads(pickled)
            except:
                return pickle.loads(compressed_data)
        return pickle.loads(compressed_data)

    def get_cached_result(self, command: str, args: List[str], project_root: str = ".") -> Optional[Any]:
        """获取缓存的Git命令结果"""
        if not self._should_cache(command, args):
            return None

        cache_key = self._generate_cache_key(command, args, project_root)

        with self.lock:
            self.stats['total_requests'] += 1

            if cache_key in self.cache:
                entry = self.cache[cache_key]

                # 检查TTL
                if time.time() - entry.timestamp <= entry.ttl:
                    entry.hit_count += 1
                    entry.last_access = time.time()
                    self.stats['hits'] += 1

                    log_info(f"Git缓存命中: {command} {' '.join(args[:3])}... (hit_count: {entry.hit_count})")
                    return entry.result
                else:
                    # 过期删除
                    del self.cache[cache_key]
                    self.stats['evictions'] += 1

            self.stats['misses'] += 1
            return None

    def cache_result(self, command: str, args: List[str], result: Any, project_root: str = ".") -> None:
        """缓存Git命令结果"""
        if not self._should_cache(command, args):
            return

        cache_key = self._generate_cache_key(command, args, project_root)
        ttl = self._determine_ttl(command, args)

        # 检查缓存容量
        if len(self.cache) >= self.max_cache_size:
            self._evict_cache()

        with self.lock:
            entry = GitCacheEntry(
                command=command,
                args=args.copy(),
                result=result,
                timestamp=time.time(),
                ttl=ttl,
                last_access=time.time(),
                project_root=project_root
            )

            self.cache[cache_key] = entry
            log_info(f"Git结果已缓存: {command} (TTL: {ttl}s)")

    def _evict_cache(self) -> None:
        """缓存淘汰"""
        with self.lock:
            if not self.cache:
                return

            # LFU + LRU 混合策略
            entries = list(self.cache.items())

            # 按照访问频率和时间排序
            entries.sort(key=lambda x: (x[1].hit_count, x[1].last_access))

            # 淘汰最少使用的25%
            evict_count = max(1, len(entries) // 4)
            for i in range(evict_count):
                key = entries[i][0]
                if key in self.cache:
                    del self.cache[key]
                    self.stats['evictions'] += 1

        log_info(f"Git缓存淘汰: 移除 {evict_count} 个条目")

    def invalidate_status_cache(self, project_root: str = ".") -> None:
        """使状态相关缓存失效"""
        status_commands = {'status', 'diff', 'log'}

        with self.lock:
            keys_to_remove = []
            for key, entry in self.cache.items():
                if (entry.project_root == project_root and
                    entry.command in status_commands):
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del self.cache[key]

        if keys_to_remove:
            log_info(f"状态缓存失效: 移除 {len(keys_to_remove)} 个条目")

    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self.lock:
            hit_rate = (self.stats['hits'] / max(1, self.stats['total_requests'])) * 100

            return {
                'total_entries': len(self.cache),
                'hit_rate': f"{hit_rate:.1f}%",
                'total_requests': self.stats['total_requests'],
                'hits': self.stats['hits'],
                'misses': self.stats['misses'],
                'evictions': self.stats['evictions'],
                'cache_size_limit': self.max_cache_size
            }

class GitBatchProcessor:
    """Git批量操作处理器"""

    def __init__(self, git_cache: EnhancedGitCache):
        self.git_cache = git_cache
        self.batch_queue = deque()
        self.batch_lock = threading.Lock()
        self.batch_timer: Optional[threading.Timer] = None
        self.batch_interval = 2.0  # 2秒批量间隔
        self.processing = False

        # 批量策略配置
        self.batchable_commands = {'status', 'log', 'branch', 'diff', 'show'}
        self.max_batch_size = 50

        log_info("Git批量处理器初始化完成")

    def queue_operation(self, command: str, args: List[str], callback: Optional[Callable] = None,
                       priority: int = 5, project_root: str = ".") -> str:
        """队列Git操作"""
        operation_id = f"{command}_{int(time.time() * 1000000)}"

        operation = BatchOperation(
            operation_id=operation_id,
            command=command,
            args=args,
            callback=callback,
            priority=priority,
            project_root=project_root
        )

        with self.batch_lock:
            self.batch_queue.append(operation)

        # 调度批量处理
        self._schedule_batch_processing()

        return operation_id

    def _schedule_batch_processing(self):
        """调度批量处理"""
        if self.batch_timer is None or not self.batch_timer.is_alive():
            self.batch_timer = threading.Timer(self.batch_interval, self._process_batch)
            self.batch_timer.start()

    def _process_batch(self):
        """处理批量操作"""
        with self.batch_lock:
            if not self.batch_queue or self.processing:
                return

            self.processing = True
            current_batch = list(self.batch_queue)
            self.batch_queue.clear()

        try:
            # 按项目根目录和命令类型分组
            operations_by_group = defaultdict(list)
            for op in current_batch:
                group_key = f"{op.project_root}:{op.command}"
                operations_by_group[group_key].append(op)

            # 处理各组操作
            for group_key, operations in operations_by_group.items():
                self._process_operation_group(operations)

        except Exception as e:
            log_error(f"批量处理失败: {e}")

        finally:
            self.processing = False
            self.batch_timer = None

    def _process_operation_group(self, operations: List[BatchOperation]):
        """处理操作组"""
        if not operations:
            return

        command = operations[0].command
        project_root = operations[0].project_root

        if command in self.batchable_commands:
            if command == 'status':
                self._batch_status_operations(operations)
            elif command == 'log':
                self._batch_log_operations(operations)
            elif command == 'branch':
                self._batch_branch_operations(operations)
            else:
                # 其他可批量命令
                for op in operations:
                    self._execute_single_operation(op)
        else:
            # 不可批量命令逐个执行
            for op in operations:
                self._execute_single_operation(op)

    def _batch_status_operations(self, operations: List[BatchOperation]):
        """批量状态操作"""
        if not operations:
            return

        project_root = operations[0].project_root

        try:
            # 检查缓存
            cached_result = self.git_cache.get_cached_result('status', [], project_root)
            if cached_result:
                # 使用缓存结果回调所有操作
                for op in operations:
                    if op.callback:
                        op.callback(cached_result)
                log_info(f"批量状态查询使用缓存: {len(operations)} 个操作")
                return

            # 执行一次完整的Git状态查询
            result = self._execute_git_command('status', ['--porcelain', '-b'], project_root)

            if result['success']:
                # 解析结果
                status_data = self._parse_status_output(result['output'])

                # 缓存结果
                self.git_cache.cache_result('status', [], status_data, project_root)

                # 为所有操作提供结果
                for op in operations:
                    # 根据具体参数筛选结果
                    filtered_result = self._filter_status_result(status_data, op.args)
                    if op.callback:
                        op.callback(filtered_result)

                log_info(f"批量状态查询完成: {len(operations)} 个操作")

            else:
                log_error(f"批量状态查询失败: {result.get('error', 'unknown')}")
                # 回调错误
                for op in operations:
                    if op.callback:
                        op.callback({'error': result.get('error', 'Git command failed')})

        except Exception as e:
            log_error(f"批量状态操作异常: {e}")

    def _batch_log_operations(self, operations: List[BatchOperation]):
        """批量日志操作"""
        if not operations:
            return

        project_root = operations[0].project_root

        try:
            # 分析所有操作的参数，确定最大需求
            max_count = 50  # 默认最大数量
            all_files = set()

            for op in operations:
                # 解析--max-count或-n参数
                for i, arg in enumerate(op.args):
                    if arg == '--max-count' or arg == '-n':
                        if i + 1 < len(op.args):
                            try:
                                count = int(op.args[i + 1])
                                max_count = max(max_count, count)
                            except ValueError:
                                pass
                    elif arg.startswith('--max-count='):
                        try:
                            count = int(arg.split('=', 1)[1])
                            max_count = max(max_count, count)
                        except ValueError:
                            pass

                # 收集文件路径
                for arg in op.args:
                    if not arg.startswith('-') and os.path.exists(os.path.join(project_root, arg)):
                        all_files.add(arg)

            # 构建批量查询参数
            batch_args = ['--oneline', f'--max-count={max_count}']
            if all_files:
                batch_args.extend(['--'] + list(all_files))

            # 检查缓存
            cache_key = f"log:{':'.join(batch_args)}"
            cached_result = self.git_cache.get_cached_result('log', batch_args, project_root)
            if cached_result:
                # 为每个操作筛选结果
                for op in operations:
                    filtered_result = self._filter_log_result(cached_result, op.args)
                    if op.callback:
                        op.callback(filtered_result)
                log_info(f"批量日志查询使用缓存: {len(operations)} 个操作")
                return

            # 执行批量Git日志查询
            result = self._execute_git_command('log', batch_args, project_root)

            if result['success']:
                log_data = self._parse_log_output(result['output'])

                # 缓存结果
                self.git_cache.cache_result('log', batch_args, log_data, project_root)

                # 为每个操作提供筛选后的结果
                for op in operations:
                    filtered_result = self._filter_log_result(log_data, op.args)
                    if op.callback:
                        op.callback(filtered_result)

                log_info(f"批量日志查询完成: {len(operations)} 个操作")

            else:
                log_error(f"批量日志查询失败: {result.get('error', 'unknown')}")

        except Exception as e:
            log_error(f"批量日志操作异常: {e}")

    def _batch_branch_operations(self, operations: List[BatchOperation]):
        """批量分支操作"""
        project_root = operations[0].project_root

        try:
            # 执行完整的分支查询
            result = self._execute_git_command('branch', ['-a', '-v'], project_root)

            if result['success']:
                branch_data = self._parse_branch_output(result['output'])

                # 缓存结果
                self.git_cache.cache_result('branch', ['-a', '-v'], branch_data, project_root)

                # 为每个操作筛选结果
                for op in operations:
                    filtered_result = self._filter_branch_result(branch_data, op.args)
                    if op.callback:
                        op.callback(filtered_result)

                log_info(f"批量分支查询完成: {len(operations)} 个操作")

        except Exception as e:
            log_error(f"批量分支操作异常: {e}")

    def _execute_single_operation(self, operation: BatchOperation):
        """执行单个Git操作"""
        try:
            # 检查缓存
            cached_result = self.git_cache.get_cached_result(
                operation.command, operation.args, operation.project_root
            )
            if cached_result:
                if operation.callback:
                    operation.callback(cached_result)
                return

            # 执行Git命令
            result = self._execute_git_command(
                operation.command, operation.args, operation.project_root
            )

            if result['success']:
                # 缓存结果
                self.git_cache.cache_result(
                    operation.command, operation.args, result['output'], operation.project_root
                )

                if operation.callback:
                    operation.callback(result['output'])
            else:
                if operation.callback:
                    operation.callback({'error': result.get('error', 'Git command failed')})

        except Exception as e:
            log_error(f"单个Git操作执行失败 {operation.command}: {e}")
            if operation.callback:
                operation.callback({'error': str(e)})

    def _execute_git_command(self, command: str, args: List[str], project_root: str = ".") -> Dict[str, Any]:
        """执行Git命令"""
        cmd = ['git', command] + args

        try:
            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=30
            )

            return {
                'success': result.returncode == 0,
                'output': result.stdout.strip(),
                'error': result.stderr.strip() if result.returncode != 0 else None
            }

        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Git command timeout'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _parse_status_output(self, output: str) -> Dict[str, Any]:
        """解析状态输出"""
        lines = output.split('\n') if output else []
        status_data = {
            'branch': '',
            'staged': [],
            'modified': [],
            'untracked': [],
            'ahead': 0,
            'behind': 0
        }

        for line in lines:
            if line.startswith('##'):
                # 分支信息
                parts = line[3:].split()
                if parts:
                    branch_info = parts[0]
                    if '...' in branch_info:
                        status_data['branch'] = branch_info.split('...')[0]
                    else:
                        status_data['branch'] = branch_info

                    # 检查ahead/behind
                    if '[ahead' in line:
                        import re
                        ahead_match = re.search(r'ahead (\d+)', line)
                        if ahead_match:
                            status_data['ahead'] = int(ahead_match.group(1))

                    if '[behind' in line or ', behind' in line:
                        import re
                        behind_match = re.search(r'behind (\d+)', line)
                        if behind_match:
                            status_data['behind'] = int(behind_match.group(1))

            elif len(line) >= 3:
                # 文件状态
                status = line[:2]
                filename = line[3:]

                if status[0] != ' ':  # 暂存区
                    status_data['staged'].append(filename)
                elif status[1] != ' ':  # 工作区
                    status_data['modified'].append(filename)
                elif status == '??':  # 未跟踪
                    status_data['untracked'].append(filename)

        return status_data

    def _parse_log_output(self, output: str) -> List[Dict[str, str]]:
        """解析日志输出"""
        lines = output.split('\n') if output else []
        log_entries = []

        for line in lines:
            if line.strip():
                parts = line.split(' ', 1)
                if len(parts) >= 2:
                    log_entries.append({
                        'hash': parts[0],
                        'message': parts[1]
                    })

        return log_entries

    def _parse_branch_output(self, output: str) -> Dict[str, Any]:
        """解析分支输出"""
        lines = output.split('\n') if output else []
        branches = {
            'local': [],
            'remote': [],
            'current': ''
        }

        for line in lines:
            line = line.strip()
            if not line:
                continue

            is_current = line.startswith('*')
            branch_line = line[2:] if is_current else line

            if branch_line.startswith('remotes/'):
                # 远程分支
                branch_name = branch_line[8:]  # 移除"remotes/"前缀
                branches['remote'].append(branch_name)
            else:
                # 本地分支
                branch_name = branch_line.split()[0]
                branches['local'].append(branch_name)
                if is_current:
                    branches['current'] = branch_name

        return branches

    def _filter_status_result(self, status_data: Dict[str, Any], args: List[str]) -> Dict[str, Any]:
        """筛选状态结果"""
        # 根据参数筛选状态结果
        if '--short' in args or '-s' in args:
            # 简短格式
            return {
                'staged': len(status_data['staged']),
                'modified': len(status_data['modified']),
                'untracked': len(status_data['untracked'])
            }
        else:
            return status_data

    def _filter_log_result(self, log_data: List[Dict[str, str]], args: List[str]) -> List[Dict[str, str]]:
        """筛选日志结果"""
        # 根据参数筛选日志结果
        count_limit = None

        for i, arg in enumerate(args):
            if arg == '--max-count' or arg == '-n':
                if i + 1 < len(args):
                    try:
                        count_limit = int(args[i + 1])
                    except ValueError:
                        pass
            elif arg.startswith('--max-count='):
                try:
                    count_limit = int(arg.split('=', 1)[1])
                except ValueError:
                    pass

        if count_limit is not None:
            return log_data[:count_limit]
        else:
            return log_data

    def _filter_branch_result(self, branch_data: Dict[str, Any], args: List[str]) -> Dict[str, Any]:
        """筛选分支结果"""
        # 根据参数筛选分支结果
        if '-r' in args:
            # 只显示远程分支
            return {'branches': branch_data['remote']}
        elif '-a' not in args:
            # 只显示本地分支
            return {
                'branches': branch_data['local'],
                'current': branch_data['current']
            }
        else:
            return branch_data

# 全局实例
enhanced_git_cache = EnhancedGitCache()
git_batch_processor = GitBatchProcessor(enhanced_git_cache)

# 便捷函数
def get_cached_git_result(command: str, args: List[str], project_root: str = ".") -> Optional[Any]:
    """获取Git缓存结果"""
    return enhanced_git_cache.get_cached_result(command, args, project_root)

def cache_git_result(command: str, args: List[str], result: Any, project_root: str = ".") -> None:
    """缓存Git结果"""
    enhanced_git_cache.cache_result(command, args, result, project_root)

def queue_git_operation(command: str, args: List[str], callback: Optional[Callable] = None,
                       project_root: str = ".") -> str:
    """队列Git操作"""
    return git_batch_processor.queue_operation(command, args, callback, project_root=project_root)

def invalidate_git_status_cache(project_root: str = ".") -> None:
    """使Git状态缓存失效"""
    enhanced_git_cache.invalidate_status_cache(project_root)

def get_git_cache_stats() -> Dict[str, Any]:
    """获取Git缓存统计"""
    return enhanced_git_cache.get_cache_stats()

if __name__ == "__main__":
    # 测试增强Git缓存
    print("🚀 测试增强Git缓存系统")

    # 测试缓存功能
    test_result = "test git output"
    cache_git_result('status', [], test_result)

    cached = get_cached_git_result('status', [])
    print(f"缓存测试结果: {cached == test_result}")

    # 测试批量操作
    def test_callback(result):
        print(f"批量操作回调: {result}")

    op_id = queue_git_operation('status', [], test_callback)
    print(f"操作已队列: {op_id}")

    # 等待批量处理
    time.sleep(3)

    # 获取统计信息
    stats = get_git_cache_stats()
    print(f"缓存统计: {stats}")

    print("✅ 增强Git缓存测试完成")