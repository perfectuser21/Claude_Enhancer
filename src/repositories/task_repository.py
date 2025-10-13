"""
任务数据访问层
==============

实现Repository模式，提供：
- 基础CRUD操作
- 复杂查询和筛选
- 关联数据预加载
- 性能优化查询
- 统计查询
- 缓存支持
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple, Union
from uuid import UUID
import json

from sqlalchemy import and_, or_, func, text, desc, asc, exists
from sqlalchemy.orm import Session, joinedload, selectinload, contains_eager
from sqlalchemy.sql import Select
from sqlalchemy.exc import IntegrityError

from src.repositories.base_repository import BaseRepository
from src.task_management.models import (
    Task,
    TaskStatus,
    TaskPriority,
    TaskDependency,
    Project,
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

    # === 基础CRUD操作增强 ===

    async def create(self, data: Dict[str, Any]) -> Task:
        """
        创建任务

        Args:
            data: 任务数据

        Returns:
            创建的任务对象

        Raises:
            IntegrityError: 数据完整性错误
        """
        try:
            task = Task(**data)
            self.db.add(task)
            await self.db.commit()
            await self.db.refresh(task)
            return task
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"数据完整性错误: {str(e)}")

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

    async def get_multiple_by_ids(
        self, task_ids: List[str], include_relations: bool = False
    ) -> List[Task]:
        """
        批量获取任务

        Args:
            task_ids: 任务ID列表
            include_relations: 是否包含关联数据

        Returns:
            任务列表
        """
        query = self.db.query(Task).filter(
            and_(Task.id.in_(task_ids), Task.is_deleted == False)
        )

        if include_relations:
            query = query.options(
                joinedload(Task.assignee),
                joinedload(Task.project),
                joinedload(Task.creator),
            )

        return await query.all()

    async def update(self, task_id: str, data: Dict[str, Any]) -> Task:
        """
        更新任务

        Args:
            task_id: 任务ID
            data: 更新数据

        Returns:
            更新后的任务对象

        Raises:
            ValueError: 任务不存在
        """
        task = await self.get_by_id(task_id)
        if not task:
            raise ValueError("任务不存在")

        try:
            for key, value in data.items():
                if hasattr(task, key):
                    setattr(task, key, value)

            task.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(task)
            return task
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"更新失败: {str(e)}")

    async def soft_delete(self, task_id: str) -> bool:
        """
        软删除任务

        Args:
            task_id: 任务ID

        Returns:
            删除是否成功
        """
        task = await self.get_by_id(task_id)
        if not task:
            return False

        task.is_deleted = True
        task.deleted_at = datetime.utcnow()
        await self.db.commit()
        return True

    async def hard_delete(self, task_id: str) -> bool:
        """
        硬删除任务

        Args:
            task_id: 任务ID

        Returns:
            删除是否成功
        """
        task = await self.get_by_id(task_id)
        if not task:
            return False

        await self.db.delete(task)
        await self.db.commit()
        return True

    # === 搜索和筛选 ===

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

    async def search_tasks(
        self,
        user_id: str,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        搜索和筛选任务（带分页）

        Args:
            user_id: 用户ID
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

        # 应用筛选条件
        if filters:
            base_query = self._apply_filters(base_query, filters)

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
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_count + page_size - 1) // page_size,
        }

    # === 专门查询方法 ===

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

    # === 依赖关系管理 ===

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

        Raises:
            ValueError: 依赖关系已存在或会形成循环依赖
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

    async def remove_task_dependency(self, task_id: str, dependency_id: str) -> bool:
        """
        移除任务依赖关系

        Args:
            task_id: 任务ID
            dependency_id: 依赖任务ID

        Returns:
            删除是否成功
        """
        dependency = (
            await self.db.query(TaskDependency)
            .filter(
                and_(
                    TaskDependency.task_id == task_id,
                    TaskDependency.dependency_id == dependency_id,
                )
            )
            .first()
        )

        if not dependency:
            return False

        await self.db.delete(dependency)
        await self.db.commit()
        return True

    # === 统计查询 ===

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

    async def count_user_tasks(self, user_id: str) -> int:
        """
        统计用户任务总数

        Args:
            user_id: 用户ID

        Returns:
            任务总数
        """
        return (
            await self.db.query(Task)
            .filter(
                and_(
                    or_(Task.assignee_id == user_id, Task.created_by == user_id),
                    Task.is_deleted == False,
                )
            )
            .count()
        )

    # === 标签管理 ===

    async def get_popular_tags(
        self,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        获取热门标签

        Args:
            user_id: 用户ID筛选
            project_id: 项目ID筛选
            limit: 结果数量限制

        Returns:
            标签列表（包含使用次数）
        """
        # 使用原生SQL查询标签统计
        conditions = ["t.is_deleted = false"]
        params = {}

        if user_id:
            conditions.append("(t.assignee_id = :user_id OR t.created_by = :user_id)")
            params["user_id"] = user_id

        if project_id:
            conditions.append("t.project_id = :project_id")
            params["project_id"] = project_id

        sql = f"""
        SELECT
            unnest(tags) as tag,
            COUNT(*) as usage_count
        FROM tasks t
        WHERE {' AND '.join(conditions)}
            AND tags IS NOT NULL
            AND array_length(tags, 1) > 0
        GROUP BY unnest(tags)
        ORDER BY usage_count DESC
        LIMIT :limit
        """

        params["limit"] = limit

        result = await self.db.execute(text(sql), params)
        return [
            {"tag": row.tag, "usage_count": row.usage_count}
            for row in result.fetchall()
        ]

    async def search_tasks_by_tags(
        self, tags: List[str], user_id: str, match_all: bool = True
    ) -> List[Task]:
        """
        根据标签搜索任务

        Args:
            tags: 标签列表
            user_id: 用户ID
            match_all: 是否匹配所有标签

        Returns:
            匹配的任务列表
        """
        query = self.db.query(Task).filter(
            and_(Task.is_deleted == False, self._build_user_access_filter(user_id))
        )

        if match_all:
            # 匹配所有标签
            query = query.filter(Task.tags.op("@>")(tags))
        else:
            # 匹配任意标签
            query = query.filter(Task.tags.op("&&")(tags))

        return await query.order_by(desc(Task.updated_at)).all()

    # === 私有辅助方法 ===

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


