"""
DocGate Agent API依赖注入
定义DocGate系统的依赖注入函数和服务获取逻辑
"""

from fastapi import Depends, HTTPException, status, Request
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta
import asyncio
from functools import lru_cache

# 导入基础依赖
from backend.api.auth.dependencies import (
    get_current_active_user,
    require_permissions,
    get_client_info,
    rate_limit_check as base_rate_limit_check,
)
from backend.core.models import User
from backend.core.cache import CacheManager
from backend.core.database import get_async_session
from backend.security.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


# =============== 服务依赖 ===============


class DocGateServiceConfig:
    """DocGate服务配置"""

    def __init__(self):
        self.max_document_size = 50 * 1024 * 1024  # 50MB
        self.supported_formats = ["md", "markdown", "html", "htm", "txt", "rst"]
        self.max_concurrent_checks = 10
        self.default_timeout = 300
        self.report_retention_days = 90
        self.webhook_timeout = 30
        self.webhook_retry_attempts = 3

    @property
    def is_valid(self) -> bool:
        """检查配置是否有效"""
        return (
            self.max_document_size > 0
            and len(self.supported_formats) > 0
            and self.max_concurrent_checks > 0
            and self.default_timeout > 0
        )


@lru_cache()
def get_docgate_config() -> DocGateServiceConfig:
    """获取DocGate配置（缓存单例）"""
    return DocGateServiceConfig()


class DocGateHealthCheck:
    """DocGate健康检查"""

    def __init__(self):
        self.last_check = None
        self.status = "unknown"
        self.services_status = {}

    async def check_health(self) -> Dict[str, Any]:
        """执行健康检查"""
        try:
            # 检查各个服务组件
            checks = await asyncio.gather(
                self._check_document_parser(),
                self._check_quality_checker(),
                self._check_report_generator(),
                self._check_webhook_service(),
                return_exceptions=True,
            )

            # 汇总结果
            services = {
                "document_parser": "healthy"
                if not isinstance(checks[0], Exception)
                else "unhealthy",
                "quality_checker": "healthy"
                if not isinstance(checks[1], Exception)
                else "unhealthy",
                "report_generator": "healthy"
                if not isinstance(checks[2], Exception)
                else "unhealthy",
                "webhook_service": "healthy"
                if not isinstance(checks[3], Exception)
                else "unhealthy",
            }

            # 计算整体状态
            unhealthy_count = sum(
                1 for status in services.values() if status == "unhealthy"
            )
            if unhealthy_count == 0:
                overall_status = "healthy"
            elif unhealthy_count <= len(services) // 2:
                overall_status = "degraded"
            else:
                overall_status = "unhealthy"

            self.status = overall_status
            self.services_status = services
            self.last_check = datetime.utcnow()

            return {
                "status": overall_status,
                "services": services,
                "checked_at": self.last_check,
            }

        except Exception as e:
            logger.error(f"健康检查异常: {e}", exc_info=True)
            self.status = "unhealthy"
            return {
                "status": "unhealthy",
                "error": str(e),
                "checked_at": datetime.utcnow(),
            }

    async def _check_document_parser(self):
        """检查文档解析器"""
        # 实际实现中应该测试文档解析功能
        await asyncio.sleep(0.1)  # 模拟检查
        return True

    async def _check_quality_checker(self):
        """检查质量检查器"""
        # 实际实现中应该测试质量检查功能
        await asyncio.sleep(0.1)  # 模拟检查
        return True

    async def _check_report_generator(self):
        """检查报告生成器"""
        # 实际实现中应该测试报告生成功能
        await asyncio.sleep(0.1)  # 模拟检查
        return True

    async def _check_webhook_service(self):
        """检查Webhook服务"""
        # 实际实现中应该测试Webhook功能
        await asyncio.sleep(0.1)  # 模拟检查
        return True


# 全局健康检查实例
_health_checker = DocGateHealthCheck()


async def get_docgate_health() -> DocGateHealthCheck:
    """获取健康检查器"""
    return _health_checker


# =============== 权限依赖 ===============


def require_docgate_permissions(permissions: List[str]):
    """要求DocGate特定权限"""

    def permission_checker(
        current_user: User = Depends(get_current_active_user),
        _: bool = Depends(require_permissions(permissions)),
    ) -> User:
        return current_user

    return permission_checker


