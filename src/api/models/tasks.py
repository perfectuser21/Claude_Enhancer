"""
任务相关数据模型
===============

定义任务管理相关的请求和响应模型
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, validator
from .common import BaseResponse, PaginatedResponse


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


class TaskCreateRequest(BaseModel):
    """创建任务请求"""

    title: str = Field(..., min_length=1, max_length=200, description="任务标题")
    description: Optional[str] = Field(None, description="任务描述，支持Markdown")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="任务优先级")
    project_id: Optional[UUID] = Field(None, description="所属项目ID")
    assignee_id: Optional[UUID] = Field(None, description="分配给用户ID")
    due_date: Optional[datetime] = Field(None, description="截止日期")
    estimated_hours: Optional[int] = Field(None, ge=0, le=1000, description="预估工时（小时）")
    tags: List[str] = Field(default_factory=list, description="任务标签", max_items=10)
    labels: Dict[str, Any] = Field(default_factory=dict, description="标签元数据（颜色、描述等）")
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="自定义字段数据")

    @validator("tags")
    def validate_tags(cls, v):
        """验证标签"""
        if v:
            # 检查标签长度
            for tag in v:
                if len(tag) > 50:
                    raise ValueError("标签长度不能超过50个字符")
                if not tag.strip():
                    raise ValueError("标签不能为空")
        return v

    @validator("due_date")
    def validate_due_date(cls, v):
        """验证截止日期"""
        if v and v < datetime.utcnow():
            raise ValueError("截止日期不能早于当前时间")
        return v


class TaskUpdateRequest(BaseModel):
    """更新任务请求"""

    title: Optional[str] = Field(None, min_length=1, max_length=200, description="任务标题")
    description: Optional[str] = Field(None, description="任务描述")
    status: Optional[TaskStatus] = Field(None, description="任务状态")
    priority: Optional[TaskPriority] = Field(None, description="任务优先级")
    assignee_id: Optional[UUID] = Field(None, description="分配给用户ID")
    due_date: Optional[datetime] = Field(None, description="截止日期")
    estimated_hours: Optional[int] = Field(None, ge=0, le=1000, description="预估工时")
    actual_hours: Optional[int] = Field(None, ge=0, le=1000, description="实际工时")
    progress_percentage: Optional[int] = Field(None, ge=0, le=100, description="完成百分比")
    tags: Optional[List[str]] = Field(None, description="任务标签")
    labels: Optional[Dict[str, Any]] = Field(None, description="标签元数据")
    custom_fields: Optional[Dict[str, Any]] = Field(None, description="自定义字段")


class TaskResponse(BaseResponse):
    """任务响应"""

    class TaskData(BaseModel):
        id: UUID = Field(description="任务ID")
        title: str = Field(description="任务标题")
        description: Optional[str] = Field(description="任务描述")
        status: TaskStatus = Field(description="任务状态")
        priority: TaskPriority = Field(description="任务优先级")
        project_id: Optional[UUID] = Field(description="所属项目ID")
        assignee_id: Optional[UUID] = Field(description="分配用户ID")
        due_date: Optional[datetime] = Field(description="截止日期")
        estimated_hours: Optional[int] = Field(description="预估工时")
        actual_hours: Optional[int] = Field(description="实际工时")
        progress_percentage: int = Field(description="完成百分比")
        tags: List[str] = Field(description="任务标签")
        labels: Dict[str, Any] = Field(description="标签元数据")
        custom_fields: Dict[str, Any] = Field(description="自定义字段")
        created_at: datetime = Field(description="创建时间")
        updated_at: datetime = Field(description="更新时间")
        started_at: Optional[datetime] = Field(description="开始时间")
        completed_at: Optional[datetime] = Field(description="完成时间")
        is_overdue: bool = Field(description="是否逾期")
        is_completed: bool = Field(description="是否已完成")

        # 关联数据
        assignee: Optional[Dict[str, Any]] = Field(description="分配用户信息")
        project: Optional[Dict[str, Any]] = Field(description="所属项目信息")
        comments_count: int = Field(0, description="评论数量")
        attachments_count: int = Field(0, description="附件数量")

        class Config:
            from_attributes = True

    data: TaskData = Field(description="任务数据")


class TaskListResponse(PaginatedResponse[TaskResponse.TaskData]):
    """任务列表响应"""

    pass


class TaskFilterParams(BaseModel):
    """任务过滤参数"""

    status: Optional[List[TaskStatus]] = Field(None, description="状态过滤")
    priority: Optional[List[TaskPriority]] = Field(None, description="优先级过滤")
    project_id: Optional[UUID] = Field(None, description="项目ID过滤")
    assignee_id: Optional[UUID] = Field(None, description="分配用户ID过滤")
    created_by: Optional[UUID] = Field(None, description="创建者ID过滤")
    tags: Optional[List[str]] = Field(None, description="标签过滤")
    due_date_from: Optional[datetime] = Field(None, description="截止日期范围开始")
    due_date_to: Optional[datetime] = Field(None, description="截止日期范围结束")
    is_overdue: Optional[bool] = Field(None, description="是否逾期")
    search: Optional[str] = Field(None, description="搜索关键词")
    sort_by: Optional[str] = Field("created_at", description="排序字段")
    sort_order: Optional[str] = Field("desc", description="排序方向")


class TaskCommentCreateRequest(BaseModel):
    """创建任务评论请求"""

    content: str = Field(
        ..., min_length=1, max_length=2000, description="评论内容，支持Markdown"
    )
    is_internal: bool = Field(False, description="是否内部评论")
    reply_to: Optional[UUID] = Field(None, description="回复的评论ID")


class TaskCommentResponse(BaseResponse):
    """任务评论响应"""

    class CommentData(BaseModel):
        id: UUID = Field(description="评论ID")
        task_id: UUID = Field(description="任务ID")
        content: str = Field(description="评论内容")
        is_internal: bool = Field(description="是否内部评论")
        reply_to: Optional[UUID] = Field(description="回复的评论ID")
        created_at: datetime = Field(description="创建时间")
        updated_at: datetime = Field(description="更新时间")

        # 关联数据
        author: Dict[str, Any] = Field(description="作者信息")
        replies: List[Dict[str, Any]] = Field(description="回复列表")

        class Config:
            from_attributes = True

    data: CommentData = Field(description="评论数据")


class TaskAttachmentResponse(BaseResponse):
    """任务附件响应"""

    class AttachmentData(BaseModel):
        id: UUID = Field(description="附件ID")
        task_id: UUID = Field(description="任务ID")
        filename: str = Field(description="存储文件名")
        original_name: str = Field(description="原始文件名")
        file_size: int = Field(description="文件大小")
        mime_type: Optional[str] = Field(description="MIME类型")
        download_url: str = Field(description="下载URL")
        thumbnail_url: Optional[str] = Field(description="缩略图URL")
        created_at: datetime = Field(description="上传时间")

        # 关联数据
        uploader: Dict[str, Any] = Field(description="上传者信息")

        class Config:
            from_attributes = True

    data: AttachmentData = Field(description="附件数据")


class TaskActivityResponse(BaseResponse):
    """任务活动日志响应"""

    class ActivityData(BaseModel):
        id: UUID = Field(description="活动ID")
        task_id: UUID = Field(description="任务ID")
        action: str = Field(description="操作类型")
        field_name: Optional[str] = Field(description="变更字段")
        old_value: Optional[str] = Field(description="旧值")
        new_value: Optional[str] = Field(description="新值")
        description: Optional[str] = Field(description="活动描述")
        created_at: datetime = Field(description="发生时间")

        # 关联数据
        user: Optional[Dict[str, Any]] = Field(description="操作用户")

        class Config:
            from_attributes = True

    data: List[ActivityData] = Field(description="活动日志列表")


class TaskStatsResponse(BaseResponse):
    """任务统计响应"""

    class TaskStats(BaseModel):
        total_tasks: int = Field(description="总任务数")
        completed_tasks: int = Field(description="已完成任务数")
        in_progress_tasks: int = Field(description="进行中任务数")
        todo_tasks: int = Field(description="待办任务数")
        overdue_tasks: int = Field(description="逾期任务数")
        blocked_tasks: int = Field(description="阻塞任务数")

        # 按优先级统计
        priority_stats: Dict[str, int] = Field(description="按优先级统计")

        # 按状态统计
        status_stats: Dict[str, int] = Field(description="按状态统计")

        # 时间统计
        avg_completion_time: Optional[float] = Field(description="平均完成时间（天）")
        completion_rate: float = Field(description="完成率")

    data: TaskStats = Field(description="任务统计数据")


class TaskBulkUpdateRequest(BaseModel):
    """批量更新任务请求"""

    task_ids: List[UUID] = Field(..., min_items=1, description="任务ID列表")
    updates: TaskUpdateRequest = Field(..., description="更新数据")


class TaskAssignRequest(BaseModel):
    """任务分配请求"""

    assignee_id: Optional[UUID] = Field(None, description="分配用户ID，null表示取消分配")
    notify_assignee: bool = Field(True, description="是否通知被分配者")
