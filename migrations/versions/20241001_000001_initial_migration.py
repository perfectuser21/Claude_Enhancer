"""初始数据库结构创建

Revision ID: 20241001_000001
Revises:
Create Date: 2024-10-01 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20241001_000001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升级数据库结构"""

    # 创建用户表
    op.create_table(
        "user",
        sa.Column("id", sa.String(length=36), nullable=False, comment="主键ID"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("username", sa.String(length=50), nullable=False, comment="用户名"),
        sa.Column("email", sa.String(length=255), nullable=False, comment="邮箱地址"),
        sa.Column(
            "password_hash", sa.String(length=255), nullable=False, comment="密码哈希"
        ),
        sa.Column("full_name", sa.String(length=100), nullable=True, comment="全名"),
        sa.Column("avatar_url", sa.String(length=500), nullable=True, comment="头像URL"),
        sa.Column("bio", sa.Text(), nullable=True, comment="个人简介"),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, default=True, comment="是否激活"
        ),
        sa.Column(
            "is_verified",
            sa.Boolean(),
            nullable=False,
            default=False,
            comment="是否已验证邮箱",
        ),
        sa.Column(
            "last_login_at", sa.DateTime(timezone=True), nullable=True, comment="最后登录时间"
        ),
        sa.Column(
            "timezone",
            sa.String(length=50),
            nullable=False,
            default="UTC",
            comment="用户时区",
        ),
        sa.Column("preferences", sa.Text(), nullable=True, comment="用户偏好设置（JSON格式）"),
        sa.PrimaryKeyConstraint("id"),
    )

    # 创建用户表索引
    op.create_index(op.f("ix_user_id"), "user", ["id"], unique=False)
    op.create_index(op.f("ix_user_username"), "user", ["username"], unique=True)
    op.create_index(op.f("ix_user_email"), "user", ["email"], unique=True)

    # 创建项目表
    op.create_table(
        "project",
        sa.Column("id", sa.String(length=36), nullable=False, comment="主键ID"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("name", sa.String(length=200), nullable=False, comment="项目名称"),
        sa.Column("description", sa.Text(), nullable=True, comment="项目描述"),
        sa.Column("creator_id", sa.String(length=36), nullable=False, comment="创建者ID"),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            default="active",
            comment="项目状态",
        ),
        sa.Column(
            "priority",
            sa.String(length=20),
            nullable=False,
            default="medium",
            comment="优先级",
        ),
        sa.Column(
            "start_date", sa.DateTime(timezone=True), nullable=True, comment="开始日期"
        ),
        sa.Column(
            "due_date", sa.DateTime(timezone=True), nullable=True, comment="截止日期"
        ),
        sa.Column(
            "completed_at", sa.DateTime(timezone=True), nullable=True, comment="完成时间"
        ),
        sa.Column(
            "is_public", sa.Boolean(), nullable=False, default=False, comment="是否公开"
        ),
        sa.Column(
            "color",
            sa.String(length=7),
            nullable=False,
            default="#3b82f6",
            comment="项目颜色标识",
        ),
        sa.Column("settings", sa.Text(), nullable=True, comment="项目设置（JSON格式）"),
        sa.ForeignKeyConstraint(
            ["creator_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 创建项目表索引
    op.create_index(op.f("ix_project_id"), "project", ["id"], unique=False)
    op.create_index(op.f("ix_project_name"), "project", ["name"], unique=False)
    op.create_index(
        op.f("ix_project_creator_id"), "project", ["creator_id"], unique=False
    )
    op.create_index(op.f("ix_project_status"), "project", ["status"], unique=False)
    op.create_index(op.f("ix_project_priority"), "project", ["priority"], unique=False)
    op.create_index(op.f("ix_project_due_date"), "project", ["due_date"], unique=False)

    # 创建标签表
    op.create_table(
        "label",
        sa.Column("id", sa.String(length=36), nullable=False, comment="主键ID"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("name", sa.String(length=50), nullable=False, comment="标签名称"),
        sa.Column("description", sa.Text(), nullable=True, comment="标签描述"),
        sa.Column(
            "color",
            sa.String(length=7),
            nullable=False,
            default="#6b7280",
            comment="标签颜色（HEX格式）",
        ),
        sa.Column(
            "is_system", sa.Boolean(), nullable=False, default=False, comment="是否为系统标签"
        ),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, default=True, comment="是否激活"
        ),
        sa.Column(
            "sort_order", sa.Integer(), nullable=False, default=0, comment="排序顺序"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 创建标签表索引
    op.create_index(op.f("ix_label_id"), "label", ["id"], unique=False)
    op.create_index(op.f("ix_label_name"), "label", ["name"], unique=True)

    # 创建任务表
    op.create_table(
        "task",
        sa.Column("id", sa.String(length=36), nullable=False, comment="主键ID"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="创建时间",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
            comment="更新时间",
        ),
        sa.Column("title", sa.String(length=200), nullable=False, comment="任务标题"),
        sa.Column("description", sa.Text(), nullable=True, comment="任务描述"),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            default="todo",
            comment="任务状态",
        ),
        sa.Column(
            "priority",
            sa.String(length=20),
            nullable=False,
            default="medium",
            comment="优先级",
        ),
        sa.Column("project_id", sa.String(length=36), nullable=True, comment="所属项目ID"),
        sa.Column("creator_id", sa.String(length=36), nullable=False, comment="创建者ID"),
        sa.Column(
            "assignee_id", sa.String(length=36), nullable=True, comment="分配给的用户ID"
        ),
        sa.Column("parent_id", sa.String(length=36), nullable=True, comment="父任务ID"),
        sa.Column("position", sa.Integer(), nullable=False, default=0, comment="排序位置"),
        sa.Column("estimated_hours", sa.Float(), nullable=True, comment="预估工时"),
        sa.Column("actual_hours", sa.Float(), nullable=True, comment="实际工时"),
        sa.Column(
            "due_date", sa.DateTime(timezone=True), nullable=True, comment="截止日期"
        ),
        sa.Column(
            "completed_at", sa.DateTime(timezone=True), nullable=True, comment="完成时间"
        ),
        sa.Column(
            "is_archived", sa.Boolean(), nullable=False, default=False, comment="是否归档"
        ),
        sa.Column("metadata", sa.Text(), nullable=True, comment="额外元数据（JSON格式）"),
        sa.ForeignKeyConstraint(
            ["assignee_id"],
            ["user.id"],
        ),
        sa.ForeignKeyConstraint(
            ["creator_id"],
            ["user.id"],
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["task.id"],
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["project.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # 创建任务表索引
    op.create_index(op.f("ix_task_id"), "task", ["id"], unique=False)
    op.create_index(op.f("ix_task_title"), "task", ["title"], unique=False)
    op.create_index(op.f("ix_task_status"), "task", ["status"], unique=False)
    op.create_index(op.f("ix_task_priority"), "task", ["priority"], unique=False)
    op.create_index(op.f("ix_task_project_id"), "task", ["project_id"], unique=False)
    op.create_index(op.f("ix_task_creator_id"), "task", ["creator_id"], unique=False)
    op.create_index(op.f("ix_task_assignee_id"), "task", ["assignee_id"], unique=False)
    op.create_index(op.f("ix_task_parent_id"), "task", ["parent_id"], unique=False)
    op.create_index(op.f("ix_task_due_date"), "task", ["due_date"], unique=False)

    # 创建项目成员关联表
    op.create_table(
        "project_members",
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column(
            "role",
            sa.String(length=20),
            nullable=True,
            default="member",
            comment="成员角色",
        ),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=True,
            comment="加入时间",
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["project.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("project_id", "user_id"),
    )

    # 创建任务标签关联表
    op.create_table(
        "task_labels",
        sa.Column("task_id", sa.String(length=36), nullable=False),
        sa.Column("label_id", sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(
            ["label_id"],
            ["label.id"],
        ),
        sa.ForeignKeyConstraint(
            ["task_id"],
            ["task.id"],
        ),
        sa.PrimaryKeyConstraint("task_id", "label_id"),
    )


def downgrade() -> None:
    """降级数据库结构"""

    # 删除关联表
    op.drop_table("task_labels")
    op.drop_table("project_members")

    # 删除主表
    op.drop_index(op.f("ix_task_due_date"), table_name="task")
    op.drop_index(op.f("ix_task_parent_id"), table_name="task")
    op.drop_index(op.f("ix_task_assignee_id"), table_name="task")
    op.drop_index(op.f("ix_task_creator_id"), table_name="task")
    op.drop_index(op.f("ix_task_project_id"), table_name="task")
    op.drop_index(op.f("ix_task_priority"), table_name="task")
    op.drop_index(op.f("ix_task_status"), table_name="task")
    op.drop_index(op.f("ix_task_title"), table_name="task")
    op.drop_index(op.f("ix_task_id"), table_name="task")
    op.drop_table("task")

    op.drop_index(op.f("ix_label_name"), table_name="label")
    op.drop_index(op.f("ix_label_id"), table_name="label")
    op.drop_table("label")

    op.drop_index(op.f("ix_project_due_date"), table_name="project")
    op.drop_index(op.f("ix_project_priority"), table_name="project")
    op.drop_index(op.f("ix_project_status"), table_name="project")
    op.drop_index(op.f("ix_project_creator_id"), table_name="project")
    op.drop_index(op.f("ix_project_name"), table_name="project")
    op.drop_index(op.f("ix_project_id"), table_name="project")
    op.drop_table("project")

    op.drop_index(op.f("ix_user_email"), table_name="user")
    op.drop_index(op.f("ix_user_username"), table_name="user")
    op.drop_index(op.f("ix_user_id"), table_name="user")
    op.drop_table("user")
