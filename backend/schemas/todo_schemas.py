"""
Pydantic schemas for the Todo system.
Type-safe API schemas with comprehensive validation and serialization.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, validator
from pydantic.types import PositiveInt, constr

from backend.models.todo_models import ActionType, PermissionLevel, PriorityLevel, StatusType


# =============================================================================
# BASE SCHEMAS
# =============================================================================

class BaseSchema(BaseModel):
    """Base schema with common configuration."""

    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        arbitrary_types_allowed=True,
        str_strip_whitespace=True,
        extra="forbid"
    )


# =============================================================================
# USER SCHEMAS
# =============================================================================

class UserBase(BaseSchema):
    """Base user schema with common fields."""
    email: EmailStr
    username: constr(min_length=3, max_length=100, pattern=r"^[A-Za-z0-9_]+$")
    first_name: Optional[constr(max_length=100)] = None
    last_name: Optional[constr(max_length=100)] = None
    is_active: bool = True


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: constr(min_length=8, max_length=128)
    confirm_password: constr(min_length=8, max_length=128)

    @validator("confirm_password")
    def passwords_match(cls, v, values):
        if "password" in values and v != values["password"]:
            raise ValueError("Passwords do not match")
        return v

    @validator("password")
    def password_complexity(cls, v):
        """Validate password complexity."""
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain at least one special character")
        return v


class UserUpdate(BaseSchema):
    """Schema for updating user information."""
    email: Optional[EmailStr] = None
    username: Optional[constr(min_length=3, max_length=100, pattern=r"^[A-Za-z0-9_]+$")] = None
    first_name: Optional[constr(max_length=100)] = None
    last_name: Optional[constr(max_length=100)] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user response data."""
    id: UUID
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime]

    # Computed fields
    full_name: Optional[str] = None

    @validator("full_name", always=True)
    def compute_full_name(cls, v, values):
        first = values.get("first_name", "")
        last = values.get("last_name", "")
        if first and last:
            return f"{first} {last}"
        elif first:
            return first
        elif last:
            return last
        else:
            return values.get("username", "")


# =============================================================================
# CATEGORY SCHEMAS
# =============================================================================

class CategoryBase(BaseSchema):
    """Base category schema."""
    name: constr(min_length=1, max_length=100)
    description: Optional[str] = None
    color: constr(regex=r"^#[0-9A-Fa-f]{6}$") = "#007bff"
    icon: constr(max_length=50) = "folder"
    is_active: bool = True
    sort_order: int = 0


class CategoryCreate(CategoryBase):
    """Schema for creating a new category."""
    pass


class CategoryUpdate(BaseSchema):
    """Schema for updating a category."""
    name: Optional[constr(min_length=1, max_length=100)] = None
    description: Optional[str] = None
    color: Optional[constr(regex=r"^#[0-9A-Fa-f]{6}$")] = None
    icon: Optional[constr(max_length=50)] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class CategoryResponse(CategoryBase):
    """Schema for category response data."""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    # Computed fields
    todo_count: int = 0
    completed_count: int = 0


# =============================================================================
# TODO ITEM SCHEMAS
# =============================================================================

class TodoItemBase(BaseSchema):
    """Base todo item schema."""
    title: constr(min_length=1, max_length=255)
    description: Optional[str] = None
    status: StatusType = StatusType.PENDING
    priority: PriorityLevel = PriorityLevel.MEDIUM
    due_date: Optional[datetime] = None
    sort_order: int = 0
    is_pinned: bool = False
    progress_percentage: int = Field(default=0, ge=0, le=100)
    estimated_hours: Optional[float] = Field(default=None, ge=0)
    actual_hours: Optional[float] = Field(default=None, ge=0)
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class TodoItemCreate(TodoItemBase):
    """Schema for creating a new todo item."""
    category_id: Optional[UUID] = None
    parent_id: Optional[UUID] = None

    @validator("tags")
    def validate_tags(cls, v):
        if v is not None:
            # Remove duplicates and empty strings
            v = list(set(tag.strip() for tag in v if tag.strip()))
            # Limit number of tags
            if len(v) > 20:
                raise ValueError("Maximum 20 tags allowed")
            # Validate tag format
            for tag in v:
                if len(tag) > 50:
                    raise ValueError("Tag length cannot exceed 50 characters")
                if not tag.replace("-", "").replace("_", "").isalnum():
                    raise ValueError("Tags can only contain letters, numbers, hyphens, and underscores")
        return v


