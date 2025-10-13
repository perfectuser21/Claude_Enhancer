"""
任务管理API路由
===============

提供任务管理相关的API端点
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.dependencies import get_current_active_user, get_task_service
from src.api.models.tasks import (
    TaskCreateRequest,
    TaskUpdateRequest,
    TaskResponse,
    TaskListResponse,
    TaskFilterParams,
    TaskCommentCreateRequest,
    TaskCommentResponse,
    TaskAttachmentResponse,
    TaskActivityResponse,
    TaskStatsResponse,
    TaskBulkUpdateRequest,
    TaskAssignRequest,
)
from src.api.models.common import (
    BaseResponse,
    PaginationParams,
    BulkOperationRequest,
    BulkOperationResponse,
    FileUploadResponse,
)

router = APIRouter()


# ===== 任务CRUD操作 =====


@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建任务",
    description="创建新的任务记录",
)
async def create_task(
    request: TaskCreateRequest,
    current_user=Depends(get_current_active_user),
    task_service=Depends(get_task_service),
):
    """
    创建任务
    ========

    创建新的任务记录，包括：
    - 基本信息设置
    - 分配管理
    - 时间管理
    - 标签和自定义字段
    """
    try:
        pass  # Auto-fixed empty block
        # 调用任务服务创建任务
        task = await task_service.create_task(
            user_id=current_user.id, task_data=request.dict()
        )

        return TaskResponse(
            success=True, message="任务创建成功", data=TaskResponse.TaskData.from_orm(task)
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建任务失败: {str(e)}",
        )


@router.get(
    "/",
    response_model=TaskListResponse,
    summary="获取任务列表",
    description="获取任务列表，支持分页、过滤和搜索",
)
async def get_tasks(
    pagination: PaginationParams = Depends(),
    filters: TaskFilterParams = Depends(),
    current_user=Depends(get_current_active_user),
    task_service=Depends(get_task_service),
):
    """
    获取任务列表
    ============

    支持功能：
    - 分页查询
    - 多条件过滤
    - 关键词搜索
    - 排序
    """
    try:
        pass  # Auto-fixed empty block
        # 获取任务列表
        tasks, total = await task_service.get_tasks(
            user_id=current_user.id,
            offset=pagination.offset,
            limit=pagination.size,
            filters=filters.dict(exclude_unset=True),
        )

        # 构建分页元信息
        meta = {
            "page": pagination.page,
            "size": pagination.size,
            "total": total,
            "pages": (total + pagination.size - 1) // pagination.size,
            "has_next": pagination.page * pagination.size < total,
            "has_prev": pagination.page > 1,
        }

        return TaskListResponse(
            success=True,
            message="获取任务列表成功",
            data=[TaskResponse.TaskData.from_orm(task) for task in tasks],
            meta=meta,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务列表失败: {str(e)}",
        )


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="获取任务详情",
    description="根据ID获取任务的详细信息",
)
async def get_task(
    task_id: UUID,
    current_user=Depends(get_current_active_user),
    task_service=Depends(get_task_service),
):
    """
    获取任务详情
    ============

    返回指定任务的完整信息，包括关联数据
    """
    try:
        task = await task_service.get_task_by_id(
            task_id=task_id, user_id=current_user.id
        )

        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")

        return TaskResponse(
            success=True, message="获取任务详情成功", data=TaskResponse.TaskData.from_orm(task)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务详情失败: {str(e)}",
        )


@router.put(
    "/{task_id}", response_model=TaskResponse, summary="更新任务", description="更新指定任务的信息"
)
async def update_task(
    task_id: UUID,
    request: TaskUpdateRequest,
    current_user=Depends(get_current_active_user),
    task_service=Depends(get_task_service),
):
    """
    更新任务
    ========

    支持部分更新任务信息
    """
    try:
        pass  # Auto-fixed empty block
        # 检查任务是否存在和权限
        task = await task_service.get_task_by_id(task_id, current_user.id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")

        # 更新任务
        updated_task = await task_service.update_task(
            task_id=task_id,
            user_id=current_user.id,
            update_data=request.dict(exclude_unset=True),
        )

        return TaskResponse(
            success=True,
            message="任务更新成功",
            data=TaskResponse.TaskData.from_orm(updated_task),
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新任务失败: {str(e)}",
        )


@router.delete(
    "/{task_id}", response_model=BaseResponse, summary="删除任务", description="删除指定的任务"
)
async def delete_task(
    task_id: UUID,
    current_user=Depends(get_current_active_user),
    task_service=Depends(get_task_service),
):
    """
    删除任务
    ========

    软删除任务记录，保留历史数据
    """
    try:
        pass  # Auto-fixed empty block
        # 检查任务是否存在和权限
        task = await task_service.get_task_by_id(task_id, current_user.id)
        if not task:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="任务不存在")

        # 删除任务
        await task_service.delete_task(task_id, current_user.id)

        return BaseResponse(success=True, message="任务删除成功")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除任务失败: {str(e)}",
        )


# ===== 任务状态管理 =====


@router.patch(
    "/{task_id}/status",
    response_model=TaskResponse,
    summary="更新任务状态",
    description="更新任务的状态",
)
async def update_task_status(
    task_id: UUID,
    status: str = Query(..., description="新状态"),
    current_user=Depends(get_current_active_user),
    task_service=Depends(get_task_service),
):
    """
    更新任务状态
    ============

    支持任务状态转换和进度更新
    """
    try:
        updated_task = await task_service.update_task_status(
            task_id=task_id, user_id=current_user.id, new_status=status
        )

        return TaskResponse(
            success=True,
            message="任务状态更新成功",
            data=TaskResponse.TaskData.from_orm(updated_task),
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新任务状态失败: {str(e)}",
        )


@router.patch(
    "/{task_id}/assign",
    response_model=TaskResponse,
    summary="分配任务",
    description="分配任务给指定用户",
)
async def assign_task(
    task_id: UUID,
    request: TaskAssignRequest,
    current_user=Depends(get_current_active_user),
    task_service=Depends(get_task_service),
):
    """
    分配任务
    ========

    分配任务给用户或取消分配
    """
    try:
        updated_task = await task_service.assign_task(
            task_id=task_id,
            assigner_id=current_user.id,
            assignee_id=request.assignee_id,
            notify=request.notify_assignee,
        )

        return TaskResponse(
            success=True,
            message="任务分配成功" if request.assignee_id else "任务分配已取消",
            data=TaskResponse.TaskData.from_orm(updated_task),
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"分配任务失败: {str(e)}",
        )


# ===== 任务评论 =====


@router.post(
    "/{task_id}/comments",
    response_model=TaskCommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="添加任务评论",
    description="为任务添加评论",
)
async def create_task_comment(
    task_id: UUID,
    request: TaskCommentCreateRequest,
    current_user=Depends(get_current_active_user),
    task_service=Depends(get_task_service),
):
    """
    添加任务评论
    ============

    支持普通评论和回复评论
    """
    try:
        comment = await task_service.create_comment(
            task_id=task_id, user_id=current_user.id, comment_data=request.dict()
        )

        return TaskCommentResponse(
            success=True,
            message="评论添加成功",
            data=TaskCommentResponse.CommentData.from_orm(comment),
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加评论失败: {str(e)}",
        )


@router.get(
    "/{task_id}/comments",
    response_model=List[TaskCommentResponse.CommentData],
    summary="获取任务评论",
    description="获取任务的所有评论",
)
async def get_task_comments(
    task_id: UUID,
    current_user=Depends(get_current_active_user),
    task_service=Depends(get_task_service),
):
    """
    获取任务评论
    ============

    返回任务的所有评论，按时间排序
    """
    try:
        comments = await task_service.get_task_comments(
            task_id=task_id, user_id=current_user.id
        )

        return [
            TaskCommentResponse.CommentData.from_orm(comment) for comment in comments
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取评论失败: {str(e)}",
        )


# ===== 任务附件 =====


@router.post(
    "/{task_id}/attachments",
    response_model=TaskAttachmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="上传任务附件",
    description="为任务上传文件附件",
)
async def upload_task_attachment(
    task_id: UUID,
    file: UploadFile = File(...),
    current_user=Depends(get_current_active_user),
    task_service=Depends(get_task_service),
):
    """
    上传任务附件
    ============

    支持多种文件类型的上传
    """
    try:
        attachment = await task_service.upload_attachment(
            task_id=task_id, user_id=current_user.id, file=file
        )

        return TaskAttachmentResponse(
            success=True,
            message="附件上传成功",
            data=TaskAttachmentResponse.AttachmentData.from_orm(attachment),
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传附件失败: {str(e)}",
        )


@router.get(
    "/{task_id}/attachments",
    response_model=List[TaskAttachmentResponse.AttachmentData],
    summary="获取任务附件",
    description="获取任务的所有附件",
)
async def get_task_attachments(
    task_id: UUID,
    current_user=Depends(get_current_active_user),
    task_service=Depends(get_task_service),
):
    """
    获取任务附件
    ============

    返回任务的所有附件列表
    """
    try:
        attachments = await task_service.get_task_attachments(
            task_id=task_id, user_id=current_user.id
        )

        return [
            TaskAttachmentResponse.AttachmentData.from_orm(attachment)
            for attachment in attachments
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取附件失败: {str(e)}",
        )


# ===== 任务活动日志 =====


@router.get(
    "/{task_id}/activities",
    response_model=TaskActivityResponse,
    summary="获取任务活动日志",
    description="获取任务的所有活动记录",
)
async def get_task_activities(
    task_id: UUID,
    current_user=Depends(get_current_active_user),
    task_service=Depends(get_task_service),
):
    """
    获取任务活动日志
    ================

    返回任务的完整活动历史
    """
    try:
        activities = await task_service.get_task_activities(
            task_id=task_id, user_id=current_user.id
        )

        return TaskActivityResponse(
            success=True,
            message="获取活动日志成功",
            data=[
                TaskActivityResponse.ActivityData.from_orm(activity)
                for activity in activities
            ],
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取活动日志失败: {str(e)}",
        )


# ===== 批量操作 =====


@router.patch(
    "/bulk-update",
    response_model=BulkOperationResponse,
    summary="批量更新任务",
    description="批量更新多个任务",
)
async def bulk_update_tasks(
    request: TaskBulkUpdateRequest,
    current_user=Depends(get_current_active_user),
    task_service=Depends(get_task_service),
):
    """
    批量更新任务
    ============

    支持批量更新任务的状态、分配等信息
    """
    try:
        results = await task_service.bulk_update_tasks(
            task_ids=request.task_ids,
            user_id=current_user.id,
            update_data=request.updates.dict(exclude_unset=True),
        )

        return BulkOperationResponse(
            success=True,
            message="批量更新完成",
            total=len(request.task_ids),
            success_count=len([r for r in results if r.get("success")]),
            failure_count=len([r for r in results if not r.get("success")]),
            results=results,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量更新失败: {str(e)}",
        )


@router.delete(
    "/bulk-delete",
    response_model=BulkOperationResponse,
    summary="批量删除任务",
    description="批量删除多个任务",
)
async def bulk_delete_tasks(
    request: BulkOperationRequest,
    current_user=Depends(get_current_active_user),
    task_service=Depends(get_task_service),
):
    """
    批量删除任务
    ============

    支持批量删除任务
    """
    try:
        results = await task_service.bulk_delete_tasks(
            task_ids=request.ids, user_id=current_user.id
        )

        return BulkOperationResponse(
            success=True,
            message="批量删除完成",
            total=len(request.ids),
            success_count=len([r for r in results if r.get("success")]),
            failure_count=len([r for r in results if not r.get("success")]),
            results=results,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量删除失败: {str(e)}",
        )


# ===== 任务统计 =====


@router.get(
    "/stats",
    response_model=TaskStatsResponse,
    summary="获取任务统计",
    description="获取当前用户的任务统计信息",
)
async def get_task_stats(
    project_id: Optional[UUID] = Query(None, description="项目ID过滤"),
    current_user=Depends(get_current_active_user),
    task_service=Depends(get_task_service),
):
    """
    获取任务统计
    ============

    返回任务的统计信息，包括状态分布、优先级分布等
    """
    try:
        stats = await task_service.get_task_stats(
            user_id=current_user.id, project_id=project_id
        )

        return TaskStatsResponse(success=True, message="获取任务统计成功", data=stats)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务统计失败: {str(e)}",
        )
