#!/usr/bin/env python3
"""
认证系统控制器层 - Controller模式
负责HTTP请求处理和响应格式化
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.auth.models import (
    UserCreate, UserUpdate, UserResponse, LoginRequest, LoginResponse,
    RefreshTokenRequest, RefreshTokenResponse, PasswordChangeRequest, ApiResponse
)
from backend.auth.services import AuthService, AdminService
from backend.auth.repositories import UserRepository, SessionRepository, AuditLogRepository
from backend.auth.jwt_manager import JWTManager
from backend.auth.password_manager import PasswordManager
from backend.core.database import get_database_session
from backend.core.dependencies import get_current_user, require_admin_user
from backend.core.exceptions import (
    AuthenticationError, ValidationError, UserNotFoundError,
    AccountLockedException, TokenExpiredError
)

# 创建路由器
auth_router = APIRouter(prefix="/api/auth", tags=["Authentication"])
admin_router = APIRouter(prefix="/api/admin", tags=["Admin"])

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)

def get_auth_service(db: Session = Depends(get_database_session)) -> AuthService:
    """获取认证服务实例"""
    user_repo = UserRepository(db)
    session_repo = SessionRepository(db)
    audit_repo = AuditLogRepository(db)
    jwt_manager = JWTManager()
    password_manager = PasswordManager()

    return AuthService(
        user_repo=user_repo,
        session_repo=session_repo,
        audit_repo=audit_repo,
        jwt_manager=jwt_manager,
        password_manager=password_manager
    )

def get_admin_service(db: Session = Depends(get_database_session)) -> AdminService:
    """获取管理员服务实例"""
    user_repo = UserRepository(db)
    session_repo = SessionRepository(db)
    audit_repo = AuditLogRepository(db)

    return AdminService(
        user_repo=user_repo,
        session_repo=session_repo,
        audit_repo=audit_repo
    )

def get_client_info(request: Request) -> tuple[Optional[str], Optional[str]]:
    """获取客户端信息"""
    ip_address = None
    user_agent = request.headers.get("user-agent")

    # 获取真实IP地址
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        ip_address = forwarded_for.split(",")[0].strip()
    else:
        ip_address = getattr(request.client, 'host', None)

    return ip_address, user_agent

# === 公开端点 ===

@auth_router.post("/register", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
) -> ApiResponse:
    """用户注册"""
    try:
        ip_address, user_agent = get_client_info(request)

        result = await auth_service.register_user(
            user_data=user_data,
            ip_address=ip_address,
            user_agent=user_agent
        )

        return ApiResponse(
            success=True,
            message=result['message'],
            data={
                'user_id': result['user_id'],
                'verification_token': result['verification_token']
            }
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败"
        )

@auth_router.post("/login", response_model=LoginResponse)
async def login_user(
    login_data: LoginRequest,
    request: Request,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service)
) -> LoginResponse:
    """用户登录"""
    try:
        ip_address, user_agent = get_client_info(request)

        result = await auth_service.authenticate_user(
            login_data=login_data,
            ip_address=ip_address,
            user_agent=user_agent
        )

        # 设置安全的HTTP-only Cookie（可选）
        if login_data.remember_me:
            response.set_cookie(
                key="refresh_token",
                value=result.refresh_token,
                max_age=7 * 24 * 3600,  # 7天
                httponly=True,
                secure=True,
                samesite="strict"
            )

        return result

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except AccountLockedException as e:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@auth_router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
) -> RefreshTokenResponse:
    """刷新访问令牌"""
    try:
        ip_address, _ = get_client_info(request)

        result = await auth_service.refresh_access_token(
            refresh_token=refresh_data.refresh_token,
            ip_address=ip_address
        )

        return RefreshTokenResponse(
            access_token=result['access_token'],
            expires_in=result['expires_in']
        )

    except (AuthenticationError, TokenExpiredError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@auth_router.post("/logout", response_model=ApiResponse)
async def logout_user(
    request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> ApiResponse:
    """用户登出"""
    try:
        ip_address, _ = get_client_info(request)

        result = await auth_service.logout_user(
            access_token=credentials.credentials,
            ip_address=ip_address
        )

        # 清除Cookie
        response.delete_cookie(key="refresh_token")

        return ApiResponse(
            success=True,
            message=result['message']
        )

    except Exception as e:
        # 登出操作即使失败也返回成功
        response.delete_cookie(key="refresh_token")
        return ApiResponse(
            success=True,
            message="登出成功"
        )

# === 需要认证的端点 ===

@auth_router.get("/verify", response_model=ApiResponse)
async def verify_token(
    current_user: dict = Depends(get_current_user)
) -> ApiResponse:
    """验证访问令牌"""
    return ApiResponse(
        success=True,
        message="令牌有效",
        data={
            'user_id': current_user['user_id'],
            'username': current_user['username'],
            'role': current_user['role']
        }
    )

@auth_router.get("/profile", response_model=UserResponse)
async def get_user_profile(
    current_user: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> UserResponse:
    """获取用户资料"""
    try:
        return await auth_service.get_user_profile(current_user['user_id'])

    except UserNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

@auth_router.put("/profile", response_model=ApiResponse)
async def update_user_profile(
    profile_data: UserUpdate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> ApiResponse:
    """更新用户资料"""
    try:
        ip_address, _ = get_client_info(request)

        result = await auth_service.update_user_profile(
            user_id=current_user['user_id'],
            update_data=profile_data,
            ip_address=ip_address
        )

        return ApiResponse(
            success=True,
            message=result['message']
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@auth_router.post("/change-password", response_model=ApiResponse)
async def change_password(
    password_data: PasswordChangeRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> ApiResponse:
    """修改密码"""
    try:
        ip_address, _ = get_client_info(request)

        result = await auth_service.change_password(
            user_id=current_user['user_id'],
            current_password=password_data.current_password,
            new_password=password_data.new_password,
            ip_address=ip_address
        )

        return ApiResponse(
            success=True,
            message=result['message'],
            data={'revoked_sessions': result['revoked_sessions']}
        )

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@auth_router.get("/sessions")
async def get_user_sessions(
    current_user: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    """获取用户的活跃会话"""
    try:
        sessions = await auth_service.get_user_sessions(current_user['user_id'])

        return {
            'success': True,
            'sessions': sessions,
            'total': len(sessions)
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取会话列表失败"
        )

@auth_router.delete("/sessions/{session_id}", response_model=ApiResponse)
async def revoke_user_session(
    session_id: str,
    current_user: dict = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> ApiResponse:
    """撤销指定会话"""
    try:
        result = await auth_service.revoke_session(
            user_id=current_user['user_id'],
            session_id=session_id
        )

        return ApiResponse(
            success=True,
            message=result['message']
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

# === 管理员端点 ===

@admin_router.get("/users")
async def list_users(
    offset: int = 0,
    limit: int = 50,
    status_filter: Optional[str] = None,
    role_filter: Optional[str] = None,
    search_query: Optional[str] = None,
    admin_user: dict = Depends(require_admin_user),
    admin_service: AdminService = Depends(get_admin_service)
) -> Dict[str, Any]:
    """获取用户列表（管理员）"""
    try:
        # 验证分页参数
        if limit > 100:
            limit = 100
        if offset < 0:
            offset = 0

        result = await admin_service.get_users(
            offset=offset,
            limit=limit,
            status_filter=status_filter,
            role_filter=role_filter,
            search_query=search_query
        )

        return {
            'success': True,
            'data': result
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取用户列表失败"
        )

@admin_router.get("/security/stats")
async def get_security_statistics(
    admin_user: dict = Depends(require_admin_user),
    admin_service: AdminService = Depends(get_admin_service)
) -> Dict[str, Any]:
    """获取安全统计信息"""
    try:
        stats = await admin_service.get_security_stats()

        return {
            'success': True,
            'data': stats
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取安全统计失败"
        )

# === 健康检查端点 ===

@auth_router.get("/health")
async def health_check() -> Dict[str, Any]:
    """认证服务健康检查"""
    return {
        'status': 'healthy',
        'service': 'authentication',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    }

# === 密码要求端点 ===

@auth_router.get("/password-requirements")
async def get_password_requirements() -> Dict[str, Any]:
    """获取密码要求说明"""
    password_manager = PasswordManager()
    requirements = password_manager.get_password_requirements()

    return {
        'success': True,
        'data': requirements
    }