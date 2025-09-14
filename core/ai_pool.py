#!/usr/bin/env python3
"""
AI实例池管理器
管理Claude Code和Codex实例的并行执行
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("AIPool")

class AIInstanceType(Enum):
    CLAUDE = "claude"
    CODEX = "codex"

class AIInstanceStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"

@dataclass
class AIInstance:
    """AI实例状态管理"""
    instance_id: str
    instance_type: AIInstanceType
    status: AIInstanceStatus
    current_task: Optional[str] = None
    workspace: Optional[str] = None
    created_at: datetime = None
    last_activity: datetime = None
    task_count: int = 0
    error_count: int = 0

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_activity is None:
            self.last_activity = datetime.now()

class AIPool:
    """AI实例池管理器"""

    def __init__(self, claude_max_instances=3, codex_max_instances=2):
        """初始化AI池"""
        self.claude_max_instances = claude_max_instances
        self.codex_max_instances = codex_max_instances
        self.instances: Dict[str, AIInstance] = {}
        self.task_queue = asyncio.Queue()
        self.running = False
        logger.info(f"AI池初始化: Claude={claude_max_instances}, Codex={codex_max_instances}")

    def create_instance(self, instance_type: AIInstanceType, workspace: str = None) -> str:
        """创建新的AI实例"""
        if instance_type == AIInstanceType.CLAUDE:
            current_count = len([i for i in self.instances.values()
                               if i.instance_type == AIInstanceType.CLAUDE])
            if current_count >= self.claude_max_instances:
                raise RuntimeError(f"Claude实例数已达上限: {self.claude_max_instances}")

        elif instance_type == AIInstanceType.CODEX:
            current_count = len([i for i in self.instances.values()
                               if i.instance_type == AIInstanceType.CODEX])
            if current_count >= self.codex_max_instances:
                raise RuntimeError(f"Codex实例数已达上限: {self.codex_max_instances}")

        # 生成实例ID
        instance_id = f"{instance_type.value}_{len(self.instances)}_{int(time.time())}"

        # 创建实例
        instance = AIInstance(
            instance_id=instance_id,
            instance_type=instance_type,
            status=AIInstanceStatus.IDLE,
            workspace=workspace
        )

        self.instances[instance_id] = instance
        logger.info(f"创建AI实例: {instance_id} (workspace: {workspace})")
        return instance_id

    def get_available_instance(self, instance_type: AIInstanceType, workspace: str = None) -> Optional[str]:
        """获取可用的AI实例"""
        available_instances = [
            instance_id for instance_id, instance in self.instances.items()
            if (instance.instance_type == instance_type and
                instance.status == AIInstanceStatus.IDLE and
                (workspace is None or instance.workspace == workspace))
        ]

        if available_instances:
            return available_instances[0]

        # 尝试创建新实例
        try:
            return self.create_instance(instance_type, workspace)
        except RuntimeError:
            logger.warning(f"无法创建新{instance_type.value}实例，已达上限")
            return None

    def assign_task(self, instance_id: str, task: str) -> bool:
        """为实例分配任务"""
        if instance_id not in self.instances:
            return False

        instance = self.instances[instance_id]
        if instance.status != AIInstanceStatus.IDLE:
            return False

        instance.status = AIInstanceStatus.BUSY
        instance.current_task = task
        instance.last_activity = datetime.now()
        instance.task_count += 1

        logger.info(f"任务分配: {instance_id} -> {task[:50]}...")
        return True

    def complete_task(self, instance_id: str, success: bool = True) -> bool:
        """完成任务"""
        if instance_id not in self.instances:
            return False

        instance = self.instances[instance_id]

        if success:
            instance.status = AIInstanceStatus.IDLE
        else:
            instance.status = AIInstanceStatus.ERROR
            instance.error_count += 1

        instance.current_task = None
        instance.last_activity = datetime.now()

        logger.info(f"任务完成: {instance_id} (成功: {success})")
        return True

    def get_pool_status(self) -> Dict[str, Any]:
        """获取池状态"""
        claude_instances = [i for i in self.instances.values()
                          if i.instance_type == AIInstanceType.CLAUDE]
        codex_instances = [i for i in self.instances.values()
                         if i.instance_type == AIInstanceType.CODEX]

        return {
            "total_instances": len(self.instances),
            "claude": {
                "total": len(claude_instances),
                "idle": len([i for i in claude_instances if i.status == AIInstanceStatus.IDLE]),
                "busy": len([i for i in claude_instances if i.status == AIInstanceStatus.BUSY]),
                "error": len([i for i in claude_instances if i.status == AIInstanceStatus.ERROR])
            },
            "codex": {
                "total": len(codex_instances),
                "idle": len([i for i in codex_instances if i.status == AIInstanceStatus.IDLE]),
                "busy": len([i for i in codex_instances if i.status == AIInstanceStatus.BUSY]),
                "error": len([i for i in codex_instances if i.status == AIInstanceStatus.ERROR])
            },
            "queue_size": self.task_queue.qsize() if hasattr(self.task_queue, 'qsize') else 0
        }

    def cleanup_error_instances(self):
        """清理错误实例"""
        error_instances = [
            instance_id for instance_id, instance in self.instances.items()
            if instance.status == AIInstanceStatus.ERROR and
               (datetime.now() - instance.last_activity).seconds > 300  # 5分钟后清理
        ]

        for instance_id in error_instances:
            logger.info(f"清理错误实例: {instance_id}")
            del self.instances[instance_id]

    def get_instance_info(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """获取实例详细信息"""
        if instance_id not in self.instances:
            return None

        instance = self.instances[instance_id]
        return {
            "instance_id": instance.instance_id,
            "type": instance.instance_type.value,
            "status": instance.status.value,
            "workspace": instance.workspace,
            "current_task": instance.current_task,
            "created_at": instance.created_at.isoformat(),
            "last_activity": instance.last_activity.isoformat(),
            "task_count": instance.task_count,
            "error_count": instance.error_count
        }