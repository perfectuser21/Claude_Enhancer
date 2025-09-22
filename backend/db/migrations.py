"""
数据库迁移管理
==============

提供数据库迁移的管理功能:
- Alembic集成
- 版本管理
- 自动迁移
- 回滚支持
"""

import os
import logging
from typing import Optional, List
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import text

from .database import engine, get_db_session
from .config import get_database_config

# 配置日志
logger = logging.getLogger(__name__)


class MigrationManager:
    """
    迁移管理器
    ==========

    管理数据库迁移的完整生命周期
    """

    def __init__(self, migrations_dir: Optional[str] = None):
        """
        初始化迁移管理器

        Args:
            migrations_dir: 迁移文件目录
        """
        self.migrations_dir = migrations_dir or "backend/migrations"
        self.alembic_cfg = None
        self._setup_alembic_config()

    def _setup_alembic_config(self):
        """设置Alembic配置"""
        try:
            # 创建迁移目录
            Path(self.migrations_dir).mkdir(parents=True, exist_ok=True)

            # 创建alembic.ini配置文件
            alembic_ini_path = os.path.join(self.migrations_dir, "alembic.ini")
            if not os.path.exists(alembic_ini_path):
                self._create_alembic_ini(alembic_ini_path)

            # 配置Alembic
            self.alembic_cfg = Config(alembic_ini_path)
            self.alembic_cfg.set_main_option("script_location", self.migrations_dir)

            # 设置数据库连接
            db_config = get_database_config()
            self.alembic_cfg.set_main_option("sqlalchemy.url", db_config.get_sync_url())

        except Exception as e:
            logger.error(f"Alembic配置设置失败: {e}")
            raise

    def _create_alembic_ini(self, ini_path: str):
        """创建alembic.ini配置文件"""
        ini_content = """[alembic]
script_location = %(here)s
file_template = %%(rev)s_%%(slug)s
truncate_slug_length = 40
timezone = UTC

# Logging configuration
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""
        with open(ini_path, "w") as f:
            f.write(ini_content)

    def init_migrations(self) -> bool:
        """
        初始化迁移环境

        Returns:
            是否初始化成功
        """
        try:
            # 初始化Alembic环境
            command.init(self.alembic_cfg, self.migrations_dir)

            # 创建env.py文件
            self._create_env_py()

            logger.info("迁移环境初始化完成")
            return True

        except Exception as e:
            logger.error(f"迁移环境初始化失败: {e}")
            return False

    def _create_env_py(self):
        """创建env.py文件"""
        env_py_path = os.path.join(self.migrations_dir, "env.py")
        env_py_content = '''"""Alembic环境配置"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# 导入模型
from backend.models.base import Base

# Alembic配置对象
config = context.config

