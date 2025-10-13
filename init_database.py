#!/usr/bin/env python3
"""
数据库初始化脚本
用于初始化数据库、运行迁移和创建默认数据
"""

import sys
import os
import logging
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def check_dependencies():
    """检查依赖包"""
    required_packages = ["sqlalchemy", "alembic", "psycopg2", "redis", "pydantic"]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✅ {package} 已安装")
        except ImportError:
            missing_packages.append(package)
            logger.error(f"❌ {package} 未安装")

    if missing_packages:
        logger.error(f"缺少依赖包: {', '.join(missing_packages)}")
        logger.error("请运行: pip install -r backend/requirements.txt")
        return False

    return True


def run_migrations():
    """运行数据库迁移"""
    try:
        import subprocess

        # 检查Alembic配置
        alembic_ini = project_root / "alembic.ini"
        if not alembic_ini.exists():
            logger.error("alembic.ini 文件不存在")
            return False

        # 检查迁移目录
        migrations_dir = project_root / "migrations"
        if not migrations_dir.exists():
            logger.error("migrations 目录不存在")
            return False

        logger.info("开始运行数据库迁移...")

        # 运行迁移
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=project_root,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            logger.info("✅ 数据库迁移完成")
            return True
        else:
            logger.error(f"❌ 数据库迁移失败: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"运行迁移时出错: {e}")
        return False


def init_database_direct():
    """直接初始化数据库（不使用迁移）"""
    try:
        from core.database import init_db

        init_db()
        logger.info("✅ 数据库直接初始化完成")
        return True
    except Exception as e:
        logger.error(f"❌ 数据库直接初始化失败: {e}")
        return False


def create_sample_data():
    """创建示例数据"""
    try:
        from core.database import get_db_manager
        from models import User, Project, Task, Label
        import uuid
        from datetime import datetime, timedelta

        db_manager = get_db_manager()

        with db_manager.get_session() as session:
            pass  # Auto-fixed empty block
            # 检查是否已有用户
            existing_users = session.query(User).count()
            if existing_users > 0:
                logger.info("数据库中已有用户，跳过示例数据创建")
                return True

            # 创建管理员用户
            admin_id = str(uuid.uuid4())
            admin_user = User(
                id=admin_id,
                username="admin",
                email="admin@taskmanager.com",
                password_hash="$2b$12$example_hash",  # 实际应用中应该是真正的哈希
                full_name="系统管理员",
                is_verified=True,
            )
            session.add(admin_user)

            # 创建测试用户
            user_id = str(uuid.uuid4())
            test_user = User(
                id=user_id,
                username="testuser",
                email="test@taskmanager.com",
                password_hash="$2b$12$example_hash",
                full_name="测试用户",
                is_verified=True,
            )
            session.add(test_user)

            session.flush()  # 确保用户被保存

            # 创建示例项目
            project_id = str(uuid.uuid4())
            sample_project = Project(
                id=project_id,
                name="示例项目",
                description="这是一个示例项目，用于演示任务管理系统的功能",
                creator_id=admin_id,
                status="active",
                priority="high",
                due_date=datetime.utcnow() + timedelta(days=30),
                color="#3b82f6",
            )
            session.add(sample_project)
            session.flush()

            # 添加项目成员
            sample_project.add_member(test_user)

            # 创建示例任务
            tasks_data = [
                {
                    "title": "项目规划",
                    "description": "制定项目计划和时间表",
                    "status": "completed",
                    "priority": "high",
                    "assignee_id": admin_id,
                },
                {
                    "title": "需求分析",
                    "description": "分析项目需求和功能点",
                    "status": "in_progress",
                    "priority": "high",
                    "assignee_id": user_id,
                },
                {
                    "title": "界面设计",
                    "description": "设计用户界面和交互流程",
                    "status": "todo",
                    "priority": "medium",
                    "assignee_id": user_id,
                },
                {
                    "title": "后端开发",
                    "description": "开发后端API和数据库",
                    "status": "todo",
                    "priority": "high",
                    "assignee_id": admin_id,
                },
                {
                    "title": "前端开发",
                    "description": "开发前端界面和功能",
                    "status": "todo",
                    "priority": "medium",
                    "assignee_id": user_id,
                },
            ]

            for i, task_data in enumerate(tasks_data):
                task = Task(
                    id=str(uuid.uuid4()),
                    title=task_data["title"],
                    description=task_data["description"],
                    status=task_data["status"],
                    priority=task_data["priority"],
                    project_id=project_id,
                    creator_id=admin_id,
                    assignee_id=task_data["assignee_id"],
                    position=i,
                    due_date=datetime.utcnow() + timedelta(days=7 + i * 3),
                )
                session.add(task)

            # 为任务添加标签
            labels = session.query(Label).filter_by(is_system=True).all()
            if labels:
                tasks = session.query(Task).all()
                for i, task in enumerate(tasks):
                    if i < len(labels):
                        task.add_label(labels[i])

            session.commit()
            logger.info("✅ 示例数据创建完成")
            logger.info(f"  - 创建了 2 个用户")
            logger.info(f"  - 创建了 1 个项目")
            logger.info(f"  - 创建了 {len(tasks_data)} 个任务")

            return True

    except Exception as e:
        logger.error(f"❌ 示例数据创建失败: {e}")
        return False


def main():
    """主函数"""
    logger.info("🚀 开始数据库初始化")
    logger.info("=" * 50)

    # 检查依赖
    if not check_dependencies():
        sys.exit(1)

    logger.info("-" * 30)

    # 选择初始化方式
    use_migrations = True

    if use_migrations:
        pass  # Auto-fixed empty block
        # 使用迁移方式
        if not run_migrations():
            logger.warning("迁移失败，尝试直接初始化...")
            if not init_database_direct():
                logger.error("数据库初始化失败")
                sys.exit(1)
    else:
        pass  # Auto-fixed empty block
        # 直接初始化
        if not init_database_direct():
            logger.error("数据库初始化失败")
            sys.exit(1)

    logger.info("-" * 30)

    # 创建示例数据
    if create_sample_data():
        logger.info("数据库初始化完全成功！")
    else:
        logger.warning("示例数据创建失败，但数据库初始化成功")

    logger.info("=" * 50)
    logger.info("🎉 数据库初始化完成！")

    # 显示使用说明
    logger.info("\n使用说明:")
    logger.info("1. 管理员账户: admin / admin@taskmanager.com")
    logger.info("2. 测试账户: testuser / test@taskmanager.com")
    logger.info("3. 示例项目已创建，包含多个示例任务")
    logger.info("4. 可以运行 python src/test_database_setup.py 来测试数据库设置")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("初始化被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"初始化失败: {e}")
        sys.exit(1)
