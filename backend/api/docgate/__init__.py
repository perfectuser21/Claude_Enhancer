"""
DocGate Agent API模块
文档质量管理系统的完整API实现

提供以下功能：
- 文档质量检查
- 批量文档处理
- 质量报告生成
- 配置管理
- Webhook通知
- 系统监控

API版本: v1.0.0
"""

from fastapi import APIRouter

from .routes import router as docgate_router
from .exceptions import register_exception_handlers
from .models import *
from .dependencies import *

# 版本信息
__version__ = "1.0.0"
__api_version__ = "v1"

# 导出主要组件
__all__ = [
    # 路由
    "docgate_router",
    "register_exception_handlers",
    # 请求模型
    "QualityCheckRequest",
    "BatchQualityCheckRequest",
    "ConfigCreateRequest",
    "WebhookCreateRequest",
    # 响应模型
    "QualityCheckResponse",
    "QualityReport",
    "ConfigResponse",
    "WebhookResponse",
    "SystemHealth",
    "UsageStats",
    # 枚举
    "DocumentSourceType",
    "CheckStatus",
    "IssueSeverity",
    "QualityProfile",
    "Priority",
    "WebhookEvent",
    # 依赖
    "get_docgate_dependencies",
    "require_docgate_read",
    "require_docgate_write",
    "require_docgate_config",
    "require_docgate_admin",
    "require_docgate_webhook",
    # 异常
    "DocGateException",
    "ValidationError",
    "NotFoundError",
    "AuthorizationError",
    "ConflictError",
    "RateLimitError",
    "ServiceError",
]

# API信息
API_INFO = {
    "title": "DocGate Agent API",
    "description": "文档质量管理系统API",
    "version": __version__,
    "api_version": __api_version__,
    "contact": {
        "name": "Claude Enhancer团队",
        "email": "support@claude-enhancer.com",
    },
    "license": {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    "tags": [
        {
            "name": "DocGate质量管理",
            "description": "文档质量检查和管理功能",
        },
        {
            "name": "配置管理",
            "description": "质量检查配置的创建和管理",
        },
        {
            "name": "Webhook管理",
            "description": "事件通知和Webhook配置",
        },
        {
            "name": "系统监控",
            "description": "系统状态和使用统计",
        },
    ],
}


def create_docgate_app():
    """创建DocGate API应用"""
    from fastapi import FastAPI

    app = FastAPI(**API_INFO)

    # 注册路由
    app.include_router(docgate_router)

    # 注册异常处理器
    register_exception_handlers(app)

    return app


def setup_docgate_api(main_app: "FastAPI"):
    """在主应用中设置DocGate API"""

    # 包含DocGate路由
    main_app.include_router(docgate_router, prefix="/api", tags=["DocGate质量管理"])

    # 注册异常处理器
    register_exception_handlers(main_app)

    return main_app
