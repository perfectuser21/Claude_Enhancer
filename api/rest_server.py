#!/usr/bin/env python3
"""
Perfect21 REST API Server
提供HTTP接口用于远程调用Perfect21功能
"""

import os
import sys
import json
import asyncio
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
import uvicorn
from contextlib import asynccontextmanager

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from api.perfect21_sdk import Perfect21SDK
from api.auth_api import auth_router
from api.middleware import (
    create_rate_limit_middleware,
    create_logging_middleware,
    create_security_headers_middleware,
    create_error_handling_middleware,
    create_response_time_middleware
)
from features.auth_system.jwt_middleware import create_jwt_middleware
from features.auth_system.redis_session_manager import RedisSessionManager
from features.auth_system import AuthManager

# 请求模型
class TaskRequest(BaseModel):
    description: str
    timeout: Optional[int] = 300
    verbose: Optional[bool] = False

class WorkflowRequest(BaseModel):
    action: str
    name: Optional[str] = None
    version: Optional[str] = None
    source: Optional[str] = None
    branch: Optional[str] = None

class HooksRequest(BaseModel):
    hook_group: str = 'standard'
    force: bool = False

# 响应模型
class TaskResponse(BaseModel):
    success: bool
    task_id: Optional[str] = None
    output: Optional[str] = None
    error: Optional[str] = None

class StatusResponse(BaseModel):
    success: bool
    perfect21_available: bool
    output: Optional[str] = None
    error: Optional[str] = None

# 创建FastAPI应用
app = FastAPI(
    title="Perfect21 API",
    description="Perfect21智能开发平台REST API接口，包含JWT认证、bcrypt加密、Redis会话管理和速率限制",
    version="3.0.0"
)

# 初始化认证和会话管理器
auth_manager = AuthManager()
session_manager = RedisSessionManager()

# 添加JWT认证中间件
jwt_middleware = create_jwt_middleware(auth_manager, session_manager)
app.middleware("http")(jwt_middleware)

# 添加其他中间件
app.middleware("http")(create_error_handling_middleware())
app.middleware("http")(create_rate_limit_middleware(max_requests=100, window_seconds=60))
app.middleware("http")(create_logging_middleware())
app.middleware("http")(create_security_headers_middleware())
app.middleware("http")(create_response_time_middleware())

# 添加中间件
# 从环境变量获取允许的域名，默认只允许本地开发
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # 使用具体的域名列表
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # 明确指定允许的方法
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],  # 限制允许的头部
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# 包含认证路由
app.include_router(auth_router)

# 全局SDK实例
sdk = None
running_tasks = {}  # 存储异步任务

@asynccontextmanager
async def get_async_sdk():
    """异步上下文管理器获取SDK实例"""
    global sdk
    if sdk is None:
        try:
            # 在后台线程中初始化SDK（如果它是同步的）
            loop = asyncio.get_event_loop()
            sdk = await loop.run_in_executor(None, lambda: Perfect21SDK())
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Perfect21初始化失败: {str(e)}")
    yield sdk

async def get_sdk() -> Perfect21SDK:
    """异步获取SDK实例"""
    async with get_async_sdk() as sdk_instance:
        return sdk_instance

@app.get("/")
async def root():
    """API根路径"""
    return {
        "message": "Perfect21 REST API",
        "version": "3.0.0",
        "features": [
            "JWT认证与授权",
            "bcrypt密码加密",
            "Redis会话管理",
            "API速率限制",
            "智能开发任务执行",
            "Git工作流管理",
            "多Agent协作"
        ],
        "security": {
            "authentication": "JWT Bearer Token",
            "password_hashing": "bcrypt",
            "session_storage": "Redis",
            "rate_limiting": "滑动窗口算法"
        },
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "auth": "/api/auth",
            "tasks": "/task",
            "workflow": "/workflow"
        }
    }

@app.get("/health", response_model=StatusResponse)
async def health_check():
    """健康检查"""
    try:
        sdk = await get_sdk()
        # 在executor中运行同步方法
        loop = asyncio.get_event_loop()
        status_result = await loop.run_in_executor(None, sdk.status)

        return StatusResponse(
            success=status_result['success'],
            perfect21_available=status_result['success'],
            output=status_result.get('output'),
            error=status_result.get('error')
        )
    except Exception as e:
        return StatusResponse(
            success=False,
            perfect21_available=False,
            error=str(e)
        )

