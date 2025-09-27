"""
任务验证器
==========

提供完整的数据验证和业务规则验证：
- Pydantic模型验证
- 业务规则验证
- 权限验证
- 数据一致性验证
- 自定义验证规则
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Set, Union
from uuid import UUID
import re

from pydantic import BaseModel, validator, root_validator, Field
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.task_management.models import (
    Task,
    TaskStatus,
    TaskPriority,
    Project,
    ProjectMember,
    MemberRole,
    User,
)
from backend.models.user import User as UserModel


class TaskValidationError(Exception):
    """任务验证异常"""

    def __init__(
        self, message: str, field: Optional[str] = None, code: Optional[str] = None
    ):
        self.message = message
        self.field = field
        self.code = code
        super().__init__(message)


class BusinessRuleValidator:
    """
    业务规则验证器
    ==============

    负责验证任务管理中的各种业务规则：
    - 任务创建规则
    - 状态转换规则
    - 分配规则
    - 依赖关系规则
    - 项目权限规则
    """

    def __init__(self, db: Session):
        self.db = db

    # === 任务创建验证 ===

    async def validate_task_creation(
        self,
        title: str,
        creator_id: str,
        project_id: Optional[str] = None,
        assignee_id: Optional[str] = None,
        due_date: Optional[datetime] = None,
        tags: Optional[List[str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        验证任务创建的所有规则

        Args:
            title: 任务标题
            creator_id: 创建者ID
            project_id: 项目ID
            assignee_id: 分配者ID
            due_date: 截止日期
            tags: 标签列表
            **kwargs: 其他字段

        Returns:
            验证结果字典

        Raises:
            TaskValidationError: 验证失败
        """
        errors = []

        # 1. 标题验证
        title_errors = await self._validate_title(title)
        errors.extend(title_errors)

        # 2. 创建者验证
        creator_errors = await self._validate_creator(creator_id)
        errors.extend(creator_errors)

        # 3. 项目权限验证
        if project_id:
            project_errors = await self._validate_project_access(project_id, creator_id)
            errors.extend(project_errors)

        # 4. 分配者验证
        if assignee_id:
            assignee_errors = await self._validate_assignee(assignee_id, project_id)
            errors.extend(assignee_errors)

        # 5. 日期验证
        if due_date:
            date_errors = await self._validate_due_date(due_date)
            errors.extend(date_errors)

        # 6. 标签验证
        if tags:
            tag_errors = await self._validate_tags(tags)
            errors.extend(tag_errors)

        # 7. 用户任务数量限制验证
        quota_errors = await self._validate_user_task_quota(creator_id)
        errors.extend(quota_errors)

        if errors:
            raise TaskValidationError(message="任务创建验证失败", code="VALIDATION_FAILED")

        return {"valid": True, "warnings": []}

    async def _validate_title(self, title: str) -> List[Dict[str, str]]:
        """验证任务标题"""
        errors = []

        if not title or not title.strip():
            errors.append(
                {"field": "title", "message": "任务标题不能为空", "code": "TITLE_REQUIRED"}
            )
            return errors

        title = title.strip()

        # 长度检查
        if len(title) < 3:
            errors.append(
                {"field": "title", "message": "任务标题至少需要3个字符", "code": "TITLE_TOO_SHORT"}
            )

        if len(title) > 200:
            errors.append(
                {
                    "field": "title",
                    "message": "任务标题不能超过200个字符",
                    "code": "TITLE_TOO_LONG",
                }
            )

        # 特殊字符检查
        forbidden_chars = ["<", ">", '"', "'", "&"]
        if any(char in title for char in forbidden_chars):
            errors.append(
                {
                    "field": "title",
                    "message": "任务标题包含不允许的特殊字符",
                    "code": "TITLE_INVALID_CHARS",
                }
            )

        # 重复标题检查（在同一项目中）
        # 这里可以添加项目内标题唯一性检查

        return errors

    async def _validate_creator(self, creator_id: str) -> List[Dict[str, str]]:
        """验证创建者"""
        errors = []

        try:
            # 检查用户是否存在
            user = (
                await self.db.query(UserModel)
                .filter(UserModel.id == creator_id)
                .first()
            )

            if not user:
                errors.append(
                    {
                        "field": "creator_id",
                        "message": "创建者不存在",
                        "code": "CREATOR_NOT_FOUND",
                    }
                )
                return errors

            # 检查用户状态
            if user.status != "active":
                errors.append(
                    {
                        "field": "creator_id",
                        "message": "创建者账户未激活",
                        "code": "CREATOR_INACTIVE",
                    }
                )

            # 检查用户权限
            if not user.can_create_tasks:
                errors.append(
                    {
                        "field": "creator_id",
                        "message": "创建者没有创建任务的权限",
                        "code": "CREATOR_NO_PERMISSION",
                    }
                )

        except Exception as e:
            errors.append(
                {
                    "field": "creator_id",
                    "message": f"验证创建者时发生错误: {str(e)}",
                    "code": "CREATOR_VALIDATION_ERROR",
                }
            )

        return errors

    async def _validate_project_access(
        self, project_id: str, user_id: str
    ) -> List[Dict[str, str]]:
        """验证项目访问权限"""
        errors = []

        try:
            # 检查项目是否存在
            project = (
                await self.db.query(Project).filter(Project.id == project_id).first()
            )

            if not project:
                errors.append(
                    {
                        "field": "project_id",
                        "message": "项目不存在",
                        "code": "PROJECT_NOT_FOUND",
                    }
                )
                return errors

            # 检查项目状态
            if project.is_archived:
                errors.append(
                    {
                        "field": "project_id",
                        "message": "不能在已归档的项目中创建任务",
                        "code": "PROJECT_ARCHIVED",
                    }
                )

            # 检查用户是否是项目成员
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
                errors.append(
                    {
                        "field": "project_id",
                        "message": "用户不是项目成员",
                        "code": "NOT_PROJECT_MEMBER",
                    }
                )
                return errors

            # 检查成员权限
            if member.role == MemberRole.VIEWER.value:
                errors.append(
                    {
                        "field": "project_id",
                        "message": "查看者角色不能创建任务",
                        "code": "INSUFFICIENT_PROJECT_PERMISSION",
                    }
                )

        except Exception as e:
            errors.append(
                {
                    "field": "project_id",
                    "message": f"验证项目权限时发生错误: {str(e)}",
                    "code": "PROJECT_VALIDATION_ERROR",
                }
            )

        return errors

    async def _validate_assignee(
        self, assignee_id: str, project_id: Optional[str]
    ) -> List[Dict[str, str]]:
        """验证分配者"""
        errors = []

        try:
            # 检查分配者是否存在
            assignee = (
                await self.db.query(UserModel)
                .filter(UserModel.id == assignee_id)
                .first()
            )

            if not assignee:
                errors.append(
                    {
                        "field": "assignee_id",
                        "message": "分配者不存在",
                        "code": "ASSIGNEE_NOT_FOUND",
                    }
                )
                return errors

            # 检查分配者状态
            if assignee.status != "active":
                errors.append(
                    {
                        "field": "assignee_id",
                        "message": "分配者账户未激活",
                        "code": "ASSIGNEE_INACTIVE",
                    }
                )

            # 如果指定了项目，检查分配者是否是项目成员
            if project_id:
                member = (
                    await self.db.query(ProjectMember)
                    .filter(
                        and_(
                            ProjectMember.project_id == project_id,
                            ProjectMember.user_id == assignee_id,
                        )
                    )
                    .first()
                )

                if not member:
                    errors.append(
                        {
                            "field": "assignee_id",
                            "message": "分配者不是项目成员",
                            "code": "ASSIGNEE_NOT_PROJECT_MEMBER",
                        }
                    )

            # 检查分配者工作负载
            workload_errors = await self._validate_assignee_workload(assignee_id)
            errors.extend(workload_errors)

        except Exception as e:
            errors.append(
                {
                    "field": "assignee_id",
                    "message": f"验证分配者时发生错误: {str(e)}",
                    "code": "ASSIGNEE_VALIDATION_ERROR",
                }
            )

        return errors

    async def _validate_assignee_workload(
        self, assignee_id: str
    ) -> List[Dict[str, str]]:
        """验证分配者工作负载"""
        errors = []
        warnings = []

        try:
            # 统计分配者当前活跃任务数
            active_tasks_count = (
                await self.db.query(Task)
                .filter(
                    and_(
                        Task.assignee_id == assignee_id,
                        Task.status.in_(
                            [
                                TaskStatus.TODO.value,
                                TaskStatus.IN_PROGRESS.value,
                                TaskStatus.IN_REVIEW.value,
                                TaskStatus.BLOCKED.value,
                            ]
                        ),
                        Task.is_deleted == False,
                    )
                )
                .count()
            )

            # 硬限制：超过100个活跃任务
            if active_tasks_count >= 100:
                errors.append(
                    {
                        "field": "assignee_id",
                        "message": f"分配者有{active_tasks_count}个活跃任务，超过限制",
                        "code": "ASSIGNEE_OVERLOADED",
                    }
                )

            # 软警告：超过50个活跃任务
            elif active_tasks_count >= 50:
                warnings.append(
                    {
                        "field": "assignee_id",
                        "message": f"分配者有{active_tasks_count}个活跃任务，工作量较大",
                        "code": "ASSIGNEE_HIGH_WORKLOAD",
                    }
                )

            # 检查逾期任务数
            overdue_count = (
                await self.db.query(Task)
                .filter(
                    and_(
                        Task.assignee_id == assignee_id,
                        Task.due_date < datetime.utcnow(),
                        Task.status.notin_(
                            [TaskStatus.DONE.value, TaskStatus.CANCELLED.value]
                        ),
                        Task.is_deleted == False,
                    )
                )
                .count()
            )

            if overdue_count >= 10:
                warnings.append(
                    {
                        "field": "assignee_id",
                        "message": f"分配者有{overdue_count}个逾期任务",
                        "code": "ASSIGNEE_OVERDUE_TASKS",
                    }
                )

        except Exception as e:
            errors.append(
                {
                    "field": "assignee_id",
                    "message": f"验证分配者工作负载时发生错误: {str(e)}",
                    "code": "WORKLOAD_VALIDATION_ERROR",
                }
            )

        return errors

    async def _validate_due_date(self, due_date: datetime) -> List[Dict[str, str]]:
        """验证截止日期"""
        errors = []

        # 检查是否是过去时间
        if due_date < datetime.utcnow():
            errors.append(
                {
                    "field": "due_date",
                    "message": "截止日期不能是过去时间",
                    "code": "DUE_DATE_IN_PAST",
                }
            )

        # 检查是否过于遥远（超过10年）
        max_date = datetime.utcnow() + timedelta(days=365 * 10)
        if due_date > max_date:
            errors.append(
                {
                    "field": "due_date",
                    "message": "截止日期不能超过10年",
                    "code": "DUE_DATE_TOO_FAR",
                }
            )

        return errors

    async def _validate_tags(self, tags: List[str]) -> List[Dict[str, str]]:
        """验证标签"""
        errors = []

        # 数量限制
        if len(tags) > 10:
            errors.append(
                {"field": "tags", "message": "标签数量不能超过10个", "code": "TOO_MANY_TAGS"}
            )

        # 标签格式验证
        tag_pattern = re.compile(r"^[a-zA-Z0-9\u4e00-\u9fa5_-]+$")
        for i, tag in enumerate(tags):
            tag = tag.strip()

            if not tag:
                errors.append(
                    {"field": f"tags[{i}]", "message": "标签不能为空", "code": "EMPTY_TAG"}
                )
                continue

            if len(tag) > 20:
                errors.append(
                    {
                        "field": f"tags[{i}]",
                        "message": "标签长度不能超过20个字符",
                        "code": "TAG_TOO_LONG",
                    }
                )

            if not tag_pattern.match(tag):
                errors.append(
                    {
                        "field": f"tags[{i}]",
                        "message": "标签只能包含字母、数字、中文、下划线和连字符",
                        "code": "INVALID_TAG_FORMAT",
                    }
                )

        # 检查重复标签
        unique_tags = set(tag.lower().strip() for tag in tags)
        if len(unique_tags) != len(tags):
            errors.append(
                {"field": "tags", "message": "标签列表包含重复项", "code": "DUPLICATE_TAGS"}
            )

        return errors

    async def _validate_user_task_quota(self, user_id: str) -> List[Dict[str, str]]:
        """验证用户任务配额"""
        errors = []

        try:
            # 统计用户当前任务总数
            total_tasks = (
                await self.db.query(Task)
                .filter(
                    and_(
                        or_(Task.created_by == user_id, Task.assignee_id == user_id),
                        Task.is_deleted == False,
                    )
                )
                .count()
            )

            # 检查任务配额限制
            max_tasks = 1000  # 可以从配置中获取
            if total_tasks >= max_tasks:
                errors.append(
                    {
                        "field": "user_quota",
                        "message": f"用户任务数量已达上限({max_tasks})",
                        "code": "USER_QUOTA_EXCEEDED",
                    }
                )

        except Exception as e:
            errors.append(
                {
                    "field": "user_quota",
                    "message": f"验证用户配额时发生错误: {str(e)}",
                    "code": "QUOTA_VALIDATION_ERROR",
                }
            )

        return errors

    # === 状态转换验证 ===

    async def validate_status_transition(
        self, task: Task, new_status: str, user_id: str
    ) -> Dict[str, Any]:
        """
        验证状态转换

        Args:
            task: 任务对象
            new_status: 新状态
            user_id: 操作用户ID

        Returns:
            验证结果

        Raises:
            TaskValidationError: 验证失败
        """
        errors = []

        # 1. 检查状态转换是否有效
        if not task.can_transition_to(new_status):
            errors.append(
                {
                    "field": "status",
                    "message": f"无法从 {task.status} 转换到 {new_status}",
                    "code": "INVALID_STATUS_TRANSITION",
                }
            )

        # 2. 检查权限
        permission_errors = await self._validate_status_change_permission(task, user_id)
        errors.extend(permission_errors)

        # 3. 检查依赖关系
        if new_status == TaskStatus.DONE.value:
            dependency_errors = await self._validate_completion_dependencies(task)
            errors.extend(dependency_errors)

        # 4. 检查任务完整性
        if new_status == TaskStatus.IN_REVIEW.value:
            completeness_errors = await self._validate_task_completeness(task)
            errors.extend(completeness_errors)

        if errors:
            raise TaskValidationError(
                message="状态转换验证失败", code="STATUS_TRANSITION_FAILED"
            )

        return {"valid": True}

    async def _validate_status_change_permission(
        self, task: Task, user_id: str
    ) -> List[Dict[str, str]]:
        """验证状态变更权限"""
        errors = []

        # 创建者和分配者可以更改状态
        if task.created_by != user_id and task.assignee_id != user_id:
            # 检查是否是项目管理员
            if task.project_id:
                member = (
                    await self.db.query(ProjectMember)
                    .filter(
                        and_(
                            ProjectMember.project_id == task.project_id,
                            ProjectMember.user_id == user_id,
                            ProjectMember.role.in_(
                                [MemberRole.OWNER.value, MemberRole.ADMIN.value]
                            ),
                        )
                    )
                    .first()
                )

                if not member:
                    errors.append(
                        {
                            "field": "permission",
                            "message": "没有更改任务状态的权限",
                            "code": "NO_STATUS_CHANGE_PERMISSION",
                        }
                    )
            else:
                errors.append(
                    {
                        "field": "permission",
                        "message": "没有更改任务状态的权限",
                        "code": "NO_STATUS_CHANGE_PERMISSION",
                    }
                )

        return errors

    async def _validate_completion_dependencies(
        self, task: Task
    ) -> List[Dict[str, str]]:
        """验证完成依赖关系"""
        errors = []

        try:
            # 检查前置依赖任务是否都已完成
            incomplete_dependencies = (
                await self.db.query(Task)
                .join(TaskDependency, Task.id == TaskDependency.dependency_id)
                .filter(
                    and_(
                        TaskDependency.task_id == str(task.id),
                        TaskDependency.dependency_type == "blocks",
                        Task.status != TaskStatus.DONE.value,
                        Task.is_deleted == False,
                    )
                )
                .all()
            )

            if incomplete_dependencies:
                dep_titles = [dep.title for dep in incomplete_dependencies]
                errors.append(
                    {
                        "field": "dependencies",
                        "message": f"以下前置任务未完成: {', '.join(dep_titles)}",
                        "code": "INCOMPLETE_DEPENDENCIES",
                    }
                )

        except Exception as e:
            errors.append(
                {
                    "field": "dependencies",
                    "message": f"验证依赖关系时发生错误: {str(e)}",
                    "code": "DEPENDENCY_VALIDATION_ERROR",
                }
            )

        return errors

    async def _validate_task_completeness(self, task: Task) -> List[Dict[str, str]]:
        """验证任务完整性"""
        errors = []

        # 检查任务是否有描述
        if not task.description or not task.description.strip():
            errors.append(
                {
                    "field": "description",
                    "message": "提交审查的任务必须有描述",
                    "code": "DESCRIPTION_REQUIRED_FOR_REVIEW",
                }
            )

        # 检查是否有分配者
        if not task.assignee_id:
            errors.append(
                {
                    "field": "assignee",
                    "message": "提交审查的任务必须有分配者",
                    "code": "ASSIGNEE_REQUIRED_FOR_REVIEW",
                }
            )

        return errors

    # === 依赖关系验证 ===

    async def validate_dependency_addition(
        self, task_id: str, dependency_id: str, dependency_type: str
    ) -> Dict[str, Any]:
        """
        验证依赖关系添加

        Args:
            task_id: 任务ID
            dependency_id: 依赖任务ID
            dependency_type: 依赖类型

        Returns:
            验证结果

        Raises:
            TaskValidationError: 验证失败
        """
        errors = []

        # 1. 检查任务是否存在
        task = await self.db.query(Task).filter(Task.id == task_id).first()
        dependency_task = (
            await self.db.query(Task).filter(Task.id == dependency_id).first()
        )

        if not task:
            errors.append(
                {"field": "task_id", "message": "任务不存在", "code": "TASK_NOT_FOUND"}
            )

        if not dependency_task:
            errors.append(
                {
                    "field": "dependency_id",
                    "message": "依赖任务不存在",
                    "code": "DEPENDENCY_TASK_NOT_FOUND",
                }
            )

        if errors:
            raise TaskValidationError(
                message="依赖关系验证失败", code="DEPENDENCY_VALIDATION_FAILED"
            )

        # 2. 检查是否会形成循环依赖
        if await self._would_create_cycle(task_id, dependency_id):
            errors.append(
                {
                    "field": "dependency",
                    "message": "添加此依赖会形成循环依赖",
                    "code": "CIRCULAR_DEPENDENCY",
                }
            )

        # 3. 检查是否已存在相同依赖
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
            errors.append(
                {
                    "field": "dependency",
                    "message": "依赖关系已存在",
                    "code": "DEPENDENCY_ALREADY_EXISTS",
                }
            )

        # 4. 检查项目兼容性
        if task.project_id != dependency_task.project_id:
            if task.project_id and dependency_task.project_id:
                errors.append(
                    {
                        "field": "dependency",
                        "message": "跨项目依赖需要特殊权限",
                        "code": "CROSS_PROJECT_DEPENDENCY",
                    }
                )

        if errors:
            raise TaskValidationError(
                message="依赖关系验证失败", code="DEPENDENCY_VALIDATION_FAILED"
            )

        return {"valid": True}

    async def _would_create_cycle(self, task_id: str, dependency_id: str) -> bool:
        """检查是否会创建循环依赖"""
        visited = set()
        path = set()

        async def dfs(current_id: str) -> bool:
            if current_id in path:
                return True
            if current_id in visited:
                return False

            visited.add(current_id)
            path.add(current_id)

            dependencies = (
                await self.db.query(TaskDependency.dependency_id)
                .filter(TaskDependency.task_id == current_id)
                .all()
            )

            for dep in dependencies:
                if await dfs(str(dep.dependency_id)):
                    return True

            path.remove(current_id)
            return False

        return await dfs(dependency_id)

    # === 批量操作验证 ===

    async def validate_bulk_operation(
        self, task_ids: List[str], operation: str, data: Dict[str, Any], user_id: str
    ) -> Dict[str, Any]:
        """
        验证批量操作

        Args:
            task_ids: 任务ID列表
            operation: 操作类型
            data: 操作数据
            user_id: 操作用户ID

        Returns:
            验证结果

        Raises:
            TaskValidationError: 验证失败
        """
        errors = []

        # 1. 检查操作类型
        valid_operations = ["update", "delete", "assign", "change_status"]
        if operation not in valid_operations:
            errors.append(
                {
                    "field": "operation",
                    "message": f"无效的操作类型: {operation}",
                    "code": "INVALID_OPERATION",
                }
            )

        # 2. 检查任务数量限制
        if len(task_ids) > 100:
            errors.append(
                {
                    "field": "task_ids",
                    "message": "批量操作任务数量不能超过100",
                    "code": "TOO_MANY_TASKS",
                }
            )

        # 3. 检查任务是否存在
        tasks = await self.db.query(Task).filter(Task.id.in_(task_ids)).all()

        found_ids = {str(task.id) for task in tasks}
        missing_ids = set(task_ids) - found_ids

        if missing_ids:
            errors.append(
                {
                    "field": "task_ids",
                    "message": f"以下任务不存在: {', '.join(missing_ids)}",
                    "code": "TASKS_NOT_FOUND",
                }
            )

        # 4. 检查权限
        for task in tasks:
            if not await self._check_task_operation_permission(
                task, operation, user_id
            ):
                errors.append(
                    {
                        "field": "permission",
                        "message": f"没有对任务 {task.title} 执行 {operation} 操作的权限",
                        "code": "INSUFFICIENT_PERMISSION",
                    }
                )

        # 5. 操作特定验证
        if operation == "change_status" and "status" in data:
            for task in tasks:
                if not task.can_transition_to(data["status"]):
                    errors.append(
                        {
                            "field": "status",
                            "message": f"任务 {task.title} 无法转换到状态 {data['status']}",
                            "code": "INVALID_STATUS_TRANSITION",
                        }
                    )

        if errors:
            raise TaskValidationError(
                message="批量操作验证失败", code="BULK_OPERATION_VALIDATION_FAILED"
            )

        return {"valid": True, "tasks": tasks}

    async def _check_task_operation_permission(
        self, task: Task, operation: str, user_id: str
    ) -> bool:
        """检查任务操作权限"""
        # 创建者和分配者有基本权限
        if task.created_by == user_id or task.assignee_id == user_id:
            return True

        # 删除操作需要更高权限
        if operation == "delete":
            if task.created_by == user_id:
                return True

            # 检查项目管理员权限
            if task.project_id:
                member = (
                    await self.db.query(ProjectMember)
                    .filter(
                        and_(
                            ProjectMember.project_id == task.project_id,
                            ProjectMember.user_id == user_id,
                            ProjectMember.role.in_(
                                [MemberRole.OWNER.value, MemberRole.ADMIN.value]
                            ),
                        )
                    )
                    .first()
                )
                return member is not None

        # 其他操作检查项目成员权限
        if task.project_id:
            member = (
                await self.db.query(ProjectMember)
                .filter(
                    and_(
                        ProjectMember.project_id == task.project_id,
                        ProjectMember.user_id == user_id,
                    )
                )
                .first()
            )
            return member is not None

        return False


