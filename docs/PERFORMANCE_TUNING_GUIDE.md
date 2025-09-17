# Perfect21 性能调优指南

> ⚡ **专业性能调优策略 - 让 Perfect21 运行如飞**
>
> 系统性能优化、监控和故障排除的完整解决方案

## 📖 目录

- [性能基准](#性能基准)
- [系统资源优化](#系统资源优化)
- [API性能优化](#API性能优化)
- [数据库性能调优](#数据库性能调优)
- [缓存策略优化](#缓存策略优化)
- [并发性能优化](#并发性能优化)
- [网络性能优化](#网络性能优化)
- [监控与告警](#监控与告警)
- [性能测试](#性能测试)

## 📊 性能基准

### 目标性能指标

| 指标类型 | 目标值 | 优秀值 | 说明 |
|---------|--------|--------|------|
| **API响应时间** | P95 < 200ms | P95 < 100ms | 95%请求响应时间 |
| **并发请求** | 1000 req/s | 2000+ req/s | 稳定处理能力 |
| **内存使用** | < 512MB | < 256MB | 进程内存占用 |
| **CPU使用率** | < 70% | < 50% | 平均CPU使用率 |
| **数据库连接** | < 100ms | < 50ms | 连接建立时间 |
| **缓存命中率** | > 85% | > 95% | Redis缓存命中率 |

### 性能基准测试

```bash
#!/bin/bash
# Perfect21 性能基准测试脚本

echo "⚡ Perfect21 性能基准测试"
echo "========================"

# 1. API响应时间测试
echo "📡 API响应时间测试:"
ab -n 1000 -c 10 http://localhost:8000/health | grep "Time per request"

# 2. 并发处理测试
echo -e "\n🚀 并发处理测试:"
ab -n 5000 -c 100 http://localhost:8000/api/auth/health | grep "Requests per second"

# 3. 内存使用测试
echo -e "\n💾 内存使用测试:"
echo "开始前内存:" $(ps -o rss= -p $(pgrep -f "perfect21") | awk '{sum+=$1} END {print sum/1024 "MB"}')

# 执行压力测试
ab -n 10000 -c 50 http://localhost:8000/health > /dev/null 2>&1

echo "测试后内存:" $(ps -o rss= -p $(pgrep -f "perfect21") | awk '{sum+=$1} END {print sum/1024 "MB"}')

# 4. 数据库连接测试
echo -e "\n🗄️ 数据库连接测试:"
python3 -c "
import time
from features.auth_system import AuthManager

times = []
for i in range(10):
    start = time.time()
    auth = AuthManager()
    auth.health_check()
    end = time.time()
    times.append((end-start)*1000)

print(f'平均连接时间: {sum(times)/len(times):.2f}ms')
print(f'最大连接时间: {max(times):.2f}ms')
print(f'最小连接时间: {min(times):.2f}ms')
"

# 5. 缓存性能测试
echo -e "\n🔄 缓存性能测试:"
redis-cli eval "
local hits = redis.call('info', 'stats'):match('keyspace_hits:(%d+)')
local misses = redis.call('info', 'stats'):match('keyspace_misses:(%d+)')
local hit_rate = hits / (hits + misses) * 100
return string.format('缓存命中率: %.2f%%', hit_rate)
" 0

echo -e "\n✅ 基准测试完成"
```

## 🖥️ 系统资源优化

### 1. 内存优化策略

```python
#!/usr/bin/env python3
"""
Perfect21 内存优化模块
"""

import gc
import sys
import psutil
import threading
from functools import wraps
from typing import Dict, Any, Optional
import weakref

class MemoryOptimizer:
    """内存优化器"""

    def __init__(self):
        self.object_pools: Dict[str, list] = {}
        self.memory_threshold = 500 * 1024 * 1024  # 500MB
        self.cleanup_interval = 300  # 5分钟
        self.start_cleanup_timer()

    def start_cleanup_timer(self):
        """启动定期内存清理"""
        def cleanup():
            self.cleanup_memory()
            # 重新启动计时器
            timer = threading.Timer(self.cleanup_interval, cleanup)
            timer.daemon = True
            timer.start()

        timer = threading.Timer(self.cleanup_interval, cleanup)
        timer.daemon = True
        timer.start()

    def cleanup_memory(self):
        """执行内存清理"""
        try:
            # 强制垃圾回收
            collected = gc.collect()

            # 清理对象池
            for pool_name in list(self.object_pools.keys()):
                if len(self.object_pools[pool_name]) > 100:
                    self.object_pools[pool_name] = self.object_pools[pool_name][:50]

            # 检查内存使用
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024

            print(f"🧹 内存清理完成: 回收{collected}个对象, 当前内存: {memory_mb:.1f}MB")

        except Exception as e:
            print(f"❌ 内存清理失败: {e}")

    def get_object_pool(self, pool_name: str, create_func):
        """获取对象池"""
        if pool_name not in self.object_pools:
            self.object_pools[pool_name] = []

        pool = self.object_pools[pool_name]
        if pool:
            return pool.pop()
        else:
            return create_func()

    def return_to_pool(self, pool_name: str, obj):
        """归还对象到池"""
        if pool_name not in self.object_pools:
            self.object_pools[pool_name] = []

        pool = self.object_pools[pool_name]
        if len(pool) < 50:  # 限制池大小
            # 清理对象状态
            if hasattr(obj, 'reset'):
                obj.reset()
            pool.append(obj)

# 全局内存优化器
memory_optimizer = MemoryOptimizer()

def memory_efficient(pool_name: str):
    """内存效率装饰器"""
    def decorator(cls):
        original_new = cls.__new__

        def new_with_pool(cls_ref, *args, **kwargs):
            obj = memory_optimizer.get_object_pool(
                pool_name,
                lambda: original_new(cls_ref)
            )
            return obj

        cls.__new__ = new_with_pool
        return cls
    return decorator

class SlottedClass:
    """使用__slots__的基类减少内存使用"""
    __slots__ = ()

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.__slots__:
                setattr(self, key, value)

# 内存监控装饰器
def monitor_memory(func):
    """监控函数内存使用"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        process = psutil.Process()
        start_memory = process.memory_info().rss

        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_memory = process.memory_info().rss
            memory_diff = (end_memory - start_memory) / 1024 / 1024

            if memory_diff > 10:  # 超过10MB增长
                print(f"⚠️ {func.__name__} 内存增长: {memory_diff:.1f}MB")

    return wrapper

# 智能缓存类
class SmartCache:
    """智能缓存，支持LRU和大小限制"""

    def __init__(self, max_size=1000, max_memory_mb=100):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache = {}
        self.access_order = []
        self.current_memory = 0

    def get(self, key):
        if key in self.cache:
            # 更新访问顺序
            self.access_order.remove(key)
            self.access_order.append(key)
            return self.cache[key]
        return None

    def set(self, key, value):
        # 估算值的大小
        value_size = sys.getsizeof(value)

        # 检查是否需要清理
        while (len(self.cache) >= self.max_size or
               self.current_memory + value_size > self.max_memory_bytes):
            if not self.access_order:
                break

            # 移除最久未使用的项
            old_key = self.access_order.pop(0)
            if old_key in self.cache:
                old_value = self.cache.pop(old_key)
                self.current_memory -= sys.getsizeof(old_value)

        # 添加新值
        self.cache[key] = value
        self.access_order.append(key)
        self.current_memory += value_size

# 使用示例
@memory_efficient("user_objects")
class User(SlottedClass):
    __slots__ = ['id', 'username', 'email', 'created_at']

    def reset(self):
        """重置对象状态"""
        self.id = None
        self.username = None
        self.email = None
        self.created_at = None

# 全局智能缓存实例
smart_cache = SmartCache(max_size=5000, max_memory_mb=50)
```

### 2. CPU优化配置

```python
# CPU优化配置
import multiprocessing
import concurrent.futures
import asyncio
from functools import lru_cache

# 系统配置
CPU_COUNT = multiprocessing.cpu_count()
OPTIMAL_WORKERS = min(CPU_COUNT * 2, 8)  # 最多8个worker
THREAD_POOL_SIZE = CPU_COUNT * 4

# FastAPI优化配置
API_CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
    "workers": OPTIMAL_WORKERS,
    "worker_class": "uvicorn.workers.UvicornWorker",
    "worker_connections": 1000,
    "max_requests": 10000,
    "max_requests_jitter": 1000,
    "keepalive": 5,
    "preload_app": True,
}

# 异步执行器配置
class OptimizedExecutor:
    def __init__(self):
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=THREAD_POOL_SIZE
        )
        self.process_pool = concurrent.futures.ProcessPoolExecutor(
            max_workers=CPU_COUNT
        )

    async def run_cpu_bound_task(self, func, *args, **kwargs):
        """执行CPU密集型任务"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.process_pool, func, *args, **kwargs)

    async def run_io_bound_task(self, func, *args, **kwargs):
        """执行IO密集型任务"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.thread_pool, func, *args, **kwargs)

# 计算密集型任务优化
@lru_cache(maxsize=1000)
def expensive_calculation(param):
    """缓存计算结果"""
    # 复杂计算逻辑
    return result
```

## 🚀 API性能优化

### 1. 响应时间优化

```python
#!/usr/bin/env python3
"""
API性能优化模块
"""

import time
import asyncio
from fastapi import FastAPI, Request, Response
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.cors import CORSMiddleware
import uvloop
import httpx
from typing import Dict, Any
import json

# 使用高性能事件循环
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

class PerformanceMiddleware:
    """性能优化中间件"""

    def __init__(self, app: FastAPI):
        self.app = app
        self.response_cache = {}
        self.cache_ttl = 300  # 5分钟缓存

    async def __call__(self, request: Request, call_next):
        start_time = time.time()

        # 检查缓存
        if request.method == "GET":
            cache_key = f"{request.url.path}?{request.url.query}"
            cached_response = self.get_cached_response(cache_key)
            if cached_response:
                return cached_response

        response = await call_next(request)

        # 计算响应时间
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)

        # 缓存GET请求的响应
        if request.method == "GET" and response.status_code == 200:
            cache_key = f"{request.url.path}?{request.url.query}"
            self.cache_response(cache_key, response)

        # 性能告警
        if process_time > 1.0:  # 超过1秒
            print(f"⚠️ 慢请求: {request.url.path} 耗时 {process_time:.2f}s")

        return response

    def get_cached_response(self, cache_key: str) -> Response:
        """获取缓存的响应"""
        if cache_key in self.response_cache:
            cached_data, timestamp = self.response_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return Response(
                    content=cached_data["content"],
                    status_code=cached_data["status_code"],
                    headers={"X-Cache": "HIT", **cached_data["headers"]},
                    media_type=cached_data["media_type"]
                )
        return None

    def cache_response(self, cache_key: str, response: Response):
        """缓存响应"""
        # 简化的缓存实现
        self.response_cache[cache_key] = (
            {
                "content": response.body,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "media_type": response.media_type
            },
            time.time()
        )

# 批量处理优化
class BatchProcessor:
    """批量处理器"""

    def __init__(self, batch_size=100, max_wait_time=0.1):
        self.batch_size = batch_size
        self.max_wait_time = max_wait_time
        self.pending_requests = []
        self.processing_lock = asyncio.Lock()

    async def add_request(self, request_data):
        """添加请求到批次"""
        async with self.processing_lock:
            self.pending_requests.append(request_data)

            # 检查是否达到批次大小或超时
            if (len(self.pending_requests) >= self.batch_size or
                self.should_process_batch()):
                return await self.process_batch()

            # 等待更多请求或超时
            await asyncio.sleep(self.max_wait_time)
            if self.pending_requests:
                return await self.process_batch()

    def should_process_batch(self):
        """判断是否应该处理批次"""
        if not self.pending_requests:
            return False

        # 检查最早请求的等待时间
        oldest_request = self.pending_requests[0]
        wait_time = time.time() - oldest_request.get('timestamp', time.time())
        return wait_time > self.max_wait_time

    async def process_batch(self):
        """处理批次请求"""
        if not self.pending_requests:
            return []

        batch = self.pending_requests.copy()
        self.pending_requests.clear()

        # 并行处理批次中的请求
        tasks = [self.process_single_request(req) for req in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return results

    async def process_single_request(self, request_data):
        """处理单个请求"""
        # 实际的请求处理逻辑
        await asyncio.sleep(0.01)  # 模拟处理时间
        return {"processed": True, "data": request_data}

# HTTP客户端优化
class OptimizedHTTPClient:
    """优化的HTTP客户端"""

    def __init__(self):
        # 连接池配置
        limits = httpx.Limits(
            max_keepalive_connections=50,
            max_connections=100,
            keepalive_expiry=30.0
        )

        # 超时配置
        timeout = httpx.Timeout(
            connect=5.0,
            read=30.0,
            write=10.0,
            pool=5.0
        )

        self.client = httpx.AsyncClient(
            limits=limits,
            timeout=timeout,
            http2=True  # 启用HTTP/2
        )

    async def batch_requests(self, urls):
        """批量请求"""
        tasks = [self.client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        return responses

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

# 预热机制
class APIWarmer:
    """API预热器"""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.warmup_endpoints = [
            "/health",
            "/api/auth/health",
            "/api/metrics"
        ]

    async def warmup(self):
        """执行预热"""
        print("🔥 开始API预热...")

        async with OptimizedHTTPClient() as client:
            tasks = []
            for endpoint in self.warmup_endpoints:
                url = f"{self.base_url}{endpoint}"
                # 每个端点预热3次
                for _ in range(3):
                    tasks.append(client.client.get(url))

            results = await asyncio.gather(*tasks, return_exceptions=True)
            success_count = sum(1 for r in results if not isinstance(r, Exception))

        print(f"✅ API预热完成: {success_count}/{len(tasks)} 请求成功")

# 应用配置
def create_optimized_app():
    """创建优化的FastAPI应用"""
    app = FastAPI(
        title="Perfect21 API",
        version="3.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    # 添加性能中间件
    app.add_middleware(PerformanceMiddleware)

    # 添加压缩中间件
    app.add_middleware(GZipMiddleware, minimum_size=1000)

    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应该限制
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app

# 启动时预热
async def startup_warmup():
    """启动时执行预热"""
    warmer = APIWarmer()
    await warmer.warmup()

# 使用示例
if __name__ == "__main__":
    app = create_optimized_app()

    # 添加启动事件
    @app.on_event("startup")
    async def startup_event():
        await startup_warmup()

    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        workers=4,
        loop="uvloop",
        http="httptools"
    )
```

### 2. 并发处理优化

```python
#!/usr/bin/env python3
"""
并发处理优化
"""

import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import List, Callable, Any
import functools
import time

class ConcurrencyManager:
    """并发管理器"""

    def __init__(self, max_concurrent_tasks=100):
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)
        self.thread_pool = ThreadPoolExecutor(max_workers=20)
        self.process_pool = ProcessPoolExecutor(max_workers=4)

    async def run_with_semaphore(self, coro):
        """使用信号量限制并发"""
        async with self.semaphore:
            return await coro

    async def gather_with_limit(self, tasks, limit=50):
        """限制并发数量的gather"""
        semaphore = asyncio.Semaphore(limit)

        async def run_task(task):
            async with semaphore:
                return await task

        limited_tasks = [run_task(task) for task in tasks]
        return await asyncio.gather(*limited_tasks, return_exceptions=True)

    def cpu_bound_task(self, func: Callable, *args, **kwargs):
        """CPU密集型任务"""
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(self.process_pool, func, *args, **kwargs)

    def io_bound_task(self, func: Callable, *args, **kwargs):
        """IO密集型任务"""
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(self.thread_pool, func, *args, **kwargs)

# 智能负载均衡器
class LoadBalancer:
    """智能负载均衡器"""

    def __init__(self, servers: List[str]):
        self.servers = servers
        self.server_stats = {server: {"requests": 0, "errors": 0, "response_time": 0}
                           for server in servers}
        self.current_index = 0

    def get_best_server(self) -> str:
        """获取最佳服务器"""
        # 简单的权重算法
        best_server = min(self.servers, key=lambda s: (
            self.server_stats[s]["errors"] * 1000 +
            self.server_stats[s]["response_time"] +
            self.server_stats[s]["requests"] * 0.1
        ))
        return best_server

    def record_request(self, server: str, response_time: float, is_error: bool = False):
        """记录请求统计"""
        stats = self.server_stats[server]
        stats["requests"] += 1
        stats["response_time"] = (stats["response_time"] * 0.9) + (response_time * 0.1)
        if is_error:
            stats["errors"] += 1

    async def make_request(self, path: str, **kwargs) -> Any:
        """发起负载均衡的请求"""
        server = self.get_best_server()
        url = f"{server}{path}"

        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, **kwargs) as response:
                    result = await response.json()
                    response_time = time.time() - start_time
                    self.record_request(server, response_time, False)
                    return result
        except Exception as e:
            response_time = time.time() - start_time
            self.record_request(server, response_time, True)
            raise e

# 自适应线程池
class AdaptiveThreadPool:
    """自适应线程池"""

    def __init__(self, min_workers=5, max_workers=50):
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.current_workers = min_workers
        self.pool = ThreadPoolExecutor(max_workers=min_workers)
        self.queue_size = 0
        self.completed_tasks = 0
        self.last_adjustment = time.time()

    def submit(self, fn, *args, **kwargs):
        """提交任务"""
        self.queue_size += 1

        # 检查是否需要调整线程池大小
        self._adjust_pool_size()

        future = self.pool.submit(self._wrapped_fn, fn, *args, **kwargs)
        return future

    def _wrapped_fn(self, fn, *args, **kwargs):
        """包装的函数执行"""
        try:
            result = fn(*args, **kwargs)
            self.completed_tasks += 1
            return result
        finally:
            self.queue_size = max(0, self.queue_size - 1)

    def _adjust_pool_size(self):
        """调整线程池大小"""
        now = time.time()
        if now - self.last_adjustment < 30:  # 30秒内不重复调整
            return

        # 基于队列大小和完成任务数调整
        if self.queue_size > self.current_workers * 2:  # 队列积压严重
            new_size = min(self.current_workers * 2, self.max_workers)
            if new_size > self.current_workers:
                self._resize_pool(new_size)
        elif self.queue_size < self.current_workers * 0.5:  # 队列较空
            new_size = max(self.current_workers // 2, self.min_workers)
            if new_size < self.current_workers:
                self._resize_pool(new_size)

        self.last_adjustment = now

    def _resize_pool(self, new_size: int):
        """调整线程池大小"""
        old_pool = self.pool
        self.pool = ThreadPoolExecutor(max_workers=new_size)
        self.current_workers = new_size

        print(f"📈 线程池大小调整: {self.current_workers} -> {new_size}")

        # 优雅关闭旧线程池
        old_pool.shutdown(wait=False)

# 全局并发管理器
concurrency_manager = ConcurrencyManager()
adaptive_pool = AdaptiveThreadPool()
```

## 🗄️ 数据库性能调优

### 1. 连接池优化

```python
#!/usr/bin/env python3
"""
数据库性能优化
"""

import asyncpg
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from typing import Optional
import time
import logging

class DatabaseManager:
    """数据库管理器"""

    def __init__(self, database_url: str):
        # 连接池配置
        self.engine = create_async_engine(
            database_url,
            # 连接池配置
            poolclass=QueuePool,
            pool_size=20,          # 连接池大小
            max_overflow=30,       # 最大溢出连接
            pool_timeout=30,       # 获取连接超时
            pool_recycle=3600,     # 连接回收时间(1小时)
            pool_pre_ping=True,    # 连接前ping检查
            # 性能优化
            echo=False,            # 生产环境关闭SQL日志
            future=True,
            # PostgreSQL特定优化
            connect_args={
                "server_settings": {
                    "jit": "off",  # 关闭JIT优化(小查询)
                    "application_name": "perfect21",
                },
                "command_timeout": 30,
            }
        )

        # 会话工厂
        self.async_session = sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        # 监控统计
        self.query_stats = {
            "total_queries": 0,
            "slow_queries": 0,
            "total_time": 0
        }

    async def get_session(self) -> AsyncSession:
        """获取数据库会话"""
        return self.async_session()

    async def execute_with_stats(self, session: AsyncSession, query, params=None):
        """执行查询并统计性能"""
        start_time = time.time()

        try:
            if params:
                result = await session.execute(query, params)
            else:
                result = await session.execute(query)

            execution_time = time.time() - start_time

            # 更新统计
            self.query_stats["total_queries"] += 1
            self.query_stats["total_time"] += execution_time

            # 慢查询告警
            if execution_time > 0.5:  # 500ms
                self.query_stats["slow_queries"] += 1
                logging.warning(f"慢查询检测: {execution_time:.3f}s - {str(query)[:100]}...")

            return result

        except Exception as e:
            logging.error(f"数据库查询失败: {e}")
            raise

    def get_performance_stats(self):
        """获取性能统计"""
        total = self.query_stats["total_queries"]
        if total > 0:
            avg_time = self.query_stats["total_time"] / total
            slow_ratio = self.query_stats["slow_queries"] / total * 100

            return {
                "total_queries": total,
                "average_time": f"{avg_time:.3f}s",
                "slow_queries": self.query_stats["slow_queries"],
                "slow_query_ratio": f"{slow_ratio:.1f}%"
            }
        return {"total_queries": 0}

# 数据库查询优化器
class QueryOptimizer:
    """查询优化器"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.query_cache = {}

    async def execute_with_cache(self, query, params=None, cache_key=None, ttl=300):
        """带缓存的查询执行"""
        if cache_key:
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                return cached_result

        async with self.db_manager.get_session() as session:
            result = await self.db_manager.execute_with_stats(session, query, params)

            if cache_key:
                self._cache_result(cache_key, result, ttl)

            return result

    def _get_cached_result(self, cache_key):
        """获取缓存结果"""
        if cache_key in self.query_cache:
            result, timestamp = self.query_cache[cache_key]
            if time.time() - timestamp < 300:  # 5分钟缓存
                return result
            else:
                del self.query_cache[cache_key]
        return None

    def _cache_result(self, cache_key, result, ttl):
        """缓存查询结果"""
        self.query_cache[cache_key] = (result, time.time())

# PostgreSQL特定优化
class PostgreSQLOptimizer:
    """PostgreSQL优化器"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    async def optimize_database(self):
        """优化数据库配置"""
        conn = await asyncpg.connect(self.connection_string)

        try:
            # 设置优化参数
            optimizations = [
                # 内存配置
                "SET shared_buffers = '256MB'",
                "SET effective_cache_size = '1GB'",
                "SET work_mem = '4MB'",
                "SET maintenance_work_mem = '64MB'",

                # 检查点配置
                "SET wal_buffers = '16MB'",
                "SET checkpoint_completion_target = 0.9",
                "SET checkpoint_segments = 32",

                # 连接配置
                "SET max_connections = 200",

                # 查询优化
                "SET random_page_cost = 1.1",
                "SET effective_io_concurrency = 200",

                # 统计信息
                "SET default_statistics_target = 100",
            ]

            for sql in optimizations:
                try:
                    await conn.execute(sql)
                    print(f"✅ 应用优化: {sql}")
                except Exception as e:
                    print(f"⚠️ 优化失败: {sql} - {e}")

            # 更新统计信息
            await conn.execute("ANALYZE")
            print("✅ 数据库统计信息已更新")

        finally:
            await conn.close()

    async def get_slow_queries(self, limit=10):
        """获取慢查询"""
        conn = await asyncpg.connect(self.connection_string)

        try:
            # 需要启用pg_stat_statements扩展
            slow_queries = await conn.fetch("""
                SELECT
                    query,
                    calls,
                    total_time,
                    mean_time,
                    rows
                FROM pg_stat_statements
                ORDER BY mean_time DESC
                LIMIT $1
            """, limit)

            return [dict(record) for record in slow_queries]

        except Exception as e:
            print(f"获取慢查询失败: {e}")
            return []
        finally:
            await conn.close()

# 使用示例
async def setup_optimized_database():
    """设置优化的数据库"""
    database_url = "postgresql+asyncpg://user:password@localhost/perfect21"

    # 创建数据库管理器
    db_manager = DatabaseManager(database_url)

    # 创建查询优化器
    query_optimizer = QueryOptimizer(db_manager)

    # PostgreSQL优化
    pg_optimizer = PostgreSQLOptimizer(database_url.replace("+asyncpg", ""))
    await pg_optimizer.optimize_database()

    return db_manager, query_optimizer
```

### 2. 索引优化

```sql
-- Perfect21 数据库索引优化

-- 用户表索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_email
ON users(email) WHERE active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_username
ON users(username) WHERE active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_created_at
ON users(created_at);

-- 认证令牌表索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tokens_user_id
ON auth_tokens(user_id) WHERE active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tokens_expires_at
ON auth_tokens(expires_at) WHERE active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tokens_token_hash
ON auth_tokens USING hash(token_hash) WHERE active = true;

-- 任务执行记录索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_task_executions_user_id
ON task_executions(user_id);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_task_executions_created_at
ON task_executions(created_at);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_task_executions_status
ON task_executions(status) WHERE status IN ('running', 'pending');

-- 工作空间索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_workspaces_user_id
ON workspaces(user_id) WHERE active = true;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_workspaces_name
ON workspaces(name) WHERE active = true;

-- 复合索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_task_executions_user_status
ON task_executions(user_id, status, created_at);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tokens_user_type
ON auth_tokens(user_id, token_type) WHERE active = true;

-- 分区表示例（大量数据时使用）
CREATE TABLE task_execution_logs_partitioned (
    id BIGSERIAL,
    task_execution_id BIGINT,
    log_level VARCHAR(20),
    message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY RANGE (created_at);

-- 创建月度分区
CREATE TABLE task_execution_logs_202509
PARTITION OF task_execution_logs_partitioned
FOR VALUES FROM ('2025-09-01') TO ('2025-10-01');

CREATE TABLE task_execution_logs_202510
PARTITION OF task_execution_logs_partitioned
FOR VALUES FROM ('2025-10-01') TO ('2025-11-01');

-- 分区索引
CREATE INDEX ON task_execution_logs_202509(task_execution_id, created_at);
CREATE INDEX ON task_execution_logs_202510(task_execution_id, created_at);

-- 清理旧分区的定时任务
-- 在cron中运行: 0 2 1 * * psql -d perfect21 -c "DROP TABLE IF EXISTS task_execution_logs_$(date -d '3 months ago' +%Y%m)"
```

## 🔄 缓存策略优化

### Redis缓存优化

```python
#!/usr/bin/env python3
"""
Redis缓存优化
"""

import redis.asyncio as aioredis
import json
import pickle
import time
import hashlib
from typing import Any, Optional, Union
import asyncio

class OptimizedRedisCache:
    """优化的Redis缓存"""

    def __init__(self, redis_url="redis://localhost:6379", db=0):
        # 连接池配置
        self.pool = aioredis.ConnectionPool.from_url(
            redis_url,
            db=db,
            max_connections=50,        # 最大连接数
            retry_on_timeout=True,     # 超时重试
            socket_keepalive=True,     # 保持连接
            socket_keepalive_options={
                1: 1,  # TCP_KEEPIDLE
                2: 3,  # TCP_KEEPINTVL
                3: 5,  # TCP_KEEPCNT
            },
            health_check_interval=30   # 健康检查间隔
        )
        self.redis = aioredis.Redis(connection_pool=self.pool)

        # 缓存统计
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0
        }

    async def get(self, key: str, default=None) -> Any:
        """获取缓存值"""
        try:
            value = await self.redis.get(key)
            if value is not None:
                self.stats["hits"] += 1
                return self._deserialize(value)
            else:
                self.stats["misses"] += 1
                return default
        except Exception as e:
            print(f"Redis GET error: {e}")
            return default

    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """设置缓存值"""
        try:
            serialized_value = self._serialize(value)
            result = await self.redis.setex(key, ttl, serialized_value)
            if result:
                self.stats["sets"] += 1
            return result
        except Exception as e:
            print(f"Redis SET error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            result = await self.redis.delete(key)
            if result:
                self.stats["deletes"] += 1
            return bool(result)
        except Exception as e:
            print(f"Redis DELETE error: {e}")
            return False

    async def get_or_set(self, key: str, func, ttl: int = 3600, *args, **kwargs) -> Any:
        """获取或设置缓存"""
        # 先尝试获取
        value = await self.get(key)
        if value is not None:
            return value

        # 缓存未命中，执行函数
        if asyncio.iscoroutinefunction(func):
            value = await func(*args, **kwargs)
        else:
            value = func(*args, **kwargs)

        # 设置缓存
        await self.set(key, value, ttl)
        return value

    async def batch_get(self, keys: list) -> dict:
        """批量获取"""
        try:
            values = await self.redis.mget(keys)
            result = {}
            for i, key in enumerate(keys):
                if values[i] is not None:
                    result[key] = self._deserialize(values[i])
                    self.stats["hits"] += 1
                else:
                    self.stats["misses"] += 1
            return result
        except Exception as e:
            print(f"Redis BATCH GET error: {e}")
            return {}

    async def batch_set(self, items: dict, ttl: int = 3600) -> bool:
        """批量设置"""
        try:
            pipe = self.redis.pipeline()
            for key, value in items.items():
                serialized_value = self._serialize(value)
                pipe.setex(key, ttl, serialized_value)

            results = await pipe.execute()
            success_count = sum(1 for r in results if r)
            self.stats["sets"] += success_count
            return success_count == len(items)
        except Exception as e:
            print(f"Redis BATCH SET error: {e}")
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """按模式清理缓存"""
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                deleted = await self.redis.delete(*keys)
                self.stats["deletes"] += deleted
                return deleted
            return 0
        except Exception as e:
            print(f"Redis CLEAR PATTERN error: {e}")
            return 0

    def _serialize(self, value: Any) -> bytes:
        """序列化值"""
        # 对于简单类型使用JSON，复杂类型使用pickle
        try:
            return json.dumps(value).encode('utf-8')
        except (TypeError, ValueError):
            return pickle.dumps(value)

    def _deserialize(self, value: bytes) -> Any:
        """反序列化值"""
        try:
            return json.loads(value.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return pickle.loads(value)

    async def get_stats(self) -> dict:
        """获取缓存统计"""
        info = await self.redis.info("stats")

        hit_rate = 0
        if self.stats["hits"] + self.stats["misses"] > 0:
            hit_rate = self.stats["hits"] / (self.stats["hits"] + self.stats["misses"]) * 100

        return {
            "local_stats": self.stats,
            "hit_rate": f"{hit_rate:.2f}%",
            "redis_stats": {
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0)
            }
        }

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            await self.redis.ping()
            return True
        except Exception:
            return False

    async def close(self):
        """关闭连接"""
        await self.redis.close()

# 智能缓存键生成器
class CacheKeyGenerator:
    """缓存键生成器"""

    @staticmethod
    def generate_key(prefix: str, *args, **kwargs) -> str:
        """生成缓存键"""
        # 构建键的组成部分
        key_parts = [prefix]

        # 添加位置参数
        for arg in args:
            if isinstance(arg, (str, int, float)):
                key_parts.append(str(arg))
            else:
                # 对复杂对象使用hash
                key_parts.append(hashlib.md5(str(arg).encode()).hexdigest()[:8])

        # 添加关键字参数
        if kwargs:
            sorted_kwargs = sorted(kwargs.items())
            kwargs_str = "&".join(f"{k}={v}" for k, v in sorted_kwargs)
            key_parts.append(hashlib.md5(kwargs_str.encode()).hexdigest()[:8])

        return ":".join(key_parts)

    @staticmethod
    def user_specific_key(user_id: str, prefix: str, *args) -> str:
        """生成用户特定的键"""
        return CacheKeyGenerator.generate_key(f"user:{user_id}:{prefix}", *args)

# 缓存装饰器
def cached(ttl: int = 3600, key_prefix: str = None):
    """缓存装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 生成缓存键
            if key_prefix:
                cache_key = CacheKeyGenerator.generate_key(key_prefix, *args, **kwargs)
            else:
                cache_key = CacheKeyGenerator.generate_key(func.__name__, *args, **kwargs)

            # 尝试从缓存获取
            cached_result = await redis_cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # 执行函数
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)

            # 设置缓存
            await redis_cache.set(cache_key, result, ttl)
            return result

        return wrapper
    return decorator

# 全局缓存实例
redis_cache = OptimizedRedisCache()

# 使用示例
@cached(ttl=1800, key_prefix="user_profile")
async def get_user_profile(user_id: str):
    """获取用户资料（带缓存）"""
    # 模拟数据库查询
    await asyncio.sleep(0.1)
    return {"user_id": user_id, "name": "Test User", "email": "test@example.com"}

# 清理过期缓存的定时任务
async def cache_cleanup_task():
    """定时清理缓存任务"""
    while True:
        try:
            # 清理过期的用户会话
            await redis_cache.clear_pattern("session:*")

            # 清理临时数据
            await redis_cache.clear_pattern("temp:*")

            print("✅ 缓存清理完成")
        except Exception as e:
            print(f"❌ 缓存清理失败: {e}")

        # 每小时清理一次
        await asyncio.sleep(3600)
```

## 📊 监控与告警

### 性能监控系统

```python
#!/usr/bin/env python3
"""
性能监控和告警系统
"""

import psutil
import time
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self.metrics_history = {}
        self.alert_thresholds = {
            "cpu_usage": 80,           # CPU使用率阈值
            "memory_usage": 85,        # 内存使用率阈值
            "disk_usage": 90,          # 磁盘使用率阈值
            "api_response_time": 1.0,  # API响应时间阈值(秒)
            "error_rate": 5.0,         # 错误率阈值(%)
            "connection_count": 100    # 数据库连接数阈值
        }
        self.alerts_sent = {}

    async def collect_system_metrics(self) -> Dict[str, Any]:
        """收集系统指标"""
        # CPU使用率
        cpu_usage = psutil.cpu_percent(interval=1)

        # 内存使用
        memory = psutil.virtual_memory()
        memory_usage = memory.percent

        # 磁盘使用
        disk = psutil.disk_usage('/')
        disk_usage = (disk.used / disk.total) * 100

        # 网络IO
        net_io = psutil.net_io_counters()

        # 进程信息
        process_count = len(psutil.pids())

        metrics = {
            "timestamp": datetime.now().isoformat(),
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "memory_available_gb": memory.available / (1024**3),
            "disk_usage": disk_usage,
            "disk_free_gb": disk.free / (1024**3),
            "network_bytes_sent": net_io.bytes_sent,
            "network_bytes_recv": net_io.bytes_recv,
            "process_count": process_count
        }

        return metrics

    async def collect_api_metrics(self) -> Dict[str, Any]:
        """收集API指标"""
        try:
            start_time = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.get('http://localhost:8000/health') as response:
                    response_time = time.time() - start_time
                    status_code = response.status

            # 模拟获取更多API指标
            api_metrics = {
                "api_response_time": response_time,
                "api_status": "healthy" if status_code == 200 else "unhealthy",
                "requests_per_second": self._calculate_rps(),
                "error_rate": self._calculate_error_rate(),
                "active_connections": self._get_active_connections()
            }

        except Exception as e:
            api_metrics = {
                "api_response_time": float('inf'),
                "api_status": "down",
                "error": str(e)
            }

        return api_metrics

    async def collect_database_metrics(self) -> Dict[str, Any]:
        """收集数据库指标"""
        # 这里应该连接实际的数据库获取指标
        # 为演示目的，使用模拟数据
        db_metrics = {
            "active_connections": 15,
            "slow_query_count": 2,
            "cache_hit_rate": 94.5,
            "database_size_mb": 256.7,
            "longest_query_time": 0.234
        }

        return db_metrics

    def _calculate_rps(self) -> float:
        """计算每秒请求数"""
        # 简化实现，实际应该基于实际请求日志
        return 25.3

    def _calculate_error_rate(self) -> float:
        """计算错误率"""
        # 简化实现
        return 0.8

    def _get_active_connections(self) -> int:
        """获取活跃连接数"""
        # 简化实现
        return 42

    async def check_alerts(self, metrics: Dict[str, Any]):
        """检查告警条件"""
        alerts = []

        # 检查各项指标
        for metric_name, threshold in self.alert_thresholds.items():
            if metric_name in metrics:
                value = metrics[metric_name]

                if isinstance(value, (int, float)) and value > threshold:
                    # 避免重复告警（5分钟内不重复发送相同告警）
                    alert_key = f"{metric_name}_{threshold}"
                    last_alert = self.alerts_sent.get(alert_key, 0)

                    if time.time() - last_alert > 300:  # 5分钟
                        alerts.append({
                            "metric": metric_name,
                            "current_value": value,
                            "threshold": threshold,
                            "severity": "warning" if value < threshold * 1.2 else "critical",
                            "timestamp": datetime.now().isoformat()
                        })
                        self.alerts_sent[alert_key] = time.time()

        if alerts:
            await self.send_alerts(alerts)

        return alerts

    async def send_alerts(self, alerts: List[Dict[str, Any]]):
        """发送告警"""
        for alert in alerts:
            print(f"🚨 ALERT: {alert['metric']} = {alert['current_value']}, "
                  f"threshold = {alert['threshold']} ({alert['severity']})")

            # 这里可以集成实际的告警系统
            # 如Slack、邮件、钉钉等
            await self._send_to_webhook(alert)

    async def _send_to_webhook(self, alert: Dict[str, Any]):
        """发送到Webhook"""
        webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

        try:
            payload = {
                "text": f"Perfect21 Alert: {alert['metric']} exceeded threshold",
                "attachments": [{
                    "color": "danger" if alert['severity'] == "critical" else "warning",
                    "fields": [
                        {"title": "Metric", "value": alert['metric'], "short": True},
                        {"title": "Current Value", "value": str(alert['current_value']), "short": True},
                        {"title": "Threshold", "value": str(alert['threshold']), "short": True},
                        {"title": "Severity", "value": alert['severity'], "short": True}
                    ]
                }]
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload) as response:
                    if response.status == 200:
                        print("✅ 告警已发送到Slack")
                    else:
                        print(f"❌ 告警发送失败: {response.status}")

        except Exception as e:
            print(f"❌ 告警发送异常: {e}")

    def store_metrics(self, metrics: Dict[str, Any]):
        """存储历史指标"""
        timestamp = metrics.get('timestamp', datetime.now().isoformat())

        # 保存到内存（实际应该保存到时序数据库）
        for key, value in metrics.items():
            if key not in self.metrics_history:
                self.metrics_history[key] = []

            self.metrics_history[key].append({
                "timestamp": timestamp,
                "value": value
            })

            # 只保留最近1小时的数据
            cutoff_time = datetime.now() - timedelta(hours=1)
            self.metrics_history[key] = [
                item for item in self.metrics_history[key]
                if datetime.fromisoformat(item["timestamp"].replace('Z', '')) > cutoff_time
            ]

    def get_metrics_summary(self, hours=1) -> Dict[str, Any]:
        """获取指标摘要"""
        summary = {}
        cutoff_time = datetime.now() - timedelta(hours=hours)

        for metric_name, history in self.metrics_history.items():
            recent_data = [
                item for item in history
                if datetime.fromisoformat(item["timestamp"].replace('Z', '')) > cutoff_time
            ]

            if recent_data and all(isinstance(item["value"], (int, float)) for item in recent_data):
                values = [item["value"] for item in recent_data]
                summary[metric_name] = {
                    "current": values[-1] if values else 0,
                    "average": sum(values) / len(values),
                    "max": max(values),
                    "min": min(values),
                    "count": len(values)
                }

        return summary

    async def run_monitoring_loop(self, interval=30):
        """运行监控循环"""
        print("🔍 启动性能监控...")

        while True:
            try:
                # 收集所有指标
                system_metrics = await self.collect_system_metrics()
                api_metrics = await self.collect_api_metrics()
                db_metrics = await self.collect_database_metrics()

                # 合并指标
                all_metrics = {**system_metrics, **api_metrics, **db_metrics}

                # 存储指标
                self.store_metrics(all_metrics)

                # 检查告警
                await self.check_alerts(all_metrics)

                # 打印摘要
                if int(time.time()) % 300 == 0:  # 每5分钟打印一次
                    summary = self.get_metrics_summary()
                    print(f"📊 系统状态摘要: CPU={summary.get('cpu_usage', {}).get('current', 0):.1f}%, "
                          f"内存={summary.get('memory_usage', {}).get('current', 0):.1f}%, "
                          f"API响应={summary.get('api_response_time', {}).get('current', 0):.3f}s")

            except Exception as e:
                print(f"❌ 监控异常: {e}")

            await asyncio.sleep(interval)

# 性能报告生成器
class PerformanceReporter:
    """性能报告生成器"""

    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor

    def generate_daily_report(self) -> str:
        """生成日报"""
        summary = self.monitor.get_metrics_summary(hours=24)

        report = []
        report.append("📊 Perfect21 性能日报")
        report.append("=" * 40)
        report.append(f"报告时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # 系统指标
        report.append("🖥️ 系统指标:")
        if 'cpu_usage' in summary:
            cpu = summary['cpu_usage']
            report.append(f"  CPU使用率: 平均{cpu['average']:.1f}%, 峰值{cpu['max']:.1f}%")

        if 'memory_usage' in summary:
            memory = summary['memory_usage']
            report.append(f"  内存使用率: 平均{memory['average']:.1f}%, 峰值{memory['max']:.1f}%")

        # API指标
        report.append("")
        report.append("🚀 API指标:")
        if 'api_response_time' in summary:
            api = summary['api_response_time']
            report.append(f"  响应时间: 平均{api['average']:.3f}s, 最大{api['max']:.3f}s")

        if 'error_rate' in summary:
            error = summary['error_rate']
            report.append(f"  错误率: 平均{error['average']:.2f}%")

        # 建议
        report.append("")
        report.append("💡 优化建议:")
        recommendations = self._generate_recommendations(summary)
        for rec in recommendations:
            report.append(f"  - {rec}")

        return "\n".join(report)

    def _generate_recommendations(self, summary: Dict[str, Any]) -> List[str]:
        """生成优化建议"""
        recommendations = []

        # CPU使用率建议
        if 'cpu_usage' in summary:
            cpu_avg = summary['cpu_usage']['average']
            if cpu_avg > 70:
                recommendations.append("CPU使用率较高，建议增加worker数量或优化算法")
            elif cpu_avg < 30:
                recommendations.append("CPU使用率较低，可以考虑减少资源分配")

        # 内存使用建议
        if 'memory_usage' in summary:
            memory_avg = summary['memory_usage']['average']
            if memory_avg > 80:
                recommendations.append("内存使用率高，建议启用内存清理或增加内存")

        # API响应时间建议
        if 'api_response_time' in summary:
            api_avg = summary['api_response_time']['average']
            if api_avg > 0.5:
                recommendations.append("API响应时间较慢，建议启用缓存或优化数据库查询")

        if not recommendations:
            recommendations.append("系统运行良好，无需特别优化")

        return recommendations

# 使用示例
async def main():
    """主函数"""
    monitor = PerformanceMonitor()
    reporter = PerformanceReporter(monitor)

    # 启动监控（在后台运行）
    monitor_task = asyncio.create_task(monitor.run_monitoring_loop(interval=30))

    # 定期生成报告
    async def report_task():
        while True:
            await asyncio.sleep(3600 * 24)  # 每天生成一次报告
            report = reporter.generate_daily_report()
            print(report)

            # 保存报告到文件
            with open(f"performance_report_{datetime.now().strftime('%Y%m%d')}.txt", "w") as f:
                f.write(report)

    report_task_obj = asyncio.create_task(report_task())

    # 等待任务完成
    await asyncio.gather(monitor_task, report_task_obj)

if __name__ == "__main__":
    asyncio.run(main())
```

---

> ⚡ **总结**: Perfect21 v3.0.0 性能调优涵盖了从系统资源到应用层面的全方位优化。通过系统性的调优和监控，Perfect21 能够在各种负载下保持高性能运行，为用户提供快速、稳定的智能开发体验。
>
> **记住**: 性能优化是一个持续的过程，需要根据实际使用情况不断调整和改进。