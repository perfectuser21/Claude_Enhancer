#!/usr/bin/env python3
"""
Perfect21 多工作空间管理器
===============================

智能管理多个并行开发工作空间，支持单人多功能并行开发
每个工作空间独立运行，自动协调合并，避免冲突

核心理念：
- 工作空间隔离：每个feature独立分支和端口
- 智能切换：基于上下文自动推荐工作空间
- 自动协调：冲突检测和合并建议
- 状态同步：实时监控所有工作空间状态
"""

import os
import sys
import json
import subprocess
import shutil
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import asyncio
import threading
from contextlib import contextmanager, asynccontextmanager
import weakref
import atexit

# Import resource manager
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from modules.resource_manager import ResourceManager, ResourceType, managed_file

class WorkspaceStatus(Enum):
    """工作空间状态"""
    ACTIVE = "active"           # 活跃开发中
    IDLE = "idle"              # 闲置但保持
    PAUSED = "paused"          # 暂停开发
    MERGING = "merging"        # 合并进行中
    CONFLICT = "conflict"      # 存在冲突
    ARCHIVED = "archived"      # 已归档

class WorkspaceType(Enum):
    """工作空间类型"""
    FEATURE = "feature"        # 功能开发
    BUGFIX = "bugfix"         # Bug修复
    EXPERIMENT = "experiment"  # 实验性开发
    HOTFIX = "hotfix"         # 热修复
    REFACTOR = "refactor"     # 重构

@dataclass
class WorkspaceConfig:
    """工作空间配置"""
    workspace_id: str
    name: str
    description: str
    workspace_type: WorkspaceType
    base_branch: str
    feature_branch: str
    dev_port: int
    api_port: Optional[int]
    created_at: str
    last_accessed: str
    status: WorkspaceStatus
    priority: int  # 1-10，优先级
    tags: List[str]
    dependencies: List[str]  # 依赖的其他工作空间

    def to_dict(self) -> Dict:
        """转换为字典"""
        data = asdict(self)
        data['workspace_type'] = self.workspace_type.value
        data['status'] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'WorkspaceConfig':
        """从字典创建"""
        data['workspace_type'] = WorkspaceType(data['workspace_type'])
        data['status'] = WorkspaceStatus(data['status'])
        return cls(**data)

