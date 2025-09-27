"""
任务数据模型
管理任务信息、状态和关系
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Integer, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


# 任务标签关联表（多对多关系）
task_labels = Table(
    "task_labels",
    BaseModel.metadata,
    mapped_column("task_id", String(36), ForeignKey("task.id"), primary_key=True),
    mapped_column("label_id", String(36), ForeignKey("label.id"), primary_key=True),
)


class Task(BaseModel):
    """
    任务模型

    字段说明：
    - title: 任务标题
    - description: 任务描述
    - status: 任务状态（todo, in_progress, completed, blocked）
    - priority: 优先级（low, medium, high, urgent）
    - project_id: 所属项目ID
    - creator_id: 创建者ID
    - assignee_id: 分配给的用户ID
    - parent_id: 父任务ID（子任务）
    - position: 在项目中的排序位置
    - estimated_hours: 预估工时
    - actual_hours: 实际工时
    - due_date: 截止日期
    - completed_at: 完成时间
    - is_archived: 是否归档
    - metadata: 额外元数据（JSON格式）
    """

    # 基本信息
    title: Mapped[str] = mapped_column(
        String(200), nullable=False, index=True, comment="任务标题"
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="任务描述"
    )

    # 状态和优先级
    status: Mapped[str] = mapped_column(
        String(20), default="todo", nullable=False, index=True, comment="任务状态"
    )

    priority: Mapped[str] = mapped_column(
        String(20), default="medium", nullable=False, index=True, comment="优先级"
    )

    # 关联关系
    project_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("project.id"),
        nullable=True,
        index=True,
        comment="所属项目ID",
    )

    creator_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("user.id"), nullable=False, index=True, comment="创建者ID"
    )

    assignee_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("user.id"), nullable=True, index=True, comment="分配给的用户ID"
    )

    parent_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("task.id"), nullable=True, index=True, comment="父任务ID"
    )

    # 排序和工时
    position: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="排序位置"
    )

    estimated_hours: Mapped[Optional[float]] = mapped_column(
        nullable=True, comment="预估工时"
    )

    actual_hours: Mapped[Optional[float]] = mapped_column(nullable=True, comment="实际工时")

    # 时间相关
    due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True, comment="截止日期"
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="完成时间"
    )

    # 状态标记
    is_archived: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否归档"
    )

    # 额外数据
    metadata: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="额外元数据（JSON格式）"
    )

    # 关系定义
    project: Mapped[Optional["Project"]] = relationship(
        "Project", back_populates="tasks"
    )

    creator: Mapped["User"] = relationship(
        "User", back_populates="created_tasks", foreign_keys=[creator_id]
    )

    assignee: Mapped[Optional["User"]] = relationship(
        "User", back_populates="assigned_tasks", foreign_keys=[assignee_id]
    )

    # 子任务关系
    parent: Mapped[Optional["Task"]] = relationship(
        "Task", remote_side="Task.id", back_populates="subtasks"
    )

    subtasks: Mapped[List["Task"]] = relationship(
        "Task", back_populates="parent", cascade="all, delete-orphan"
    )

    # 标签关系
    labels: Mapped[List["Label"]] = relationship(
        "Label", secondary=task_labels, back_populates="tasks"
    )

    def __repr__(self) -> str:
        return f"<Task(title={self.title}, status={self.status})>"

    @property
    def is_completed(self) -> bool:
        """任务是否已完成"""
        return self.status == "completed"

    @property
    def is_overdue(self) -> bool:
        """任务是否已过期"""
        if not self.due_date or self.is_completed:
            return False
        return datetime.utcnow() > self.due_date

    @property
    def has_subtasks(self) -> bool:
        """是否有子任务"""
        return len(self.subtasks) > 0

    @property
    def subtask_progress(self) -> float:
        """子任务完成百分比"""
        if not self.has_subtasks:
            return 0.0

        total_subtasks = len(self.subtasks)
        completed_subtasks = len([t for t in self.subtasks if t.is_completed])
        return (completed_subtasks / total_subtasks) * 100

    @property
    def hours_variance(self) -> Optional[float]:
        """工时差异（实际 - 预估）"""
        if self.estimated_hours is None or self.actual_hours is None:
            return None
        return self.actual_hours - self.estimated_hours

    def can_user_access(self, user: "User") -> bool:
        """检查用户是否可以访问任务"""
        # 创建者可以访问
        if self.creator_id == user.id:
            return True

        # 分配的用户可以访问
        if self.assignee_id == user.id:
            return True

        # 项目成员可以访问
        if self.project:
            return self.project.can_user_access(user)

        return False

    def can_user_edit(self, user: "User") -> bool:
        """检查用户是否可以编辑任务"""
        # 创建者可以编辑
        if self.creator_id == user.id:
            return True

        # 分配的用户可以编辑
        if self.assignee_id == user.id:
            return True

        # 项目创建者可以编辑
        if self.project and self.project.creator_id == user.id:
            return True

        return False

    def update_status(self, status: str, user: "User") -> None:
        """更新任务状态"""
        if not self.can_user_edit(user):
            raise PermissionError("没有权限修改此任务")

        old_status = self.status
        self.status = status

        # 如果状态变为完成，设置完成时间
        if status == "completed" and old_status != "completed":
            self.completed_at = datetime.utcnow()
        elif status != "completed" and old_status == "completed":
            self.completed_at = None

    def add_label(self, label: "Label") -> None:
        """添加标签"""
        if label not in self.labels:
            self.labels.append(label)

    def remove_label(self, label: "Label") -> None:
        """移除标签"""
        if label in self.labels:
            self.labels.remove(label)