class DataConsistencyValidator:
    """
    数据一致性验证器
    ================

    验证数据的一致性和完整性
    """

    def __init__(self, db: Session):
        self.db = db

    async def validate_task_data_consistency(
        self, task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """验证任务数据一致性"""
        errors = []
        warnings = []

        # 1. 时间一致性验证
        time_errors = self._validate_time_consistency(task_data)
        errors.extend(time_errors)

        # 2. 进度一致性验证
        progress_errors = self._validate_progress_consistency(task_data)
        errors.extend(progress_errors)

        # 3. 工时一致性验证
        hour_errors = self._validate_hour_consistency(task_data)
        errors.extend(hour_errors)

        if errors:
            raise TaskValidationError(
                message="数据一致性验证失败", code="DATA_CONSISTENCY_FAILED"
            )

        return {"valid": True, "warnings": warnings}

    def _validate_time_consistency(
        self, task_data: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """验证时间一致性"""
        errors = []

        started_at = task_data.get("started_at")
        completed_at = task_data.get("completed_at")
        due_date = task_data.get("due_date")
        created_at = task_data.get("created_at")

        # 开始时间不能晚于完成时间
        if started_at and completed_at and started_at > completed_at:
            errors.append(
                {
                    "field": "time_consistency",
                    "message": "开始时间不能晚于完成时间",
                    "code": "INVALID_TIME_ORDER",
                }
            )

        # 完成时间不能早于创建时间
        if created_at and completed_at and completed_at < created_at:
            errors.append(
                {
                    "field": "time_consistency",
                    "message": "完成时间不能早于创建时间",
                    "code": "INVALID_COMPLETION_TIME",
                }
            )

        return errors

    def _validate_progress_consistency(
        self, task_data: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """验证进度一致性"""
        errors = []

        status = task_data.get("status")
        progress_percentage = task_data.get("progress_percentage", 0)

        # 状态和进度的一致性检查
        if status == TaskStatus.TODO.value and progress_percentage > 0:
            errors.append(
                {
                    "field": "progress_consistency",
                    "message": "待办任务的进度应该为0",
                    "code": "INVALID_TODO_PROGRESS",
                }
            )

        if status == TaskStatus.DONE.value and progress_percentage < 100:
            errors.append(
                {
                    "field": "progress_consistency",
                    "message": "已完成任务的进度应该为100%",
                    "code": "INVALID_DONE_PROGRESS",
                }
            )

        return errors

    def _validate_hour_consistency(
        self, task_data: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """验证工时一致性"""
        errors = []

        estimated_hours = task_data.get("estimated_hours")
        actual_hours = task_data.get("actual_hours")

        # 实际工时不应该过度超出预估工时
        if estimated_hours and actual_hours:
            if actual_hours > estimated_hours * 3:  # 超出3倍
                errors.append(
                    {
                        "field": "hour_consistency",
                        "message": "实际工时显著超出预估工时，请检查数据",
                        "code": "EXCESSIVE_ACTUAL_HOURS",
                    }
                )

        return errors


# === Pydantic 验证模型扩展 ===


class EnhancedTaskCreateRequest(BaseModel):
    """增强的任务创建请求模型"""

    title: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    priority: TaskPriority = TaskPriority.MEDIUM
    project_id: Optional[str] = None
    assignee_id: Optional[str] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[int] = Field(None, ge=0, le=1000)
    tags: List[str] = Field(default_factory=list, max_items=10)
    labels: Dict[str, Any] = Field(default_factory=dict)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)

    @validator("title")
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError("标题不能为空或只包含空格")

        # 检查特殊字符
        forbidden_chars = ["<", ">", '"', "'", "&"]
        if any(char in v for char in forbidden_chars):
            raise ValueError("标题包含不允许的特殊字符")

        return v.strip()

    @validator("due_date")
    def validate_due_date(cls, v):
        if v and v < datetime.utcnow():
            raise ValueError("截止日期不能是过去时间")

        max_date = datetime.utcnow() + timedelta(days=365 * 10)
        if v and v > max_date:
            raise ValueError("截止日期不能超过10年")

        return v

    @validator("tags")
    def validate_tags(cls, v):
        if not v:
            return []

        # 清理和验证标签
        cleaned_tags = []
        seen = set()

        for tag in v:
            tag = tag.strip().lower()
            if not tag:
                continue

            if len(tag) > 20:
                raise ValueError(f'标签 "{tag}" 长度不能超过20个字符')

            if not re.match(r"^[a-zA-Z0-9\u4e00-\u9fa5_-]+$", tag):
                raise ValueError(f'标签 "{tag}" 格式无效')

            if tag in seen:
                continue  # 跳过重复标签

            seen.add(tag)
            cleaned_tags.append(tag)

        return cleaned_tags

    @validator("custom_fields")
    def validate_custom_fields(cls, v):
        if not v:
            return {}

        # 限制自定义字段数量
        if len(v) > 20:
            raise ValueError("自定义字段数量不能超过20个")

        # 验证字段名
        for key in v.keys():
            if not re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", key):
                raise ValueError(f'自定义字段名 "{key}" 格式无效')

        return v

    @root_validator
    def validate_business_rules(cls, values):
        """业务规则验证"""
        # 这里可以添加跨字段的业务规则验证
        return values

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


# === 验证服务聚合器 ===


class TaskValidationService:
    """
    任务验证服务
    ============

    聚合所有验证功能的服务类
    """

    def __init__(self, db: Session):
        self.db = db
        self.business_validator = BusinessRuleValidator(db)
        self.consistency_validator = DataConsistencyValidator(db)

    async def validate_task_creation(
        self, task_data: Dict[str, Any], creator_id: str
    ) -> Dict[str, Any]:
        """完整的任务创建验证"""
        # 1. 业务规则验证
        business_result = await self.business_validator.validate_task_creation(
            title=task_data.get("title"),
            creator_id=creator_id,
            project_id=task_data.get("project_id"),
            assignee_id=task_data.get("assignee_id"),
            due_date=task_data.get("due_date"),
            tags=task_data.get("tags"),
            **task_data,
        )

        # 2. 数据一致性验证
        consistency_result = (
            await self.consistency_validator.validate_task_data_consistency(task_data)
        )

        return {
            "valid": True,
            "warnings": business_result.get("warnings", [])
            + consistency_result.get("warnings", []),
        }

    async def validate_task_update(
        self, task: Task, update_data: Dict[str, Any], user_id: str
    ) -> Dict[str, Any]:
        """完整的任务更新验证"""
        # 合并现有数据和更新数据
        merged_data = {
            "title": update_data.get("title", task.title),
            "description": update_data.get("description", task.description),
            "status": update_data.get("status", task.status),
            "priority": update_data.get("priority", task.priority),
            "assignee_id": update_data.get("assignee_id", task.assignee_id),
            "due_date": update_data.get("due_date", task.due_date),
            "estimated_hours": update_data.get("estimated_hours", task.estimated_hours),
            "actual_hours": update_data.get("actual_hours", task.actual_hours),
            "progress_percentage": update_data.get(
                "progress_percentage", task.progress_percentage
            ),
            "started_at": task.started_at,
            "completed_at": task.completed_at,
            "created_at": task.created_at,
        }

        # 状态转换验证
        if "status" in update_data and update_data["status"] != task.status:
            await self.business_validator.validate_status_transition(
                task, update_data["status"], user_id
            )

        # 数据一致性验证
        await self.consistency_validator.validate_task_data_consistency(merged_data)

        return {"valid": True}
