"""
DocGate Agent API异常处理
定义DocGate系统的自定义异常和统一异常处理器
"""

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, Union
import logging
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


# =============== 异常代码枚举 ===============

class DocGateErrorCode(str, Enum):
    """DocGate错误代码"""

    # 验证错误 (400)
    INVALID_DOCUMENT_PATH = "DOC_VAL_001"
    INVALID_CONFIG_FORMAT = "DOC_VAL_002"
    UNSUPPORTED_DOCUMENT_TYPE = "DOC_VAL_003"
    BATCH_SIZE_EXCEEDED = "DOC_VAL_004"
    INVALID_WEBHOOK_URL = "DOC_VAL_005"
    INVALID_DATE_RANGE = "DOC_VAL_006"

    # 认证错误 (401)
    INVALID_ACCESS_TOKEN = "AUT_AUT_001"
    EXPIRED_ACCESS_TOKEN = "AUT_AUT_002"

    # 权限错误 (403)
    INSUFFICIENT_READ_PERMISSION = "DOC_FOR_001"
    INSUFFICIENT_WRITE_PERMISSION = "DOC_FOR_002"
    INSUFFICIENT_CONFIG_PERMISSION = "DOC_FOR_003"
    INSUFFICIENT_WEBHOOK_PERMISSION = "DOC_FOR_004"
    INSUFFICIENT_ADMIN_PERMISSION = "DOC_FOR_005"

    # 资源不存在 (404)
    DOCUMENT_NOT_FOUND = "DOC_NOT_001"
    CHECK_TASK_NOT_FOUND = "DOC_NOT_002"
    CONFIG_NOT_FOUND = "DOC_NOT_003"
    WEBHOOK_NOT_FOUND = "DOC_NOT_004"
    REPORT_NOT_FOUND = "DOC_NOT_005"

    # 冲突错误 (409)
    CHECK_TASK_IN_PROGRESS = "DOC_CON_001"
    CONFIG_NAME_EXISTS = "DOC_CON_002"
    WEBHOOK_URL_EXISTS = "DOC_CON_003"

    # 请求过大 (413)
    DOCUMENT_TOO_LARGE = "DOC_PAY_001"
    BATCH_TOO_LARGE = "DOC_PAY_002"

    # 频率限制 (429)
    QUALITY_CHECK_RATE_LIMIT = "DOC_RAT_001"
    BATCH_CHECK_RATE_LIMIT = "DOC_RAT_002"
    WEBHOOK_RATE_LIMIT = "DOC_RAT_003"
    REPORT_DOWNLOAD_RATE_LIMIT = "DOC_RAT_004"

    # 服务器错误 (500)
    DOCUMENT_PARSE_FAILED = "DOC_SER_001"
    QUALITY_CHECK_FAILED = "DOC_SER_002"
    REPORT_GENERATION_FAILED = "DOC_SER_003"
    SERVICE_UNAVAILABLE = "DOC_SER_004"
    WEBHOOK_DELIVERY_FAILED = "DOC_SER_005"
    DATABASE_ERROR = "DOC_SER_006"
    CACHE_ERROR = "DOC_SER_007"

    # 外部服务错误 (502)
    GIT_SERVICE_ERROR = "DOC_EXT_001"
    WEBHOOK_SERVICE_ERROR = "DOC_EXT_002"
    STORAGE_SERVICE_ERROR = "DOC_EXT_003"

    # 服务超时 (504)
    CHECK_TIMEOUT = "DOC_TIM_001"
    WEBHOOK_TIMEOUT = "DOC_TIM_002"
    DATABASE_TIMEOUT = "DOC_TIM_003"


# =============== 自定义异常类 ===============

class DocGateException(Exception):
    """DocGate基础异常"""

    def __init__(
        self,
        message: str,
        error_code: DocGateErrorCode,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.headers = headers or {}
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "code": self.error_code.value,
            "type": self._get_error_type(),
            "message": self.message,
            "details": self.details,
        }

    def _get_error_type(self) -> str:
        """根据状态码获取错误类型"""
        if self.status_code == 400:
            return "VALIDATION_ERROR"
        elif self.status_code == 401:
            return "AUTHENTICATION_ERROR"
        elif self.status_code == 403:
            return "AUTHORIZATION_ERROR"
        elif self.status_code == 404:
            return "NOT_FOUND_ERROR"
        elif self.status_code == 409:
            return "CONFLICT_ERROR"
        elif self.status_code == 413:
            return "PAYLOAD_TOO_LARGE_ERROR"
        elif self.status_code == 429:
            return "RATE_LIMIT_ERROR"
        elif self.status_code == 500:
            return "INTERNAL_SERVER_ERROR"
        elif self.status_code == 502:
            return "BAD_GATEWAY_ERROR"
        elif self.status_code == 503:
            return "SERVICE_UNAVAILABLE_ERROR"
        elif self.status_code == 504:
            return "GATEWAY_TIMEOUT_ERROR"
        else:
            return "UNKNOWN_ERROR"