class WorkspaceManager:
    """多工作空间管理器 - 带资源管理"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.workspace_dir = self.project_root / ".perfect21" / "workspaces"
        self.config_file = self.workspace_dir / "workspace_config.json"
        self.port_range = (3000, 4000)  # 可用端口范围

        # 资源管理
        self._resource_manager = ResourceManager()
        self._active_processes: Dict[str, subprocess.Popen] = {}
        self._file_handles: Dict[str, Any] = {}
        self._temp_dirs: List[Path] = []
        self._lock = threading.RLock()
        self._cleanup_registered = False

        self._ensure_directories()
        self._load_config()

        # 注册资源管理器
        manager_id = f"workspace_manager_{id(self)}"
        self._resource_manager.register_resource(
            manager_id, self, ResourceType.OTHER,
            cleanup_callback=self._cleanup_resources
        )

        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        # 注册清理函数
        if not self._cleanup_registered:
            atexit.register(self._emergency_cleanup)
            self._cleanup_registered = True

    def _ensure_directories(self):
        """确保目录结构存在"""
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    def _load_config(self):
        """加载工作空间配置"""
        if self.config_file.exists():
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.workspaces = {
                    ws_id: WorkspaceConfig.from_dict(ws_data)
                    for ws_id, ws_data in data.items()
                }
        else:
            self.workspaces = {}

    def _save_config(self):
        """保存工作空间配置"""
        data = {
            ws_id: ws_config.to_dict()
            for ws_id, ws_config in self.workspaces.items()
        }
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _get_available_port(self, preferred_port: Optional[int] = None) -> int:
        """获取可用端口"""
        used_ports = {ws.dev_port for ws in self.workspaces.values()}
        for ws in self.workspaces.values():
            if ws.api_port:
                used_ports.add(ws.api_port)

        if preferred_port and preferred_port not in used_ports:
            return preferred_port

        for port in range(self.port_range[0], self.port_range[1]):
            if port not in used_ports:
                return port

        raise RuntimeError("No available ports in range")

    def _run_git_command(self, command: List[str], cwd: Optional[str] = None) -> Tuple[bool, str]:
        """执行Git命令"""
        try:
            result = subprocess.run(
                ['git'] + command,
                cwd=cwd or str(self.project_root),
                capture_output=True,
                text=True,
                check=True
            )
            return True, result.stdout.strip()
        except subprocess.CalledProcessError as e:
            # 某些Git命令即使成功也可能返回非零状态码
            error_output = e.stderr.strip()
            stdout_output = e.stdout.strip() if e.stdout else ""

            # 对于checkout命令，Hook错误不应该被视为命令失败
            if command[0] == 'checkout' and "Switched to" in error_output:
                return True, error_output

            return False, error_output or stdout_output

    def create_workspace(
        self,
        name: str,
        description: str,
        workspace_type: WorkspaceType,
        base_branch: str = "main",
        preferred_port: Optional[int] = None,
        tags: Optional[List[str]] = None,
        priority: int = 5
    ) -> str:
        """创建新工作空间"""

        # 生成工作空间ID
        workspace_id = f"{workspace_type.value}_{name.lower().replace(' ', '_')}"

        if workspace_id in self.workspaces:
            raise ValueError(f"Workspace {workspace_id} already exists")

        # 创建功能分支
        feature_branch = f"feature/{name.lower().replace(' ', '_')}"
        success, output = self._run_git_command(['checkout', '-b', feature_branch, base_branch])
        if not success and "already exists" not in output:
            raise RuntimeError(f"Failed to create branch: {output}")

        # 如果分支已存在，切换到该分支
        if "already exists" in output:
            success, output = self._run_git_command(['checkout', feature_branch])
            if not success:
                raise RuntimeError(f"Failed to switch to existing branch: {output}")

        # 获取可用端口
        dev_port = self._get_available_port(preferred_port)
        api_port = self._get_available_port(dev_port + 1) if workspace_type != WorkspaceType.EXPERIMENT else None

        # 创建工作空间配置
        workspace = WorkspaceConfig(
            workspace_id=workspace_id,
            name=name,
            description=description,
            workspace_type=workspace_type,
            base_branch=base_branch,
            feature_branch=feature_branch,
            dev_port=dev_port,
            api_port=api_port,
            created_at=datetime.now().isoformat(),
            last_accessed=datetime.now().isoformat(),
            status=WorkspaceStatus.ACTIVE,
            priority=priority,
            tags=tags or [],
            dependencies=[]
        )

        # 创建工作空间目录
        workspace_path = self.workspace_dir / workspace_id
        workspace_path.mkdir(exist_ok=True)

        # 创建工作空间专用配置
        workspace_config = {
            "name": name,
            "dev_port": dev_port,
            "api_port": api_port,
            "branch": feature_branch,
            "created_at": workspace.created_at
        }

        with open(workspace_path / "config.json", 'w', encoding='utf-8') as f:
            json.dump(workspace_config, f, indent=2, ensure_ascii=False)

        # 保存工作空间
        self.workspaces[workspace_id] = workspace
        self._save_config()

        self.logger.info(f"Created workspace: {workspace_id} on port {dev_port}")
        return workspace_id

    def switch_workspace(self, workspace_id: str) -> bool:
        """切换到指定工作空间"""
        if workspace_id not in self.workspaces:
            self.logger.error(f"Workspace {workspace_id} not found")
            return False

        workspace = self.workspaces[workspace_id]

        # 检查当前是否有未提交的更改
        success, output = self._run_git_command(['status', '--porcelain'])
        if success and output.strip():
            self.logger.warning("有未提交的更改，请先提交或暂存")
            return False

        # 切换到工作空间分支
        success, output = self._run_git_command(['checkout', workspace.feature_branch])
        if not success:
            self.logger.error(f"Failed to switch branch: {output}")
            return False

        # 更新最后访问时间
        workspace.last_accessed = datetime.now().isoformat()
        workspace.status = WorkspaceStatus.ACTIVE
        self._save_config()

        self.logger.info(f"Switched to workspace: {workspace_id}")
        return True

    def pause_workspace(self, workspace_id: str) -> bool:
        """暂停工作空间"""
        if workspace_id not in self.workspaces:
            return False

        workspace = self.workspaces[workspace_id]

        # 暂存当前更改
        success, output = self._run_git_command(['stash', 'push', '-m', f'Auto stash for workspace {workspace_id}'])
        if not success:
            self.logger.warning(f"Failed to stash changes: {output}")

        workspace.status = WorkspaceStatus.PAUSED
        self._save_config()

        self.logger.info(f"Paused workspace: {workspace_id}")
        return True

    def resume_workspace(self, workspace_id: str) -> bool:
        """恢复工作空间"""
        if workspace_id not in self.workspaces:
            return False

        workspace = self.workspaces[workspace_id]

        # 切换到工作空间
        if not self.switch_workspace(workspace_id):
            return False

        # 恢复暂存的更改
        success, output = self._run_git_command(['stash', 'list'])
        if success and f'workspace {workspace_id}' in output:
            success, output = self._run_git_command(['stash', 'pop'])
            if not success:
                self.logger.warning(f"Failed to restore stashed changes: {output}")

        workspace.status = WorkspaceStatus.ACTIVE
        self._save_config()

        self.logger.info(f"Resumed workspace: {workspace_id}")
        return True

    def list_workspaces(self) -> List[Dict]:
        """列出所有工作空间"""
        workspaces_info = []

        for workspace_id, workspace in self.workspaces.items():
            # 获取分支状态
            success, output = self._run_git_command(['rev-list', '--count', f'{workspace.base_branch}..{workspace.feature_branch}'])
            commits_ahead = int(output) if success else 0

            success, output = self._run_git_command(['rev-list', '--count', f'{workspace.feature_branch}..{workspace.base_branch}'])
            commits_behind = int(output) if success else 0

            workspaces_info.append({
                'id': workspace_id,
                'name': workspace.name,
                'type': workspace.workspace_type.value,
                'status': workspace.status.value,
                'branch': workspace.feature_branch,
                'dev_port': workspace.dev_port,
                'api_port': workspace.api_port,
                'priority': workspace.priority,
                'commits_ahead': commits_ahead,
                'commits_behind': commits_behind,
                'last_accessed': workspace.last_accessed,
                'tags': workspace.tags
            })

        return sorted(workspaces_info, key=lambda x: x['last_accessed'], reverse=True)

    def detect_conflicts(self, workspace_id: str) -> Dict:
        """检测工作空间冲突"""
        if workspace_id not in self.workspaces:
            return {"error": "Workspace not found"}

        workspace = self.workspaces[workspace_id]

        # 检查与基分支的冲突
        success, output = self._run_git_command(['merge-tree', workspace.base_branch, workspace.feature_branch])

        conflicts = []
        if success and output:
            # 解析冲突信息
            lines = output.split('\n')
            for line in lines:
                if 'changed in both' in line or 'conflict' in line.lower():
                    conflicts.append(line.strip())

        # 检查与其他活跃工作空间的潜在冲突
        file_changes = self._get_workspace_file_changes(workspace_id)
        potential_conflicts = []

        for other_id, other_workspace in self.workspaces.items():
            if other_id != workspace_id and other_workspace.status == WorkspaceStatus.ACTIVE:
                other_changes = self._get_workspace_file_changes(other_id)
                common_files = set(file_changes) & set(other_changes)
                if common_files:
                    potential_conflicts.append({
                        'workspace': other_id,
                        'common_files': list(common_files)
                    })

        return {
            'direct_conflicts': conflicts,
            'potential_conflicts': potential_conflicts,
            'file_changes': file_changes
        }

    def _get_workspace_file_changes(self, workspace_id: str) -> List[str]:
        """获取工作空间的文件更改"""
        workspace = self.workspaces[workspace_id]
        success, output = self._run_git_command(['diff', '--name-only', workspace.base_branch, workspace.feature_branch])

        if success:
            return [line.strip() for line in output.split('\n') if line.strip()]
        return []

    def suggest_merge_order(self) -> List[str]:
        """建议合并顺序"""
        active_workspaces = [
            (ws_id, ws) for ws_id, ws in self.workspaces.items()
            if ws.status in [WorkspaceStatus.ACTIVE, WorkspaceStatus.IDLE]
        ]

        # 按优先级和依赖关系排序
        def sort_key(item):
            ws_id, ws = item
            return (ws.priority, len(ws.dependencies))

        sorted_workspaces = sorted(active_workspaces, key=sort_key, reverse=True)
        return [ws_id for ws_id, _ in sorted_workspaces]

    def auto_merge_workspace(self, workspace_id: str, dry_run: bool = True) -> Dict:
        """自动合并工作空间"""
        if workspace_id not in self.workspaces:
            return {"error": "Workspace not found"}

        workspace = self.workspaces[workspace_id]

        # 检查冲突
        conflict_info = self.detect_conflicts(workspace_id)
        if conflict_info['direct_conflicts']:
            return {
                "error": "Cannot auto-merge with conflicts",
                "conflicts": conflict_info['direct_conflicts']
            }

        if dry_run:
            return {
                "success": True,
                "message": f"Workspace {workspace_id} can be safely merged",
                "file_changes": conflict_info['file_changes'],
                "potential_conflicts": conflict_info['potential_conflicts']
            }

        # 实际合并
        original_branch = self._get_current_branch()

        try:
            # 切换到基分支
            success, output = self._run_git_command(['checkout', workspace.base_branch])
            if not success:
                return {"error": f"Failed to checkout base branch: {output}"}

            # 合并功能分支
            success, output = self._run_git_command(['merge', '--no-ff', workspace.feature_branch])
            if not success:
                return {"error": f"Merge failed: {output}"}

            # 更新工作空间状态
            workspace.status = WorkspaceStatus.ARCHIVED
            self._save_config()

            return {
                "success": True,
                "message": f"Successfully merged workspace {workspace_id}",
                "merged_files": conflict_info['file_changes']
            }

        except Exception as e:
            # 恢复到原始分支
            self._run_git_command(['checkout', original_branch])
            return {"error": f"Merge failed with exception: {str(e)}"}

    def _get_current_branch(self) -> str:
        """获取当前分支"""
        success, output = self._run_git_command(['branch', '--show-current'])
        return output if success else "main"

    def cleanup_workspace(self, workspace_id: str, force: bool = False) -> bool:
        """清理工作空间"""
        if workspace_id not in self.workspaces:
            return False

        workspace = self.workspaces[workspace_id]

        # 检查是否可以安全删除
        if not force and workspace.status not in [WorkspaceStatus.ARCHIVED, WorkspaceStatus.IDLE]:
            self.logger.warning(f"Workspace {workspace_id} is {workspace.status.value}, use force=True to delete")
            return False

        # 删除分支
        success, output = self._run_git_command(['branch', '-D', workspace.feature_branch])
        if not success:
            self.logger.warning(f"Failed to delete branch: {output}")

        # 删除工作空间目录
        workspace_path = self.workspace_dir / workspace_id
        if workspace_path.exists():
            shutil.rmtree(workspace_path)

        # 从配置中移除
        del self.workspaces[workspace_id]
        self._save_config()

        self.logger.info(f"Cleaned up workspace: {workspace_id}")
        return True

    def get_workspace_stats(self) -> Dict:
        """获取工作空间统计信息"""
        status_counts = {}
        type_counts = {}

        for workspace in self.workspaces.values():
            status_counts[workspace.status.value] = status_counts.get(workspace.status.value, 0) + 1
            type_counts[workspace.workspace_type.value] = type_counts.get(workspace.workspace_type.value, 0) + 1

        return {
            'total_workspaces': len(self.workspaces),
            'by_status': status_counts,
            'by_type': type_counts,
            'port_usage': [ws.dev_port for ws in self.workspaces.values()],
            'active_count': len([ws for ws in self.workspaces.values() if ws.status == WorkspaceStatus.ACTIVE])
        }

    def _cleanup_process(self, process_id: str):
        """清理进程资源"""
        with self._lock:
            if process_id in self._active_processes:
                process = self._active_processes[process_id]
                try:
                    if process.poll() is None:  # 进程仍在运行
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
                            process.wait()
                    del self._active_processes[process_id]
                    self.logger.info(f"清理进程: {process_id}")
                except Exception as e:
                    self.logger.error(f"清理进程 {process_id} 失败: {e}")

    def _cleanup_resources(self):
        """清理所有资源"""
        with self._lock:
            # 清理进程
            for process_id in list(self._active_processes.keys()):
                self._cleanup_process(process_id)

            # 清理文件句柄
            for handle_id, handle in list(self._file_handles.items()):
                try:
                    if hasattr(handle, 'close'):
                        handle.close()
                    self.logger.info(f"清理文件句柄: {handle_id}")
                except Exception as e:
                    self.logger.error(f"清理文件句柄 {handle_id} 失败: {e}")
            self._file_handles.clear()

            # 清理临时目录
            for temp_dir in self._temp_dirs[:]:
                try:
                    if temp_dir.exists():
                        shutil.rmtree(temp_dir)
                        self.logger.info(f"清理临时目录: {temp_dir}")
                except Exception as e:
                    self.logger.error(f"清理临时目录 {temp_dir} 失败: {e}")
            self._temp_dirs.clear()

    def _emergency_cleanup(self):
        """紧急清理资源"""
        try:
            self._cleanup_resources()
            # 清理资源管理器
            if hasattr(self, '_resource_manager'):
                self._resource_manager.cleanup_all()
        except Exception as e:
            # 紧急清理不应该抛出异常
            print(f"紧急清理失败: {e}")

    @contextmanager
    def managed_temp_dir(self, prefix: str = "workspace_"):
        """管理临时目录的上下文管理器"""
        temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
        with self._lock:
            self._temp_dirs.append(temp_dir)

        try:
            yield temp_dir
        finally:
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                with self._lock:
                    if temp_dir in self._temp_dirs:
                        self._temp_dirs.remove(temp_dir)
            except Exception as e:
                self.logger.error(f"清理临时目录失败: {e}")

    def __enter__(self):
        """进入上下文管理器"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文管理器"""
        self._cleanup_resources()

    async def __aenter__(self):
        """异步进入上下文管理器"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步退出上下文管理器"""
        self._cleanup_resources()

    def recommend_workspace(self, task_description: str) -> Optional[str]:
        """基于任务描述推荐工作空间"""
        task_lower = task_description.lower()

        # 关键词匹配
        keywords_mapping = {
            'bug': WorkspaceType.BUGFIX,
            'fix': WorkspaceType.BUGFIX,
            'hotfix': WorkspaceType.HOTFIX,
            'urgent': WorkspaceType.HOTFIX,
            'refactor': WorkspaceType.REFACTOR,
            'experiment': WorkspaceType.EXPERIMENT,
            'test': WorkspaceType.EXPERIMENT,
            'feature': WorkspaceType.FEATURE,
        }

        recommended_type = None
        for keyword, workspace_type in keywords_mapping.items():
            if keyword in task_lower:
                recommended_type = workspace_type
                break

        if not recommended_type:
            recommended_type = WorkspaceType.FEATURE

        # 寻找匹配的现有工作空间
        for ws_id, workspace in self.workspaces.items():
            if (workspace.workspace_type == recommended_type and
                workspace.status in [WorkspaceStatus.IDLE, WorkspaceStatus.PAUSED]):

                # 检查标签或名称匹配
                if any(tag in task_lower for tag in workspace.tags):
                    return ws_id
                if workspace.name.lower() in task_lower:
                    return ws_id

        return None

