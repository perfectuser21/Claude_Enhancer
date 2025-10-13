"""
任务管理系统服务层
==================

实现完整的业务逻辑层，包括：
- TaskService: 任务管理服务
- ProjectService: 项目管理服务
- NotificationService: 通知服务
- ActivityService: 活动记录服务
- FileService: 文件管理服务
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
import asyncio

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
from fastapi import HTTPException, status, UploadFile

from src.repositories.base_repository import BaseRepository
from src.task_management.models import (
    Task,
    TaskStatus,
    TaskPriority,
    TaskDependency,
    Project,
    ProjectStatus,
    ProjectMember,
    MemberRole,
    TaskComment,
    TaskAttachment,
    TaskActivity,
    Notification,
    Team,
)
from backend.services.notification_service import (
    NotificationService as BaseNotificationService,
)
from backend.core.cache import CacheManager


class TaskService:
    """
    任务管理服务
    ============

    提供完整的任务管理功能：
    - 任务CRUD操作
    - 状态流转管理
    - 分配和权限控制
    - 依赖关系管理
    - 搜索和筛选
    - 批量操作
    """

    def __init__(
        self,
        db: Session,
        cache_manager: CacheManager,
        notification_service: "NotificationService",
        activity_service: "ActivityService",
    ):
        self.db = db
        self.cache = cache_manager
        self.notification_service = notification_service
        self.activity_service = activity_service

    async def create_task(
        self, task_data: Dict[str, Any], creator_id: str, notify_assignee: bool = True
    ) -> Task:
        """
        创建新任务

        Args:
            task_data: 任务数据
            creator_id: 创建者ID
            notify_assignee: 是否通知分配者

        Returns:
            创建的任务对象

        Raises:
            HTTPException: 验证失败或权限不足
        """
        # 1. 数据验证
        await self._validate_task_creation(task_data, creator_id)

        # 2. 创建任务对象
        task = Task(
            title=task_data["title"],
            description=task_data.get("description"),
            priority=task_data.get("priority", TaskPriority.MEDIUM.value),
            project_id=task_data.get("project_id"),
            assignee_id=task_data.get("assignee_id"),
            due_date=task_data.get("due_date"),
            estimated_hours=task_data.get("estimated_hours"),
            tags=task_data.get("tags", []),
            labels=task_data.get("labels", {}),
            custom_fields=task_data.get("custom_fields", {}),
            created_by=creator_id,
        )

        # 3. 处理分配信息
        if task.assignee_id:
            task.assigned_at = datetime.utcnow()
            task.assigned_by = creator_id

        # 4. 保存到数据库
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)

        # 5. 记录活动
        await self.activity_service.log_task_activity(
            task_id=str(task.id),
            user_id=creator_id,
            action="created",
            description=f"创建任务: {task.title}",
        )

        # 6. 发送通知
        if notify_assignee and task.assignee_id:
            await self.notification_service.send_task_assigned_notification(
                task_id=str(task.id),
                assignee_id=task.assignee_id,
                assigner_id=creator_id,
            )

        # 7. 清除相关缓存
        await self._invalidate_task_caches(task)

        return task

    async def update_task(
        self, task_id: str, update_data: Dict[str, Any], user_id: str
    ) -> Task:
        """
        更新任务

        Args:
            task_id: 任务ID
            update_data: 更新数据
            user_id: 操作用户ID

        Returns:
            更新后的任务对象
        """
        # 1. 获取现有任务
        task = await self.get_task_by_id(task_id, user_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")

        # 2. 权限检查
        await self._check_task_edit_permission(task, user_id)

        # 3. 记录变更
        changes = []
        for field, new_value in update_data.items():
            if hasattr(task, field):
                old_value = getattr(task, field)
                if old_value != new_value:
                    changes.append(
                        {
                            "field": field,
                            "old_value": str(old_value) if old_value else None,
                            "new_value": str(new_value) if new_value else None,
                        }
                    )
                    setattr(task, field, new_value)

        # 4. 特殊字段处理
        if "status" in update_data:
            await self._handle_status_change(task, update_data["status"], user_id)

        if "assignee_id" in update_data:
            await self._handle_assignee_change(
                task, update_data["assignee_id"], user_id
            )

        # 5. 更新时间戳
        task.updated_at = datetime.utcnow()

        # 6. 保存变更
        await self.db.commit()
        await self.db.refresh(task)

        # 7. 记录活动
        for change in changes:
            await self.activity_service.log_task_activity(
                task_id=task_id,
                user_id=user_id,
                action="updated",
                field_name=change["field"],
                old_value=change["old_value"],
                new_value=change["new_value"],
            )

        # 8. 清除缓存
        await self._invalidate_task_caches(task)

        return task

    async def update_task_status(
        self, task_id: str, new_status: str, user_id: str, comment: Optional[str] = None
    ) -> Task:
        """
        更新任务状态

        Args:
            task_id: 任务ID
            new_status: 新状态
            user_id: 操作用户ID
            comment: 状态变更说明

        Returns:
            更新后的任务对象
        """
        task = await self.get_task_by_id(task_id, user_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")

        # 验证状态转换
        if not task.can_transition_to(new_status):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"无法从 {task.status} 转换到 {new_status}",
            )

        old_status = task.status

        # 更新状态相关字段
        task.status = new_status
        task.update_progress_from_status()

        if new_status == TaskStatus.IN_PROGRESS.value and not task.started_at:
            task.started_at = datetime.utcnow()
        elif new_status == TaskStatus.DONE.value:
            task.completed_at = datetime.utcnow()
            task.progress_percentage = 100

        await self.db.commit()

        # 记录活动
        await self.activity_service.log_task_activity(
            task_id=task_id,
            user_id=user_id,
            action="status_changed",
            field_name="status",
            old_value=old_status,
            new_value=new_status,
            description=comment,
        )

        # 发送通知
        await self.notification_service.send_task_status_changed_notification(
            task_id=task_id,
            old_status=old_status,
            new_status=new_status,
            changed_by=user_id,
        )

        await self._invalidate_task_caches(task)
        return task

    async def assign_task(
        self, task_id: str, assignee_id: str, assigner_id: str
    ) -> Task:
        """分配任务"""
        task = await self.get_task_by_id(task_id, assigner_id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")

        # 检查分配权限
        await self._check_assignment_permission(task, assigner_id, assignee_id)

        old_assignee_id = task.assignee_id

        # 更新分配信息
        task.assignee_id = assignee_id
        task.assigned_at = datetime.utcnow()
        task.assigned_by = assigner_id

        await self.db.commit()

        # 记录活动
        await self.activity_service.log_task_activity(
            task_id=task_id,
            user_id=assigner_id,
            action="assigned",
            old_value=str(old_assignee_id) if old_assignee_id else None,
            new_value=str(assignee_id),
        )

        # 发送通知
        await self.notification_service.send_task_assigned_notification(
            task_id=task_id, assignee_id=assignee_id, assigner_id=assigner_id
        )

        await self._invalidate_task_caches(task)
        return task

    async def search_tasks(
        self,
        user_id: str,
        query: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        搜索和筛选任务

        Args:
            user_id: 用户ID
            query: 搜索关键词
            filters: 筛选条件
            sort_by: 排序字段
            sort_order: 排序方向
            page: 页码
            page_size: 每页大小

        Returns:
            包含任务列表和分页信息的字典
        """
        # 构建基础查询
        base_query = self.db.query(Task).filter(
            and_(Task.is_deleted == False, self._build_user_access_filter(user_id))
        )

        # 应用搜索条件
        if query:
            search_filter = or_(
                Task.title.ilike(f"%{query}%"),
                Task.description.ilike(f"%{query}%"),
                Task.tags.op("&&")(func.array([query])),  # 标签搜索
            )
            base_query = base_query.filter(search_filter)

        # 应用筛选条件
        if filters:
            base_query = self._apply_task_filters(base_query, filters)

        # 计算总数
        total_count = await base_query.count()

        # 应用排序
        if hasattr(Task, sort_by):
            order_column = getattr(Task, sort_by)
            if sort_order.lower() == "desc":
                order_column = order_column.desc()
            base_query = base_query.order_by(order_column)

        # 应用分页
        offset = (page - 1) * page_size
        tasks = await base_query.offset(offset).limit(page_size).all()

        return {
            "tasks": tasks,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "total_pages": (total_count + page_size - 1) // page_size,
            },
        }

    async def get_task_by_id(
        self, task_id: str, user_id: str, include_relations: bool = True
    ) -> Optional[Task]:
        """获取任务详情"""
        # 先尝试从缓存获取
        cache_key = f"task:{task_id}"
        cached_task = await self.cache.get(cache_key)

        if cached_task and not include_relations:
            return cached_task

        # 从数据库查询
        query = self.db.query(Task).filter(
            and_(
                Task.id == task_id,
                Task.is_deleted == False,
                self._build_user_access_filter(user_id),
            )
        )

        if include_relations:
            query = query.options(
                joinedload(Task.assignee),
                joinedload(Task.project),
                selectinload(Task.comments),
                selectinload(Task.attachments),
            )

        task = await query.first()

        # 缓存结果
        if task:
            await self.cache.set(cache_key, task, ttl=300)  # 5分钟缓存

        return task

    async def get_user_tasks_summary(self, user_id: str) -> Dict[str, Any]:
        """获取用户任务概览"""
        cache_key = f"user_tasks_summary:{user_id}"
        cached_summary = await self.cache.get(cache_key)

        if cached_summary:
            return cached_summary

        # 构建查询
        user_tasks_filter = or_(Task.assignee_id == user_id, Task.created_by == user_id)

        base_query = self.db.query(Task).filter(
            and_(Task.is_deleted == False, user_tasks_filter)
        )

        # 按状态统计
        status_counts = {}
        for status in TaskStatus:
            count = await base_query.filter(Task.status == status.value).count()
            status_counts[status.value] = count

        # 逾期任务数
        overdue_count = await base_query.filter(
            and_(
                Task.due_date < datetime.utcnow(),
                Task.status.notin_([TaskStatus.DONE.value, TaskStatus.CANCELLED.value]),
            )
        ).count()

        # 今日到期任务数
        today_end = datetime.utcnow().replace(hour=23, minute=59, second=59)
        today_due_count = await base_query.filter(
            and_(
                Task.due_date <= today_end,
                Task.due_date >= datetime.utcnow().replace(hour=0, minute=0, second=0),
                Task.status.notin_([TaskStatus.DONE.value, TaskStatus.CANCELLED.value]),
            )
        ).count()

        summary = {
            "status_counts": status_counts,
            "overdue_count": overdue_count,
            "today_due_count": today_due_count,
            "total_count": sum(status_counts.values()),
        }

        # 缓存1分钟
        await self.cache.set(cache_key, summary, ttl=60)

        return summary

    async def bulk_update_tasks(
        self, task_ids: List[str], update_data: Dict[str, Any], user_id: str
    ) -> List[Task]:
        """批量更新任务"""
        # 获取所有任务
        tasks = (
            await self.db.query(Task)
            .filter(
                and_(
                    Task.id.in_(task_ids),
                    Task.is_deleted == False,
                    self._build_user_access_filter(user_id),
                )
            )
            .all()
        )

        if len(tasks) != len(task_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="部分任务不存在或无权限访问"
            )

        updated_tasks = []
        for task in tasks:
            pass  # Auto-fixed empty block
            # 检查编辑权限
            await self._check_task_edit_permission(task, user_id)

            # 应用更新
            for field, value in update_data.items():
                if hasattr(task, field):
                    setattr(task, field, value)

            task.updated_at = datetime.utcnow()
            updated_tasks.append(task)

        await self.db.commit()

        # 批量记录活动
        for task in updated_tasks:
            await self.activity_service.log_task_activity(
                task_id=str(task.id),
                user_id=user_id,
                action="bulk_updated",
                description="批量更新任务",
            )

        # 清除缓存
        for task in updated_tasks:
            await self._invalidate_task_caches(task)

        return updated_tasks

    # === 私有方法 ===
    async def _validate_task_creation(self, task_data: Dict[str, Any], creator_id: str):
        """验证任务创建数据"""
        # 验证必填字段
        if not task_data.get("title"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="任务标题不能为空"
            )

        # 验证项目权限
        if task_data.get("project_id"):
            has_permission = await self._check_project_permission(
                task_data["project_id"], creator_id
            )
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN, detail="没有项目权限"
                )

        # 验证分配者权限
        if task_data.get("assignee_id"):
            can_assign = await self._check_assignment_permission_user(
                task_data["assignee_id"], creator_id
            )
            if not can_assign:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="无法分配给指定用户"
                )

    def _build_user_access_filter(self, user_id: str):
        """构建用户访问权限过滤条件"""
        return or_(
            Task.created_by == user_id,
            Task.assignee_id == user_id,
            Task.project_id.in_(
                self.db.query(ProjectMember.project_id)
                .filter(ProjectMember.user_id == user_id)
                .subquery()
            ),
        )

    def _apply_task_filters(self, query, filters: Dict[str, Any]):
        """应用任务筛选条件"""
        for key, value in filters.items():
            if value is None:
                continue

            if key == "status" and isinstance(value, list):
                query = query.filter(Task.status.in_(value))
            elif key == "priority" and isinstance(value, list):
                query = query.filter(Task.priority.in_(value))
            elif key == "assignee_id":
                query = query.filter(Task.assignee_id == value)
            elif key == "project_id":
                query = query.filter(Task.project_id == value)
            elif key == "due_date_from":
                query = query.filter(Task.due_date >= value)
            elif key == "due_date_to":
                query = query.filter(Task.due_date <= value)
            elif key == "tags" and isinstance(value, list):
                query = query.filter(Task.tags.op("&&")(value))

        return query

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

    async def _check_task_edit_permission(self, task: Task, user_id: str) -> bool:
        """检查任务编辑权限"""
        # 创建者、分配者或项目成员可以编辑
        if task.created_by == user_id or task.assignee_id == user_id:
            return True

        if task.project_id:
            return await self._check_project_permission(str(task.project_id), user_id)

        return False

    async def _check_project_permission(self, project_id: str, user_id: str) -> bool:
        """检查项目权限"""
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

    async def _check_assignment_permission(
        self, task: Task, assigner_id: str, assignee_id: str
    ) -> bool:
        """检查分配权限"""
        # 检查分配者权限
        if not await self._check_task_edit_permission(task, assigner_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="没有分配权限")

        # 检查被分配者是否存在且可分配
        return await self._check_assignment_permission_user(assignee_id, assigner_id)

    async def _check_assignment_permission_user(
        self, assignee_id: str, assigner_id: str
    ) -> bool:
        """检查用户是否可被分配"""
        from backend.models.user import User

        user = (
            await self.db.query(User)
            .filter(and_(User.id == assignee_id, User.status == "active"))
            .first()
        )

        return user is not None

    async def _invalidate_task_caches(self, task: Task):
        """清除任务相关缓存"""
        # 清除任务缓存
        await self.cache.delete(f"task:{task.id}")

        # 清除用户任务概览缓存
        if task.assignee_id:
            await self.cache.delete(f"user_tasks_summary:{task.assignee_id}")
        if task.created_by:
            await self.cache.delete(f"user_tasks_summary:{task.created_by}")

        # 清除项目缓存
        if task.project_id:
            await self.cache.delete(f"project:{task.project_id}")