class ValidationError(DocGateException):
    """验证错误"""

    def __init__(
        self,
        message: str,
        error_code: DocGateErrorCode,
        field: Optional[str] = None,
        constraint: Optional[str] = None,
    ):
        details = {}
        if field:
            details["field"] = field
        if constraint:
            details["constraint"] = constraint

        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )


class AuthenticationError(DocGateException):
    """认证错误"""

    def __init__(self, message: str, error_code: DocGateErrorCode):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class AuthorizationError(DocGateException):
    """授权错误"""

    def __init__(self, message: str, error_code: DocGateErrorCode, required_permission: Optional[str] = None):
        details = {}
        if required_permission:
            details["required_permission"] = required_permission

        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class NotFoundError(DocGateException):
    """资源不存在错误"""

    def __init__(self, message: str, error_code: DocGateErrorCode, resource_type: Optional[str] = None, resource_id: Optional[str] = None):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id

        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class ConflictError(DocGateException):
    """冲突错误"""

    def __init__(self, message: str, error_code: DocGateErrorCode, conflict_field: Optional[str] = None):
        details = {}
        if conflict_field:
            details["conflict_field"] = conflict_field

        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class PayloadTooLargeError(DocGateException):
    """负载过大错误"""

    def __init__(self, message: str, error_code: DocGateErrorCode, max_size: Optional[int] = None, actual_size: Optional[int] = None):
        details = {}
        if max_size:
            details["max_size"] = max_size
        if actual_size:
            details["actual_size"] = actual_size

        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            details=details,
        )


class RateLimitError(DocGateException):
    """频率限制错误"""

    def __init__(
        self,
        message: str,
        error_code: DocGateErrorCode,
        limit: Optional[int] = None,
        remaining: Optional[int] = None,
        reset_time: Optional[int] = None,
    ):
        details = {}
        if limit:
            details["limit"] = limit
        if remaining is not None:
            details["remaining"] = remaining
        if reset_time:
            details["reset_time"] = reset_time

        headers = {}
        if limit:
            headers["X-RateLimit-Limit"] = str(limit)
        if remaining is not None:
            headers["X-RateLimit-Remaining"] = str(remaining)
        if reset_time:
            headers["X-RateLimit-Reset"] = str(reset_time)
            headers["Retry-After"] = str(reset_time - int(datetime.utcnow().timestamp()))

        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details,
            headers=headers,
        )


class ServiceError(DocGateException):
    """服务错误"""

    def __init__(
        self,
        message: str,
        error_code: DocGateErrorCode,
        service_name: Optional[str] = None,
        internal_error: Optional[str] = None,
    ):
        details = {}
        if service_name:
            details["service_name"] = service_name
        if internal_error:
            details["internal_error"] = internal_error

        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class ExternalServiceError(DocGateException):
    """外部服务错误"""

    def __init__(
        self,
        message: str,
        error_code: DocGateErrorCode,
        service_name: Optional[str] = None,
        service_response: Optional[str] = None,
    ):
        details = {}
        if service_name:
            details["service_name"] = service_name
        if service_response:
            details["service_response"] = service_response

        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_502_BAD_GATEWAY,
            details=details,
        )


class TimeoutError(DocGateException):
    """超时错误"""

    def __init__(
        self,
        message: str,
        error_code: DocGateErrorCode,
        timeout_duration: Optional[int] = None,
        operation: Optional[str] = None,
    ):
        details = {}
        if timeout_duration:
            details["timeout_duration"] = timeout_duration
        if operation:
            details["operation"] = operation

        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            details=details,
        )


# =============== 异常处理器 ===============

