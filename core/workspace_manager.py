#!/usr/bin/env python3
"""
工作空间管理器
管理多个并行开发项目的工作空间隔离
"""

import os
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger("WorkspaceManager")

@dataclass
class WorkspaceInfo:
    """工作空间信息"""
    workspace_id: str
    name: str
    description: str
    path: str
    created_at: datetime
    last_activity: datetime
    project_type: str = "general"
    status: str = "active"  # active, paused, archived
    ai_instances: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.ai_instances is None:
            self.ai_instances = []
        if self.metadata is None:
            self.metadata = {}

class WorkspaceManager:
    """工作空间管理器"""

    def __init__(self, base_directory: str = "/tmp/vibepilot_workspaces"):
        """初始化工作空间管理器"""
        self.base_directory = Path(base_directory)
        self.config_file = self.base_directory / "workspaces.json"
        self.workspaces: Dict[str, WorkspaceInfo] = {}

        # 确保基础目录存在
        self.base_directory.mkdir(parents=True, exist_ok=True)

        # 加载现有配置
        self._load_workspaces()
        logger.info(f"工作空间管理器初始化: {self.base_directory}")

    def _load_workspaces(self):
        """加载工作空间配置"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                for ws_id, ws_data in data.items():
                    # 转换时间戳
                    ws_data['created_at'] = datetime.fromisoformat(ws_data['created_at'])
                    ws_data['last_activity'] = datetime.fromisoformat(ws_data['last_activity'])

                    self.workspaces[ws_id] = WorkspaceInfo(**ws_data)

                logger.info(f"加载{len(self.workspaces)}个工作空间")
            except Exception as e:
                logger.error(f"加载工作空间配置失败: {e}")

    def _save_workspaces(self):
        """保存工作空间配置"""
        try:
            data = {}
            for ws_id, workspace in self.workspaces.items():
                ws_dict = asdict(workspace)
                # 转换时间戳为字符串
                ws_dict['created_at'] = workspace.created_at.isoformat()
                ws_dict['last_activity'] = workspace.last_activity.isoformat()
                data[ws_id] = ws_dict

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug("工作空间配置已保存")
        except Exception as e:
            logger.error(f"保存工作空间配置失败: {e}")

    def create_workspace(self, name: str, description: str = "",
                        project_type: str = "general",
                        source_template: str = None) -> Optional[str]:
        """创建新工作空间"""

        # 生成工作空间ID
        timestamp = int(datetime.now().timestamp())
        workspace_id = f"ws_{name.lower().replace(' ', '_')}_{timestamp}"

        # 创建工作空间目录
        workspace_path = self.base_directory / workspace_id
        workspace_path.mkdir(parents=True, exist_ok=True)

        # 如果有模板，复制模板内容
        if source_template and Path(source_template).exists():
            try:
                shutil.copytree(source_template, workspace_path, dirs_exist_ok=True)
                logger.info(f"从模板复制: {source_template} -> {workspace_path}")
            except Exception as e:
                logger.error(f"复制模板失败: {e}")

        # 创建基础目录结构
        (workspace_path / "src").mkdir(exist_ok=True)
        (workspace_path / "tests").mkdir(exist_ok=True)
        (workspace_path / "docs").mkdir(exist_ok=True)
        (workspace_path / ".vibepilot").mkdir(exist_ok=True)

        # 创建工作空间配置文件
        workspace_config = {
            "name": name,
            "description": description,
            "project_type": project_type,
            "created_at": datetime.now().isoformat(),
            "workspace_id": workspace_id
        }

        config_path = workspace_path / ".vibepilot" / "workspace.json"
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(workspace_config, f, indent=2, ensure_ascii=False)

        # 记录工作空间信息
        workspace_info = WorkspaceInfo(
            workspace_id=workspace_id,
            name=name,
            description=description,
            path=str(workspace_path),
            created_at=datetime.now(),
            last_activity=datetime.now(),
            project_type=project_type,
            status="active"
        )

        self.workspaces[workspace_id] = workspace_info
        self._save_workspaces()

        logger.info(f"创建工作空间: {workspace_id} ({name})")
        return workspace_id

    def get_workspace(self, workspace_id: str) -> Optional[WorkspaceInfo]:
        """获取工作空间信息"""
        return self.workspaces.get(workspace_id)

    def list_workspaces(self, status: str = None) -> List[WorkspaceInfo]:
        """列出工作空间"""
        workspaces = list(self.workspaces.values())

        if status:
            workspaces = [ws for ws in workspaces if ws.status == status]

        # 按最后活动时间排序
        workspaces.sort(key=lambda x: x.last_activity, reverse=True)
        return workspaces

    def update_workspace_activity(self, workspace_id: str):
        """更新工作空间活动时间"""
        if workspace_id in self.workspaces:
            self.workspaces[workspace_id].last_activity = datetime.now()
            self._save_workspaces()

    def assign_ai_instance(self, workspace_id: str, instance_id: str) -> bool:
        """为工作空间分配AI实例"""
        if workspace_id not in self.workspaces:
            return False

        workspace = self.workspaces[workspace_id]
        if instance_id not in workspace.ai_instances:
            workspace.ai_instances.append(instance_id)
            self.update_workspace_activity(workspace_id)
            self._save_workspaces()
            logger.info(f"AI实例分配: {instance_id} -> {workspace_id}")

        return True

    def release_ai_instance(self, workspace_id: str, instance_id: str) -> bool:
        """释放工作空间的AI实例"""
        if workspace_id not in self.workspaces:
            return False

        workspace = self.workspaces[workspace_id]
        if instance_id in workspace.ai_instances:
            workspace.ai_instances.remove(instance_id)
            self.update_workspace_activity(workspace_id)
            self._save_workspaces()
            logger.info(f"AI实例释放: {instance_id} <- {workspace_id}")

        return True

    def archive_workspace(self, workspace_id: str) -> bool:
        """归档工作空间"""
        if workspace_id not in self.workspaces:
            return False

        workspace = self.workspaces[workspace_id]
        workspace.status = "archived"
        workspace.last_activity = datetime.now()

        # 清空AI实例分配
        workspace.ai_instances = []

        self._save_workspaces()
        logger.info(f"工作空间已归档: {workspace_id}")
        return True

    def delete_workspace(self, workspace_id: str, force: bool = False) -> bool:
        """删除工作空间"""
        if workspace_id not in self.workspaces:
            return False

        workspace = self.workspaces[workspace_id]

        # 检查是否有活跃的AI实例
        if workspace.ai_instances and not force:
            logger.warning(f"工作空间{workspace_id}有活跃AI实例，无法删除")
            return False

        # 删除文件系统中的目录
        workspace_path = Path(workspace.path)
        if workspace_path.exists():
            try:
                shutil.rmtree(workspace_path)
                logger.info(f"删除工作空间目录: {workspace_path}")
            except Exception as e:
                logger.error(f"删除目录失败: {e}")
                if not force:
                    return False

        # 从配置中移除
        del self.workspaces[workspace_id]
        self._save_workspaces()

        logger.info(f"工作空间已删除: {workspace_id}")
        return True

    def get_workspace_stats(self) -> Dict[str, Any]:
        """获取工作空间统计信息"""
        total = len(self.workspaces)
        active = len([ws for ws in self.workspaces.values() if ws.status == "active"])
        archived = len([ws for ws in self.workspaces.values() if ws.status == "archived"])

        # 计算AI实例使用情况
        total_ai_instances = sum(len(ws.ai_instances) for ws in self.workspaces.values())

        # 按项目类型统计
        project_types = {}
        for workspace in self.workspaces.values():
            project_type = workspace.project_type
            project_types[project_type] = project_types.get(project_type, 0) + 1

        return {
            "total_workspaces": total,
            "active_workspaces": active,
            "archived_workspaces": archived,
            "total_ai_instances": total_ai_instances,
            "project_types": project_types,
            "base_directory": str(self.base_directory)
        }

    def cleanup_stale_workspaces(self, days: int = 30) -> int:
        """清理长期未活动的工作空间"""
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=days)
        stale_workspaces = [
            ws_id for ws_id, ws in self.workspaces.items()
            if ws.last_activity < cutoff_date and ws.status != "active"
        ]

        cleaned = 0
        for ws_id in stale_workspaces:
            if self.delete_workspace(ws_id, force=True):
                cleaned += 1

        logger.info(f"清理过期工作空间: {cleaned}个")
        return cleaned