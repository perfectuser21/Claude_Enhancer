"""
任务管理系统API路由
==================

实现完整的RESTful API端点，包括：
- TaskRouter: 任务管理API
- ProjectRouter: 项目管理API
- DashboardRouter: 仪表板API
- NotificationRouter: 通知API
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Path,
    File,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.dependencies import get_current_user, get_current_active_user
from backend.models.user import User
from src.task_management.models import (
    Task,
    TaskStatus,
    TaskPriority,
    Project,
    ProjectStatus,
)
from src.task_management.services import (
    TaskService,
    ProjectService,
    NotificationService,
    FileService,
)
from src.task_management.repositories import TaskRepository, ProjectRepository


# ===== Pydantic 模型定义 =====


class TaskCreateRequest(BaseModel):
    """创建任务请求模型"""

    title: str = Field(..., min_length=1, max_length=200, description="任务标题")
    description: Optional[str] = Field(None, description="任务描述")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="任务优先级")
    project_id: Optional[UUID] = Field(None, description="所属项目ID")
    assignee_id: Optional[UUID] = Field(None, description="分配给用户ID")
    due_date: Optional[datetime] = Field(None, description="截止日期")
    estimated_hours: Optional[int] = Field(None, ge=0, description="预估工时（小时）")
    tags: List[str] = Field(default_factory=list, description="任务标签")
    labels: Dict[str, Any] = Field(default_factory=dict, description="标签元数据")
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="自定义字段")


class TaskUpdateRequest(BaseModel):
    """更新任务请求模型"""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    assignee_id: Optional[UUID] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[int] = Field(None, ge=0)
    actual_hours: Optional[int] = Field(None, ge=0)
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    tags: Optional[List[str]] = None
    labels: Optional[Dict[str, Any]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class TaskStatusUpdateRequest(BaseModel):
    """任务状态更新请求模型"""

    status: TaskStatus = Field(..., description="新状态")
    comment: Optional[str] = Field(None, description="状态变更说明")


class TaskAssignRequest(BaseModel):
    """任务分配请求模型"""

    assignee_id: UUID = Field(..., description="分配给用户ID")


class TaskResponse(BaseModel):
    """任务响应模型"""

    id: UUID
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    assignee_id: Optional[UUID]
    project_id: Optional[UUID]
    due_date: Optional[datetime]
    estimated_hours: Optional[int]
    actual_hours: Optional[int]
    progress_percentage: int
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    is_overdue: bool

    class Config:
        from_attributes = True


class TaskListQuery(BaseModel):
    """任务列表查询参数"""

    page: int = Field(1, ge=1, description="页码")
    size: int = Field(20, ge=1, le=100, description="每页数量")
    search: Optional[str] = Field(None, description="搜索关键词")
    status: Optional[List[TaskStatus]] = Field(None, description="状态筛选")
    priority: Optional[List[TaskPriority]] = Field(None, description="优先级筛选")
    assignee_id: Optional[UUID] = Field(None, description="分配者筛选")
    project_id: Optional[UUID] = Field(None, description="项目筛选")
    due_date_from: Optional[datetime] = Field(None, description="截止日期起始")
    due_date_to: Optional[datetime] = Field(None, description="截止日期结束")
    tags: Optional[List[str]] = Field(None, description="标签筛选")
    sort_by: str = Field("updated_at", description="排序字段")
    sort_order: str = Field("desc", regex="^(asc|desc)$", description="排序方向")


class ProjectCreateRequest(BaseModel):
    """创建项目请求模型"""

    name: str = Field(..., min_length=1, max_length=100, description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    start_date: Optional[datetime] = Field(None, description="开始日期")
    end_date: Optional[datetime] = Field(None, description="结束日期")
    team_id: Optional[UUID] = Field(None, description="团队ID")
    color: str = Field("#1976d2", regex="^#[0-9a-fA-F]{6}$", description="项目颜色")
    is_public: bool = Field(False, description="是否公开项目")


class ProjectResponse(BaseModel):
    """项目响应模型"""

    id: UUID
    name: str
    description: Optional[str]
    status: ProjectStatus
    color: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    is_public: bool
    task_count: int
    completion_percentage: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel):
    """分页响应模型"""

    items: List[Any]
    total: int
    page: int
    size: int
    pages: int


# ===== 任务管理API路由 =====


def create_task_router(
    task_service: TaskService, file_service: FileService
) -> APIRouter:
    """创建任务管理路由器"""

    router = APIRouter()

    @router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
    async def create_task(
        task_data: TaskCreateRequest,
        current_user: User = Depends(get_current_active_user),
    ):
        """
        创建新任务

        创建一个新的任务。如果指定了分配者，将自动发送分配通知。
        """
        try:
            task = await task_service.create_task(
                task_data=task_data.dict(),
                creator_id=str(current_user.id),
                notify_assignee=True,
            )
            return TaskResponse.from_orm(task)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except PermissionError as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    @router.get("/", response_model=PaginatedResponse)
    async def list_tasks(
        page: int = Query(1, ge=1, description="页码"),
        size: int = Query(20, ge=1, le=100, description="每页数量"),
        search: Optional[str] = Query(None, description="搜索关键词"),
        status: Optional[List[TaskStatus]] = Query(None, description="状态筛选"),
        priority: Optional[List[TaskPriority]] = Query(None, description="优先级筛选"),
        assignee_id: Optional[UUID] = Query(None, description="分配者筛选"),
        project_id: Optional[UUID] = Query(None, description="项目筛选"),
        due_date_from: Optional[datetime] = Query(None, description="截止日期起始"),
        due_date_to: Optional[datetime] = Query(None, description="截止日期结束"),
        tags: Optional[List[str]] = Query(None, description="标签筛选"),
        sort_by: str = Query("updated_at", description="排序字段"),
        sort_order: str = Query("desc", regex="^(asc|desc)$", description="排序方向"),
        current_user: User = Depends(get_current_active_user),
    ):
        """
        获取任务列表

        支持多种筛选和排序选项的任务列表查询。
        """
        filters = {
            "status": status,
            "priority": priority,
            "assignee_id": assignee_id,
            "project_id": project_id,
            "due_date_from": due_date_from,
            "due_date_to": due_date_to,
            "tags": tags,
        }

        # 移除None值
        filters = {k: v for k, v in filters.items() if v is not None}

        result = await task_service.search_tasks(
            user_id=str(current_user.id),
            query=search,
            filters=filters,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            page_size=size,
        )

        return PaginatedResponse(
            items=[TaskResponse.from_orm(task) for task in result["tasks"]],
            total=result["pagination"]["total_count"],
            page=result["pagination"]["page"],
            size=result["pagination"]["page_size"],
            pages=result["pagination"]["total_pages"],
        )

    @router.get("/{task_id}", response_model=TaskResponse)
    async def get_task(
        task_id: UUID = Path(..., description="任务ID"),
        current_user: User = Depends(get_current_active_user),
    ):
        """
        获取任务详情

        返回指定任务的详细信息，包括关联的评论和附件。
        """
        task = await task_service.get_task_by_id(
            task_id=str(task_id), user_id=str(current_user.id), include_relations=True
        )

        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")

        return TaskResponse.from_orm(task)

    @router.put("/{task_id}", response_model=TaskResponse)
    async def update_task(
        task_id: UUID = Path(..., description="任务ID"),
        update_data: TaskUpdateRequest = ...,
        current_user: User = Depends(get_current_active_user),
    ):
        """
        更新任务

        更新任务的各项信息。只有有权限的用户才能更新任务。
        """
        try:
            # 只更新提供的字段
            update_dict = update_data.dict(exclude_unset=True)

            task = await task_service.update_task(
                task_id=str(task_id),
                update_data=update_dict,
                user_id=str(current_user.id),
            )

            return TaskResponse.from_orm(task)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except PermissionError as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    @router.patch("/{task_id}/status", response_model=TaskResponse)
    async def update_task_status(
        task_id: UUID = Path(..., description="任务ID"),
        status_data: TaskStatusUpdateRequest = ...,
        current_user: User = Depends(get_current_active_user),
    ):
        """
        更新任务状态

        更新任务状态，支持状态转换验证和通知。
        """
        try:
            task = await task_service.update_task_status(
                task_id=str(task_id),
                new_status=status_data.status.value,
                user_id=str(current_user.id),
                comment=status_data.comment,
            )

            return TaskResponse.from_orm(task)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    @router.post("/{task_id}/assign", response_model=TaskResponse)
    async def assign_task(
        task_id: UUID = Path(..., description="任务ID"),
        assign_data: TaskAssignRequest = ...,
        current_user: User = Depends(get_current_active_user),
    ):
        """
        分配任务

        将任务分配给指定用户，自动发送分配通知。
        """
        try:
            task = await task_service.assign_task(
                task_id=str(task_id),
                assignee_id=str(assign_data.assignee_id),
                assigner_id=str(current_user.id),
            )

            return TaskResponse.from_orm(task)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except PermissionError as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    @router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_task(
        task_id: UUID = Path(..., description="任务ID"),
        current_user: User = Depends(get_current_active_user),
    ):
        """
        删除任务

        软删除指定任务。只有任务创建者或项目管理员可以删除任务。
        """
        # 获取任务并检查权限
        task = await task_service.get_task_by_id(
            task_id=str(task_id), user_id=str(current_user.id)
        )

        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")

        # 检查删除权限（创建者或项目管理员）
        can_delete = task.created_by == str(
            current_user.id
        ) or await task_service._check_project_permission(
            str(task.project_id), str(current_user.id)
        )

        if not can_delete:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有删除权限")

        # 执行软删除
        task.soft_delete()
        await task_service.db.commit()

        # 记录活动
        await task_service.activity_service.log_task_activity(
            task_id=str(task_id),
            user_id=str(current_user.id),
            action="deleted",
            description=f"删除任务: {task.title}",
        )

    @router.post("/{task_id}/files", status_code=status.HTTP_201_CREATED)
    async def upload_task_file(
        task_id: UUID = Path(..., description="任务ID"),
        file: UploadFile = File(..., description="上传的文件"),
        current_user: User = Depends(get_current_active_user),
    ):
        """
        上传任务附件

        为指定任务上传文件附件。
        """
        try:
            attachment = await file_service.upload_task_attachment(
                task_id=str(task_id), file=file, user_id=str(current_user.id)
            )

            return {
                "id": str(attachment.id),
                "filename": attachment.original_name,
                "size": attachment.file_size,
                "uploaded_at": attachment.created_at,
            }
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    @router.get("/my/summary")
    async def get_my_tasks_summary(
        current_user: User = Depends(get_current_active_user),
    ):
        """
        获取我的任务概览

        返回当前用户的任务统计信息。
        """
        summary = await task_service.get_user_tasks_summary(str(current_user.id))
        return summary

    @router.get("/overdue")
    async def get_overdue_tasks(current_user: User = Depends(get_current_active_user)):
        """
        获取逾期任务

        返回当前用户的所有逾期任务。
        """
        from src.task_management.repositories import TaskRepository

        task_repo = TaskRepository(task_service.db)
        overdue_tasks = await task_repo.get_overdue_tasks(user_id=str(current_user.id))

        return [TaskResponse.from_orm(task) for task in overdue_tasks]

    @router.get("/due-soon")
    async def get_tasks_due_soon(
        days: int = Query(7, ge=1, le=30, description="提前天数"),
        current_user: User = Depends(get_current_active_user),
    ):
        """
        获取即将到期的任务

        返回指定天数内到期的任务。
        """
        from src.task_management.repositories import TaskRepository

        task_repo = TaskRepository(task_service.db)
        due_soon_tasks = await task_repo.get_tasks_due_soon(
            days_ahead=days, user_id=str(current_user.id)
        )

        return [TaskResponse.from_orm(task) for task in due_soon_tasks]

    @router.post("/bulk-update")
    async def bulk_update_tasks(
        task_ids: List[UUID],
        update_data: TaskUpdateRequest,
        current_user: User = Depends(get_current_active_user),
    ):
        """
        批量更新任务

        同时更新多个任务的相同字段。
        """
        try:
            update_dict = update_data.dict(exclude_unset=True)

            updated_tasks = await task_service.bulk_update_tasks(
                task_ids=[str(tid) for tid in task_ids],
                update_data=update_dict,
                user_id=str(current_user.id),
            )

            return [TaskResponse.from_orm(task) for task in updated_tasks]
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except PermissionError as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    return router


# ===== 项目管理API路由 =====


def create_project_router(project_service: ProjectService) -> APIRouter:
    """创建项目管理路由器"""

    router = APIRouter()

    @router.post(
        "/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED
    )
    async def create_project(
        project_data: ProjectCreateRequest,
        current_user: User = Depends(get_current_active_user),
    ):
        """
        创建新项目

        创建一个新项目，创建者自动成为项目所有者。
        """
        try:
            project = await project_service.create_project(
                project_data=project_data.dict(), creator_id=str(current_user.id)
            )

            return ProjectResponse.from_orm(project)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    @router.get("/", response_model=List[ProjectResponse])
    async def list_projects(
        status_filter: Optional[List[ProjectStatus]] = Query(None, description="状态筛选"),
        include_archived: bool = Query(False, description="包含已归档项目"),
        current_user: User = Depends(get_current_active_user),
    ):
        """
        获取项目列表

        返回当前用户参与的所有项目。
        """
        from src.task_management.repositories import ProjectRepository

        project_repo = ProjectRepository(project_service.db)
        projects = await project_repo.get_user_projects(
            user_id=str(current_user.id),
            status_filter=[s.value for s in status_filter] if status_filter else None,
            include_archived=include_archived,
        )

        return [ProjectResponse.from_orm(project) for project in projects]

    @router.get("/{project_id}", response_model=ProjectResponse)
    async def get_project(
        project_id: UUID = Path(..., description="项目ID"),
        current_user: User = Depends(get_current_active_user),
    ):
        """
        获取项目详情

        返回指定项目的详细信息。
        """
        from src.task_management.repositories import ProjectRepository

        project_repo = ProjectRepository(project_service.db)
        project = await project_repo.get_by_id(str(project_id))

        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

        # 检查访问权限
        if not await project_repo._check_project_access(
            str(project_id), str(current_user.id)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="没有项目访问权限"
            )

        return ProjectResponse.from_orm(project)

    @router.get("/{project_id}/statistics")
    async def get_project_statistics(
        project_id: UUID = Path(..., description="项目ID"),
        current_user: User = Depends(get_current_active_user),
    ):
        """
        获取项目统计信息

        返回项目的任务统计、成员信息等数据。
        """
        try:
            stats = await project_service.get_project_statistics(
                project_id=str(project_id), user_id=str(current_user.id)
            )

            return stats
        except PermissionError as e:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    @router.get("/{project_id}/tasks")
    async def get_project_tasks(
        project_id: UUID = Path(..., description="项目ID"),
        status_filter: Optional[List[TaskStatus]] = Query(None, description="状态筛选"),
        assignee_filter: Optional[UUID] = Query(None, description="分配者筛选"),
        current_user: User = Depends(get_current_active_user),
    ):
        """
        获取项目任务列表

        返回指定项目的所有任务。
        """
        from src.task_management.repositories import TaskRepository

        task_repo = TaskRepository(project_service.db)
        tasks = await task_repo.get_tasks_by_project(
            project_id=str(project_id),
            user_id=str(current_user.id),
            status_filter=[s.value for s in status_filter] if status_filter else None,
            assignee_filter=str(assignee_filter) if assignee_filter else None,
            include_relations=True,
        )

        return [TaskResponse.from_orm(task) for task in tasks]

    return router


# ===== 仪表板API路由 =====


def create_dashboard_router(
    task_service: TaskService, project_service: ProjectService
) -> APIRouter:
    """创建仪表板路由器"""

    router = APIRouter()

    @router.get("/stats")
    async def get_dashboard_stats(
        current_user: User = Depends(get_current_active_user),
    ):
        """
        获取仪表板统计数据

        返回用户的整体任务和项目统计信息。
        """
        # 获取任务概览
        task_summary = await task_service.get_user_tasks_summary(str(current_user.id))

        # 获取项目列表
        from src.task_management.repositories import ProjectRepository

        project_repo = ProjectRepository(project_service.db)
        projects = await project_repo.get_user_projects(
            user_id=str(current_user.id), include_archived=False
        )

        # 获取工作负载
        from src.task_management.repositories import TaskRepository

        task_repo = TaskRepository(task_service.db)
        workload = await task_repo.get_user_workload(str(current_user.id))

        return {
            "task_summary": task_summary,
            "project_count": len(projects),
            "workload": workload,
            "recent_activity_count": 0,  # 可以添加最近活动统计
        }

    @router.get("/recent-tasks")
    async def get_recent_tasks(
        limit: int = Query(10, ge=1, le=50, description="返回数量"),
        current_user: User = Depends(get_current_active_user),
    ):
        """
        获取最近任务

        返回用户最近创建或更新的任务。
        """
        from src.task_management.repositories import TaskRepository

        task_repo = TaskRepository(task_service.db)

        # 获取最近更新的任务
        recent_tasks = await task_repo.get_user_assigned_tasks(
            user_id=str(current_user.id)
        )

        # 按更新时间排序并限制数量
        recent_tasks = sorted(recent_tasks, key=lambda t: t.updated_at, reverse=True)[
            :limit
        ]

        return [TaskResponse.from_orm(task) for task in recent_tasks]

    @router.get("/workload")
    async def get_workload_analysis(
        days: int = Query(30, ge=7, le=90, description="分析天数"),
        current_user: User = Depends(get_current_active_user),
    ):
        """
        获取工作负载分析

        返回指定时间范围内的工作负载分析数据。
        """
        from src.task_management.repositories import TaskRepository

        task_repo = TaskRepository(task_service.db)

        # 计算日期范围
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        workload = await task_repo.get_user_workload(
            user_id=str(current_user.id), date_range=(start_date, end_date)
        )

        return workload

    @router.get("/timeline")
    async def get_timeline(
        days: int = Query(30, ge=7, le=90, description="时间线天数"),
        current_user: User = Depends(get_current_active_user),
    ):
        """
        获取时间线数据

        返回用户在指定时间范围内的任务活动时间线。
        """
        from src.task_management.repositories import TaskRepository

        task_repo = TaskRepository(task_service.db)

        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # 获取时间范围内的任务
        tasks = await task_repo.get_user_assigned_tasks(
            user_id=str(current_user.id), due_date_range=(start_date, end_date)
        )

        # 构建时间线数据
        timeline_events = []
        for task in tasks:
            if task.due_date:
                timeline_events.append(
                    {
                        "date": task.due_date.isoformat(),
                        "type": "due_date",
                        "task_id": str(task.id),
                        "task_title": task.title,
                        "priority": task.priority,
                        "status": task.status,
                    }
                )

        # 按日期排序
        timeline_events.sort(key=lambda x: x["date"])

        return timeline_events

    return router


# ===== 通知API路由 =====


def create_notification_router(notification_service: NotificationService) -> APIRouter:
    """创建通知路由器"""

    router = APIRouter()

    @router.get("/")
    async def list_notifications(
        page: int = Query(1, ge=1, description="页码"),
        size: int = Query(20, ge=1, le=100, description="每页数量"),
        unread_only: bool = Query(False, description="仅未读通知"),
        current_user: User = Depends(get_current_active_user),
    ):
        """
        获取通知列表

        返回用户的通知列表，支持分页和未读筛选。
        """
        from src.task_management.models import Notification

        query = notification_service.db.query(Notification).filter(
            Notification.user_id == str(current_user.id)
        )

        if unread_only:
            query = query.filter(Notification.is_read == False)

        total = await query.count()

        offset = (page - 1) * size
        notifications = (
            await query.order_by(Notification.created_at.desc())
            .offset(offset)
            .limit(size)
            .all()
        )

        return {
            "notifications": [
                {
                    "id": str(notif.id),
                    "title": notif.title,
                    "content": notif.content,
                    "type": notif.type,
                    "is_read": notif.is_read,
                    "created_at": notif.created_at,
                    "action_url": notif.action_url,
                }
                for notif in notifications
            ],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size,
        }

    @router.put("/{notification_id}/read")
    async def mark_notification_read(
        notification_id: UUID = Path(..., description="通知ID"),
        current_user: User = Depends(get_current_active_user),
    ):
        """
        标记通知为已读

        将指定通知标记为已读状态。
        """
        from src.task_management.models import Notification

        notification = (
            await notification_service.db.query(Notification)
            .filter(
                and_(
                    Notification.id == str(notification_id),
                    Notification.user_id == str(current_user.id),
                )
            )
            .first()
        )

        if not notification:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="通知不存在")

        notification.mark_as_read()
        await notification_service.db.commit()

        return {"message": "通知已标记为已读"}

    @router.patch("/mark-all-read")
    async def mark_all_notifications_read(
        current_user: User = Depends(get_current_active_user),
    ):
        """
        标记所有通知为已读

        将用户的所有未读通知标记为已读。
        """
        from src.task_management.models import Notification

        await notification_service.db.query(Notification).filter(
            and_(
                Notification.user_id == str(current_user.id),
                Notification.is_read == False,
            )
        ).update({"is_read": True, "read_at": datetime.utcnow()})

        await notification_service.db.commit()

        return {"message": "所有通知已标记为已读"}

    @router.delete("/{notification_id}")
    async def delete_notification(
        notification_id: UUID = Path(..., description="通知ID"),
        current_user: User = Depends(get_current_active_user),
    ):
        """
        删除通知

        删除指定的通知。
        """
        from src.task_management.models import Notification

        notification = (
            await notification_service.db.query(Notification)
            .filter(
                and_(
                    Notification.id == str(notification_id),
                    Notification.user_id == str(current_user.id),
                )
            )
            .first()
        )

        if not notification:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="通知不存在")

        await notification_service.db.delete(notification)
        await notification_service.db.commit()

        return {"message": "通知已删除"}

    return router


# ===== 路由器工厂函数 =====


def create_all_routers() -> Dict[str, APIRouter]:
    """创建所有路由器的工厂函数"""

    # 注意：这里需要根据实际的依赖注入系统来创建服务实例
    # 这只是一个示例结构

    return {
        "tasks": create_task_router(None, None),  # 需要注入实际的服务实例
        "projects": create_project_router(None),
        "dashboard": create_dashboard_router(None, None),
        "notifications": create_notification_router(None),
    }
