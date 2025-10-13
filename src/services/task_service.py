"""
任务管理服务层
==============

实现完整的任务业务逻辑，包括：
- 任务CRUD操作
- 状态流转管理
- 分配和权限控制
- 批量操作
- 搜索和筛选
- 业务规则验证
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID, uuid4
import asyncio
from dataclasses import dataclass

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status
from pydantic import BaseModel, validator, Field

from src.task_management.models import (
    Task,
    TaskStatus,
    TaskPriority,
    TaskDependency,
    Project,
    ProjectMember,
    TaskActivity,
)
from src.repositories.task_repository import TaskRepository
from backend.core.cache import CacheManager


# === Pydantic 数据模型 ===


class TaskCreateRequest(BaseModel):
    """创建任务请求模型"""

    title: str = Field(..., min_length=1, max_length=200, description="任务标题")
    description: Optional[str] = Field(None, max_length=2000, description="任务描述")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="任务优先级")
    project_id: Optional[str] = Field(None, description="所属项目ID")
    assignee_id: Optional[str] = Field(None, description="分配者ID")
    due_date: Optional[datetime] = Field(None, description="截止日期")
    estimated_hours: Optional[int] = Field(None, ge=0, le=999, description="预估工时")
    tags: List[str] = Field(default_factory=list, description="任务标签")
    labels: Dict[str, Any] = Field(default_factory=dict, description="标签元数据")
    custom_fields: Dict[str, Any] = Field(default_factory=dict, description="自定义字段")

    @validator("due_date")
    def validate_due_date(cls, v):
        if v and v < datetime.utcnow():
            raise ValueError("截止日期不能早于当前时间")
        return v

    @validator("tags")
    def validate_tags(cls, v):
        if len(v) > 10:
            raise ValueError("标签数量不能超过10个")
        return [tag.strip() for tag in v if tag.strip()]

    class Config:
        schema_extra = {
            "example": {
                "title": "实现用户认证功能",
                "description": "实现JWT认证，包括登录、注册、密码重置功能",
                "priority": "high",
                "project_id": "123e4567-e89b-12d3-a456-426614174000",
                "assignee_id": "987fcdeb-51a2-43d1-9f12-123456789abc",
                "due_date": "2024-12-31T23:59:59",
                "estimated_hours": 8,
                "tags": ["backend", "authentication", "security"],
                "custom_fields": {"complexity": "medium", "epic": "user-management"},
            }
        }


class TaskUpdateRequest(BaseModel):
    """更新任务请求模型"""

    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    assignee_id: Optional[str] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[int] = Field(None, ge=0, le=999)
    actual_hours: Optional[int] = Field(None, ge=0, le=999)
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    tags: Optional[List[str]] = None
    labels: Optional[Dict[str, Any]] = None
    custom_fields: Optional[Dict[str, Any]] = None

    @validator("due_date")
    def validate_due_date(cls, v):
        if v and v < datetime.utcnow():
            raise ValueError("截止日期不能早于当前时间")
        return v

    @validator("tags")
    def validate_tags(cls, v):
        if v and len(v) > 10:
            raise ValueError("标签数量不能超过10个")
        return [tag.strip() for tag in v if tag.strip()] if v else None


class TaskSearchRequest(BaseModel):
    """任务搜索请求模型"""

    query: Optional[str] = Field(None, description="搜索关键词")
    status: Optional[List[TaskStatus]] = Field(None, description="状态筛选")
    priority: Optional[List[TaskPriority]] = Field(None, description="优先级筛选")
    assignee_id: Optional[str] = Field(None, description="分配者筛选")
    project_id: Optional[str] = Field(None, description="项目筛选")
    tags: Optional[List[str]] = Field(None, description="标签筛选")
    due_date_from: Optional[datetime] = Field(None, description="截止日期起始")
    due_date_to: Optional[datetime] = Field(None, description="截止日期结束")
    created_by: Optional[str] = Field(None, description="创建者筛选")
    sort_by: str = Field("updated_at", description="排序字段")
    sort_order: str = Field("desc", description="排序方向", regex="^(asc|desc)$")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页大小")

    @validator("due_date_to")
    def validate_date_range(cls, v, values):
        if v and values.get("due_date_from") and v < values["due_date_from"]:
            raise ValueError("结束日期不能早于开始日期")
        return v


class TaskResponse(BaseModel):
    """任务响应模型"""

    id: str
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    assignee_id: Optional[str]
    assignee_name: Optional[str]
    project_id: Optional[str]
    project_name: Optional[str]
    creator_id: str
    creator_name: Optional[str]
    due_date: Optional[datetime]
    estimated_hours: Optional[int]
    actual_hours: Optional[int]
    progress_percentage: int
    tags: List[str]
    labels: Dict[str, Any]
    custom_fields: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    is_overdue: bool
    dependencies_count: int
    comments_count: int
    attachments_count: int

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """任务列表响应模型"""

    tasks: List[TaskResponse]
    pagination: Dict[str, Any]
    filters_applied: Dict[str, Any]
    summary: Dict[str, Any]


class BulkOperationRequest(BaseModel):
    """批量操作请求模型"""

    task_ids: List[str] = Field(..., min_items=1, max_items=100, description="任务ID列表")
    operation: str = Field(
        ..., description="操作类型", regex="^(update|delete|assign|change_status)$"
    )
    data: Dict[str, Any] = Field(default_factory=dict, description="操作数据")

    @validator("task_ids")
    def validate_task_ids(cls, v):
        if len(set(v)) != len(v):
            raise ValueError("任务ID列表包含重复项")
        return v


# === 业务逻辑服务类 ===


@dataclass
class TaskServiceConfig:
    """任务服务配置"""

    max_tasks_per_user: int = 1000
    max_bulk_operation_size: int = 100
    default_cache_ttl: int = 300  # 5分钟
    enable_activity_logging: bool = True
    enable_notifications: bool = True


class TaskService:
    """
    任务管理服务
    ============

    提供完整的任务管理业务逻辑：
    - 任务CRUD操作
    - 状态流转管理
    - 权限控制
    - 搜索筛选
    - 批量操作
    - 统计分析
    """

    def __init__(
        self,
        db: Session,
        task_repository: TaskRepository,
        cache_manager: Optional[CacheManager] = None,
        config: Optional[TaskServiceConfig] = None,
    ):
        self.db = db
        self.repository = task_repository
        self.cache = cache_manager
        self.config = config or TaskServiceConfig()

    # === 基础CRUD操作 ===

    async def create_task(
        self, request: TaskCreateRequest, creator_id: str
    ) -> TaskResponse:
        """
        创建新任务

        Args:
            request: 创建任务请求
            creator_id: 创建者ID

        Returns:
            创建的任务响应

        Raises:
            HTTPException: 验证失败或权限不足
        """
        # 1. 业务规则验证
        await self._validate_task_creation(request, creator_id)

        # 2. 检查用户任务数量限制
        user_task_count = await self.repository.count_user_tasks(creator_id)
        if user_task_count >= self.config.max_tasks_per_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"用户任务数量已达上限({self.config.max_tasks_per_user})",
            )

        # 3. 创建任务对象
        task_data = {
            "id": str(uuid4()),
            "title": request.title,
            "description": request.description,
            "priority": request.priority.value,
            "project_id": request.project_id,
            "assignee_id": request.assignee_id,
            "due_date": request.due_date,
            "estimated_hours": request.estimated_hours,
            "tags": request.tags,
            "labels": request.labels,
            "custom_fields": request.custom_fields,
            "created_by": creator_id,
            "status": TaskStatus.TODO.value,
            "progress_percentage": 0,
        }

        # 4. 处理分配信息
        if request.assignee_id:
            task_data.update(
                {"assigned_at": datetime.utcnow(), "assigned_by": creator_id}
            )

        # 5. 保存到数据库
        task = await self.repository.create(task_data)

        # 6. 记录活动日志
        if self.config.enable_activity_logging:
            await self._log_task_activity(
                task_id=task.id,
                user_id=creator_id,
                action="created",
                description=f"创建任务: {task.title}",
            )

        # 7. 发送通知
        if self.config.enable_notifications and request.assignee_id:
            await self._send_task_assigned_notification(
                task_id=task.id, assignee_id=request.assignee_id, assigner_id=creator_id
            )

        # 8. 清除相关缓存
        await self._invalidate_caches(task)

        return await self._build_task_response(task)

    async def get_task(
        self, task_id: str, user_id: str, include_relations: bool = True
    ) -> Optional[TaskResponse]:
        """
        获取任务详情

        Args:
            task_id: 任务ID
            user_id: 用户ID
            include_relations: 是否包含关联数据

        Returns:
            任务响应或None
        """
        # 1. 检查缓存
        if self.cache:
            cache_key = f"task:{task_id}:user:{user_id}"
            cached_response = await self.cache.get(cache_key)
            if cached_response:
                return TaskResponse.parse_obj(cached_response)

        # 2. 从数据库获取
        task = await self.repository.get_by_id_with_relations(
            task_id=task_id,
            include_comments=include_relations,
            include_attachments=include_relations,
            include_activities=include_relations,
        )

        if not task:
            return None

        # 3. 权限检查
        if not await self._check_task_access_permission(task, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="没有访问此任务的权限"
            )

        # 4. 构建响应
        response = await self._build_task_response(task)

        # 5. 缓存结果
        if self.cache:
            await self.cache.set(
                cache_key, response.dict(), ttl=self.config.default_cache_ttl
            )

        return response

    async def update_task(
        self, task_id: str, request: TaskUpdateRequest, user_id: str
    ) -> TaskResponse:
        """
        更新任务

        Args:
            task_id: 任务ID
            request: 更新请求
            user_id: 操作用户ID

        Returns:
            更新后的任务响应
        """
        # 1. 获取现有任务
        task = await self.repository.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")

        # 2. 权限检查
        if not await self._check_task_edit_permission(task, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="没有编辑此任务的权限"
            )

        # 3. 构建更新数据
        update_data = {}
        changes = []

        for field, value in request.dict(exclude_unset=True).items():
            if hasattr(task, field):
                old_value = getattr(task, field)
                if old_value != value:
                    update_data[field] = value
                    changes.append(
                        {
                            "field": field,
                            "old_value": str(old_value) if old_value else None,
                            "new_value": str(value) if value else None,
                        }
                    )

        if not update_data:
            return await self._build_task_response(task)

        # 4. 特殊字段处理
        if "status" in update_data:
            await self._validate_status_transition(task, update_data["status"])
            await self._handle_status_change(task, update_data["status"], user_id)

        if "assignee_id" in update_data:
            await self._handle_assignee_change(
                task, update_data["assignee_id"], user_id
            )

        # 5. 更新数据库
        updated_task = await self.repository.update(task_id, update_data)

        # 6. 记录活动日志
        if self.config.enable_activity_logging:
            for change in changes:
                await self._log_task_activity(
                    task_id=task_id,
                    user_id=user_id,
                    action="updated",
                    field_name=change["field"],
                    old_value=change["old_value"],
                    new_value=change["new_value"],
                )

        # 7. 清除缓存
        await self._invalidate_caches(updated_task)

        return await self._build_task_response(updated_task)

    async def delete_task(
        self, task_id: str, user_id: str, hard_delete: bool = False
    ) -> bool:
        """
        删除任务

        Args:
            task_id: 任务ID
            user_id: 操作用户ID
            hard_delete: 是否硬删除

        Returns:
            删除是否成功
        """
        # 1. 获取任务
        task = await self.repository.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")

        # 2. 权限检查
        if not await self._check_task_delete_permission(task, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="没有删除此任务的权限"
            )

        # 3. 检查依赖关系
        dependencies = await self.repository.get_task_dependencies(task_id)
        if dependencies["dependents"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="无法删除被其他任务依赖的任务"
            )

        # 4. 执行删除
        if hard_delete:
            success = await self.repository.hard_delete(task_id)
        else:
            success = await self.repository.soft_delete(task_id)

        if success:
            pass  # Auto-fixed empty block
            # 5. 记录活动日志
            if self.config.enable_activity_logging:
                await self._log_task_activity(
                    task_id=task_id,
                    user_id=user_id,
                    action="deleted",
                    description=f"删除任务: {task.title}",
                )

            # 6. 清除缓存
            await self._invalidate_caches(task)

        return success

    # === 高级功能 ===

    async def search_tasks(
        self, request: TaskSearchRequest, user_id: str
    ) -> TaskListResponse:
        """
        搜索和筛选任务

        Args:
            request: 搜索请求
            user_id: 用户ID

        Returns:
            任务列表响应
        """
        # 1. 构建筛选条件
        filters = {}
        if request.status:
            filters["status"] = [s.value for s in request.status]
        if request.priority:
            filters["priority"] = [p.value for p in request.priority]
        if request.assignee_id:
            filters["assignee_id"] = request.assignee_id
        if request.project_id:
            filters["project_id"] = request.project_id
        if request.tags:
            filters["tags"] = request.tags
        if request.due_date_from:
            filters["due_date_from"] = request.due_date_from
        if request.due_date_to:
            filters["due_date_to"] = request.due_date_to
        if request.created_by:
            filters["created_by"] = request.created_by

        # 2. 执行搜索
        if request.query:
            pass  # Auto-fixed empty block
            # 全文搜索
            tasks = await self.repository.search_with_fulltext(
                query_text=request.query,
                user_id=user_id,
                filters=filters,
                limit=request.page_size,
            )
            total_count = len(tasks)  # 简化处理，实际应该单独查询总数
        else:
            pass  # Auto-fixed empty block
            # 普通筛选
            result = await self.repository.search_tasks(
                user_id=user_id,
                filters=filters,
                sort_by=request.sort_by,
                sort_order=request.sort_order,
                page=request.page,
                page_size=request.page_size,
            )
            tasks = result["tasks"]
            total_count = result["total_count"]

        # 3. 构建响应
        task_responses = []
        for task in tasks:
            task_responses.append(await self._build_task_response(task))

        # 4. 构建分页信息
        pagination = {
            "page": request.page,
            "page_size": request.page_size,
            "total_count": total_count,
            "total_pages": (total_count + request.page_size - 1) // request.page_size,
        }

        # 5. 构建摘要信息
        summary = await self._build_search_summary(tasks)

        return TaskListResponse(
            tasks=task_responses,
            pagination=pagination,
            filters_applied=filters,
            summary=summary,
        )

    async def bulk_operation(
        self, request: BulkOperationRequest, user_id: str
    ) -> Dict[str, Any]:
        """
        批量操作任务

        Args:
            request: 批量操作请求
            user_id: 操作用户ID

        Returns:
            操作结果
        """
        if len(request.task_ids) > self.config.max_bulk_operation_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"批量操作任务数量不能超过{self.config.max_bulk_operation_size}",
            )

        # 1. 获取所有任务
        tasks = await self.repository.get_multiple_by_ids(request.task_ids)
        found_ids = {str(task.id) for task in tasks}
        missing_ids = set(request.task_ids) - found_ids

        if missing_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"以下任务不存在: {', '.join(missing_ids)}",
            )

        # 2. 权限检查
        permission_errors = []
        for task in tasks:
            if not await self._check_task_edit_permission(task, user_id):
                permission_errors.append(str(task.id))

        if permission_errors:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"没有编辑以下任务的权限: {', '.join(permission_errors)}",
            )

        # 3. 执行批量操作
        results = {
            "success_count": 0,
            "failed_count": 0,
            "errors": [],
            "updated_tasks": [],
        }

        for task in tasks:
            try:
                if request.operation == "update":
                    updated_task = await self.repository.update(
                        str(task.id), request.data
                    )
                    results["updated_tasks"].append(str(updated_task.id))
                    results["success_count"] += 1
                elif request.operation == "delete":
                    success = await self.repository.soft_delete(str(task.id))
                    if success:
                        results["success_count"] += 1
                    else:
                        results["failed_count"] += 1
                elif request.operation == "assign":
                    if "assignee_id" in request.data:
                        update_data = {
                            "assignee_id": request.data["assignee_id"],
                            "assigned_at": datetime.utcnow(),
                            "assigned_by": user_id,
                        }
                        updated_task = await self.repository.update(
                            str(task.id), update_data
                        )
                        results["updated_tasks"].append(str(updated_task.id))
                        results["success_count"] += 1
                elif request.operation == "change_status":
                    if "status" in request.data:
                        updated_task = await self.repository.update(
                            str(task.id), {"status": request.data["status"]}
                        )
                        results["updated_tasks"].append(str(updated_task.id))
                        results["success_count"] += 1

                # 记录活动日志
                if self.config.enable_activity_logging:
                    await self._log_task_activity(
                        task_id=str(task.id),
                        user_id=user_id,
                        action=f"bulk_{request.operation}",
                        description=f"批量{request.operation}操作",
                    )

            except Exception as e:
                results["failed_count"] += 1
                results["errors"].append({"task_id": str(task.id), "error": str(e)})

        # 4. 清除缓存
        for task in tasks:
            await self._invalidate_caches(task)

        return results

    async def change_task_status(
        self,
        task_id: str,
        new_status: TaskStatus,
        user_id: str,
        comment: Optional[str] = None,
    ) -> TaskResponse:
        """
        更改任务状态

        Args:
            task_id: 任务ID
            new_status: 新状态
            user_id: 操作用户ID
            comment: 状态变更说明

        Returns:
            更新后的任务响应
        """
        # 1. 获取任务
        task = await self.repository.get_by_id(task_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")

        # 2. 权限检查
        if not await self._check_task_edit_permission(task, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="没有编辑此任务的权限"
            )

        # 3. 验证状态转换
        await self._validate_status_transition(task, new_status.value)

        # 4. 准备更新数据
        old_status = task.status
        update_data = {"status": new_status.value}

        # 根据状态设置相关字段
        if new_status == TaskStatus.IN_PROGRESS and not task.started_at:
            update_data["started_at"] = datetime.utcnow()
        elif new_status == TaskStatus.DONE:
            update_data["completed_at"] = datetime.utcnow()
            update_data["progress_percentage"] = 100

        # 5. 更新任务
        updated_task = await self.repository.update(task_id, update_data)

        # 6. 记录活动日志
        if self.config.enable_activity_logging:
            await self._log_task_activity(
                task_id=task_id,
                user_id=user_id,
                action="status_changed",
                field_name="status",
                old_value=old_status,
                new_value=new_status.value,
                description=comment or f"状态从 {old_status} 变更为 {new_status.value}",
            )

        # 7. 发送通知
        if self.config.enable_notifications:
            await self._send_status_changed_notification(
                task_id=task_id,
                old_status=old_status,
                new_status=new_status.value,
                changed_by=user_id,
            )

        # 8. 清除缓存
        await self._invalidate_caches(updated_task)

        return await self._build_task_response(updated_task)

    # === 统计和分析 ===

    async def get_user_task_summary(self, user_id: str) -> Dict[str, Any]:
        """获取用户任务概览统计"""
        if self.cache:
            cache_key = f"user_task_summary:{user_id}"
            cached_summary = await self.cache.get(cache_key)
            if cached_summary:
                return cached_summary

        summary = await self.repository.get_user_workload(user_id)

        if self.cache:
            await self.cache.set(cache_key, summary, ttl=60)  # 缓存1分钟

        return summary

    async def get_project_task_statistics(
        self, project_id: str, user_id: str
    ) -> Dict[str, Any]:
        """获取项目任务统计"""
        # 检查项目访问权限
        if not await self._check_project_access(project_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="没有项目访问权限"
            )

        return await self.repository.get_task_statistics(project_id=project_id)

    # === 私有辅助方法 ===

    async def _validate_task_creation(
        self, request: TaskCreateRequest, creator_id: str
    ):
        """验证任务创建数据"""
        # 验证项目权限
        if request.project_id:
            if not await self._check_project_access(request.project_id, creator_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="没有项目权限"
                )

        # 验证分配者权限
        if request.assignee_id:
            if not await self._check_user_exists_and_active(request.assignee_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="指定的分配者不存在或不可用"
                )

    async def _validate_status_transition(self, task: Task, new_status: str):
        """验证状态转换"""
        if not task.can_transition_to(new_status):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无法从 {task.status} 转换到 {new_status}",
            )

    async def _check_task_access_permission(self, task: Task, user_id: str) -> bool:
        """检查任务访问权限"""
        # 创建者、分配者或项目成员可以访问
        if task.created_by == user_id or task.assignee_id == user_id:
            return True

        if task.project_id:
            return await self._check_project_access(task.project_id, user_id)

        return False

    async def _check_task_edit_permission(self, task: Task, user_id: str) -> bool:
        """检查任务编辑权限"""
        return await self._check_task_access_permission(task, user_id)

    async def _check_task_delete_permission(self, task: Task, user_id: str) -> bool:
        """检查任务删除权限"""
        # 只有创建者或项目管理员可以删除
        if task.created_by == user_id:
            return True

        if task.project_id:
            return await self._check_project_admin_access(task.project_id, user_id)

        return False

    async def _check_project_access(self, project_id: str, user_id: str) -> bool:
        """检查项目访问权限"""
        member = (
            await self.db.query(ProjectMember)
            .filter(
                and_(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == user_id,
                )
            )
            .first()
        )
        return member is not None

    async def _check_project_admin_access(self, project_id: str, user_id: str) -> bool:
        """检查项目管理员权限"""
        member = (
            await self.db.query(ProjectMember)
            .filter(
                and_(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == user_id,
                    ProjectMember.role.in_(["owner", "admin"]),
                )
            )
            .first()
        )
        return member is not None

    async def _check_user_exists_and_active(self, user_id: str) -> bool:
        """检查用户是否存在且活跃"""
        # 这里应该查询用户表，简化实现
        return True

    async def _handle_status_change(self, task: Task, new_status: str, user_id: str):
        """处理状态变更的副作用"""
        if new_status == TaskStatus.IN_PROGRESS.value and not task.started_at:
            task.started_at = datetime.utcnow()
        elif new_status == TaskStatus.DONE.value:
            task.completed_at = datetime.utcnow()
            task.progress_percentage = 100

    async def _handle_assignee_change(
        self, task: Task, new_assignee_id: str, user_id: str
    ):
        """处理分配者变更"""
        if new_assignee_id != task.assignee_id:
            task.assigned_at = datetime.utcnow()
            task.assigned_by = user_id

    async def _build_task_response(self, task: Task) -> TaskResponse:
        """构建任务响应对象"""
        # 获取相关数据
        dependencies_count = len(
            (await self.repository.get_task_dependencies(str(task.id)))["dependencies"]
        )

        return TaskResponse(
            id=str(task.id),
            title=task.title,
            description=task.description,
            status=TaskStatus(task.status),
            priority=TaskPriority(task.priority),
            assignee_id=str(task.assignee_id) if task.assignee_id else None,
            assignee_name=task.assignee.first_name + " " + task.assignee.last_name
            if task.assignee
            else None,
            project_id=str(task.project_id) if task.project_id else None,
            project_name=task.project.name if task.project else None,
            creator_id=str(task.created_by),
            creator_name=task.creator.first_name + " " + task.creator.last_name
            if task.creator
            else None,
            due_date=task.due_date,
            estimated_hours=task.estimated_hours,
            actual_hours=task.actual_hours,
            progress_percentage=task.progress_percentage or 0,
            tags=task.tags or [],
            labels=task.labels or {},
            custom_fields=task.custom_fields or {},
            created_at=task.created_at,
            updated_at=task.updated_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            is_overdue=task.is_overdue,
            dependencies_count=dependencies_count,
            comments_count=len(task.comments)
            if hasattr(task, "comments") and task.comments
            else 0,
            attachments_count=len(task.attachments)
            if hasattr(task, "attachments") and task.attachments
            else 0,
        )

    async def _build_search_summary(self, tasks: List[Task]) -> Dict[str, Any]:
        """构建搜索结果摘要"""
        if not tasks:
            return {
                "total_count": 0,
                "status_distribution": {},
                "priority_distribution": {},
                "overdue_count": 0,
            }

        status_counts = {}
        priority_counts = {}
        overdue_count = 0

        for task in tasks:
            pass  # Auto-fixed empty block
            # 状态统计
            status_counts[task.status] = status_counts.get(task.status, 0) + 1

            # 优先级统计
            priority_counts[task.priority] = priority_counts.get(task.priority, 0) + 1

            # 逾期统计
            if task.is_overdue:
                overdue_count += 1

        return {
            "total_count": len(tasks),
            "status_distribution": status_counts,
            "priority_distribution": priority_counts,
            "overdue_count": overdue_count,
        }

    async def _log_task_activity(
        self,
        task_id: str,
        user_id: str,
        action: str,
        field_name: Optional[str] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        description: Optional[str] = None,
    ):
        """记录任务活动日志"""
        activity = TaskActivity(
            task_id=task_id,
            user_id=user_id,
            action=action,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            description=description,
        )

        self.db.add(activity)
        await self.db.commit()

    async def _send_task_assigned_notification(
        self, task_id: str, assignee_id: str, assigner_id: str
    ):
        """发送任务分配通知"""
        # 这里应该集成通知服务
        pass

    async def _send_status_changed_notification(
        self, task_id: str, old_status: str, new_status: str, changed_by: str
    ):
        """发送状态变更通知"""
        # 这里应该集成通知服务
        pass

    async def _invalidate_caches(self, task: Task):
        """清除任务相关缓存"""
        if not self.cache:
            return

        # 清除任务缓存
        await self.cache.delete(f"task:{task.id}:*")

        # 清除用户任务概览缓存
        if task.assignee_id:
            await self.cache.delete(f"user_task_summary:{task.assignee_id}")
        if task.created_by:
            await self.cache.delete(f"user_task_summary:{task.created_by}")

        # 清除项目缓存
        if task.project_id:
            await self.cache.delete(f"project_stats:{task.project_id}")
