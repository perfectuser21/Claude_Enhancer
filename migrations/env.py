"""
Alembic环境配置
处理数据库迁移的环境设置和配置
"""

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入模型
from src.models.base import BaseModel
from src.models import User, Project, Task, Label
from src.core.config import get_database_config

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = BaseModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def get_database_url():
    """获取数据库URL"""
    # 首先尝试从环境变量获取
    url = os.getenv("DATABASE_URL")
    if url:
        return url

    # 如果没有环境变量，使用配置文件
    try:
        db_config = get_database_config()
        return db_config.sync_database_url
    except Exception:
        # 如果配置失败，使用默认值
        return "postgresql://postgres:password@localhost:5432/task_management"


def run_migrations_offline() -> None:
    """
    在'离线'模式下运行迁移。

    这将配置上下文以使用URL而不实际连接到数据库引擎。
    通过跳过Engine创建，我们甚至不需要DBAPI可用。

    调用context.execute()会直接将生成的SQL发送到输出文件。
    """
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    在'在线'模式下运行迁移。

    在这种场景下，我们需要创建一个Engine
    并将连接与上下文关联。
    """
    # 获取数据库URL并设置到配置中
    database_url = get_database_url()
    config.set_main_option("sqlalchemy.url", database_url)

    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            include_schemas=True,
            # 表名过滤器 - 只迁移我们的表
            include_name=lambda name, type_: type_ == "table"
            and name
            in ["user", "project", "task", "label", "project_members", "task_labels"],
        )

        with context.begin_transaction():
            context.run_migrations()


# 根据运行模式选择迁移方法
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
