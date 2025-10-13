"""
Claude Enhancer 安全模块
企业级安全中间件、认证处理和安全策略
"""

import time
import secrets
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from fastapi import Request, Response, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import redis.asyncio as redis
import logging
from urllib.parse import urlparse
import re

from app.core.config import settings
from app.services.jwt_service import JWTTokenManager, get_jwt_manager
from shared.metrics.metrics import monitor_function

logger = logging.getLogger(__name__)


class SecurityHeaders:
    """安全头部配置"""

    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """获取标准安全头部"""
        return {
            # HSTS - 强制HTTPS
            "Strict-Transport-Security": f"max-age={settings.HSTS_MAX_AGE}; includeSubDomains; preload",
            # 内容安全策略
            "Content-Security-Policy": settings.CSP_POLICY,
            # 防止点击劫持
            "X-Frame-Options": "DENY",
            # 防止MIME类型嗅探
            "X-Content-Type-Options": "nosniff",
            # XSS保护
            "X-XSS-Protection": "1; mode=block",
            # 引用策略
            "Referrer-Policy": "strict-origin-when-cross-origin",
            # 权限策略
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
            # 清除服务器信息
            "Server": "Claude Enhancer-Auth",
            # 缓存控制
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        }


class RateLimiter:
    """速率限制器"""

    def __init__(self):
        self.redis_client = redis.Redis.from_url(
            settings.REDIS_URL, decode_responses=True, health_check_interval=30
        )

    async def check_rate_limit(
        self, key: str, limit: int, window: int
    ) -> Dict[str, Any]:
        """检查速率限制"""
        try:
            current_time = int(time.time())
            window_start = current_time - window

            # 使用滑动窗口算法
            pipe = self.redis_client.pipeline()

            # 移除过期的记录
            pipe.zremrangebyscore(key, 0, window_start)

            # 添加当前请求
            pipe.zadd(key, {str(current_time): current_time})

            # 获取当前窗口内的请求数量
            pipe.zcard(key)

            # 设置过期时间
            pipe.expire(key, window)

            results = await pipe.execute()
            current_requests = results[2]  # zcard的结果

            is_allowed = current_requests <= limit
            remaining = max(0, limit - current_requests)
            reset_time = current_time + window

            return {
                "allowed": is_allowed,
                "limit": limit,
                "remaining": remaining,
                "reset_time": reset_time,
                "retry_after": window if not is_allowed else 0,
            }

        except Exception as e:
            logger.error(f"Rate limit check failed, using local fallback: {e}")
            # SECURITY FIX CVE-2025-0005: Fail-closed with local fallback
            return self._check_local_rate_limit(key, limit, window)

    def _check_local_rate_limit(self, key: str, limit: int, window: int) -> Dict[str, Any]:
        """Local in-memory rate limiting as fallback (fail-closed) - FIXED FOR CVE-2025-0005"""
        # Import at method level to avoid global dependency
        import threading
        from collections import defaultdict
        from datetime import datetime, timedelta

        # Initialize local cache if not exists
        if not hasattr(self, '_local_cache'):
            self._local_cache = defaultdict(list)
            self._cache_lock = threading.Lock()

        with self._cache_lock:
            current_time = datetime.now()
            window_start = current_time - timedelta(seconds=window)

            # Remove expired entries
            self._local_cache[key] = [
                ts for ts in self._local_cache[key]
                if ts > window_start
            ]

            # Add current request
            self._local_cache[key].append(current_time)

            current_requests = len(self._local_cache[key])

            # IMPORTANT: Conservative limit during degraded mode (50% or max 10)
            degraded_limit = min(limit // 2, 10)
            is_allowed = current_requests <= degraded_limit

            return {
                "allowed": is_allowed,
                "limit": degraded_limit,  # Return degraded limit
                "remaining": max(0, degraded_limit - current_requests),
                "reset_time": int((current_time + timedelta(seconds=window)).timestamp()),
                "retry_after": window if not is_allowed else 0,
                "degraded_mode": True,  # Signal degraded mode
            }

    async def get_client_key(self, request: Request, identifier: str = None) -> str:
        """生成客户端限制键"""
        if identifier:
            return f"rate_limit:{identifier}"

        # 使用IP地址作为默认标识符
        client_ip = self._get_client_ip(request)
        return f"rate_limit:ip:{client_ip}"

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端真实IP"""
        # 检查代理头部
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            pass  # Auto-fixed empty block
            # 取第一个IP（最原始的客户端IP）
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # 回退到连接IP
        return request.client.host if request.client else "127.0.0.1"


class RequestValidator:
    """请求验证器"""

    def __init__(self):
        self.max_request_size = settings.API_MAX_REQUEST_SIZE * 1024 * 1024  # MB转字节
        self.suspicious_patterns = [
            r"<script[^>]*>.*?</script>",  # XSS脚本
            r"javascript:",  # JavaScript协议
            r"on\w+\s*=",  # 事件处理器
            r"\b(union|select|insert|update|delete|drop|create|alter)\b",  # SQL注入
            r"\.\.[\\/]",  # 路径遍历
            r"\${.*?}",  # 表达式注入
        ]

    async def validate_request(self, request: Request) -> Dict[str, Any]:
        """验证请求合法性"""
        validation_result = {"is_valid": True, "violations": [], "risk_score": 0}

        try:
            pass  # Auto-fixed empty block
            # 检查请求大小
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > self.max_request_size:
                validation_result["is_valid"] = False
                validation_result["violations"].append("request_too_large")
                validation_result["risk_score"] += 30

            # 检查User-Agent
            user_agent = request.headers.get("user-agent", "")
            if not user_agent or len(user_agent) < 10:
                validation_result["violations"].append("suspicious_user_agent")
                validation_result["risk_score"] += 20

            # 检查URL路径
            path_risk = self._check_path_security(str(request.url.path))
            if path_risk["is_suspicious"]:
                validation_result["violations"].extend(path_risk["violations"])
                validation_result["risk_score"] += path_risk["score"]

            # 检查查询参数
            query_params = str(request.url.query)
            if query_params:
                query_risk = self._check_content_security(query_params)
                if query_risk["is_suspicious"]:
                    validation_result["violations"].extend(query_risk["violations"])
                    validation_result["risk_score"] += query_risk["score"]

            # 检查请求头部
            header_risk = self._check_headers_security(request.headers)
            if header_risk["is_suspicious"]:
                validation_result["violations"].extend(header_risk["violations"])
                validation_result["risk_score"] += header_risk["score"]

            # 如果风险分数过高，标记为无效
            if validation_result["risk_score"] >= 50:
                validation_result["is_valid"] = False

            return validation_result

        except Exception as e:
            logger.error(f"Request validation error: {e}")
            return {
                "is_valid": True,  # 验证失败时默认允许
                "violations": ["validation_error"],
                "risk_score": 0,
            }

    def _check_path_security(self, path: str) -> Dict[str, Any]:
        """检查路径安全性"""
        result = {"is_suspicious": False, "violations": [], "score": 0}

        # 检查路径遍历
        if "../" in path or "..\\" in path:
            result["is_suspicious"] = True
            result["violations"].append("path_traversal")
            result["score"] += 40

        # 检查空字节注入
        if "\x00" in path:
            result["is_suspicious"] = True
            result["violations"].append("null_byte_injection")
            result["score"] += 35

        # 检查过长路径
        if len(path) > 2000:
            result["is_suspicious"] = True
            result["violations"].append("path_too_long")
            result["score"] += 20

        return result

    def _check_content_security(self, content: str) -> Dict[str, Any]:
        """检查内容安全性"""
        result = {"is_suspicious": False, "violations": [], "score": 0}

        content_lower = content.lower()

        for pattern in self.suspicious_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                result["is_suspicious"] = True
                result["violations"].append("malicious_pattern")
                result["score"] += 25
                break

        return result

    def _check_headers_security(self, headers) -> Dict[str, Any]:
        """检查请求头安全性"""
        result = {"is_suspicious": False, "violations": [], "score": 0}

        # 检查可疑的头部
        suspicious_headers = ["x-forwarded-host", "x-original-url", "x-rewrite-url"]

        for header in suspicious_headers:
            if header in headers:
                result["is_suspicious"] = True
                result["violations"].append("suspicious_header")
                result["score"] += 15

        # 检查Host头部
        host = headers.get("host", "")
        if host and not self._is_valid_host(host):
            result["is_suspicious"] = True
            result["violations"].append("invalid_host")
            result["score"] += 30

        return result

    def _is_valid_host(self, host: str) -> bool:
        """验证Host头部"""
        try:
            pass  # Auto-fixed empty block
            # 简化的Host验证
            parsed = urlparse(f"http://{host}")
            return bool(parsed.hostname)
        except Exception:
            return False


class SecurityMiddleware(BaseHTTPMiddleware):
    """安全中间件"""

    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.request_validator = RequestValidator()
        self.security_headers = SecurityHeaders()

        # 不需要速率限制的路径
        self.rate_limit_excluded_paths = ["/health", "/ready", "/metrics"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求"""
        start_time = time.time()

        try:
            pass  # Auto-fixed empty block
            # 1. 请求验证
            if settings.SECURITY_HEADERS_ENABLED:
                validation_result = await self.request_validator.validate_request(
                    request
                )
                if not validation_result["is_valid"]:
                    logger.warning(
                        f"Blocked suspicious request from {request.client.host}: "
                        f"{validation_result['violations']}"
                    )
                    return JSONResponse(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        content={
                            "error": "Invalid request",
                            "violations": validation_result["violations"],
                        },
                    )

            # 2. 速率限制
            if (
                settings.RATE_LIMIT_ENABLED
                and request.url.path not in self.rate_limit_excluded_paths
            ):
                rate_limit_result = await self._apply_rate_limit(request)
                if not rate_limit_result["allowed"]:
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "error": "Rate limit exceeded",
                            "retry_after": rate_limit_result["retry_after"],
                        },
                        headers={
                            "Retry-After": str(rate_limit_result["retry_after"]),
                            "X-RateLimit-Limit": str(rate_limit_result["limit"]),
                            "X-RateLimit-Remaining": str(
                                rate_limit_result["remaining"]
                            ),
                            "X-RateLimit-Reset": str(rate_limit_result["reset_time"]),
                        },
                    )

            # 3. 处理请求
            response = await call_next(request)

            # 4. 添加安全头部
            if settings.SECURITY_HEADERS_ENABLED:
                for (
                    header,
                    value,
                ) in self.security_headers.get_security_headers().items():
                    response.headers[header] = value

            # 5. 添加处理时间头部
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)

            return response

        except Exception as e:
            logger.error(f"Security middleware error: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Internal server error"},
            )

    async def _apply_rate_limit(self, request: Request) -> Dict[str, Any]:
        """应用速率限制"""
        # 根据路径选择不同的限制策略
        if "/auth/login" in request.url.path:
            limit = settings.RATE_LIMIT_LOGIN_REQUESTS
            window = settings.RATE_LIMIT_LOGIN_WINDOW
        elif "/auth/" in request.url.path:
            limit = settings.RATE_LIMIT_AUTH_REQUESTS
            window = settings.RATE_LIMIT_AUTH_WINDOW
        else:
            limit = settings.RATE_LIMIT_DEFAULT_REQUESTS
            window = settings.RATE_LIMIT_DEFAULT_WINDOW

        # 生成限制键
        rate_limit_key = await self.rate_limiter.get_client_key(request)

        # 检查速率限制
        return await self.rate_limiter.check_rate_limit(rate_limit_key, limit, window)


