"""
认证中间件和装饰器
提供Flask、FastAPI等框架的认证中间件
包含路由保护、令牌验证、权限检查等功能
"""

import re
import time
from functools import wraps
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta

from .auth import auth_service
from .jwt import jwt_manager, token_blacklist
from .rbac import rbac_manager


class AuthMiddleware:
    """通用认证中间件基类"""

    def __init__(
        self,
        auth_service=None,
        jwt_manager=None,
        rbac_manager=None,
        excluded_paths: List[str] = None,
        public_endpoints: List[str] = None,
    ):
        """
        初始化认证中间件

        Args:
            auth_service: 认证服务实例
            jwt_manager: JWT管理器实例
            rbac_manager: RBAC管理器实例
            excluded_paths: 排除的路径列表（正则表达式）
            public_endpoints: 公开端点列表
        """
        self.auth_service = auth_service or auth_service
        self.jwt_manager = jwt_manager or jwt_manager
        self.rbac_manager = rbac_manager or rbac_manager

        # 默认排除的路径
        self.excluded_paths = excluded_paths or [
            r"^/auth/login$",
            r"^/auth/register$",
            r"^/auth/refresh$",
            r"^/health$",
            r"^/status$",
            r"^/docs.*",
            r"^/openapi.*",
            r"^/static/.*",
            r"^/favicon\.ico$",
        ]

        # 公开端点
        self.public_endpoints = public_endpoints or []

        # 编译正则表达式
        self.excluded_patterns = [
            re.compile(pattern) for pattern in self.excluded_paths
        ]

    def is_excluded_path(self, path: str) -> bool:
        """检查路径是否被排除"""
        for pattern in self.excluded_patterns:
            if pattern.match(path):
                return True
        return path in self.public_endpoints

    def extract_token(self, authorization_header: str) -> Optional[str]:
        """从Authorization头中提取令牌"""
        if not authorization_header:
            return None

        # Bearer token格式
        if authorization_header.startswith("Bearer "):
            return authorization_header[7:]

        # 直接token格式
        return authorization_header

    def validate_request(
        self,
        path: str,
        method: str,
        headers: Dict[str, str],
        required_permissions: List[tuple] = None,
    ) -> Dict[str, Any]:
        """
        验证请求

        Args:
            path: 请求路径
            method: HTTP方法
            headers: 请求头
            required_permissions: 需要的权限列表 [(resource, action), ...]

        Returns:
            Dict: 验证结果
        """
        # 检查是否为排除路径
        if self.is_excluded_path(path):
            return {"valid": True, "user": None, "message": "Public endpoint"}

        # 提取令牌
        auth_header = headers.get("Authorization", "")
        token = self.extract_token(auth_header)

        if not token:
            return {"valid": False, "error": "Missing authorization token", "code": 401}

        # 验证令牌
        user_info = self.auth_service.verify_token(token)
        if not user_info:
            return {"valid": False, "error": "Invalid or expired token", "code": 401}

        # 检查权限
        if required_permissions:
            user_id = user_info.get("user_id")
            for resource, action in required_permissions:
                if not self.rbac_manager.check_permission(user_id, resource, action):
                    return {
                        "valid": False,
                        "error": f"Insufficient permissions for {resource}:{action}",
                        "code": 403,
                    }

        return {
            "valid": True,
            "user": user_info,
            "message": "Authentication successful",
        }


