#!/usr/bin/env python3
"""
FastAPI依赖项
定义认证、授权等通用依赖
"""

from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.core.database import get_database_session
from backend.auth.repositories import UserRepository
from backend.auth.jwt_manager import JWTManager
from backend.core.exceptions import (
    AuthenticationError, TokenExpiredError, UserNotFoundError
)

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)

# JWT管理器实例
jwt_manager = JWTManager()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_database_session)
) -> Dict[str, Any]:
    """
    获取当前认证用户
    依赖项：验证JWT令牌并返回用户信息
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需要认证",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        # 验证JWT令牌
        token_payload = jwt_manager.verify_token(credentials.credentials, 'access')

        # 从数据库获取用户信息
        user_repo = UserRepository(db)
        user = user_repo.get_user_by_id(token_payload.user_id)

        if not user or user.status != 'active':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在或已被禁用",
                headers={"WWW-Authenticate": "Bearer"}
            )

        return {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'session_id': getattr(token_payload, 'session_id', None)
        }

    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="令牌已过期",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="认证验证失败"
        )

async def get_optional_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_database_session)
) -> Optional[Dict[str, Any]]:
    """
    获取可选的当前用户
    如果没有认证信息则返回None，不抛出异常
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None

async def require_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    要求管理员权限
    依赖项：验证当前用户是否为管理员
    """
    if current_user.get('role') != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )

    return current_user

async def require_moderator_user(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    要求版主权限
    依赖项：验证当前用户是否为版主或管理员
    """
    if current_user.get('role') not in ['admin', 'moderator']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要版主或管理员权限"
        )

    return current_user

async def require_verified_user(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_database_session)
) -> Dict[str, Any]:
    """
    要求已验证邮箱的用户
    依赖项：验证用户是否已验证邮箱
    """
    user_repo = UserRepository(db)
    user = user_repo.get_user_by_id(current_user['user_id'])

    if not user or not user.email_verified_at:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要验证邮箱后才能访问此功能"
        )

    return current_user

def get_client_ip(request: Request) -> str:
    """
    获取客户端真实IP地址
    依赖项：提取客户端IP
    """
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip

    return getattr(request.client, 'host', 'unknown')

def get_user_agent(request: Request) -> str:
    """
    获取用户代理字符串
    依赖项：提取用户代理信息
    """
    return request.headers.get("user-agent", "unknown")

class RoleChecker:
    """角色检查器类"""

    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if current_user.get('role') not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"需要以下角色之一: {', '.join(self.allowed_roles)}"
            )
        return current_user

# 预定义的角色检查器
require_admin = RoleChecker(['admin'])
require_admin_or_moderator = RoleChecker(['admin', 'moderator'])
require_any_authenticated = RoleChecker(['admin', 'moderator', 'user'])

class PermissionChecker:
    """权限检查器类"""

    def __init__(self, required_permission: str):
        self.required_permission = required_permission

    def __call__(
        self,
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: Session = Depends(get_database_session)
    ) -> Dict[str, Any]:
        """
        检查用户是否具有指定权限
        这里简化处理，实际应该实现完整的权限系统
        """
        user_role = current_user.get('role')

        # 管理员拥有所有权限
        if user_role == 'admin':
            return current_user

        # 根据权限名称进行检查
        permission_role_map = {
            'read_users': ['admin', 'moderator'],
            'write_users': ['admin'],
            'read_logs': ['admin', 'moderator'],
            'system_config': ['admin'],
        }

        allowed_roles = permission_role_map.get(self.required_permission, [])
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足: {self.required_permission}"
            )

        return current_user

def rate_limit_key_generator(request: Request) -> str:
    """
    生成速率限制键
    依赖项：为速率限制生成唯一键
    """
    client_ip = get_client_ip(request)
    endpoint = request.url.path
    return f"rate_limit:{client_ip}:{endpoint}"

async def validate_pagination(
    offset: int = 0,
    limit: int = 50
) -> Dict[str, int]:
    """
    验证分页参数
    依赖项：验证和规范化分页参数
    """
    # 验证offset
    if offset < 0:
        offset = 0

    # 验证limit
    if limit <= 0:
        limit = 50
    elif limit > 100:  # 最大限制
        limit = 100

    return {'offset': offset, 'limit': limit}

class DatabaseTransactionManager:
    """数据库事务管理器"""

    def __init__(self, db: Session = Depends(get_database_session)):
        self.db = db

    async def __aenter__(self):
        return self.db

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.db.rollback()
        else:
            self.db.commit()

# 预定义权限检查器
require_read_users_permission = PermissionChecker('read_users')
require_write_users_permission = PermissionChecker('write_users')
require_read_logs_permission = PermissionChecker('read_logs')
require_system_config_permission = PermissionChecker('system_config')