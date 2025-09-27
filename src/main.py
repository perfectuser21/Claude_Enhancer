"""
任务管理系统 - FastAPI主应用
============================

这是任务管理系统的FastAPI主应用入口，提供：
- 完整的RESTful API
- 自动API文档生成
- 中间件配置
- 错误处理
- 安全认证
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

# 配置导入
from src.core.config import get_settings
from src.core.database import engine, create_all_tables
from src.core.dependencies import setup_dependencies

# API路由导入
from src.api.routes.auth import router as auth_router
from src.api.routes.tasks import router as tasks_router
from src.api.routes.projects import router as projects_router
from src.api.routes.dashboard import router as dashboard_router
from src.api.routes.notifications import router as notifications_router

# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 获取配置
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("🚀 启动任务管理系统...")

    # 初始化数据库
    try:
        create_all_tables()
        logger.info("✅ 数据库表创建成功")
    except Exception as e:
        logger.error(f"❌ 数据库初始化失败: {e}")
        raise

    # 设置依赖
    setup_dependencies()
    logger.info("✅ 依赖注入配置完成")

    yield

    # 关闭时执行
    logger.info("🔄 正在关闭任务管理系统...")
    logger.info("✅ 系统关闭完成")


# 创建FastAPI应用实例
app = FastAPI(
    title="Task Management System API",
    description="""
    ## 📋 任务管理系统 API

    ### 功能特性
    - 🔐 **用户认证**: JWT Token认证，安全可靠
    - 📝 **任务管理**: 创建、更新、删除、查询任务
    - 📊 **项目管理**: 项目组织和进度跟踪
    - 👥 **团队协作**: 成员管理和权限控制
    - 🔔 **通知系统**: 实时消息推送
    - 📈 **仪表板**: 数据统计和可视化
    - 📁 **文件管理**: 任务附件上传下载

    ### 技术栈
    - **后端框架**: FastAPI + Python 3.9+
    - **数据库**: PostgreSQL + Redis
    - **认证**: JWT + bcrypt
    - **文档**: 自动生成OpenAPI规范

    ### API使用指南
    1. 首先注册账户或登录获取访问令牌
    2. 在请求头中包含 `Authorization: Bearer <your-token>`
    3. 所有时间格式使用ISO 8601标准
    4. 支持分页、过滤、排序等查询参数
    """,
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
    contact={
        "name": "任务管理系统开发团队",
        "email": "support@taskmanager.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# ===== 中间件配置 =====

# CORS中间件 - 处理跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# 信任主机中间件 - 安全防护
if settings.TRUSTED_HOSTS:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.TRUSTED_HOSTS)


# 请求日志中间件
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """请求日志中间件 - 记录所有API请求"""
    start_time = time.time()

    # 记录请求信息
    logger.info(
        f"📥 {request.method} {request.url.path} - "
        f"Client: {request.client.host if request.client else 'unknown'}"
    )

    # 处理请求
    response = await call_next(request)

    # 计算处理时间
    process_time = time.time() - start_time

    # 记录响应信息
    logger.info(
        f"📤 {request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )

    # 添加响应头
    response.headers["X-Process-Time"] = str(process_time)

    return response


# 错误处理中间件
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    logger.warning(
        f"⚠️ HTTP异常: {request.method} {request.url.path} - "
        f"Status: {exc.status_code} - Detail: {exc.detail}"
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path),
            "timestamp": time.time(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error(
        f"💥 服务器错误: {request.method} {request.url.path} - " f"Error: {str(exc)}"
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "内部服务器错误，请稍后重试",
            "status_code": 500,
            "path": str(request.url.path),
            "timestamp": time.time(),
        },
    )


# ===== 路由注册 =====


# 健康检查端点
@app.get("/health", tags=["Health"], summary="健康检查")
async def health_check():
    """
    系统健康检查接口

    返回系统状态信息，用于负载均衡器和监控系统检查服务可用性。
    """
    return {
        "status": "healthy",
        "service": "Task Management System",
        "version": "1.0.0",
        "timestamp": time.time(),
        "environment": settings.ENVIRONMENT,
    }


# 根路径重定向到文档
@app.get("/", include_in_schema=False)
async def root():
    """根路径重定向到API文档"""
    return {
        "message": "欢迎使用任务管理系统 API",
        "documentation": "/docs",
        "health_check": "/health",
        "version": "1.0.0",
    }


# 注册API路由
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(tasks_router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(projects_router, prefix="/api/projects", tags=["Projects"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(
    notifications_router, prefix="/api/notifications", tags=["Notifications"]
)


# 自定义OpenAPI配置
def custom_openapi():
    """自定义OpenAPI配置"""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="任务管理系统 API",
        version="1.0.0",
        description=app.description,
        routes=app.routes,
    )

    # 添加安全方案
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "在此输入JWT Token，格式: Bearer <your-token>",
        }
    }

    # 为所有需要认证的端点添加安全要求
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if method != "options" and not path.startswith("/health"):
                openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# ===== 启动配置 =====

if __name__ == "__main__":
    # 开发环境直接运行
    logger.info("🚀 启动开发服务器...")
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        access_log=True,
        log_level="info" if settings.DEBUG else "warning",
    )
