#!/usr/bin/env python3
"""
Perfect21 Async CLI Wrapper
处理CLI中的异步操作，避免事件循环冲突
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable, Awaitable
from concurrent.futures import ThreadPoolExecutor
import threading

logger = logging.getLogger(__name__)

class AsyncCliWrapper:
    """异步CLI包装器，用于处理混合的async/sync操作"""

    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._loop = None
        self._thread = None

    def run_async_safe(self, coro: Awaitable[Any]) -> Any:
        """
        安全地运行异步协程，处理事件循环冲突
        """
        try:
            # 检查是否已有事件循环
            current_loop = asyncio.get_running_loop()
            # 如果已有事件循环，在新线程中运行
            future = self._executor.submit(self._run_in_new_loop, coro)
            return future.result()
        except RuntimeError:
            # 没有运行的事件循环，直接创建新的
            return asyncio.run(coro)

    def _run_in_new_loop(self, coro: Awaitable[Any]) -> Any:
        """在新事件循环中运行协程"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            loop.close()

    async def execute_parallel_workflow(self, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行并行工作流
        """
        try:
            from features.workflow_orchestrator.orchestrator import WorkflowOrchestrator

            orchestrator = WorkflowOrchestrator()

            # 加载工作流
            load_result = orchestrator.load_workflow(workflow_config)
            if not load_result['success']:
                return load_result

            # 执行所有阶段
            results = []
            for stage_name in workflow_config.get('stages', []):
                stage_result = await orchestrator.execute_stage_async(stage_name['name'])
                results.append(stage_result)

                if not stage_result['success']:
                    break

            return {
                'success': all(r['success'] for r in results),
                'stage_results': results,
                'workflow_id': load_result['workflow_id']
            }

        except Exception as e:
            logger.error(f"Parallel workflow execution failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    async def execute_async_task(self, task_description: str,
                                force_parallel: bool = False) -> Dict[str, Any]:
        """
        执行异步任务
        """
        try:
            from features.smart_decomposer import get_smart_decomposer
            from features.parallel_executor import get_parallel_executor

            # 任务分析
            decomposer = get_smart_decomposer()
            analysis = decomposer.decompose_task(task_description)

            if not analysis:
                return {'success': False, 'error': 'Task analysis failed'}

            # 执行并行任务
            executor = get_parallel_executor()

            if hasattr(executor, 'execute_parallel_task_async'):
                # 使用异步版本
                result = await executor.execute_parallel_task_async(task_description, analysis)
            else:
                # 回退到同步版本，在executor中运行
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    self._executor,
                    executor.execute_parallel_task,
                    task_description,
                    analysis
                )

            return result

        except Exception as e:
            logger.error(f"Async task execution failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def sync_execute_async_task(self, task_description: str,
                               force_parallel: bool = False) -> Dict[str, Any]:
        """
        同步接口来执行异步任务
        """
        coro = self.execute_async_task(task_description, force_parallel)
        return self.run_async_safe(coro)

    async def execute_git_operation_async(self, operation: str, *args) -> Dict[str, Any]:
        """
        异步执行Git操作
        """
        try:
            from main.perfect21 import Perfect21

            # 在executor中运行同步的Perfect21操作
            loop = asyncio.get_event_loop()

            def run_git_operation():
                p21 = Perfect21()
                if operation == 'status':
                    return p21.status()
                elif operation == 'workflow':
                    return p21.workflow_command(*args)
                elif operation == 'git_hook_handler':
                    return p21.git_hook_handler(*args)
                else:
                    return {'success': False, 'error': f'Unknown operation: {operation}'}

            result = await loop.run_in_executor(self._executor, run_git_operation)
            return result

        except Exception as e:
            logger.error(f"Async git operation failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def sync_execute_git_operation(self, operation: str, *args) -> Dict[str, Any]:
        """
        同步接口来执行Git操作
        """
        coro = self.execute_git_operation_async(operation, *args)
        return self.run_async_safe(coro)

    async def batch_execute_tasks(self, tasks: list) -> Dict[str, Any]:
        """
        批量执行多个任务
        """
        try:
            # 创建任务协程列表
            task_coros = []
            for task in tasks:
                if task['type'] == 'parallel':
                    coro = self.execute_async_task(task['description'], task.get('force_parallel', False))
                elif task['type'] == 'git':
                    coro = self.execute_git_operation_async(task['operation'], *task.get('args', []))
                else:
                    continue
                task_coros.append(coro)

            # 并行执行所有任务
            results = await asyncio.gather(*task_coros, return_exceptions=True)

            # 处理结果
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append({
                        'task_index': i,
                        'success': False,
                        'error': str(result)
                    })
                else:
                    processed_results.append({
                        'task_index': i,
                        'success': result.get('success', False),
                        'result': result
                    })

            return {
                'success': all(r['success'] for r in processed_results),
                'results': processed_results,
                'total_tasks': len(tasks),
                'successful_tasks': sum(1 for r in processed_results if r['success'])
            }

        except Exception as e:
            logger.error(f"Batch task execution failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def cleanup(self):
        """清理资源"""
        if self._executor:
            self._executor.shutdown(wait=True)

# 全局实例
_cli_wrapper = None

def get_async_cli_wrapper() -> AsyncCliWrapper:
    """获取全局异步CLI包装器实例"""
    global _cli_wrapper
    if _cli_wrapper is None:
        _cli_wrapper = AsyncCliWrapper()
    return _cli_wrapper

# 便利函数
def run_async_task_safely(task_description: str, force_parallel: bool = False) -> Dict[str, Any]:
    """便利函数：安全地运行异步任务"""
    wrapper = get_async_cli_wrapper()
    return wrapper.sync_execute_async_task(task_description, force_parallel)

def run_async_git_operation_safely(operation: str, *args) -> Dict[str, Any]:
    """便利函数：安全地运行异步Git操作"""
    wrapper = get_async_cli_wrapper()
    return wrapper.sync_execute_git_operation(operation, *args)

def run_batch_tasks_safely(tasks: list) -> Dict[str, Any]:
    """便利函数：安全地运行批量任务"""
    wrapper = get_async_cli_wrapper()
    coro = wrapper.batch_execute_tasks(tasks)
    return wrapper.run_async_safe(coro)

# 上下文管理器
class AsyncCliContext:
    """异步CLI上下文管理器"""

    def __init__(self):
        self.wrapper = None

    def __enter__(self):
        self.wrapper = get_async_cli_wrapper()
        return self.wrapper

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.wrapper:
            self.wrapper.cleanup()

# 装饰器
def async_safe(func):
    """装饰器：使函数在异步环境中安全运行"""
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            # 如果返回协程，使用包装器运行
            if asyncio.iscoroutine(result):
                cli_wrapper = get_async_cli_wrapper()
                return cli_wrapper.run_async_safe(result)
            return result
        except Exception as e:
            logger.error(f"Async safe execution failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    return wrapper