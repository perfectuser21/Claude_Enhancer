"""
项目管理API路由
===============

提供项目管理相关的API端点
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.core.dependencies import get_current_active_user, get_project_service
from src.api.models.projects import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectResponse,
    ProjectListResponse,
    ProjectFilterParams,
    ProjectMemberAddRequest,
    ProjectMemberUpdateRequest,
    ProjectMemberResponse,
    ProjectStatsResponse,
    ProjectTimelineResponse,
    ProjectTemplateResponse,
    ProjectArchiveRequest,
    ProjectBulkUpdateRequest,
    ProjectInviteRequest,
)
from src.api.models.common import (
    BaseResponse,
    PaginationParams,
    BulkOperationRequest,
    BulkOperationResponse,
)

router = APIRouter()


# ===== 项目CRUD操作 =====


@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建项目",
    description="创建新的项目",
)
async def create_project(
    request: ProjectCreateRequest,
    current_user=Depends(get_current_active_user),
    project_service=Depends(get_project_service),
):
    """
    创建项目
    ========

    创建新项目，包括基本信息设置和权限配置
    """
    try:
        project = await project_service.create_project(
            user_id=current_user.id, project_data=request.dict()
        )

        return ProjectResponse(
            success=True,
            message="项目创建成功",
            data=ProjectResponse.ProjectData.from_orm(project),
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建项目失败: {str(e)}",
        )


@router.get(
    "/",
    response_model=ProjectListResponse,
    summary="获取项目列表",
    description="获取项目列表，支持分页和过滤",
)
async def get_projects(
    pagination: PaginationParams = Depends(),
    filters: ProjectFilterParams = Depends(),
    current_user=Depends(get_current_active_user),
    project_service=Depends(get_project_service),
):
    """
    获取项目列表
    ============

    支持分页、过滤和搜索功能
    """
    try:
        projects, total = await project_service.get_projects(
            user_id=current_user.id,
            offset=pagination.offset,
            limit=pagination.size,
            filters=filters.dict(exclude_unset=True),
        )

        meta = {
            "page": pagination.page,
            "size": pagination.size,
            "total": total,
            "pages": (total + pagination.size - 1) // pagination.size,
            "has_next": pagination.page * pagination.size < total,
            "has_prev": pagination.page > 1,
        }

        return ProjectListResponse(
            success=True,
            message="获取项目列表成功",
            data=[
                ProjectResponse.ProjectData.from_orm(project) for project in projects
            ],
            meta=meta,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取项目列表失败: {str(e)}",
        )


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="获取项目详情",
    description="获取指定项目的详细信息",
)
async def get_project(
    project_id: UUID,
    current_user=Depends(get_current_active_user),
    project_service=Depends(get_project_service),
):
    """
    获取项目详情
    ============

    返回项目的完整信息，包括统计数据和成员信息
    """
    try:
        project = await project_service.get_project_by_id(
            project_id=project_id, user_id=current_user.id
        )

        if not project:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="项目不存在")

        return ProjectResponse(
            success=True,
            message="获取项目详情成功",
            data=ProjectResponse.ProjectData.from_orm(project),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取项目详情失败: {str(e)}",
        )


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="更新项目",
    description="更新项目信息",
)
async def update_project(
    project_id: UUID,
    request: ProjectUpdateRequest,
    current_user=Depends(get_current_active_user),
    project_service=Depends(get_project_service),
):
    """
    更新项目
    ========

    支持部分更新项目信息
    """
    try:
        updated_project = await project_service.update_project(
            project_id=project_id,
            user_id=current_user.id,
            update_data=request.dict(exclude_unset=True),
        )

        return ProjectResponse(
            success=True,
            message="项目更新成功",
            data=ProjectResponse.ProjectData.from_orm(updated_project),
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新项目失败: {str(e)}",
        )


@router.delete(
    "/{project_id}", response_model=BaseResponse, summary="删除项目", description="删除指定项目"
)
async def delete_project(
    project_id: UUID,
    current_user=Depends(get_current_active_user),
    project_service=Depends(get_project_service),
):
    """
    删除项目
    ========

    软删除项目，保留历史数据
    """
    try:
        await project_service.delete_project(
            project_id=project_id, user_id=current_user.id
        )

        return BaseResponse(success=True, message="项目删除成功")

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除项目失败: {str(e)}",
        )


# ===== 项目成员管理 =====


@router.post(
    "/{project_id}/members",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="添加项目成员",
    description="向项目添加新成员",
)
async def add_project_member(
    project_id: UUID,
    request: ProjectMemberAddRequest,
    current_user=Depends(get_current_active_user),
    project_service=Depends(get_project_service),
):
    """
    添加项目成员
    ============

    向项目添加成员并设置角色权限
    """
    try:
        member = await project_service.add_member(
            project_id=project_id, adder_id=current_user.id, member_data=request.dict()
        )

        return ProjectMemberResponse(
            success=True,
            message="成员添加成功",
            data=ProjectMemberResponse.MemberData.from_orm(member),
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加成员失败: {str(e)}",
        )


@router.get(
    "/{project_id}/members",
    response_model=List[ProjectMemberResponse.MemberData],
    summary="获取项目成员",
    description="获取项目的所有成员",
)
async def get_project_members(
    project_id: UUID,
    current_user=Depends(get_current_active_user),
    project_service=Depends(get_project_service),
):
    """
    获取项目成员
    ============

    返回项目的所有成员列表
    """
    try:
        members = await project_service.get_project_members(
            project_id=project_id, user_id=current_user.id
        )

        return [ProjectMemberResponse.MemberData.from_orm(member) for member in members]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取项目成员失败: {str(e)}",
        )


@router.put(
    "/{project_id}/members/{user_id}",
    response_model=ProjectMemberResponse,
    summary="更新项目成员",
    description="更新项目成员的角色和权限",
)
async def update_project_member(
    project_id: UUID,
    user_id: UUID,
    request: ProjectMemberUpdateRequest,
    current_user=Depends(get_current_active_user),
    project_service=Depends(get_project_service),
):
    """
    更新项目成员
    ============

    更新成员的角色和权限设置
    """
    try:
        updated_member = await project_service.update_member(
            project_id=project_id,
            member_user_id=user_id,
            updater_id=current_user.id,
            update_data=request.dict(exclude_unset=True),
        )

        return ProjectMemberResponse(
            success=True,
            message="成员信息更新成功",
            data=ProjectMemberResponse.MemberData.from_orm(updated_member),
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新成员信息失败: {str(e)}",
        )


@router.delete(
    "/{project_id}/members/{user_id}",
    response_model=BaseResponse,
    summary="移除项目成员",
    description="从项目中移除成员",
)
async def remove_project_member(
    project_id: UUID,
    user_id: UUID,
    current_user=Depends(get_current_active_user),
    project_service=Depends(get_project_service),
):
    """
    移除项目成员
    ============

    从项目中移除指定成员
    """
    try:
        await project_service.remove_member(
            project_id=project_id, member_user_id=user_id, remover_id=current_user.id
        )

        return BaseResponse(success=True, message="成员移除成功")

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"移除成员失败: {str(e)}",
        )


# ===== 项目统计和报告 =====


@router.get(
    "/{project_id}/stats",
    response_model=ProjectStatsResponse,
    summary="获取项目统计",
    description="获取项目的统计信息",
)
async def get_project_stats(
    project_id: UUID,
    current_user=Depends(get_current_active_user),
    project_service=Depends(get_project_service),
):
    """
    获取项目统计
    ============

    返回项目的详细统计信息
    """
    try:
        stats = await project_service.get_project_stats(
            project_id=project_id, user_id=current_user.id
        )

        return ProjectStatsResponse(success=True, message="获取项目统计成功", data=stats)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取项目统计失败: {str(e)}",
        )


@router.get(
    "/{project_id}/timeline",
    response_model=ProjectTimelineResponse,
    summary="获取项目时间线",
    description="获取项目的活动时间线",
)
async def get_project_timeline(
    project_id: UUID,
    limit: int = Query(50, ge=1, le=100, description="返回事件数量"),
    current_user=Depends(get_current_active_user),
    project_service=Depends(get_project_service),
):
    """
    获取项目时间线
    ==============

    返回项目的活动历史时间线
    """
    try:
        timeline = await project_service.get_project_timeline(
            project_id=project_id, user_id=current_user.id, limit=limit
        )

        return ProjectTimelineResponse(success=True, message="获取项目时间线成功", data=timeline)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取项目时间线失败: {str(e)}",
        )


# ===== 项目模板 =====


@router.get(
    "/templates",
    response_model=ProjectTemplateResponse,
    summary="获取项目模板",
    description="获取可用的项目模板",
)
async def get_project_templates(
    category: Optional[str] = Query(None, description="模板分类过滤"),
    current_user=Depends(get_current_active_user),
    project_service=Depends(get_project_service),
):
    """
    获取项目模板
    ============

    返回可用的项目模板列表
    """
    try:
        templates = await project_service.get_project_templates(
            user_id=current_user.id, category=category
        )

        return ProjectTemplateResponse(success=True, message="获取项目模板成功", data=templates)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取项目模板失败: {str(e)}",
        )


@router.post(
    "/from-template/{template_id}",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="从模板创建项目",
    description="使用模板创建新项目",
)
async def create_project_from_template(
    template_id: UUID,
    name: str = Query(..., description="项目名称"),
    description: Optional[str] = Query(None, description="项目描述"),
    current_user=Depends(get_current_active_user),
    project_service=Depends(get_project_service),
):
    """
    从模板创建项目
    ==============

    使用预定义模板快速创建项目
    """
    try:
        project = await project_service.create_project_from_template(
            template_id=template_id,
            user_id=current_user.id,
            name=name,
            description=description,
        )

        return ProjectResponse(
            success=True,
            message="项目创建成功",
            data=ProjectResponse.ProjectData.from_orm(project),
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建项目失败: {str(e)}",
        )


# ===== 项目归档和恢复 =====


@router.patch(
    "/{project_id}/archive",
    response_model=BaseResponse,
    summary="归档项目",
    description="归档指定项目",
)
async def archive_project(
    project_id: UUID,
    request: ProjectArchiveRequest,
    current_user=Depends(get_current_active_user),
    project_service=Depends(get_project_service),
):
    """
    归档项目
    ========

    将项目标记为归档状态
    """
    try:
        await project_service.archive_project(
            project_id=project_id,
            user_id=current_user.id,
            reason=request.reason,
            backup_data=request.backup_data,
        )

        return BaseResponse(success=True, message="项目归档成功")

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"归档项目失败: {str(e)}",
        )


@router.patch(
    "/{project_id}/restore",
    response_model=BaseResponse,
    summary="恢复项目",
    description="恢复归档的项目",
)
async def restore_project(
    project_id: UUID,
    current_user=Depends(get_current_active_user),
    project_service=Depends(get_project_service),
):
    """
    恢复项目
    ========

    恢复归档状态的项目
    """
    try:
        await project_service.restore_project(
            project_id=project_id, user_id=current_user.id
        )

        return BaseResponse(success=True, message="项目恢复成功")

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"恢复项目失败: {str(e)}",
        )


# ===== 批量操作 =====


@router.patch(
    "/bulk-update",
    response_model=BulkOperationResponse,
    summary="批量更新项目",
    description="批量更新多个项目",
)
async def bulk_update_projects(
    request: ProjectBulkUpdateRequest,
    current_user=Depends(get_current_active_user),
    project_service=Depends(get_project_service),
):
    """
    批量更新项目
    ============

    支持批量更新项目信息
    """
    try:
        results = await project_service.bulk_update_projects(
            project_ids=request.project_ids,
            user_id=current_user.id,
            update_data=request.updates.dict(exclude_unset=True),
        )

        return BulkOperationResponse(
            success=True,
            message="批量更新完成",
            total=len(request.project_ids),
            success_count=len([r for r in results if r.get("success")]),
            failure_count=len([r for r in results if not r.get("success")]),
            results=results,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量更新失败: {str(e)}",
        )


# ===== 项目邀请 =====


@router.post(
    "/{project_id}/invite",
    response_model=BaseResponse,
    summary="邀请用户加入项目",
    description="通过邮箱邀请用户加入项目",
)
async def invite_to_project(
    project_id: UUID,
    request: ProjectInviteRequest,
    current_user=Depends(get_current_active_user),
    project_service=Depends(get_project_service),
):
    """
    邀请用户加入项目
    ================

    发送邀请邮件给指定用户
    """
    try:
        await project_service.invite_user(
            project_id=project_id,
            inviter_id=current_user.id,
            invite_data=request.dict(),
        )

        return BaseResponse(success=True, message="邀请发送成功")

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送邀请失败: {str(e)}",
        )