class TodoItemUpdate(BaseSchema):
    """Schema for updating a todo item."""
    title: Optional[constr(min_length=1, max_length=255)] = None
    description: Optional[str] = None
    status: Optional[StatusType] = None
    priority: Optional[PriorityLevel] = None
    due_date: Optional[datetime] = None
    category_id: Optional[UUID] = None
    sort_order: Optional[int] = None
    is_pinned: Optional[bool] = None
    is_archived: Optional[bool] = None
    progress_percentage: Optional[int] = Field(default=None, ge=0, le=100)
    estimated_hours: Optional[float] = Field(default=None, ge=0)
    actual_hours: Optional[float] = Field(default=None, ge=0)
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    @validator("tags")
    def validate_tags(cls, v):
        if v is not None:
            v = list(set(tag.strip() for tag in v if tag.strip()))
            if len(v) > 20:
                raise ValueError("Maximum 20 tags allowed")
            for tag in v:
                if len(tag) > 50:
                    raise ValueError("Tag length cannot exceed 50 characters")
                if not tag.replace("-", "").replace("_", "").isalnum():
                    raise ValueError("Tags can only contain letters, numbers, hyphens, and underscores")
        return v


class TodoItemResponse(TodoItemBase):
    """Schema for todo item response data."""
    id: UUID
    user_id: UUID
    category_id: Optional[UUID]
    parent_id: Optional[UUID]
    completed_at: Optional[datetime]
    started_at: Optional[datetime]
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    # Computed fields
    is_overdue: bool = False
    days_until_due: Optional[int] = None
    completion_time: Optional[float] = None

    # Related data
    category: Optional[CategoryResponse] = None
    subtasks: List["TodoItemResponse"] = []
    attachment_count: int = 0
    comment_count: int = 0


# =============================================================================
# ATTACHMENT SCHEMAS
# =============================================================================

class AttachmentBase(BaseSchema):
    """Base attachment schema."""
    filename: constr(min_length=1, max_length=255)
    original_filename: constr(min_length=1, max_length=255)
    file_size: PositiveInt
    mime_type: constr(max_length=100)
    description: Optional[str] = None
    is_public: bool = False


class AttachmentCreate(AttachmentBase):
    """Schema for creating a new attachment."""
    file_path: constr(min_length=1, max_length=500)
    file_hash: constr(min_length=64, max_length=64)  # SHA-256 hash

    @validator("file_size")
    def validate_file_size(cls, v):
        if v > 10 * 1024 * 1024:  # 10MB
            raise ValueError("File size cannot exceed 10MB")
        return v


class AttachmentResponse(AttachmentBase):
    """Schema for attachment response data."""
    id: UUID
    todo_id: UUID
    user_id: UUID
    uploaded_at: datetime

    # Computed fields
    file_size_mb: float = 0.0


# =============================================================================
# COMMENT SCHEMAS
# =============================================================================

class CommentBase(BaseSchema):
    """Base comment schema."""
    content: constr(min_length=1, max_length=5000)


class CommentCreate(CommentBase):
    """Schema for creating a new comment."""
    parent_id: Optional[UUID] = None


class CommentUpdate(BaseSchema):
    """Schema for updating a comment."""
    content: constr(min_length=1, max_length=5000)


class CommentResponse(CommentBase):
    """Schema for comment response data."""
    id: UUID
    todo_id: UUID
    user_id: UUID
    parent_id: Optional[UUID]
    is_edited: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime

    # Related data
    user: UserResponse
    replies: List["CommentResponse"] = []


