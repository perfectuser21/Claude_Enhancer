"""
SQLAlchemy models for the Todo system.
Production-ready models with comprehensive features, security, and performance optimizations.
"""

import enum
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import (
    ARRAY, Boolean, CheckConstraint, Column, DateTime, Enum, ForeignKey,
    Index, Integer, JSON, Numeric, String, Text, UniqueConstraint, func
)
from sqlalchemy.dialects.postgresql import INET, JSONB, UUID as PG_UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


# =============================================================================
# ENUMS
# =============================================================================

class PriorityLevel(enum.Enum):
    """Priority levels for todo items."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class StatusType(enum.Enum):
    """Status types for todo items."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"


class PermissionLevel(enum.Enum):
    """Permission levels for shared todos."""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"


class ActionType(enum.Enum):
    """Action types for activity logging."""
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
    COMPLETED = "completed"
    REOPENED = "reopened"
    ASSIGNED = "assigned"
    COMMENTED = "commented"


# =============================================================================
# USER MODEL
# =============================================================================

class User(Base):
    """User model with authentication and profile information."""

    __tablename__ = "users"
    __table_args__ = (
        {"schema": "todo"},
        CheckConstraint(
            "email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'",
            name="email_format"
        ),
        CheckConstraint(
            "username ~* '^[A-Za-z0-9_]{3,}$'",
            name="username_format"
        ),
        Index("idx_users_email", "email"),
        Index("idx_users_username", "username"),
        Index("idx_users_active", "is_active", postgresql_where="is_active = true"),
    )

    # Authentication fields
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Profile fields
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))

    # Status fields
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    categories: Mapped[List["Category"]] = relationship(
        "Category", back_populates="user", cascade="all, delete-orphan"
    )
    todos: Mapped[List["TodoItem"]] = relationship(
        "TodoItem", back_populates="user", cascade="all, delete-orphan"
    )
    comments: Mapped[List["Comment"]] = relationship(
        "Comment", back_populates="user", cascade="all, delete-orphan"
    )
    owned_shares: Mapped[List["SharedTodo"]] = relationship(
        "SharedTodo",
        foreign_keys="SharedTodo.owner_id",
        back_populates="owner",
        cascade="all, delete-orphan"
    )
    received_shares: Mapped[List["SharedTodo"]] = relationship(
        "SharedTodo",
        foreign_keys="SharedTodo.shared_with_id",
        back_populates="shared_with",
        cascade="all, delete-orphan"
    )
    activity_logs: Mapped[List["ActivityLog"]] = relationship(
        "ActivityLog", back_populates="user", cascade="all, delete-orphan"
    )

    @hybrid_property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username

    def __repr__(self) -> str:
        return f"<User(username={self.username}, email={self.email})>"


# =============================================================================
# CATEGORY MODEL
# =============================================================================

class Category(Base):
    """Category model for organizing todos."""

    __tablename__ = "categories"
    __table_args__ = (
        {"schema": "todo"},
        UniqueConstraint("user_id", "name", name="unique_category_per_user"),
        CheckConstraint(
            "color ~* '^#[0-9A-Fa-f]{6}$'",
            name="color_hex_format"
        ),
        Index("idx_categories_user_id", "user_id"),
        Index("idx_categories_active", "user_id", "is_active", postgresql_where="is_active = true"),
        Index("idx_categories_sort_order", "user_id", "sort_order"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("todo.users.id", ondelete="CASCADE"),
        nullable=False
    )

    # Category details
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    color: Mapped[str] = mapped_column(String(7), default="#007bff")  # Hex color
    icon: Mapped[str] = mapped_column(String(50), default="folder")

    # Organization
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="categories")
    todos: Mapped[List["TodoItem"]] = relationship(
        "TodoItem", back_populates="category", cascade="all, delete-orphan"
    )

    @hybrid_property
    def todo_count(self) -> int:
        """Get count of todos in this category."""
        return len([todo for todo in self.todos if not todo.is_archived])

    @hybrid_property
    def completed_count(self) -> int:
        """Get count of completed todos in this category."""
        return len([
            todo for todo in self.todos
            if todo.status == StatusType.COMPLETED and not todo.is_archived
        ])

    def __repr__(self) -> str:
        return f"<Category(name={self.name}, user_id={self.user_id})>"


# =============================================================================
# TODO ITEM MODEL
# =============================================================================

