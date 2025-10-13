#!/usr/bin/env python3
"""
数据库设置测试脚本
测试数据库连接、模型创建和基本功能
"""

import sys
import uuid
import asyncio
import logging
from datetime import datetime, timedelta

# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_imports():
    """测试模块导入"""
    try:
        from core.config import get_database_config
        from core.database import get_db_manager, init_db
        from models import User, Project, Task, Label

        logger.info("✅ 所有模块导入成功")
        return True
    except Exception as e:
        logger.error(f"❌ 模块导入失败: {e}")
        return False


def test_database_config():
    """测试数据库配置"""
    try:
        from core.config import get_database_config

        config = get_database_config()

        logger.info(f"数据库配置:")
        logger.info(f"  - URL: {config.database_url}")
        logger.info(f"  - 连接池大小: {config.pool_size}")
        logger.info(f"  - 最大溢出: {config.max_overflow}")
        logger.info(f"  - 连接超时: {config.pool_timeout}s")

        # 测试URL生成
        sync_url = config.sync_database_url
        async_url = config.async_database_url

        logger.info(f"  - 同步URL: {sync_url}")
        logger.info(f"  - 异步URL: {async_url}")

        logger.info("✅ 数据库配置测试通过")
        return True
    except Exception as e:
        logger.error(f"❌ 数据库配置测试失败: {e}")
        return False


def test_database_connection():
    """测试数据库连接"""
    try:
        from core.database import get_db_manager

        db_manager = get_db_manager()

        # 测试同步连接
        if db_manager.test_connection():
            logger.info("✅ 同步数据库连接成功")
        else:
            logger.error("❌ 同步数据库连接失败")
            return False

        # 测试Redis连接（如果可用）
        try:
            if db_manager.test_redis_connection():
                logger.info("✅ Redis连接成功")
            else:
                logger.warning("⚠️  Redis连接失败（可选）")
        except Exception as e:
            logger.warning(f"⚠️  Redis测试跳过: {e}")

        return True
    except Exception as e:
        logger.error(f"❌ 数据库连接测试失败: {e}")
        return False


async def test_async_database_connection():
    """测试异步数据库连接"""
    try:
        from core.database import get_db_manager

        db_manager = get_db_manager()

        if await db_manager.test_async_connection():
            logger.info("✅ 异步数据库连接成功")
            return True
        else:
            logger.error("❌ 异步数据库连接失败")
            return False
    except Exception as e:
        logger.error(f"❌ 异步数据库连接测试失败: {e}")
        return False


def test_table_creation():
    """测试数据库表创建"""
    try:
        from core.database import get_db_manager

        db_manager = get_db_manager()

        # 删除现有表（如果存在）
        try:
            db_manager.drop_all_tables()
            logger.info("删除现有表完成")
        except Exception as e:
            logger.info(f"删除表跳过（可能不存在）: {e}")

        # 创建表
        db_manager.create_all_tables()
        logger.info("✅ 数据库表创建成功")

        # 初始化默认数据
        db_manager.init_default_data()
        logger.info("✅ 默认数据初始化成功")

        return True
    except Exception as e:
        logger.error(f"❌ 表创建失败: {e}")
        return False


