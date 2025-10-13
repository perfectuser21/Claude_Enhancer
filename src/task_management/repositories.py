"""
任务管理系统数据访问层
======================

实现Repository模式，提供：
- TaskRepository: 任务数据访问
- ProjectRepository: 项目数据访问
- CachedRepository: 带缓存的数据访问
- QueryBuilder: 复杂查询构建器
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple, Union
from uuid import UUID
import json

from sqlalchemy import and_, or_, func, text, desc, asc
from sqlalchemy.orm import Session, joinedload, selectinload, contains_eager
from sqlalchemy.sql import Select
from redis import Redis

from backend.repositories.base_repository import BaseRepository
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


class TaskRepository(BaseRepository[Task]):
    """
    任务数据访问类
    ==============

    提供任务相关的所有数据库操作，包括：
    - 基础CRUD操作
    - 复杂查询和筛选
    - 关联数据预加载
    - 性能优化查询
    - 统计查询
    """

    def __init__(self, db: Session):
        super().__init__(db, Task)

    async def get_by_id_with_relations(
        self,
        task_id: str,
        include_comments: bool = True,
        include_attachments: bool = True,
        include_activities: bool = False,
    ) -> Optional[Task]:
        """
        获取任务详情（包含关联数据）

        Args:
            task_id: 任务ID
            include_comments: 是否包含评论
            include_attachments: 是否包含附件
            include_activities: 是否包含活动日志

        Returns:
            任务对象或None
        """
        query = self.db.query(Task).options(
            joinedload(Task.assignee),
            joinedload(Task.project),
            joinedload(Task.creator),
        )

        if include_comments:
            query = query.options(
                selectinload(Task.comments).joinedload(TaskComment.author)
            )

        if include_attachments:
            query = query.options(
                selectinload(Task.attachments).joinedload(TaskAttachment.uploader)
            )

        if include_activities:
            query = query.options(
                selectinload(Task.activities).joinedload(TaskActivity.user)
            )

        return await query.filter(
            and_(Task.id == task_id, Task.is_deleted == False)
        ).first()

    async def search_with_fulltext(
        self,
        query_text: str,
        user_id: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
    ) -> List[Task]:
        """
        全文搜索任务

        Args:
            query_text: 搜索文本
            user_id: 用户ID（用于权限过滤）
            filters: 额外筛选条件
            limit: 结果数量限制

        Returns:
            匹配的任务列表
        """
        # 构建基础查询
        base_query = self.db.query(Task).filter(
            and_(Task.is_deleted == False, self._build_user_access_filter(user_id))
        )

        # 全文搜索条件
        search_conditions = []
        if query_text:
            search_terms = query_text.split()
            for term in search_terms:
                term_filter = or_(
                    Task.title.ilike(f"%{term}%"),
                    Task.description.ilike(f"%{term}%"),
                    Task.tags.op("&&")(func.array([term])),
                )
                search_conditions.append(term_filter)

        if search_conditions:
            base_query = base_query.filter(and_(*search_conditions))

        # 应用额外筛选
        if filters:
            base_query = self._apply_filters(base_query, filters)

        # 添加相关性排序（标题匹配优先级更高）
        relevance_score = func.coalesce(
            func.case([(Task.title.ilike(f"%{query_text}%"), 10)], else_=0)
            + func.case([(Task.description.ilike(f"%{query_text}%"), 5)], else_=0),
            0,
        ).label("relevance")

        return (
            await base_query.add_columns(relevance_score)
            .order_by(desc("relevance"), desc(Task.updated_at))
            .limit(limit)
            .all()
        )

    async def get_tasks_by_project(
        self,
        project_id: str,
        user_id: str,
        status_filter: Optional[List[str]] = None,
        assignee_filter: Optional[str] = None,
        include_relations: bool = False,
    ) -> List[Task]:
        """
        获取项目任务列表

        Args:
            project_id: 项目ID
            user_id: 用户ID
            status_filter: 状态筛选
            assignee_filter: 分配者筛选
            include_relations: 是否包含关联数据

        Returns:
            任务列表
        """
        query = self.db.query(Task).filter(
            and_(
                Task.project_id == project_id,
                Task.is_deleted == False,
                self._build_user_access_filter(user_id),
            )
        )

        if include_relations:
            query = query.options(
                joinedload(Task.assignee), selectinload(Task.comments)
            )

        if status_filter:
            query = query.filter(Task.status.in_(status_filter))

        if assignee_filter:
            query = query.filter(Task.assignee_id == assignee_filter)

        return await query.order_by(
            desc(Task.priority == TaskPriority.URGENT.value),
            desc(Task.priority == TaskPriority.HIGH.value),
            asc(Task.due_date),
            desc(Task.created_at),
        ).all()

    async def get_user_assigned_tasks(
        self,
        user_id: str,
        status_filter: Optional[List[str]] = None,
        project_filter: Optional[str] = None,
        due_date_range: Optional[Tuple[datetime, datetime]] = None,
        priority_filter: Optional[List[str]] = None,
    ) -> List[Task]:
        """
        获取用户分配的任务

        Args:
            user_id: 用户ID
            status_filter: 状态筛选
            project_filter: 项目筛选
            due_date_range: 截止日期范围
            priority_filter: 优先级筛选

        Returns:
            任务列表
        """
        query = (
            self.db.query(Task)
            .filter(and_(Task.assignee_id == user_id, Task.is_deleted == False))
            .options(joinedload(Task.project), joinedload(Task.creator))
        )

        if status_filter:
            query = query.filter(Task.status.in_(status_filter))

        if project_filter:
            query = query.filter(Task.project_id == project_filter)

        if due_date_range:
            start_date, end_date = due_date_range
            query = query.filter(
                and_(Task.due_date >= start_date, Task.due_date <= end_date)
            )

        if priority_filter:
            query = query.filter(Task.priority.in_(priority_filter))

        return await query.order_by(
            asc(Task.due_date),
            desc(Task.priority == TaskPriority.URGENT.value),
            desc(Task.priority == TaskPriority.HIGH.value),
            desc(Task.updated_at),
        ).all()

    async def get_overdue_tasks(
        self, user_id: Optional[str] = None, project_id: Optional[str] = None
    ) -> List[Task]:
        """
        获取逾期任务

        Args:
            user_id: 用户ID筛选
            project_id: 项目ID筛选

        Returns:
            逾期任务列表
        """
        query = (
            self.db.query(Task)
            .filter(
                and_(
                    Task.is_deleted == False,
                    Task.status.notin_(
                        [TaskStatus.DONE.value, TaskStatus.CANCELLED.value]
                    ),
                    Task.due_date < datetime.utcnow(),
                )
            )
            .options(joinedload(Task.assignee), joinedload(Task.project))
        )

        if user_id:
            query = query.filter(
                or_(Task.assignee_id == user_id, Task.created_by == user_id)
            )

        if project_id:
            query = query.filter(Task.project_id == project_id)

        return await query.order_by(
            asc(Task.due_date), desc(Task.priority == TaskPriority.URGENT.value)
        ).all()

    async def get_tasks_due_soon(
        self, days_ahead: int = 7, user_id: Optional[str] = None
    ) -> List[Task]:
        """
        获取即将到期的任务

        Args:
            days_ahead: 提前天数
            user_id: 用户ID筛选

        Returns:
            即将到期的任务列表
        """
        due_date_threshold = datetime.utcnow() + timedelta(days=days_ahead)

        query = (
            self.db.query(Task)
            .filter(
                and_(
                    Task.is_deleted == False,
                    Task.status.notin_(
                        [TaskStatus.DONE.value, TaskStatus.CANCELLED.value]
                    ),
                    Task.due_date <= due_date_threshold,
                    Task.due_date >= datetime.utcnow(),
                )
            )
            .options(joinedload(Task.assignee), joinedload(Task.project))
        )

        if user_id:
            query = query.filter(Task.assignee_id == user_id)

        return await query.order_by(asc(Task.due_date)).all()

    async def get_task_dependencies(self, task_id: str) -> Dict[str, List[Task]]:
        """
        获取任务依赖关系

        Args:
            task_id: 任务ID

        Returns:
            包含依赖和被依赖任务的字典
        """
        # 获取前置依赖（此任务依赖的其他任务）
        dependencies = (
            await self.db.query(Task)
            .join(TaskDependency, Task.id == TaskDependency.dependency_id)
            .filter(and_(TaskDependency.task_id == task_id, Task.is_deleted == False))
            .options(joinedload(Task.assignee))
            .all()
        )

        # 获取后续依赖（依赖此任务的其他任务）
        dependents = (
            await self.db.query(Task)
            .join(TaskDependency, Task.id == TaskDependency.task_id)
            .filter(
                and_(TaskDependency.dependency_id == task_id, Task.is_deleted == False)
            )
            .options(joinedload(Task.assignee))
            .all()
        )

        return {"dependencies": dependencies, "dependents": dependents}

    async def add_task_dependency(
        self,
        task_id: str,
        dependency_id: str,
        dependency_type: str = "blocks",
        notes: Optional[str] = None,
    ) -> TaskDependency:
        """
        添加任务依赖关系

        Args:
            task_id: 任务ID
            dependency_id: 依赖任务ID
            dependency_type: 依赖类型
            notes: 备注

        Returns:
            创建的依赖关系对象
        """
        # 检查是否已存在依赖关系
        existing = (
            await self.db.query(TaskDependency)
            .filter(
                and_(
                    TaskDependency.task_id == task_id,
                    TaskDependency.dependency_id == dependency_id,
                )
            )
            .first()
        )

        if existing:
            raise ValueError("依赖关系已存在")

        # 检查是否会形成循环依赖
        if await self._would_create_cycle(task_id, dependency_id):
            raise ValueError("添加此依赖会形成循环依赖")

        dependency = TaskDependency(
            task_id=task_id,
            dependency_id=dependency_id,
            dependency_type=dependency_type,
            notes=notes,
        )

        self.db.add(dependency)
        await self.db.commit()
        await self.db.refresh(dependency)

        return dependency

    async def get_task_statistics(
        self,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        date_range: Optional[Tuple[datetime, datetime]] = None,
    ) -> Dict[str, Any]:
        """
        获取任务统计信息

        Args:
            user_id: 用户ID筛选
            project_id: 项目ID筛选
            date_range: 日期范围筛选

        Returns:
            统计信息字典
        """
        base_query = self.db.query(Task).filter(Task.is_deleted == False)

        # 应用筛选条件
        if user_id:
            base_query = base_query.filter(
                or_(Task.assignee_id == user_id, Task.created_by == user_id)
            )

        if project_id:
            base_query = base_query.filter(Task.project_id == project_id)

        if date_range:
            start_date, end_date = date_range
            base_query = base_query.filter(
                and_(Task.created_at >= start_date, Task.created_at <= end_date)
            )

        # 按状态统计
        status_stats = await self.db.execute(
            base_query.with_entities(Task.status, func.count(Task.id).label("count"))
            .group_by(Task.status)
            .statement
        )

        # 按优先级统计
        priority_stats = await self.db.execute(
            base_query.with_entities(Task.priority, func.count(Task.id).label("count"))
            .group_by(Task.priority)
            .statement
        )

        # 逾期任务统计
        overdue_count = await base_query.filter(
            and_(
                Task.due_date < datetime.utcnow(),
                Task.status.notin_([TaskStatus.DONE.value, TaskStatus.CANCELLED.value]),
            )
        ).count()

        # 完成率统计
        total_count = await base_query.count()
        completed_count = await base_query.filter(
            Task.status == TaskStatus.DONE.value
        ).count()

        completion_rate = (
            (completed_count / total_count * 100) if total_count > 0 else 0
        )

        return {
            "total_count": total_count,
            "completed_count": completed_count,
            "completion_rate": completion_rate,
            "overdue_count": overdue_count,
            "status_distribution": {
                row.status: row.count for row in status_stats.fetchall()
            },
            "priority_distribution": {
                row.priority: row.count for row in priority_stats.fetchall()
            },
        }

    async def get_user_workload(
        self, user_id: str, date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """
        获取用户工作负载统计

        Args:
            user_id: 用户ID
            date_range: 日期范围

        Returns:
            工作负载统计
        """
        query = self.db.query(Task).filter(
            and_(Task.assignee_id == user_id, Task.is_deleted == False)
        )

        if date_range:
            start_date, end_date = date_range
            query = query.filter(
                or_(
                    and_(Task.due_date >= start_date, Task.due_date <= end_date),
                    and_(Task.created_at >= start_date, Task.created_at <= end_date),
                )
            )

        # 按状态分组统计
        status_workload = {}
        for status in TaskStatus:
            count = await query.filter(Task.status == status.value).count()
            status_workload[status.value] = count

        # 估算工时统计
        estimated_hours = (
            await query.with_entities(func.sum(Task.estimated_hours)).scalar() or 0
        )

        actual_hours = (
            await query.with_entities(func.sum(Task.actual_hours)).scalar() or 0
        )

        # 优先级分布
        priority_workload = {}
        for priority in TaskPriority:
            count = await query.filter(Task.priority == priority.value).count()
            priority_workload[priority.value] = count

        return {
            "status_workload": status_workload,
            "priority_workload": priority_workload,
            "estimated_hours": estimated_hours,
            "actual_hours": actual_hours,
            "total_tasks": sum(status_workload.values()),
        }

    # === 私有方法 ===
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

    def _apply_filters(self, query, filters: Dict[str, Any]):
        """应用筛选条件"""
        for key, value in filters.items():
            if value is None:
                continue

            if key == "status":
                if isinstance(value, list):
                    query = query.filter(Task.status.in_(value))
                else:
                    query = query.filter(Task.status == value)
            elif key == "priority":
                if isinstance(value, list):
                    query = query.filter(Task.priority.in_(value))
                else:
                    query = query.filter(Task.priority == value)
            elif key == "assignee_id":
                query = query.filter(Task.assignee_id == value)
            elif key == "project_id":
                query = query.filter(Task.project_id == value)
            elif key == "due_date_from":
                query = query.filter(Task.due_date >= value)
            elif key == "due_date_to":
                query = query.filter(Task.due_date <= value)
            elif key == "tags":
                if isinstance(value, list) and value:
                    query = query.filter(Task.tags.op("&&")(value))
            elif key == "created_by":
                query = query.filter(Task.created_by == value)

        return query

    async def _would_create_cycle(self, task_id: str, dependency_id: str) -> bool:
        """检查是否会创建循环依赖"""
        # 深度优先搜索检查循环
        visited = set()
        path = set()

        async def dfs(current_task_id: str) -> bool:
            if current_task_id in path:
                return True  # 发现循环
            if current_task_id in visited:
                return False

            visited.add(current_task_id)
            path.add(current_task_id)

            # 获取当前任务的所有依赖
            dependencies = (
                await self.db.query(TaskDependency.dependency_id)
                .filter(TaskDependency.task_id == current_task_id)
                .all()
            )

            for dep in dependencies:
                if await dfs(str(dep.dependency_id)):
                    return True

            path.remove(current_task_id)
            return False

        return await dfs(dependency_id)


class ProjectRepository(BaseRepository[Project]):
    """
    项目数据访问类
    ==============

    提供项目相关的数据库操作
    """

    def __init__(self, db: Session):
        super().__init__(db, Project)

    async def get_user_projects(
        self,
        user_id: str,
        status_filter: Optional[List[str]] = None,
        include_archived: bool = False,
    ) -> List[Project]:
        """
        获取用户参与的项目

        Args:
            user_id: 用户ID
            status_filter: 状态筛选
            include_archived: 是否包含已归档项目

        Returns:
            项目列表
        """
        query = (
            self.db.query(Project)
            .join(ProjectMember, Project.id == ProjectMember.project_id)
            .filter(and_(ProjectMember.user_id == user_id, Project.is_deleted == False))
            .options(
                joinedload(Project.team),
                contains_eager(Project.members).joinedload(ProjectMember.user),
            )
        )

        if not include_archived:
            query = query.filter(Project.is_archived == False)

        if status_filter:
            query = query.filter(Project.status.in_(status_filter))

        return await query.order_by(desc(Project.updated_at)).all()

    async def get_project_with_tasks(
        self,
        project_id: str,
        user_id: str,
        task_status_filter: Optional[List[str]] = None,
    ) -> Optional[Project]:
        """
        获取项目及其任务

        Args:
            project_id: 项目ID
            user_id: 用户ID
            task_status_filter: 任务状态筛选

        Returns:
            项目对象（包含任务）
        """
        # 检查用户权限
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

        if not member:
            return None

        query = (
            self.db.query(Project)
            .filter(and_(Project.id == project_id, Project.is_deleted == False))
            .options(
                joinedload(Project.team),
                selectinload(Project.members).joinedload(ProjectMember.user),
            )
        )

        project = await query.first()
        if not project:
            return None

        # 获取项目任务
        task_query = (
            self.db.query(Task)
            .filter(and_(Task.project_id == project_id, Task.is_deleted == False))
            .options(joinedload(Task.assignee), joinedload(Task.creator))
        )

        if task_status_filter:
            task_query = task_query.filter(Task.status.in_(task_status_filter))

        project.tasks = await task_query.order_by(desc(Task.updated_at)).all()

        return project

    async def get_project_statistics(self, project_id: str) -> Dict[str, Any]:
        """获取项目统计信息"""
        # 任务统计
        task_stats = await self.db.execute(
            text(
                """
            SELECT
                status,
                priority,
                COUNT(*) as count,
                AVG(CASE WHEN estimated_hours IS NOT NULL THEN estimated_hours END) as avg_estimated_hours,
                AVG(CASE WHEN actual_hours IS NOT NULL THEN actual_hours END) as avg_actual_hours
            FROM tasks
            WHERE project_id = :project_id
                AND is_deleted = false
            GROUP BY status, priority
        """
            ),
            {"project_id": project_id},
        )

        # 成员统计
        member_count = (
            await self.db.query(ProjectMember)
            .filter(ProjectMember.project_id == project_id)
            .count()
        )

        # 活跃度统计（最近7天的活动）
        recent_activity_count = (
            await self.db.query(TaskActivity)
            .join(Task, TaskActivity.task_id == Task.id)
            .filter(
                and_(
                    Task.project_id == project_id,
                    TaskActivity.created_at >= datetime.utcnow() - timedelta(days=7),
                )
            )
            .count()
        )

        stats = {
            "member_count": member_count,
            "recent_activity_count": recent_activity_count,
            "task_stats": {},
        }

        # 处理任务统计结果
        for row in task_stats.fetchall():
            if row.status not in stats["task_stats"]:
                stats["task_stats"][row.status] = {
                    "count": 0,
                    "priority_distribution": {},
                    "avg_estimated_hours": 0,
                    "avg_actual_hours": 0,
                }

            stats["task_stats"][row.status]["count"] += row.count
            stats["task_stats"][row.status]["priority_distribution"][
                row.priority
            ] = row.count

            if row.avg_estimated_hours:
                stats["task_stats"][row.status][
                    "avg_estimated_hours"
                ] = row.avg_estimated_hours
            if row.avg_actual_hours:
                stats["task_stats"][row.status][
                    "avg_actual_hours"
                ] = row.avg_actual_hours

        return stats

    async def add_project_member(
        self,
        project_id: str,
        user_id: str,
        role: str = MemberRole.MEMBER.value,
        added_by: str = None,
    ) -> ProjectMember:
        """添加项目成员"""
        # 检查是否已是成员
        existing_member = (
            await self.db.query(ProjectMember)
            .filter(
                and_(
                    ProjectMember.project_id == project_id,
                    ProjectMember.user_id == user_id,
                )
            )
            .first()
        )

        if existing_member:
            raise ValueError("用户已是项目成员")

        member = ProjectMember(project_id=project_id, user_id=user_id, role=role)

        self.db.add(member)
        await self.db.commit()
        await self.db.refresh(member)

        return member

    async def remove_project_member(
        self, project_id: str, user_id: str, removed_by: str
    ) -> bool:
        """移除项目成员"""
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

        if not member:
            return False

        # 检查是否是项目所有者
        if member.role == MemberRole.OWNER.value:
            pass  # Auto-fixed empty block
            # 检查是否还有其他所有者
            other_owners = (
                await self.db.query(ProjectMember)
                .filter(
                    and_(
                        ProjectMember.project_id == project_id,
                        ProjectMember.role == MemberRole.OWNER.value,
                        ProjectMember.user_id != user_id,
                    )
                )
                .count()
            )

            if other_owners == 0:
                raise ValueError("无法移除最后一个项目所有者")

        await self.db.delete(member)
        await self.db.commit()

        return True


class CachedTaskRepository(TaskRepository):
    """
    带缓存的任务Repository
    ======================

    在TaskRepository基础上添加Redis缓存支持
    """

    def __init__(self, db: Session, redis_client: Redis):
        super().__init__(db)
        self.redis = redis_client
        self.cache_ttl = {
            "task": 300,  # 任务缓存5分钟
            "search": 60,  # 搜索结果缓存1分钟
            "statistics": 180,  # 统计数据缓存3分钟
            "user_tasks": 120,  # 用户任务缓存2分钟
        }

    async def get_by_id_with_relations(
        self,
        task_id: str,
        include_comments: bool = True,
        include_attachments: bool = True,
        include_activities: bool = False,
    ) -> Optional[Task]:
        """从缓存获取任务（如果不存在则查询数据库）"""
        cache_key = f"task:{task_id}:relations:{include_comments}:{include_attachments}:{include_activities}"

        # 尝试从缓存获取
        cached_data = await self.redis.get(cache_key)
        if cached_data:
            return self._deserialize_task(json.loads(cached_data))

        # 缓存未命中，查询数据库
        task = await super().get_by_id_with_relations(
            task_id, include_comments, include_attachments, include_activities
        )

        if task:
            pass  # Auto-fixed empty block
            # 存储到缓存
            await self.redis.setex(
                cache_key,
                self.cache_ttl["task"],
                json.dumps(self._serialize_task(task)),
            )

        return task

    async def search_with_fulltext(
        self,
        query_text: str,
        user_id: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 50,
    ) -> List[Task]:
        """缓存搜索结果"""
        # 生成缓存键
        cache_key = f"search:{hash(query_text)}:{user_id}:{hash(str(filters))}:{limit}"

        # 尝试从缓存获取
        cached_results = await self.redis.get(cache_key)
        if cached_results:
            task_data_list = json.loads(cached_results)
            return [self._deserialize_task(data) for data in task_data_list]

        # 缓存未命中，查询数据库
        tasks = await super().search_with_fulltext(query_text, user_id, filters, limit)

        if tasks:
            pass  # Auto-fixed empty block
            # 序列化并缓存结果
            serialized_tasks = [self._serialize_task(task) for task in tasks]
            await self.redis.setex(
                cache_key, self.cache_ttl["search"], json.dumps(serialized_tasks)
            )

        return tasks

    async def get_user_assigned_tasks(
        self,
        user_id: str,
        status_filter: Optional[List[str]] = None,
        project_filter: Optional[str] = None,
        due_date_range: Optional[Tuple[datetime, datetime]] = None,
        priority_filter: Optional[List[str]] = None,
    ) -> List[Task]:
        """缓存用户任务"""
        cache_key = f"user_tasks:{user_id}:{hash(str(status_filter))}:{project_filter}:{hash(str(due_date_range))}:{hash(str(priority_filter))}"

        # 尝试从缓存获取
        cached_tasks = await self.redis.get(cache_key)
        if cached_tasks:
            task_data_list = json.loads(cached_tasks)
            return [self._deserialize_task(data) for data in task_data_list]

        # 查询数据库
        tasks = await super().get_user_assigned_tasks(
            user_id, status_filter, project_filter, due_date_range, priority_filter
        )

        if tasks:
            pass  # Auto-fixed empty block
            # 缓存结果
            serialized_tasks = [self._serialize_task(task) for task in tasks]
            await self.redis.setex(
                cache_key, self.cache_ttl["user_tasks"], json.dumps(serialized_tasks)
            )

        return tasks

    async def update(self, entity_id: str, data: Dict[str, Any]) -> Task:
        """更新任务并清除相关缓存"""
        # 先清除相关缓存
        await self._invalidate_task_caches(entity_id)

        # 更新数据库
        task = await super().update(entity_id, data)

        return task

    async def delete(self, entity_id: str) -> bool:
        """删除任务并清除缓存"""
        await self._invalidate_task_caches(entity_id)
        return await super().delete(entity_id)

    # === 缓存相关私有方法 ===
    def _serialize_task(self, task: Task) -> Dict[str, Any]:
        """序列化任务对象为字典"""
        return {
            "id": str(task.id),
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "priority": task.priority,
            "assignee_id": str(task.assignee_id) if task.assignee_id else None,
            "project_id": str(task.project_id) if task.project_id else None,
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
            # 根据需要添加更多字段
        }

    def _deserialize_task(self, data: Dict[str, Any]) -> Task:
        """反序列化字典为任务对象"""
        task = Task()
        task.id = UUID(data["id"])
        task.title = data["title"]
        task.description = data["description"]
        task.status = data["status"]
        task.priority = data["priority"]
        task.assignee_id = UUID(data["assignee_id"]) if data["assignee_id"] else None
        task.project_id = UUID(data["project_id"]) if data["project_id"] else None

        if data["due_date"]:
            task.due_date = datetime.fromisoformat(data["due_date"])
        if data["created_at"]:
            task.created_at = datetime.fromisoformat(data["created_at"])
        if data["updated_at"]:
            task.updated_at = datetime.fromisoformat(data["updated_at"])

        return task

    async def _invalidate_task_caches(self, task_id: str):
        """清除任务相关的所有缓存"""
        # 获取任务信息
        task = await self.get_by_id(task_id)
        if not task:
            return

        # 清除任务详情缓存
        patterns = [
            f"task:{task_id}:*",
            f"user_tasks:{task.assignee_id}:*" if task.assignee_id else None,
            f"user_tasks:{task.created_by}:*" if task.created_by else None,
            "search:*",  # 清除所有搜索缓存（简化处理）
        ]

        for pattern in patterns:
            if pattern:
                keys = await self.redis.keys(pattern)
                if keys:
                    await self.redis.delete(*keys)


class QueryBuilder:
    """
    查询构建器
    ==========

    提供灵活的查询构建功能，支持复杂的筛选和排序条件
    """

    def __init__(self, db: Session, model_class):
        self.db = db
        self.model_class = model_class
        self.query = db.query(model_class)
        self._joins = []
        self._filters = []
        self._orders = []

    def filter_by(self, **kwargs) -> "QueryBuilder":
        """添加等值筛选条件"""
        for key, value in kwargs.items():
            if hasattr(self.model_class, key):
                self._filters.append(getattr(self.model_class, key) == value)
        return self

    def filter_in(self, field: str, values: List[Any]) -> "QueryBuilder":
        """添加IN筛选条件"""
        if hasattr(self.model_class, field):
            self._filters.append(getattr(self.model_class, field).in_(values))
        return self

    def filter_range(self, field: str, start: Any, end: Any) -> "QueryBuilder":
        """添加范围筛选条件"""
        if hasattr(self.model_class, field):
            column = getattr(self.model_class, field)
            self._filters.append(and_(column >= start, column <= end))
        return self

    def filter_like(self, field: str, pattern: str) -> "QueryBuilder":
        """添加模糊匹配筛选条件"""
        if hasattr(self.model_class, field):
            self._filters.append(getattr(self.model_class, field).ilike(f"%{pattern}%"))
        return self

    def order_by(self, field: str, direction: str = "asc") -> "QueryBuilder":
        """添加排序条件"""
        if hasattr(self.model_class, field):
            column = getattr(self.model_class, field)
            if direction.lower() == "desc":
                self._orders.append(column.desc())
            else:
                self._orders.append(column.asc())
        return self

    def join_related(self, relationship: str) -> "QueryBuilder":
        """添加关联查询"""
        if hasattr(self.model_class, relationship):
            self.query = self.query.options(
                joinedload(getattr(self.model_class, relationship))
            )
        return self

    async def all(self) -> List[Any]:
        """执行查询并返回所有结果"""
        if self._filters:
            self.query = self.query.filter(and_(*self._filters))

        if self._orders:
            self.query = self.query.order_by(*self._orders)

        return await self.query.all()

    async def first(self) -> Optional[Any]:
        """执行查询并返回第一个结果"""
        if self._filters:
            self.query = self.query.filter(and_(*self._filters))

        if self._orders:
            self.query = self.query.order_by(*self._orders)

        return await self.query.first()

    async def count(self) -> int:
        """执行查询并返回结果数量"""
        if self._filters:
            self.query = self.query.filter(and_(*self._filters))

        return await self.query.count()

    async def paginate(self, page: int, page_size: int) -> Dict[str, Any]:
        """执行分页查询"""
        if self._filters:
            self.query = self.query.filter(and_(*self._filters))

        total = await self.query.count()

        if self._orders:
            self.query = self.query.order_by(*self._orders)

        offset = (page - 1) * page_size
        items = await self.query.offset(offset).limit(page_size).all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size,
        }
