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
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from api.perfect21_sdk import Perfect21SDK

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
    description="Perfect21智能开发平台REST API接口",
    version="2.2.0"
)

# 全局SDK实例
sdk = None
running_tasks = {}  # 存储异步任务

def get_sdk() -> Perfect21SDK:
    """获取SDK实例"""
    global sdk
    if sdk is None:
        try:
            sdk = Perfect21SDK()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Perfect21初始化失败: {str(e)}")
    return sdk

@app.get("/")
async def root():
    """API根路径"""
    return {
        "message": "Perfect21 REST API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=StatusResponse)
async def health_check():
    """健康检查"""
    try:
        sdk = get_sdk()
        status_result = sdk.status()

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
async def execute_task(request: TaskRequest):
    """执行开发任务"""
    try:
        sdk = get_sdk()
        result = sdk.task(
            description=request.description,
            timeout=request.timeout,
            verbose=request.verbose
        )

        return TaskResponse(
            success=result['success'],
            output=result.get('stdout'),
            error=result.get('stderr') or result.get('error')
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/task/async", response_model=TaskResponse)
async def execute_task_async(request: TaskRequest, background_tasks: BackgroundTasks):
    """异步执行开发任务"""
    try:
        sdk = get_sdk()

        # 创建任务ID
        import uuid
        task_id = str(uuid.uuid4())

        # 任务完成回调
        def task_callback(tid: str, result: Dict[str, Any]):
            running_tasks[tid] = result

        # 启动异步任务
        actual_task_id = sdk.async_task(
            description=request.description,
            callback=task_callback,
            timeout=request.timeout,
            verbose=request.verbose
        )

        # 将任务标记为运行中
        running_tasks[actual_task_id] = {'status': 'running'}

        return TaskResponse(
            success=True,
            task_id=actual_task_id,
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
async def execute_workflow(request: WorkflowRequest):
    """执行Git工作流操作"""
    try:
        sdk = get_sdk()
        result = sdk.git_workflow(
            action=request.action,
            name=request.name,
            version=request.version,
            source=request.source,
            branch=request.branch
        )

        return {
            "success": result['success'],
            "output": result.get('output'),
            "error": result.get('error')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/hooks/install")
async def install_hooks(request: HooksRequest):
    """安装Git钩子"""
    try:
        sdk = get_sdk()
        result = sdk.install_hooks(
            hook_group=request.hook_group,
            force=request.force
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
        sdk = get_sdk()
        result = sdk.status()

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
        sdk = get_sdk()

        await websocket.send_text(json.dumps({
            "type": "status",
            "message": "任务开始执行..."
        }))

        # 这里可以扩展为真正的流式输出
        result = sdk.task(
            description=request_data['description'],
            timeout=request_data.get('timeout', 300)
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

    start_server(args.host, args.port, args.reload)