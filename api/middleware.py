#!/usr/bin/env python3
"""
Perfect21 API中间件
提供认证、授权、限流、日志等中间件功能
"""

import os
import sys
import time
import json
from typing import Callable, Dict, Any, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
import asyncio

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from features.auth_system import AuthManager
from modules.logger import log_info, log_error, log_warning
from modules.cache import cache_manager

class RateLimitMiddleware:
    """API限流中间件"""

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """初始化限流中间件"""
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}

    async def __call__(self, request: Request, call_next: Callable):
        """中间件主函数"""
        client_ip = self._get_client_ip(request)
        current_time = time.time()

        # 清理过期记录
        self._cleanup_expired(current_time)

        # 检查限流
        if not self._is_allowed(client_ip, current_time):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": f"请求过于频繁，请在{self.window_seconds}秒后重试",
                    "retry_after": self.window_seconds
                }
            )

        # 记录请求
        self._record_request(client_ip, current_time)

        # 继续处理请求
        return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        # 检查代理头部
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host

    def _is_allowed(self, client_ip: str, current_time: float) -> bool:
        """检查是否允许请求"""
        if client_ip not in self.requests:
            return True

        request_times = self.requests[client_ip]
        recent_requests = [t for t in request_times if current_time - t < self.window_seconds]

        return len(recent_requests) < self.max_requests

    def _record_request(self, client_ip: str, current_time: float):
        """记录请求时间"""
        if client_ip not in self.requests:
            self.requests[client_ip] = []

        self.requests[client_ip].append(current_time)

        # 保持列表大小合理
        if len(self.requests[client_ip]) > self.max_requests:
            self.requests[client_ip] = self.requests[client_ip][-self.max_requests:]

    def _cleanup_expired(self, current_time: float):
        """清理过期记录"""
        for client_ip in list(self.requests.keys()):
            self.requests[client_ip] = [
                t for t in self.requests[client_ip]
                if current_time - t < self.window_seconds
            ]

            if not self.requests[client_ip]:
                del self.requests[client_ip]

class AuthenticationMiddleware:
    """认证中间件"""

    def __init__(self):
        """初始化认证中间件"""
        self.auth_manager = None
        self.public_paths = {
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/api/auth/login",
            "/api/auth/register",
            "/api/auth/health"
        }

    def _get_auth_manager(self) -> AuthManager:
        """获取认证管理器"""
        if self.auth_manager is None:
            self.auth_manager = AuthManager()
        return self.auth_manager

    async def __call__(self, request: Request, call_next: Callable):
        """中间件主函数"""
        path = request.url.path

        # 跳过公开路径
        if path in self.public_paths or path.startswith("/static/"):
            return await call_next(request)

        # 检查认证头部
        authorization = request.headers.get("Authorization")
        if not authorization:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "MISSING_AUTH_HEADER",
                    "message": "需要Authorization头部"
                }
            )

        # 验证令牌
        try:
            if not authorization.startswith("Bearer "):
                raise ValueError("Invalid authorization format")

            token = authorization.split(" ")[1]
            auth_mgr = self._get_auth_manager()
            result = auth_mgr.verify_token(token)

            if not result['success']:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "error": "INVALID_TOKEN",
                        "message": result['message']
                    }
                )

            # 将用户信息添加到请求状态
            request.state.user = result['user']

        except Exception as e:
            log_error("认证中间件错误", e)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "AUTH_ERROR",
                    "message": "认证过程中发生错误"
                }
            )

        return await call_next(request)

