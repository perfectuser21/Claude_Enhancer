#!/usr/bin/env python3
"""
Claude Enhancer - 高性能Hook执行引擎
基于压力测试结果的完全重构版本

核心特性：
- 异步并行执行
- 智能缓存机制
- 熔断和降级策略
- 自动错误恢复
- 实时性能监控
"""

import asyncio
import json
import time
import hashlib
import subprocess
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import threading
from collections import defaultdict, deque
import psutil
import signal
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("/tmp/claude_hook_engine.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


@dataclass
class HookResult:
    """Hook执行结果"""

    hook_name: str
    success: bool
    execution_time: float
    output: str
    error: Optional[str] = None
    cached: bool = False
    retries: int = 0


@dataclass
class HookConfig:
    """Hook配置"""

    name: str
    command: str
    timeout: float
    priority: int = 5
    max_retries: int = 2
    cache_ttl: int = 300  # 5分钟
    circuit_breaker_threshold: int = 5
    async_mode: bool = True
    fallback_command: Optional[str] = None


class CircuitBreaker:
    """熔断器实现"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.lock = threading.Lock()

    def call(self, func: Callable, *args, **kwargs):
        """执行函数调用，应用熔断逻辑"""
        with self.lock:
            if self.state == "OPEN":
                if time.time() - self.last_failure_time < self.recovery_timeout:
                    raise Exception("Circuit breaker is OPEN")
                else:
                    self.state = "HALF_OPEN"

            try:
                result = func(*args, **kwargs)
                if self.state == "HALF_OPEN":
                    self.state = "CLOSED"
                    self.failure_count = 0
                return result
            except Exception as e:
                self.failure_count += 1
                self.last_failure_time = time.time()

                if self.failure_count >= self.failure_threshold:
                    self.state = "OPEN"
                    logger.warning(
                        f"Circuit breaker opened after {self.failure_count} failures"
                    )

                raise e


class PerformanceCache:
    """智能缓存系统"""

    def __init__(self, max_size: int = 1000):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, float] = {}
        self.max_size = max_size
        self.lock = threading.RLock()

    def _generate_key(self, hook_name: str, context: Dict[str, Any]) -> str:
        """生成缓存键"""
        context_str = json.dumps(context, sort_keys=True)
        return hashlib.md5(f"{hook_name}:{context_str}".encode()).hexdigest()

    def get(
        self, hook_name: str, context: Dict[str, Any], ttl: int = 300
    ) -> Optional[HookResult]:
        """获取缓存结果"""
        key = self._generate_key(hook_name, context)

        with self.lock:
            if key in self.cache:
                cache_entry = self.cache[key]
                if time.time() - cache_entry["timestamp"] < ttl:
                    self.access_times[key] = time.time()
                    result = cache_entry["result"]
                    result.cached = True
                    logger.debug(f"Cache hit for hook {hook_name}")
                    return result
                else:
                    # 缓存过期
                    del self.cache[key]
                    del self.access_times[key]

        return None

    def set(self, hook_name: str, context: Dict[str, Any], result: HookResult):
        """设置缓存"""
        key = self._generate_key(hook_name, context)

        with self.lock:
            # 如果缓存满了，删除最久未访问的条目
            if len(self.cache) >= self.max_size:
                oldest_key = min(
                    self.access_times.keys(), key=lambda k: self.access_times[k]
                )
                del self.cache[oldest_key]
                del self.access_times[oldest_key]

            self.cache[key] = {"result": result, "timestamp": time.time()}
            self.access_times[key] = time.time()
            logger.debug(f"Cached result for hook {hook_name}")


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self, window_size: int = 100):
        self.execution_times = deque(maxlen=window_size)
        self.error_counts = defaultdict(int)
        self.success_counts = defaultdict(int)
        self.lock = threading.Lock()

    def record_execution(self, hook_name: str, execution_time: float, success: bool):
        """记录执行结果"""
        with self.lock:
            self.execution_times.append(execution_time)
            if success:
                self.success_counts[hook_name] += 1
            else:
                self.error_counts[hook_name] += 1

    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        with self.lock:
            if not self.execution_times:
                return {}

            return {
                "avg_execution_time": sum(self.execution_times)
                / len(self.execution_times),
                "min_execution_time": min(self.execution_times),
                "max_execution_time": max(self.execution_times),
                "total_executions": len(self.execution_times),
                "error_rates": {
                    hook: self.error_counts[hook]
                    / (self.error_counts[hook] + self.success_counts[hook])
                    for hook in set(self.error_counts.keys())
                    | set(self.success_counts.keys())
                },
                "system_load": psutil.cpu_percent(),
                "memory_usage": psutil.virtual_memory().percent,
            }


class HighPerformanceHookEngine:
    """高性能Hook执行引擎"""

    def __init__(
        self,
        config_path: str = "/home/xx/dev/Claude_Enhancer/.claude/hooks/engine_config.json",
    ):
        self.config_path = config_path
        self.hooks: Dict[str, HookConfig] = {}
        self.cache = PerformanceCache()
        self.monitor = PerformanceMonitor()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.thread_pool = ThreadPoolExecutor(max_workers=8)
        self.process_pool = ProcessPoolExecutor(max_workers=4)
        self.running = True

        # 加载配置
        self._load_config()

        # 设置信号处理
        signal.signal(signal.SIGTERM, self._shutdown_handler)
        signal.signal(signal.SIGINT, self._shutdown_handler)

    def _load_config(self):
        """加载Hook配置"""
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, "r") as f:
                    config_data = json.load(f)

                for hook_data in config_data.get("hooks", []):
                    hook_config = HookConfig(**hook_data)
                    self.hooks[hook_config.name] = hook_config
                    self.circuit_breakers[hook_config.name] = CircuitBreaker(
                        hook_config.circuit_breaker_threshold
                    )

                logger.info(f"Loaded {len(self.hooks)} hook configurations")
            else:
                logger.warning(f"Config file not found: {self.config_path}")
                self._create_default_config()
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self._create_default_config()

    def _create_default_config(self):
        """创建默认配置"""
        default_hooks = [
            {
                "name": "smart_agent_selector",
                "command": "bash /home/xx/dev/Claude_Enhancer/.claude/hooks/ultra_fast_agent_selector.sh",
                "timeout": 0.5,
                "priority": 8,
                "async_mode": True,
                "cache_ttl": 60,
            },
            {
                "name": "performance_monitor",
                "command": "bash /home/xx/dev/Claude_Enhancer/.claude/hooks/optimized_performance_monitor.sh",
                "timeout": 0.1,
                "priority": 10,
                "async_mode": True,
                "cache_ttl": 30,
            },
            {
                "name": "error_recovery",
                "command": "bash /home/xx/dev/Claude_Enhancer/.claude/hooks/smart_error_recovery.sh",
                "timeout": 0.2,
                "priority": 9,
                "async_mode": True,
                "cache_ttl": 120,
            },
        ]

        for hook_data in default_hooks:
            hook_config = HookConfig(**hook_data)
            self.hooks[hook_config.name] = hook_config
            self.circuit_breakers[hook_config.name] = CircuitBreaker()

    async def _execute_hook_async(
        self, hook_config: HookConfig, context: Dict[str, Any]
    ) -> HookResult:
        """异步执行Hook"""
        start_time = time.time()

        try:
            # 检查缓存
            cached_result = self.cache.get(
                hook_config.name, context, hook_config.cache_ttl
            )
            if cached_result:
                return cached_result

            # 执行Hook
            def run_command():
                return subprocess.run(
                    hook_config.command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=hook_config.timeout,
                    env={
                        **dict(
                            Path.cwd()
                            .parent.parent.joinpath(".env")
                            .open()
                            .read()
                            .strip()
                            .split("\n")
                        ),
                        "HOOK_CONTEXT": json.dumps(context),
                    }
                    if Path.cwd().parent.parent.joinpath(".env").exists()
                    else {"HOOK_CONTEXT": json.dumps(context)},
                )

            # 使用熔断器执行
            circuit_breaker = self.circuit_breakers[hook_config.name]

            if hook_config.async_mode:
                # 在线程池中执行
                loop = asyncio.get_event_loop()
                proc_result = await loop.run_in_executor(
                    self.thread_pool, lambda: circuit_breaker.call(run_command)
                )
            else:
                proc_result = circuit_breaker.call(run_command)

            execution_time = time.time() - start_time

            result = HookResult(
                hook_name=hook_config.name,
                success=proc_result.returncode == 0,
                execution_time=execution_time,
                output=proc_result.stdout,
                error=proc_result.stderr if proc_result.returncode != 0 else None,
            )

            # 缓存结果
            if result.success:
                self.cache.set(hook_config.name, context, result)

            # 记录性能
            self.monitor.record_execution(
                hook_config.name, execution_time, result.success
            )

            return result

        except subprocess.TimeoutExpired:
            execution_time = time.time() - start_time
            result = HookResult(
                hook_name=hook_config.name,
                success=False,
                execution_time=execution_time,
                output="",
                error=f"Hook timeout after {hook_config.timeout}s",
            )

            # 尝试fallback
            if hook_config.fallback_command:
                try:
                    fallback_proc = subprocess.run(
                        hook_config.fallback_command,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=hook_config.timeout / 2,
                    )
                    result.output = fallback_proc.stdout
                    result.success = fallback_proc.returncode == 0
                    logger.info(f"Fallback executed for {hook_config.name}")
                except Exception as e:
                    logger.error(f"Fallback failed for {hook_config.name}: {e}")

            self.monitor.record_execution(
                hook_config.name, execution_time, result.success
            )
            return result

        except Exception as e:
            execution_time = time.time() - start_time
            self.monitor.record_execution(hook_config.name, execution_time, False)
            return HookResult(
                hook_name=hook_config.name,
                success=False,
                execution_time=execution_time,
                output="",
                error=str(e),
            )

    async def execute_hooks(
        self, hook_names: List[str], context: Dict[str, Any]
    ) -> List[HookResult]:
        """批量执行Hook"""
        if not self.running:
            return []

        # 过滤有效的Hook
        valid_hooks = [name for name in hook_names if name in self.hooks]

        if not valid_hooks:
            logger.warning(f"No valid hooks found in: {hook_names}")
            return []

        # 按优先级排序
        hook_configs = sorted(
            [self.hooks[name] for name in valid_hooks],
            key=lambda h: h.priority,
            reverse=True,
        )

        # 创建异步任务
        tasks = [
            self._execute_hook_async(hook_config, context)
            for hook_config in hook_configs
        ]

        # 并行执行
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 处理异常结果
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    hook_name = hook_configs[i].name
                    processed_results.append(
                        HookResult(
                            hook_name=hook_name,
                            success=False,
                            execution_time=0,
                            output="",
                            error=str(result),
                        )
                    )
                    logger.error(f"Hook {hook_name} failed with exception: {result}")
                else:
                    processed_results.append(result)

            return processed_results

        except Exception as e:
            logger.error(f"Failed to execute hooks: {e}")
            return []

    def execute_hooks_sync(
        self, hook_names: List[str], context: Dict[str, Any]
    ) -> List[HookResult]:
        """同步执行Hook（兼容性接口）"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.execute_hooks(hook_names, context))
        except Exception as e:
            logger.error(f"Sync execution failed: {e}")
            return []
        finally:
            loop.close()

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        stats = self.monitor.get_stats()
        stats["cache_hit_rate"] = len([k for k in self.cache.cache.keys()]) / max(
            1, len(self.cache.access_times)
        )
        stats["circuit_breaker_states"] = {
            name: breaker.state for name, breaker in self.circuit_breakers.items()
        }
        return stats

    def _shutdown_handler(self, signum, frame):
        """优雅关闭"""
        logger.info("Shutting down Hook Engine...")
        self.running = False
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)
        sys.exit(0)


def main():
    """主函数 - 可以作为独立服务运行"""
    engine = HighPerformanceHookEngine()

    # 示例使用
    context = {"task_type": "code_writing", "file_count": 5, "complexity": "medium"}

    results = engine.execute_hooks_sync(
        ["smart_agent_selector", "performance_monitor", "error_recovery"], context
    )

    print("Execution Results:")
    for result in results:
        print(
            f"  {result.hook_name}: {'✅' if result.success else '❌'} ({result.execution_time:.3f}s)"
        )
        if result.output:
            print(f"    Output: {result.output[:100]}...")
        if result.error:
            print(f"    Error: {result.error}")

    print("\nPerformance Stats:")
    stats = engine.get_performance_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
