"""
通知系统API路由
===============

提供通知管理相关的API端点
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from src.core.database import get_db
from src.core.dependencies import get_current_active_user, get_notification_service
from src.api.models.common import BaseResponse, PaginationParams
from datetime import datetime
from typing import Dict, Any

router = APIRouter()


# ===== 通知数据模型 =====


class NotificationResponse(BaseResponse):
    """通知响应"""

    class NotificationData(BaseModel):
        id: UUID = Field(description="通知ID")
        title: str = Field(description="通知标题")
        content: str = Field(description="通知内容")
        type: str = Field(description="通知类型")
        is_read: bool = Field(description="是否已读")
        read_at: Optional[datetime] = Field(description="阅读时间")
        related_entity_type: Optional[str] = Field(description="关联实体类型")
        related_entity_id: Optional[UUID] = Field(description="关联实体ID")
        action_url: Optional[str] = Field(description="行动URL")
        metadata: Dict[str, Any] = Field(description="额外数据")
        created_at: datetime = Field(description="创建时间")

        class Config:
            from_attributes = True

    data: NotificationData = Field(description="通知数据")


class NotificationListResponse(BaseResponse):
    """通知列表响应"""

    data: List[NotificationResponse.NotificationData] = Field(description="通知列表")
    meta: Dict[str, Any] = Field(description="分页信息")


class NotificationStatsResponse(BaseResponse):
    """通知统计响应"""

    class NotificationStats(BaseModel):
        total_count: int = Field(description="总通知数")
        unread_count: int = Field(description="未读通知数")
        today_count: int = Field(description="今日通知数")
        by_type: Dict[str, int] = Field(description="按类型统计")

    data: NotificationStats = Field(description="通知统计")


class NotificationSettingsResponse(BaseResponse):
    """通知设置响应"""

    class NotificationSettings(BaseModel):
        email_notifications: bool = Field(description="邮件通知")
        push_notifications: bool = Field(description="推送通知")
        task_assignments: bool = Field(description="任务分配通知")
        task_updates: bool = Field(description="任务更新通知")
        project_updates: bool = Field(description="项目更新通知")
        comments: bool = Field(description="评论通知")
        mentions: bool = Field(description="提及通知")
        deadlines: bool = Field(description="截止日期提醒")
        daily_summary: bool = Field(description="每日摘要")

    data: NotificationSettings = Field(description="通知设置")


class NotificationSettingsUpdateRequest(BaseModel):
    """通知设置更新请求"""

    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    task_assignments: Optional[bool] = None
    task_updates: Optional[bool] = None
    project_updates: Optional[bool] = None
    comments: Optional[bool] = None
    mentions: Optional[bool] = None
    deadlines: Optional[bool] = None
    daily_summary: Optional[bool] = None


# ===== 获取通知 =====


@router.get(
    "/",
    response_model=NotificationListResponse,
    summary="获取通知列表",
    description="获取用户的通知列表，支持分页和过滤",
)
async def get_notifications(
    pagination: PaginationParams = Depends(),
    is_read: Optional[bool] = Query(None, description="是否已读过滤"),
    notification_type: Optional[str] = Query(None, description="通知类型过滤"),
    current_user=Depends(get_current_active_user),
    notification_service=Depends(get_notification_service),
):
    """
    获取通知列表
    ============

    支持分页查询和多种过滤条件
    """
    try:
        notifications, total = await notification_service.get_notifications(
            user_id=current_user.id,
            offset=pagination.offset,
            limit=pagination.size,
            is_read=is_read,
            notification_type=notification_type,
        )

        meta = {
            "page": pagination.page,
            "size": pagination.size,
            "total": total,
            "pages": (total + pagination.size - 1) // pagination.size,
            "has_next": pagination.page * pagination.size < total,
            "has_prev": pagination.page > 1,
        }

        return NotificationListResponse(
            success=True,
            message="获取通知列表成功",
            data=[
                NotificationResponse.NotificationData.from_orm(notif)
                for notif in notifications
            ],
            meta=meta,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取通知列表失败: {str(e)}",
        )


@router.get(
    "/{notification_id}",
    response_model=NotificationResponse,
    summary="获取通知详情",
    description="获取指定通知的详细信息",
)
async def get_notification(
    notification_id: UUID,
    current_user=Depends(get_current_active_user),
    notification_service=Depends(get_notification_service),
):
    """
    获取通知详情
    ============

    返回指定通知的详细信息
    """
    try:
        notification = await notification_service.get_notification_by_id(
            notification_id=notification_id, user_id=current_user.id
        )

        if not notification:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="通知不存在")

        return NotificationResponse(
            success=True,
            message="获取通知详情成功",
            data=NotificationResponse.NotificationData.from_orm(notification),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取通知详情失败: {str(e)}",
        )


# ===== 通知状态管理 =====


@router.patch(
    "/{notification_id}/read",
    response_model=BaseResponse,
    summary="标记通知为已读",
    description="标记指定通知为已读状态",
)
async def mark_notification_as_read(
    notification_id: UUID,
    current_user=Depends(get_current_active_user),
    notification_service=Depends(get_notification_service),
):
    """
    标记通知为已读
    ==============

    将指定通知标记为已读状态
    """
    try:
        await notification_service.mark_as_read(
            notification_id=notification_id, user_id=current_user.id
        )

        return BaseResponse(success=True, message="通知已标记为已读")

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"标记通知失败: {str(e)}",
        )


@router.patch(
    "/{notification_id}/unread",
    response_model=BaseResponse,
    summary="标记通知为未读",
    description="标记指定通知为未读状态",
)
async def mark_notification_as_unread(
    notification_id: UUID,
    current_user=Depends(get_current_active_user),
    notification_service=Depends(get_notification_service),
):
    """
    标记通知为未读
    ==============

    将指定通知标记为未读状态
    """
    try:
        await notification_service.mark_as_unread(
            notification_id=notification_id, user_id=current_user.id
        )

        return BaseResponse(success=True, message="通知已标记为未读")

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"标记通知失败: {str(e)}",
        )


@router.patch(
    "/mark-all-read",
    response_model=BaseResponse,
    summary="标记所有通知为已读",
    description="将用户的所有未读通知标记为已读",
)
async def mark_all_notifications_as_read(
    current_user=Depends(get_current_active_user),
    notification_service=Depends(get_notification_service),
):
    """
    标记所有通知为已读
    ==================

    将用户的所有未读通知批量标记为已读
    """
    try:
        count = await notification_service.mark_all_as_read(user_id=current_user.id)

        return BaseResponse(success=True, message=f"已标记{count}条通知为已读")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量标记失败: {str(e)}",
        )


# ===== 删除通知 =====


@router.delete(
    "/{notification_id}",
    response_model=BaseResponse,
    summary="删除通知",
    description="删除指定的通知",
)
async def delete_notification(
    notification_id: UUID,
    current_user=Depends(get_current_active_user),
    notification_service=Depends(get_notification_service),
):
    """
    删除通知
    ========

    删除指定的通知记录
    """
    try:
        await notification_service.delete_notification(
            notification_id=notification_id, user_id=current_user.id
        )

        return BaseResponse(success=True, message="通知删除成功")

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除通知失败: {str(e)}",
        )


@router.delete(
    "/clear-read",
    response_model=BaseResponse,
    summary="清除已读通知",
    description="删除所有已读的通知",
)
async def clear_read_notifications(
    current_user=Depends(get_current_active_user),
    notification_service=Depends(get_notification_service),
):
    """
    清除已读通知
    ============

    删除用户所有已读的通知
    """
    try:
        count = await notification_service.clear_read_notifications(
            user_id=current_user.id
        )

        return BaseResponse(success=True, message=f"已清除{count}条已读通知")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清除通知失败: {str(e)}",
        )


# ===== 通知统计 =====


@router.get(
    "/stats",
    response_model=NotificationStatsResponse,
    summary="获取通知统计",
    description="获取用户的通知统计信息",
)
async def get_notification_stats(
    current_user=Depends(get_current_active_user),
    notification_service=Depends(get_notification_service),
):
    """
    获取通知统计
    ============

    返回用户的通知统计信息
    """
    try:
        stats = await notification_service.get_notification_stats(
            user_id=current_user.id
        )

        return NotificationStatsResponse(success=True, message="获取通知统计成功", data=stats)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取通知统计失败: {str(e)}",
        )


# ===== 通知设置 =====


@router.get(
    "/settings",
    response_model=NotificationSettingsResponse,
    summary="获取通知设置",
    description="获取用户的通知偏好设置",
)
async def get_notification_settings(
    current_user=Depends(get_current_active_user),
    notification_service=Depends(get_notification_service),
):
    """
    获取通知设置
    ============

    返回用户的通知偏好配置
    """
    try:
        settings = await notification_service.get_user_notification_settings(
            user_id=current_user.id
        )

        return NotificationSettingsResponse(
            success=True, message="获取通知设置成功", data=settings
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取通知设置失败: {str(e)}",
        )


@router.put(
    "/settings",
    response_model=NotificationSettingsResponse,
    summary="更新通知设置",
    description="更新用户的通知偏好设置",
)
async def update_notification_settings(
    request: NotificationSettingsUpdateRequest,
    current_user=Depends(get_current_active_user),
    notification_service=Depends(get_notification_service),
):
    """
    更新通知设置
    ============

    更新用户的通知偏好配置
    """
    try:
        updated_settings = await notification_service.update_notification_settings(
            user_id=current_user.id, settings=request.dict(exclude_unset=True)
        )

        return NotificationSettingsResponse(
            success=True, message="通知设置更新成功", data=updated_settings
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新通知设置失败: {str(e)}",
        )


# ===== 实时通知 =====


@router.get(
    "/realtime/unread-count", summary="获取未读通知数量", description="获取用户的未读通知数量（用于实时更新）"
)
async def get_unread_count(
    current_user=Depends(get_current_active_user),
    notification_service=Depends(get_notification_service),
):
    """
    获取未读通知数量
    ================

    返回用户当前的未读通知数量，用于实时显示
    """
    try:
        count = await notification_service.get_unread_count(user_id=current_user.id)

        return {"success": True, "data": {"unread_count": count}}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取未读通知数量失败: {str(e)}",
        )


@router.get(
    "/realtime/latest",
    response_model=List[NotificationResponse.NotificationData],
    summary="获取最新通知",
    description="获取用户的最新通知（用于实时推送）",
)
async def get_latest_notifications(
    limit: int = Query(5, ge=1, le=20, description="返回数量"),
    since: Optional[datetime] = Query(None, description="起始时间"),
    current_user=Depends(get_current_active_user),
    notification_service=Depends(get_notification_service),
):
    """
    获取最新通知
    ============

    返回用户的最新通知，用于实时推送更新
    """
    try:
        notifications = await notification_service.get_latest_notifications(
            user_id=current_user.id, limit=limit, since=since
        )

        return [
            NotificationResponse.NotificationData.from_orm(notif)
            for notif in notifications
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取最新通知失败: {str(e)}",
        )
