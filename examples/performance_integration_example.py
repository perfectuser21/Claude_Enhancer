#!/usr/bin/env python3
"""
Claude Enhancer Performance Optimization Integration Example
性能优化系统集成使用示例
"""

import asyncio
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import time
from typing import Dict, Any

# 导入性能优化组件
from backend.core import (
    get_performance_manager,
    setup_performance_middleware,
    PerformanceManager,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# 全局性能管理器
performance_manager: PerformanceManager = None

# 创建FastAPI应用
app = FastAPI(
    title="Claude Enhancer Performance Demo API",
    description="展示性能优化系统的完整集成",
    version="1.0.0",
)


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    global performance_manager

    logger.info("🚀 启动性能优化系统...")

    # 初始化性能管理器
    performance_manager = await get_performance_manager(
        service_name="perfect21-demo-api", config_file="performance.yaml"
    )

    # 设置性能监控中间件
    setup_performance_middleware(app, performance_manager)

    logger.info("✅ 性能优化系统启动完成")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    global performance_manager

    if performance_manager:
        logger.info("🛑 关闭性能优化系统...")
        await performance_manager.shutdown()
        logger.info("✅ 性能优化系统已关闭")


# ===== API端点示例 =====


@app.get("/")
async def root():
    """根端点"""
    return {
        "service": "Claude Enhancer Performance Demo API",
        "status": "running",
        "timestamp": time.time(),
        "performance_enabled": performance_manager is not None,
    }


@app.get("/api/users/{user_id}")
async def get_user(user_id: int):
    """获取用户信息 - 演示缓存使用"""
    # 使用性能上下文
    async with performance_manager.performance_context("get_user"):
        # 1. 尝试从缓存获取
        if performance_manager.cache_manager:
            cached_user = await performance_manager.cache_manager.get(
                "users", f"user_{user_id}"
            )

            if cached_user:
                logger.info(f"🎯 缓存命中: user_{user_id}")
                return {"user_id": user_id, "data": cached_user, "source": "cache"}

        # 2. 模拟数据库查询
        await asyncio.sleep(0.1)  # 模拟数据库延迟

        user_data = {
            "id": user_id,
            "name": f"User {user_id}",
            "email": f"user{user_id}@perfect21.com",
            "created_at": time.time(),
        }

        # 3. 存入缓存
        if performance_manager.cache_manager:
            await performance_manager.cache_manager.set(
                "users", f"user_{user_id}", user_data, ttl=300  # 5分钟
            )
            logger.info(f"💾 缓存存储: user_{user_id}")

        return {"user_id": user_id, "data": user_data, "source": "database"}


@app.post("/api/users/{user_id}/process")
async def process_user_data(user_id: int, data: Dict[str, Any]):
    """处理用户数据 - 演示异步任务"""
    async with performance_manager.performance_context("process_user_data"):
        # 提交异步任务
        if performance_manager.async_processor:
            task_id = await performance_manager.async_processor.submit_custom_task(
                process_user_background_task,
                user_id,
                data,
                name=f"process_user_{user_id}",
                priority=performance_manager.async_processor.config.__class__.__dict__.get(
                    "TaskPriority", "NORMAL"
                ),
            )

            return {
                "message": "User data processing started",
                "task_id": task_id,
                "user_id": user_id,
            }

        # 如果没有异步处理器，直接处理
        result = await process_user_background_task(user_id, data)
        return {"message": "User data processed", "result": result, "user_id": user_id}


@app.get("/api/stats")
async def get_performance_stats():
    """获取性能统计"""
    if not performance_manager:
        raise HTTPException(status_code=503, detail="Performance manager not available")

    # 收集各组件统计
    stats = {}

    # 缓存统计
    if performance_manager.cache_manager:
        cache_stats = await performance_manager.cache_manager.get_stats()
        stats["cache"] = cache_stats

    # 数据库统计
    if performance_manager.database_optimizer:
        db_stats = await performance_manager.database_optimizer.get_database_stats()
        stats["database"] = db_stats

    # 异步处理器统计
    if performance_manager.async_processor:
        queue_stats = await performance_manager.async_processor.get_queue_status()
        stats["async_processor"] = queue_stats

    # 指标收集器统计
    if performance_manager.metrics_collector:
        metrics_stats = (
            await performance_manager.metrics_collector.get_metrics_summary()
        )
        stats["metrics"] = metrics_stats

    # 生成性能报告
    performance_report = await performance_manager.generate_performance_report()
    stats["performance_report"] = {
        "overall_score": performance_report.overall_score,
        "response_time_p95": performance_report.response_time_p95,
        "cache_hit_rate": performance_report.cache_hit_rate,
        "system_health": performance_report.system_health,
        "bottlenecks": performance_report.bottlenecks,
        "recommendations": performance_report.recommendations,
    }

    return stats


@app.get("/api/health")
async def health_check():
    """健康检查"""
    if not performance_manager:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "reason": "Performance manager not initialized",
            },
        )

    health_status = await performance_manager.get_health_status()

    overall_healthy = all(health_status.values()) if health_status else False

    return {
        "status": "healthy" if overall_healthy else "unhealthy",
        "components": health_status,
        "timestamp": time.time(),
    }


@app.post("/api/load-test")
async def run_load_test(requests_count: int = 100):
    """运行负载测试"""
    async with performance_manager.performance_context("load_test"):
        # 创建并发任务
        tasks = []
        for i in range(requests_count):
            task = asyncio.create_task(simulate_load_request(i))
            tasks.append(task)

        # 等待所有任务完成
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()

        # 统计结果
        successful = sum(1 for r in results if not isinstance(r, Exception))
        failed = len(results) - successful
        duration = end_time - start_time

        return {
            "total_requests": requests_count,
            "successful": successful,
            "failed": failed,
            "duration": duration,
            "requests_per_second": requests_count / duration,
            "avg_response_time": duration / requests_count * 1000,  # ms
        }