# 预定义权限检查器
require_docgate_read = require_docgate_permissions(["docgate:read"])
require_docgate_write = require_docgate_permissions(["docgate:write"])
require_docgate_config = require_docgate_permissions(["docgate:config"])
require_docgate_admin = require_docgate_permissions(["docgate:admin"])
require_docgate_webhook = require_docgate_permissions(["docgate:webhook"])


# =============== 限流依赖 ===============


class DocGateRateLimiter:
    """DocGate专用限流器"""

    def __init__(self):
        self.limiter = RateLimiter()
        self.limits = {
            "quality_check": {"limit": 100, "window": 3600},  # 100次/小时
            "batch_check": {"limit": 10, "window": 3600},  # 10次/小时
            "report_download": {"limit": 1000, "window": 3600},  # 1000次/小时
            "webhook_trigger": {"limit": 10000, "window": 3600},  # 10000次/小时
        }

    async def check_limit(self, user_id: str, operation: str) -> bool:
        """检查限流"""
        if operation not in self.limits:
            return True

        limit_config = self.limits[operation]
        key = f"docgate:{operation}:{user_id}"

        return await self.limiter.is_allowed(
            key=key, limit=limit_config["limit"], window=limit_config["window"]
        )

    async def get_remaining(self, user_id: str, operation: str) -> Optional[int]:
        """获取剩余次数"""
        if operation not in self.limits:
            return None

        limit_config = self.limits[operation]
        key = f"docgate:{operation}:{user_id}"

        return await self.limiter.get_remaining(
            key=key, limit=limit_config["limit"], window=limit_config["window"]
        )


_rate_limiter = DocGateRateLimiter()


async def get_docgate_rate_limiter() -> DocGateRateLimiter:
    """获取DocGate限流器"""
    return _rate_limiter


def docgate_rate_limit_check(operation: str):
    """DocGate操作限流检查"""

    async def rate_limit_checker(
        request: Request,
        current_user: User = Depends(get_current_active_user),
        rate_limiter: DocGateRateLimiter = Depends(get_docgate_rate_limiter),
    ) -> bool:
        # 检查限流
        allowed = await rate_limiter.check_limit(str(current_user.id), operation)

        if not allowed:
            # 获取剩余次数和重置时间
            remaining = await rate_limiter.get_remaining(
                str(current_user.id), operation
            )
            limit_config = rate_limiter.limits.get(operation, {})

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": "DOC_RAT_001",
                    "type": "RATE_LIMIT_ERROR",
                    "message": f"{operation}请求过于频繁",
                    "retry_after": limit_config.get("window", 3600),
                    "remaining": remaining or 0,
                },
                headers={
                    "X-RateLimit-Limit": str(limit_config.get("limit", 0)),
                    "X-RateLimit-Remaining": str(remaining or 0),
                    "X-RateLimit-Reset": str(
                        int(
                            (
                                datetime.utcnow()
                                + timedelta(seconds=limit_config.get("window", 3600))
                            ).timestamp()
                        )
                    ),
                    "Retry-After": str(limit_config.get("window", 3600)),
                },
            )

        return True

    return rate_limit_checker


# 预定义限流检查器
quality_check_rate_limit = docgate_rate_limit_check("quality_check")
batch_check_rate_limit = docgate_rate_limit_check("batch_check")
report_download_rate_limit = docgate_rate_limit_check("report_download")
webhook_rate_limit = docgate_rate_limit_check("webhook_trigger")


# =============== 验证依赖 ===============


class DocumentValidator:
    """文档验证器"""

    def __init__(self, config: DocGateServiceConfig):
        self.config = config

    def validate_document_path(self, path: str) -> bool:
        """验证文档路径"""
        if not path or not path.strip():
            raise ValueError("文档路径不能为空")

        # 检查路径安全性（防止路径遍历攻击）
        if ".." in path or path.startswith("/"):
            raise ValueError("文档路径不安全")

        return True

    def validate_document_size(self, size: int) -> bool:
        """验证文档大小"""
        if size > self.config.max_document_size:
            raise ValueError(
                f"文档大小超出限制（最大{self.config.max_document_size / 1024 / 1024:.1f}MB）"
            )

        return True

    def validate_document_format(self, filename: str) -> bool:
        """验证文档格式"""
        if not filename:
            raise ValueError("文件名不能为空")

        # 提取文件扩展名
        parts = filename.lower().split(".")
        if len(parts) < 2:
            raise ValueError("无法识别文件格式")

        extension = parts[-1]
        if extension not in self.config.supported_formats:
            raise ValueError(f"不支持的文档格式：{extension}")

        return True

    def validate_batch_size(self, count: int) -> bool:
        """验证批量大小"""
        if count <= 0:
            raise ValueError("批量文档数量必须大于0")

        if count > 50:  # 硬编码的批量限制
            raise ValueError("批量文档数量不能超过50个")

        return True


