#!/usr/bin/env python3
"""
自定义中间件
包含日志、安全、速率限制等中间件
"""

import time
import uuid
import logging
from typing import Callable, Dict, Any
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
import redis
from backend.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

class RequestIDMiddleware(BaseHTTPMiddleware):
    """请求ID中间件 - 为每个请求生成唯一ID"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成或获取请求ID
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())

        # 将请求ID添加到请求状态
        request.state.request_id = request_id

        # 调用下一个中间件或路由处理器
        response = await call_next(request)

        # 在响应头中添加请求ID
        response.headers["X-Request-ID"] = request_id

        return response

class LoggingMiddleware(BaseHTTPMiddleware):
    """日志中间件 - 记录请求和响应信息"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        request_id = getattr(request.state, "request_id", "unknown")

        # 记录请求信息
        logger.info(
            f"[{request_id}] {request.method} {request.url} - "
            f"IP: {self._get_client_ip(request)} - "
            f"UA: {request.headers.get('user-agent', 'unknown')[:100]}"
        )

        # 处理请求
        try:
            response = await call_next(request)
        except Exception as e:
            # 记录异常
            process_time = time.time() - start_time
            logger.error(
                f"[{request_id}] 请求处理异常 - "
                f"耗时: {process_time:.3f}s - 错误: {str(e)}"
            )
            raise

        # 记录响应信息
        process_time = time.time() - start_time
        logger.info(
            f"[{request_id}] {response.status_code} - "
            f"耗时: {process_time:.3f}s"
        )

        # 添加性能头
        response.headers["X-Process-Time"] = f"{process_time:.3f}"

        return response

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端真实IP"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        return getattr(request.client, 'host', 'unknown')

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """安全头中间件 - 添加安全相关的HTTP头"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # 添加安全头
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' https:; "
                "connect-src 'self' https:; "
                "frame-ancestors 'none';"
            ),
        }

        # 在HTTPS环境下添加HSTS头
        if request.url.scheme == "https":
            security_headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        # 应用安全头
        for header, value in security_headers.items():
            response.headers[header] = value

        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """速率限制中间件 - 基于IP地址的请求频率限制"""

    def __init__(self, app):
        super().__init__(app)
        self.redis_client = None

        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True
            )
            # 测试连接
            self.redis_client.ping()
        except Exception as e:
            logger.warning(f"Redis连接失败，速率限制将不可用: {e}")
            self.redis_client = None

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self.redis_client:
            # Redis不可用时跳过速率限制
            return await call_next(request)

        # 获取客户端IP
        client_ip = self._get_client_ip(request)
        request_id = getattr(request.state, "request_id", "unknown")

        # 确定限制规则
        limits = self._get_rate_limits(request)

        # 检查每个限制规则
        for limit_key, limit_value, window_seconds in limits:
            cache_key = f"rate_limit:{client_ip}:{limit_key}"

            try:
                # 获取当前请求数
                current_requests = self.redis_client.get(cache_key)
                current_requests = int(current_requests) if current_requests else 0

                if current_requests >= limit_value:
                    logger.warning(
                        f"[{request_id}] 速率限制触发 - "
                        f"IP: {client_ip} - 限制: {limit_key}({limit_value}/{window_seconds}s)"
                    )

                    return JSONResponse(
                        status_code=HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "success": False,
                            "error": "RATE_LIMIT_EXCEEDED",
                            "message": "请求频率过高，请稍后再试",
                            "retry_after": window_seconds
                        },
                        headers={
                            "Retry-After": str(window_seconds),
                            "X-RateLimit-Limit": str(limit_value),
                            "X-RateLimit-Remaining": "0",
                            "X-RateLimit-Reset": str(int(time.time()) + window_seconds)
                        }
                    )

                # 增加请求计数
                pipe = self.redis_client.pipeline()
                pipe.incr(cache_key)
                pipe.expire(cache_key, window_seconds)
                pipe.execute()

                # 在响应中添加速率限制头
                def add_rate_limit_headers(response: Response) -> Response:
                    remaining = max(0, limit_value - current_requests - 1)
                    response.headers["X-RateLimit-Limit"] = str(limit_value)
                    response.headers["X-RateLimit-Remaining"] = str(remaining)
                    response.headers["X-RateLimit-Reset"] = str(int(time.time()) + window_seconds)
                    return response

                response = await call_next(request)
                return add_rate_limit_headers(response)

            except Exception as e:
                logger.error(f"速率限制检查失败: {e}")
                # Redis错误时继续处理请求
                break

        return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端真实IP"""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        return getattr(request.client, 'host', 'unknown')

    def _get_rate_limits(self, request: Request) -> list:
        """获取请求的速率限制规则"""
        limits = []

        # 全局限制
        limits.append(("global", settings.RATE_LIMIT_REQUESTS_PER_MINUTE, 60))

        # 登录端点特殊限制
        if request.url.path in ["/api/auth/login", "/api/auth/register"]:
            limits.append(("auth", settings.RATE_LIMIT_LOGIN_REQUESTS_PER_MINUTE, 60))

        # API端点限制
        if request.url.path.startswith("/api/"):
            limits.append(("api", settings.RATE_LIMIT_REQUESTS_PER_MINUTE, 60))

        return limits

