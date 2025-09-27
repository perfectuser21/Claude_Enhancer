"""
认证API路由
===========

提供用户认证相关的API端点
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
import bcrypt

from src.core.config import get_settings
from src.core.database import get_db
from src.core.dependencies import get_current_user, get_current_active_user
from src.api.models.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    TokenRefreshRequest,
    UserProfileResponse,
    UserUpdateRequest,
    PasswordChangeRequest,
    EmailVerificationRequest,
    PasswordResetRequest,
    PasswordResetConfirmRequest,
    UserStatsResponse,
)
from src.api.models.common import BaseResponse

# 这里需要导入实际的用户模型和服务
# from src.auth.models import User
# from src.auth.services import AuthService

router = APIRouter()
settings = get_settings()
security = HTTPBearer()


# ===== 用户注册和登录 =====


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
    description="创建新用户账户并返回访问令牌",
)
async def register_user(request: UserRegisterRequest, db: Session = Depends(get_db)):
    """
    用户注册
    ========

    创建新用户账户，包括：
    - 验证用户名和邮箱唯一性
    - 密码强度验证
    - 创建用户记录
    - 生成访问令牌
    """
    try:
        # 检查用户名是否已存在
        # existing_user = auth_service.get_user_by_username(request.username)
        # if existing_user:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="用户名已存在"
        #     )

        # 检查邮箱是否已存在
        # existing_email = auth_service.get_user_by_email(request.email)
        # if existing_email:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="邮箱已被注册"
        #     )

        # 加密密码
        password_hash = bcrypt.hashpw(
            request.password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        # 创建用户（这里是示例实现）
        user_data = {
            "username": request.username,
            "email": request.email,
            "password_hash": password_hash,
            "full_name": request.full_name,
            "avatar_url": request.avatar_url,
            "is_active": True,
            "is_verified": False,
            "created_at": datetime.utcnow(),
        }

        # 实际应该调用服务层创建用户
        # user = auth_service.create_user(user_data)

        # 生成JWT Token（示例实现）
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user_data["email"])}, expires_delta=access_token_expires
        )

        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_token = create_access_token(
            data={"sub": str(user_data["email"]), "type": "refresh"},
            expires_delta=refresh_token_expires,
        )

        return TokenResponse(
            success=True,
            message="注册成功",
            data={
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"注册失败: {str(e)}"
        )


@router.post(
    "/login", response_model=TokenResponse, summary="用户登录", description="用户登录验证并返回访问令牌"
)
async def login_user(request: UserLoginRequest, db: Session = Depends(get_db)):
    """
    用户登录
    ========

    验证用户凭据并返回JWT令牌
    """
    try:
        # 查找用户（示例实现）
        # user = auth_service.get_user_by_email(request.email)
        # if not user:
        #     raise HTTPException(
        #         status_code=status.HTTP_401_UNAUTHORIZED,
        #         detail="邮箱或密码错误"
        #     )

        # 验证密码（示例实现）
        # if not bcrypt.checkpw(request.password.encode('utf-8'), user.password_hash.encode('utf-8')):
        #     raise HTTPException(
        #         status_code=status.HTTP_401_UNAUTHORIZED,
        #         detail="邮箱或密码错误"
        #     )

        # 检查用户是否激活
        # if not user.is_active:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="账户已被禁用"
        #     )

        # 生成JWT Token（示例实现）
        token_expires = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        if request.remember_me:
            token_expires = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

        access_token = create_access_token(
            data={"sub": request.email}, expires_delta=timedelta(seconds=token_expires)
        )

        refresh_token = create_access_token(
            data={"sub": request.email, "type": "refresh"},
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )

        # 更新最后登录时间
        # auth_service.update_last_login(user.id)

        return TokenResponse(
            success=True,
            message="登录成功",
            data={
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": token_expires,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"登录失败: {str(e)}"
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="刷新令牌",
    description="使用刷新令牌获取新的访问令牌",
)
async def refresh_token(request: TokenRefreshRequest, db: Session = Depends(get_db)):
    """
    刷新访问令牌
    ============

    使用有效的刷新令牌获取新的访问令牌
    """
    try:
        # 验证刷新令牌
        payload = jwt.decode(
            request.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )

        email: str = payload.get("sub")
        token_type: str = payload.get("type")

        if email is None or token_type != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的刷新令牌"
            )

        # 验证用户是否存在且激活
        # user = auth_service.get_user_by_email(email)
        # if not user or not user.is_active:
        #     raise HTTPException(
        #         status_code=status.HTTP_401_UNAUTHORIZED,
        #         detail="用户不存在或已被禁用"
        #     )

        # 生成新的访问令牌
        access_token = create_access_token(
            data={"sub": email},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        return TokenResponse(
            success=True,
            message="令牌刷新成功",
            data={
                "access_token": access_token,
                "refresh_token": request.refresh_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            },
        )

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="无效的刷新令牌")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"令牌刷新失败: {str(e)}",
        )


# ===== 用户资料管理 =====


@router.get(
    "/profile",
    response_model=UserProfileResponse,
    summary="获取用户资料",
    description="获取当前登录用户的详细资料信息",
)
async def get_user_profile(current_user=Depends(get_current_active_user)):
    """
    获取用户资料
    ============

    返回当前用户的详细资料信息
    """
    try:
        return UserProfileResponse(
            success=True,
            message="获取用户资料成功",
            data=UserProfileResponse.UserData.from_orm(current_user),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户资料失败: {str(e)}",
        )


@router.put(
    "/profile",
    response_model=UserProfileResponse,
    summary="更新用户资料",
    description="更新当前用户的资料信息",
)
async def update_user_profile(
    request: UserUpdateRequest,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    更新用户资料
    ============

    更新当前用户的个人信息
    """
    try:
        # 更新用户信息（示例实现）
        update_data = request.dict(exclude_unset=True)

        # 实际应该调用服务层更新用户
        # updated_user = auth_service.update_user(current_user.id, update_data)

        return UserProfileResponse(
            success=True,
            message="用户资料更新成功",
            data=UserProfileResponse.UserData.from_orm(current_user),
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户资料失败: {str(e)}",
        )


