#!/usr/bin/env python3
"""
Perfect21 Main Controller
集成AI池、路由器、工作空间管理和Claude执行的主控制器
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional

# 添加项目路径
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from main.vp import Perfect21
from features.git_workflow import GitHooks, WorkflowManager, BranchManager

logger = logging.getLogger("Perfect21")

class Perfect21Controller:
    """Perfect21 主控制器"""

    def __init__(self):
        """初始化Perfect21"""
        self.ai_pool = AIPool(claude_max_instances=3, codex_max_instances=2)
        self.router = IntelligentRouter(self.ai_pool)
        self.workspace_manager = WorkspaceManager()
        self.claude_executor = ClaudeExecutor()
        self.ai_butler = AIButler()

        # 系统状态
        self.is_running = False
        self.task_counter = 0

        logger.info("Perfect21 主控制器初始化完成")

    async def initialize(self):
        """异步初始化系统组件"""
        logger.info("正在初始化Perfect21系统...")

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
        logger.info("✅ Perfect21 系统初始化完成")

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

                # 智能超时设置：复杂任务给更长时间
                task_timeout = self._calculate_task_timeout(task_description)

                execution_result = await self.claude_executor.execute_task(
                    task_description, context, workspace=workspace_path, timeout=task_timeout
                )

                # 记录任务完成到56个SubAgent系统
                subagent_info = routing_result.get("subagent_info", {})
                subagent_name = subagent_info.get("subagent") if subagent_info else None

                self.router.record_task_completion(
                    task_id=routing_result["task_id"],
                    task_description=task_description,
                    task_type=routing_result["task_type"],
                    complexity=routing_result["complexity"],
                    execution_time=execution_result["execution_time"],
                    success=execution_result["success"],
                    ai_type=ai_type,
                    subagent_match=subagent_name,
                    error_message=execution_result.get("error") if not execution_result["success"] else None
                )

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
        logger.info("正在关闭Perfect21系统...")

        # 清理AI池中的错误实例
        self.ai_pool.cleanup_error_instances()

        # 归档空闲工作空间
        # (可选实现)

        self.is_running = False
        logger.info("✅ Perfect21 系统已关闭")

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

    def _calculate_task_timeout(self, task_description: str) -> int:
        """根据任务复杂度智能计算超时时间"""
        task_lower = task_description.lower()

        # 复杂任务关键词
        complex_keywords = [
            '分析', '检测', '优化', '架构', '设计', '重构',
            '性能', '安全', '质量', '全面', '完整', '详细',
            'analyze', 'detect', 'optimize', 'architecture',
            'refactor', 'performance', 'security', 'quality'
        ]

        # 简单任务关键词
        simple_keywords = [
            '创建', '添加', '修改', '删除', '显示', '列出',
            'create', 'add', 'modify', 'delete', 'show', 'list'
        ]

        # 默认超时：5分钟
        default_timeout = 300

        # 检查复杂任务
        complex_count = sum(1 for keyword in complex_keywords if keyword in task_lower)
        if complex_count >= 2:
            return 600  # 10分钟
        elif complex_count >= 1:
            return 450  # 7.5分钟

        # 检查简单任务
        simple_count = sum(1 for keyword in simple_keywords if keyword in task_lower)
        if simple_count >= 1 and complex_count == 0:
            return 180  # 3分钟

        # 根据任务描述长度调整
        if len(task_description) > 200:
            return default_timeout + 120  # 长任务+2分钟
        elif len(task_description) < 50:
            return 120  # 短任务2分钟

        return default_timeout