@app.get("/api/cache/clear")
async def clear_cache():
    """清空缓存"""
    if not performance_manager or not performance_manager.cache_manager:
        raise HTTPException(status_code=503, detail="Cache manager not available")

    # 清空用户缓存
    cleared_count = await performance_manager.cache_manager.delete_pattern("users", "*")

    return {"message": "Cache cleared", "cleared_keys": cleared_count}


# ===== 后台任务示例 =====


async def process_user_background_task(user_id: int, data: Dict[str, Any]):
    """用户数据处理后台任务"""
    # 模拟处理时间
    await asyncio.sleep(0.5)

    # 模拟处理逻辑
    processed_data = {
        "user_id": user_id,
        "original_data": data,
        "processed_at": time.time(),
        "status": "completed",
    }

    # 发送通知
    if performance_manager and performance_manager.async_processor:
        await performance_manager.async_processor.submit_notification_task(
            user_id=str(user_id),
            message=f"Your data has been processed successfully",
            notification_type="info",
        )

    logger.info(f"✅ 用户数据处理完成: user_{user_id}")
    return processed_data


async def simulate_load_request(request_id: int):
    """模拟负载请求"""
    # 模拟不同类型的操作
    operations = [
        lambda: performance_manager.cache_manager.set(
            "load_test", f"key_{request_id}", f"value_{request_id}"
        ),
        lambda: performance_manager.cache_manager.get(
            "load_test", f"key_{request_id % 10}"
        ),
        lambda: asyncio.sleep(0.01),  # 模拟CPU操作
    ]

    # 随机选择操作
    import random

    operation = random.choice(operations)

    if asyncio.iscoroutinefunction(operation):
        await operation()
    else:
        operation()

    return f"Request {request_id} completed"


# ===== 性能监控中间件 =====


@app.middleware("http")
async def performance_monitoring_middleware(request: Request, call_next):
    """性能监控中间件"""
    start_time = time.time()

    # 记录请求开始
    if performance_manager and performance_manager.metrics_collector:
        performance_manager.metrics_collector.increment_counter(
            "http_requests_total",
            labels={"method": request.method, "endpoint": request.url.path},
        )

    try:
        response = await call_next(request)

        # 记录成功请求
        duration = time.time() - start_time
        if performance_manager and performance_manager.metrics_collector:
            performance_manager.metrics_collector.record_timer(
                "http_request_duration",
                duration,
                labels={
                    "method": request.method,
                    "endpoint": request.url.path,
                    "status": str(response.status_code),
                },
            )

        return response

    except Exception as e:
        # 记录错误请求
        duration = time.time() - start_time
        if performance_manager and performance_manager.metrics_collector:
            performance_manager.metrics_collector.increment_counter(
                "http_errors_total",
                labels={
                    "method": request.method,
                    "endpoint": request.url.path,
                    "error_type": type(e).__name__,
                },
            )

        raise


# ===== 演示脚本 =====


async def run_demo():
    """运行演示"""
    # print("🚀 Claude Enhancer Performance Integration Demo")
    # print("=" * 50)

    # 等待服务启动
    await asyncio.sleep(2)

    import aiohttp

    base_url = "http://localhost:8080"

    async with aiohttp.ClientSession() as session:
        # 1. 测试基本功能
        # print("\n📋 Phase 1: Basic API Test")
        async with session.get(f"{base_url}/") as response:
            data = await response.json()
        # print(f"✅ Root endpoint: {data['status']}")

        # 2. 测试缓存功能
        # print("\n💾 Phase 2: Cache Test")
        for i in range(5):
            async with session.get(f"{base_url}/api/users/{i}") as response:
                data = await response.json()
        # print(f"📊 User {i}: {data['source']}")

        # 3. 测试异步任务
        # print("\n⚡ Phase 3: Async Task Test")
        async with session.post(
            f"{base_url}/api/users/1/process",
            json={"action": "update_profile", "data": {"name": "Updated Name"}},
        ) as response:
            data = await response.json()
        # print(f"🔄 Task submitted: {data['task_id']}")

        # 4. 运行负载测试
        # print("\n🔥 Phase 4: Load Test")
        async with session.post(
            f"{base_url}/api/load-test?requests_count=50"
        ) as response:
            data = await response.json()
        # print(f"📈 Load test: {data['requests_per_second']:.0f} req/sec")

        # 5. 获取性能统计
        # print("\n📊 Phase 5: Performance Stats")
        async with session.get(f"{base_url}/api/stats") as response:
            data = await response.json()
            report = data.get("performance_report", {})
    # print(f"🎯 Performance Score: {report.get('overall_score', 0):.1f}/100")
    # print(f"⚡ Response Time P95: {report.get('response_time_p95', 0):.2f}ms")
    # print(f"💾 Cache Hit Rate: {report.get('cache_hit_rate', 0):.1f}%")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        # 运行演示客户端
        asyncio.run(run_demo())
    else:
        # 启动服务器
        # print("🚀 Starting Claude Enhancer Performance Demo API...")
        # print("📊 Performance Dashboard: http://localhost:8000/")
        # print("🌐 API Endpoint: http://localhost:8080/")
        # print("📈 API Stats: http://localhost:8080/api/stats")
        # print("🔍 Health Check: http://localhost:8080/api/health")
        # print("\n运行演示客户端: python examples/performance_integration_example.py demo")

        uvicorn.run(
            "examples.performance_integration_example:app",
            host="0.0.0.0",
            port=8080,
            reload=False,
            log_level="info",
        )