async def docgate_exception_handler(request: Request, exc: DocGateException) -> JSONResponse:
    """DocGate异常处理器"""

    # 记录异常日志
    logger.error(
        f"DocGate异常: {exc.error_code.value} - {exc.message}",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "user_id": getattr(request.state, "user_id", None),
            "url": str(request.url),
            "method": request.method,
            "error_code": exc.error_code.value,
            "details": exc.details,
        },
        exc_info=True if exc.status_code >= 500 else False,
    )

    # 生成响应
    response_data = {
        "success": False,
        "error": exc.to_dict(),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "request_id": getattr(request.state, "request_id", None),
    }

    return JSONResponse(
        status_code=exc.status_code,
        content=response_data,
        headers=exc.headers,
    )


async def validation_exception_handler(request: Request, exc: ValueError) -> JSONResponse:
    """值错误异常处理器"""

    error_code = DocGateErrorCode.INVALID_CONFIG_FORMAT
    message = str(exc)

    # 根据错误消息确定具体的错误代码
    if "文档路径" in message:
        error_code = DocGateErrorCode.INVALID_DOCUMENT_PATH
    elif "文档类型" in message or "格式" in message:
        error_code = DocGateErrorCode.UNSUPPORTED_DOCUMENT_TYPE
    elif "批量" in message or "数量" in message:
        error_code = DocGateErrorCode.BATCH_SIZE_EXCEEDED
    elif "URL" in message:
        error_code = DocGateErrorCode.INVALID_WEBHOOK_URL

    docgate_exc = ValidationError(
        message=message,
        error_code=error_code,
    )

    return await docgate_exception_handler(request, docgate_exc)


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """HTTP异常处理器"""

    # 映射HTTP状态码到DocGate错误代码
    error_code_mapping = {
        400: DocGateErrorCode.INVALID_CONFIG_FORMAT,
        401: DocGateErrorCode.INVALID_ACCESS_TOKEN,
        403: DocGateErrorCode.INSUFFICIENT_READ_PERMISSION,
        404: DocGateErrorCode.DOCUMENT_NOT_FOUND,
        409: DocGateErrorCode.CHECK_TASK_IN_PROGRESS,
        413: DocGateErrorCode.DOCUMENT_TOO_LARGE,
        429: DocGateErrorCode.QUALITY_CHECK_RATE_LIMIT,
        500: DocGateErrorCode.QUALITY_CHECK_FAILED,
        502: DocGateErrorCode.GIT_SERVICE_ERROR,
        503: DocGateErrorCode.SERVICE_UNAVAILABLE,
        504: DocGateErrorCode.CHECK_TIMEOUT,
    }

    error_code = error_code_mapping.get(exc.status_code, DocGateErrorCode.QUALITY_CHECK_FAILED)

    # 处理详情信息
    details = {}
    if isinstance(exc.detail, dict):
        details = exc.detail
        message = details.get("message", "操作失败")
        error_code = DocGateErrorCode(details.get("code", error_code.value))
    else:
        message = str(exc.detail) if exc.detail else "操作失败"

    docgate_exc = DocGateException(
        message=message,
        error_code=error_code,
        status_code=exc.status_code,
        details=details,
        headers=getattr(exc, "headers", {}),
    )

    return await docgate_exception_handler(request, docgate_exc)


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """通用异常处理器"""

    # 记录未处理的异常
    logger.error(
        f"未处理的异常: {type(exc).__name__} - {str(exc)}",
        extra={
            "request_id": getattr(request.state, "request_id", None),
            "user_id": getattr(request.state, "user_id", None),
            "url": str(request.url),
            "method": request.method,
        },
        exc_info=True,
    )

    # 创建通用服务错误
    docgate_exc = ServiceError(
        message="系统内部错误，请稍后重试",
        error_code=DocGateErrorCode.QUALITY_CHECK_FAILED,
        internal_error=str(exc),
    )

    return await docgate_exception_handler(request, docgate_exc)


# =============== 便捷异常创建函数 ===============

def create_validation_error(
    message: str,
    field: Optional[str] = None,
    constraint: Optional[str] = None,
    error_code: DocGateErrorCode = DocGateErrorCode.INVALID_CONFIG_FORMAT,
) -> ValidationError:
    """创建验证错误"""
    return ValidationError(
        message=message,
        error_code=error_code,
        field=field,
        constraint=constraint,
    )


