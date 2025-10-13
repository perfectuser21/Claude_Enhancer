"""
Claude Enhancer 认证API依赖注入
提供认证和授权相关的依赖项
"""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
import logging
from datetime import datetime

# 导入服务层
from backend.core.security import JWTSecurityHandler
from backend.core.services import UserService, JWTTokenManager, MFAService
from backend.core.models import User

logger = logging.getLogger(__name__)

# 安全认证依赖
security = HTTPBearer(auto_error=False)
jwt_handler = JWTSecurityHandler()


async def get_client_info(request: Request) -> Dict[str, Any]:
    """
    获取客户端信息

    Args:
        request: FastAPI请求对象

    Returns:
        包含客户端信息的字典
    """
    return {
        "ip_address": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", ""),
        "real_ip": request.headers.get(
            "x-real-ip", request.client.host if request.client else "unknown"
        ),
        "forwarded_for": request.headers.get("x-forwarded-for", ""),
        "device_info": {
            "user_agent": request.headers.get("user-agent", ""),
            "accept_language": request.headers.get("accept-language", ""),
            "accept_encoding": request.headers.get("accept-encoding", ""),
            "origin": request.headers.get("origin", ""),
            "referer": request.headers.get("referer", ""),
        },
        "request_id": request.headers.get(
            "x-request-id", f"req-{datetime.utcnow().timestamp()}"
        ),
    }


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    jwt_manager: JWTTokenManager = Depends(),
    user_service: UserService = Depends(),
) -> User:
    """
    获取当前认证用户

    Args:
        credentials: JWT认证凭据
        jwt_manager: JWT管理器
        user_service: 用户服务

    Returns:
        当前用户对象

    Raises:
        HTTPException: 认证失败时抛出
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        pass  # Auto-fixed empty block
        # 验证JWT令牌
        validation_result = await jwt_manager.validate_token(credentials.credentials)

        if not validation_result.valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 获取用户信息
        user = await user_service.get_user_by_id(validation_result.claims.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 检查用户状态
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"用户账户状态异常: {user.status}",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # 将令牌声明信息附加到用户对象（用于权限检查）
        user._token_claims = validation_result.claims

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户认证失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证服务暂时不可用",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    获取当前活跃用户（已验证邮箱）

    Args:
        current_user: 当前用户

    Returns:
        当前活跃用户对象

    Raises:
        HTTPException: 用户未激活时抛出
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="用户邮箱未验证，请先验证邮箱"
        )

    return current_user


async def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    jwt_manager: JWTTokenManager = Depends(),
    user_service: UserService = Depends(),
) -> Optional[User]:
    """
    获取可选的当前用户（不强制要求认证）

    Args:
        credentials: JWT认证凭据
        jwt_manager: JWT管理器
        user_service: 用户服务

    Returns:
        当前用户对象或None
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, jwt_manager, user_service)
    except HTTPException:
        return None


def require_permissions(*required_permissions: str):
    """
    权限检查装饰器工厂

    Args:
        *required_permissions: 需要的权限列表

    Returns:
        权限检查依赖函数
    """

    async def permission_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        """检查用户权限"""
        if not hasattr(current_user, "_token_claims"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="缺少权限信息")

        user_permissions = set(current_user._token_claims.permissions)
        required_perms = set(required_permissions)

        # 检查是否具有所有必需权限
        if not required_perms.issubset(user_permissions):
            missing_perms = required_perms - user_permissions
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"缺少必要权限: {', '.join(missing_perms)}",
            )

        return current_user

    return permission_checker


def require_any_permission(*required_permissions: str):
    """
    任一权限检查装饰器工厂

    Args:
        *required_permissions: 需要的权限列表（满足任一即可）

    Returns:
        权限检查依赖函数
    """

    async def permission_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        """检查用户是否具有任一权限"""
        if not hasattr(current_user, "_token_claims"):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="缺少权限信息")

        user_permissions = set(current_user._token_claims.permissions)
        required_perms = set(required_permissions)

        # 检查是否具有任一权限
        if not user_permissions.intersection(required_perms):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要以下任一权限: {', '.join(required_permissions)}",
            )

        return current_user

    return permission_checker


def require_admin():
    """
    管理员权限检查

    Returns:
        管理员权限检查依赖函数
    """
    return require_permissions("admin:all", "admin:read", "admin:write")