class ProjectService:
    """
    项目管理服务
    ============

    提供项目相关的所有业务逻辑
    """

    def __init__(
        self,
        db: Session,
        cache_manager: CacheManager,
        notification_service: "NotificationService",
    ):
        self.db = db
        self.cache = cache_manager
        self.notification_service = notification_service

    async def create_project(
        self, project_data: Dict[str, Any], creator_id: str
    ) -> Project:
        """创建项目"""
        project = Project(
            name=project_data["name"],
            description=project_data.get("description"),
            start_date=project_data.get("start_date"),
            end_date=project_data.get("end_date"),
            team_id=project_data.get("team_id"),
            settings=project_data.get("settings", {}),
            is_public=project_data.get("is_public", False),
            created_by=creator_id,
        )

        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)

        # 添加创建者为项目所有者
        project_member = ProjectMember(
            project_id=project.id, user_id=creator_id, role=MemberRole.OWNER.value
        )

        self.db.add(project_member)
        await self.db.commit()

        return project

    async def get_project_statistics(
        self, project_id: str, user_id: str
    ) -> Dict[str, Any]:
        """获取项目统计信息"""
        cache_key = f"project_stats:{project_id}"
        cached_stats = await self.cache.get(cache_key)

        if cached_stats:
            return cached_stats

        # 检查权限
        if not await self._check_project_access(project_id, user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="没有项目访问权限"
            )

        # 统计任务
        task_stats = await self.db.execute(
            text(
                """
            SELECT
                status,
                priority,
                COUNT(*) as count
            FROM tasks
            WHERE project_id = :project_id
                AND is_deleted = false
            GROUP BY status, priority
        """
            ),
            {"project_id": project_id},
        )

        # 处理统计结果
        stats = {
            "task_counts": {"total": 0, "by_status": {}, "by_priority": {}},
            "completion_rate": 0.0,
            "overdue_count": 0,
        }

        for row in task_stats.fetchall():
            stats["task_counts"]["total"] += row.count
            stats["task_counts"]["by_status"][row.status] = (
                stats["task_counts"]["by_status"].get(row.status, 0) + row.count
            )
            stats["task_counts"]["by_priority"][row.priority] = (
                stats["task_counts"]["by_priority"].get(row.priority, 0) + row.count
            )

        # 计算完成率
        completed_count = stats["task_counts"]["by_status"].get(
            TaskStatus.DONE.value, 0
        )
        total_count = stats["task_counts"]["total"]
        if total_count > 0:
            stats["completion_rate"] = (completed_count / total_count) * 100

        # 缓存5分钟
        await self.cache.set(cache_key, stats, ttl=300)

        return stats

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