@router.post(
    "/change-password",
    response_model=BaseResponse,
    summary="修改密码",
    description="修改当前用户的登录密码",
)
async def change_password(
    request: PasswordChangeRequest,
    current_user=Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    修改密码
    ========

    验证当前密码并设置新密码
    """
    try:
        # 验证当前密码（示例实现）
        # if not bcrypt.checkpw(request.current_password.encode('utf-8'), current_user.password_hash.encode('utf-8')):
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="当前密码错误"
        #     )

        # 加密新密码
        new_password_hash = bcrypt.hashpw(
            request.new_password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        # 更新密码（示例实现）
        # auth_service.update_password(current_user.id, new_password_hash)

        return BaseResponse(success=True, message="密码修改成功")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"修改密码失败: {str(e)}",
        )


# ===== 邮箱验证和密码重置 =====


@router.post(
    "/verify-email",
    response_model=BaseResponse,
    summary="验证邮箱",
    description="使用验证令牌验证用户邮箱",
)
async def verify_email(
    request: EmailVerificationRequest, db: Session = Depends(get_db)
):
    """
    验证邮箱
    ========

    使用邮件中的验证令牌激活用户邮箱
    """
    try:
        # 验证令牌并激活邮箱（示例实现）
        # auth_service.verify_email(request.token)

        return BaseResponse(success=True, message="邮箱验证成功")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"邮箱验证失败: {str(e)}"
        )


@router.post(
    "/reset-password",
    response_model=BaseResponse,
    summary="请求密码重置",
    description="发送密码重置邮件",
)
async def request_password_reset(
    request: PasswordResetRequest, db: Session = Depends(get_db)
):
    """
    请求密码重置
    ============

    向用户邮箱发送密码重置链接
    """
    try:
        # 发送重置邮件（示例实现）
        # auth_service.send_password_reset_email(request.email)

        return BaseResponse(success=True, message="密码重置邮件已发送，请检查您的邮箱")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"发送重置邮件失败: {str(e)}",
        )


@router.post(
    "/reset-password/confirm",
    response_model=BaseResponse,
    summary="确认密码重置",
    description="使用重置令牌设置新密码",
)
async def confirm_password_reset(
    request: PasswordResetConfirmRequest, db: Session = Depends(get_db)
):
    """
    确认密码重置
    ============

    使用重置令牌设置新密码
    """
    try:
        # 验证令牌并重置密码（示例实现）
        # auth_service.reset_password(request.token, request.new_password)

        return BaseResponse(success=True, message="密码重置成功")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"密码重置失败: {str(e)}"
        )


@router.post(
    "/logout",
    response_model=BaseResponse,
    summary="用户登出",
    description="登出当前用户（可选：撤销令牌）",
)
async def logout_user(current_user=Depends(get_current_user)):
    """
    用户登出
    ========

    登出当前用户并可选择性撤销令牌
    """
    try:
        # 可以在这里实现令牌黑名单逻辑
        # auth_service.logout_user(current_user.id)

        return BaseResponse(success=True, message="登出成功")

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"登出失败: {str(e)}"
        )


# ===== 用户统计 =====


@router.get(
    "/stats",
    response_model=UserStatsResponse,
    summary="获取用户统计",
    description="获取当前用户的统计信息",
)
async def get_user_stats(
    current_user=Depends(get_current_active_user), db: Session = Depends(get_db)
):
    """
    获取用户统计
    ============

    返回用户的任务、项目等统计信息
    """
    try:
        # 获取用户统计数据（示例实现）
        stats = UserStatsResponse.UserStats(
            total_tasks=0,
            completed_tasks=0,
            in_progress_tasks=0,
            overdue_tasks=0,
            total_projects=0,
            active_projects=0,
            login_count=0,
            last_activity=datetime.utcnow(),
        )

        return UserStatsResponse(success=True, message="获取用户统计成功", data=stats)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户统计失败: {str(e)}",
        )


# ===== 辅助函数 =====


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建JWT访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt
