#!/usr/bin/env python3
"""
Perfect21认证API接口
提供用户登录、注册、令牌管理等HTTP接口
"""

import os
import sys
from typing import Dict, Any, Optional, Union
from fastapi import APIRouter, HTTPException, Depends, Request, Response, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field, validator
import json

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from features.auth_system import AuthManager
from modules.logger import log_info, log_error

# 创建API路由器
auth_router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)

# 全局认证管理器
auth_manager: Optional[AuthManager] = None

def get_auth_manager() -> AuthManager:
    """获取认证管理器实例"""
    global auth_manager
    if auth_manager is None:
        auth_manager = AuthManager()
    return auth_manager

# === 请求模型 ===

class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(description="邮箱地址")
    password: str = Field(min_length=8, description="密码")
    role: str = Field(default="user", description="用户角色")

    @validator('username')
    def validate_username(cls, v: str) -> str:
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('用户名只能包含字母、数字、下划线和连字符')
        return v

    @validator('password')
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('密码长度至少8位')
        return v

class LoginRequest(BaseModel):
    identifier: str = Field(min_length=1, description="用户名或邮箱")
    password: str = Field(min_length=1, description="密码")
    remember_me: bool = Field(default=False, description="记住我")

class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(min_length=1, description="刷新令牌")

class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=1, description="旧密码")
    new_password: str = Field(min_length=8, description="新密码")

    @validator('new_password')
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('新密码长度至少8位')
        return v

