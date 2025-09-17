#!/usr/bin/env python3
"""
Perfect21认证系统主应用入口
FastAPI应用程序配置和启动
"""

import logging
import sys
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.core.config import get_settings
from backend.core.database import create_tables, db_manager
from backend.core.exceptions import BaseAppException, get_http_status_code
from backend.auth.controllers import auth_router, admin_router
from backend.core.middleware import (
    LoggingMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    RequestIDMiddleware
)

# 获取配置
settings = get_settings()

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用程序生命周期管理"""
    # 启动时执行
    logger.info(f"启动 {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"环境: {settings.ENVIRONMENT}")

    # 创建数据库表
    try:
        create_tables()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        sys.exit(1)

    # 测试数据库连接
    if not db_manager.test_connection():
        logger.error("数据库连接失败")
        sys.exit(1)

    # 应用程序运行中...
    yield

    # 关闭时执行
    logger.info("应用程序正在关闭...")

# 创建FastAPI应用实例
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Perfect21智能开发平台认证系统",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan
)

# === 中间件配置 ===

# 请求ID中间件（最先执行）
app.add_middleware(RequestIDMiddleware)

# 日志中间件
app.add_middleware(LoggingMiddleware)

# 安全头中间件
app.add_middleware(SecurityHeadersMiddleware)

# 速率限制中间件
if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(RateLimitMiddleware)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_CREDENTIALS,
    allow_methods=settings.CORS_METHODS,
    allow_headers=settings.CORS_HEADERS,
    expose_headers=["X-Request-ID"]
)

# 受信任主机中间件（生产环境）
if settings.ENVIRONMENT == "production":
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.perfect21.com", "localhost", "127.0.0.1"]
    )

# === 异常处理器 ===

@app.exception_handler(BaseAppException)
async def app_exception_handler(request: Request, exc: BaseAppException) -> JSONResponse:
    """处理自定义应用异常"""
    status_code = get_http_status_code(exc)

    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": exc.code,
            "message": exc.message,
            "details": exc.details,
            "request_id": getattr(request.state, "request_id", None)
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """处理请求验证异常"""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "VALIDATION_ERROR",
            "message": "请求数据验证失败",
            "details": {"errors": errors},
            "request_id": getattr(request.state, "request_id", None)
        }
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """处理HTTP异常"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": f"HTTP_{exc.status_code}",
            "message": exc.detail,
            "request_id": getattr(request.state, "request_id", None)
        }
    )

@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """处理内部服务器错误"""
    logger.error(f"内部服务器错误: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "INTERNAL_SERVER_ERROR",
            "message": "服务器内部错误" if not settings.DEBUG else str(exc),
            "request_id": getattr(request.state, "request_id", None)
        }
    )

# === 路由配置 ===

# 注册认证路由
app.include_router(auth_router)

# 注册管理员路由
app.include_router(admin_router)

# === 根路由和健康检查 ===

@app.get("/")
async def root() -> Dict[str, Any]:
    """根路由"""
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "running",
        "docs_url": "/docs" if settings.DEBUG else None
    }

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """健康检查端点"""
    # 检查数据库连接
    db_status = "healthy" if db_manager.test_connection() else "unhealthy"

    # 检查Redis连接
    redis_status = "healthy"  # 简化处理，实际应该测试Redis连接

    return {
        "status": "healthy" if db_status == "healthy" and redis_status == "healthy" else "unhealthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "checks": {
            "database": db_status,
            "redis": redis_status
        }
    }

@app.get("/info")
async def system_info() -> Dict[str, Any]:
    """系统信息端点（仅开发环境）"""
    if not settings.DEBUG:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not Found"
        )

    db_info = db_manager.get_engine_info()

    return {
        "application": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG
        },
        "database": db_info,
        "redis": {
            "url": settings.REDIS_URL,
            "host": settings.REDIS_HOST,
            "port": settings.REDIS_PORT,
            "db": settings.REDIS_DB
        },
        "security": {
            "jwt_algorithm": settings.JWT_ALGORITHM,
            "access_token_expire": f"{settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES}分钟",
            "refresh_token_expire": f"{settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS}天",
            "password_bcrypt_rounds": settings.PASSWORD_BCRYPT_ROUNDS,
            "max_login_attempts": settings.MAX_LOGIN_ATTEMPTS,
            "rate_limit_enabled": settings.RATE_LIMIT_ENABLED
        }
    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        workers=settings.WORKERS if settings.ENVIRONMENT == "production" else 1,
        reload=settings.RELOAD,
        access_log=settings.ACCESS_LOG,
        log_level=settings.LOG_LEVEL.lower()
    )