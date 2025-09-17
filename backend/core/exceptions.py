#!/usr/bin/env python3
"""
自定义异常类
定义业务逻辑相关的异常
"""

from typing import Optional, Dict, Any

class BaseAppException(Exception):
    """应用程序基础异常"""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'error': self.code,
            'message': self.message,
            'details': self.details
        }

# === 认证相关异常 ===

class AuthenticationError(BaseAppException):
    """认证失败异常"""
    pass

class AuthorizationError(BaseAppException):
    """授权失败异常"""
    pass

class TokenExpiredError(AuthenticationError):
    """令牌过期异常"""

    def __init__(self, message: str = "令牌已过期"):
        super().__init__(message, "TOKEN_EXPIRED")

class TokenInvalidError(AuthenticationError):
    """令牌无效异常"""

    def __init__(self, message: str = "无效的令牌"):
        super().__init__(message, "TOKEN_INVALID")

class AccountLockedException(AuthenticationError):
    """账户锁定异常"""

    def __init__(self, message: str = "账户已被锁定"):
        super().__init__(message, "ACCOUNT_LOCKED")

class PasswordTooWeakError(AuthenticationError):
    """密码太弱异常"""

    def __init__(self, message: str = "密码强度不足"):
        super().__init__(message, "PASSWORD_TOO_WEAK")

# === 用户相关异常 ===

class UserNotFoundError(BaseAppException):
    """用户不存在异常"""

    def __init__(self, message: str = "用户不存在"):
        super().__init__(message, "USER_NOT_FOUND")

class UserAlreadyExistsError(BaseAppException):
    """用户已存在异常"""

    def __init__(self, message: str = "用户已存在"):
        super().__init__(message, "USER_ALREADY_EXISTS")

class UserInactiveError(BaseAppException):
    """用户未激活异常"""

    def __init__(self, message: str = "用户账户未激活"):
        super().__init__(message, "USER_INACTIVE")

# === 验证相关异常 ===

class ValidationError(BaseAppException):
    """数据验证异常"""

    def __init__(self, message: str, field: Optional[str] = None):
        details = {'field': field} if field else {}
        super().__init__(message, "VALIDATION_ERROR", details)

class InvalidInputError(ValidationError):
    """无效输入异常"""

    def __init__(self, message: str = "无效的输入数据"):
        super().__init__(message)

# === 数据库相关异常 ===

class DatabaseError(BaseAppException):
    """数据库操作异常"""

    def __init__(self, message: str = "数据库操作失败"):
        super().__init__(message, "DATABASE_ERROR")

class DatabaseConnectionError(DatabaseError):
    """数据库连接异常"""

    def __init__(self, message: str = "数据库连接失败"):
        super().__init__(message, "DATABASE_CONNECTION_ERROR")

class DatabaseIntegrityError(DatabaseError):
    """数据库完整性异常"""

    def __init__(self, message: str = "数据完整性约束违反"):
        super().__init__(message, "DATABASE_INTEGRITY_ERROR")

# === 业务逻辑异常 ===

class BusinessLogicError(BaseAppException):
    """业务逻辑异常"""
    pass

class ResourceNotFoundError(BusinessLogicError):
    """资源不存在异常"""

    def __init__(self, message: str = "请求的资源不存在"):
        super().__init__(message, "RESOURCE_NOT_FOUND")

class ResourceConflictError(BusinessLogicError):
    """资源冲突异常"""

    def __init__(self, message: str = "资源冲突"):
        super().__init__(message, "RESOURCE_CONFLICT")

class PermissionDeniedError(BusinessLogicError):
    """权限不足异常"""

    def __init__(self, message: str = "权限不足"):
        super().__init__(message, "PERMISSION_DENIED")

# === 外部服务异常 ===

class ExternalServiceError(BaseAppException):
    """外部服务异常"""

    def __init__(self, message: str = "外部服务错误", service: Optional[str] = None):
        details = {'service': service} if service else {}
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", details)

class EmailServiceError(ExternalServiceError):
    """邮件服务异常"""

    def __init__(self, message: str = "邮件发送失败"):
        super().__init__(message, "EMAIL_SERVICE_ERROR")

class RedisServiceError(ExternalServiceError):
    """Redis服务异常"""

    def __init__(self, message: str = "Redis服务错误"):
        super().__init__(message, "REDIS_SERVICE_ERROR")

# === 配置相关异常 ===

class ConfigurationError(BaseAppException):
    """配置错误异常"""

    def __init__(self, message: str = "配置错误"):
        super().__init__(message, "CONFIGURATION_ERROR")

class MissingConfigurationError(ConfigurationError):
    """缺少配置异常"""

    def __init__(self, config_key: str):
        message = f"缺少必要的配置项: {config_key}"
        super().__init__(message, "MISSING_CONFIGURATION")

# === 速率限制异常 ===

class RateLimitExceededError(BaseAppException):
    """速率限制超出异常"""

    def __init__(self, message: str = "请求频率过高，请稍后再试"):
        super().__init__(message, "RATE_LIMIT_EXCEEDED")

# === 文件相关异常 ===

class FileError(BaseAppException):
    """文件操作异常"""

    def __init__(self, message: str = "文件操作失败"):
        super().__init__(message, "FILE_ERROR")

class FileNotFoundError(FileError):
    """文件不存在异常"""

    def __init__(self, filename: str):
        message = f"文件不存在: {filename}"
        super().__init__(message, "FILE_NOT_FOUND")

class FileTooLargeError(FileError):
    """文件过大异常"""

    def __init__(self, message: str = "文件大小超出限制"):
        super().__init__(message, "FILE_TOO_LARGE")

class InvalidFileTypeError(FileError):
    """无效文件类型异常"""

    def __init__(self, message: str = "不支持的文件类型"):
        super().__init__(message, "INVALID_FILE_TYPE")

# === 网络相关异常 ===

class NetworkError(BaseAppException):
    """网络错误异常"""

    def __init__(self, message: str = "网络错误"):
        super().__init__(message, "NETWORK_ERROR")

class TimeoutError(NetworkError):
    """超时异常"""

    def __init__(self, message: str = "操作超时"):
        super().__init__(message, "TIMEOUT_ERROR")

# 异常映射表（用于HTTP状态码映射）
EXCEPTION_STATUS_MAP = {
    AuthenticationError: 401,
    AuthorizationError: 403,
    TokenExpiredError: 401,
    TokenInvalidError: 401,
    AccountLockedException: 423,
    PasswordTooWeakError: 400,
    UserNotFoundError: 404,
    UserAlreadyExistsError: 409,
    UserInactiveError: 403,
    ValidationError: 400,
    InvalidInputError: 400,
    DatabaseError: 500,
    DatabaseConnectionError: 503,
    DatabaseIntegrityError: 409,
    BusinessLogicError: 400,
    ResourceNotFoundError: 404,
    ResourceConflictError: 409,
    PermissionDeniedError: 403,
    ExternalServiceError: 502,
    EmailServiceError: 502,
    RedisServiceError: 502,
    ConfigurationError: 500,
    MissingConfigurationError: 500,
    RateLimitExceededError: 429,
    FileError: 500,
    FileNotFoundError: 404,
    FileTooLargeError: 413,
    InvalidFileTypeError: 415,
    NetworkError: 502,
    TimeoutError: 504,
}

def get_http_status_code(exception: BaseAppException) -> int:
    """获取异常对应的HTTP状态码"""
    return EXCEPTION_STATUS_MAP.get(type(exception), 500)