class TaskQueryBuilder:
    """
    任务查询构建器
    ==============

    提供流畅的查询构建接口
    """

    def __init__(self, db: Session, user_id: str):
        self.db = db
        self.user_id = user_id
        self.query = db.query(Task).filter(
            and_(Task.is_deleted == False, self._build_user_access_filter(user_id))
        )
        self._filters = []
        self._orders = []
        self._includes = []

    def filter_by_status(
        self, status: Union[TaskStatus, List[TaskStatus]]
    ) -> "TaskQueryBuilder":
        """按状态筛选"""
        if isinstance(status, list):
            self._filters.append(Task.status.in_([s.value for s in status]))
        else:
            self._filters.append(Task.status == status.value)
        return self

    def filter_by_priority(
        self, priority: Union[TaskPriority, List[TaskPriority]]
    ) -> "TaskQueryBuilder":
        """按优先级筛选"""
        if isinstance(priority, list):
            self._filters.append(Task.priority.in_([p.value for p in priority]))
        else:
            self._filters.append(Task.priority == priority.value)
        return self

    def filter_by_assignee(self, assignee_id: str) -> "TaskQueryBuilder":
        """按分配者筛选"""
        self._filters.append(Task.assignee_id == assignee_id)
        return self

    def filter_by_project(self, project_id: str) -> "TaskQueryBuilder":
        """按项目筛选"""
        self._filters.append(Task.project_id == project_id)
        return self

    def filter_by_tags(
        self, tags: List[str], match_all: bool = False
    ) -> "TaskQueryBuilder":
        """按标签筛选"""
        if match_all:
            self._filters.append(Task.tags.op("@>")(tags))
        else:
            self._filters.append(Task.tags.op("&&")(tags))
        return self

    def filter_by_due_date_range(
        self, start: datetime, end: datetime
    ) -> "TaskQueryBuilder":
        """按截止日期范围筛选"""
        self._filters.append(and_(Task.due_date >= start, Task.due_date <= end))
        return self

    def filter_overdue(self) -> "TaskQueryBuilder":
        """筛选逾期任务"""
        self._filters.append(
            and_(
                Task.due_date < datetime.utcnow(),
                Task.status.notin_([TaskStatus.DONE.value, TaskStatus.CANCELLED.value]),
            )
        )
        return self

    def include_assignee(self) -> "TaskQueryBuilder":
        """包含分配者信息"""
        self._includes.append(joinedload(Task.assignee))
        return self

    def include_project(self) -> "TaskQueryBuilder":
        """包含项目信息"""
        self._includes.append(joinedload(Task.project))
        return self

    def include_comments(self) -> "TaskQueryBuilder":
        """包含评论信息"""
        self._includes.append(selectinload(Task.comments))
        return self

    def order_by_priority(self, desc: bool = True) -> "TaskQueryBuilder":
        """按优先级排序"""
        if desc:
            self._orders.append(desc(Task.priority == TaskPriority.URGENT.value))
            self._orders.append(desc(Task.priority == TaskPriority.HIGH.value))
        else:
            self._orders.append(asc(Task.priority))
        return self

    def order_by_due_date(self, desc: bool = False) -> "TaskQueryBuilder":
        """按截止日期排序"""
        if desc:
            self._orders.append(desc(Task.due_date))
        else:
            self._orders.append(asc(Task.due_date))
        return self

    def order_by_updated_at(self, desc: bool = True) -> "TaskQueryBuilder":
        """按更新时间排序"""
        if desc:
            self._orders.append(desc(Task.updated_at))
        else:
            self._orders.append(asc(Task.updated_at))
        return self

    async def all(self) -> List[Task]:
        """执行查询并返回所有结果"""
        query = self._build_final_query()
        return await query.all()

    async def first(self) -> Optional[Task]:
        """执行查询并返回第一个结果"""
        query = self._build_final_query()
        return await query.first()

    async def count(self) -> int:
        """执行查询并返回结果数量"""
        query = self._build_count_query()
        return await query.scalar()

    async def paginate(self, page: int, page_size: int) -> Dict[str, Any]:
        """执行分页查询"""
        # 获取总数
        count_query = self._build_count_query()
        total = await count_query.scalar()

        # 获取分页数据
        query = self._build_final_query()
        offset = (page - 1) * page_size
        items = await query.offset(offset).limit(page_size).all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size,
        }

    def _build_final_query(self):
        """构建最终查询"""
        query = self.query

        # 应用筛选条件
        if self._filters:
            query = query.filter(and_(*self._filters))

        # 应用预加载
        if self._includes:
            query = query.options(*self._includes)

        # 应用排序
        if self._orders:
            query = query.order_by(*self._orders)

        return query

    def _build_count_query(self):
        """构建计数查询"""
        query = self.db.query(func.count(Task.id)).filter(
            and_(Task.is_deleted == False, self._build_user_access_filter(self.user_id))
        )

        if self._filters:
            query = query.filter(and_(*self._filters))

        return query

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
