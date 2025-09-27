#!/usr/bin/env python3
"""
配置回滚管理器
==============

管理配置文件、环境变量的版本控制和回滚
支持多环境配置的原子性切换
"""

import os
import sys
import json
import yaml
import shutil
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict


@dataclass
class ConfigSnapshot:
    """配置快照"""

    snapshot_id: str
    timestamp: datetime
    phase: str
    task_id: str
    description: str
    git_commit: str
    files: Dict[str, str]  # 文件路径 -> 文件哈希
    env_vars: Dict[str, str]  # 环境变量快照
    checksum: str


class ConfigRollbackManager:
    """配置回滚管理器"""

    def __init__(self, project_root: Optional[str] = None):
        """
        初始化配置回滚管理器

        Args:
            project_root: 项目根目录
        """
        self.project_root = Path(project_root or ".")
        self.rollback_dir = self.project_root / "rollback-strategy" / "config-snapshots"
        self.rollback_dir.mkdir(parents=True, exist_ok=True)

        # 快照存储
        self.snapshots_file = self.rollback_dir / "config_snapshots.json"
        self.snapshots = self._load_snapshots()

        # 配置文件监控列表
        self.monitored_configs = [
            ".claude/settings.json",
            ".workflow/config.yml",
            ".phase/current",
            ".limits/*/max",
            ".gates/*.ok",
            "backend/core/config.py",
            "backend/db/config.py",
            ".env",
            ".env.local",
            ".env.production",
            "docker-compose.yml",
            "pyproject.toml",
        ]

        # 关键环境变量列表
        self.monitored_env_vars = [
            "CLAUDE_ENHANCER_MODE",
            "PYTHON_PATH",
            "CACHE_DIR",
            "METRICS_FILE",
            "LOG_LEVEL",
            "DB_HOST",
            "DB_PORT",
            "DB_NAME",
            "DB_USER",
            "DB_PASSWORD",
        ]

        self.logger = logging.getLogger(__name__)

    def _load_snapshots(self) -> Dict[str, ConfigSnapshot]:
        """加载配置快照"""
        if not self.snapshots_file.exists():
            return {}

        try:
            with open(self.snapshots_file, "r") as f:
                data = json.load(f)

            snapshots = {}
            for snapshot_id, item in data.items():
                item["timestamp"] = datetime.fromisoformat(item["timestamp"])
                snapshots[snapshot_id] = ConfigSnapshot(**item)

            return snapshots
        except Exception as e:
            self.logger.error(f"加载配置快照失败: {e}")
            return {}

    def _save_snapshots(self):
        """保存快照元数据"""
        try:
            data = {}
            for snapshot_id, snapshot in self.snapshots.items():
                item = asdict(snapshot)
                item["timestamp"] = snapshot.timestamp.isoformat()
                data[snapshot_id] = item

            with open(self.snapshots_file, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"保存配置快照失败: {e}")

    def _get_git_commit(self) -> str:
        """获取当前Git commit"""
        try:
            import subprocess

            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=self.project_root,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "unknown"

    def _get_current_phase(self) -> str:
        """获取当前Phase"""
        phase_file = self.project_root / ".phase" / "current"
        if phase_file.exists():
            return phase_file.read_text().strip()
        return "unknown"

    def _calculate_file_hash(self, file_path: Path) -> str:
        """计算文件哈希"""
        try:
            with open(file_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return "error"

    def _expand_glob_patterns(self, patterns: List[str]) -> List[Path]:
        """展开glob模式的文件路径"""
        files = []
        for pattern in patterns:
            pattern_path = self.project_root / pattern
            if "*" in pattern:
                # 处理glob模式
                from glob import glob

                matched_files = glob(str(pattern_path))
                files.extend([Path(f) for f in matched_files])
            else:
                # 直接路径
                if pattern_path.exists():
                    files.append(pattern_path)
        return files

    def _capture_current_state(self) -> Tuple[Dict[str, str], Dict[str, str]]:
        """
        捕获当前配置状态

        Returns:
            (文件快照, 环境变量快照)
        """
        # 文件快照
        files_snapshot = {}
        config_files = self._expand_glob_patterns(self.monitored_configs)

        for file_path in config_files:
            if file_path.exists() and file_path.is_file():
                relative_path = str(file_path.relative_to(self.project_root))
                files_snapshot[relative_path] = self._calculate_file_hash(file_path)

        # 环境变量快照
        env_snapshot = {}
        for var in self.monitored_env_vars:
            value = os.getenv(var)
            if value is not None:
                env_snapshot[var] = value

        return files_snapshot, env_snapshot

    def _calculate_snapshot_checksum(
        self, files_snapshot: Dict[str, str], env_snapshot: Dict[str, str]
    ) -> str:
        """计算快照校验和"""
        combined_data = json.dumps(
            {"files": files_snapshot, "env": env_snapshot}, sort_keys=True
        )
        return hashlib.sha256(combined_data.encode()).hexdigest()

    def create_config_snapshot(
        self, description: str = "", task_id: str = "auto"
    ) -> Optional[str]:
        """
        创建配置快照

        Args:
            description: 快照描述
            task_id: 任务ID

        Returns:
            快照ID
        """
        timestamp = datetime.now()
        snapshot_id = f"config_{timestamp.strftime('%Y%m%d_%H%M%S')}"

        self.logger.info(f"创建配置快照: {snapshot_id}")

        try:
            # 捕获当前状态
            files_snapshot, env_snapshot = self._capture_current_state()

            # 创建快照目录
            snapshot_dir = self.rollback_dir / snapshot_id
            snapshot_dir.mkdir(exist_ok=True)

            # 备份配置文件
            self._backup_config_files(snapshot_dir, files_snapshot)

            # 计算校验和
            checksum = self._calculate_snapshot_checksum(files_snapshot, env_snapshot)

            # 创建快照元数据
            snapshot = ConfigSnapshot(
                snapshot_id=snapshot_id,
                timestamp=timestamp,
                phase=self._get_current_phase(),
                task_id=task_id,
                description=description or f"Config snapshot at {timestamp}",
                git_commit=self._get_git_commit(),
                files=files_snapshot,
                env_vars=env_snapshot,
                checksum=checksum,
            )

            # 保存快照
            self.snapshots[snapshot_id] = snapshot
            self._save_snapshots()

            # 保存环境变量
            self._save_env_snapshot(snapshot_dir, env_snapshot)

            self.logger.info(f"配置快照创建成功: {snapshot_id}")
            return snapshot_id

        except Exception as e:
            self.logger.error(f"创建配置快照失败: {e}")
            return None

    def _backup_config_files(self, snapshot_dir: Path, files_snapshot: Dict[str, str]):
        """备份配置文件"""
        files_dir = snapshot_dir / "files"
        files_dir.mkdir(exist_ok=True)

        for relative_path in files_snapshot.keys():
            source_file = self.project_root / relative_path
            if source_file.exists():
                # 创建目标目录结构
                target_file = files_dir / relative_path
                target_file.parent.mkdir(parents=True, exist_ok=True)

                # 复制文件
                shutil.copy2(source_file, target_file)

    def _save_env_snapshot(self, snapshot_dir: Path, env_snapshot: Dict[str, str]):
        """保存环境变量快照"""
        env_file = snapshot_dir / "environment.json"
        with open(env_file, "w") as f:
            json.dump(env_snapshot, f, indent=2, ensure_ascii=False)

        # 同时生成.env格式文件
        env_dotfile = snapshot_dir / "environment.env"
        with open(env_dotfile, "w") as f:
            for key, value in env_snapshot.items():
                f.write(f"{key}={value}\n")

    def rollback_config(
        self,
        snapshot_id: str,
        confirm: bool = False,
        restore_files: bool = True,
        restore_env: bool = True,
    ) -> bool:
        """
        回滚配置

        Args:
            snapshot_id: 快照ID
            confirm: 是否确认回滚
            restore_files: 是否恢复文件
            restore_env: 是否恢复环境变量

        Returns:
            是否回滚成功
        """
        if not confirm:
            self.logger.warning("配置回滚需要确认，请设置confirm=True")
            return False

        if snapshot_id not in self.snapshots:
            self.logger.error(f"配置快照不存在: {snapshot_id}")
            return False

        snapshot = self.snapshots[snapshot_id]
        snapshot_dir = self.rollback_dir / snapshot_id

        if not snapshot_dir.exists():
            self.logger.error(f"快照目录不存在: {snapshot_dir}")
            return False

        self.logger.info(f"开始回滚配置: {snapshot_id}")

        try:
            # 首先创建当前配置的紧急快照
            emergency_snapshot = self.create_config_snapshot(
                description=f"Emergency snapshot before rollback to {snapshot_id}",
                task_id="emergency",
            )

            if not emergency_snapshot:
                self.logger.error("创建紧急快照失败，终止回滚")
                return False

            success = True

            # 恢复配置文件
            if restore_files:
                if not self._restore_config_files(snapshot_dir, snapshot.files):
                    self.logger.error("配置文件恢复失败")
                    success = False

            # 恢复环境变量（仅在当前进程中）
            if restore_env:
                if not self._restore_env_vars(snapshot_dir):
                    self.logger.error("环境变量恢复失败")
                    success = False

            if success:
                self.logger.info(f"配置回滚成功: {snapshot_id}")
                return True
            else:
                self.logger.error(f"配置回滚失败: {snapshot_id}")
                return False

        except Exception as e:
            self.logger.error(f"配置回滚异常: {e}")
            return False

    def _restore_config_files(
        self, snapshot_dir: Path, files_snapshot: Dict[str, str]
    ) -> bool:
        """恢复配置文件"""
        try:
            files_dir = snapshot_dir / "files"

            for relative_path in files_snapshot.keys():
                source_file = files_dir / relative_path
                target_file = self.project_root / relative_path

                if source_file.exists():
                    # 确保目标目录存在
                    target_file.parent.mkdir(parents=True, exist_ok=True)

                    # 恢复文件
                    shutil.copy2(source_file, target_file)
                    self.logger.debug(f"恢复文件: {relative_path}")

            return True

        except Exception as e:
            self.logger.error(f"恢复配置文件失败: {e}")
            return False

    def _restore_env_vars(self, snapshot_dir: Path) -> bool:
        """恢复环境变量（仅当前进程）"""
        try:
            env_file = snapshot_dir / "environment.json"
            if not env_file.exists():
                self.logger.warning("环境变量快照不存在")
                return True

            with open(env_file, "r") as f:
                env_snapshot = json.load(f)

            # 恢复环境变量到当前进程
            for key, value in env_snapshot.items():
                os.environ[key] = value
                self.logger.debug(f"恢复环境变量: {key}")

            self.logger.info("环境变量恢复完成（仅当前进程）")
            return True

        except Exception as e:
            self.logger.error(f"恢复环境变量失败: {e}")
            return False

    def validate_snapshot(self, snapshot_id: str) -> bool:
        """
        验证快照完整性

        Args:
            snapshot_id: 快照ID

        Returns:
            是否验证通过
        """
        if snapshot_id not in self.snapshots:
            self.logger.error(f"快照不存在: {snapshot_id}")
            return False

        snapshot = self.snapshots[snapshot_id]
        snapshot_dir = self.rollback_dir / snapshot_id

        if not snapshot_dir.exists():
            self.logger.error(f"快照目录不存在: {snapshot_dir}")
            return False

        try:
            # 验证文件完整性
            files_dir = snapshot_dir / "files"
            for relative_path, expected_hash in snapshot.files.items():
                file_path = files_dir / relative_path
                if not file_path.exists():
                    self.logger.error(f"快照文件缺失: {relative_path}")
                    return False

                actual_hash = self._calculate_file_hash(file_path)
                if actual_hash != expected_hash:
                    self.logger.error(f"快照文件哈希不匹配: {relative_path}")
                    return False

            # 验证环境变量文件存在
            env_file = snapshot_dir / "environment.json"
            if not env_file.exists():
                self.logger.error("环境变量快照文件缺失")
                return False

            # 验证整体校验和
            files_snapshot = snapshot.files
            env_snapshot = snapshot.env_vars
            expected_checksum = self._calculate_snapshot_checksum(
                files_snapshot, env_snapshot
            )

            if expected_checksum != snapshot.checksum:
                self.logger.error("快照校验和不匹配")
                return False

            self.logger.info(f"快照验证通过: {snapshot_id}")
            return True

        except Exception as e:
            self.logger.error(f"快照验证失败: {e}")
            return False

    def compare_configs(self, snapshot_id1: str, snapshot_id2: str) -> Dict[str, Any]:
        """
        比较两个配置快照

        Args:
            snapshot_id1: 快照1 ID
            snapshot_id2: 快照2 ID

        Returns:
            比较结果
        """
        if snapshot_id1 not in self.snapshots or snapshot_id2 not in self.snapshots:
            self.logger.error("快照不存在")
            return {}

        snapshot1 = self.snapshots[snapshot_id1]
        snapshot2 = self.snapshots[snapshot_id2]

        comparison = {
            "snapshot1": {
                "id": snapshot_id1,
                "timestamp": snapshot1.timestamp.isoformat(),
                "phase": snapshot1.phase,
            },
            "snapshot2": {
                "id": snapshot_id2,
                "timestamp": snapshot2.timestamp.isoformat(),
                "phase": snapshot2.phase,
            },
            "file_differences": [],
            "env_differences": [],
            "added_files": [],
            "removed_files": [],
            "added_env_vars": [],
            "removed_env_vars": [],
        }

        # 比较文件
        all_files = set(snapshot1.files.keys()) | set(snapshot2.files.keys())
        for file_path in all_files:
            hash1 = snapshot1.files.get(file_path)
            hash2 = snapshot2.files.get(file_path)

            if hash1 and hash2:
                if hash1 != hash2:
                    comparison["file_differences"].append(file_path)
            elif hash1 and not hash2:
                comparison["removed_files"].append(file_path)
            elif not hash1 and hash2:
                comparison["added_files"].append(file_path)

        # 比较环境变量
        all_env_vars = set(snapshot1.env_vars.keys()) | set(snapshot2.env_vars.keys())
        for var_name in all_env_vars:
            value1 = snapshot1.env_vars.get(var_name)
            value2 = snapshot2.env_vars.get(var_name)

            if value1 and value2:
                if value1 != value2:
                    comparison["env_differences"].append(
                        {"variable": var_name, "old_value": value1, "new_value": value2}
                    )
            elif value1 and not value2:
                comparison["removed_env_vars"].append(var_name)
            elif not value1 and value2:
                comparison["added_env_vars"].append(var_name)

        return comparison

    def list_snapshots(self, limit: int = 20) -> List[ConfigSnapshot]:
        """
        列出配置快照

        Args:
            limit: 限制数量

        Returns:
            快照列表
        """
        snapshots = list(self.snapshots.values())
        snapshots.sort(key=lambda x: x.timestamp, reverse=True)
        return snapshots[:limit]

    def cleanup_old_snapshots(self, keep_days: int = 30, keep_count: int = 10):
        """
        清理旧快照

        Args:
            keep_days: 保留天数
            keep_count: 最少保留数量
        """
        from datetime import timedelta

        cutoff_date = datetime.now() - timedelta(days=keep_days)
        snapshots_to_remove = []

        # 按时间排序的快照列表
        sorted_snapshots = sorted(
            self.snapshots.items(), key=lambda x: x[1].timestamp, reverse=True
        )

        # 保留最新的keep_count个快照
        for i, (snapshot_id, snapshot) in enumerate(sorted_snapshots):
            if i >= keep_count and snapshot.timestamp < cutoff_date:
                snapshots_to_remove.append(snapshot_id)

        # 删除旧快照
        for snapshot_id in snapshots_to_remove:
            self.remove_snapshot(snapshot_id)

        self.logger.info(f"清理了 {len(snapshots_to_remove)} 个旧配置快照")

    def remove_snapshot(self, snapshot_id: str) -> bool:
        """
        删除快照

        Args:
            snapshot_id: 快照ID

        Returns:
            是否删除成功
        """
        if snapshot_id not in self.snapshots:
            self.logger.error(f"快照不存在: {snapshot_id}")
            return False

        try:
            # 删除快照目录
            snapshot_dir = self.rollback_dir / snapshot_id
            if snapshot_dir.exists():
                shutil.rmtree(snapshot_dir)

            # 删除元数据
            del self.snapshots[snapshot_id]
            self._save_snapshots()

            self.logger.info(f"删除配置快照成功: {snapshot_id}")
            return True

        except Exception as e:
            self.logger.error(f"删除配置快照失败: {e}")
            return False

    def export_snapshot(self, snapshot_id: str, output_file: str) -> bool:
        """
        导出快照

        Args:
            snapshot_id: 快照ID
            output_file: 输出文件路径

        Returns:
            是否导出成功
        """
        if snapshot_id not in self.snapshots:
            self.logger.error(f"快照不存在: {snapshot_id}")
            return False

        try:
            import tarfile

            snapshot_dir = self.rollback_dir / snapshot_id
            with tarfile.open(output_file, "w:gz") as tar:
                tar.add(snapshot_dir, arcname=snapshot_id)

            self.logger.info(f"快照导出成功: {output_file}")
            return True

        except Exception as e:
            self.logger.error(f"导出快照失败: {e}")
            return False

    def import_snapshot(self, archive_file: str) -> Optional[str]:
        """
        导入快照

        Args:
            archive_file: 归档文件路径

        Returns:
            导入的快照ID
        """
        try:
            import tarfile

            with tarfile.open(archive_file, "r:gz") as tar:
                tar.extractall(self.rollback_dir)

            # 重新加载快照元数据
            self.snapshots = self._load_snapshots()

            self.logger.info(f"快照导入成功: {archive_file}")
            return "imported"

        except Exception as e:
            self.logger.error(f"导入快照失败: {e}")
            return None


# 创建全局实例
config_rollback_manager = ConfigRollbackManager()


# 便捷函数
def create_config_snapshot(
    description: str = "", task_id: str = "auto"
) -> Optional[str]:
    """创建配置快照"""
    return config_rollback_manager.create_config_snapshot(description, task_id)


def rollback_config(snapshot_id: str, confirm: bool = False) -> bool:
    """回滚配置"""
    return config_rollback_manager.rollback_config(snapshot_id, confirm)


def list_config_snapshots(limit: int = 20) -> List[ConfigSnapshot]:
    """列出配置快照"""
    return config_rollback_manager.list_snapshots(limit)


if __name__ == "__main__":
    import argparse

    # 设置日志
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    parser = argparse.ArgumentParser(description="配置回滚管理器")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 创建快照
    snapshot_parser = subparsers.add_parser("snapshot", help="创建配置快照")
    snapshot_parser.add_argument("--description", help="快照描述")
    snapshot_parser.add_argument("--task-id", help="任务ID")

    # 回滚
    rollback_parser = subparsers.add_parser("rollback", help="回滚配置")
    rollback_parser.add_argument("snapshot_id", help="快照ID")
    rollback_parser.add_argument("--confirm", action="store_true", help="确认回滚")
    rollback_parser.add_argument("--files-only", action="store_true", help="仅恢复文件")
    rollback_parser.add_argument("--env-only", action="store_true", help="仅恢复环境变量")

    # 列出快照
    list_parser = subparsers.add_parser("list", help="列出配置快照")
    list_parser.add_argument("--limit", type=int, default=20, help="限制数量")

    # 验证快照
    validate_parser = subparsers.add_parser("validate", help="验证快照")
    validate_parser.add_argument("snapshot_id", help="快照ID")

    # 比较快照
    compare_parser = subparsers.add_parser("compare", help="比较两个快照")
    compare_parser.add_argument("snapshot1", help="快照1 ID")
    compare_parser.add_argument("snapshot2", help="快照2 ID")

    # 导出快照
    export_parser = subparsers.add_parser("export", help="导出快照")
    export_parser.add_argument("snapshot_id", help="快照ID")
    export_parser.add_argument("output_file", help="输出文件")

    # 导入快照
    import_parser = subparsers.add_parser("import", help="导入快照")
    import_parser.add_argument("archive_file", help="归档文件")

    # 清理
    cleanup_parser = subparsers.add_parser("cleanup", help="清理旧快照")
    cleanup_parser.add_argument("--days", type=int, default=30, help="保留天数")
    cleanup_parser.add_argument("--count", type=int, default=10, help="最少保留数量")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # 执行命令
    if args.command == "snapshot":
        snapshot_id = config_rollback_manager.create_config_snapshot(
            description=args.description or "", task_id=args.task_id or "cli"
        )
        if snapshot_id:
            print(f"配置快照创建成功: {snapshot_id}")
        else:
            print("配置快照创建失败")
            sys.exit(1)

    elif args.command == "rollback":
        restore_files = not args.env_only
        restore_env = not args.files_only

        success = config_rollback_manager.rollback_config(
            args.snapshot_id,
            confirm=args.confirm,
            restore_files=restore_files,
            restore_env=restore_env,
        )
        if success:
            print(f"配置回滚成功: {args.snapshot_id}")
        else:
            print(f"配置回滚失败: {args.snapshot_id}")
            sys.exit(1)

    elif args.command == "list":
        snapshots = config_rollback_manager.list_snapshots(args.limit)
        print(f"{'快照ID':<25} {'时间':<20} {'阶段':<5} {'任务ID':<10} {'提交':<10} {'描述'}")
        print("-" * 100)
        for snapshot in snapshots:
            commit = (
                snapshot.git_commit[:8]
                if snapshot.git_commit != "unknown"
                else "unknown"
            )
            print(
                f"{snapshot.snapshot_id:<25} {snapshot.timestamp.strftime('%Y-%m-%d %H:%M'):<20} {snapshot.phase:<5} {snapshot.task_id:<10} {commit:<10} {snapshot.description}"
            )

    elif args.command == "validate":
        success = config_rollback_manager.validate_snapshot(args.snapshot_id)
        if success:
            print(f"快照验证通过: {args.snapshot_id}")
        else:
            print(f"快照验证失败: {args.snapshot_id}")
            sys.exit(1)

    elif args.command == "compare":
        comparison = config_rollback_manager.compare_configs(
            args.snapshot1, args.snapshot2
        )
        if comparison:
            print(f"比较快照 {args.snapshot1} 和 {args.snapshot2}:")
            print(f"文件差异: {len(comparison['file_differences'])} 个")
            print(f"环境变量差异: {len(comparison['env_differences'])} 个")
            print(f"新增文件: {len(comparison['added_files'])} 个")
            print(f"删除文件: {len(comparison['removed_files'])} 个")

            if comparison["file_differences"]:
                print("\n文件差异:")
                for file_path in comparison["file_differences"]:
                    print(f"  - {file_path}")

            if comparison["env_differences"]:
                print("\n环境变量差异:")
                for diff in comparison["env_differences"]:
                    print(
                        f"  - {diff['variable']}: {diff['old_value']} -> {diff['new_value']}"
                    )

    elif args.command == "export":
        success = config_rollback_manager.export_snapshot(
            args.snapshot_id, args.output_file
        )
        if success:
            print(f"快照导出成功: {args.output_file}")
        else:
            print(f"快照导出失败: {args.snapshot_id}")
            sys.exit(1)

    elif args.command == "import":
        snapshot_id = config_rollback_manager.import_snapshot(args.archive_file)
        if snapshot_id:
            print(f"快照导入成功: {args.archive_file}")
        else:
            print(f"快照导入失败: {args.archive_file}")
            sys.exit(1)

    elif args.command == "cleanup":
        config_rollback_manager.cleanup_old_snapshots(args.days, args.count)
        print("清理完成")