async def get_document_validator() -> DocumentValidator:
    """获取文档验证器"""
    config = get_docgate_config()
    return DocumentValidator(config)


def validate_document_request():
    """文档请求验证依赖"""

    async def validator(
        request: Request,
        validator: DocumentValidator = Depends(get_document_validator),
    ) -> DocumentValidator:
        # 这里可以添加请求级别的验证逻辑
        return validator

    return validator


# =============== 缓存依赖 ===============


class DocGateCacheManager:
    """DocGate缓存管理器"""

    def __init__(self):
        self.cache = CacheManager()
        self.default_ttl = 3600  # 1小时
        self.report_ttl = 86400  # 24小时
        self.config_ttl = 1800  # 30分钟

    async def get_check_status(self, check_id: str) -> Optional[Dict[str, Any]]:
        """获取检查状态缓存"""
        key = f"docgate:check_status:{check_id}"
        return await self.cache.get(key)

    async def set_check_status(
        self, check_id: str, status: Dict[str, Any], ttl: Optional[int] = None
    ) -> None:
        """设置检查状态缓存"""
        key = f"docgate:check_status:{check_id}"
        await self.cache.set(key, status, ttl or self.default_ttl)

    async def get_report(self, check_id: str) -> Optional[Dict[str, Any]]:
        """获取报告缓存"""
        key = f"docgate:report:{check_id}"
        return await self.cache.get(key)

    async def set_report(self, check_id: str, report: Dict[str, Any]) -> None:
        """设置报告缓存"""
        key = f"docgate:report:{check_id}"
        await self.cache.set(key, report, self.report_ttl)

    async def get_config(self, config_id: str) -> Optional[Dict[str, Any]]:
        """获取配置缓存"""
        key = f"docgate:config:{config_id}"
        return await self.cache.get(key)

    async def set_config(self, config_id: str, config: Dict[str, Any]) -> None:
        """设置配置缓存"""
        key = f"docgate:config:{config_id}"
        await self.cache.set(key, config, self.config_ttl)

    async def invalidate_user_cache(self, user_id: str) -> None:
        """清除用户相关缓存"""
        patterns = [
            f"docgate:check_status:*{user_id}*",
            f"docgate:report:*{user_id}*",
            f"docgate:config:*{user_id}*",
        ]

        for pattern in patterns:
            await self.cache.delete_pattern(pattern)


_cache_manager = DocGateCacheManager()


async def get_docgate_cache() -> DocGateCacheManager:
    """获取DocGate缓存管理器"""
    return _cache_manager


# =============== 请求追踪依赖 ===============


async def get_request_context(
    request: Request,
    client_info: Dict[str, Any] = Depends(get_client_info),
) -> Dict[str, Any]:
    """获取请求上下文信息"""

    # 生成请求ID（如果没有的话）
    request_id = client_info.get("request_id")
    if not request_id:
        import uuid

        request_id = str(uuid.uuid4())

    return {
        "request_id": request_id,
        "timestamp": datetime.utcnow(),
        "method": request.method,
        "url": str(request.url),
        "ip_address": client_info.get("ip_address"),
        "user_agent": client_info.get("user_agent"),
        "headers": dict(request.headers),
    }


# =============== 服务质量依赖 ===============