@app.post("/task", response_model=TaskResponse)
async def execute_task(request: TaskRequest, http_request: Request):
    """执行开发任务（需要认证）"""
    try:
        # 获取当前用户（由JWT中间件提供）
        current_user = getattr(http_request.state, 'user', None)
        if not current_user:
            raise HTTPException(status_code=401, detail="需要认证")

        # 加强认证验证：确保用户会话有效
        if not hasattr(current_user, 'id') or not current_user.id:
            raise HTTPException(status_code=401, detail="无效的用户认证")

        # 可选：验证用户权限
        # if not auth_manager.has_permission(current_user, 'execute_task'):
        #     raise HTTPException(status_code=403, detail="权限不足")

        sdk = await get_sdk()
        # 在executor中运行同步任务
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: sdk.task(
                description=request.description,
                timeout=request.timeout,
                verbose=request.verbose
            )
        )

        return TaskResponse(
            success=result['success'],
            output=result.get('stdout'),
            error=result.get('stderr') or result.get('error')
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/task/async", response_model=TaskResponse)
async def execute_task_async(request: TaskRequest, background_tasks: BackgroundTasks, http_request: Request):
    """异步执行开发任务（需要认证）"""
    try:
        # 获取当前用户
        current_user = getattr(http_request.state, 'user', None)
        if not current_user:
            raise HTTPException(status_code=401, detail="需要认证")

        sdk = await get_sdk()

        # 创建任务ID
        import uuid
        task_id = str(uuid.uuid4())

        # 异步任务执行函数
        async def execute_background_task():
            try:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: sdk.task(
                        description=request.description,
                        timeout=request.timeout,
                        verbose=request.verbose
                    )
                )
                running_tasks[task_id] = result
            except Exception as e:
                running_tasks[task_id] = {
                    'success': False,
                    'error': str(e),
                    'status': 'failed'
                }

        # 添加到后台任务
        background_tasks.add_task(execute_background_task)

        # 将任务标记为运行中
        running_tasks[task_id] = {'status': 'running'}

        return TaskResponse(
            success=True,
            task_id=task_id,
            output="任务已开始异步执行"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/task/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str):
    """获取异步任务状态"""
    if task_id not in running_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task_result = running_tasks[task_id]

    if task_result.get('status') == 'running':
        return TaskResponse(
            success=True,
            task_id=task_id,
            output="任务运行中..."
        )
    else:
        return TaskResponse(
            success=task_result.get('success', False),
            task_id=task_id,
            output=task_result.get('stdout'),
            error=task_result.get('stderr') or task_result.get('error')
        )

@app.post("/workflow")
async def execute_workflow(request: WorkflowRequest, http_request: Request):
    """执行Git工作流操作（需要认证）"""
    try:
        # 获取当前用户
        current_user = getattr(http_request.state, 'user', None)
        if not current_user:
            raise HTTPException(status_code=401, detail="需要认证")

        sdk = await get_sdk()
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: sdk.git_workflow(
                action=request.action,
                name=request.name,
                version=request.version,
                source=request.source,
                branch=request.branch
            )
        )

        return {
            "success": result['success'],
            "output": result.get('output'),
            "error": result.get('error')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/hooks/install")
async def install_hooks(request: HooksRequest, http_request: Request):
    """安装Git钩子（需要管理员权限）"""
    try:
        # 获取当前用户
        current_user = getattr(http_request.state, 'user', None)
        if not current_user:
            raise HTTPException(status_code=401, detail="需要认证")

        # 检查管理员权限
        if current_user.get('role') not in ['admin', 'super_admin']:
            raise HTTPException(status_code=403, detail="需要管理员权限")

        sdk = await get_sdk()
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: sdk.install_hooks(
                hook_group=request.hook_group,
                force=request.force
            )
        )

        return {
            "success": result['success'],
            "output": result.get('output'),
            "error": result.get('error')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    """获取Perfect21系统状态"""
    try:
        sdk = await get_sdk()
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, sdk.status)

        return {
            "success": result['success'],
            "output": result.get('output'),
            "error": result.get('error')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/task")
async def websocket_task_stream(websocket):
    """WebSocket流式任务执行"""
    await websocket.accept()

    try:
        # 接收任务请求
        data = await websocket.receive_text()
        request_data = json.loads(data)

        # 执行任务并流式返回结果
        sdk = await get_sdk()

        await websocket.send_text(json.dumps({
            "type": "status",
            "message": "任务开始执行..."
        }))

        # 在executor中执行同步任务
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: sdk.task(
                description=request_data['description'],
                timeout=request_data.get('timeout', 300)
            )
        )

        await websocket.send_text(json.dumps({
            "type": "result",
            "success": result['success'],
            "output": result.get('stdout'),
            "error": result.get('stderr')
        }))

    except Exception as e:
        await websocket.send_text(json.dumps({
            "type": "error",
            "message": str(e)
        }))
    finally:
        await websocket.close()

def start_server(host: str = "127.0.0.1", port: int = 8000, reload: bool = False):
    """启动REST API服务器"""
    uvicorn.run(
        "api.rest_server:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Perfect21 REST API Server')
    parser.add_argument('--host', default='127.0.0.1', help='服务器地址')
    parser.add_argument('--port', type=int, default=8000, help='端口号')
    parser.add_argument('--reload', action='store_true', help='开发模式自动重载')

    args = parser.parse_args()

    print(f"🚀 启动Perfect21 REST API服务器...")
    print(f"📡 地址: http://{args.host}:{args.port}")
    print(f"📚 API文档: http://{args.host}:{args.port}/docs")
    print(f"🔐 认证功能: JWT + bcrypt + Redis 会话管理")
    print(f"🛡️  安全功能: 速率限制 + 安全头部 + 错误处理")

    start_server(args.host, args.port, args.reload)