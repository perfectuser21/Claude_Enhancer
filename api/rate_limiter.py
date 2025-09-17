#!/usr/bin/env python3
"""
Perfect21 API速率限制器
防止暴力破解和滥用
"""

import time
import redis
import hashlib
from typing import Optional, Tuple
from functools import wraps
from fastapi import HTTPException, Request, status
from modules.logger import log_info, log_warning, log_error

class RateLimiter:
    """速率限制器"""

    def __init__(self):
        """初始化速率限制器"""
        try:
            # 尝试连接Redis
            self.redis_client = redis.Redis(
                host='localhost',
                port=6379,
                db=1,  # 使用不同的db避免冲突
                decode_responses=True,
                socket_keepalive=True
            )
            self.redis_client.ping()
            self.use_redis = True
            log_info("Rate limiter initialized with Redis backend")
        except redis.ConnectionError:
            # Redis不可用，使用内存存储
            self.use_redis = False
            self.memory_storage = {}
            log_warning("Redis unavailable, using in-memory rate limiting")

    def _get_key(self, identifier: str, endpoint: str = "") -> str:
        """生成限制key"""
        if endpoint:
            return f"rate_limit:{endpoint}:{identifier}"
        return f"rate_limit:{identifier}"

    def _get_identifier(self, request: Request) -> str:
        """获取请求标识符"""
        # 优先使用用户ID
        if hasattr(request.state, 'user_id') and request.state.user_id:
            return f"user:{request.state.user_id}"

        # 使用IP地址
        client_ip = request.client.host
        # 处理代理情况
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(',')[0].strip()

        return f"ip:{client_ip}"

    def check_rate_limit(
        self,
        identifier: str,
        max_requests: int,
        time_window: int,
        endpoint: str = ""
    ) -> Tuple[bool, int, int]:
        """
        检查速率限制

        Args:
            identifier: 请求标识符
            max_requests: 时间窗口内最大请求数
            time_window: 时间窗口（秒）
            endpoint: API端点

        Returns:
            (是否允许, 剩余请求数, 重置时间)
        """
        key = self._get_key(identifier, endpoint)
        current_time = int(time.time())

        if self.use_redis:
            # Redis实现
            try:
                # 使用滑动窗口算法
                pipe = self.redis_client.pipeline()
                pipe.zremrangebyscore(key, 0, current_time - time_window)
                pipe.zadd(key, {str(current_time): current_time})
                pipe.zcard(key)
                pipe.expire(key, time_window + 1)
                results = pipe.execute()

                request_count = results[2]
                remaining = max(0, max_requests - request_count)
                reset_time = current_time + time_window

                if request_count > max_requests:
                    return False, 0, reset_time

                return True, remaining, reset_time

            except Exception as e:
                log_error(f"Redis rate limit check failed: {e}")
                # 失败时允许请求
                return True, max_requests, current_time + time_window

        else:
            # 内存实现
            if key not in self.memory_storage:
                self.memory_storage[key] = []

            # 清理过期记录
            self.memory_storage[key] = [
                timestamp for timestamp in self.memory_storage[key]
                if timestamp > current_time - time_window
            ]

            # 添加当前请求
            self.memory_storage[key].append(current_time)

            request_count = len(self.memory_storage[key])
            remaining = max(0, max_requests - request_count)
            reset_time = current_time + time_window

            if request_count > max_requests:
                # 移除超出的请求
                self.memory_storage[key].pop()
                return False, 0, reset_time

            return True, remaining, reset_time

    def limit(
        self,
        max_requests: int,
        time_window: int = 60,
        endpoint: str = "",
        error_message: str = "Rate limit exceeded"
    ):
        """
        速率限制装饰器

        Args:
            max_requests: 最大请求数
            time_window: 时间窗口（秒）
            endpoint: 端点名称
            error_message: 错误消息
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(request: Request, *args, **kwargs):
                identifier = self._get_identifier(request)

                allowed, remaining, reset_time = self.check_rate_limit(
                    identifier,
                    max_requests,
                    time_window,
                    endpoint or request.url.path
                )

                # 设置响应头
                request.state.rate_limit_remaining = remaining
                request.state.rate_limit_reset = reset_time

                if not allowed:
                    log_warning(f"Rate limit exceeded for {identifier} on {endpoint or request.url.path}")
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=error_message,
                        headers={
                            "X-RateLimit-Limit": str(max_requests),
                            "X-RateLimit-Remaining": "0",
                            "X-RateLimit-Reset": str(reset_time),
                            "Retry-After": str(time_window)
                        }
                    )

                return await func(request, *args, **kwargs)

            return wrapper
        return decorator

    def limit_by_key(
        self,
        key_func,
        max_requests: int,
        time_window: int = 60,
        error_message: str = "Rate limit exceeded"
    ):
        """
        基于自定义key的速率限制

        Args:
            key_func: 生成key的函数
            max_requests: 最大请求数
            time_window: 时间窗口（秒）
            error_message: 错误消息
        """
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # 从参数中获取key
                key = key_func(*args, **kwargs)

                allowed, remaining, reset_time = self.check_rate_limit(
                    key,
                    max_requests,
                    time_window
                )

                if not allowed:
                    log_warning(f"Rate limit exceeded for key {key}")
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=error_message,
                        headers={
                            "X-RateLimit-Limit": str(max_requests),
                            "X-RateLimit-Remaining": "0",
                            "X-RateLimit-Reset": str(reset_time),
                            "Retry-After": str(time_window)
                        }
                    )

                return await func(*args, **kwargs)

            return wrapper
        return decorator

    def reset_limit(self, identifier: str, endpoint: str = ""):
        """重置速率限制"""
        key = self._get_key(identifier, endpoint)

        if self.use_redis:
            try:
                self.redis_client.delete(key)
                log_info(f"Rate limit reset for {key}")
            except Exception as e:
                log_error(f"Failed to reset rate limit: {e}")
        else:
            if key in self.memory_storage:
                del self.memory_storage[key]
                log_info(f"Rate limit reset for {key}")

    def get_limit_info(self, identifier: str, endpoint: str = "") -> dict:
        """获取限制信息"""
        key = self._get_key(identifier, endpoint)
        current_time = int(time.time())

        if self.use_redis:
            try:
                count = self.redis_client.zcard(key)
                ttl = self.redis_client.ttl(key)
                return {
                    "requests": count,
                    "ttl": ttl if ttl > 0 else 0
                }
            except Exception:
                return {"requests": 0, "ttl": 0}
        else:
            if key in self.memory_storage:
                # 清理过期记录
                self.memory_storage[key] = [
                    t for t in self.memory_storage[key]
                    if t > current_time - 3600  # 假设最大窗口1小时
                ]
                return {
                    "requests": len(self.memory_storage[key]),
                    "ttl": 0
                }
            return {"requests": 0, "ttl": 0}


# 全局实例
_rate_limiter = None

def get_rate_limiter() -> RateLimiter:
    """获取全局速率限制器实例"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter

# 预定义的速率限制
class RateLimits:
    """预定义的速率限制配置"""

    # 登录尝试：每分钟5次，每小时20次
    LOGIN = {"per_minute": 5, "per_hour": 20}

    # 注册：每小时3次，每天10次
    REGISTER = {"per_hour": 3, "per_day": 10}

    # 密码重置：每小时3次
    PASSWORD_RESET = {"per_hour": 3}

    # API通用限制：每分钟60次，每小时1000次
    API_DEFAULT = {"per_minute": 60, "per_hour": 1000}

    # 搜索：每分钟30次
    SEARCH = {"per_minute": 30}

    # 文件上传：每小时10次
    UPLOAD = {"per_hour": 10}


def apply_rate_limits(app):
    """
    应用全局速率限制到FastAPI应用

    Args:
        app: FastAPI应用实例
    """
    from fastapi import Request

    limiter = get_rate_limiter()

    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        """全局速率限制中间件"""
        # 跳过健康检查等端点
        skip_paths = ["/health", "/metrics", "/"]
        if request.url.path in skip_paths:
            return await call_next(request)

        # 获取请求标识
        identifier = limiter._get_identifier(request)

        # 应用全局限制
        allowed, remaining, reset_time = limiter.check_rate_limit(
            identifier,
            max_requests=RateLimits.API_DEFAULT["per_minute"],
            time_window=60,
            endpoint="global"
        )

        if not allowed:
            log_warning(f"Global rate limit exceeded for {identifier}")
            return HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later.",
                headers={
                    "X-RateLimit-Limit": str(RateLimits.API_DEFAULT["per_minute"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time),
                    "Retry-After": "60"
                }
            )

        response = await call_next(request)

        # 添加速率限制头
        response.headers["X-RateLimit-Limit"] = str(RateLimits.API_DEFAULT["per_minute"])
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)

        return response