# 设置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 目标元数据
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """离线模式运行迁移"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """在线模式运行迁移"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''
        with open(env_py_path, "w") as f:
            f.write(env_py_content)

    def create_migration(
        self, message: str, auto_generate: bool = True
    ) -> Optional[str]:
        """
        创建新迁移

        Args:
            message: 迁移描述
            auto_generate: 是否自动生成

        Returns:
            迁移文件路径
        """
        try:
            if auto_generate:
                command.revision(self.alembic_cfg, message=message, autogenerate=True)
            else:
                command.revision(self.alembic_cfg, message=message)

            logger.info(f"创建迁移: {message}")
            return self._get_latest_migration_file()

        except Exception as e:
            logger.error(f"创建迁移失败: {e}")
            return None

    def upgrade(self, revision: str = "head") -> bool:
        """
        升级数据库

        Args:
            revision: 目标版本

        Returns:
            是否升级成功
        """
        try:
            command.upgrade(self.alembic_cfg, revision)
            logger.info(f"数据库升级到版本: {revision}")
            return True

        except Exception as e:
            logger.error(f"数据库升级失败: {e}")
            return False

    def downgrade(self, revision: str) -> bool:
        """
        降级数据库

        Args:
            revision: 目标版本

        Returns:
            是否降级成功
        """
        try:
            command.downgrade(self.alembic_cfg, revision)
            logger.info(f"数据库降级到版本: {revision}")
            return True

        except Exception as e:
            logger.error(f"数据库降级失败: {e}")
            return False

    def get_current_revision(self) -> Optional[str]:
        """
        获取当前数据库版本

        Returns:
            当前版本号
        """
        try:
            with get_db_session() as session:
                context = MigrationContext.configure(session.connection())
                return context.get_current_revision()

        except Exception as e:
            logger.error(f"获取当前版本失败: {e}")
            return None

    def get_migration_history(self) -> List[dict]:
        """
        获取迁移历史

        Returns:
            迁移历史列表
        """
        try:
            script_dir = ScriptDirectory.from_config(self.alembic_cfg)
            history = []

            for revision in script_dir.walk_revisions():
                history.append(
                    {
                        "revision": revision.revision,
                        "down_revision": revision.down_revision,
                        "message": revision.doc,
                        "created_at": revision.create_date
                        if hasattr(revision, "create_date")
                        else None,
                    }
                )

            return history

        except Exception as e:
            logger.error(f"获取迁移历史失败: {e}")
            return []

    def check_pending_migrations(self) -> bool:
        """
        检查是否有待执行的迁移

        Returns:
            是否有待执行的迁移
        """
        try:
            current = self.get_current_revision()
            script_dir = ScriptDirectory.from_config(self.alembic_cfg)
            head = script_dir.get_current_head()

            return current != head

        except Exception as e:
            logger.error(f"检查待执行迁移失败: {e}")
            return False

    def _get_latest_migration_file(self) -> Optional[str]:
        """获取最新的迁移文件路径"""
        try:
            versions_dir = os.path.join(self.migrations_dir, "versions")
            if not os.path.exists(versions_dir):
                return None

            migration_files = [
                f
                for f in os.listdir(versions_dir)
                if f.endswith(".py") and not f.startswith("__")
            ]

            if not migration_files:
                return None

            # 按创建时间排序，返回最新的
            migration_files.sort(
                key=lambda f: os.path.getctime(os.path.join(versions_dir, f))
            )
            return os.path.join(versions_dir, migration_files[-1])

        except Exception as e:
            logger.error(f"获取最新迁移文件失败: {e}")
            return None

    def generate_schema_sql(self, output_file: str = "schema.sql") -> bool:
        """
        生成数据库架构SQL

        Args:
            output_file: 输出文件路径

        Returns:
            是否生成成功
        """
        try:
            from backend.models.base import Base
            from sqlalchemy.schema import CreateTable

            with open(output_file, "w") as f:
                for table in Base.metadata.sorted_tables:
                    f.write(str(CreateTable(table).compile(engine)) + ";\n\n")

            logger.info(f"架构SQL已生成: {output_file}")
            return True

        except Exception as e:
            logger.error(f"生成架构SQL失败: {e}")
            return False

    def backup_before_migration(self, backup_file: str) -> bool:
        """
        迁移前备份数据库

        Args:
            backup_file: 备份文件路径

        Returns:
            是否备份成功
        """
        try:
            config = get_database_config()

            # 使用pg_dump备份PostgreSQL数据库
            import subprocess

            cmd = [
                "pg_dump",
                "-h",
                config.host,
                "-p",
                str(config.port),
                "-U",
                config.username,
                "-d",
                config.database,
                "-f",
                backup_file,
                "--verbose",
            ]

            # 设置密码环境变量
            env = os.environ.copy()
            env["PGPASSWORD"] = config.password

            result = subprocess.run(cmd, env=env, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"数据库备份成功: {backup_file}")
                return True
            else:
                logger.error(f"数据库备份失败: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"数据库备份失败: {e}")
            return False


# 创建全局迁移管理器
migration_manager = MigrationManager()


# 便捷函数
def init_migrations() -> bool:
    """初始化迁移环境"""
    return migration_manager.init_migrations()


def create_migration(message: str, auto_generate: bool = True) -> Optional[str]:
    """创建新迁移"""
    return migration_manager.create_migration(message, auto_generate)


def upgrade_database(revision: str = "head") -> bool:
    """升级数据库"""
    return migration_manager.upgrade(revision)


def downgrade_database(revision: str) -> bool:
    """降级数据库"""
    return migration_manager.downgrade(revision)


def get_current_version() -> Optional[str]:
    """获取当前数据库版本"""
    return migration_manager.get_current_revision()


def check_migrations() -> bool:
    """检查待执行的迁移"""
    return migration_manager.check_pending_migrations()


# 导出公共接口
__all__ = [
    "MigrationManager",
    "migration_manager",
    "init_migrations",
    "create_migration",
    "upgrade_database",
    "downgrade_database",
    "get_current_version",
    "check_migrations",
]
