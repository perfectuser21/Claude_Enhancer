"""
Multi Workspace Manager - Mock Implementation for Testing
多工作空间管理器 - 管理多个开发工作空间
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path


class MultiWorkspaceManager:
    """多工作空间管理器"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path or ".perfect21/workspaces.json")
        self.config_path.parent.mkdir(exist_ok=True)
        self.workspaces: Dict[str, Dict[str, Any]] = {}
        self.current_workspace: Optional[str] = None
        self._load_workspaces()

    def create_workspace(self, workspace_config: Dict[str, Any]) -> Dict[str, Any]:
        """创建新工作空间"""
        try:
            name = workspace_config.get('name')
            if not name:
                return {'success': False, 'error': 'Workspace name is required'}

            if name in self.workspaces:
                return {'success': False, 'error': f'Workspace "{name}" already exists'}

            # 创建工作空间配置
            workspace = {
                'name': name,
                'path': workspace_config.get('path', f'/tmp/workspace_{name}'),
                'type': workspace_config.get('type', 'development'),
                'description': workspace_config.get('description', ''),
                'created_at': datetime.now().isoformat(),
                'last_accessed': datetime.now().isoformat(),
                'status': 'active',
                'settings': workspace_config.get('settings', {}),
                'metadata': {
                    'version': '1.0',
                    'creator': workspace_config.get('creator', 'system'),
                    'project_count': 0,
                    'total_size': 0
                }
            }

            # 模拟创建目录
            workspace_path = Path(workspace['path'])
            try:
                workspace_path.mkdir(parents=True, exist_ok=True)
                workspace['path_exists'] = True
            except:
                workspace['path_exists'] = False

            self.workspaces[name] = workspace
            self._save_workspaces()

            return {
                'success': True,
                'workspace_name': name,
                'workspace_path': workspace['path'],
                'message': f'Workspace "{name}" created successfully'
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to create workspace: {str(e)}'
            }

    def switch_workspace(self, workspace_name: str) -> Dict[str, Any]:
        """切换工作空间"""
        try:
            if workspace_name not in self.workspaces:
                return {'success': False, 'error': f'Workspace "{workspace_name}" not found'}

            # 更新当前工作空间
            previous_workspace = self.current_workspace
            self.current_workspace = workspace_name

            # 更新访问时间
            self.workspaces[workspace_name]['last_accessed'] = datetime.now().isoformat()

            self._save_workspaces()

            return {
                'success': True,
                'current_workspace': workspace_name,
                'previous_workspace': previous_workspace,
                'workspace_path': self.workspaces[workspace_name]['path'],
                'message': f'Switched to workspace "{workspace_name}"'
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to switch workspace: {str(e)}'
            }

    def list_workspaces(self) -> List[Dict[str, Any]]:
        """获取工作空间列表"""
        workspace_list = []

        for name, workspace in self.workspaces.items():
            workspace_info = {
                'name': name,
                'path': workspace['path'],
                'type': workspace['type'],
                'status': workspace['status'],
                'created_at': workspace['created_at'],
                'last_accessed': workspace['last_accessed'],
                'is_current': name == self.current_workspace,
                'path_exists': workspace.get('path_exists', False),
                'project_count': workspace['metadata'].get('project_count', 0)
            }
            workspace_list.append(workspace_info)

        # 按最后访问时间排序
        workspace_list.sort(key=lambda x: x['last_accessed'], reverse=True)

        return workspace_list

    def get_current_workspace(self) -> Optional[Dict[str, Any]]:
        """获取当前工作空间"""
        if self.current_workspace and self.current_workspace in self.workspaces:
            workspace = self.workspaces[self.current_workspace].copy()
            workspace['is_current'] = True
            return workspace
        return None

    def get_workspace(self, workspace_name: str) -> Optional[Dict[str, Any]]:
        """获取特定工作空间信息"""
        if workspace_name in self.workspaces:
            workspace = self.workspaces[workspace_name].copy()
            workspace['is_current'] = workspace_name == self.current_workspace
            return workspace
        return None

    def update_workspace(self, workspace_name: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """更新工作空间配置"""
        try:
            if workspace_name not in self.workspaces:
                return {'success': False, 'error': f'Workspace "{workspace_name}" not found'}

            workspace = self.workspaces[workspace_name]

            # 更新允许的字段
            updatable_fields = ['description', 'type', 'settings']
            for field in updatable_fields:
                if field in updates:
                    workspace[field] = updates[field]

            workspace['metadata']['last_modified'] = datetime.now().isoformat()
            workspace['metadata']['version'] = self._increment_version(
                workspace['metadata'].get('version', '1.0')
            )

            self._save_workspaces()

            return {
                'success': True,
                'workspace_name': workspace_name,
                'message': f'Workspace "{workspace_name}" updated successfully'
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to update workspace: {str(e)}'
            }

    def delete_workspace(self, workspace_name: str, force: bool = False) -> Dict[str, Any]:
        """删除工作空间"""
        try:
            if workspace_name not in self.workspaces:
                return {'success': False, 'error': f'Workspace "{workspace_name}" not found'}

            if workspace_name == self.current_workspace and not force:
                return {
                    'success': False,
                    'error': 'Cannot delete current workspace. Switch to another workspace first or use force=True'
                }

            # 删除工作空间
            del self.workspaces[workspace_name]

            # 如果删除的是当前工作空间，清除当前工作空间
            if workspace_name == self.current_workspace:
                self.current_workspace = None

            self._save_workspaces()

            return {
                'success': True,
                'workspace_name': workspace_name,
                'message': f'Workspace "{workspace_name}" deleted successfully'
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to delete workspace: {str(e)}'
            }

    def get_workspace_statistics(self) -> Dict[str, Any]:
        """获取工作空间统计信息"""
        total_workspaces = len(self.workspaces)
        active_workspaces = len([w for w in self.workspaces.values() if w['status'] == 'active'])

        # 统计工作空间类型
        type_counts = {}
        for workspace in self.workspaces.values():
            workspace_type = workspace.get('type', 'unknown')
            type_counts[workspace_type] = type_counts.get(workspace_type, 0) + 1

        # 计算总项目数
        total_projects = sum(
            workspace['metadata'].get('project_count', 0)
            for workspace in self.workspaces.values()
        )

        return {
            'total_workspaces': total_workspaces,
            'active_workspaces': active_workspaces,
            'inactive_workspaces': total_workspaces - active_workspaces,
            'current_workspace': self.current_workspace,
            'workspace_types': type_counts,
            'total_projects': total_projects,
            'average_projects_per_workspace': total_projects / total_workspaces if total_workspaces > 0 else 0
        }

    def clone_workspace(self, source_name: str, target_name: str, target_path: Optional[str] = None) -> Dict[str, Any]:
        """克隆工作空间"""
        try:
            if source_name not in self.workspaces:
                return {'success': False, 'error': f'Source workspace "{source_name}" not found'}

            if target_name in self.workspaces:
                return {'success': False, 'error': f'Target workspace "{target_name}" already exists'}

            # 复制源工作空间配置
            source_workspace = self.workspaces[source_name]
            target_workspace = source_workspace.copy()

            # 更新目标工作空间信息
            target_workspace['name'] = target_name
            target_workspace['path'] = target_path or f'/tmp/workspace_{target_name}'
            target_workspace['created_at'] = datetime.now().isoformat()
            target_workspace['last_accessed'] = datetime.now().isoformat()
            target_workspace['metadata'] = source_workspace['metadata'].copy()
            target_workspace['metadata']['cloned_from'] = source_name
            target_workspace['metadata']['version'] = '1.0'

            # 模拟创建目录
            workspace_path = Path(target_workspace['path'])
            try:
                workspace_path.mkdir(parents=True, exist_ok=True)
                target_workspace['path_exists'] = True
            except:
                target_workspace['path_exists'] = False

            self.workspaces[target_name] = target_workspace
            self._save_workspaces()

            return {
                'success': True,
                'source_workspace': source_name,
                'target_workspace': target_name,
                'target_path': target_workspace['path'],
                'message': f'Workspace "{target_name}" cloned from "{source_name}" successfully'
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to clone workspace: {str(e)}'
            }

    def _load_workspaces(self) -> None:
        """加载工作空间配置"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.workspaces = data.get('workspaces', {})
                    self.current_workspace = data.get('current_workspace')
        except Exception:
            self.workspaces = {}
            self.current_workspace = None

    def _save_workspaces(self) -> None:
        """保存工作空间配置"""
        try:
            data = {
                'metadata': {
                    'last_updated': datetime.now().isoformat(),
                    'total_workspaces': len(self.workspaces),
                    'format_version': '1.0'
                },
                'current_workspace': self.current_workspace,
                'workspaces': self.workspaces
            }

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception:
            # 静默失败
            pass

    def _increment_version(self, current_version: str) -> str:
        """递增版本号"""
        try:
            parts = current_version.split('.')
            if len(parts) >= 2:
                major, minor = int(parts[0]), int(parts[1])
                return f"{major}.{minor + 1}"
            else:
                return "1.1"
        except:
            return "1.1"