def create_not_found_error(
    resource_type: str,
    resource_id: Optional[str] = None,
    error_code: Optional[DocGateErrorCode] = None,
) -> NotFoundError:
    """创建资源不存在错误"""
    if not error_code:
        if resource_type == "document":
            error_code = DocGateErrorCode.DOCUMENT_NOT_FOUND
        elif resource_type == "check":
            error_code = DocGateErrorCode.CHECK_TASK_NOT_FOUND
        elif resource_type == "config":
            error_code = DocGateErrorCode.CONFIG_NOT_FOUND
        elif resource_type == "webhook":
            error_code = DocGateErrorCode.WEBHOOK_NOT_FOUND
        elif resource_type == "report":
            error_code = DocGateErrorCode.REPORT_NOT_FOUND
        else:
            error_code = DocGateErrorCode.DOCUMENT_NOT_FOUND

    message = f"{resource_type}不存在"
    if resource_id:
        message += f": {resource_id}"

    return NotFoundError(
        message=message,
        error_code=error_code,
        resource_type=resource_type,
        resource_id=resource_id,
    )


def create_permission_error(
    permission: str,
    error_code: Optional[DocGateErrorCode] = None,
) -> AuthorizationError:
    """创建权限错误"""
    if not error_code:
        if "read" in permission:
            error_code = DocGateErrorCode.INSUFFICIENT_READ_PERMISSION
        elif "write" in permission:
            error_code = DocGateErrorCode.INSUFFICIENT_WRITE_PERMISSION
        elif "config" in permission:
            error_code = DocGateErrorCode.INSUFFICIENT_CONFIG_PERMISSION
        elif "webhook" in permission:
            error_code = DocGateErrorCode.INSUFFICIENT_WEBHOOK_PERMISSION
        elif "admin" in permission:
            error_code = DocGateErrorCode.INSUFFICIENT_ADMIN_PERMISSION
        else:
            error_code = DocGateErrorCode.INSUFFICIENT_READ_PERMISSION

    return AuthorizationError(
        message=f"缺少必要权限: {permission}",
        error_code=error_code,
        required_permission=permission,
    )


def create_rate_limit_error(
    operation: str,
    limit: int,
    remaining: int = 0,
    reset_time: Optional[int] = None,
) -> RateLimitError:
    """创建频率限制错误"""
    error_code_mapping = {
        "quality_check": DocGateErrorCode.QUALITY_CHECK_RATE_LIMIT,
        "batch_check": DocGateErrorCode.BATCH_CHECK_RATE_LIMIT,
        "webhook_trigger": DocGateErrorCode.WEBHOOK_RATE_LIMIT,
        "report_download": DocGateErrorCode.REPORT_DOWNLOAD_RATE_LIMIT,
    }

    error_code = error_code_mapping.get(operation, DocGateErrorCode.QUALITY_CHECK_RATE_LIMIT)

    return RateLimitError(
        message=f"{operation}请求过于频繁，请稍后重试",
        error_code=error_code,
        limit=limit,
        remaining=remaining,
        reset_time=reset_time,
    )


def create_service_error(
    service_name: str,
    message: Optional[str] = None,
    internal_error: Optional[str] = None,
    error_code: Optional[DocGateErrorCode] = None,
) -> ServiceError:
    """创建服务错误"""
    if not message:
        message = f"{service_name}服务暂时不可用"

    if not error_code:
        service_error_mapping = {
            "document_parser": DocGateErrorCode.DOCUMENT_PARSE_FAILED,
            "quality_checker": DocGateErrorCode.QUALITY_CHECK_FAILED,
            "report_generator": DocGateErrorCode.REPORT_GENERATION_FAILED,
            "webhook_service": DocGateErrorCode.WEBHOOK_DELIVERY_FAILED,
            "database": DocGateErrorCode.DATABASE_ERROR,
            "cache": DocGateErrorCode.CACHE_ERROR,
        }
        error_code = service_error_mapping.get(service_name, DocGateErrorCode.QUALITY_CHECK_FAILED)

    return ServiceError(
        message=message,
        error_code=error_code,
        service_name=service_name,
        internal_error=internal_error,
    )


# =============== 异常处理器注册 ===============

def register_exception_handlers(app):
    """注册异常处理器到FastAPI应用"""
    app.add_exception_handler(DocGateException, docgate_exception_handler)
    app.add_exception_handler(ValueError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)