class TodoItem(Base):
    """Main todo item model with comprehensive features."""

    __tablename__ = "items"
    __table_args__ = (
        {"schema": "todo"},
        CheckConstraint("LENGTH(TRIM(title)) > 0", name="title_not_empty"),
        CheckConstraint(
            "(status = 'completed' AND completed_at IS NOT NULL) OR "
            "(status != 'completed' AND completed_at IS NULL)",
            name="completed_at_logic"
        ),
        CheckConstraint(
            "(status = 'completed' AND progress_percentage = 100) OR "
            "(status != 'completed')",
            name="progress_status_logic"
        ),
        CheckConstraint(
            "progress_percentage >= 0 AND progress_percentage <= 100",
            name="progress_percentage_range"
        ),
        CheckConstraint("estimated_hours >= 0", name="estimated_hours_positive"),
        CheckConstraint("actual_hours >= 0", name="actual_hours_positive"),
        # Performance indexes
        Index("idx_todos_user_id", "user_id"),
        Index("idx_todos_status", "user_id", "status"),
        Index("idx_todos_priority", "user_id", "priority"),
        Index("idx_todos_due_date", "user_id", "due_date", postgresql_where="due_date IS NOT NULL"),
        Index("idx_todos_category", "category_id", postgresql_where="category_id IS NOT NULL"),
        Index("idx_todos_parent", "parent_id", postgresql_where="parent_id IS NOT NULL"),
        Index("idx_todos_archived", "user_id", "is_archived"),
        Index("idx_todos_pinned", "user_id", "is_pinned", postgresql_where="is_pinned = true"),
        Index("idx_todos_created_at", "user_id", "created_at"),
        Index("idx_todos_updated_at", "user_id", "updated_at"),
        # Full-text search index
        Index(
            "idx_todos_search",
            func.to_tsvector("english", Column("title") + " " + func.coalesce(Column("description"), "")),
            postgresql_using="gin"
        ),
        # Tags search index
        Index("idx_todos_tags", "tags", postgresql_using="gin", postgresql_where="tags IS NOT NULL"),
    )

    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("todo.users.id", ondelete="CASCADE"),
        nullable=False
    )
    category_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("todo.categories.id", ondelete="SET NULL")
    )
    parent_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("todo.items.id", ondelete="CASCADE")
    )

    # Core fields
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[StatusType] = mapped_column(Enum(StatusType), default=StatusType.PENDING)
    priority: Mapped[PriorityLevel] = mapped_column(Enum(PriorityLevel), default=PriorityLevel.MEDIUM)

    # Dates and deadlines
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Organization
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)

    # Progress tracking
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0)
    estimated_hours: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    actual_hours: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))

    # Metadata
    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String))
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="todos")
    category: Mapped[Optional["Category"]] = relationship("Category", back_populates="todos")
    parent: Mapped[Optional["TodoItem"]] = relationship(
        "TodoItem", remote_side="TodoItem.id", back_populates="subtasks"
    )
    subtasks: Mapped[List["TodoItem"]] = relationship(
        "TodoItem", back_populates="parent", cascade="all, delete-orphan"
    )
    attachments: Mapped[List["Attachment"]] = relationship(
        "Attachment", back_populates="todo", cascade="all, delete-orphan"
    )
    comments: Mapped[List["Comment"]] = relationship(
        "Comment", back_populates="todo", cascade="all, delete-orphan"
    )
    shares: Mapped[List["SharedTodo"]] = relationship(
        "SharedTodo", back_populates="todo", cascade="all, delete-orphan"
    )
    activity_logs: Mapped[List["ActivityLog"]] = relationship(
        "ActivityLog", back_populates="todo", cascade="all, delete-orphan"
    )

    @hybrid_property
    def is_overdue(self) -> bool:
        """Check if todo is overdue."""
        if not self.due_date or self.status == StatusType.COMPLETED:
            return False
        return datetime.utcnow() > self.due_date

    @hybrid_property
    def days_until_due(self) -> Optional[int]:
        """Get days until due date."""
        if not self.due_date:
            return None
        delta = self.due_date - datetime.utcnow()
        return delta.days

    @hybrid_property
    def completion_time(self) -> Optional[float]:
        """Get completion time in hours."""
        if not self.started_at or not self.completed_at:
            return None
        delta = self.completed_at - self.started_at
        return delta.total_seconds() / 3600

    def mark_completed(self) -> None:
        """Mark todo as completed."""
        self.status = StatusType.COMPLETED
        self.completed_at = datetime.utcnow()
        self.progress_percentage = 100

    def mark_in_progress(self) -> None:
        """Mark todo as in progress."""
        if not self.started_at:
            self.started_at = datetime.utcnow()
        self.status = StatusType.IN_PROGRESS

    def __repr__(self) -> str:
        return f"<TodoItem(title={self.title}, status={self.status.value})>"


# =============================================================================
# ATTACHMENT MODEL
# =============================================================================

