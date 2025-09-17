#!/usr/bin/env python3
"""
Perfect21 Async Error Handler
专门处理异步操作中的错误和事件循环冲突
"""

import asyncio
import logging
import traceback
from typing import Dict, Any, Optional, Callable, Awaitable, Union
from functools import wraps
from concurrent.futures import ThreadPoolExecutor
import threading
import weakref

logger = logging.getLogger(__name__)

class AsyncExecutionError(Exception):
    """异步执行错误"""
    pass

class EventLoopConflictError(Exception):
    """事件循环冲突错误"""
    pass

class AsyncErrorHandler:
    """异步错误处理器"""

    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="AsyncHandler")
        self._running_loops = weakref.WeakSet()
        self._lock = threading.Lock()

    def safe_run_async(self, coro: Awaitable[Any], timeout: Optional[float] = None) -> Any:
        """
        安全地运行异步协程，自动处理事件循环冲突

        Args:
            coro: 要运行的协程
            timeout: 超时时间（秒）

        Returns:
            协程的返回值

        Raises:
            AsyncExecutionError: 执行失败
            TimeoutError: 超时
        """
        try:
            # 检查当前是否在事件循环中
            try:
                current_loop = asyncio.get_running_loop()
                logger.debug("Detected running event loop, using thread executor")
                # 在新线程中运行协程
                future = self._executor.submit(self._run_in_new_thread, coro, timeout)
                return future.result(timeout=timeout)
            except RuntimeError:
                # 没有运行的事件循环，创建新的
                logger.debug("No running event loop, creating new one")
                if timeout:
                    return asyncio.wait_for(coro, timeout=timeout)
                else:
                    return asyncio.run(coro)

        except asyncio.TimeoutError:
            raise TimeoutError(f"Async operation timed out after {timeout} seconds")
        except Exception as e:
            logger.error(f"Async execution failed: {str(e)}")
            raise AsyncExecutionError(f"Failed to execute async operation: {str(e)}") from e

    def _run_in_new_thread(self, coro: Awaitable[Any], timeout: Optional[float] = None) -> Any:
        """在新线程中运行协程"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            with self._lock:
                self._running_loops.add(loop)

            try:
                if timeout:
                    return loop.run_until_complete(asyncio.wait_for(coro, timeout=timeout))
                else:
                    return loop.run_until_complete(coro)
            finally:
                loop.close()

        except Exception as e:
            logger.error(f"Thread execution failed: {str(e)}")
            raise

    def safe_run_sync_in_async(self, func: Callable, *args, **kwargs) -> Awaitable[Any]:
        """
        在异步环境中安全地运行同步函数

        Args:
            func: 要运行的同步函数
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            协程，返回函数结果
        """
        async def _async_wrapper():
            try:
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(self._executor, lambda: func(*args, **kwargs))
            except Exception as e:
                logger.error(f"Sync function execution failed: {str(e)}")
                raise AsyncExecutionError(f"Failed to run sync function {func.__name__}: {str(e)}") from e

        return _async_wrapper()

    def create_async_context_manager(self, sync_manager):
        """将同步上下文管理器转换为异步版本"""
        class AsyncContextManager:
            def __init__(self, sync_manager, error_handler):
                self.sync_manager = sync_manager
                self.error_handler = error_handler

            async def __aenter__(self):
                return await self.error_handler.safe_run_sync_in_async(
                    self.sync_manager.__enter__
                )

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                return await self.error_handler.safe_run_sync_in_async(
                    self.sync_manager.__exit__, exc_type, exc_val, exc_tb
                )

        return AsyncContextManager(sync_manager, self)

    def cleanup(self):
        """清理资源"""
        try:
            self._executor.shutdown(wait=True)
        except Exception as e:
            logger.warning(f"Error during cleanup: {str(e)}")

# 装饰器
def async_safe(func):
    """
    装饰器：使函数在异步和同步环境中都能安全运行

    自动检测返回值类型：
    - 如果是协程，使用错误处理器安全运行
    - 如果是普通值，直接返回
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        handler = get_async_error_handler()

        try:
            result = func(*args, **kwargs)

            # 如果返回协程，安全运行
            if asyncio.iscoroutine(result):
                return handler.safe_run_async(result)

            # 如果是普通值，直接返回
            return result

        except Exception as e:
            logger.error(f"Function {func.__name__} failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }

    return wrapper

def async_retry(max_attempts: int = 3, delay: float = 1.0, exponential_backoff: bool = True):
    """
    异步重试装饰器

    Args:
        max_attempts: 最大尝试次数
        delay: 基础延迟时间
        exponential_backoff: 是否使用指数退避
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_attempts):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        # 同步函数在executor中运行
                        handler = get_async_error_handler()
                        return await handler.safe_run_sync_in_async(func, *args, **kwargs)

                except Exception as e:
                    last_exception = e
                    logger.warning(f"Attempt {attempt + 1}/{max_attempts} failed: {str(e)}")

                    if attempt < max_attempts - 1:
                        await asyncio.sleep(current_delay)
                        if exponential_backoff:
                            current_delay *= 2

            # 所有尝试都失败了
            logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
            raise last_exception

        return wrapper
    return decorator

def mixed_execution_safe(sync_fallback: bool = True):
    """
    混合执行装饰器，支持同步和异步环境

    Args:
        sync_fallback: 是否允许同步回退
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            handler = get_async_error_handler()

            try:
                # 尝试检测是否在异步环境中
                try:
                    loop = asyncio.get_running_loop()
                    # 在异步环境中，安全运行
                    if asyncio.iscoroutinefunction(func):
                        return handler.safe_run_async(func(*args, **kwargs))
                    else:
                        # 同步函数在executor中运行
                        result = handler.safe_run_async(
                            handler.safe_run_sync_in_async(func, *args, **kwargs)
                        )
                        return result

                except RuntimeError:
                    # 不在异步环境中，直接运行
                    if asyncio.iscoroutinefunction(func):
                        return handler.safe_run_async(func(*args, **kwargs))
                    else:
                        return func(*args, **kwargs)

            except Exception as e:
                if sync_fallback and not asyncio.iscoroutinefunction(func):
                    logger.warning(f"Async execution failed, falling back to sync: {str(e)}")
                    try:
                        return func(*args, **kwargs)
                    except Exception as sync_error:
                        logger.error(f"Sync fallback also failed: {str(sync_error)}")
                        raise sync_error
                else:
                    raise e

        return wrapper
    return decorator

# 全局实例
_error_handler = None

def get_async_error_handler() -> AsyncErrorHandler:
    """获取全局异步错误处理器实例"""
    global _error_handler
    if _error_handler is None:
        _error_handler = AsyncErrorHandler()
    return _error_handler

# 便利函数
def run_async_safely(coro: Awaitable[Any], timeout: Optional[float] = None) -> Any:
    """便利函数：安全运行异步协程"""
    handler = get_async_error_handler()
    return handler.safe_run_async(coro, timeout)

def run_sync_in_async_safely(func: Callable, *args, **kwargs) -> Awaitable[Any]:
    """便利函数：在异步环境中安全运行同步函数"""
    handler = get_async_error_handler()
    return handler.safe_run_sync_in_async(func, *args, **kwargs)

# 上下文管理器
class AsyncSafeContext:
    """异步安全上下文管理器"""

    def __init__(self):
        self.handler = get_async_error_handler()

    def __enter__(self):
        return self.handler

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.handler.cleanup()

# 批量异步执行
async def batch_async_execute(tasks: list, max_concurrent: int = 5) -> Dict[str, Any]:
    """
    批量执行异步任务，带并发控制

    Args:
        tasks: 任务列表，每个任务可以是协程或同步函数
        max_concurrent: 最大并发数

    Returns:
        执行结果汇总
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    handler = get_async_error_handler()

    async def execute_task(task, index):
        async with semaphore:
            try:
                if asyncio.iscoroutine(task):
                    result = await task
                elif callable(task):
                    result = await handler.safe_run_sync_in_async(task)
                else:
                    result = task

                return {
                    'index': index,
                    'success': True,
                    'result': result
                }
            except Exception as e:
                logger.error(f"Task {index} failed: {str(e)}")
                return {
                    'index': index,
                    'success': False,
                    'error': str(e),
                    'traceback': traceback.format_exc()
                }

    # 执行所有任务
    results = await asyncio.gather(
        *[execute_task(task, i) for i, task in enumerate(tasks)],
        return_exceptions=True
    )

    # 汇总结果
    successful = [r for r in results if isinstance(r, dict) and r.get('success')]
    failed = [r for r in results if isinstance(r, dict) and not r.get('success')]
    exceptions = [r for r in results if isinstance(r, Exception)]

    return {
        'total_tasks': len(tasks),
        'successful_tasks': len(successful),
        'failed_tasks': len(failed) + len(exceptions),
        'success_rate': len(successful) / len(tasks) if tasks else 0,
        'results': results,
        'successful_results': successful,
        'failed_results': failed + [{'error': str(e), 'exception': True} for e in exceptions]
    }