class LoggingMiddleware:
    """请求日志中间件"""

    def __init__(self):
        """初始化日志中间件"""
        self.skip_paths = {"/health", "/docs", "/redoc", "/openapi.json"}

    async def __call__(self, request: Request, call_next: Callable):
        """中间件主函数"""
        start_time = time.time()
        client_ip = self._get_client_ip(request)

        # 记录请求开始
        if request.url.path not in self.skip_paths:
            log_info(f"API请求开始: {request.method} {request.url.path} - IP: {client_ip}")

        try:
            # 处理请求
            response = await call_next(request)
            process_time = time.time() - start_time

            # 记录请求完成
            if request.url.path not in self.skip_paths:
                user_info = getattr(request.state, 'user', None)
                user_id = user_info['id'] if user_info else 'anonymous'

                log_info(
                    f"API请求完成: {request.method} {request.url.path} "
                    f"- 状态: {response.status_code} "
                    f"- 耗时: {process_time:.3f}s "
                    f"- 用户: {user_id} "
                    f"- IP: {client_ip}"
                )

                # 记录到缓存统计
                self._record_api_stats(request, response, process_time, user_id, client_ip)

            return response

        except Exception as e:
            process_time = time.time() - start_time
            log_error(f"API请求异常: {request.method} {request.url.path} - 耗时: {process_time:.3f}s", e)
            raise

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host

    def _record_api_stats(self, request: Request, response: Response,
                         process_time: float, user_id: str, client_ip: str):
        """记录API统计信息"""
        try:
            stats_key = f"api_stats:{int(time.time() // 60)}"  # 按分钟统计
            current_stats = cache_manager.get(stats_key) or {}

            endpoint_key = f"{request.method}:{request.url.path}"
            if endpoint_key not in current_stats:
                current_stats[endpoint_key] = {
                    'count': 0,
                    'total_time': 0,
                    'status_codes': {},
                    'users': set(),
                    'ips': set()
                }

            endpoint_stats = current_stats[endpoint_key]
            endpoint_stats['count'] += 1
            endpoint_stats['total_time'] += process_time

            status_code = str(response.status_code)
            endpoint_stats['status_codes'][status_code] = endpoint_stats['status_codes'].get(status_code, 0) + 1

            endpoint_stats['users'].add(user_id)
            endpoint_stats['ips'].add(client_ip)

            # 转换set为list以便JSON序列化
            for key in ['users', 'ips']:
                if isinstance(endpoint_stats[key], set):
                    endpoint_stats[key] = list(endpoint_stats[key])

            cache_manager.set(stats_key, current_stats, ttl=3600)  # 1小时TTL

        except Exception as e:
            log_error("记录API统计失败", e)

class SecurityHeadersMiddleware:
    """安全头部中间件"""

    def __init__(self):
        """初始化安全头部中间件"""
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }

    async def __call__(self, request: Request, call_next: Callable):
        """中间件主函数"""
        response = await call_next(request)

        # 添加安全头部
        for header, value in self.security_headers.items():
            response.headers[header] = value

        return response

class CORSMiddleware:
    """自定义CORS中间件"""

    def __init__(self, allow_origins: list = None, allow_methods: list = None,
                 allow_headers: list = None, allow_credentials: bool = True):
        """初始化CORS中间件"""
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        self.allow_headers = allow_headers or ["*"]
        self.allow_credentials = allow_credentials

    async def __call__(self, request: Request, call_next: Callable):
        """中间件主函数"""
        # 处理预检请求
        if request.method == "OPTIONS":
            response = Response()
            self._add_cors_headers(response, request)
            return response

        # 处理实际请求
        response = await call_next(request)
        self._add_cors_headers(response, request)
        return response

    def _add_cors_headers(self, response: Response, request: Request):
        """添加CORS头部"""
        origin = request.headers.get("Origin")

        if self.allow_origins == ["*"] or (origin and origin in self.allow_origins):
            response.headers["Access-Control-Allow-Origin"] = origin or "*"

        response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
        response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)

        if self.allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"

class ErrorHandlingMiddleware:
    """错误处理中间件"""

    async def __call__(self, request: Request, call_next: Callable):
        """中间件主函数"""
        try:
            return await call_next(request)

        except HTTPException as e:
            # FastAPI HTTP异常
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": "HTTP_ERROR",
                    "message": e.detail,
                    "status_code": e.status_code
                }
            )

        except ValueError as e:
            # 值错误
            log_warning(f"API值错误: {request.url.path} - {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": "VALIDATION_ERROR",
                    "message": str(e)
                }
            )

        except Exception as e:
            # 其他未处理异常
            log_error(f"API未处理异常: {request.url.path}", e)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": "INTERNAL_SERVER_ERROR",
                    "message": "服务器内部错误",
                    "detail": str(e) if os.getenv("DEBUG") else None
                }
            )

class ResponseTimeMiddleware:
    """响应时间中间件"""

    async def __call__(self, request: Request, call_next: Callable):
        """中间件主函数"""
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # 添加响应时间头部
        response.headers["X-Process-Time"] = str(round(process_time, 6))

        return response

# 中间件工厂函数
def create_rate_limit_middleware(max_requests: int = 100, window_seconds: int = 60):
    """创建限流中间件"""
    return RateLimitMiddleware(max_requests, window_seconds)

def create_auth_middleware():
    """创建认证中间件"""
    return AuthenticationMiddleware()

def create_logging_middleware():
    """创建日志中间件"""
    return LoggingMiddleware()

def create_security_headers_middleware():
    """创建安全头部中间件"""
    return SecurityHeadersMiddleware()

def create_error_handling_middleware():
    """创建错误处理中间件"""
    return ErrorHandlingMiddleware()

def create_response_time_middleware():
    """创建响应时间中间件"""
    return ResponseTimeMiddleware()