class NotificationService:
    """
    通知服务
    ========

    管理系统通知的发送和处理
    """

    def __init__(self, db: Session, base_notification_service: BaseNotificationService):
        self.db = db
        self.base_service = base_notification_service

    async def send_task_assigned_notification(
        self, task_id: str, assignee_id: str, assigner_id: str
    ):
        """发送任务分配通知"""
        # 获取任务信息
        task = await self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return

        # 获取分配者信息
        from backend.models.user import User

        assigner = await self.db.query(User).filter(User.id == assigner_id).first()
        if not assigner:
            return

        # 创建通知
        notification = Notification(
            user_id=assignee_id,
            title="新任务分配",
            content=f"{assigner.first_name} {assigner.last_name} 为您分配了任务: {task.title}",
            type="task_assigned",
            related_entity_type="task",
            related_entity_id=task_id,
            action_url=f"/tasks/{task_id}",
        )

        self.db.add(notification)
        await self.db.commit()

        # 发送实时通知（WebSocket等）
        await self.base_service.send_realtime_notification(
            user_id=assignee_id,
            notification_data={
                "type": "task_assigned",
                "task_id": task_id,
                "task_title": task.title,
                "assigner_name": f"{assigner.first_name} {assigner.last_name}",
            },
        )

    async def send_task_status_changed_notification(
        self, task_id: str, old_status: str, new_status: str, changed_by: str
    ):
        """发送任务状态变更通知"""
        # 获取任务信息
        task = await self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return

        # 通知相关人员（创建者、分配者、项目成员等）
        notification_users = set()

        if task.created_by:
            notification_users.add(task.created_by)
        if task.assignee_id:
            notification_users.add(task.assignee_id)

        # 移除操作者本人
        notification_users.discard(changed_by)

        # 发送通知
        for user_id in notification_users:
            notification = Notification(
                user_id=user_id,
                title="任务状态更新",
                content=f"任务 {task.title} 状态从 {old_status} 变更为 {new_status}",
                type="task_status_changed",
                related_entity_type="task",
                related_entity_id=task_id,
                action_url=f"/tasks/{task_id}",
            )

            self.db.add(notification)

        await self.db.commit()