async def rate_limit_check(
    request: Request, client_info: Dict[str, Any] = Depends(get_client_info)
) -> bool:
    """
    速率限制检查

    Args:
        request: FastAPI请求对象
        client_info: 客户端信息

    Returns:
        是否通过速率限制检查

    Raises:
        HTTPException: 超过速率限制时抛出
    """
    # TODO: 实现基于Redis的速率限制
    # 这里简化实现，实际应该使用Redis计数器

    endpoint = request.url.path
    method = request.method
    client_ip = client_info["ip_address"]

    # 不同端点的限制策略
    limits = {
        "/auth/login": {"requests": 5, "window": 300},  # 5次/5分钟
        "/auth/register": {"requests": 3, "window": 3600},  # 3次/小时
        "/auth/refresh": {"requests": 10, "window": 300},  # 10次/5分钟
        "default": {"requests": 100, "window": 3600},  # 默认100次/小时
    }

    # 获取限制配置
    limit_config = limits.get(endpoint, limits["default"])

    # TODO: 使用Redis实现实际的速率限制逻辑
    # 现在暂时返回True（通过检查）

    return True


async def security_headers_middleware(request: Request, call_next):
    """
    安全头中间件

    Args:
        request: FastAPI请求对象
        call_next: 下一个中间件

    Returns:
        添加了安全头的响应
    """
    response = await call_next(request)

    # 添加安全头
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers[
        "Strict-Transport-Security"
    ] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'"

    return response


# 服务依赖注入
async def get_user_service() -> UserService:
    """获取用户服务实例"""
    # TODO: 实现实际的服务获取逻辑
    # 这里应该从应用状态或依赖注入容器中获取
    return UserService()


async def get_jwt_manager() -> JWTTokenManager:
    """获取JWT管理器实例"""
    # TODO: 实现实际的服务获取逻辑
    return JWTTokenManager()


async def get_mfa_service() -> MFAService:
    """获取MFA服务实例"""
    # TODO: 实现实际的服务获取逻辑
    return MFAService()


# 验证辅助函数
def validate_email_domain(email: str, allowed_domains: Optional[list] = None) -> bool:
    """
    验证邮箱域名

    Args:
        email: 邮箱地址
        allowed_domains: 允许的域名列表

    Returns:
        是否为允许的域名
    """
    if not allowed_domains:
        return True

    domain = email.split("@")[1].lower()
    return domain in [d.lower() for d in allowed_domains]


def validate_password_history(user_id: str, new_password: str) -> bool:
    """
    验证密码历史（确保不重复使用最近的密码）

    Args:
        user_id: 用户ID
        new_password: 新密码

    Returns:
        是否通过历史密码检查
    """
    # TODO: 实现密码历史检查逻辑
    # 检查用户最近N个密码，确保新密码不在历史记录中
    return True


async def validate_device_trust(
    user_id: str, device_fingerprint: str, client_info: Dict[str, Any]
) -> bool:
    """
    验证设备信任状态

    Args:
        user_id: 用户ID
        device_fingerprint: 设备指纹
        client_info: 客户端信息

    Returns:
        设备是否受信任
    """
    # TODO: 实现设备信任验证逻辑
    # 检查设备是否在用户的信任设备列表中
    return False


# 错误处理辅助函数
def create_auth_error(
    error_code: str, message: str, details: Optional[Dict[str, Any]] = None
) -> HTTPException:
    """
    创建认证错误响应

    Args:
        error_code: 错误代码
        message: 错误消息
        details: 错误详情

    Returns:
        HTTP异常对象
    """
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "error": error_code,
            "message": message,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat(),
        },
        headers={"WWW-Authenticate": "Bearer"},
    )


def create_permission_error(
    required_permissions: list, user_permissions: list
) -> HTTPException:
    """
    创建权限错误响应

    Args:
        required_permissions: 需要的权限
        user_permissions: 用户拥有的权限

    Returns:
        HTTP异常对象
    """
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={
            "error": "INSUFFICIENT_PERMISSIONS",
            "message": "权限不足",
            "details": {"required": required_permissions, "current": user_permissions},
            "timestamp": datetime.utcnow().isoformat(),
        },
    )