# 受管理的工作空间管理器上下文管理器
@contextmanager
def managed_workspace_manager(project_root: str):
    """受管理的工作空间管理器"""
    manager = WorkspaceManager(project_root)
    try:
        yield manager
    finally:
        manager._cleanup_resources()

@asynccontextmanager
async def managed_workspace_manager_async(project_root: str):
    """异步受管理的工作空间管理器"""
    manager = WorkspaceManager(project_root)
    try:
        yield manager
    finally:
        manager._cleanup_resources()

def main():
    """命令行界面"""
    import argparse

    parser = argparse.ArgumentParser(description="Perfect21 多工作空间管理器")
    parser.add_argument('--project-root', default='.', help='项目根目录')

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 创建工作空间
    create_parser = subparsers.add_parser('create', help='创建新工作空间')
    create_parser.add_argument('name', help='工作空间名称')
    create_parser.add_argument('description', help='工作空间描述')
    create_parser.add_argument('--type', choices=['feature', 'bugfix', 'experiment', 'hotfix', 'refactor'],
                              default='feature', help='工作空间类型')
    create_parser.add_argument('--base-branch', default='main', help='基分支')
    create_parser.add_argument('--port', type=int, help='首选端口')
    create_parser.add_argument('--priority', type=int, default=5, help='优先级 (1-10)')

    # 列出工作空间
    subparsers.add_parser('list', help='列出所有工作空间')

    # 切换工作空间
    switch_parser = subparsers.add_parser('switch', help='切换工作空间')
    switch_parser.add_argument('workspace_id', help='工作空间ID')

    # 检测冲突
    conflict_parser = subparsers.add_parser('conflicts', help='检测冲突')
    conflict_parser.add_argument('workspace_id', help='工作空间ID')

    # 合并工作空间
    merge_parser = subparsers.add_parser('merge', help='合并工作空间')
    merge_parser.add_argument('workspace_id', help='工作空间ID')
    merge_parser.add_argument('--dry-run', action='store_true', help='只检查，不实际合并')

    # 统计信息
    subparsers.add_parser('stats', help='显示统计信息')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    manager = WorkspaceManager(args.project_root)

    if args.command == 'create':
        workspace_type = WorkspaceType(args.type)
        workspace_id = manager.create_workspace(
            args.name, args.description, workspace_type,
            args.base_branch, args.port, priority=args.priority
        )
        print(f"Created workspace: {workspace_id}")

    elif args.command == 'list':
        workspaces = manager.list_workspaces()
        if not workspaces:
            print("No workspaces found")
            return

        print(f"{'ID':<20} {'Name':<15} {'Type':<12} {'Status':<10} {'Port':<6} {'Ahead':<6} {'Behind':<7}")
        print("-" * 80)
        for ws in workspaces:
            print(f"{ws['id']:<20} {ws['name']:<15} {ws['type']:<12} {ws['status']:<10} "
                  f"{ws['dev_port']:<6} {ws['commits_ahead']:<6} {ws['commits_behind']:<7}")

    elif args.command == 'switch':
        if manager.switch_workspace(args.workspace_id):
            print(f"Switched to workspace: {args.workspace_id}")
        else:
            print(f"Failed to switch to workspace: {args.workspace_id}")

    elif args.command == 'conflicts':
        conflicts = manager.detect_conflicts(args.workspace_id)
        if 'error' in conflicts:
            print(f"Error: {conflicts['error']}")
            return

        print(f"Conflict analysis for workspace: {args.workspace_id}")
        if conflicts['direct_conflicts']:
            print("\nDirect conflicts:")
            for conflict in conflicts['direct_conflicts']:
                print(f"  - {conflict}")

        if conflicts['potential_conflicts']:
            print("\nPotential conflicts with other workspaces:")
            for conflict in conflicts['potential_conflicts']:
                print(f"  - {conflict['workspace']}: {', '.join(conflict['common_files'])}")

        if not conflicts['direct_conflicts'] and not conflicts['potential_conflicts']:
            print("No conflicts detected")

    elif args.command == 'merge':
        result = manager.auto_merge_workspace(args.workspace_id, args.dry_run)
        if 'error' in result:
            print(f"Error: {result['error']}")
        else:
            print(result['message'])
            if 'file_changes' in result and result['file_changes']:
                print(f"Files changed: {', '.join(result['file_changes'])}")

    elif args.command == 'stats':
        stats = manager.get_workspace_stats()
        print(f"Total workspaces: {stats['total_workspaces']}")
        print(f"Active workspaces: {stats['active_count']}")
        print("\nBy status:")
        for status, count in stats['by_status'].items():
            print(f"  {status}: {count}")
        print("\nBy type:")
        for ws_type, count in stats['by_type'].items():
            print(f"  {ws_type}: {count}")

if __name__ == "__main__":
    main()