class FlaskAuthMiddleware(AuthMiddleware):
    """Flask认证中间件"""

    def __init__(self, app=None, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        if app:
            self.init_app(app)

    def init_app(self, app):
        """初始化Flask应用"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)

    def before_request(self):
        """请求前处理"""
        from flask import request, g, jsonify

        # 获取请求信息
        path = request.path
        method = request.method
        headers = dict(request.headers)

        # 验证请求
        result = self.validate_request(path, method, headers)

        if not result["valid"]:
            return (
                jsonify({"error": result["error"], "code": result["code"]}),
                result["code"],
            )

        # 将用户信息存储到g对象
        g.current_user = result.get("user")

    def after_request(self, response):
        """请求后处理"""
        # 可以添加日志记录、清理等逻辑
        return response


class FastAPIAuthMiddleware:
    """FastAPI认证中间件"""

    def __init__(self, auth_middleware: AuthMiddleware):
        self.auth_middleware = auth_middleware

    async def __call__(self, request, call_next):
        """中间件处理函数"""
        # 获取请求信息
        path = str(request.url.path)
        method = request.method
        headers = dict(request.headers)

        # 验证请求
        result = self.auth_middleware.validate_request(path, method, headers)

        if not result["valid"]:
            from fastapi import HTTPException

            raise HTTPException(status_code=result["code"], detail=result["error"])

        # 将用户信息添加到request state
        request.state.current_user = result.get("user")

        # 继续处理请求
        response = await call_next(request)
        return response


# 装饰器函数
def require_auth(
    func: Callable = None,
    *,
    roles: List[str] = None,
    permissions: List[tuple] = None,
    allow_refresh_token: bool = False,
):
    """
    需要认证的装饰器

    Args:
        func: 被装饰的函数
        roles: 需要的角色列表
        permissions: 需要的权限列表 [(resource, action), ...]
        allow_refresh_token: 是否允许使用刷新令牌
    """

    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            # 尝试从不同来源获取令牌
            token = _extract_token_from_context(*args, **kwargs)

            if not token:
                return _auth_error("Missing authorization token", 401)

            # 验证令牌
            token_type = "refresh" if allow_refresh_token else "access"
            user_info = None

            if allow_refresh_token:
                # 尝试验证访问令牌，失败则尝试刷新令牌
                user_info = auth_service.verify_token(token)
                if not user_info:
                    payload = jwt_manager.verify_token(token, "refresh")
                    if payload:
                        user_id = payload.get("user_id")
                        user_info = auth_service.get_user_info(user_id)
            else:
                user_info = auth_service.verify_token(token)

            if not user_info:
                return _auth_error("Invalid or expired token", 401)

            # 检查角色
            if roles:
                user_roles = user_info.get("roles", [])
                if not any(role in user_roles for role in roles):
                    return _auth_error("Insufficient role permissions", 403)

            # 检查权限
            if permissions:
                user_id = user_info.get("user_id")
                for resource, action in permissions:
                    if not rbac_manager.check_permission(user_id, resource, action):
                        return _auth_error(
                            f"Insufficient permissions for {resource}:{action}", 403
                        )

            # 将用户信息添加到参数
            kwargs["current_user"] = user_info

            return f(*args, **kwargs)

        return wrapper

    if func is None:
        return decorator
    else:
        return decorator(func)


def require_roles(roles: Union[str, List[str]]):
    """需要特定角色的装饰器"""
    if isinstance(roles, str):
        roles = [roles]

    return require_auth(roles=roles)


def require_permissions(*permission_pairs):
    """
    需要特定权限的装饰器

    Args:
        *permission_pairs: 权限对 (resource, action)
    """
    return require_auth(permissions=list(permission_pairs))


def require_admin(func: Callable = None):
    """需要管理员权限的装饰器"""
    return require_auth(func, roles=["admin", "super_admin"])


def require_owner(resource_id_param: str = "id"):
    """
    需要资源所有者权限的装饰器

    Args:
        resource_id_param: 资源ID参数名
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取资源ID
            resource_id = kwargs.get(resource_id_param)
            if not resource_id:
                return _auth_error("Resource ID required", 400)

            # 获取当前用户
            current_user = kwargs.get("current_user")
            if not current_user:
                # 应用认证装饰器
                @require_auth
                def temp_func(*a, **kw):
                    return func(*a, **kw)

                return temp_func(*args, **kwargs)

            # 检查是否为资源所有者或管理员
            user_id = current_user.get("user_id")
            user_roles = current_user.get("roles", [])

            is_admin = any(role in ["admin", "super_admin"] for role in user_roles)
            is_owner = str(user_id) == str(resource_id)

            if not (is_admin or is_owner):
                return _auth_error("Access denied: not resource owner", 403)

            return func(*args, **kwargs)

        return wrapper

    return decorator


def optional_auth(func: Callable):
    """可选认证装饰器 - 有令牌则验证，无令牌则继续"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        token = _extract_token_from_context(*args, **kwargs)

        current_user = None
        if token:
            current_user = auth_service.verify_token(token)

        kwargs["current_user"] = current_user
        return func(*args, **kwargs)

    return wrapper


def rate_limit(max_requests: int = 100, window_minutes: int = 15):
    """
    速率限制装饰器

    Args:
        max_requests: 最大请求数
        window_minutes: 时间窗口（分钟）
    """

    def decorator(func):
        # 简单的内存存储（生产环境应使用Redis）
        if not hasattr(decorator, "requests"):
            decorator.requests = {}

        @wraps(func)
        def wrapper(*args, **kwargs):
            # 获取客户端标识（IP或用户ID）
            client_id = _get_client_id(*args, **kwargs)

            now = datetime.utcnow()
            window_start = now - timedelta(minutes=window_minutes)

            # 清理过期记录
            if client_id in decorator.requests:
                decorator.requests[client_id] = [
                    req_time
                    for req_time in decorator.requests[client_id]
                    if req_time > window_start
                ]

            # 检查请求数量
            client_requests = decorator.requests.get(client_id, [])
            if len(client_requests) >= max_requests:
                return _auth_error("Rate limit exceeded", 429)

            # 记录请求
            if client_id not in decorator.requests:
                decorator.requests[client_id] = []
            decorator.requests[client_id].append(now)

            return func(*args, **kwargs)

        return wrapper

    return decorator


# 辅助函数
def _extract_token_from_context(*args, **kwargs) -> Optional[str]:
    """从上下文中提取令牌"""
    # 从kwargs中获取
    token = kwargs.get("token") or kwargs.get("authorization")

    if token:
        return token

    # 从Flask请求中获取
    try:
        from flask import request

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            return auth_header[7:]
    except (ImportError, RuntimeError):
        pass

    # 从FastAPI请求中获取
    if args:
        arg = args[0]
        if hasattr(arg, "headers"):
            auth_header = arg.headers.get("authorization", "")
            if auth_header.startswith("Bearer "):
                return auth_header[7:]

    return None


def _get_client_id(*args, **kwargs) -> str:
    """获取客户端标识"""
    # 优先使用用户ID
    current_user = kwargs.get("current_user")
    if current_user and current_user.get("user_id"):
        return f"user_{current_user['user_id']}"

    # 使用IP地址
    try:
        from flask import request

        return f"ip_{request.remote_addr}"
    except (ImportError, RuntimeError):
        pass

    # 默认标识
    return "unknown_client"


def _auth_error(message: str, code: int) -> Dict[str, Any]:
    """返回认证错误"""
    return {"error": message, "code": code, "timestamp": datetime.utcnow().isoformat()}


# 权限检查函数
def check_permission(
    user_id: int, resource: str, action: str, context: Dict[str, Any] = None
) -> bool:
    """检查用户权限"""
    return rbac_manager.check_permission(user_id, resource, action, context)


def check_role(user_info: Dict[str, Any], required_roles: List[str]) -> bool:
    """检查用户角色"""
    user_roles = user_info.get("roles", [])
    return any(role in user_roles for role in required_roles)


def get_current_user_from_token(token: str) -> Optional[Dict[str, Any]]:
    """从令牌获取当前用户信息"""
    return auth_service.verify_token(token)


class TokenValidator:
    """令牌验证器"""

    @staticmethod
    def validate_access_token(token: str) -> Optional[Dict[str, Any]]:
        """验证访问令牌"""
        return jwt_manager.verify_token(token, "access")

    @staticmethod
    def validate_refresh_token(token: str) -> Optional[Dict[str, Any]]:
        """验证刷新令牌"""
        return jwt_manager.verify_token(token, "refresh")

    @staticmethod
    def is_token_blacklisted(token: str) -> bool:
        """检查令牌是否在黑名单中"""
        return token_blacklist.is_blacklisted(token)

    @staticmethod
    def get_token_info(token: str) -> Dict[str, Any]:
        """获取令牌信息"""
        return jwt_manager.get_token_info(token)


# 安全工具类
class SecurityUtils:
    """安全工具类"""

    @staticmethod
    def log_security_event(
        event_type: str, user_id: int = None, details: Dict[str, Any] = None
    ):
        """记录安全事件"""
        # 简单的日志记录（生产环境应使用专业的安全日志系统）
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "details": details or {},
        }
        print(f"SECURITY_EVENT: {log_entry}")

    @staticmethod
    def detect_suspicious_activity(user_id: int, activity_type: str) -> bool:
        """检测可疑活动"""
        # 简单的可疑活动检测逻辑
        # 生产环境应实现更复杂的检测算法
        return False

    @staticmethod
    def get_client_info(request=None) -> Dict[str, Any]:
        """获取客户端信息"""
        client_info = {
            "ip_address": "unknown",
            "user_agent": "unknown",
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            from flask import request as flask_request

            if flask_request:
                client_info.update(
                    {
                        "ip_address": flask_request.remote_addr,
                        "user_agent": flask_request.user_agent.string,
                    }
                )
        except (ImportError, RuntimeError):
            pass

        return client_info