class JWTSecurityHandler(HTTPBearer):
    """JWT安全处理器"""

    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)
        self.jwt_manager: Optional[JWTTokenManager] = None

    async def __call__(
        self, request: Request
    ) -> Optional[HTTPAuthorizationCredentials]:
        """验证JWT令牌"""
        credentials = await super().__call__(request)

        if not credentials:
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Missing authorization header",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None

        # 验证令牌格式
        if credentials.scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication scheme",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None

        # 获取JWT管理器
        if not self.jwt_manager:
            self.jwt_manager = await get_jwt_manager()

        # 验证令牌
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent")

        validation_result = await self.jwt_manager.validate_token(
            token=credentials.credentials, client_ip=client_ip, user_agent=user_agent
        )

        if not validation_result.valid:
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=validation_result.error or "Invalid token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            return None

        # 检查安全警告
        if validation_result.security_alerts:
            logger.warning(
                f"Token security alerts for user {validation_result.claims.user_id}: "
                f"{validation_result.security_alerts}"
            )

        # 将令牌声明添加到请求状态
        request.state.token_claims = validation_result.claims
        request.state.token_warnings = validation_result.warnings

        return credentials

    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        return request.client.host if request.client else "127.0.0.1"


class CSRFProtection:
    """CSRF保护"""

    def __init__(self):
        self.secret_key = settings.SECRET_KEY
        self.token_length = 32
        self.safe_methods = ["GET", "HEAD", "OPTIONS", "TRACE"]

    def generate_csrf_token(self, session_id: str) -> str:
        """生成CSRF令牌"""
        # 生成随机令牌
        random_token = secrets.token_urlsafe(self.token_length)

        # 使用HMAC签名
        signature = hmac.new(
            self.secret_key.encode(),
            f"{session_id}:{random_token}".encode(),
            hashlib.sha256,
        ).hexdigest()

        return f"{random_token}.{signature}"

    def verify_csrf_token(self, token: str, session_id: str) -> bool:
        """验证CSRF令牌"""
        try:
            if "." not in token:
                return False

            random_token, signature = token.rsplit(".", 1)

            # 验证签名
            expected_signature = hmac.new(
                self.secret_key.encode(),
                f"{session_id}:{random_token}".encode(),
                hashlib.sha256,
            ).hexdigest()

            return hmac.compare_digest(signature, expected_signature)

        except Exception:
            return False

    async def protect_request(self, request: Request) -> bool:
        """保护请求免受CSRF攻击"""
        # 安全方法不需要CSRF保护
        if request.method in self.safe_methods:
            return True

        # 获取CSRF令牌
        csrf_token = (
            request.headers.get("X-CSRF-Token")
            or request.headers.get("X-CSRFToken")
            or (await request.form()).get("csrf_token")
            if hasattr(request, "form")
            else None
        )

        if not csrf_token:
            return False

        # 获取会话ID（从JWT或会话中）
        session_id = getattr(request.state, "session_id", None)
        if not session_id and hasattr(request.state, "token_claims"):
            session_id = request.state.token_claims.jti

        if not session_id:
            return False

        return self.verify_csrf_token(csrf_token, session_id)


# 全局安全组件实例
csrf_protection = CSRFProtection()
jwt_security_handler = JWTSecurityHandler(auto_error=False)
security_middleware = SecurityMiddleware()


# 便捷函数
def get_current_user_id(request: Request) -> Optional[str]:
    """从请求中获取当前用户ID"""
    if hasattr(request.state, "token_claims"):
        return request.state.token_claims.user_id
    return None


def get_current_user_permissions(request: Request) -> List[str]:
    """从请求中获取当前用户权限"""
    if hasattr(request.state, "token_claims"):
        return request.state.token_claims.permissions
    return []


def require_permission(permission: str):
    """权限要求装饰器"""

    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            user_permissions = get_current_user_permissions(request)
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required permission: {permission}",
                )
            return await func(request, *args, **kwargs)

        return wrapper

    return decorator