# =============================================================================
# SHARED TODO SCHEMAS
# =============================================================================

class SharedTodoBase(BaseSchema):
    """Base shared todo schema."""
    permission: PermissionLevel = PermissionLevel.READ
    expires_at: Optional[datetime] = None


class SharedTodoCreate(SharedTodoBase):
    """Schema for creating a new shared todo."""
    shared_with_email: EmailStr

    @validator("expires_at")
    def validate_expiry(cls, v):
        if v and v <= datetime.utcnow():
            raise ValueError("Expiry date must be in the future")
        return v


class SharedTodoResponse(SharedTodoBase):
    """Schema for shared todo response data."""
    id: UUID
    todo_id: UUID
    owner_id: UUID
    shared_with_id: UUID
    created_at: datetime

    # Computed fields
    is_expired: bool = False

    # Related data
    todo: TodoItemResponse
    owner: UserResponse
    shared_with: UserResponse


# =============================================================================
# ACTIVITY LOG SCHEMAS
# =============================================================================

class ActivityLogResponse(BaseSchema):
    """Schema for activity log response data."""
    id: UUID
    todo_id: Optional[UUID]
    user_id: UUID
    action: ActionType
    old_values: Optional[Dict[str, Any]]
    new_values: Optional[Dict[str, Any]]
    description: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime

    # Related data
    user: UserResponse
    todo: Optional[TodoItemResponse] = None


# =============================================================================
# UTILITY SCHEMAS
# =============================================================================

class TodoStats(BaseSchema):
    """Schema for todo statistics."""
    total_todos: int
    completed_todos: int
    pending_todos: int
    overdue_todos: int
    completion_rate: float

    # By category
    categories: List[Dict[str, Any]] = []

    # By priority
    priority_breakdown: Dict[str, int] = {}

    # Time-based stats
    todos_this_week: int = 0
    todos_this_month: int = 0
    completed_this_week: int = 0
    completed_this_month: int = 0


class SearchResult(BaseSchema):
    """Schema for search results."""
    query: str
    total_results: int
    page: int
    page_size: int
    results: List[TodoItemResponse]

    # Search metadata
    search_time_ms: float = 0.0
    suggested_terms: List[str] = []


class PaginationParams(BaseSchema):
    """Schema for pagination parameters."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: str = "created_at"
    sort_order: str = Field(default="desc", regex="^(asc|desc)$")


class FilterParams(BaseSchema):
    """Schema for filtering parameters."""
    status: Optional[StatusType] = None
    priority: Optional[PriorityLevel] = None
    category_id: Optional[UUID] = None
    tags: Optional[List[str]] = None
    is_overdue: Optional[bool] = None
    is_pinned: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


# =============================================================================
# BULK OPERATION SCHEMAS
# =============================================================================

class BulkUpdateTodos(BaseSchema):
    """Schema for bulk updating todos."""
    todo_ids: List[UUID] = Field(min_items=1, max_items=100)
    updates: TodoItemUpdate


class BulkDeleteTodos(BaseSchema):
    """Schema for bulk deleting todos."""
    todo_ids: List[UUID] = Field(min_items=1, max_items=100)
    permanent: bool = False  # If False, just archive


class BulkOperationResult(BaseSchema):
    """Schema for bulk operation results."""
    success_count: int
    failed_count: int
    errors: List[str] = []
    updated_ids: List[UUID] = []


# =============================================================================
# API RESPONSE SCHEMAS
# =============================================================================

class APIResponse(BaseSchema):
    """Generic API response schema."""
    success: bool = True
    message: str = "Operation successful"
    data: Optional[Any] = None
    errors: Optional[List[str]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PaginatedResponse(BaseSchema):
    """Schema for paginated responses."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool


# Update forward references for self-referencing models
TodoItemResponse.model_rebuild()
CommentResponse.model_rebuild()