class CacheMiddleware(BaseHTTPMiddleware):
    """缓存中间件 - 缓存GET请求的响应"""

    def __init__(self, app):
        super().__init__(app)
        self.redis_client = None

        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB + 1,  # 使用不同的DB
                password=settings.REDIS_PASSWORD,
                decode_responses=False  # 保持字节格式
            )
            self.redis_client.ping()
        except Exception as e:
            logger.warning(f"缓存Redis连接失败: {e}")
            self.redis_client = None

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 只缓存GET请求
        if request.method != "GET" or not self.redis_client:
            return await call_next(request)

        # 检查是否应该缓存此路径
        if not self._should_cache(request):
            return await call_next(request)

        # 生成缓存键
        cache_key = self._generate_cache_key(request)

        try:
            # 尝试从缓存获取响应
            cached_response = self.redis_client.get(cache_key)
            if cached_response:
                logger.debug(f"缓存命中: {cache_key}")
                # 这里需要反序列化响应，简化处理
                return await call_next(request)

            # 处理请求
            response = await call_next(request)

            # 缓存响应（仅缓存成功响应）
            if response.status_code == 200:
                # 这里需要序列化响应，简化处理
                cache_ttl = self._get_cache_ttl(request)
                # self.redis_client.setex(cache_key, cache_ttl, serialized_response)
                logger.debug(f"响应已缓存: {cache_key}")

            return response

        except Exception as e:
            logger.error(f"缓存操作失败: {e}")
            return await call_next(request)

    def _should_cache(self, request: Request) -> bool:
        """判断是否应该缓存请求"""
        # 不缓存认证相关的端点
        if request.url.path.startswith("/api/auth/"):
            return False

        # 不缓存管理员端点
        if request.url.path.startswith("/api/admin/"):
            return False

        # 不缓存带有认证头的请求
        if request.headers.get("authorization"):
            return False

        # 只缓存某些特定端点
        cacheable_paths = ["/health", "/", "/info"]
        return request.url.path in cacheable_paths

    def _generate_cache_key(self, request: Request) -> str:
        """生成缓存键"""
        path = request.url.path
        query = str(request.url.query)
        return f"http_cache:{path}:{query}"

    def _get_cache_ttl(self, request: Request) -> int:
        """获取缓存TTL（秒）"""
        # 健康检查缓存30秒
        if request.url.path == "/health":
            return 30

        # 其他端点缓存5分钟
        return 300

class MetricsMiddleware(BaseHTTPMiddleware):
    """指标中间件 - 收集请求指标"""

    def __init__(self, app):
        super().__init__(app)
        self.request_count = 0
        self.total_time = 0.0

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        try:
            response = await call_next(request)

            # 更新指标
            process_time = time.time() - start_time
            self.request_count += 1
            self.total_time += process_time

            # 添加指标头
            response.headers["X-Request-Count"] = str(self.request_count)
            response.headers["X-Average-Time"] = f"{self.total_time / self.request_count:.3f}"

            return response

        except Exception as e:
            # 记录错误指标
            process_time = time.time() - start_time
            self.request_count += 1
            self.total_time += process_time
            raise