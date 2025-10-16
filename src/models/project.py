"""
项目数据模型
管理项目信息、成员和权限
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


# 项目成员关联表（多对多关系）
# 注意：Table()定义中必须使用Column()，不能使用mapped_column()
project_members = Table(
    "project_members",
    BaseModel.metadata,
    Column("project_id", String(36), ForeignKey("project.id"), primary_key=True),
    Column("user_id", String(36), ForeignKey("user.id"), primary_key=True),
    Column("role", String(20), default="member", comment="成员角色"),
    Column(
        "joined_at", DateTime(timezone=True), server_default="NOW()", comment="加入时间"
    ),
)


class Project(BaseModel):
    """
    项目模型

    字段说明：
    - name: 项目名称
    - description: 项目描述
    - creator_id: 创建者ID
    - status: 项目状态（active, archived, deleted）
    - priority: 优先级（low, medium, high, urgent）
    - start_date: 开始日期
    - due_date: 截止日期
    - completed_at: 完成时间
    - is_public: 是否公开
    - color: 项目颜色标识
    - settings: 项目设置（JSON格式）
    """

    # 基本信息
    name: Mapped[str] = mapped_column(
        String(200), nullable=False, index=True, comment="项目名称"
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="项目描述"
    )

    # 创建者
    creator_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user.id"), nullable=False, index=True, comment="创建者ID"
    )

    # 状态和优先级
    status: Mapped[str] = mapped_column(
        String(20), default="active", nullable=False, index=True, comment="项目状态"
    )

    priority: Mapped[str] = mapped_column(
        String(20), default="medium", nullable=False, index=True, comment="优先级"
    )

    # 时间相关
    start_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="开始日期"
    )

    due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True, comment="截止日期"
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="完成时间"
    )

    # 可见性和设置
    is_public: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否公开"
    )

    color: Mapped[str] = mapped_column(
        String(7), default="#3b82f6", nullable=False, comment="项目颜色标识"
    )

    settings: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="项目设置（JSON格式）"
    )

    # 关系定义
    creator: Mapped["User"] = relationship(
        "User", back_populates="created_projects", foreign_keys=[creator_id]
    )

    members: Mapped[List["User"]] = relationship(
        "User", secondary=project_members, back_populates="projects", lazy="dynamic"
    )

    tasks: Mapped[List["Task"]] = relationship(
        "Task", back_populates="project", cascade="all, delete-orphan", lazy="dynamic"
    )

    def __repr__(self) -> str:
        return f"<Project(name={self.name}, status={self.status})>"

    @property
    def is_completed(self) -> bool:
        """项目是否已完成"""
        return self.status == "completed"

    @property
    def is_overdue(self) -> bool:
        """项目是否已过期"""
        if not self.due_date or self.is_completed:
            return False
        return datetime.utcnow() > self.due_date

    @property
    def progress_percentage(self) -> float:
        """项目完成百分比"""
        total_tasks = self.tasks.count()
        if total_tasks == 0:
            return 0.0

        completed_tasks = self.tasks.filter_by(status="completed").count()
        return (completed_tasks / total_tasks) * 100

    @property
    def task_counts(self) -> dict:
        """各状态任务数量统计"""
        from sqlalchemy import func
        from .task import Task

        counts = {"total": 0, "todo": 0, "in_progress": 0, "completed": 0, "blocked": 0}

        # 统计各状态任务数量
        result = (
            Task.query.filter_by(project_id=self.id)
            .with_entities(Task.status, func.count(Task.id))
            .group_by(Task.status)
            .all()
        )

        for status, count in result:
            counts[status] = count
            counts["total"] += count

        return counts

    def add_member(self, user: "User", role: str = "member") -> None:
        """添加项目成员"""
        if not self.is_member(user):
            self.members.append(user)

    def remove_member(self, user: "User") -> None:
        """移除项目成员"""
        if self.is_member(user):
            self.members.remove(user)

    def is_member(self, user: "User") -> bool:
        """检查用户是否是项目成员"""
        return self.members.filter_by(id=user.id).first() is not None

    def can_user_access(self, user: "User") -> bool:
        """检查用户是否可以访问项目"""
        # 创建者始终可以访问
        if self.creator_id == user.id:
            return True

        # 公开项目任何人都可以访问
        if self.is_public:
            return True

        # 检查是否是项目成员
        return self.is_member(user)
