"""
任务管理API路由
===============

提供完整的任务管理REST API：
- 基础CRUD操作
- 搜索和筛选
- 批量操作
- 状态管理
- 依赖关系管理
- 统计分析
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.auth.dependencies import get_current_user
from backend.models.user import User
from backend.core.cache import get_cache_manager, CacheManager

from src.services.task_service import (
    TaskService,
    TaskServiceConfig,
    TaskCreateRequest,
    TaskUpdateRequest,
    TaskSearchRequest,
    TaskResponse,
    TaskListResponse,
    BulkOperationRequest,
)
from src.repositories.task_repository import TaskRepository, TaskQueryBuilder
from src.task_management.models import TaskStatus, TaskPriority


# 创建路由器
router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


# 依赖注入
def get_task_service(
    db: Session = Depends(get_db), cache: CacheManager = Depends(get_cache_manager)
) -> TaskService:
    """获取任务服务实例"""
    repository = TaskRepository(db)
    config = TaskServiceConfig(
        max_tasks_per_user=1000,
        max_bulk_operation_size=100,
        default_cache_ttl=300,
        enable_activity_logging=True,
        enable_notifications=True,
    )
    return TaskService(db, repository, cache, config)


def get_task_query_builder(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> TaskQueryBuilder:
    """获取任务查询构建器"""
    return TaskQueryBuilder(db, str(current_user.id))


# === 基础CRUD操作 ===


@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建任务",
    description="创建新任务，支持分配给用户、设置项目、截止日期等",
)
async def create_task(
    request: TaskCreateRequest,
    task_service: TaskService = Depends(get_task_service),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    """
    创建新任务

    - **title**: 任务标题（必填）
    - **description**: 任务描述
    - **priority**: 优先级（low/medium/high/urgent）
    - **project_id**: 所属项目ID
    - **assignee_id**: 分配给的用户ID
    - **due_date**: 截止日期
    - **estimated_hours**: 预估工时
    - **tags**: 任务标签列表
    - **custom_fields**: 自定义字段
    """
    try:
        task = await task_service.create_task(request, str(current_user.id))
        return task
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建任务失败: {str(e)}",
        )


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="获取任务详情",
    description="获取指定任务的详细信息，包括关联数据",
)
async def get_task(
    task_id: str = Path(..., description="任务ID"),
    include_relations: bool = Query(True, description="是否包含关联数据"),
    task_service: TaskService = Depends(get_task_service),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    """
    获取任务详情

    返回包含以下信息的任务详情：
    - 基本任务信息
    - 分配者和创建者信息
    - 项目信息
    - 评论和附件数量
    - 依赖关系数量
    """
    task = await task_service.get_task(task_id, str(current_user.id), include_relations)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")
    return task


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="更新任务",
    description="更新任务信息，支持部分更新",
)
async def update_task(
    task_id: str = Path(..., description="任务ID"),
    request: TaskUpdateRequest = Body(...),
    task_service: TaskService = Depends(get_task_service),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    """
    更新任务

    支持更新的字段：
    - 基本信息（标题、描述、优先级）
    - 状态和进度
    - 分配信息
    - 时间信息（截止日期、工时）
    - 标签和自定义字段
    """
    try:
        task = await task_service.update_task(task_id, request, str(current_user.id))
        return task
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="删除任务",
    description="删除指定任务（软删除）",
)
async def delete_task(
    task_id: str = Path(..., description="任务ID"),
    hard_delete: bool = Query(False, description="是否硬删除"),
    task_service: TaskService = Depends(get_task_service),
    current_user: User = Depends(get_current_user),
):
    """
    删除任务

    默认执行软删除，可选择硬删除：
    - **软删除**: 标记为已删除，可恢复
    - **硬删除**: 永久删除，不可恢复
    """
    success = await task_service.delete_task(task_id, str(current_user.id), hard_delete)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")


# === 搜索和筛选 ===


@router.get(
    "/", response_model=TaskListResponse, summary="搜索任务", description="搜索和筛选任务，支持多种条件组合"
)
async def search_tasks(
    query: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[List[TaskStatus]] = Query(None, description="状态筛选"),
    priority: Optional[List[TaskPriority]] = Query(None, description="优先级筛选"),
    assignee_id: Optional[str] = Query(None, description="分配者筛选"),
    project_id: Optional[str] = Query(None, description="项目筛选"),
    tags: Optional[List[str]] = Query(None, description="标签筛选"),
    due_date_from: Optional[datetime] = Query(None, description="截止日期起始"),
    due_date_to: Optional[datetime] = Query(None, description="截止日期结束"),
    created_by: Optional[str] = Query(None, description="创建者筛选"),
    sort_by: str = Query("updated_at", description="排序字段"),
    sort_order: str = Query("desc", description="排序方向", regex="^(asc|desc)$"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小"),
    task_service: TaskService = Depends(get_task_service),
    current_user: User = Depends(get_current_user),
) -> TaskListResponse:
    """
    搜索和筛选任务

    支持的搜索条件：
    - **全文搜索**: 在标题、描述、标签中搜索
    - **状态筛选**: 按任务状态筛选
    - **优先级筛选**: 按优先级筛选
    - **用户筛选**: 按分配者或创建者筛选
    - **项目筛选**: 按项目筛选
    - **时间筛选**: 按截止日期范围筛选
    - **标签筛选**: 按标签筛选

    返回结果包含分页信息和搜索摘要。
    """
    search_request = TaskSearchRequest(
        query=query,
        status=status,
        priority=priority,
        assignee_id=assignee_id,
        project_id=project_id,
        tags=tags,
        due_date_from=due_date_from,
        due_date_to=due_date_to,
        created_by=created_by,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )

    return await task_service.search_tasks(search_request, str(current_user.id))


@router.get("/builder/query", summary="查询构建器", description="使用流畅接口查询任务")
async def query_tasks_with_builder(
    status: Optional[List[TaskStatus]] = Query(None),
    priority: Optional[List[TaskPriority]] = Query(None),
    assignee_id: Optional[str] = Query(None),
    project_id: Optional[str] = Query(None),
    tags: Optional[List[str]] = Query(None),
    overdue_only: bool = Query(False),
    include_assignee: bool = Query(False),
    include_project: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    builder: TaskQueryBuilder = Depends(get_task_query_builder),
):
    """
    使用查询构建器进行任务查询

    这是一个展示查询构建器使用的示例接口。
    """
    # 应用筛选条件
    if status:
        builder = builder.filter_by_status(status)

    if priority:
        builder = builder.filter_by_priority(priority)

    if assignee_id:
        builder = builder.filter_by_assignee(assignee_id)

    if project_id:
        builder = builder.filter_by_project(project_id)

    if tags:
        builder = builder.filter_by_tags(tags)

    if overdue_only:
        builder = builder.filter_overdue()

    # 包含关联数据
    if include_assignee:
        builder = builder.include_assignee()

    if include_project:
        builder = builder.include_project()

    # 排序
    builder = builder.order_by_priority().order_by_due_date().order_by_updated_at()

    # 执行分页查询
    result = await builder.paginate(page, page_size)

    return result


# === 状态管理 ===


@router.patch(
    "/{task_id}/status",
    response_model=TaskResponse,
    summary="更改任务状态",
    description="更改任务状态，支持状态流转验证",
)
async def change_task_status(
    task_id: str = Path(..., description="任务ID"),
    new_status: TaskStatus = Body(..., embed=True, description="新状态"),
    comment: Optional[str] = Body(None, embed=True, description="状态变更说明"),
    task_service: TaskService = Depends(get_task_service),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    """
    更改任务状态

    支持的状态流转：
    - TODO → IN_PROGRESS, CANCELLED
    - IN_PROGRESS → TODO, IN_REVIEW, BLOCKED, CANCELLED
    - IN_REVIEW → IN_PROGRESS, DONE, CANCELLED
    - BLOCKED → TODO, IN_PROGRESS, CANCELLED
    - DONE → IN_PROGRESS (重新打开)
    - CANCELLED → TODO (重新激活)
    """
    return await task_service.change_task_status(
        task_id, new_status, str(current_user.id), comment
    )


@router.get(
    "/status/transitions/{task_id}", summary="获取可用状态转换", description="获取任务可以转换到的状态列表"
)
async def get_available_status_transitions(
    task_id: str = Path(..., description="任务ID"),
    task_service: TaskService = Depends(get_task_service),
    current_user: User = Depends(get_current_user),
) -> Dict[str, List[str]]:
    """
    获取任务可用的状态转换

    返回当前任务可以转换到的状态列表。
    """
    task = await task_service.get_task(task_id, str(current_user.id), False)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")

    # 根据任务模型定义的状态转换规则
    valid_transitions = {
        TaskStatus.TODO: [TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED],
        TaskStatus.IN_PROGRESS: [
            TaskStatus.TODO,
            TaskStatus.IN_REVIEW,
            TaskStatus.BLOCKED,
            TaskStatus.CANCELLED,
        ],
        TaskStatus.IN_REVIEW: [
            TaskStatus.IN_PROGRESS,
            TaskStatus.DONE,
            TaskStatus.CANCELLED,
        ],
        TaskStatus.BLOCKED: [
            TaskStatus.TODO,
            TaskStatus.IN_PROGRESS,
            TaskStatus.CANCELLED,
        ],
        TaskStatus.DONE: [TaskStatus.IN_PROGRESS],
        TaskStatus.CANCELLED: [TaskStatus.TODO],
    }

    current_status = TaskStatus(task.status)
    available_transitions = valid_transitions.get(current_status, [])

    return {
        "current_status": current_status.value,
        "available_transitions": [status.value for status in available_transitions],
    }


# === 批量操作 ===


@router.post("/bulk", summary="批量操作任务", description="对多个任务执行批量操作")
async def bulk_operation(
    request: BulkOperationRequest,
    task_service: TaskService = Depends(get_task_service),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    批量操作任务

    支持的操作类型：
    - **update**: 批量更新任务字段
    - **delete**: 批量删除任务
    - **assign**: 批量分配任务
    - **change_status**: 批量更改状态

    返回操作结果统计和错误信息。
    """
    return await task_service.bulk_operation(request, str(current_user.id))