def test_model_operations():
    """测试模型基本操作"""
    try:
        from core.database import get_db_manager
        from models import User, Project, Task, Label

        db_manager = get_db_manager()

        with db_manager.get_session() as session:
            pass  # Auto-fixed empty block
            # 创建测试用户
            user_id = str(uuid.uuid4())
            test_user = User(
                id=user_id,
                username="testuser",
                email="test@example.com",
                password_hash="hashed_password",
                full_name="Test User",
            )
            session.add(test_user)
            session.flush()  # 确保用户被保存

            logger.info(f"✅ 创建测试用户: {test_user.username}")

            # 创建测试项目
            project_id = str(uuid.uuid4())
            test_project = Project(
                id=project_id, name="测试项目", description="这是一个测试项目", creator_id=user_id
            )
            session.add(test_project)
            session.flush()

            logger.info(f"✅ 创建测试项目: {test_project.name}")

            # 创建测试任务
            task_id = str(uuid.uuid4())
            test_task = Task(
                id=task_id,
                title="测试任务",
                description="这是一个测试任务",
                creator_id=user_id,
                assignee_id=user_id,
                project_id=project_id,
                due_date=datetime.utcnow() + timedelta(days=7),
            )
            session.add(test_task)
            session.flush()

            logger.info(f"✅ 创建测试任务: {test_task.title}")

            # 测试查询
            users = session.query(User).all()
            projects = session.query(Project).all()
            tasks = session.query(Task).all()
            labels = session.query(Label).all()

            logger.info(f"数据统计:")
            logger.info(f"  - 用户数: {len(users)}")
            logger.info(f"  - 项目数: {len(projects)}")
            logger.info(f"  - 任务数: {len(tasks)}")
            logger.info(f"  - 标签数: {len(labels)}")

            # 测试关系查询
            user_projects = test_user.created_projects.all()
            user_tasks = test_user.assigned_tasks.all()
            project_tasks = test_project.tasks.all()

            logger.info(f"关系测试:")
            logger.info(f"  - 用户创建的项目: {len(user_projects)}")
            logger.info(f"  - 用户分配的任务: {len(user_tasks)}")
            logger.info(f"  - 项目下的任务: {len(project_tasks)}")

            # 测试方法
            logger.info(f"模型方法测试:")
            logger.info(f"  - 用户显示名: {test_user.display_name}")
            logger.info(f"  - 项目完成度: {test_project.progress_percentage:.1f}%")
            logger.info(f"  - 任务已完成: {test_task.is_completed}")
            logger.info(f"  - 任务已过期: {test_task.is_overdue}")

            logger.info("✅ 模型操作测试通过")
            return True

    except Exception as e:
        logger.error(f"❌ 模型操作测试失败: {e}")
        return False


def test_environment_variables():
    """测试环境变量"""
    import os

    logger.info("环境变量检查:")

    env_vars = [
        "DATABASE_URL",
        "DB_DATABASE_HOST",
        "DB_DATABASE_PORT",
        "DB_DATABASE_NAME",
        "DB_DATABASE_USER",
        "DB_DATABASE_PASSWORD",
        "REDIS_URL",
    ]

    for var in env_vars:
        value = os.getenv(var)
        if value:
            pass  # Auto-fixed empty block
            # 隐藏敏感信息
            if "password" in var.lower() or "url" in var.lower():
                display_value = value[:10] + "..." if len(value) > 10 else value
            else:
                display_value = value
            logger.info(f"  - {var}: {display_value}")
        else:
            logger.info(f"  - {var}: 未设置（使用默认值）")


async def run_all_tests():
    """运行所有测试"""
    logger.info("🚀 开始数据库设置测试")
    logger.info("=" * 50)

    # 测试环境变量
    test_environment_variables()
    logger.info("-" * 30)

    # 测试导入
    if not test_imports():
        return False
    logger.info("-" * 30)

    # 测试配置
    if not test_database_config():
        return False
    logger.info("-" * 30)

    # 测试连接
    if not test_database_connection():
        return False
    logger.info("-" * 30)

    # 测试异步连接
    if not await test_async_database_connection():
        return False
    logger.info("-" * 30)

    # 测试表创建
    if not test_table_creation():
        return False
    logger.info("-" * 30)

    # 测试模型操作
    if not test_model_operations():
        return False

    logger.info("=" * 50)
    logger.info("🎉 所有测试通过！数据库设置成功！")
    return True


def main():
    """主函数"""
    try:
        pass  # Auto-fixed empty block
        # 添加项目路径到系统路径
        import sys
        from pathlib import Path

        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))

        # 运行测试
        success = asyncio.run(run_all_tests())

        if success:
            logger.info("✅ 数据库设置测试完成")
            sys.exit(0)
        else:
            logger.error("❌ 数据库设置测试失败")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("测试被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"测试执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
