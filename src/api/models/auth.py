"""
认证相关数据模型
===============

定义用户认证相关的请求和响应模型
"""

from typing import Optional, List
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, EmailStr, validator
from .common import BaseResponse


class UserRegisterRequest(BaseModel):
    """用户注册请求"""

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        regex="^[a-zA-Z0-9_-]+$",
        description="用户名，3-50个字符，只能包含字母、数字、下划线和连字符",
    )
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=8, max_length=128, description="密码，8-128个字符")
    confirm_password: str = Field(..., description="确认密码")
    full_name: Optional[str] = Field(None, max_length=100, description="真实姓名")
    avatar_url: Optional[str] = Field(None, description="头像URL")

    @validator("confirm_password")
    def passwords_match(cls, v, values, **kwargs):
        if "password" in values and v != values["password"]:
            raise ValueError("密码确认不匹配")
        return v

    @validator("password")
    def validate_password_strength(cls, v):
        """验证密码强度"""
        if len(v) < 8:
            raise ValueError("密码至少8个字符")

        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)

        if not has_upper:
            raise ValueError("密码必须包含至少一个大写字母")
        if not has_lower:
            raise ValueError("密码必须包含至少一个小写字母")
        if not has_digit:
            raise ValueError("密码必须包含至少一个数字")

        return v


class UserLoginRequest(BaseModel):
    """用户登录请求"""

    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., description="密码")
    remember_me: bool = Field(False, description="记住我")


class TokenResponse(BaseResponse):
    """Token响应"""

    access_token: str = Field(description="访问令牌")
    refresh_token: str = Field(description="刷新令牌")
    token_type: str = Field("bearer", description="令牌类型")
    expires_in: int = Field(description="过期时间（秒）")


class TokenRefreshRequest(BaseModel):
    """刷新令牌请求"""

    refresh_token: str = Field(..., description="刷新令牌")


class UserProfileResponse(BaseResponse):
    """用户资料响应"""

    class UserData(BaseModel):
        id: UUID = Field(description="用户ID")
        username: str = Field(description="用户名")
        email: str = Field(description="邮箱")
        full_name: Optional[str] = Field(description="真实姓名")
        avatar_url: Optional[str] = Field(description="头像URL")
        is_active: bool = Field(description="是否激活")
        is_verified: bool = Field(description="是否已验证邮箱")
        created_at: datetime = Field(description="创建时间")
        last_login: Optional[datetime] = Field(description="最后登录时间")
        role: str = Field(description="用户角色")

        class Config:
            from_attributes = True

    data: UserData = Field(description="用户数据")


class UserUpdateRequest(BaseModel):
    """用户信息更新请求"""

    full_name: Optional[str] = Field(None, max_length=100, description="真实姓名")
    avatar_url: Optional[str] = Field(None, description="头像URL")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")
    location: Optional[str] = Field(None, max_length=100, description="地理位置")
    website: Optional[str] = Field(None, description="个人网站")
    timezone: Optional[str] = Field(None, description="时区")


class PasswordChangeRequest(BaseModel):
    """密码修改请求"""

    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., min_length=8, max_length=128, description="新密码")
    confirm_new_password: str = Field(..., description="确认新密码")

    @validator("confirm_new_password")
    def passwords_match(cls, v, values, **kwargs):
        if "new_password" in values and v != values["new_password"]:
            raise ValueError("新密码确认不匹配")
        return v

    @validator("new_password")
    def validate_password_strength(cls, v):
        """验证密码强度"""
        if len(v) < 8:
            raise ValueError("密码至少8个字符")

        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)

        if not has_upper:
            raise ValueError("密码必须包含至少一个大写字母")
        if not has_lower:
            raise ValueError("密码必须包含至少一个小写字母")
        if not has_digit:
            raise ValueError("密码必须包含至少一个数字")

        return v


class EmailVerificationRequest(BaseModel):
    """邮箱验证请求"""

    token: str = Field(..., description="验证令牌")


class PasswordResetRequest(BaseModel):
    """密码重置请求"""

    email: EmailStr = Field(..., description="邮箱地址")


class PasswordResetConfirmRequest(BaseModel):
    """密码重置确认请求"""

    token: str = Field(..., description="重置令牌")
    new_password: str = Field(..., min_length=8, max_length=128, description="新密码")
    confirm_new_password: str = Field(..., description="确认新密码")

    @validator("confirm_new_password")
    def passwords_match(cls, v, values, **kwargs):
        if "new_password" in values and v != values["new_password"]:
            raise ValueError("密码确认不匹配")
        return v


class UserListResponse(BaseResponse):
    """用户列表响应"""

    class UserItem(BaseModel):
        id: UUID = Field(description="用户ID")
        username: str = Field(description="用户名")
        email: str = Field(description="邮箱")
        full_name: Optional[str] = Field(description="真实姓名")
        avatar_url: Optional[str] = Field(description="头像URL")
        is_active: bool = Field(description="是否激活")
        created_at: datetime = Field(description="创建时间")
        role: str = Field(description="用户角色")

        class Config:
            from_attributes = True

    data: List[UserItem] = Field(description="用户列表")


class UserStatsResponse(BaseResponse):
    """用户统计响应"""

    class UserStats(BaseModel):
        total_tasks: int = Field(description="总任务数")
        completed_tasks: int = Field(description="已完成任务数")
        in_progress_tasks: int = Field(description="进行中任务数")
        overdue_tasks: int = Field(description="逾期任务数")
        total_projects: int = Field(description="总项目数")
        active_projects: int = Field(description="活跃项目数")
        login_count: int = Field(description="登录次数")
        last_activity: Optional[datetime] = Field(description="最后活动时间")

    data: UserStats = Field(description="用户统计数据")
