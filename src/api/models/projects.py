"""
项目相关数据模型
===============

定义项目管理相关的请求和响应模型
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, validator
from .common import BaseResponse, PaginatedResponse


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


class ProjectCreateRequest(BaseModel):
    """创建项目请求"""

    name: str = Field(..., min_length=1, max_length=100, description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    color: str = Field("#1976d2", regex="^#[0-9A-Fa-f]{6}$", description="项目颜色（十六进制）")
    start_date: Optional[datetime] = Field(None, description="计划开始日期")
    end_date: Optional[datetime] = Field(None, description="计划结束日期")
    team_id: Optional[UUID] = Field(None, description="所属团队ID")
    is_public: bool = Field(False, description="是否公开项目")
    settings: Dict[str, Any] = Field(default_factory=dict, description="项目配置")

    @validator("end_date")
    def validate_end_date(cls, v, values):
        """验证结束日期"""
        if v and "start_date" in values and values["start_date"]:
            if v <= values["start_date"]:
                raise ValueError("结束日期必须晚于开始日期")
        return v


class ProjectUpdateRequest(BaseModel):
    """更新项目请求"""

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    status: Optional[ProjectStatus] = Field(None, description="项目状态")
    color: Optional[str] = Field(None, regex="^#[0-9A-Fa-f]{6}$", description="项目颜色")
    start_date: Optional[datetime] = Field(None, description="计划开始日期")
    end_date: Optional[datetime] = Field(None, description="计划结束日期")
    actual_start_date: Optional[datetime] = Field(None, description="实际开始日期")
    actual_end_date: Optional[datetime] = Field(None, description="实际结束日期")
    is_public: Optional[bool] = Field(None, description="是否公开项目")
    is_archived: Optional[bool] = Field(None, description="是否归档")
    settings: Optional[Dict[str, Any]] = Field(None, description="项目配置")


class ProjectResponse(BaseResponse):
    """项目响应"""

    class ProjectData(BaseModel):
        id: UUID = Field(description="项目ID")
        name: str = Field(description="项目名称")
        description: Optional[str] = Field(description="项目描述")
        status: ProjectStatus = Field(description="项目状态")
        color: str = Field(description="项目颜色")
        start_date: Optional[datetime] = Field(description="计划开始日期")
        end_date: Optional[datetime] = Field(description="计划结束日期")
        actual_start_date: Optional[datetime] = Field(description="实际开始日期")
        actual_end_date: Optional[datetime] = Field(description="实际结束日期")
        team_id: Optional[UUID] = Field(description="所属团队ID")
        is_public: bool = Field(description="是否公开")
        is_archived: bool = Field(description="是否归档")
        settings: Dict[str, Any] = Field(description="项目配置")
        created_at: datetime = Field(description="创建时间")
        updated_at: datetime = Field(description="更新时间")

        # 统计信息
        task_count: int = Field(description="任务总数")
        completed_task_count: int = Field(description="已完成任务数")
        completion_percentage: float = Field(description="完成百分比")
        member_count: int = Field(description="成员数量")

        # 关联数据
        team: Optional[Dict[str, Any]] = Field(description="所属团队信息")
        creator: Dict[str, Any] = Field(description="创建者信息")
        members: List[Dict[str, Any]] = Field(description="项目成员列表")

        class Config:
            from_attributes = True

    data: ProjectData = Field(description="项目数据")


class ProjectListResponse(PaginatedResponse[ProjectResponse.ProjectData]):
    """项目列表响应"""

    pass


class ProjectFilterParams(BaseModel):
    """项目过滤参数"""

    status: Optional[List[ProjectStatus]] = Field(None, description="状态过滤")
    team_id: Optional[UUID] = Field(None, description="团队ID过滤")
    created_by: Optional[UUID] = Field(None, description="创建者ID过滤")
    is_public: Optional[bool] = Field(None, description="是否公开过滤")
    is_archived: Optional[bool] = Field(None, description="是否归档过滤")
    start_date_from: Optional[datetime] = Field(None, description="开始日期范围")
    start_date_to: Optional[datetime] = Field(None, description="开始日期范围")
    search: Optional[str] = Field(None, description="搜索关键词")
    sort_by: Optional[str] = Field("created_at", description="排序字段")
    sort_order: Optional[str] = Field("desc", description="排序方向")


class ProjectMemberAddRequest(BaseModel):
    """添加项目成员请求"""

    user_id: UUID = Field(..., description="用户ID")
    role: MemberRole = Field(MemberRole.MEMBER, description="成员角色")
    permissions: Dict[str, Any] = Field(default_factory=dict, description="特殊权限设置")
    notify_user: bool = Field(True, description="是否通知用户")


class ProjectMemberUpdateRequest(BaseModel):
    """更新项目成员请求"""

    role: Optional[MemberRole] = Field(None, description="成员角色")
    permissions: Optional[Dict[str, Any]] = Field(None, description="特殊权限")


class ProjectMemberResponse(BaseResponse):
    """项目成员响应"""

    class MemberData(BaseModel):
        id: UUID = Field(description="成员记录ID")
        project_id: UUID = Field(description="项目ID")
        user_id: UUID = Field(description="用户ID")
        role: MemberRole = Field(description="成员角色")
        permissions: Dict[str, Any] = Field(description="特殊权限")
        joined_at: datetime = Field(description="加入时间")

        # 关联数据
        user: Dict[str, Any] = Field(description="用户信息")

        class Config:
            from_attributes = True

    data: MemberData = Field(description="成员数据")


class ProjectStatsResponse(BaseResponse):
    """项目统计响应"""

    class ProjectStats(BaseModel):
        total_projects: int = Field(description="总项目数")
        active_projects: int = Field(description="活跃项目数")
        completed_projects: int = Field(description="已完成项目数")
        planning_projects: int = Field(description="计划中项目数")
        on_hold_projects: int = Field(description="暂停项目数")
        cancelled_projects: int = Field(description="取消项目数")

        # 按状态统计
        status_stats: Dict[str, int] = Field(description="按状态统计")

        # 时间统计
        avg_project_duration: Optional[float] = Field(description="平均项目持续时间（天）")
        project_completion_rate: float = Field(description="项目完成率")

        # 任务统计
        total_tasks: int = Field(description="所有项目总任务数")
        completed_tasks: int = Field(description="已完成任务数")
        task_completion_rate: float = Field(description="任务完成率")

    data: ProjectStats = Field(description="项目统计数据")


class ProjectTimelineResponse(BaseResponse):
    """项目时间线响应"""

    class TimelineEvent(BaseModel):
        id: UUID = Field(description="事件ID")
        type: str = Field(description="事件类型")
        title: str = Field(description="事件标题")
        description: Optional[str] = Field(description="事件描述")
        date: datetime = Field(description="事件日期")
        user: Optional[Dict[str, Any]] = Field(description="关联用户")
        metadata: Dict[str, Any] = Field(description="事件元数据")

    data: List[TimelineEvent] = Field(description="时间线事件列表")


class ProjectTemplateResponse(BaseResponse):
    """项目模板响应"""

    class TemplateData(BaseModel):
        id: UUID = Field(description="模板ID")
        name: str = Field(description="模板名称")
        description: Optional[str] = Field(description="模板描述")
        category: str = Field(description="模板分类")
        tasks: List[Dict[str, Any]] = Field(description="任务模板")
        settings: Dict[str, Any] = Field(description="项目配置模板")
        created_at: datetime = Field(description="创建时间")

        class Config:
            from_attributes = True

    data: List[TemplateData] = Field(description="项目模板列表")


class ProjectArchiveRequest(BaseModel):
    """项目归档请求"""

    reason: Optional[str] = Field(None, description="归档原因")
    backup_data: bool = Field(True, description="是否备份数据")


class ProjectBulkUpdateRequest(BaseModel):
    """批量更新项目请求"""

    project_ids: List[UUID] = Field(..., min_items=1, description="项目ID列表")
    updates: ProjectUpdateRequest = Field(..., description="更新数据")


class ProjectInviteRequest(BaseModel):
    """项目邀请请求"""

    email: str = Field(..., description="邀请邮箱")
    role: MemberRole = Field(MemberRole.MEMBER, description="成员角色")
    message: Optional[str] = Field(None, description="邀请消息")
    expires_in_days: int = Field(7, ge=1, le=30, description="邀请有效期（天）")
