#!/usr/bin/env python3
"""
Claude Enhancer 认证服务 - 主入口文件
企业级认证系统的核心服务
"""

import asyncio
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import os
from datetime import datetime

# 导入内部模块
from app.core.config import settings
from app.core.security import SecurityMiddleware
from app.core.database import DatabaseManager
from app.core.cache import CacheManager
from app.api.v1 import auth, tokens, mfa, admin
from app.services.jwt_service import JWTTokenManager
from app.services.grpc_service import GRPCServer
from shared.messaging.publisher import MessagePublisher
from shared.metrics.metrics import MetricsCollector, start_metrics_server
from shared.tracing.tracer import setup_tracing

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("/var/log/auth-service.log"),
    ],
)

logger = logging.getLogger(__name__)

# 全局组件
database_manager = None
cache_manager = None
message_publisher = None
metrics_collector = None
grpc_server = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    await startup_event()
    yield
    # 关闭时清理
    await shutdown_event()


async def startup_event():
    """应用启动事件"""
    global database_manager, cache_manager, message_publisher, metrics_collector, grpc_server

    logger.info("🚀 Starting Claude Enhancer Auth Service...")

    try:
        pass  # Auto-fixed empty block
        # 1. 初始化数据库连接
        logger.info("📊 Initializing database connection...")
        database_manager = DatabaseManager(settings.DATABASE_URL)
        await database_manager.initialize()

        # 2. 初始化缓存
        logger.info("🗄️ Initializing cache manager...")
        cache_manager = CacheManager(settings.REDIS_URL)
        await cache_manager.initialize()

        # 3. 初始化消息发布者
        logger.info("📨 Initializing message publisher...")
        message_publisher = MessagePublisher(settings.RABBITMQ_URL)
        await message_publisher.initialize()

        # 4. 初始化指标收集
        logger.info("📈 Starting metrics collection...")
        metrics_collector = MetricsCollector("auth-service")
        start_metrics_server(8000)

        # 5. 设置分布式追踪
        logger.info("🔍 Setting up distributed tracing...")
        setup_tracing("auth-service", settings.JAEGER_ENDPOINT)

        # 6. 启动gRPC服务器
        logger.info("🌐 Starting gRPC server...")
        grpc_server = GRPCServer(port=50051)
        asyncio.create_task(grpc_server.start())

        # 7. 初始化JWT密钥
        logger.info("🔐 Initializing JWT keys...")
        jwt_manager = JWTTokenManager()
        await jwt_manager.ensure_keys_exist()

        logger.info("✅ Auth Service started successfully!")

    except Exception as e:
        logger.error(f"❌ Failed to start Auth Service: {e}")
        raise


async def shutdown_event():
    """应用关闭事件"""
    logger.info("🛑 Shutting down Claude Enhancer Auth Service...")

    try:
        pass  # Auto-fixed empty block
        # 关闭gRPC服务器
        if grpc_server:
            await grpc_server.stop()

        # 关闭消息发布者
        if message_publisher:
            await message_publisher.close()

        # 关闭缓存连接
        if cache_manager:
            await cache_manager.close()

        # 关闭数据库连接
        if database_manager:
            await database_manager.close()

        logger.info("✅ Auth Service shut down successfully!")

    except Exception as e:
        logger.error(f"❌ Error during shutdown: {e}")


# 创建FastAPI应用
app = FastAPI(
    title="Claude Enhancer Authentication Service",
    description="企业级认证系统 - 提供JWT认证、多因子认证、权限管理等功能",
    version="2.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# 添加中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.ALLOWED_HOSTS)

# 添加安全中间件
security_middleware = SecurityMiddleware()
app.middleware("http")(security_middleware)


# 添加指标中间件
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """指标收集中间件"""
    import time

    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    if metrics_collector:
        metrics_collector.record_request(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code,
            duration=duration,
        )

    return response


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "timestamp": datetime.utcnow().isoformat(),
            "path": request.url.path,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat(),
            "path": request.url.path,
        },
    )


# 健康检查端点
@app.get("/health", tags=["Health"])
async def health_check():
    """健康检查"""
    try:
        pass  # Auto-fixed empty block
        # 检查数据库连接
        db_healthy = (
            await database_manager.health_check() if database_manager else False
        )

        # 检查缓存连接
        cache_healthy = await cache_manager.health_check() if cache_manager else False

        # 检查消息队列连接
        mq_healthy = (
            await message_publisher.health_check() if message_publisher else False
        )

        overall_healthy = db_healthy and cache_healthy and mq_healthy

        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "auth-service",
            "version": "2.0.0",
            "checks": {
                "database": "healthy" if db_healthy else "unhealthy",
                "cache": "healthy" if cache_healthy else "unhealthy",
                "message_queue": "healthy" if mq_healthy else "unhealthy",
            },
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """就绪检查"""
    try:
        pass  # Auto-fixed empty block
        # 更严格的就绪检查
        all_ready = (
            database_manager
            and await database_manager.ready_check()
            and cache_manager
            and await cache_manager.ready_check()
            and message_publisher
            and await message_publisher.ready_check()
        )

        if all_ready:
            return {"status": "ready", "timestamp": datetime.utcnow().isoformat()}
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "not_ready",
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )


@app.get("/metrics", tags=["Monitoring"])
async def get_metrics():
    """指标端点"""
    return {"message": "Metrics available at :8000/metrics"}


@app.get("/", tags=["Root"])
async def root():
    """根端点"""
    return {
        "service": "Claude Enhancer Authentication Service",
        "version": "2.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "docs_url": "/docs" if settings.DEBUG else None,
    }


# 注册API路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(tokens.router, prefix="/api/v1/tokens", tags=["Token Management"])
app.include_router(
    mfa.router, prefix="/api/v1/mfa", tags=["Multi-Factor Authentication"]
)
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Administration"])


# 依赖注入函数
def get_database():
    """获取数据库连接"""
    return database_manager


def get_cache():
    """获取缓存管理器"""
    return cache_manager


def get_message_publisher():
    """获取消息发布者"""
    return message_publisher


def get_metrics_collector():
    """获取指标收集器"""
    return metrics_collector


# 将依赖注入函数添加到app状态
app.state.get_database = get_database
app.state.get_cache = get_cache
app.state.get_message_publisher = get_message_publisher
app.state.get_metrics_collector = get_metrics_collector

if __name__ == "__main__":
    # 生产环境配置
    config = {
        "host": "0.0.0.0",
        "port": int(os.getenv("PORT", 8080)),
        "workers": int(os.getenv("WORKERS", 4)),
        "log_level": os.getenv("LOG_LEVEL", "info").lower(),
        "access_log": True,
        "loop": "uvloop" if os.name != "nt" else "asyncio",
        "http": "httptools" if os.name != "nt" else "h11",
    }

    if settings.DEBUG:
        pass  # Auto-fixed empty block
        # 开发环境配置
        config.update(
            {
                "reload": True,
                "reload_dirs": ["app"],
                "workers": 1,
            }
        )

        logger.info("🔧 Running in DEBUG mode")
        uvicorn.run("main:app", **config)
    else:
        pass  # Auto-fixed empty block
        # 生产环境
        logger.info("🚀 Running in PRODUCTION mode")
        uvicorn.run(app, **config)