class ActivityService:
    """
    活动记录服务
    ============

    记录和管理系统活动日志
    """

    def __init__(self, db: Session):
        self.db = db

    async def log_task_activity(
        self,
        task_id: str,
        user_id: str,
        action: str,
        field_name: Optional[str] = None,
        old_value: Optional[str] = None,
        new_value: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """记录任务活动"""
        activity = TaskActivity(
            task_id=task_id,
            user_id=user_id,
            action=action,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            description=description,
            metadata=metadata or {},
        )

        self.db.add(activity)
        await self.db.commit()

    async def get_task_activities(
        self, task_id: str, limit: int = 50
    ) -> List[TaskActivity]:
        """获取任务活动历史"""
        return (
            await self.db.query(TaskActivity)
            .filter(TaskActivity.task_id == task_id)
            .order_by(TaskActivity.created_at.desc())
            .limit(limit)
            .all()
        )


class FileService:
    """
    文件管理服务
    ============

    处理任务附件的上传、存储和管理
    """

    def __init__(self, db: Session, upload_path: str = "/uploads"):
        self.db = db
        self.upload_path = upload_path

    async def upload_task_attachment(
        self, task_id: str, file: UploadFile, user_id: str
    ) -> TaskAttachment:
        """上传任务附件"""
        import os
        import uuid
        from pathlib import Path

        # 验证文件
        await self._validate_file(file)

        # 生成文件名
        file_extension = Path(file.filename).suffix
        stored_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(self.upload_path, "tasks", task_id, stored_filename)

        # 确保目录存在
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # 保存文件
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # 创建附件记录
        attachment = TaskAttachment(
            task_id=task_id,
            filename=stored_filename,
            original_name=file.filename,
            file_size=len(content),
            file_path=file_path,
            mime_type=file.content_type,
            created_by=user_id,
        )

        self.db.add(attachment)
        await self.db.commit()
        await self.db.refresh(attachment)

        return attachment

    async def _validate_file(self, file: UploadFile):
        """验证上传文件"""
        # 文件大小限制（10MB）
        max_size = 10 * 1024 * 1024

        content = await file.read()
        await file.seek(0)  # 重置文件指针

        if len(content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="文件大小超出限制（最大10MB）",
            )

        # 文件类型验证
        allowed_types = {
            "image/jpeg",
            "image/png",
            "image/gif",
            "application/pdf",
            "text/plain",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }

        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="不支持的文件类型"
            )
