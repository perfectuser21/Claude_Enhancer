#!/usr/bin/env python3
"""
VibePilot V2 Main Controller
集成AI池、路由器、工作空间管理和Claude执行的主控制器
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional

from core.ai_pool import AIPool, AIInstanceType
from core.router import IntelligentRouter
from core.workspace_manager import WorkspaceManager
from modules.claude_bridge.executor import ClaudeExecutor
from features.ai_butler.butler import AIButler

logger = logging.getLogger("VibePilotV2")

class VibePilotV2:
    """VibePilot V2 主控制器"""

    def __init__(self):
        """初始化VibePilot V2"""
        self.ai_pool = AIPool(claude_max_instances=3, codex_max_instances=2)
        self.router = IntelligentRouter(self.ai_pool)
        self.workspace_manager = WorkspaceManager()
        self.claude_executor = ClaudeExecutor()
        self.ai_butler = AIButler()

        # 系统状态
        self.is_running = False
        self.task_counter = 0

        logger.info("VibePilot V2 主控制器初始化完成")

    async def initialize(self):
        """异步初始化系统组件"""
        logger.info("正在初始化VibePilot V2系统...")

        # 检查Claude可用性
        if not self.claude_executor.is_available:
            logger.warning("Claude Code不可用，部分功能可能受限")

        # 创建默认工作空间
        default_workspace = self.workspace_manager.create_workspace(
            name="Default",
            description="默认开发工作空间",
            project_type="general"
        )

        if default_workspace:
            logger.info(f"创建默认工作空间: {default_workspace}")

        # 预创建一些AI实例
        try:
            claude_instance = self.ai_pool.create_instance(AIInstanceType.CLAUDE, default_workspace)
            logger.info(f"预创建Claude实例: {claude_instance}")
        except Exception as e:
            logger.warning(f"预创建Claude实例失败: {e}")

        self.is_running = True
        logger.info("✅ VibePilot V2 系统初始化完成")

    async def process_task(self, task_description: str, workspace_id: str = None,
                          context: Dict[str, Any] = None) -> Dict[str, Any]:
        """处理用户任务"""

        self.task_counter += 1
        task_id = f"task_{self.task_counter}"

        logger.info(f"[{task_id}] 处理任务: {task_description[:100]}...")

        try:
            # 1. 路由任务到合适的AI实例
            routing_result = self.router.route_task(task_description, workspace_id)

            if not routing_result["success"]:
                return {
                    "task_id": task_id,
                    "success": False,
                    "error": routing_result["error"],
                    "routing_info": routing_result
                }

            instance_id = routing_result["instance_id"]
            ai_type = routing_result["ai_type"]

            # 2. 更新工作空间活动
            if workspace_id:
                self.workspace_manager.update_workspace_activity(workspace_id)
                self.workspace_manager.assign_ai_instance(workspace_id, instance_id)

            # 3. 执行任务
            if ai_type == "claude":
                # 使用Claude执行器
                workspace_path = None
                if workspace_id:
                    workspace_info = self.workspace_manager.get_workspace(workspace_id)
                    workspace_path = workspace_info.path if workspace_info else None

                execution_result = await self.claude_executor.execute_task(
                    task_description, context, workspace=workspace_path
                )

                # 记录性能
                self.router.record_task_performance(ai_type, execution_result["execution_time"])

                result = {
                    "task_id": task_id,
                    "success": execution_result["success"],
                    "output": execution_result["output"],
                    "execution_time": execution_result["execution_time"],
                    "ai_type": ai_type,
                    "instance_id": instance_id,
                    "workspace_id": workspace_id,
                    "routing_info": routing_result
                }

                if not execution_result["success"]:
                    result["error"] = execution_result["error"]
                    result["stderr"] = execution_result.get("stderr", "")

                # 4. 完成任务并释放实例
                self.ai_pool.complete_task(instance_id, execution_result["success"])

                if workspace_id:
                    self.workspace_manager.release_ai_instance(workspace_id, instance_id)

                return result

            else:
                # Codex实例（暂时返回未实现）
                self.ai_pool.complete_task(instance_id, False)
                return {
                    "task_id": task_id,
                    "success": False,
                    "error": "Codex执行器尚未实现",
                    "ai_type": ai_type,
                    "instance_id": instance_id
                }

        except Exception as e:
            logger.error(f"[{task_id}] 任务处理异常: {e}")
            return {
                "task_id": task_id,
                "success": False,
                "error": str(e),
                "exception_type": type(e).__name__
            }

    async def chat(self, message: str, workspace_id: str = None) -> Dict[str, Any]:
        """处理聊天消息"""

        # 使用AI管家分析消息
        analysis = self.ai_butler.analyze_user_message(message)

        if analysis["should_execute_claude"]:
            # 执行任务
            return await self.process_task(message, workspace_id)
        else:
            # 普通聊天回复
            response = self.ai_butler.generate_chat_response(message)
            return {
                "success": True,
                "response": response,
                "type": "chat",
                "analysis": analysis
            }

    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        return {
            "is_running": self.is_running,
            "task_counter": self.task_counter,
            "ai_pool_status": self.ai_pool.get_pool_status(),
            "workspace_stats": self.workspace_manager.get_workspace_stats(),
            "claude_executor_stats": self.claude_executor.get_execution_stats(),
            "routing_stats": self.router.get_routing_stats(),
            "ai_butler_stats": self.ai_butler.get_session_stats()
        }

    def create_workspace(self, name: str, description: str = "",
                        project_type: str = "general") -> Optional[str]:
        """创建工作空间"""
        return self.workspace_manager.create_workspace(name, description, project_type)

    def list_workspaces(self) -> List[Dict[str, Any]]:
        """列出所有工作空间"""
        workspaces = self.workspace_manager.list_workspaces()
        return [
            {
                "workspace_id": ws.workspace_id,
                "name": ws.name,
                "description": ws.description,
                "status": ws.status,
                "project_type": ws.project_type,
                "created_at": ws.created_at.isoformat(),
                "last_activity": ws.last_activity.isoformat(),
                "ai_instances": ws.ai_instances,
                "path": ws.path
            }
            for ws in workspaces
        ]

    async def shutdown(self):
        """关闭系统"""
        logger.info("正在关闭VibePilot V2系统...")

        # 清理AI池中的错误实例
        self.ai_pool.cleanup_error_instances()

        # 归档空闲工作空间
        # (可选实现)

        self.is_running = False
        logger.info("✅ VibePilot V2 系统已关闭")

    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        health_status = {
            "system_running": self.is_running,
            "claude_available": self.claude_executor.is_available,
            "total_workspaces": len(self.workspace_manager.workspaces),
            "ai_pool_health": True,  # 可以添加更详细的检查
            "timestamp": self.ai_butler.get_session_stats()["timestamp"]
        }

        # 刷新Claude可用性
        self.claude_executor.refresh_availability()

        return health_status