class ServiceQualityMonitor:
    """服务质量监控"""

    def __init__(self):
        self.metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time": 0.0,
            "last_error": None,
        }

    async def record_request(
        self, success: bool, response_time: float, error: Optional[str] = None
    ):
        """记录请求指标"""
        self.metrics["total_requests"] += 1

        if success:
            self.metrics["successful_requests"] += 1
        else:
            self.metrics["failed_requests"] += 1
            self.metrics["last_error"] = error

        # 更新平均响应时间
        total_time = self.metrics["avg_response_time"] * (
            self.metrics["total_requests"] - 1
        )
        self.metrics["avg_response_time"] = (total_time + response_time) / self.metrics[
            "total_requests"
        ]

    def get_success_rate(self) -> float:
        """获取成功率"""
        if self.metrics["total_requests"] == 0:
            return 0.0

        return (
            self.metrics["successful_requests"] / self.metrics["total_requests"] * 100
        )

    def get_metrics(self) -> Dict[str, Any]:
        """获取所有指标"""
        return {
            **self.metrics,
            "success_rate": self.get_success_rate(),
        }


_service_monitor = ServiceQualityMonitor()


async def get_service_monitor() -> ServiceQualityMonitor:
    """获取服务质量监控器"""
    return _service_monitor


# =============== 异步任务依赖 ===============


class TaskManager:
    """异步任务管理器"""

    def __init__(self):
        self.active_tasks = {}
        self.task_results = {}
        self.max_concurrent_tasks = 10

    async def submit_task(self, task_id: str, coroutine) -> str:
        """提交异步任务"""
        if len(self.active_tasks) >= self.max_concurrent_tasks:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "DOC_SER_004",
                    "type": "SERVICE_UNAVAILABLE",
                    "message": "系统繁忙，请稍后重试",
                },
            )

        # 创建任务
        task = asyncio.create_task(coroutine)
        self.active_tasks[task_id] = task

        # 设置完成回调
        task.add_done_callback(lambda t: self._task_completed(task_id, t))

        return task_id

    def _task_completed(self, task_id: str, task: asyncio.Task):
        """任务完成回调"""
        # 移除活动任务
        self.active_tasks.pop(task_id, None)

        # 保存结果
        try:
            result = task.result()
            self.task_results[task_id] = {"success": True, "result": result}
        except Exception as e:
            self.task_results[task_id] = {"success": False, "error": str(e)}

        # 清理旧结果（保留最近100个）
        if len(self.task_results) > 100:
            oldest_keys = list(self.task_results.keys())[:-100]
            for key in oldest_keys:
                self.task_results.pop(key, None)

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        # 检查活动任务
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            return {
                "status": "running",
                "done": task.done(),
                "cancelled": task.cancelled(),
            }

        # 检查完成任务
        if task_id in self.task_results:
            result = self.task_results[task_id]
            return {
                "status": "completed" if result["success"] else "failed",
                "done": True,
                "result": result.get("result"),
                "error": result.get("error"),
            }

        return None

    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            task.cancel()
            return True

        return False


_task_manager = TaskManager()


async def get_task_manager() -> TaskManager:
    """获取任务管理器"""
    return _task_manager


# =============== 组合依赖 ===============


class DocGateDependencies:
    """DocGate依赖集合"""

    def __init__(
        self,
        current_user: User,
        client_info: Dict[str, Any],
        config: DocGateServiceConfig,
        validator: DocumentValidator,
        cache: DocGateCacheManager,
        monitor: ServiceQualityMonitor,
        task_manager: TaskManager,
        rate_limiter: DocGateRateLimiter,
    ):
        self.current_user = current_user
        self.client_info = client_info
        self.config = config
        self.validator = validator
        self.cache = cache
        self.monitor = monitor
        self.task_manager = task_manager
        self.rate_limiter = rate_limiter


async def get_docgate_dependencies(
    current_user: User = Depends(get_current_active_user),
    client_info: Dict[str, Any] = Depends(get_client_info),
    config: DocGateServiceConfig = Depends(get_docgate_config),
    validator: DocumentValidator = Depends(get_document_validator),
    cache: DocGateCacheManager = Depends(get_docgate_cache),
    monitor: ServiceQualityMonitor = Depends(get_service_monitor),
    task_manager: TaskManager = Depends(get_task_manager),
    rate_limiter: DocGateRateLimiter = Depends(get_docgate_rate_limiter),
) -> DocGateDependencies:
    """获取DocGate完整依赖集合"""
    return DocGateDependencies(
        current_user=current_user,
        client_info=client_info,
        config=config,
        validator=validator,
        cache=cache,
        monitor=monitor,
        task_manager=task_manager,
        rate_limiter=rate_limiter,
    )
