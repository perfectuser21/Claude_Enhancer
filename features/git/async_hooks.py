#!/usr/bin/env python3
"""
异步Git Hooks - 性能优化版本
使用异步操作、批量处理、连接池提升Git操作性能
"""

import asyncio
import logging
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import aiofiles
from concurrent.futures import ThreadPoolExecutor

from ..modules.async_git_cache import get_async_git_cache, AsyncGitCache, GitCommand

logger = logging.getLogger("AsyncGitHooks")


@dataclass
class HookExecutionResult:
    """Hook执行结果"""
    hook_name: str
    success: bool
    execution_time: float
    agents_called: List[str]
    result_data: Dict[str, Any]
    error_message: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class AsyncAgentOrchestrator:
    """异步Agent编排器"""

    def __init__(self, max_concurrent_agents: int = 6):
        self.max_concurrent_agents = max_concurrent_agents
        self.agent_pool = ThreadPoolExecutor(
            max_workers=max_concurrent_agents,
            thread_name_prefix="agent-executor"
        )
        self.execution_stats = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'total_execution_time': 0.0
        }

    async def execute_agents_parallel(self, agents_config: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """并行执行多个agents"""
        if not agents_config:
            return []

        logger.info(f"并行执行 {len(agents_config)} 个agents")
        start_time = time.time()

        try:
            # 创建并行任务
            tasks = []
            for config in agents_config:
                task = asyncio.create_task(self._execute_single_agent(config))
                tasks.append(task)

            # 等待所有任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理结果
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append({
                        'agent_name': agents_config[i].get('agent_name', 'unknown'),
                        'success': False,
                        'error': str(result),
                        'execution_time': 0.0
                    })
                    self.execution_stats['failed_calls'] += 1
                else:
                    processed_results.append(result)
                    self.execution_stats['successful_calls'] += 1

                self.execution_stats['total_calls'] += 1

            execution_time = time.time() - start_time
            self.execution_stats['total_execution_time'] += execution_time

            logger.info(f"并行执行完成，耗时 {execution_time:.2f}s")
            return processed_results

        except Exception as e:
            logger.error(f"并行执行agents失败: {e}")
            return []

    async def _execute_single_agent(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """执行单个agent"""
        agent_name = config.get('agent_name', 'unknown')
        task_description = config.get('task_description', '')
        context = config.get('context', {})

        start_time = time.time()

        try:
            logger.info(f"执行agent: {agent_name} - {task_description}")

            # 这里应该是实际的agent调用逻辑
            # 为了演示，我们模拟agent执行
            await asyncio.sleep(0.5)  # 模拟执行时间

            execution_time = time.time() - start_time

            return {
                'agent_name': agent_name,
                'task_description': task_description,
                'success': True,
                'execution_time': execution_time,
                'result': f"模拟执行结果 for {agent_name}",
                'context': context,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Agent {agent_name} 执行失败: {e}")

            return {
                'agent_name': agent_name,
                'task_description': task_description,
                'success': False,
                'execution_time': execution_time,
                'error': str(e),
                'context': context,
                'timestamp': datetime.now().isoformat()
            }

    def get_stats(self) -> Dict[str, Any]:
        """获取执行统计"""
        total_calls = self.execution_stats['total_calls']
        success_rate = (self.execution_stats['successful_calls'] / total_calls * 100) if total_calls > 0 else 0
        avg_execution_time = (self.execution_stats['total_execution_time'] / total_calls) if total_calls > 0 else 0

        return {
            'total_calls': total_calls,
            'successful_calls': self.execution_stats['successful_calls'],
            'failed_calls': self.execution_stats['failed_calls'],
            'success_rate': f"{success_rate:.1f}%",
            'average_execution_time': f"{avg_execution_time:.2f}s",
            'total_execution_time': f"{self.execution_stats['total_execution_time']:.2f}s"
        }

    def close(self):
        """关闭agent编排器"""
        self.agent_pool.shutdown(wait=False)


class AsyncGitHooks:
    """异步Git钩子管理器"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root or '.'
        self.git_cache: Optional[AsyncGitCache] = None
        self.agent_orchestrator = AsyncAgentOrchestrator()

        # SubAgent映射
        self.subagent_mapping = {
            'code_review': '@code-reviewer',
            'security_audit': '@security-auditor',
            'test_execution': '@test-engineer',
            'performance_check': '@performance-engineer',
            'deployment_check': '@devops-engineer',
            'quality_gate': '@orchestrator'
        }

        # 执行历史
        self.execution_history: List[HookExecutionResult] = []

        logger.info("异步Git Hooks初始化完成")

    async def _ensure_git_cache(self) -> AsyncGitCache:
        """确保Git缓存可用"""
        if self.git_cache is None:
            self.git_cache = await get_async_git_cache(self.project_root)
        return self.git_cache

    async def _get_parallel_agents_config(self, primary_agent: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """获取并行agents配置"""
        # 基础并行Agent配置
        base_parallel_agents = {
            '@orchestrator': ['@orchestrator', '@code-reviewer', '@security-auditor', '@test-engineer'],
            '@code-reviewer': ['@code-reviewer', '@security-auditor', '@test-engineer'],
            '@security-auditor': ['@security-auditor', '@test-engineer', '@devops-engineer'],
            '@test-engineer': ['@test-engineer', '@code-reviewer', '@devops-engineer'],
            '@devops-engineer': ['@devops-engineer', '@security-auditor', '@test-engineer']
        }

        # 获取默认并行Agent
        agents = base_parallel_agents.get(primary_agent, [primary_agent, '@code-reviewer', '@test-engineer'])

        # 根据上下文调整
        if context:
            branch = context.get('branch', '')
            if branch == 'main':
                agents = ['@orchestrator', '@code-reviewer', '@security-auditor', '@test-engineer', '@devops-engineer']
            elif 'feature' in branch:
                agents = ['@code-reviewer', '@test-engineer', '@security-auditor']
            elif 'hotfix' in branch:
                agents = ['@test-engineer', '@code-reviewer', '@devops-engineer']

        # 转换为配置格式
        agents_config = []
        for agent in list(set(agents)):  # 去重
            agents_config.append({
                'agent_name': agent.replace('@', ''),
                'task_description': f"Git Hook任务 - {context.get('hook_name', 'unknown')}",
                'context': context or {}
            })

        return agents_config

    async def get_git_status_async(self) -> Dict[str, Any]:
        """异步获取Git状态"""
        try:
            git_cache = await self._ensure_git_cache()
            status = await git_cache.batch_git_status()

            # 添加额外的统计信息
            return {
                **status,
                'status_check_time': datetime.now().isoformat(),
                'cache_stats': await git_cache.get_performance_stats()
            }

        except Exception as e:
            logger.error(f"异步获取Git状态失败: {e}")
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
                'error': str(e)
            }

    async def pre_commit_hook_async(self) -> HookExecutionResult:
        """异步提交前钩子"""
        start_time = time.time()
        hook_name = "pre-commit"

        try:
            logger.info("执行异步pre-commit钩子")

            # 并行获取Git状态和其他信息
            git_status_task = asyncio.create_task(self.get_git_status_async())

            # 同时检查是否有暂存文件
            git_cache = await self._ensure_git_cache()
            staged_files_task = asyncio.create_task(
                git_cache.get_cached_git_result(['git', 'diff', '--cached', '--name-only'], priority=1)
            )

            git_status, staged_files_result = await asyncio.gather(git_status_task, staged_files_task)

            # 检查是否有暂存文件
            has_staged = len(git_status.get('staged_files', [])) > 0
            if not has_staged:
                execution_time = time.time() - start_time
                result = HookExecutionResult(
                    hook_name=hook_name,
                    success=False,
                    execution_time=execution_time,
                    agents_called=[],
                    result_data={
                        'message': '没有暂存的文件，无法提交',
                        'should_abort': True
                    }
                )
                self.execution_history.append(result)
                return result

            # 根据分支类型决定检查级别
            branch = git_status['current_branch']
            context = {
                'hook_name': hook_name,
                'branch': branch,
                'staged_files': git_status.get('staged_files', []),
                'git_status': git_status
            }

            # 选择agents
            if branch in ['main', 'master', 'release']:
                primary_agent = '@orchestrator'
                context['check_level'] = 'strict'
            else:
                primary_agent = '@code-reviewer'
                context['check_level'] = 'basic'

            # 获取agents配置并并行执行
            agents_config = await self._get_parallel_agents_config(primary_agent, context)
            agent_results = await self.agent_orchestrator.execute_agents_parallel(agents_config)

            execution_time = time.time() - start_time
            agents_called = [config['agent_name'] for config in agents_config]

            result = HookExecutionResult(
                hook_name=hook_name,
                success=True,
                execution_time=execution_time,
                agents_called=agents_called,
                result_data={
                    'branch': branch,
                    'check_level': context['check_level'],
                    'staged_files_count': len(git_status.get('staged_files', [])),
                    'agent_results': agent_results,
                    'performance_stats': self.agent_orchestrator.get_stats()
                }
            )

            self.execution_history.append(result)
            logger.info(f"异步pre-commit钩子执行完成，耗时 {execution_time:.2f}s")
            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"异步pre-commit钩子执行失败: {e}")

            result = HookExecutionResult(
                hook_name=hook_name,
                success=False,
                execution_time=execution_time,
                agents_called=[],
                result_data={},
                error_message=str(e)
            )
            self.execution_history.append(result)
            return result

    async def pre_push_hook_async(self, remote: str = 'origin', branch: str = None) -> HookExecutionResult:
        """异步推送前钩子"""
        start_time = time.time()
        hook_name = "pre-push"

        try:
            logger.info(f"执行异步pre-push钩子: {remote}")

            git_status = await self.get_git_status_async()
            current_branch = branch or git_status['current_branch']

            # 保护主分支
            if current_branch in ['main', 'master']:
                execution_time = time.time() - start_time
                result = HookExecutionResult(
                    hook_name=hook_name,
                    success=False,
                    execution_time=execution_time,
                    agents_called=[],
                    result_data={
                        'message': '禁止直接推送到主分支，请使用Pull Request流程',
                        'should_abort': True,
                        'branch_protection': True
                    }
                )
                self.execution_history.append(result)
                return result

            # 准备上下文
            context = {
                'hook_name': hook_name,
                'branch': current_branch,
                'remote': remote,
                'git_status': git_status
            }

            # 根据分支类型选择检查策略
            if current_branch.startswith('release/'):
                primary_agent = '@orchestrator'
                context['check_type'] = 'release'
            elif current_branch.startswith('hotfix/'):
                primary_agent = '@test-engineer'
                context['check_type'] = 'hotfix'
                context['priority'] = 'high'
            else:
                primary_agent = '@test-engineer'
                context['check_type'] = 'feature'

            # 获取agents配置并并行执行
            agents_config = await self._get_parallel_agents_config(primary_agent, context)
            agent_results = await self.agent_orchestrator.execute_agents_parallel(agents_config)

            execution_time = time.time() - start_time
            agents_called = [config['agent_name'] for config in agents_config]

            result = HookExecutionResult(
                hook_name=hook_name,
                success=True,
                execution_time=execution_time,
                agents_called=agents_called,
                result_data={
                    'branch': current_branch,
                    'remote': remote,
                    'check_type': context['check_type'],
                    'agent_results': agent_results,
                    'performance_stats': self.agent_orchestrator.get_stats()
                }
            )

            self.execution_history.append(result)
            logger.info(f"异步pre-push钩子执行完成，耗时 {execution_time:.2f}s")
            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"异步pre-push钩子执行失败: {e}")

            result = HookExecutionResult(
                hook_name=hook_name,
                success=False,
                execution_time=execution_time,
                agents_called=[],
                result_data={},
                error_message=str(e)
            )
            self.execution_history.append(result)
            return result

    async def post_checkout_hook_async(self, old_ref: str, new_ref: str, branch_flag: str) -> HookExecutionResult:
        """异步分支切换后钩子"""
        start_time = time.time()
        hook_name = "post-checkout"

        try:
            logger.info("执行异步post-checkout钩子")

            # 只处理分支切换
            if branch_flag != "1":
                execution_time = time.time() - start_time
                result = HookExecutionResult(
                    hook_name=hook_name,
                    success=True,
                    execution_time=execution_time,
                    agents_called=[],
                    result_data={'message': '非分支切换，跳过处理'}
                )
                self.execution_history.append(result)
                return result

            git_status = await self.get_git_status_async()
            current_branch = git_status['current_branch']

            context = {
                'hook_name': hook_name,
                'branch': current_branch,
                'old_ref': old_ref,
                'new_ref': new_ref,
                'action': 'branch_switch',
                'checks': ['dependencies', 'environment', 'configuration']
            }

            # 执行DevOps检查
            agents_config = await self._get_parallel_agents_config('@devops-engineer', context)
            agent_results = await self.agent_orchestrator.execute_agents_parallel(agents_config)

            execution_time = time.time() - start_time
            agents_called = [config['agent_name'] for config in agents_config]

            result = HookExecutionResult(
                hook_name=hook_name,
                success=True,
                execution_time=execution_time,
                agents_called=agents_called,
                result_data={
                    'branch': current_branch,
                    'old_ref': old_ref,
                    'new_ref': new_ref,
                    'agent_results': agent_results
                }
            )

            self.execution_history.append(result)
            logger.info(f"异步post-checkout钩子执行完成，耗时 {execution_time:.2f}s")
            return result

        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"异步post-checkout钩子执行失败: {e}")

            result = HookExecutionResult(
                hook_name=hook_name,
                success=False,
                execution_time=execution_time,
                agents_called=[],
                result_data={},
                error_message=str(e)
            )
            self.execution_history.append(result)
            return result

    async def batch_hook_operations(self, hooks: List[Dict[str, Any]]) -> List[HookExecutionResult]:
        """批量执行多个钩子操作"""
        if not hooks:
            return []

        logger.info(f"批量执行 {len(hooks)} 个钩子操作")

        # 并行执行所有钩子
        tasks = []
        for hook_config in hooks:
            hook_name = hook_config.get('hook_name')
            if hook_name == 'pre-commit':
                task = asyncio.create_task(self.pre_commit_hook_async())
            elif hook_name == 'pre-push':
                task = asyncio.create_task(self.pre_push_hook_async(
                    hook_config.get('remote', 'origin'),
                    hook_config.get('branch')
                ))
            elif hook_name == 'post-checkout':
                task = asyncio.create_task(self.post_checkout_hook_async(
                    hook_config.get('old_ref', ''),
                    hook_config.get('new_ref', ''),
                    hook_config.get('branch_flag', '1')
                ))
            else:
                continue
            tasks.append(task)

        # 等待所有钩子执行完成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        processed_results = []
        for result in results:
            if isinstance(result, Exception):
                processed_results.append(HookExecutionResult(
                    hook_name="unknown",
                    success=False,
                    execution_time=0.0,
                    agents_called=[],
                    result_data={},
                    error_message=str(result)
                ))
            else:
                processed_results.append(result)

        return processed_results

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标"""
        if not self.execution_history:
            return {
                'total_executions': 0,
                'average_execution_time': 0.0,
                'success_rate': 0.0,
                'agent_stats': self.agent_orchestrator.get_stats()
            }

        total_executions = len(self.execution_history)
        successful_executions = sum(1 for h in self.execution_history if h.success)
        total_execution_time = sum(h.execution_time for h in self.execution_history)

        # 按钩子类型统计
        hook_stats = {}
        for hook in self.execution_history:
            if hook.hook_name not in hook_stats:
                hook_stats[hook.hook_name] = {
                    'count': 0,
                    'success_count': 0,
                    'total_time': 0.0,
                    'agents_used': set()
                }

            stats = hook_stats[hook.hook_name]
            stats['count'] += 1
            if hook.success:
                stats['success_count'] += 1
            stats['total_time'] += hook.execution_time
            stats['agents_used'].update(hook.agents_called)

        # 转换agents_used为列表
        for hook_name, stats in hook_stats.items():
            stats['agents_used'] = list(stats['agents_used'])
            stats['average_time'] = stats['total_time'] / stats['count'] if stats['count'] > 0 else 0.0
            stats['success_rate'] = (stats['success_count'] / stats['count'] * 100) if stats['count'] > 0 else 0.0

        git_cache_stats = {}
        if self.git_cache:
            git_cache_stats = await self.git_cache.get_performance_stats()

        return {
            'total_executions': total_executions,
            'successful_executions': successful_executions,
            'failed_executions': total_executions - successful_executions,
            'success_rate': (successful_executions / total_executions * 100) if total_executions > 0 else 0.0,
            'average_execution_time': total_execution_time / total_executions if total_executions > 0 else 0.0,
            'total_execution_time': total_execution_time,
            'hook_stats': hook_stats,
            'agent_stats': self.agent_orchestrator.get_stats(),
            'git_cache_stats': git_cache_stats,
            'last_execution': self.execution_history[-1].__dict__ if self.execution_history else None
        }

    async def save_performance_report(self, filename: Optional[str] = None) -> str:
        """保存性能报告"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"async_git_hooks_performance_{timestamp}.json"

        metrics = await self.get_performance_metrics()

        report_data = {
            'report_type': 'async_git_hooks_performance',
            'timestamp': datetime.now().isoformat(),
            'performance_metrics': metrics,
            'execution_history': [h.__dict__ for h in self.execution_history[-20:]],  # 最近20次执行
            'configuration': {
                'project_root': self.project_root,
                'subagent_mapping': self.subagent_mapping,
                'max_concurrent_agents': self.agent_orchestrator.max_concurrent_agents
            }
        }

        async with aiofiles.open(filename, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(report_data, indent=2, ensure_ascii=False, default=str))

        logger.info(f"异步Git Hooks性能报告已保存到: {filename}")
        return filename

    async def optimize_configuration(self) -> Dict[str, Any]:
        """优化配置建议"""
        metrics = await self.get_performance_metrics()

        optimizations = []
        recommended_config = {}

        # 分析执行时间
        avg_time = metrics.get('average_execution_time', 0.0)
        if avg_time > 10.0:
            optimizations.append("平均执行时间过长，建议增加并发agent数量")
            recommended_config['max_concurrent_agents'] = min(10, self.agent_orchestrator.max_concurrent_agents + 2)

        # 分析成功率
        success_rate = metrics.get('success_rate', 0.0)
        if success_rate < 90.0:
            optimizations.append("成功率较低，建议检查agent执行逻辑和错误处理")

        # 分析Git缓存效果
        git_cache_stats = metrics.get('git_cache_stats', {})
        hit_rate = git_cache_stats.get('hit_rate', '0%')
        if float(hit_rate.replace('%', '')) < 50.0:
            optimizations.append("Git缓存命中率较低，建议调整缓存策略")

        # 分析hook类型分布
        hook_stats = metrics.get('hook_stats', {})
        for hook_name, stats in hook_stats.items():
            if stats['average_time'] > 15.0:
                optimizations.append(f"{hook_name} hook执行时间过长，建议优化相关agents")

        return {
            'optimizations': optimizations,
            'current_metrics': metrics,
            'recommended_config': recommended_config,
            'analysis_timestamp': datetime.now().isoformat()
        }

    async def close(self):
        """关闭异步Git Hooks"""
        logger.info("关闭异步Git Hooks...")

        # 关闭agent编排器
        self.agent_orchestrator.close()

        # 关闭Git缓存
        if self.git_cache:
            self.git_cache.close()

        logger.info("异步Git Hooks已关闭")

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self._ensure_git_cache()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()


# 向后兼容的同步包装器
class SyncGitHooksWrapper:
    """同步Git Hooks包装器"""

    def __init__(self, project_root: str = None):
        self.project_root = project_root
        self._async_hooks = None
        self._loop = None

    def _get_or_create_loop(self):
        """获取或创建事件循环"""
        try:
            self._loop = asyncio.get_event_loop()
        except RuntimeError:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
        return self._loop

    async def _get_async_hooks(self):
        """获取异步hooks实例"""
        if self._async_hooks is None:
            self._async_hooks = AsyncGitHooks(self.project_root)
        return self._async_hooks

    def pre_commit_hook(self) -> Dict[str, Any]:
        """同步版本的pre-commit hook"""
        loop = self._get_or_create_loop()

        async def _async_wrapper():
            hooks = await self._get_async_hooks()
            result = await hooks.pre_commit_hook_async()
            return result.__dict__

        return loop.run_until_complete(_async_wrapper())

    def pre_push_hook(self, remote: str = 'origin', branch: str = None) -> Dict[str, Any]:
        """同步版本的pre-push hook"""
        loop = self._get_or_create_loop()

        async def _async_wrapper():
            hooks = await self._get_async_hooks()
            result = await hooks.pre_push_hook_async(remote, branch)
            return result.__dict__

        return loop.run_until_complete(_async_wrapper())

    def get_git_status(self) -> Dict[str, Any]:
        """同步版本的git status"""
        loop = self._get_or_create_loop()

        async def _async_wrapper():
            hooks = await self._get_async_hooks()
            return await hooks.get_git_status_async()

        return loop.run_until_complete(_async_wrapper())


# 全局异步Git Hooks实例
_async_git_hooks: Optional[AsyncGitHooks] = None


async def get_async_git_hooks(project_root: str = None) -> AsyncGitHooks:
    """获取异步Git Hooks实例"""
    global _async_git_hooks
    if _async_git_hooks is None:
        _async_git_hooks = AsyncGitHooks(project_root)
    return _async_git_hooks


def get_git_hooks(project_root: str = None) -> SyncGitHooksWrapper:
    """获取兼容的Git Hooks实例"""
    return SyncGitHooksWrapper(project_root)