class UpdateProfileRequest(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = Field(None, description="邮箱地址")

    @validator('username')
    def validate_username(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('用户名只能包含字母、数字、下划线和连字符')
        return v

class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(description="邮箱地址")

class PasswordResetConfirmRequest(BaseModel):
    token: str = Field(min_length=1, description="重置令牌")
    new_password: str = Field(min_length=8, description="新密码")

    @validator('new_password')
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('新密码长度至少8位')
        return v

# === 响应模型 ===

class UserResponse(BaseModel):
    id: str = Field(description="用户ID")
    username: str = Field(description="用户名")
    email: str = Field(description="邮箱地址")
    role: str = Field(description="用户角色")
    created_at: Optional[str] = Field(None, description="创建时间")
    last_login: Optional[str] = Field(None, description="最后登录时间")

class LoginResponse(BaseModel):
    success: bool = Field(description="操作是否成功")
    access_token: Optional[str] = Field(None, description="访问令牌")
    refresh_token: Optional[str] = Field(None, description="刷新令牌")
    user: Optional[UserResponse] = Field(None, description="用户信息")
    expires_in: Optional[float] = Field(None, description="令牌过期时间（秒）")
    message: str = Field(description="响应消息")

class RegisterResponse(BaseModel):
    success: bool = Field(description="操作是否成功")
    user_id: Optional[str] = Field(None, description="用户ID")
    verification_token: Optional[str] = Field(None, description="验证令牌")
    message: str = Field(description="响应消息")

class RefreshResponse(BaseModel):
    success: bool = Field(description="操作是否成功")
    access_token: Optional[str] = Field(None, description="访问令牌")
    user: Optional[UserResponse] = Field(None, description="用户信息")
    expires_in: Optional[float] = Field(None, description="令牌过期时间（秒）")
    message: str = Field(description="响应消息")

class ApiResponse(BaseModel):
    success: bool = Field(description="操作是否成功")
    message: str = Field(description="响应消息")
    error: Optional[str] = Field(None, description="错误信息")

# === 依赖项 ===

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """获取当前用户（认证依赖）"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要认证",
            headers={"WWW-Authenticate": "Bearer"}
        )

    auth_mgr = get_auth_manager()
    result = auth_mgr.verify_token(credentials.credentials)

    if not result['success']:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result['message'],
            headers={"WWW-Authenticate": "Bearer"}
        )

    return result['user']

async def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[Dict[str, Any]]:
    """获取可选的当前用户"""
    if not credentials:
        return None

    try:
        auth_mgr = get_auth_manager()
        result = auth_mgr.verify_token(credentials.credentials)
        return result['user'] if result['success'] else None
    except Exception:
        return None

# === API端点 ===

@auth_router.post("/register", response_model=RegisterResponse)
async def register(request: RegisterRequest, req: Request):
    """用户注册"""
    try:
        auth_mgr = get_auth_manager()
        result = auth_mgr.register(
            username=request.username,
            email=request.email,
            password=request.password,
            role=request.role
        )

        # 记录请求信息
        if not result['success']:
            log_info(f"注册失败: {result['message']} - IP: {req.client.host}")
        else:
            log_info(f"用户注册成功: {request.username} - IP: {req.client.host}")

        return RegisterResponse(
            success=result['success'],
            user_id=result.get('user_id'),
            verification_token=result.get('verification_token'),
            message=result['message']
        )

    except Exception as e:
        log_error("注册接口异常", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误"
        )

@auth_router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, req: Request):
    """用户登录"""
    try:
        auth_mgr = get_auth_manager()
        result = auth_mgr.login(
            identifier=request.identifier,
            password=request.password,
            remember_me=request.remember_me
        )

        # 记录请求信息
        if not result['success']:
            log_info(f"登录失败: {result['message']} - {request.identifier} - IP: {req.client.host}")
        else:
            log_info(f"用户登录成功: {request.identifier} - IP: {req.client.host}")

        response_data = LoginResponse(
            success=result['success'],
            access_token=result.get('access_token'),
            refresh_token=result.get('refresh_token'),
            expires_in=result.get('expires_in'),
            message=result['message']
        )

        # 添加用户信息
        if result['success'] and 'user' in result:
            user_data = result['user']
            response_data.user = UserResponse(
                id=str(user_data['id']),
                username=user_data['username'],
                email=user_data['email'],
                role=user_data['role'],
                created_at=user_data.get('created_at'),
                last_login=user_data.get('last_login')
            )

        return response_data

    except Exception as e:
        log_error("登录接口异常", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误"
        )

@auth_router.post("/logout", response_model=ApiResponse)
async def logout(current_user: Dict[str, Any] = Depends(get_current_user),
                credentials: HTTPAuthorizationCredentials = Depends(security)):
    """用户登出"""
    try:
        auth_mgr = get_auth_manager()
        result = auth_mgr.logout(credentials.credentials)

        log_info(f"用户登出: {current_user['username']}")

        return ApiResponse(
            success=result['success'],
            message=result['message']
        )

    except Exception as e:
        log_error("登出接口异常", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误"
        )

@auth_router.post("/refresh", response_model=RefreshResponse)
async def refresh_token(request: RefreshTokenRequest):
    """刷新访问令牌"""
    try:
        auth_mgr = get_auth_manager()
        result = auth_mgr.refresh_token(request.refresh_token)

        response_data = RefreshResponse(
            success=result['success'],
            access_token=result.get('access_token'),
            expires_in=result.get('expires_in'),
            message=result['message']
        )

        # 添加用户信息
        if result['success'] and 'user' in result:
            user_data = result['user']
            response_data.user = UserResponse(
                id=str(user_data['id']),
                username=user_data['username'],
                email=user_data['email'],
                role=user_data['role']
            )

        return response_data

    except Exception as e:
        log_error("令牌刷新接口异常", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误"
        )

@auth_router.get("/verify", response_model=ApiResponse)
async def verify_token(current_user: Dict[str, Any] = Depends(get_current_user)):
    """验证访问令牌"""
    return ApiResponse(
        success=True,
        message="令牌验证成功"
    )

@auth_router.get("/profile", response_model=UserResponse)
async def get_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """获取用户资料"""
    try:
        auth_mgr = get_auth_manager()
        result = auth_mgr.get_user_profile(current_user['id'])

        if not result['success']:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result['message']
            )

        user_data = result['user']
        return UserResponse(
            id=str(user_data['id']),
            username=user_data['username'],
            email=user_data['email'],
            role=user_data['role'],
            created_at=user_data.get('created_at'),
            last_login=user_data.get('last_login')
        )

    except HTTPException:
        raise
    except Exception as e:
        log_error("获取用户资料接口异常", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误"
        )

@auth_router.put("/profile", response_model=ApiResponse)
async def update_profile(request: UpdateProfileRequest,
                        current_user: Dict[str, Any] = Depends(get_current_user)):
    """更新用户资料"""
    try:
        auth_mgr = get_auth_manager()

        # 构建更新数据
        update_data = {}
        if request.username is not None:
            update_data['username'] = request.username
        if request.email is not None:
            update_data['email'] = str(request.email)

        result = auth_mgr.update_user_profile(current_user['id'], **update_data)

        log_info(f"用户资料更新: {current_user['username']} - 更新字段: {list(update_data.keys())}")

        return ApiResponse(
            success=result['success'],
            message=result['message'],
            error=result.get('error')
        )

    except Exception as e:
        log_error("更新用户资料接口异常", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误"
        )

@auth_router.post("/change-password", response_model=ApiResponse)
async def change_password(request: ChangePasswordRequest,
                         current_user: Dict[str, Any] = Depends(get_current_user)):
    """修改密码"""
    try:
        auth_mgr = get_auth_manager()
        result = auth_mgr.change_password(
            user_id=current_user['id'],
            old_password=request.old_password,
            new_password=request.new_password
        )

        log_info(f"用户修改密码: {current_user['username']}")

        return ApiResponse(
            success=result['success'],
            message=result['message'],
            error=result.get('error')
        )

    except Exception as e:
        log_error("修改密码接口异常", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误"
        )

@auth_router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: Dict[str, Any] = Depends(get_current_user)):
    """获取当前用户信息"""
    return UserResponse(
        id=str(current_user['id']),
        username=current_user['username'],
        email=current_user['email'],
        role=current_user['role']
    )

# === 管理员端点（需要admin角色） ===

async def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)):
    """需要管理员权限"""
    if current_user.get('role') != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user

@auth_router.get("/admin/users")
async def list_users(admin_user: Dict[str, Any] = Depends(require_admin)):
    """管理员：获取用户列表"""
    try:
        auth_mgr = get_auth_manager()
        # 这里应该实现获取用户列表的逻辑
        # 暂时返回空列表
        return {
            "success": True,
            "users": [],
            "total": 0,
            "message": "功能待实现"
        }

    except Exception as e:
        log_error("获取用户列表接口异常", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误"
        )

@auth_router.get("/admin/security/stats")
async def get_security_stats(admin_user: Dict[str, Any] = Depends(require_admin)):
    """管理员：获取安全统计"""
    try:
        auth_mgr = get_auth_manager()
        stats = auth_mgr.security_service.get_security_stats()

        return {
            "success": True,
            "stats": stats
        }

    except Exception as e:
        log_error("获取安全统计接口异常", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误"
        )

# === 健康检查端点 ===

@auth_router.get("/health")
async def health_check():
    """认证服务健康检查"""
    try:
        auth_mgr = get_auth_manager()
        return {
            "status": "healthy",
            "service": "auth",
            "timestamp": str(json.dumps({"timestamp": "now"}, default=str))
        }
    except Exception as e:
        log_error("认证服务健康检查失败", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="认证服务不可用"
        )