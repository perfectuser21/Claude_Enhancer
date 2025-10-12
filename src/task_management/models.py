"""
任务管理系统数据模型
====================

包含完整的数据模型定义，支持：
- 任务管理（Task）
- 项目管理（Project）
- 团队管理（Team）
- 评论系统（Comment）
- 文件附件（Attachment）
- 通知系统（Notification）
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Integer,
    Boolean,
    ForeignKey,
    func,
    Index,
)
from sqlalchemy.orm import relationship, validates
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.ext.hybrid import hybrid_property

from backend.models.base import BaseModel, AuditMixin


# 枚举定义
class TaskStatus(str, Enum):
    """任务状态枚举"""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """任务优先级枚举"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ProjectStatus(str, Enum):
    """项目状态枚举"""

    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MemberRole(str, Enum):
    """成员角色枚举"""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


# 核心模型定义
class Task(BaseModel, AuditMixin):
    """
    任务模型
    ========

    完整的任务管理功能，包括：
    - 基本信息（标题、描述、状态等）
    - 分配管理（责任人、分配时间）
    - 时间管理（截止日期、工时估算）
    - 项目关联
    - 依赖关系
    - 标签和自定义字段
    """

    __tablename__ = "tasks"
    __table_args__ = (
        # 创建复合索引优化查询性能
        Index("idx_task_status_assignee", "status", "assignee_id"),
        Index("idx_task_project_status", "project_id", "status"),
        Index("idx_task_due_date", "due_date"),
        Index("idx_task_created_at", "created_at"),
        {"comment": "任务表 - 存储所有任务信息"},
    )

    # === 基本信息 ===
    title = Column(String(200), nullable=False, comment="任务标题")

    description = Column(Text, nullable=True, comment="任务详细描述，支持Markdown格式")

    status = Column(
        String(20), nullable=False, default=TaskStatus.TODO.value, comment="任务状态"
    )

    priority = Column(
        String(10), nullable=False, default=TaskPriority.MEDIUM.value, comment="任务优先级"
    )

    # === 分配信息 ===
    assignee_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="当前责任人ID",
    )

    assigned_at = Column(DateTime(timezone=True), nullable=True, comment="分配时间")

    assigned_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="分配者ID",
    )

    # === 项目关联 ===
    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        comment="所属项目ID",
    )

    # === 时间管理 ===
    due_date = Column(DateTime(timezone=True), nullable=True, comment="截止日期")

    estimated_hours = Column(Integer, nullable=True, comment="预估工时（小时）")

    actual_hours = Column(Integer, nullable=True, comment="实际工时（小时）")

    started_at = Column(DateTime(timezone=True), nullable=True, comment="实际开始时间")

    completed_at = Column(DateTime(timezone=True), nullable=True, comment="实际完成时间")

    # === 组织信息 ===
    tags = Column(ARRAY(String), nullable=True, default=[], comment="任务标签数组")

    labels = Column(JSONB, nullable=True, comment="标签元数据（颜色、描述等）")

    custom_fields = Column(JSONB, nullable=True, comment="自定义字段数据")

    # === 进度和质量 ===
    progress_percentage = Column(Integer, default=0, comment="完成百分比 (0-100)")

    quality_score = Column(Integer, nullable=True, comment="质量评分 (1-10)")

    # === 关联关系 ===
    # 用户关系
    assignee = relationship(
        "User",
        foreign_keys=[assignee_id],
        back_populates="assigned_tasks",
        lazy="selectin",
    )

    assigner = relationship("User", foreign_keys=[assigned_by], lazy="selectin")

    creator = relationship(
        "User", foreign_keys=[AuditMixin.created_by], lazy="selectin"
    )

    # 项目关系
    project = relationship("Project", back_populates="tasks", lazy="selectin")

    # 评论关系
    comments = relationship(
        "TaskComment",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskComment.created_at.desc()",
    )

    # 附件关系
    attachments = relationship(
        "TaskAttachment", back_populates="task", cascade="all, delete-orphan"
    )

    # 活动日志关系
    activities = relationship(
        "TaskActivity",
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskActivity.created_at.desc()",
    )

    # === 验证器 ===
    @validates("status")
    def validate_status(self, key, status):
        """验证任务状态"""
        if status not in [s.value for s in TaskStatus]:
            raise ValueError(f"Invalid task status: {status}")
        return status

    @validates("priority")
    def validate_priority(self, key, priority):
        """验证任务优先级"""
        if priority not in [p.value for p in TaskPriority]:
            raise ValueError(f"Invalid task priority: {priority}")
        return priority

    @validates("progress_percentage")
    def validate_progress(self, key, progress):
        """验证进度百分比"""
        if progress is not None and (progress < 0 or progress > 100):
            raise ValueError("Progress must be between 0 and 100")
        return progress

    # === 计算属性 ===
    @hybrid_property
    def is_overdue(self) -> bool:
        """是否逾期"""
        if not self.due_date:
            return False
        return (
            self.status not in [TaskStatus.DONE, TaskStatus.CANCELLED]
            and self.due_date < datetime.utcnow()
        )

    @hybrid_property
    def is_completed(self) -> bool:
        """是否已完成"""
        return self.status == TaskStatus.DONE

    @hybrid_property
    def duration_days(self) -> Optional[int]:
        """任务持续时间（天）"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).days
        return None

    # === 业务方法 ===
    def can_transition_to(self, new_status: str) -> bool:
        """检查是否可以转换到指定状态"""
        valid_transitions = {
            TaskStatus.TODO: [TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED],
            TaskStatus.IN_PROGRESS: [
                TaskStatus.TODO,
                TaskStatus.IN_REVIEW,
                TaskStatus.BLOCKED,
                TaskStatus.CANCELLED,
            ],
            TaskStatus.IN_REVIEW: [
                TaskStatus.IN_PROGRESS,
                TaskStatus.DONE,
                TaskStatus.CANCELLED,
            ],
            TaskStatus.BLOCKED: [
                TaskStatus.TODO,
                TaskStatus.IN_PROGRESS,
                TaskStatus.CANCELLED,
            ],
            TaskStatus.DONE: [TaskStatus.IN_PROGRESS],  # 允许重新打开
            TaskStatus.CANCELLED: [TaskStatus.TODO],  # 允许重新激活
        }

        current_status = TaskStatus(self.status)
        target_status = TaskStatus(new_status)

        return target_status in valid_transitions.get(current_status, [])

    def update_progress_from_status(self):
        """根据状态自动更新进度"""
        status_progress_map = {
            TaskStatus.TODO: 0,
            TaskStatus.IN_PROGRESS: 50,
            TaskStatus.IN_REVIEW: 90,
            TaskStatus.DONE: 100,
            TaskStatus.BLOCKED: None,  # 保持当前进度
            TaskStatus.CANCELLED: 0,
        }

        new_progress = status_progress_map.get(TaskStatus(self.status))
        if new_progress is not None:
            self.progress_percentage = new_progress


class TaskDependency(BaseModel):
    """
    任务依赖关系模型
    ================

    管理任务之间的依赖关系：
    - 阻塞依赖（必须完成前置任务）
    - 链接依赖（相关任务关联）
    """

    __tablename__ = "task_dependencies"
    __table_args__ = (
        Index("idx_task_dependency_task", "task_id"),
        Index("idx_task_dependency_dep", "dependency_id"),
        {"comment": "任务依赖关系表"},
    )

    task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        comment="任务ID",
    )

    dependency_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        comment="依赖的任务ID",
    )

    dependency_type = Column(
        String(20), default="blocks", comment="依赖类型：blocks（阻塞）, links（关联）"
    )

    notes = Column(Text, nullable=True, comment="依赖关系说明")

    # 关联关系
    task = relationship("Task", foreign_keys=[task_id])
    dependency_task = relationship("Task", foreign_keys=[dependency_id])


class Project(BaseModel, AuditMixin):
    """
    项目模型
    ========

    项目管理功能，包括：
    - 基本信息管理
    - 成员管理
    - 任务组织
    - 进度跟踪
    """

    __tablename__ = "projects"
    __table_args__ = (
        Index("idx_project_status", "status"),
        Index("idx_project_team", "team_id"),
        {"comment": "项目表"},
    )

    # === 基本信息 ===
    name = Column(String(100), nullable=False, comment="项目名称")

    description = Column(Text, nullable=True, comment="项目描述")

    status = Column(
        String(20), nullable=False, default=ProjectStatus.PLANNING.value, comment="项目状态"
    )

    color = Column(String(7), default="#1976d2", comment="项目颜色（十六进制）")

    # === 时间管理 ===
    start_date = Column(DateTime(timezone=True), nullable=True, comment="计划开始日期")

    end_date = Column(DateTime(timezone=True), nullable=True, comment="计划结束日期")

    actual_start_date = Column(DateTime(timezone=True), nullable=True, comment="实际开始日期")

    actual_end_date = Column(DateTime(timezone=True), nullable=True, comment="实际结束日期")

    # === 团队关联 ===
    team_id = Column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True,
        comment="所属团队ID",
    )

    # === 项目设置 ===
    settings = Column(JSONB, nullable=True, default={}, comment="项目配置（工作流、字段定义等）")

    is_public = Column(Boolean, default=False, comment="是否公开项目")

    is_archived = Column(Boolean, default=False, comment="是否已归档")

    # === 关联关系 ===
    team = relationship("Team", back_populates="projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    members = relationship(
        "ProjectMember", back_populates="project", cascade="all, delete-orphan"
    )

    # === 验证器 ===
    @validates("status")
    def validate_status(self, key, status):
        """验证项目状态"""
        if status not in [s.value for s in ProjectStatus]:
            raise ValueError(f"Invalid project status: {status}")
        return status

    # === 计算属性 ===
    @hybrid_property
    def task_count(self) -> int:
        """任务总数"""
        return len([t for t in self.tasks if not t.is_deleted])

    @hybrid_property
    def completed_task_count(self) -> int:
        """已完成任务数"""
        return len(
            [t for t in self.tasks if t.status == TaskStatus.DONE and not t.is_deleted]
        )

    @hybrid_property
    def completion_percentage(self) -> float:
        """完成百分比"""
        total = self.task_count
        if total == 0:
            return 0.0
        return (self.completed_task_count / total) * 100


class ProjectMember(BaseModel):
    """
    项目成员模型
    ============

    管理项目成员及其角色权限
    """

    __tablename__ = "project_members"
    __table_args__ = (
        Index("idx_project_member_project", "project_id"),
        Index("idx_project_member_user", "user_id"),
        {"comment": "项目成员表"},
    )

    project_id = Column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        comment="项目ID",
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="用户ID",
    )

    role = Column(String(20), default=MemberRole.MEMBER.value, comment="成员角色")

    joined_at = Column(
        DateTime(timezone=True), server_default=func.now(), comment="加入时间"
    )

    permissions = Column(JSONB, default={}, comment="特殊权限设置")

    # 关联关系
    project = relationship("Project", back_populates="members")
    user = relationship("User")

    @validates("role")
    def validate_role(self, key, role):
        """验证成员角色"""
        if role not in [r.value for r in MemberRole]:
            raise ValueError(f"Invalid member role: {role}")
        return role


class Team(BaseModel, AuditMixin):
    """
    团队模型
    ========

    团队管理功能
    """

    __tablename__ = "teams"
    __table_args__ = {"comment": "团队表"}

    name = Column(String(100), nullable=False, comment="团队名称")
    description = Column(Text, nullable=True, comment="团队描述")
    avatar_url = Column(String(500), nullable=True, comment="团队头像URL")

    # 关联关系
    projects = relationship("Project", back_populates="team")
    members = relationship(
        "TeamMember", back_populates="team", cascade="all, delete-orphan"
    )


class TeamMember(BaseModel):
    """团队成员模型"""

    __tablename__ = "team_members"

    team_id = Column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role = Column(String(20), default=MemberRole.MEMBER.value)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    team = relationship("Team", back_populates="members")
    user = relationship("User")


class TaskComment(BaseModel, AuditMixin):
    """
    任务评论模型
    ============

    支持任务讨论和协作
    """

    __tablename__ = "task_comments"
    __table_args__ = (Index("idx_task_comment_task", "task_id"), {"comment": "任务评论表"})

    task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        comment="任务ID",
    )

    content = Column(Text, nullable=False, comment="评论内容，支持Markdown")

    is_internal = Column(Boolean, default=False, comment="是否内部评论（仅团队可见）")

    reply_to = Column(
        UUID(as_uuid=True),
        ForeignKey("task_comments.id", ondelete="CASCADE"),
        nullable=True,
        comment="回复的评论ID",
    )

    # 关联关系
    task = relationship("Task", back_populates="comments")
    author = relationship("User", foreign_keys=[AuditMixin.created_by])
    replies = relationship(
        "TaskComment", backref="parent_comment", remote_side="TaskComment.id"
    )


class TaskAttachment(BaseModel, AuditMixin):
    """
    任务附件模型
    ============

    文件附件管理
    """

    __tablename__ = "task_attachments"
    __table_args__ = (
        Index("idx_task_attachment_task", "task_id"),
        {"comment": "任务附件表"},
    )

    task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        comment="任务ID",
    )

    filename = Column(String(255), nullable=False, comment="存储文件名")

    original_name = Column(String(255), nullable=False, comment="原始文件名")

    file_size = Column(Integer, nullable=False, comment="文件大小（字节）")

    file_path = Column(String(500), nullable=False, comment="文件存储路径")

    mime_type = Column(String(100), nullable=True, comment="MIME类型")

    thumbnail_path = Column(String(500), nullable=True, comment="缩略图路径（图片文件）")

    # 关联关系
    task = relationship("Task", back_populates="attachments")
    uploader = relationship("User", foreign_keys=[AuditMixin.created_by])


class TaskActivity(BaseModel):
    """
    任务活动日志模型
    ================

    记录任务的所有变更历史
    """

    __tablename__ = "task_activities"
    __table_args__ = (
        Index("idx_task_activity_task", "task_id"),
        Index("idx_task_activity_created", "created_at"),
        {"comment": "任务活动日志表"},
    )

    task_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tasks.id", ondelete="CASCADE"),
        nullable=False,
        comment="任务ID",
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="操作用户ID",
    )

    action = Column(
        String(50), nullable=False, comment="操作类型（created, updated, assigned, etc.）"
    )

    field_name = Column(String(50), nullable=True, comment="变更的字段名")

    old_value = Column(Text, nullable=True, comment="变更前的值")

    new_value = Column(Text, nullable=True, comment="变更后的值")

    description = Column(Text, nullable=True, comment="活动描述")

    extra_metadata = Column(JSONB, nullable=True, comment="额外的元数据")

    # 关联关系
    task = relationship("Task", back_populates="activities")
    user = relationship("User")


class Notification(BaseModel):
    """
    通知模型
    ========

    系统通知管理
    """

    __tablename__ = "notifications"
    __table_args__ = (
        Index("idx_notification_user", "user_id"),
        Index("idx_notification_read", "is_read"),
        {"comment": "通知表"},
    )

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="接收用户ID",
    )

    title = Column(String(200), nullable=False, comment="通知标题")

    content = Column(Text, nullable=False, comment="通知内容")

    type = Column(
        String(50), nullable=False, comment="通知类型（task_assigned, task_completed, etc.）"
    )

    is_read = Column(Boolean, default=False, comment="是否已读")

    read_at = Column(DateTime(timezone=True), nullable=True, comment="阅读时间")

    related_entity_type = Column(
        String(50), nullable=True, comment="关联实体类型（task, project, etc.）"
    )

    related_entity_id = Column(UUID(as_uuid=True), nullable=True, comment="关联实体ID")

    action_url = Column(String(500), nullable=True, comment="行动URL")

    extra_metadata = Column(JSONB, nullable=True, comment="额外数据")

    # 关联关系
    user = relationship("User")

    def mark_as_read(self):
        """标记为已读"""
        self.is_read = True
        self.read_at = datetime.utcnow()
