#!/usr/bin/env python3
"""
Migration回滚管理器
==================

基于现有的MigrationManager扩展回滚功能
提供安全的migration版本管理和回滚策略
"""

import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# 导入现有的迁移管理器
sys.path.append(str(Path(__file__).parent.parent))
from backend.db.migrations import MigrationManager, migration_manager
from rollback_strategy.database_backup_manager import create_backup_manager


@dataclass
class MigrationSnapshot:
    """Migration快照"""

    revision: str
    timestamp: datetime
    phase: str
    task_id: str
    backup_id: Optional[str]
    description: str


class MigrationRollbackManager:
    """Migration回滚管理器"""

    def __init__(self, migration_manager: MigrationManager):
        """
        初始化回滚管理器

        Args:
            migration_manager: 迁移管理器实例
        """
        self.migration_manager = migration_manager
        self.backup_manager = create_backup_manager()

        # 快照存储目录
        self.snapshots_dir = Path("./rollback-strategy/migration-snapshots")
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

        # 快照元数据文件
        self.snapshots_file = self.snapshots_dir / "snapshots.json"
        self.snapshots = self._load_snapshots()

        # 设置日志
        self.logger = logging.getLogger(__name__)

    def _load_snapshots(self) -> Dict[str, MigrationSnapshot]:
        """加载迁移快照"""
        if not self.snapshots_file.exists():
            return {}

        try:
            with open(self.snapshots_file, "r") as f:
                data = json.load(f)

            snapshots = {}
            for revision, item in data.items():
                item["timestamp"] = datetime.fromisoformat(item["timestamp"])
                snapshots[revision] = MigrationSnapshot(**item)

            return snapshots
        except Exception as e:
            self.logger.error(f"加载快照失败: {e}")
            return {}

    def _save_snapshots(self):
        """保存快照元数据"""
        try:
            data = {}
            for revision, snapshot in self.snapshots.items():
                item = {
                    "revision": snapshot.revision,
                    "timestamp": snapshot.timestamp.isoformat(),
                    "phase": snapshot.phase,
                    "task_id": snapshot.task_id,
                    "backup_id": snapshot.backup_id,
                    "description": snapshot.description,
                }
                data[revision] = item

            with open(self.snapshots_file, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"保存快照失败: {e}")

    def _get_current_phase(self) -> str:
        """获取当前Phase"""
        phase_file = Path(".phase/current")
        if phase_file.exists():
            return phase_file.read_text().strip()
        return "unknown"

    def create_migration_snapshot(
        self, description: str = "", task_id: str = "auto", create_backup: bool = True
    ) -> Optional[str]:
        """
        创建迁移快照

        Args:
            description: 快照描述
            task_id: 任务ID
            create_backup: 是否同时创建数据库备份

        Returns:
            快照的revision ID
        """
        current_revision = self.migration_manager.get_current_revision()
        if not current_revision:
            self.logger.error("无法获取当前迁移版本")
            return None

        self.logger.info(f"创建迁移快照: {current_revision}")

        backup_id = None
        if create_backup:
            backup_id = self.backup_manager.create_full_backup(
                description=f"Migration snapshot backup for {current_revision}",
                task_id=task_id,
            )
            if not backup_id:
                self.logger.warning("备份创建失败，但继续创建快照")

        # 创建快照
        snapshot = MigrationSnapshot(
            revision=current_revision,
            timestamp=datetime.now(),
            phase=self._get_current_phase(),
            task_id=task_id,
            backup_id=backup_id,
            description=description or f"Migration snapshot at {current_revision}",
        )

        # 保存快照
        self.snapshots[current_revision] = snapshot
        self._save_snapshots()

        self.logger.info(f"迁移快照创建成功: {current_revision}")
        return current_revision

    def rollback_to_snapshot(
        self, target_revision: str, confirm: bool = False, use_backup: bool = True
    ) -> bool:
        """
        回滚到指定快照

        Args:
            target_revision: 目标revision
            confirm: 是否确认回滚
            use_backup: 是否使用数据库备份恢复

        Returns:
            是否回滚成功
        """
        if not confirm:
            self.logger.warning("回滚操作需要确认，请设置confirm=True")
            return False

        if target_revision not in self.snapshots:
            self.logger.error(f"快照不存在: {target_revision}")
            return False

        snapshot = self.snapshots[target_revision]
        current_revision = self.migration_manager.get_current_revision()

        self.logger.info(f"开始回滚从 {current_revision} 到 {target_revision}")

        try:
            pass  # Auto-fixed empty block
            # 首先创建当前状态的紧急快照
            emergency_snapshot = self.create_migration_snapshot(
                description=f"Emergency snapshot before rollback to {target_revision}",
                task_id="emergency",
            )

            if not emergency_snapshot:
                self.logger.error("创建紧急快照失败，终止回滚")
                return False

            # 方案1: 使用数据库备份恢复（推荐）
            if use_backup and snapshot.backup_id:
                self.logger.info("使用数据库备份恢复")
                if not self.backup_manager.restore_backup(
                    snapshot.backup_id, confirm=True
                ):
                    self.logger.error("数据库备份恢复失败")
                    return False
            else:
                pass  # Auto-fixed empty block
                # 方案2: 使用migration downgrade
                self.logger.info("使用迁移降级")
                if not self.migration_manager.downgrade(target_revision):
                    self.logger.error("迁移降级失败")
                    return False

            # 验证回滚结果
            new_revision = self.migration_manager.get_current_revision()
            if new_revision == target_revision:
                self.logger.info(f"回滚成功: 当前版本 {new_revision}")
                return True
            else:
                self.logger.error(f"回滚验证失败: 期望 {target_revision}, 实际 {new_revision}")
                return False

        except Exception as e:
            self.logger.error(f"回滚过程异常: {e}")
            return False

    def get_rollback_path(self, target_revision: str) -> List[str]:
        """
        获取回滚路径

        Args:
            target_revision: 目标版本

        Returns:
            回滚路径中的revision列表
        """
        current_revision = self.migration_manager.get_current_revision()
        if not current_revision:
            return []

        # 获取迁移历史
        history = self.migration_manager.get_migration_history()
        if not history:
            return []

        # 构建revision链
        revision_chain = []
        for migration in history:
            revision_chain.append(migration["revision"])

        try:
            current_index = revision_chain.index(current_revision)
            target_index = revision_chain.index(target_revision)

            if target_index > current_index:
                self.logger.error("目标版本比当前版本新，无法回滚")
                return []

            # 返回从当前版本到目标版本的路径
            return revision_chain[target_index : current_index + 1][::-1]

        except ValueError:
            self.logger.error("版本链中找不到指定版本")
            return []

    def validate_rollback_safety(self, target_revision: str) -> Tuple[bool, List[str]]:
        """
        验证回滚安全性

        Args:
            target_revision: 目标版本

        Returns:
            (是否安全, 警告列表)
        """
        warnings = []
        is_safe = True

        # 检查快照是否存在
        if target_revision not in self.snapshots:
            warnings.append(f"目标版本 {target_revision} 没有快照")
            is_safe = False

        # 检查备份是否可用
        snapshot = self.snapshots.get(target_revision)
        if snapshot and snapshot.backup_id:
            if not self.backup_manager.verify_backup(snapshot.backup_id):
                warnings.append(f"快照关联的备份 {snapshot.backup_id} 不可用")
                is_safe = False

        # 检查回滚路径
        rollback_path = self.get_rollback_path(target_revision)
        if not rollback_path:
            warnings.append("无法确定回滚路径")
            is_safe = False

        # 检查数据丢失风险
        current_revision = self.migration_manager.get_current_revision()
        if current_revision and target_revision != current_revision:
            warnings.append("回滚可能导致数据丢失，建议先备份当前数据")

        # 检查环境一致性
        if snapshot and snapshot.phase != self._get_current_phase():
            warnings.append(
                f"快照阶段 ({snapshot.phase}) 与当前阶段 ({self._get_current_phase()}) 不匹配"
            )

        return is_safe, warnings

    def list_snapshots(self, limit: int = 20) -> List[MigrationSnapshot]:
        """
        列出迁移快照

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
        for i, (revision, snapshot) in enumerate(sorted_snapshots):
            if i >= keep_count and snapshot.timestamp < cutoff_date:
                snapshots_to_remove.append(revision)

        # 删除旧快照
        for revision in snapshots_to_remove:
            self.remove_snapshot(revision)

        self.logger.info(f"清理了 {len(snapshots_to_remove)} 个旧快照")

    def remove_snapshot(self, revision: str) -> bool:
        """
        删除快照

        Args:
            revision: 快照版本

        Returns:
            是否删除成功
        """
        if revision not in self.snapshots:
            self.logger.error(f"快照不存在: {revision}")
            return False

        snapshot = self.snapshots[revision]

        try:
            pass  # Auto-fixed empty block
            # 删除关联的备份（可选）
            if snapshot.backup_id:
                self.logger.info(f"同时删除关联备份: {snapshot.backup_id}")
                self.backup_manager.remove_backup(snapshot.backup_id)

            # 删除快照记录
            del self.snapshots[revision]
            self._save_snapshots()

            self.logger.info(f"删除快照成功: {revision}")
            return True

        except Exception as e:
            self.logger.error(f"删除快照失败: {e}")
            return False

    def safe_upgrade(self, revision: str = "head") -> bool:
        """
        安全升级（自动创建快照）

        Args:
            revision: 目标版本

        Returns:
            是否升级成功
        """
        # 升级前创建快照
        snapshot_revision = self.create_migration_snapshot(
            description=f"Auto snapshot before upgrade to {revision}"
        )

        if not snapshot_revision:
            self.logger.error("创建快照失败，终止升级")
            return False

        # 执行升级
        if self.migration_manager.upgrade(revision):
            self.logger.info(f"安全升级成功到 {revision}")
            return True
        else:
            self.logger.error("升级失败，可使用快照回滚")
            return False

    def get_migration_status(self) -> Dict[str, any]:
        """
        获取迁移状态信息

        Returns:
            状态信息字典
        """
        current_revision = self.migration_manager.get_current_revision()
        pending_migrations = self.migration_manager.check_pending_migrations()
        history = self.migration_manager.get_migration_history()

        return {
            "current_revision": current_revision,
            "has_pending_migrations": pending_migrations,
            "total_migrations": len(history),
            "snapshots_count": len(self.snapshots),
            "latest_snapshot": max(
                self.snapshots.values(), key=lambda x: x.timestamp, default=None
            ),
            "phase": self._get_current_phase(),
        }


# 创建全局实例
migration_rollback_manager = MigrationRollbackManager(migration_manager)


# 便捷函数
def create_snapshot(description: str = "", task_id: str = "auto") -> Optional[str]:
    """创建迁移快照"""
    return migration_rollback_manager.create_migration_snapshot(description, task_id)


def rollback_to(revision: str, confirm: bool = False) -> bool:
    """回滚到指定版本"""
    return migration_rollback_manager.rollback_to_snapshot(revision, confirm)


def safe_upgrade(revision: str = "head") -> bool:
    """安全升级"""
    return migration_rollback_manager.safe_upgrade(revision)


if __name__ == "__main__":
    import argparse

    # 设置日志
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    parser = argparse.ArgumentParser(description="Migration回滚管理器")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 创建快照
    snapshot_parser = subparsers.add_parser("snapshot", help="创建迁移快照")
    snapshot_parser.add_argument("--description", help="快照描述")
    snapshot_parser.add_argument("--task-id", help="任务ID")
    snapshot_parser.add_argument("--no-backup", action="store_true", help="不创建数据库备份")

    # 回滚
    rollback_parser = subparsers.add_parser("rollback", help="回滚到快照")
    rollback_parser.add_argument("revision", help="目标revision")
    rollback_parser.add_argument("--confirm", action="store_true", help="确认回滚")
    rollback_parser.add_argument("--no-backup", action="store_true", help="不使用数据库备份")

    # 列出快照
    list_parser = subparsers.add_parser("list", help="列出快照")
    list_parser.add_argument("--limit", type=int, default=20, help="限制数量")

    # 验证回滚安全性
    validate_parser = subparsers.add_parser("validate", help="验证回滚安全性")
    validate_parser.add_argument("revision", help="目标revision")

    # 安全升级
    upgrade_parser = subparsers.add_parser("upgrade", help="安全升级")
    upgrade_parser.add_argument("--revision", default="head", help="目标版本")

    # 状态查看
    status_parser = subparsers.add_parser("status", help="查看迁移状态")

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
        revision = migration_rollback_manager.create_migration_snapshot(
            description=args.description or "",
            task_id=args.task_id or "cli",
            create_backup=not args.no_backup,
        )
        if revision:
            print(f"快照创建成功: {revision}")
        else:
            print("快照创建失败")
            sys.exit(1)

    elif args.command == "rollback":
        pass  # Auto-fixed empty block
        # 先验证安全性
        is_safe, warnings = migration_rollback_manager.validate_rollback_safety(
            args.revision
        )
        if warnings:
            print("回滚警告:")
            for warning in warnings:
                print(f"  - {warning}")

        if not is_safe and not args.confirm:
            print("回滚存在风险，请添加 --confirm 参数强制执行")
            sys.exit(1)

        success = migration_rollback_manager.rollback_to_snapshot(
            args.revision, confirm=args.confirm, use_backup=not args.no_backup
        )
        if success:
            print(f"回滚成功: {args.revision}")
        else:
            print(f"回滚失败: {args.revision}")
            sys.exit(1)

    elif args.command == "list":
        snapshots = migration_rollback_manager.list_snapshots(args.limit)
        print(f"{'版本':<15} {'时间':<20} {'阶段':<5} {'任务ID':<10} {'备份ID':<20} {'描述'}")
        print("-" * 100)
        for snapshot in snapshots:
            backup_id = snapshot.backup_id or "无"
            print(
                f"{snapshot.revision:<15} {snapshot.timestamp.strftime('%Y-%m-%d %H:%M'):<20} {snapshot.phase:<5} {snapshot.task_id:<10} {backup_id:<20} {snapshot.description}"
            )

    elif args.command == "validate":
        is_safe, warnings = migration_rollback_manager.validate_rollback_safety(
            args.revision
        )
        print(f"回滚到 {args.revision} 的安全性: {'安全' if is_safe else '不安全'}")
        if warnings:
            print("警告:")
            for warning in warnings:
                print(f"  - {warning}")

    elif args.command == "upgrade":
        success = migration_rollback_manager.safe_upgrade(args.revision)
        if success:
            print(f"安全升级成功: {args.revision}")
        else:
            print(f"安全升级失败: {args.revision}")
            sys.exit(1)

    elif args.command == "status":
        status = migration_rollback_manager.get_migration_status()
        print("迁移状态:")
        print(f"  当前版本: {status['current_revision']}")
        print(f"  待执行迁移: {'有' if status['has_pending_migrations'] else '无'}")
        print(f"  总迁移数: {status['total_migrations']}")
        print(f"  快照数量: {status['snapshots_count']}")
        print(f"  当前阶段: {status['phase']}")
        if status["latest_snapshot"]:
            latest = status["latest_snapshot"]
            print(
                f"  最新快照: {latest.revision} ({latest.timestamp.strftime('%Y-%m-%d %H:%M')})"
            )

    elif args.command == "cleanup":
        migration_rollback_manager.cleanup_old_snapshots(args.days, args.count)
        print("清理完成")
