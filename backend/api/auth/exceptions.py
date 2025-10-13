"""
Claude Enhancer 认证API异常定义
定义认证相关的自定义异常类
"""

from typing import Dict, Any, Optional
from fastapi import HTTPException, status


class AuthException(Exception):
    """认证异常基类"""

    def __init__(
        self,
        message: str,
        error_code: str = "AUTH_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class InvalidCredentialsException(AuthException):
    """无效凭据异常"""

    def __init__(self, message: str = "无效的用户名或密码"):
        super().__init__(message=message, error_code="INVALID_CREDENTIALS")


class AccountLockedException(AuthException):
    """账户锁定异常"""

    def __init__(self, message: str = "账户已被锁定", lock_duration: Optional[int] = None):
        details = {}
        if lock_duration:
            details["lock_duration_minutes"] = lock_duration

        super().__init__(message=message, error_code="ACCOUNT_LOCKED", details=details)


class AccountDisabledException(AuthException):
    """账户禁用异常"""

    def __init__(self, message: str = "账户已被禁用"):
        super().__init__(message=message, error_code="ACCOUNT_DISABLED")


class EmailNotVerifiedException(AuthException):
    """邮箱未验证异常"""

    def __init__(self, message: str = "邮箱地址未验证"):
        super().__init__(message=message, error_code="EMAIL_NOT_VERIFIED")


class MFARequiredException(AuthException):
    """需要MFA验证异常"""

    def __init__(self, message: str = "需要多因子认证", mfa_token: Optional[str] = None):
        details = {}
        if mfa_token:
            details["mfa_token"] = mfa_token

        super().__init__(message=message, error_code="MFA_REQUIRED", details=details)


class InvalidMFACodeException(AuthException):
    """无效MFA验证码异常"""

    def __init__(
        self, message: str = "无效的验证码", attempts_remaining: Optional[int] = None
    ):
        details = {}
        if attempts_remaining is not None:
            details["attempts_remaining"] = attempts_remaining

        super().__init__(
            message=message, error_code="INVALID_MFA_CODE", details=details
        )


class MFACodeExpiredException(AuthException):
    """MFA验证码过期异常"""

    def __init__(self, message: str = "验证码已过期"):
        super().__init__(message=message, error_code="MFA_CODE_EXPIRED")


class InvalidTokenException(AuthException):
    """无效Token异常"""

    def __init__(self, message: str = "无效或已过期的令牌", token_type: str = "access_token"):
        super().__init__(
            message=message,
            error_code="INVALID_TOKEN",
            details={"token_type": token_type},
        )


class TokenExpiredException(AuthException):
    """Token过期异常"""

    def __init__(self, message: str = "令牌已过期", token_type: str = "access_token"):
        super().__init__(
            message=message,
            error_code="TOKEN_EXPIRED",
            details={"token_type": token_type},
        )


class TokenRevokedException(AuthException):
    """Token已撤销异常"""

    def __init__(self, message: str = "令牌已被撤销", reason: Optional[str] = None):
        details = {}
        if reason:
            details["revocation_reason"] = reason

        super().__init__(message=message, error_code="TOKEN_REVOKED", details=details)


class InsufficientPermissionsException(AuthException):
    """权限不足异常"""

    def __init__(
        self,
        message: str = "权限不足",
        required_permissions: Optional[list] = None,
        current_permissions: Optional[list] = None,
    ):
        details = {}
        if required_permissions:
            details["required_permissions"] = required_permissions
        if current_permissions:
            details["current_permissions"] = current_permissions

        super().__init__(
            message=message, error_code="INSUFFICIENT_PERMISSIONS", details=details
        )


class UserAlreadyExistsException(AuthException):
    """用户已存在异常"""

    def __init__(self, message: str = "用户已存在", existing_field: str = "email"):
        super().__init__(
            message=message,
            error_code="USER_ALREADY_EXISTS",
            details={"existing_field": existing_field},
        )


class UserNotFoundException(AuthException):
    """用户不存在异常"""

    def __init__(self, message: str = "用户不存在"):
        super().__init__(message=message, error_code="USER_NOT_FOUND")


class WeakPasswordException(AuthException):
    """弱密码异常"""

    def __init__(
        self, message: str = "密码强度不足", password_requirements: Optional[list] = None
    ):
        details = {}
        if password_requirements:
            details["requirements"] = password_requirements

        super().__init__(message=message, error_code="WEAK_PASSWORD", details=details)


class PasswordHistoryException(AuthException):
    """密码历史冲突异常"""

    def __init__(self, message: str = "不能使用最近使用过的密码"):
        super().__init__(message=message, error_code="PASSWORD_HISTORY_CONFLICT")


class RateLimitExceededException(AuthException):
    """速率限制超出异常"""

    def __init__(
        self,
        message: str = "请求过于频繁，请稍后再试",
        retry_after: Optional[int] = None,
        limit: Optional[int] = None,
    ):
        details = {}
        if retry_after:
            details["retry_after_seconds"] = retry_after
        if limit:
            details["rate_limit"] = limit

        super().__init__(
            message=message, error_code="RATE_LIMIT_EXCEEDED", details=details
        )


class SuspiciousActivityException(AuthException):
    """可疑活动异常"""

    def __init__(
        self, message: str = "检测到可疑活动，账户已被临时限制", risk_factors: Optional[list] = None
    ):
        details = {}
        if risk_factors:
            details["risk_factors"] = risk_factors

        super().__init__(
            message=message, error_code="SUSPICIOUS_ACTIVITY", details=details
        )


class DeviceNotTrustedException(AuthException):
    """设备不受信任异常"""

    def __init__(self, message: str = "设备未受信任，需要额外验证"):
        super().__init__(message=message, error_code="DEVICE_NOT_TRUSTED")


class SessionExpiredException(AuthException):
    """会话过期异常"""

    def __init__(self, message: str = "会话已过期，请重新登录"):
        super().__init__(message=message, error_code="SESSION_EXPIRED")


class ConcurrentSessionException(AuthException):
    """并发会话异常"""

    def __init__(
        self, message: str = "检测到并发会话，请重新认证", max_sessions: Optional[int] = None
    ):
        details = {}
        if max_sessions:
            details["max_allowed_sessions"] = max_sessions

        super().__init__(
            message=message, error_code="CONCURRENT_SESSION_LIMIT", details=details
        )


# HTTP异常转换器
def auth_exception_to_http_exception(exc: AuthException) -> HTTPException:
    """
    将认证异常转换为HTTP异常

    Args:
        exc: 认证异常

    Returns:
        HTTP异常
    """
    # 映射错误代码到HTTP状态码
    status_code_mapping = {
        "INVALID_CREDENTIALS": status.HTTP_401_UNAUTHORIZED,
        "ACCOUNT_LOCKED": status.HTTP_423_LOCKED,
        "ACCOUNT_DISABLED": status.HTTP_403_FORBIDDEN,
        "EMAIL_NOT_VERIFIED": status.HTTP_403_FORBIDDEN,
        "MFA_REQUIRED": status.HTTP_202_ACCEPTED,
        "INVALID_MFA_CODE": status.HTTP_401_UNAUTHORIZED,
        "MFA_CODE_EXPIRED": status.HTTP_401_UNAUTHORIZED,
        "INVALID_TOKEN": status.HTTP_401_UNAUTHORIZED,
        "TOKEN_EXPIRED": status.HTTP_401_UNAUTHORIZED,
        "TOKEN_REVOKED": status.HTTP_401_UNAUTHORIZED,
        "INSUFFICIENT_PERMISSIONS": status.HTTP_403_FORBIDDEN,
        "USER_ALREADY_EXISTS": status.HTTP_409_CONFLICT,
        "USER_NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "WEAK_PASSWORD": status.HTTP_400_BAD_REQUEST,
        "PASSWORD_HISTORY_CONFLICT": status.HTTP_400_BAD_REQUEST,
        "RATE_LIMIT_EXCEEDED": status.HTTP_429_TOO_MANY_REQUESTS,
        "SUSPICIOUS_ACTIVITY": status.HTTP_403_FORBIDDEN,
        "DEVICE_NOT_TRUSTED": status.HTTP_403_FORBIDDEN,
        "SESSION_EXPIRED": status.HTTP_401_UNAUTHORIZED,
        "CONCURRENT_SESSION_LIMIT": status.HTTP_409_CONFLICT,
    }

    status_code = status_code_mapping.get(
        exc.error_code, status.HTTP_500_INTERNAL_SERVER_ERROR
    )

    # 构建错误响应
    detail = {
        "success": False,
        "error": exc.error_code,
        "message": exc.message,
        "details": exc.details,
    }

    # 添加特殊头部
    headers = {}
    if exc.error_code in ["INVALID_TOKEN", "TOKEN_EXPIRED", "TOKEN_REVOKED"]:
        headers["WWW-Authenticate"] = "Bearer"
    elif exc.error_code == "RATE_LIMIT_EXCEEDED":
        if "retry_after_seconds" in exc.details:
            headers["Retry-After"] = str(exc.details["retry_after_seconds"])

    return HTTPException(
        status_code=status_code, detail=detail, headers=headers if headers else None
    )


# 装饰器：自动转换认证异常
def handle_auth_exceptions(func):
    """
    装饰器：自动捕获并转换认证异常为HTTP异常
    """

    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except AuthException as e:
            raise auth_exception_to_http_exception(e)
        except Exception:
            pass  # Auto-fixed empty block
            # 重新抛出非认证异常
            raise

    return wrapper


# 自定义错误代码常量
class ErrorCodes:
    """错误代码常量"""

    # 认证相关
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    ACCOUNT_DISABLED = "ACCOUNT_DISABLED"
    EMAIL_NOT_VERIFIED = "EMAIL_NOT_VERIFIED"

    # MFA相关
    MFA_REQUIRED = "MFA_REQUIRED"
    INVALID_MFA_CODE = "INVALID_MFA_CODE"
    MFA_CODE_EXPIRED = "MFA_CODE_EXPIRED"
    MFA_SETUP_REQUIRED = "MFA_SETUP_REQUIRED"

    # Token相关
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_REVOKED = "TOKEN_REVOKED"

    # 权限相关
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"

    # 用户管理
    USER_ALREADY_EXISTS = "USER_ALREADY_EXISTS"
    USER_NOT_FOUND = "USER_NOT_FOUND"

    # 密码相关
    WEAK_PASSWORD = "WEAK_PASSWORD"
    PASSWORD_HISTORY_CONFLICT = "PASSWORD_HISTORY_CONFLICT"

    # 速率限制
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # 安全相关
    SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"
    DEVICE_NOT_TRUSTED = "DEVICE_NOT_TRUSTED"

    # 会话相关
    SESSION_EXPIRED = "SESSION_EXPIRED"
    CONCURRENT_SESSION_LIMIT = "CONCURRENT_SESSION_LIMIT"