@router.patch("/bulk/status", summary="批量更改状态", description="批量更改多个任务的状态")
async def bulk_change_status(
    task_ids: List[str] = Body(..., description="任务ID列表"),
    new_status: TaskStatus = Body(..., description="新状态"),
    comment: Optional[str] = Body(None, description="状态变更说明"),
    task_service: TaskService = Depends(get_task_service),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    批量更改任务状态

    快捷方式，等同于批量操作的change_status操作。
    """
    request = BulkOperationRequest(
        task_ids=task_ids,
        operation="change_status",
        data={"status": new_status.value, "comment": comment},
    )

    return await task_service.bulk_operation(request, str(current_user.id))


# === 统计和分析 ===


@router.get("/statistics/user", summary="用户任务统计", description="获取当前用户的任务统计信息")
async def get_user_task_statistics(
    task_service: TaskService = Depends(get_task_service),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    获取用户任务统计

    包含以下统计信息：
    - 按状态分组的任务数量
    - 按优先级分组的任务数量
    - 预估工时和实际工时
    - 任务总数
    """
    return await task_service.get_user_task_summary(str(current_user.id))


@router.get(
    "/statistics/project/{project_id}", summary="项目任务统计", description="获取指定项目的任务统计信息"
)
async def get_project_task_statistics(
    project_id: str = Path(..., description="项目ID"),
    task_service: TaskService = Depends(get_task_service),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    获取项目任务统计

    包含项目任务的详细统计信息。
    """
    return await task_service.get_project_task_statistics(
        project_id, str(current_user.id)
    )


# === 任务依赖关系 ===


@router.get("/{task_id}/dependencies", summary="获取任务依赖关系", description="获取任务的依赖关系信息")
async def get_task_dependencies(
    task_id: str = Path(..., description="任务ID"),
    task_service: TaskService = Depends(get_task_service),
    current_user: User = Depends(get_current_user),
) -> Dict[str, List[TaskResponse]]:
    """
    获取任务依赖关系

    返回：
    - **dependencies**: 此任务依赖的其他任务
    - **dependents**: 依赖此任务的其他任务
    """
    # 首先验证任务访问权限
    task = await task_service.get_task(task_id, str(current_user.id), False)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")

    # 获取依赖关系
    repository = TaskRepository(next(get_db()))
    dependencies_data = await repository.get_task_dependencies(task_id)

    # 转换为响应模型
    result = {"dependencies": [], "dependents": []}

    for dep_task in dependencies_data["dependencies"]:
        result["dependencies"].append(await task_service._build_task_response(dep_task))

    for dep_task in dependencies_data["dependents"]:
        result["dependents"].append(await task_service._build_task_response(dep_task))

    return result


@router.post("/{task_id}/dependencies", summary="添加任务依赖", description="为任务添加依赖关系")
async def add_task_dependency(
    task_id: str = Path(..., description="任务ID"),
    dependency_id: str = Body(..., embed=True, description="依赖任务ID"),
    dependency_type: str = Body("blocks", embed=True, description="依赖类型"),
    notes: Optional[str] = Body(None, embed=True, description="备注"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    添加任务依赖关系

    依赖类型：
    - **blocks**: 阻塞依赖（必须完成前置任务）
    - **links**: 链接依赖（相关任务关联）
    """
    # 验证权限
    task_service = get_task_service(db)
    task = await task_service.get_task(task_id, str(current_user.id), False)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")

    dependency_task = await task_service.get_task(
        dependency_id, str(current_user.id), False
    )
    if not dependency_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="依赖任务不存在")

    try:
        repository = TaskRepository(db)
        dependency = await repository.add_task_dependency(
            task_id, dependency_id, dependency_type, notes
        )

        return {
            "id": str(dependency.id),
            "task_id": task_id,
            "dependency_id": dependency_id,
            "dependency_type": dependency_type,
            "notes": notes,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{task_id}/dependencies/{dependency_id}", summary="移除任务依赖", description="移除任务的依赖关系"
)
async def remove_task_dependency(
    task_id: str = Path(..., description="任务ID"),
    dependency_id: str = Path(..., description="依赖任务ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    移除任务依赖关系
    """
    # 验证权限
    task_service = get_task_service(db)
    task = await task_service.get_task(task_id, str(current_user.id), False)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")

    repository = TaskRepository(db)
    success = await repository.remove_task_dependency(task_id, dependency_id)

    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="依赖关系不存在")

    return {"message": "依赖关系已移除"}


# === 标签管理 ===


@router.get("/tags/popular", summary="获取热门标签", description="获取最常用的任务标签")
async def get_popular_tags(
    project_id: Optional[str] = Query(None, description="项目筛选"),
    limit: int = Query(20, ge=1, le=100, description="结果数量限制"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """
    获取热门标签

    返回按使用频率排序的标签列表。
    """
    repository = TaskRepository(db)
    return await repository.get_popular_tags(
        user_id=str(current_user.id), project_id=project_id, limit=limit
    )


@router.get("/tags/{tag}/tasks", summary="按标签搜索任务", description="获取包含指定标签的任务")
async def get_tasks_by_tag(
    tag: str = Path(..., description="标签名称"),
    match_all: bool = Query(True, description="是否匹配所有标签"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    按标签搜索任务

    支持单个标签或多个标签的搜索。
    """
    repository = TaskRepository(db)
    tags = [tag]  # 这里可以扩展为支持多个标签

    tasks = await repository.search_tasks_by_tags(
        tags=tags, user_id=str(current_user.id), match_all=match_all
    )

    # 简单分页处理
    start = (page - 1) * page_size
    end = start + page_size
    paginated_tasks = tasks[start:end]

    # 构建响应
    task_service = get_task_service(db)
    task_responses = []
    for task in paginated_tasks:
        task_responses.append(await task_service._build_task_response(task))

    return {
        "tasks": task_responses,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_count": len(tasks),
            "total_pages": (len(tasks) + page_size - 1) // page_size,
        },
        "tag": tag,
    }


# === 特殊查询 ===


@router.get("/overdue", summary="获取逾期任务", description="获取当前用户的逾期任务列表")
async def get_overdue_tasks(
    project_id: Optional[str] = Query(None, description="项目筛选"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[TaskResponse]:
    """
    获取逾期任务

    返回已过截止日期且未完成的任务。
    """
    repository = TaskRepository(db)
    tasks = await repository.get_overdue_tasks(
        user_id=str(current_user.id), project_id=project_id
    )

    task_service = get_task_service(db)
    result = []
    for task in tasks:
        result.append(await task_service._build_task_response(task))

    return result


@router.get("/due-soon", summary="获取即将到期的任务", description="获取即将到期的任务列表")
async def get_tasks_due_soon(
    days_ahead: int = Query(7, ge=1, le=30, description="提前天数"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> List[TaskResponse]:
    """
    获取即将到期的任务

    返回在指定天数内到期的任务。
    """
    repository = TaskRepository(db)
    tasks = await repository.get_tasks_due_soon(
        days_ahead=days_ahead, user_id=str(current_user.id)
    )

    task_service = get_task_service(db)
    result = []
    for task in tasks:
        result.append(await task_service._build_task_response(task))

    return result


# === 健康检查和信息 ===


@router.get("/health", summary="健康检查", description="检查任务管理系统的健康状态")
async def health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    任务管理系统健康检查

    返回系统状态和基本统计信息。
    """
    try:
        # 检查数据库连接
        repository = TaskRepository(db)
        total_tasks = await repository.count()

        # 获取基本统计
        stats = await repository.get_task_statistics()

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected",
            "total_tasks": total_tasks,
            "statistics": {
                "total_tasks": stats["total_count"],
                "completion_rate": stats["completion_rate"],
                "overdue_count": stats["overdue_count"],
            },
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
            },
        )


# === 导出功能 ===


@router.get("/export", summary="导出任务数据", description="导出用户的任务数据")
async def export_tasks(
    format: str = Query("json", regex="^(json|csv)$", description="导出格式"),
    project_id: Optional[str] = Query(None, description="项目筛选"),
    status: Optional[List[TaskStatus]] = Query(None, description="状态筛选"),
    date_from: Optional[datetime] = Query(None, description="创建日期起始"),
    date_to: Optional[datetime] = Query(None, description="创建日期结束"),
    task_service: TaskService = Depends(get_task_service),
    current_user: User = Depends(get_current_user),
):
    """
    导出任务数据

    支持JSON和CSV格式导出。
    """
    # 构建搜索条件
    search_request = TaskSearchRequest(
        status=status,
        project_id=project_id,
        due_date_from=date_from,
        due_date_to=date_to,
        page=1,
        page_size=10000,  # 大数量导出
    )

    # 获取任务数据
    result = await task_service.search_tasks(search_request, str(current_user.id))
    tasks = result.tasks

    if format == "json":
        return {
            "exported_at": datetime.utcnow().isoformat(),
            "total_count": len(tasks),
            "tasks": [task.dict() for task in tasks],
        }
    elif format == "csv":
        # 这里应该返回CSV格式的响应
        # 简化实现，实际应该使用适当的CSV库
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # 写入标题行
        writer.writerow(
            [
                "ID",
                "Title",
                "Description",
                "Status",
                "Priority",
                "Assignee",
                "Project",
                "Due Date",
                "Created At",
            ]
        )

        # 写入数据行
        for task in tasks:
            writer.writerow(
                [
                    task.id,
                    task.title,
                    task.description or "",
                    task.status.value,
                    task.priority.value,
                    task.assignee_name or "",
                    task.project_name or "",
                    task.due_date.isoformat() if task.due_date else "",
                    task.created_at.isoformat(),
                ]
            )

        output.seek(0)

        from fastapi.responses import StreamingResponse

        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=tasks.csv"},
        )
