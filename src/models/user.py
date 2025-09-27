"""
用户数据模型
管理用户账户信息、认证和权限
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Text, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class User(BaseModel):
    """
    用户模型

    字段说明：
    - username: 用户名（唯一）
    - email: 邮箱地址（唯一）
    - password_hash: 密码哈希
    - full_name: 全名
    - avatar_url: 头像URL
    - bio: 个人简介
    - is_active: 是否激活
    - is_verified: 是否已验证邮箱
    - last_login_at: 最后登录时间
    - timezone: 用户时区
    - preferences: 用户偏好设置（JSON格式）
    """

    # 基本信息
    username: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False, comment="用户名"
    )

    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False, comment="邮箱地址"
    )

    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="密码哈希"
    )

    # 个人资料
    full_name: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="全名"
    )

    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="头像URL"
    )

    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="个人简介")

    # 状态字段
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="是否激活"
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否已验证邮箱"
    )

    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="最后登录时间"
    )

    # 设置
    timezone: Mapped[str] = mapped_column(
        String(50), default="UTC", nullable=False, comment="用户时区"
    )

    preferences: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="用户偏好设置（JSON格式）"
    )

    # 关系定义
    # 用户创建的项目
    created_projects: Mapped[List["Project"]] = relationship(
        "Project",
        back_populates="creator",
        foreign_keys="[Project.creator_id]",
        lazy="dynamic",
    )

    # 用户参与的项目（多对多关系）
    projects: Mapped[List["Project"]] = relationship(
        "Project", secondary="project_members", back_populates="members", lazy="dynamic"
    )

    # 用户分配到的任务
    assigned_tasks: Mapped[List["Task"]] = relationship(
        "Task",
        back_populates="assignee",
        foreign_keys="[Task.assignee_id]",
        lazy="dynamic",
    )

    # 用户创建的任务
    created_tasks: Mapped[List["Task"]] = relationship(
        "Task",
        back_populates="creator",
        foreign_keys="[Task.creator_id]",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"<User(username={self.username}, email={self.email})>"

    @property
    def display_name(self) -> str:
        """显示名称，优先使用全名，否则使用用户名"""
        return self.full_name if self.full_name else self.username

    def is_member_of(self, project_id: str) -> bool:
        """检查用户是否是指定项目的成员"""
        return self.projects.filter_by(id=project_id).first() is not None

    def can_access_task(self, task_id: str) -> bool:
        """检查用户是否可以访问指定任务"""
        from .task import Task
        from .project import Project

        # 查询任务是否存在且用户有权限访问
        task = self.assigned_tasks.filter_by(id=task_id).first()
        if task:
            return True

        # 检查是否是任务所属项目的成员
        task = Task.query.filter_by(id=task_id).first()
        if task and task.project:
            return self.is_member_of(task.project.id)

        return False