class Attachment(Base):
    """File attachment model for todos."""

    __tablename__ = "attachments"
    __table_args__ = (
        {"schema": "todo"},
        CheckConstraint("LENGTH(TRIM(filename)) > 0", name="filename_not_empty"),
        CheckConstraint("file_size > 0", name="file_size_positive"),
        CheckConstraint("file_size <= 10485760", name="file_size_limit"),  # 10MB
        Index("idx_attachments_todo_id", "todo_id"),
        Index("idx_attachments_user_id", "user_id"),
        Index("idx_attachments_hash", "file_hash"),
    )

    todo_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("todo.items.id", ondelete="CASCADE"),
        nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("todo.users.id", ondelete="CASCADE"),
        nullable=False
    )

    # File information
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Security
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)

    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    todo: Mapped["TodoItem"] = relationship("TodoItem", back_populates="attachments")
    user: Mapped["User"] = relationship("User")

    @hybrid_property
    def file_size_mb(self) -> float:
        """Get file size in megabytes."""
        return self.file_size / (1024 * 1024)

    def __repr__(self) -> str:
        return f"<Attachment(filename={self.filename}, todo_id={self.todo_id})>"


# =============================================================================
# COMMENT MODEL
# =============================================================================

class Comment(Base):
    """Comment model for todos with nested comments support."""

    __tablename__ = "comments"
    __table_args__ = (
        {"schema": "todo"},
        CheckConstraint("LENGTH(TRIM(content)) > 0", name="content_not_empty"),
        Index("idx_comments_todo_id", "todo_id"),
        Index("idx_comments_user_id", "user_id"),
        Index("idx_comments_parent", "parent_id", postgresql_where="parent_id IS NOT NULL"),
    )

    todo_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("todo.items.id", ondelete="CASCADE"),
        nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("todo.users.id", ondelete="CASCADE"),
        nullable=False
    )
    parent_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("todo.comments.id", ondelete="CASCADE")
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    todo: Mapped["TodoItem"] = relationship("TodoItem", back_populates="comments")
    user: Mapped["User"] = relationship("User", back_populates="comments")
    parent: Mapped[Optional["Comment"]] = relationship(
        "Comment", remote_side="Comment.id", back_populates="replies"
    )
    replies: Mapped[List["Comment"]] = relationship(
        "Comment", back_populates="parent", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Comment(id={self.id}, todo_id={self.todo_id}, user_id={self.user_id})>"


# =============================================================================
# SHARED TODO MODEL
# =============================================================================

class SharedTodo(Base):
    """Model for sharing todos between users."""

    __tablename__ = "shared_todos"
    __table_args__ = (
        {"schema": "todo"},
        UniqueConstraint("todo_id", "shared_with_id", name="unique_sharing"),
        CheckConstraint("owner_id != shared_with_id", name="no_self_sharing"),
        Index("idx_shared_todos_owner", "owner_id"),
        Index("idx_shared_todos_shared_with", "shared_with_id"),
        Index("idx_shared_todos_todo", "todo_id"),
    )

    todo_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("todo.items.id", ondelete="CASCADE"),
        nullable=False
    )
    owner_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("todo.users.id", ondelete="CASCADE"),
        nullable=False
    )
    shared_with_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("todo.users.id", ondelete="CASCADE"),
        nullable=False
    )

    permission: Mapped[PermissionLevel] = mapped_column(
        Enum(PermissionLevel), default=PermissionLevel.READ
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Relationships
    todo: Mapped["TodoItem"] = relationship("TodoItem", back_populates="shares")
    owner: Mapped["User"] = relationship(
        "User", foreign_keys=[owner_id], back_populates="owned_shares"
    )
    shared_with: Mapped["User"] = relationship(
        "User", foreign_keys=[shared_with_id], back_populates="received_shares"
    )

    @hybrid_property
    def is_expired(self) -> bool:
        """Check if sharing has expired."""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at

    def __repr__(self) -> str:
        return f"<SharedTodo(todo_id={self.todo_id}, shared_with_id={self.shared_with_id})>"


# =============================================================================
# ACTIVITY LOG MODEL
# =============================================================================

class ActivityLog(Base):
    """Activity log model for audit trail."""

    __tablename__ = "activity_log"
    __table_args__ = (
        {"schema": "todo"},
        Index("idx_activity_log_todo_id", "todo_id"),
        Index("idx_activity_log_user_id", "user_id"),
        Index("idx_activity_log_created_at", "created_at"),
        Index("idx_activity_log_action", "action"),
    )

    todo_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("todo.items.id", ondelete="CASCADE")
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("todo.users.id", ondelete="CASCADE"),
        nullable=False
    )

    action: Mapped[ActionType] = mapped_column(Enum(ActionType), nullable=False)

    # Change tracking
    old_values: Mapped[Optional[dict]] = mapped_column(JSONB)
    new_values: Mapped[Optional[dict]] = mapped_column(JSONB)
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Security information
    ip_address: Mapped[Optional[str]] = mapped_column(INET)
    user_agent: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    todo: Mapped[Optional["TodoItem"]] = relationship("TodoItem", back_populates="activity_logs")
    user: Mapped["User"] = relationship("User", back_populates="activity_logs")

    def __repr__(self) -> str:
        return f"<ActivityLog(action={self.action.value}, user_id={self.user_id})>"