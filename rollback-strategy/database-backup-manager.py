#!/usr/bin/env python3
"""
数据库备份和回滚管理器
====================

提供自动化的数据库备份、验证和回滚功能
支持多版本备份和增量备份策略
"""

import os
import sys
import json
import logging
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from contextlib import contextmanager

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


@dataclass
class BackupMetadata:
    """备份元数据"""

    backup_id: str
    timestamp: datetime
    database_version: str
    schema_hash: str
    size_bytes: int
    backup_type: str  # full, incremental, schema_only
    phase: str
    task_id: str
    file_path: str
    description: str
    git_commit: str


class DatabaseBackupManager:
    """数据库备份管理器"""

    def __init__(self, config: Dict[str, str]):
        """
        初始化备份管理器

        Args:
            config: 数据库配置
        """
        self.config = config
        self.backup_root = Path("./backups/database")
        self.backup_root.mkdir(parents=True, exist_ok=True)

        # 设置日志
        self.logger = logging.getLogger(__name__)

        # 元数据存储
        self.metadata_file = self.backup_root / "backup_metadata.json"
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> Dict[str, BackupMetadata]:
        """加载备份元数据"""
        if not self.metadata_file.exists():
            return {}

        try:
            with open(self.metadata_file, "r") as f:
                data = json.load(f)

            metadata = {}
            for backup_id, item in data.items():
                # 转换datetime字符串
                item["timestamp"] = datetime.fromisoformat(item["timestamp"])
                metadata[backup_id] = BackupMetadata(**item)

            return metadata
        except Exception as e:
            self.logger.error(f"加载元数据失败: {e}")
            return {}

    def _save_metadata(self):
        """保存备份元数据"""
        try:
            data = {}
            for backup_id, metadata in self.metadata.items():
                item = asdict(metadata)
                # 转换datetime为字符串
                item["timestamp"] = metadata.timestamp.isoformat()
                data[backup_id] = item

            with open(self.metadata_file, "w") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"保存元数据失败: {e}")

    def _get_git_commit(self) -> str:
        """获取当前Git commit"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "unknown"

    def _get_current_phase(self) -> str:
        """获取当前Phase"""
        phase_file = Path(".phase/current")
        if phase_file.exists():
            return phase_file.read_text().strip()
        return "unknown"

    def _calculate_schema_hash(self) -> str:
        """计算数据库架构哈希"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    # 获取所有表结构
                    cursor.execute(
                        """
                        SELECT table_name, column_name, data_type, is_nullable
                        FROM information_schema.columns
                        WHERE table_schema = 'public'
                        ORDER BY table_name, ordinal_position
                    """
                    )

                    schema_info = cursor.fetchall()
                    schema_str = str(schema_info)

                    import hashlib

                    return hashlib.md5(schema_str.encode()).hexdigest()

        except Exception as e:
            self.logger.error(f"计算架构哈希失败: {e}")
            return "unknown"

    @contextmanager
    def _get_connection(self):
        """获取数据库连接上下文管理器"""
        conn = None
        try:
            conn = psycopg2.connect(
                host=self.config["host"],
                port=self.config["port"],
                database=self.config["database"],
                user=self.config["username"],
                password=self.config["password"],
            )
            yield conn
        finally:
            if conn:
                conn.close()

    def create_full_backup(
        self, description: str = "", task_id: str = "auto"
    ) -> Optional[str]:
        """
        创建完整备份

        Args:
            description: 备份描述
            task_id: 任务ID

        Returns:
            备份ID
        """
        timestamp = datetime.now()
        backup_id = f"full_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        backup_file = self.backup_root / f"{backup_id}.sql"

        self.logger.info(f"开始创建完整备份: {backup_id}")

        try:
            # 创建pg_dump命令
            cmd = [
                "pg_dump",
                "-h",
                self.config["host"],
                "-p",
                str(self.config["port"]),
                "-U",
                self.config["username"],
                "-d",
                self.config["database"],
                "-f",
                str(backup_file),
                "--verbose",
                "--no-password",
                "--format=custom",
                "--compress=9",
            ]

            # 设置密码环境变量
            env = os.environ.copy()
            env["PGPASSWORD"] = self.config["password"]

            # 执行备份
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)

            if result.returncode != 0:
                self.logger.error(f"备份失败: {result.stderr}")
                return None

            # 创建元数据
            metadata = BackupMetadata(
                backup_id=backup_id,
                timestamp=timestamp,
                database_version=self._get_database_version(),
                schema_hash=self._calculate_schema_hash(),
                size_bytes=backup_file.stat().st_size,
                backup_type="full",
                phase=self._get_current_phase(),
                task_id=task_id,
                file_path=str(backup_file),
                description=description or f"Full backup at {timestamp}",
                git_commit=self._get_git_commit(),
            )

            # 保存元数据
            self.metadata[backup_id] = metadata
            self._save_metadata()

            self.logger.info(
                f"完整备份创建成功: {backup_id} ({backup_file.stat().st_size} bytes)"
            )
            return backup_id

        except Exception as e:
            self.logger.error(f"创建完整备份失败: {e}")
            return None

    def create_schema_backup(self, description: str = "") -> Optional[str]:
        """
        创建架构备份（仅结构，不含数据）

        Args:
            description: 备份描述

        Returns:
            备份ID
        """
        timestamp = datetime.now()
        backup_id = f"schema_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        backup_file = self.backup_root / f"{backup_id}.sql"

        self.logger.info(f"开始创建架构备份: {backup_id}")

        try:
            cmd = [
                "pg_dump",
                "-h",
                self.config["host"],
                "-p",
                str(self.config["port"]),
                "-U",
                self.config["username"],
                "-d",
                self.config["database"],
                "-f",
                str(backup_file),
                "--schema-only",
                "--verbose",
                "--no-password",
            ]

            env = os.environ.copy()
            env["PGPASSWORD"] = self.config["password"]

            result = subprocess.run(cmd, env=env, capture_output=True, text=True)

            if result.returncode != 0:
                self.logger.error(f"架构备份失败: {result.stderr}")
                return None

            metadata = BackupMetadata(
                backup_id=backup_id,
                timestamp=timestamp,
                database_version=self._get_database_version(),
                schema_hash=self._calculate_schema_hash(),
                size_bytes=backup_file.stat().st_size,
                backup_type="schema_only",
                phase=self._get_current_phase(),
                task_id="schema",
                file_path=str(backup_file),
                description=description or f"Schema backup at {timestamp}",
                git_commit=self._get_git_commit(),
            )

            self.metadata[backup_id] = metadata
            self._save_metadata()

            self.logger.info(f"架构备份创建成功: {backup_id}")
            return backup_id

        except Exception as e:
            self.logger.error(f"创建架构备份失败: {e}")
            return None

    def _get_database_version(self) -> str:
        """获取数据库版本"""
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT version()")
                    return cursor.fetchone()[0]
        except Exception:
            return "unknown"

    def restore_backup(self, backup_id: str, confirm: bool = False) -> bool:
        """
        恢复备份

        Args:
            backup_id: 备份ID
            confirm: 是否确认恢复

        Returns:
            是否恢复成功
        """
        if backup_id not in self.metadata:
            self.logger.error(f"备份不存在: {backup_id}")
            return False

        metadata = self.metadata[backup_id]
        backup_file = Path(metadata.file_path)

        if not backup_file.exists():
            self.logger.error(f"备份文件不存在: {backup_file}")
            return False

        if not confirm:
            self.logger.warning("恢复操作需要确认，请设置confirm=True")
            return False

        self.logger.info(f"开始恢复备份: {backup_id}")

        try:
            # 首先创建当前状态的备份
            emergency_backup = self.create_full_backup(
                description=f"Emergency backup before restore {backup_id}"
            )

            if not emergency_backup:
                self.logger.error("创建紧急备份失败，终止恢复操作")
                return False

            # 恢复备份
            if metadata.backup_type == "schema_only":
                # 仅恢复架构
                success = self._restore_schema_only(backup_file)
            else:
                # 完整恢复
                success = self._restore_full_backup(backup_file)

            if success:
                self.logger.info(f"备份恢复成功: {backup_id}")
                return True
            else:
                self.logger.error(f"备份恢复失败: {backup_id}")
                # 如果恢复失败，尝试恢复紧急备份
                self.logger.info("尝试恢复紧急备份...")
                self._restore_full_backup(
                    Path(self.metadata[emergency_backup].file_path)
                )
                return False

        except Exception as e:
            self.logger.error(f"恢复备份异常: {e}")
            return False

    def _restore_full_backup(self, backup_file: Path) -> bool:
        """恢复完整备份"""
        try:
            # 终止所有活动连接
            self._terminate_connections()

            # 删除并重建数据库
            self._recreate_database()

            # 恢复数据
            cmd = [
                "pg_restore",
                "-h",
                self.config["host"],
                "-p",
                str(self.config["port"]),
                "-U",
                self.config["username"],
                "-d",
                self.config["database"],
                "--verbose",
                "--no-password",
                str(backup_file),
            ]

            env = os.environ.copy()
            env["PGPASSWORD"] = self.config["password"]

            result = subprocess.run(cmd, env=env, capture_output=True, text=True)

            return result.returncode == 0

        except Exception as e:
            self.logger.error(f"恢复完整备份失败: {e}")
            return False

    def _restore_schema_only(self, backup_file: Path) -> bool:
        """恢复架构备份"""
        try:
            cmd = [
                "psql",
                "-h",
                self.config["host"],
                "-p",
                str(self.config["port"]),
                "-U",
                self.config["username"],
                "-d",
                self.config["database"],
                "-f",
                str(backup_file),
                "--quiet",
            ]

            env = os.environ.copy()
            env["PGPASSWORD"] = self.config["password"]

            result = subprocess.run(cmd, env=env, capture_output=True, text=True)

            return result.returncode == 0

        except Exception as e:
            self.logger.error(f"恢复架构备份失败: {e}")
            return False

    def _terminate_connections(self):
        """终止数据库所有连接"""
        try:
            # 连接到postgres数据库来终止目标数据库的连接
            admin_conn = psycopg2.connect(
                host=self.config["host"],
                port=self.config["port"],
                database="postgres",
                user=self.config["username"],
                password=self.config["password"],
            )
            admin_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

            with admin_conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = %s AND pid <> pg_backend_pid()
                """,
                    (self.config["database"],),
                )

            admin_conn.close()

        except Exception as e:
            self.logger.warning(f"终止连接失败: {e}")

    def _recreate_database(self):
        """重建数据库"""
        try:
            admin_conn = psycopg2.connect(
                host=self.config["host"],
                port=self.config["port"],
                database="postgres",
                user=self.config["username"],
                password=self.config["password"],
            )
            admin_conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

            with admin_conn.cursor() as cursor:
                # 删除数据库
                cursor.execute(f'DROP DATABASE IF EXISTS "{self.config["database"]}"')
                # 重建数据库
                cursor.execute(f'CREATE DATABASE "{self.config["database"]}"')

            admin_conn.close()

        except Exception as e:
            self.logger.error(f"重建数据库失败: {e}")
            raise

    def list_backups(
        self, limit: int = 20, backup_type: Optional[str] = None
    ) -> List[BackupMetadata]:
        """
        列出备份

        Args:
            limit: 限制数量
            backup_type: 备份类型过滤

        Returns:
            备份列表
        """
        backups = list(self.metadata.values())

        # 按类型过滤
        if backup_type:
            backups = [b for b in backups if b.backup_type == backup_type]

        # 按时间排序
        backups.sort(key=lambda x: x.timestamp, reverse=True)

        return backups[:limit]

    def cleanup_old_backups(self, keep_days: int = 30, keep_count: int = 10):
        """
        清理旧备份

        Args:
            keep_days: 保留天数
            keep_count: 最少保留数量
        """
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        backups_to_remove = []

        # 按时间排序的备份列表
        sorted_backups = sorted(
            self.metadata.items(), key=lambda x: x[1].timestamp, reverse=True
        )

        # 保留最新的keep_count个备份
        for i, (backup_id, metadata) in enumerate(sorted_backups):
            if i >= keep_count and metadata.timestamp < cutoff_date:
                backups_to_remove.append(backup_id)

        # 删除旧备份
        for backup_id in backups_to_remove:
            self.remove_backup(backup_id)

        self.logger.info(f"清理了 {len(backups_to_remove)} 个旧备份")

    def remove_backup(self, backup_id: str) -> bool:
        """
        删除备份

        Args:
            backup_id: 备份ID

        Returns:
            是否删除成功
        """
        if backup_id not in self.metadata:
            self.logger.error(f"备份不存在: {backup_id}")
            return False

        metadata = self.metadata[backup_id]
        backup_file = Path(metadata.file_path)

        try:
            # 删除备份文件
            if backup_file.exists():
                backup_file.unlink()

            # 删除元数据
            del self.metadata[backup_id]
            self._save_metadata()

            self.logger.info(f"删除备份成功: {backup_id}")
            return True

        except Exception as e:
            self.logger.error(f"删除备份失败: {e}")
            return False

    def verify_backup(self, backup_id: str) -> bool:
        """
        验证备份完整性

        Args:
            backup_id: 备份ID

        Returns:
            是否验证通过
        """
        if backup_id not in self.metadata:
            self.logger.error(f"备份不存在: {backup_id}")
            return False

        metadata = self.metadata[backup_id]
        backup_file = Path(metadata.file_path)

        if not backup_file.exists():
            self.logger.error(f"备份文件不存在: {backup_file}")
            return False

        # 检查文件大小
        if backup_file.stat().st_size != metadata.size_bytes:
            self.logger.error(f"备份文件大小不匹配: {backup_id}")
            return False

        # 如果是pg_dump格式，验证文件头
        try:
            if metadata.backup_type == "full":
                # 验证pg_restore能否读取文件头
                cmd = ["pg_restore", "--list", str(backup_file)]

                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode != 0:
                    self.logger.error(f"备份文件损坏: {backup_id}")
                    return False

        except Exception as e:
            self.logger.error(f"验证备份失败: {e}")
            return False

        self.logger.info(f"备份验证通过: {backup_id}")
        return True


# 便捷函数
def create_backup_manager() -> DatabaseBackupManager:
    """创建备份管理器实例"""
    # 从环境变量或配置文件读取数据库配置
    config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "database": os.getenv("DB_NAME", "claude_enhancer"),
        "username": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", ""),
    }

    return DatabaseBackupManager(config)


if __name__ == "__main__":
    import argparse

    # 设置日志
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )

    parser = argparse.ArgumentParser(description="数据库备份管理器")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # 创建备份
    backup_parser = subparsers.add_parser("backup", help="创建备份")
    backup_parser.add_argument(
        "--type", choices=["full", "schema"], default="full", help="备份类型"
    )
    backup_parser.add_argument("--description", help="备份描述")
    backup_parser.add_argument("--task-id", help="任务ID")

    # 恢复备份
    restore_parser = subparsers.add_parser("restore", help="恢复备份")
    restore_parser.add_argument("backup_id", help="备份ID")
    restore_parser.add_argument("--confirm", action="store_true", help="确认恢复")

    # 列出备份
    list_parser = subparsers.add_parser("list", help="列出备份")
    list_parser.add_argument("--type", choices=["full", "schema"], help="过滤备份类型")
    list_parser.add_argument("--limit", type=int, default=20, help="限制数量")

    # 验证备份
    verify_parser = subparsers.add_parser("verify", help="验证备份")
    verify_parser.add_argument("backup_id", help="备份ID")

    # 清理备份
    cleanup_parser = subparsers.add_parser("cleanup", help="清理旧备份")
    cleanup_parser.add_argument("--days", type=int, default=30, help="保留天数")
    cleanup_parser.add_argument("--count", type=int, default=10, help="最少保留数量")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # 创建管理器
    manager = create_backup_manager()

    # 执行命令
    if args.command == "backup":
        if args.type == "full":
            backup_id = manager.create_full_backup(
                description=args.description or "", task_id=args.task_id or "cli"
            )
        else:
            backup_id = manager.create_schema_backup(description=args.description or "")

        if backup_id:
            print(f"备份创建成功: {backup_id}")
        else:
            print("备份创建失败")
            sys.exit(1)

    elif args.command == "restore":
        success = manager.restore_backup(args.backup_id, args.confirm)
        if success:
            print(f"备份恢复成功: {args.backup_id}")
        else:
            print(f"备份恢复失败: {args.backup_id}")
            sys.exit(1)

    elif args.command == "list":
        backups = manager.list_backups(args.limit, args.type)
        print(f"{'备份ID':<30} {'类型':<10} {'时间':<20} {'大小':<10} {'阶段':<5} {'描述'}")
        print("-" * 100)
        for backup in backups:
            size_mb = backup.size_bytes / 1024 / 1024
            print(
                f"{backup.backup_id:<30} {backup.backup_type:<10} {backup.timestamp.strftime('%Y-%m-%d %H:%M'):<20} {size_mb:.1f}MB {backup.phase:<5} {backup.description}"
            )

    elif args.command == "verify":
        success = manager.verify_backup(args.backup_id)
        if success:
            print(f"备份验证通过: {args.backup_id}")
        else:
            print(f"备份验证失败: {args.backup_id}")
            sys.exit(1)

    elif args.command == "cleanup":
        manager.cleanup_old_backups(args.days, args.count)
        print("清理完成")
